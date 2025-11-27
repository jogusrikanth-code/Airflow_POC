"""
Power BI Connector
=================
Handles Power BI REST API interactions for dataset refresh and metadata updates.

Supports:
- Dataset refresh triggers
- Dataset metadata access
- Report information retrieval
"""

from typing import Dict, List, Optional
import logging
import time

logger = logging.getLogger(__name__)


class PowerBIConnector:
    """
    Connector for Power BI Service via REST API.
    
    Usage:
        connector = PowerBIConnector(token='access_token')
        connector.refresh_dataset('workspace_id', 'dataset_id')
    """
    
    BASE_URL = "https://api.powerbi.com/v1.0/myorg"
    
    def __init__(self, token: str):
        """
        Initialize Power BI connector.
        
        Args:
            token: Azure AD access token with Power BI scope
                   (Scope: https://analysis.windows.net/powerbi/api)
        """
        self.token = token
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
            logger.info("✓ Power BI session initialized")
        except Exception as e:
            logger.error(f"✗ Failed to setup Power BI session: {str(e)}")
            raise
    
    def list_workspaces(self) -> List[Dict]:
        """
        List all Power BI workspaces.
        
        Returns:
            List of workspace dictionaries with id and name
        """
        logger.info("Fetching Power BI workspaces...")
        try:
            response = self.session.get(f"{self.BASE_URL}/groups")
            response.raise_for_status()
            
            workspaces = response.json().get('value', [])
            logger.info(f"✓ Found {len(workspaces)} workspaces")
            return workspaces
        except Exception as e:
            logger.error(f"✗ Failed to fetch workspaces: {str(e)}")
            raise
    
    def list_datasets(self, workspace_id: str) -> List[Dict]:
        """
        List datasets in a workspace.
        
        Args:
            workspace_id: Power BI workspace/group ID
            
        Returns:
            List of dataset dictionaries
        """
        logger.info(f"Fetching datasets from workspace {workspace_id}...")
        try:
            response = self.session.get(
                f"{self.BASE_URL}/groups/{workspace_id}/datasets"
            )
            response.raise_for_status()
            
            datasets = response.json().get('value', [])
            logger.info(f"✓ Found {len(datasets)} datasets")
            return datasets
        except Exception as e:
            logger.error(f"✗ Failed to fetch datasets: {str(e)}")
            raise
    
    def refresh_dataset(self, workspace_id: str, dataset_id: str, 
                       wait_for_completion: bool = True,
                       timeout: int = 300) -> bool:
        """
        Trigger dataset refresh in Power BI.
        
        Args:
            workspace_id: Power BI workspace/group ID
            dataset_id: Dataset ID to refresh
            wait_for_completion: Wait for refresh to complete
            timeout: Maximum seconds to wait for refresh
            
        Returns:
            True if refresh successful
        """
        logger.info(f"Triggering refresh for dataset {dataset_id}...")
        try:
            # Trigger refresh
            response = self.session.post(
                f"{self.BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}/refreshes"
            )
            response.raise_for_status()
            logger.info("✓ Refresh triggered")
            
            if wait_for_completion:
                return self._wait_for_refresh(
                    workspace_id, dataset_id, timeout
                )
            return True
        except Exception as e:
            logger.error(f"✗ Refresh failed: {str(e)}")
            raise
    
    def _wait_for_refresh(self, workspace_id: str, dataset_id: str, 
                         timeout: int) -> bool:
        """Wait for dataset refresh to complete."""
        logger.info(f"Waiting for refresh (timeout: {timeout}s)...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.session.get(
                    f"{self.BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}/refreshes?$top=1"
                )
                response.raise_for_status()
                
                refreshes = response.json().get('value', [])
                if refreshes:
                    latest_refresh = refreshes[0]
                    status = latest_refresh.get('status')
                    
                    if status == 'Completed':
                        logger.info("✓ Refresh completed successfully")
                        return True
                    elif status == 'Failed':
                        logger.error("✗ Refresh failed")
                        return False
                    elif status == 'Unknown':
                        logger.warning("⚠ Refresh status unknown")
                        # Continue waiting
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.warning(f"Error checking refresh status: {str(e)}")
                time.sleep(5)
        
        logger.warning(f"⚠ Refresh did not complete within {timeout}s")
        return False
    
    def get_dataset_tables(self, workspace_id: str, dataset_id: str) -> List[Dict]:
        """
        Get tables in a dataset.
        
        Args:
            workspace_id: Power BI workspace ID
            dataset_id: Dataset ID
            
        Returns:
            List of table dictionaries with metadata
        """
        logger.info(f"Fetching tables for dataset {dataset_id}...")
        try:
            response = self.session.get(
                f"{self.BASE_URL}/groups/{workspace_id}/datasets/{dataset_id}/tables"
            )
            response.raise_for_status()
            
            tables = response.json().get('value', [])
            logger.info(f"✓ Found {len(tables)} tables")
            return tables
        except Exception as e:
            logger.error(f"✗ Failed to fetch tables: {str(e)}")
            raise
    
    def get_report_info(self, workspace_id: str, report_id: str) -> Dict:
        """
        Get report information.
        
        Args:
            workspace_id: Power BI workspace ID
            report_id: Report ID
            
        Returns:
            Report dictionary with metadata
        """
        logger.info(f"Fetching report {report_id}...")
        try:
            response = self.session.get(
                f"{self.BASE_URL}/groups/{workspace_id}/reports/{report_id}"
            )
            response.raise_for_status()
            
            report = response.json()
            logger.info(f"✓ Report info: {report.get('name')}")
            return report
        except Exception as e:
            logger.error(f"✗ Failed to fetch report: {str(e)}")
            raise


def get_powerbi_token(client_id: str, client_secret: str, 
                     tenant_id: str) -> str:
    """
    Get Power BI access token using service principal.
    
    Args:
        client_id: Azure AD application client ID
        client_secret: Azure AD application client secret
        tenant_id: Azure AD tenant ID
        
    Returns:
        Access token string
    """
    import requests
    
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    
    payload = {
        'client_id': client_id,
        'scope': 'https://analysis.windows.net/powerbi/api/.default',
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    
    logger.info("Getting Power BI token...")
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        token = response.json().get('access_token')
        logger.info("✓ Token obtained")
        return token
    except Exception as e:
        logger.error(f"✗ Failed to get token: {str(e)}")
        raise


def get_powerbi_connector(conn_id: str = 'powerbi_default') -> PowerBIConnector:
    """
    Get Power BI connector from Airflow Connection.
    
    Args:
        conn_id: Airflow Connection ID
        
    Returns:
        PowerBIConnector instance
        
    Note:
        Connection can have either:
        - password: Direct access token
        - extra: {"client_id": "...", "client_secret": "...", "tenant_id": "..."}
    """
    from airflow.hooks.base import BaseHook
    
    conn = BaseHook.get_connection(conn_id)
    extra = conn.extra_dejson if hasattr(conn, 'extra_dejson') else {}
    
    if conn.password and not extra.get('client_id'):
        # Direct token
        token = conn.password
    else:
        # Get token from service principal
        token = get_powerbi_token(
            client_id=extra.get('client_id'),
            client_secret=extra.get('client_secret'),
            tenant_id=extra.get('tenant_id')
        )
    
    return PowerBIConnector(token=token)
