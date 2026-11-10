# Google Antigravity Türkçe Yama Kurulum Aracı (Installer)
# Path: D:\Android\Tools\Antigravity-TR\Install-AntigravityTR.ps1

[CmdletBinding()]
param ()

$Host.UI.RawUI.WindowTitle = "Antigravity Türkçe Yama Kurulumu"
Clear-Host

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "     Google Antigravity 2.0 Türkçe Yama Kurulum Aracı     " -ForegroundColor White
Write-Host "         Otomatik Güncelleme Dirençli (Addon Modu)        " -ForegroundColor DarkCyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Python Tespiti
function Get-PythonPath {
    if (Test-Path "D:\Android\Tools\Python\Python312\python.exe") { return "D:\Android\Tools\Python\Python312\python.exe" }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { return $pyCmd.Source }
    return $null
}

$PythonExe = Get-PythonPath
if (-not $PythonExe) {
    Write-Host "[-] HATA: Sistemde Python 3 bulunamadı." -ForegroundColor Red
    Write-Host "    Lütfen Python 3.10+ kurun veya PATH ortam değişkenine ekleyin." -ForegroundColor Yellow
    exit 1
}
Write-Host "[+] Python Ortamı Bulundu: $PythonExe" -ForegroundColor Green

# 2. Antigravity Tespiti
$AsarPath = "$env:LOCALAPPDATA\Programs\antigravity\resources\app.asar"
if (-not (Test-Path $AsarPath)) {
    Write-Host "[-] HATA: Antigravity kurulumu bulunamadı ($AsarPath)." -ForegroundColor Red
    Write-Host "    Lütfen Google Antigravity'nin kurulu olduğundan emin olun." -ForegroundColor Yellow
    exit 1
}
Write-Host "[+] Antigravity Kurulumu Doğrulandı: $AsarPath" -ForegroundColor Green

# 3. Orijinal Yedek Güvencesi (Sadece yamasız fabrika ASAR'ını yedekle)
$BakOriginal = "$AsarPath.bak.original"
$PatcherScript = Join-Path $ScriptDir "patch_asar.py"
if (-not (Test-Path $BakOriginal)) {
    & $PythonExe $PatcherScript --asar $AsarPath --check *>$null
    if ($LASTEXITCODE -ne 0) {
        Copy-Item $AsarPath $BakOriginal -Force
        Write-Host "[+] Orijinal fabrika yedeği alındı: $BakOriginal" -ForegroundColor Green
    } else {
        $cleanBak = Get-ChildItem (Join-Path $ScriptDir "backups") -Filter "app.asar.bak.*" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($cleanBak) {
            Copy-Item $cleanBak.FullName $BakOriginal -Force
            Write-Host "[+] Mevcut temiz yedekten fabrika yedeği oluşturuldu: $BakOriginal" -ForegroundColor Green
        }
    }
} else {
    Write-Host "[*] Orijinal fabrika yedeği zaten mevcut, korundu." -ForegroundColor DarkGray
}

# 4. Dil Dosyasını Derleme
Write-Host "[*] Türkçe sözlük ve desenler derleniyor..." -ForegroundColor Yellow
$BuildScript = Join-Path $ScriptDir "build_locale.py"
& $PythonExe $BuildScript
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] HATA: Dil dosyası derlenemedi." -ForegroundColor Red
    exit 1
}
Write-Host "[+] Dil modülü (tr-locale.js) başarıyla derlendi." -ForegroundColor Green

# 5. ASAR Yamalama
Write-Host "[*] app.asar mühürleniyor..." -ForegroundColor Yellow
$PatcherScript = Join-Path $ScriptDir "patch_asar.py"
& $PythonExe $PatcherScript --asar $AsarPath --force
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] UYARI: ASAR yamalama sırasında bir uyarı/hata oluştu." -ForegroundColor Yellow
} else {
    Write-Host "[+] ASAR Türkçe yaması başarıyla diske uygulandı!" -ForegroundColor Green
}

# 6. Sıfır Arka Plan Görevli Addon & Kısayol Koruması Kaydı
Write-Host "[*] Addon koruma kancası ve başlatıcı kısayollar yapılandırılıyor..." -ForegroundColor Yellow
$RegisterScript = Join-Path $ScriptDir "Register-AntigravityTRTask.ps1"
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $RegisterScript

# 6.5. Hızlı açılış mühür damgasını güncelle
try {
    $fso = New-Object -ComObject Scripting.FileSystemObject
    $f = $fso.GetFile($AsarPath)
    $stamp = "$($f.Size)|$($f.DateLastModified)"
    [System.IO.File]::WriteAllText((Join-Path $ScriptDir ".last_patched_stamp"), $stamp, [System.Text.UTF8Encoding]::new($false))
} catch {}

# 7. Canlı Uygulama Sıcak Enjeksiyonu (Antigravity Açıksa)
$DevPortFile = "$env:APPDATA\antigravity\DevToolsActivePort"
if (Test-Path $DevPortFile) {
    Write-Host "[*] Açık Antigravity penceresi tespit edildi, canlı sıcak enjeksiyon yapılıyor..." -ForegroundColor Yellow
    $NodeExe = "D:\Android\Tools\Nodejs\node.exe"
    if (-not (Test-Path $NodeExe)) {
        $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
        if ($nodeCmd) { $NodeExe = $nodeCmd.Source }
    }
    if ($NodeExe -and (Test-Path $NodeExe)) {
        $HotScript = Join-Path $ScriptDir "hot_apply.js"
        & $NodeExe $HotScript
        Write-Host "[+] Canlı pencere başarıyla Türkçe'ye dönüştürüldü (Yeniden başlatma gerekmedi)!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "  Antigravity Türkçe Yama Başarıyla Kuruldu.              " -ForegroundColor White
Write-Host "  Arka planda sürekli çalışan hiçbir görev olmadan,       " -ForegroundColor Cyan
Write-Host "  açılışta ve güncellemede kendini otomatik koruyacaktır.  " -ForegroundColor Cyan
Write-Host "  Kaldırmak için Uninstall.cmd dosyasını çalıştırın.      " -ForegroundColor DarkGray
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
