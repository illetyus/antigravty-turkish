# Antigravity Turkish Auto-Enforcer
# Path: D:\Android\Tools\Antigravity-TR\Ensure-AntigravityTR.ps1

[CmdletBinding()]
param (
    [switch]$Force,
    [switch]$Restore,
    [switch]$CheckOnly,
    [string]$CustomPython
)

function Get-PythonPath {
    param([string]$explicit)
    if ($explicit -and (Test-Path $explicit)) { return $explicit }
    if (Test-Path "D:\Android\Tools\Python\Python312\python.exe") { return "D:\Android\Tools\Python\Python312\python.exe" }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) { return $pyCmd.Source }
    return "python"
}

$PythonExe = Get-PythonPath -explicit $CustomPython
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatcherScript = Join-Path $ScriptDir "patch_asar.py"
$AsarPath = "$env:LOCALAPPDATA\Programs\antigravity\resources\app.asar"

if (-not (Test-Path $PythonExe) -and -not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    Write-Error "Python runtime bulunamadı: $PythonExe"
    exit 1
}

if (-not (Test-Path $AsarPath)) {
    Write-Warning "Antigravity app.asar bulunamadı: $AsarPath"
    exit 0
}

if ($CheckOnly) {
    & $PythonExe $PatcherScript --asar $AsarPath --check
    exit $LASTEXITCODE
}

if ($Restore) {
    & $PythonExe $PatcherScript --asar $AsarPath --restore
    exit $LASTEXITCODE
}

# Check if already patched
& $PythonExe $PatcherScript --asar $AsarPath --check *>$null
$isPatched = ($LASTEXITCODE -eq 0)

if ($isPatched -and (-not $Force)) {
    Write-Host "[Antigravity-TR] Antigravity v2 arayüzü zaten Türkçe yamalı." -ForegroundColor Green
    exit 0
}

Write-Host "[Antigravity-TR] Güncelleme veya eksik yama tespit edildi. Türkçe yama uygulanıyor..." -ForegroundColor Yellow
$patchArgs = @($PatcherScript, "--asar", $AsarPath)
if ($Force) {
    $patchArgs += "--force"
}
& $PythonExe @patchArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "[Antigravity-TR] Türkçe yama başarıyla uygulandı!" -ForegroundColor Green
} else {
    Write-Host "[Antigravity-TR] Yama sırasında bir uyarı/hata oluştu (Antigravity çalışıyor olabilir)." -ForegroundColor Yellow
}
exit $LASTEXITCODE
