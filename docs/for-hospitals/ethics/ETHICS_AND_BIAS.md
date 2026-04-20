# Ethical AI & Algorithmic Bias Framework

Systematic detection and mitigation of algorithmic bias in precision medicine, aligned with FDA AI/ML SaMD guidance, AMA ethics standards, and NIH All of Us diversity requirements.

**Clinician-in-the-Loop:** Every AI-generated result requires APPROVE/REVISE/REJECT before clinical use. The system assists -- it never replaces clinical judgment.

---

## Why Bias Matters in Precision Medicine

Variant interpretation databases are predominantly Euro-centric (~70% European in ClinVar/COSMIC). A pathogenic variant classified in European populations may have uncertain significance in other ancestries, leading to missed diagnoses or inappropriate treatments.

**Key risks by modality:**
- **Genomics:** Euro-centric reference databases may miss population-specific variants
- **Spatial/Multi-omics:** Reference cell-type signatures may not generalize across populations
- **Clinical:** Treatment recommendations influenced by insurance status or inappropriate race-as-biology proxies

---

## Bias Types in This Platform

| Bias Type | Where It Occurs | Mitigation |
|-----------|----------------|------------|
| **Selection bias** | Training data ancestry skew | Use gnomAD (43% European, 21% African, 14% Latino), All of Us (80% underrepresented) |
| **Measurement bias** | Sequencing platform differences | Batch correction (ComBat in mcp-spatialtools) |
| **Annotation bias** | Euro-centric ClinVar/COSMIC | Flag variants with <5 studies; reduce confidence 30% for underrepresented populations |
| **Algorithmic bias** | Model performance disparity | Validate equal performance across demographic subgroups (fairness metrics below) |

---

## Fairness Metrics

Quarterly audits track three metrics per demographic subgroup:

| Metric | Threshold | Action if Exceeded |
|--------|-----------|-------------------|
| **Demographic parity** | <10% disparity in positive prediction rates | Retrain with balanced sampling |
| **Equalized odds** | <10% disparity in TPR/FPR | Adjust classification thresholds |
| **Calibration** | <10% gap between predicted and observed outcomes | Recalibrate probability estimates |

**Risk thresholds:** <5% subgroup representation = CRITICAL; >20% fairness disparity = CRITICAL.

---

## Diverse Reference Datasets

| Dataset | Population Coverage | Use |
|---------|-------------------|-----|
| **gnomAD v4** | 43% European, 21% African, 14% Latino, 10% East Asian | Variant frequency |
| **All of Us** | 80% underrepresented minorities | Variant validation |
| **Human Cell Atlas** | 35M+ cells, global diversity | Cell-type signatures |
| **TOPMed** | 180K+ genomes, 60% non-European | Rare variant frequency |
| **1000 Genomes** | 26 populations, 5 superpopulations | Population structure |

---

## Audit Process (Quarterly)

1. **Prepare:** Collect de-identified patient data (>=100 patients per ancestry group)
2. **Run:** Execute bias detection across all analysis modalities
3. **Evaluate:** Compute fairness metrics per demographic subgroup
4. **Report:** Document findings with risk levels (LOW/MEDIUM/HIGH/CRITICAL)
5. **Mitigate:** Apply corrections (balanced sampling, threshold adjustment, confidence reduction)
6. **Archive:** Retain audit reports for 10 years (HIPAA-aligned)

**PatientOne audit result:** MEDIUM risk (acceptable with mitigations). Finding: BRCA databases Euro-centric -> flagged variants with <5 studies, reduced confidence 30%.

---

## Regulatory Alignment

| Standard | How Platform Complies |
|----------|----------------------|
| **FDA AI/ML SaMD** | Quarterly bias audits, performance monitoring, update protocols |
| **AMA Ethics** | Clinician-in-the-loop, transparent AI reasoning, no autonomous decisions |
| **NIH All of Us** | Diverse reference datasets, ancestry-aware analysis |
| **21st Century Cures Act** | Health equity through technology, interoperable data |
| **HIPAA** | De-identified audits, 10-year retention, see [hipaa.md](../compliance/hipaa.md) |

---

**See also:** [HIPAA Summary](../../reference/shared/hipaa-summary.md) | [Value Proposition](../../reference/shared/value-proposition.md)
