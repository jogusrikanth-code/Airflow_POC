# Permanent Databricks Provider Installation
# Build and deploy custom Airflow image with Databricks provider

Write-Host "Building custom Airflow image with Databricks provider..." -ForegroundColor Cyan

# Step 1: Build the custom image
Write-Host "`n1. Building Docker image..." -ForegroundColor Yellow
docker build -t your-registry/airflow-databricks:3.0.2 -f Dockerfile .

# Step 2: Push to registry
Write-Host "`n2. Pushing to container registry..." -ForegroundColor Yellow
Write-Host "   Please tag and push to your registry:" -ForegroundColor Gray
Write-Host "   docker tag your-registry/airflow-databricks:3.0.2 <your-actual-registry>/airflow-databricks:3.0.2" -ForegroundColor Gray
Write-Host "   docker push <your-actual-registry>/airflow-databricks:3.0.2" -ForegroundColor Gray

# Step 3: Update deployment to use new image
Write-Host "`n3. Update deployments to use new image..." -ForegroundColor Yellow
kubectl set image deployment/airflow-api-server -n airflow api-server=your-registry/airflow-databricks:3.0.2
kubectl set image deployment/airflow-scheduler -n airflow scheduler=your-registry/airflow-databricks:3.0.2
kubectl set image deployment/airflow-dag-processor -n airflow dag-processor=your-registry/airflow-databricks:3.0.2

Write-Host "`n✅ Deployment updated!" -ForegroundColor Green
Write-Host "`nWaiting for rollout..." -ForegroundColor Cyan
kubectl rollout status deployment/airflow-api-server -n airflow
kubectl rollout status deployment/airflow-scheduler -n airflow
kubectl rollout status deployment/airflow-dag-processor -n airflow

Write-Host "`n✅ Databricks provider permanently installed!" -ForegroundColor Green
