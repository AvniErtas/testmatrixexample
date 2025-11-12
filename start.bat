@echo off
title Turbine Test Matrix Optimizer
color 0A

echo.
echo ================================================================
echo.
echo     TURBINE TEST MATRIX OPTIMIZER
echo.
echo ================================================================
echo.
echo Baslatiiliyor...
echo.

REM Flask API'yi baslat
echo [1/3] Flask API baslatiiliyor (port 5000)...
start "Flask API - Port 5000" cmd /k "python flask_api.py"
timeout /t 3 /nobreak >nul

REM Web sunucusunu baslat
echo [2/3] Web sunucusu baslatiiliyor (port 8080)...
start "Web Server - Port 8080" cmd /k "python -m http.server 8080"
timeout /t 2 /nobreak >nul

REM Tarayiciyi ac
echo [3/3] Tarayici aciliyor...
start http://localhost:8080/index.html

echo.
echo ================================================================
echo.
echo   HAZIR! Tarayici acildi.
echo.
echo   Web Arayuz: http://localhost:8080/index.html
echo   Flask API:  http://localhost:5000
echo.
echo   Kapatmak icin acilan tum console pencerelerini kapatin.
echo.
echo ================================================================
echo.
pause
