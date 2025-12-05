# Airflow on AKS - Documentation

Complete documentation for deploying and managing Apache Airflow 3.0.2 on Azure Kubernetes Service.

## 📖 Getting Started

**New to Airflow on AKS?** Start here:

1. **[QUICKSTART.md](QUICKSTART.md)** - Deploy Airflow in 15 minutes
2. **[AKS_DEPLOYMENT_GUIDE.md](AKS_DEPLOYMENT_GUIDE.md)** - Detailed deployment guide

## 🔗 Connection Setup Guides

Configure Airflow connections to enterprise systems:

- **[AZURE_CONNECTIONS_SETUP.md](AZURE_CONNECTIONS_SETUP.md)** - Azure Blob Storage, Data Lake, Key Vault
- **[DATABRICKS_CONNECTION_SETUP.md](DATABRICKS_CONNECTION_SETUP.md)** - Databricks jobs, notebooks, SQL
- **[POWERBI_CONNECTION_SETUP.md](POWERBI_CONNECTION_SETUP.md)** - PowerBI dataset refresh
- **[ONPREM_SQLSERVER_SETUP.md](ONPREM_SQLSERVER_SETUP.md)** - On-premises SQL Server connectivity

## 📊 Monitoring & Operations

- **[GRAFANA_SETUP_GUIDE.md](GRAFANA_SETUP_GUIDE.md)** - Metrics visualization and alerting

## 🗂️ Document Index

### Deployment
- **QUICKSTART.md** - Fast deployment guide
- **AKS_DEPLOYMENT_GUIDE.md** - Comprehensive AKS setup

### Connections
- **AZURE_CONNECTIONS_SETUP.md** - Azure services
- **DATABRICKS_CONNECTION_SETUP.md** - Databricks platform
- **POWERBI_CONNECTION_SETUP.md** - PowerBI integration
- **ONPREM_SQLSERVER_SETUP.md** - SQL Server connections

### Monitoring
- **GRAFANA_SETUP_GUIDE.md** - Observability setup

## 🎯 Common Tasks

### Deploy Airflow
See [QUICKSTART.md](QUICKSTART.md) for step-by-step instructions.

### Add Azure Blob Connection
Follow [AZURE_CONNECTIONS_SETUP.md](AZURE_CONNECTIONS_SETUP.md#azure-blob-storage).

### Run Databricks Jobs
Configure connection in [DATABRICKS_CONNECTION_SETUP.md](DATABRICKS_CONNECTION_SETUP.md).

### Set Up Monitoring
Install Grafana using [GRAFANA_SETUP_GUIDE.md](GRAFANA_SETUP_GUIDE.md).

## 📚 Additional Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/apache-airflow/stable/)
- [Helm Chart Documentation](https://airflow.apache.org/docs/helm-chart/stable/)
- [Azure Kubernetes Service Docs](https://docs.microsoft.com/en-us/azure/aks/)

## 💡 Quick Reference

### Useful Commands
```powershell
# View pods
kubectl get pods -n airflow

# Check logs
kubectl logs -n airflow <pod-name> -c <container>

# Access UI
kubectl get svc airflow-api-server -n airflow

# Scale workers
helm upgrade airflow apache-airflow/airflow -n airflow `
  -f ../kubernetes/values.yaml `
  --set workers.replicas=3
```

### Configuration Files
- `../kubernetes/values.yaml` - Main Helm configuration
- `../kubernetes/postgres.yaml` - Database deployment
- `../dags/` - DAG definitions

## 🔍 Troubleshooting

**DAGs not showing?**
```powershell
kubectl logs -n airflow -l component=dag-processor -c dag-processor
```

**Database connection issues?**
```powershell
kubectl logs -n airflow <postgres-pod>
kubectl exec -it -n airflow <postgres-pod> -- psql -U airflow
```

**Pod not starting?**
```powershell
kubectl describe pod <pod-name> -n airflow
```

---

**Need help?** All guides include troubleshooting sections. Start with [QUICKSTART.md](QUICKSTART.md) for the basics.
