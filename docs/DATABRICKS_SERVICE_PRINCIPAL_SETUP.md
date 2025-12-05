# Databricks Service Principal Setup for Airflow

## Overview
Instead of using personal PAT tokens (which are tied to your user account), you can create a **Service Principal** that:
- Has limited, scoped permissions (workspace-specific)
- Is not tied to a user account (survives if you leave the org)
- Can bypass IP allowlisting restrictions
- Is more secure for production environments

## Method 1: Using Databricks API (Recommended for Automation)

### Step 1: Get Your Databricks Workspace ID
```bash
# Your workspace ID from the URL: https://adb-5444953219183209.9.azuredatabricks.net
# Workspace ID = 5444953219183209
```

### Step 2: Create Service Principal via API
Run this from your local machine (requires admin PAT token):

```bash
curl -X POST https://adb-5444953219183209.9.azuredatabricks.net/api/2.0/service-principals \
  -H "Authorization: Bearer <YOUR_ADMIN_PAT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "Airflow-AKS-ServicePrincipal",
    "active": true
  }'
```

This returns a Service Principal ID (e.g., `123456789`).

### Step 3: Generate OAuth Token for Service Principal
```bash
curl -X POST https://adb-5444953219183209.9.azuredatabricks.net/api/2.0/service-principals/oauth2/token \
  -H "Authorization: Bearer <YOUR_ADMIN_PAT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "service_principal_id": "123456789",
    "lifetime_seconds": 0
  }'
```

This returns:
```json
{
  "access_token": "dapi...",
  "token_type": "bearer",
  "expires_in": 2592000
}
```

### Step 4: Update Airflow Connection

Use the `access_token` from the response to update your Databricks connection:

```bash
kubectl set env deployment/airflow-webserver \
  -n airflow \
  AIRFLOW_CONN_DATABRICKS_DEFAULT=databricks://<access_token>@adb-5444953219183209.9.azuredatabricks.net
```

Or update it through the Airflow UI:
- Connection ID: `databricks_default`
- Connection Type: `databricks`
- Host: `https://adb-5444953219183209.9.azuredatabricks.net`
- Password: `dapi...` (the access_token)

---

## Method 2: Using Databricks Admin Console (Manual, UI-based)

### Step 1: Log into Databricks Admin Console
1. Go to `https://adb-5444953219183209.9.azuredatabricks.net`
2. Click **Admin Settings** (requires admin role)
3. Navigate to **Service Principals** (or **Users & Groups**)

### Step 2: Create Service Principal
1. Click **Add** → **Service Principal**
2. Fill in details:
   - **Display Name**: `Airflow-AKS-ServicePrincipal`
   - **Active**: Yes
3. Click **Create**

### Step 3: Generate OAuth Token
1. Click on the service principal you just created
2. Click **Generate Token** or **OAuth Token**
3. Set expiration (0 = never expires for production, or set to 1 month)
4. Copy the token (starts with `dapi`)

### Step 4: Assign Workspace Permissions (Optional but Recommended)
1. Go to **Workspace Settings**
2. Grant the service principal:
   - **Workspace Admin** (simplest, for production recommend: Jobs Viewer, Clusters Viewer)
   - Or specific permissions: `jobs/read`, `clusters/read`, `directories/read`

### Step 5: Update Airflow Connection
Same as Method 1 Step 4 above.

---

## Benefits of Service Principal Approach

✅ **Workspace-scoped access** - No need for IP allowlisting  
✅ **Fine-grained permissions** - Grant only what Airflow needs  
✅ **Audit trail** - Can track service principal activities separately  
✅ **Production-ready** - Survives employee turnover  
✅ **Automatic token rotation** - Can regenerate without user involvement  
✅ **No IP restrictions apply** - Bypasses network allowlisting  

---

## Testing the Connection

Once updated, run:

```bash
kubectl exec -n airflow airflow-dag-processor-64598fd9f4-j24sj -c dag-processor -- \
  airflow dags test databricks_list_workflows 2025-12-05
```

You should now see:
- ✅ Connection retrieved successfully
- ✅ WorkspaceClient created successfully
- ✅ **Workflows/Jobs listed** (no more "Unauthorized" error)

---

## Troubleshooting

### Still getting "Unauthorized" error?
- Verify the token is correctly set in Airflow connection
- Check the token hasn't expired
- Ensure service principal has workspace permissions (Admin Settings → check Active status)

### How to verify token is working?
```bash
curl -H "Authorization: Bearer <token>" \
  https://adb-5444953219183209.9.azuredatabricks.net/api/2.0/jobs/list
```

If successful, you'll see a JSON list of jobs. If not, you'll get an auth error.

---

## What Airflow DAGs Can Now Access

With a service principal token, your Airflow DAGs can:
- ✅ List jobs
- ✅ Trigger jobs
- ✅ Monitor job runs
- ✅ Read workspace files
- ✅ Submit notebooks
- ✅ Query workspace metadata

**All without needing IP allowlisting!**

---

## Reverting to User PAT (if needed)

If you want to go back to your personal PAT token:
1. Get your personal PAT from Databricks UI (User Settings → Generate New Token)
2. Update Airflow connection with the new PAT token
3. Keep the service principal disabled in case you want to reuse it later
