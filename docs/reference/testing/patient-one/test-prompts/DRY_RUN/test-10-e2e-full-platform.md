# PatientOne End-to-End Test — Full Platform (All 17 Custom Servers)

**Last Updated:** 2026-03-08

**Purpose:** Comprehensive single-prompt E2E test exercising **all 17 custom MCP servers** in DRY_RUN mode. Follows the 5-step HGSOC Immunotherapy Target Discovery workflow aligned with the project research plan: deconvolve platinum-resistant bulk RNA-seq cohorts, profile 30+ known immunotherapy targets at cell-type resolution, and generate a ranked target priority list.

**Research context:** Immunotherapy Target Prioritization in Platinum-Resistant Stage IV HGSOC (Fischbach & Walsh Cell 2024 framework). The core question: *Which known immunotherapy targets are specifically upregulated, compositionally enriched, or mechanistically active in platinum-resistant vs. platinum-sensitive HGSOC — and in which immune cell types?*

**Servers tested (17):** mockepic, fgbio, mocktcga, genomic-results, **geodownload**, multiomics, spatialtools, **cibersortx**, openimagedata, deepcell, cell-classify, **opentargets**, perturbation, quantum-celltype-fidelity, **neoantigen**, patient-report *(mcp-epic excluded — local-only, requires hospital credentials)*

**Setup:** See [desktop-configs/](../../../../../getting-started/desktop-configs/) for Claude Desktop configuration. All 17 servers must be configured.

**See also:** [Base E2E (6 servers)](test-7-e2e-claude-desktop.md) | [E2E + Connectors](test-8-e2e-claude-desktop-with-connectors.md) | [Server Registry](../../../../shared/server-registry.md)

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientOne (PAT001-OVC-2025) full-platform HGSOC Immunotherapy Target Discovery analysis. This exercises ALL 17 custom MCP servers in DRY_RUN mode. Summarize results as a table after each step before moving to the next.

Patient profile: 58-year-old female, Stage IV High-Grade Serous Ovarian Carcinoma (HGSOC), platinum-resistant (PFI < 6 months), BRCA1 germline mutation, HRD-positive, TMB 3.2 mut/Mb. HLA type: HLA-A*02:01, HLA-A*03:01, HLA-B*07:02, HLA-B*44:02.

Research question: Which known immunotherapy targets are upregulated, compositionally enriched, or mechanistically active in platinum-resistant HGSOC — and in which immune cell types?

## Step 1 — Data Audit & Acquisition (5 servers: mockepic, fgbio, mocktcga, genomic-results, geodownload)

1a. **Clinical history (mockepic):** Retrieve patient demographics, CA-125 trend, BRCA status, and current medications.

1b. **FASTQ quality (fgbio):** Run validate_fastq on "/data/PAT001_tumor_R1.fastq.gz". Report read count, quality, and read length.

1c. **Cohort context (mocktcga):** Query TP53 mutation frequency and survival data for the TCGA-OV cohort. This is one of 3 platinum-resistant reference cohorts (TCGA-OV, GSE32062, GSE26712).

1d. **Somatic variants (genomic-results):** Parse somatic variants from "/data/patient-data/PAT001-OVC-2025/genomics/somatic_variants.vcf", parse CNV calls from "/data/patient-data/PAT001-OVC-2025/genomics/copy_number_results.cns", and calculate HRD score. Summarize actionable mutations and PARP eligibility.

1e. **GEO reference cohorts (geodownload):** Search GEO for "high-grade serous ovarian cancer platinum resistant" to identify public cohorts. We expect to find GSE32062 (Tothill, 260 samples), GSE26712 (Bonome, 185 samples), and GSE9899. Return top results with accession IDs, sample counts, and platforms.

## Step 2 — Deconvolution & Multi-Omics Setup (4 servers: spatialtools, multiomics, fgbio, cibersortx)

2a. **Spatial transcriptomics (spatialtools):** Load spatial coordinates and gene expression. Run differential expression between tumor vs stroma regions. Compute spatial autocorrelation (Moran's I) for MKI67 — this helps identify proliferating vs. immune-infiltrated zones.

2b. **Multi-omics integration (multiomics):** Run integrate_omics_data with RNA, protein, and phospho CSVs. Then calculate_stouffer_meta for key immunotherapy-relevant genes: PDCD1 (PD-1), CD274 (PD-L1), CTLA4, TIGIT, LAG3, CD47, CSF1R, TGFB1, VEGFA, CCL22.

2c. **Immune deconvolution (cibersortx):** Run run_mock_deconvolution on expression data with LM22 signature matrix. Report the top 5 immune cell types by fraction — we expect high TAM-M2 (tumor-associated macrophages), low CD8+ T cells, and elevated Tregs, consistent with the immunosuppressive TME of platinum-resistant HGSOC.

## Step 3 — Immunotherapy Target Profiling (3 servers: opentargets, genomic-results, mocktcga)

Profile the full immunotherapy target panel from the research plan. Score targets across categories:

3a. **Checkpoint targets (opentargets):** Use batch_score_targets for checkpoint genes [PDCD1, CD274, CTLA4, TIGIT, LAG3, HAVCR2] against ovarian carcinoma (EFO_0001071). Rank by association score.

3b. **TME remodeling targets (opentargets):** Use batch_score_targets for [CD47, CSF1R, TGFB1, VEGFA, CCL22, PTK2] against ovarian carcinoma. These represent phagocytosis checkpoints, TAM reprogramming, immune exclusion, and Treg recruitment.

3c. **Druggability (opentargets):** Use get_target_drugs for the top 2 scoring targets from 3a and 3b. List approved drugs, clinical phases, and mechanisms of action.

3d. **Safety profile (opentargets):** Use get_target_safety for VEGFA and CSF1R. Report safety liabilities — these are key for combination therapy planning.

## Step 4 — Cross-Validation & Perturbation (6 servers: perturbation, quantum-celltype-fidelity, deepcell, cell-classify, neoantigen, openimagedata)

4a. **Imaging — histology (openimagedata):** Run fetch_histology_image for a mock H&E slide at "/data/patient-data/PAT001-OVC-2025/imaging/HE_slide.tiff". This anchors the spatial analysis to tissue morphology.

4b. **Imaging — cell segmentation (deepcell):** Run segment_cells on the histology image using model_type="nuclear". Report cell count and segmentation quality metrics.

4c. **Imaging — phenotyping (cell-classify):** Run classify_cell_states on the segmented cells using marker_columns ["CD8", "CD4", "FOXP3", "PanCK", "CD68", "CD163"]. CD68/CD163 mark TAMs which dominate the HGSOC TME.

4d. **Perturbation prediction (perturbation):** Run perturbation_predict_response to predict tumor cell response to checkpoint blockade (PDCD1 perturbation). This models whether anti-PD-1 therapy would shift the transcriptional state toward immune activation.

4e. **Quantum fidelity (quantum-celltype-fidelity):** Run identify_immune_evasion_states to detect tumor cells evading immune surveillance. In platinum-resistant HGSOC, we expect tumor cells mimicking macrophage signatures as an immune evasion mechanism.

4f. **Neoantigen burden (neoantigen):** Run estimate_neoantigen_burden with TMB=3.2, cancer_type="HGSOC". Then run score_antigen_presentation_pathway using the estimated neoantigen count — include b2m_expression=0.6 to model the B2M loss common in HRD-Dup HGSOC.

4g. **MHC binding (neoantigen):** Run predict_mhc1_binding for peptides ["RMPEAAPPV", "VVPCEPPEV", "HMTEVVRRC"] with alleles ["HLA-A*02:01", "HLA-A*03:01"]. These represent candidate neoantigens from TP53 R175H and PIK3CA E545K mutations. Report strong vs weak binders.

## Step 5 — Synthesis & Reporting (3 servers: multiomics, spatialtools, patient-report)

5a. **Upstream regulators (multiomics):** Run predict_upstream_regulators to identify kinases and transcription factors driving the resistance profile. Look for immune-related regulators: JAK/STAT pathway, NF-kB, and DNMT1/HDAC (epigenetic priming targets per Landon 2026 azacitidine trial NCT02900560).

5b. **Patient report (patient-report):** First call get_report_template_schema to get the exact JSON schema, then:
   1. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
   2. Include findings from ALL prior steps: clinical history, genomic variants (HRD score, actionable mutations), spatial DE results, multi-omics meta-analysis (Stouffer Z-scores for immunotherapy targets), immune deconvolution fractions (TAM-M2 dominance), ranked target scores from Open Targets, neoantigen burden + antigen presentation pathway score, perturbation predictions, and quantum immune evasion results
   3. In treatment_options, frame findings as ranked immunotherapy target hypotheses:
      - Combination hypothesis 1: anti-TAM remodeling (CSF1R inhibitor) + checkpoint (anti-TIGIT or anti-PD-1)
      - Combination hypothesis 2: anti-VEGF (bevacizumab) + checkpoint (anti-PD-L1)
      - Combination hypothesis 3: epigenetic priming (azacitidine) + checkpoint (anti-PD-1), per Landon 2026 NCT02900560
   4. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
2. **Server coverage table** — list all 17 servers used, with a checkmark for each one that returned successfully
3. **Ranked immunotherapy target table** — top 10 targets with: gene, target category (checkpoint/TAM/exclusion/etc.), Open Targets score, cell-type context from deconvolution, and recommended combination approach
4. Key findings from each step (1-2 bullets each)
5. The report file_path from the generate_patient_report response
6. Instructions: "Use patient-report:approve_patient_report with reviewer_name to finalize"
7. Note that ALL results are DRY_RUN synthetic data, not for clinical use
```

---

## Expected Results

| Step | Server | Tool(s) Called | Key Expected Output |
|------|--------|---------------|-------------------|
| 1a | mockepic | query_patient_records | Demographics, CA-125 trend, BRCA1+, medications |
| 1b | fgbio | validate_fastq | 1M reads, avg quality ~32.5, 150bp |
| 1c | mocktcga | query_gene_mutations, query_survival_data | TP53 freq ~96%, survival curves |
| 1d | genomic-results | parse_somatic_variants, parse_cnv_calls, calculate_hr_deficiency_score | TP53/PIK3CA/PTEN mutations, HRD=44, PARP eligible |
| 1e | **geodownload** | search_geo_datasets | GSE32062 (260 samples), GSE26712 (185 samples), GSE9899 |
| 2a | spatialtools | differential_expression, spatial_autocorrelation | DE genes, Moran's I for MKI67 |
| 2b | multiomics | integrate_omics_data, calculate_stouffer_meta | Stouffer Z-scores for immunotherapy targets (PDCD1, TIGIT, etc.) |
| 2c | **cibersortx** | run_mock_deconvolution | TAM-M2 ~35%, CD8+ T ~12%, Tregs ~5%, NK ~3%, B cells ~8% |
| 3a | **opentargets** | batch_score_targets | Checkpoint target scores: PDCD1, TIGIT, LAG3 ranked |
| 3b | **opentargets** | batch_score_targets | TME targets scores: VEGFA, CSF1R, TGFB1 ranked |
| 3c | **opentargets** | get_target_drugs | Drug lists for top targets (e.g., bevacizumab, pembrolizumab) |
| 3d | **opentargets** | get_target_safety | VEGFA: hypertension, bleeding risk; CSF1R: hepatotoxicity |
| 4a | openimagedata | fetch_histology_image | Image metadata, dimensions |
| 4b | deepcell | segment_cells | Cell count, segmentation mask path |
| 4c | cell-classify | classify_cell_states | Cell type proportions (CD8+, CD4+, Treg, tumor, TAM) |
| 4d | perturbation | perturbation_predict_response | PDCD1 perturbation: immune activation shift |
| 4e | quantum | identify_immune_evasion_states | Evasion states with fidelity scores |
| 4f | **neoantigen** | estimate_neoantigen_burden, score_antigen_presentation_pathway | ~38 neoantigens, pathway score ~0.65 (B2M loss modeled) |
| 4g | **neoantigen** | predict_mhc1_binding | Strong/weak binder classification for TP53/PIK3CA neoantigens |
| 5a | multiomics | predict_upstream_regulators | Kinases (AKT1, JAK2), TFs (TP53, NF-kB, STAT3) |
| 5b | patient-report | get_report_template_schema, generate_patient_report | Draft PDF with ranked target priority list |

**Final output should include:**
> DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

**Server coverage table: 17/17 servers with checkmarks.**

**Ranked target table example (top 5):**

| Rank | Gene | Category | OT Score | Cell-Type Context | Combination Hypothesis |
|------|------|----------|----------|-------------------|----------------------|
| 1 | TIGIT | Checkpoint | 0.82 | CD8+ TEX cells | + anti-VEGF |
| 2 | VEGFA | Exclusion | 0.78 | Stroma/endothelial | + anti-PD-L1 (bev+atezo) |
| 3 | CSF1R | TAM reprog. | 0.71 | TAM-M2 (35% TME) | + anti-PD-1 |
| 4 | CD47 | Phagocytosis | 0.68 | Tumor + TAM | + anti-TIGIT |
| 5 | PDCD1 | Checkpoint | 0.65 | CD8+ T cells | + azacitidine (Landon 2026) |

---

## Notes

- All 17 servers run in DRY_RUN mode — results are **synthetic, not for clinical use**
- No real files need to exist (DRY_RUN returns mock data for any path)
- Typical runtime: 5-15 minutes depending on model (longer than test-7 due to 17 servers vs 6)
- **New servers exercised for the first time:** geodownload (1e), cibersortx (2c), opentargets (3a-3d), neoantigen (4f-4g)
- **Research alignment:** This test follows the HGSOC Immunotherapy Target Prioritization research plan — deconvolving platinum-resistant cohorts, profiling known targets at cell-type resolution, and generating ranked combination hypotheses
- **Target panel tested:** Checkpoint (PDCD1, TIGIT, LAG3, HAVCR2), phagocytosis (CD47), TAM reprogramming (CSF1R), immune exclusion (TGFB1, VEGFA, PTK2), Treg recruitment (CCL22), antigen presentation (HLA, B2M, TAP1)
- To add live literature/trial data, combine with Anthropic connectors per [test-8](test-8-e2e-claude-desktop-with-connectors.md) — specifically PubMed for Landon 2026 (NCT02900560) and ClinicalTrials.gov for active HGSOC immunotherapy trials
- **Key references for validation:** Vazquez-Garcia 2022 Nature (scRNA-seq atlas), Landon 2026 Comms Med (PROC serial biopsies), Xu 2022 Clin Cancer Res (TIGIT on CD8+ TEX)

**See also:** [Base E2E (6 servers)](test-7-e2e-claude-desktop.md) | [E2E + Connectors](test-8-e2e-claude-desktop-with-connectors.md) | [Individual test prompts](./) | [Full demo guide](../../../../../for-funders/DEMO_AND_PITCH.md)
