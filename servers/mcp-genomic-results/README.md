# mcp-genomic-results

MCP server for parsing somatic variant (VCF) and copy number (CNS) results with clinical annotations for the PatientOne ovarian cancer case study.

## Tools (4)

| Tool | Description |
|------|-------------|
| `parse_somatic_variants` | Parse VCF files, filter by allele frequency, annotate with ClinVar/COSMIC |
| `parse_cnv_calls` | Parse CNVkit .cns files, classify amplifications/deletions, annotate genes |
| `calculate_hr_deficiency_score` | Estimate HRD score from LOH/TAI/LST + BRCA status (simplified, non-clinical) |
| `generate_genomic_report` | Comprehensive report combining VCF + CNV + HRD analysis with therapy recommendations |

## XAI Metadata

Every tool returns an `xai_metadata` field with explainability information:

| Field | Description |
|-------|-------------|
| `confidence_level` | `high`, `moderate`, or `low` — how reliable the result is given the inputs |
| `confidence_note` | Why this confidence level was assigned |
| `key_drivers` | 1-3 inputs that most influenced the result |
| `guideline_version` | Specific guideline or algorithm reference |
| `evidence_grade` | Clinical Grade (CAP/CLIA) or Algorithm-Predicted — Not Clinical Grade |
| `counterfactual` | What would change if a key input were different |

## Quick Start

**Requires:** Python 3.11+

> **Standard setup:** See [Server Installation Guide](../../docs/reference/shared/server-installation.md) for venv creation, pip install, and Claude Desktop config.

```bash
# Run (stdio transport for Claude Desktop)
python -m mcp_genomic_results

# Run (SSE transport for Cloud Run)
MCP_TRANSPORT=sse PORT=3012 python -m mcp_genomic_results
```

## Usage Examples

### Parse somatic variants
```
Parse the VCF file at data/patient-data/PAT001-OVC-2025/genomics/somatic_variants.vcf
and identify actionable mutations with therapy associations.
```

### Parse copy number alterations
```
Analyze the CNVkit results at data/patient-data/PAT001-OVC-2025/genomics/copy_number_results.cns
and report amplified/deleted genes with clinical significance.
```

### Generate comprehensive report
```
Generate a full genomic report for PAT001 using both the VCF and CNS files.
Include HRD scoring and therapy recommendations.
```

## PatientOne Integration

This server fits into the PatientOne workflow:

1. **Upstream:** Seqera/Nextflow runs nf-core/sarek variant calling pipeline
2. **This server:** Parses VCF + CNS outputs, annotates with clinical significance
3. **Downstream:** mcp-patient-report generates patient-facing summary

## Design

- **Pure Python** - No C dependencies (cyvcf2/pysam). Files are small enough for line-by-line parsing.
- **DRY_RUN mode** - Set `GENOMIC_RESULTS_DRY_RUN=true` for synthetic responses without file access.
- **Hardcoded annotations** - Simplified ClinVar/COSMIC lookup tables in `annotations.py`. Not a substitute for real annotation pipelines.
- **HRD scoring** - Simplified LOH+TAI+LST calculation. Documented as non-clinical-grade.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GENOMIC_RESULTS_DRY_RUN` | `true` | Return synthetic data without file access |
| `MCP_TRANSPORT` | `stdio` | Transport protocol (`stdio` or `sse`) |
| `PORT` | `8000` | Port for SSE transport |

## Tests

```bash
pytest tests/unit/mcp-genomic-results/ -v
```
