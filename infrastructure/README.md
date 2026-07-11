# Infrastructure

Deployment scripts and configuration for the Precision Medicine MCP Platform.

---

## Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| **Google Cloud SDK** (`gcloud`) | Latest | GCP project setup, Cloud Run deployment, Secret Manager |
| **Docker** | 20.10+ | Building container images for MCP servers |
| **Python** | 3.11+ | Running MCP servers locally, bias audit scripts |
| **uv** | Latest | Python dependency management (used by all servers) |
| **Bash** | 4.0+ | Running deployment and setup scripts |

**Not required:** Kubernetes/kubectl (Cloud Run is serverless), Terraform (shell scripts used instead).

---

## Directory Structure

```
infrastructure/
├── deployment/          # GCP Cloud Run deployment
│   ├── deploy_to_gcp.sh         # Deploy all MCP servers to Cloud Run
│   ├── setup_environment.sh     # Environment setup helper
│   ├── .env.gcp                 # GCP environment template
│   └── test-data/               # Deployment validation data
├── docker/              # Docker base images
│   ├── README.md                # Docker build instructions
│   └── base-images/             # Shared base images for servers
├── hospital-deployment/ # Hospital-specific setup
│   ├── README.md                # Full hospital deployment guide
│   ├── setup-project.sh         # GCP project initialization
│   ├── setup-vpc.sh             # VPC and networking
│   ├── setup-secrets.sh         # Secret Manager configuration
│   ├── setup-audit-logging.sh   # HIPAA-compliant audit logging
│   ├── deploy-oauth2-proxy.sh   # Azure AD SSO proxy
│   └── verify-fhir-data.sh     # Epic FHIR connectivity test
└── audit/               # Compliance tooling
    ├── README.md                # Bias audit environment setup guide
    └── audit_bias.py            # Quarterly bias audit script
```

---

## Quick Start

### Local Development (no GCP needed)

```bash
# All servers run in DRY_RUN mode by default (synthetic data)
cd servers/mcp-fgbio
uv run python -m mcp_fgbio
```

### Deploy to GCP Cloud Run

```bash
# Deploy all servers to your GCP project
./infrastructure/deployment/deploy_to_gcp.sh YOUR_PROJECT_ID us-central1
```

### Hospital Production Setup

See [Hospital Deployment Guide](hospital-deployment/README.md) for the full 3-month deployment process including VPC, SSO, Epic FHIR integration, and HIPAA compliance.

---

## Environment Variables

See the root [`.env.example`](../.env.example) for all required configuration. Sensitive values (API keys, FHIR credentials, SSO secrets) are stored in GCP Secret Manager, not in environment files.
