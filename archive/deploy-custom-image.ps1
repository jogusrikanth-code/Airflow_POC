# DEPRECATED: This script is no longer needed for AKS deployment.
#
# For Azure Kubernetes Service, use Helm chart deployment directly.
# Custom Docker images are not needed.
#
# All required providers are configured in kubernetes/values.yaml
# and installed automatically by Helm during deployment.
#
# To deploy to AKS, see:
# - docs/AKS_DEPLOYMENT_GUIDE.md

Write-Host "⚠️ This script is deprecated. Use Helm deployment instead." -ForegroundColor Yellow
Write-Host "See: docs/AKS_DEPLOYMENT_GUIDE.md" -ForegroundColor Cyan
exit 0
