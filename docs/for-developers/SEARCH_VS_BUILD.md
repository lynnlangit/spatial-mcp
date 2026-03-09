# Search vs Build: MCP Server Decision Guide

**Always search before you build.** Before creating a new MCP server, check whether an existing internal or external server already covers your needs. This guide walks you through the decision process.

---

## Decision Flowchart

```
  Need a new capability?
          │
          ▼
  ┌───────────────────┐
  │ Step 1: Search    │
  │ internal servers  │──── Found a match? ──── YES ──→ Use it. Done.
  └───────────────────┘
          │ NO
          ▼
  ┌───────────────────┐
  │ Step 2: Search    │
  │ external servers  │──── Found a match? ──── YES ──→ Connect it. Done.
  └───────────────────┘
          │ NO
          ▼
  ┌───────────────────┐
  │ Step 3: Evaluate  │
  │ partial matches   │──── Can you extend? ──── YES ──→ Add tool to existing server.
  └───────────────────┘
          │ NO
          ▼
  ┌───────────────────┐
  │ Step 4: Build     │
  │ a new server      │──→ Follow ADD_NEW_MODALITY_SERVER.md
  └───────────────────┘
```

---

## Step 1: Search Internal Servers

Check the [Server Registry](../reference/shared/server-registry.md) — the canonical list of all 17 internal servers (97 tools total).

### Quick Find by Analysis Type

| If you need... | Use this server | Tools | Status |
|----------------|----------------|-------|--------|
| **Clinical/EHR data** | mcp-epic (real) or mcp-mockepic (synthetic) | 4 / 3 | Production / Mock |
| **FASTQ/VCF QC, variant calling** | mcp-fgbio | 4 | Production |
| **Somatic variants, CNV, HRD** | mcp-genomic-results | 4 | Production |
| **TCGA cohort comparison** | mcp-mocktcga | 5 | Mock |
| **RNA/Protein/Phospho integration** | mcp-multiomics | 10 | Production |
| **Spatial transcriptomics** | mcp-spatialtools | 14 | Production |
| **Histology, image registration** | mcp-openimagedata | 5 | Production |
| **Cell segmentation** | mcp-deepcell | 3 | Production |
| **Cell phenotype classification** | mcp-cell-classify | 3 | Production |
| **Treatment response prediction** | mcp-perturbation | 8 | Production |
| **Quantum cell type fidelity** | mcp-quantum-celltype-fidelity | 6 | Production |
| **Patient-facing PDF reports** | mcp-patient-report | 5 | Production |
| **GEO/SRA dataset download** | mcp-geodownload | 6 | Production |
| **Drug-target associations** | mcp-opentargets | 6 | Production |
| **Immune deconvolution** | mcp-cibersortx | 5 | Production |
| **Neoantigen prediction & HLA** | mcp-neoantigen | 6 | Production |

If you find a match, you're done — use that server directly. If a server partially covers your need, consider adding a tool to it (see Step 3).

---

## Step 2: Search External MCP Servers

Six external MCP servers are available for life sciences research. See [CONNECT_EXTERNAL_MCP.md](../for-researchers/CONNECT_EXTERNAL_MCP.md) for full setup instructions.

### Anthropic Connectors (hosted, toggle-on)

| Server | Tools | What it provides |
|--------|-------|-----------------|
| **ClinicalTrials.gov** | 6 | Search 500K+ trials by condition, sponsor, phase, eligibility |
| **bioRxiv & medRxiv** | 9 | Search 260K+ preprints, track publication status, submission trends |
| **PubMed** | 5 | Search 36M+ biomedical citations, full text via PMC, related articles |
| **Seqera** | 7 | Nextflow pipeline orchestration, nf-core module search |

### Community Servers (self-hosted)

| Server | Tools | What it provides |
|--------|-------|-----------------|
| **cBioPortal** | 12 | TCGA and cancer genomics — mutations, expression, CNV, clinical data |
| **Hugging Face** | 7 | ML model/dataset/paper search, biomedical NLP models |

If an external server covers your need, connect it and you're done.

---

## Step 3: Evaluate Fit

If you found a partial match in Steps 1 or 2, evaluate whether extending an existing server is better than building new.

### Check these questions:

1. **Does the existing server already handle your data type?** If yes, add a tool to it rather than creating a new server.
2. **Is the server production-ready or mock?** Check the [Server Registry](../reference/shared/server-registry.md) status column. Mock servers (mcp-mocktcga, mcp-mockepic) return synthetic data only.
3. **Does DRY_RUN mode meet your needs?** All servers default to DRY_RUN=true (synthetic data). For real analysis, you need DRY_RUN=false with the appropriate data and dependencies installed.
4. **Does the tool list cover your workflow?** Read the server's README for the full tool list and capabilities.

### When to add a tool to an existing server

- Your new capability fits the server's domain (e.g., a new statistical test in mcp-multiomics)
- It uses the same libraries and data formats
- It would be used alongside the server's existing tools

### When to build a new server

Move to Step 4 if no existing server handles your data type or analysis domain.

---

## Step 4: Decide to Build

Before building, answer these four questions (from the [New Modality Server Guide](ADD_NEW_MODALITY_SERVER.md#when-to-add-a-new-server)):

1. Does this data type have **5 or more distinct analysis tools**?
2. Does it require **2 or more specialized Python libraries**?
3. Will it integrate with **2 or more other modalities** in workflows?
4. Is there a **clear audience** who needs just this modality?

**If 3+ answers are YES** — create a new server. Follow the complete implementation guide: [ADD_NEW_MODALITY_SERVER.md](ADD_NEW_MODALITY_SERVER.md).

**If fewer than 3 are YES** — add your capability as a tool in an existing server instead.

---

## Quick Reference Table

| I need to... | First check | Then check | Build only if... |
|-------------|------------|------------|-------------------|
| Analyze genomic variants | mcp-fgbio, mcp-genomic-results | — | Neither covers your variant type |
| Query clinical records | mcp-epic, mcp-mockepic | — | Different FHIR resource needed |
| Search literature | — | PubMed, bioRxiv connectors | Need a domain-specific corpus |
| Find clinical trials | — | ClinicalTrials.gov connector | Need custom trial matching logic |
| Run bioinformatics pipelines | — | Seqera connector | Need non-Nextflow orchestration |
| Query TCGA cohorts | mcp-mocktcga | cBioPortal (community) | Need a cancer DB not in cBioPortal |
| Analyze spatial data | mcp-spatialtools | — | New spatial method not covered |
| Process histology images | mcp-openimagedata, mcp-deepcell | — | Radiology or other imaging modality |
| Classify cell phenotypes | mcp-cell-classify | — | New classification approach needed |
| Integrate multi-omics | mcp-multiomics | — | New omics type (e.g., metabolomics) |
| Predict treatment response | mcp-perturbation | — | Different prediction model needed |
| Find ML models/datasets | — | Hugging Face connector | Need custom model registry |
| Generate patient reports | mcp-patient-report | — | Different report format needed |
| Download GEO/SRA datasets | mcp-geodownload | — | Different public data source |
| Query drug-target evidence | mcp-opentargets | — | Different target DB needed |
| Deconvolve immune cell types | mcp-cibersortx | — | Different deconvolution method |
| Predict neoantigens & HLA binding | mcp-neoantigen | — | Different binding prediction model |

---

## Related Guides

- [Server Registry](../reference/shared/server-registry.md) — Canonical list of all internal servers and tools
- [Connect External MCP Servers](../for-researchers/CONNECT_EXTERNAL_MCP.md) — Setup for the 6 external servers
- [Add a New Modality Server](ADD_NEW_MODALITY_SERVER.md) — Full implementation guide for building new servers
- [Architecture Overview](ARCHITECTURE.md) — System design and integration points

---

**Last Updated:** 2026-03-09
