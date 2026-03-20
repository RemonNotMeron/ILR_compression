@echo off
setlocal EnableDelayedExpansion
title PDF Compressor - Setup and Launch
color 0A

echo.
echo  =========================================================
echo    PDF Compressor  ^|  UKVCAS ILR Edition
echo  =========================================================
echo.

:: -- Step 1: Find or install Python -------------------------------------------
set PYTHON_EXE=

:: Check if python is already on PATH
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_EXE=python
    goto :python_ready
)

:: Check common install locations directly (in case PATH just isn't updated)
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

:: Python not found anywhere - download and install it
echo  [INFO] Python not found. Downloading Python 3.12...
echo         This will take a minute. Please wait.
echo.

set INSTALLER=%TEMP%\python_setup.exe
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe' -OutFile '%INSTALLER%'"

if not exist "%INSTALLER%" (
    echo  [ERROR] Download failed. Please check your internet connection.
    pause
    exit /b 1
)

echo  [INFO] Installing Python 3.12 (this may take a minute)...
"%INSTALLER%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=0
set INST_ERR=%ERRORLEVEL%
del "%INSTALLER%" >nul 2>&1

if %INST_ERR% NEQ 0 (
    echo  [ERROR] Python installation failed (code: %INST_ERR%)
    echo          Please install Python manually from https://python.org
    pause
    exit /b 1
)

echo  [OK] Python 3.12 installed.

:: Find the freshly installed python.exe
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) do (
    if exist %%D (
        set PYTHON_EXE=%%D
        goto :python_ready
    )
)

echo  [ERROR] Python was installed but could not be located.
echo          Please restart your computer and run this file again.
pause
exit /b 1

:python_ready
for /f "tokens=*" %%v in ('"%PYTHON_EXE%" --version 2^>^&1') do set PYVER=%%v
echo  [OK] Using %PYVER% at %PYTHON_EXE%

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
