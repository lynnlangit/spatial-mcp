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
| Patient report PDF finalization | Medium | S | Template approval | Partial |
| Conference submission (AACR or AMIA) | Medium | M | No deadline set | Planned |
| Educator glossary validation by domain expert | Medium | S | Educator contact | Planned |
| Add metabolomics server (LC-MS integration) | Medium | L | Metabolomics data | Planned |
| Federated learning across hospital deployments | Low | XL | Multiple hospital partners | Planned |
| DICOM/radiology image integration | Medium | L | PACS access | Planned |
| PAT002 breast cancer validation dataset | Medium | M | Synthetic data generation | Planned |
| Automated CI regression test against PAT001 canonical values | Medium | S | CI infrastructure | Planned |
| Multi-language patient report (Spanish, Mandarin) | Low | M | Translation resources | Planned |
| Cardiometabolic server (lipid panel + CVD risk scoring + Lp(a) + biomarker tracking) | High | M | PAT003 gap report v3 | **Done** |
| Cardiovascular polygenic risk score server | High | M | PAT003 data design | Planned |
| Longitudinal biomarker tracking server | Medium | M | PAT003 use case | Planned |
| Lifestyle intervention evidence server (literature-based) | Medium | L | PAT003 use case | Planned |

## Version history

| Version | Date | Summary |
|---------|------|---------|
| v17 | April 2026 | Server #19 cardiometabolic added — Reynolds/Framingham/ASCVD risk scoring for women, biomarker panels, Lp(a) assessment, preventive reports; PAT003 e2e 16/16 useful calls; PAT003 live validation April 23, 2026 (no dry\_run): Reynolds 14.3% / Framingham 12.0% / ASCVD 10.3%; 19 custom servers (104 tools); platform paper needs v17 update |
| v16 | April 17, 2026 | FastMCP 2.x upgrade complete; all servers (see `docs/reference/shared/server-registry.md` for current count) pass live PAT001 e2e (no DRY\_RUN); GEARS perturbation pipeline fully validated; quantum CPU fallback fixed; MHC1 multi-peptide stale variable fixed |
| v15 | March 27, 2026 | Initial quantum + GEARS integration; spatial and deconvolution servers added |

*(Run `git log --oneline` to find earlier versions and add them here.)*
