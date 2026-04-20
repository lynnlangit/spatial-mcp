# PatientOne End-to-End Test — Seqera Connector + Genomic Analysis

**Last Updated:** 2026-02-23

**Purpose:** Focused E2E test that demonstrates Seqera nf-core pipeline discovery alongside custom MCP servers for genomic analysis and reporting. Uses 3 custom MCP servers (DRY_RUN) plus the Seqera connector (live nf-core queries).

**Prerequisites:**
- Claude Desktop with custom servers configured ([desktop-configs/](../../../../../getting-started/desktop-configs/))
- A free Seqera Platform account ([cloud.seqera.io](https://cloud.seqera.io) — free Cloud Basic tier, no credit card)

> **IMPORTANT — Connect to Seqera before running this test:**
> Open Claude Desktop > Settings > Connectors > find **Seqera** > click **Connect** and complete the Seqera sign-in flow. The connector must show as authenticated (not just toggled on) before the Seqera tools will be available. See [Verify Seqera Connector](#verify-seqera-connector-before-running) below.

**See also:** [Base E2E test (no connectors)](test-7-e2e-claude-desktop.md) | [E2E + Connectors (test-8)](test-8-e2e-claude-desktop-with-connectors.md) | [Connector setup guide](../../../../../for-researchers/CONNECT_EXTERNAL_MCP.md)

---

## Verify Seqera Connector Before Running

The Seqera connector connects to Seqera's infrastructure at `mcp.seqera.io` (unlike PubMed/ClinicalTrials/bioRxiv which are fully Anthropic-hosted). If authentication is incomplete, the connector will show as "connected" in the UI but expose zero tools — causing a `Failed to fetch https://mcp.seqera.io/mcp` error.

**Quick verification** — paste this into a new Claude Desktop conversation first:

```
What nf-core pipelines are available for somatic variant calling?
```

If Seqera tools are working, Claude will call `nfcore_suggest_analysis` and return pipeline recommendations. If you see "Failed to fetch" or a web search fallback instead, revisit Settings > Connectors > Seqera and re-authenticate.

---

## Prompt

Copy and paste the following into Claude Desktop:

```
Run a PatientOne (PAT001-OVC-2025) precision oncology analysis focusing on pipeline selection and genomic interpretation. Uses 3 custom MCP servers (DRY_RUN) plus the Seqera connector for nf-core pipeline discovery (live).

Patient profile for context: 58-year-old female, Stage IV High-Grade Serous Ovarian Carcinoma (HGSOC), platinum-resistant, BRCA1 germline mutation, HRD-positive.

## Stage 1 — Clinical Context (mockepic)
Retrieve patient clinical data using mockepic:
- Patient demographics and diagnosis
- Lab observations (CA-125 trend, BRCA status)
- Current medications

## Stage 2 — Pipeline Selection (Seqera connector)
Use the Seqera connector tools (not web search) to recommend and explore nf-core pipelines for this patient's analysis. Call each tool directly:
1. Call the Seqera `nfcore_suggest_analysis` tool — suggest an appropriate nf-core pipeline for somatic variant calling in a BRCA1-mutated HGSOC tumor sample (WES data, GRCh38 reference)
2. Call the Seqera `describe_nfcore_module` tool twice — first for the "mutect2" module (somatic SNV/indel calling), then for the "cnvkit" module (copy number analysis)
3. Call the Seqera `search_nfcore_module` tool — search for modules related to "HRD" or "homologous recombination deficiency"
4. Summarize: recommended pipeline, key modules, and why they are appropriate for this patient

## Stage 3 — Somatic Variants & HRD (genomic-results)
Parse genomic results (simulating output from the recommended pipeline):
- parse_somatic_variants from "/data/patient-data/PAT001-OVC-2025/genomics/somatic_variants.vcf"
- parse_cnv_calls from "/data/patient-data/PAT001-OVC-2025/genomics/copy_number_results.cns"
- calculate_hr_deficiency_score using both files
- Summarize actionable mutations and PARP eligibility

## Stage 4 — Patient Report (patient-report)
First call get_report_template_schema to get the exact JSON schema, then construct valid JSON and call generate_patient_report:
1. Call get_report_template_schema — use the returned schema and example to build report_data_json
2. Build report_data_json as a JSON string with all 5 required sections: patient_info, diagnosis_summary, genomic_findings (list), treatment_options (list), monitoring_plan
3. Include findings from ALL prior stages: clinical context, pipeline recommendation, genomic findings
4. In treatment_options, reference the pipeline used and genomic evidence supporting PARP inhibitor eligibility
5. Call generate_patient_report with the JSON string, report_type="full", output_format="pdf"

## IMPORTANT — Final Output
After generating the report, display a final summary that includes:
1. A banner: "⚠️ DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY"
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
| 1 | mockepic | DRY_RUN | Patient demographics, CA-125 trend, BRCA status, medications |
| 2 | Seqera connector | **Live** | nf-core/sarek recommended, Mutect2 + CNVkit module details, HRD module search results |
| 3 | genomic-results | DRY_RUN | TP53/PIK3CA/PTEN mutations, HRD score 44, PARP eligible |
| 4 | patient-report | DRY_RUN | Draft PDF path, validation passed |

**Final banner should read:**
> ⚠️ DRAFT — REQUIRES CLINICIAN REVIEW AND APPROVAL BEFORE PATIENT DELIVERY

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
