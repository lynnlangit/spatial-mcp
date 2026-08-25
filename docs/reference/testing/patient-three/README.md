# PatientThree: Preventive Cardiovascular Health Workflow

Preventive cardiovascular risk assessment for a 67F post-menopausal patient using the mcp-cardiometabolic server.

## Overview

> **Quick references:** [PAT003 Data](../../../../data/patient-data/PAT003-CVD-2026/) | [Canonical Values](../../../../tests/fixtures/pat003_canonical.py) | [Server Registry](../../shared/server-registry.md)

PatientThree validates the platform's preventive health capabilities beyond oncology. The same architecture used for PAT001 (HGSOC) and PAT002 (ER+ breast cancer) extends to cardiovascular risk assessment with **zero architectural changes**.

### Clinical Scenario

**Patient:** Synthetic, 67F post-menopausal
**Key profile:** Controlled hypertension (lisinopril 5 mg), BMI 26.4, bilateral family history of CVD (father MI at 61, mother stroke at 69)
**Genetic screen:** Tier 1 population screen NEGATIVE (FH, HBOC, Lynch all ruled out)
**Risk category:** Intermediate (Reynolds 14.3%, Framingham 12.0%, ASCVD 10.3%)

### Key Results

| Metric | Value | Server |
|--------|-------|--------|
| Reynolds Risk Score | 14.3% (intermediate) | mcp-cardiometabolic |
| Framingham 10-year risk | 12.0% | mcp-cardiometabolic |
| ASCVD 10-year risk | 10.3% | mcp-cardiometabolic |
| hsCRP | 1.8 mg/L (moderate) | mcp-cardiometabolic |
| LDL | 118 mg/dL | mcp-cardiometabolic |

### 3 Evidence Gaps (missed by standard lipid panel + Tier 1 genetic screen)

| # | Gap | Why It Matters |
|---|-----|----------------|
| 1 | Serum Lp(a) not measured | Independent CVD risk factor; genetically fixed; measure once |
| 2 | APOE genotype unknown | CVD + cognitive risk at age 67; not on population screens |
| 3 | CAC score not obtained | Best reclassification tool for intermediate-risk patients |

---

## Research Use Only Disclaimer

**CRITICAL:** This workflow is for RESEARCH and EDUCATIONAL purposes only.

- **NOT clinically validated** — Do not use for actual patient care decisions
- **NOT FDA-approved** — Not a medical device or diagnostic tool
- **FOR demonstration** — Shows preventive health extension of the precision medicine platform

**All data is synthetic.** Any resemblance to actual patients is coincidental.

---

## Test Prompts

### [DRY_RUN](test-prompts/DRY_RUN/) — Hardcoded Mock Data (default)

| # | Test | Servers | Focus |
|---|------|---------|-------|
| 1 | [CVD Risk Assessment](test-prompts/DRY_RUN/test-1-cvd-risk-assessment.md) | cardiometabolic, mockepic | Full preventive workflow: biomarkers, risk scores, evidence gaps, lifestyle evidence |

### SYNTHETIC_DATA — TBD

Scenario-level SYNTHETIC_DATA test prompts for file-based parsing are planned but not yet created.

## MCP Tools Used

The mcp-cardiometabolic server provides 14 tools:

| Tool | Purpose |
|------|---------|
| `assess_biomarker_panel` | Evaluate lipid panel, glucose, hsCRP, BP |
| `calculate_cvd_risk_scores` | Framingham, ASCVD, and Reynolds risk calculations |
| `assess_lpa_status` | Lp(a) risk assessment |
| `generate_preventive_report` | Integrated preventive health report |
| `get_lifestyle_evidence` | Evidence-based lifestyle intervention recommendations |

## What Makes PatientThree Unique

1. **Beyond oncology** — Proves the platform handles preventive health, not just cancer
2. **Evidence gap detection** — Surfaces what standard screening *misses*, not just what it finds
3. **Zero architecture changes** — Same MCP infrastructure, different clinical domain
4. **Underrepresented population** — 65+ post-menopausal women are significantly underrepresented in CVD research

---

**Status:** 100% Synthetic — Research/Demo Only
