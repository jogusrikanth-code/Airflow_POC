# Apply Databricks Provider to Airflow Deployment
# This script permanently adds the Databricks provider to all Airflow pods

Write-Host "Applying Databricks Provider to Airflow deployment..." -ForegroundColor Cyan

# Apply the ConfigMap with the installation script
Write-Host "`n1. Creating provider installation ConfigMap..." -ForegroundColor Yellow
kubectl apply -f kubernetes/provider-init-configmap.yaml

# Apply patches to add init containers to deployments
Write-Host "`n2. Patching API Server deployment..." -ForegroundColor Yellow
kubectl patch deployment airflow-api-server -n airflow --patch "
spec:
  template:
    spec:
      initContainers:
      - name: install-providers
        image: apache/airflow:3.0.2-python3.11
        command: ['/bin/bash', '/scripts/install-providers.sh']
        volumeMounts:
        - name: provider-scripts
          mountPath: /scripts
        - name: airflow-providers
          mountPath: /home/airflow/.local
      containers:
      - name: api-server
        volumeMounts:
        - name: airflow-providers
          mountPath: /home/airflow/.local
      volumes:
      - name: provider-scripts
        configMap:
          name: airflow-provider-init
          defaultMode: 493
      - name: airflow-providers
        emptyDir: {}
"

Write-Host "`n3. Patching Scheduler deployment..." -ForegroundColor Yellow
kubectl patch deployment airflow-scheduler -n airflow --patch "
spec:
  template:
    spec:
      initContainers:
      - name: install-providers
        image: apache/airflow:3.0.2-python3.11
        command: ['/bin/bash', '/scripts/install-providers.sh']
        volumeMounts:
        - name: provider-scripts
          mountPath: /scripts
        - name: airflow-providers
          mountPath: /home/airflow/.local
      containers:
      - name: scheduler
        volumeMounts:
        - name: airflow-providers
          mountPath: /home/airflow/.local
      volumes:
      - name: provider-scripts
        configMap:
          name: airflow-provider-init
          defaultMode: 493
      - name: airflow-providers
        emptyDir: {}
"

Write-Host "`n4. Patching DAG Processor deployment..." -ForegroundColor Yellow
kubectl patch deployment airflow-dag-processor -n airflow --patch "
spec:
  template:
    spec:
      initContainers:
      - name: install-providers
        image: apache/airflow:3.0.2-python3.11
        command: ['/bin/bash', '/scripts/install-providers.sh']
        volumeMounts:
        - name: provider-scripts
          mountPath: /scripts
        - name: airflow-providers
          mountPath: /home/airflow/.local
      containers:
      - name: dag-processor
        volumeMounts:
        - name: airflow-providers
          mountPath: /home/airflow/.local
      volumes:
      - name: provider-scripts
        configMap:
          name: airflow-provider-init
          defaultMode: 493
      - name: airflow-providers
        emptyDir: {}
"

Write-Host "`n5. Waiting for rollout to complete..." -ForegroundColor Yellow
kubectl rollout status deployment/airflow-api-server -n airflow
kubectl rollout status deployment/airflow-scheduler -n airflow  
kubectl rollout status deployment/airflow-dag-processor -n airflow

Write-Host "`n✅ Databricks provider permanently installed!" -ForegroundColor Green
Write-Host "`nThe provider will now be installed automatically on every pod restart." -ForegroundColor Cyan
Write-Host "Refresh your Airflow UI to see Databricks in the connection dropdown." -ForegroundColor Cyan
