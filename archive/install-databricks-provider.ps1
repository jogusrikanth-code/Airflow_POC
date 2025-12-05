# DEPRECATED: This script is no longer needed for AKS deployment.
#
# For Azure Kubernetes Service, providers are installed automatically via:
# - kubernetes/values.yaml (extraPipPackages)
# - Helm deployment with helm install/upgrade
#
# This script was used for temporary pod installation and is kept for reference only.
#
# To deploy to AKS, see:
# - docs/AKS_DEPLOYMENT_GUIDE.md
# - Databricks setup: docs/DATABRICKS_CONNECTION_SETUP.md

Write-Host "⚠️ This script is deprecated. Use Helm deployment instead." -ForegroundColor Yellow
Write-Host "See: docs/AKS_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
exit 0
