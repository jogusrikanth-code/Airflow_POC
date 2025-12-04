# Install Databricks Provider in Airflow Pods
# This script installs apache-airflow-providers-databricks in running Airflow pods
# Note: This is a temporary installation that will be lost when pods restart

Write-Host "Installing Databricks Provider in Airflow pods..." -ForegroundColor Cyan

# Get current pod names
$apiServerPod = kubectl get pods -n airflow -l component=api-server -o jsonpath='{.items[0].metadata.name}'
$schedulerPod = kubectl get pods -n airflow -l component=scheduler -o jsonpath='{.items[0].metadata.name}'
$dagProcessorPod = kubectl get pods -n airflow -l component=dag-processor -o jsonpath='{.items[0].metadata.name}'

Write-Host "`nInstalling in API Server pod: $apiServerPod" -ForegroundColor Yellow
kubectl exec -n airflow $apiServerPod -- pip install apache-airflow-providers-databricks==7.8.0 --quiet

Write-Host "`nInstalling in Scheduler pod: $schedulerPod" -ForegroundColor Yellow
kubectl exec -n airflow $schedulerPod -- pip install apache-airflow-providers-databricks==7.8.0 --quiet

Write-Host "`nInstalling in DAG Processor pod: $dagProcessorPod" -ForegroundColor Yellow
kubectl exec -n airflow $dagProcessorPod -c dag-processor -- pip install apache-airflow-providers-databricks==7.8.0 --quiet

Write-Host "`n✅ Databricks provider installed successfully!" -ForegroundColor Green
Write-Host "`nRefresh your Airflow UI to see Databricks in the connection type dropdown." -ForegroundColor Cyan
Write-Host "`nNote: This installation is temporary. For permanent installation, see:" -ForegroundColor Yellow
Write-Host "      docs/DATABRICKS_PROVIDER_INSTALLATION.md" -ForegroundColor Yellow
