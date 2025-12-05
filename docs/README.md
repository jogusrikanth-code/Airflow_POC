# Airflow POC Documentation

Complete guide for deploying and testing Apache Airflow 3.0.2 on Azure Kubernetes Service.

## 📖 Start Here

- **[../README.md](../README.md)** - Project overview and quick start
- **[QUICKSTART.md](QUICKSTART.md)** - Fast-track 5-minute deployment
- **[AKS_DEPLOYMENT_GUIDE.md](AKS_DEPLOYMENT_GUIDE.md)** - Detailed deployment instructions

## 🔗 Connections & Integration

- **[CONNECTIONS_SETUP.md](CONNECTIONS_SETUP.md)** - Configure all 4 connection types:
  - Azure Blob Storage
  - Databricks
  - Power BI
  - On-Premises SQL Server

## 🏗️ Project Structure

```
Airflow_POC/
├── dags/                 - 4 focused POC DAGs
│   ├── azure/           - Azure Blob Storage POC
│   ├── databricks/      - Databricks integration POC
│   ├── powerbi/         - Power BI refresh POC
│   └── onprem/          - On-Prem SQL Server POC
├── kubernetes/          - Helm deployment config
├── monitoring/          - Airflow monitoring guide
├── docs/                - This documentation
└── archive/             - Previous implementations
```

## 🎯 POC DAGs

The POC includes 4 focused test DAGs with server-side operations:

### 1. Azure ETL POC (`azure_etl_poc`)
- Extract data from Azure Blob Storage
- Process locally in Airflow
- Load results back to Azure Blob
- **Connection needed:** `azure_blob_default`

### 2. Databricks ETL POC (`databricks_etl_poc`)
- Verify Databricks connection
- Submit notebook transformation job
- Load results to Delta Lake
- **Connection needed:** `databricks_default`

### 3. Power BI Refresh POC (`powerbi_refresh_poc`)
- Authenticate with Azure
- Trigger Power BI dataset refresh
- Monitor refresh status
- Validate data
- **Connection needed:** `azure_default`

### 4. On-Prem SQL Server ETL POC (`onprem_sqlserver_etl_poc`)
- Connect to on-premises SQL Server
- Extract source data
- Execute server-side transformation (stored procedure)
- Load to target table
- Validate data quality
- **Connection needed:** `onprem_mssql`

## 🚀 Deployment Steps

1. **Setup AKS cluster** → See [AKS_DEPLOYMENT_GUIDE.md](AKS_DEPLOYMENT_GUIDE.md)
2. **Deploy Airflow** → See [QUICKSTART.md](QUICKSTART.md)
3. **Configure connections** → See [CONNECTIONS_SETUP.md](CONNECTIONS_SETUP.md)
4. **Test POC DAGs** → Trigger from Airflow UI at `http://localhost:8080`

## 📊 Monitoring

View Airflow logs and status:

```powershell
# Port-forward to UI
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080

# View scheduler logs
kubectl logs -n airflow deployment/airflow-scheduler -f

# View worker logs
kubectl logs -n airflow deployment/airflow-worker -f
```

See [../monitoring/README.md](../monitoring/README.md) for more details.

## 🔧 Troubleshooting

Check if all pods are running:
```powershell
kubectl get pods -n airflow
```

View pod events and errors:
```powershell
kubectl describe pod -n airflow <pod-name>
```

## 📝 Notes

- **Airflow Version:** 3.0.2
- **Executor:** CeleryExecutor with Redis broker
- **Database:** PostgreSQL (external service)
- **Python:** 3.11
- **Kubernetes:** 1.24+

## 🔗 External Resources

- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Airflow Helm Chart](https://airflow.apache.org/docs/helm-chart/stable/)
- [Azure Kubernetes Service](https://learn.microsoft.com/en-us/azure/aks/)
- [Databricks API Reference](https://docs.databricks.com/api/)
- [SQL Server ODBC Driver](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
