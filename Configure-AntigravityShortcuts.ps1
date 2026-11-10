# Antigravity Turkish Shortcut Wrapper Configurator
# Wraps Start Menu / TaskBar / Desktop shortcuts to launch via Launch-Antigravity.vbs
# without leaving any persistent background process running.
# Path: D:\Android\Tools\Antigravity-TR\Configure-AntigravityShortcuts.ps1

[CmdletBinding()]
param (
    [switch]$Restore,
    [switch]$Quiet,
    [string[]]$ShortcutPaths = @(),
    [string]$TargetExe = "$env:LOCALAPPDATA\Programs\antigravity\Antigravity.exe",
    [string]$BackupDir = ""
)

$ErrorActionPreference = "SilentlyContinue"

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$LaunchVbs = Join-Path $ScriptDir "Launch-Antigravity.vbs"
if ([string]::IsNullOrWhiteSpace($BackupDir)) {
    $BackupDir = Join-Path (Join-Path $ScriptDir "backups") "shortcuts"
}

if (-not $ShortcutPaths -or $ShortcutPaths.Count -eq 0) {
    $ShortcutPaths = @(
        "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Antigravity.lnk",
        "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar\Antigravity.lnk",
        "$env:USERPROFILE\Desktop\Antigravity.lnk"
    )
}

function Get-BackupPath {
    param([string]$LnkPath)
    $sha = [System.Security.Cryptography.SHA256]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($LnkPath.ToLowerInvariant())
    $hash = ([System.BitConverter]::ToString($sha.ComputeHash($bytes))).Replace("-", "").Substring(0, 12)
    $name = [System.IO.Path]::GetFileName($LnkPath)
    return (Join-Path $BackupDir "${hash}_${name}")
}

$WshShell = New-Object -ComObject WScript.Shell
$WscriptExe = "$env:WINDIR\System32\wscript.exe"

if (-not $Restore) {
    if (-not (Test-Path $LaunchVbs)) {
        if (-not $Quiet) { Write-Warning "Launch-Antigravity.vbs bulunamadi: $LaunchVbs" }
        exit 1
    }
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null
    }

    $updatedCount = 0
    foreach ($lnkPath in $ShortcutPaths) {
        if (-not (Test-Path $lnkPath)) { continue }
        $sc = $WshShell.CreateShortcut($lnkPath)
        $isAlreadyWrapped = ($sc.TargetPath -like "*wscript.exe") -and ($sc.Arguments -like "*Launch-Antigravity.vbs*")

        if (-not $isAlreadyWrapped) {
            $bakPath = Get-BackupPath -LnkPath $lnkPath
            if (-not (Test-Path $bakPath)) {
                Copy-Item -Path $lnkPath -Destination $bakPath -Force
            }
        }

        $origIcon = $sc.IconLocation
        if ([string]::IsNullOrWhiteSpace($origIcon) -or $origIcon -eq ",0" -or $origIcon.StartsWith(",")) {
            $origIcon = "$TargetExe,0"
        }

        $extraArgs = ""
        if (-not $isAlreadyWrapped -and -not [string]::IsNullOrWhiteSpace($sc.Arguments)) {
            $extraArgs = " " + $sc.Arguments
        }

        $sc.TargetPath = $WscriptExe
        $sc.Arguments = "`"$LaunchVbs`"$extraArgs"
        $sc.WorkingDirectory = Split-Path -Parent $TargetExe
        $sc.IconLocation = $origIcon
        $sc.Save()
        $updatedCount++
        if (-not $Quiet) {
            Write-Host "[+] Kisayol Turkce baslaticiya baglandi: $lnkPath" -ForegroundColor Green
        }
    }
    if ((-not $Quiet) -and $updatedCount -eq 0) {
        Write-Host "[*] Guncellenecek mevcut Antigravity kisayolu bulunamadi." -ForegroundColor Yellow
    }
} else {
    foreach ($lnkPath in $ShortcutPaths) {
        if (-not (Test-Path $lnkPath)) { continue }
        $bakPath = Get-BackupPath -LnkPath $lnkPath
        if (Test-Path $bakPath) {
            Copy-Item -Path $bakPath -Destination $lnkPath -Force
            if (-not $Quiet) {
                Write-Host "[+] Kisayol orijinal yedeginden geri yuklendi: $lnkPath" -ForegroundColor Green
            }
            continue
        }

        $sc = $WshShell.CreateShortcut($lnkPath)
        if ($sc.TargetPath -like "*wscript.exe" -and $sc.Arguments -like "*Launch-Antigravity.vbs*") {
            $sc.TargetPath = $TargetExe
            $sc.Arguments = ""
            $sc.WorkingDirectory = Split-Path -Parent $TargetExe
            $sc.IconLocation = "$TargetExe,0"
            $sc.Save()
            if (-not $Quiet) {
                Write-Host "[+] Kisayol dogrudan Antigravity.exe hedefine donduruldu: $lnkPath" -ForegroundColor Green
            }
        }
    }
}
exit 0
