# Connect VS Code to AKS PostgreSQL (Windows)

This guide documents the steps to connect Visual Studio Code to the PostgreSQL database running in AKS by port-forwarding locally.

## Prerequisites
- Azure CLI installed: `winget install --id Microsoft.AzureCLI -e`
- VS Code installed with one of:
  - PostgreSQL (Chris Kolkman) extension
  - or SQLTools + SQLTools PostgreSQL Driver

## 1) Authenticate and fetch AKS credentials
```powershell
az login
az aks get-credentials --resource-group bi_lakehouse_dev_rg --name aks-airflow-poc --overwrite-existing
```

## 2) Install kubectl (if not already available)
```powershell
Invoke-WebRequest -Uri "https://dl.k8s.io/release/v1.28.0/bin/windows/amd64/kubectl.exe" -OutFile "$Env:USERPROFILE\kubectl.exe"
$env:Path += ";$Env:USERPROFILE"
# Verify
kubectl version --client
kubectl get nodes
```

## 3) Port-forward PostgreSQL (keep this terminal open)
```powershell
kubectl port-forward postgres-0 5432:5432 -n airflow
# Expect output like:
# Forwarding from 127.0.0.1:5432 -> 5432
```

## 4) Create connection in VS Code

### Option A: PostgreSQL (Chris Kolkman) extension
- Open PostgreSQL view (left sidebar) → New Connection
- Enter:
  - Host: `localhost`
  - Port: `5432`
  - Database: `airflow`
  - Username: `airflow`
  - Password: `airflow123`
  - SSL: Off
- Save name: `AKS Airflow PostgreSQL`

### Option B: SQLTools
- Install `mtxr.sqltools` and `mtxr.sqltools-driver-pg`
- Create a new connection:
  - Driver: PostgreSQL
  - Server: `localhost`
  - Port: `5432`
  - Database: `airflow`
  - Username: `airflow`
  - Password: `airflow123`
  - Name: `AKS Airflow PostgreSQL`

## 5) Verify with a test query
```sql
SELECT dag_id, is_paused, is_active, last_parsed_time
FROM dag
ORDER BY last_parsed_time DESC;
```

## Troubleshooting
- Ensure the port-forward terminal remains open and shows `Forwarding from 127.0.0.1:5432`.
- Reload VS Code: `Ctrl+Shift+P` → "Reload Window".
- Verify the database exists:
```powershell
kubectl exec -it postgres-0 -n airflow -- psql -U airflow -d airflow -c "SELECT current_database();"
```
- Firewall: allow local connections to `localhost:5432`.

## Notes
- Port-forwarding in Azure Cloud Shell binds to Cloud Shell’s localhost, not your PC. Always port-forward from your Windows machine for VS Code to connect.
