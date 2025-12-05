# Test if Databricks appears in UI connection types
$uiUrl = "http://51.8.246.115"

Write-Host "Testing Airflow UI connection types..." -ForegroundColor Cyan
Write-Host "URL: $uiUrl/ui/connections/hook_meta" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "$uiUrl/ui/connections/hook_meta" -UseBasicParsing -ErrorAction Stop
    $json = $response.Content | ConvertFrom-Json
    
    Write-Host "Total connection types: $($json.Count)" -ForegroundColor Yellow
    
    $databricks = $json | Where-Object { $_.connection_type -eq 'databricks' }
    
    if ($databricks) {
        Write-Host "`n✓ DATABRICKS FOUND!" -ForegroundColor Green
        Write-Host "Details:" -ForegroundColor Green
        $databricks | ConvertTo-Json -Depth 3 | Write-Host
    } else {
        Write-Host "`n✗ Databricks NOT found in UI response" -ForegroundColor Red
        Write-Host "`nAvailable connection types:" -ForegroundColor Yellow
        $json | Select-Object -First 10 -ExpandProperty connection_type | ForEach-Object { Write-Host "  - $_" }
        Write-Host "  ... and $($json.Count - 10) more"
    }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n---"
Write-Host "If Databricks is not showing in the browser:"
Write-Host "1. Press Ctrl+Shift+Delete in browser"
Write-Host "2. Clear 'Cached images and files'"
Write-Host "3. Press Ctrl+Shift+R to hard refresh"
Write-Host ""
