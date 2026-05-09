# Open Research Questions

These are questions the precision medicine platform is positioned to help answer across oncology and preventive health, pending access to real clinical cohort data. Questions 1–10 address the HGSOC use case (PAT001); questions 11–13 address the ER+ breast cancer use case (PAT002); questions 14–16 address the preventive cardiovascular use case (PAT003, added in v17).

1. **Does HRD score >= 42 predict PARP inhibitor response in HGSOC patients with BRCA1/2 wild-type tumors?**
   This matters clinically because most PARP inhibitor approvals target BRCA-mutant tumors, but HRD-high wild-type patients may also benefit. Servers: `genomic-results` (`calculate_hr_deficiency_score`), `mocktcga` (`get_survival_data`). Data needed: real TCGA HGSOC cohort with treatment outcomes.

2. **Which MHC-I neoantigen binding thresholds (IC50 cutoffs) best predict CD8+ T cell infiltration in HGSOC?**
   Clinically, identifying the IC50 value that correlates with actual immune response would improve neoantigen vaccine design. Servers: `neoantigen` (`predict_mhc1_binding`), `cell-classify` (`classify_cell_states`). Data needed: paired neoantigen and TIL data from HGSOC tumor bank.

3. **Does spatial clustering of CD8+ T cells (Moran's I > 0.1) predict checkpoint immunotherapy response?**
   Clustered vs dispersed immune infiltration may predict which patients benefit from PD-1/PD-L1 blockade. Servers: `spatialtools` (`calculate_spatial_autocorrelation`, `deconvolve_cell_types`). Data needed: spatial transcriptomics plus treatment response data from a treated HGSOC cohort.

4. **Can GEARS perturbation modeling identify synthetic lethal combinations with PARP inhibitors in HRD-high HGSOC?**
   Identifying gene knockdowns that sensitize cells to olaparib could reveal new combination strategies. Servers: `perturbation` (`perturbation_predict_response`), `genomic-results`. Data needed: GEARS model retrained on real HGSOC perturbation screen data.

5. **What is the concordance between this platform's therapeutic hypotheses and actual tumor board decisions in a retrospective HGSOC cohort?**
   This is the core validation question for clinical deployment. Servers: all 19. Data needed: 50+ de-identified retrospective HGSOC cases with documented tumor board decisions.

6. **Does high TMB (> 10 mut/Mb) in HGSOC correlate with neoantigen burden and predict immunotherapy benefit independently of HRD?**
   TMB and HRD may act as independent or synergistic predictors. Servers: `genomic-results` (`parse_somatic_variants`), `neoantigen`. Data needed: TCGA HGSOC WES plus immunotherapy response data.

7. **Can spatial cell neighborhood composition (macrophage-to-CD8 ratio) predict platinum resistance in HGSOC?**
   Platinum resistance is the primary cause of HGSOC mortality; early spatial biomarkers could guide second-line therapy selection. Servers: `spatialtools` (`generate_region_composition_chart`, `perform_differential_expression`). Data needed: pre-treatment spatial transcriptomics from platinum-sensitive vs resistant HGSOC patients.

8. **Does multi-modal integration (HRD + neoantigen + spatial + perturbation) outperform single-modality prediction for HGSOC outcomes?**
   The core scientific premise of this platform needs formal validation against clinical outcomes data. Servers: `multiomics` (`integrate_omics_data`). Data needed: complete multi-modal dataset for >= 100 HGSOC patients with survival outcomes.

9. **Can the quantum server's cell-state embedding improve deconvolution accuracy over classical methods for low-cellularity HGSOC biopsies?**
   Low-cellularity biopsies are common in recurrent HGSOC; quantum approaches may outperform classical methods on sparse data. Servers: `quantum-celltype-fidelity`, `cell-classify`. Data needed: paired low- and high-cellularity biopsies from the same patient with known ground-truth composition.

10. **What is the minimum viable biopsy size (number of spatial spots) needed for reliable deconvolution and Moran's I calculation?**
    Smaller biopsies are clinically preferable; understanding the floor for reliable AI analysis informs biopsy protocol design. Servers: `spatialtools` (`filter_quality`, `calculate_spatial_autocorrelation`). Data needed: titration experiment with biopsies of known composition at varying spot counts.

---

## ER+ Breast Cancer Questions (PAT002, v17+)

11. **Does PIK3CA H1047R mutation status reliably distinguish inavolisib-eligible from alpelisib-eligible ER+/HER2− patients, and does the platform's drug-ranking output match multidisciplinary tumor board selections?**
    The platform's PAT002 analysis ranked inavolisib over alpelisib based on the 2024 FDA approval for PIK3CA-mutant ER+ BC. Validating this ranking against real prescribing decisions would test whether automated mutation-to-drug mapping adds clinical value. Servers: `genomic-results` (`parse_somatic_variants`), `opentargets` (`get_target_drugs`, `batch_score_targets`). Data needed: retrospective ER+/PIK3CA-mutant cohort with treatment selection and PFS outcomes.

12. **Can the quantum server's immune evasion scoring identify ER+ breast cancers that would respond to checkpoint blockade despite being classified as immunologically cold by conventional metrics?**
    ER+ BC is generally considered immune-excluded, but PAT002 showed an evasion score of 0.41 — suggesting partial immune engagement that standard PD-L1 IHC might miss. If quantum-derived evasion scores correlate with immunotherapy response in ER+ BC, this would expand the eligible population. Servers: `quantum-celltype-fidelity` (`identify_immune_evasion_states`, `compute_cell_type_fidelity`), `cibersortx`. Data needed: ER+ BC cohort treated with pembrolizumab or atezolizumab, with paired spatial or bulk RNA-seq.

13. **Does the platform's cross-cancer portability — zero disease-specific code changes between HGSOC and ER+ BC — hold for additional cancer types (e.g., NSCLC, colorectal), and where does the shared architecture break?**
    PAT001 (HGSOC) and PAT002 (ER+ BC) ran on the same 19-server pipeline without modification. Identifying the cancer types or data modalities that require server changes would define the platform's generalizability boundary. Servers: all 19. Data needed: synthetic or de-identified datasets for 2–3 additional cancer types with multi-modal data (WES, spatial, clinical).

---

## Preventive Cardiovascular Health Questions (PAT003, v17+)

14. **Does integrating Reynolds Risk Score, Framingham, and ACC/AHA PCE simultaneously — rather than using a single algorithm — improve intermediate-risk reclassification for post-menopausal women?** The three algorithms use partially overlapping inputs (hsCRP in Reynolds only; treated vs. untreated SBP paths in PCE); convergence vs. divergence across algorithms may itself be clinically informative. Servers: `cardiometabolic` (`calculate_cvd_risk_scores`). Data needed: cohort of women aged 55–75 with known 10-year CVD outcomes.

15. **What fraction of patients classified as "intermediate risk" (7.5–20% 10-yr ASCVD) by standard lipid panel alone are reclassified by Lp(a) measurement, APOE genotyping, or CAC score?** This directly quantifies the clinical value of the three gap tests the platform identifies. Servers: `cardiometabolic` (`assess_lpa_status`, `assess_biomarker_panel`), `opentargets` (`get_target_disease_associations` for LPA, APOE). Data needed: intermediate-risk primary prevention cohort with Lp(a), APOE, and CAC data.

16. **Does negative population-level genetic screening (e.g. Helix Tier 1 — ruling out monogenic FH) systematically shift the downstream clinical workup toward polygenic risk quantification, and does the platform's gap-analysis output align with what cardiologists would order?** The platform's PAT003 result — "negative screen → prioritise Lp(a)/APOE/CAC" — reflects current ESC/AHA guidelines, but this reclassification logic has not been validated against real cardiologist decisions. Servers: `cardiometabolic` (`generate_preventive_report`), `opentargets`. Data needed: intermediate-risk cohort with paired genetic screen results, cardiologist next-test orders, and 5-year outcomes.

---

Researchers interested in collaborating: open a GitHub issue with the `research-question`
label or email {{RESEARCH_CONTACT}}.
