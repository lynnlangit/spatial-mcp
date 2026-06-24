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
# Phase 2 tools (implemented) + Phase 3-5 stubs
# ---------------------------------------------------------------------------


@mcp.tool()
async def deidentify_json(
    json_content: str,
    patient_id: str,
    code_map: Optional[Dict] = None,
) -> Dict[str, Any]:
    """De-identify a JSON clinical record (Stage 0 preprocessing).

    Recursively scans every string leaf in the JSON dict, detects PII using
    Haiku (or returns synthetic fixture in DRY_RUN mode), and replaces each
    entity with a deterministic anonymization code. The anonymization key is
    written to disk at {DEIDENTIFY_KEY_DIR}/{patient_id}/{patient_id}_anonymization_key.json.

    Args:
        json_content: JSON string of the clinical record to de-identify.
        patient_id:   Canonical patient identifier (e.g. "PAT004").
        code_map:     Optional dict of entity_text->code overrides. If provided,
                      these mappings take priority over auto-generated codes.

    Returns:
        {
          "deidentified": <dict>,          # de-identified record
          "key_path": <str>,               # path to written anonymization key
          "entities_found": [...]          # list of detected entities
          "entity_count": <int>,
          "synthetic_data": <bool>,
          "dry_run": <bool>
        }
    """
    import json as _json

    from mcp_deidentify.format_handlers.json_handler import deidentify_json_dict
    from mcp_deidentify.key_manager import KeyManager

    # Parse input
    try:
        record = _json.loads(json_content)
    except _json.JSONDecodeError as e:
        return add_dry_run_warning({"error": f"Invalid JSON: {e}", "patient_id": patient_id})

    # Load / create key
    km = KeyManager(patient_id)

    # Apply any caller-supplied overrides to the session key
    if code_map:
        for entity_text, code in code_map.items():
            km.session_key.setdefault("entity_map", {})[entity_text] = {
                "code": code,
                "entity_type": "OVERRIDE",
            }

    # De-identify
    deidentified, entities = await deidentify_json_dict(
        record, patient_id=patient_id, session_key=km.session_key
    )

    # Persist key
    key_path = km.save()

    return add_dry_run_warning(
        {
            "deidentified": deidentified,
            "key_path": key_path,
            "entities_found": entities,
            "entity_count": len(entities),
            "synthetic_data": DRY_RUN,
            "dry_run": DRY_RUN,
        }
    )


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
    """Retrieve or initialise the anonymization key for a patient.

    If a key file already exists on disk for this patient, loads and returns it.
    If no key exists yet, creates an empty key, writes it to disk, and returns it.
    Does not modify any existing entity->code mappings.

    Args:
        patient_id: Canonical patient identifier (e.g. "PAT004").

    Returns:
        {
          "patient_id": <str>,
          "key_path": <str>,
          "code_map": <dict>,     # entity_text -> {code, entity_type}
          "entry_count": <int>,
          "generated_at": <str>,
          "dry_run": <bool>
        }
    """
    from mcp_deidentify.key_manager import KeyManager

    km = KeyManager(patient_id)
    key_path = km.save()  # no-op if already exists (save is idempotent)
    clean = km.as_dict()

    return add_dry_run_warning(
        {
            "patient_id": patient_id,
            "key_path": key_path,
            "code_map": clean.get("entity_map", {}),
            "entry_count": len(clean.get("entity_map", {})),
            "generated_at": clean.get("generated_at", ""),
            "dry_run": DRY_RUN,
        }
    )


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
