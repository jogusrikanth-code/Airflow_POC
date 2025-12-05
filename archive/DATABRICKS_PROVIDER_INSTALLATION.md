# Databricks Provider Installation Guide

This document explains how to install and configure the Apache Airflow Databricks provider for permanent use.

## Quick Temporary Installation

For immediate use (temporary, lost on pod restart):

```powershell
.\scripts\install-databricks-provider.ps1
```

Then refresh your Airflow UI to see Databricks in the connection type dropdown.

---

## Permanent Installation Methods

### Option 1: Custom Docker Image (Recommended for Production)

Build a custom Airflow image with the provider pre-installed:

1. Create a `Dockerfile`:

```dockerfile
FROM apache/airflow:3.0.2-python3.11

# Install Databricks provider
RUN pip install --no-cache-dir apache-airflow-providers-databricks==7.8.0
```

2. Build and push the image:

```powershell
docker build -t your-registry/airflow-with-databricks:3.0.2 .
docker push your-registry/airflow-with-databricks:3.0.2
```

3. Update `kubernetes/helm-values.yaml`:

```yaml
images:
  airflow:
    repository: your-registry/airflow-with-databricks
    tag: 3.0.2
    pullPolicy: IfNotPresent
```

4. Upgrade the deployment:

```powershell
helm upgrade airflow apache-airflow/airflow -n airflow -f kubernetes/helm-values.yaml
```

### Option 2: Helm Chart extraPipPackages (Simpler but slower startup)

**Note:** This option currently has compatibility issues with the existing deployment configuration. Use Option 1 or 3 instead.

Add to `kubernetes/helm-values.yaml`:

```yaml
extraPipPackages:
  - "apache-airflow-providers-databricks==7.8.0"
```

Then upgrade:

```powershell
helm upgrade airflow apache-airflow/airflow -n airflow -f kubernetes/helm-values.yaml
```

**Caveats:**
- Increases pod startup time (provider installs on every pod start)
- Your Helm values must match your current deployment configuration exactly
- Requires alignment of airflowVersion, executor, image tag, and database connection format

### Option 3: Init Container (Compromise)

Add an init container to install the provider before the main container starts.

Create a patch file `kubernetes/databricks-provider-patch.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: airflow-api-server
  namespace: airflow
spec:
  template:
    spec:
      initContainers:
      - name: install-databricks-provider
        image: apache/airflow:3.0.2-python3.11
        command:
        - /bin/bash
        - -c
        - |
          pip install --target=/providers apache-airflow-providers-databricks==7.8.0
        volumeMounts:
        - name: providers
          mountPath: /providers
      containers:
      - name: api-server
        env:
        - name: PYTHONPATH
          value: "/providers:$PYTHONPATH"
        volumeMounts:
        - name: providers
          mountPath: /providers
      volumes:
      - name: providers
        emptyDir: {}
```

Apply the patch to each deployment (api-server, scheduler, dag-processor):

```powershell
kubectl patch deployment airflow-api-server -n airflow --patch-file kubernetes/databricks-provider-patch.yaml
kubectl patch deployment airflow-scheduler -n airflow --patch-file kubernetes/databricks-provider-patch.yaml
kubectl patch deployment airflow-dag-processor -n airflow --patch-file kubernetes/databricks-provider-patch.yaml
```

---

## Verification

After permanent installation, verify the provider is available:

```powershell
kubectl exec -n airflow deployment/airflow-api-server -- airflow providers list | Select-String "databricks"
```

Expected output:
```
apache-airflow-providers-databricks | Databricks https://databricks.com/ | 7.8.0
```

---

## Configuring Databricks Connection

Once the provider is installed, add a Databricks connection in the Airflow UI:

1. Go to **Admin** → **Connections** → **Add Connection**
2. Select **Connection Type**: Databricks
3. Fill in the details:
   - **Connection Id**: `databricks_default`
   - **Host**: Your Databricks workspace URL (e.g., `https://adb-1234567890123456.7.azuredatabricks.net`)
   - **Extra**: JSON configuration
   
   ```json
   {
     "token": "your-databricks-personal-access-token",
     "host": "https://adb-1234567890123456.7.azuredatabricks.net"
   }
   ```

4. Test the connection and save

---

## Using Databricks in DAGs

Example DAG using the Databricks provider:

```python
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from datetime import datetime

with DAG(
    dag_id="databricks_example",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:
    
    run_notebook = DatabricksRunNowOperator(
        task_id="run_databricks_notebook",
        databricks_conn_id="databricks_default",
        job_id="your-job-id",  # Your Databricks job ID
    )
```

---

## Troubleshooting

### Provider not showing in UI dropdown

1. Verify provider is installed in API server pod:
   ```powershell
   kubectl exec -n airflow deployment/airflow-api-server -- pip list | Select-String "databricks"
   ```

2. Restart the API server:
   ```powershell
   kubectl rollout restart deployment/airflow-api-server -n airflow
   ```

3. Clear browser cache and hard refresh (Ctrl+Shift+R)

### Connection test fails

1. Verify your Databricks token is valid
2. Check the host URL format (must include `https://`)
3. Verify network connectivity from AKS to Databricks workspace

---

## Current Deployment Status

Your current deployment uses:
- **Airflow Version**: 3.0.2
- **Executor**: KubernetesExecutor
- **Image**: apache/airflow:3.0.2-python3.11
- **Namespace**: airflow

The provider has been temporarily installed and is currently available in your running pods. It will be lost if pods restart. Choose one of the permanent installation methods above for production use.

---

## Recommended Approach

For your POC environment: **Use the temporary installation script** (`install-databricks-provider.ps1`) whenever needed.

For production: **Build a custom Docker image** (Option 1) with all required providers baked in.
