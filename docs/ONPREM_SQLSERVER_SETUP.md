# On-Premises SQL Server Connection Setup

Configure Airflow to connect to on-premises SQL Server instances for data extraction, loading, and transformations.

## Prerequisites

- SQL Server instance running (on-premises or private network)
- SQL Server username and password
- Network connectivity from AKS to SQL Server (VPN or Private Endpoint)
- pyodbc and ODBC driver installed

## ODBC Driver Installation in Kubernetes

The ODBC drivers are installed automatically in your AKS deployment via the Helm values:

```yaml
extraPipPackages:
  - "pyodbc>=4.0.0"
  - "apache-airflow-providers-odbc>=4.1.0"
  - "apache-airflow-providers-microsoft-mssql>=3.8.0"
```

## Connection Setup in Airflow UI

### Method 1: MSSQL Connection (Recommended)

1. Go to **Admin** → **Connections** → **Create**
2. **Connection ID:** `mssql_onprem`
3. **Connection Type:** `Microsoft SQL Server`
4. **Host:** Your SQL Server address (e.g., `192.168.1.100` or `sql.internal.company.com`)
5. **Database:** Target database name (e.g., `DataWarehouse`)
6. **Login:** SQL Server username
7. **Password:** SQL Server password
8. **Port:** `1433` (or your custom port)
9. **Extra** (optional):
```json
{
  "driver": "ODBC Driver 17 for SQL Server",
  "TrustServerCertificate": "yes"
}
```
10. **Test** and **Save**

### Method 2: ODBC Connection (Alternative)

1. **Connection ID:** `odbc_onprem`
2. **Connection Type:** `ODBC`
3. **Connection String:**
```
Driver={ODBC Driver 17 for SQL Server};Server=sql.company.com;Port=1433;Database=DataWarehouse;Uid=username;Pwd=password;
```

### Method 3: Environment Variables in AKS

Edit `kubernetes/values.yaml`:

```yaml
env:
  - name: AIRFLOW_CONN_MSSQL_ONPREM
    value: "mssql+pyodbc://username:password@192.168.1.100:1433/DataWarehouse?driver=ODBC+Driver+17+for+SQL+Server"
```

## Network Connectivity for On-Premises SQL Server

For Airflow in AKS to reach on-premises SQL Server:

### Option 1: VPN Connection

Configure a site-to-site VPN from Azure to your on-premises network:

```powershell
# Create VPN gateway in Azure
az network local-gateway create `
  --name OnPremisesGateway `
  --resource-group <YOUR_RESOURCE_GROUP> `
  --gateway-ip-address <YOUR_ON_PREM_VPN_PUBLIC_IP> `
  --local-address-prefixes 192.168.0.0/16

# Create VPN connection
az network vpn-connection create `
  --name VPN-Connection `
  --resource-group <YOUR_RESOURCE_GROUP> `
  --vnet-gateway1 <AZURE_VPN_GATEWAY_NAME> `
  --local-gateway2 OnPremisesGateway `
  --connection-type IPsec
```

### Option 2: Azure Private Endpoint

For SQL Server in private data centers:

```powershell
# Create private endpoint for SQL Server
az network private-endpoint create `
  --name sql-server-endpoint `
  --resource-group <YOUR_RESOURCE_GROUP> `
  --vnet <YOUR_VNET> `
  --subnet <YOUR_SUBNET> `
  --private-connection-resource-id /subscriptions/...sqlServers/myserver `
  --connection-name sql-connection
```

### Option 3: Azure Hybrid Connection

For simpler scenarios without VPN:

```powershell
# Create relay namespace
az relay namespace create `
  --resource-group <YOUR_RESOURCE_GROUP> `
  --name <RELAY_NAMESPACE> `
  --location eastus
```

## Common SQL Server Operations in DAGs

### Execute SQL Query

```python
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from airflow import DAG
from datetime import datetime

with DAG(
    'sqlserver_example',
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    query_task = MsSqlOperator(
        task_id='query_data',
        mssql_conn_id='mssql_onprem',
        sql='''
            SELECT TOP 100 
                CustomerID, 
                OrderDate, 
                SUM(Amount) as TotalAmount
            FROM Orders
            WHERE OrderDate >= CAST(GETDATE() - 1 AS DATE)
            GROUP BY CustomerID, OrderDate
        ''',
    )
```

### Execute Stored Procedure

```python
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator

exec_sp_task = MsSqlOperator(
    task_id='execute_stored_proc',
    mssql_conn_id='mssql_onprem',
    sql='EXEC dbo.sp_RefreshProductCatalog',
)
```

### Extract Data to File

```python
import pandas as pd
from airflow.operators.python import PythonOperator
from airflow.models import BaseHook

def extract_data_to_csv(**context):
    """Extract data from SQL Server and save to CSV"""
    from pyodbc import connect
    
    conn_info = BaseHook.get_connection('mssql_onprem')
    
    connection_string = (
        f'Driver={{ODBC Driver 17 for SQL Server}};'
        f'Server={conn_info.host},{conn_info.port or 1433};'
        f'Database={conn_info.schema};'
        f'Uid={conn_info.login};'
        f'Pwd={conn_info.password};'
    )
    
    conn = connect(connection_string)
    df = pd.read_sql('SELECT * FROM dbo.SalesData WHERE date = CAST(GETDATE() AS DATE)', conn)
    df.to_csv('/tmp/sales_data.csv', index=False)
    conn.close()
    
    return '/tmp/sales_data.csv'

extract_task = PythonOperator(
    task_id='extract_data',
    python_callable=extract_data_to_csv,
)
```

### Full ETL Pipeline Example

```python
from airflow import DAG
from airflow.providers.microsoft.mssql.operators.mssql import MsSqlOperator
from airflow.operators.python import PythonOperator
from airflow.providers.microsoft.azure.operators.blob import AzureBlobStorageUploadOperator
from datetime import datetime, timedelta
import pandas as pd
from pyodbc import connect
from airflow.models import BaseHook

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_on_prem_data(**context):
    """Extract data from on-premises SQL Server"""
    conn_info = BaseHook.get_connection('mssql_onprem')
    
    connection_string = (
        f'Driver={{ODBC Driver 17 for SQL Server}};'
        f'Server={conn_info.host},{conn_info.port or 1433};'
        f'Database={conn_info.schema};'
        f'Uid={conn_info.login};'
        f'Pwd={conn_info.password};'
    )
    
    conn = connect(connection_string)
    df = pd.read_sql('SELECT * FROM dbo.SourceTable WHERE status = "Active"', conn)
    
    # Save to local temp file
    output_path = '/tmp/extracted_data.csv'
    df.to_csv(output_path, index=False)
    conn.close()
    
    context['task_instance'].xcom_push(key='extracted_file', value=output_path)
    return output_path

with DAG(
    'onprem_to_azure_etl',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    # Step 1: Extract from on-prem SQL Server
    extract = PythonOperator(
        task_id='extract_from_onprem',
        python_callable=extract_on_prem_data,
    )
    
    # Step 2: Upload to Azure Blob Storage
    upload = AzureBlobStorageUploadOperator(
        task_id='upload_to_azure',
        file_path='{{ task_instance.xcom_pull("extract_from_onprem", key="extracted_file") }}',
        container_name='raw-data',
        blob_name='onprem/extracted_data.csv',
        azure_conn_id='azure_blob_storage_default',
    )
    
    # Step 3: Staging data in SQL Server
    stage_data = MsSqlOperator(
        task_id='stage_data',
        mssql_conn_id='mssql_onprem',
        sql='''
            INSERT INTO dbo.StagingTable
            SELECT * FROM dbo.SourceTable
            WHERE ModifiedDate >= CAST(GETDATE() - 1 AS DATE)
        ''',
    )
    
    # Step 4: Quality checks
    quality_check = MsSqlOperator(
        task_id='quality_check',
        mssql_conn_id='mssql_onprem',
        sql='''
            SELECT COUNT(*) as row_count
            FROM dbo.StagingTable
            WHERE ModifiedDate = CAST(GETDATE() AS DATE)
        ''',
    )
    
    extract >> upload
    extract >> stage_data >> quality_check
```

## Verifying the Connection

### Test from Airflow UI

1. Go to **Admin** → **Connections**
2. Find `mssql_onprem`
3. Click the connection
4. Click **Test** button

### Test from Python

```python
from airflow.models import BaseHook
from pyodbc import connect

def test_sql_connection():
    conn_info = BaseHook.get_connection('mssql_onprem')
    
    connection_string = (
        f'Driver={{ODBC Driver 17 for SQL Server}};'
        f'Server={conn_info.host},{conn_info.port or 1433};'
        f'Database={conn_info.schema};'
        f'Uid={conn_info.login};'
        f'Pwd={conn_info.password};'
    )
    
    try:
        conn = connect(connection_string)
        cursor = conn.cursor()
        cursor.execute('SELECT @@VERSION')
        version = cursor.fetchone()[0]
        print(f"✅ Connected! SQL Server version: {version}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

test_sql_connection()
```

### Test from Kubernetes Pod

```powershell
kubectl exec -it -n airflow deployment/airflow-scheduler -- /bin/bash

python3 << 'EOF'
from airflow.models import BaseHook
from pyodbc import connect

conn_info = BaseHook.get_connection('mssql_onprem')
connection_string = f'Driver={{ODBC Driver 17 for SQL Server}};Server={conn_info.host};Database={conn_info.schema};Uid={conn_info.login};Pwd={conn_info.password};'

try:
    conn = connect(connection_string)
    print("✅ Connection successful!")
    conn.close()
except Exception as e:
    print(f"❌ Failed: {str(e)}")
EOF
```

## Troubleshooting

### Connection Refused

1. Verify SQL Server is running and listening on the specified port
2. Check firewall rules allow traffic from AKS to SQL Server port (default 1433)
3. Verify hostname/IP address is correct
4. Test connectivity from AKS pod:
   ```powershell
   kubectl exec -it -n airflow deployment/airflow-scheduler -- telnet <SQL_SERVER_IP> 1433
   ```

### Authentication Failed

1. Verify username and password are correct
2. Check SQL Server authentication mode (Windows or Mixed)
3. Ensure user has SELECT/INSERT permissions
4. Verify credentials in connection settings

### ODBC Driver Not Found

```
ERROR: ('01000', "[01000] [unixODBC][Driver Manager] Can't open lib 'ODBC Driver 17 for SQL Server'"
```

The driver should install automatically. If not, rebuild your AKS deployment:

```powershell
helm upgrade airflow apache-airflow/airflow -n airflow -f kubernetes/values.yaml
```

### Network Connectivity Issues

1. Verify VPN or Private Endpoint is properly configured
2. Check network security groups (NSGs) allow traffic
3. Verify DNS resolution:
   ```powershell
   kubectl exec -n airflow deployment/airflow-scheduler -- nslookup <SQL_SERVER_HOST>
   ```

### Slow Queries

1. Check SQL Server performance
2. Add indexes to frequently queried columns
3. Optimize the SELECT statement
4. Consider using database views for complex queries

## Performance Tips

1. **Batch Operations:** Combine multiple small queries into fewer larger queries
2. **Pagination:** Use OFFSET/FETCH for large result sets
3. **Indexing:** Ensure proper indexes exist on filtered columns
4. **Connection Pooling:** Enable connection pooling in pyodbc
5. **Query Optimization:** Use execution plans to identify bottlenecks

## Security Best Practices

1. **Never hardcode credentials:** Use Airflow Connections or Azure Key Vault
2. **Encrypt connections:** Always use encrypted SQL Server connections
3. **Limit permissions:** Create dedicated service accounts with minimal required permissions
4. **Network isolation:** Restrict SQL Server access to authorized networks only
5. **Audit logging:** Enable SQL Server audit logging for compliance

## See Also

- [Apache Airflow MSSQL Provider](https://airflow.apache.org/docs/apache-airflow-providers-microsoft-mssql/stable/)
- [Apache Airflow ODBC Provider](https://airflow.apache.org/docs/apache-airflow-providers-odbc/stable/)
- [SQL Server Documentation](https://docs.microsoft.com/en-us/sql/sql-server/)
- [pyodbc Documentation](https://github.com/mkleehammer/pyodbc/wiki)
- [Airflow Connections](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
