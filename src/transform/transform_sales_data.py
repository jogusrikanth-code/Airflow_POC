"""
Transform Task
==============
Aggregates raw sales data by date and writes to processed folder.

Purpose: Demonstrate data transformation and output writing
Input: data/raw/sample_source_a.csv
Output: data/processed/sales_daily_summary.csv
"""

import os
import pandas as pd


def transform_sales_data(**context):
    """
    Transform and aggregate sales data.
    
    This function:
    1. Reads raw CSV file
    2. Groups amounts by date
    3. Sums amounts for each date
    4. Writes results to processed folder
    
    Args:
        **context: Airflow context object (passed automatically)
        
    Raises:
        FileNotFoundError: If raw file not found
        ValueError: If required columns missing
    """
    # Calculate paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    raw_path = os.path.join(base_dir, "data", "raw", "sample_source_a.csv")
    processed_path = os.path.join(base_dir, "data", "processed", "sales_daily_summary.csv")

    # Read raw data
    df = pd.read_csv(raw_path)

    # Validate required columns exist
    if "date" not in df.columns or "amount" not in df.columns:
        raise ValueError("Expected columns 'date' and 'amount' in sample_source_a.csv")

    # Transform: Group by date and sum amounts
    summary = df.groupby("date", as_index=False)["amount"].sum()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    
    # Write results to processed folder
    summary.to_csv(processed_path, index=False)

    print(f"✓ Transformed {len(df)} rows into {len(summary)} daily summaries")
    print(f"✓ Wrote aggregated data to {processed_path}")
