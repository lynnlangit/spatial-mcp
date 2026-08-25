"""MCP De-identification server -- Stage 0 preprocessing for Precision Medicine MCP.

Runs live by default. DEIDENTIFY_DRY_RUN=true returns synthetic fixtures instead
of de-identifying anything; every field of such a response is prefixed
"SYNTHETIC:" and carries status="SYNTHETIC_DRY_RUN" so that downstream code
which ignores metadata cannot mistake fixture output for a real result.

Set ANTHROPIC_API_KEY for the Haiku calls. See config.py for DEIDENTIFY_DATE_POLICY.
"""

import logging
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP("deidentify")

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _add_dry_run_warning
from common.transport import run_server as _run_server

from mcp_deidentify import config

_SYNTHETIC_PREFIX = "SYNTHETIC:"

# Fields the caller supplied and we merely echo back. These are not fabricated,
# and prefixing them would corrupt legitimate downstream dispatch -- e.g. code
# that switches on file_type would stop recognising "vcf".
_ECHO_KEYS = frozenset({"patient_id", "file_type", "source_format"})


def _mark_synthetic(value: Any) -> Any:
    """Recursively prefix server-generated strings in a DRY_RUN payload.

    Metadata-only warnings are easy to ignore: a caller that reads
    result["deidentified_text"] and nothing else has no way to know the text was
    fabricated. Prefixing the values themselves makes fixture data impossible to
    consume by accident.

    Keys beginning with "_" (the warning fields) and _ECHO_KEYS are left alone.
    """
    if isinstance(value, str):
        return f"{_SYNTHETIC_PREFIX} {value}"
    if isinstance(value, list):
        return [_mark_synthetic(v) for v in value]
    if isinstance(value, dict):
        return {
            k: (v if (k.startswith("_") or k in _ECHO_KEYS) else _mark_synthetic(v))
            for k, v in value.items()
        }
    return value


def add_dry_run_warning(result: dict) -> dict:
    """Tag a result with DRY_RUN metadata, and in DRY_RUN make it unmissable."""
    if not config.DRY_RUN:
        return result
    marked = _mark_synthetic(result)
    marked["status"] = "SYNTHETIC_DRY_RUN"
    marked["dry_run"] = True
    return _add_dry_run_warning(marked, dry_run=True, env_var="DEIDENTIFY_DRY_RUN")


# ---------------------------------------------------------------------------
# Phase 2 tools (implemented) + Phase 3-5 stubs
# ---------------------------------------------------------------------------


@mcp.tool()
async def deidentify_json(
    json_content: str,
    patient_id: str,
    code_map: dict | None = None,
) -> dict[str, Any]:
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
            "synthetic_data": config.DRY_RUN,
            "dry_run": config.DRY_RUN,
        }
    )


@mcp.tool()
async def deidentify_text(
    text: str,
    patient_id: str,
    source_format: str = "txt",
    output_path: str | None = None,
) -> dict[str, Any]:
    """De-identify plain text or DOCX content (Stage 0 preprocessing).

    For source_format="txt": de-identifies the supplied string in memory.
    For source_format="docx": treats `text` as a file path, reads the DOCX,
    de-identifies all paragraphs, and writes a new DOCX to output_path.

    Args:
        text:          Plain text string (if source_format="txt"), or path to
                       DOCX file (if source_format="docx").
        patient_id:    Canonical patient identifier (e.g. "PAT004").
        source_format: "txt" or "docx". Defaults to "txt".
        output_path:   For DOCX only -- destination path for de-identified file.
                       Defaults to {DEIDENTIFY_OUTPUT_DIR}/{patient_id}/deidentified/{stem}_deid.docx

    Returns:
        {
          "deidentified_text": <str>,
          "output_path": <str | null>,
          "key_path": <str>,
          "entities_found": [...],
          "entity_count": <int>,
          "source_format": <str>,
          "dry_run": <bool>
        }
    """
    from mcp_deidentify.format_handlers.text_handler import (
        deidentify_docx_file,
        deidentify_text_string,
    )
    from mcp_deidentify.key_manager import KeyManager

    km = KeyManager(patient_id)

    if source_format == "docx":
        deid_text, written_path, entities = await deidentify_docx_file(
            docx_path=text,
            patient_id=patient_id,
            session_key=km.session_key,
            output_path=output_path,
        )
        key_path = km.save()
        return add_dry_run_warning(
            {
                "deidentified_text": deid_text,
                "output_path": written_path,
                "key_path": key_path,
                "entities_found": entities,
                "entity_count": len(entities),
                "source_format": source_format,
                "dry_run": config.DRY_RUN,
            }
        )
    else:
        deid_text, entities = await deidentify_text_string(
            text=text, patient_id=patient_id, session_key=km.session_key
        )
        key_path = km.save()
        return add_dry_run_warning(
            {
                "deidentified_text": deid_text,
                "output_path": None,
                "key_path": key_path,
                "entities_found": entities,
                "entity_count": len(entities),
                "source_format": source_format,
                "dry_run": config.DRY_RUN,
            }
        )


@mcp.tool()
async def deidentify_pdf_text(
    pdf_path: str,
    patient_id: str,
) -> dict[str, Any]:
    """Extract and de-identify the TEXT LAYER of a PDF (Stage 0 preprocessing).

    This tool reads the text layer via pdfplumber and de-identifies it. It does
    NOT produce a redacted PDF file, and it cannot see text that exists only as
    pixels. Scanned or image-only PDFs -- which is what most clinical documents
    are -- have no text layer, and are reported as status="no_text_layer" rather
    than silently returning zero entities.

    Args:
        pdf_path:   Path to the source PDF file.
        patient_id: Canonical patient identifier (e.g. "PAT004").

    Returns:
        {
          "status": "ok" | "no_text_layer",
          "extracted_text": <str>,
          "deidentified_text": <str>,
          "key_path": <str>,
          "page_count": <int>,
          "pages_without_text": [<int>, ...],   # 1-indexed; NOT de-identified
          "entities_found": [...],
          "entity_count": <int>,
          "dry_run": <bool>
        }
    """
    from mcp_deidentify.format_handlers.pdf_handler import deidentify_pdf_file
    from mcp_deidentify.key_manager import KeyManager

    km = KeyManager(patient_id)
    res = await deidentify_pdf_file(
        pdf_path=pdf_path, patient_id=patient_id, session_key=km.session_key
    )

    payload: dict[str, Any] = {
        "status": res["status"],
        "extracted_text": res["raw_text"],
        "deidentified_text": res["deidentified_text"],
        "key_path": km.save() if res["status"] == "ok" else None,
        "page_count": res["page_count"],
        "pages_without_text": res["pages_without_text"],
        "entities_found": res["entities_found"],
        "entity_count": len(res["entities_found"]),
        "dry_run": config.DRY_RUN,
    }
    if "error" in res:
        payload["error"] = res["error"]
    return add_dry_run_warning(payload)


@mcp.tool()
async def deidentify_genomics_file(
    file_path: str,
    patient_id: str,
    file_type: str = "vcf",
) -> dict[str, Any]:
    """De-identify PII from genomics file headers (Stage 0 preprocessing).

    Supported file types:
      "vcf"  -- scrubs ## meta-information header lines; data rows untouched
      "h5ad" -- de-identifies string values in adata.uns only; writes file in-place
      "cns"  -- scrubs # comment lines; CNV segment data rows untouched

    Args:
        file_path:  Path to the genomics file.
        patient_id: Canonical patient identifier (e.g. "PAT004").
        file_type:  One of "vcf", "h5ad", "cns". Defaults to "vcf".

    Returns:
        {
          "deidentified_content": <str>,
          "key_path": <str>,
          "fields_modified": [<str>, ...],
          "entity_count": <int>,
          "file_type": <str>,
          "dry_run": <bool>
        }
    """
    from mcp_deidentify.format_handlers.genomics_handler import (
        deidentify_genomics_file as _deid_genomics,
    )
    from mcp_deidentify.key_manager import KeyManager

    km = KeyManager(patient_id)
    try:
        content, fields_modified, entities = await _deid_genomics(
            file_path=file_path,
            patient_id=patient_id,
            session_key=km.session_key,
            file_type=file_type,
        )
    except ValueError as e:
        return add_dry_run_warning({"error": str(e), "patient_id": patient_id})

    key_path = km.save()
    return add_dry_run_warning(
        {
            "deidentified_content": content,
            "key_path": key_path,
            "fields_modified": fields_modified,
            "entity_count": len(entities),
            "file_type": file_type,
            "dry_run": config.DRY_RUN,
        }
    )


@mcp.tool()
async def generate_anonymization_key(patient_id: str) -> dict[str, Any]:
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
            "dry_run": config.DRY_RUN,
        }
    )


@mcp.tool()
async def validate_deidentification(
    content: str,
    patient_id: str,
) -> dict[str, Any]:
    """Three-layer validation that de-identified content contains no residual PII.

    Runs three independent layers:
      Layer 1 -- Haiku red-team: aggressive Haiku prompt.
      Layer 2 -- Regex sweep: 9 structural patterns (SSN, phone, email, dates,
                             MRN, accession numbers).
      Layer 3 -- Key reverse lookup: checks that no original entity text from the
                             patient's anonymization key appears verbatim.

    All three layers must RUN and pass for passed=True. If any layer could not
    run -- DRY_RUN is on, or the Haiku call failed -- this returns
    status="unavailable_in_dry_run" (or "incomplete") with passed=None. It never
    reports a verdict based only on the layers that happened to execute.

    Args:
        content:    The de-identified text to audit.
        patient_id: Canonical patient identifier -- used to load the anonymization
                    key for Layer 3.

    Returns:
        {
          "status": "complete" | "unavailable_in_dry_run" | "incomplete",
          "passed": <bool | None>,   # None whenever any layer was skipped
          "confidence": <float | None>,
          "layers": { ... },         # per-layer status + passed + hits
          "layers_skipped": [...],
          "residual_pii_found": [...],
          "date_policy": <str>,
          "patient_id": <str>,
          "dry_run": <bool>
        }
    """
    from mcp_deidentify.key_manager import KeyManager
    from mcp_deidentify.validator import validate

    km = KeyManager(patient_id)
    result = await validate(content=content, session_key=km.session_key)
    result["patient_id"] = patient_id
    result["dry_run"] = config.DRY_RUN

    # add_dry_run_warning() would overwrite status with SYNTHETIC_DRY_RUN and
    # prefix every field. For this tool the validator's own
    # status="unavailable_in_dry_run" is the more precise signal, so preserve it.
    if config.DRY_RUN:
        result["_DRY_RUN_WARNING"] = "NOT VALIDATED - no verdict available in DRY_RUN"
    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    _run_server(
        mcp,
        server_name="mcp-deidentify",
        dry_run=config.DRY_RUN,
        env_var="DEIDENTIFY_DRY_RUN",
    )


if __name__ == "__main__":
    main()
