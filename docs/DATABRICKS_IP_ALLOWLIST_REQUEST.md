# Databricks IP Allowlist Request

**To**: Databricks Workspace Administrator  
**From**: Srikanth Jogu  
**Date**: December 5, 2025  
**Priority**: Medium  

---

## Request Summary

Please add the following IP address to the Databricks workspace IP allowlist to enable Airflow integration.

## Details

| Item | Value |
|------|-------|
| **IP Address** | `48.216.148.118` |
| **CIDR Notation** | `48.216.148.118/32` |
| **Purpose** | AKS Airflow cluster - trigger and monitor Databricks jobs |
| **Workspace URL** | https://adb-5444953219183209.9.azuredatabricks.net |
| **Workspace ID** | 5444953219183209 |
| **Type** | Allow/Whitelist |
| **Label/Comment** | "AKS Airflow Cluster" |

## Why This is Needed

Our Airflow orchestration platform running on Azure Kubernetes Service (AKS) needs to:
1. Trigger Databricks jobs automatically
2. Monitor job execution status
3. Manage workflows and data pipelines
4. Integrate with our ETL processes

Currently, all API calls from the AKS cluster are being blocked with:
```
Error: "Unauthorized network access to workspace"
```

Adding this IP to the allowlist will enable the integration.

## Steps to Add IP (For Admin)

1. Log into Databricks workspace: https://adb-5444953219183209.9.azuredatabricks.net
2. Go to **Admin Settings** → **Security** → **IP Access Lists**
3. Click **"+ Add"** or **"Edit Access List"**
4. Fill in:
   - **IP Address/CIDR**: `48.216.148.118/32`
   - **Label**: `AKS Airflow Cluster`
   - **Type**: Allow
5. Click **Save**

## Impact

- ✅ Low risk - Only allows one specific IP address
- ✅ Production ready - Used by Airflow orchestration
- ✅ Reversible - Can be removed/changed anytime
- ✅ No user impact - Applies to service account, not individual users

## Rollback Plan

If issues arise, this IP can be immediately removed from the allowlist without affecting other users.

---

## Contact

If you have questions, please reach out.

Thank you!
