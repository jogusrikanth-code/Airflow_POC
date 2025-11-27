"""
Load Task
=========
Verifies that processed data file exists (in POC, only validation).

Purpose: Demonstrate final step in ETL pipeline
Input: data/processed/sales_daily_summary.csv
Output: Prints load confirmation to logs
"""

import os


def load_to_dw(**context):
    """
    Load step for the Data Warehouse (DW).
    
    In a real scenario, this would:
    - Connect to a database or data warehouse
    - Load the processed data
    - Perform data quality checks
    - Generate audit logs
    
    For this POC, it simply verifies the processed file exists.
    
    Args:
        **context: Airflow context object (passed automatically)
        
    Raises:
        FileNotFoundError: If processed file not found
    """
    # Calculate path to processed data
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    processed_path = os.path.join(base_dir, "data", "processed", "sales_daily_summary.csv")

    # Verify processed file exists
    if not os.path.exists(processed_path):
        raise FileNotFoundError(f"Processed file not found: {processed_path}")

    # In production, would load to actual DW system here
    print(f"✓ Load step verified: {processed_path} exists")
    print(f"✓ In production, data from {processed_path} would be loaded to target system")
