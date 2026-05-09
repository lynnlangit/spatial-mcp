# Documentation Index

Central navigation for all documentation. Canonical references are in `reference/shared/`.

---

## Canonical References

| Doc | Covers |
|-----|--------|
| [Server Registry](reference/shared/server-registry.md) | 19 custom servers (104 tools) + 6 external |
| [Value Proposition](reference/shared/value-proposition.md) | Time savings, cost savings, ROI |
| [PatientOne Profile (PAT001)](reference/shared/patientone-profile.md) | HGSOC Stage IV — clinical profile, genomic findings, 3 investigational findings |
| [PAT002 Outcomes](reference/shared/patient-outcomes.md#pat002) | ER+ breast cancer — BRCA2 germline, PIK3CA H1047R, 3 investigational hypotheses |
| [PAT003 Outcomes](reference/shared/patient-outcomes.md#pat003) | Preventive CVD — cardiometabolic risk, Helix Tier 1 negative screen, 3 evidence gaps |
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

- [PAT001 Scenario (HGSOC)](reference/testing/patient-one/README.md) -- End-to-end HGSOC test case
- [PAT001 Test Prompts](reference/testing/patient-one/test-prompts/) -- DRY_RUN and synthetic data prompts
- [PAT002 Scenario (ER+ BC)](reference/testing/patient-two/README.md) -- End-to-end breast cancer test case
- [PAT002 Test Prompts](reference/testing/patient-two/test-prompts/) -- 10 DRY_RUN + 6 SYNTHETIC_DATA prompts
- [GCP Integration Testing](reference/testing/gcp-integration.md) -- Cloud Run verification

---

## Compliance & Ethics

- [HIPAA Compliance](for-hospitals/compliance/hipaa.md) -- De-identification, audit logging, encryption
- [Ethics & Bias](for-hospitals/ethics/ETHICS_AND_BIAS.md) -- Bias detection, fairness metrics, diverse datasets
- [Security Overview](for-hospitals/SECURITY_OVERVIEW.md) -- Security architecture

---

## By Task

| I want to... | Go to |
|--------------|-------|
| Install the system | [Installation Guide](getting-started/installation.md) |
| Run my first analysis | [PAT001 prompts](reference/testing/patient-one/test-prompts/) or [PAT002 prompts](reference/testing/patient-two/test-prompts/) |
| Deploy to GCP | [GCP Integration](reference/testing/gcp-integration.md) |
| Ensure HIPAA compliance | [HIPAA docs](for-hospitals/compliance/hipaa.md) |
| Add a new server | [Add New Modality Server](for-developers/ADD_NEW_MODALITY_SERVER.md) |
| Understand costs | [Cost Analysis](reference/shared/cost-analysis.md) |
| Generate patient reports | [Automated Reports](for-developers/automation-guides/AUTOMATED_PATIENT_REPORTS.md) |
