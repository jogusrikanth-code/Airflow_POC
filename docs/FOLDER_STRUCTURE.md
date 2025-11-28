# Project Folder Structure Guide

## Overview
This document explains the purpose of each folder in your Airflow POC and best practices for organizing your files.

---

## 📂 Directory Reference

### `airflow_home/`
**Purpose:** Airflow configuration and logs directory

**Contents:**
- `airflow.cfg` - Main Airflow configuration file
- `webserver_config.py` - Web UI customization
- `airflow.db` - SQLite database (auto-created)
- `logs/` - Task execution logs (organized by DAG and task)

**When to modify:**
- Only modify `airflow.cfg` for environment-specific settings
- Leave `webserver_config.py` as-is for POC

---

### `dags/`
**Purpose:** Airflow DAG definitions

**Contents:**
- `__init__.py` - Package marker
- `demo_dag.py` - Simple starter DAG
- `etl_example_dag.py` - Full ETL pipeline example

**Best Practices:**
- ✅ One DAG per file or group related DAGs
- ✅ Use descriptive names: `daily_sales_etl.py` not `dag1.py`
- ✅ Add docstrings explaining the DAG purpose
- ✅ Keep DAG files in this folder only
- ❌ Don't import from this folder in other modules (creates circular dependencies)

**Adding Your First DAG:**
1. Create `my_first_dag.py` in this folder
2. Define your DAG with unique `dag_id`
3. Refresh Airflow UI
4. It will appear in the DAG list

---

### `src/`
**Purpose:** Application business logic (not Airflow-specific)

**Structure:**
```
src/
├── __init__.py
├── extract/          # Data extraction logic
│   ├── __init__.py
│   └── extract_from_source_a.py
├── transform/        # Data transformation logic
│   ├── __init__.py
│   └── transform_sales_data.py
├── load/             # Data loading logic
│   ├── __init__.py
│   └── load_to_dw.py
└── utils/            # Shared utilities
	├── __init__.py
	└── helpers.py
```

**Best Practices:**
- ✅ Keep business logic separate from DAG files
- ✅ Functions should be reusable and testable
- ✅ Use meaningful module names
- ✅ Add docstrings to all functions
- ✅ Import in DAGs using: `from src.extract.extract_from_source_a import extract_from_source_a`

**Example Structure for Growing Project:**
```
src/
├── connectors/       # Database/API connections
├── schemas/          # Data schemas and validation
├── processors/       # Data processing logic
└── logging/          # Custom logging utilities
```

---

### `data/`
**Purpose:** Input and output data storage

**Structure:**
```
data/
├── raw/                          # Input data (read-only)
│   └── sample_source_a.csv
├── processed/                    # Transformed data
│   └── sales_daily_summary.csv
├── staging/                      # Intermediate data
└── archive/                      # Historical data
```

**Best Practices:**
- ✅ `raw/` - Never modify, treat as read-only
- ✅ `processed/` - Task outputs go here
- ✅ `staging/` - Temporary files between tasks
- ✅ `archive/` - Keep historical data for auditing
- ❌ Don't commit large files to git (add to .gitignore)

**File Organization Example:**
```
data/
├── raw/
│   ├── 2024-01/
│   ├── 2024-02/
│   └── ...
└── processed/
	├── daily_summary_2024-01-01.csv
	├── daily_summary_2024-01-02.csv
	└── ...
```

---

### `docker/`
**Purpose:** Docker containerization files

**Contents:**
- `docker-compose.yaml` - Multi-container orchestration

**When to use:**
- Deploy Airflow with PostgreSQL database
- Share development environment with team
- Replicate production setup locally

**Quick Start:**
```bash
cd docker
docker-compose up
```

---

### `plugins/`
**Purpose:** Custom Airflow extensions

**Structure:**
```
plugins/
├── __init__.py
├── hooks/                        # Custom database connectors
│   ├── __init__.py
│   └── my_custom_hook.py
├── operators/                    # Custom operators
│   ├── __init__.py
│   └── my_custom_operator.py
└── sensors/                      # Custom sensors
	├── __init__.py
	└── my_custom_sensor.py
```

**When to use:**
- Reusable components across multiple DAGs
- Custom integration with external systems
- Shared business logic for operators

**Example Custom Operator:**
```python
# plugins/operators/my_operator.py
from airflow.models import BaseOperator

class MyCustomOperator(BaseOperator):
	def execute(self, context):
		# Your logic here
		pass
```

---

### `config/`
**Purpose:** Configuration files for application

**Suggested Contents:**
```
config/
├── __init__.py
├── dev.py              # Development settings
├── prod.py             # Production settings
├── database.py         # Database configurations
└── logging.py          # Logging configurations
```

**Example:**
```python
# config/dev.py
DEBUG = True
LOG_LEVEL = 'DEBUG'
DB_HOST = 'localhost'
```

---

### `reports/`
**Purpose:** Generated output reports and figures

**Structure:**
```
reports/
├── figures/            # Visualizations
│   ├── daily_sales.png
│   └── trends.pdf
├── summaries/          # Text reports
│   └── 2024-01-01_daily_summary.txt
└── dashboards/         # Dashboard configurations
```

---

### `tests/`
**Purpose:** Unit and integration tests

**Structure:**
```
tests/
├── __init__.py
├── test_extract.py     # Test extract functions
├── test_transform.py   # Test transform functions
├── test_load.py        # Test load functions
└── test_dags.py        # Test DAG structure and dependencies
```

**Example Test:**
```python
# tests/test_extract.py
import pytest
from src.extract.extract_from_source_a import extract_from_source_a

def test_extract_returns_count():
	result = extract_from_source_a()
	assert isinstance(result, int)
```

**Run Tests:**
```bash
pytest tests/
```

---

### `logs/`
**Purpose:** Airflow execution logs (auto-generated)

**Structure:**
```
logs/
├── dag_processor_manager/
├── scheduler/
└── dags/
	└── demo_dag/
		├── start/
		│   └── 2024-01-01T08:00:00+00:00/
		│       └── attempt=1.log
		└── end/
			└── 2024-01-01T08:00:00+00:00/
				└── attempt=1.log
```

**Notes:**
- Auto-generated by Airflow
- Safe to delete (logs can be recreated)
- Add to `.gitignore`

---

### `docs/`
**Purpose:** Project documentation

**Suggested Contents:**
```
docs/
├── architecture.md              # System design
├── deployment.md                # How to deploy
├── troubleshooting.md           # Common issues
└── data_dictionary.md           # Data field definitions
```

---

## 📋 File Organization Best Practices

### Adding a New Feature

**Step 1: Create business logic**
```
src/my_feature/
├── __init__.py
└── processor.py
```

**Step 2: Create DAG to use it**
```
dags/
└── my_feature_dag.py
```

**Step 3: Add data**
```
data/
├── raw/my_data.csv
└── processed/
```

**Step 4: Add tests**
```
tests/
└── test_my_feature.py
```

### Growth Path

```
POC Phase:
├── dags/demo_dag.py
├── src/extract/
└── data/raw/

Early Production:
├── dags/daily_etl_dag.py
├── dags/hourly_etl_dag.py
├── src/extract/, transform/, load/
├── plugins/operators/
├── tests/
└── config/

Mature Production:
├── dags/ (multiple files)
├── src/ (organized by domain)
├── plugins/ (custom operators/hooks)
├── config/ (env-specific)
├── tests/ (comprehensive)
├── docs/ (architecture, runbooks)
└── monitoring/ (alerting, metrics)
```

---

## 🚀 How to Add Files to Source Control

### Create `.gitignore`
```
# Airflow
airflow.db
airflow_home/logs/
airflow_home/plugins/

# Data
data/raw/*
data/processed/*
data/staging/*

# Python
__pycache__/
*.pyc
.venv/
venv/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

### Track Important Files
```bash
git add dags/
git add src/
git add tests/
git add config/
git add README.md
git add docs/
```

---

## 🎯 Quick Reference

| Folder | Purpose | Who Creates | Modify? |
|--------|---------|-------------|---------|
| `airflow_home/` | Config & logs | Airflow | Rarely |
| `dags/` | DAG definitions | You | Often |
| `src/` | Business logic | You | Often |
| `data/` | Files in/out | Tasks | Often |
| `docker/` | Deployment | You | Rarely |
| `plugins/` | Extensions | You | Sometimes |
| `config/` | App config | You | Sometimes |
| `tests/` | Unit tests | You | Often |
| `reports/` | Generated reports | Tasks | Often |
| `docs/` | Documentation | You | Sometimes |
| `logs/` | Execution logs | Airflow | Never |

---

## 📞 Troubleshooting

### "Module not found" error
- Check file is in correct folder
- Check `__init__.py` exists in package folders
- Check import path matches folder structure

### "DAG not appearing"
- Verify file is in `dags/` folder
- Check for Python syntax errors
- Check `dag_id` is unique

### "Too many files in root"
- Create subdirectories under `src/`
- Group related DAGs into category folders
- Use clear naming conventions

---

## ✅ Your Project is Well-Organized!

Your current structure is clean and ready to scale:
```
✓ Separation of concerns (dags/ vs src/)
✓ Data organization (raw/ vs processed/)
✓ Documentation (README, docs/*)
✓ Docker support ready
✓ Space for custom plugins
```

Good foundation for learning and growing your Airflow POC! 🚀
