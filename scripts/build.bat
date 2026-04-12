@echo off
REM Build script for creating Windows EXE from Logikus
REM Usage: build.bat

setlocal enabledelayedexpansion

REM Resolve script and repository root directories
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"

echo ========================================
echo Logikus Windows EXE Builder
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo Error: pip is not available
    exit /b 1
)

echo [1/4] Installing/Updating dependencies...
pip install --upgrade pip setuptools wheel >nul
pip install pygame>=2.0.0 >nul
pip install pyinstaller >nul

if errorlevel 1 (
    echo Error: Failed to install dependencies
    exit /b 1
)
echo [1/4] ✓ Dependencies installed

echo [2/4] Cleaning previous builds...
if exist "%REPO_ROOT%\dist" rmdir /s /q "%REPO_ROOT%\dist" >nul 2>&1
if exist "%REPO_ROOT%\build" rmdir /s /q "%REPO_ROOT%\build" >nul 2>&1
echo [2/4] ✓ Cleaned previous builds

echo [3/4] Building EXE with PyInstaller...
python -m PyInstaller "%SCRIPT_DIR%logikus.spec" --distpath "%REPO_ROOT%\dist" --workpath "%REPO_ROOT%\build"

if errorlevel 1 (
    echo Error: PyInstaller build failed
    exit /b 1
)
echo [3/4] ✓ Build completed

echo [4/4] Verifying EXE...
if exist "%REPO_ROOT%\dist\Logikus.exe" (
    for %%A in ("%REPO_ROOT%\dist\Logikus.exe") do set size=%%~zA
    echo [4/4] ✓ EXE successfully created: %REPO_ROOT%\dist\Logikus.exe (!size! bytes)
    echo.
    echo ========================================
    echo Build successful!
    echo ========================================
    exit /b 0
) else (
    echo Error: EXE file not created
    exit /b 1
)

