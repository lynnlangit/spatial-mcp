# mcp-genomic-results

MCP server for parsing somatic variant (VCF) and copy number (CNS) results with clinical annotations for the PatientOne ovarian cancer case study.

## Tools (12)

### Variant and CNV parsing

| Tool | Description |
|------|-------------|
| `parse_somatic_variants` | Parse VCF files, filter by allele frequency, annotate with ClinVar/COSMIC |
| `parse_cnv_calls` | Parse CNVkit .cns files, classify amplifications/deletions, annotate genes |
| `calculate_hr_deficiency_score` | Estimate HRD score from LOH/TAI/LST + BRCA status (simplified, non-clinical) |
| `generate_genomic_report` | Comprehensive report combining VCF + CNV + HRD analysis with therapy recommendations |

### Allelic-imbalance copy number

Eight tools for copy-number inference from allele ratios on tumour-only panel
data. Every one returns a `GradedResult` envelope (`shared/common/graded_result.py`)
carrying its evidence grade, assumptions, limits and detectability analysis — a
bare number cannot leave these tools.

| Tool | Description |
|------|-------------|
| `detect_library_chemistry` | **The gate.** Decides amplicon vs hybrid capture from a BAM. Its verdict is a *required* input to every tool below, because depth-ratio CNV is invalid on an amplicon library. Also reports that deduplication must not be run and that primer trimming is required. |
| `extract_heterozygous_sites` | Pulls informative germline heterozygous loci from a tumour-only VCF and groups them into haplotype blocks. Germline/somatic separation uses dbSNP membership plus a purity argument, not a population-frequency cutoff. Recounts per amplicon with primers trimmed when given a BAM. |
| `qc_heterozygous_sites` | Three QC rules — within-block concordance, within-amplicon concordance, per-site artifact screens — plus a beta-binomial overdispersion fit on the surviving copy-neutral pool. |
| `estimate_tumor_purity` | Purity from clonal driver VAFs (`purity = 2 x VAF`). Emits its three assumptions every time and degrades its own grade when a driver's locus is not verified copy-neutral. |
| `assess_cnv_detectability` | "Could we even have seen this?" Expected deviations per copy-number event, minimum detectable effect, and the depth-scaling ceiling. Standard error uses the **block** count, not the site count. |
| `test_allelic_imbalance` | The core statistic: a latent-sign beta-binomial mixture with significance from resampling whole haplotype blocks. Returns `direction: "undetermined"` unless orthogonal depth evidence is supplied *and* the chemistry permits it. |
| `compare_cnv_architectures` | Ranks M0 (neutral), M1 (one event), M2 (two segments with a breakpoint) by AIC and likelihood ratio. Fires a `caution` flag when the winning model rests on a single locus. |
| `assess_um_prognostic_class` | Uveal melanoma prognostic integration. `actionability` is hard-coded `PROGNOSTIC_ONLY`: chromosome 3 status estimates the risk that a *primary* tumour will metastasise and does not select therapy. |

**These eight tools do not honour `GENOMIC_RESULTS_DRY_RUN` by returning synthetic
payloads.** A dry-run fixture wearing the same envelope as a real result is
exactly the failure the graded envelope exists to prevent. A missing or
unreadable input returns `grade=NOT_ASSESSABLE` with the reason stated.

Optional extra for BAM inspection (`detect_library_chemistry`, primer-aware
recounting):

```bash
uv sync --extra bam
```

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
