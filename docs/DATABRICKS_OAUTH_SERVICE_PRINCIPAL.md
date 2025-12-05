# Databricks Service Principal with OAuth Client ID & Secret

## What You Have
After creating a service principal with "Generate Secret", you'll get:
- **Application ID** (Client ID): `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`
- **Secret Value**: `abc123XYZ...` (one-time display)
- **Service Principal Object ID**: `12345678-abcd-1234-efgh-567890abcdef`

This is **OAuth 2.0 Client Credentials** authentication - more secure than PAT tokens.

---

## Step 1: Save Your Service Principal Details

When you click "Generate Secret" in Databricks, save these immediately:

```
Application (Client) ID: <copy this>
Secret Value: <copy this - shown only once!>
Tenant ID (if shown): <copy this>
```

**Example**:
```
Application ID: a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6
Secret Value: dJH8Q~abcdefghijklmnopqrstuvwxyz1234567890
Tenant ID: 12345678-1234-1234-1234-123456789012
```

---

## Step 2: Update Airflow Connection with OAuth Credentials

### Option A: Via Airflow UI (Recommended)

1. **Port forward to Airflow**:
   ```powershell
   kubectl port-forward -n airflow svc/airflow-webserver 8080:8080
   ```

2. **Open browser**: `http://localhost:8080`

3. **Go to Connections**:
   - Admin → Connections → Search "databricks_default" → Edit

4. **Configure OAuth connection**:
   ```
   Connection ID: databricks_default
   Connection Type: databricks
   Host: https://adb-5444953219183209.9.azuredatabricks.net
   Login: <Application/Client ID>
   Password: <Secret Value>
   Extra: {"use_azure_cli": false, "auth_type": "oauth-m2m"}
   ```

5. **Click Save** → **Test Connection**

### Option B: Via Kubernetes Secret (More Secure)

Create a Kubernetes secret with OAuth credentials:

```powershell
# Create secret with service principal credentials
kubectl create secret generic databricks-sp-oauth `
  -n airflow `
  --from-literal=client-id='<YOUR_APPLICATION_ID>' `
  --from-literal=client-secret='<YOUR_SECRET_VALUE>' `
  --dry-run=client -o yaml | kubectl apply -f -
```

Then update the connection:

```powershell
kubectl exec -n airflow airflow-webserver-* -c webserver -- `
  airflow connections upsert databricks_default `
  --conn-type databricks `
  --conn-host 'https://adb-5444953219183209.9.azuredatabricks.net' `
  --conn-login '<YOUR_APPLICATION_ID>' `
  --conn-password '<YOUR_SECRET_VALUE>' `
  --conn-extra '{"auth_type": "oauth-m2m", "use_azure_cli": false}'
```

### Option C: Using Environment Variables

Update your `kubernetes/values.yaml` to include the secret:

```yaml
env:
  - name: AIRFLOW_CONN_DATABRICKS_DEFAULT
    value: "databricks://<CLIENT_ID>:<SECRET_VALUE>@adb-5444953219183209.9.azuredatabricks.net?auth_type=oauth-m2m"
```

Then upgrade Airflow:
```powershell
helm upgrade airflow apache-airflow/airflow -n airflow -f kubernetes/values.yaml
```

---

## Step 3: Verify Connection Works

### Test 1: Basic Connection Check
```powershell
kubectl exec -n airflow airflow-dag-processor-64598fd9f4-j24sj -c dag-processor -- python3 -c "
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection('databricks_default')
print(f'✅ Host: {conn.host}')
print(f'✅ Client ID: {conn.login[:20]}...' if conn.login else '❌ No client ID')
print(f'✅ Secret present: {\"Yes\" if conn.password else \"No\"}')
print(f'✅ Extra config: {conn.extra}')
"
```

### Test 2: Test OAuth Authentication
```powershell
kubectl exec -n airflow airflow-dag-processor-64598fd9f4-j24sj -c dag-processor -- python3 -c "
from databricks.sdk import WorkspaceClient
from databricks.sdk.oauth import ClientCredentials
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection('databricks_default')

# Create client with OAuth
client = WorkspaceClient(
    host=conn.host,
    client_id=conn.login,
    client_secret=conn.password
)

print('✅ OAuth WorkspaceClient created successfully')
print(f'✅ Workspace: {conn.host}')
"
```

### Test 3: Run the List Workflows DAG
```powershell
kubectl exec -n airflow airflow-dag-processor-64598fd9f4-j24sj -c dag-processor -- \
  airflow dags test databricks_list_workflows 2025-12-05
```

---

## Update the DAG to Use OAuth (If Needed)

If your DAG needs to explicitly use OAuth, update `databricks_list_workflows.py`:

```python
def list_workflows(**context):
    from databricks.sdk import WorkspaceClient
    from airflow.hooks.base import BaseHook
    
    conn = BaseHook.get_connection('databricks_default')
    
    # OAuth authentication
    client = WorkspaceClient(
        host=conn.host,
        client_id=conn.login,      # Application/Client ID
        client_secret=conn.password  # Secret Value
    )
    
    # Rest of your code...
    jobs = list(client.jobs.list())
```

---

## Connection String Format

The complete connection string format for OAuth:

```
databricks://<CLIENT_ID>:<SECRET_VALUE>@<WORKSPACE_HOST>?auth_type=oauth-m2m
```

**Example**:
```
databricks://a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6:dJH8Q~abc123xyz@adb-5444953219183209.9.azuredatabricks.net?auth_type=oauth-m2m
```

**Fields**:
- `CLIENT_ID`: Application/Client ID from service principal
- `SECRET_VALUE`: Secret value (generated once, copy immediately)
- `WORKSPACE_HOST`: Your Databricks workspace URL
- `auth_type=oauth-m2m`: Machine-to-machine OAuth authentication

---

## Advantages of OAuth vs PAT Token

✅ **More secure**: Follows OAuth 2.0 standard  
✅ **Automatic token refresh**: SDK handles token lifecycle  
✅ **Better audit trail**: Separate service principal identity  
✅ **Workspace-scoped**: Permissions limited to workspace  
✅ **No expiration**: Secret doesn't expire (unless rotated)  
✅ **Enterprise-ready**: Recommended for production environments  

---

## Troubleshooting

### Issue: "Invalid client credentials"
**Solution**: Verify client ID and secret are correct
```powershell
# Test credentials directly
curl -X POST https://adb-5444953219183209.9.azuredatabricks.net/oidc/v1/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=<CLIENT_ID>&client_secret=<SECRET>&scope=all-apis"
```

### Issue: "Unauthorized network access" persists
**Solution**: OAuth also requires IP allowlisting bypass
- Ask admin to add AKS IP to allowlist, OR
- Service principal should bypass restrictions (if configured properly)

### Issue: Connection test fails with "auth_type not recognized"
**Solution**: Update `apache-airflow-providers-databricks` package
```powershell
kubectl exec -n airflow airflow-worker-0 -c worker -- \
  pip install --upgrade apache-airflow-providers-databricks
```

---

## What Information to Share with Me

Once you've created the service principal with secret, share:

1. **Application/Client ID**: `a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6`
2. **Secret Value**: `dJH8Q~abc...` (the secret itself)
3. **Workspace URL**: `https://adb-5444953219183209.9.azuredatabricks.net` (I already have this)

Then I'll update the Airflow connection for you!

---

## Summary

1. ✅ Create service principal in Databricks
2. ✅ Click **"Generate Secret"** (not "Generate Token")
3. ✅ Copy **Application ID** and **Secret Value** immediately
4. ✅ Update Airflow connection:
   - **Login**: Application/Client ID
   - **Password**: Secret Value
   - **Extra**: `{"auth_type": "oauth-m2m"}`
5. ✅ Test the connection
6. ✅ Run DAGs successfully!
