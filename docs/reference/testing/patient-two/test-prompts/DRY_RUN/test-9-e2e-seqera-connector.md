# PatientTwo End-to-End Test — Seqera Connector + Genomic Analysis

**Purpose:** Focused E2E test that demonstrates Seqera nf-core pipeline discovery alongside custom MCP servers for genomic analysis and reporting. Uses 3 custom MCP servers (DRY_RUN) plus the Seqera connector (live nf-core queries). Adapted for PAT002-BC-2026 (Stage IIA ER+/PR+/HER2- IDC, BRCA2 germline).

**Prerequisites:**
- Claude Desktop with custom servers configured ([desktop-configs/](../../../../../getting-started/desktop-configs/))
- A free Seqera Platform account ([cloud.seqera.io](https://cloud.seqera.io) — free Cloud Basic tier, no credit card)

> **IMPORTANT — Connect to Seqera before running this test:**
> Open Claude Desktop > Settings > Connectors > find **Seqera** > click **Connect** and complete the Seqera sign-in flow. The connector must show as authenticated (not just toggled on) before the Seqera tools will be available. See [Verify Seqera Connector](#verify-seqera-connector-before-running) below.

**See also:** [Base E2E test (no connectors)](test-7-e2e-claude-desktop.md) | [E2E + Connectors (test-8)](test-8-e2e-claude-desktop-with-connectors.md) | [Connector setup guide](../../../../../for-researchers/CONNECT_EXTERNAL_MCP.md)

---

## Verify Seqera Connector Before Running

The Seqera connector connects to Seqera's infrastructure at `mcp.seqera.io`. If authentication is incomplete, the connector will show as "connected" in the UI but expose zero tools.

**Quick verification** — paste this into a new Claude Desktop conversation first:

```
What nf-core pipelines are available for somatic variant calling?
```

If Seqera tools are working, Claude will call `nfcore_suggest_analysis` and return pipeline recommendations. If you see "Failed to fetch" or a web search fallback instead, revisit Settings > Connectors > Seqera and re-authenticate.

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientTwo (PAT002-BC-2026) precision oncology analysis focusing on pipeline selection and genomic interpretation. Uses 3 custom MCP servers (DRY_RUN) plus the Seqera connector for nf-core pipeline discovery (live).

Patient profile for context: 42-year-old female, Stage IIA ER+/PR+/HER2- Invasive Ductal Carcinoma (IDC), BRCA2 germline mutation (c.5946delT), Luminal A subtype, currently on adjuvant tamoxifen.

## Stage 1 — Clinical Context (mockepic)
Retrieve patient clinical data using mockepic:
- Patient demographics and diagnosis (Michelle Thompson, 42F, breast cancer)
- Lab observations (CEA, CA 15-3, BRCA2 status)
- Current medications (tamoxifen)

## Stage 2 — Pipeline Selection (Seqera connector)
Use the Seqera connector tools (not web search) to recommend and explore nf-core pipelines for this patient's analysis. Call each tool directly:
1. Call the Seqera `nfcore_suggest_analysis` tool — suggest an appropriate nf-core pipeline for somatic variant calling in a BRCA2-mutated ER+ breast cancer sample (WES data, GRCh38 reference)
2. Call the Seqera `describe_nfcore_module` tool twice — first for the "mutect2" module (somatic SNV/indel calling), then for the "cnvkit" module (copy number analysis for MYC/CCND1 amplification detection)
3. Call the Seqera `search_nfcore_module` tool — search for modules related to "HRD" or "homologous recombination deficiency" (relevant for BRCA2 germline carriers)
4. Summarize: recommended pipeline, key modules, and why they are appropriate for this patient (focus on BRCA2 germline + PIK3CA somatic detection)

## Stage 3 — Somatic Variants & HRD (genomic-results)
Parse genomic results (simulating output from the recommended pipeline):
- parse_somatic_variants from "/data/patient-data/PAT002-BC-2026/genomics/somatic_variants.vcf"
- parse_cnv_calls from "/data/patient-data/PAT002-BC-2026/genomics/copy_number_results.cns"
- calculate_hr_deficiency_score using both files
- Summarize actionable mutations (PIK3CA H1047R, BRCA2 germline, GATA3 frameshift) and PARP eligibility

## Stage 4 — Patient Report (patient-report)
First call get_report_template_schema to get the exact JSON schema, then construct valid JSON and call generate_patient_report:
1. Call get_report_template_schema — use the returned schema and example to build report_data_json
2. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
3. Include findings from ALL prior stages: clinical context, pipeline recommendation, genomic findings
4. In treatment_options, reference the pipeline used and genomic evidence supporting PARP inhibitor eligibility (BRCA2 germline), PI3K inhibitor consideration (PIK3CA H1047R), and CDK4/6 inhibitor option
5. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
2. Key findings from each stage (1-2 bullets each)
3. A "Pipeline Recommendation" section listing:
   - Recommended nf-core pipeline and why
   - Key modules (Mutect2, CNVkit, HRD-related)
   - Any relevant modules found for BRCA/HRD analysis
4. The report file_path from the generate_patient_report response
5. Instructions: "Use patient-report:approve_patient_report with reviewer_name to finalize"
6. Note which results are DRY_RUN synthetic data (Stages 1, 3, 4) vs live data (Stage 2)
```

---

## Expected Results

| Stage | Server/Connector | Data Source | Key Expected Output |
|-------|-----------------|-------------|-------------------|
| 1 | mockepic | DRY_RUN | Michelle Thompson, 42F, ER+/PR+/HER2- IDC, BRCA2, tamoxifen |
| 2 | Seqera connector | **Live** | nf-core/sarek recommended, Mutect2 + CNVkit module details, HRD module search results |
| 3 | genomic-results | DRY_RUN | PIK3CA H1047R, BRCA2 germline, GATA3 fs, MYC/CCND1 amp, HRD score |
| 4 | patient-report | DRY_RUN | Draft PDF path, validation passed |

**Final banner should read:**
> DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

---

## Key Differences from PatientOne Test-9

| Aspect | PatientOne (Ovarian) | PatientTwo (Breast) |
|--------|---------------------|-------------------|
| Germline mutation | BRCA1 | BRCA2 |
| Pipeline focus | HGSOC WES | ER+ breast WES |
| Key somatic | TP53 R175H, PIK3CA E545K | PIK3CA H1047R, GATA3 fs |
| CNV focus | PTEN loss | MYC/CCND1 amplification |
| HRD context | Platinum-resistant | Adjuvant PARP eligibility |
| Treatment | PARP + PI3K combination | Tamoxifen + PARP if recurrence |

---

## Notes

- **Custom servers** (Stages 1, 3, 4) run in DRY_RUN mode — results are synthetic, not for clinical use
- **Seqera connector** (Stage 2) queries the live nf-core module/pipeline registry — requires a free Seqera account for authentication ([free Cloud Basic tier](https://seqera.io/pricing/))
- The 3 Seqera tools used (`nfcore_suggest_analysis`, `describe_nfcore_module`, `search_nfcore_module`) access the public nf-core registry only — they do not launch pipelines or incur compute costs
- Typical runtime: 3-5 minutes (Seqera nf-core queries add ~1 minute vs the base test)
- The report in Stage 4 is DRY_RUN (no real PDF generated) but the pipeline recommendation it references is grounded in real nf-core data

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Failed to fetch https://mcp.seqera.io/mcp` | Connector not authenticated | Settings > Connectors > Seqera > disconnect and reconnect, complete sign-in |
| Seqera listed as connected but tools fall back to web search | Auth token expired or tools not exposed | Disconnect, reconnect, and re-authenticate |
| Stage 2 skipped entirely | Connector not enabled | Settings > Connectors > find Seqera > click Connect |

**See also:** [Base E2E test (no connectors)](test-7-e2e-claude-desktop.md) | [E2E + Connectors (test-8)](test-8-e2e-claude-desktop-with-connectors.md) | [Connector setup guide](../../../../../for-researchers/CONNECT_EXTERNAL_MCP.md)
