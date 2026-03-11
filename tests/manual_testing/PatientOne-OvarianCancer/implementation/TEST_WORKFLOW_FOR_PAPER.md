# TEST WORKFLOW PROMPT 

For paper reproducability.  

## Promp Text 

You are running the HGSOC Immunotherapy Target Discovery workflow for a platinum-resistant Stage IV patient (PatientOne). Execute each step in order and summarize results as a table before moving to the next step.
Step 1 — Data Acquisition: Search GEO for "high-grade serous ovarian cancer" and return the top result. Then fetch expression data for genes TP53, CD8A, and VEGFA from the TCGA-OV cohort.
Step 2 — Deconvolution: Run a mock CIBERSORTx deconvolution on the expression data returned in Step 1. Return the top 5 cell types by fraction.
Step 3 — Target Profiling: Use mcp-opentargets to get association scores for TP53, VEGFA, and PDCD1 against ovarian carcinoma (EFO_0001071). Return scores ranked highest to lowest.
Step 4 — Neoantigen Burden: Estimate neoantigen burden for a HGSOC tumor with TMB = 3.2 mutations/Mb. Then score the antigen presentation pathway using the estimated neoantigen count.
Step 5 — Report: Generate a one-sentence plain-language summary of the findings suitable for a patient report.