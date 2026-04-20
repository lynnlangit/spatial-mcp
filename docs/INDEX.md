# Documentation Index

Central navigation for all documentation. Canonical references are in `reference/shared/`.

---

## Canonical References

| Doc | Covers |
|-----|--------|
| [Server Registry](reference/shared/server-registry.md) | 17 custom servers (99 tools) + 6 external |
| [Value Proposition](reference/shared/value-proposition.md) | Time savings, cost savings, ROI |
| [PatientOne Profile](reference/shared/patientone-profile.md) | Clinical profile, genomic findings |
| [Cost Analysis](reference/shared/cost-analysis.md) | Per-patient costs, infrastructure |
| [HIPAA Summary](reference/shared/hipaa-summary.md) | Compliance checklist |
| [DRY_RUN Mode](reference/shared/dry-run-mode.md) | Mock mode explanation |

---

## By Audience

| Audience | Start Here |
|----------|------------|
| **Funders / Grant Reviewers** | [for-funders/README.md](for-funders/README.md) |
| **Hospital IT / Admins** | [for-hospitals/README.md](for-hospitals/README.md) |
| **Developers** | [for-developers/README.md](for-developers/README.md) |
| **Researchers** | [for-researchers/README.md](for-researchers/README.md) |
| **Educators** | [for-educators/README.md](for-educators/README.md) |
| **Patients / Families** | [for-patients/README.md](for-patients/README.md) |

---

## Getting Started

- [Installation Guide](getting-started/installation.md) -- 5-minute quick start (Claude Code or Claude Desktop)
- [Gemini Setup](getting-started/gemini-setup.md) -- For teams with Google Gemini
- [Desktop Config Files](getting-started/desktop-configs/README.md) -- Pre-built JSON configs

---

## Architecture & Development

- [Architecture Overview](for-developers/ARCHITECTURE.md) -- System layers, data flow, integration patterns
- [Architecture Reference](reference/architecture/README.md) -- Supplementary arch docs
- [Add New Server](for-developers/ADD_NEW_MODALITY_SERVER.md) -- Step-by-step guide
- [Connect External MCP](for-researchers/CONNECT_EXTERNAL_MCP.md) -- PubMed, bioRxiv, ClinicalTrials.gov, Seqera, cBioPortal, HuggingFace

---

## Testing

- [PatientOne Scenario](reference/testing/patient-one/README.md) -- End-to-end test case
- [Test Prompts](reference/testing/patient-one/test-prompts/) -- DRY_RUN and synthetic data prompts
- [GCP Integration Testing](reference/testing/gcp-integration.md) -- Cloud Run verification

---

## Compliance & Ethics

- [HIPAA Compliance](for-hospitals/compliance/hipaa.md) -- De-identification, audit logging, encryption
- [Ethics & Bias](for-hospitals/ethics/ETHICS_AND_BIAS.md) -- Bias detection, fairness metrics, diverse datasets
- [Security Overview](for-hospitals/SECURITY_OVERVIEW.md) -- Security architecture

---

## Book

- [AI-Orchestrated Precision Oncology](book/) -- Quarto book (separate from platform docs)

---

## By Task

| I want to... | Go to |
|--------------|-------|
| Install the system | [Installation Guide](getting-started/installation.md) |
| Run my first analysis | [PatientOne test prompts](reference/testing/patient-one/test-prompts/) |
| Deploy to GCP | [GCP Integration](reference/testing/gcp-integration.md) |
| Ensure HIPAA compliance | [HIPAA docs](for-hospitals/compliance/hipaa.md) |
| Add a new server | [Add New Modality Server](for-developers/ADD_NEW_MODALITY_SERVER.md) |
| Understand costs | [Cost Analysis](reference/shared/cost-analysis.md) |
| Generate patient reports | [Automated Reports](for-developers/automation-guides/AUTOMATED_PATIENT_REPORTS.md) |
