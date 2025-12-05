# Airflow POC - Azure Kubernetes Service Deployment

Welcome to the Airflow Proof of Concept repository! This project demonstrates running Apache Airflow on **Azure Kubernetes Service (AKS)** with enterprise integrations.

## 🚀 Quick Start (5 minutes)

Deploy Airflow to your AKS cluster:

```powershell
# 1. Connect to AKS
az aks get-credentials --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_CLUSTER_NAME>

# 2. Add Helm repository
helm repo add apache-airflow https://airflow.apache.org
helm repo update

# 3. Deploy Airflow
helm install airflow apache-airflow/airflow `
  --namespace airflow `
  --create-namespace `
  -f kubernetes/values.yaml

# 4. Get access details
$AIRFLOW_IP = kubectl get svc airflow-webserver -n airflow -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Write-Host "Airflow URL: http://$AIRFLOW_IP:8080"
```

**See [QUICKSTART.md](docs/QUICKSTART.md) for detailed setup and configuration.**

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

### 📖 Additional Resources

- **[docs/00_START_HERE.md](docs/00_START_HERE.md)** - Documentation index
- **[docs/README.md](docs/README.md)** - Full documentation guide

## 💼 Supported Integrations

This setup includes pre-configured providers for:

- ☁️ **Azure** - Blob Storage, Data Lake, Event Hubs, Synapse
- 🧱 **Databricks** - Jobs, Notebooks, SQL warehouses
- 📊 **PowerBI** - Dataset refresh, report management
- 🗄️ **On-Premises SQL Server** - ODBC, MSSQL providers
- 🐘 **PostgreSQL** - Data warehouse backend
- 🔴 **Redis** - Celery broker for task execution

## 📁 Project Structure

```
Airflow_POC/
├── dags/                          # Your DAG files go here
│   ├── simple_etl_pipeline.py
│   ├── azure/                     # Azure-specific DAGs
│   ├── databricks/                # Databricks-specific DAGs
│   ├── powerbi/                   # PowerBI-specific DAGs
│   └── onprem/                    # On-premises SQL DAGs
├── kubernetes/                    # Kubernetes & Helm configuration
│   ├── values.yaml               # Main Helm values (customize here)
│   ├── airflow.yaml              # Raw K8s manifests
│   └── provider-init-configmap.yaml
├── docs/                         # Complete documentation
│   ├── QUICKSTART.md             # Start here!
│   ├── AKS_DEPLOYMENT_GUIDE.md
│   ├── AZURE_CONNECTIONS_SETUP.md
│   ├── DATABRICKS_CONNECTION_SETUP.md
│   ├── POWERBI_CONNECTION_SETUP.md
│   └── ONPREM_SQLSERVER_SETUP.md
├── requirements.txt              # Python dependencies
└── Dockerfile                    # (Deprecated - use Helm instead)
```

## 🔄 Common Workflows

### 1. Deploying a New DAG

1. Create your DAG file in `dags/` folder
2. Airflow automatically picks it up (usually within 1-2 minutes)
3. Enable it in the Airflow UI

Example DAG:
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def hello_world():
    print("Hello from Airflow on AKS!")

with DAG('hello_world', start_date=datetime(2025, 1, 1)) as dag:
    hello = PythonOperator(
        task_id='hello',
        python_callable=hello_world,
    )
```

### 2. Adding a New Connection

1. Go to Airflow UI → **Admin** → **Connections** → **Create**
2. Fill in connection details (see connection guides above)
3. Test the connection
4. Use in your DAGs

### 3. Scaling Workers

For more parallel task execution:

```powershell
helm upgrade airflow apache-airflow/airflow `
  --namespace airflow `
  -f kubernetes/values.yaml `
  --set workers.replicas=5
```

### 4. Updating Configuration

Edit `kubernetes/values.yaml` and upgrade:

```powershell
helm upgrade airflow apache-airflow/airflow `
  --namespace airflow `
  -f kubernetes/values.yaml
```

## 🔍 Monitoring & Troubleshooting

### Check Pod Status

```powershell
kubectl get pods -n airflow
kubectl describe pod <pod-name> -n airflow
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
conn = BaseHook.get_connection('your_connection_id')
print(f"Connection: {conn.conn_id} ({conn.conn_type})")
EOF
```

## 🚀 What's Included

✅ Pre-configured for Azure Kubernetes Service (AKS)  
✅ Helm chart deployment (no Docker image building needed)  
✅ All major providers pre-installed:
- Apache Airflow Providers for Azure, Databricks, MSSQL, ODBC
- Database connectors (pyodbc, psycopg2, etc.)
- Data processing libraries (pandas, pyarrow, openpyxl)

✅ CeleryExecutor for distributed task execution  
✅ PostgreSQL backend database  
✅ Redis broker for Celery  
✅ Comprehensive documentation and examples  

## 📊 Example DAGs

Located in `dags/` folder:

- **simple_etl_pipeline.py** - Basic extract, transform, load workflow
- **azure/*** - Azure Blob Storage, Data Lake examples
- **databricks/*** - Databricks job and notebook execution
- **powerbi/*** - PowerBI dataset refresh automation
- **onprem/*** - On-premises SQL Server integration

## 💡 Tips

- **Fernet Key:** Generated automatically on deployment for credential encryption
- **DAG Load:** Airflow checks for new DAGs every minute
- **Resource Limits:** Configured in `kubernetes/values.yaml`
- **High Availability:** Scale replicas for production use
- **Database:** External PostgreSQL recommended for production

## 🔐 Security

- Credentials stored in Airflow Connections (encrypted)
- Consider Azure Key Vault for sensitive data
- Network policies restrict pod communication
- RBAC for Kubernetes access control

## 📚 Learning Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Azure Kubernetes Service Documentation](https://docs.microsoft.com/en-us/azure/aks/)
- [Helm Chart Reference](https://airflow.apache.org/docs/helm-chart/stable/)

## ⚠️ Important Notes

- **No Docker Build Needed:** Use Helm chart for AKS deployment
- **Custom Images Deprecated:** All providers configured in `kubernetes/values.yaml`
- **DAG Changes:** No need to rebuild or redeploy - changes auto-load
- **Secrets:** Use Airflow Connections for all credentials

## 🎯 Next Steps

1. **Quick Deploy:** Follow [QUICKSTART.md](docs/QUICKSTART.md)
2. **Configure Connections:** See connection setup guides above
3. **Create DAGs:** Add your workflows to `dags/` folder
4. **Monitor:** Use Airflow UI and Kubernetes dashboard
5. **Scale:** Adjust worker count based on workload

## 📞 Help

Detailed guides for each component are in the `docs/` folder. Start with [QUICKSTART.md](docs/QUICKSTART.md) and reference the specific connection guides as needed.

## 🗂️ Database Queries

Use **`airflow_queries.sql`** for debugging Airflow's PostgreSQL database:
- DAG status and run history
- Failed task analysis
- Performance metrics
- XCom data inspection

See [docs/deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md](docs/deployment-guides/self-managed/POSTGRES_VSCODE_CONNECTION.md) for connection setup.

## 📁 Folder Structure

```
Airflow_POC/
├── README.md                     # Project overview (this file)
├── airflow_queries.sql           # SQL queries for debugging
├── docs/                         # 📚 Organized documentation
│   ├── README.md                 # Documentation hub
│   ├── 00_START_HERE.md          # Personalized learning path
│   ├── learning/                 # Core concepts & tutorials
│   ├── deployment-guides/        # Deployment options
│   │   ├── self-managed/         # Self-managed K8s deployment
│   │   ├── aks/                  # Azure Kubernetes Service
│   │   └── astronomer/           # Managed Airflow platform
│   ├── enterprise/               # Production patterns & integrations
│   └── reference/                # Quick reference materials
├── dags/                         # Airflow DAG definitions
├── src/                          # Python source code
│   ├── connectors/               # Enterprise connectors (Azure, Databricks, Power BI)
│   ├── extract/                  # Data extraction modules
│   ├── transform/                # Data transformation logic
│   └── load/                     # Data loading utilities
├── plugins/                      # Custom Airflow plugins
├── kubernetes/                   # K8s deployment manifests
├── data/                         # Sample data files
│   ├── raw/                      # Source data
│   └── processed/                # Transformed data
├── scripts/                      # Setup and utility scripts
└── archive/                      # Historical files for reference
```

## ⚙️ Common Commands

```powershell
# View all pods
kubectl get pods -n airflow

# Check logs
kubectl logs -n airflow deploy/airflow-scheduler -f
kubectl logs -n airflow deploy/airflow-webserver -f

# Port-forward to database (for querying)
kubectl port-forward -n airflow pod/postgres-0 5432:5432
```

**Troubleshooting?** Check [docs/deployment-guides/self-managed/QUICKSTART.md](docs/deployment-guides/self-managed/QUICKSTART.md) for detailed debugging steps.

---

**Ready to get started?** Head to [docs/README.md](docs/README.md) for your personalized learning path! 🎓
