# DRY_RUN Mode (Canonical Reference)

## Purpose

DRY_RUN mode enables development and testing with realistic synthetic responses, without requiring:
- External tool dependencies (fgbio, STAR, DeepCell, etc.)
- Real data files or GCS access
- API credentials or authentication
- Large compute resources

## Activation

Set the server's DRY_RUN environment variable to `true`:

```bash
export {SERVER_NAME}_DRY_RUN=true
```

### Per-Server Variable Names

| Server | Variable |
|--------|----------|
| mcp-spatialtools | `SPATIAL_DRY_RUN` |
| mcp-fgbio | `FGBIO_DRY_RUN` |
| mcp-multiomics | `MULTIOMICS_DRY_RUN` |
| mcp-perturbation | `PERTURBATION_DRY_RUN` |
| mcp-deepcell | `DEEPCELL_DRY_RUN` |
| mcp-cell-classify | `CELL_CLASSIFY_DRY_RUN` |
| mcp-openimagedata | `IMAGE_DRY_RUN` |
| mcp-mocktcga | `MOCKTCGA_DRY_RUN` |
| mcp-genomic-results | `GENOMIC_RESULTS_DRY_RUN` |
| mcp-quantum-celltype-fidelity | `QUANTUM_DRY_RUN` |
| mcp-deidentify | `DEIDENTIFY_DRY_RUN` (**defaults to `false`** — see below) |

> **Exception — mcp-deidentify defaults to DRY_RUN off.** Every other server
> defaults its DRY_RUN variable to `true`. `mcp-deidentify` defaults to `false`,
> because a de-identification server that silently returns fabricated entities is
> a safety failure rather than a safe default: a caller who forgets the variable
> must get a loud error, never synthetic output that reads like a successful
> de-identification. Fixture mode must be opted into explicitly.
>
> DRY_RUN is also all-or-nothing per tool there. `validate_deidentification`
> cannot run its Haiku red-team layer in DRY_RUN, so instead of letting the other
> two layers imply a verdict it returns `status="unavailable_in_dry_run"` with
> `passed=null`. See the
> [server README](../../../servers/mcp-deidentify/README.md#dry_run-mode).

## When to Use

- **Local development** — Test without installing bioinformatics tools
- **CI/CD pipelines** — Automated testing with predictable outputs
- **Demonstrations** — Show capabilities without real patient data
- **Onboarding** — New developers can explore immediately
- **Education** — Classroom use with ~$0.32 total cost

## What DRY_RUN Returns

Each server returns clinically realistic synthetic data based on the PatientOne case study. Responses include:
- Realistic data structures matching production output
- Biologically plausible values calibrated to published studies
- Appropriate metadata and annotations

## Cost

- **DRY_RUN:** ~$1 total for full PatientOne workflow (25-35 minutes, tokens only)
- **Production:** Low per-patient compute cost ([Cost Analysis](cost-analysis.md))

## Production

Always set `DRY_RUN=false` in production deployments. Production mode requires:
- Real data files accessible via GCS or local paths
- Bioinformatics tools installed (or Cloud Run containers)
- Appropriate API credentials

> **mcp-deidentify note:** When `DEIDENTIFY_DRY_RUN=false`, the server calls `claude-haiku-4-5-20251001` via the Anthropic API. `ANTHROPIC_API_KEY` must be set. In Cloud Run (HOSPITAL1), this is provided via ambient service account auth — no Secret Manager action required.

---

**Server installation:** [server-installation.md](server-installation.md)
**Cost analysis:** [cost-analysis.md](cost-analysis.md)
