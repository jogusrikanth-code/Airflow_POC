# Connection Setup Guide for Airflow POC

This guide explains how to configure connections for the 4 POC test scenarios:
1. Azure Blob Storage
2. Databricks
3. Power BI
4. On-Premises SQL Server

## Accessing Airflow Connections UI

```powershell
# Port-forward to Airflow UI
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080

# Login to http://localhost:8080
# Default: admin / admin
```

In the UI, go to **Admin → Connections** to add connections.

---

## 1. Azure Blob Storage Connection

**Connection ID:** `azure_blob_default`

### Steps:
1. In Airflow UI, click **Create** (+)
2. Fill in:
   - **Connection Id:** `azure_blob_default`
   - **Connection Type:** `Azure Blob Storage`
   - **Login:** Your Azure Storage Account name
   - **Password:** Your Azure Storage Account key (or connection string)
   - **Host:** Leave blank or use `https://<account>.blob.core.windows.net`

### Test:
```python
# In Airflow scheduler pod
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection('azure_blob_default')
print(conn)
```

---

## 2. Databricks Connection

**Connection ID:** `databricks_default`

### Steps:
1. In Airflow UI, click **Create** (+)
2. Fill in:
   - **Connection Id:** `databricks_default`
   - **Connection Type:** `Databricks`
   - **Host:** Your Databricks workspace URL (e.g., `https://adb-123456789.azuredatabricks.net`)
   - **Login:** Your Databricks username (optional)
   - **Password:** Your Personal Access Token (PAT) from Databricks
   - **Extra:** 
     ```json
     {
       "token": "dapi123...",
       "host": "https://adb-123456789.azuredatabricks.net"
     }
     ```

### Get Databricks PAT:
1. Log in to Databricks workspace
2. Click your profile icon → **User Settings**
3. **Developer** tab → **Access tokens**
4. **Generate new token** and copy it

### Test:
```python
from airflow.providers.databricks.hooks.databricks import DatabricksHook
hook = DatabricksHook('databricks_default')
print(hook.get_jobs_list())
```

---

## 3. Power BI Connection

**Connection ID:** `azure_default` (uses Azure auth)

### Steps:
1. In Airflow UI, click **Create** (+)
2. Fill in:
   - **Connection Id:** `azure_default`
   - **Connection Type:** `Azure`
   - **Login:** Your Azure username/service principal ID
   - **Password:** Your password/client secret
   - **Extra:**
     ```json
     {
       "extra__azure__subscription_id": "your-subscription-id",
       "extra__azure__tenant_id": "your-tenant-id",
       "extra__azure__client_id": "your-client-id"
     }
     ```

### Alternative - Service Principal:
For production, use Azure Service Principal:
1. Create a Service Principal in Azure AD
2. Grant it access to Power BI workspace
3. Store credentials in Airflow connection

---

## 4. On-Premises SQL Server Connection

**Connection ID:** `onprem_mssql`

### Steps:
1. In Airflow UI, click **Create** (+)
2. Fill in:
   - **Connection Id:** `onprem_mssql`
   - **Connection Type:** `Microsoft SQL Server`
   - **Host:** Your SQL Server hostname/IP
   - **Schema:** Default database name
   - **Login:** SQL Server username
   - **Password:** SQL Server password
   - **Port:** 1433 (default SQL Server port)
   - **Extra:**
     ```json
     {
       "driver": "ODBC Driver 17 for SQL Server"
     }
     ```

### Network Requirements:
- Ensure AKS can reach your on-premises SQL Server
- May require VPN or ExpressRoute connection
- SQL Server must allow remote connections

### Test Connection:
In Airflow UI, after creating the connection, click **Test** to verify connectivity.

---

## Testing All Connections

Run the POC DAGs to test each connection:

```powershell
# Port-forward to Airflow
kubectl port-forward -n airflow svc/airflow-webserver 8080:8080

# Go to http://localhost:8080/dags
# Trigger each POC DAG:
# - azure_etl_poc
# - databricks_etl_poc
# - powerbi_refresh_poc
# - onprem_sqlserver_etl_poc
```

Monitor task execution in the DAG's **Task** tab to verify connections work.

---

## Troubleshooting Connections

### Check Connection in Terminal:
```powershell
kubectl exec -n airflow deployment/airflow-scheduler -- airflow connections test <connection_id>
```

### View Scheduler Logs:
```powershell
kubectl logs -n airflow deployment/airflow-scheduler -f | grep -i connection
```

### Common Issues:

| Issue | Solution |
|-------|----------|
| Connection refused | Check firewall rules, verify host/port, ensure network connectivity |
| Authentication failed | Verify credentials, check token expiration, confirm permissions |
| SSL certificate error | Add CA certificate to connection Extra, or disable SSL verification (dev only) |
| DNS resolution fails | Check if hostname is resolvable from AKS pods |

---

## Connection Details Reference

| Connection | ID | Type | Required Fields |
|----------|----|----|---|
| Azure Blob | `azure_blob_default` | Azure Blob Storage | Login (account name), Password (key) |
| Databricks | `databricks_default` | Databricks | Host, Token (in Extra) |
| Power BI | `azure_default` | Azure | Login, Password, subscription/tenant/client IDs (Extra) |
| SQL Server | `onprem_mssql` | Microsoft SQL Server | Host, Schema, Login, Password, Port |

---

## Security Best Practices

1. **Never hardcode secrets** - Use Kubernetes secrets or Airflow Variables
2. **Rotate credentials regularly** - Update tokens and passwords periodically
3. **Use service accounts** - Create dedicated service accounts for Airflow
4. **Enable audit logging** - Monitor connection access and DAG execution
5. **Restrict network access** - Use network policies and firewalls
6. **Encrypt in transit** - Use TLS/SSL for all connections

For production, migrate credentials to:
- Azure Key Vault
- Kubernetes Secrets
- Airflow Backend Secrets Plugins

See `docs/SECURITY.md` for production security setup.
