"""
On-Premises Data Source Connector
=================================
Handles connections to on-premises databases and file systems.

Supports:
- SQL Server
- PostgreSQL
- MySQL
- File systems (SMB, local paths)
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class OnPremConnector:
    """
    Connector for on-premises data sources.
    
    Usage:
        connector = OnPremConnector(source_type='sql_server', config={...})
        data = connector.fetch_data(query='SELECT * FROM table')
    """
    
    def __init__(self, source_type: str, config: Dict[str, Any]):
        """
        Initialize on-premises connector.
        
        Args:
            source_type: 'sql_server', 'postgresql', 'mysql', 'file'
            config: Connection configuration dict
                {
                    'host': 'server.company.com',
                    'port': 1433,
                    'database': 'mydb',
                    'username': 'user',
                    'password': 'pass'  # Better: use Airflow Connections
                }
        """
        self.source_type = source_type
        self.config = config
        self.connection = None
        
    def connect(self):
        """Establish connection to on-premises source."""
        logger.info(f"Connecting to on-premises {self.source_type}...")
        try:
            if self.source_type == 'sql_server':
                import pyodbc
                conn_string = (
                    f"Driver={{ODBC Driver 17 for SQL Server}};"
                    f"Server={self.config['host']};"
                    f"Database={self.config['database']};"
                    f"UID={self.config['username']};"
                    f"PWD={self.config['password']}"
                )
                self.connection = pyodbc.connect(conn_string)
            elif self.source_type == 'postgresql':
                import psycopg2
                self.connection = psycopg2.connect(**self.config)
            elif self.source_type == 'mysql':
                import mysql.connector
                self.connection = mysql.connector.connect(**self.config)
            logger.info("✓ Connected successfully")
        except Exception as e:
            logger.error(f"✗ Connection failed: {str(e)}")
            raise
    
    def fetch_data(self, query: str) -> List[Dict]:
        """
        Fetch data from on-premises source.
        
        Args:
            query: SQL query to execute
            
        Returns:
            List of dictionaries with query results
        """
        if not self.connection:
            self.connect()
        
        logger.info(f"Executing query...")
        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            # Get column names
            columns = [desc[0] for desc in cursor.description]
            
            # Fetch all data
            rows = cursor.fetchall()
            data = [dict(zip(columns, row)) for row in rows]
            
            logger.info(f"✓ Fetched {len(data)} rows")
            cursor.close()
            return data
        except Exception as e:
            logger.error(f"✗ Query execution failed: {str(e)}")
            raise
    
    def close(self):
        """Close connection."""
        if self.connection:
            self.connection.close()
            logger.info("Connection closed")


def fetch_from_onprem(source_type: str, config: Dict, query: str) -> List[Dict]:
    """
    Convenience function to fetch data from on-premises source.
    
    Args:
        source_type: Type of source (sql_server, postgresql, mysql, file)
        config: Connection configuration
        query: SQL query or file path
        
    Returns:
        Data as list of dictionaries
    """
    connector = OnPremConnector(source_type, config)
    try:
        data = connector.fetch_data(query)
        return data
    finally:
        connector.close()
