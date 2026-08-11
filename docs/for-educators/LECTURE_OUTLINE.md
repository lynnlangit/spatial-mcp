# HGSOC Platform — Lecture Outlines

Three 90-minute lectures covering precision oncology, hands-on analysis, and ethical considerations.

---

## Lecture 1: Precision Oncology Data Landscape and MCP Architecture

**Learning objectives:**
- Describe the key data modalities in HGSOC precision oncology
- Explain the Model Context Protocol (MCP) architecture
- Identify the 19 servers and their roles

**Outline:**

1. **HGSOC epidemiology and clinical challenge** (15 min)
   - Ovarian cancer subtypes; why HGSOC is the most lethal
   - Standard workup: BRCA1/2, HRD panel, CA-125, CT imaging
   - Gap: standard workup generates no immunotherapy hypotheses

2. **Genomic instability: HRD and TMB** (10 min)
   - What HRD scores measure (LOH, TAI, LST)
   - Tumor mutational burden and its clinical significance
   - PAT001 values: HRD = 54, TMB = 47.3 mut/Mb

3. **Spatial biology and the tumor microenvironment** (10 min)
   - Visium spatial transcriptomics workflow
   - Moran's I spatial autocorrelation
   - Cell type deconvolution: who's in the neighborhood?

4. **AI in oncology: opportunities and risks** (10 min)
   - Natural language interfaces for bioinformatics
   - Human-in-the-loop: APPROVE/REVISE/REJECT gate
   - Bias and hallucination risks

5. **The Model Context Protocol (MCP)** (15 min)
   - Protocol specification: JSON-RPC, tool schemas, transport
   - Why MCP over REST APIs for AI-orchestrated workflows
   - FastMCP framework: decorators, Pydantic validation, DRY_RUN

6. **Server architecture walkthrough** (15 min)
   - 19 custom servers (119 tools) — see `docs/reference/shared/server-registry.md`
   - 6 external connectors (PubMed, bioRxiv, ClinicalTrials.gov, etc.)
   - Data flow: acquisition -> deconvolution -> profiling -> inference -> report

7. **HIPAA basics for AI systems** (10 min)
   - PHI definition and the 18 HIPAA identifiers
   - De-identification Safe Harbor vs. Expert Determination
   - Audit logging and access controls

8. **Q&A and setup check** (5 min)
   - Verify students have cloned repo and can run `uv sync`

**Suggested reading:**
- [Architecture documentation](../for-developers/ARCHITECTURE.md)
- Konstantinopoulos PA et al. "Homologous Recombination Deficiency: Exploiting the Fundamental Vulnerability of Ovarian Cancer." *Cancer Discovery* 5(11), 2015.

**Hands-on exercise:**
Clone the repo, run `uv sync`, execute a single server's test suite in DRY_RUN mode, and verify the canonical PAT001 values appear in the output.

```bash
git clone https://github.com/lynnlangit/precision-medicine-mcp.git
cd precision-medicine-mcp
cd servers/mcp-genomic-results && uv sync && uv run pytest -v
```

---

## Lecture 2: Live Demo — PAT001 Multi-Modal Analysis

**Learning objectives:**
- Execute the PAT001 walkthrough notebook end-to-end
- Interpret genomic, spatial, and neoantigen results
- Formulate a therapeutic hypothesis from multi-modal data

**Outline:**

1. **Setup and notebook orientation** (10 min)
   - Open `docs/for-educators/PAT001_walkthrough.ipynb`
   - Import canonical fixture; verify values load
   - Explain DRY_RUN vs. live MCP connections

2. **Step 1: Genomic instability (HRD + TMB)** (15 min)
   - Run genomic-results cells
   - Interpret HRD = 54: PARP inhibitor candidacy
   - Discuss TMB = 47.3: well above the pan-cancer TMB-high threshold (≥10 mut/Mb); POLE-corrected hypermutator phenotype supporting checkpoint-inhibitor rationale

3. **Step 2: Neoantigen prediction** (15 min)
   - Run neoantigen cells (RMPEAAPPV, HLA-A*02:01)
   - IC50 = 7.8 nM: strong MHC-I binder
   - Discuss implications for personalized vaccine design

4. **Step 3: Spatial transcriptomics** (15 min)
   - 300 spatial spots analyzed
   - Moran's I = -0.0033: essentially random spatial distribution
   - What this means for tumor heterogeneity

5. **Step 4: Cell type deconvolution** (10 min)
   - Review tumor=56, endothelial=44, macrophages=43, fibroblasts=41, CD8=30
   - Immune-excluded vs. immune-infiltrated phenotypes
   - Clinical implications of CD8+ T cell counts

6. **Step 5: Perturbation prediction** (10 min)
   - NNMT knockdown prediction via GEARS
   - Expected recovery of immune markers
   - From prediction to experimental validation

7. **Synthesis: formulating a therapeutic hypothesis** (15 min)
   - Integrate all five data modalities
   - Three hypotheses: neoantigen vaccine, NNMT/CAF inhibition, checkpoint blockade
   - Class discussion: which hypothesis is strongest and why?

**Suggested reading:**
- [PAT001 walkthrough notebook](PAT001_walkthrough.ipynb)

**Hands-on exercise:**
Modify one PAT001 parameter (e.g., set HRD = 35 instead of 54) and discuss how the therapeutic hypothesis changes. Does PARP inhibitor candidacy still hold? Write a 1-paragraph argument.

---

## Lecture 3: Limitations, Ethics, HIPAA, and Future Directions

**Learning objectives:**
- Identify what this system cannot do
- Explain HIPAA requirements for AI in oncology
- Propose one future research direction

**What this system cannot do:**
- No real-time EHR integration (mock EPIC only -- not validated against production Epic FHIR)
- Quantum server is a research prototype, not an FDA-cleared device
- GEARS model trained on synthetic data -- must be retrained on real TCGA data before clinical use
- All outputs require pathologist and oncologist review before any clinical action
- DRY_RUN mode returns synthetic data that should never be used for patient care decisions

**Outline:**

1. **DRY_RUN vs. live: what's real and what's simulated** (15 min)
   - DRY_RUN contract: same schema, `dry_run: true` flag
   - Which servers have been validated end-to-end with real data
   - Risk of confusing synthetic with clinical results

2. **HIPAA Security Rule overview** (15 min)
   - Administrative, physical, and technical safeguards
   - Minimum Necessary principle for PHI access
   - Breach notification requirements
   - Cloud deployment considerations (GCP BAA, encryption at rest/in transit)

3. **De-identification in practice** (10 min)
   - Safe Harbor method: 18 identifiers
   - Expert Determination: statistical re-identification risk
   - Audit logging: 10-year retention for clinical AI systems

4. **AI bias in oncology** (15 min)
   - Training data representation gaps
   - Disparities in genomic databases by ancestry
   - Prompt injection and hallucination risks in clinical contexts
   - Human-in-the-loop as mitigation

5. **Open research questions** (10 min)
   - Real-time MCP orchestration with production EHR
   - Federated learning across hospital systems
   - Quantum advantage threshold for cell classification
   - Multi-patient cohort analysis at scale
   - Link to [Open Questions](../for-researchers/OPEN_QUESTIONS.md) if available

6. **Student presentations: gap analysis** (20 min)
   - Each student/group presents one HIPAA gap they identified
   - Propose a technical remediation
   - Class votes on most impactful remediation

7. **Wrap-up and course evaluation** (5 min)

**Suggested reading:**
- [HIPAA Checklist](../for-hospitals/HIPAA_CHECKLIST.md) (if available)
- [Known Limitations in README](../../README.md#known-limitations)

**Hands-on exercise:**
Review the HIPAA checklist and identify one gap in the current platform deployment. Propose a technical remediation (e.g., "add field-level encryption for genomic results at rest") and estimate implementation effort (hours/days/weeks).
