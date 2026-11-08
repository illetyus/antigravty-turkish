# Google Antigravity Türkçe Yama Kaldırma Aracı (Uninstaller)
# Path: D:\Android\Tools\Antigravity-TR\Uninstall-AntigravityTR.ps1

[CmdletBinding()]
param ()

$Host.UI.RawUI.WindowTitle = "Antigravity Türkçe Yama Kaldırma"
Clear-Host

Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host "     Google Antigravity Türkçe Yama Kaldırma Aracı        " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Yellow
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Otomatik Güncelleme Görevini Kaldırma
Write-Host "[*] Arka plan izleyicisi ve başlangıç kaydı temizleniyor..." -ForegroundColor Yellow
$UnregScript = Join-Path $ScriptDir "Unregister-AntigravityTRTask.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $UnregScript

# 2. Orijinal ASAR'ı Geri Yükleme
$AsarPath = "$env:LOCALAPPDATA\Programs\antigravity\resources\app.asar"
$BakOriginal = "$AsarPath.bak.original"

if (Test-Path $BakOriginal) {
    Write-Host "[*] Orijinal fabrika yedeği geri yükleniyor ($BakOriginal)..." -ForegroundColor Yellow
    try {
        Copy-Item $BakOriginal $AsarPath -Force
        Write-Host "[+] Orijinal fabrika app.asar başarıyla geri yüklendi!" -ForegroundColor Green
    } catch {
        Write-Host "[-] UYARI: app.asar dosyası Antigravity tarafından kilitli olabilir. Lütfen Antigravity'yi kapatıp tekrar deneyin." -ForegroundColor Red
    }
} else {
    Write-Host "[*] Orijinal yedek bulunamadı, unpatch deneniyor..." -ForegroundColor Yellow
    function Get-PythonPath {
        if (Test-Path "D:\Android\Tools\Python\Python312\python.exe") { return "D:\Android\Tools\Python\Python312\python.exe" }
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
        return "python"
    }
    $py = Get-PythonPath
    $patcher = Join-Path $ScriptDir "patch_asar.py"
    & $py $patcher --asar $AsarPath --restore
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Antigravity Türkçe Yaması Başarıyla Kaldırıldı.        " -ForegroundColor White
Write-Host "  Uygulama orijinal İngilizce haline döndürüldü.         " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
