# Connection Test Guide

This guide shows how to test each connection using the simplified test DAGs before running the full POC functionality DAGs.

## Overview

We have 4 connection test DAGs that verify connectivity without performing any data operations:

1. **test_azure_connection** - Tests Azure Blob Storage (✅ PASSED)
2. **test_databricks_connection** - Tests Databricks workspace
3. **test_powerbi_connection** - Tests PowerBI/Azure AD authentication
4. **test_sqlserver_connection** - Tests SQL Server connectivity

## Test Sequence

### Step 1: Azure Blob Storage (✅ COMPLETED)

**Connection ID:** `azure_blob_default`  
**Status:** ✅ Configured and tested successfully

```powershell
# Unpause the DAG
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags unpause test_azure_connection

# Trigger the test
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags trigger test_azure_connection

# Check results (wait 30 seconds first)
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow tasks states-for-dag-run test_azure_connection <run-id>
```

**Test Results:**
- ✅ Connection retrieved successfully
- ✅ BlobServiceClient created
- ✅ Found 25 containers (adobe, airflow, airflow-logs, alation, etc.)
- ✅ Storage Account: sgbilakehousestoragedev

**What it tests:**
- Connection exists in Airflow
- Storage account name is correct
- Storage account key is valid
- Can list containers
- Network connectivity to Azure

---

### Step 2: Databricks Connection

**Connection ID:** `databricks_default`  
**Status:** ⏳ Not yet configured

**Configure the connection:**
```powershell
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow connections add databricks_default `
  --conn-type databricks `
  --conn-host "https://your-workspace.azuredatabricks.net" `
  --conn-password "your-personal-access-token"
```

**Run the test:**
```powershell
# Unpause and trigger
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags unpause test_databricks_connection
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags trigger test_databricks_connection

# Check results
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow tasks states-for-dag-run test_databricks_connection <run-id>
```

**What it tests:**
- Connection exists in Airflow
- Host URL is accessible
- Personal Access Token is valid
- Can authenticate to Databricks workspace

**Expected output if successful:**
```
✓ Connection retrieved: databricks_default
✓ Host: https://your-workspace.azuredatabricks.net
✓ Token present: Yes
✅ Databricks Connection Test PASSED
```

**Expected output if not configured:**
```
❌ Connection 'databricks_default' not found
📝 Please configure the Databricks connection first
```

---

### Step 3: PowerBI Connection

**Connection ID:** `azure_default` (for Azure AD authentication)  
**Status:** ⏳ Not yet configured

**Prerequisites:**
1. Azure AD App Registration
2. Client ID, Client Secret, and Tenant ID
3. PowerBI Service Principal access

**Configure the connection:**
```powershell
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow connections add azure_default `
  --conn-type generic `
  --conn-login "your-client-id" `
  --conn-password "your-client-secret" `
  --conn-extra '{"tenantId": "your-tenant-id"}'
```

**Run the test:**
```powershell
# Unpause and trigger
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags unpause test_powerbi_connection
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags trigger test_powerbi_connection

# Check results
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow tasks states-for-dag-run test_powerbi_connection <run-id>
```

**What it tests:**
- Connection exists in Airflow
- Azure AD Client ID is configured
- Azure AD Client Secret is present
- Tenant ID is in extra field

**Expected output if successful:**
```
✓ Connection retrieved: azure_default
✓ Client ID: abc123...
✓ Client Secret: Present
✓ Tenant ID: def456...
✅ PowerBI/Azure AD Connection Test PASSED
```

---

### Step 4: SQL Server Connection

**Connection ID:** `onprem_mssql`  
**Status:** ⏳ Not yet configured

**Configure the connection:**
```powershell
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow connections add onprem_mssql `
  --conn-type mssql `
  --conn-host "your-sql-server.database.windows.net" `
  --conn-schema "your-database-name" `
  --conn-login "your-username" `
  --conn-password "your-password" `
  --conn-port 1433
```

**Run the test:**
```powershell
# Unpause and trigger
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags unpause test_sqlserver_connection
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags trigger test_sqlserver_connection

# Check results
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow tasks states-for-dag-run test_sqlserver_connection <run-id>
```

**What it tests:**
- Connection exists in Airflow
- Host, database, login credentials are configured
- Port is set (default 1433)

**Expected output if successful:**
```
✓ Connection retrieved: onprem_mssql
✓ Host: your-sql-server.database.windows.net:1433
✓ Database: your-database-name
✓ Login: your-username
✅ SQL Server Connection Test PASSED
```

---

## Quick Commands Reference

### Get Current Pod Name
```powershell
kubectl get pods -n airflow | Select-String "dag-processor"
```

### List All Test DAGs
```powershell
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags list | Select-String "test_"
```

### Check Task Status
```powershell
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow tasks states-for-dag-run <dag-id> <run-id>
```

### View Task Logs
```powershell
kubectl exec -n airflow airflow-worker-0 -c worker -- cat /opt/airflow/logs/dag_id=<dag-id>/run_id=<run-id>/task_id=<task-id>/attempt=1.log
```

---

## After All Tests Pass

Once all connection tests pass, you can run the full POC functionality DAGs:

1. **azure_etl_poc** - Copy files from seasonal_buy to Airflow folder
2. **databricks_etl_poc** - Run Databricks notebooks and jobs
3. **powerbi_refresh_poc** - Trigger PowerBI dataset refresh
4. **onprem_sqlserver_etl_poc** - Extract data from SQL Server

### Run Azure File Copy POC (Fixed Version)
```powershell
# This version copies a single test file (no longer fails with InvalidInput)
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags trigger azure_etl_poc

# Check results
kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow tasks states-for-dag-run azure_etl_poc <run-id>
```

---

## Troubleshooting

### Task stays in "queued" state
- Wait 30-60 seconds for scheduler cycle
- Check if worker pods are running: `kubectl get pods -n airflow`
- Check scheduler logs: `kubectl logs -n airflow airflow-scheduler-<pod-id> -c scheduler --tail=50`

### Task fails with "Connection not found"
- List connections: `kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow connections list`
- Configure the missing connection using commands above

### Cannot see test DAGs in UI
- Check if DAGs are parsed: `kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags list`
- Check for import errors: `kubectl exec -n airflow airflow-dag-processor-<pod-id> -c dag-processor -- airflow dags list-import-errors`
- Wait for bundle refresh (happens every ~30 seconds)

### View logs in Airflow UI
1. Navigate to http://48.216.148.118:8080
2. Login: admin/admin
3. Click on DAG name (e.g., test_azure_connection)
4. Click on the latest run
5. Click on task box → Click "Log" button

---

## Summary

**Current Status:**
- ✅ Azure Blob Storage: Tested and working (25 containers found)
- ⏳ Databricks: Connection needs configuration
- ⏳ PowerBI: Connection needs configuration  
- ⏳ SQL Server: Connection needs configuration

**Next Steps:**
1. Configure remaining 3 connections
2. Run their test DAGs to verify
3. Once all tests pass, run the full functionality POCs
4. Azure file copy is ready to test (fixed max_results parameter issue)
