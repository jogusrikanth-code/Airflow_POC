# ⚡ Quickstart — Get Airflow Running in 30 Minutes!

Hey there! Ready to see Airflow in action? This guide will have you in the Airflow UI in no time. We'll show you two deployment methods: a quick local dev setup and a production-ready Helm approach for teams. 🚀

## 🎯 What You'll Achieve

By the end of this guide, you'll have:
- ✅ Airflow running on your local Kubernetes cluster
- ✅ Access to the Airflow web UI at `http://localhost:8080`
- ✅ An admin account configured and ready
- ✅ Your first DAG pipeline (`enterprise_integration_pipeline`) loaded and running

> **Time Estimate:** 20-30 minutes depending on your method

---

## 🛤️ Choose Your Path

### Method 1: Quick Local Dev (hostPath Mounts) 🏃‍♂️
**Best for:** Solo developers, quick testing, local development  
**Time:** 10-15 minutes  
**Pros:** Fast, simple, immediate changes to DAGs

### Method 2: Production-Ready Helm (Git Sync) 🏢
**Best for:** Teams, production environments, CI/CD workflows  
**Time:** 20-30 minutes  
**Pros:** Automated DAG updates, version control, team collaboration

---

## 🏃‍♂️ Method 1: Quick Local Dev with Kubernetes Manifests

Perfect for getting started quickly! Your DAGs will be mounted directly from your local filesystem.

### Step 1️⃣: Deploy to Kubernetes

```powershell
# Deploy all Airflow resources
kubectl apply -f kubernetes/airflow.yaml
```

> **Hit an immutable selector error on webserver?** No worries! Just recreate it:
> ```powershell
> kubectl delete deploy airflow-webserver -n airflow --ignore-not-found=true
> kubectl apply -f kubernetes/airflow.yaml
> ```

**Wait for rollout to complete:**
```powershell
kubectl rollout status deploy/airflow-webserver -n airflow
```

✅ **Success looks like:** `deployment "airflow-webserver" successfully rolled out`

### Step 2️⃣: Access the Airflow UI

Open your browser and head to: **http://localhost:8080** 🌐

You should see the Airflow login page!

### Step 3️⃣: Create Your Admin User

```powershell
# Get the webserver pod name
$pod = (kubectl get pods -n airflow | Select-String "airflow-webserver-" | ForEach-Object { ($_ -split "\s+")[0] } | Select-Object -First 1)

# Create a new admin user
kubectl exec -it -n airflow $pod -- airflow users create `
  --username admin `
  --password "YourStrongPassword123!" `
  --firstname Admin `
  --lastname User `
  --role Admin `
  --email admin@example.com
```

> **Already have an admin user?** Reset the password instead:
> ```powershell
> kubectl exec -it -n airflow $pod -- airflow users set-password -u admin -p "NewStrongPassword123!"
> ```

### Step 4️⃣: Activate Your First DAG

1. Log in to the Airflow UI with your admin credentials
2. Find the DAG named `enterprise_integration_pipeline`
3. Click the toggle switch to **unpause** it 🟢

✅ **Success looks like:** The DAG should now be active and visible in the dashboard!

### ⚠️ Important: Local Path Configuration

The Kubernetes manifests mount your local repo into pods using Docker Desktop's Linux VM path. If your DAGs aren't showing up:

1. Check your Windows path in `kubernetes/airflow.yaml`
2. Update the `hostPath` entries if your location differs
3. See `SETUP_SUMMARY.md` for detailed path configuration

---

## 🏢 Method 2: Production-Ready Helm Deployment with Git Sync

This method automatically pulls DAGs from your Git repository—perfect for teams and production environments!

### Step 1️⃣: Add the Official Airflow Helm Repository

```powershell
helm repo add apache-airflow https://airflow.apache.org
helm repo update
```

✅ **Success looks like:** `Successfully got an update from the "apache-airflow" chart repository`

### Step 2️⃣: Configure Git Sync in helm-values.yaml

Open `kubernetes/helm-values.yaml` and find the `dags.gitSync` section. Uncomment and configure it:

```yaml
dags:
  persistence:
    enabled: false
  gitSync:
    enabled: true
    repo: "https://github.com/your-org/Airflow_POC.git"  # 👈 Change this!
    branch: "master"
    subPath: "dags"
    depth: 1
    syncWait: 60  # Sync every 60 seconds
```

> **💡 Pro Tip:** Use `syncWait: 60` for development (faster updates) and `syncWait: 300` for production (less load).

### Step 3️⃣: Deploy Airflow with Helm

```powershell
helm upgrade --install airflow apache-airflow/airflow `
  -n airflow `
  -f kubernetes/helm-values.yaml `
  --create-namespace
```

**Wait for pods to be ready:**
```powershell
kubectl get pods -n airflow -w
```

✅ **Success looks like:** All pods showing `Running` status with `1/1` or `2/2` ready containers

### Step 4️⃣: Access UI and Create Admin User

1. **Open the UI:** http://localhost:8080 🌐
2. **Create admin user** (same as Method 1):

```powershell
$pod = (kubectl get pods -n airflow | Select-String "airflow-webserver-" | ForEach-Object { ($_ -split "\s+")[0] } | Select-Object -First 1)

kubectl exec -it -n airflow $pod -- airflow users create `
  --username admin `
  --password "YourStrongPassword123!" `
  --firstname Admin `
  --lastname User `
  --role Admin `
  --email admin@example.com
```

### Step 5️⃣: Verify Git Sync is Working

Check that DAGs are being synced from your repository:

```powershell
# List DAGs in the scheduler
kubectl exec -n airflow deploy/airflow-scheduler -- airflow dags list
```

✅ **Success looks like:** You should see your DAGs listed (e.g., `enterprise_integration_pipeline`)

---

## 🐛 Troubleshooting

### No DAGs Showing Up?

**Check if DAGs are imported:**
```powershell
$pod = (kubectl get pods -n airflow | Select-String "airflow-webserver-" | ForEach-Object { ($_ -split "\s+")[0] } | Select-Object -First 1)
kubectl exec -it -n airflow $pod -- airflow dags list
```

**Check for import errors:**
```powershell
kubectl exec -it -n airflow $pod -- airflow dags list-import-errors
```

> **Common causes:**
> - **Method 1 (hostPath):** Wrong local path in `airflow.yaml`
> - **Method 2 (git-sync):** Wrong repo URL, branch, or subPath
> - **Both:** Missing Python dependencies (check `requirements.txt`)

### Can't Log In?

**Reset your admin password:**
```powershell
$pod = (kubectl get pods -n airflow | Select-String "airflow-webserver-" | ForEach-Object { ($_ -split "\s+")[0] } | Select-Object -First 1)
kubectl exec -it -n airflow $pod -- airflow users set-password -u admin -p "NewPassword123!"
```

### Import Errors on `src/` Modules?

If your DAGs import from `src/` (like `from src.transform import ...`):

**For Method 1 (hostPath):** We mount `src/` alongside `dags/`, so it should work automatically.

**For Method 2 (git-sync):** You need to either:
- Include `src/` in your Git repository under the `dags/` folder, OR
- Build a custom Docker image with your `src/` modules pre-installed

See `SETUP_SUMMARY.md` for more details on module paths.

### Pods Not Starting?

**Check pod status and logs:**
```powershell
kubectl get pods -n airflow
kubectl logs -n airflow deploy/airflow-scheduler --tail=50
kubectl logs -n airflow deploy/airflow-webserver --tail=50
```

> **Common issues:**
> - Database not ready → Wait for `postgres-0` to be `Running`
> - Image pull errors → Check your Docker registry access
> - Resource limits → Increase CPU/memory in `helm-values.yaml`

---

## 🎉 What's Next?

Now that Airflow is running, here's your next steps:

1. **Learn Airflow Basics** → Check out [AIRFLOW_BASICS.md](AIRFLOW_BASICS.md) for DAG tutorials
2. **Explore the UI** → Navigate to DAGs, click into `enterprise_integration_pipeline`, and trigger a manual run
3. **Connect the Database** → Use [POSTGRES_VSCODE_CONNECTION.md](POSTGRES_VSCODE_CONNECTION.md) to query task states
4. **Build Your First DAG** → Follow examples in [AIRFLOW_BASICS.md](AIRFLOW_BASICS.md)

> **💡 Pro Tip:** Keep the logs open in a separate terminal while developing:
> ```powershell
> kubectl logs -n airflow deploy/airflow-scheduler -f
> ```

---

**Happy DAG Building! 🚀** You're now ready to orchestrate workflows like a pro!
