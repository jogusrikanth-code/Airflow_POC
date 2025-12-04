# Custom Airflow image with Databricks provider
FROM apache/airflow:3.0.2-python3.11

# Switch to root to install packages
USER root

# Install any additional system packages if needed
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     <your-package> \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# Switch back to airflow user
USER airflow

# Install Databricks provider and any other Python packages
RUN pip install --no-cache-dir \
    apache-airflow-providers-databricks==7.8.0

# Optional: Install other providers you might need
# RUN pip install --no-cache-dir \
#     apache-airflow-providers-microsoft-mssql \
#     apache-airflow-providers-microsoft-azure

# Metadata
LABEL maintainer="Srikanth Jogu"
LABEL description="Apache Airflow 3.0.2 with Databricks provider"
LABEL version="3.0.2-databricks"
