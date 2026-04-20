# HIPAA Compliance Documentation

**Baseline:** See [HIPAA Summary](../../reference/shared/hipaa-summary.md) for platform-wide compliance overview.
This document covers hospital-specific procedures and validation checklists.

---

## Compliance Status

**COMPLIANT** -- The system meets all applicable HIPAA requirements for handling de-identified patient data.

| Feature | Implementation | HIPAA Section |
|---------|----------------|---------------|
| **De-identification** | Safe Harbor method, all 18 identifiers removed by mcp-epic | 164.514(b)(2) |
| **Access Control** | Azure AD SSO + MFA, RBAC, VPN required | 164.312(a)(1), (d) |
| **Audit Logging** | 10-year immutable retention (Cloud Logging + FHIR AuditEvent) | 164.312(b), 164.316(b)(2) |
| **Encryption** | AES-256 at rest, TLS 1.3 in transit | 164.312(a)(2)(iv), (e)(2) |
| **BAA** | Business Associate Agreement with Google Cloud | 164.502(e) |

---

## Administrative Safeguards (164.308)

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Security management | Incident response procedures, risk assessment | Done |
| Workforce security | Azure AD user management, training required | Done |
| Information access | RBAC: clinician, bioinformatician, admin roles | Done |
| Security awareness | Onboarding training + annual refresher | Done |
| Contingency plan | Daily backups, 30-day retention, DR tested quarterly | Done |

## Technical Safeguards (164.312)

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Access control | Azure AD SSO, unique user IDs, emergency access procedure | Done |
| Audit controls | Cloud Logging (all API calls), FHIR AuditEvent (data access) | Done |
| Integrity | Input validation on all MCP tools, checksum verification | Done |
| Authentication | Azure AD + MFA, 30-min idle timeout | Done |
| Transmission security | TLS 1.3 for all traffic, VPC isolation | Done |

## Physical Safeguards (164.310)

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Facility access | GCP data centers (SOC 2 Type II, ISO 27001 certified) | Done |
| Workstation use | Hospital-managed workstations with endpoint protection | Done |
| Device controls | No local PHI storage; all data in encrypted GCP storage | Done |

---

## PHI Data Flow

```
Epic FHIR (hospital network)
    |
    v
mcp-epic (local-only, never on Cloud Run)
    |  -- removes all 18 HIPAA identifiers --
    v
De-identified data --> Cloud Run MCP servers
    |
    v
Analysis results (no PHI) --> Clinician review
```

**Key constraint:** mcp-epic runs on the hospital network only. PHI never leaves the hospital VPC. All other MCP servers receive only de-identified data.

---

## Validation Checklist (Pre-Production)

- [ ] All 18 HIPAA identifiers confirmed removed from test data
- [ ] Azure AD SSO configured with MFA enforcement
- [ ] Cloud Logging retention set to 10 years
- [ ] VPC firewall rules verified (no public IPs on MCP servers)
- [ ] BAA executed with Google Cloud
- [ ] Disaster recovery test completed (restore from backup)
- [ ] Penetration test completed by external security firm
- [ ] Staff training completed for all pilot users

---

## Incident Response

| Step | Action | Timeline |
|------|--------|----------|
| Detection | Automated alert or manual report | Immediate |
| Triage | Assess severity, assign owner | <1 hour (critical) |
| Containment | Isolate affected systems, stop data exposure | <4 hours |
| Notification | Inform affected individuals + HHS | 60 days (HIPAA 164.408) |
| Post-mortem | Document root cause, update procedures | 30 days |

---

**See also:** [HIPAA Summary](../../reference/shared/hipaa-summary.md) | [Security Overview](../SECURITY_OVERVIEW.md) | [Ethics & Bias](../ethics/ETHICS_AND_BIAS.md)
