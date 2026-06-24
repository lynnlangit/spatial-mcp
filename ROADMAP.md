# ROADMAP

## Planned improvements

| Item | Priority | Effort | Depends on | Status |
|------|----------|--------|------------|--------|
| Replace synthetic GSE184880 with real TCGA HGSOC cohort | High | L | Data access agreement | Planned |
| Real EPIC FHIR R4 integration | High | L | Hospital partner | Planned |
| Multi-patient batch processing | High | M | Refactor patient context | Planned |
| External patient advocate review of docs/for-patients/ | High | S | Advocate contact | Planned |
| External HIPAA security audit | High | M | Hospital partner | Planned |
| Quantum server validation on real circuit hardware (IBM/IonQ) | Medium | L | Cloud account | Planned |
| scVI/scANVI batch-corrected atlas integration | Medium | M | Single-cell data | Planned |
| Patient report PDF finalization | Medium | S | Template approval | **Done** |
| Conference submission (AACR or AMIA) | Medium | M | No deadline set | **Done** (Mayo AI Summit poster) |
| Educator glossary validation by domain expert | Medium | S | Educator contact | Planned |
| Add metabolomics server (LC-MS integration) | Medium | L | Metabolomics data | Planned |
| Federated learning across hospital deployments | Low | XL | Multiple hospital partners | Planned |
| DICOM/radiology image integration | Medium | L | PACS access | Planned |
| PAT002 breast cancer validation dataset | Medium | M | Synthetic data generation | **Done** |
| Automated CI regression test against canonical values | Medium | S | CI infrastructure | Planned |
| Multi-language patient report (Spanish, Mandarin) | Low | M | Translation resources | Planned |
| Cardiometabolic server (lipid panel + CVD risk scoring + Lp(a) + biomarker tracking) | High | M | PAT003 gap report v3 | **Done** |
| HIPAA Safe Harbor de-identification server (JSON, DOCX, PDF, VCF, h5ad) | High | M | Stage 0 pipeline | **Done** |
| Cardiovascular polygenic risk score server | High | M | PAT003 data design | Planned |
| Longitudinal biomarker tracking server | Medium | M | PAT003 use case | Planned |
| Lifestyle intervention evidence server (literature-based) | Medium | L | PAT003 use case | Planned |

## Version history

| Version | Date | Summary |
|---------|------|---------|
| v19 | June 2026 | Server #20 mcp-deidentify added — Stage 0 HIPAA Safe Harbor de-identification (JSON, DOCX, PDF, VCF, h5ad); three-layer validation; missing data policy; CITL statement; Mayo AI Summit poster; 20 servers (110 tools) |
| v18 | May 2026 | Patient report examples updated; platform paper v18; PAT002/PAT003 prompt refinements |
| v17 | April–May 2026 | Server #19 cardiometabolic added — Reynolds/Framingham/ASCVD risk scoring, Lp(a), preventive reports; PAT003 live validation; PAT002 deep-stage validation — HLA typing, quantum immune evasion, 3 ER+ BC investigational hypotheses; 6 beyond-SOC hypotheses across 2 cancer types; platform paper v17; 19 servers (104 tools) |
| v16 | April 17, 2026 | FastMCP 2.x upgrade complete; all servers (see `docs/reference/shared/server-registry.md` for current count) pass live PAT001 e2e (no DRY\_RUN); GEARS perturbation pipeline fully validated; quantum CPU fallback fixed; MHC1 multi-peptide stale variable fixed |
| v15 | March 27, 2026 | Initial quantum + GEARS integration; spatial and deconvolution servers added |

*(Run `git log --oneline` to find earlier versions and add them here.)*
