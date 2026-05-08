# PAT002 Deep Stage Test — Target Profiling + Causal Inference (SYNTHETIC_DATA Mode)

**Purpose:** Run Stage 3 (Target Profiling) and Stage 4 (Causal Inference) for PAT002-BC-2026
to surface investigational hypotheses beyond standard clinical workup. These stages were not
exercised in the initial e2e run.

**Setup:** All `*_DRY_RUN` vars = false except EPIC_DRY_RUN=true. Data at:
`/Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/`

**HLA alleles for PAT002:** HLA-A*02:01, HLA-A*03:01, HLA-B*07:02, HLA-B*44:02,
HLA-C*07:02, HLA-C*05:01

---

### Prompt to paste into Claude Desktop:

```
Run a deep precision oncology analysis for PAT002-BC-2026 (Michelle Thompson, 42F,
Stage IIA ER+/PR+/HER2- IDC, BRCA2 germline c.5946delT, PIK3CA H1047R, on tamoxifen).
Focus on Stages 3 and 4 of the pipeline — target profiling and causal inference.

STAGE 3 — TARGET PROFILING (opentargets + multiomics)

1. Use mcp-opentargets batch_score_targets to score these genes against breast cancer
   (EFO_0000305): PIK3CA, BRCA2, ESR1, GATA3, CDH1, MAP3K1, AKT1, CCND1, CDK4, MTOR
   Return OT evidence scores and top drug candidates for each.

2. Use mcp-opentargets get_target_drugs for PIK3CA and CDK4 — return approved and
   investigational drugs.

3. Use mcp-multiomics predict_upstream_regulators with the stouffer results at:
   /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/multiomics/stouffer_results.csv
   Return top 5 upstream regulators with confidence scores.

STAGE 4 — CAUSAL INFERENCE (perturbation + quantum + neoantigen)

4. Use mcp-perturbation perturbation_load_dataset with:
   h5ad_path: /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/perturbation/pat002_tcells.h5ad
   Then run perturbation_predict_response for these gene knockouts: ESR1, PIK3CA, CDK4
   Return predicted expression changes and top affected genes.

5. Use mcp-quantum-celltype-fidelity compute_cell_type_fidelity with:
   h5ad_path: /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/quantum/PAT002_tumor_spatial.h5ad
   Return cell type fidelity scores and any immune evasion signatures detected.

6. Use mcp-neoantigen predict_mhc1_binding with:
   - peptides derived from PAT002's somatic mutations:
     PIK3CA H1047R → KEILSDDQAR (9-mer spanning H1047)
     PIK3CA H1047R → SDDQARFNL (9-mer)
     GATA3 frameshift → YSAPLSSSL (predicted neoepitope)
     TP53 subclonal → VVRCPHHERCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEV (process for 9-mers)
   - hla_alleles: ["HLA-A*02:01", "HLA-A*03:01", "HLA-B*07:02", "HLA-B*44:02"]
   - Return IC50 values and flag any strong binders (IC50 < 50 nM) as vaccine candidates.

7. Use mcp-neoantigen estimate_neoantigen_burden with the somatic VCF at:
   /Users/lynnlangit/Documents/GitHub/spatial-mcp/data/patient-data/PAT002-BC-2026/genomics/PAT002_somatic.vcf
   and hla_alleles: ["HLA-A*02:01", "HLA-A*03:01", "HLA-B*07:02", "HLA-B*44:02"]

SYNTHESIS

After completing all 7 tool calls, provide:
a) Which findings from Stages 3-4 would NOT be discoverable through standard breast cancer
   clinical workup (standard = BRCA testing + tumor genomic panel + standard imaging)?
b) Top 3 investigational hypotheses ranked by clinical actionability
c) Any convergent signals across perturbation + spatial + neoantigen that strengthen a
   specific hypothesis

Flag the response: SYNTHETIC DATA — not for clinical use.
```
