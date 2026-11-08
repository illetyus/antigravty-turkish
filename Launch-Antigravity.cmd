@echo off
rem Antigravity Turkce Baslatici
powershell.exe -WindowStyle Hidden -NoProfile -ExecutionPolicy Bypass -File "D:\Android\Tools\Antigravity-TR\Ensure-AntigravityTR.ps1"
start "" "%LOCALAPPDATA%\Programs\antigravity\Antigravity.exe" %*
