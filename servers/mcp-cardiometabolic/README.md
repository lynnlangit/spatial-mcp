# mcp-cardiometabolic

Cardiovascular risk scoring, biomarker interpretation, and preventive health monitoring. Server #19 in the Precision Medicine MCP Platform.

## Tools (14)

| Tool | Description |
|------|-------------|
| `assess_biomarker_panel` | Interpret cardiovascular biomarkers against clinical reference ranges (LDL, HDL, hsCRP, glucose, HbA1c, BP, triglycerides, ApoB, Non-HDL) with bidirectional flagging |
| `calculate_cvd_risk_scores` | Compute Reynolds, Framingham, and ASCVD Pooled Cohort 10-year risk scores |
| `assess_lpa_status` | Interpret Lp(a) status or recommend testing if not yet measured |
| `generate_preventive_report` | Structured preventive health summary with priority actions, monitoring schedule, inline confidence markers, and evidence strength summary table |
| `get_lifestyle_evidence` | Evidence-based lifestyle interventions with landmark trial citations |
| `interpret_lipid_pattern` | Classify lipid phenotype (mixed dyslipidemia, isolated hypercholesterolemia, etc.), Friedewald validity, ApoB/LDL concordance |
| `calculate_fh_clinical_score` | Dutch Lipid Clinic Network (DLCN) scoring for familial hypercholesterolemia with genetic test interpretation |
| `assess_renal_drug_constraints` | Assess CV drug safety by eGFR stage and kidney count (13 drug classes, single-kidney modifier, KDIGO 2024) |
| `calculate_lipid_treatment_targets` | LDL/ApoB/Non-HDL targets by risk tier with stepwise therapy pathway modeling (statin → ezetimibe → PCSK9) |
| `assess_postcovid_cv_risk` | Post-COVID CV risk tier adjustment, mechanism flags, double endothelial injury detection, cardiac workup recommendations |
| `search_cvd_prs_scores` | Query PGS Catalog REST API for validated CVD polygenic risk scores by trait |
| `calculate_cvd_prs` | Compute polygenic risk score from germline genotype file + PGS Catalog score |
| `interpret_cvd_prs_percentile` | Map raw PRS to population percentile and clinical risk tier (Khera et al. 2018) |
| `assess_pregnancy_complication_cv_risk` | Evaluate adverse pregnancy outcomes as CVD risk enhancers per 2025 AHA/ACC and ESC guidelines, with COVID double endothelial injury detection |

## Risk Equations

- **Reynolds Risk Score** (women) — validated in Women's Health Study (n=24,558); incorporates hsCRP and family history. Reference: Ridker PM et al. JAMA. 2007;297(6):611-619.
- **Framingham Risk Score** (women) — point-based 10-year CHD risk. Reference: Wilson PW et al. Circulation. 1998;97(18):1837-1847.
- **ACC/AHA Pooled Cohort Equation** (White women) — 10-year ASCVD risk for statin decisions. Reference: Goff DC Jr et al. JACC. 2014;63(25 Pt B):2935-59.

## XAI Metadata

Every tool returns an `xai_metadata` field with explainability information for clinical decision support:

| Field | Description |
|-------|-------------|
| `confidence_level` | `high`, `moderate`, or `low` — how reliable the result is given the inputs |
| `confidence_note` | Why this confidence level was assigned |
| `key_drivers` | 1-3 inputs that most influenced the result |
| `guideline_version` | Specific guideline name and year |
| `evidence_grade` | Class I (AHA/ACC), Class I (ESC/EAS), Class IIa, Expert Consensus, Observational Data, or Research Only |
| `counterfactual` | What would change if a key input were different |

`generate_preventive_report` aggregates per-tool XAI metadata into an `evidence_strength_summary` with a formatted evidence table, confidence counts, and action-required flags.

## Quick Start

```bash
cd servers/mcp-cardiometabolic
uv run python -m mcp_cardiometabolic
```

## Tests

```bash
cd servers/mcp-cardiometabolic
uv run pytest -v
```

107 tests covering risk equations, biomarker classification, lipid pattern interpretation, FH clinical scoring, renal drug constraints, lipid treatment targets, post-COVID CV risk, double endothelial injury detection, PRS tools, APO risk assessment, XAI metadata (per-tool presence, confidence logic, report integration), and DRY_RUN behavior.

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `CARDIOMETABOLIC_DRY_RUN` | `true` | When true, adds DRY_RUN warning to responses. Risk equations run real computation in both modes. |

## PAT003 Canonical Values

Designed for PAT003: 67-year-old post-menopausal woman, controlled hypertension, bilateral CVD family history.

| Score | PAT003 Value | Category |
|-------|-------------|----------|
| Reynolds | ~14.3% | Intermediate |
| Framingham | 10% | Intermediate |
| ASCVD | ~10.3% | Intermediate |
