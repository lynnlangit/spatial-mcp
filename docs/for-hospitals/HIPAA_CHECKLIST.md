# HIPAA Security Rule Technical Safeguards -- Checklist

This checklist covers HIPAA Security Rule 164.312 technical safeguards as applied
to the Precision Medicine MCP platform. For a full compliance audit, engage a qualified HIPAA
Security Officer.

Controls marked IMPLEMENTED are documented in `docs/for-hospitals/compliance/hipaa.md`.

## Safeguard status table

| Requirement | Status | Implementation | Notes |
|-------------|--------|----------------|-------|
| Unique user identification | IMPLEMENTED | Azure AD SSO with unique user IDs | Per-user identity via Azure AD groups |
| Emergency access procedure | NOT_IMPLEMENTED | -- | Define break-glass procedure for oncology emergencies |
| Automatic logoff | IMPLEMENTED | 30-min idle timeout, 1-day session expiry | Configured via OAuth2 Proxy |
| Encryption and decryption | IMPLEMENTED | AES-256 at rest, TLS 1.3 in transit | Documented in compliance/hipaa.md |
| Audit controls (PHI access log) | IMPLEMENTED | Cloud Logging + FHIR AuditEvent, 10-year retention | Documented in compliance/hipaa.md |
| Integrity controls | IMPLEMENTED | Input validation on MCP tools, checksum verification at de-identification layer | Documented in compliance/hipaa.md |
| Authentication | IMPLEMENTED | Azure AD SSO + MFA enforced for all clinical users | Documented in compliance/hipaa.md |
| Transmission security (TLS) | IMPLEMENTED | TLS 1.3 for all traffic, VPC isolation | Documented in compliance/hipaa.md |
| De-identification | IMPLEMENTED | Safe Harbor method, all 18 identifiers removed — mcp-epic (FHIR/EHR data) and mcp-deidentify Stage 0 (JSON, DOCX, PDF, VCF, h5ad) | Documented in compliance/hipaa.md |

## Gap analysis

| Gap | Severity | Suggested fix | Effort |
|-----|----------|---------------|--------|
| No emergency access procedure defined | HIGH | Document break-glass process; store credentials in hospital password vault | S |

---

**Last Updated:** 2026-02-19
