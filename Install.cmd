@echo off
chcp 65001 >nul
title Antigravity Türkçe Yama Kurulumu
echo ========================================================
echo  Google Antigravity 2.0 Türkçe Yama Kurulumu Başlatılıyor...
echo ========================================================
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-AntigravityTR.ps1"
echo.
echo Kurulum penceresini kapatmak için herhangi bir tuşa basın...
pause >nul
