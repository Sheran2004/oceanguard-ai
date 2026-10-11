# OceanGuard AI - Foolproof startup (PowerShell)
# Run this from the project root.  Resolves paths relative to its own location,
# so it works whether you extracted the zip as v4, v5, or any custom folder.
#
#   1. Stop any old backend/frontend processes
#   2. Ensure the database is initialised and demo data is seeded
#   3. Start the FastAPI backend on port 8000 in a new window
#   4. Start the Vite frontend on port 5173 in a new window
#   5. Verify both are responding
#
# After it finishes, open http://localhost:5173 and log in with
#   demo-operator / demo123    (operator)
#   admin / admin123           (admin)

# Use Continue (not Stop) so harmless stderr noise (e.g. passlib's
# "trapped error reading bcrypt version" warning) does not abort the script.
$ErrorActionPreference = 'Continue'

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition }
$VenvPython  = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FrontendDir = Join-Path $ProjectRoot "frontend"

Write-Host ""
Write-Host "=== OceanGuard AI Startup ===" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"
Write-Host ""

# Sanity checks
if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Virtual environment not found at $VenvPython" -ForegroundColor Red
    Write-Host "        Run FIX_VENV.ps1 first (uses Python 3.12)." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    Write-Host "[ERROR] frontend\package.json missing.  Run this from the project root." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Kill old processes
Write-Host "[1/5] Killing any old backend/frontend processes..." -ForegroundColor Yellow
try {
    Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {} }
    Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { try { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } catch {} }
} catch {}
Start-Sleep -Seconds 2
Write-Host "  Done." -ForegroundColor Green
Write-Host ""

# Initialise database and seed
Write-Host "[2/5] Initialising database and seeding demo data..." -ForegroundColor Yellow
Set-Location $ProjectRoot

# Create .env from .env.example if missing
if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    if (Test-Path (Join-Path $ProjectRoot ".env.example")) {
        Copy-Item (Join-Path $ProjectRoot ".env.example") (Join-Path $ProjectRoot ".env")
        Write-Host "  Created .env from .env.example" -ForegroundColor Green
    }
}

# Run the helper script.  We swallow stderr (2>$null) to hide the harmless
# passlib "trapped error reading bcrypt version" warning that bcrypt 4.x emits
# but which does NOT affect functionality.  We also use Continue error
# preference to make sure non-terminating errors don't abort us.
$initResult = & $VenvPython (Join-Path $ProjectRoot "scripts/oceanguard_init.py") 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] init_db helper exited with code $LASTEXITCODE" -ForegroundColor Red
    Write-Host "  Output: $initResult" -ForegroundColor Red
}
foreach ($line in $initResult) { Write-Host "  $line" }

$userCount = ($initResult | Select-String -Pattern "^USERS=(\d+)" | ForEach-Object { $_.Matches[0].Groups[1].Value }) | Select-Object -First 1
$scanCount = ($initResult | Select-String -Pattern "^SCANS=(\d+)" | ForEach-Object { $_.Matches[0].Groups[1].Value }) | Select-Object -First 1

if ([int]$userCount -lt 1) {
    Write-Host "  [WARN] No users in DB - seeding may have failed." -ForegroundColor Red
}
if ([int]$scanCount -lt 1) {
    Write-Host "  No scans in DB - generating demo data (8 scans, 2 missions)..." -ForegroundColor Yellow
    # Suppress stderr here too for the same reason.
    $seedOutput = & $VenvPython (Join-Path $ProjectRoot "scripts/generate_demo_data.py") --clear --scans 8 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  [WARN] Demo data seeding failed - login still works but pages will be empty." -ForegroundColor Red
    } else {
        Write-Host "  Demo data generated successfully." -ForegroundColor Green
    }
} else {
    Write-Host "  Database already has $scanCount scans - skipping seed." -ForegroundColor Green
}
Write-Host ""

# Start backend
Write-Host "[3/5] Starting backend on port 8000..." -ForegroundColor Yellow
$backendCmd = "cd `"$ProjectRoot`" ; `"$VenvPython`" -m uvicorn app.main:app --app-dir `"$ProjectRoot/backend`" --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal
Start-Sleep -Seconds 6
Write-Host "  Done." -ForegroundColor Green
Write-Host ""

# Start frontend
Write-Host "[4/5] Starting frontend on port 5173..." -ForegroundColor Yellow
# Install node_modules if missing (first run only)
if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "  First run: installing frontend dependencies (npm install, 2-3 minutes)..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    try { npm install 2>&1 | Select-Object -Last 5 } catch { Write-Host "  [WARN] npm install failed" -ForegroundColor Red }
    Pop-Location
}
$frontendCmd = "cd `"$FrontendDir`" ; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd -WindowStyle Normal
Start-Sleep -Seconds 15
Write-Host "  Done." -ForegroundColor Green
Write-Host ""

# Verify
Write-Host "[5/5] Verifying..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
$backendOk = $false
try {
    $h = Invoke-WebRequest "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  Backend  : $($h.StatusCode) OK" -ForegroundColor Green
    $backendOk = $true
} catch {
    Write-Host "  Backend  : NOT responding" -ForegroundColor Red
}
try {
    Invoke-WebRequest "http://localhost:5173" -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host "  Frontend : OK" -ForegroundColor Green
} catch {
    Write-Host "  Frontend : NOT responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Ready ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Open in browser:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Login credentials:" -ForegroundColor White
Write-Host "  Operator: " -NoNewline -ForegroundColor White
Write-Host "demo-operator / demo123" -ForegroundColor Green
Write-Host "  Admin   : " -NoNewline -ForegroundColor White
Write-Host "admin / admin123" -ForegroundColor Green
Write-Host ""
Write-Host "Two PowerShell windows opened (backend + frontend).  KEEP THEM OPEN." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to close this window"
