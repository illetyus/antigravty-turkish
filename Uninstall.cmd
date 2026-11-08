@echo off
chcp 65001 >nul
title Antigravity Türkçe Yama Kaldırma
echo ========================================================
echo  Google Antigravity 2.0 Türkçe Yama Kaldırılıyor...
echo ========================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Uninstall-AntigravityTR.ps1"
echo.
echo Pencereyi kapatmak için herhangi bir tuşa basın...
pause >nul
