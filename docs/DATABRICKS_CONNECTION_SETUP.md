# Databricks Connection Setup

Configure Airflow to connect to Databricks for running jobs, queries, and notebooks.

## Prerequisites

- Databricks workspace created
- Personal access token generated
- Databricks workspace URL (e.g., `https://adb-1234567890123456.7.azuredatabricks.net`)

## Generating a Databricks Personal Access Token

1. In your Databricks workspace, click your **User Profile** icon (top right)
2. Select **User Settings**
3. Go to **Access Tokens** tab
4. Click **Generate New Token**
5. Set an expiration period
6. Copy the token (shown once)
7. Save it securely (we'll use it in the connection)

## Connection Setup in Airflow UI

### Method 1: Using Airflow UI (Recommended)

1. Go to **Admin** → **Connections** → **Create**
2. **Connection ID:** `databricks_default`
3. **Connection Type:** `Databricks`
4. **Host:** Your workspace URL (e.g., `https://adb-1234567890123456.7.azuredatabricks.net`)
5. **Token:** Your personal access token from above
6. **Port:** (leave empty or 443)
7. **Test** and **Save**

### Method 2: Using Connection String

In Airflow UI, under **Extra** JSON:

```json
{
  "token": "dapi1234567890abcdef",
  "host": "https://adb-1234567890123456.7.azuredatabricks.net",
  "use_ssl": true
}
```

### Method 3: Environment Variable in AKS

Edit `kubernetes/values.yaml`:

```yaml
env:
  - name: AIRFLOW_CONN_DATABRICKS_DEFAULT
    value: "databricks://<token>@<workspace-url>?use_ssl=true"
```

## Common Databricks Operations in DAGs

### Run a Databricks Job

```python
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow import DAG
from datetime import datetime

with DAG(
    'databricks_job_example',
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False
) as dag:
    
    run_job = DatabricksRunNowOperator(
        task_id='run_databricks_job',
        job_id='123456789',  # Your Databricks job ID
        databricks_conn_id='databricks_default',
    )
```

### Run a Databricks Notebook

```python
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

run_notebook = DatabricksRunNowOperator(
    task_id='run_notebook',
    job_id='your-notebook-job-id',
    databricks_conn_id='databricks_default',
    notebook_params={
        'param1': 'value1',
        'param2': 'value2',
    }
)
```

### Submit a Spark Job

```python
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator

submit_spark_job = DatabricksSubmitRunOperator(
    task_id='submit_spark_job',
    databricks_conn_id='databricks_default',
    new_cluster_config={
        'spark_version': '12.2.x-scala2.12',
        'node_type_id': 'i3.xlarge',
        'num_workers': 2,
        'aws_attributes': {'availability': 'SPOT'},
    },
    spark_python_task={
        'python_file': 'dbfs:/path/to/script.py',
        'parameters': ['arg1', 'arg2'],
    }
)
```

### SQL Query Task

```python
from airflow.providers.databricks.operators.databricks_sql import DatabricksSqlOperator

query_task = DatabricksSqlOperator(
    task_id='databricks_query',
    databricks_conn_id='databricks_default',
    sql='''
        SELECT COUNT(*) as total_rows
        FROM my_table
        WHERE date = CURRENT_DATE()
    ''',
    warehouse_id='your-warehouse-id',  # Requires SQL warehouse
)
```

## Full Example DAG

```python
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator
from airflow.providers.databricks.operators.databricks_sql import DatabricksSqlOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'airflow',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'databricks_etl_pipeline',
    default_args=default_args,
    start_date=datetime(2025, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    # Task 1: Run Databricks job to extract raw data
    extract_data = DatabricksRunNowOperator(
        task_id='extract_from_source',
        job_id='123456',
        databricks_conn_id='databricks_default',
    )
    
    # Task 2: Run SQL transformation on data
    transform_data = DatabricksSqlOperator(
        task_id='transform_data',
        databricks_conn_id='databricks_default',
        sql='''
            CREATE OR REPLACE TABLE processed_data AS
            SELECT *
            FROM raw_data
            WHERE quality_score > 0.8
        ''',
        warehouse_id='warehouse-123',
    )
    
    # Task 3: Run validation notebook
    validate = DatabricksRunNowOperator(
        task_id='validate_results',
        job_id='789012',
        databricks_conn_id='databricks_default',
    )
    
    extract_data >> transform_data >> validate
```

## Verifying the Connection

### Test from Airflow UI

1. Go to **Admin** → **Connections**
2. Find `databricks_default`
3. Click the connection
4. Click **Test** button

### Test from Kubernetes Pod

```powershell
kubectl exec -it -n airflow deployment/airflow-scheduler -- /bin/bash

python3 << 'EOF'
from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection('databricks_default')
print(f"Host: {conn.host}")
print(f"Extra: {conn.extra_dejson}")
EOF
```

### Test Connectivity from DAG

```python
from airflow.providers.databricks.hooks.databricks import DatabricksHook
from airflow.operators.python import PythonOperator

def test_databricks_connection():
    hook = DatabricksHook(databricks_conn_id='databricks_default')
    client = hook.get_client()
    print("Connection successful!")
    return True

test_task = PythonOperator(
    task_id='test_connection',
    python_callable=test_databricks_connection,
)
```

## Troubleshooting

### Connection Type Not Showing in UI

1. Verify Databricks provider is installed:
   ```powershell
   kubectl exec -n airflow deployment/airflow-api-server -- pip list | Select-String "databricks"
   ```

2. Restart API server:
   ```powershell
   kubectl rollout restart deployment/airflow-api-server -n airflow
   ```

3. Clear browser cache and refresh

### Authentication Failures

1. Verify the personal access token is valid (not expired)
2. Ensure the token has proper permissions
3. Check the workspace URL format (should start with `https://`)
4. Verify network connectivity from AKS to Databricks

### Job Not Found

Ensure the job ID is correct:
- In Databricks UI, go to **Jobs** and note the job ID
- Job IDs are numeric (e.g., `123456789`)

### SSL Certificate Errors

If using self-hosted Databricks, in the connection **Extra** JSON:

```json
{
  "token": "your-token",
  "host": "https://your-workspace.com",
  "use_ssl": false
}
```

## Performance Tips

1. **Batch Operations:** Group multiple tasks into fewer Databricks jobs
2. **Warehouse Sizing:** Use appropriate warehouse sizes for your workload
3. **Cluster Configuration:** Reuse clusters when possible
4. **Monitoring:** Monitor Databricks job runs in Databricks UI for optimization

## See Also

- [Apache Airflow Databricks Provider](https://airflow.apache.org/docs/apache-airflow-providers-databricks/stable/)
- [Databricks Documentation](https://docs.databricks.com/)
- [Databricks API Reference](https://docs.databricks.com/api/workspace/jobs/list)
- [Airflow Connections Documentation](https://airflow.apache.org/docs/apache-airflow/stable/howto/connection.html)
