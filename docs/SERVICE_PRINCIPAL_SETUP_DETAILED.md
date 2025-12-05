# Complete Guide: Create Databricks Service Principal with Workspace-Only Access

## Overview
This guide will help you create a **Service Principal** with limited permissions scoped only to your workspace. This is more secure than personal PAT tokens.

---

## Prerequisites
- Databricks workspace admin access
- Your workspace URL: `https://adb-5444953219183209.9.azuredatabricks.net`
- Your workspace ID: `5444953219183209`

---

## Part 1: Create Service Principal via UI (Easiest Method)

### Step 1: Go to Databricks Admin Settings
1. Log into your Databricks workspace: `https://adb-5444953219183209.9.azuredatabricks.net`
2. Click your **profile icon** (bottom left)
3. Select **Admin Settings**
4. Look for **"Service Principals"** or **"Users & Groups"** section (varies by Databricks version)

### Step 2: Create New Service Principal
1. Click **"Add"** or **"Create Service Principal"** button
2. Fill in the details:
   - **Display Name**: `airflow-aks-service-principal`
   - **Description** (optional): `Service principal for Airflow on AKS cluster`
   - **Workspace Assignment** (if available): Select your current workspace
3. Click **Create**

**You'll see a new service principal created with an ID** (e.g., `a1b2c3d4e5f6g7h8`)

---

## Part 2: Assign Workspace Permissions to Service Principal

### Option A: Admin Access (Simplest for Testing)
If you just want it to work quickly:
1. Click on the service principal you created
2. Look for **"Admin"** or **"Workspace Admin"** checkbox
3. Enable it
4. Click **Save**

✅ **This grants full workspace access** - good for initial testing

### Option B: Fine-Grained Access (Production Recommended)
For more security, grant only what Airflow needs:

1. Click on the service principal
2. Look for **"Permissions"** or **"ACL"** section
3. Grant these permissions:
   - **Jobs**: `jobs/read`, `jobs/run`, `jobs/modify` (if running/modifying jobs)
   - **Clusters**: `clusters/read` (if querying clusters)
   - **Notebooks**: `directories/read` (if accessing workspace files)
   - **Workspace**: `workspace/read` (read workspace metadata)

**Minimal set for `databricks_list_workflows`**:
```
- jobs/read
- workspace/read
```

**Full set for production Airflow DAGs**:
```
- jobs/read
- jobs/run
- jobs/modify
- clusters/read
- workspace/read
- directories/read
- notebooks/read
- run/read (to query job run status)
```

---

## Part 3: Generate OAuth Token for Service Principal

### Step 1: Locate the Service Principal
1. In Admin Settings → Service Principals
2. Find `airflow-aks-service-principal`
3. Click on it

### Step 2: Generate Token
1. Click **"Generate Token"** or **"New Token"** button
2. You'll see options:
   - **Lifetime**: Choose duration
     - **Recommended for production**: 0 (never expires) or 3 months
     - **Recommended for testing**: 7 days (auto-rotate frequently)
   - **Comment** (optional): `Airflow AKS cluster access`
3. Click **Generate**

### Step 3: Copy the Token
1. You'll see a token starting with `dapi...` (example: `dapiXXXXXXXXXXXXXXXXXXXXXXXXXXX`)
2. **Copy and save this immediately** - you won't see it again!
3. Store it securely (don't commit to git, don't share in messages)

**Format**: `dapi[base64-encoded-token]`

---

## Part 4: Update Airflow Connection with Service Principal Token

### Option A: Update via Airflow UI (Easiest)

1. **Port forward to Airflow UI**:
   ```powershell
   kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
   ```

2. **Open in browser**: `http://localhost:8080`

3. **Navigate to Connections**:
   - Click **Admin** → **Connections**
   - Search for **"databricks_default"**
   - Click the **pencil icon** to edit

4. **Update the connection**:
   - **Connection ID**: `databricks_default` (keep same)
   - **Connection Type**: `databricks` (keep same)
   - **Host**: `https://adb-5444953219183209.9.azuredatabricks.net`
   - **Password**: `dapi[YOUR_SERVICE_PRINCIPAL_TOKEN]`
   - Leave **Login** empty
   - Leave other fields as-is

5. **Click "Save"**

6. **Verify**: Click **"Test"** button to confirm connection works

### Option B: Update via kubectl (Command Line)

```powershell
kubectl exec -n airflow airflow-webserver-* -c webserver -- \
  airflow connections upsert --conn-id databricks_default \
  --conn-type databricks \
  --conn-host https://adb-5444953219183209.9.azuredatabricks.net \
  --conn-password "dapi[YOUR_SERVICE_PRINCIPAL_TOKEN]"
```

### Option C: Update via Kubernetes Secret (Most Secure)

```powershell
# Create a Kubernetes secret with the token
kubectl create secret generic databricks-sp-token \
  -n airflow \
  --from-literal=token="dapi[YOUR_SERVICE_PRINCIPAL_TOKEN]" \
  --dry-run=client -o yaml | kubectl apply -f -

# Then update the Airflow connection to use this secret
```

---

## Part 5: Test the Connection

### Test 1: Verify Connection in Airflow
```powershell
kubectl exec -n airflow airflow-dag-processor-64598fd9f4-j24sj -c dag-processor -- \
  python3 -c "
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection('databricks_default')
print(f'✅ Connection: {conn.conn_id}')
print(f'✅ Host: {conn.host}')
print(f'✅ Type: {conn.conn_type}')
print(f'✅ Token present: {\"Yes\" if conn.password else \"No\"}')
"
```

### Test 2: Run the List Workflows DAG
```powershell
kubectl exec -n airflow airflow-dag-processor-64598fd9f4-j24sj -c dag-processor -- \
  airflow dags test databricks_list_workflows 2025-12-05
```

**Expected output**:
```
✅ Connection retrieved: databricks_default
✅ WorkspaceClient created successfully
📋 Fetching workflows/jobs from workspace...
======================================================================
WORKFLOWS/JOBS IN WORKSPACE
======================================================================
#1 📌 Job ID: 123
    Name: My First Job
    Created: 2025-01-15
#2 📌 Job ID: 124
    Name: Data Processing Job
    Created: 2025-01-16
...
======================================================================
✅ Total Workflows Found: 15
======================================================================
```

---

## Permission Levels Explained

### Admin
- Full workspace access
- Can modify workspace settings
- **Best for**: Development/testing

### Workspace Permissions (Fine-grained)

| Permission | What it allows |
|-----------|----------------|
| `admin` | Full admin access to workspace |
| `jobs/read` | List and query jobs |
| `jobs/run` | Trigger/execute jobs |
| `jobs/manage` | Create/modify/delete jobs |
| `clusters/read` | List and query clusters |
| `clusters/manage` | Create/modify/delete clusters |
| `workspace/read` | List workspace files/directories |
| `workspace/write` | Create/modify files |
| `notebooks/read` | Read notebook content |
| `runs/read` | Query job run status |

### Recommended Permissions for Airflow

**Minimum (read-only)**:
```json
{
  "permissions": [
    "jobs/read",
    "workspace/read",
    "runs/read"
  ]
}
```

**Full (for production DAGs)**:
```json
{
  "permissions": [
    "jobs/read",
    "jobs/run",
    "clusters/read",
    "workspace/read",
    "runs/read",
    "directories/read",
    "notebooks/read"
  ]
}
```

---

## Troubleshooting

### Issue: "Unauthorized network access" error persists
**Cause**: IP allowlisting is still blocking the request
**Solution**: Ask Databricks admin to add your AKS IP to the allowlist
- Get AKS IP: `kubectl get svc -A | Select-String LoadBalancer`
- Admin adds to: Databricks Admin → Network → IP Allowlist

### Issue: Token invalid or expired
**Solution**: Generate a new token for the service principal
1. Go to service principal
2. Click **"Revoke Token"** (optional, to remove old one)
3. Click **"Generate New Token"**
4. Update Airflow connection with new token

### Issue: "Permission denied" even with token
**Cause**: Service principal doesn't have required permissions
**Solution**: 
1. Go to service principal settings
2. Verify **"Active"** is enabled
3. Check assigned permissions include at least `jobs/read`
4. If using Admin role, enable it

### Issue: Connection test passes but DAGs still fail
**Cause**: Connection is working but workspace has additional restrictions
**Solutions**:
1. Check workspace IP allowlist settings
2. Verify service principal has workspace access (not just connection access)
3. Check Airflow pod logs for detailed error: `kubectl logs -n airflow <pod-name>`

---

## Security Best Practices

✅ **DO**:
- Use service principals for service-to-service auth (Airflow → Databricks)
- Grant minimal required permissions (principle of least privilege)
- Rotate tokens every 90 days
- Store tokens in Kubernetes secrets, not in code
- Enable token expiration (e.g., 3 months)

❌ **DON'T**:
- Use personal PAT tokens (tied to user accounts)
- Commit tokens to git repositories
- Grant admin access if not needed
- Share tokens in messages/emails
- Use same token across environments (dev/staging/prod)

---

## Summary of Steps

1. ✅ Create service principal in Databricks Admin Settings
2. ✅ Assign workspace permissions (admin or fine-grained)
3. ✅ Generate OAuth token for the service principal
4. ✅ Copy the token securely
5. ✅ Update Airflow `databricks_default` connection with new token
6. ✅ Test the connection
7. ✅ Verify DAG runs and lists workflows

---

## Next Steps

Once your service principal is set up and Airflow can access Databricks:

1. **Deploy production DAGs**:
   - `databricks_production_etl.py` - ETL using DatabricksSubmitRunOperator
   - `databricks_job_orchestration.py` - Run existing jobs via DatabricksRunNowOperator

2. **Configure PowerBI connection** (similar process)

3. **Configure SQL Server connection** for on-premises data

4. **Set up monitoring** for DAG runs and job execution
