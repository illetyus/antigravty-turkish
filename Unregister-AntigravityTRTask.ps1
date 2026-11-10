# Antigravity Turkish Addon Unregistrar & Shortcut Restorer
# Path: D:\Android\Tools\Antigravity-TR\Unregister-AntigravityTRTask.ps1

[CmdletBinding()]
param ()

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

# 1. Remove any legacy HKCU Run entry
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$regName = "AntigravityTurkishAutoPatch"
if (Get-ItemProperty -Path $regPath -Name $regName -ErrorAction SilentlyContinue) {
    Remove-ItemProperty -Path $regPath -Name $regName -ErrorAction SilentlyContinue
    Write-Host "[+] Baslangic kaydi (HKCU Run) kaldirildi." -ForegroundColor Green
}

# 2. Stop any legacy watcher processes if present
$watchers = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -like "*-File*Watch-AntigravityUpdate.ps1*" -and $_.CommandLine -notmatch "Get-CimInstance" }
foreach ($w in $watchers) {
    try {
        Stop-Process -Id $w.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[+] Arka plan izleyici sureci durduruldu (PID: $($w.ProcessId))." -ForegroundColor Green
    } catch {}
}

# 3. Restore original Antigravity shortcuts
$ShortcutsPs = Join-Path $ScriptDir "Configure-AntigravityShortcuts.ps1"
if (Test-Path $ShortcutsPs) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ShortcutsPs -Restore
}
