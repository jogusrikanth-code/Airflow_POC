# Complete Guide: Deploying Apache Airflow 3.0.2 on Azure Kubernetes Service (AKS)

**Author:** Srikanth Jogu  
**Date:** December 3, 2025  
**Airflow Version:** 3.0.2  
**Kubernetes Version:** 1.32.9  
**Deployment Method:** Helm Chart via Azure Cloud Shell  

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture](#architecture)
4. [Step-by-Step Deployment](#step-by-step-deployment)
5. [Accessing the System](#accessing-the-system)
6. [Setting Up a New Developer](#setting-up-a-new-developer)
7. [Troubleshooting Guide](#troubleshooting-guide)
8. [Verification](#verification)
9. [Next Steps](#next-steps)

---

## Overview

This guide documents the complete process of deploying Apache Airflow 3.0.2 on Azure Kubernetes Service (AKS) with:
- **Executor:** KubernetesExecutor (no Redis/Celery needed)
- **Database:** PostgreSQL 15-alpine (deployed as StatefulSet in AKS)
- **DAG Sync:** Git-sync from GitHub repository
- **UI Access:** LoadBalancer service with external IP
- **Storage:** Azure Blob Storage integration for logs (optional)

**Key Decisions:**
- Used Azure Portal for AKS cluster creation (simpler than CLI for initial setup)
- Used Azure Cloud Shell for kubectl/helm commands (pre-configured, no local installation needed)
- Deployed PostgreSQL in-cluster instead of Azure Database for PostgreSQL (cost-effective for POC, no provider registration needed)
- Used KubernetesExecutor for simpler architecture (each task runs in isolated pod)

---

## Prerequisites

### Azure Resources
- **Azure Subscription:** Active subscription with permissions to create resources
- **Resource Group:** `bi_lakehouse_dev_rg` (existing or create new)
- **Storage Account:** `sgbilakehousestoragedev` (existing, for optional log persistence)

### Tools & Access
- **Azure Portal Access:** https://portal.azure.com
- **Azure Cloud Shell:** Accessible from Azure Portal (top-right icon)
- **GitHub Repository:** https://github.com/jogusrikanth-code/Airflow_POC.git

### Knowledge Requirements
- Basic Kubernetes concepts (pods, deployments, services)
- Basic Helm chart usage
- Git basics

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Kubernetes Service                 │
│                      (aks-airflow-poc)                       │
│                                                              │
│  ┌─────────────────┐      ┌──────────────────┐             │
│  │   Namespace:    │      │  PostgreSQL 15   │             │
│  │    airflow      │      │   StatefulSet    │             │
│  │                 │      │  (postgres-0)    │             │
│  └─────────────────┘      └──────────────────┘             │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Airflow Components                       │  │
│  │                                                        │  │
│  │  • airflow-scheduler (2 replicas)                    │  │
│  │  • airflow-triggerer (3 replicas)                    │  │
│  │  • airflow-dag-processor (1 replica)                 │  │
│  │  • airflow-api-server (1 replica)                    │  │
│  │  • airflow-statsd (1 replica)                        │  │
│  │                                                        │  │
│  │  Git-sync sidecar: pulls DAGs from GitHub           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           LoadBalancer Service                        │  │
│  │     airflow-ui-lb → External IP: 51.8.246.115       │  │
│  │     Port 80 → airflow-api-server:8080                │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
              │
              │ Internet Access
              ▼
        User's Browser
     http://51.8.246.115
```

**Data Flow:**
1. User commits DAGs to GitHub
2. Git-sync pulls DAGs into pods every 5 seconds
3. Dag-processor scans `/opt/airflow/dags/repo/dags` for Python files
4. Scheduler creates task pods via KubernetesExecutor
5. UI accessible via LoadBalancer external IP

---

## Step-by-Step Deployment

### Phase 1: Create AKS Cluster (Azure Portal)

1. **Navigate to Azure Portal**
   - Go to https://portal.azure.com
   - Search for "Kubernetes services" in the top search bar
   - Click "Create" → "Create a Kubernetes cluster"

2. **Configure Basics Tab**
   - **Subscription:** Select your subscription
   - **Resource Group:** `bi_lakehouse_dev_rg`
   - **Cluster name:** `aks-airflow-poc`
   - **Region:** `East US` (or your preferred region)
   - **Kubernetes version:** `1.32.9` (or latest stable)
   - **Node size:** `Standard_D2s_v3` (2 vCPUs, 8 GB RAM - cost-effective)
   - **Node count:** `3` (for high availability)

3. **Configure Node Pools Tab**
   - Keep default settings (system node pool)
   - Enable autoscaling if desired (min: 3, max: 5)

4. **Configure Networking Tab**
   - **Network configuration:** Azure CNI or Kubenet (Azure CNI recommended)
   - **Load balancer:** Standard
   - **Enable HTTP application routing:** No (not needed)

5. **Configure Integrations Tab**
   - **Container registry:** None (using public Docker Hub images)
   - **Azure Monitor:** Enable if desired (optional for POC)

6. **Review + Create**
   - Review all settings
   - Click "Create"
   - Wait 5-10 minutes for cluster provisioning

7. **Verify Cluster Creation**
   - Once deployed, click "Go to resource"
   - Note the cluster name: `aks-airflow-poc`

---

### Phase 2: Connect to AKS Cluster (Azure Cloud Shell)

1. **Open Azure Cloud Shell**
   - In Azure Portal, click the Cloud Shell icon (top-right, looks like `>_`)
   - Select "Bash" or "PowerShell" (Bash recommended)
   - Wait for shell to initialize

2. **Get AKS Credentials**
   ```bash
   # Connect kubectl to your AKS cluster
   az aks get-credentials \
     --resource-group bi_lakehouse_dev_rg \
     --name aks-airflow-poc
   ```

3. **Verify Connection**
   ```bash
   # Check cluster nodes
   kubectl get nodes
   
   # Expected output: 3 nodes in Ready state
   # NAME                                STATUS   ROLES   AGE   VERSION
   # aks-nodepool1-12345678-vmss000000   Ready    agent   5m    v1.32.9
   # aks-nodepool1-12345678-vmss000001   Ready    agent   5m    v1.32.9
   # aks-nodepool1-12345678-vmss000002   Ready    agent   5m    v1.32.9
   ```

---

### Phase 3: Create Kubernetes Namespace and Secrets

1. **Create Airflow Namespace**
   ```bash
   kubectl create namespace airflow
   ```

2. **Create Webserver Secret Key**
   ```bash
   # Generate a random Flask secret key
   WEBSECRET=$(openssl rand -base64 32)
   
   kubectl create secret generic airflow-webserver-secret \
     --from-literal=webserver-secret-key=$WEBSECRET \
     --namespace airflow
   ```

3. **Create Azure Storage Secret (Optional - for log persistence)**
   ```bash
   # Replace with your actual storage account credentials
   STORAGE_ACCOUNT_NAME="sgbilakehousestoragedev"
   STORAGE_ACCOUNT_KEY="***REDACTED***"
   
   kubectl create secret generic airflow-storage \
     --from-literal=storage-account-name=$STORAGE_ACCOUNT_NAME \
     --from-literal=storage-account-key=$STORAGE_ACCOUNT_KEY \
     --namespace airflow
   ```

---

### Phase 4: Deploy PostgreSQL Database

**Why in-cluster PostgreSQL?**
- Azure Database for PostgreSQL requires provider registration (may need subscription admin)
- In-cluster deployment is cost-effective for POC/dev environments
- Suitable for development; use Azure Database for production

1. **Create PostgreSQL Deployment File**
   
   Create `postgres-standalone.yaml`:
   ```yaml
   apiVersion: v1
   kind: Service
   metadata:
     name: postgres-service
     namespace: airflow
   spec:
     selector:
       app: postgres
     ports:
       - protocol: TCP
         port: 5432
         targetPort: 5432
     clusterIP: None  # Headless service
   ---
   apiVersion: apps/v1
   kind: StatefulSet
   metadata:
     name: postgres
     namespace: airflow
   spec:
     serviceName: postgres-service
     replicas: 1
     selector:
       matchLabels:
         app: postgres
     template:
       metadata:
         labels:
           app: postgres
       spec:
         containers:
         - name: postgres
           image: postgres:15-alpine
           ports:
           - containerPort: 5432
             name: postgres
           env:
           - name: POSTGRES_USER
             value: "airflow"
           - name: POSTGRES_PASSWORD
             value: "airflow123"
           - name: POSTGRES_DB
             value: "airflow"
           - name: PGDATA
             value: /var/lib/postgresql/data/pgdata
           volumeMounts:
           - name: postgres-storage
             mountPath: /var/lib/postgresql/data
     volumeClaimTemplates:
     - metadata:
         name: postgres-storage
       spec:
         accessModes: [ "ReadWriteOnce" ]
         resources:
           requests:
             storage: 10Gi
   ```

2. **Deploy PostgreSQL**
   ```bash
   # Apply the manifest
   kubectl apply -f postgres-standalone.yaml
   
   # Wait for PostgreSQL to be ready
   kubectl wait --for=condition=ready pod/postgres-0 -n airflow --timeout=300s
   
   # Verify deployment
   kubectl get pods -n airflow
   # Expected: postgres-0   1/1   Running
   ```

3. **Test PostgreSQL Connection**
   ```bash
   # Connect to PostgreSQL pod and test
   kubectl exec -it postgres-0 -n airflow -- psql -U airflow -d airflow -c "SELECT version();"
   ```

---

### Phase 5: Install Airflow via Helm

1. **Add Airflow Helm Repository**
   ```bash
   helm repo add apache-airflow https://airflow.apache.org
   helm repo update
   ```

2. **Create Helm Values File**
   
   Create `values-aks-airflow.yaml` in Cloud Shell:
   ```yaml
   # Executor Configuration
   executor: "KubernetesExecutor"
   
   # Airflow Image
   images:
     airflow:
       repository: apache/airflow
       tag: 3.0.2-python3.11
       pullPolicy: IfNotPresent
   
   # PostgreSQL Configuration (External)
   postgresql:
     enabled: false  # Using our own PostgreSQL deployment
   
   # Database Connection
   data:
     metadataConnection:
       user: airflow
       pass: airflow123
       protocol: postgresql
       host: postgres-service
       port: 5432
       db: airflow
   
   # Redis (Not needed for KubernetesExecutor)
   redis:
     enabled: false
   
   # Airflow Configuration
   config:
     core:
       dags_folder: /opt/airflow/dags/repo/dags
       load_examples: "False"
       dag_discovery_safe_mode: "False"
     webserver:
       expose_config: "True"
     kubernetes_executor:
       namespace: airflow
       delete_worker_pods: "True"
   
   # DAG Deployment via Git-Sync
   dags:
     gitSync:
       enabled: true
       repo: https://github.com/jogusrikanth-code/Airflow_POC.git
       branch: master
       subPath: dags
       wait: 5  # Poll every 5 seconds
   
   # Scheduler Configuration
   scheduler:
     replicas: 1
   
   # Triggerer Configuration
   triggerer:
     enabled: true
     replicas: 3
   
   # Webserver Configuration
   webserver:
     enabled: true
     replicas: 1
     service:
       type: LoadBalancer  # Expose externally
     defaultUser:
       enabled: true
       username: admin
       password: admin123
   
   # RBAC
   rbac:
     create: true
   
   # Service Account
   serviceAccount:
     create: true
   
   # Environment Variables (Critical for imports)
   env:
     - name: PYTHONPATH
       value: /opt/airflow/dags/repo
   ```

3. **Install Airflow**
   ```bash
   helm install airflow apache-airflow/airflow \
     --namespace airflow \
     --values values-aks-airflow.yaml \
     --timeout 15m
   ```

4. **Monitor Installation**
   ```bash
   # Watch pods come up
   kubectl get pods -n airflow --watch
   
   # Wait for all pods to be Running (may take 2-5 minutes)
   # Press Ctrl+C to stop watching
   ```

5. **Expected Pod Status**
   ```
   NAME                                   READY   STATUS    RESTARTS   AGE
   airflow-api-server-xxxxx               1/1     Running   0          3m
   airflow-dag-processor-xxxxx            3/3     Running   0          3m
   airflow-scheduler-xxxxx                2/2     Running   0          3m
   airflow-statsd-xxxxx                   1/1     Running   0          3m
   airflow-triggerer-0                    3/3     Running   0          3m
   postgres-0                             1/1     Running   0          10m
   ```

---

### Phase 6: Expose Airflow UI

**Issue:** In Airflow 3.0, the Helm chart may not automatically create a LoadBalancer service for the UI.

**Solution:** Manually expose the api-server as a LoadBalancer.

1. **Check Existing Services**
   ```bash
   kubectl get svc -n airflow
   
   # You'll see services, but likely no LoadBalancer with external IP
   ```

2. **Expose API Server**
   ```bash
   kubectl expose deployment airflow-api-server \
     -n airflow \
     --type=LoadBalancer \
     --name=airflow-ui-lb \
     --port=80 \
     --target-port=8080
   ```

3. **Wait for External IP Assignment**
   ```bash
   kubectl get svc airflow-ui-lb -n airflow --watch
   
   # Wait until EXTERNAL-IP shows an IP address (1-3 minutes)
   # NAME            TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
   # airflow-ui-lb   LoadBalancer   10.0.66.56   51.8.246.115    80:32623/TCP   2m
   
   # Press Ctrl+C when IP appears
   ```

4. **Access Airflow UI**
   - Open browser: `http://<EXTERNAL-IP>` (e.g., `http://51.8.246.115`)
   - Login credentials:
     - Username: `admin`
     - Password: `admin123`

---

### Phase 7: Fix DAG Import Issues

**Symptom:** UI is accessible, but no DAGs appear in the list.

#### Issue 1: Recursive Loop in DAG Directory

**Error:**
```
RuntimeError: Detected recursive loop when walking DAG directory /opt/airflow/dags: 
/opt/airflow/dags/.worktrees/... has appeared more than once.
```

**Cause:** Git-sync creates `.worktrees` metadata that Airflow tries to scan recursively.

**Solution 1: Add .airflowignore**

1. Create `.airflowignore` in your repo's `dags/` folder:
   ```bash
   # In your local repo or via GitHub web UI
   cd dags/
   cat > .airflowignore << 'EOF'
   .git/
   .worktrees/
   __pycache__/
   archive/
   EOF
   
   git add .airflowignore
   git commit -m "Add .airflowignore to prevent recursive scanning"
   git push origin master
   ```

**Solution 2: Point dags_folder to subdirectory**

2. Update Helm values to point Airflow at the actual DAGs subdirectory:
   ```bash
   helm upgrade airflow apache-airflow/airflow \
     --namespace airflow \
     --reuse-values \
     --set config.core.dags_folder=/opt/airflow/dags/repo/dags
   
   kubectl rollout restart deployment airflow-dag-processor -n airflow
   ```

3. **Verify Fix**
   ```bash
   kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=200
   
   # Look for: "Found X files for bundle dags-folder"
   # Should NOT see recursive loop errors
   ```

---

#### Issue 2: Module 'src' Not Found

**Error:**
```
ModuleNotFoundError: No module named 'src'
```

**Cause:** DAGs import `from src.connectors import ...` but `src/` is not on Python path.

**Solution: Add PYTHONPATH**

```bash
# Set PYTHONPATH to repo root so "from src..." works
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set env[0].name=PYTHONPATH \
  --set env[0].value=/opt/airflow/dags/repo

# Restart components
kubectl rollout restart deployment airflow-scheduler -n airflow
kubectl rollout restart deployment airflow-dag-processor -n airflow
```

**Verify Fix:**
```bash
kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=200

# Should show: "# DAGs: 0  # Errors: 0" (no import errors)
```

---

#### Issue 3: Airflow 3.0 Compatibility - schedule_interval Deprecated

**Error:**
```
TypeError: DAG.__init__() got an unexpected keyword argument 'schedule_interval'
```

**Cause:** Airflow 3.0 replaced `schedule_interval` with `schedule`.

**Solution: Update DAG Definitions**

1. **Edit `dags/enterprise_integration_dag.py`:**
   
   Change:
   ```python
   with DAG(
       dag_id='enterprise_integration_pipeline',
       ...
       schedule_interval='@daily',  # OLD
       ...
   ) as dag:
   ```
   
   To:
   ```python
   with DAG(
       dag_id='enterprise_integration_pipeline',
       ...
       schedule='@daily',  # NEW - Airflow 3.0+
       ...
   ) as dag:
   ```

2. **Edit `dags/enterprise_integration_dag_poc.py`:**
   
   Make the same change (replace `schedule_interval` with `schedule`).

3. **Commit and Push**
   ```bash
   git add dags/enterprise_integration_dag.py dags/enterprise_integration_dag_poc.py
   git commit -m "Fix Airflow 3.0 compatibility: replace schedule_interval with schedule"
   git push origin master
   ```

4. **Wait for Git-Sync**
   
   Git-sync will automatically pull changes within ~10-30 seconds. Monitor:
   ```bash
   kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=200 --follow
   
   # Wait for: "# DAGs: 2  # Errors: 0"
   ```

5. **Refresh UI**
   
   Go to `http://<EXTERNAL-IP>` and refresh the page. You should now see:
   - `enterprise_integration_pipeline`
   - `enterprise_integration_pipeline_poc`

---

### Phase 8: Stabilize Deployment

1. **Set Static Webserver Secret Key**
   
   Prevents unnecessary pod restarts due to dynamic secret key regeneration:
   ```bash
   # Generate a secure 50-character key
   WEBSECRET=$(python3 - <<'PY'
   import secrets, string
   alphabet = string.ascii_letters + string.digits
   print(''.join(secrets.choice(alphabet) for _ in range(50)))
   PY)
   
   # Apply via Helm
   helm upgrade airflow apache-airflow/airflow \
     --namespace airflow \
     --reuse-values \
     --set webserverSecretKey="$WEBSECRET"
   ```

2. **Verify All Pods are Stable**
   ```bash
   kubectl get pods -n airflow
   
   # All pods should be Running with no recent restarts
   ```

---

## Accessing the System

### Access Airflow Web UI

**URL:** `http://51.8.246.115` (or your assigned EXTERNAL-IP)

**Login Credentials:**
- **Username:** `admin`
- **Password:** `admin123`

**To Get Your External IP:**
```bash
kubectl get svc airflow-ui-lb -n airflow

# Output:
# NAME            TYPE           CLUSTER-IP   EXTERNAL-IP      PORT(S)        AGE
# airflow-ui-lb   LoadBalancer   10.0.66.56   51.8.246.115    80:32623/TCP   2h
```

**UI Features:**
- **DAGs:** View all available DAGs, trigger runs, pause/unpause
- **Browse → DAG Runs:** Monitor DAG execution history
- **Browse → Task Instances:** Detailed task-level logs and status
- **Browse → DAG Import Errors:** Debug DAG parsing issues
- **Admin → Connections:** Configure external service connections (databases, APIs, cloud services)
- **Admin → Variables:** Store configuration values accessible in DAGs
- **Security → List Users:** Manage user accounts and permissions

**Changing Admin Password:**
```bash
# Via Helm (recommended for production)
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set webserver.defaultUser.password="YourSecurePassword123!"

# Or via UI: Security → List Users → Edit admin user → Change password
```

**Alternative Access Methods:**

1. **Port Forward (if LoadBalancer is not available):**
   ```bash
   # From Azure Cloud Shell or local terminal with kubectl configured
   kubectl port-forward svc/airflow-api-server 8080:8080 -n airflow
   
   # Access at: http://localhost:8080
   # Note: Keep terminal open while using
   ```

2. **From Inside the Cluster:**
   ```bash
   # Internal DNS name (from other pods)
   http://airflow-api-server.airflow.svc.cluster.local:8080
   ```

---

### Access PostgreSQL Database

**Connection Details:**
- **Host:** `postgres-service.airflow.svc.cluster.local` (internal DNS)
- **Port:** `5432`
- **Database:** `airflow`
- **Username:** `airflow`
- **Password:** `airflow123`

**Method 1: From Cloud Shell or Terminal**

```bash
# Connect via psql in the PostgreSQL pod
kubectl exec -it postgres-0 -n airflow -- psql -U airflow -d airflow

# Once connected, you can run SQL commands:
\dt              # List all tables
\d dag           # Describe 'dag' table schema
SELECT * FROM dag LIMIT 10;
\q               # Quit
```

**Method 2: Port Forward for External Database Client**

If you want to use a GUI tool like pgAdmin, DBeaver, or TablePlus:

```bash
# Forward PostgreSQL port to local machine
kubectl port-forward postgres-0 5432:5432 -n airflow

# Then connect your database client to:
# Host: localhost
# Port: 5432
# Database: airflow
# User: airflow
# Password: airflow123
```

**Method 3: From Another Pod in the Cluster**

```bash
# Create a temporary pod with PostgreSQL client
kubectl run postgres-client -it --rm --restart=Never \
  --image=postgres:15-alpine \
  --namespace airflow \
  -- psql -h postgres-service -U airflow -d airflow

# This will drop you into a psql prompt connected to the database
```

**Common Database Queries:**

```sql
-- List all DAGs
SELECT dag_id, is_paused, is_active, last_parsed_time 
FROM dag 
ORDER BY last_parsed_time DESC;

-- Count DAG runs by status
SELECT state, COUNT(*) 
FROM dag_run 
GROUP BY state;

-- View recent task instances
SELECT dag_id, task_id, state, start_date, end_date, duration
FROM task_instance
WHERE start_date > NOW() - INTERVAL '24 hours'
ORDER BY start_date DESC
LIMIT 20;

-- Check Airflow configuration
SELECT * FROM airflow_config;

-- View connection details (passwords are encrypted)
SELECT conn_id, conn_type, host, schema, port
FROM connection;
```

**Database Backup:**

```bash
# Backup database to a file
kubectl exec postgres-0 -n airflow -- \
  pg_dump -U airflow airflow > airflow_backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
cat airflow_backup_20251203_120000.sql | \
  kubectl exec -i postgres-0 -n airflow -- \
  psql -U airflow -d airflow
```

**Database Maintenance:**

```bash
# Check database size
kubectl exec postgres-0 -n airflow -- \
  psql -U airflow -d airflow -c "SELECT pg_size_pretty(pg_database_size('airflow'));"

# Vacuum and analyze (maintenance)
kubectl exec postgres-0 -n airflow -- \
  psql -U airflow -d airflow -c "VACUUM ANALYZE;"

# Check active connections
kubectl exec postgres-0 -n airflow -- \
  psql -U airflow -d airflow -c "SELECT * FROM pg_stat_activity WHERE datname = 'airflow';"
```

---

### Access Kubernetes Resources

**View All Airflow Pods:**
```bash
kubectl get pods -n airflow

# Get detailed pod information
kubectl describe pod <pod-name> -n airflow

# Stream logs from a specific pod
kubectl logs -f <pod-name> -n airflow

# For pods with multiple containers, specify container:
kubectl logs -f <pod-name> -n airflow -c scheduler
```

**View Airflow Logs:**
```bash
# Scheduler logs (shows DAG parsing, task scheduling)
kubectl logs deployment/airflow-scheduler -n airflow --tail=200

# DAG Processor logs (shows DAG import errors)
kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=200

# Triggerer logs (for deferred tasks)
kubectl logs statefulset/airflow-triggerer -n airflow --tail=200

# Worker task logs are visible in the UI under task instance logs
```

**Execute Commands Inside Pods:**
```bash
# Open shell in scheduler pod
kubectl exec -it deployment/airflow-scheduler -n airflow -- bash

# Run Airflow CLI commands
kubectl exec deployment/airflow-scheduler -n airflow -- \
  airflow dags list

# Test DAG
kubectl exec deployment/airflow-scheduler -n airflow -- \
  airflow dags test enterprise_integration_pipeline 2024-01-01

# List connections
kubectl exec deployment/airflow-scheduler -n airflow -- \
  airflow connections list
```

**View Kubernetes Events:**
```bash
# Recent events in namespace
kubectl get events -n airflow --sort-by=.lastTimestamp | tail -20

# Watch events in real-time
kubectl get events -n airflow --watch
```

---

## Setting Up a New Developer

This section guides you through onboarding a colleague to work on DAGs for this Airflow deployment.

### Prerequisites for Developer

The developer needs:
1. **GitHub Account** with access to the repository: `https://github.com/jogusrikanth-code/Airflow_POC`
2. **Git installed** on their local machine
3. **Python 3.11+** installed (to match Airflow runtime)
4. **Code Editor** (VS Code recommended with Python extension)
5. **Access to Airflow UI** (share the external IP and credentials)

**Optional but Recommended:**
- **Docker Desktop** (for local DAG testing)
- **Azure Account** (if they need to access AKS for debugging)

---

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/jogusrikanth-code/Airflow_POC.git
cd Airflow_POC

# Create a new branch for their work
git checkout -b feature/my-new-dag
```

**Repository Structure:**
```
Airflow_POC/
├── dags/                    # DAG files go here (synced to Airflow)
│   ├── __init__.py
│   ├── .airflowignore      # Files/folders to ignore
│   ├── demo_dag.py
│   ├── enterprise_integration_dag.py
│   └── enterprise_integration_dag_poc.py
├── src/                     # Shared Python modules
│   ├── __init__.py
│   ├── connectors/          # Database/API connectors
│   ├── extract/             # ETL extract logic
│   ├── transform/           # ETL transform logic
│   └── load/                # ETL load logic
├── plugins/                 # Custom Airflow plugins (operators, hooks)
├── docs/                    # Documentation
└── tests/                   # Unit tests for DAGs
```

---

### Step 2: Set Up Local Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install Airflow and dependencies
pip install apache-airflow==3.0.2
pip install apache-airflow-providers-microsoft-azure
pip install pandas azure-storage-blob databricks-sdk

# Install development tools
pip install pytest black flake8
```

**Create `requirements.txt` for team consistency:**
```txt
apache-airflow==3.0.2
apache-airflow-providers-microsoft-azure==10.5.0
apache-airflow-providers-databricks==6.11.0
pandas==2.2.0
azure-storage-blob==12.19.0
databricks-sdk==0.23.0
```

---

### Step 3: Understanding DAG Structure

**Minimal DAG Example:**

Create `dags/my_first_dag.py`:

```python
"""
My First DAG - Simple example for learning Airflow
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator


# Default arguments for all tasks
default_args = {
    'owner': 'your_name',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def hello_world(**context):
    """Simple task that prints hello"""
    print("Hello from Airflow!")
    print(f"Execution date: {context['ds']}")
    return "Success!"


def goodbye_world(**context):
    """Task that uses output from previous task"""
    task_instance = context['task_instance']
    message = task_instance.xcom_pull(task_ids='hello_task')
    print(f"Previous task returned: {message}")
    print("Goodbye from Airflow!")


# Define the DAG
with DAG(
    dag_id='my_first_dag',
    description='A simple tutorial DAG',
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule='@daily',  # Run once per day
    catchup=False,       # Don't backfill historical runs
    tags=['tutorial', 'beginner'],
) as dag:
    
    # Task 1
    hello_task = PythonOperator(
        task_id='hello_task',
        python_callable=hello_world,
    )
    
    # Task 2
    goodbye_task = PythonOperator(
        task_id='goodbye_task',
        python_callable=goodbye_world,
    )
    
    # Define task dependencies
    hello_task >> goodbye_task  # hello runs first, then goodbye
```

**Key Concepts:**

1. **DAG ID:** Unique identifier (`my_first_dag`)
2. **Schedule:** When the DAG runs (`@daily`, `@hourly`, cron expressions)
3. **Start Date:** When the DAG becomes active
4. **Catchup:** Whether to backfill missed runs
5. **Tasks:** Individual units of work (use operators)
6. **Dependencies:** Define task execution order with `>>`

---

### Step 4: Testing DAGs Locally

**Method 1: Airflow Standalone (Local Testing)**

```bash
# Initialize Airflow database (SQLite for local dev)
export AIRFLOW_HOME=~/airflow
airflow db init

# Create admin user
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin

# Start Airflow webserver (in one terminal)
airflow webserver --port 8080

# Start Airflow scheduler (in another terminal)
airflow scheduler

# Access UI at http://localhost:8080
```

**Method 2: Test DAG Syntax Without Running**

```bash
# Check for Python syntax errors
python dags/my_first_dag.py

# Validate DAG structure
airflow dags list-import-errors

# Print DAG structure
airflow dags show my_first_dag

# Test a specific task
airflow tasks test my_first_dag hello_task 2024-01-01
```

**Method 3: Unit Testing**

Create `tests/test_my_first_dag.py`:

```python
import pytest
from airflow.models import DagBag


def test_dag_loads():
    """Test that DAG can be imported without errors"""
    dagbag = DagBag(dag_folder='dags/', include_examples=False)
    assert 'my_first_dag' in dagbag.dags
    assert len(dagbag.import_errors) == 0


def test_task_count():
    """Test correct number of tasks"""
    dagbag = DagBag(dag_folder='dags/', include_examples=False)
    dag = dagbag.get_dag('my_first_dag')
    assert len(dag.tasks) == 2


def test_task_dependencies():
    """Test task dependency chain"""
    dagbag = DagBag(dag_folder='dags/', include_examples=False)
    dag = dagbag.get_dag('my_first_dag')
    hello_task = dag.get_task('hello_task')
    goodbye_task = dag.get_task('goodbye_task')
    
    assert goodbye_task in hello_task.downstream_list
```

Run tests:
```bash
pytest tests/
```

---

### Step 5: Deploying DAGs to AKS

**Deployment Process:**

1. **Commit and Push:**
   ```bash
   # Add your new DAG file
   git add dags/my_first_dag.py
   
   # Commit with descriptive message
   git commit -m "Add my_first_dag for daily data processing"
   
   # Push to GitHub
   git push origin feature/my-new-dag
   ```

2. **Create Pull Request (Recommended):**
   - Go to GitHub repository
   - Click "Pull Requests" → "New Pull Request"
   - Select your branch
   - Request review from team lead
   - Once approved, merge to `master`

3. **Automatic Deployment:**
   - Git-sync in Airflow polls the repository every 5 seconds
   - After merge to `master`, DAG appears in UI within ~10-30 seconds
   - No manual deployment needed!

4. **Verify in UI:**
   - Open `http://51.8.246.115`
   - Your DAG should appear in the list
   - If not visible, check Browse → DAG Import Errors

**Hot Reload (for quick testing):**

If you need to test without waiting for git-sync:

```bash
# Copy DAG directly to pod (bypass git-sync)
kubectl cp dags/my_first_dag.py \
  airflow-dag-processor-xxxxx:/opt/airflow/dags/repo/dags/my_first_dag.py \
  -n airflow -c dag-processor

# Wait 30 seconds for dag-processor to scan
# Check logs
kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=50
```

---

### Step 6: Using Shared Modules

If your DAG uses code from `src/`:

```python
# In your DAG file
from src.connectors import get_azure_storage_connector
from src.transform import transform_sales_data

def my_task(**context):
    # Use shared connector
    storage = get_azure_storage_connector(conn_id='azure_default')
    data = storage.download_blob('container', 'file.csv')
    
    # Use shared transformation
    transformed = transform_sales_data(data)
    return transformed
```

**Important:** The `PYTHONPATH` is already configured in the Helm deployment to include `/opt/airflow/dags/repo`, so imports from `src.` will work automatically.

---

### Step 7: Creating Airflow Connections

Many DAGs need connections to external systems (databases, APIs, cloud services).

**Via UI (Easiest):**
1. Login to Airflow UI
2. Go to **Admin → Connections**
3. Click **+** to add new connection
4. Fill in connection details:
   - **Connection ID:** `my_postgres_db`
   - **Connection Type:** `Postgres`
   - **Host:** `mydb.example.com`
   - **Schema:** `production`
   - **Login:** `dbuser`
   - **Password:** `dbpass`
   - **Port:** `5432`

**Via Airflow CLI:**
```bash
kubectl exec deployment/airflow-scheduler -n airflow -- \
  airflow connections add 'my_postgres_db' \
  --conn-type 'postgres' \
  --conn-host 'mydb.example.com' \
  --conn-schema 'production' \
  --conn-login 'dbuser' \
  --conn-password 'dbpass' \
  --conn-port 5432
```

**Using Connections in DAGs:**
```python
from airflow.providers.postgres.hooks.postgres import PostgresHook

def query_database(**context):
    # Hook automatically uses connection
    hook = PostgresHook(postgres_conn_id='my_postgres_db')
    results = hook.get_records("SELECT * FROM users LIMIT 10")
    return results
```

---

### Step 8: Best Practices for DAG Development

**1. Code Style:**
- Use descriptive DAG IDs (`process_daily_sales` not `dag1`)
- Add docstrings to all functions and DAGs
- Follow PEP 8 style guide
- Use type hints for function parameters

**2. Error Handling:**
```python
from airflow.exceptions import AirflowException

def safe_task(**context):
    try:
        result = risky_operation()
        return result
    except Exception as e:
        # Log error details
        context['task_instance'].log.error(f"Task failed: {str(e)}")
        # Re-raise with Airflow exception
        raise AirflowException(f"Failed to process data: {str(e)}")
```

**3. Testing Checklist:**
- [ ] DAG imports without errors (`python dags/my_dag.py`)
- [ ] No linting errors (`flake8 dags/my_dag.py`)
- [ ] Unit tests pass (`pytest tests/`)
- [ ] Task tested locally (`airflow tasks test ...`)
- [ ] Verified in UI after deployment
- [ ] Checked logs for warnings/errors

**4. Performance Tips:**
- Use `provide_context=True` sparingly
- Avoid storing large data in XComs (use external storage)
- Set appropriate task timeouts
- Use pools to limit concurrent tasks
- Consider task groups for complex DAGs

**5. Security:**
- Never hardcode credentials in DAG files
- Use Airflow Connections or Variables
- Store sensitive values in Azure Key Vault
- Don't commit `.env` files or secrets

---

### Step 9: Common DAG Patterns

**Pattern 1: Daily ETL Pipeline**
```python
with DAG(
    dag_id='daily_etl_pipeline',
    schedule='0 2 * * *',  # Run at 2 AM daily
    default_args=default_args,
    catchup=False,
) as dag:
    
    extract_task = PythonOperator(
        task_id='extract_data',
        python_callable=extract_from_source
    )
    
    transform_task = PythonOperator(
        task_id='transform_data',
        python_callable=transform_logic
    )
    
    load_task = PythonOperator(
        task_id='load_to_warehouse',
        python_callable=load_to_dw
    )
    
    extract_task >> transform_task >> load_task
```

**Pattern 2: Branching Logic**
```python
from airflow.operators.python import BranchPythonOperator

def decide_branch(**context):
    """Decide which path to take based on data"""
    if check_condition():
        return 'process_large_dataset'
    else:
        return 'process_small_dataset'

with DAG(...) as dag:
    branch_task = BranchPythonOperator(
        task_id='branch_decision',
        python_callable=decide_branch
    )
    
    large_task = PythonOperator(task_id='process_large_dataset', ...)
    small_task = PythonOperator(task_id='process_small_dataset', ...)
    
    branch_task >> [large_task, small_task]
```

**Pattern 3: Dynamic Task Generation**
```python
with DAG(...) as dag:
    start = DummyOperator(task_id='start')
    end = DummyOperator(task_id='end')
    
    # Generate tasks dynamically
    for i in range(5):
        task = PythonOperator(
            task_id=f'process_partition_{i}',
            python_callable=process_partition,
            op_args=[i]
        )
        start >> task >> end
```

---

### Step 10: Getting Help

**Resources:**
- **Airflow Documentation:** https://airflow.apache.org/docs/apache-airflow/3.0.2/
- **Team Slack/Teams Channel:** [Your team channel]
- **DAG Examples:** Look at existing DAGs in `dags/` folder
- **Stack Overflow:** Tag questions with `apache-airflow`

**Debugging Checklist:**
1. Check DAG Import Errors in UI
2. Review task logs in UI
3. Check scheduler logs: `kubectl logs deployment/airflow-scheduler -n airflow --tail=200`
4. Verify connections are configured
5. Test task locally before deploying
6. Ask team lead for help!

**Common Issues:**

| Issue | Solution |
|-------|----------|
| DAG not appearing in UI | Check Browse → DAG Import Errors |
| Import errors | Ensure `PYTHONPATH` includes `src/`, check module names |
| Task stuck in "queued" | Check scheduler logs, verify KubernetesExecutor is running |
| Connection not found | Create connection in Admin → Connections |
| Task timeout | Increase `execution_timeout` in task definition |

---

### Quick Reference: Developer Workflow

```bash
# 1. Clone and setup
git clone https://github.com/jogusrikanth-code/Airflow_POC.git
cd Airflow_POC
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Create new branch
git checkout -b feature/my-dag

# 3. Write DAG in dags/ folder
code dags/my_new_dag.py

# 4. Test locally
python dags/my_new_dag.py
pytest tests/

# 5. Commit and push
git add dags/my_new_dag.py
git commit -m "Add new DAG for X processing"
git push origin feature/my-dag

# 6. Create PR on GitHub

# 7. After merge, verify in UI
# Open http://51.8.246.115 and check DAGs list

# 8. Monitor execution
# Click on DAG → Grid view → Task logs
```

---

## Troubleshooting Guide

### Problem: Pods Stuck in ImagePullBackOff

**Symptoms:**
```
airflow-scheduler-xxxxx   0/2   ImagePullBackOff
```

**Causes:**
1. Incorrect image tag or repository
2. Rate limiting from Docker Hub
3. Network issues

**Solutions:**
```bash
# Check pod events
kubectl describe pod <pod-name> -n airflow

# Verify image exists
docker pull apache/airflow:3.0.2-python3.11

# If rate-limited, wait or use authenticated registry
```

---

### Problem: PostgreSQL Connection Failures

**Symptoms:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Verify PostgreSQL is running
kubectl get pods -n airflow | grep postgres
# Should show: postgres-0   1/1   Running

# Test connection from scheduler pod
kubectl exec -it deployment/airflow-scheduler -n airflow -- \
  python -c "from airflow.settings import Session; print(Session().execute('SELECT 1').scalar())"

# Check PostgreSQL logs
kubectl logs postgres-0 -n airflow

# Verify service exists
kubectl get svc postgres-service -n airflow
```

---

### Problem: DAGs Not Appearing in UI

**Step-by-step diagnosis:**

1. **Check if dag-processor is running:**
   ```bash
   kubectl get pods -n airflow | grep dag-processor
   # Should be Running, not CrashLoopBackOff
   ```

2. **Check dag-processor logs:**
   ```bash
   kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=200
   
   # Look for:
   # - "Found X files for bundle dags-folder" (confirms files detected)
   # - "# DAGs: N  # Errors: 0" (confirms successful parsing)
   # - Any Python exceptions (import errors, syntax errors)
   ```

3. **Check git-sync is pulling code:**
   ```bash
   kubectl logs deployment/airflow-dag-processor -n airflow -c git-sync --tail=50
   
   # Should show periodic sync messages:
   # "updated successfully" or "already up to date"
   ```

4. **Verify files in container:**
   ```bash
   # List DAGs directory
   kubectl exec deployment/airflow-dag-processor -n airflow -c dag-processor -- \
     ls -la /opt/airflow/dags/repo/dags
   
   # Should show your Python DAG files
   ```

5. **Check UI for import errors:**
   - Go to UI: Browse → DAG Import Errors
   - Click on any entry to see detailed traceback
   - Fix the specific error (usually imports or syntax)

---

### Problem: UI Returns 404 or Connection Refused

**Solutions:**
```bash
# Verify LoadBalancer service has external IP
kubectl get svc airflow-ui-lb -n airflow

# If EXTERNAL-IP is <pending>, wait 2-3 minutes
# If stuck, check Azure Load Balancer quota

# Verify api-server deployment is running
kubectl get deployment airflow-api-server -n airflow

# Test from inside cluster
kubectl run test-pod --rm -it --image=curlimages/curl -- \
  curl http://airflow-api-server.airflow.svc.cluster.local:8080
```

---

### Problem: Tasks Not Running (KubernetesExecutor)

**Symptoms:** Tasks stuck in "queued" state.

**Solutions:**
```bash
# Check scheduler logs
kubectl logs deployment/airflow-scheduler -n airflow --tail=200

# Verify RBAC permissions
kubectl get role,rolebinding -n airflow | grep airflow

# Check if worker pods are created
kubectl get pods -n airflow | grep worker

# Verify executor configuration
helm get values airflow -n airflow | grep executor
# Should show: executor: KubernetesExecutor
```

---

## Verification

### 1. Verify All Components are Running

```bash
kubectl get pods -n airflow

# Expected output:
# NAME                                   READY   STATUS    RESTARTS   AGE
# airflow-api-server-xxxxx               1/1     Running   0          10m
# airflow-dag-processor-xxxxx            3/3     Running   0          10m
# airflow-scheduler-xxxxx                2/2     Running   0          10m
# airflow-statsd-xxxxx                   1/1     Running   0          10m
# airflow-triggerer-0                    3/3     Running   0          10m
# postgres-0                             1/1     Running   0          15m
```

### 2. Verify Services

```bash
kubectl get svc -n airflow

# Should include:
# airflow-ui-lb         LoadBalancer   10.0.66.56   51.8.246.115   80:32623/TCP
# postgres-service      ClusterIP      None         <none>         5432/TCP
```

### 3. Test UI Access

1. Open browser: `http://<EXTERNAL-IP>`
2. Login with `admin` / `admin123`
3. Verify DAGs are visible
4. Click on a DAG to view details

### 4. Trigger a Test DAG Run

1. In UI, click on `enterprise_integration_pipeline_poc` (the mock version)
2. Click "Trigger DAG" (play button)
3. Monitor the run in Graph or Grid view
4. Verify tasks turn green (success)

### 5. Check Logs

```bash
# Scheduler logs
kubectl logs deployment/airflow-scheduler -n airflow --tail=100

# DAG processor logs
kubectl logs deployment/airflow-dag-processor -n airflow -c dag-processor --tail=100

# View task logs via UI (click on task → Logs)
```

---

## Next Steps

### Immediate Production Readiness

1. **Security Hardening**
   ```bash
   # Change default admin password via UI or Helm
   helm upgrade airflow apache-airflow/airflow \
     --namespace airflow \
     --reuse-values \
     --set webserver.defaultUser.password="<strong-password>"
   
   # Enable HTTPS (requires cert-manager or Azure Application Gateway)
   # Add authentication (Azure AD, OAuth, LDAP)
   ```

2. **Configure Remote Logging (Azure Blob Storage)**
   ```bash
   helm upgrade airflow apache-airflow/airflow \
     --namespace airflow \
     --reuse-values \
     --set config.logging.remote_logging=True \
     --set config.logging.remote_base_log_folder="wasb-<container>@<storage-account>.blob.core.windows.net/" \
     --set config.logging.remote_log_conn_id="azure_blob_storage_default"
   ```

3. **Set Up Monitoring**
   - Enable Azure Monitor for AKS
   - Configure Prometheus + Grafana for metrics
   - Set up alerts for pod failures, high memory usage

4. **Database Migration to Azure PostgreSQL**
   ```bash
   # For production, migrate to Azure Database for PostgreSQL Flexible Server
   # Update Helm values with new connection string
   # Run: airflow db migrate
   ```

5. **CI/CD for DAG Deployments**
   - Set up GitHub Actions to validate DAG syntax on PR
   - Automated testing with pytest
   - Branch-based deployments (dev/staging/prod)

### Optional Enhancements

1. **Install Airflow Providers**
   ```bash
   helm upgrade airflow apache-airflow/airflow \
     --namespace airflow \
     --reuse-values \
     --set images.airflow.pip.install="apache-airflow-providers-microsoft-azure apache-airflow-providers-databricks pandas"
   ```

2. **Configure Autoscaling**
   ```bash
   # Enable cluster autoscaling in AKS
   az aks update \
     --resource-group bi_lakehouse_dev_rg \
     --name aks-airflow-poc \
     --enable-cluster-autoscaler \
     --min-count 3 \
     --max-count 10
   ```

3. **Set Up Azure AD Integration**
   - Configure Azure AD for user authentication
   - Integrate with Azure Key Vault for secrets management

4. **Cost Optimization**
   - Use Azure Spot VMs for worker nodes (KubernetesExecutor tasks)
   - Set up pod autoscaling based on DAG load
   - Schedule AKS cluster shutdown during non-business hours (dev only)

---

## Key Configuration Files

### Complete Helm Values Reference

```yaml
# values-aks-airflow.yaml - Complete working configuration

executor: "KubernetesExecutor"

images:
  airflow:
    repository: apache/airflow
    tag: 3.0.2-python3.11
    pullPolicy: IfNotPresent

postgresql:
  enabled: false

data:
  metadataConnection:
    user: airflow
    pass: airflow123
    protocol: postgresql
    host: postgres-service
    port: 5432
    db: airflow

redis:
  enabled: false

config:
  core:
    dags_folder: /opt/airflow/dags/repo/dags
    load_examples: "False"
    dag_discovery_safe_mode: "False"
  webserver:
    expose_config: "True"
  kubernetes_executor:
    namespace: airflow
    delete_worker_pods: "True"

dags:
  gitSync:
    enabled: true
    repo: https://github.com/jogusrikanth-code/Airflow_POC.git
    branch: master
    subPath: dags
    wait: 5

scheduler:
  replicas: 1

triggerer:
  enabled: true
  replicas: 3

webserver:
  enabled: true
  replicas: 1
  service:
    type: LoadBalancer
  defaultUser:
    enabled: true
    username: admin
    password: admin123

rbac:
  create: true

serviceAccount:
  create: true

env:
  - name: PYTHONPATH
    value: /opt/airflow/dags/repo
```

---

## Important Notes

### Cost Considerations

- **AKS Cluster:** ~$0.10/hour per node (Standard_D2s_v3) = ~$216/month for 3 nodes
- **LoadBalancer:** ~$0.025/hour = ~$18/month
- **Storage:** Minimal cost for PVCs (~$0.10/GB/month)
- **Total Estimated Cost:** ~$250-300/month for this setup

**Cost Saving Tips:**
- Stop AKS cluster when not in use (dev environments)
- Use Azure Reserved Instances for production (up to 72% savings)
- Use Spot VMs for non-critical workloads

### Security Best Practices

1. **Never commit secrets to Git**
   - Use Kubernetes Secrets or Azure Key Vault
   - Rotate credentials regularly

2. **Network Security**
   - Use Network Policies to restrict pod-to-pod communication
   - Consider Azure Private Link for database connections
   - Enable AKS managed identity instead of service principals

3. **Access Control**
   - Use Azure RBAC for AKS access
   - Implement Airflow RBAC for DAG-level permissions
   - Enable audit logging

### Maintenance

1. **Regular Updates**
   ```bash
   # Update Helm chart
   helm repo update
   helm upgrade airflow apache-airflow/airflow --namespace airflow --reuse-values
   
   # Update Kubernetes
   az aks upgrade --resource-group bi_lakehouse_dev_rg --name aks-airflow-poc --kubernetes-version <new-version>
   ```

2. **Backup Strategy**
   - Database: Regular PostgreSQL backups (pg_dump or Azure Backup)
   - Persistent Volumes: Snapshot PVCs
   - Configuration: Version control Helm values files

3. **Monitoring Checklist**
   - Pod resource usage (CPU, memory)
   - Database connection pool exhaustion
   - DAG execution duration trends
   - Failed task rates

---

## Common Helm Upgrade Commands

```bash
# Upgrade Airflow version
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set images.airflow.tag=3.1.0-python3.11

# Scale scheduler replicas
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set scheduler.replicas=2

# Update admin password
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set webserver.defaultUser.password="new-secure-password"

# Enable additional providers
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set images.airflow.pip.install="apache-airflow-providers-microsoft-azure"

# Change Git repository
helm upgrade airflow apache-airflow/airflow \
  --namespace airflow \
  --reuse-values \
  --set dags.gitSync.repo="https://github.com/yourorg/yourrepo.git"
```

---

## Cleanup / Teardown

To completely remove the deployment:

```bash
# Uninstall Airflow Helm release
helm uninstall airflow --namespace airflow

# Delete namespace (removes all resources)
kubectl delete namespace airflow

# Delete AKS cluster (via Azure Portal or CLI)
az aks delete \
  --resource-group bi_lakehouse_dev_rg \
  --name aks-airflow-poc \
  --yes --no-wait
```

---

## Support & Resources

- **Apache Airflow Documentation:** https://airflow.apache.org/docs/
- **Helm Chart Documentation:** https://airflow.apache.org/docs/helm-chart/
- **AKS Documentation:** https://learn.microsoft.com/en-us/azure/aks/
- **GitHub Repository:** https://github.com/jogusrikanth-code/Airflow_POC

---

## Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-03 | 1.0 | Initial deployment guide created |

---

**Document Status:** ✅ Production-Ready  
**Last Tested:** December 3, 2025  
**Tested By:** Srikanth Jogu
