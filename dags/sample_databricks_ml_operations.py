"""
Databricks ML Model Operations
===============================
Train, register, and deploy ML models using MLflow.

What this demonstrates:
- Training ML models
- Registering models in MLflow
- Model versioning
- Deploying models for inference
- Batch predictions

Connection: databricks_default
"""
from airflow import DAG
from airflow.providers.databricks.operators.databricks import DatabricksSubmitRunOperator
from datetime import datetime

CLUSTER = {
    "spark_version": "14.3.x-scala2.12",
    "node_type_id": "Standard_DS3_v2",
    "num_workers": 2
}

with DAG(
    dag_id='databricks_ml_operations',
    description='ML: train, register, deploy models with MLflow',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'mlflow', 'ml', 'sample'],
) as dag:
    
    # Task 1: Prepare training data
    prepare_data = DatabricksSubmitRunOperator(
        task_id='prepare_training_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/ml/prepare_data",
            "base_parameters": {
                "data_source": "sales_data",
                "train_split": "0.8"
            }
        },
    )
    
    # Task 2: Train ML model
    train_model = DatabricksSubmitRunOperator(
        task_id='train_model',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/ml/train_model",
            "base_parameters": {
                "model_type": "RandomForest",
                "max_depth": "10"
            }
        },
    )
    
    # Task 3: Evaluate model
    evaluate_model = DatabricksSubmitRunOperator(
        task_id='evaluate_model',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/ml/evaluate_model",
            "base_parameters": {
                "metrics": "accuracy,precision,recall"
            }
        },
    )
    
    # Task 4: Register model in MLflow
    register_model = DatabricksSubmitRunOperator(
        task_id='register_model',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/ml/register_model",
            "base_parameters": {
                "model_name": "sales_forecasting",
                "stage": "Staging"
            }
        },
    )
    
    # Task 5: Deploy for batch inference
    batch_inference = DatabricksSubmitRunOperator(
        task_id='batch_inference',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/ml/batch_inference",
            "base_parameters": {
                "model_name": "sales_forecasting",
                "input_table": "new_sales_data"
            }
        },
    )
    
    # Flow: Prepare → Train → Evaluate → Register → Inference
    prepare_data >> train_model >> evaluate_model >> register_model >> batch_inference
