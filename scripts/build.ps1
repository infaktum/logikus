# Build script for creating Windows EXE from Logikus
# Usage: .\build.ps1

param(
    [switch]$Clean,
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$SpecFile = Join-Path $ScriptDir "logikus.spec"
$DistDir = Join-Path $RepoRoot "dist"
$BuildDir = Join-Path $RepoRoot "build"
$ExePath = Join-Path $DistDir "Logikus.exe"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Logikus Windows EXE Builder (PowerShell)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Found: $pythonVersion"
} catch {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Step 1: Clean previous builds
if ($Clean) {
    Write-Host "[1/4] Cleaning previous builds..." -ForegroundColor Yellow
    Remove-Item -Path $DistDir, $BuildDir -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "[1/4] ✓ Cleaned previous builds" -ForegroundColor Green
} else {
    Write-Host "[1/4] Skipping clean (use -Clean to force clean)" -ForegroundColor Yellow
}

# Step 2: Install dependencies
Write-Host "[2/4] Installing/Updating dependencies..." -ForegroundColor Yellow
try {
    python -m pip install --upgrade pip setuptools wheel | Out-Null
    pip install pygame>=2.0.0 | Out-Null
    pip install pyinstaller | Out-Null
    Write-Host "[2/4] ✓ Dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Step 3: Build EXE
Write-Host "[3/4] Building EXE with PyInstaller..." -ForegroundColor Yellow
try {
    python -m PyInstaller $SpecFile --distpath $DistDir --workpath $BuildDir
    Write-Host "[3/4] ✓ Build completed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] PyInstaller build failed" -ForegroundColor Red
    exit 1
}

# Step 4: Verify EXE
Write-Host "[4/4] Verifying EXE..." -ForegroundColor Yellow
if (Test-Path $ExePath) {
    $fileSize = (Get-Item $ExePath).Length
    $fileSizeMB = [math]::Round($fileSize / 1MB, 2)
    Write-Host "[4/4] ✓ EXE successfully created: $ExePath ($fileSizeMB MB)" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Build successful! ✓" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    exit 0
} else {
    Write-Host "[ERROR] EXE file not created" -ForegroundColor Red
    exit 1
}

