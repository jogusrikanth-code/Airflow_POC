"""
Databricks Connector (POC)
=========================
Minimal connector for running SQL queries on a Databricks workspace/warehouse
and creating a table from a query. Kept intentionally simple for readability.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class DatabricksConnector:
    """
    Connector for Databricks workspace.
    
    Usage:
        connector = DatabricksConnector(host='adb-xxx.azuredatabricks.net', token='dapi...')
        result = connector.run_query('SELECT * FROM table')
    """
    
    def __init__(self, host: str, token: str, cluster_id: str = None):
        """
        Initialize Databricks connector.
        
        Args:
            host: Databricks workspace host (e.g., adb-xxx.azuredatabricks.net)
            token: Databricks API token (store in Airflow Connection!)
            cluster_id: Optional cluster ID for SQL queries
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
            logger.error(f"✗ Failed to setup Databricks session: {str(e)}")
            raise
    
    def run_query(self, query: str, warehouse_id: str = None) -> List[Dict]:
        """
        Run SQL query on Databricks SQL warehouse.
        
        Args:
            query: SQL query to execute
            warehouse_id: Databricks SQL warehouse ID (if using warehouse instead of cluster)
            
        Returns:
            Query results as list of dictionaries
        """
        logger.info("Executing SQL on Databricks...")
        try:
            from databricks.sql import connect
            
            conn = connect(
                host=self.host,
                http_path="/sql/1.0/warehouses/" + (warehouse_id or self.cluster_id),
                auth_token=self.token
            )
            
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Get results
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            results = [dict(zip(columns, row)) for row in rows]
            
            logger.info(f"✓ Query returned {len(results)} rows")
            cursor.close()
            conn.close()
            
            return results
        except Exception as e:
            logger.error(f"✗ Query failed: {str(e)}")
            raise
    
    def create_table_from_query(self, source_query: str, target_table: str):
        """
        Create or replace a table from a query result (CTAS pattern).
        
        Args:
            source_query: SQL query to get data from
            target_table: Target table to create
        """
        logger.info(f"Creating table {target_table} from query...")
        try:
            from databricks.sql import connect
            
            conn = connect(
                host=self.host,
                http_path="/sql/1.0/warehouses/" + self.cluster_id,
                auth_token=self.token
            )
            
            cursor = conn.cursor()
            
            create_query = f"""
            CREATE OR REPLACE TABLE {target_table} AS
            {source_query}
            """
            cursor.execute(create_query)
            logger.info(f"✓ Table {target_table} created successfully")
            
            cursor.close()
            conn.close()
        except Exception as e:
            logger.error(f"✗ Table creation failed: {str(e)}")
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
