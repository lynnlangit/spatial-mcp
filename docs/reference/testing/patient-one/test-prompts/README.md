# PatientOne Test Prompts

Ready-to-use test prompts for the complete PatientOne (PAT001-OVC-2025) precision oncology workflow.

## Two Data Layers

MCP servers support two layers of synthetic data. Choose the mode that fits your use case:

### [DRY_RUN/](DRY_RUN/) — Hardcoded Mock Data (default)

**When to use:** Quick demos, CI testing, no-setup exploration.

- `*_DRY_RUN=true` (the default)
- Servers return **hardcoded inline mock data** — zero file I/O, instant responses
- No prerequisites beyond the MCP servers themselves
- 10 test prompts covering all modalities

| # | Test | Servers |
|---|------|---------|
| 1 | [Clinical & Genomic](DRY_RUN/test-1-clinical-genomic.md) | mockepic, fgbio, mocktcga |
| 2 | [Multi-Omics Enhanced](DRY_RUN/test-2-multiomics-enhanced.md) | multiomics |
| 3 | [Spatial Transcriptomics](DRY_RUN/test-3-spatial.md) | spatialtools |
| 4 | [Imaging](DRY_RUN/test-4-imaging.md) | openimagedata, deepcell, cell-classify |
| 5 | [Integration](DRY_RUN/test-5-integration.md) | all (synthesis of Tests 1-4) |
| 6 | [CitL Review](DRY_RUN/test-6-citl-review.md) | patient-report |
| 7 | [E2E Claude Desktop](DRY_RUN/test-7-e2e-claude-desktop.md) | 6 servers, single prompt |
| 8 | [E2E + Connectors](DRY_RUN/test-8-e2e-claude-desktop-with-connectors.md) | 6 servers + PubMed, ClinicalTrials, bioRxiv |
| 9 | [E2E Seqera Connector](DRY_RUN/test-9-e2e-seqera-connector.md) | mockepic, genomic-results, patient-report + Seqera |
| 10 | [**E2E Full Platform**](DRY_RUN/test-10-e2e-full-platform.md) | **All 17 servers**, HGSOC immunotherapy target discovery |

### [SYNTHETIC_DATA/](SYNTHETIC_DATA/) — Real File Parsing

**When to use:** Validating server parsing code, testing file I/O, integration testing.

- `*_DRY_RUN=false`
- Servers **parse the actual generated files** in `data/patient-data/PAT001-OVC-2025/`
- Requires Python parsing dependencies (pandas, numpy, scipy) and the data files
- 4 test prompts for servers that have real parsing code

| # | Test | Servers | Data Files |
|---|------|---------|------------|
| 1 | [Clinical & Genomic](SYNTHETIC_DATA/test-1-clinical-genomic.md) | mockepic, genomic-results, mocktcga | JSON, VCF, CNS |
| 2 | [Multi-Omics Enhanced](SYNTHETIC_DATA/test-2-multiomics-enhanced.md) | multiomics | CSV (RNA, protein, phospho) |
| 3 | [Spatial Transcriptomics](SYNTHETIC_DATA/test-3-spatial.md) | spatialtools | CSV (coordinates, expression, regions) |
| 7 | [E2E Claude Desktop](SYNTHETIC_DATA/test-7-e2e-claude-desktop.md) | 6 servers, single prompt | All of the above |

## Prerequisites

| Mode | Python | Data Files | Bioinformatics Tools | Speed |
|------|--------|------------|---------------------|-------|
| DRY_RUN | Base only | None | None | Instant |
| SYNTHETIC_DATA | + pandas, numpy, scipy | `data/patient-data/PAT001-OVC-2025/` | None | Seconds |

## Related Resources

- **[Prompt Library](../../../prompts/)** — 96+ reusable prompts by audience and modality (Tests 1-6 here are the canonical source for clinical-workflow.md Prompts 1-6)
- [Data Modes Guide](../data-modes-guide.md) — DRY_RUN vs SYNTHETIC_DATA configuration
- [Quick Test Prompts](../../quick-test-prompts.md) — Rapid single-server verification
- [PatientOne Overview](../README.md) — Complete patient scenario walkthrough
- [Server Registry](../../../shared/server-registry.md) — Canonical server and tool counts
