"""Create Azure Blob Storage connection"""
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import sys
sys.path.insert(0, '/opt/airflow/dags/repo')
from src.connectors.azure_connector import AZURE_CONN_ID, AZURE_STORAGE_ACCOUNT, AZURE_STORAGE_KEY

def create_connection(**context):
    """Create azure_blob_default connection."""
    from airflow.models import Connection
    from airflow.utils.session import create_session
    
    # Note: Update azure_connector.py with real credentials before running
    conn = Connection(
        conn_id=AZURE_CONN_ID,
        conn_type='wasb',
        login=AZURE_STORAGE_ACCOUNT,
        password=AZURE_STORAGE_KEY
    )
    
    with create_session() as session:
        existing = session.query(Connection).filter(Connection.conn_id == AZURE_CONN_ID).first()
        if existing:
            session.delete(existing)
        session.add(conn)
        session.commit()
        print(f"✓ Created connection: {AZURE_CONN_ID}")

with DAG(
    'setup_azure_connection',
    start_date=datetime(2025, 1, 1),
    schedule=None,
    catchup=False,
    tags=['setup']
) as dag:
    PythonOperator(task_id='create_connection', python_callable=create_connection)

