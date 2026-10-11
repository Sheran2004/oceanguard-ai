# Recreate the venv using Python 3.12 (NOT 3.14, which breaks numpy/opencv).
$ErrorActionPreference = 'Stop'
$ProjectRoot = $PSScriptRoot

$py312 = $null
foreach ($p in @(
    "C:\Users\asus\AppData\Local\Programs\Python\Python312\python.exe",
    "C:\Python312\python.exe",
    "C:\Program Files\Python312\python.exe"
)) { if (Test-Path $p) { $py312 = $p; break } }
if (-not $py312) {
    try {
        $ver = & py -3.12 -c "import sys; print(sys.executable)" 2>&1
        if ($ver -and (Test-Path $ver)) { $py312 = $ver }
    } catch {}
}
if (-not $py312) {
    Write-Host "[ERROR] Python 3.12 not found.  Install from python.org and re-run." -ForegroundColor Red
    Read-Host "Press Enter to exit"; exit 1
}
Write-Host "[OK] Using Python 3.12 at $py312" -ForegroundColor Green

if (Test-Path (Join-Path $ProjectRoot ".venv")) {
    Write-Host "Removing old .venv..." -ForegroundColor Yellow
    cmd /c "rmdir /S /Q `"$ProjectRoot/.venv`""
    Start-Sleep -Seconds 2
}
Write-Host "Creating fresh .venv with Python 3.12..." -ForegroundColor Yellow
& $py312 -m venv (Join-Path $ProjectRoot ".venv")
if ($LASTEXITCODE -ne 0) { Read-Host "venv failed - Press Enter to exit"; exit 1 }

$VenvPy = Join-Path $ProjectRoot ".venv/Scripts/python.exe"
& $VenvPy -m pip install --upgrade pip wheel setuptools 2>&1 | Select-Object -Last 3
Write-Host ""
Write-Host "Installing backend requirements (3-5 minutes)..." -ForegroundColor Yellow
& $VenvPy -m pip install -r (Join-Path $ProjectRoot "backend/requirements.txt")
if ($LASTEXITCODE -ne 0) { Read-Host "pip failed - Press Enter to exit"; exit 1 }
& $VenvPy -c "import numpy, cv2; print(f'numpy={numpy.__version__} opencv={cv2.__version__}')"
Write-Host ""
Write-Host "=== venv ready ===" -ForegroundColor Cyan
Write-Host "Next:  powershell -ExecutionPolicy Bypass -File ./start.ps1" -ForegroundColor Green
Read-Host "Press Enter to exit"
