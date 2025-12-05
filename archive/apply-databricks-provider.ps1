# DEPRECATED: This script is no longer needed for AKS deployment.
#
# For Azure Kubernetes Service, providers are installed automatically via:
# - kubernetes/values.yaml (extraPipPackages)
# - Helm deployment with helm install/upgrade
#
# This script was used for manual patching of deployments and is kept for reference only.
#
# To deploy to AKS, see:
# - docs/AKS_DEPLOYMENT_GUIDE.md
# - All providers configured in: kubernetes/values.yaml

Write-Host "⚠️ This script is deprecated. Use Helm deployment instead." -ForegroundColor Yellow
Write-Host "See: docs/AKS_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
exit 0
Write-Host "`nThe provider will now be installed automatically on every pod restart." -ForegroundColor Cyan
Write-Host "Refresh your Airflow UI to see Databricks in the connection dropdown." -ForegroundColor Cyan
