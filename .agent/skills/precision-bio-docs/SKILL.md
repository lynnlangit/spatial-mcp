---
name: precision-bio-docs
description: >
  Expert guide for project-specific documentation and clinical reporting.
  Maintains consistency across persona-based guides and automated reports.
---

# Precision Bio-Documentation

This skill ensures that all documentation is consistent, high-quality, and targeted to the right audience.

## 👤 Persona-Based Content

We write for different stakeholders. Always follow the established styles:
- **Funders**: ROI, cost logic, and grant-ready "Value Propositions."
- **Hospitals**: Security, HIPAA, deployment scripts, and runbooks.
- **Researchers**: Methodological details, GEARS architectures, and scRNA-seq parameters.
- **Patients**: Plain-language summaries and "What this means for you."

## 📚 Documentation Hierarchy

- **Main Hub**: `docs/INDEX.md`.
- **Cross-Reference**: Always link to the "Single Source of Truth" files in `docs/reference/shared/` (e.g., `patientone-profile.md`).
- **Automation**: Templates for automated reporting live in `docs/for-developers/automation-guides/`.

## 📧 Specialized Templates

- **Email Summaries**: Use the formatting in `docs/email-summary.md` for daily/weekly project status updates.
- **Patient Reports**: Ensure reports follow the structure in `mcp-patient-report` to maintain clinical standards.

## 🎨 Visualization Standards

- **Mermaid**: Use for all architecture flows. Ensure colors are readable in both light and dark modes.
- **Screenshots**: Store visual assets in `data/images/` and reference with absolute paths where possible.

## ✍️ Editorial Checklist
- [ ] Biological terms are accurately linked to citations.
- [ ] PHI/PII is strictly excluded from all public docs.
- [ ] New servers are added to the `Server Registry`.
- [ ] Architecture changes follow the **ADR Process** defined in **@universal-collaboration** (Sub-Skill 2).
- [ ] Mermaid diagrams remain under 100 nodes for readability.

---

**Use this skill when:**
- Drafting new user guides.
- Updating the System Architecture.
- Creating automated reporting templates for clinicians.
