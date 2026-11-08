# Antigravity Turkish Auto-Patch Watcher Unregistrar
# Path: D:\Android\Tools\Antigravity-TR\Unregister-AntigravityTRTask.ps1

[CmdletBinding()]
param ()

# 1. Remove from HKCU Run
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$regName = "AntigravityTurkishAutoPatch"

if (Get-ItemProperty -Path $regPath -Name $regName -ErrorAction SilentlyContinue) {
    Remove-ItemProperty -Path $regPath -Name $regName -ErrorAction SilentlyContinue
    Write-Host "[+] Başlangıç kaydı (HKCU Run) kaldırıldı." -ForegroundColor Green
} else {
    Write-Host "[*] Başlangıç kaydı bulunamadı veya zaten silinmiş." -ForegroundColor Yellow
}

# 2. Stop running watcher processes
$watchers = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*Watch-AntigravityUpdate*" }
foreach ($w in $watchers) {
    try {
        Stop-Process -Id $w.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "[+] Arka plan izleyici süreci durduruldu (PID: $($w.ProcessId))." -ForegroundColor Green
    } catch {}
}
