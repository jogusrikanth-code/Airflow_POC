"""
Databricks Connector (POC)
=========================
Minimal connector for Databricks API calls. Kept simple for POC.
"""

import logging

logger = logging.getLogger(__name__)


class DatabricksConnector:
    """
    Simple connector for Databricks REST API.
    
    Usage:
        db = DatabricksConnector(host='adb-xxx.azuredatabricks.net', token='dapi...')
        response = db.session.get(f"https://{db.host}/api/2.0/clusters/list")
    """
    
    def __init__(self, host: str, token: str, cluster_id: str = None):
        """
        Initialize Databricks connector.
        
        Args:
            host: Databricks workspace host
            token: Databricks API token
            cluster_id: Optional cluster ID
        """
        self.host = host
        self.token = token
        self.cluster_id = cluster_id
        self.session = None
        self._setup_session()
    
    def _setup_session(self):
        """Setup HTTP session with authentication."""
        try:
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            })
            logger.info("✓ Databricks session initialized")
        except Exception as e:
            logger.error(f"✗ Failed to setup session: {str(e)}")
            raise


def get_databricks_connector(conn_id: str = 'databricks_default') -> DatabricksConnector:
    """
    Get Databricks connector from Airflow Connection.
    
    Args:
        conn_id: Airflow Connection ID (default: 'databricks_default')
        
    Returns:
        DatabricksConnector instance
        
    Note:
        Connection should have:
        - host: Databricks workspace host
        - password: Databricks API token
        - extra: {"cluster_id": "xxx"} or {"warehouse_id": "xxx"}
    """
    from airflow.hooks.base import BaseHook
    
    conn = BaseHook.get_connection(conn_id)
    extra = conn.extra_dejson if hasattr(conn, 'extra_dejson') else {}
    
    return DatabricksConnector(
        host=conn.host,
        token=conn.password,
        cluster_id=extra.get('cluster_id')
    )
