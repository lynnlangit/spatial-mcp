# For Hospital IT & Administrators

> **This is a clinical decision support tool. AI assists -- clinicians decide.**
> Every AI-generated analysis requires clinician APPROVE/REVISE/REJECT before clinical use.

---

## Documents in This Section

| Doc | Purpose |
|-----|---------|
| [SECURITY_OVERVIEW.md](SECURITY_OVERVIEW.md) | Security architecture, VPC, encryption, access control |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Step-by-step deployment requirements (6-month timeline) |
| [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md) | System diagram, minimum viable deployment, data flow |
| [POC_RUNBOOK.md](POC_RUNBOOK.md) | 90-day proof-of-concept runbook |
| [RESOURCE_ESTIMATES.md](RESOURCE_ESTIMATES.md) | Compute, API cost, and personnel estimates |
| [EHR_INTEGRATION_GUIDE.md](EHR_INTEGRATION_GUIDE.md) | Mock-to-real Epic FHIR migration guide |
| [HIPAA_CHECKLIST.md](HIPAA_CHECKLIST.md) | HIPAA Security Rule technical safeguards checklist |
| [STAKEHOLDER_ONE_PAGER.md](STAKEHOLDER_ONE_PAGER.md) | One-page summary for hospital leadership |
| [USER_GUIDE.md](USER_GUIDE.md) | For clinicians and researchers using the platform |
| [compliance/hipaa.md](compliance/hipaa.md) | HIPAA compliance details and incident response |
| [ethics/ETHICS_AND_BIAS.md](ethics/ETHICS_AND_BIAS.md) | Bias detection and mitigation framework |

---

## Deployment Requirements

| Component | Requirement |
|-----------|-------------|
| **Cloud** | GCP organization (HIPAA-compliant) |
| **Compute** | Cloud Run (serverless, auto-scales) |
| **Auth** | Azure AD SSO |
| **EHR** | Epic FHIR R4 (local-only deployment for PHI) |
| **Monitoring** | Cloud Logging (10-year audit retention) |

**Personnel:** Hospital IT lead, security officer, Epic integration team, Azure AD admin, bioinformatics lead.

**Timelines:**
- **90-day POC** -- see [POC_RUNBOOK.md](POC_RUNBOOK.md)
- **Full production deployment** (6 months) -- see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Infrastructure setup scripts** (3 months) -- see [infrastructure/hospital-deployment](../../infrastructure/hospital-deployment/README.md)

---

## Cost & Value

See [Value Proposition](../reference/shared/value-proposition.md) for metrics and [Cost Analysis](../reference/shared/cost-analysis.md) for breakdowns.

---

**See also:** [Executive Summary](../for-funders/EXECUTIVE_SUMMARY.md) | [Server Registry](../reference/shared/server-registry.md) | [HIPAA Summary](../reference/shared/hipaa-summary.md)

---

**Last Updated:** 2026-02-19
