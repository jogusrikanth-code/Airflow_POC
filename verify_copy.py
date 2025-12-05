"""Verify Azure file copy was successful"""
from azure.storage.blob import BlobServiceClient
from airflow.hooks.base import BaseHook

# Get connection
conn = BaseHook.get_connection('azure_blob_default')
conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"

client = BlobServiceClient.from_connection_string(conn_str)
container_client = client.get_container_client('sg-analytics-raw')

# Check if file was copied
print("\n" + "=" * 60)
print("Verifying File Copy - Checking Airflow/test/ folder")
print("=" * 60)

blob_list = container_client.list_blobs(name_starts_with='Airflow/test')
count = 0
for blob in blob_list:
    if not blob.name.endswith('/'):
        print(f"✅ {blob.name} ({blob.size} bytes)")
        count += 1

if count > 0:
    print(f"\n✅ SUCCESS! Found {count} file(s) in target folder Airflow/test/")
else:
    print("\n❌ No files found in target folder")

print("=" * 60)
