"""
Extract Task
============
Reads raw CSV data from the file system and logs the record count.

Purpose: Demonstrate basic file reading and Python operator usage
Output: Prints row count to logs
"""

import os
import pandas as pd


def extract_from_source_a(**context):
    """
    Extract raw data from CSV file.
    
    This function:
    1. Locates the raw CSV file (data/raw/sample_source_a.csv)
    2. Reads it using pandas
    3. Logs the number of records
    
    Args:
        **context: Airflow context object (passed automatically)
        
    Raises:
        FileNotFoundError: If sample file doesn't exist
    """
    # Calculate path to raw data file
    # Go up 3 directory levels: src/extract -> src -> project_root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    raw_path = os.path.join(base_dir, "data", "raw", "sample_source_a.csv")

    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Sample file not found: {raw_path}")

    # Read CSV file
    df = pd.read_csv(raw_path)
    
    # Log the result
    print(f"✓ Extracted {len(df)} rows from {raw_path}")
    
    # Return data for next task (optional)
    return len(df)