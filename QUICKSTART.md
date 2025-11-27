# Quick Start Guide - Running Your First Airflow DAG

## ⚡ 5-Minute Quick Start

### Step 1: Initialize Airflow
```bash
# Set up the SQLite database
airflow db init

# Create admin user
airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

### Step 2: Start Airflow (2 Terminals Required)

**Terminal 1 - Scheduler:**
```bash
airflow scheduler
```

**Terminal 2 - Web Server:**
```bash
airflow webserver --port 8080
```

### Step 3: Access the Web UI
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

## ✅ Test Your Setup

### Run demo_dag (Simplest)
```bash
# From command line
airflow dags trigger -d demo_dag

# View in UI
# - It will show 2 tasks (start → end)
# - Should complete in seconds
```

### Run etl_example_dag (Full Pipeline)
```bash
# From command line
airflow dags trigger -d etl_example_dag

# What happens:
# 1. Extract reads data/raw/sample_source_a.csv
# 2. Transform aggregates by date
# 3. Load verifies data/processed/sales_daily_summary.csv

# Check results
# - Open data/processed/sales_daily_summary.csv
# - Should have aggregated data by date
```

---

## 🔍 Debugging Tips

### Check Logs
1. Go to DAG → Runs → Task → Logs tab
2. Look for any error messages

### Test Individual Tasks
```bash
# Test a single task without running full DAG
airflow tasks test demo_dag start 2024-01-01
```

### List All DAGs
```bash
airflow dags list
```

### View Task Details
```bash
airflow tasks list -d demo_dag
```

### Pause/Unpause DAG
```bash
# Stop DAG from running on schedule
airflow dags pause demo_dag

# Resume
airflow dags unpause demo_dag
```

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
