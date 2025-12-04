# Azure Blob Copy Generic DAG - Quick Reference

## 🎯 DAG Name: `azure_blob_copy_generic`

Simple, reusable DAG to copy files between any Azure Blob Storage containers.

## 🚀 How to Use

### 1. Open Airflow UI
http://51.8.246.115

### 2. Find DAG
Search for: `azure_blob_copy_generic`

### 3. Trigger with Config

Click **Trigger DAG w/ config** button and paste one of these examples:

---

## 📋 Usage Examples

### Example 1: Copy Single File

Copy one specific file to a different location:

```json
{
  "source_container": "raw-data",
  "target_container": "processed-data",
  "source_path": "sales/report.csv",
  "target_path": "archive/2024/sales/report.csv"
}
```

**What it does**: Copies `raw-data/sales/report.csv` → `processed-data/archive/2024/sales/report.csv`

---

### Example 2: Copy Entire Folder

Copy all files from one folder to another:

```json
{
  "source_container": "staging",
  "target_container": "production",
  "prefix": "daily-reports/2024-12-03/"
}
```

**What it does**: Copies all files in `staging/daily-reports/2024-12-03/` → `production/daily-reports/2024-12-03/`

---

### Example 3: Copy Only CSV Files

Copy only CSV files from a folder:

```json
{
  "source_container": "raw-data",
  "target_container": "analytics",
  "prefix": "exports/",
  "file_pattern": "*.csv"
}
```

**What it does**: Copies only `*.csv` files from `raw-data/exports/` → `analytics/exports/`

---

### Example 4: Copy Log Files by Date

Copy log files matching a pattern:

```json
{
  "source_container": "logs",
  "target_container": "archive-logs",
  "prefix": "application/2024-12/",
  "file_pattern": "app_*.log"
}
```

**What it does**: Copies files like `app_*.log` from `logs/application/2024-12/` → `archive-logs/application/2024-12/`

---

### Example 5: Your Seasonal Buy Files (Default)

Already configured as default:

```json
{
  "source_container": "sg-analytics-raw",
  "target_container": "airflow",
  "prefix": "seasonal_buy/2025-10-13/"
}
```

**What it does**: Copies all 40 files from seasonal buy folder

---

## ⚙️ Configuration Parameters

| Parameter | Required | Description | Example |
|-----------|----------|-------------|---------|
| `source_container` | ✅ Yes | Source container name | `"raw-data"` |
| `target_container` | ✅ Yes | Target container name | `"processed-data"` |
| `source_path` | ⬜ Optional | Single file path (for copying one file) | `"sales/data.csv"` |
| `target_path` | ⬜ Optional | Target path (if different from source) | `"archive/sales/data.csv"` |
| `prefix` | ⬜ Optional | Folder prefix for multiple files | `"reports/2024/"` |
| `file_pattern` | ⬜ Optional | File pattern to match | `"*.csv"`, `"data_*.txt"` |

---

## 🎮 Copy Modes

### Mode 1: Single File Copy
- Provide: `source_path`
- Optional: `target_path` (uses same path if not specified)
- Example: Copy one specific file

### Mode 2: Multiple Files Copy
- Provide: `prefix` and/or `file_pattern`
- Copies all matching files
- Preserves folder structure

---

## 📝 Real-World Examples

### Backup Daily Files
```json
{
  "source_container": "production-data",
  "target_container": "backup",
  "prefix": "daily-exports/2024-12-03/"
}
```

### Move Processed Files to Archive
```json
{
  "source_container": "processing",
  "target_container": "archive",
  "source_path": "completed/batch_123.csv",
  "target_path": "archive/2024/12/batch_123.csv"
}
```

### Copy Only Excel Files
```json
{
  "source_container": "reports",
  "target_container": "shared-reports",
  "prefix": "quarterly/",
  "file_pattern": "*.xlsx"
}
```

### Replicate Entire Dataset
```json
{
  "source_container": "master-data",
  "target_container": "dev-data",
  "prefix": ""
}
```

---

## ✅ Success Indicators

After triggering, check the logs:

**Single File Mode:**
```
✓ File copied successfully!
Status: success
Files copied: 1
```

**Multiple Files Mode:**
```
Found 40 files to copy
  ✓ Copied: file1.txt
  ✓ Copied: file2.txt
  ...
Copy completed: 40 succeeded, 0 failed
```

---

## 🔍 Monitoring

### In Airflow UI:
1. Click on DAG run
2. Click on `copy_files` task
3. View logs for progress
4. Check return value for summary

### In Azure Portal:
1. Go to Storage Account
2. Open target container
3. Verify files appeared

---

## 🛠️ Troubleshooting

### "Connection 'azure_blob_default' not found"
**Fix**: Create the connection first (see main setup guide)

### "Source file not found"
**Fix**: Check `source_path` is correct and file exists

### "Container not found"
**Fix**: Create target container first:
```powershell
az storage container create --name YOUR_CONTAINER --account-name sgbilakehousestoragedev
```

### No files copied (0 matched)
**Fix**: Check `prefix` and `file_pattern` are correct

---

## 💡 Pro Tips

1. **Test with single file first** - Use `source_path` to copy one file and verify it works

2. **Use prefix for organization** - Keep folder structure by using `prefix`

3. **Pattern matching** - Use `*.csv`, `*.txt`, `data_*`, etc. to filter files

4. **Same path vs different path**:
   - Omit `target_path` to keep same folder structure
   - Specify `target_path` to reorganize files

5. **Check logs** - Always check task logs for detailed progress

---

## 🎯 Quick Start (3 Steps)

1. **Ensure connection exists**: `azure_blob_default` in Airflow connections

2. **Trigger DAG** with your config (copy any example above)

3. **Monitor** the task logs to see progress

That's it! 🚀

---

## 📚 Related Documentation

- Full setup: `docs/AZURE_BLOB_COPY_SETUP.md`
- Other example: `dags/azure_blob_copy_seasonal_buy.py`
- Storage key script: `scripts/get-azure-storage-key.ps1`

---

**Storage Account**: sgbilakehousestoragedev  
**Airflow UI**: http://51.8.246.115
