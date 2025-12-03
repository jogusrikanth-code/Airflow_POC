"""
Azure Storage Connector
======================
Handles connections to Azure Blob Storage for data staging.

Supports:
- Upload/download blobs
- List containers and blobs
- Generate SAS URLs
"""

from typing import Dict, List, Optional, Callable, TypeVar, Any
import logging
from io import BytesIO
import pandas as pd
from time import sleep

T = TypeVar("T")

logger = logging.getLogger(__name__)


class AzureStorageConnector:
    """
    Connector for Azure Blob Storage.
    
    Usage:
        connector = AzureStorageConnector(conn_string='DefaultEndpointsProtocol=...')
        connector.upload_file('local_file.csv', 'container', 'remote/file.csv')
    """
    
    def __init__(self, conn_string: str = None, account_name: str = None,
                 account_key: str = None, default_container: Optional[str] = None):
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
        self.default_container = default_container
        self._setup_client()

    def _with_retries(self, func: Callable[[], T], *, retries: int = 3, backoff_seconds: float = 1.0) -> T:
        """Simple retry wrapper for transient errors.

        Args:
            func: Zero-arg callable to execute
            retries: Number of attempts
            backoff_seconds: Initial backoff time, doubles each retry
        """
        attempt = 0
        while True:
            try:
                return func()
            except Exception as e:
                attempt += 1
                if attempt > retries:
                    logger.error(f"✗ Operation failed after {retries} retries: {e}")
                    raise
                sleep_time = backoff_seconds * (2 ** (attempt - 1))
                logger.warning(f"Retry {attempt}/{retries} after error: {e}. Sleeping {sleep_time:.1f}s...")
                sleep(sleep_time)
    
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

    def ensure_container(self, container_name: Optional[str] = None) -> None:
        """Create container if it doesn't exist (idempotent)."""
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        try:
            from azure.core.exceptions import ResourceExistsError
            container_client = self.client.get_container_client(name)
            def _create():
                container_client.create_container()
                return True
            try:
                self._with_retries(_create)
                logger.info(f"✓ Container created: {name}")
            except Exception as e:
                # If it already exists, ignore; else re-raise
                if isinstance(e, ResourceExistsError) or 'ContainerAlreadyExists' in str(e):
                    logger.info(f"ℹ Container already exists: {name}")
                else:
                    raise
        except Exception as e:
            logger.error(f"✗ ensure_container failed: {e}")
            raise

    def list_containers(self) -> List[str]:
        """List storage containers."""
        try:
            def _list() -> List[str]:
                return [c['name'] if isinstance(c, dict) else c.name for c in self.client.list_containers()]
            names = self._with_retries(_list)
            logger.info(f"✓ Found {len(names)} containers")
            return names
        except Exception as e:
            logger.error(f"✗ list_containers failed: {e}")
            raise
    
    def upload_file(self, local_path: str, container_name: Optional[str],
                    blob_name: str, overwrite: bool = True, ensure_container: bool = True):
        """
        Upload file to Azure Blob Storage.
        
        Args:
            local_path: Local file path
            container_name: Azure container name
            blob_name: Blob name (path in container)
            overwrite: Whether to overwrite if exists
        """
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        logger.info(f"Uploading {local_path} to {name}/{blob_name}...")
        try:
            container_client = self.client.get_container_client(name)
            if ensure_container:
                try:
                    self.ensure_container(name)
                except Exception:
                    # Ignore if exists or creation race
                    pass
            with open(local_path, 'rb') as data:
                def _upload():
                    return container_client.upload_blob(
                        name=blob_name,
                        data=data,
                        overwrite=overwrite
                    )
                self._with_retries(_upload)
            logger.info("✓ Upload completed")
        except Exception as e:
            logger.error(f"✗ Upload failed: {str(e)}")
            raise
    
    def download_file(self, container_name: Optional[str], blob_name: str,
                      local_path: str):
        """
        Download file from Azure Blob Storage.
        
        Args:
            container_name: Azure container name
            blob_name: Blob name (path in container)
            local_path: Local file path to save
        """
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        logger.info(f"Downloading {name}/{blob_name}...")
        try:
            blob_client = self.client.get_blob_client(container=name, blob=blob_name)
            with open(local_path, 'wb') as file:
                def _download() -> bytes:
                    return blob_client.download_blob().readall()
                data = self._with_retries(_download)
                file.write(data)
            
            logger.info(f"✓ Downloaded to {local_path}")
        except Exception as e:
            logger.error(f"✗ Download failed: {str(e)}")
            raise
    
    def upload_dataframe(self, df: pd.DataFrame, container_name: Optional[str],
                         blob_name: str, format: str = 'csv'):
        """
        Upload pandas DataFrame to Azure Blob Storage.
        
        Args:
            df: Pandas DataFrame
            container_name: Azure container name
            blob_name: Blob name
            format: 'csv', 'parquet', or 'json'
        """
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        logger.info(f"Uploading DataFrame ({len(df)} rows) as {format}...")
        try:
            container_client = self.client.get_container_client(name)
            
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
            data_bytes = buffer.getvalue()
            def _upload():
                return container_client.upload_blob(
                    name=blob_name,
                    data=data_bytes,
                    overwrite=True
                )
            self._with_retries(_upload)
            logger.info("✓ DataFrame uploaded")
        except Exception as e:
            logger.error(f"✗ Upload failed: {str(e)}")
            raise
    
    def download_dataframe(self, container_name: Optional[str], blob_name: str,
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
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        logger.info(f"Downloading DataFrame from {blob_name}...")
        try:
            blob_client = self.client.get_blob_client(container=name, blob=blob_name)
            def _download() -> bytes:
                return blob_client.download_blob().readall()
            data = self._with_retries(_download)
            
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
    
    def list_blobs(self, container_name: Optional[str], prefix: str = '') -> List[str]:
        """
        List blobs in container.
        
        Args:
            container_name: Azure container name
            prefix: Optional prefix filter
            
        Returns:
            List of blob names
        """
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        logger.info(f"Listing blobs in {name}...")
        try:
            container_client = self.client.get_container_client(name)
            def _list() -> List[str]:
                return [blob.name for blob in container_client.list_blobs(name_starts_with=prefix)]
            blobs = self._with_retries(_list)
            logger.info(f"✓ Found {len(blobs)} blobs")
            return blobs
        except Exception as e:
            logger.error(f"✗ List failed: {str(e)}")
            raise

    def blob_exists(self, container_name: Optional[str], blob_name: str) -> bool:
        """Check if a blob exists."""
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        try:
            blob_client = self.client.get_blob_client(container=name, blob=blob_name)
            def _exists() -> bool:
                return blob_client.exists()
            exists = bool(self._with_retries(_exists))
            return exists
        except Exception as e:
            logger.error(f"✗ blob_exists failed: {e}")
            raise

    def delete_blob(self, container_name: Optional[str], blob_name: str, *, if_exists: bool = True) -> None:
        """Delete a blob (optionally ignoring missing)."""
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        try:
            blob_client = self.client.get_blob_client(container=name, blob=blob_name)
            def _delete():
                return blob_client.delete_blob()
            if if_exists and not self.blob_exists(name, blob_name):
                return
            self._with_retries(_delete)
            logger.info(f"✓ Deleted blob {name}/{blob_name}")
        except Exception as e:
            logger.error(f"✗ delete_blob failed: {e}")
            raise

    def generate_sas_url(self, container_name: Optional[str], blob_name: str,
                          expiry_minutes: int = 60, permission: str = 'r') -> str:
        """Generate a SAS URL for a blob.

        Note: SAS generation requires an account key. If the connector was
        initialized without an account_key, this will raise an error.
        """
        name = container_name or self.default_container
        if not name:
            raise ValueError("container_name is required when default_container is not set")
        if not self.account_name or not self.account_key:
            raise RuntimeError("SAS generation requires account_name and account_key")
        try:
            from datetime import datetime, timedelta
            from azure.storage.blob import generate_blob_sas, BlobSasPermissions
            token = generate_blob_sas(
                account_name=self.account_name,
                container_name=name,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read='r' in permission,
                                              write='w' in permission,
                                              create='c' in permission,
                                              delete='d' in permission,
                                              add='a' in permission,
                                              list='l' in permission),
                expiry=datetime.utcnow() + timedelta(minutes=expiry_minutes)
            )
            url = f"https://{self.account_name}.blob.core.windows.net/{name}/{blob_name}?{token}"
            return url
        except Exception as e:
            logger.error(f"✗ generate_sas_url failed: {e}")
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
        return AzureStorageConnector(conn_string=extra['connection_string'], default_container=extra.get('container'))

    # Fallback to account name/key from extras or standard fields
    account_name = extra.get('account_name') or getattr(conn, 'login', None)
    account_key = extra.get('account_key') or getattr(conn, 'password', None)
    return AzureStorageConnector(
        account_name=account_name,
        account_key=account_key,
        default_container=extra.get('container')
    )
