---
name: precision-bio-infra
description: >
  Expert guide for GCP deployment, security, and hospital-specific infrastructure.
  Covers Cloud Run, IAM, VPC, and secrets management for bioinformatics.
---

# Precision Bio-Infrastructure

This skill ensures that the platform is deployed securely and efficiently on Google Cloud or in clinical environments.

## ☁️ GCP Deployment

Standard deployment uses Cloud Run and Cloud Build:
- **Service Account**: Use the dedicated compute service account with `roles/run.invoker` and `roles/storage.objectViewer`.
- **Scaling**: Most servers scale to zero (`min-instances 0`) to save costs, except for heavy-use multiomics servers.
- **Automation**: Use `deploy.sh` and `cloudbuild.yaml` in each server directory.

## 🏥 Hospital & Clinical Deployment

Follow the patterns in `infrastructure/hospital-deployment/`:
- **VPC Networking**: Use `setup-vpc.sh` to isolate genomic data traffic.
- **Secrets**: Store all API keys (Anthropic/Gemini) in GCP Secret Manager, never in environment variables in production.
- **OAuth2**: Use `deploy-oauth2-proxy.sh` if deploying beyond IAM-restricted Cloud Run (e.g., GKE).

## 🔒 Security & Audit

- **Audit Logging**: Ensure `setup-audit-logging.sh` is run to track all tool invocations in Cloud Logging.
- **Bias Auditing**: Utilize `shared/utils/bias_detection.py` and the tools in `infrastructure/audit/` when deploying new predictive models (e.g., GEARS).

## 💰 Cost Optimization

- Reference `shared/utils/cost_tracking.py` to ensure new infras include budget alerting.
- Set `timeout` appropriately (300s default, 600s for perturbation training).

---

**Use this skill when:**
- Deploying a new MCP server to Cloud Run.
- Setting up a new hospital project environment.
- Configuring IAM or VPC permissions for bioinformatics workloads.
