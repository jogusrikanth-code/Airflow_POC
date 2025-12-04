# Setup Centralized DAG Monitoring in Azure Monitor
# Run this script to create action groups and alert rules

Write-Host "`n=== AIRFLOW DAG MONITORING SETUP ===" -ForegroundColor Cyan
Write-Host "Setting up centralized monitoring in Azure Monitor...`n" -ForegroundColor Yellow

# Variables
$resourceGroup = "bi_lakehouse_dev_rg"
$workspace = "airflow-logs-workspace"
$subscriptionId = "12f4f875-7d27-4234-889e-249988508376"
$workspaceResourceId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.OperationalInsights/workspaces/$workspace"

# Step 1: Get your email address
$email = Read-Host "Enter your email address for alerts"

Write-Host "`n[1/4] Creating action group for notifications..." -ForegroundColor Green

# Create action group
az monitor action-group create `
  --resource-group $resourceGroup `
  --name airflow-dag-alerts `
  --short-name dagalerts `
  --email-receiver name="Team" email=$email

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Action group created successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create action group" -ForegroundColor Red
    exit 1
}

$actionGroupId = "/subscriptions/$subscriptionId/resourceGroups/$resourceGroup/providers/Microsoft.Insights/actionGroups/airflow-dag-alerts"

Write-Host "`n[2/4] Creating alert: DAG Failures..." -ForegroundColor Green

# Alert 1: DAG Failure Alert
$query1 = @"
ContainerLog
| where Namespace == 'airflow'
| where LogEntry contains 'failed' or LogEntry contains 'ERROR'
| where LogEntry contains 'DAG'
| where TimeGenerated > ago(5m)
| summarize FailureCount = count()
"@

az monitor scheduled-query create `
  --resource-group $resourceGroup `
  --name "Airflow-DAG-Failure-Alert" `
  --scopes $workspaceResourceId `
  --condition "count > 0" `
  --condition-query $query1 `
  --description "Alerts when any Airflow DAG fails" `
  --evaluation-frequency 5m `
  --window-size 5m `
  --severity 2 `
  --action-groups $actionGroupId `
  --auto-mitigate true

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ DAG Failure alert created" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create DAG failure alert (may already exist)" -ForegroundColor Yellow
}

Write-Host "`n[3/4] Creating alert: Long-Running DAGs..." -ForegroundColor Green

# Alert 2: Long Running DAG
$query2 = @"
ContainerLog
| where Namespace == 'airflow'
| where LogEntry contains 'Running for' or LogEntry contains 'duration'
| extend Duration = extract(@'(\d+\.?\d*)\s*seconds?', 1, LogEntry)
| where todouble(Duration) > 3600
| summarize Count = count()
"@

az monitor scheduled-query create `
  --resource-group $resourceGroup `
  --name "Airflow-Long-Running-DAG-Alert" `
  --scopes $workspaceResourceId `
  --condition "count > 0" `
  --condition-query $query2 `
  --description "Alerts when DAG runs longer than 1 hour" `
  --evaluation-frequency 15m `
  --window-size 15m `
  --severity 3 `
  --action-groups $actionGroupId `
  --auto-mitigate true

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Long-running DAG alert created" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create long-running alert (may already exist)" -ForegroundColor Yellow
}

Write-Host "`n[4/4] Creating alert: High Failure Rate..." -ForegroundColor Green

# Alert 3: High Failure Rate
$query3 = @"
ContainerLog
| where Namespace == 'airflow'
| where TimeGenerated > ago(1h)
| extend Status = case(
    LogEntry contains 'success' or LogEntry contains 'completed', 'Success',
    LogEntry contains 'failed' or LogEntry contains 'error', 'Failed',
    'Other'
)
| where Status in ('Success', 'Failed')
| summarize SuccessCount = countif(Status == 'Success'), FailureCount = countif(Status == 'Failed')
| extend FailureRate = (todouble(FailureCount) / (SuccessCount + FailureCount)) * 100
| where FailureRate > 20
| project FailureRate
"@

az monitor scheduled-query create `
  --resource-group $resourceGroup `
  --name "Airflow-High-Failure-Rate-Alert" `
  --scopes $workspaceResourceId `
  --condition "count > 0" `
  --condition-query $query3 `
  --description "Alerts when DAG failure rate exceeds 20%" `
  --evaluation-frequency 30m `
  --window-size 1h `
  --severity 2 `
  --action-groups $actionGroupId `
  --auto-mitigate true

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ High failure rate alert created" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to create failure rate alert (may already exist)" -ForegroundColor Yellow
}

Write-Host "`n=== SETUP COMPLETE! ===" -ForegroundColor Cyan
Write-Host "`nWhat was created:" -ForegroundColor Yellow
Write-Host "  ✓ Action Group: airflow-dag-alerts (sends to $email)"
Write-Host "  ✓ Alert: DAG Failures (checks every 5 min)"
Write-Host "  ✓ Alert: Long-Running DAGs (checks every 15 min)"
Write-Host "  ✓ Alert: High Failure Rate (checks every 30 min)`n"

Write-Host "Next steps:" -ForegroundColor Magenta
Write-Host "  1. Import the workbook to Azure Portal"
Write-Host "  2. Go to: https://portal.azure.com"
Write-Host "  3. Navigate to: Monitor > Workbooks > + New"
Write-Host "  4. Click: Advanced Editor"
Write-Host "  5. Paste contents of: monitoring/azure-dag-monitoring-workbook.json"
Write-Host "  6. Click: Apply, then Save`n"

Write-Host "Test your alerts:" -ForegroundColor Magenta
Write-Host "  az monitor action-group test-notifications create ``"
Write-Host "    --action-group-name airflow-dag-alerts ``"
Write-Host "    --resource-group $resourceGroup ``"
Write-Host "    --notification-type Email`n"

Write-Host "View your alerts:" -ForegroundColor Cyan
Write-Host "  https://portal.azure.com/#view/Microsoft_Azure_Monitoring/AzureMonitoringBrowseBlade/~/alertsV2`n"
