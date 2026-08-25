# mcp-deidentify

**Stage 0 preprocessing server — HIPAA Safe Harbor de-identification for the Precision Medicine MCP Platform**

Runs before the 5-stage pipeline. Strips all 18 HIPAA Safe Harbor identifiers from clinical JSON records, DOCX/PDF documents, and genomics file headers (VCF, h5ad, CNS). Produces a coded patient record and a companion anonymization key stored separately from all pipeline data.

---

## Tools (6)

| Tool | Description |
|---|---|
| `deidentify_json` | De-identify a JSON clinical record. Recursively walks all string leaves, detects PII via Haiku LLM, replaces with deterministic codes (e.g. `Dr. ONC-001`, `FAC-002`). Writes anonymization key to disk. |
| `deidentify_text` | De-identify plain text (`source_format="txt"`) or a DOCX file (`source_format="docx"`). DOCX is written to `output_path`. |
| `deidentify_pdf_text` | Extract and de-identify the **text layer** of a PDF (page by page). Returns de-identified plain text; does not rewrite the PDF binary. Image-only/scanned PDFs have no text layer and return `status="no_text_layer"` rather than an empty result. |
| `deidentify_genomics_file` | De-identify headers only in VCF (`##` meta lines), h5ad (`.uns` fields), or CNS (`#` comment lines). Data rows are never modified. |
| `generate_anonymization_key` | Retrieve or initialize the anonymization key for a patient. Safe to call on new or existing patients. |
| `validate_deidentification` | Three-layer PII audit: (1) Haiku red-team prompt, (2) deterministic regex sweep (SSN, phone, email, dates, MRN, accession patterns), (3) anonymization key reverse lookup. All three must pass for `passed: true`. |

---

## Installation

```bash
cd servers/mcp-deidentify
uv pip install -e ".[dev]"

# Run tests (DRY_RUN mode — no API key needed)
uv run pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DEIDENTIFY_DRY_RUN` | `false` | When `true`, returns synthetic fixture data without calling Haiku. **Defaults to `false`**: for a de-identification server, fabricating output must be opt-in. |
| `DEIDENTIFY_DATE_POLICY` | `SAFE_HARBOR` | `SAFE_HARBOR` (no date elements except year, 45 CFR 164.514(b)(2)) or `LIMITED_DATA_SET` (full dates retained, 45 CFR 164.514(e), requires a data use agreement). Applied by both the `deidentify_*` tools and `validate_deidentification`. |
| `DEIDENTIFY_KEY_DIR` | `<repo_root>/data/patients` | Root directory for anonymization key files. Key for PAT004 → `{dir}/PAT004/PAT004_anonymization_key.json`. Absolute by default — not resolved against the process CWD. |
| `DEIDENTIFY_OUTPUT_DIR` | `data/patients` | Root directory for de-identified DOCX output files. |
| `ANTHROPIC_API_KEY` | — | Required when `DEIDENTIFY_DRY_RUN=false`. Haiku calls use `claude-haiku-4-5-20251001`. |

---

## Pipeline Position

```
[Source documents: JSON / DOCX / PDF / VCF / h5ad]
          │
          ▼
  Stage 0: mcp-deidentify          ← THIS SERVER
          │
          ├── PAT00X_complete_record.json  (de-identified)
          └── PAT00X_anonymization_key.json  (stored separately)
          │
          ▼
  Stage 1: mcp-epic / mcp-mockepic
  Stage 2: mcp-spatialtools
  Stage 3: mcp-multiomics / mcp-perturbation
  Stage 4: mcp-neoantigen / mcp-cibersortx
  Stage 5: mcp-patient-report
```

The anonymization key is never passed to Stages 1–5. Downstream servers see only coded identifiers.

---

## Example Claude Prompts

**Onboard a new patient record:**
```
Using mcp-deidentify, de-identify this patient JSON record for PAT005:
[paste JSON content]
```

**De-identify a clinical PDF:**
```
De-identify the PDF at data/patients/PAT005/intake.pdf for patient PAT005.
```

**De-identify genomics files:**
```
De-identify the VCF header at data/patients/PAT005/somatic.vcf for PAT005.
Then de-identify the h5ad .uns fields at data/patients/PAT005/spatial.h5ad.
```

**Validate a de-identified record:**
```
Run validate_deidentification on this text for PAT005 and confirm all three layers pass.
```

---

## DRY_RUN Mode

`DEIDENTIFY_DRY_RUN` defaults to **`false`**. This deliberately diverges from the repo-wide convention of defaulting DRY_RUN on: a de-identification tool that silently returns fabricated entities is a safety failure, not a safe default.

When `DEIDENTIFY_DRY_RUN=true`, tools return synthetic fixture data. No Haiku calls are made and no files are read from or written to disk. Such a response is marked three ways, so that code ignoring metadata still cannot consume it by accident:

- `"status": "SYNTHETIC_DRY_RUN"` and `"dry_run": true`
- every **server-generated** string prefixed `SYNTHETIC:` (caller-supplied echo fields — `patient_id`, `file_type`, `source_format` — are left intact so downstream dispatch keeps working)
- the usual `_DRY_RUN_WARNING` / `_message` banner

### DRY_RUN is all-or-nothing per tool

`validate_deidentification` cannot run its Haiku red-team layer in DRY_RUN. Rather than let the remaining two layers imply a verdict, it returns:

```json
{
  "status": "unavailable_in_dry_run",
  "passed": null,
  "confidence": null,
  "layers_skipped": ["haiku_red_team"],
  "residual_pii_found": [ ... ]
}
```

`passed` is **never** `true` when any layer was skipped. Hits from the layers that did run are still reported — they are real findings — but their absence does not mean the content is clean. The same shape (`status: "incomplete"`) is returned if the Haiku call fails at runtime.

### Extraction failures

An empty entity list means **"this text contains no PII"** — a finding. It never means "extraction did not run". Conflating the two is what makes a de-identifier hand back the original document as though it had been redacted, so every failure path in the engine raises `ExtractionFailure` instead of returning `[]`:

- the `anthropic` package is missing
- Haiku returns malformed JSON (previously: chunk skipped, its PII silently dropped)
- any API or transport error
- retries exhausted after rate limiting

**Extraction is all-or-nothing per document.** One failed chunk fails the whole document; a partial result would redact some chunks and leave others untouched while still presenting as a completed de-identification.

At the tool boundary this becomes:

```json
{
  "status": "extraction_failed",
  "error": "Haiku returned malformed JSON: ...",
  "patient_id": "PAT004",
  "_SAFETY_NOTE": "PII extraction did not complete. NO de-identified content is returned. ..."
}
```

The envelope carries **no** `deidentified`, `deidentified_text`, `deidentified_content` or `extracted_text` key. On failure the source is unmodified, so returning it under a name asserting it is safe would be the original defect wearing an error message.

---

## Security Notes

- **No real PII in the repo.** All test fixtures use synthetic data.
- **Anonymization key separation.** The key file is written to `DEIDENTIFY_KEY_DIR`, never embedded in the de-identified record, and never passed downstream.
- **Deterministic codes.** The same `(patient_id, entity_type, entity_text)` triple always produces the same code, making re-runs idempotent.
- **Extraction failure is never silent.** A failed Haiku call aborts the whole document rather than skipping a chunk. See [Extraction failures](#extraction-failures) below.

---

## Dependencies

| Package | Purpose |
|---|---|
| `fastmcp>=2.13.0` | MCP server framework |
| `anthropic>=0.30.0` | Haiku LLM calls (entity extraction) |
| `pydantic>=2.0.0` | Schema models |
| `python-docx>=1.1.0` | DOCX paragraph extraction and rewrite |
| `pdfplumber>=0.11.0` | PDF text extraction per page |
| `anndata>=0.10.0` | h5ad `.uns` field access |

---

**Stage 0 of 5** | **FastMCP** | **Python 3.11+** | **uv**
