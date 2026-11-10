# Antigravity Turkish Addon Configurator (Zero Background Process)
# Removes any legacy background watcher and links shortcuts to Launch-Antigravity.vbs.
# Path: D:\Android\Tools\Antigravity-TR\Register-AntigravityTRTask.ps1

[CmdletBinding()]
param ()

$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }

# 1. Remove any legacy background watcher startup entry or process
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$regName = "AntigravityTurkishAutoPatch"
if (Get-ItemProperty -Path $regPath -Name $regName -ErrorAction SilentlyContinue) {
    Remove-ItemProperty -Path $regPath -Name $regName -ErrorAction SilentlyContinue
    Write-Host "[+] Eski arka plan izleyici baslangic kaydi temizlendi." -ForegroundColor Yellow
}

$legacyWatchers = Get-CimInstance Win32_Process -Filter "Name='powershell.exe'" | Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -like "*-File*Watch-AntigravityUpdate.ps1*" -and $_.CommandLine -notmatch "Get-CimInstance" }
foreach ($w in $legacyWatchers) {
    Stop-Process -Id $w.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "[+] Eski arka plan izleyici sureci durduruldu (PID: $($w.ProcessId))." -ForegroundColor Yellow
}

# 2. Wrap Antigravity shortcuts for on-launch protection (zero idle task)
$ShortcutsPs = Join-Path $ScriptDir "Configure-AntigravityShortcuts.ps1"
if (Test-Path $ShortcutsPs) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $ShortcutsPs
}
Write-Host "[+] Uygulama ici guncelleme addon kancasi (dist/updater.js) ve baslatici kisayollar hazir." -ForegroundColor Green
