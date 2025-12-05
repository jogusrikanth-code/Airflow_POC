#!/usr/bin/env python3
"""
Check existing Databricks Service Principals
"""
import requests
import sys
sys.path.insert(0, '/opt/airflow')

from airflow.hooks.base import BaseHook

conn = BaseHook.get_connection('databricks_default')
host = conn.host.rstrip('/')
token = conn.password

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

try:
    print("=" * 70)
    print("EXISTING SERVICE PRINCIPALS IN YOUR DATABRICKS WORKSPACE")
    print("=" * 70)
    
    # List service principals
    resp = requests.get(f"{host}/api/2.0/service-principals", headers=headers, timeout=10)
    resp.raise_for_status()
    
    sps = resp.json().get('resources', [])
    
    if not sps:
        print("\n❌ No service principals found")
        print("\nYou'll need to create one. Options:")
        print("  1. Create via Databricks UI (Admin Settings > Service Principals)")
        print("  2. Use the API to create one programmatically")
    else:
        print(f"\n✅ Found {len(sps)} service principal(s):\n")
        for idx, sp in enumerate(sps, 1):
            print(f"#{idx}")
            print(f"  ID: {sp.get('id')}")
            print(f"  Name: {sp.get('display_name')}")
            print(f"  Active: {sp.get('active')}")
            print(f"  Created: {sp.get('created_at', 'N/A')}")
            print()
            
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ Network Error (Connection Refused)")
    print(f"Error: {e}")
    print("\n⚠️  This is the IP allowlisting issue!")
    print("The Databricks workspace is blocking API calls from this IP.")
    print("\nWorkaround: You need to either:")
    print("  1. Add the AKS cluster IP to Databricks IP allowlist")
    print("  2. Use a service principal that was created BEFORE IP restrictions")
    print("  3. Contact Databricks admin to temporarily disable restrictions")
    
except requests.exceptions.HTTPError as e:
    print(f"\n❌ HTTP Error: {e.response.status_code}")
    print(f"Response: {e.response.text}")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
