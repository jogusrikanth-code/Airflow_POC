"""
Databricks Cluster Management
==============================
Create, start, stop, and manage Databricks clusters from Airflow.

What this demonstrates:
- Creating new clusters
- Starting/stopping existing clusters
- Resizing clusters
- Terminating clusters

Connection: databricks_default
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import (
    DatabricksCreateJobsOperator,
    DatabricksSubmitRunOperator
)
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    dag_id='databricks_cluster_management',
    description='Manage Databricks clusters: create, start, stop, resize',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'cluster-management', 'sample'],
) as dag:
    
    def create_cluster():
        """Create a new Databricks cluster"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        # Create cluster configuration
        cluster = client.clusters.create(
            cluster_name="airflow-managed-cluster",
            spark_version="14.3.x-scala2.12",
            node_type_id="Standard_DS3_v2",
            num_workers=2,
            autotermination_minutes=60
        )
        
        print(f"✓ Created cluster: {cluster.cluster_id}")
        return cluster.cluster_id
    
    def start_cluster(**context):
        """Start an existing cluster"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        cluster_id = context['ti'].xcom_pull(task_ids='create_cluster')
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        client.clusters.start(cluster_id=cluster_id).result()
        print(f"✓ Started cluster: {cluster_id}")
    
    def resize_cluster(**context):
        """Resize a running cluster"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        cluster_id = context['ti'].xcom_pull(task_ids='create_cluster')
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        client.clusters.resize(cluster_id=cluster_id, num_workers=4).result()
        print(f"✓ Resized cluster to 4 workers: {cluster_id}")
    
    def terminate_cluster(**context):
        """Terminate a cluster"""
        from databricks.sdk import WorkspaceClient
        from airflow.hooks.base import BaseHook
        
        cluster_id = context['ti'].xcom_pull(task_ids='create_cluster')
        conn = BaseHook.get_connection('databricks_default')
        client = WorkspaceClient(host=conn.host, token=conn.password)
        
        client.clusters.delete(cluster_id=cluster_id)
        print(f"✓ Terminated cluster: {cluster_id}")
    
    # Tasks
    create = PythonOperator(task_id='create_cluster', python_callable=create_cluster)
    start = PythonOperator(task_id='start_cluster', python_callable=start_cluster)
    resize = PythonOperator(task_id='resize_cluster', python_callable=resize_cluster)
    terminate = PythonOperator(task_id='terminate_cluster', python_callable=terminate_cluster)
    
    # Flow: Create → Start → Resize → Terminate
    create >> start >> resize >> terminate
