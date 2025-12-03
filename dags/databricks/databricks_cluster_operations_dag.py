"""Databricks Cluster Operations DAG
====================================
Demonstrates listing and managing Databricks clusters.

Examples:
- List all clusters in workspace
- Get cluster details
"""

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def list_clusters(**context):
    """List all clusters in Databricks workspace."""
    from airflow.providers.databricks.hooks.databricks import DatabricksHook
    
    hook = DatabricksHook(databricks_conn_id='databricks_default')
    
    logger.info("Listing all clusters in workspace...")
    
    response = hook._do_api_call(('GET', 'api/2.0/clusters/list'))
    clusters = response.get('clusters', [])
    
    logger.info(f"✓ Found {len(clusters)} clusters")
    
    for cluster in clusters:
        cluster_id = cluster.get('cluster_id')
        cluster_name = cluster.get('cluster_name')
        state = cluster.get('state')
        logger.info(f"  - {cluster_name} ({cluster_id}): {state}")
    
    return {'cluster_count': len(clusters), 'clusters': clusters}


def get_cluster_details(**context):
    """Get details for a specific cluster."""
    from airflow.providers.databricks.hooks.databricks import DatabricksHook
    from airflow.hooks.base import BaseHook
    
    hook = DatabricksHook(databricks_conn_id='databricks_default')
    
    # Get cluster_id from connection extra config
    conn = BaseHook.get_connection('databricks_default')
    extra = conn.extra_dejson if hasattr(conn, 'extra_dejson') else {}
    cluster_id = extra.get('cluster_id')
    
    if not cluster_id:
        logger.warning("No cluster_id configured in connection")
        return {'status': 'skipped'}
    
    logger.info(f"Getting details for cluster: {cluster_id}")
    
    response = hook._do_api_call(
        ('GET', 'api/2.0/clusters/get'),
        {'cluster_id': cluster_id}
    )
    
    logger.info(f"✓ Cluster: {response.get('cluster_name')}")
    logger.info(f"  State: {response.get('state')}")
    logger.info(f"  Node Type: {response.get('node_type_id')}")
    logger.info(f"  Workers: {response.get('num_workers')}")
    
    return {
        'cluster_id': cluster_id,
        'cluster_name': response.get('cluster_name'),
        'state': response.get('state')
    }


# DAG definition
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 12, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'databricks_cluster_operations',
    default_args=default_args,
    description='List and manage Databricks clusters',
    schedule='@daily',
    catchup=False,
    tags=['databricks', 'cluster', 'example'],
) as dag:
    
    # Task 1: List all clusters
    list_all_clusters = PythonOperator(
        task_id='list_clusters',
        python_callable=list_clusters,
    )
    
    # Task 2: Get cluster details
    get_details = PythonOperator(
        task_id='get_cluster_details',
        python_callable=get_cluster_details,
    )
    
    # Tasks run independently
    [list_all_clusters, get_details]
