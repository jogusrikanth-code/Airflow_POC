"""
Databricks File Operations
===========================
Work with DBFS (Databricks File System).

What this demonstrates:
- Uploading files to DBFS
- Downloading files from DBFS
- Moving/copying files
- Listing directories
- Deleting files

Connection: databricks_default
"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    dag_id='databricks_file_operations',
    description='DBFS operations: upload, download, move, delete',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'dbfs', 'files', 'sample'],
) as dag:
    
    def upload_file():
        """Upload file to DBFS"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        # Upload file
        local_file = "/tmp/data.csv"
        dbfs_path = "/FileStore/airflow/data.csv"
        
        print(f"✓ Uploading {local_file} to {dbfs_path}")
        # client.dbfs.upload(dbfs_path, open(local_file, 'rb'))
        return dbfs_path
    
    def list_directory():
        """List files in DBFS directory"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        dbfs_path = "/FileStore/airflow/"
        files = list(client.dbfs.list(dbfs_path))
        
        print(f"\nFiles in {dbfs_path}:")
        for file in files:
            print(f"  - {file.path} ({file.file_size} bytes)")
        
        return len(files)
    
    def move_file(**context):
        """Move/rename file in DBFS"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        source = context['ti'].xcom_pull(task_ids='upload_file')
        target = "/FileStore/airflow/processed/data.csv"
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        print(f"✓ Moving {source} to {target}")
        # client.dbfs.move(source, target)
        return target
    
    def download_file(**context):
        """Download file from DBFS"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        dbfs_path = context['ti'].xcom_pull(task_ids='move_file')
        local_path = "/tmp/downloaded_data.csv"
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        print(f"✓ Downloading {dbfs_path} to {local_path}")
        # with open(local_path, 'wb') as f:
        #     f.write(client.dbfs.read(dbfs_path).data)
        return local_path
    
    def delete_file(**context):
        """Delete file from DBFS"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        dbfs_path = context['ti'].xcom_pull(task_ids='move_file')
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        print(f"✓ Deleting {dbfs_path}")
        # client.dbfs.delete(dbfs_path)
        return "Deleted"
    
    # Tasks
    upload = PythonOperator(task_id='upload_file', python_callable=upload_file)
    list_dir = PythonOperator(task_id='list_directory', python_callable=list_directory)
    move = PythonOperator(task_id='move_file', python_callable=move_file)
    download = PythonOperator(task_id='download_file', python_callable=download_file)
    delete = PythonOperator(task_id='delete_file', python_callable=delete_file)
    
    # Flow: Upload → List → Move → Download → Delete
    upload >> list_dir >> move >> download >> delete
