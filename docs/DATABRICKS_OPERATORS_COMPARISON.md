# Airflow Databricks Integration Methods

## Current Implementation vs. Native Operators

### Current: PythonOperator + SDK (What we're using)

```python
from airflow.operators.python import PythonOperator
from databricks.sdk import WorkspaceClient

# Your code manages everything manually
def list_workflows(**context):
    from airflow.hooks.base import BaseHook
    conn = BaseHook.get_connection('databricks_default')
    client = WorkspaceClient(
        host=conn.host,
        token=conn.password
    )
    jobs = client.jobs.list()
    # ... custom handling ...

task = PythonOperator(
    task_id='list_workflows',
    python_callable=list_workflows
)
```

**Pros:**
- Full control over implementation
- Can use any Databricks SDK feature
- Flexible error handling
- Good for complex logic

**Cons:**
- Manual connection management
- More boilerplate code
- Need to handle retry logic yourself
- Less Airflow integration

---

## ✅ Recommended: Airflow Native Operators

### Option 1: Run Notebook with DatabricksSubmitRunOperator

```python
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator

task = DatabricksSubmitRunOperator(
    task_id='run_notebook',
    databricks_conn_id='databricks_default',  # Uses Airflow connection
    new_cluster={
        "spark_version": "14.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 2
    },
    notebook_task={
        "notebook_path": "/Users/email@company.com/my_notebook",
        "base_parameters": {"key": "value"}
    }
)
```

**Pros:**
- ✅ Built-in retry logic
- ✅ Better Airflow UI integration
- ✅ Automatic connection management
- ✅ Better error handling and logging
- ✅ Xcom integration for data passing
- ✅ Less boilerplate code

**Cons:**
- Limited to specific Databricks operations
- May need custom code for complex scenarios

---

### Option 2: Run Existing Job with DatabricksRunNowOperator

```python
from airflow.providers.databricks.operators.databricks import DatabricksRunNowOperator

task = DatabricksRunNowOperator(
    task_id='run_job',
    databricks_conn_id='databricks_default',
    job_id=123,  # Your Databricks job ID
    notebook_params={"date": "{{ ds }}"}
)
```

This is perfect for triggering existing Databricks jobs from Airflow!

---

### Option 3: List Workflows with SQL Operator (Alternative)

```python
from airflow.providers.databricks.operators.databricks_sql import DatabricksSqlOperator

task = DatabricksSqlOperator(
    task_id='query_data',
    databricks_conn_id='databricks_default',
    sql="SELECT * FROM my_table WHERE date = '{{ ds }}'",
    output_path="/path/to/output"
)
```

---

## Comparison Table

| Feature | PythonOperator + SDK | DatabricksSubmitRunOperator | DatabricksRunNowOperator |
|---------|---------------------|-----------------------------|--------------------------|
| Retry Logic | Manual | ✅ Built-in | ✅ Built-in |
| Connection Mgmt | Manual | ✅ Automatic | ✅ Automatic |
| Error Handling | Custom | ✅ Standard | ✅ Standard |
| UI Integration | Basic | ✅ Enhanced | ✅ Enhanced |
| Xcom Support | Manual | ✅ Automatic | ✅ Automatic |
| Learning Curve | Medium | Easy | Easy |
| Flexibility | High | Medium | Medium |
| Code Complexity | High | Low | Low |

---

## Recommendation for Your POC

Since you have `databricks_default` connection already configured:

### For Testing/Listing Workflows:
**Keep using PythonOperator + SDK** - It's more flexible for exploration

### For Production ETL:
**Use DatabricksRunNowOperator** or **DatabricksSubmitRunOperator** - Better for:
- Running scheduled jobs
- Production ETL pipelines
- Data quality monitoring
- Retry/error handling

---

## Available Native Operators

Airflow provides these Databricks operators:

1. **DatabricksSubmitRunOperator** - Submit and run new job runs
2. **DatabricksRunNowOperator** - Run existing Databricks jobs
3. **DatabricksSqlOperator** - Execute SQL queries on Databricks SQL
4. **DatabricksCopyIntoOperator** - Copy data into Databricks tables
5. **DatabricksCreateJobOperator** - Create Databricks jobs
6. **DatabricksDeleteJobOperator** - Delete Databricks jobs
7. **DatabricksGetJobRunOperator** - Get job run status
8. **DatabricksRepairRunOperator** - Repair failed job runs

---

## Your Current Setup

**Current:** `databricks_list_workflows.py` uses PythonOperator + SDK ✅
**Status:** Working perfectly (network policy is separate issue)

**Recommendation:**
1. Keep this for exploration/testing
2. Create new DAG with native operators for production jobs
3. Example file provided: `databricks_native_operators.py`

---

## Next Steps

1. ✅ Connection is configured: `databricks_default`
2. ✅ SDK is installed in worker pod
3. ⏳ Resolve network policy (IP allowlisting)
4. ⏳ When ready: Deploy native operator DAG for production use

Would you like me to:
- [ ] Create a production-ready ETL DAG with native operators?
- [ ] Set up job scheduling with Databricks native operators?
- [ ] Move to PowerBI/SQL Server connection testing?
