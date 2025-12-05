# Airflow on Azure Kubernetes Service (AKS) - Helm Deployment

This directory contains the Helm chart configuration for deploying Apache Airflow 3.0.2 on AKS.

## Files

- **`values.yaml`** - Helm chart values for Airflow deployment on AKS
  - Configures PostgreSQL connection (external service)
  - Sets up CeleryExecutor with Redis broker
  - Configures all required Airflow providers (Azure, Databricks, MSSQL, ODBC)
  - Enables DAG persistence via Azure File CSI driver
  - Configures logging with emptyDir for pod logs

## Quick Start

### Prerequisites
- AKS cluster running and configured with `kubectl`
- Helm 3.x installed
- PostgreSQL external service deployed in the airflow namespace

### Deploy

```powershell
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# Deploy with Helm
helm install airflow apache-airflow/airflow `
  -n airflow --create-namespace `
  -f kubernetes/values.yaml `
  --set "config.core.fernet_key=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")"
```

### Verify Deployment

```powershell
# Check pod status
kubectl get pods -n airflow

# Check services
kubectl get svc -n airflow

# Port-forward to access UI
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
# Access at http://localhost:8080
```

## Architecture

```
AKS Cluster
├── airflow namespace
│   ├── Webserver (Deployment) - UI access
│   ├── Scheduler (Deployment) - DAG orchestration
│   ├── Worker (Deployment) - Task execution
│   ├── Triggerer (Deployment) - Async trigger handling
│   ├── DAG Processor (Deployment) - DAG parsing
│   ├── Redis (Deployment) - Celery broker
│   ├── Statsd (Deployment) - Metrics export
│   └── PostgreSQL - External service
│
├── Volumes
│   ├── DAGs (Azure File CSI) - /opt/airflow/dags
│   └── Logs (emptyDir) - /opt/airflow/logs
```

## Configuration Reference

See `values.yaml` for detailed configuration including:
- Provider package installation (Azure, Databricks, MSSQL, ODBC)
- Database connection settings
- Executor configuration (CeleryExecutor)
- Pod resource limits
- PersistentVolume claims for DAGs
- Environment variables and secrets management

## Troubleshooting

Check pod logs:
```powershell
kubectl logs -n airflow deployment/airflow-webserver
kubectl logs -n airflow deployment/airflow-scheduler
kubectl logs -n airflow deployment/airflow-worker -f
```

Check events:
```powershell
kubectl describe pod -n airflow <pod-name>
kubectl get events -n airflow
```

## Upgrades

To upgrade Airflow version or configuration:

```powershell
helm upgrade airflow apache-airflow/airflow `
  -n airflow `
  -f kubernetes/values.yaml
```

## Notes

- Helm chart version: 1.18.0
- Airflow version: 3.0.2
- Python: 3.11
- All 4 POC DAGs are automatically synced to pods via Azure File CSI
