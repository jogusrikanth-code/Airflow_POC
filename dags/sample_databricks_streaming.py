"""
Databricks Streaming Jobs
==========================
Work with Spark Structured Streaming jobs.

What this demonstrates:
- Starting streaming jobs
- Processing real-time data
- Managing stream checkpoints
- Monitoring streaming queries
- Stopping streams

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
    dag_id='databricks_streaming_jobs',
    description='Spark Streaming: process real-time data',
    schedule=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['databricks', 'streaming', 'spark', 'sample'],
) as dag:
    
    # Task 1: Start streaming from Kafka
    kafka_stream = DatabricksSubmitRunOperator(
        task_id='kafka_to_delta_stream',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/streaming/kafka_consumer",
            "base_parameters": {
                "kafka_servers": "kafka:9092",
                "topic": "events",
                "checkpoint": "/tmp/checkpoints/kafka"
            }
        },
    )
    
    # Task 2: Stream from Event Hubs
    eventhub_stream = DatabricksSubmitRunOperator(
        task_id='eventhub_to_delta_stream',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/streaming/eventhub_consumer",
            "base_parameters": {
                "connection_string": "${eventhub_connection}",
                "checkpoint": "/tmp/checkpoints/eventhub"
            }
        },
    )
    
    # Task 3: Process streaming data
    process_stream = DatabricksSubmitRunOperator(
        task_id='process_streaming_data',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/streaming/process_stream",
            "base_parameters": {
                "window_duration": "5 minutes",
                "watermark": "10 minutes"
            }
        },
    )
    
    # Task 4: Write to multiple sinks
    write_to_sinks = DatabricksSubmitRunOperator(
        task_id='write_to_multiple_sinks',
        databricks_conn_id='databricks_default',
        new_cluster=CLUSTER,
        notebook_task={
            "notebook_path": "/Workspace/streaming/write_sinks",
            "base_parameters": {
                "sink_1": "delta_table",
                "sink_2": "kafka_output",
                "trigger": "processingTime='30 seconds'"
            }
        },
    )
    
    # Parallel streaming jobs
    [kafka_stream, eventhub_stream] >> process_stream >> write_to_sinks
