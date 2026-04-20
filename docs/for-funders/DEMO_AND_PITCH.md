# Demo & Pitch Guide

Copy-paste demo scripts for funders, grant reviewers, and hospital decision-makers.
Uses synthetic PatientOne data (PAT001-OVC-2025) -- 100% safe, no PHI.

**Prerequisites:** Claude Desktop with MCP servers configured ([setup guide](../getting-started/installation.md)), OR deployed Streamlit UI, OR Jupyter notebook.

---

## 90-Second Demo Script

### Prompt 1: Show the Problem (15s)

```
What data modalities need to be integrated for a comprehensive Stage IV
ovarian cancer precision medicine analysis?
```

Talking point: *"Each modality traditionally requires separate tools and 8+ hours."*

### Prompt 2: Show the Solution (30s)

```
Using PatientOne data (PAT001-OVC-2025), identify the top 3 actionable
treatment targets based on spatial transcriptomics pathway enrichment.
```

Talking point: *"Natural language, no coding. AI coordinates the servers automatically."*

### Prompt 3: Show the Speed (20s)

```
How long would this analysis take manually vs. with MCP servers?
```

Key result: **40 hours -> 2-5 hours** (production); 25-35 min in DRY_RUN demo.
See [Value Proposition](../reference/shared/value-proposition.md) for full metrics.

### Prompt 4: Show the ROI (25s)

```
Calculate the annual ROI for analyzing 100 ovarian cancer patients per year,
assuming $6,000 traditional cost per patient.
```

Key result: ~$313K modeled annual savings at 100 patients; payback in first 2-3 patients.

---

## Full PatientOne Demo (25-35 minutes)

End-to-end demo using all platform capabilities. For clinical details see [PatientOne Profile](../reference/shared/patientone-profile.md).

### Pathway 1: Quick Clinical Overview (5 min)

```
Using the mockepic server, summarize PAT001-OVC-2025's clinical history,
current medications, and treatment timeline.
```

```
Load PAT001-OVC-2025 genomic data and identify pathogenic variants
associated with ovarian cancer or treatment resistance.
```

Servers: `mcp-mockepic`, `mcp-fgbio`

### Pathway 2: Multi-Omics Integration (15 min)

```
Load PAT001-OVC-2025 multi-omics data (RNA, protein, phospho) and run
Stouffer meta-analysis to identify consistently dysregulated genes.
```

```
Perform pathway enrichment on the top 50 hits. Focus on druggable pathways.
```

Servers: `mcp-multiomics`, `mcp-fgbio`

### Pathway 3: Spatial Transcriptomics (15 min)

```
Load PAT001-OVC-2025 Visium spatial data. Run spatial differential expression
comparing tumor vs stromal regions, then pathway enrichment on spatially
variable genes.
```

Servers: `mcp-spatialtools`

### Pathway 4: Full Platform E2E (45-60 min)

Uses all 18 servers including GEO, Open Targets, CIBERSORTx, neoantigen prediction.
See [Full E2E test prompt](../reference/testing/patient-one/test-prompts/DRY_RUN/test-10-e2e-full-platform.md).

---

## Post-Demo Talking Points

- **Safety:** Every AI result requires clinician APPROVE/REVISE/REJECT
- **Status:** Validated on synthetic data; clinical pilot is the next step
- **Timeline:** 6 months to hospital pilot (assumes GCP + Azure AD in place)
- **Cost:** $50K pilot (100 patients) or $75K/year production (500 patients)
- **Open source:** Apache 2.0, no vendor lock-in on the server layer

---

**See also:** [Executive Summary](EXECUTIVE_SUMMARY.md) | [Value Proposition](../reference/shared/value-proposition.md) | [PatientOne Profile](../reference/shared/patientone-profile.md)
