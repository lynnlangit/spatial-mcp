# Full Workflow Smoke Test — Single Prompt

---

You are running the HGSOC Immunotherapy Target Discovery workflow for a platinum-resistant Stage IV patient (PatientOne). Execute each step in order and summarize results as a table before moving to the next step.

**Step 1 — Data Acquisition:** Search GEO for "high-grade serous ovarian cancer" and return the top result. Then fetch expression data for genes TP53, CD8A, and VEGFA from the TCGA-OV cohort.

**Step 2 — Deconvolution:** Run a mock CIBERSORTx deconvolution on the expression data returned in Step 1. Return the top 5 cell types by fraction.

**Step 3 — Target Profiling:** Use mcp-opentargets `batch_score_targets` with the full 32-target immunotherapy panel below against ovarian carcinoma (EFO_0001071). Return results as a table with columns: Category | Gene | Druggable | Top Drug | OC Evidence. Flag any gene with an approved or Phase 2+ OC-specific trial with ★.

```
gene_symbols = [
  "PDCD1", "CD274", "CTLA4", "TIGIT", "LAG3", "HAVCR2",
  "CD47", "SIRPA", "CD36",
  "CSF1R", "IL10", "CD163", "PPARG",
  "TGFB1", "PTK2", "COL6A3", "VEGFA",
  "CCL22", "CCR4", "FOXP3", "IL2RA",
  "KLRC1", "MICA", "MICB", "NCR1",
  "DNMT1", "DNMT3A", "HDAC1", "HDAC2",
  "B2M", "TAP1", "TAP2"
]
disease_id = "EFO_0001071"
```

Categories (for output table):
- T Cell Checkpoint: PDCD1, CD274, CTLA4, TIGIT, LAG3, HAVCR2
- Phagocytosis Checkpoint: CD47, SIRPA, CD36
- TAM Reprogramming: CSF1R, IL10, CD163, PPARG
- Immune Exclusion / Stroma: TGFB1, PTK2, COL6A3, VEGFA
- Treg Recruitment: CCL22, CCR4, FOXP3, IL2RA
- NK Cell Dysfunction: KLRC1, MICA, MICB, NCR1
- Epigenetic Priming: DNMT1, DNMT3A, HDAC1, HDAC2
- Antigen Presentation: B2M, TAP1, TAP2

**Step 4 — Neoantigen Burden:** Estimate neoantigen burden for a HGSOC tumor with TMB = 3.2 mutations/Mb. Then score the antigen presentation pathway using the estimated neoantigen count.

**Step 5 — Report:** Generate a one-sentence plain-language summary of the findings suitable for a patient report.