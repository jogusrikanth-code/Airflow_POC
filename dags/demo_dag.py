"""
Demo DAG - A Simple Airflow Workflow for Beginners

This is the simplest possible Airflow DAG to understand basic concepts:
- DAG structure
- Task definition
- Task dependencies

To run this DAG:
4. Check logs by clicking on tasks
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.empty import EmptyOperator

"""
ARCHIVED: demo_dag.py

This file was an example/demo DAG and has been archived (made a no-op).
Removing DAG definitions prevents Airflow from loading example workloads.

If you need this example later, restore from Git history or copy from
the project README/examples.
"""

# No DAG objects are defined in this file. Archived to keep Airflow clean.