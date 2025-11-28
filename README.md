# Airflow POC — Kubernetes-first Setup

## Overview
This repository contains a Kubernetes-first Apache Airflow POC running on Docker Desktop’s local Kubernetes. It includes enterprise connectors, example DAGs, and production-lean K8s manifests to run Airflow (webserver, scheduler, worker) with PostgreSQL and Redis.

- Run locally on Docker Desktop + Kubernetes
- Deploy with simple `kubectl apply` commands
- Access Airflow UI via port-forward or LoadBalancer

## Quick Start

1) Deploy PostgreSQL
```
kubectl apply -f kubernetes/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n airflow --timeout=300s
```

2) Deploy Airflow (CeleryExecutor + Redis)
```
kubectl apply -f kubernetes/airflow.yaml
kubectl get pods -n airflow
```

3) Access Airflow UI
```
kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow
```
Open http://localhost:8080 (username: `admin`, password: `admin`).

## 📁 Folder Structure

```
Airflow_POC/
├── README.md
├── docs/                         # Centralized documentation
│   ├── INDEX.md                  # Documentation map and quick links
│   ├── AIRFLOW_BASICS.md         # Airflow learning guide
│   ├── ENTERPRISE_INTEGRATION.md # Enterprise connectors & DAG overview
│   ├── ENTERPRISE_POC_SUMMARY.md # POC scope and outcomes
│   ├── SETUP_SUMMARY.md          # Setup decisions and environment notes
│   ├── LEARNING_CHECKLIST.md     # Learning and validation checklist
│   └── QUICKSTART.md             # Kubernetes quickstart
├── KUBERNETES_CLEANUP_SUMMARY.md # Repo & K8s modernization summary
│
├── kubernetes/                   # Kubernetes deployment manifests
│   ├── README.md                 # K8s deployment guide
│   ├── postgres.yaml             # PostgreSQL deployment
│   ├── airflow.yaml              # Airflow components (webserver, scheduler, worker, Redis)
│   └── values.yaml               # Helm chart reference values
│
├── dags/                         # DAG definitions scanned by Airflow
│   ├── __init__.py
│   ├── demo_dag.py
│   ├── etl_example_dag.py
│   └── enterprise_integration_dag.py
│
├── src/                          # Application source code
│   ├── connectors/               # On-prem, Azure, Databricks, PowerBI
│   ├── extract/
│   ├── transform/
│   └── load/
│
├── data/                         # Sample data for local tests
│   ├── raw/
│   └── processed/
│
├── plugins/                      # Custom Airflow plugins
└── archive/                      # Archived/legacy files
```

## Runbook

- Check pods: `kubectl get pods -n airflow`
- Check services: `kubectl get svc -n airflow`
- Logs:
  - Webserver: `kubectl logs -f deployment/airflow-webserver -n airflow`
  - Scheduler: `kubectl logs -f statefulset/airflow-scheduler -n airflow`
  - Worker: `kubectl logs -f statefulset/airflow-worker -n airflow`

## Notes

- Images use `IfNotPresent` to minimize Docker Hub pulls.
- For rate limit issues, `docker login` before deploying.
- To reset cluster on Docker Desktop: Settings → Kubernetes → Reset Cluster.

## Next Steps

- Configure Airflow Connections for your sources (UI → Admin → Connections).
- Enable and run `enterprise_integration_dag` from the UI.
- Consider migrating to Helm using `kubernetes/values.yaml` as baseline.

## 🚀 Quick Start

### 1. **Initial Setup**
```bash
# Initialize Airflow database
airflow db init

# Create default admin user
airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

### 2. **Start Airflow Components**
```bash
# Terminal 1: Start the scheduler
airflow scheduler

# Terminal 2: Start the web server
airflow webserver --port 8080
```

### 3. **Access the Web UI**
- Open browser: `http://localhost:8080`
- Login with `admin` / `admin`
- Enable DAGs to start running

### 4. **Using Docker (Alternative)**
```bash
cd docker
docker-compose up
```

---

## 📚 Project DAGs

### 1. **demo_dag.py** - Simple Introduction
- **Purpose**: Learn the bare minimum to run a DAG
- **Tasks**: 
  - `start` (EmptyOperator)
  - `end` (EmptyOperator)
- **Schedule**: Daily
- **Use Case**: Great for understanding DAG structure

### 2. **etl_example_dag.py** - Full ETL Pipeline
- **Purpose**: Learn how to chain tasks and work with data
- **Tasks**:
  1. `extract_from_source_a` - Reads sample CSV
  2. `transform_sales_data` - Aggregates by date
  3. `load_to_dw` - Verifies processed file
- **Schedule**: Daily
- **Data Flow**: `raw/sample_source_a.csv` → `processed/sales_daily_summary.csv`

---

## 🔑 Key Airflow Concepts

### DAG (Directed Acyclic Graph)
- Workflow definition with dependencies
- `start_date`: When DAG starts running
- `schedule_interval`: How often to run (e.g., `@daily`, `0 8 * * *`)
- `catchup`: Whether to run past schedules

### Tasks
- Individual units of work
- Connected by dependencies: `task1 >> task2` means task2 depends on task1
- Common operators:
  - `PythonOperator`: Run Python functions
  - `BashOperator`: Run shell commands
  - `EmptyOperator`: No-op for testing

### Execution
- **DAG Run**: One execution of an entire DAG
- **Task Instance**: One execution of a task
- **XCom**: Communication between tasks via key-value pairs

---

## 📝 Sample Data

### `data/raw/sample_source_a.csv`
```csv
date,amount
2024-01-01,100
2024-01-01,200
2024-01-02,150
```

### `data/processed/sales_daily_summary.csv` (Generated)
```csv
date,amount
2024-01-01,300
2024-01-02,150
```

---

## 🛠️ Common Airflow CLI Commands

```bash
# List all DAGs
airflow dags list

# Trigger a DAG
airflow dags trigger -d demo_dag

# View task logs
airflow tasks logs -d demo_dag -t start -e 2024-01-01

# List task instances
airflow tasks list -d demo_dag

# Test a task
airflow tasks test demo_dag start 2024-01-01

# Validate DAG
airflow dags validate

# Pause/unpause DAG
airflow dags pause demo_dag
airflow dags unpause demo_dag
```

---

## 📖 Learning Path

1. **Phase 1: Understand DAG Basics**
   - Read AIRFLOW_BASICS.md
   - Review `demo_dag.py`
   - Run it in the UI and observe

2. **Phase 2: Task Dependencies**
   - Modify `demo_dag.py` to add more tasks
   - Experiment with different operators
   - Understand task execution order

3. **Phase 3: Data Processing**
   - Review `etl_example_dag.py`
   - Run the full ETL pipeline
   - Check logs and output files

4. **Phase 4: Advanced Topics**
   - Learn about XCom for task communication
   - Create custom operators in `plugins/`
   - Add error handling and retries

---

## 🔧 Configuration

### `airflow_home/airflow.cfg` (Key Settings)
- `dags_folder`: Where Airflow scans for DAGs
- `executor`: Task execution method (SequentialExecutor for POC)
- `sql_alchemy_conn`: Database connection

### Environment Variables
```bash
# Override config with environment variables
export AIRFLOW__CORE__EXECUTOR=LocalExecutor
export AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql://user:password@localhost/airflow
```

---

## 🐛 Troubleshooting

### DAG not showing up?
- Ensure DAG file is in `dags/` folder
- Check DAG file has no syntax errors
- Verify DAG file contains a DAG object

### Tasks not running?
- Check if DAG is paused (unpause in UI)
- Review logs in `airflow_home/logs/`
- Ensure `schedule_interval` is set correctly

### Import errors?
- Add project root to PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:$(pwd)`
- Ensure `__init__.py` exists in each package

---

## 📖 Additional Resources

- **Official Docs**: https://airflow.apache.org/docs/
- **Concepts**: https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/
- **API Reference**: https://airflow.apache.org/docs/apache-airflow/stable/_api/

---

## ✅ Next Steps

1. ✅ Understand folder structure
2. ⏳ Run `demo_dag.py` successfully
3. ⏳ Run `etl_example_dag.py` and check output
4. ⏳ Modify DAGs and experiment
5. ⏳ Create your own custom DAG

---

**Happy Learning! 🎓**
