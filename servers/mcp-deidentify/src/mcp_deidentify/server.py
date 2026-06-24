"""MCP De-identification server -- Stage 0 preprocessing for Precision Medicine MCP.

Phase 1: Engine and code generator only. Format handler tools are stubs.
Set DEIDENTIFY_DRY_RUN=false and ANTHROPIC_API_KEY to enable live Haiku calls.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("deidentify")

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _add_dry_run_warning  # noqa: E402
from common.transport import run_server as _run_server  # noqa: E402

DRY_RUN = os.getenv("DEIDENTIFY_DRY_RUN", "true").lower() == "true"


def add_dry_run_warning(result: Dict) -> Dict:
    return _add_dry_run_warning(result, dry_run=DRY_RUN, env_var="DEIDENTIFY_DRY_RUN")


# ---------------------------------------------------------------------------
# Phase 1 stubs -- tools not yet implemented
# ---------------------------------------------------------------------------


@mcp.tool()
async def deidentify_json(
    json_content: str,
    patient_id: str,
    code_map: Optional[Dict] = None,
) -> Dict[str, Any]:
    """[PHASE 2] De-identify a JSON clinical record.

    Not yet implemented. Raises NotImplementedError.
    """
    raise NotImplementedError("deidentify_json is implemented in Phase 2.")


@mcp.tool()
async def deidentify_text(
    text: str,
    patient_id: str,
    source_format: str = "txt",
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """[PHASE 3] De-identify plain text or DOCX content.

    Not yet implemented. Raises NotImplementedError.
    """
    raise NotImplementedError("deidentify_text is implemented in Phase 3.")


@mcp.tool()
async def deidentify_pdf(
    pdf_path: str,
    patient_id: str,
) -> Dict[str, Any]:
    """[PHASE 3] Extract and de-identify a PDF document.

    Not yet implemented. Raises NotImplementedError.
    """
    raise NotImplementedError("deidentify_pdf is implemented in Phase 3.")


@mcp.tool()
async def deidentify_genomics_file(
    file_path: str,
    patient_id: str,
    file_type: str = "vcf",
) -> Dict[str, Any]:
    """[PHASE 4] De-identify VCF headers, h5ad .uns fields, or CNS headers.

    Not yet implemented. Raises NotImplementedError.
    """
    raise NotImplementedError("deidentify_genomics_file is implemented in Phase 4.")


@mcp.tool()
async def generate_anonymization_key(patient_id: str) -> Dict[str, Any]:
    """[PHASE 2] Retrieve or regenerate the anonymization key for a patient.

    Not yet implemented. Raises NotImplementedError.
    """
    raise NotImplementedError("generate_anonymization_key is implemented in Phase 2.")


@mcp.tool()
async def validate_deidentification(
    content: str,
    patient_id: str,
) -> Dict[str, Any]:
    """[PHASE 5] Three-layer PII validation: Haiku red-team + regex + key reverse lookup.

    Not yet implemented. Raises NotImplementedError.
    """
    raise NotImplementedError("validate_deidentification is implemented in Phase 5.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    _run_server(mcp, server_name="mcp-deidentify", dry_run=DRY_RUN, env_var="DEIDENTIFY_DRY_RUN")


if __name__ == "__main__":
    main()
