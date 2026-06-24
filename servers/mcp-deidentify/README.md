# mcp-deidentify

HIPAA-aligned de-identification server for Precision Medicine MCP -- Stage 0 preprocessing.
Detects PII via Claude Haiku, replaces it with deterministic anonymization codes, and validates
the result through a three-layer audit. All tools default to `DRY_RUN=true` (synthetic data,
no API calls or disk I/O).

## Tools (6)

| Tool | Description |
|------|-------------|
| `deidentify_json` | De-identify a JSON clinical record (recursive string-leaf scan) |
| `deidentify_text` | De-identify plain text or DOCX content |
| `deidentify_pdf` | Extract text from PDF (pdfplumber) and de-identify |
| `deidentify_genomics_file` | Scrub PII from VCF/h5ad/CNS headers (data rows untouched) |
| `generate_anonymization_key` | Retrieve or initialise the anonymization key for a patient |
| `validate_deidentification` | Three-layer validation: Haiku red-team, regex sweep (9 patterns), key reverse lookup |

## Architecture

```
engine.py            Haiku-based PII extraction + chunked text processing
code_generator.py    Deterministic code assignment (SHA-256 seeded counters)
key_manager.py       Disk-persisted anonymization key per patient
validator.py         Three-layer post-deidentification audit

format_handlers/
  json_handler.py    Recursive JSON dict walker
  text_handler.py    Plain text + DOCX (python-docx)
  pdf_handler.py     PDF text extraction (pdfplumber)
  genomics_handler.py VCF headers, h5ad .uns, CNS comment lines
```

## Quick start

```bash
cd servers/mcp-deidentify
uv pip install -e ".[dev]"
uv run pytest -v            # 73 tests (1 skipped without ANTHROPIC_API_KEY)
```

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DEIDENTIFY_DRY_RUN` | `true` | Return synthetic fixtures; no API calls or file I/O |
| `ANTHROPIC_API_KEY` | -- | Required when `DRY_RUN=false` for Haiku entity extraction |
| `DEIDENTIFY_KEY_DIR` | `data/patients` | Directory for anonymization key files |
| `DEIDENTIFY_OUTPUT_DIR` | `data/patients` | Directory for de-identified output files (DOCX) |
