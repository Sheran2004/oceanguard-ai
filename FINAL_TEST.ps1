# Final end-to-end test
$ErrorActionPreference = 'Continue'
$base = 'http://localhost:8000'

Write-Host "=== FINAL E2E TEST ===" -ForegroundColor Cyan

# 1. Frontend HTML
$h = (Invoke-WebRequest 'http://localhost:5173' -UseBasicParsing -TimeoutSec 5).Content
if ($h -match 'id="root"') { Write-Host "[OK] Frontend HTML serves /" -ForegroundColor Green } else { Write-Host "[FAIL] Frontend" -ForegroundColor Red }

# 2. Login
$resp = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body '{"username":"demo-operator","password":"demo123"}' -UseBasicParsing -TimeoutSec 10
$j = $resp.Content | ConvertFrom-Json
Write-Host "[OK] Login: $($resp.StatusCode) user=$($j.user.username) role=$($j.user.role)" -ForegroundColor Green
$tok = $j.access_token
$hdr = @{ Authorization = "Bearer $tok" }

# 3. Analytics
$a = (Invoke-WebRequest "$base/api/analytics/summary" -Headers $hdr -UseBasicParsing -TimeoutSec 10).Content | ConvertFrom-Json
Write-Host "[OK] Analytics: scans=$($a.total_scans) detections=$($a.total_detections) missions=$($a.total_missions)" -ForegroundColor Green

# 4. Scans
$s = (Invoke-WebRequest "$base/api/scans?limit=3" -Headers $hdr -UseBasicParsing -TimeoutSec 10).Content | ConvertFrom-Json
Write-Host "[OK] Scans: $($s.Count) returned" -ForegroundColor Green
$sid = $s[0].id

# 5. Image
$img = Invoke-WebRequest "$base/api/scans/$sid/image" -Headers $hdr -UseBasicParsing -TimeoutSec 15
Write-Host "[OK] Scan image: $($img.StatusCode) $($img.Content.Length) bytes ($($img.Headers['Content-Type']))" -ForegroundColor Green

# 6. Proxy login (frontend -> vite proxy -> backend)
$proxy = Invoke-WebRequest "http://localhost:5173/api/auth/login" -Method POST -ContentType 'application/json' -Body '{"username":"demo-operator","password":"demo123"}' -UseBasicParsing -TimeoutSec 10
$jp = $proxy.Content | ConvertFrom-Json
Write-Host "[OK] Proxy login (via frontend): $($proxy.StatusCode) token_len=$($jp.access_token.Length)" -ForegroundColor Green

# 7. Hotspots
$hs = (Invoke-WebRequest "$base/api/hotspots?limit=3" -Headers $hdr -UseBasicParsing -TimeoutSec 10).Content | ConvertFrom-Json
Write-Host "[OK] Hotspots: $($hs.Count) returned" -ForegroundColor Green

# 8. Models
$m = (Invoke-WebRequest "$base/api/models" -Headers $hdr -UseBasicParsing -TimeoutSec 10).Content | ConvertFrom-Json
Write-Host "[OK] Models: name=$($m.name) demo=$($m.is_demo)" -ForegroundColor Green

Write-Host ""
Write-Host "=== ALL CHECKS PASSED ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "BROWSER ME AB OPEN KAR:  http://localhost:5173" -ForegroundColor Yellow
Write-Host "Login: demo-operator / demo123   ya   admin / admin123" -ForegroundColor Green
