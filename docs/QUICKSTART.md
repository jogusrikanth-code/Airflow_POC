# Quick Start: Deploy Airflow to Azure Kubernetes Service

This is a fast-track guide to get Airflow running on AKS with Azure, Databricks, PowerBI, and on-prem SQL Server connections.

## ⚡ 5-Minute Setup

### Step 1: Connect to Your AKS Cluster

```powershell
# Get credentials for your AKS cluster
az aks get-credentials --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_CLUSTER_NAME>

# Verify connection
kubectl get nodes
```

### Step 2: Add Helm Repository

```powershell
helm repo add apache-airflow https://airflow.apache.org
helm repo update
```

### Step 3: Deploy Airflow

```powershell
cd Airflow_POC

# Generate a Fernet key for encryption
$FERNET_KEY = python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Deploy to AKS
helm install airflow apache-airflow/airflow `
  --namespace airflow `
  --create-namespace `
  -f kubernetes/values.yaml `
  --set "config.core.fernet_key=$FERNET_KEY"
```

### Step 4: Access Airflow

```powershell
# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=airflow -n airflow --timeout=300s

# Get the web server URL
$AIRFLOW_IP = kubectl get svc airflow-webserver -n airflow -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Write-Host "Airflow URL: http://$AIRFLOW_IP:8080"

# Default credentials: admin / admin
```

## ✅ Verify Providers Are Installed

```powershell
# Check that all providers are available
kubectl exec -n airflow deployment/airflow-scheduler -- airflow providers list

# You should see:
# apache-airflow-providers-databricks     
# apache-airflow-providers-microsoft-azure
# apache-airflow-providers-microsoft-mssql
# apache-airflow-providers-odbc
```

## 🔧 Configure Connections in Airflow UI

### 1. Azure Blob Storage

1. Go to **Admin** → **Connections** → **Create**
2. **Connection ID:** `azure_blob_storage_default`
3. **Connection Type:** `Azure Blob Storage`
4. **Account Name:** Your Azure storage account name
5. **Account Key:** Your storage account key
6. Click **Test** and **Save**

### 2. Databricks

1. **Connection ID:** `databricks_default`
2. **Connection Type:** `Databricks`
3. **Host:** `https://adb-xxxxxxx.azuredatabricks.net`
4. **Token:** Your personal access token
5. Click **Test** and **Save**

### 3. On-Premises SQL Server

1. **Connection ID:** `mssql_onprem`
2. **Connection Type:** `Microsoft SQL Server`
3. **Host:** Your SQL Server IP or hostname
4. **Database:** Your database name
5. **Login:** SQL Server username
6. **Password:** SQL Server password
7. **Port:** 1433 (default)
8. Click **Test** and **Save**

### 4. PowerBI (Optional)

1. **Connection ID:** `powerbi_default`
2. **Connection Type:** `HTTP`
3. **Host:** `https://app.powerbi.com`
4. **Extra** JSON:
```json
{
  "tenant_id": "your-azure-tenant-id",
  "client_id": "your-aad-app-client-id",
  "client_secret": "your-aad-app-secret",
  "scope": "https://analysis.windows.net/.default"
}
```

## 📚 Example DAG

Create a file `dags/quickstart_pipeline.py`:

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageDownloadOperator
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from datetime import datetime

def process_data(**context):
    print("Processing data...")
    return "Data processed successfully"

with DAG(
    'quickstart_pipeline',
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    # Step 1: Download from Azure
    download = AzureBlobStorageDownloadOperator(
        task_id='download_from_azure',
        container_name='data',
        blob_name='input/data.csv',
        file_path='/tmp/data.csv',
        azure_conn_id='azure_blob_storage_default',
    )
    
    # Step 2: Process the data
    process = PythonOperator(
        task_id='process_data',
        python_callable=process_data,
    )
    
    # Step 3: Load to on-prem SQL Server
    load_sql = MsSqlOperator(
        task_id='load_to_sqlserver',
        mssql_conn_id='mssql_onprem',
        sql='INSERT INTO dbo.ProcessedData SELECT * FROM SourceData',
    )
    
    # Step 4: Trigger Databricks job
    databricks_job = DatabricksRunNowOperator(
        task_id='run_databricks_job',
        job_id='123456789',  # Replace with your job ID
        databricks_conn_id='databricks_default',
    )
    
    download >> process >> load_sql >> databricks_job
```

Upload this to your AKS cluster:

```powershell
kubectl cp dags/quickstart_pipeline.py airflow-scheduler:/opt/airflow/dags -n airflow
```

## 🔍 Monitor Your Deployment

```powershell
# Check pod status
kubectl get pods -n airflow

# View logs
kubectl logs -n airflow deployment/airflow-scheduler -f

# Check resource usage
kubectl top nodes
kubectl top pods -n airflow

# Access Kubernetes dashboard (AKS only)
az aks browse --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_CLUSTER_NAME>
```

## 📖 Detailed Guides

For detailed setup of specific services:

- **Azure:** See `docs/AZURE_CONNECTIONS_SETUP.md`
- **Databricks:** See `docs/DATABRICKS_CONNECTION_SETUP.md`
- **PowerBI:** See `docs/POWERBI_CONNECTION_SETUP.md`
- **On-Prem SQL Server:** See `docs/ONPREM_SQLSERVER_SETUP.md`
- **Full AKS Deployment:** See `docs/AKS_DEPLOYMENT_GUIDE.md`

## 🔧 Common Tasks

### Upgrade Airflow

```powershell
helm upgrade airflow apache-airflow/airflow `
  --namespace airflow `
  -f kubernetes/values.yaml
```

### Scale Workers

```powershell
helm upgrade airflow apache-airflow/airflow `
  --namespace airflow `
  -f kubernetes/values.yaml `
  --set workers.replicas=3
```

### View All Connections

```powershell
kubectl exec -n airflow deployment/airflow-scheduler -- /bin/bash

python3 << 'EOF'
from airflow.models import Connection
from airflow.utils.db import create_default_conn_if_not_exists

session = create_default_conn_if_not_exists()
conns = session.query(Connection).all()
for conn in conns:
    print(f"{conn.conn_id}: {conn.conn_type}")
EOF
```

### Uninstall Airflow

```powershell
helm uninstall airflow -n airflow
kubectl delete namespace airflow
```

## ⚠️ Troubleshooting

### Pods not starting?

```powershell
# Check pod events
kubectl describe pod <POD_NAME> -n airflow

# Check logs
kubectl logs <POD_NAME> -n airflow --previous
```

### Provider not showing in UI?

```powershell
# Verify installation
kubectl exec -n airflow deployment/airflow-api-server -- pip list | grep -i databricks

# Restart API server
kubectl rollout restart deployment/airflow-api-server -n airflow
```

### Connection failing?

```powershell
# Test from pod
kubectl exec -n airflow deployment/airflow-scheduler -- python3 << 'EOF'
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection('your_connection_id')
print(f"Host: {conn.host}")
EOF
```

## 🚀 Next Steps

1. **Create DAGs** in the `dags/` folder
2. **Configure connections** in Airflow UI
3. **Monitor runs** in Airflow web UI
4. **Set up alerts** for failed tasks
5. **Enable audit logging** for compliance

## 📞 Support

For issues:
1. Check the detailed guides in `docs/`
2. Review Airflow logs: `kubectl logs -n airflow deployment/airflow-scheduler -f`
3. Check Kubernetes events: `kubectl describe pod <pod-name> -n airflow`
4. Consult [Apache Airflow Documentation](https://airflow.apache.org/docs/)
