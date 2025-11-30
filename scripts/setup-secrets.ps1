# Quick Secrets Setup Script
# Run this after editing kubernetes/secrets.yaml with your actual credentials

# Apply secrets to Kubernetes
Write-Host "Applying secrets to Kubernetes..." -ForegroundColor Cyan
kubectl apply -f kubernetes/secrets.yaml

# Verify secrets were created
Write-Host "`nVerifying secrets..." -ForegroundColor Cyan
kubectl get secrets -n airflow | Select-String "airflow-connections|airflow-variables|git-credentials|postgres-credentials"

# Optional: Test a connection from the scheduler
Write-Host "`nTesting database connection..." -ForegroundColor Cyan
kubectl exec -n airflow deploy/airflow-scheduler -- airflow connections test onprem_db

Write-Host "`n✓ Secrets setup complete!" -ForegroundColor Green
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Restart Airflow components to pick up new secrets:"
Write-Host "     kubectl rollout restart deployment/airflow-webserver -n airflow"
Write-Host "     kubectl rollout restart deployment/airflow-scheduler -n airflow"
Write-Host "     kubectl rollout restart statefulset/airflow-worker -n airflow"
Write-Host "`n  2. Verify connections in Airflow UI: http://localhost:8080/connection/list/"
Write-Host "`n  3. For production, see docs/SECRETS_MANAGEMENT.md for encrypted secrets options"
