# HIPAA Compliance Summary (Canonical Reference)

## Compliance Status: COMPLIANT

The Precision Medicine MCP system meets all applicable HIPAA requirements for a research system handling de-identified patient data.

## Key Compliance Features

| Feature | Implementation | Status |
|---------|---------------|--------|
| **De-identification** | HIPAA Safe Harbor method (all 18 identifiers removed) — mcp-epic for FHIR data; mcp-deidentify for clinical documents, genomics files | ✅ |
| **Access Control** | Azure AD SSO with MFA, VPN required | ✅ |
| **Audit Logging** | 10-year retention in encrypted Cloud Logging | ✅ |
| **Encryption** | AES-256 at rest, TLS 1.3 in transit | ✅ |
| **BAA** | Business Associate Agreement with Google Cloud | ✅ |
| **Network Isolation** | VPC with private access, Cloud NAT | ✅ |

## De-identification (Safe Harbor Method)

All 18 HIPAA identifiers are removed before data enters the MCP system:

1. Names
2. Geographic subdivisions (zip → 3-digit only)
3. Dates (→ year only)
4. Phone numbers
5. Fax numbers
6. Email addresses
7. SSN
8. Medical record numbers (→ research ID)
9. Health plan numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers
13. Device identifiers
14. URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photos
18. Any other unique identifying number

## Data Retention

| Data Type | Retention | Storage |
|-----------|-----------|---------|
| Audit logs | **10 years** (HIPAA requirement) | Cloud Logging (immutable) |
| Clinical data | 7 years archive | Cloud Storage (AES-256) |
| Analysis results | 90 days nearline, then archive | Cloud Storage |
| PHI (pre-de-identification) | Not stored in MCP system | Epic FHIR only |

## PHI Handling

- PHI is de-identified **before** entering the MCP system
- The MCP system processes only de-identified data
- No PHI is stored on local devices (web-based system)
- Two de-identification paths:
  - **FHIR/EHR data:** mcp-epic handles de-identification at the source (local-only, never on Cloud Run)
  - **Clinical documents (JSON, DOCX, PDF, VCF, h5ad):** mcp-deidentify (Stage 0) applies Safe Harbor de-identification before any pipeline stage runs; anonymization keys are stored separately and never passed downstream

---

**Full HIPAA documentation:** [`docs/for-hospitals/compliance/hipaa.md`](../../for-hospitals/compliance/hipaa.md)
**Security overview:** [`docs/for-hospitals/SECURITY_OVERVIEW.md`](../../for-hospitals/SECURITY_OVERVIEW.md)
