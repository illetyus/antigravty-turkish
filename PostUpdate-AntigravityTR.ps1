# Antigravity Turkish One-Shot Post-Update Guard
# Spawned ONLY when an update is being installed; seals the new app.asar and exits immediately.
# Path: D:\Android\Tools\Antigravity-TR\PostUpdate-AntigravityTR.ps1

[CmdletBinding()]
param (
    [string]$AsarPath = "$env:LOCALAPPDATA\Programs\antigravity\resources\app.asar",
    [string]$PatcherScript = "",
    [string]$HotApplyScript = "",
    [string]$ShortcutsScript = "",
    [string]$StampPath = "",
    [string]$LogPath = "",
    [int]$OldPid = 0,
    [int]$MaxWaitSeconds = 180,
    [switch]$DisableHotApply,
    [switch]$SkipShortcuts
)

$ErrorActionPreference = "SilentlyContinue"

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if ([string]::IsNullOrWhiteSpace($PatcherScript)) {
    $PatcherScript = Join-Path $ScriptDir "patch_asar.py"
}
if ($DisableHotApply) {
    $HotApplyScript = ""
} elseif ([string]::IsNullOrWhiteSpace($HotApplyScript)) {
    $HotApplyScript = Join-Path $ScriptDir "hot_apply.js"
}
if ([string]::IsNullOrWhiteSpace($ShortcutsScript)) {
    $ShortcutsScript = Join-Path $ScriptDir "Configure-AntigravityShortcuts.ps1"
}
if ([string]::IsNullOrWhiteSpace($StampPath)) {
    $StampPath = Join-Path $ScriptDir ".last_patched_stamp"
}
if ([string]::IsNullOrWhiteSpace($LogPath)) {
    $baseTemp = if (Test-Path "D:\Android\Temp") { "D:\Android\Temp" } else { $env:TEMP }
    $LogPath = Join-Path $baseTemp "antigravity-tr-postupdate.log"
}

function Get-PythonPath {
    if (Test-Path "D:\Android\Tools\Python\Python312\python.exe") { return "D:\Android\Tools\Python\Python312\python.exe" }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { return $pyCmd.Source }
    return "python"
}

function Get-NodePath {
    if (Test-Path "D:\Android\Tools\Nodejs\node.exe") { return "D:\Android\Tools\Nodejs\node.exe" }
    $cmd = Get-Command node -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Write-GuardLog {
    param([string]$Message)
    if ([string]::IsNullOrWhiteSpace($LogPath)) { return }
    try {
        $dir = Split-Path -Parent $LogPath
        if ($dir -and (-not (Test-Path $dir))) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        if (Test-Path $LogPath) {
            $fi = Get-Item $LogPath -ErrorAction SilentlyContinue
            if ($fi -and $fi.Length -gt 65536) {
                $tail = Get-Content $LogPath -Tail 150 -ErrorAction SilentlyContinue
                [System.IO.File]::WriteAllLines($LogPath, $tail, [System.Text.UTF8Encoding]::new($false))
            }
        }
        $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        [System.IO.File]::AppendAllText($LogPath, "[$ts] $Message`r`n", [System.Text.UTF8Encoding]::new($false))
    } catch {}
}

function Get-AsarFingerprint {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    $item = Get-Item $Path -ErrorAction SilentlyContinue
    if (-not $item) { return $null }
    return "$($item.Length):$($item.LastWriteTimeUtc.Ticks)"
}

function Wait-FileStable {
    param([string]$Path, [int]$MaxChecks = 16)
    $prevLen = -1
    for ($i = 0; $i -lt $MaxChecks; $i++) {
        if (-not (Test-Path $Path)) {
            Start-Sleep -Milliseconds 250
            continue
        }
        $item = Get-Item $Path -ErrorAction SilentlyContinue
        if ($item) {
            try {
                $fs = [System.IO.File]::Open($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
                $fs.Close()
                if ($prevLen -eq $item.Length -and $item.Length -gt 0) {
                    return $true
                }
                $prevLen = $item.Length
            } catch {
                $prevLen = -1
            }
        }
        Start-Sleep -Milliseconds 250
    }
    return (Test-Path $Path)
}

function Write-FsoStamp {
    param([string]$Path)
    try {
        if (-not (Test-Path $Path)) { return }
        $fso = New-Object -ComObject Scripting.FileSystemObject
        $f = $fso.GetFile($Path)
        $stamp = "$($f.Size)|$($f.DateLastModified)"
        [System.IO.File]::WriteAllText($StampPath, $stamp, [System.Text.UTF8Encoding]::new($false))
    } catch {}
}

function Invoke-HotApplyIfLive {
    if ([string]::IsNullOrWhiteSpace($HotApplyScript) -or (-not (Test-Path $HotApplyScript))) { return }
    $nodeExe = Get-NodePath
    if (-not $nodeExe) { return }
    $devPortFile = "$env:APPDATA\antigravity\DevToolsActivePort"
    # Give newly relaunched Antigravity a short window to expose DevToolsActivePort
    for ($wait = 0; $wait -lt 8; $wait++) {
        $live = Get-Process -Name "Antigravity" -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $OldPid }
        if ($live -and (Test-Path $devPortFile)) {
            $out = (& $nodeExe $HotApplyScript 2>&1) | Out-String
            if ($LASTEXITCODE -eq 0 -and $out -match "Hot apply completed successfully") {
                Write-GuardLog "Canli yeni pencereye hot_apply.js uygulandi."
                return
            }
        }
        Start-Sleep -Seconds 1
    }
}

$PythonExe = Get-PythonPath
$initialSig = Get-AsarFingerprint -Path $AsarPath
$deadline = (Get-Date).AddSeconds($MaxWaitSeconds)
Write-GuardLog "Tek seferlik guncelleme koruyucusu basladi (OldPid=$OldPid, MaxWait=${MaxWaitSeconds}s)."

$initialCheckedUnpatched = $false
while ((Get-Date) -lt $deadline) {
    if (Test-Path $AsarPath) {
        $curSig = Get-AsarFingerprint -Path $AsarPath
        $changed = ($null -eq $initialSig) -or ($curSig -ne $initialSig)
        if ($changed -or (-not $initialCheckedUnpatched)) {
            $initialCheckedUnpatched = $true
            [void](Wait-FileStable -Path $AsarPath)
            & $PythonExe $PatcherScript --asar $AsarPath --check *>$null
            if ($LASTEXITCODE -ne 0) {
                Write-GuardLog "Yamasiz yeni app.asar tespit edildi, muhurleniyor..."
                $patchedOk = $false
                for ($attempt = 1; $attempt -le 5; $attempt++) {
                    $out = (& $PythonExe $PatcherScript --asar $AsarPath 2>&1) | Out-String
                    if ($LASTEXITCODE -eq 0) {
                        Write-GuardLog "Yeni surum basariyla yamalandi (deneme $attempt)."
                        $patchedOk = $true
                        break
                    }
                    Write-GuardLog "Yama denemesi $attempt basarisiz: $($out.Trim())"
                    Start-Sleep -Seconds 2
                }
                if ($patchedOk) {
                    Write-FsoStamp -Path $AsarPath
                    if ((-not $SkipShortcuts) -and (Test-Path $ShortcutsScript)) {
                        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ShortcutsScript -Quiet *>$null
                        Write-GuardLog "Kisayollar yenilendi."
                    }
                    Invoke-HotApplyIfLive
                    Write-GuardLog "Tek seferlik koruma tamamlandi, cikiliyor."
                    exit 0
                }
            } elseif ($changed) {
                Write-FsoStamp -Path $AsarPath
                Write-GuardLog "Degisen app.asar zaten yamali, cikiliyor."
                exit 0
            }
        }
    }
    Start-Sleep -Seconds 1
}

Write-GuardLog "Zaman asimi (${MaxWaitSeconds}s) doldu, arka planda bekleme yapmadan cikiliyor."
exit 0
