"""
Azure Storage Connector
======================
Handles basic connections to Azure Blob Storage for data staging.

Supports (POC scope):
- Upload/download blobs
- Upload/download pandas DataFrames
- List blobs in a container
"""

from typing import List
import logging
from io import BytesIO
import pandas as pd
 

logger = logging.getLogger(__name__)


class AzureStorageConnector:
    """
    Connector for Azure Blob Storage.
    
    Usage:
        connector = AzureStorageConnector(conn_string='DefaultEndpointsProtocol=...')
        connector.upload_file('local_file.csv', 'container', 'remote/file.csv')
    """
    
    def __init__(self, conn_string: str = None, account_name: str = None,
                 account_key: str = None):
        """
        Initialize Azure Storage connector.
        
        Args:
            conn_string: Azure Storage connection string (preferred)
            account_name: Storage account name (alternative)
            account_key: Storage account key (alternative)
        """
        self.conn_string = conn_string
        self.account_name = account_name
        self.account_key = account_key
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup Azure Storage client."""
        try:
            from azure.storage.blob import BlobServiceClient
            
            if self.conn_string:
                self.client = BlobServiceClient.from_connection_string(
                    self.conn_string
                )
            elif self.account_name and self.account_key:
                self.client = BlobServiceClient(
                    account_url=f"https://{self.account_name}.blob.core.windows.net",
                    credential=self.account_key
                )
            logger.info("✓ Azure Storage client initialized")
        except Exception as e:
            logger.error(f"✗ Failed to setup Azure Storage client: {str(e)}")
            raise
    
    def upload_file(self, local_path: str, container_name: str,
                    blob_name: str, overwrite: bool = True):
        """
        Upload file to Azure Blob Storage.
        
        Args:
            local_path: Local file path
            container_name: Azure container name
            blob_name: Blob name (path in container)
            overwrite: Whether to overwrite if exists
        """
        logger.info(f"Uploading {local_path} to {container_name}/{blob_name}...")
        try:
            container_client = self.client.get_container_client(container_name)
            with open(local_path, 'rb') as data:
                container_client.upload_blob(
                    name=blob_name,
                    data=data,
                    overwrite=overwrite
                )
            logger.info("✓ Upload completed")
        except Exception as e:
            logger.error(f"✗ Upload failed: {str(e)}")
            raise
    
    def download_file(self, container_name: str, blob_name: str,
                      local_path: str):
        """
        Download file from Azure Blob Storage.
        
        Args:
            container_name: Azure container name
            blob_name: Blob name (path in container)
            local_path: Local file path to save
        """
        logger.info(f"Downloading {container_name}/{blob_name}...")
        try:
            blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
            with open(local_path, 'wb') as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())
            
            logger.info(f"✓ Downloaded to {local_path}")
        except Exception as e:
            logger.error(f"✗ Download failed: {str(e)}")
            raise
    
    def upload_dataframe(self, df: pd.DataFrame, container_name: str,
                         blob_name: str, format: str = 'csv'):
        """
        Upload pandas DataFrame to Azure Blob Storage.
        
        Args:
            df: Pandas DataFrame
            container_name: Azure container name
            blob_name: Blob name
            format: 'csv', 'parquet', or 'json'
        """
        logger.info(f"Uploading DataFrame ({len(df)} rows) as {format}...")
        try:
            container_client = self.client.get_container_client(container_name)
            
            # Convert DataFrame to bytes
            buffer = BytesIO()
            if format == 'csv':
                df.to_csv(buffer, index=False)
            elif format == 'parquet':
                try:
                    df.to_parquet(buffer, index=False)
                except Exception as e:
                    raise RuntimeError("Parquet support requires 'pyarrow' or 'fastparquet' to be installed") from e
            elif format == 'json':
                df.to_json(buffer, orient='records')
            else:
                raise ValueError("format must be one of: 'csv', 'parquet', 'json'")
            
            buffer.seek(0)
            container_client.upload_blob(
                name=blob_name,
                data=buffer.getvalue(),
                overwrite=True
            )
            logger.info("✓ DataFrame uploaded")
        except Exception as e:
            logger.error(f"✗ Upload failed: {str(e)}")
            raise
    
    def download_dataframe(self, container_name: str, blob_name: str,
                           format: str = 'csv') -> pd.DataFrame:
        """
        Download file from Azure as pandas DataFrame.
        
        Args:
            container_name: Azure container name
            blob_name: Blob name
            format: 'csv', 'parquet', or 'json'
            
        Returns:
            Pandas DataFrame
        """
        logger.info(f"Downloading DataFrame from {blob_name}...")
        try:
            blob_client = self.client.get_blob_client(container=container_name, blob=blob_name)
            download_stream = blob_client.download_blob()
            data = download_stream.readall()
            
            # Convert bytes to DataFrame
            buffer = BytesIO(data)
            if format == 'csv':
                df = pd.read_csv(buffer)
            elif format == 'parquet':
                try:
                    df = pd.read_parquet(buffer)
                except Exception as e:
                    raise RuntimeError("Parquet support requires 'pyarrow' or 'fastparquet' to be installed") from e
            elif format == 'json':
                df = pd.read_json(buffer)
            else:
                raise ValueError("format must be one of: 'csv', 'parquet', 'json'")
            
            logger.info(f"✓ Downloaded {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"✗ Download failed: {str(e)}")
            raise
    
    def list_blobs(self, container_name: str, prefix: str = '') -> List[str]:
        """
        List blobs in container.
        
        Args:
            container_name: Azure container name
            prefix: Optional prefix filter
            
        Returns:
            List of blob names
        """
        logger.info(f"Listing blobs in {container_name}...")
        try:
            container_client = self.client.get_container_client(container_name)
            blobs = [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
            logger.info(f"✓ Found {len(blobs)} blobs")
            return blobs
        except Exception as e:
            logger.error(f"✗ List failed: {str(e)}")
            raise


def get_azure_storage_connector(conn_id: str = 'azure_default') -> AzureStorageConnector:
    """
    Get Azure Storage connector from Airflow Connection.
    
    Args:
        conn_id: Airflow Connection ID
        
    Returns:
        AzureStorageConnector instance
        
    Note:
        Connection should have:
        - extra: {"connection_string": "..."} or {"account_name": "...", "account_key": "..."}
    """
    from airflow.hooks.base import BaseHook
    
    conn = BaseHook.get_connection(conn_id)
    extra = conn.extra_dejson if hasattr(conn, 'extra_dejson') else {}

    # Prefer explicit connection_string in extras
    if 'connection_string' in extra and extra['connection_string']:
        return AzureStorageConnector(conn_string=extra['connection_string'])

    # Fallback to account name/key from extras or standard fields
    account_name = extra.get('account_name') or getattr(conn, 'login', None)
    account_key = extra.get('account_key') or getattr(conn, 'password', None)
    return AzureStorageConnector(
        account_name=account_name,
        account_key=account_key
    )
