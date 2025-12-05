# 📚 Airflow Basics - Your Complete Learning Guide

Hey there! Welcome to your comprehensive guide to mastering Apache Airflow. Whether you're building your first DAG or designing complex enterprise workflows, this guide has you covered. Let's dive in! 🚀

> **New to Airflow?** Perfect! This guide starts from the fundamentals and builds up to advanced patterns. Take your time, experiment with examples, and don't hesitate to revisit sections.

## 📖 Table of Contents
1. [What is Apache Airflow?](#what-is-apache-airflow) — The big picture (5 min)
2. [Core Concepts](#core-concepts) — Essential terminology (10 min)
3. [DAG Structure](#dag-structure) — Building your first workflow (15 min)
4. [Operators](#operators) — Task types and when to use them (15 min)
5. [Task Dependencies](#task-dependencies) — Orchestrating workflow logic (10 min)
6. [Execution Model](#execution-model) — How Airflow runs your DAGs (10 min)
7. [Hands-On Examples](#hands-on-examples) — Real code you can use (30 min)
8. [Best Practices](#best-practices) — Production-ready patterns (15 min)

**Total Learning Time:** ~2 hours to mastery! ⏱️

---

## 🎯 What is Apache Airflow?

**Apache Airflow** is an open-source workflow orchestration platform that allows you to:
- Define workflows as code (Python)
- Schedule and monitor job executions
- Handle dependencies between tasks
- Retry failed tasks automatically
- Scale from a single task to thousands

### 🌍 Real-World Use Cases:

> **Where is Airflow used in the wild?**

| Use Case | Example | Typical Schedule |
|----------|---------|------------------|
| **📊 ETL Pipelines** | Extract data from sources, transform, load to warehouse | Hourly/Daily |
| **✅ Data Quality Checks** | Validate data at various stages | After each ETL run |
| **⚙️ Batch Processing** | Run large computational jobs on a schedule | Nightly |
| **📈 Reporting** | Generate and distribute business reports | Daily/Weekly |
| **🔗 Microservice Orchestration** | Coordinate multiple services and APIs | Event-driven |

> **💡 Pro Tip:** Start with simple ETL pipelines before moving to complex orchestration patterns!

---

## 🧠 Core Concepts (Master These First!)

These are the building blocks you'll use every day. Don't worry if they seem abstract—they'll make perfect sense once you see code examples!

### 1️⃣ **DAG (Directed Acyclic Graph)** 🗺️
A workflow represented as a directed graph where:
- **Nodes** = Tasks (individual units of work)
- **Edges** = Dependencies (task order)
- **Acyclic** = No circular dependencies (A→B→C, not A→B→A)

> **Think of it like:** A recipe! Each step (task) has an order, and you can't start step 3 before step 2 is done.

```
	┌─────────┐
	│  Start  │
	└────┬────┘
		 │
	┌────▼────┐
	│ Extract  │
	└────┬────┘
		 │
	┌────▼────┐
	│Transform │
	└────┬────┘
		 │
	┌────▼────┐
	│   Load   │
	└────┬────┘
		 │
	┌────▼────┐
	│   End    │
	└─────────┘
```

### 2️⃣ **Task** ✅
A single unit of work in your workflow:
- Execute Python code 🐍
- Run shell commands 💻
- Wait for a sensor condition ⏳
- Transfer data between systems 📤

### 3️⃣ **Operator** 🔧
Defines what a task does. Common operators:
- `PythonOperator`: Execute Python callable 🐍
- `BashOperator`: Execute bash command 💻
- `EmailOperator`: Send email 📧
- `SensorOperator`: Wait for a condition ⏰
- `CustomOperator`: Your own logic 🎨

> **Remember:** Operators are like tools in your toolbox. Pick the right one for the job!

### 4️⃣ **Schedule Interval** ⏰
How often a DAG runs:

| Schedule | Cron Expression | When It Runs |
|----------|----------------|---------------|
| `@hourly` | `0 * * * *` | Every hour at minute 0 |
| `@daily` | `0 0 * * *` | Every day at midnight |
| `@weekly` | `0 0 * * 0` | Every Sunday at midnight |
| `@monthly` | `0 0 1 * *` | First day of month at midnight |
| Custom | `"0 8 * * *"` | Every day at 8 AM |

> **💡 Pro Tip:** Start with `@daily` for learning. You can always change it later!

### 5️⃣ **Task Instance** 🎯
One execution of a specific task at a specific time.
- Example: `extract_from_source_a` on 2024-01-01 08:00 is ONE task instance

### 6. **DAG Run**
One complete execution of all tasks in a DAG.
- Example: All tasks on 2024-01-01 08:00 form ONE DAG run

---

## 🏗️ DAG Structure (Let's Build Your First Workflow!)

Time to see real code! This section shows you how to create a DAG from scratch.

### 📝 Minimal DAG Example

> **This is the simplest possible DAG.** Copy this, modify it, and you'll have your first workflow running in minutes!

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator

# Define default arguments
default_args = {
	'owner': 'airflow',                    # Task owner
	'retries': 1,                          # Retry failed tasks once
	'retry_delay': timedelta(minutes=5),   # Wait 5 min before retry
	'start_date': datetime(2024, 1, 1),    # When DAG can first run
}

# Create DAG object
with DAG(
	dag_id='my_first_dag',                 # Unique identifier
	default_args=default_args,
	schedule_interval='@daily',            # Run daily
	catchup=False,                         # Don't run past schedules
	description='My first Airflow DAG',
	tags=['learning'],                     # For organization
) as dag:
    
	# Define tasks
	start_task = EmptyOperator(task_id='start')
	end_task = EmptyOperator(task_id='end')
    
	# Define dependencies
	start_task >> end_task
```

### Key Parameters Explained

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `dag_id` | Unique DAG identifier | `'etl_pipeline'` |
| `default_args` | Default settings for all tasks | retries, owner, etc. |
| `schedule_interval` | How often to run | `'@daily'`, `'0 8 * * *'` |
| `start_date` | First possible execution date | `datetime(2024, 1, 1)` |
| `end_date` | Last possible execution date | `datetime(2024, 12, 31)` |
| `catchup` | Run backlog of missed schedules | `True/False` |
| `tags` | For organizing DAGs in UI | `['prod', 'etl']` |

---

## 🔧 Operators (Your Task Toolbox!)

Operators are the building blocks of your workflows. Each operator type has a specific purpose. Let's explore the most common ones!

### 1️⃣ **EmptyOperator** (No-op) ⭕
```python
from airflow.operators.empty import EmptyOperator

task = EmptyOperator(task_id='placeholder')
```

> **When to use:** Structuring workflows, testing dependencies, placeholders

---

### 2️⃣ **PythonOperator** (Execute Python) 🐍

> **Most popular operator!** This is what you'll use for most custom logic.
```python
from airflow.operators.python import PythonOperator

def my_python_function(param1, **context):
	print(f"Param: {param1}")
	return "result"

task = PythonOperator(
	task_id='python_task',
	python_callable=my_python_function,
	op_kwargs={'param1': 'value1'}  # Pass parameters
)
```
Use: Data processing, transformations

---

### 3. **BashOperator** (Execute Shell)
```python
from airflow.operators.bash import BashOperator

task = BashOperator(
	task_id='bash_task',
	bash_command='echo "Hello from Bash"'
)
```
Use: System commands, ETL tools

---

### 4. **EmailOperator** (Send Email)
```python
from airflow.operators.email import EmailOperator

task = EmailOperator(
	task_id='send_email',
	to='user@example.com',
	subject='Task Completed',
	html_content='<h1>Your task ran successfully</h1>'
)
```
Use: Notifications

---

### 5. **Sensor** (Wait for Condition)
```python
from airflow.sensors.filesystem import FileSensor

task = FileSensor(
	task_id='wait_for_file',
	filepath='/path/to/file.txt',
	poke_interval=60  # Check every 60 seconds
)
```
Use: Waiting for external events, file arrivals, etc.

---

## 🔗 Task Dependencies (Connecting the Dots!)

Dependencies define the order tasks run in. Airflow gives you flexible ways to express this!

### Method 1: Bitshift Operators (Recommended!) 👍
```python
# Sequential
task1 >> task2 >> task3

# Parallel branches
task1 >> [task2, task3] >> task4
```

### Method 2: Set Methods
```python
# Set upstream
task2.set_upstream(task1)

# Set downstream
task1.set_downstream(task2)
```

### Visual Examples

**Sequential:**
```
task1 >> task2 >> task3
  ▼      ▼      ▼
  1      2      3
```

**Parallel:**
```
	   ┌─ task2
task1 ┤
	   └─ task3
	   ▼  ▼
	   2  3
```

**Diamond Pattern:**
```
	┌─ task2 ─┐
task1         task4
	└─ task3 ─┘
```

```python
task1 >> [task2, task3] >> task4
```

---

## ⚙️ Execution Model (How Airflow Works Behind the Scenes)

Understanding how Airflow executes your workflows will help you debug issues and optimize performance!

### 🔄 DAG Execution Flow

```
1. DAG Definition (your Python code)
   ↓
2. Scheduler Parses DAG
   ↓
3. Creates DAG Runs (based on schedule_interval)
   ↓
4. Task Instances Created
   ↓
5. Executor Runs Tasks (based on dependencies)
   ↓
6. Task Status Updated (success/failed/retry)
   ↓
7. Logs Stored
   ↓
8. Results Available in UI
```

### 🚦 Task States (The Task Lifecycle)

> **Every task goes through these states.** Understanding them helps with debugging!

```
queued 🟡
  ↓
running 🔵
  ├─→ success ✅ (Task completed successfully!)
  ├─→ failed ❌ → retry → queued → running
  ├─→ skipped ⊘ (Intentionally skipped)
  ├─→ upstream_failed ⚠️ (A dependency failed)
  └─→ upstream_skipped 〰️ (A dependency was skipped)
```

> **💡 Tip:** Check the UI Grid View to see task states visually—colors make it easy!

### Context Object (**kwargs)
Airflow passes context to tasks:

```python
def my_task(**context):
	# Common context variables
	execution_date = context['execution_date']
	task_instance = context['task_instance']
	ti_key = context['ti']  # Shorthand
    
	# Get values
	print(f"Execution Date: {execution_date}")
	print(f"Task: {task_instance.task_id}")
	print(f"Try: {task_instance.try_number}")
```

---

## 💻 Hands-On Examples (Copy, Paste, Run!)

Time to get practical! These are real, working examples you can copy into your `dags/` folder and run immediately.

### Example 1️⃣: Simple Sequential Pipeline

> **Perfect for:** Your first DAG! A classic ETL pattern that runs tasks in sequence.

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

def extract():
	print("Extracting data...")
	return {"rows": 1000}

def transform():
	print("Transforming data...")
	return {"rows": 950}

def load():
	print("Loading data...")

default_args = {
	'owner': 'data_team',
	'retries': 2,
	'retry_delay': timedelta(minutes=5),
	'start_date': datetime(2024, 1, 1),
}

with DAG(
	dag_id='etl_pipeline',
	default_args=default_args,
	schedule_interval='@daily',
) as dag:
    
	t1 = PythonOperator(task_id='extract', python_callable=extract)
	t2 = PythonOperator(task_id='transform', python_callable=transform)
	t3 = PythonOperator(task_id='load', python_callable=load)
    
	t1 >> t2 >> t3
```

---

### Example 2: Parallel Branches

```python
from airflow import DAG
from airflow.operators.empty import EmptyOperator
from datetime import datetime

default_args = {'owner': 'airflow', 'start_date': datetime(2024, 1, 1)}

with DAG(dag_id='parallel_dag', default_args=default_args) as dag:
    
	start = EmptyOperator(task_id='start')
    
	# Parallel branches
	check_quality = EmptyOperator(task_id='check_quality')
	generate_report = EmptyOperator(task_id='generate_report')
	send_notification = EmptyOperator(task_id='send_notification')
    
	end = EmptyOperator(task_id='end')
    
	# Dependencies
	start >> [check_quality, generate_report] >> send_notification >> end
```

---

### Example 3: Task Communication (XCom)

```python
def push_task(**context):
	context['task_instance'].xcom_push(key='data', value={'result': 42})

def pull_task(**context):
	value = context['task_instance'].xcom_pull(
		task_ids='push_task',
		key='data'
	)
	print(f"Received: {value}")  # {'result': 42}

with DAG(dag_id='xcom_dag', ...) as dag:
	t1 = PythonOperator(task_id='push_task', python_callable=push_task)
	t2 = PythonOperator(task_id='pull_task', python_callable=pull_task)
    
	t1 >> t2
```

---

## ⭐ Best Practices (Production-Ready Patterns!)

Follow these guidelines to write maintainable, reliable DAGs that your team will love!

### 1️⃣ **Idempotence** (Run It Twice, Get Same Result) 🔄

> **The Golden Rule:** Your tasks should produce the same result no matter how many times they run.
Tasks should produce the same result if run multiple times:
```python
# Bad: Appends to file (not idempotent)
with open('output.txt', 'a') as f:
	f.write('data\n')

# Good: Overwrites file (idempotent)
with open('output.txt', 'w') as f:
	f.write('data\n')
```

### 2. **Atomic Tasks**
Each task should do one thing:
```python
# Bad: Multiple steps in one task
def etl_all():
	extract()
	transform()
	load()

# Good: Separate tasks
def extract(): ...
def transform(): ...
def load(): ...
```

### 3. **Meaningful Task IDs**
```python
# Bad
task1 = PythonOperator(task_id='t1', ...)

# Good
task1 = PythonOperator(task_id='extract_customer_data', ...)
```

### 4. **Set Owners**
```python
default_args = {
	'owner': 'data_engineering_team',
	'email': 'team@example.com',
	'email_on_failure': True,
}
```

### 5. **Use Tags**
```python
with DAG(dag_id='my_dag', tags=['prod', 'etl', 'daily']) as dag:
	...
```

### 6. **Error Handling**
```python
default_args = {
	'retries': 3,
	'retry_delay': timedelta(minutes=5),
	'max_retry_delay': timedelta(hours=1),  # Cap retry wait time
	'retry_exponential_backoff': True,  # Exponential backoff
}
```

### 7. **Document DAGs**
```python
with DAG(
	dag_id='my_dag',
	description='Extract sales data daily, transform to summary, load to DW',
	...
) as dag:
	pass
```

---

## Common Patterns

### Pattern 1: Conditional Execution
```python
from airflow.operators.python import BranchPythonOperator

def choose_branch(**context):
	if some_condition:
		return 'task_a'
	else:
		return 'task_b'

branch = BranchPythonOperator(
	task_id='branch_task',
	python_callable=choose_branch
)

task_a = EmptyOperator(task_id='task_a')
task_b = EmptyOperator(task_id='task_b')

branch >> [task_a, task_b]
```

### Pattern 2: Retry on Failure
```python
default_args = {
	'retries': 3,
	'retry_delay': timedelta(minutes=5),
}
```

### Pattern 3: Schedule with Cron
```python
# Run at 8 AM every Monday
schedule_interval = '0 8 * * 1'

# Run every 30 minutes
schedule_interval = '*/30 * * * *'
```

---

## 🎉 Summary — You Did It!

### ✅ **You now understand:**
- ✨ What Airflow is and why it's the industry standard for orchestration
- 🏗️ DAG structure and how to define workflows as code
- 🔧 Different operators and when to use each one
- 🔗 How to create task dependencies (sequential, parallel, conditional)
- ⚙️ Execution model and task states (how Airflow runs your code)
- ⭐ Best practices for production-ready DAGs

### 🎯 **Your Next Steps:**

1️⃣ **Practice Makes Perfect** → Review the existing DAGs in `dags/` folder  
2️⃣ **See It Live** → Run them in the Airflow UI at http://localhost:8080  
3️⃣ **Debug Like a Pro** → Check logs and task outputs  
4️⃣ **Experiment Freely** → Modify examples to see what happens  
5️⃣ **Build Your Own** → Create a DAG for your specific use case

> **💡 Pro Tip:** Start with Example 1 (Simple Sequential Pipeline), get it working, then build from there. Every expert started exactly where you are now!

### 📚 **Continue Learning:**
- [LEARNING_CHECKLIST.md](LEARNING_CHECKLIST.md) — Track your progress
- [ARCHITECTURE.md](ARCHITECTURE.md) — Understand how components fit together
- [POSTGRES_VSCODE_CONNECTION.md](POSTGRES_VSCODE_CONNECTION.md) — Query the database for debugging

---

**Happy Airflow Learning! 🚀** You're now equipped to build production-grade workflows. Go orchestrate something amazing!
