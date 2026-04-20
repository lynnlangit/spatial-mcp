# PatientOne End-to-End Test — Claude Desktop + Anthropic Connectors

**Last Updated:** 2026-02-22

**Purpose:** Extended E2E test that adds literature search, clinical trial matching, and preprint discovery to the base PatientOne workflow. Uses 6 custom MCP servers (DRY_RUN) plus 3 Anthropic connectors (live data).

**Prerequisites:**
- Claude Desktop with custom servers configured ([desktop-configs/](../../../../../getting-started/desktop-configs/))
- Anthropic connectors enabled: Settings > Connectors > toggle on **ClinicalTrials.gov**, **bioRxiv & medRxiv**, and **PubMed**

**See also:** [Base E2E test (no connectors)](test-7-e2e-claude-desktop.md) | [Connector setup guide](../../../../../for-researchers/CONNECT_EXTERNAL_MCP.md)

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientOne (PAT001-OVC-2025) end-to-end precision oncology analysis across 6 custom MCP servers plus 3 Anthropic connectors. Custom servers use DRY_RUN synthetic data. Connectors query live databases.

Patient profile for context: 58-year-old female, Stage IV High-Grade Serous Ovarian Carcinoma (HGSOC), platinum-resistant, BRCA1 germline mutation, HRD-positive.

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

## Stage 6 — Literature Search (PubMed connector)
Search PubMed for evidence supporting treatment decisions:
- Search for "PARP inhibitor resistance BRCA1 ovarian cancer" (recent 2 years)
- Search for "PIK3CA targeted therapy high-grade serous ovarian"
- Summarize the top 3-5 most relevant findings that apply to this patient

## Stage 7 — Clinical Trial Matching (ClinicalTrials.gov connector)
Find recruiting trials this patient might be eligible for:
- search_by_eligibility: condition="ovarian cancer", sex=FEMALE, min_age="18 Years", max_age="70 Years"
- Also search_trials: condition="ovarian cancer", intervention="PARP inhibitor", status=RECRUITING, phase=["PHASE2","PHASE3"]
- Highlight any trials targeting PI3K/AKT pathway or PARP combinations
- List top 3-5 trials with NCT ID, title, and why they match this patient

## Stage 8 — Preprint Check (bioRxiv/medRxiv connector)
Check for recent preprints on emerging approaches:
- Search bioRxiv for recent cancer biology preprints (last 90 days) in the "cancer biology" category
- Search medRxiv for recent clinical trials preprints (last 90 days)
- Note any preprints relevant to HGSOC, PARP resistance, or PI3K pathway

## Stage 9 — Patient Report (patient-report)
First call get_report_template_schema to get the exact JSON schema, then construct valid JSON and call generate_patient_report:
1. Call get_report_template_schema — use the returned schema and example to build report_data_json
2. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
3. Include findings from ALL prior stages: clinical, genomic, spatial, multi-omics
4. In treatment_options, incorporate the PubMed evidence and matching clinical trials from Stages 6-7
5. Include a clinical_trials list with the top matching trials from Stage 7
6. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "⚠️ DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
2. Key findings from each stage (1-2 bullets each)
3. A "Literature & Trials" section listing:
   - Top PubMed references (author, year, key finding)
   - Top matching clinical trials (NCT ID, title, phase)
   - Any relevant preprints noted
4. The report file_path from the generate_patient_report response
5. Instructions: "Use patient-report:approve_patient_report with reviewer_name to finalize"
6. Note which results are DRY_RUN synthetic data (Stages 1-5, 9) vs live data (Stages 6-8)
```

---

## Expected Results

| Stage | Server/Connector | Data Source | Key Expected Output |
|-------|-----------------|-------------|-------------------|
| 1 | mockepic | DRY_RUN | Patient demographics, CA-125 trend, BRCA status, medications |
| 2 | fgbio | DRY_RUN | 1M reads, avg quality ~32.5, 150bp read length |
| 3 | genomic-results | DRY_RUN | TP53/PIK3CA/PTEN mutations, HRD score 44, PARP eligible |
| 4 | spatialtools | DRY_RUN | DE genes between regions, Moran's I for MKI67 |
| 5 | multiomics | DRY_RUN | Stouffer Z-scores for resistance genes |
| 6 | PubMed | **Live** | Recent papers on PARP resistance, PI3K therapy in HGSOC |
| 7 | ClinicalTrials.gov | **Live** | Recruiting Phase 2/3 trials for BRCA1+ platinum-resistant HGSOC |
| 8 | bioRxiv/medRxiv | **Live** | Recent preprints on HGSOC, PARP, PI3K pathway |
| 9 | patient-report | DRY_RUN | Draft PDF path, validation passed |

**Final banner should read:**
> ⚠️ DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

---

## Notes

- **Custom servers** (Stages 1-5, 9) run in DRY_RUN mode — results are synthetic, not for clinical use
- **Anthropic connectors** (Stages 6-8) query live databases — PubMed, ClinicalTrials.gov, and bioRxiv return real, current data
- Connectors require no API keys or config files — just toggle them on in Claude Desktop Settings > Connectors
- Typical runtime: 5-10 minutes (connector queries add ~2-3 minutes vs the base test)
- The report in Stage 9 is still DRY_RUN (no real PDF generated) but the treatment recommendations and trial matches it references are grounded in real literature

**See also:** [Base E2E test (no connectors)](test-7-e2e-claude-desktop.md) | [Connector setup guide](../../../../../for-researchers/CONNECT_EXTERNAL_MCP.md) | [Full demo guide](../../../../../for-funders/DEMO_AND_PITCH.md)
