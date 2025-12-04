# Azure Blob Copy Generic DAG - Quick Reference

## 🎯 DAG Name: `azure_blob_copy_generic`

Super simple DAG to copy files between Azure Blob Storage containers.

## 🚀 How to Use (3 Easy Steps)

### 1. Open Airflow UI
http://51.8.246.115

### 2. Find the DAG
Search for: `azure_blob_copy_generic`

### 3. Trigger with Your Settings

Click **Trigger DAG w/ config** and enter:

```json
{
  "source_container": "where-files-are",
  "target_container": "where-to-copy",
  "folder_path": "path/to/folder/"
}
```

That's it! 🎉

---

## 📋 Real Examples

### Example 1: Copy Seasonal Buy Files (Default)
```json
{
  "source_container": "sg-analytics-raw",
  "target_container": "airflow",
  "folder_path": "seasonal_buy/2025-10-13/"
}
```

### Example 2: Copy Daily Reports
```json
{
  "source_container": "staging",
  "target_container": "production",
  "folder_path": "daily-reports/2024-12-03/"
}
```

### Example 3: Copy Sales Data
```json
{
  "source_container": "raw-data",
  "target_container": "analytics",
  "folder_path": "sales/december/"
}
```

### Example 4: Backup Files
```json
{
  "source_container": "production-data",
  "target_container": "backup",
  "folder_path": "exports/2024/"
}
```

---

## ⚙️ Parameters (Only 3!)

| Parameter | What it does | Example |
|-----------|--------------|---------|
| `source_container` | Container to copy FROM | `"raw-data"` |
| `target_container` | Container to copy TO | `"processed-data"` |
| `folder_path` | Folder to copy | `"sales/2024-12/"` |

---

## ✅ What Happens

1. **Finds all files** in source container's folder
2. **Copies each file** to target container
3. **Keeps same folder structure**
4. **Shows progress** in logs

---

## 🔍 Check Progress

In Airflow UI:
1. Click on the DAG run
2. Click on `copy_files` task  
3. Click **Logs**
4. You'll see:
   ```
   Found 40 files to copy
     Copying: file1.txt
     ✓ Success
     Copying: file2.txt
     ✓ Success
   Done! Copied 40 files, 0 failed
   ```

---

## 🛠️ Troubleshooting

**"Connection not found"**  
→ Create `azure_blob_default` connection first (see main setup guide)

**"No files found"**  
→ Check `folder_path` is correct

**"Container not found"**  
→ Create the target container first

---

## 💡 Tips

- Leave trailing `/` in folder_path: `"sales/2024/"`
- Copies **all files** in that folder
- Files keep their original names and structure
- Safe to re-run (overwrites existing files)

---

**Storage Account**: sgbilakehousestoragedev  
**Airflow UI**: http://51.8.246.115
