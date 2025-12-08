"""
SQL Server to Azure Data Lake ETL
==================================
Extract data from on-premise SQL Server and load to Azure Data Lake Storage (ADLS).

What you need:
1. SQL Server connection 'mssql_onprem' configured in Airflow
2. Azure Blob Storage connection 'azure_blob_default' configured
3. Source table in SQL Server
4. ADLS container and path

Connection setup in Airflow UI:

SQL Server (mssql_onprem):
- Type: Microsoft SQL Server
- Host: your-sql-server.domain.com
- Schema: YourDatabase
- Login: your_username
- Password: your_password
- Port: 1433

Azure Blob Storage (azure_blob_default):
- Type: Azure Blob Storage
- Login: storage_account_name
- Password: storage_account_key (or SAS token)
- Extra: {"connection_string": "DefaultEndpointsProtocol=https;AccountName=..."}
"""
from airflow import DAG
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.microsoft.azure.hooks.wasb import WasbHook
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import io

# Configuration
MSSQL_CONN_ID = 'mssql_onprem'
AZURE_CONN_ID = 'azure_blob_default'

# SQL Server settings
SOURCE_TABLE = '[dbo].[orders]'  # Update with your table name
SOURCE_QUERY = f"""
SELECT 
    order_id,
    customer_id,
    customer_name,
    order_date,
    order_amount,
    status,
    created_at,
    updated_at
FROM {SOURCE_TABLE}
WHERE CAST(updated_at AS DATE) >= CAST(DATEADD(day, -1, GETDATE()) AS DATE)
ORDER BY order_id;
"""

# Azure ADLS settings
CONTAINER_NAME = 'airflow'  # Your ADLS container
BLOB_PREFIX = 'sqlserver-data'  # Folder path in ADLS
FILE_FORMAT = 'parquet'  # Options: 'parquet', 'csv', 'json'

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='mssql_to_adls_etl',
    default_args=default_args,
    description='Extract from SQL Server and load to Azure Data Lake Storage',
    schedule='0 2 * * *',  # Daily at 2 AM
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['mssql', 'azure', 'adls', 'etl'],
) as dag:
    
    def extract_from_sqlserver(**context):
        """Extract data from SQL Server"""
        hook = MsSqlHook(mssql_conn_id=MSSQL_CONN_ID)
        
        print(f"Connecting to SQL Server...")
        print(f"Executing query: {SOURCE_QUERY}")
        
        # Extract data as pandas DataFrame
        df = hook.get_pandas_df(SOURCE_QUERY)
        
        row_count = len(df)
        print(f"✅ Extracted {row_count} rows from SQL Server")
        
        if row_count == 0:
            print("⚠️  No data to extract")
            return {'status': 'no_data', 'row_count': 0}
        
        # Display sample data
        print("\n📊 Sample data (first 5 rows):")
        print(df.head())
        
        print(f"\n📈 Data summary:")
        print(f"  Columns: {list(df.columns)}")
        print(f"  Data types:\n{df.dtypes}")
        
        # Store DataFrame in XCom for next task
        context['task_instance'].xcom_push(key='dataframe', value=df.to_json(orient='split', date_format='iso'))
        context['task_instance'].xcom_push(key='row_count', value=row_count)
        
        return {
            'status': 'extracted',
            'row_count': row_count,
            'columns': list(df.columns)
        }
    
    def load_to_adls(**context):
        """Load data to Azure Data Lake Storage"""
        # Get DataFrame from previous task
        df_json = context['task_instance'].xcom_pull(
            task_ids='extract_from_sqlserver',
            key='dataframe'
        )
        
        if not df_json:
            print("No data to load")
            return {'status': 'no_data'}
        
        # Convert back to DataFrame
        df = pd.read_json(io.StringIO(df_json), orient='split')
        
        row_count = len(df)
        print(f"Loading {row_count} rows to ADLS...")
        
        # Get Azure connection
        azure_hook = WasbHook(wasb_conn_id=AZURE_CONN_ID)
        
        # Generate filename with timestamp
        execution_date = context['ds']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if FILE_FORMAT == 'parquet':
            filename = f"{BLOB_PREFIX}/orders_{execution_date}_{timestamp}.parquet"
            # Convert to parquet bytes
            buffer = io.BytesIO()
            df.to_parquet(buffer, index=False, engine='pyarrow')
            data = buffer.getvalue()
            
        elif FILE_FORMAT == 'csv':
            filename = f"{BLOB_PREFIX}/orders_{execution_date}_{timestamp}.csv"
            data = df.to_csv(index=False).encode('utf-8')
            
        elif FILE_FORMAT == 'json':
            filename = f"{BLOB_PREFIX}/orders_{execution_date}_{timestamp}.json"
            data = df.to_json(orient='records', date_format='iso').encode('utf-8')
        
        else:
            raise ValueError(f"Unsupported file format: {FILE_FORMAT}")
        
        print(f"Uploading to: {CONTAINER_NAME}/{filename}")
        print(f"File size: {len(data):,} bytes")
        
        # Upload to ADLS
        azure_hook.load_bytes(
            data=data,
            container_name=CONTAINER_NAME,
            blob_name=filename,
            overwrite=True
        )
        
        print(f"✅ Successfully uploaded to ADLS")
        print(f"   Container: {CONTAINER_NAME}")
        print(f"   Path: {filename}")
        print(f"   Rows: {row_count}")
        print(f"   Format: {FILE_FORMAT}")
        
        # Store upload info
        context['task_instance'].xcom_push(key='blob_path', value=filename)
        context['task_instance'].xcom_push(key='container', value=CONTAINER_NAME)
        
        return {
            'status': 'loaded',
            'container': CONTAINER_NAME,
            'blob_path': filename,
            'row_count': row_count,
            'file_size_bytes': len(data),
            'format': FILE_FORMAT
        }
    
    def validate_upload(**context):
        """Validate that file was uploaded successfully"""
        container = context['task_instance'].xcom_pull(
            task_ids='load_to_adls',
            key='container'
        )
        blob_path = context['task_instance'].xcom_pull(
            task_ids='load_to_adls',
            key='blob_path'
        )
        row_count = context['task_instance'].xcom_pull(
            task_ids='extract_from_sqlserver',
            key='row_count'
        )
        
        if not blob_path:
            raise ValueError("No blob path found - upload may have failed")
        
        # Check if blob exists
        azure_hook = WasbHook(wasb_conn_id=AZURE_CONN_ID)
        
        exists = azure_hook.check_for_blob(
            container_name=container,
            blob_name=blob_path
        )
        
        if exists:
            # Get blob properties
            blob_client = azure_hook.get_blobs_list(
                container_name=container,
                prefix=blob_path
            )
            
            print("✅ Validation successful!")
            print(f"   File exists in ADLS: {container}/{blob_path}")
            print(f"   Rows transferred: {row_count}")
            
            return {
                'status': 'validated',
                'blob_exists': True,
                'container': container,
                'blob_path': blob_path,
                'rows_transferred': row_count
            }
        else:
            raise ValueError(f"Blob not found in ADLS: {container}/{blob_path}")
    
    # Task definitions
    extract = PythonOperator(
        task_id='extract_from_sqlserver',
        python_callable=extract_from_sqlserver,
    )
    
    load = PythonOperator(
        task_id='load_to_adls',
        python_callable=load_to_adls,
    )
    
    validate = PythonOperator(
        task_id='validate_upload',
        python_callable=validate_upload,
    )
    
    # Pipeline flow
    extract >> load >> validate
