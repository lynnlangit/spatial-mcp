# XAI Metadata Schema Reference

Canonical schema for the `xai_metadata` object returned by every tool across all MCP servers. This is the single source of truth; all other docs link here.

---

## Field Definitions

| Field | Type | Required | Valid Values | Description |
|-------|------|----------|--------------|-------------|
| `confidence_level` | `string` | Yes | `"high"`, `"medium"`, `"low"` | Overall confidence in the result |
| `confidence_note` | `string` | Yes | Free text | Human-readable explanation of why this confidence level was assigned |
| `key_drivers` | `list[string]` | Yes | 1-3 items | Top factors that determined the result |
| `guideline_version` | `string` | Yes | Free text | Clinical guideline or reference standard used (e.g., `"NCCN 2024.2"`, `"AHA/ACC 2019"`) |
| `evidence_grade` | `string` | Yes | Domain-specific (see table below) | Strength of supporting evidence |
| `counterfactual` | `string` | No | Free text or `null` | What would change the result (e.g., `"If BRCA1 were wild-type, PARP inhibitor would not be recommended"`) |

---

## Evidence Grade Values by Server Domain

| Domain | Server(s) | Grades Used | Source Standard |
|--------|-----------|-------------|-----------------|
| Oncology genomics | mcp-fgbio, mcp-genomic-results | `Tier_I` / `Tier_II` / `Tier_III` / `Tier_IV` | AMP/ASCO/CAP variant classification |
| Multi-omics | mcp-multiomics | `strong` / `moderate` / `suggestive` | Stouffer meta-analysis thresholds |
| Spatial transcriptomics | mcp-spatialtools | `strong` / `moderate` / `suggestive` | Spatial statistics significance |
| Drug targets | mcp-opentargets | `Phase_III` / `Phase_II` / `Phase_I` / `Preclinical` | Open Targets clinical phase |
| Immune deconvolution | mcp-cibersortx | `strong` / `moderate` / `suggestive` | CIBERSORTx correlation thresholds |
| Neoantigen prediction | mcp-neoantigen | `strong_binder` / `weak_binder` / `non_binder` | HLA binding affinity (IC50) |
| Perturbation | mcp-perturbation | `strong` / `moderate` / `suggestive` | Predicted effect size |
| Cardiometabolic | mcp-cardiometabolic | `guideline_based` / `model_derived` / `extrapolated` | AHA/ACC risk score guidelines |
| Cell classification | mcp-cell-classify | `strong` / `moderate` / `suggestive` | Classification confidence score |
| EHR / clinical | mcp-mockepic | `EHR_structured` / `EHR_unstructured` / `patient_reported` | Data source reliability |

---

## Validation Rules

1. **`confidence_level`** must be one of exactly three values: `"high"`, `"medium"`, `"low"`.
2. **`key_drivers`** must contain 1 to 3 items. Each item is a short phrase describing a contributing factor.
3. **`counterfactual`** is nullable -- tools may return `null` when no meaningful counterfactual applies.
4. **`guideline_version`** should reference a specific version or year (e.g., `"NCCN 2024.2"`, not just `"NCCN"`).
5. All six fields must be present in every tool response (with `counterfactual` allowed to be `null`).

---

## Helper Function Pattern

Every server implements `_build_xai_metadata()` as a private helper:

```python
def _build_xai_metadata(
    confidence_level: str,
    confidence_note: str,
    key_drivers: list[str],
    guideline_version: str,
    evidence_grade: str,
    counterfactual: str | None = None,
) -> dict:
    return {
        "confidence_level": confidence_level,
        "confidence_note": confidence_note,
        "key_drivers": key_drivers,
        "guideline_version": guideline_version,
        "evidence_grade": evidence_grade,
        "counterfactual": counterfactual,
    }
```

---

## Report Aggregation

When Claude synthesizes results from multiple tools, the patient report includes an `evidence_strength_summary`:

```json
{
  "evidence_strength_summary": {
    "high_confidence_count": 3,
    "medium_confidence_count": 1,
    "low_confidence_count": 0,
    "weakest_link": "Spatial pathway enrichment (medium — limited tumor region coverage)",
    "overall_assessment": "Strong evidence across genomic, multi-omic, and clinical modalities"
  }
}
```

This summary enables clinicians to make informed APPROVE / REVISE / REJECT decisions per the clinician-in-the-loop workflow.

---

**See also:** [Server Registry](server-registry.md) for the current list of XAI-enabled servers
