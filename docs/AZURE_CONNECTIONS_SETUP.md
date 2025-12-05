# Azure Connection Setup

Configure Airflow to connect to Azure services for data transfer, monitoring, and integration.

## Prerequisites

- Azure storage account created
- Service principal with appropriate permissions
- Connection string or access keys

## Connection Types in Airflow UI

### 1. Azure Blob Storage Connection

**In Airflow UI:**
1. Go to **Admin** → **Connections** → **Create**
2. **Connection ID:** `azure_blob_storage_default`
3. **Connection Type:** `Azure Blob Storage`
4. **Account Name:** Your storage account name (e.g., `mystorageaccount`)
5. **Account Key:** Your storage account key
6. **Container Name:** (optional) Default container to use
7. **Test** and **Save**

**In DAG Code:**
```python
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageUploadOperator
from airflow import DAG
from datetime import datetime

with DAG('azure_blob_example', start_date=datetime(2025, 1, 1)) as dag:
    upload_task = AzureBlobStorageUploadOperator(
        task_id='upload_blob',
        file_path='/local/path/file.csv',
        container_name='my-container',
        blob_name='uploaded-file.csv',
        azure_conn_id='azure_blob_storage_default',
    )
```

### 2. Azure Data Lake Gen2 (ADLS Gen2) Connection

**In Airflow UI:**
1. Go to **Admin** → **Connections** → **Create**
2. **Connection ID:** `adls_default`
3. **Connection Type:** `Azure Data Lake`
4. **Account Name:** Your ADLS account name
5. **Account Key** or **Connection String**
6. **Test** and **Save**

### 3. Azure Service Principal Connection

For programmatic access and managed identity scenarios:

**In Airflow UI:**
1. **Connection ID:** `azure_sp_default`
2. **Connection Type:** `Azure Blob Storage`
3. **Connection String** format:
```
DefaultEndpointsProtocol=https;AccountName=<account_name>;AccountKey=<account_key>;EndpointSuffix=core.windows.net
```

## Environment Variables (Alternative)

Instead of using the UI, set environment variables in your AKS deployment:

Edit `kubernetes/values.yaml`:

```yaml
env:
  - name: AIRFLOW_CONN_AZURE_BLOB_STORAGE_DEFAULT
    value: "wasbs://<container>@<account_name>.blob.core.windows.net?connection_string=DefaultEndpointsProtocol=https;AccountName=<account_name>;AccountKey=<key>;EndpointSuffix=core.windows.net"
```

## Using Azure Key Vault (Recommended for Production)

Store credentials in Azure Key Vault and reference them:

```python
from airflow.providers.microsoft.azure.secrets.key_vault import AzureKeyVaultBackend
from airflow.models import Variable

# Retrieve connection from Key Vault
connection = Variable.get("my_azure_connection")
```

## Common Azure Operations in DAGs

### Upload File to Blob Storage

```python
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageUploadOperator

upload_task = AzureBlobStorageUploadOperator(
    task_id='upload_file',
    file_path='/local/file.parquet',
    container_name='data-container',
    blob_name='raw/file.parquet',
    azure_conn_id='azure_blob_storage_default',
)
```

### Download File from Blob Storage

```python
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageDownloadOperator

download_task = AzureBlobStorageDownloadOperator(
    task_id='download_file',
    container_name='data-container',
    blob_name='processed/file.parquet',
    file_path='/local/downloads/file.parquet',
    azure_conn_id='azure_blob_storage_default',
)
```

### Copy Between Containers

```python
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageCopyOperator

copy_task = AzureBlobStorageCopyOperator(
    task_id='copy_blob',
    src_container='source-container',
    src_blob='file.csv',
    dest_container='dest-container',
    dest_blob='archive/file.csv',
    azure_conn_id='azure_blob_storage_default',
)
```

## Testing Connectivity

Verify your connection works:

```powershell
# SSH into API server pod
kubectl exec -it -n airflow deployment/airflow-api-server -- /bin/bash

# Test connection in Python
python3 << 'EOF'
from airflow.models import Connection
from airflow.models.variable import Variable

# List all connections
import airflow.utils.db as db
session = db.create_default_conn_if_not_exists()
conns = session.query(Connection).all()
for conn in conns:
    if 'azure' in conn.conn_id.lower():
        print(f"Found: {conn.conn_id}")
EOF
```

## Troubleshooting

### Connection Not Appearing in UI

1. Verify the provider is installed:
   ```powershell
   kubectl exec -n airflow deployment/airflow-api-server -- pip list | Select-String "azure"
   ```

2. Restart the API server:
   ```powershell
   kubectl rollout restart deployment/airflow-api-server -n airflow
   ```

3. Clear browser cache and refresh

### Authentication Failures

1. Verify credentials are correct
2. Check storage account firewall settings (allow Kubernetes cluster IP)
3. Verify service principal has appropriate RBAC roles:
   - `Storage Blob Data Contributor` for write access
   - `Storage Blob Data Reader` for read-only access

### Network Connectivity

If running on-premises, ensure:
- Kubernetes cluster can reach Azure storage endpoints
- Network policies don't block outbound HTTPS to `*.blob.core.windows.net`
- Proxy settings configured if needed

## See Also

- [Apache Airflow Microsoft Azure Provider](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-azure/stable/index.html)
- [Azure Storage Documentation](https://docs.microsoft.com/en-us/azure/storage/)
- [Airflow Connections Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
