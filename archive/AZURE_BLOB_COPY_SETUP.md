# Azure Blob Copy DAG - Setup Guide

## 🎯 Goal
Use Airflow's built-in Azure operators to copy seasonal buy files from `sg-analytics-raw` to `airflow` container in Azure Storage Account `sgbilakehousestoragedev`.

## 📋 Prerequisites

1. **Azure Provider Package** (should already be installed in your Airflow)
   ```bash
   pip install apache-airflow-providers-microsoft-azure
   ```

2. **Azure Storage Account Details**
   - Account Name: `sgbilakehousestoragedev`
   - Source Container: `sg-analytics-raw`
   - Target Container: `airflow`
   - Files: `seasonal_buy/2025-10-13/*` (40 files)

## ⚙️ Step 1: Configure Airflow Connection

### Option A: Via Airflow UI (Recommended)

1. **Open Airflow UI**: http://51.8.246.115

2. **Go to Admin → Connections**

3. **Create New Connection**:
   - **Connection Id**: `azure_blob_default`
   - **Connection Type**: `Azure Blob Storage`
   - **Login**: `sgbilakehousestoragedev` (storage account name)
   - **Password**: `<your-storage-account-key>`
   - **Extra**: Leave empty or add:
     ```json
     {
       "account_url": "https://sgbilakehousestoragedev.blob.core.windows.net"
     }
     ```

4. **Test Connection** and **Save**

### Option B: Via kubectl (Direct to Kubernetes)

Get your storage account key first:
```powershell
az storage account keys list --resource-group bi_lakehouse_dev_rg --account-name sgbilakehousestoragedev --query "[0].value" -o tsv
```

Then create the connection using kubectl:
```powershell
$storageKey = "YOUR_STORAGE_KEY_HERE"

$connectionJson = @{
    conn_id = "azure_blob_default"
    conn_type = "wasb"
    login = "sgbilakehousestoragedev"
    password = $storageKey
} | ConvertTo-Json -Compress

# Encode to base64
$encoded = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($connectionJson))

# Create secret in Airflow namespace
kubectl create secret generic airflow-azure-connection `
    --from-literal=connection=$encoded `
    --namespace airflow
```

### Option C: Get Storage Key and Add Manually

```powershell
# Get storage key
az storage account keys list `
    --resource-group bi_lakehouse_dev_rg `
    --account-name sgbilakehousestoragedev `
    --query "[0].value" -o tsv
```

Copy the key and use it in Airflow UI connection setup.

## 🚀 Step 2: Run the DAG

### Method 1: Airflow UI

1. Open http://51.8.246.115
2. Find DAG: `azure_blob_copy_seasonal_buy`
3. Unpause the DAG (toggle switch)
4. Click **Trigger DAG** button
5. **Optional**: Modify parameters if needed:
   ```json
   {
     "source_container": "sg-analytics-raw",
     "target_container": "airflow",
     "prefix": "seasonal_buy/2025-10-13/"
   }
   ```
6. Click **Trigger**

### Method 2: Airflow CLI (from pod)

```powershell
# Get scheduler pod
kubectl get pods -n airflow -l component=scheduler

# Trigger DAG
kubectl exec -it airflow-scheduler-xxxxx -n airflow -- airflow dags trigger azure_blob_copy_seasonal_buy
```

## 📊 Monitor Progress

### Watch in Real-Time (Airflow UI)
1. Click on DAG name
2. Click on running DAG run
3. Click on task (list_source_files, copy_files, verify_copy)
4. Click **Logs** to see detailed output

### Expected Execution Flow
```
list_source_files (30s)
    ↓
    Lists 40 files in sg-analytics-raw/seasonal_buy/2025-10-13/
    ↓
copy_files (2-5 minutes)
    ↓
    Copies each file from source to target
    Logs progress for each file
    ↓
verify_copy (30s)
    ↓
    Verifies all files copied successfully
    ✓ Success
```

## 🎯 What Each Task Does

### Task 1: `list_source_files`
- Connects to Azure Storage
- Lists all files matching prefix `seasonal_buy/2025-10-13/`
- Should find 40 files
- Passes list to next task via XCom

### Task 2: `copy_files`
- Gets file list from previous task
- Reads each file from `sg-analytics-raw`
- Writes to `airflow` container
- Logs progress for each file
- Returns count of successes/failures

### Task 3: `verify_copy`
- Lists files in target container
- Compares count with source
- Confirms copy was successful

## ✅ Verify Results

### Check in Airflow UI
- All 3 tasks should show green (success)
- Check logs for "✓" symbols

### Check in Azure Portal
1. Go to Storage Account: `sgbilakehousestoragedev`
2. Navigate to container: `airflow`
3. Browse to: `seasonal_buy/2025-10-13/`
4. Should see 40 files

### Check via Azure CLI
```powershell
az storage blob list `
    --account-name sgbilakehousestoragedev `
    --container-name airflow `
    --prefix "seasonal_buy/2025-10-13/" `
    --output table
```

## 🔧 Troubleshooting

### Error: "Connection 'azure_blob_default' not found"
**Solution**: Create the connection in Airflow UI (see Step 1)

### Error: "AuthenticationError" or "403 Forbidden"
**Solution**: Check storage account key is correct in connection

### Error: "Container 'airflow' not found"
**Solution**: Create container first:
```powershell
az storage container create `
    --name airflow `
    --account-name sgbilakehousestoragedev
```

### DAG not visible in UI
**Solution**: 
1. Check DAG file is in `/dags` folder in pod
2. Check for syntax errors in Airflow UI → Browse → DAG Code
3. Wait 30 seconds for DAG to be parsed

### Task fails with "No module named 'azure'"
**Solution**: Install Azure provider in Airflow:
```bash
kubectl exec -it airflow-scheduler-xxxxx -n airflow -- pip install apache-airflow-providers-microsoft-azure
```

## 🎓 DAG Features

✅ **Uses Airflow's Official Azure Provider** - No custom code
✅ **Built-in WasbHook** - Production-ready Azure Blob operations
✅ **Error Handling** - Continues on individual file failures
✅ **XCom for Data Passing** - Task communication
✅ **Verification Step** - Confirms successful copy
✅ **Detailed Logging** - Progress visibility
✅ **Parameterized** - Easy to customize source/target
✅ **Idempotent** - Safe to re-run

## 📝 Next Steps

After successful test:
1. ✅ Test with this seasonal buy data
2. Create similar DAGs for other data sources
3. Add scheduling (daily/weekly)
4. Add email notifications on failure
5. Add Slack/Teams integration
6. Create monitoring dashboard

## 🔗 Related Files

- **DAG**: `dags/azure_blob_copy_seasonal_buy.py`
- **Original Examples**: `dags/azure/azure_blob_copy_dag.py`
- **Azure Connector**: `src/connectors/azure_connector.py`

---

**Storage Account**: sgbilakehousestoragedev  
**Source**: sg-analytics-raw/seasonal_buy/2025-10-13/  
**Target**: airflow/seasonal_buy/2025-10-13/  
**Files**: 40 files (~150 MB total)
