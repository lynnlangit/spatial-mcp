# Hospital Deployment Infrastructure

**Precision Medicine MCP Servers - HIPAA-Compliant GCP Deployment**

This directory contains infrastructure scripts for deploying the Precision Medicine MCP servers to a research hospital's existing HIPAA-compliant GCP organization.

## Overview

These scripts set up:
- ✅ GCP project in hospital's existing organization
- ✅ HIPAA-compliant VPC networking
- ✅ Secret Manager for credentials (Epic FHIR, Azure AD, Anthropic API)
- ✅ Audit logging with 10-year retention
- ✅ OAuth2 Proxy for Azure AD SSO authentication
- ✅ Service accounts with least-privilege access
- ✅ Cost controls and monitoring

## Deployment Phases

The deployment follows a 3-month phased approach optimized for research hospital adoption:

### Phase 1: MVP Foundation (Month 1)
- **Week 1**: Infrastructure setup (GCP project, VPC, secrets, audit logging)
- **Week 2**: Azure AD SSO integration (OAuth2 Proxy, Streamlit, JupyterHub)
- **Week 3**: Core MCP server deployment (fgbio, multiomics, spatialtools)
- **Week 4**: Epic FHIR integration (research endpoint with de-identification)

### Phase 2: Pilot Testing (Month 2)
- **Week 5**: Deploy additional servers as needed for pilot workflows (mock/partial for demo)
- **Week 6**: Initial testing with 10-20 patients
- **Week 7**: User training (2 clinicians, 3 bioinformaticians)
- **Week 8**: Iteration and scale to 100 patients

### Phase 3: Production (Month 3)
- **Week 9**: Monitoring and alerting setup
- **Week 10**: Documentation and compliance validation
- **Week 11**: Knowledge transfer to hospital IT and research team
- **Week 12**: Final validation and go-live

**Full deployment plan**: See [`/docs/for-hospitals/`](../../docs/for-hospitals/)

## Scripts

### 1. GCP Project Setup
```bash
./setup-project.sh
```

**What it does:**
- Creates GCP project in hospital's existing GCP Organization
- Links billing to Ovarian Cancer PI's grant account
- Enables required APIs:
  - Cloud Run (serverless MCP servers)
  - Compute Engine (VPC networking)
  - VPC Access (Serverless VPC Connector)
  - Secret Manager (credentials storage)
  - Cloud Logging (10-year audit logs)
  - Cloud Monitoring (dashboards and alerts)
- Sets up budget alerts at $1,000/month threshold

**Prerequisites:**
- Hospital GCP Organization ID
- Billing account ID (from PI's grant)
- Organization admin permissions
- Billing admin permissions

**Configuration:**
Edit these variables in the script:
```bash
ORG_ID="123456789012"              # Hospital's GCP org ID
BILLING_ACCOUNT_ID="00B597-..."    # PI's billing account
PROJECT_ID="precision-medicine-poc"
REGION="us-central1"
```

### 2. VPC Networking Setup
```bash
./setup-vpc.sh
```

**What it does:**
- Creates subnet for MCP servers (10.10.0.0/24)
- Creates Serverless VPC Connector for Cloud Run
- Enables Private Google Access (secure GCS access)
- Sets up firewall rules:
  - Allow health checks from Google
  - Allow internal traffic between servers
  - Deny all external ingress (requires VPN)

**Prerequisites:**
- Existing hospital VPC network (or creates new one)
- Compute Engine API enabled
- VPC Access API enabled

**Configuration:**
```bash
PROJECT_ID="precision-medicine-poc"
REGION="us-central1"
VPC_NAME="hospital-vpc"  # Use existing hospital VPC
SUBNET_CIDR="10.10.0.0/24"
```

### 3. Secret Manager Setup
```bash
./setup-secrets.sh
```

**What it does:**
- Creates 7 secrets for production deployment:
  - `anthropic-api-key` - Claude API access
  - `epic-fhir-endpoint` - Epic FHIR base URL
  - `epic-client-id` - Epic OAuth client ID
  - `epic-client-secret` - Epic OAuth client secret
  - `azure-ad-client-id` - Azure AD app client ID
  - `azure-ad-client-secret` - Azure AD app secret
  - `azure-ad-tenant-id` - Hospital's Azure AD tenant ID
- Enables automatic encryption at rest
- Sets up IAM bindings for service accounts

**Prerequisites:**
- Secret Manager API enabled
- Epic FHIR credentials from hospital IT
- Azure AD app registered (see [Azure AD Setup](#azure-ad-setup))
- Anthropic API key

**Usage:**
```bash
# Run the script to create empty secrets
./setup-secrets.sh

# Populate secrets interactively (prompts for values)
./setup-secrets.sh --interactive

# Or manually populate each secret:
echo -n "sk-ant-..." | gcloud secrets versions add anthropic-api-key --data-file=-
echo -n "https://hospital.epic.com/api/FHIR/R4/" | gcloud secrets versions add epic-fhir-endpoint --data-file=-
# ... etc
```

**Verification:**
```bash
# List all secrets
gcloud secrets list --project=$PROJECT_ID

# Verify IAM bindings
gcloud secrets get-iam-policy anthropic-api-key
```

### 4. Audit Logging Setup
```bash
./setup-audit-logging.sh
```

**What it does:**
- Creates log bucket with **10-year retention** (HIPAA requirement)
- Sets up log sinks for:
  - All Cloud Run requests (user queries)
  - Authentication events (login/logout)
  - Epic FHIR API calls
  - De-identification operations
- Creates custom log-based metrics:
  - De-identification success rate
  - Epic FHIR failure rate
  - User access events
- Configures log exports for compliance reporting

**Prerequisites:**
- Cloud Logging API enabled
- Logging Admin permissions

**Log Retention:**
- **10 years** (3,650 days) for HIPAA compliance
- Automatically encrypted at rest
- Immutable (cannot be deleted before retention period)

**Accessing Logs:**
```bash
# View recent user queries
gcloud logging read "jsonPayload.event=\"mcp_query\"" \
  --limit=50 \
  --format=json

# View Epic FHIR calls
gcloud logging read "jsonPayload.event=\"epic_fhir_call\"" \
  --limit=50

# Export logs for compliance report
gcloud logging read "jsonPayload.event=\"mcp_query\"" \
  --format=csv > compliance_report.csv
```

### 5. OAuth2 Proxy Deployment
```bash
./deploy-oauth2-proxy.sh
```

**What it does:**
- Builds OAuth2 Proxy container with Azure AD configuration
- Deploys to Cloud Run as authentication layer
- Configures to sit in front of Streamlit and JupyterHub
- Generates secure cookie secret (32 bytes)
- Sets up redirect URLs for Azure AD callbacks

**Prerequisites:**
- Azure AD app registered (see [Azure AD Setup](#azure-ad-setup))
- Secrets populated (azure-ad-client-id, azure-ad-client-secret, azure-ad-tenant-id)
- Docker installed locally

**OAuth2 Proxy Configuration:**
- Provider: Azure AD
- Scopes: `openid profile email`
- Cookie settings:
  - Secure: true (HTTPS only)
  - HttpOnly: true (no JavaScript access)
  - SameSite: lax (CSRF protection)
  - Max age: 1 day (sessions expire daily)
- Email domains: `@{hospital.org}` (only hospital users)

**Testing:**
```bash
# Get OAuth2 Proxy URL
PROXY_URL=$(gcloud run services describe oauth2-proxy \
  --region=us-central1 \
  --format='value(status.url)')

# Test authentication flow
curl -I $PROXY_URL
# Should return 302 redirect to Azure AD login
```

## Azure AD Setup

Before running deployment scripts, register an Azure AD application:

### 1. Register App in Azure Portal

1. Navigate to **Azure Active Directory** > **App registrations**
2. Click **New registration**
3. Name: "Precision Medicine MCP"
4. Supported account types: **Single tenant** (hospital only)
5. Redirect URIs:
   - Type: Web
   - URIs (update after deployment):
     - `https://{oauth2-proxy-url}/oauth2/callback`
     - `https://{streamlit-url}/auth/callback`
     - `https://{jupyter-url}/hub/oauth_callback`

### 2. Configure API Permissions

1. Click **API permissions** > **Add a permission**
2. Select **Microsoft Graph**
3. Add **Delegated permissions**:
   - `User.Read` (read user profile)
   - `User.ReadBasic.All` (read basic user info)
4. Add **Application permissions**:
   - `Directory.Read.All` (read directory data)
5. Click **Grant admin consent for {hospital}**

### 3. Create Client Secret

1. Click **Certificates & secrets** > **New client secret**
2. Description: "MCP OAuth2 Proxy Secret"
3. Expires: **24 months** (maximum allowed)
4. Click **Add**
5. **Copy the secret value immediately** (only shown once)
6. Store in Secret Manager:
   ```bash
   echo -n "{secret-value}" | gcloud secrets versions add azure-ad-client-secret --data-file=-
   ```

### 4. Create User Group

1. Navigate to **Azure Active Directory** > **Groups**
2. Click **New group**
3. Group type: **Security**
4. Group name: `precision-medicine-users`
5. Membership type: **Assigned**
6. Add members:
   - 2 clinicians
   - 3 bioinformaticians
   - Hospital IT administrators

**Note:** Only users in this group can access the MCP system.

### 5. Record Configuration

Save these values for deployment:

```bash
# Azure AD Configuration
AZURE_TENANT_ID="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
AZURE_CLIENT_ID="yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"
AZURE_CLIENT_SECRET="zzzzzz~xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
HOSPITAL_DOMAIN="hospital.org"
```

Store in Secret Manager:
```bash
echo -n "$AZURE_TENANT_ID" | gcloud secrets versions add azure-ad-tenant-id --data-file=-
echo -n "$AZURE_CLIENT_ID" | gcloud secrets versions add azure-ad-client-id --data-file=-
echo -n "$AZURE_CLIENT_SECRET" | gcloud secrets versions add azure-ad-client-secret --data-file=-
```

## Epic FHIR Setup

### Research FHIR Endpoint

Work with hospital IT to obtain:

1. **FHIR Base URL** (research endpoint, NOT production)
   - Example: `https://hospital-research.epic.com/api/FHIR/R4/`
   - Must be **research FHIR**, not production (patient safety)

2. **OAuth 2.0 Client Credentials**
   - Client ID (for backend server access)
   - Client secret
   - Token endpoint URL (usually `/oauth2/token`)

3. **Authorized Scopes**
   - `patient/*.read` (read-only patient data)
   - `Observation.read` (lab results, vitals)
   - `Condition.read` (diagnoses)
   - `MedicationStatement.read` (medications)

4. **Patient ID Format**
   - Epic uses research patient IDs (e.g., `RESEARCH-PAT001`)
   - NOT production MRNs (patient safety and privacy)

### Testing Epic Connection

```bash
# Set Epic credentials
export EPIC_FHIR_ENDPOINT="https://hospital-research.epic.com/api/FHIR/R4/"
export EPIC_CLIENT_ID="your-client-id"
export EPIC_CLIENT_SECRET="your-client-secret"

# Test OAuth token
curl -X POST "${EPIC_FHIR_ENDPOINT}/oauth2/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=${EPIC_CLIENT_ID}" \
  -d "client_secret=${EPIC_CLIENT_SECRET}" \
  -d "scope=patient/*.read"

# Test FHIR endpoint (with token)
TOKEN="your-access-token"
curl -H "Authorization: Bearer $TOKEN" \
  "${EPIC_FHIR_ENDPOINT}/metadata"
```

### Store Epic Credentials

```bash
echo -n "$EPIC_FHIR_ENDPOINT" | gcloud secrets versions add epic-fhir-endpoint --data-file=-
echo -n "$EPIC_CLIENT_ID" | gcloud secrets versions add epic-client-id --data-file=-
echo -n "$EPIC_CLIENT_SECRET" | gcloud secrets versions add epic-client-secret --data-file=-
```

## Full Deployment Workflow

Run scripts in order:

```bash
# 1. Set up GCP project (Week 1)
cd /path/to/spatial-mcp/infrastructure/hospital-deployment
./setup-project.sh

# 2. Set up VPC networking (Week 1)
./setup-vpc.sh

# 3. Set up Secret Manager (Week 1)
./setup-secrets.sh --interactive

# 4. Set up audit logging (Week 1)
./setup-audit-logging.sh

# 5. Deploy OAuth2 Proxy (Week 2)
./deploy-oauth2-proxy.sh

# 6. Deploy MCP servers (Week 3-5)
# See: ../deployment/deploy_to_gcp.sh
```

## Environment Variables

Each script uses these environment variables (set in script or export):

| Variable | Description | Example |
|----------|-------------|---------|
| `PROJECT_ID` | GCP project ID | `precision-medicine-poc` |
| `ORG_ID` | Hospital's GCP organization ID | `123456789012` |
| `BILLING_ACCOUNT_ID` | Grant billing account | `00B597-858846-408197` |
| `REGION` | GCP region | `us-central1` |
| `VPC_NAME` | Hospital VPC network | `hospital-vpc` |
| `AZURE_TENANT_ID` | Hospital Azure AD tenant | `{guid}` |
| `AZURE_CLIENT_ID` | Azure AD app client ID | `{guid}` |
| `AZURE_CLIENT_SECRET` | Azure AD app secret | `{secret}` |
| `EPIC_FHIR_ENDPOINT` | Epic FHIR base URL | `https://...` |
| `EPIC_CLIENT_ID` | Epic OAuth client ID | `{client-id}` |
| `EPIC_CLIENT_SECRET` | Epic OAuth secret | `{secret}` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-...` |

## Security Considerations

### Network Security
- ✅ All servers require authentication (no `--allow-unauthenticated`)
- ✅ VPC egress routes through hospital network
- ✅ Firewall rules deny all external ingress
- ✅ Access via hospital VPN only
- ✅ URL whitelisting configured

### Data Security
- ✅ All patient data automatically de-identified (HIPAA Safe Harbor)
- ✅ Secrets encrypted at rest in Secret Manager
- ✅ Service accounts use least-privilege IAM
- ✅ Audit logs immutable with 10-year retention
- ✅ TLS 1.2+ enforced for all connections

### Authentication
- ✅ Azure AD SSO (hospital Active Directory)
- ✅ OAuth 2.0 with Azure AD groups
- ✅ Session expiry after 1 day
- ✅ CSRF protection (SameSite cookies)
- ✅ All actions logged with user identity

### Compliance
- ✅ HIPAA Business Associate Agreement with Google Cloud
- ✅ Audit logging with 10-year retention
- ✅ De-identification validated by privacy officer
- ✅ IRB approval for research patient data
- ✅ VPN access with URL whitelisting

## Cost Management

### Budget
- **Monthly budget**: $1,000
- **Budget alerts**:
  - 50% ($500) - Warning email
  - 75% ($750) - Alert email
  - 90% ($900) - Critical alert
  - 100% ($1,000) - Budget exceeded

### Cost Breakdown (Estimated)
- Cloud Run: $400/month (all servers, moderate usage)
- VPC/Networking: $50/month
- Storage: $100/month (100 patients)
- Anthropic API: $500/month (5 users, optimized usage)
- Monitoring/Logging: $50/month

**Total**: ~$1,100/month during pilot (budget alerts at $1,000; expect to optimize down after pilot)

### Cost Optimization
- Set `min-instances=0` for mock servers (saves ~$100/month)
- Use Haiku model for simple queries (saves ~$100/month)
- Cache MCP responses (saves ~$100/month)
- Reduce to 3 core servers if needed (saves ~$200/month)

## Monitoring

### Dashboards
- Server health (request rate, error rate, latency)
- User activity (queries per server, token usage)
- Epic FHIR (connection status, API calls, errors)
- De-identification (success rate, failures)
- Cost tracking (daily spend, projected monthly cost)

### Alerts
- **Critical (P0)**: Server down, Epic connection failure
- **High (P1)**: High error rate (>5%), de-identification failures
- **Medium (P2)**: Budget threshold exceeded, slow queries
- **Low (P3)**: Unusual usage patterns, minor errors

### Accessing Monitoring
```bash
# View monitoring dashboard
gcloud monitoring dashboards list
gcloud monitoring dashboards describe {dashboard-id}

# View active alerts
gcloud alpha monitoring policies list

# Test alert (trigger intentionally)
gcloud run services update mcp-fgbio --max-instances=0  # Triggers "server down"
gcloud run services update mcp-fgbio --max-instances=5  # Restore
```

## Bias Audit Environment Setup

See **[Bias Audit Setup Guide](../audit/README.md)** for the full environment setup, including workstation provisioning, service accounts, Cloud Storage, scheduling, and troubleshooting.

Related: [Ethics & Bias Framework](../../docs/for-hospitals/ethics/ETHICS_AND_BIAS.md)

---

## Troubleshooting

### Common Issues

**1. OAuth2 Proxy login fails**
- Check Azure AD app redirect URIs match deployed URLs
- Verify `azure-ad-client-secret` is correct and not expired
- Check user is in `precision-medicine-users` Azure AD group

**Solution**: See [Security Overview](../../docs/for-hospitals/SECURITY_OVERVIEW.md)

**2. Epic FHIR connection fails**
- Verify research FHIR endpoint URL is correct
- Check OAuth client credentials are valid
- Ensure service account has Secret Manager access

**Solution**: See [Security Overview](../../docs/for-hospitals/SECURITY_OVERVIEW.md)

**3. Server deployment fails**
- Check VPC connector exists and is ready
- Verify service account has necessary IAM roles
- Ensure secrets are populated

**Solution**: See [Security Overview](../../docs/for-hospitals/SECURITY_OVERVIEW.md)

**4. Audit logs missing**
- Verify log sink is created
- Check service account has Logging Writer role
- Confirm application is using structured logging

**Solution**: Check [HIPAA Compliance](../../docs/for-hospitals/compliance/hipaa.md)

## Support

### Hospital IT Support
- **Tier 1**: Login issues, VPN access, basic troubleshooting
- **Contact**: Hospital IT help desk

### Development Team Support
- **Tier 2**: Server errors, Epic integration, complex issues
- **Contact**: See [Hospital Deployment Guide](../../docs/for-hospitals/README.md)

### Vendor Support
- **Tier 3**: Anthropic API, GCP platform issues
- **Contact**: Anthropic support, Google Cloud support

## Documentation

### For Users
- **[User Guide](../../docs/for-hospitals/USER_GUIDE.md)**: How to use Streamlit and Jupyter
- **[FAQ](../../docs/for-hospitals/USER_GUIDE.md#faq)**: Common questions and answers

### For Administrators
- **[Hospital Deployment Guide](../../docs/for-hospitals/README.md)**: System architecture and operations
- **[HIPAA Compliance](../../docs/for-hospitals/compliance/hipaa.md)**: Compliance validation
- **[Security Overview](../../docs/for-hospitals/SECURITY_OVERVIEW.md)**: Security controls and troubleshooting

## Contributing

This deployment is specific to the research hospital's GCP organization. For questions or issues:

1. Check documentation in `/docs/for-hospitals/`
2. Review runbooks for common issues
3. Contact development team
4. Submit issue to GitHub (redact any PHI/credentials)

## License

See main repository LICENSE file.

---

**Version**: 1.0.0
**Contact**: See [Hospital Deployment Guide](../../docs/for-hospitals/README.md)
