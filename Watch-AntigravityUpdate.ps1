# Antigravity Turkish Auto-Update Watcher
# Path: D:\Android\Tools\Antigravity-TR\Watch-AntigravityUpdate.ps1

$ErrorActionPreference = "SilentlyContinue"

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

$PythonExe = Get-PythonPath
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PatcherScript = Join-Path $ScriptDir "patch_asar.py"
$ResourcesDir = "$env:LOCALAPPDATA\Programs\antigravity\resources"
$AsarPath = Join-Path $ResourcesDir "app.asar"

function Invoke-PatchIfUnpatched {
    if (-not (Test-Path $AsarPath)) { return }
    & $PythonExe $PatcherScript --asar $AsarPath --check *>$null
    if ($LASTEXITCODE -ne 0) {
        Start-Sleep -Seconds 2
        & $PythonExe $PatcherScript --asar $AsarPath *>$null
    }
}

# 1. Initial check on launch
Invoke-PatchIfUnpatched

# 2. Watch resources directory for updates
$Watcher = New-Object System.IO.FileSystemWatcher
$Watcher.Path = $ResourcesDir
$Watcher.Filter = "app.asar*"
$Watcher.IncludeSubdirectories = $false
$Watcher.EnableRaisingEvents = $true

$Params = @{
    Python = $PythonExe
    Script = $PatcherScript
    Asar   = $AsarPath
}

$Action = {
    Start-Sleep -Seconds 3
    $py = $Event.MessageData.Python
    $sc = $Event.MessageData.Script
    $as = $Event.MessageData.Asar
    if (-not (Test-Path $as)) { return }
    & $py $sc --asar $as --check *>$null
    if ($LASTEXITCODE -ne 0) {
        & $py $sc --asar $as *>$null
    }
}

Register-ObjectEvent $Watcher "Changed" -MessageData $Params -Action $Action | Out-Null
Register-ObjectEvent $Watcher "Created" -MessageData $Params -Action $Action | Out-Null
Register-ObjectEvent $Watcher "Renamed" -MessageData $Params -Action $Action | Out-Null

while ($true) {
    Start-Sleep -Seconds 60
}
