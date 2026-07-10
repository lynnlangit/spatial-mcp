# MCP Patient Report Server

Generate patient-facing precision oncology reports from multi-modal analysis results.

## Overview

This MCP server transforms complex genomic, spatial, and clinical analysis results into plain-language summaries that patients can:
- Take home after appointments
- Share with family members
- Reference between visits
- Use to prepare questions for their care team

**Key Features:**
- Structured `PatientReportData` model for type-safe report generation
- Jinja2 templates for customizable HTML output
- WeasyPrint PDF generation with print-optimized styling
- Clinician review gate (draft watermark until approved)
- White-label support for hospital branding
- Health literacy compliant (6th-8th grade reading level target)

## Installation

**Requires:** Python 3.11+

> **Standard setup:** See [Server Installation Guide](../../docs/reference/shared/server-installation.md) for venv creation, pip install, and Claude Desktop config.

### PDF Generation (Optional)

For PDF output, WeasyPrint requires system libraries:

**macOS:**
```bash
brew install pango libffi
pip install weasyprint
```

**Ubuntu/Debian:**
```bash
apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
pip install weasyprint
```

If WeasyPrint is not installed, the server will fall back to HTML output.

## MCP Tools

### `generate_patient_report`

Generate a patient-facing summary report from analysis results.

```python
result = await generate_patient_report(
    report_data_json='{"patient_info": {...}, ...}',
    report_type="full",      # "full", "onepage", or "clinical"
    output_format="pdf"      # "pdf" or "html"
)
```

**Input:** JSON string conforming to `PatientReportData` schema.

**Output:** PDF or HTML file with plain-language patient summary.

### `validate_report_data`

Validate report data JSON without generating output.

```python
result = await validate_report_data('{"patient_info": {...}}')
if result["valid"]:
    # Proceed with generation
```

### `approve_patient_report`

Mark a draft report as clinician-reviewed (removes watermark).

```python
result = await approve_patient_report(
    report_file_path="/reports/PAT001_full_report_DRAFT.pdf",
    reviewer_name="Dr. Jane Smith"
)
```

### `get_report_template_schema`

Get the full JSON schema for `PatientReportData`.

### `check_pdf_capability`

Check if PDF generation is available.

## XAI Metadata

`generate_patient_report` accepts an optional `xai_collection_json` parameter containing per-tool XAI metadata from upstream oncology servers. When provided, the report includes an `evidence_strength_summary` with a formatted evidence table, confidence counts, lowest-confidence flags, and action-required items.

## PatientReportData Schema

The LLM constructs this JSON from conversation context:

```json
{
  "patient_info": {
    "name": "Sarah Anderson",
    "age": 58,
    "sex": "Female",
    "patient_id": "PAT001-OVC-2025",
    "diagnosis": "Stage IV Ovarian Cancer"
  },
  "diagnosis_summary": {
    "cancer_type": "Ovarian Cancer",
    "subtype": "High-Grade Serous Carcinoma",
    "stage": "Stage IV",
    "plain_language_description": "...",
    "key_positive_factors": ["..."],
    "key_challenges": ["..."]
  },
  "genomic_findings": [
    {
      "gene": "BRCA1",
      "variant": "Pathogenic germline mutation",
      "significance": "Pathogenic",
      "plain_language": "You carry a BRCA1 mutation...",
      "actionability": "PARP inhibitors available",
      "icon": "positive"
    }
  ],
  "treatment_options": [...],
  "monitoring_plan": {
    "schedule": [...],
    "warning_signs": [...]
  },
  "spatial_findings": {...},      // Optional
  "histology_findings": {...},    // Optional
  "clinical_trials": [...],       // Optional
  "family_implications": {...},   // Optional
  "support_resources": [...]      // Optional
}
```

See `tests/fixtures/pat001_report_data.json` for a complete example.

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PATIENT_REPORT_DRY_RUN` | `true` | Simulate report generation |
| `PATIENT_REPORT_OUTPUT_DIR` | `./reports` | Output directory for generated files |
| `PATIENT_REPORT_TEMPLATES_DIR` | Auto-detected | Custom templates directory |

## Health Literacy Guidelines

When the LLM generates plain-language text for reports, it should follow these guidelines:

1. **Target 6th-8th grade reading level** (Flesch-Kincaid)
2. **Define medical terms on first use** (e.g., "BRCA1, a gene that helps repair DNA")
3. **Use analogies** (e.g., "PARP inhibitors remove the backup repair crew from cancer cells")
4. **Positive framing where honest** (e.g., "Your BRCA1 status means you're eligible for targeted therapy")
5. **Explicit uncertainty** (e.g., "Approximately 60% of patients respond to this therapy")
6. **Never omit the disclaimer** that a clinician must review

## Clinician Review Gate

Reports are NEVER delivered directly to patients without clinician review:

1. Reports generate with `status: "preliminary"` and "DRAFT" watermark
2. Clinician reviews report content
3. Clinician calls `approve_patient_report` tool
4. Approved report generated without watermark, `status: "current"`
5. Both versions preserved for audit trail

## Testing

```bash
cd servers/mcp-patient-report
pip install -e ".[dev]"
pytest tests/
```

## Directory Structure

```
servers/mcp-patient-report/
├── src/mcp_patient_report/
│   ├── models/
│   │   └── patient_report.py    # Pydantic data models
│   ├── report/
│   │   ├── report_generator.py  # Jinja2 template engine
│   │   └── report_pdf.py        # WeasyPrint PDF generation
│   └── server.py                # MCP server with tools
├── tests/
│   ├── fixtures/
│   │   └── pat001_report_data.json
│   ├── test_models.py
│   └── test_report_generator.py
└── README.md
```

Templates are bundled with the package at `src/mcp_patient_report/templates/`

## Example Workflow

```
1. Complete multi-modal analysis (clinical, genomic, spatial, imaging)
2. LLM constructs PatientReportData JSON with plain-language explanations
3. Call validate_report_data to check structure
4. Call generate_patient_report to create draft PDF
5. Clinician reviews draft
6. Call approve_patient_report to finalize
7. Patient receives approved report
```

## License

Apache 2.0
