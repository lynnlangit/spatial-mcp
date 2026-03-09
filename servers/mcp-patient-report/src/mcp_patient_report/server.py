"""
MCP Patient Report Server

Generates patient-facing precision oncology reports from analysis results.
Provides tools for creating plain-language summaries that patients can
take home, share with family, or reference between appointments.

Key features:
- Structured PatientReportData model for type-safe report generation
- Jinja2 templates for customizable HTML output
- WeasyPrint PDF generation with print-optimized styling
- Clinician review gate (draft watermark until approved)
- White-label support for hospital branding
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastmcp import FastMCP
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse

from .models import PatientReportData, ReportMetadata
from .report.report_generator import ReportGenerator
from .report.report_pdf import get_pdf_generator, WEASYPRINT_AVAILABLE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
mcp = FastMCP("patient-report")

# Configuration from environment
DRY_RUN = os.getenv("PATIENT_REPORT_DRY_RUN", "true").lower() == "true"
OUTPUT_DIR = Path(os.getenv("PATIENT_REPORT_OUTPUT_DIR", "./reports"))
TEMPLATES_DIR = os.getenv("PATIENT_REPORT_TEMPLATES_DIR", None)

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# --- HTTP download endpoint for generated reports ---
@mcp.custom_route("/download/{filename}", methods=["GET"])
async def download_report(request: Request) -> FileResponse | JSONResponse:
    """Serve generated report files for download."""
    filename = request.path_params["filename"]
    # Prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        return JSONResponse({"error": "Invalid filename"}, status_code=400)
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return JSONResponse({"error": "File not found"}, status_code=404)
    media_type = "application/pdf" if file_path.suffix == ".pdf" else "text/html"
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type=media_type,
    )


def _get_report_generator() -> ReportGenerator:
    """Get configured report generator."""
    if TEMPLATES_DIR:
        candidate = Path(TEMPLATES_DIR)
        # Only use the env var path if it actually exists; otherwise fall back
        # to the package-bundled templates directory.
        templates_dir = candidate if candidate.is_dir() else None
    else:
        templates_dir = None
    return ReportGenerator(templates_dir)


def _get_pdf_generator():
    """Get configured PDF generator."""
    return get_pdf_generator(OUTPUT_DIR)


@mcp.tool()
async def generate_patient_report(
    report_data_json: str,
    report_type: str = "full",
    output_format: str = "pdf",
) -> dict:
    """
    Generate a patient-facing summary report from analysis results.

    This tool creates plain-language reports suitable for patients to take home,
    share with family, or reference between appointments. Reports include:
    - Diagnosis explanation in simple terms
    - Genomic findings with actionability
    - Treatment options with evidence levels
    - Monitoring plan and warning signs
    - Support resources

    The LLM should construct the PatientReportData JSON from conversation context,
    following health literacy guidelines (6th-8th grade reading level).

    Args:
        report_data_json: JSON string containing PatientReportData structure.
            Must include: patient_info, diagnosis_summary, genomic_findings,
            treatment_options, monitoring_plan.
            Optional: spatial_findings, histology_findings, clinical_trials,
            family_implications, support_resources.

        report_type: Type of report to generate:
            - "full": Comprehensive multi-page report (default)
            - "onepage": Quick reference one-page summary

        output_format: Output format:
            - "pdf": PDF document (default, requires WeasyPrint)
            - "html": HTML file (fallback if PDF not available)

    Returns:
        Dictionary with:
        - status: "success" or "error"
        - file_path: Path to generated report file
        - report_type: Type of report generated
        - output_format: Actual output format used
        - is_draft: Whether report has draft watermark
        - patient_id: Patient identifier from report
        - message: Human-readable status message

    Example:
        >>> result = await generate_patient_report(
        ...     report_data_json='{"patient_info": {...}, ...}',
        ...     report_type="full",
        ...     output_format="pdf"
        ... )
        >>> print(result["file_path"])
        /reports/PAT001-OVC-2025_full_report_DRAFT_20260207.pdf
    """
    try:
        # Parse and validate JSON
        try:
            report_dict = json.loads(report_data_json)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "error": f"Invalid JSON: {str(e)}",
                "suggestion": "Ensure report_data_json is valid JSON"
            }

        # Validate against Pydantic model
        try:
            report_data = PatientReportData(**report_dict)
        except ValidationError as e:
            return {
                "status": "error",
                "error": f"Validation failed: {str(e)}",
                "suggestion": "Check that all required fields are present and correctly typed"
            }

        # DRY_RUN mode - return synthetic response
        if DRY_RUN:
            file_name = f"{report_data.patient_info.patient_id}_{report_type}_report_DRAFT.pdf"
            return {
                "status": "DRY_RUN",
                "message": "Report generation simulated (DRY_RUN mode). "
                           "No PDF was created. Set PATIENT_REPORT_DRY_RUN=false to generate a real report.",
                "file_path": str(OUTPUT_DIR / file_name),
                "file_name": file_name,
                "download_url": None,  # Not available in DRY_RUN mode
                "report_type": report_type,
                "output_format": output_format,
                "is_draft": True,
                "patient_id": report_data.patient_info.patient_id,
                "validation": "PatientReportData validated successfully",
                "sections_included": {
                    "genomic_findings": len(report_data.genomic_findings),
                    "treatment_options": len(report_data.treatment_options),
                    "clinical_trials": len(report_data.clinical_trials),
                    "support_resources": len(report_data.support_resources),
                    "has_spatial": report_data.spatial_findings is not None,
                    "has_histology": report_data.histology_findings is not None,
                    "has_family_implications": report_data.family_implications is not None,
                }
            }

        # Generate HTML report
        generator = _get_report_generator()
        html_content = generator.render(report_data, report_type)

        # Generate PDF or HTML output
        pdf_generator = _get_pdf_generator()
        is_draft = report_data.metadata.report_status == "preliminary"

        output_path = pdf_generator.generate_report_pdf(
            html_content=html_content,
            patient_id=report_data.patient_info.patient_id,
            report_type=report_type,
            is_draft=is_draft,
        )

        # Determine actual output format
        actual_format = "pdf" if output_path.suffix == ".pdf" else "html"

        # Build download URL (served by the /download/ custom route)
        port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))
        base_url = os.getenv("MCP_BASE_URL", f"http://localhost:{port}")
        download_url = f"{base_url}/download/{output_path.name}"

        return {
            "status": "success",
            "file_path": str(output_path),
            "file_name": output_path.name,
            "download_url": download_url,
            "report_type": report_type,
            "output_format": actual_format,
            "is_draft": is_draft,
            "patient_id": report_data.patient_info.patient_id,
            "message": f"Report generated successfully: {output_path.name}",
            "sections_included": {
                "genomic_findings": len(report_data.genomic_findings),
                "treatment_options": len(report_data.treatment_options),
                "clinical_trials": len(report_data.clinical_trials),
                "support_resources": len(report_data.support_resources),
            }
        }

    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": str(e),
            "suggestion": "Check that templates directory exists"
        }
    except Exception as e:
        logger.exception("Error generating report")
        return {
            "status": "error",
            "error": str(e),
            "suggestion": "Check logs for details"
        }


@mcp.tool()
async def approve_patient_report(
    report_file_path: str,
    reviewer_name: str,
    review_notes: Optional[str] = None,
) -> dict:
    """
    Approve a draft patient report after clinician review.

    This tool marks a draft report as reviewed and approved, removing the
    draft watermark and updating the report status. The original draft is
    preserved for audit purposes.

    IMPORTANT: Reports should NEVER be shared with patients without clinician
    review and approval through this tool.

    Args:
        report_file_path: Path to the draft report file
        reviewer_name: Name of the clinician who reviewed the report
        review_notes: Optional notes from the review

    Returns:
        Dictionary with:
        - status: "success" or "error"
        - original_file: Path to original draft (preserved)
        - approved_file: Path to approved report (watermark removed)
        - reviewer: Name of reviewer
        - review_date: Date/time of approval
        - message: Human-readable status message

    Example:
        >>> result = await approve_patient_report(
        ...     report_file_path="/reports/PAT001_full_report_DRAFT.pdf",
        ...     reviewer_name="Dr. Jane Smith",
        ...     review_notes="Reviewed genomic findings, treatment plan appropriate"
        ... )
    """
    if DRY_RUN:
        return {
            "status": "DRY_RUN",
            "message": "Report approval simulated (DRY_RUN mode)",
            "original_file": report_file_path,
            "approved_file": report_file_path.replace("_DRAFT", "_APPROVED"),
            "reviewer": reviewer_name,
            "review_date": datetime.now().isoformat(),
            "review_notes": review_notes,
        }

    # In a full implementation, this would:
    # 1. Load the original report data
    # 2. Update metadata with reviewer info and status="current"
    # 3. Re-generate report without draft watermark
    # 4. Preserve original draft for audit trail
    # 5. Return paths to both files

    return {
        "status": "not_implemented",
        "message": "Full approval workflow not yet implemented. "
                   "This would regenerate the report without draft watermark "
                   "and update FHIR DocumentReference status.",
        "original_file": report_file_path,
        "reviewer": reviewer_name,
        "review_date": datetime.now().isoformat(),
    }


@mcp.tool()
async def validate_report_data(
    report_data_json: str,
) -> dict:
    """
    Validate PatientReportData JSON without generating a report.

    Use this tool to check that report data is correctly structured
    before calling generate_patient_report.

    Args:
        report_data_json: JSON string to validate

    Returns:
        Dictionary with:
        - valid: Boolean indicating if data is valid
        - errors: List of validation errors (if any)
        - warnings: List of warnings (missing optional fields)
        - summary: Summary of report contents

    Example:
        >>> result = await validate_report_data('{"patient_info": {...}}')
        >>> if result["valid"]:
        ...     await generate_patient_report(report_data_json)
    """
    try:
        report_dict = json.loads(report_data_json)
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "errors": [f"Invalid JSON: {str(e)}"],
            "warnings": [],
            "summary": None,
        }

    try:
        report_data = PatientReportData(**report_dict)

        # Check for missing optional but recommended fields
        warnings = []
        if not report_data.spatial_findings:
            warnings.append("No spatial findings included (optional)")
        if not report_data.histology_findings:
            warnings.append("No histology findings included (optional)")
        if len(report_data.clinical_trials) == 0:
            warnings.append("No clinical trials included (optional)")
        if len(report_data.support_resources) == 0:
            warnings.append("No support resources included (recommended)")
        if not report_data.family_implications:
            warnings.append("No family implications included (optional)")

        return {
            "valid": True,
            "errors": [],
            "warnings": warnings,
            "summary": {
                "patient_id": report_data.patient_info.patient_id,
                "patient_name": report_data.patient_info.name,
                "diagnosis": report_data.diagnosis_summary.cancer_type,
                "stage": report_data.diagnosis_summary.stage,
                "genomic_findings_count": len(report_data.genomic_findings),
                "treatment_options_count": len(report_data.treatment_options),
                "clinical_trials_count": len(report_data.clinical_trials),
                "has_spatial": report_data.spatial_findings is not None,
                "has_histology": report_data.histology_findings is not None,
                "report_status": report_data.metadata.report_status,
            }
        }

    except ValidationError as e:
        return {
            "valid": False,
            "errors": [err["msg"] for err in e.errors()],
            "warnings": [],
            "summary": None,
        }


@mcp.tool()
async def get_report_template_schema() -> dict:
    """
    Get the JSON schema for PatientReportData.

    Returns the complete schema showing all required and optional fields
    for constructing report data. Use this to understand the expected
    structure before building report JSON.

    Returns:
        Dictionary with:
        - schema: Full JSON schema for PatientReportData
        - required_sections: List of required top-level sections
        - optional_sections: List of optional sections
        - example: Example valid JSON structure

    Example:
        >>> schema = await get_report_template_schema()
        >>> print(schema["required_sections"])
        ['patient_info', 'diagnosis_summary', 'genomic_findings', ...]
    """
    schema = PatientReportData.model_json_schema()

    return {
        "schema": schema,
        "required_sections": [
            "patient_info",
            "diagnosis_summary",
            "genomic_findings",
            "treatment_options",
            "monitoring_plan",
        ],
        "optional_sections": [
            "spatial_findings",
            "histology_findings",
            "clinical_trials",
            "family_implications",
            "support_resources",
            "hospital_name",
            "hospital_logo_path",
        ],
        "example": PatientReportData.model_config.get("json_schema_extra", {}).get("example", {}),
    }


@mcp.tool()
async def check_pdf_capability() -> dict:
    """
    Check if PDF generation is available.

    WeasyPrint requires system libraries (libpango, libcairo, libgdk-pixbuf).
    This tool checks if PDF generation will work or fall back to HTML.

    Returns:
        Dictionary with:
        - pdf_available: Boolean
        - output_format: "pdf" or "html" (fallback)
        - message: Status message
        - install_instructions: How to enable PDF if not available
    """
    return {
        "pdf_available": WEASYPRINT_AVAILABLE,
        "output_format": "pdf" if WEASYPRINT_AVAILABLE else "html",
        "message": (
            "PDF generation available via WeasyPrint"
            if WEASYPRINT_AVAILABLE
            else "PDF generation not available. HTML output will be used instead."
        ),
        "install_instructions": (
            None if WEASYPRINT_AVAILABLE else
            "To enable PDF generation:\n"
            "1. Install system dependencies:\n"
            "   - macOS: brew install pango libffi\n"
            "   - Ubuntu: apt install libpango-1.0-0 libpangocairo-1.0-0\n"
            "2. Install WeasyPrint: pip install weasyprint\n"
            "See: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html"
        ),
        "output_dir": str(OUTPUT_DIR),
        "dry_run_mode": DRY_RUN,
    }


def main() -> None:
    """Run the MCP patient-report server."""
    logger.info("Starting mcp-patient-report server...")

    if DRY_RUN:
        logger.warning("=" * 80)
        logger.warning("DRY_RUN MODE ENABLED - Reports will be simulated")
        logger.warning("Set PATIENT_REPORT_DRY_RUN=false for real report generation")
        logger.warning("=" * 80)

    if not WEASYPRINT_AVAILABLE:
        logger.warning("WeasyPrint not available - PDF generation will fall back to HTML")

    # Get transport and port from environment
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    port = int(os.getenv("PORT", os.getenv("MCP_PORT", "8000")))

    # Run the server with appropriate transport
    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport, port=port, host="0.0.0.0")
    else:
        mcp.run(transport=transport)


if __name__ == "__main__":
    main()
