# Azure Blob Copy DAGs

## Quick Setup

### Step 1: Create Azure Connection

**Option A: Use Setup DAG (Recommended)**
1. Go to Airflow UI: http://51.8.246.115
2. Find DAG: `setup_azure_connection`
3. Click "Trigger DAG" ▶️
4. Wait ~10 seconds for completion
5. Done! Connection `azure_blob_default` is created

**Option B: Manual UI Setup**
1. Go to Admin → Connections
2. Click ➕ Add
3. Fill in:
   - **Connection Id**: `azure_blob_default`
   - **Connection Type**: `Microsoft Azure Blob Storage`
   - **Login**: `sgbilakehousestoragedev`
   - **Password**: `<YOUR_STORAGE_KEY>`  (Get from Azure Portal or use setup DAG)
4. Save

### Step 2: Run Blob Copy

After connection is created:

1. Go to DAG: `azure_blob_copy_generic`
2. Click "Trigger DAG" ▶️
3. Files from `sg-analytics-raw/seasonal_buy/2025-10-13/` will copy to `airflow` container

## Files

- **setup_connection.py** - One-time setup DAG to create Azure connection
- **azure_blob_copy_generic.py** - Generic blob copy DAG (customizable)
- **azure_blob_copy_seasonal_buy.py** - Specific seasonal buy copy DAG

## Troubleshooting

**Error: "Connection azure_blob_default not found"**
→ Run `setup_azure_connection` DAG first

**Error: "No such container"**
→ Check container names in DAG parameters

**Files not copying**
→ Verify folder path exists in source container
