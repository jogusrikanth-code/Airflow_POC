# Quickstart (Kubernetes on Docker Desktop)

## ⚡ 5-Minute Quick Start

### Step 1: Deploy PostgreSQL
```
kubectl apply -f kubernetes/postgres.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n airflow --timeout=300s
```

### Step 2: Deploy Airflow (CeleryExecutor + Redis)
```
kubectl apply -f kubernetes/airflow.yaml
kubectl get pods -n airflow
```

### Step 3: Access the Web UI
- Port-forward: `kubectl port-forward svc/airflow-webserver 8080:8080 -n airflow`
- Open browser: **http://localhost:8080**
- Login: `admin` / `admin`

### Step 4: Enable and Run a DAG

1. **Find DAGs list** - You should see:
  - `demo_dag` - Simple example
  - `etl_example_dag` - Full pipeline

2. **Enable `demo_dag`:**
  - Click on `demo_dag` in the list
  - Toggle the **Enable** switch (top left)

3. **Trigger the DAG:**
  - Click **Trigger DAG** button
  - Select **Execute**

4. **View Results:**
  - Refresh the page
  - Click on the DAG run (shown in the calendar/timeline)
  - Click on tasks to see logs

---

## 📊 Understanding the DAG Views

### Grid View (Default)
- **Columns**: Each DAG run
- **Rows**: Each task
- **Colors**: Task status (green=success, red=failed, etc.)

### Graph View
- Shows task dependencies visually
- Click tasks to see details

### Logs Tab
- View task execution output
- Useful for debugging

---

## ✅ Test Your Setup (DAGs)

### Run demo_dag (Simplest)
Use the Airflow UI:
- Enable `demo_dag`
- Click "Trigger DAG"

### Run etl_example_dag (Full Pipeline)
In UI, trigger `etl_example_dag`:
- Extract reads `data/raw/sample_source_a.csv`
- Transform aggregates by date
- Load writes `data/processed/sales_daily_summary.csv`

---

## 🔍 Debugging Tips

### Check Logs
1. Go to DAG → Runs → Task → Logs tab
2. Look for any error messages

### Test Individual Tasks
Use UI task logs for debugging (recommended in K8s).

### List All DAGs
Use the Airflow UI DAGs page.

### View Task Details
Use the Airflow UI task details page.

### Pause/Unpause DAG
Use the UI to pause/unpause DAGs.

---

## 🎯 What to Try Next

### 1. Modify demo_dag
- Add more tasks with EmptyOperator
- Test different dependency patterns
  ```python
  # Sequence: t1 >> t2 >> t3
  # Parallel: t1 >> [t2, t3] >> t4
  ```

### 2. Check ETL Pipeline Output
- Look at `data/raw/sample_source_a.csv` (input)
- Look at `data/processed/sales_daily_summary.csv` (output)
- Understand the transformation

### 3. Create Your Own DAG
- Copy `demo_dag.py` to a new file: `my_dag.py`
- Modify the dag_id and tasks
- Save and refresh web UI to see it appear

### 4. Experiment with Scheduling
- Change `schedule_interval`:
  - `@hourly` - Every hour
  - `@daily` - Every day (default)
  - `0 8 * * *` - 8 AM daily
  - `*/5 * * * *` - Every 5 minutes

---

## 🐛 Common Issues & Solutions

### "DAG not appearing in UI"
- Check DAG file is in `dags/` folder
- Check for Python syntax errors
- Restart webserver

### "Task failed with import error"
- Add project root to PYTHONPATH:
  ```bash
  export PYTHONPATH=$PYTHONPATH:$(pwd)
  ```
- Restart scheduler/webserver

### "Data file not found"
- Ensure `data/raw/sample_source_a.csv` exists
- Check file paths in task functions

### "Scheduler not creating DAG runs"
- Check DAG is enabled (toggle in UI)
- Verify `start_date` is in the past
- Wait a few seconds for scheduler to parse DAGs

---

## 📚 Learn More

After quick start, read:
1. **AIRFLOW_BASICS.md** - Comprehensive Airflow concepts
2. **Task functions** - Check `src/extract/`, `src/transform/`, `src/load/`
3. **Official docs** - https://airflow.apache.org/docs/

---

## 🚀 You're Ready!

Your project structure is clean and ready to learn:
```
✓ dags/ - Your workflows
✓ src/ - Your business logic  
✓ data/ - Input/output files
✓ AIRFLOW_BASICS.md - Learning guide
✓ README.md - Overview
✓ This file - Quick start
```

**Next step:** Go to http://localhost:8080 and enable `demo_dag`! 🎉
