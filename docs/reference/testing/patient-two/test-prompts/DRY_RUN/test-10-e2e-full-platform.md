# PatientTwo End-to-End Test — Full Platform (All 17 Custom Servers)

**Last Updated:** 2026-03-26

**Purpose:** Comprehensive single-prompt E2E test exercising **all 17 custom MCP servers** in DRY_RUN mode. Follows a Breast Cancer Endocrine Resistance & BRCA2-Targeted Therapy workflow: profile ER pathway activity, assess HRD/PARP eligibility, evaluate immune microenvironment, and generate a ranked treatment priority list.

**Research context:** Endocrine Therapy Optimization in BRCA2-Mutant ER+/PR+/HER2- Early Breast Cancer. The core question: *What is the optimal adjuvant strategy for a BRCA2-mutant, PIK3CA-mutant, Luminal A breast cancer — and what targeted options exist if endocrine resistance develops?*

**Servers tested (17):** mockepic, fgbio, mocktcga, genomic-results, **geodownload**, multiomics, spatialtools, **cibersortx**, openimagedata, deepcell, cell-classify, **opentargets**, perturbation, quantum-celltype-fidelity, **neoantigen**, patient-report *(mcp-epic excluded — local-only, requires hospital credentials)*

**Setup:** See [desktop-configs/](../../../../../getting-started/desktop-configs/) for Claude Desktop configuration. All 17 servers must be configured.

**See also:** [Base E2E (6 servers)](test-7-e2e-claude-desktop.md) | [E2E + Connectors](test-8-e2e-claude-desktop-with-connectors.md) | [Server Registry](../../../../shared/server-registry.md)

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientTwo (PAT002-BC-2026) full-platform Breast Cancer Endocrine Resistance & BRCA2-Targeted Therapy analysis. This exercises ALL 17 custom MCP servers in DRY_RUN mode. Summarize results as a table after each step before moving to the next.

Patient profile: 42-year-old female, Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma (IDC), BRCA2 germline mutation (c.5946delT), PIK3CA H1047R somatic, Luminal A subtype, Ki67 ~15%, adjuvant tamoxifen, disease-free. HLA type: HLA-A*02:01, HLA-A*11:01, HLA-B*35:01, HLA-B*51:01.

Research question: What is the optimal adjuvant and surveillance strategy, and what targeted therapies should be prioritized if endocrine resistance develops?

## Step 1 — Data Audit & Acquisition (5 servers: mockepic, fgbio, mocktcga, genomic-results, geodownload)

1a. **Clinical history (mockepic):** Retrieve patient demographics, CEA/CA 15-3 levels, BRCA2 status, and current medications (tamoxifen).

1b. **FASTQ quality (fgbio):** Run validate_fastq on "/data/PAT002_tumor_R1.fastq.gz". Report read count, quality, and read length.

1c. **Cohort context (mocktcga):** Query PIK3CA mutation frequency and survival data for the TCGA-BRCA cohort. Filter for Luminal A subtype. This is one of 3 reference cohorts (TCGA-BRCA, METABRIC, GSE96058).

1d. **Somatic variants (genomic-results):** Parse somatic variants from "/data/patient-data/PAT002-BC-2026/genomics/somatic_variants.vcf", parse CNV calls from "/data/patient-data/PAT002-BC-2026/genomics/copy_number_results.cns", and calculate HRD score. Summarize actionable mutations (PIK3CA H1047R, BRCA2 germline, GATA3 frameshift) and PARP eligibility.

1e. **GEO reference cohorts (geodownload):** Search GEO for "ER positive breast cancer endocrine resistance BRCA" to identify public cohorts. We expect to find datasets related to tamoxifen resistance, CDK4/6 inhibitor response, and BRCA-mutant breast cancer. Return top results with accession IDs, sample counts, and platforms.

## Step 2 — ER Pathway & Multi-Omics Profiling (4 servers: spatialtools, multiomics, fgbio, cibersortx)

2a. **Spatial transcriptomics (spatialtools):** Load spatial coordinates and gene expression from patient-data/PAT002-BC-2026/spatial/. Run differential expression between tumor vs stroma regions. Compute spatial autocorrelation (Moran's I) for ESR1 and MKI67 — ESR1 clustering indicates homogeneous ER expression (good for endocrine therapy).

2b. **Multi-omics integration (multiomics):** Run integrate_omics_data with exact paths: rna_path="/data/patient-data/PAT002-BC-2026/multiomics/tumor_rna_seq.csv", protein_path="/data/patient-data/PAT002-BC-2026/multiomics/tumor_proteomics.csv", phospho_path="/data/patient-data/PAT002-BC-2026/multiomics/tumor_phosphoproteomics.csv", metadata_path="/data/patient-data/PAT002-BC-2026/multiomics/sample_metadata.csv". Then calculate_stouffer_meta for key breast cancer genes: ESR1, PGR, GATA3, FOXA1, PIK3CA, AKT1, CCND1, CDK4, MKI67, PTEN, ABCB1.

2c. **Immune deconvolution (cibersortx):** Run run_mock_deconvolution on expression data with LM22 signature matrix. Report the top 5 immune cell types by fraction — for ER+ Luminal A, we expect moderate CD8+ T cells (~15-20%), low Tregs (~3%), moderate macrophages, and higher B cell fraction than HGSOC.

## Step 3 — Targeted Therapy Profiling (3 servers: opentargets, genomic-results, mocktcga)

Profile therapeutic targets across categories relevant to ER+ breast cancer:

3a. **Endocrine & CDK4/6 targets (opentargets):** Use batch_score_targets for [ESR1, CDK4, CDK6, CCND1, RB1, FGFR1] against breast carcinoma (EFO_0000305). These represent endocrine therapy targets and CDK4/6 inhibitor pathway.

3b. **PI3K pathway targets (opentargets):** Use batch_score_targets for [PIK3CA, AKT1, MTOR, PTEN, PIK3R1, ERBB3] against breast carcinoma. These represent PI3K pathway inhibitor targets (alpelisib, everolimus).

3c. **Druggability (opentargets):** Use get_target_drugs for the top 2 scoring targets from 3a and 3b. List approved drugs, clinical phases, and mechanisms of action. Expect: tamoxifen/fulvestrant (ESR1), palbociclib/ribociclib (CDK4/6), alpelisib (PIK3CA).

3d. **Safety profile (opentargets):** Use get_target_safety for PIK3CA and CDK4. Report safety liabilities — important for adjuvant setting where quality of life matters.

## Step 4 — Cross-Validation & Advanced Analysis (6 servers: perturbation, quantum-celltype-fidelity, deepcell, cell-classify, neoantigen, openimagedata)

4a. **Imaging — histology (openimagedata):** Run fetch_histology_image for a mock H&E slide at "/data/patient-data/PAT002-BC-2026/imaging/PAT002_tumor_HE_20x.tiff". Describe ductal architecture and stromal patterns.

4b. **Imaging — cell segmentation (deepcell):** Run segment_cells on the histology image using model_type="nuclear". Report cell count and segmentation quality metrics.

4c. **Imaging — phenotyping (cell-classify):** Run classify_cell_states on the segmented cells using marker_columns ["ER", "PR", "HER2", "Ki67", "CD8", "CK19"]. CK19 marks luminal epithelial cells.

4d. **Perturbation prediction (perturbation):** Run perturbation_predict_response to predict tumor cell response to ESR1 knockdown (simulating endocrine resistance). This models what happens when ER signalling is blocked — does the tumor activate PI3K/AKT escape?

4e. **Quantum fidelity (quantum-celltype-fidelity):** Run identify_immune_evasion_states to detect tumor cells with altered antigen presentation. In ER+ breast cancer, immune evasion is subtler than in HGSOC — look for MHC-I downregulation in tumor cells.

4f. **Neoantigen burden (neoantigen):** Run estimate_neoantigen_burden with TMB=1.5 (low, typical for Luminal A), cancer_type="breast_luminal". Then run score_antigen_presentation_pathway — Luminal A typically has intact antigen presentation but low neoantigen load.

4g. **MHC binding (neoantigen):** Run predict_mhc1_binding for peptides ["RHGGWTTK", "STRDPLSE", "KTKQLHEL"] with alleles ["HLA-A*02:01", "HLA-A*11:01"]. These represent candidate neoantigens from PIK3CA H1047R and GATA3 frameshift mutations. Report strong vs weak binders.

## Step 5 — Synthesis & Reporting (3 servers: multiomics, spatialtools, patient-report)

5a. **Upstream regulators (multiomics):** Run predict_upstream_regulators to identify kinases and transcription factors driving the ER+ phenotype. Look for: ESR1/FOXA1 (ER pathway), CDK4/6 (cell cycle), PI3K/AKT (escape pathway), and FGFR (potential resistance mechanism).

5b. **Patient report (patient-report):** First call get_report_template_schema to get the exact JSON schema, then:
   1. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
   2. Include findings from ALL prior steps: clinical history, genomic variants (HRD score, PIK3CA H1047R, BRCA2 germline), spatial ER pathway analysis, multi-omics meta-analysis (Stouffer Z-scores), immune deconvolution, target scores from Open Targets, neoantigen burden, perturbation predictions, and quantum immune evasion results
   3. In treatment_options, frame findings as a tiered treatment strategy:
      - Tier 1 (current): Continue adjuvant tamoxifen; monitor with BRCA2 carrier surveillance
      - Tier 2 (if high-risk features): Ovarian function suppression + aromatase inhibitor + olaparib (OlympiA criteria)
      - Tier 3 (if endocrine-resistant recurrence): CDK4/6 inhibitor (palbociclib) + aromatase inhibitor
      - Tier 4 (if CDK4/6i-resistant): Alpelisib + fulvestrant (PIK3CA H1047R eligible)
   4. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
2. **Server coverage table** — list all 17 servers used, with a checkmark for each one that returned successfully
3. **Tiered treatment strategy table** — 4 tiers with: tier, setting, recommended therapy, molecular rationale, key evidence
4. Key findings from each step (1-2 bullets each)
5. The report file_path from the generate_patient_report response
6. Instructions: "Use patient-report:approve_patient_report with reviewer_name to finalize"
7. Note that ALL results are DRY_RUN synthetic data, not for clinical use
```

---

## Expected Results

| Step | Server | Tool(s) Called | Key Expected Output |
|------|--------|---------------|-------------------|
| 1a | mockepic | query_patient_records | Michelle Thompson, 42F, BRCA2, CEA/CA 15-3 normal, tamoxifen |
| 1b | fgbio | validate_fastq | 1M reads, avg quality ~32.5, 150bp |
| 1c | mocktcga | query_gene_mutations, query_survival_data | PIK3CA freq ~36% in TCGA-BRCA, Luminal A survival curves |
| 1d | genomic-results | parse_somatic_variants, parse_cnv_calls, calculate_hr_deficiency_score | PIK3CA H1047R, BRCA2, GATA3, MYC/CCND1 amp, HRD score |
| 1e | **geodownload** | search_geo_datasets | Tamoxifen resistance, CDK4/6i response, BRCA-BC datasets |
| 2a | spatialtools | differential_expression, spatial_autocorrelation | ESR1/PGR high in tumor, Moran's I for ESR1 and MKI67 |
| 2b | multiomics | integrate_omics_data, calculate_stouffer_meta | Stouffer Z-scores for ER pathway genes |
| 2c | **cibersortx** | run_mock_deconvolution | CD8+ ~15-20%, macrophages, B cells, low Tregs |
| 3a | **opentargets** | batch_score_targets | Endocrine/CDK4/6 target scores: ESR1, CDK4, CCND1 |
| 3b | **opentargets** | batch_score_targets | PI3K pathway scores: PIK3CA, AKT1, MTOR |
| 3c | **opentargets** | get_target_drugs | Tamoxifen, palbociclib, alpelisib, olaparib |
| 3d | **opentargets** | get_target_safety | PIK3CA: hyperglycemia; CDK4: neutropenia |
| 4a | openimagedata | fetch_histology_image | IDC morphology, ductal architecture |
| 4b | deepcell | segment_cells | Cell count, segmentation mask |
| 4c | cell-classify | classify_cell_states | ER+, PR+, HER2-, Ki67 low, CD8 moderate |
| 4d | perturbation | perturbation_predict_response | ESR1 KD: PI3K/AKT escape activation predicted |
| 4e | quantum | identify_immune_evasion_states | Subtle MHC-I downregulation in subset |
| 4f | **neoantigen** | estimate_neoantigen_burden, score_antigen_presentation_pathway | ~12 neoantigens (low TMB), pathway score ~0.82 (intact) |
| 4g | **neoantigen** | predict_mhc1_binding | Strong/weak binder classification for PIK3CA/GATA3 neoantigens |
| 5a | multiomics | predict_upstream_regulators | TFs (ESR1, FOXA1), Kinases (CDK4, PI3K, AKT1) |
| 5b | patient-report | get_report_template_schema, generate_patient_report | Draft PDF with tiered treatment strategy |

**Final output should include:**
> DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

**Server coverage table: 17/17 servers with checkmarks.**

**Tiered treatment strategy:**

| Tier | Setting | Therapy | Molecular Rationale | Key Evidence |
|------|---------|---------|-------------------|-------------|
| 1 | Current adjuvant | Tamoxifen 20mg daily | ESR1 Z=4.5, ER+ 85-95%, Luminal A | NCCN guidelines |
| 2 | High-risk adjuvant | OFS + AI + olaparib | BRCA2 germline, HRD-positive | OlympiA (Tutt 2021) |
| 3 | Endocrine-resistant | Palbociclib + AI | CDK4/CCND1 activated, RB1 intact | PALOMA-2/3, monarchE |
| 4 | CDK4/6i-resistant | Alpelisib + fulvestrant | PIK3CA H1047R | SOLAR-1 (Andre 2019) |

---

## Key Differences from PatientOne Test-10

| Aspect | PatientOne (Ovarian) | PatientTwo (Breast) |
|--------|---------------------|-------------------|
| Research question | Immunotherapy target discovery | Endocrine resistance & BRCA2 therapy |
| Treatment strategy | Ranked immunotherapy targets | Tiered escalation (endocrine > CDK4/6i > PI3Ki) |
| Perturbation model | PDCD1 KD (checkpoint) | ESR1 KD (endocrine resistance) |
| Neoantigen context | TMB 47.3, B2M loss | TMB 1.5, intact presentation |
| Deconvolution focus | TAM-M2 dominance | Moderate CD8+, low Treg |
| Target panel | Checkpoints, CD47, CSF1R | ESR1, CDK4/6, PIK3CA, FGFR1 |

---

## Notes

- All 17 servers run in DRY_RUN mode — results are **synthetic, not for clinical use**
- No real files need to exist (DRY_RUN returns mock data for any path)
- Typical runtime: 5-15 minutes depending on model (longer than test-7 due to 17 servers vs 6)
- **Research alignment:** This test follows a clinically relevant workflow for BRCA2-mutant ER+ breast cancer — current standard of care, escalation strategies, and targeted therapy options
- **Target panel tested:** Endocrine (ESR1, PGR, FOXA1), cell cycle (CDK4, CDK6, CCND1, RB1), PI3K pathway (PIK3CA, AKT1, MTOR, PTEN), growth factor (FGFR1, ERBB3), DNA repair (BRCA2, RAD51)
- To add live literature/trial data, combine with Anthropic connectors per [test-8](test-8-e2e-claude-desktop-with-connectors.md)
- **Key references for validation:** OlympiA (Tutt 2021, NEJM), SOLAR-1 (Andre 2019, NEJM), PALOMA-2 (Finn 2016, NEJM), monarchE (Johnston 2023, Lancet Oncol)

**See also:** [Base E2E (6 servers)](test-7-e2e-claude-desktop.md) | [E2E + Connectors](test-8-e2e-claude-desktop-with-connectors.md) | [Individual test prompts](./) | [PatientOne tests](../../../patient-one/test-prompts/DRY_RUN/)
