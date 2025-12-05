# PowerBI Connection Setup

Configure Airflow to connect to PowerBI for dataset refresh, report management, and data updates.

## Prerequisites

- PowerBI Premium capacity or workspace
- Azure Active Directory (AAD) application registered
- Service principal with PowerBI admin permissions
- Client ID and Client Secret

## Registering an Azure AD Application for PowerBI

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** → **App registrations** → **New registration**
3. **Name:** `AirflowPowerBI` (or your preferred name)
4. **Supported account types:** Accounts in this organizational directory only
5. Click **Register**

### Grant API Permissions

1. In the app registration, go to **API permissions**
2. Click **Add a permission** → **Microsoft Graph**
3. Select **Application permissions**
4. Search for and add:
   - `Directory.Read.All`
   - `User.Read.All`
5. Go to **Power BI Service API**
6. Select **Application permissions**
7. Add:
   - `Dataset.Read.All`
   - `Dataset.ReadWrite.All`
   - `Report.Read.All`
   - `Workspace.Read.All`
8. Click **Grant admin consent**

### Create Client Secret

1. In the app registration, go to **Certificates & secrets**
2. Click **New client secret**
3. Set expiration to desired period
4. Copy the **Value** (Secret, not ID)
5. Save this securely - we'll use it in Airflow

## Connection Setup in Airflow UI

### Method 1: Using Generic HTTP Connection with Extras

1. Go to **Admin** → **Connections** → **Create**
2. **Connection ID:** `powerbi_default`
3. **Connection Type:** `HTTP`
4. **Host:** `https://app.powerbi.com`
5. **Login:** Your Azure AD application Client ID
6. **Password:** Your Client Secret
7. **Extra** JSON:
```json
{
  "tenant_id": "your-tenant-id",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "scope": "https://analysis.windows.net/.default"
}
```
8. **Test** and **Save**

### Method 2: Using MSSQL Connection (Alternative)

Since PowerBI often connects via MSSQL analysis services:

1. **Connection ID:** `powerbi_mssql`
2. **Connection Type:** `MSSQL`
3. **Host:** Your PowerBI analysis services endpoint
4. **Database:** Your dataset name
5. **Login:** Service principal ID
6. **Password:** Service principal secret

## Common PowerBI Operations in DAGs

### Refresh PowerBI Dataset

```python
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def refresh_powerbi_dataset(**context):
    """Refresh a PowerBI dataset"""
    conn = BaseHook.get_connection('powerbi_default')
    tenant_id = conn.extra_dejson.get('tenant_id')
    client_id = conn.extra_dejson.get('client_id')
    client_secret = conn.extra_dejson.get('client_secret')
    
    # Get access token
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/.default'
    }
    auth_response = requests.post(auth_url, data=auth_data)
    token = auth_response.json()['access_token']
    
    # Refresh dataset
    headers = {'Authorization': f'Bearer {token}'}
    dataset_id = 'your-dataset-id'
    group_id = 'your-workspace-id'
    
    refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/refreshes"
    refresh_response = requests.post(refresh_url, headers=headers, json={})
    
    return refresh_response.status_code

with DAG(
    'powerbi_refresh_dag',
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    refresh_task = PythonOperator(
        task_id='refresh_powerbi_dataset',
        python_callable=refresh_powerbi_dataset,
    )
```

### Trigger Report Refresh via SQL

```python
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from airflow import DAG
from datetime import datetime

with DAG(
    'powerbi_sql_refresh',
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    # Update the underlying dataset table
    update_data_task = MsSqlOperator(
        task_id='update_powerbi_data',
        mssql_conn_id='powerbi_mssql',
        sql='''
            INSERT INTO dbo.SalesData (Date, Amount, Region)
            SELECT CAST(GETDATE() AS DATE), SUM(Amount), Region
            FROM SourceData
            GROUP BY Region
        ''',
    )
```

### Full PowerBI Integration DAG

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from datetime import datetime, timedelta
import requests
from airflow.models import BaseHook

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def get_powerbi_token():
    """Get access token for PowerBI API"""
    conn = BaseHook.get_connection('powerbi_default')
    tenant_id = conn.extra_dejson.get('tenant_id')
    client_id = conn.extra_dejson.get('client_id')
    client_secret = conn.extra_dejson.get('client_secret')
    
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/.default'
    }
    response = requests.post(auth_url, data=auth_data)
    return response.json()['access_token']

def refresh_powerbi_dataset(dataset_id, group_id):
    """Refresh a PowerBI dataset"""
    token = get_powerbi_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/refreshes"
    response = requests.post(url, headers=headers, json={})
    
    if response.status_code == 202:
        print(f"Dataset {dataset_id} refresh triggered successfully")
        return True
    else:
        raise Exception(f"Failed to refresh dataset: {response.text}")

with DAG(
    'powerbi_etl_pipeline',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    # Step 1: Update underlying data
    update_source = MsSqlOperator(
        task_id='update_source_data',
        mssql_conn_id='powerbi_mssql',
        sql='''
            EXEC sp_RefreshSourceData
        ''',
    )
    
    # Step 2: Refresh PowerBI dataset
    refresh_dataset = PythonOperator(
        task_id='refresh_powerbi',
        python_callable=refresh_powerbi_dataset,
        op_kwargs={
            'dataset_id': 'your-dataset-id',
            'group_id': 'your-workspace-id'
        },
    )
    
    update_source >> refresh_dataset
```

## Finding Dataset and Group IDs

### Get All Datasets

```python
def list_powerbi_datasets():
    token = get_powerbi_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    url = "https://api.powerbi.com/v1.0/myorg/datasets"
    response = requests.get(url, headers=headers)
    
    datasets = response.json()['value']
    for dataset in datasets:
        print(f"Dataset: {dataset['name']} | ID: {dataset['id']}")

list_powerbi_datasets()
```

### Get All Workspaces

```python
def list_powerbi_workspaces():
    token = get_powerbi_token()
    headers = {'Authorization': f'Bearer {token}'}
    
    url = "https://api.powerbi.com/v1.0/myorg/groups"
    response = requests.get(url, headers=headers)
    
    groups = response.json()['value']
    for group in groups:
        print(f"Workspace: {group['name']} | ID: {group['id']}")

list_powerbi_workspaces()
```

## Verifying the Connection

### Test from Python

```python
import requests
from airflow.models import BaseHook

def test_powerbi():
    conn = BaseHook.get_connection('powerbi_default')
    print(f"Host: {conn.host}")
    print(f"Extra: {conn.extra_dejson}")
    
    # Try to get token
    tenant_id = conn.extra_dejson.get('tenant_id')
    client_id = conn.extra_dejson.get('client_id')
    client_secret = conn.extra_dejson.get('client_secret')
    
    auth_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/.default'
    }
    response = requests.post(auth_url, data=auth_data)
    
    if response.status_code == 200:
        print("✅ Connection successful!")
        return True
    else:
        print(f"❌ Connection failed: {response.text}")
        return False

test_powerbi()
```

## Troubleshooting

### 401 Unauthorized

1. Verify client ID and secret are correct
2. Check that credentials haven't expired
3. Verify service principal has proper permissions in PowerBI

### 403 Forbidden

1. Ensure service principal has admin role in PowerBI
2. Check that the workspace/dataset IDs are correct
3. Verify the service principal can access the specific dataset

### Dataset Not Found

1. Verify the dataset ID is correct (use list_powerbi_datasets())
2. Confirm the service principal has access to that dataset
3. Check workspace/group ID matches

## PowerBI API Limits

- **API Calls:** 120 requests per minute (per user/service principal)
- **Concurrent Refreshes:** Limited by Premium capacity
- **Max file size:** 1 GB for import

## See Also

- [PowerBI REST API Documentation](https://docs.microsoft.com/en-us/rest/api/power-bi/)
- [PowerBI Embedded API Reference](https://docs.microsoft.com/en-us/rest/api/power-bi/datasets)
- [Service Principal in PowerBI](https://docs.microsoft.com/en-us/power-bi/developer/embedded/embed-service-principal)
- [Apache Airflow MSSQL Provider](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-mssql/stable/)
