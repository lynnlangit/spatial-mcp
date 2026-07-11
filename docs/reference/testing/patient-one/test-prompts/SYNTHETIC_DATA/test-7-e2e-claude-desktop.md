# PatientOne End-to-End Test — Claude Desktop (SYNTHETIC_DATA Mode)

**Purpose:** Single-prompt E2E test for Claude Desktop with MCP servers in SYNTHETIC_DATA mode (`*_DRY_RUN=false`). Servers parse actual generated files from `/data/patient-data/PAT001-OVC-2025/` instead of returning hardcoded mock data.

**Setup:** See [desktop-configs/](../../../../../getting-started/desktop-configs/) for Claude Desktop configuration. Set all `*_DRY_RUN` env vars to `false` in your `claude_desktop_config.json`.

**See also:** [DRY_RUN version](../DRY_RUN/test-7-e2e-claude-desktop.md) | [Data Modes Guide](../../data-modes-guide.md)

---

## Prerequisites

| Requirement | Details |
|------------|---------|
| All `*_DRY_RUN` env vars | `false` |
| Python deps | pandas, numpy, scipy (for CSV/VCF/JSON parsing) |
| Data files | Full `data/patient-data/PAT001-OVC-2025/` directory |

Servers that parse real files in this mode:
- **mockepic** — reads `clinical/patient_demographics.json`, `clinical/lab_results.json`
- **genomic-results** — reads `genomics/somatic_variants.vcf`, `genomics/copy_number_results.cns`
- **spatialtools** — reads `spatial/visium_*.csv`
- **multiomics** — reads `multiomics/pdx_*.csv`, `multiomics/sample_metadata.csv`

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientOne (PAT001-OVC-2025) end-to-end precision oncology analysis across 6 servers. All servers are in SYNTHETIC_DATA mode (DRY_RUN=false) — they parse real files from data/patient-data/PAT001-OVC-2025/.

## Stage 1 — Clinical History (mockepic)
Retrieve patient clinical data by parsing the actual JSON files:
- Patient demographics from patient_demographics.json
- Lab observations from lab_results.json (CA-125 trend, BRCA status)
- Current medications

## Stage 2 — FASTQ Quality (fgbio)
Validate FASTQ quality for a tumor sample:
- validate_fastq with path "data/patient-data/PAT001-OVC-2025/genomics/PAT001_tumor_R1.fastq.gz"
- Report read count, average quality, read length

## Stage 3 — Somatic Variants & HRD (genomic-results)
Parse genomic results from the actual VCF and CNS files:
- parse_somatic_variants from "data/patient-data/PAT001-OVC-2025/genomics/somatic_variants.vcf"
- parse_cnv_calls from "data/patient-data/PAT001-OVC-2025/genomics/copy_number_results.cns"
- calculate_hr_deficiency_score using both files
- Summarize actionable mutations and PARP eligibility

## Stage 4 — Spatial Transcriptomics (spatialtools)
Run spatial analysis by parsing the actual CSV files:
- Load spatial coordinates and gene expression from data/patient-data/PAT001-OVC-2025/spatial/
- Differential expression between tumor vs stroma regions
- Spatial autocorrelation (Moran's I) for MKI67

## Stage 5 — Multi-Omics Integration (multiomics)
Integrate omics layers by parsing the actual CSV files:
- integrate_omics_data with RNA, protein, and phospho CSVs from data/patient-data/PAT001-OVC-2025/multiomics/
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
5. Note that all results are from SYNTHETIC_DATA mode — parsed from generated files, not for clinical use
```

---

## Expected Results

| Stage | Server | Data Source | Key Expected Output |
|-------|--------|-------------|-------------------|
| 1 | mockepic | Parsed JSON | Patient demographics, CA-125 trend, BRCA status from actual files |
| 2 | fgbio | Parsed FASTQ | Read count, quality, length from actual file (or file-not-found if FASTQ not generated) |
| 3 | genomic-results | Parsed VCF/CNS | Somatic variants and CNVs parsed from actual files |
| 4 | spatialtools | Parsed CSV | DE genes, Moran's I computed from actual spatial CSVs |
| 5 | multiomics | Parsed CSV | Stouffer Z-scores computed from actual expression CSVs |
| 6 | patient-report | Generated | Draft PDF path, validation |

**Final banner should read:**
> ⚠️ DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

---

## How This Differs from DRY_RUN

| Aspect | DRY_RUN (test-7) | SYNTHETIC_DATA (this test) |
|--------|-------------------|---------------------------|
| `*_DRY_RUN` env var | `true` | `false` |
| File I/O | None — inline mocks | Real file reads and parsing |
| Values returned | Hardcoded predetermined | Computed from file contents |
| Prerequisites | None (zero deps) | Python parsing deps + data files |
| Speed | Instant (~seconds) | Slightly slower (file I/O + computation) |

## Notes

- All servers parse the synthetic data files in `data/patient-data/PAT001-OVC-2025/`
- Results are **computed from generated files** but still synthetic — not for clinical use
- If a file is missing or malformed, the server should return an informative error
- This mode validates that server parsing code works correctly with the synthetic data
- Typical runtime: 3-8 minutes depending on Claude Desktop model
