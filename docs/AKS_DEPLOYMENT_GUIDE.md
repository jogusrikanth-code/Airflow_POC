# Airflow Deployment on Azure Kubernetes Service (AKS)

This guide covers deploying Apache Airflow to Azure Kubernetes Service with connections to Azure, Databricks, PowerBI, and on-premises SQL Server.

## Prerequisites

- Azure CLI installed and authenticated: `az login`
- kubectl installed: `az aks install-cli`
- Helm 3+ installed
- Access to an AKS cluster

## Quick Start

### 1. Connect to Your AKS Cluster

```powershell
# List your AKS clusters
az aks list --output table

# Get credentials for your cluster
az aks get-credentials --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_CLUSTER_NAME>

# Verify connection
kubectl get nodes
```

### 2. Create Airflow Namespace

```powershell
kubectl create namespace airflow
```

### 3. Add Airflow Helm Repository

```powershell
helm repo add apache-airflow https://airflow.apache.org
helm repo update
```

### 4. Deploy Airflow to AKS

From the `Airflow_POC` directory:

```powershell
helm install airflow apache-airflow/airflow `
  --namespace airflow `
  --create-namespace `
  -f kubernetes/values.yaml `
  --set-string "config.core.fernet_key=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

**Note:** Generate a new Fernet key for your environment using the Python command above.

### 5. Verify Installation

```powershell
# Check pod status
kubectl get pods -n airflow

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod -l app=airflow -n airflow --timeout=300s

# Get the Airflow Web UI URL (LoadBalancer)
kubectl get svc -n airflow
# Look for the airflow-webserver service external IP
```

### 6. Access Airflow Web UI

```powershell
# Get the external IP of the webserver service
$AIRFLOW_IP = kubectl get svc airflow-webserver -n airflow -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
Write-Host "Airflow URL: http://$AIRFLOW_IP:8080"
```

Default credentials (if no custom auth is configured):
- **Username:** admin
- **Password:** admin

## Helm Deployment Values

The deployment uses `kubernetes/values.yaml` which includes:

### Providers Installed

All the following providers are automatically installed:

- **Azure:** `apache-airflow-providers-microsoft-azure`
- **Databricks:** `apache-airflow-providers-databricks`
- **MSSQL/PowerBI:** `apache-airflow-providers-microsoft-mssql`
- **ODBC (On-Premises SQL Server):** `apache-airflow-providers-odbc`
- **Postgres:** `apache-airflow-providers-postgres`
- **HTTP:** `apache-airflow-providers-http`

### Key Configuration

- **Executor:** CeleryExecutor (distributed task execution)
- **Database:** PostgreSQL (external or managed)
- **Broker:** Redis (for Celery)
- **Airflow Version:** 2.9.3
- **Python Version:** 3.11

## Updating the Deployment

If you modify `kubernetes/values.yaml`:

```powershell
helm upgrade airflow apache-airflow/airflow `
  --namespace airflow `
  -f kubernetes/values.yaml
```

## Scaling the Deployment

### Increase Worker Pods

```powershell
helm upgrade airflow apache-airflow/airflow `
  --namespace airflow `
  -f kubernetes/values.yaml `
  --set workers.replicas=3
```

### Check Worker Status

```powershell
kubectl get pods -n airflow -l component=worker
```

## Uninstall Airflow

```powershell
helm uninstall airflow -n airflow
kubectl delete namespace airflow
```

## Next Steps

See the following guides for configuring connections:

1. **Azure Connections:** `docs/AZURE_CONNECTIONS_SETUP.md`
2. **Databricks Connection:** `docs/DATABRICKS_CONNECTION_SETUP.md`
3. **PowerBI Connection:** `docs/POWERBI_CONNECTION_SETUP.md`
4. **On-Premises SQL Server:** `docs/ONPREM_SQLSERVER_SETUP.md`

## Troubleshooting

### Check Pod Logs

```powershell
# Check scheduler logs
kubectl logs -n airflow deployment/airflow-scheduler -f

# Check API server logs
kubectl logs -n airflow deployment/airflow-api-server -f

# Check worker logs
kubectl logs -n airflow pod/<worker-pod-name> -f
```

### Verify Providers Are Installed

```powershell
# Check Databricks provider
kubectl exec -n airflow deployment/airflow-scheduler -- pip list | Select-String "databricks"

# Check all installed providers
kubectl exec -n airflow deployment/airflow-scheduler -- airflow providers list
```

### Access Kubernetes Dashboard

```powershell
# For Azure AKS, you can use the Azure Portal or:
az aks browse --resource-group <YOUR_RESOURCE_GROUP> --name <YOUR_CLUSTER_NAME>
```

## Resource Requirements

The default configuration requests:
- **Scheduler:** 500m CPU, 512Mi memory
- **Workers:** 500m CPU, 512Mi memory each
- **Web Server:** 500m CPU, 512Mi memory

Adjust in `kubernetes/values.yaml` based on your cluster capacity and workload requirements.

## Database and Redis

The deployment uses:
- **PostgreSQL:** External managed database (configure in values.yaml)
- **Redis:** Deployed as part of the Helm chart

For production, use Azure Database for PostgreSQL.

## High Availability Considerations

For production deployments:

1. **Increase replicas:** Set `replicas: 3` for scheduler and webserver
2. **Use managed database:** Azure Database for PostgreSQL with HA
3. **Use managed Redis:** Azure Cache for Redis
4. **Configure pod disruption budgets:** Protect against cluster scaling issues
5. **Use proper RBAC:** Limit service account permissions

## Security Best Practices

1. **Use Azure Key Vault** for sensitive credentials
2. **Enable pod security policies** in your AKS cluster
3. **Use network policies** to restrict pod-to-pod communication
4. **Regularly update** the Airflow image and providers
5. **Enable audit logging** in your AKS cluster
