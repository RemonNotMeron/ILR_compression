@echo off
setlocal EnableDelayedExpansion
title PDF Compressor - Setup and Launch
color 0A

echo.
echo  =========================================================
echo    PDF Compressor  ^|  UKVCAS ILR Edition
echo  =========================================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo          Please install Python 3.10+ from https://python.org
    echo          Make sure to tick "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Found %PYVER%

:: Create venv if it doesn't exist
if not exist ".venv\" (
    echo.
    echo  [SETUP] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
) else (
    echo  [OK] Virtual environment already exists, skipping creation.
)

:: Activate venv
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] Could not activate virtual environment.
    pause
    exit /b 1
)
echo  [OK] Virtual environment activated.

:: Install dependencies
echo.
echo  [SETUP] Installing/updating dependencies (pikepdf, Pillow)...
echo          This may take a minute on first run.
echo.
pip install --quiet --upgrade pikepdf Pillow
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo  [OK] Dependencies ready.

:: Launch GUI
echo.
echo  [LAUNCH] Starting PDF Compressor GUI...
echo.
python gui.py

if errorlevel 1 (
    echo.
    echo  [ERROR] The application exited with an error. See above for details.
    pause
)

endlocal
