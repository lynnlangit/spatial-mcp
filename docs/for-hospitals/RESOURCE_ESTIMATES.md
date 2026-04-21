# Resource Estimates

## Table 1 -- Compute (on-premise, per server)

| Server | RAM (GB) | CPU cores | GPU required? | Notes |
|--------|----------|-----------|---------------|-------|
| genomic-results | 4 | 2 | No | Deterministic; output cacheable |
| neoantigen (MHC-I) | 8 | 4 | No | NetMHCpan-equivalent logic |
| neoantigen (MHC-II) | 8 | 4 | No | -- |
| spatial-tools | 8 | 4 | No | Scales with spot count |
| spatialtools | 8 | 4 | No | -- |
| cell-classify | 4 | 2 | No | -- |
| patient-report | 2 | 1 | No | PDF generation |
| perturbation (GEARS) | 16 | 8 | Optional | n_hvg=1000 min; retrain needs GPU |
| quantum | 8 | 4 | Optional | CPU fallback available; Apple M4 / cloud VM compatible |
| mockepic | 1 | 1 | No | Replace with real EHR adapter in production |
| multiomics | 8 | 4 | No | -- |
| openimagedata | 4 | 2 | No | -- |
| fgbio | 4 | 4 | No | -- |
| geodownload | 2 | 2 | No | Network-bound |
| opentargets | 2 | 1 | No | API-bound |
| mocktcga | 2 | 1 | No | -- |
| deepcell | 4 | 2 | No | -- |
| cibersortx | 4 | 2 | No | API-bound |
| patient-report | 2 | 1 | No | PDF generation |
| cell-classify | 4 | 2 | No | Lightweight classification |
| **Total (18 servers)** | **~105** | **~56** | Optional | Low-RAM servers can co-locate on shared node |

## Table 2 -- Claude API costs (cloud, estimates)

| Workflow | Est. input tokens | Est. output tokens | Est. cost per patient |
|----------|------------------|-------------------|----------------------|
| Genomic + neoantigen only | 5,000 | 2,000 | ~$0.23 (Sonnet) |
| Full 5-server MVP pipeline | 15,000 | 6,000 | ~$0.68 (Sonnet) |
| All 18 servers | 40,000 | 15,000 | ~$1.73 (Sonnet) |

*Pricing as of April 2026. Verify current pricing at https://www.anthropic.com/pricing before budgeting.*

## Table 3 -- Personnel

| Role | Setup hours | Monthly ops hours | Notes |
|------|-------------|-------------------|-------|
| Bioinformatician | 40 | 10 | Server config, data validation |
| IT / DevOps | 20 | 5 | Infrastructure, TLS, port management |
| Oncologist champion | 10 | 8 | Retrospective case review, hypothesis feedback |
| Data privacy officer | 8 | 2 | HIPAA gap review, audit log oversight |

## Cost reduction options

- **DRY_RUN mode**: All 18 servers return synthetic PAT001 data at zero API cost. Use for development, training, and classroom demos.
- **Batch processing**: Queue cases overnight rather than real-time to reduce peak compute demand.
- **Result caching**: Spatial and deconvolution outputs are deterministic for the same h5ad input. Cache at the de-identification layer to avoid recomputation.
