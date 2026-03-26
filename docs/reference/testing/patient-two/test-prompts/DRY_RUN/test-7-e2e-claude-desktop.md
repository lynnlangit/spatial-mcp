# PatientTwo End-to-End Test — Claude Desktop

**Last Updated:** 2026-03-25

**Purpose:** Single-prompt E2E test for Claude Desktop with all custom MCP servers in DRY_RUN mode.
Adapted for PAT002-BC-2026 (Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma, BRCA2 germline).

**Setup:** See [desktop-configs/](../../../../../getting-started/desktop-configs/) for Claude Desktop configuration.

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientTwo (PAT002-BC-2026) end-to-end precision oncology analysis across 6 servers. Use DRY_RUN synthetic data throughout.

## Stage 1 — Clinical History (mockepic)
Retrieve patient clinical data using mockepic:
- Patient demographics and diagnosis (Michelle Thompson, 42F, Stage IIA breast cancer)
- Lab observations (CEA, CA 15-3 levels, BRCA2 status)
- Current medications (tamoxifen)

## Stage 2 — FASTQ Quality (fgbio)
Validate FASTQ quality for a tumor sample:
- validate_fastq with path "/data/PAT002_tumor_R1.fastq.gz"
- Report read count, average quality, read length

## Stage 3 — Somatic Variants & HRD (genomic-results)
Parse genomic results:
- parse_somatic_variants from "/data/patient-data/PAT002-BC-2026/genomics/somatic_variants.vcf"
- parse_cnv_calls from "/data/patient-data/PAT002-BC-2026/genomics/copy_number_results.cns"
- calculate_hr_deficiency_score using both files
- Summarize actionable mutations (PIK3CA H1047R, BRCA2 germline) and PARP eligibility

## Stage 4 — Spatial Transcriptomics (spatialtools)
Run spatial analysis:
- Load spatial coordinates and gene expression from patient-data/PAT002-BC-2026/spatial/
- Gene expression by region for ER pathway genes (ESR1, PGR, GATA3) and immune markers (CD8A, CD68)
- Spatial autocorrelation (Moran's I) for ESR1 and MKI67

## Stage 5 — Multi-Omics Integration (multiomics)
Integrate omics layers:
- integrate_omics_data with RNA, protein, and phospho CSVs from patient-data/PAT002-BC-2026/multiomics/
- calculate_stouffer_meta for breast cancer genes (ESR1, PGR, PIK3CA, CCND1, MKI67)

## Stage 6 — Patient Report (patient-report)
First call get_report_template_schema to get the exact JSON schema, then construct valid JSON and call generate_patient_report:
1. Call get_report_template_schema — use the returned schema and example to build report_data_json
2. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
3. Include findings from ALL prior stages (clinical, genomic, spatial, multi-omics)
4. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
2. Key findings from each stage (1-2 bullets each)
3. The report file_path from the generate_patient_report response
4. Instructions: "Use patient-report:approve_patient_report with reviewer_name to finalize"
5. Note that all results are DRY_RUN synthetic data, not for clinical use
```

---

## Expected Results

| Stage | Server | Key Expected Output |
|-------|--------|-------------------|
| 1 | mockepic | Michelle Thompson, 42F, ER+/PR+/HER2- IDC, BRCA2 mutation, tamoxifen |
| 2 | fgbio | 1M reads, avg quality ~32.5, 150bp read length (DRY_RUN) |
| 3 | genomic-results | BRCA2 frameshift, PIK3CA H1047R, GATA3 fs, MYC/CCND1 amp, CDKN2A del |
| 4 | spatialtools | ESR1/PGR high in tumor regions, CD8A moderate, MKI67 low-moderate |
| 5 | multiomics | Stouffer Z-scores for ER pathway genes, PIK3CA activated |
| 6 | patient-report | Draft PDF path, DRY_RUN status, validation passed |

**Final banner should read:**
> DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

---

## Key Differences from PatientOne (PAT001-OVC-2025)

| Aspect | PatientOne (Ovarian) | PatientTwo (Breast) |
|--------|---------------------|-------------------|
| Cancer type | Stage IV HGSOC | Stage IIA IDC |
| Key mutation | BRCA1 germline | BRCA2 germline |
| TP53 status | R175H (mutant) | Wild-type |
| Biomarkers | CA-125 (389 U/mL) | CEA (2.1), CA 15-3 (18) — normal |
| Immune status | Cold (excluded) | Warm (moderate infiltration) |
| Proliferation | High (Ki67 ~50%) | Low (Ki67 ~15%) |
| Treatment | Carboplatin/paclitaxel/bevacizumab | Tamoxifen (adjuvant) |
| Disease status | Platinum-resistant progression | Disease-free surveillance |

---

## Notes

- All servers run in DRY_RUN mode — results are **synthetic, not for clinical use**
- No real files need to exist (DRY_RUN returns mock data for any path)
- Typical runtime: 2-5 minutes depending on Claude Desktop model
- MockEpic now returns PAT002-specific clinical data (breast cancer profile)

**See also:** [Individual test prompts](./) | [PatientOne tests](../../patient-one/test-prompts/DRY_RUN/)
