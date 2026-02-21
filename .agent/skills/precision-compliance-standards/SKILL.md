---
name: precision-compliance-standards
description: >
  Dedicated guide for enforcing clinical compliance (HIPAA), scientific accuracy, 
  and bioinformatics standards in the Precision Medicine MCP project.
---

# Precision Clinical & Scientific Standards

This skill ensures that all contributions meet the high bar required for clinical systems and bioinformatics research.

## 🏥 Clinical & Security Standards
To ensure clinical data safety and audit readiness, always follow the best practices defined in **@clinical-compliance-doc**. This includes HIPAA safeguards, PII protection, and audit logging patterns.

## 🧬 Scientific Accuracy
**When to trigger**: When editing data loaders, models (GEARS), or documentation.
- **Nomenclature**: Gene names must follow HUGO standards (e.g., Use `GZMB`, not `gzm-b`).
- **Context**: Tissue and disease labels must be consistent (e.g., `HGSOC` for High-grade serous ovarian cancer).
- **Validation**: Ensure that `AnnData` objects adhere to the project's 7,000 HVG standard where GEARS is used.

## 🧪 Bioinformatics Validation
- **PatientOne Alignment**: Validation logic should specifically handle the `PatientOne` profile correctly.
- **DRY_RUN Logic**: Ensure that `DRY_RUN` modes realistically simulate the scientific results, not just the connection status.

## 📝 PR & Documentation Requirements
- **Compliance Notes**: Every PR must have a section stating: "Compliance / Risk Notes: [Privacy/Security Impact]".
- **Scientific Impact**: Describe any changes to bioinformatics algorithms or data interpretation.

---

**Use this skill when:**
- Auditing code for clinical security.
- Verifying the scientific content of reports or documentation.
- Ensuring a PR meets project-specific compliance requirements.
