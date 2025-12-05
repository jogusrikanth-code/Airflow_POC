"""Test Azure blob copy functionality directly"""
from azure.storage.blob import BlobServiceClient
from airflow.hooks.base import BaseHook

print("=" * 60)
print("Azure Blob Copy Test")
print("=" * 60)

# Get connection
conn = BaseHook.get_connection('azure_blob_default')
print(f"\n✓ Connection retrieved: {conn.conn_id}")
print(f"  Storage Account: {conn.host}")

# Build connection string
conn_str = f"DefaultEndpointsProtocol=https;AccountName={conn.host};AccountKey={conn.password};EndpointSuffix=core.windows.net"

# Create client
client = BlobServiceClient.from_connection_string(conn_str)
container_client = client.get_container_client('sg-analytics-raw')

# List blobs and get first file
print(f"\n📁 Listing blobs in seasonal_buy/2025-10-12/...")
blob_list = container_client.list_blobs(name_starts_with='seasonal_buy/2025-10-12', results_per_page=5)
all_blobs = []
for i, blob in enumerate(blob_list):
    if i >= 5:
        break
    all_blobs.append(blob)

# Find first non-folder blob
source_blob = None
for blob in all_blobs:
    print(f"  - {blob.name} ({blob.size} bytes)")
    if not blob.name.endswith('/') and blob.size > 0:
        source_blob = blob.name
        break

if not source_blob:
    print("\n❌ No files found to copy")
    exit(1)

# Extract filename
filename = source_blob.split('/')[-1]
target_path = f"Airflow/test/{filename}"

print(f"\n🔄 Copying file:")
print(f"  Source: {source_blob}")
print(f"  Target: {target_path}")

# Server-side copy
source_url = f"https://{conn.host}.blob.core.windows.net/sg-analytics-raw/{source_blob}"
target_blob = container_client.get_blob_client(target_path)

print(f"\n⏳ Starting server-side copy...")
copy_result = target_blob.start_copy_from_url(source_url)

print(f"✅ Copy initiated successfully!")
print(f"   Copy ID: {copy_result.get('copy_id', 'N/A')}")
print(f"   Copy Status: {copy_result.get('copy_status', 'N/A')}")

print("\n" + "=" * 60)
print(f"✅ Test completed successfully!")
print("=" * 60)
