# Grafana Automated Setup Script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Grafana Setup Helper Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Prometheus
Write-Host "[Step 1] Checking Prometheus..." -ForegroundColor Yellow
$prom = kubectl get svc prometheus-server -n default -o jsonpath="{.spec.clusterIP}" 2>$null
if ($prom) {
    Write-Host "OK Prometheus found: $prom" -ForegroundColor Green
} else {
    Write-Host "ERROR Prometheus not found!" -ForegroundColor Red
    exit 1
}

# Check Grafana
Write-Host "[Step 2] Checking Grafana..." -ForegroundColor Yellow
$graf = kubectl get svc grafana -n default -o jsonpath="{.spec.clusterIP}" 2>$null
if ($graf) {
    Write-Host "OK Grafana found: $graf" -ForegroundColor Green
} else {
    Write-Host "ERROR Grafana not found!" -ForegroundColor Red
    exit 1
}

# Start port-forwards
Write-Host "[Step 3] Starting port forwards..." -ForegroundColor Yellow

$promPort = Get-NetTCPConnection -LocalPort 9090 -ErrorAction SilentlyContinue
if (!$promPort) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "kubectl port-forward svc/prometheus-server 9090:80 -n default"
    Start-Sleep -Seconds 2
}

$grafPort = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if (!$grafPort) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "kubectl port-forward svc/grafana 3000:80 -n default"
    Start-Sleep -Seconds 2
}

# Get password
Write-Host "[Step 4] Getting Grafana password..." -ForegroundColor Yellow
$secret = kubectl get secret --namespace default grafana -o jsonpath="{.data.admin-password}" 2>$null
if ($secret) {
    $password = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($secret))
} else {
    $password = "NewPassword123"
}

# Display info
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Grafana URL: http://localhost:3000" -ForegroundColor Yellow
Write-Host "Username: admin" -ForegroundColor Yellow
Write-Host "Password: $password" -ForegroundColor Yellow
Write-Host ""
Write-Host "Prometheus URL: http://localhost:9090" -ForegroundColor Yellow
Write-Host ""
Write-Host "Opening Grafana..." -ForegroundColor Green
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"
