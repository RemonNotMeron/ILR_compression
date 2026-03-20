@echo off
setlocal EnableDelayedExpansion
title PDF Compressor - Setup and Launch
color 0A

echo.
echo  =========================================================
echo    PDF Compressor  ^|  UKVCAS ILR Edition
echo  =========================================================
echo.

:: -- Step 1: Find Python -------------------------------------------------------
set PYTHON_EXE=

:: Check if python is already on PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=python
    goto :python_ready
)

:: Check common install locations directly (in case PATH is not updated)
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
) do (
    if exist %%D (
        set PYTHON_EXE=%%D
        goto :python_ready
    )
)

:: Python not found
echo  [ERROR] Python not found on this computer.
echo.
echo          Please install Python 3.10 or newer from:
echo          https://www.python.org/downloads/
echo.
echo          Make sure to tick "Add Python to PATH" during install,
echo          then run this file again.
echo.
pause
exit /b 1

:python_ready
for /f "tokens=*" %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do set PYVER=%%v
echo  [OK] Found %PYVER%

:: -- Step 2: Create venv -------------------------------------------------------
if not exist ".venv\" (
    echo.
    echo  [SETUP] Creating virtual environment...
    "%PYTHON_EXE%" -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created.
) else (
    echo  [OK] Virtual environment already exists.
)

:: -- Step 3: Activate venv -----------------------------------------------------
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] Could not activate virtual environment.
    pause
    exit /b 1
)
echo  [OK] Virtual environment activated.

:: -- Step 4: Install dependencies ----------------------------------------------
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

:: -- Step 5: Launch GUI --------------------------------------------------------
echo.
echo  [LAUNCH] Starting PDF Compressor...
echo.
python gui.py

if errorlevel 1 (
    echo.
    echo  [ERROR] The app exited with an error.
    pause
)

endlocal
