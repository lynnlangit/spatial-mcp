# PatientTwo End-to-End Test — Claude Desktop (SYNTHETIC_DATA Mode)

**Purpose:** Single-prompt E2E test for Claude Desktop with MCP servers in SYNTHETIC_DATA mode (`*_DRY_RUN=false`). Servers parse actual generated files from `/data/patient-data/PAT002-BC-2026/` instead of returning hardcoded mock data.

**Setup:** See [desktop-configs/](../../../../../getting-started/desktop-configs/) for Claude Desktop configuration. Set all `*_DRY_RUN` env vars to `false` in your `claude_desktop_config.json`.

**See also:** [DRY_RUN version](../DRY_RUN/test-7-e2e-claude-desktop.md) | [Data Modes Guide](../../data-modes-guide.md)

---

## Prerequisites

| Requirement | Details |
|------------|---------|
| All `*_DRY_RUN` env vars | `false` |
| Python deps | pandas, numpy, scipy (for CSV/VCF/JSON parsing) |
| `SPATIAL_DATA_DIR` | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data` |
| Data files | Full `data/patient-data/PAT002-BC-2026/` directory (see table below) |

### Required Data Files (absolute paths)

All paths below use repo root `/Users/lynnlangit/Documents/GitHub/spatial-mcp`.

| Stage | Server | File | Absolute Path |
|-------|--------|------|---------------|
| 1 | mockepic | patient_demographics.json | `.../data/patient-data/PAT002-BC-2026/clinical/patient_demographics.json` |
| 1 | mockepic | lab_results.json | `.../data/patient-data/PAT002-BC-2026/clinical/lab_results.json` |
| 2 | fgbio | PAT002_tumor_R1.fastq.gz | `.../data/patient-data/PAT002-BC-2026/genomics/PAT002_tumor_R1.fastq.gz` (may not exist) |
| 3 | genomic-results | PAT002_somatic.vcf | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/genomics/PAT002_somatic.vcf` |
| 3 | genomic-results | PAT002_cnv.cns | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/genomics/PAT002_cnv.cns` |
| 4 | spatialtools | PAT002_expression.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_expression.csv` |
| 4 | spatialtools | PAT002_coordinates.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_coordinates.csv` |
| 4 | spatialtools | PAT002_regions.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_regions.csv` |
| 4 | spatialtools | PAT002_minimal_spatial.h5ad | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_minimal_spatial.h5ad` |
| 5 | multiomics | tumor_rna_seq.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/tumor_rna_seq.csv` |
| 5 | multiomics | tumor_proteomics.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/tumor_proteomics.csv` |
| 5 | multiomics | tumor_phosphoproteomics.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/tumor_phosphoproteomics.csv` |
| 5 | multiomics | sample_metadata.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/sample_metadata.csv` |
| 5 | multiomics | stouffer_results.csv | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/stouffer_results.csv` |
| 5 | multiomics | top_omics_genes.json | `/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/top_omics_genes.json` |

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientTwo (PAT002-BC-2026) end-to-end precision oncology analysis across 6 servers. All servers are in SYNTHETIC_DATA mode (DRY_RUN=false) — they parse real files from /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/.

## Stage 1 — Clinical History (mockepic)
Retrieve patient clinical data by parsing the actual JSON files:
- Patient demographics from patient_demographics.json (Michelle Thompson, 42F, Stage IIA IDC)
- Lab observations from lab_results.json (CEA, CA 15-3 levels, BRCA2 status)
- Current medications (tamoxifen 20mg daily)

## Stage 2 — FASTQ Quality (fgbio)
Validate FASTQ quality for a tumor sample:
- validate_fastq with path "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/genomics/PAT002_tumor_R1.fastq.gz"
- Report read count, average quality, read length

## Stage 3 — Somatic Variants & HRD (genomic-results)
Parse genomic results from the actual patient-prefixed VCF and CNS files:
- parse_somatic_variants from "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/genomics/PAT002_somatic.vcf"
  - Expect: PIK3CA H1047R (VAF 0.42), GATA3 fs (0.31), CDH1 splice (0.28), MAP3K1 Q761X (0.35), TP53 R248W (0.15)
- parse_cnv_calls from "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/genomics/PAT002_cnv.cns"
  - Expect: BRCA2 loss (cn=1), MYC/CCND1/PIK3CA gain (cn=3), ERBB2 neutral (cn=2)
- calculate_hr_deficiency_score using both files above
- Summarize: PIK3CA H1047R actionable (alpelisib), BRCA2 germline (PARPi eligible), HER2-negative confirmed

## Stage 4 — Spatial Transcriptomics (spatialtools)
Run spatial analysis by parsing the actual patient-prefixed files (absolute paths):
- Expression: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_expression.csv" (900 spots, 36 genes, luminal A profile)
- Coordinates: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_coordinates.csv" (patient-prefixed spot coordinates)
- Regions: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_regions.csv" (5 regions: tumor_core, adipose, stroma, immune_infiltrate, normal_epithelium)
- H5AD: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/spatial/PAT002_minimal_spatial.h5ad"
- Differential expression between tumor_core vs stroma regions
- Spatial autocorrelation (Moran's I) for ESR1 and MKI67
- Confirm: ESR1/PGR/GATA3/FOXA1 elevated, ERBB2 low (HER2-negative spatial validation)

## Stage 5 — Multi-Omics Integration (multiomics)
Integrate omics layers by parsing the actual CSV files (absolute paths):
- integrate_omics_data with:
  - rna_path: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/tumor_rna_seq.csv"
  - protein_path: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/tumor_proteomics.csv"
  - phospho_path: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/tumor_phosphoproteomics.csv"
  - metadata_path: "/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/sample_metadata.csv"
- calculate_stouffer_meta for breast cancer genes (ESR1, PGR, PIK3CA, CCND1, MKI67)

## Stage 6 — Patient Report (patient-report)
First call get_report_template_schema to get the exact JSON schema, then construct valid JSON and call generate_patient_report:
1. Call get_report_template_schema — use the returned schema and example to build report_data_json
2. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
3. Include findings from ALL prior stages (clinical, genomic, spatial, multi-omics)
4. Include drug sensitivity: alpelisib (PIK3CA H1047R), palbociclib (CDK4/6i), olaparib (BRCA2), tamoxifen continuation
5. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
2. Key findings from each stage (1-2 bullets each)
3. The report file_path from the generate_patient_report response
4. Instructions: "Use patient-report:approve_patient_report with reviewer_name to finalize"
5. Note that all results are from SYNTHETIC_DATA mode — parsed from generated files, not for clinical use
```

---

## Expected Results

| Stage | Server | Data Source | Key Expected Output |
|-------|--------|-------------|-------------------|
| 1 | mockepic | Parsed JSON | Michelle Thompson, 42F, ER+/PR+/HER2- IDC, BRCA2, tamoxifen, CEA 2.1/CA15-3 18 (normal) |
| 2 | fgbio | Parsed FASTQ | Read count, quality, length from actual file (or file-not-found if FASTQ not generated) |
| 3 | genomic-results | Parsed VCF/CNS | 5 somatic variants from PAT002_somatic.vcf, 25 CNV segments from PAT002_cnv.cns |
| 4 | spatialtools | Parsed CSV | 900 spots, 5 regions, ESR1/PGR elevated, ERBB2 low, from PAT002_*.csv |
| 5 | multiomics | Parsed CSV | Stouffer Z-scores from tumor_*.csv, ER pathway active, PIK3CA activated |
| 6 | patient-report | Generated | Draft PDF path, validation, drug sensitivity included |

**Final banner should read:**
> DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

---

## How This Differs from DRY_RUN

| Aspect | DRY_RUN (test-7) | SYNTHETIC_DATA (this test) |
|--------|-------------------|---------------------------|
| `*_DRY_RUN` env var | `true` | `false` |
| File I/O | None — inline mocks | Real file reads and parsing |
| VCF/CNS files | `somatic_variants.vcf` / `copy_number_results.cns` | `PAT002_somatic.vcf` / `PAT002_cnv.cns` (patient-prefixed) |
| Spatial files | `visium_*.csv` | `PAT002_expression.csv` / `PAT002_coordinates.csv` / `PAT002_regions.csv` |
| Multi-omics files | Any path | `tumor_*.csv` (not `pdx_*.csv`) |
| Values returned | Hardcoded predetermined | Computed from file contents |
| Prerequisites | None (zero deps) | Python parsing deps + data files |
| Speed | Instant (~seconds) | Slightly slower (file I/O + computation) |

## Notes

For a comparison of PatientOne vs PatientTwo differences, see the [DRY_RUN test-7 comparison table](../DRY_RUN/test-7-e2e-claude-desktop.md).

- All servers parse the synthetic data files in `data/patient-data/PAT002-BC-2026/`
- Results are **computed from generated files** but still synthetic — not for clinical use
- If a file is missing or malformed, the server should return an informative error
- This mode validates that server parsing code works correctly with the PAT002 synthetic data
- The GEARS perturbation results (`perturbation/gears_pat002_results.json`) are not exercised in this test — see individual perturbation tests
- Typical runtime: 3-8 minutes depending on Claude Desktop model
