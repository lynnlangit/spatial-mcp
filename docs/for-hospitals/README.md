# For Hospital IT & Administrators

> **This is a clinical decision support tool. AI assists -- clinicians decide.**
> Every AI-generated analysis requires clinician APPROVE/REVISE/REJECT before clinical use.

---

## Documents in This Section

| Doc | Purpose |
|-----|---------|
| [SECURITY_OVERVIEW.md](SECURITY_OVERVIEW.md) | Security architecture, VPC, encryption, access control |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Step-by-step deployment requirements and 6-month timeline |
| [USER_GUIDE.md](USER_GUIDE.md) | For clinicians and researchers using the platform |
| [compliance/hipaa.md](compliance/hipaa.md) | HIPAA compliance details |
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

**Timeline:** 6 months -- see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md).

---

## Cost & Value

See [Value Proposition](../reference/shared/value-proposition.md) for metrics and [Cost Analysis](../reference/shared/cost-analysis.md) for breakdowns.

---

**See also:** [Executive Summary](../for-funders/EXECUTIVE_SUMMARY.md) | [Server Registry](../reference/shared/server-registry.md) | [HIPAA Summary](../reference/shared/hipaa-summary.md)
