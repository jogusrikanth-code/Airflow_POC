# Get Azure Storage Account Key for Airflow Connection Setup

Write-Host "Getting Azure Storage Account Key..." -ForegroundColor Cyan
Write-Host ""

$storageAccount = "sgbilakehousestoragedev"
$resourceGroup = "bi_lakehouse_dev_rg"

Write-Host "Storage Account: $storageAccount" -ForegroundColor Yellow
Write-Host "Resource Group: $resourceGroup" -ForegroundColor Yellow
Write-Host ""

try {
    # Get storage account key
    $key = az storage account keys list `
        --resource-group $resourceGroup `
        --account-name $storageAccount `
        --query "[0].value" `
        --output tsv
    
    if ($LASTEXITCODE -eq 0 -and $key) {
        Write-Host "Storage Account Key Retrieved!" -ForegroundColor Green
        Write-Host ""
        Write-Host "================================" -ForegroundColor Cyan
        Write-Host "COPY THIS KEY (keep it secret):" -ForegroundColor Yellow
        Write-Host $key -ForegroundColor White
        Write-Host "================================" -ForegroundColor Cyan
        Write-Host ""
        
        # Save to clipboard if possible
        try {
            $key | Set-Clipboard
            Write-Host "Key copied to clipboard!" -ForegroundColor Green
        } catch {
            Write-Host "Note: Could not copy to clipboard automatically" -ForegroundColor Gray
        }
        
        Write-Host ""
        Write-Host "Next Steps:" -ForegroundColor Cyan
        Write-Host "1. Open Airflow UI: http://51.8.246.115" -ForegroundColor White
        Write-Host "2. Go to Admin -> Connections" -ForegroundColor White
        Write-Host "3. Click '+' to add new connection" -ForegroundColor White
        Write-Host "4. Fill in these details:" -ForegroundColor White
        Write-Host ""
        Write-Host "   Connection Id: azure_blob_default" -ForegroundColor Gray
        Write-Host "   Connection Type: Azure Blob Storage" -ForegroundColor Gray
        Write-Host "   Login: $storageAccount" -ForegroundColor Gray
        Write-Host "   Password: [PASTE THE KEY ABOVE]" -ForegroundColor Gray
        Write-Host ""
        Write-Host "5. Click 'Test' then 'Save'" -ForegroundColor White
        Write-Host "6. Trigger DAG: azure_blob_copy_seasonal_buy" -ForegroundColor White
        Write-Host ""
        
    } else {
        Write-Host "Failed to retrieve storage key" -ForegroundColor Red
        Write-Host "Try running this command manually:" -ForegroundColor Yellow
        Write-Host "az storage account keys list --resource-group $resourceGroup --account-name $storageAccount --query `"[0].value`" -o tsv" -ForegroundColor Gray
    }
    
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you are logged into Azure CLI:" -ForegroundColor Yellow
    Write-Host "  az login" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Documentation: docs/AZURE_BLOB_COPY_SETUP.md" -ForegroundColor Cyan
