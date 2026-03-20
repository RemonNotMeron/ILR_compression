@echo off
setlocal EnableDelayedExpansion
title PDF Compressor - Setup and Launch
color 0A

echo.
echo  =========================================================
echo    PDF Compressor  ^|  UKVCAS ILR Edition
echo  =========================================================
echo.

:: -- Check if Python is already installed -------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo  [INFO] Python not found. Downloading and installing Python 3.12...
    echo         This will take a minute. Please wait.
    echo.

    :: Download Python installer using PowerShell (available on all modern Windows)
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'"

    if not exist "%TEMP%\python_installer.exe" (
        echo  [ERROR] Download failed. Check your internet connection and try again.
        pause
        exit /b 1
    )

    echo  [INFO] Installing Python silently...

    :: /quiet        = no UI
    :: InstallAllUsers=0 = current user only (no admin needed)
    :: PrependPath=1 = add to PATH automatically
    "%TEMP%\python_installer.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0

    if errorlevel 1 (
        echo  [ERROR] Python installation failed.
        echo          Try installing manually from https://python.org
        pause
        exit /b 1
    )

    echo  [OK] Python installed.

    :: Refresh PATH so python command works in this session
    for /f "tokens=2*" %%A in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USERPATH=%%B"
    set "PATH=%USERPATH%;%PATH%"

    :: Also check the standard user install location
    for /f "delims=" %%i in ('dir /b /ad "%LOCALAPPDATA%\Programs\Python\Python3*" 2^>nul') do (
        set "PATH=%LOCALAPPDATA%\Programs\Python\%%i;%LOCALAPPDATA%\Programs\Python\%%i\Scripts;%PATH%"
    )

    del "%TEMP%\python_installer.exe" >nul 2>&1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Found %PYVER%

:: -- Create venv if it doesn't exist ------------------------------------------
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

:: -- Activate venv -------------------------------------------------------------
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] Could not activate virtual environment.
    pause
    exit /b 1
)
echo  [OK] Virtual environment activated.

:: -- Install dependencies ------------------------------------------------------
echo.
echo  [SETUP] Installing dependencies (pikepdf, Pillow, tkinterdnd2)...
echo          This may take a minute on first run.
echo.
pip install --quiet --upgrade pikepdf Pillow tkinterdnd2
if errorlevel 1 (
    echo  [ERROR] pip install failed. Check your internet connection.
    pause
    exit /b 1
)
echo  [OK] Dependencies ready.

:: -- Launch GUI ----------------------------------------------------------------
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
