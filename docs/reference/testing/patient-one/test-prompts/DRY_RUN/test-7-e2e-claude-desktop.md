# PatientOne End-to-End Test — Claude Desktop

**Purpose:** Single-prompt E2E test for Claude Desktop with all custom MCP servers ([Server Registry](../../../../../../docs/reference/shared/server-registry.md)) in DRY_RUN mode.
Covers servers across clinical, genomic, spatial, multi-omics, and reporting modalities.

**Setup:** See [desktop-configs/](../../../../../getting-started/desktop-configs/) for Claude Desktop configuration.

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientOne (PAT001-OVC-2025) end-to-end precision oncology analysis across 6 servers. Use DRY_RUN synthetic data throughout.

## Stage 1 — Clinical History (mockepic)
Retrieve patient clinical data using mockepic:
- Patient demographics and diagnosis
- Lab observations (CA-125 trend, BRCA status)
- Current medications

## Stage 2 — FASTQ Quality (fgbio)
Validate FASTQ quality for a tumor sample:
- validate_fastq with path "/data/PAT001_tumor_R1.fastq.gz"
- Report read count, average quality, read length

## Stage 3 — Somatic Variants & HRD (genomic-results)
Parse genomic results:
- parse_somatic_variants from "/data/patient-data/PAT001-OVC-2025/genomics/somatic_variants.vcf"
- parse_cnv_calls from "/data/patient-data/PAT001-OVC-2025/genomics/copy_number_results.cns"
- calculate_hr_deficiency_score using both files
- Summarize actionable mutations and PARP eligibility

## Stage 4 — Spatial Transcriptomics (spatialtools)
Run spatial analysis:
- Load spatial coordinates and gene expression
- Differential expression between tumor vs stroma regions
- Spatial autocorrelation (Moran's I) for MKI67

## Stage 5 — Multi-Omics Integration (multiomics)
Integrate omics layers:
- integrate_omics_data with RNA, protein, and phospho CSVs
- calculate_stouffer_meta for resistance genes (PIK3CA, AKT1, ABCB1, TP53)

## Stage 6 — Patient Report (patient-report)
First call get_report_template_schema to get the exact JSON schema, then construct valid JSON and call generate_patient_report:
1. Call get_report_template_schema — use the returned schema and example to build report_data_json
2. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
3. Include findings from ALL prior stages (clinical, genomic, spatial, multi-omics)
4. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "⚠️ DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
2. Key findings from each stage (1-2 bullets each)
3. The report file_path from the generate_patient_report response
4. Instructions: "Use patient-report:approve_patient_report with reviewer_name to finalize"
5. Note that all results are DRY_RUN synthetic data, not for clinical use
```

---

## Expected Results

| Stage | Server | Key Expected Output |
|-------|--------|-------------------|
| 1 | mockepic | Patient demographics, CA-125 trend, BRCA status, medications |
| 2 | fgbio | 1M reads, avg quality ~32.5, 150bp read length (DRY_RUN) |
| 3 | genomic-results | TP53/PIK3CA/PTEN mutations, HRD score 44, PARP eligible |
| 4 | spatialtools | DE genes between regions, Moran's I for MKI67 (DRY_RUN) |
| 5 | multiomics | Stouffer Z-scores for resistance genes (DRY_RUN) |
| 6 | patient-report | Draft PDF path, DRY_RUN status, validation passed |

**Final banner should read:**
> ⚠️ DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

---

## Notes

- All servers run in DRY_RUN mode — results are **synthetic, not for clinical use**
- No real files need to exist (DRY_RUN returns mock data for any path)
- Typical runtime: 2-5 minutes depending on Claude Desktop model
- To run with real data, set `*_DRY_RUN=false` in `claude_desktop_config.json` (requires real bioinformatics tools installed)

**See also:** [Individual test prompts](./) | [Quick test prompts](../../../quick-test-prompts.md) | [Full demo guide](../../../../../for-funders/DEMO_AND_PITCH.md)
