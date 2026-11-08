# Antigravity Turkish Auto-Patch Watcher Registrar
# Path: D:\Android\Tools\Antigravity-TR\Register-AntigravityTRTask.ps1

[CmdletBinding()]
param ()

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VbsPath = Join-Path $ScriptDir "Start-AntigravityTR-Watcher.vbs"
$WatcherPs1 = Join-Path $ScriptDir "Watch-AntigravityUpdate.ps1"

# 1. Ensure Start-AntigravityTR-Watcher.vbs exists with correct path
$vbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File ""$WatcherPs1""", 0, False
"@

[System.IO.File]::WriteAllText($VbsPath, $vbsContent, [System.Text.Encoding]::ASCII)
Write-Host "[+] VBS başlatıcı güncellendi: $VbsPath" -ForegroundColor Cyan

# 2. Register in HKCU Run key for current user startup
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$regName = "AntigravityTurkishAutoPatch"
$regValue = "`"wscript.exe`" `"$VbsPath`""

Set-ItemProperty -Path $regPath -Name $regName -Value $regValue
Write-Host "[+] Başlangıç kaydı (HKCU Run) eklendi: $regName" -ForegroundColor Green

# 3. Start the watcher immediately if not running
$existing = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*Watch-AntigravityUpdate*" -and $_.ProcessId -ne $PID }
if (-not $existing) {
    Start-Process -FilePath "wscript.exe" -ArgumentList "`"$VbsPath`""
    Write-Host "[+] Arka plan izleyici süreci (Watch-AntigravityUpdate) hemen başlatıldı." -ForegroundColor Green
} else {
    Write-Host "[*] Arka plan izleyici süreci zaten çalışıyor." -ForegroundColor Yellow
}
