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
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    
    logger.info("Listing all clusters in workspace...")
    
    url = f"https://{db.host}/api/2.0/clusters/list"
    response = db.session.get(url)
    response.raise_for_status()
    
    clusters = response.json().get('clusters', [])
    
    logger.info(f"✓ Found {len(clusters)} clusters")
    
    for cluster in clusters:
        cluster_id = cluster.get('cluster_id')
        cluster_name = cluster.get('cluster_name')
        state = cluster.get('state')
        logger.info(f"  - {cluster_name} ({cluster_id}): {state}")
    
    return {'cluster_count': len(clusters), 'clusters': clusters}


def get_cluster_details(**context):
    """Get details for a specific cluster."""
    from src.connectors import get_databricks_connector
    
    db = get_databricks_connector('databricks_default')
    cluster_id = db.cluster_id
    
    if not cluster_id:
        logger.warning("No cluster_id configured")
        return {'status': 'skipped'}
    
    logger.info(f"Getting details for cluster: {cluster_id}")
    
    url = f"https://{db.host}/api/2.0/clusters/get"
    response = db.session.get(url, params={'cluster_id': cluster_id})
    response.raise_for_status()
    
    details = response.json()
    
    logger.info(f"✓ Cluster: {details.get('cluster_name')}")
    logger.info(f"  State: {details.get('state')}")
    logger.info(f"  Node Type: {details.get('node_type_id')}")
    logger.info(f"  Workers: {details.get('num_workers')}")
    
    return {
        'cluster_id': cluster_id,
        'cluster_name': details.get('cluster_name'),
        'state': details.get('state')
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
