# NOTE: This Dockerfile is deprecated for this AKS deployment.
# 
# For Azure Kubernetes Service (AKS), use the Helm chart deployment instead.
# The Helm chart automatically handles provider installation.
#
# To deploy to AKS:
# 1. See docs/AKS_DEPLOYMENT_GUIDE.md
# 2. Use: helm install airflow apache-airflow/airflow -n airflow -f kubernetes/values.yaml
#
# This Dockerfile is kept for reference only and should not be used.
# All required providers are configured in kubernetes/values.yaml

FROM apache/airflow:3.0.2-python3.11

# Providers are installed via Helm extraPipPackages - no Docker build needed

LABEL maintainer="Srikanth Jogu"
LABEL description="DEPRECATED - Use Helm deployment instead"
LABEL version="3.0.2"
