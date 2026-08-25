# Test 1: CVD Risk Assessment (DRY_RUN)

## Prompt

```
You are conducting a preventive cardiovascular health assessment for PAT003, a 67-year-old post-menopausal woman with controlled hypertension.

**Patient profile:**
- Age 67, female, BMI 26.4, post-menopausal
- BP: 138/82 mmHg (controlled on lisinopril 5 mg daily)
- Lipids: LDL 118, HDL 58, total cholesterol 195, triglycerides 142
- Fasting glucose: 98 mg/dL, HbA1c: 5.6%
- hsCRP: 1.8 mg/L
- Family history: father MI at 61, mother ischemic stroke at 69
- Smoking: never; exercise: moderate (3x/week); diet: low-sodium
- Tier 1 genetic screen: NEGATIVE (FH, HBOC, Lynch all ruled out)

**Using the cardiometabolic MCP server, please:**

1. Assess the biomarker panel — are any values outside optimal ranges?
2. Calculate 10-year cardiovascular risk using all available models (Framingham, ASCVD, Reynolds)
3. Assess Lp(a) status — has it been measured? What is the clinical impact of not knowing?
4. Generate a preventive health report identifying evidence gaps
5. What lifestyle interventions have the strongest evidence for her specific profile?

**Key question:** Given her negative Tier 1 genetic screen, what high-priority tests are STILL missing that could change her risk management?
```

## Expected Results

### Biomarker Panel
- BP slightly elevated but controlled
- LDL 118 mg/dL — borderline, statin decision depends on risk score
- hsCRP 1.8 mg/L — moderate cardiovascular inflammation risk
- Glucose/HbA1c — pre-diabetic range

### Risk Scores (all confirm intermediate risk, 7.5-20%)
- **Reynolds Risk Score:** ~14.3% (primary; validated in women, incorporates hsCRP + family history)
- **Framingham 10-year risk:** ~12.0%
- **ASCVD 10-year risk:** ~10.3%

### Evidence Gaps Identified
1. **Serum Lp(a)** — not measured; independent, genetically fixed CVD risk factor; measure once
2. **APOE genotype** — unknown; CVD + cognitive risk at age 67; not included in population screens
3. **Coronary artery calcium (CAC) score** — not obtained; best reclassification tool at intermediate risk

### Key Insight
Negative Tier 1 genetic screen rules out monogenic familial hypercholesterolemia but does **not** lower the Reynolds score or address polygenic/environmental risk. The three gaps above could meaningfully reclassify her risk.

## Servers Used

| Server | Tools Called |
|--------|-------------|
| mcp-cardiometabolic | `assess_biomarker_panel`, `calculate_cvd_risk_scores`, `assess_lpa_status`, `generate_preventive_report`, `get_lifestyle_evidence` |

## Success Criteria

- [ ] All 5 cardiometabolic tools return responses
- [ ] Risk scores are in intermediate range (7.5-20%)
- [ ] All 3 evidence gaps (Lp(a), APOE, CAC) are surfaced
- [ ] Lifestyle evidence is specific to her profile (post-menopausal, intermediate risk)
- [ ] Report does not recommend clinical action — recommends clinician review

## Canonical Reference

See [`tests/fixtures/pat003_canonical.py`](../../../../../tests/fixtures/pat003_canonical.py) for all validated values.

---

**Data mode:** DRY_RUN (default) | **Servers:** mcp-cardiometabolic
