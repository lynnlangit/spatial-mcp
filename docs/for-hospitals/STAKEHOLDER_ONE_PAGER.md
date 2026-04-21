# HGSOC Precision Oncology Platform -- Stakeholder Summary

## The problem
High-Grade Serous Ovarian Cancer (HGSOC) is the deadliest gynecologic cancer, with
five-year survival below 50%. Treatment decisions today rely on limited genomic panels
and clinical intuition. No integrated AI platform exists to synthesize genomic, spatial,
immune, and drug response data at the point of care.

## What this platform does
- Analyzes tumor genomics, spatial architecture, immune infiltration, and drug response prediction in a single automated workflow
- Generates a structured oncologist-ready report in under five minutes per patient
- Operates on de-identified data with HIPAA-aligned audit logging and a fully open-source codebase

## What we demonstrated
Using a synthetic patient (PAT001), the platform correctly identified high DNA repair
deficiency (HRD = 72), strong immune recognition potential (IC50 = 7.8 nM), and immune
cell infiltration (30 CD8+ T cells), generating a therapeutic hypothesis consistent with
published HGSOC treatment guidelines -- fully automated, under five minutes.

## What a 90-day POC looks like
- Days 1-30: Infrastructure setup and smoke testing with synthetic data
- Days 31-60: Blinded retrospective review of 10 de-identified HGSOC cases
- Days 61-90: Concordance analysis, HIPAA gap closure, go/no-go decision

Full runbook: docs/for-hospitals/POC_RUNBOOK.md

## What it costs
Compute: approximately 97 GB RAM, 52 CPU cores (on-premise).
API: approximately $1-2 per full 18-server analysis (Claude API).
Personnel: approximately 78 hours setup, 25 hours per month ongoing.
Full estimates: docs/for-hospitals/RESOURCE_ESTIMATES.md

## What we need from you
- Compute infrastructure meeting minimum specs (see RESOURCE_ESTIMATES.md)
- One bioinformatician and three oncologist champions available for 90 days
- Access to 10 de-identified retrospective HGSOC cases from the tumor board

## Contact
{{CONTACT_NAME}}
{{CONTACT_EMAIL}}

---
*Open-source. Apache 2.0 license. https://github.com/lynnlangit/precision-medicine-mcp*
