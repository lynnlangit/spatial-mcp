# HIPAA Security Rule Technical Safeguards -- Checklist

This checklist covers HIPAA Security Rule 164.312 technical safeguards as applied
to the HGSOC MCP platform. For a full compliance audit, engage a qualified HIPAA
Security Officer.

Controls marked IMPLEMENTED are documented in `docs/for-hospitals/compliance/hipaa.md`.

## Safeguard status table

| Requirement | Status | Implementation | Notes |
|-------------|--------|----------------|-------|
| Unique user identification | PARTIAL | No built-in auth in MCP servers | Add API key per user at gateway layer |
| Emergency access procedure | NOT_IMPLEMENTED | -- | Define break-glass procedure for oncology emergencies |
| Automatic logoff | NOT_IMPLEMENTED | -- | Claude Desktop sessions do not auto-expire |
| Encryption and decryption | IMPLEMENTED | AES-256 at rest, TLS 1.3 in transit | Documented in compliance/hipaa.md |
| Audit controls (PHI access log) | IMPLEMENTED | Cloud Logging + FHIR AuditEvent, 10-year retention | Documented in compliance/hipaa.md |
| Integrity controls | PARTIAL | Input validation on MCP tools; hash not verified on data transfer | Add checksum verification at de-identification layer |
| Authentication | PARTIAL | Azure AD + MFA documented but not integrated into MCP servers | Recommend MFA enforcement for clinical users |
| Transmission security (TLS) | IMPLEMENTED | TLS 1.3 for all traffic, VPC isolation | Documented in compliance/hipaa.md |
| De-identification | IMPLEMENTED | Safe Harbor method, all 18 identifiers removed by mcp-epic | Documented in compliance/hipaa.md |

## Gap analysis

| Gap | Severity | Suggested fix | Effort |
|-----|----------|---------------|--------|
| No emergency access procedure defined | HIGH | Document break-glass process; store credentials in hospital password vault | S |
| No automatic logoff | HIGH | Configure Claude Desktop session timeout; add idle check at API gateway | M |
| No per-user authentication in MCP servers | HIGH | Add per-user API keys or OAuth2 at the MCP gateway layer | M |
| Integrity checks missing on data transfer | MEDIUM | Implement SHA-256 checksum at de-identification layer | M |
| Azure AD + MFA not wired into MCP transport | MEDIUM | Integrate SMART on FHIR OAuth2 flow into MCP gateway | L |
