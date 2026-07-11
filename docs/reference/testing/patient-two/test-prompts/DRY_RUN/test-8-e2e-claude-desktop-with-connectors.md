# PatientTwo End-to-End Test — Claude Desktop + Anthropic Connectors

**Purpose:** Extended E2E test that adds literature search, clinical trial matching, and preprint discovery to the base PatientTwo workflow. Uses 6 custom MCP servers (DRY_RUN) plus 3 Anthropic connectors (live data). Adapted for PAT002-BC-2026 (Stage IIA ER+/PR+/HER2- IDC, BRCA2 germline).

**Prerequisites:**
- Claude Desktop with custom servers configured ([desktop-configs/](../../../../../getting-started/desktop-configs/))
- Anthropic connectors enabled: Settings > Connectors > toggle on **ClinicalTrials.gov**, **bioRxiv & medRxiv**, and **PubMed**

**See also:** [Base E2E test (no connectors)](test-7-e2e-claude-desktop.md) | [Connector setup guide](../../../../../for-researchers/CONNECT_EXTERNAL_MCP.md)

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientTwo (PAT002-BC-2026) end-to-end precision oncology analysis across 6 custom MCP servers plus 3 Anthropic connectors. Custom servers use DRY_RUN synthetic data. Connectors query live databases.

Patient profile for context: 42-year-old female, Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma (IDC), BRCA2 germline mutation (c.5946delT), Luminal A subtype, currently on adjuvant tamoxifen, disease-free.

## Stage 1 — Clinical History (mockepic)
Retrieve patient clinical data using mockepic:
- Patient demographics and diagnosis (Michelle Thompson, 42F)
- Lab observations (CEA, CA 15-3, BRCA2 status)
- Current medications (tamoxifen 20mg daily)

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
- Call integrate_omics_data with these exact paths:
  - rna_path: "/data/patient-data/PAT002-BC-2026/multiomics/tumor_rna_seq.csv"
  - protein_path: "/data/patient-data/PAT002-BC-2026/multiomics/tumor_proteomics.csv"
  - phospho_path: "/data/patient-data/PAT002-BC-2026/multiomics/tumor_phosphoproteomics.csv"
  - metadata_path: "/data/patient-data/PAT002-BC-2026/multiomics/sample_metadata.csv"
- Call calculate_stouffer_meta with p_values_dict and effect_sizes_dict for breast cancer genes (ESR1, PGR, PIK3CA, CCND1, MKI67). Use 3 modalities: rna, protein, phospho.

## Stage 6 — Literature Search (PubMed connector)
Search PubMed for evidence supporting treatment decisions:
- Search for "BRCA2 breast cancer PARP inhibitor adjuvant" (recent 2 years)
- Search for "PIK3CA H1047R ER positive breast cancer targeted therapy"
- Search for "CDK4/6 inhibitor adjuvant early breast cancer"
- Summarize the top 3-5 most relevant findings that apply to this patient

## Stage 7 — Clinical Trial Matching (ClinicalTrials.gov connector)
Find recruiting trials this patient might be eligible for:
- search_by_eligibility: condition="breast cancer", sex=FEMALE, min_age="18 Years", max_age="55 Years"
- Also search_trials: condition="breast cancer BRCA2", intervention="PARP inhibitor", status=RECRUITING, phase=["PHASE2","PHASE3"]
- Search for PIK3CA-targeted trials: condition="breast cancer", intervention="alpelisib OR PI3K inhibitor", status=RECRUITING
- Highlight any trials for adjuvant PARP inhibitors or CDK4/6 inhibitors in early ER+ BC
- List top 3-5 trials with NCT ID, title, and why they match this patient

## Stage 8 — Preprint Check (bioRxiv/medRxiv connector)
Check for recent preprints on emerging approaches:
- Search bioRxiv for recent breast cancer biology preprints (last 90 days) in the "cancer biology" category
- Search medRxiv for recent breast cancer clinical trial preprints (last 90 days)
- Note any preprints relevant to BRCA2+ ER+ breast cancer, endocrine resistance, or CDK4/6 inhibitors

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
1. A banner: "DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
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
| 1 | mockepic | DRY_RUN | Michelle Thompson, 42F, ER+/PR+/HER2- IDC, BRCA2, tamoxifen |
| 2 | fgbio | DRY_RUN | 1M reads, avg quality ~32.5, 150bp read length |
| 3 | genomic-results | DRY_RUN | PIK3CA H1047R, BRCA2 germline, MYC/CCND1 amp, TP53 WT |
| 4 | spatialtools | DRY_RUN | ESR1/PGR high in tumor, CD8A moderate, MKI67 low |
| 5 | multiomics | DRY_RUN | Stouffer Z-scores for ER pathway genes, PIK3CA activated |
| 6 | PubMed | **Live** | Recent papers on BRCA2 PARP inhibitors, PIK3CA therapy in ER+ BC |
| 7 | ClinicalTrials.gov | **Live** | Recruiting Phase 2/3 trials for BRCA2+ ER+ breast cancer |
| 8 | bioRxiv/medRxiv | **Live** | Recent preprints on ER+ BC, BRCA2, CDK4/6 inhibitors |
| 9 | patient-report | DRY_RUN | Draft PDF path, validation passed |

**Final banner should read:**
> DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

---

## Key Differences from PatientOne Test-8

| Aspect | PatientOne (Ovarian) | PatientTwo (Breast) |
|--------|---------------------|-------------------|
| PubMed searches | PARP resistance, PI3K in HGSOC | BRCA2 PARP adjuvant, PIK3CA in ER+ BC |
| Trial matching | Ovarian cancer, platinum-resistant | Breast cancer, BRCA2, adjuvant PARP |
| Key trials | PARP + PI3K combinations | OlympiA-like, CDK4/6i adjuvant, alpelisib |
| Preprint focus | HGSOC immunotherapy | ER+ BC endocrine resistance |

---

## Notes

- **Custom servers** (Stages 1-5, 9) run in DRY_RUN mode — results are synthetic, not for clinical use
- **Anthropic connectors** (Stages 6-8) query live databases — PubMed, ClinicalTrials.gov, and bioRxiv return real, current data
- Connectors require no API keys or config files — just toggle them on in Claude Desktop Settings > Connectors
- Typical runtime: 5-10 minutes (connector queries add ~2-3 minutes vs the base test)
- The report in Stage 9 is still DRY_RUN (no real PDF generated) but the treatment recommendations and trial matches it references are grounded in real literature

**See also:** [Base E2E test (no connectors)](test-7-e2e-claude-desktop.md) | [Connector setup guide](../../../../../for-researchers/CONNECT_EXTERNAL_MCP.md)
