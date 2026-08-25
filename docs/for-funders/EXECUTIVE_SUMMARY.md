# Executive Summary

> **v17 update (April 2026):** Platform expanded from oncology to preventive health.
> **v18 update (June 2026):** mcp-deidentify added — HIPAA Safe Harbor Stage 0 preprocessing.
> 19 custom servers (127 tools). PAT003 (preventive CVD) validated April 23, 2026.
> See [ROADMAP.md](../../ROADMAP.md) for full version history.

## The Problem

Standard HGSOC workup (BRCA1/2, HRD panel, CT imaging) generates no immunotherapy hypotheses. Manual multi-modal analysis across genomics, spatial transcriptomics, imaging, and clinical data takes an estimated 40 hours and $6,000-9,000 per patient -- making integrated analysis clinically impractical.

## The Platform

A 19-server MCP architecture orchestrated by AI (Claude + Gemini) executes automated multi-modal analysis pipelines: all patients first pass through Stage 0 de-identification (mcp-deidentify), then oncology patients follow a 5-stage workflow (Data Acquisition → Spatial Deconvolution → Target Profiling → Causal Inference → Report); preventive health patients use a parallel cardiometabolic risk-stratification workflow.

All tools accessible via natural language. Every AI result requires **clinician APPROVE/REVISE/REJECT**. HIPAA-compliant architecture with Safe Harbor de-identification and 10-year audit trails.

**Metrics:** 40 hours -> 2-5 hours (production), ~$324-702/patient vs $6,000-9,000 traditional. See [Value Proposition](../reference/shared/value-proposition.md) for details.

**Servers:** 19 custom (127 tools) + 6 external connectors — see [Server Registry](../reference/shared/server-registry.md) for current counts.

---

## Key Findings (PatientOne -- Synthetic HGSOC)

Three treatment hypotheses unreachable by standard workup:

1. **Personalized neoantigen vaccine** -- TP53 R175H generates RMPEAAPPV peptide (IC50 7.8 nM via netMHCpan), strong HLA-A*02:01 binding
2. **NNMT/CAF inhibition** -- 18.2% CAF fraction; GEARS predicts NNMT knockdown reduces STAT3/COL3A1 signaling, recovers PRF1/FOXP3 immune markers
3. **Convergent checkpoint blockade** -- POLE-corrected TMB 47.3 mut/Mb + spatial CD8 exclusion pattern -> anti-PD-1/CTLA-4 combination rationale

Plus: cross-cancer validation on PAT002 (ER+ breast cancer) with zero code changes.

Clinical details: [PatientOne Profile](../reference/shared/patientone-profile.md)

---

## Investment Tiers

| Tier | Investment | Deliverable | Timeline |
|------|-----------|-------------|----------|
| **Pilot** | $50,000 | 3 production servers, 100 patients, training | 6 months |
| **Production** | $75,000/year | Full 19-server deployment, Epic FHIR, 500 patients | 12 months |
| **Multi-Site** | $150,000 | 3-5 hospitals, IRB protocol, publication support | 18 months |

Projected annual savings: ~$313K (100 patients) to ~$1.6M (500 patients). Modeled, pending clinical validation.

---

## Specific Aims Template (for NIH R21 / Foundation Grants)

**Aim 1 -- Validate Clinical Utility:** Retrospective analysis of 100 ovarian cancer patients. Compare platform recommendations vs. actual clinical decisions. Target: >=80% concordance with molecular tumor board.

**Aim 2 -- Assess Scalability:** Prospective 500-patient cohort over 12 months. Track compute costs, analysis time, clinician satisfaction. Validate modeled $3,137/patient savings.

**Aim 3 -- HIPAA Infrastructure:** Epic FHIR integration, Safe Harbor de-identification, 10-year audit logging, institutional security audit.

---

## Validation Status

Three synthetic patients validated end-to-end (no dry_run), April 2026:

| Patient | Use Case | Key Finding |
|---|---|---|
| PAT001 | HGSOC Stage IV | 3 investigational hypotheses (neoantigen vaccine, NNMT/CAF inhibition, convergent checkpoint blockade) |
| PAT002 | ER+ breast cancer | PARP eligibility via germline BRCA2 despite HRD 35 < myChoice threshold |
| PAT003 | Preventive CVD | 3 evidence gaps missed by standard lipid panel + Helix Tier 1 genetic screen: Lp(a), APOE, CAC score |

Real patient data validation (30–50 patients, matched clinical outcomes) is the proposed next step.

---

## Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| Technical | LOW | Auto-scaling, comprehensive error handling, 223+ tests |
| Compliance | LOW | Built-in de-identification, audit logging, VPC isolation |
| AI Vendor | MEDIUM | Dual-provider (Claude + Gemini), MCP servers are provider-agnostic |
| Adoption | MEDIUM-HIGH | Phased rollout, Streamlit UI for clinicians, Jupyter for bioinformaticians |

---

**Contact:** Lynn Langit
**Status:** Ready for Funding Review
**See also:** [Demo & Pitch](DEMO_AND_PITCH.md) | [Value Proposition](../reference/shared/value-proposition.md) | [Server Registry](../reference/shared/server-registry.md)
