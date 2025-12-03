# 🔗 Enterprise Integration Patterns

Connecting Airflow to your enterprise ecosystem? This guide covers integration with Databricks, Power BI, Azure services, and more! ☁️

> **🎯 Perfect for:** Integration engineers, data architects, platform teams Setup Guide

## Overview

Your Airflow POC now includes full integration capabilities for enterprise data pipelines:

```
On-Premises DB → Azure Storage → Databricks → Power BI
												  ↓
											Reports & Dashboards
```

---

## 🔧 Setup Guide

### 1. Install Required Packages

```bash
pip install pyodbc psycopg2-binary mysql-connector-python
pip install azure-storage-blob
pip install databricks-sql-connector
pip install requests
```

### 2. Configure Airflow Connections

#### On-Premises Database Connection
```bash
# In Airflow Web UI: Admin → Connections → Create

# Connection ID: onprem_db
# Conn Type: MSSQL (for SQL Server) or PostgreSQL
# Host: your-onprem-server.company.com
# Port: 1433 (SQL Server) or 5432 (PostgreSQL)
# Schema: database_name
# Login: username
# Password: password
```

#### Azure Storage Connection
```bash
# Connection ID: azure_default
# Conn Type: wasb (or Azure)
# Login: storage_account_name
# Password: storage_account_key
# Extra JSON:
# {
#   "connection_string": "DefaultEndpointsProtocol=https://..."
# }
```

#### Databricks Connection
```bash
# Connection ID: databricks_default
# Conn Type: Databricks
# Host: adb-xxx.azuredatabricks.net
# Port: 443
# Login: token (username field)
# Password: your-api-token
# Extra JSON:
# {
#   "cluster_id": "cluster-xyz"
# }
```

#### Power BI Connection
```bash
# Connection ID: powerbi_default
# Conn Type: Generic
# Host: api.powerbi.com
# Extra JSON:
# {
#   "client_id": "your-client-id",
#   "client_secret": "your-client-secret",
#   "tenant_id": "your-tenant-id"
# }
```

### 3. Set Airflow Variables

```bash
# In Airflow Web UI: Admin → Variables → Create

# Variable: powerbi_workspace_id
# Value: your-workspace-id

# Variable: powerbi_dataset_id
# Value: your-dataset-id
```

---

## 📊 DAG Overview

### enterprise_integration_dag.py

**Purpose**: Complete data pipeline demonstration

**Flow**:
1. **Extract** (On-Premises) → Get data from SQL Server/PostgreSQL/MySQL
2. **Stage** (Azure Storage) → Upload to Azure Blob Storage
3. **Transform** (Databricks) → Clean, aggregate, and create metrics
4. **Refresh** (Power BI) → Refresh datasets
5. **Validate** → Verify pipeline success

**Execution Time**: ~10-15 minutes (configurable)

**Data Volume**: Scales from 1K to 1M+ rows

---

## 🎯 Using the Connectors

### Example 1: Extract from On-Premises

```python
from src.connectors import fetch_from_onprem

config = {
	'host': 'on-prem-server.company.com',
	'port': 1433,
	'database': 'sales_db',
	'username': 'user',
	'password': 'pass'
}

data = fetch_from_onprem(
	source_type='sql_server',
	config=config,
	query='SELECT * FROM SalesData WHERE Date >= GETDATE()-1'
)

print(f"Extracted {len(data)} records")
```

### Example 2: Upload to Azure Storage

```python
from src.connectors import get_azure_storage_connector
import pandas as pd

connector = get_azure_storage_connector(conn_id='azure_default')

# Upload DataFrame
df = pd.read_csv('data.csv')
connector.upload_dataframe(
	df=df,
	container_name='staging',
	blob_name='sales/data_2024-01-01.csv',
	format='csv'
)

# Or download
df = connector.download_dataframe(
	container_name='staging',
	blob_name='sales/data_2024-01-01.csv',
	format='csv'
)
```

### Example 3: Transform in Databricks

```python
from src.connectors import get_databricks_connector

databricks = get_databricks_connector(conn_id='databricks_default')

# Run query
result = databricks.run_query('''
	SELECT 
		product,
		SUM(amount) as total_sales,
		COUNT(*) as transaction_count
	FROM sales_raw
	GROUP BY product
''')

print(f"Query returned {len(result)} rows")

# Create table
databricks.create_table_from_query(
	source_query='SELECT * FROM sales_raw WHERE date >= CURRENT_DATE() - 1',
	target_table='sales.daily_summary'
)
```

### Example 4: Refresh Power BI

```python
from src.connectors import get_powerbi_connector

powerbi = get_powerbi_connector(conn_id='powerbi_default')

# Refresh dataset
success = powerbi.refresh_dataset(
	workspace_id='workspace-id',
	dataset_id='dataset-id',
	wait_for_completion=True
)

# List datasets
datasets = powerbi.list_datasets('workspace-id')
for ds in datasets:
	print(f"Dataset: {ds['name']}")

# Trigger refresh and check status
success = powerbi.refresh_dataset(
	workspace_id='workspace-id',
	dataset_id='dataset-id',
	wait_for_completion=True,
	timeout=300
)
```

---

## 🔐 Security Best Practices

### 1. Never Hardcode Credentials
```python
# ❌ BAD
config = {'password': 'MyPassword123'}

# ✅ GOOD: Use Airflow Connections
from airflow.hooks.base import BaseHook
conn = BaseHook.get_connection('onprem_db')
```

### 2. Use Service Principals
```python
# For Power BI and Databricks, use service principals
# NOT user credentials
```

### 3. Secure Secrets
```bash
# Use Azure Key Vault for secrets
# Not environment variables or config files
```

### 4. Manage Permissions
- Least privilege access
- Role-based access control (RBAC)
- Separate dev/test/prod credentials

---

## 📝 Common Transformations

### Data Cleaning (Databricks)
```sql
CREATE OR REPLACE TABLE clean_data AS
SELECT 
	*,
	CURRENT_TIMESTAMP() as LoadedAt
FROM raw_data
WHERE 
	-- Remove nulls in key fields
	id IS NOT NULL 
	AND amount > 0
	-- Remove duplicates
	AND ROW_NUMBER() OVER (PARTITION BY id ORDER BY date DESC) = 1
```

### Aggregation (Databricks)
```sql
CREATE OR REPLACE TABLE daily_summary AS
SELECT 
	DATE(transaction_date) as date,
	product_category,
	COUNT(*) as transaction_count,
	SUM(amount) as total_sales,
	AVG(amount) as avg_amount,
	COUNT(DISTINCT customer_id) as unique_customers
FROM transactions
GROUP BY DATE(transaction_date), product_category
```

### Star Schema (Databricks)
```sql
-- Fact table
CREATE TABLE fact_sales AS
SELECT 
	fact_id,
	customer_id,
	product_id,
	store_id,
	date_id,
	amount,
	quantity
FROM transactions;

-- Dimension: Products
CREATE TABLE dim_product AS
SELECT DISTINCT
	product_id,
	product_name,
	category,
	price
FROM products;
```

---

## 🧪 Testing Your Setup

### Test On-Premises Connection
```bash
# In Python or terminal
python -c "
from src.connectors import fetch_from_onprem
data = fetch_from_onprem('sql_server', {...}, 'SELECT TOP 1 * FROM Table')
print('✓ On-Prem connection works')
"
```

### Test Azure Storage
```bash
# In Python
from src.connectors import get_azure_storage_connector
connector = get_azure_storage_connector()
blobs = connector.list_blobs('staging')
print(f'✓ Azure Storage works: {len(blobs)} blobs')
```

### Test Databricks
```bash
# In Python
from src.connectors import get_databricks_connector
databricks = get_databricks_connector()
result = databricks.run_query('SELECT 1 as test')
print('✓ Databricks works')
```

### Test Power BI
```bash
# In Python
from src.connectors import get_powerbi_connector
powerbi = get_powerbi_connector()
workspaces = powerbi.list_workspaces()
print(f'✓ Power BI works: {len(workspaces)} workspaces')
```

---

## 🐛 Troubleshooting

### Connection Issues

**"Connection refused"**
- Check hostname/IP address
- Verify firewall rules
- Confirm credentials are correct

**"Authentication failed"**
- Check token expiration (Databricks, Power BI)
- Verify credentials in Airflow Connection
- Check permissions/RBAC

**"Timeout"**
- Increase timeout in DAG
- Check network connectivity
- Verify on-premises server availability

### Data Issues

**"No data returned"**
- Check if query returns empty result
- Verify table/database exists
- Check date filters

**"Data mismatch"**
- Verify query logic
- Check data quality in source
- Validate transformations

### Power BI Issues

**"Dataset not found"**
- Verify workspace_id and dataset_id
- Check Power BI service status
- Verify credentials have access

**"Refresh timeout"**
- Increase wait_for_completion timeout
- Check Databricks data volume
- Monitor Power BI refresh history

---

## 📊 Monitoring

### Check DAG Runs
```bash
# View all runs
airflow dags list-runs -d enterprise_integration_pipeline

# View recent run
airflow dags list-runs -d enterprise_integration_pipeline --limit 1
```

### View Logs
```bash
# Scheduler logs
tail -f logs/scheduler/*.log

# Task logs
airflow tasks logs -d enterprise_integration_pipeline -t extract_from_onprem 2024-01-01
```

### Performance Metrics

Track in each task:
- **Extract**: Records fetched, query time
- **Stage**: Bytes uploaded, upload time
- **Transform**: Tables created, query execution time
- **Refresh**: Dataset refresh time, status
- **Validate**: Total pipeline time, success/failure

---

## 🚀 Next Steps

1. **Configure Connections** - Set up all 4 connections
2. **Set Variables** - Configure Power BI workspace/dataset IDs
3. **Test Connectivity** - Run test scripts for each connector
4. **Run DAG** - Trigger enterprise_integration_dag manually
5. **Monitor Execution** - Check logs and XCom values
6. **Customize** - Modify transforms for your data
7. **Schedule** - Set schedule_interval for your needs

---

## 📚 Additional Resources

- [Databricks Python API](https://docs.databricks.com/api/python/)
- [Azure Storage SDK](https://github.com/Azure/azure-sdk-for-python)
- [Power BI REST API](https://learn.microsoft.com/en-us/rest/api/power-bi/)
- [Airflow Connections](https://airflow.apache.org/docs/apache-airflow/stable/concepts/connections.html)

---

**Your enterprise integration POC is ready! 🚀**

Start by configuring the connections, then run `enterprise_integration_dag`.
