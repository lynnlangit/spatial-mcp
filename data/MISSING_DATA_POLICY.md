# Missing Data Policy

**MCP Precision Medicine Platform**
*All patient data in this repository is synthetic (SYNTHETIC_DATA mode). Not for clinical use.*

---

## Design Principle: Explicit Gaps, Not Silent Imputation

The platform is designed to **flag missing data as gaps**, not to fill them with inferred or population-mean values. When a required data element is absent from a patient record, the platform:

1. Records the absence in the session provenance log
2. Proceeds with the data that is present
3. Surfaces the missing element as an **actionable output** (a recommendation to obtain the data)

This contrasts with many clinical decision-support models that silently substitute population averages for missing inputs, which can create false confidence and obscure data quality differences between patients.

---

## PAT003 — Preventive Cardiovascular Health (Exemplar Case)

PAT003 illustrates this policy clearly.

**What was present (explicitly defined synthetic inputs):**

| Input | Value |
|---|---|
| Age | 67 |
| Sex | Female |
| LDL | 118 mg/dL |
| HDL | 58 mg/dL |
| Blood pressure | 138/84 mmHg |
| hsCRP | 1.8 mg/L |
| Smoking status | Non-smoker |
| Diabetes | No |

**What was absent (flagged as gaps, NOT imputed):**

| Missing Data Element | Clinical Significance | Why Absent |
|---|---|---|
| Lp(a) serum level | Genetically determined, statin-unresponsive independent CVD risk factor; 2023 ESC/EAS guidelines recommend one lifetime measurement | Not in synthetic record |
| APOE genotype | Strongest common genetic determinant of CVD and Alzheimer's risk; absent from all population screening panels | Not in synthetic record |
| Coronary artery calcium (CAC) score | Best-validated reclassification tool at intermediate risk (7.5–20%); endorsed by 2018 ACC/AHA guidelines | Not in synthetic record |

**Platform behaviour:** All three CVD risk scores (Reynolds 14.3%, Framingham 12.0%, ASCVD 10.3%) were computed solely from the inputs present. The three absent elements were returned as the platform's primary actionable output — recommendations to obtain these tests — rather than as estimated values.

---

## PAT002 — ER+/HER2− Invasive Ductal Carcinoma (Oncology Exemplar)

PAT002 illustrates the same policy in the oncology arm.

**Deferred server: mcp-fgbio (FASTQ QC and UMI extraction)**

PAT002 had no FASTQ file associated with the case (tumour NGS was provided as a pre-processed VCF). The fgbio server, which validates raw sequencing quality and extracts UMIs, was therefore deferred rather than skipped silently. This deferral was recorded in the session provenance log with the reason `NO_FASTQ_AVAILABLE`. All downstream variant calling and HRD scoring proceeded from the VCF inputs that were present.

**Implication:** The absence of FASTQ-level QC means that sequencing artefacts cannot be fully ruled out at the raw read level. This is flagged as a limitation in the platform paper (Section 3.5), not hidden.

---

## Prospective Deployment Guidance

If this platform is adapted for use with real EHR data, the following rules apply:

**Rule 1 — Never impute silently.** Any input value not present in the source record must be either (a) explicitly requested from an integrated data source, or (b) flagged as absent in the report output. Population-mean substitution is not permitted.

**Rule 2 — Scale output confidence to data completeness.** Report sections that depend on absent data should carry an explicit caveat. Risk scores computed without Lp(a), APOE, or CAC should state this in the report.

**Rule 3 — Log all deferrals.** Every server that is skipped or deferred must write a structured log entry containing: server name, patient ID, reason for deferral, timestamp, and the data element that was absent.

**Rule 4 — Surface gaps as recommendations, not failures.** A missing data element is not a pipeline error. It is clinical information — a signal that a specific test has not been performed. The platform should route these to the patient report as clinical action items.

**Rule 5 — Quantum and experimental servers.** The quantum cell-type fidelity server (mcp-quantum-celltype-fidelity) is classified as a convergent validation layer, not a primary discovery tool. If the server is unavailable (e.g., pending restart), the platform proceeds using conventional spatial analysis (Moran's I) as the primary classification and notes the quantum layer as pending. This is demonstrated by the PAT002 quantum deferral recorded in the session log as `QUANTUM_PENDING_SERVER_RESTART`.

---

## Summary Table

| Patient | Missing Element | Platform Response |
|---|---|---|
| PAT003 | Lp(a), APOE, CAC | Flagged as evidence gaps; returned as clinical recommendations |
| PAT002 | FASTQ (raw sequencing) | fgbio server deferred; logged; downstream analysis proceeded from VCF |
| PAT002 | Quantum fidelity (initial run) | Server pending restart; logged as `QUANTUM_PENDING_SERVER_RESTART`; Moran's I used as primary classification |
| PAT001 | None | All data present; full pipeline executed |

---

*This policy document is part of the MCP Precision Medicine Platform repository. For questions, contact the platform maintainer.*
