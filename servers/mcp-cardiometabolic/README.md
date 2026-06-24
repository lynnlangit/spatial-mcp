# mcp-cardiometabolic

Cardiovascular risk scoring, biomarker interpretation, and preventive health monitoring. Server #19 in the Precision Medicine MCP Platform.

## Tools (9)

| Tool | Description |
|------|-------------|
| `assess_biomarker_panel` | Interpret cardiovascular biomarkers against clinical reference ranges (LDL, HDL, hsCRP, glucose, HbA1c, BP, triglycerides) |
| `calculate_cvd_risk_scores` | Compute Reynolds, Framingham, and ASCVD Pooled Cohort 10-year risk scores |
| `assess_lpa_status` | Interpret Lp(a) status or recommend testing if not yet measured |
| `generate_preventive_report` | Structured preventive health summary with priority actions and monitoring schedule |
| `get_lifestyle_evidence` | Evidence-based lifestyle interventions with landmark trial citations |
| `search_cvd_prs_scores` | Query PGS Catalog REST API for validated CVD polygenic risk scores by trait |
| `calculate_cvd_prs` | Compute polygenic risk score from germline genotype file + PGS Catalog score |
| `interpret_cvd_prs_percentile` | Map raw PRS to population percentile and clinical risk tier (Khera et al. 2018) |
| `assess_pregnancy_complication_cv_risk` | Evaluate adverse pregnancy outcomes as CVD risk enhancers per 2025 AHA/ACC and ESC guidelines |

## Risk Equations

- **Reynolds Risk Score** (women) — validated in Women's Health Study (n=24,558); incorporates hsCRP and family history. Reference: Ridker PM et al. JAMA. 2007;297(6):611-619.
- **Framingham Risk Score** (women) — point-based 10-year CHD risk. Reference: Wilson PW et al. Circulation. 1998;97(18):1837-1847.
- **ACC/AHA Pooled Cohort Equation** (White women) — 10-year ASCVD risk for statin decisions. Reference: Goff DC Jr et al. JACC. 2014;63(25 Pt B):2935-59.

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

34 tests covering risk equations, biomarker classification, PRS tools, APO risk assessment, and DRY_RUN behavior.

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
