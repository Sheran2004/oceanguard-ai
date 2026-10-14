# OceanGuard AI - Safe Startup
$ErrorActionPreference = "Continue"

$ProjectRoot = $PSScriptRoot
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$FrontendDir = Join-Path $ProjectRoot "frontend"

$BackendPort = 8001
$FrontendPort = 5173

Write-Host "`n=== OceanGuard AI Startup ===" -ForegroundColor Cyan

# Validate project files
if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Virtual environment not found." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path (Join-Path $FrontendDir "package.json"))) {
    Write-Host "[ERROR] frontend\package.json not found." -ForegroundColor Red
    exit 1
}

# Check whether backend is already healthy
Write-Host "`n[1/5] Checking backend..." -ForegroundColor Yellow
$backendReady = $false

try {
    $response = Invoke-RestMethod "http://127.0.0.1:$BackendPort/health" -TimeoutSec 3
    if ($response.status -eq "ok") {
        $backendReady = $true
        Write-Host "Existing backend is healthy; reusing it." -ForegroundColor Green
    }
} catch {}

# Start backend only when needed and port is free
if (-not $backendReady) {
    $connection = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue

    if ($connection) {
        Write-Host "[ERROR] Port $BackendPort is occupied by an unhealthy service." -ForegroundColor Red
        Write-Host "Inspect the process before stopping anything." -ForegroundColor Yellow
        exit 1
    }

    Write-Host "Starting backend..." -ForegroundColor Yellow

    $backendCmd = "Set-Location '$ProjectRoot'; & '$VenvPython' -m uvicorn app.main:app --app-dir '$ProjectRoot\backend' --host 127.0.0.1 --port $BackendPort"

    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 2
        try {
            $response = Invoke-RestMethod "http://127.0.0.1:$BackendPort/health" -TimeoutSec 3
            if ($response.status -eq "ok") {
                $backendReady = $true
                break
            }
        } catch {}
    }

    if (-not $backendReady) {
        Write-Host "[ERROR] Backend did not become healthy. Check its window." -ForegroundColor Red
        exit 1
    }
}

# Check frontend
Write-Host "`n[2/5] Checking frontend..." -ForegroundColor Yellow
$frontendReady = $false

try {
    $null = Invoke-WebRequest "http://127.0.0.1:$FrontendPort" -UseBasicParsing -TimeoutSec 3
    $frontendReady = $true
    Write-Host "Existing frontend is responding; reusing it." -ForegroundColor Green
} catch {}

# Start frontend only when needed
if (-not $frontendReady) {
    $connection = Get-NetTCPConnection -LocalPort $FrontendPort -State Listen -ErrorAction SilentlyContinue

    if ($connection) {
        Write-Host "[ERROR] Port $FrontendPort is occupied by an unresponsive service." -ForegroundColor Red
        Write-Host "Inspect the process before stopping anything." -ForegroundColor Yellow
        exit 1
    }

    if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
        Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
        Push-Location $FrontendDir
        try {
            npm install
            if ($LASTEXITCODE -ne 0) {
                Write-Host "[ERROR] npm install failed." -ForegroundColor Red
                exit 1
            }
        } finally {
            Pop-Location
        }
    }

    Write-Host "Starting frontend..." -ForegroundColor Yellow
    $frontendCmd = "Set-Location '$FrontendDir'; npm run dev -- --host 127.0.0.1 --port $FrontendPort --strictPort"
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

    for ($i = 0; $i -lt 30; $i++) {
        Start-Sleep -Seconds 1
        try {
            $null = Invoke-WebRequest "http://127.0.0.1:$FrontendPort" -UseBasicParsing -TimeoutSec 3
            $frontendReady = $true
            break
        } catch {}
    }
}

if (-not $frontendReady) {
    Write-Host "[ERROR] Frontend did not respond. Check its window." -ForegroundColor Red
    exit 1
}

# Final verification
Write-Host "`n[3/5] Verifying API..." -ForegroundColor Yellow

try {
    $health = Invoke-RestMethod "http://127.0.0.1:$BackendPort/health" -TimeoutSec 5

    Write-Host "Backend : HEALTHY" -ForegroundColor Green
    Write-Host "Model   : $($health.model.name)" -ForegroundColor Green
    Write-Host "Demo mode: $($health.model.demo_mode)" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Backend health check failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n=== OceanGuard AI Ready ===" -ForegroundColor Green
Write-Host "Frontend : http://127.0.0.1:$FrontendPort"
Write-Host "Backend  : http://127.0.0.1:$BackendPort"
Write-Host "API Docs : http://127.0.0.1:$BackendPort/docs"
Write-Host "`nExisting healthy servers were reused; unrelated processes were not stopped."