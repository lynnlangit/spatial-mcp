# ROADMAP

Open work only. Completed items are removed rather than accumulated — the
**Version history** below records what shipped, and `git log` has the detail.

Status was verified against server code on 2026-08-25, not against the previous
edition of this file. Where an item's code already exists, that is stated.

## Planned improvements

| Item | Priority | Effort | Depends on | Status |
|------|----------|--------|------------|--------|
| Replace synthetic GSE184880 with real TCGA HGSOC cohort | High | L | Data access agreement | Planned |
| Point Epic FHIR at a live hospital instance | High | L | Hospital partner | **Code complete** — `mcp-epic` implements FHIR R4 over httpx with OAuth 2.0 token refresh and Safe Harbor de-identification. Untested against a real Epic endpoint. |
| Run the root `tests/` tree in CI | High | S | — | **Tests exist, CI does not run them.** The matrix only runs `servers/<name>` suites, so `tests/integration/` — including the 47-assertion CNV e2e regression and `test_pat003_e2e.py` — never executes on push. Closing this also closes canonical-value regression. |
| Multi-patient batch processing | High | M | Refactor patient context | Planned |
| External patient advocate review of docs/for-patients/ | High | S | Advocate contact | Planned |
| External HIPAA security audit | High | M | Hospital partner | Planned |
| Decide the `_call_haiku` partial-failure contract | Medium | S | — | Extraction now raises `ExtractionFailure` and the tool boundary returns `status="extraction_failed"`. Whether a partial failure should instead grade `NOT_ASSESSABLE` is still open. |
| Quantum server validation on real circuit hardware (IBM/IonQ) | Medium | L | Cloud account | Planned |
| scVI/scANVI batch-corrected atlas integration | Medium | M | Single-cell data | Planned |
| Educator glossary validation by domain expert | Medium | S | Educator contact | Planned |
| Add metabolomics server (LC-MS integration) | Medium | L | Metabolomics data | Planned |
| DICOM/radiology image integration | Medium | L | PACS access | Planned |
| Longitudinal biomarker tracking | Medium | M | PAT003 use case | Planned — `mcp-cardiometabolic` covers point-in-time panels (`assess_biomarker_panel`); trend tracking over time is the gap |
| Multi-language patient report (Spanish, Mandarin) | Low | M | Translation resources | Planned |
| Federated learning across hospital deployments | Low | XL | Multiple hospital partners | Planned |

## Version history

| Version | Date | Summary |
|---------|------|---------|
| v20 | August 2026 | Graded copy-number suite — 8 tools in mcp-genomic-results (library-chemistry gate, heterozygous-site extraction + QC, tumour purity, detectability, allelic imbalance with direction guard, architecture comparison, UM prognostic class), the shared `GradedResult` envelope, and patient-report placement governance; end-to-end CNV regression on a synthetic specimen; mcp-deidentify safety fixes (DRY_RUN defaults off, all-or-nothing validation, extraction failures no longer silent); doc-audit hardened with a self-test; 19 servers (127 tools at that release) |
| v19 | June 2026 | Server #19 mcp-deidentify added — Stage 0 HIPAA Safe Harbor de-identification (JSON, DOCX, PDF, VCF, h5ad); three-layer validation; missing data policy; CITL statement; Mayo AI Summit poster; 19 servers (110 tools at that release) |
| v18 | May 2026 | Patient report examples updated; platform paper v18; PAT002/PAT003 prompt refinements |
| v17 | April–May 2026 | Server #18 cardiometabolic added — Reynolds/Framingham/ASCVD risk scoring, Lp(a), preventive reports; PAT003 live validation; PAT002 deep-stage validation — HLA typing, quantum immune evasion, 3 ER+ BC investigational hypotheses; 6 beyond-SOC hypotheses across 2 cancer types; platform paper v17; 18 servers (104 tools at that release) |
| v16 | April 17, 2026 | FastMCP 2.x upgrade complete; all servers (see `docs/reference/shared/server-registry.md` for current count) pass live PAT001 e2e (no DRY\_RUN); GEARS perturbation pipeline fully validated; quantum CPU fallback fixed; MHC1 multi-peptide stale variable fixed |
| v15 | March 27, 2026 | Initial quantum + GEARS integration; spatial and deconvolution servers added |

*(Run `git log --oneline` to find earlier versions and add them here.)*
