---
name: clinical-compliance-doc
description: >
  Ensures all development meets clinical compliance and security standards.
  Focuses on HIPAA-friendly logging, audit trails, and risk assessment.
---

# Clinical Compliance & Security

This skill provides guidelines for maintaining the documentation and architectural safeguards required for clinical environments.

## 🏥 Compliance Standards

- **HIPAA**: Ensure no PHI (Protected Health Information) is logged or stored.
- **Audit Trails**: Every write operation to the database or GCS must be logged with a timestamp and actor ID.
- **Data Locality**: Verify that infrastructure deployment scripts (Terraform/K8s) target the correct hospital-specific regions.

## 📝 Required Documentation Patterns

Every new feature or server must include a "Compliance Context" in its `README.md`:

1.  **Data Sensitivity**: What kind of data is being handled?
2.  **Security Justification**: Why is this tool safe to run in a hospital environment?
3.  **Audit Impact**: Does this feature change how data access is recorded?

## 🛠️ Infrastructure Hooks

Use the tools in `infrastructure/` to enforce compliance:
- **Audit Logs**: Reference `infrastructure/audit/` for current logging schemas.
- **Docker Security**: Ensure multi-stage builds remove all development secrets.
- **Hospital Deployment**: Follow the patterns in `infrastructure/hospital-deployment/` when drafting deployment plans.

## 🔍 Code Review Checklist

When reviewing PRs for compliance:
- [ ] Check for hardcoded credentials or API keys.
- [ ] Verify `allow_list` vs `block_list` configs for data tools.
- [ ] Ensure error messages do not leak internal system paths or data snippets.

---

**Use this skill when:**
- Drafting implementation plans for clinical features.
- Reviewing infrastructure changes.
- Writing security reports for funders or hospital partners.
