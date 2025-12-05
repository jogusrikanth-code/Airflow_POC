# Airflow POC - Azure Kubernetes Service Deployment

Apache Airflow 3.0.2 running on **Azure Kubernetes Service (AKS)** with enterprise integrations for Azure, Databricks, PowerBI, and on-premises SQL Server.

## 🚀 Quick Start

Deploy Airflow to your AKS cluster:

```powershell
# 1. Connect to AKS
az aks get-credentials --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_CLUSTER_NAME>

# 2. Add Helm repository
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# 3. Deploy PostgreSQL database
kubectl apply -f kubernetes/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n airflow --timeout=180s

# 4. Install Airflow 3.0.2
helm install airflow apache-airflow/airflow `
  -n airflow `
  -f kubernetes/values.yaml `
  --timeout 15m

# 5. Expose UI (if not using LoadBalancer in values.yaml)
kubectl patch svc airflow-api-server -n airflow -p '{\"spec\":{\"type\":\"LoadBalancer\"}}'

# 6. Get access URL
kubectl get svc airflow-api-server -n airflow
# Access: http://<EXTERNAL-IP>:8080 (admin/admin)
```

## 📚 Documentation

### 🎯 Start Here

- **[QUICKSTART.md](docs/QUICKSTART.md)** - Fast-track 5-minute setup guide
- **[AKS_DEPLOYMENT_GUIDE.md](docs/AKS_DEPLOYMENT_GUIDE.md)** - Complete AKS deployment instructions

### 🔗 Connection Guides

Configure connections to enterprise services:

- **[AZURE_CONNECTIONS_SETUP.md](docs/AZURE_CONNECTIONS_SETUP.md)** - Azure Blob Storage, Data Lake, etc.
- **[DATABRICKS_CONNECTION_SETUP.md](docs/DATABRICKS_CONNECTION_SETUP.md)** - Databricks jobs, notebooks, SQL
- **[POWERBI_CONNECTION_SETUP.md](docs/POWERBI_CONNECTION_SETUP.md)** - PowerBI dataset refresh, reports
- **[ONPREM_SQLSERVER_SETUP.md](docs/ONPREM_SQLSERVER_SETUP.md)** - On-premises SQL Server access


## 📋 What's Included

### Pre-configured Providers
- ☁️ **Azure** (`apache-airflow-providers-microsoft-azure>=10.5.0`) - Blob Storage, Data Lake
- 🧱 **Databricks** (`apache-airflow-providers-databricks>=6.11.0`) - Jobs, Notebooks, SQL
- 📊 **PowerBI/MSSQL** (`apache-airflow-providers-microsoft-mssql>=3.8.0`) - Dataset refresh
- 🗄️ **On-Premises SQL** (`pyodbc>=5.2.0`, `apache-airflow-providers-odbc>=4.9.0`)
- 🐘 **PostgreSQL** - Metadata database
- 🔴 **Redis** - Celery task queue

### Components
- **Scheduler** - Orchestrates DAG execution
- **Worker** - Executes tasks (CeleryExecutor)
- **API Server** - REST API + Web UI (Airflow 3.0+)
- **Triggerer** - Handles deferrable operators
- **DAG Processor** - Parses DAG files

## 📁 Project Structure

```
Airflow_POC/
├── dags/                          # DAG files
│   ├── simple_etl_pipeline.py
│   ├── azure/                     # Azure Blob operations
│   ├── databricks/                # Databricks jobs/notebooks
│   ├── powerbi/                   # PowerBI refresh pipelines
│   └── onprem/                    # SQL Server ETL
├── kubernetes/                    # Deployment configs
│   ├── values.yaml               # Helm chart configuration
│   ├── postgres.yaml             # Database deployment
│   └── secrets.yaml.example      # Secret templates
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── plugins/                      # Custom Airflow plugins
├── src/                          # Reusable Python modules
└── archive/                      # Deprecated/old files
```

## 🔧 Common Operations

### Add New DAGs
Copy DAG files to all pods (Azure File PVC has sync issues):
```powershell
$pods = kubectl get pods -n airflow -l component=dag-processor -o name
foreach ($pod in $pods) {
    kubectl cp dags/your_new_dag.py "airflow/${pod}:/opt/airflow/dags/" -c dag-processor
}
```

Or use ConfigMap:
```powershell
kubectl create configmap airflow-dags --from-file=dags/ -n airflow --dry-run=client -o yaml | kubectl apply -f -
```

### Scale Workers
```powershell
helm upgrade airflow apache-airflow/airflow -n airflow `
  -f kubernetes/values.yaml `
  --set workers.replicas=3
```

### View Logs
```powershell
kubectl logs -n airflow <pod-name> -c <container-name> --tail=50
```

### Access Database
```powershell
kubectl exec -it -n airflow postgres-<pod-id> -- psql -U airflow -d airflow
```
```

### View Logs

```powershell
# Scheduler logs
kubectl logs -n airflow deployment/airflow-scheduler -f

# Worker logs
kubectl logs -n airflow pod/<worker-pod-name> -f
```

### Verify Providers

```powershell
# List installed providers
kubectl exec -n airflow deployment/airflow-scheduler -- airflow providers list

# Check specific provider
kubectl exec -n airflow deployment/airflow-api-server -- pip list | Select-String "databricks"
```

### Test Connections

```powershell
kubectl exec -it -n airflow deployment/airflow-scheduler -- /bin/bash

python3 << 'EOF'
from airflow.hooks.base import BaseHook

## 🐛 Troubleshooting

### Check Pod Status
```powershell
kubectl get pods -n airflow
kubectl describe pod <pod-name> -n airflow
kubectl logs <pod-name> -n airflow -c <container> --tail=50
```

### DAGs Not Showing
```powershell
# Check DAG processor logs
kubectl logs -n airflow -l component=dag-processor -c dag-processor --tail=100

# Verify DAG files exist
kubectl exec -n airflow <dag-processor-pod> -c dag-processor -- ls -la /opt/airflow/dags/
```

### Database Issues
```powershell
# Connect to Postgres
kubectl exec -it -n airflow <postgres-pod> -- psql -U airflow -d airflow

# Check migrations
kubectl logs -n airflow -l component=scheduler -c scheduler | grep migration
```

## 📚 Documentation

See `docs/` folder for detailed guides:
- Setup and deployment instructions
- Connection configuration for Azure, Databricks, PowerBI, SQL Server
- Monitoring and alerting setup
- Enterprise integration patterns

## 🔐 Security Notes

- Default credentials: admin/admin (change in production!)
- Store sensitive data in Airflow Connections (encrypted with Fernet key)
- Consider Azure Key Vault integration for production
- Network policies restrict pod-to-pod communication

## 📝 License

This is a proof-of-concept project for evaluation purposes.

---

**Current Deployment:**
- Airflow 3.0.2
- PostgreSQL metadata database
- CeleryExecutor with Redis
- All enterprise providers installed
- Running on AKS
