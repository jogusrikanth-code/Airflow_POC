# 🔌 Connect VS Code to AKS PostgreSQL (Windows)

**Hey there!** 👋 Want to explore your Airflow database directly from VS Code? This guide will show you how to connect Visual Studio Code to the PostgreSQL database running in your AKS cluster using port-forwarding.

> **Why do this?** Being able to query your database directly is super useful for debugging, monitoring DAG runs, and understanding how Airflow stores its data. Plus, VS Code's database tools are way nicer than command-line psql!

## ✅ What You'll Need

**Software Requirements:**
- ✨ Azure CLI installed (run: `winget install --id Microsoft.AzureCLI -e`)
- 💻 VS Code with ONE of these extensions:
  - **Option A:** PostgreSQL by Chris Kolkman (simple and focused)
  - **Option B:** SQLTools + SQLTools PostgreSQL Driver (more features)

> 🤔 **Not sure which extension?** Go with PostgreSQL by Chris Kolkman if you just want to explore the database. Choose SQLTools if you work with multiple database types.

## 🔧 Step-by-Step Setup

### 1️⃣ Authenticate with Azure

First, let's get you connected to your Azure account:

```powershell
az login
az aks get-credentials --resource-group bi_lakehouse_dev_rg --name aks-airflow-poc --overwrite-existing
```

✅ **Success looks like:** You'll see "Merged 'aks-airflow-poc' as current context in ~/.kube/config"

---

### 2️⃣ Install kubectl (if needed)

Check if you already have it:
```powershell
kubectl version --client
```

If that errors, install it:
```powershell
Invoke-WebRequest -Uri "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe" -OutFile "$Env:USERPROFILE\kubectl.exe"
$env:Path += ";$Env:USERPROFILE"

# Verify it works
kubectl version --client
kubectl get nodes
```

✅ **Success looks like:** You see your 3 AKS nodes listed and ready

---

### 3️⃣ Port-Forward PostgreSQL

> ⚠️ **Important:** Keep this terminal window open the entire time you're using VS Code to connect!

```powershell
kubectl port-forward postgres-0 5432:5432 -n airflow
```

✅ **Success looks like:** 
```
Forwarding from 127.0.0.1:5432 -> 5432
Forwarding from [::1]:5432 -> 5432
```

> 💡 **Pro Tip:** If you see "port 5432 is already in use", something else on your machine is using that port (maybe a local PostgreSQL?). Stop that service or use a different port like `5433:5432`.

### 4️⃣ Create Connection in VS Code

#### 🎯 Option A: PostgreSQL Extension (Chris Kolkman)

1. **Open the PostgreSQL panel**
   - Click the PostgreSQL icon in the left sidebar (looks like an elephant)
   - Or press `Ctrl+Shift+P` and type: **PostgreSQL: New Connection**

2. **Fill in connection details:**
   ```
   📍 Host:     localhost
   🔢 Port:     5432
   🗄️ Database: airflow
   👤 Username: airflow
   🔐 Password: airflow123
   ❌ SSL:      Off/Disabled
   ```

3. **Save with a friendly name:** `AKS Airflow PostgreSQL`

✅ **Success looks like:** You'll see the connection appear in the sidebar with all the Airflow tables!

---

#### 🎯 Option B: SQLTools (if you prefer)

1. Install both extensions:
   - `mtxr.sqltools`
   - `mtxr.sqltools-driver-pg`

2. Click the SQLTools icon in sidebar → **New Connection**

3. Choose **PostgreSQL** driver and enter the same details as above

---

> 🤔 **Connection not working?**
> - Double-check the port-forward terminal is still running
> - Try `localhost` instead of `127.0.0.1` (or vice versa)
> - Restart VS Code: `Ctrl+Shift+P` → "Reload Window"
> - Check Windows Firewall isn't blocking localhost:5432

### 5️⃣ Test Your Connection

Let's run some fun queries to explore your Airflow data! 🔍

#### 🎯 See all your DAGs
```sql
SELECT dag_id, is_paused, is_active, last_parsed_time
FROM dag
ORDER BY last_parsed_time DESC;
```

#### 📊 Check DAG run success rates
```sql
SELECT 
    dag_id,
    state,
    COUNT(*) as run_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY dag_id), 2) as percentage
FROM dag_run
GROUP BY dag_id, state
ORDER BY dag_id, state;
```

#### ⏱️ Find your slowest tasks
```sql
SELECT 
    dag_id, 
    task_id, 
    state,
    ROUND(EXTRACT(EPOCH FROM (end_date - start_date))/60, 2) as duration_minutes
FROM task_instance
WHERE start_date > NOW() - INTERVAL '7 days'
    AND state = 'success'
ORDER BY duration_minutes DESC
LIMIT 20;
```

#### 🔍 Debug recent failures
```sql
SELECT 
    dag_id,
    task_id,
    execution_date,
    state,
    start_date,
    end_date
FROM task_instance
WHERE state IN ('failed', 'up_for_retry')
    AND start_date > NOW() - INTERVAL '24 hours'
ORDER BY start_date DESC;
```

> 💡 **Pro Tip:** Bookmark these queries! They're super handy for monitoring and debugging your pipelines.

## 🔧 Troubleshooting

### ❌ "Connection refused" or "Database does not exist"

**Quick fixes:**
```powershell
# 1. Verify the port-forward is running
kubectl get pods -n airflow | findstr postgres
# Should show: postgres-0   1/1   Running

# 2. Test direct connection from command line
kubectl exec -it postgres-0 -n airflow -- psql -U airflow -d airflow -c "SELECT current_database();"
# Should return: airflow

# 3. Check if another app is using port 5432
netstat -ano | findstr :5432
```

---

### ❌ VS Code doesn't show the connection

1. **Reload VS Code:** `Ctrl+Shift+P` → "Reload Window"
2. **Check extension is installed:** Extensions panel → search "PostgreSQL"
3. **Verify settings file:** Look at `.vscode/settings.json` in your workspace

---

### ❌ "SSL mode not supported" error

Make sure SSL is set to **Off** or **Disable** in your connection settings.

---

### ⚠️ Port-forward from Azure Cloud Shell Won't Work!

**The Problem:** Cloud Shell's `localhost` is in Azure, not on your PC!

**The Solution:** Always run `kubectl port-forward` from your local Windows PowerShell after installing Azure CLI locally.

---

> 👥 **Still stuck?** Check that:
> - ✅ OneDrive isn't syncing/locking files if repo is in OneDrive folder
> - ✅ Windows Firewall allows localhost connections
> - ✅ No VPN is interfering with localhost routing
> - ✅ You're using the correct password: `airflow123`

## 📝 Notes

### 👍 Best Practices

- **Never run port-forward in Azure Cloud Shell for VS Code access** - It binds to Cloud Shell's localhost, not yours!
- **Keep the port-forward terminal visible** - Easy to see if it disconnects
- **Use a different port if 5432 is busy** - Try `kubectl port-forward postgres-0 5433:5432 -n airflow`

### ⚡ Quick Reference Card

| What | Command |
|------|--------|
| **Start port-forward** | `kubectl port-forward postgres-0 5432:5432 -n airflow` |
| **Check PostgreSQL pod** | `kubectl get pod postgres-0 -n airflow` |
| **Test connection** | `kubectl exec -it postgres-0 -n airflow -- psql -U airflow -d airflow -c "\dt"` |
| **View logs** | `kubectl logs postgres-0 -n airflow` |
| **Restart PostgreSQL** | `kubectl delete pod postgres-0 -n airflow` (will auto-recreate) |

---

## 🎉 You're All Set!

You can now explore your Airflow database directly from VS Code! Try running some of the example queries above to see your DAG runs, task instances, and more.

**What's Next?**
- 📊 Build custom dashboards by joining tables
- 🔍 Debug DAG failures with SQL queries  
- 📝 Document your database schema
- ⚡ Optimize slow queries

Happy querying! 🚀
