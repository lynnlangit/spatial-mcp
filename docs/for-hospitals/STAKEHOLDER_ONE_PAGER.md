# HGSOC Precision Oncology Platform -- Stakeholder Summary

## The problem

Standard clinical workup — whether for advanced cancer or preventive health — leaves actionable findings on the table. For High-Grade Serous Ovarian Cancer (HGSOC), no integrated platform exists to synthesize genomic, spatial, immune, and drug response data at the point of care. For preventive cardiovascular health, standard lipid panels and population genetic screens routinely miss the three tests (Lp(a), APOE genotype, CAC score) most likely to change statin management decisions.

## What this platform does
- Analyzes tumor genomics, spatial architecture, immune infiltration, and drug response prediction in a single automated workflow
- Generates a structured oncologist-ready report in a single automated session, rather than a multi-day relay across bioinformatics, pathology, and clinical informatics
- Operates on de-identified data with HIPAA-aligned audit logging and a fully open-source codebase

## What we demonstrated

Three synthetic patients, three independent live end-to-end validations — no dry_run:

| Patient | Condition | Key finding missed by standard workup |
|---|---|---|
| **PAT001** | HGSOC Stage IV | 3 investigational hypotheses: neoantigen vaccine (RMPEAAPPV IC50 7.8 nM), NNMT/CAF inhibition, convergent checkpoint blockade |
| **PAT002** | ER+/HER2− breast cancer | HRD 35 below myChoice threshold but PARP-eligible via BRCA2 germline — handled without code changes |
| **PAT003** | Preventive cardiovascular | 3 evidence gaps missed by standard lipid panel + Helix Tier 1 genetic screen: Lp(a), APOE genotype, CAC score; intermediate 10-yr CVD risk confirmed (Reynolds 14.3%) |

Each analysis ran as a single automated session producing a structured clinician-ready report. End-to-end runtime on synthetic data is 5-15 minutes across the full platform; runtime on real patient data is estimated at 2-5 hours, against an estimated 40 hours for the equivalent manual multi-modal analysis. Time figures are modeled and pending clinical validation — see [Value Proposition](../reference/shared/value-proposition.md).

## What a 90-day POC looks like
- Days 1-30: Infrastructure setup and smoke testing with synthetic data
- Days 31-60: Blinded retrospective review of 10 de-identified HGSOC cases
- Days 61-90: Concordance analysis, HIPAA gap closure, go/no-go decision

Full runbook: docs/for-hospitals/POC_RUNBOOK.md

## What it costs
Compute: approximately 93 GB RAM, 50 CPU cores (on-premise).
API: approximately $1-2 per full 19-server analysis (Claude API).
Personnel: approximately 78 hours setup, 25 hours per month ongoing.
Full estimates: docs/for-hospitals/RESOURCE_ESTIMATES.md

## What we need from you
- Compute infrastructure meeting minimum specs (see RESOURCE_ESTIMATES.md)
- One bioinformatician and three oncologist champions available for 90 days
- Access to 10 de-identified retrospective cases from the tumor board (HGSOC preferred for initial POC; ER+ breast cancer and preventive CVD use cases available for parallel tracks)

## Contact
*[Insert contact name and email before distribution]*

---
*Open-source. Apache 2.0 license. https://github.com/lynnlangit/precision-medicine-mcp*
