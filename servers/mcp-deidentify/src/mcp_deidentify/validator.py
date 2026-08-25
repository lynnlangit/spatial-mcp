"""Three-layer de-identification validator for mcp-deidentify.

Layer 1 -- Haiku red-team:    Aggressive Haiku prompt that assumes PII is present.
Layer 2 -- Regex sweep:       Deterministic structural pattern matching.
Layer 3 -- Key reverse lookup: Checks that no known entity_text from the anonymization
                              key appears verbatim in the content.

All three layers must RUN and pass independently for passed=True.

If any layer could not run -- because DRY_RUN is on, or because the Haiku call
failed -- this module returns ``status`` of "unavailable_in_dry_run" or
"incomplete" with ``passed: None``. It never reports a pass on the strength of
the layers that happened to execute. A validator that silently grades itself on
two of three layers is worse than no validator, because the caller cannot tell
the difference between "clean" and "not actually checked".
"""

import logging
import re
from typing import Any

from mcp_deidentify import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Layer 2 -- Regex patterns for structural PII
# ---------------------------------------------------------------------------

_REGEX_PATTERNS: list[tuple[str, str]] = [
    ("SSN", r"\b\d{3}-\d{2}-\d{4}\b"),
    ("PHONE_PAREN", r"\(\d{3}\)\s?\d{3}[-.]\d{4}\b"),
    ("PHONE_DASH", r"\b\d{3}[-.]\d{3}[-.]\d{4}\b"),
    ("EMAIL", r"\b\S+@\S+\.\S+\b"),
    ("DATE_SLASHED", r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    ("DATE_ISO", r"\b\d{4}-\d{2}-\d{2}\b"),
    ("MRN_LABELED", r"\bMRN[-:\s]?\d{6,10}\b"),
    ("NUMERIC_LONG", r"\b\d{8,10}\b"),
    ("ACCESSION_PATTERN", r"\b[A-Z]{2}\d{2}[A-Z]\d{5,}\b"),
]

_COMPILED = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in _REGEX_PATTERNS]


def _active_patterns() -> list[tuple[str, Any]]:
    """Return the patterns that apply under the configured date policy.

    Under LIMITED_DATA_SET, full dates are permitted by 45 CFR 164.514(e), so
    flagging them as residual PII would contradict the de-identifier.
    """
    if config.DATE_POLICY == config.LIMITED_DATA_SET:
        return [(n, p) for n, p in _COMPILED if not n.startswith("DATE_")]
    return _COMPILED


def _run_regex_layer(content: str) -> tuple[bool, list[dict]]:
    """Run the active regex patterns against content. Returns (passed, hits)."""
    hits = []
    for name, pattern in _active_patterns():
        for m in pattern.finditer(content):
            hits.append(
                {
                    "layer": "regex_sweep",
                    "pattern": name,
                    "match": m.group(),
                    "offset": m.start(),
                }
            )
    return len(hits) == 0, hits


# ---------------------------------------------------------------------------
# Layer 3 -- Key reverse lookup
# ---------------------------------------------------------------------------


def _run_key_lookup_layer(content: str, session_key: dict) -> tuple[bool, list[dict]]:
    """Check that no known entity_text appears verbatim in content (case-insensitive)."""
    hits = []
    content_lower = content.lower()
    entity_map = session_key.get("entity_map", {})
    for entity_text, mapping in entity_map.items():
        if len(entity_text) >= 4 and entity_text.lower() in content_lower:
            hits.append(
                {
                    "layer": "key_reverse_lookup",
                    "entity_text": entity_text,
                    "entity_type": mapping.get("entity_type", "UNKNOWN"),
                    "expected_code": mapping.get("code", "UNKNOWN"),
                }
            )
    return len(hits) == 0, hits


# ---------------------------------------------------------------------------
# Layer 1 -- Haiku red-team
# ---------------------------------------------------------------------------

LAYER_RAN = "ran"
LAYER_SKIPPED_DRY_RUN = "skipped_dry_run"
LAYER_ERROR = "error"


async def _run_haiku_layer(content: str) -> tuple[str, bool | None, list[dict]]:
    """Call Haiku with the red-team prompt.

    Returns (status, passed, hits). ``passed`` is None whenever the layer did not
    actually run -- this layer must never manufacture a pass it did not earn.
    """
    if config.DRY_RUN:
        return LAYER_SKIPPED_DRY_RUN, None, []

    try:
        from mcp_deidentify.engine import extract_entities

        entities = await extract_entities(content, red_team=True)
    except Exception as e:  # noqa: BLE001 - any failure must degrade to "did not run"
        logger.error("Haiku red-team layer failed, reporting as not-run: %s", e)
        return LAYER_ERROR, None, []

    hits = [
        {"layer": "haiku_red_team", **ent}
        for ent in entities
        if ent.get("entity_type", "UNKNOWN") != "UNKNOWN"
    ]
    return LAYER_RAN, len(hits) == 0, hits


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def validate(content: str, session_key: dict) -> dict[str, Any]:
    """Run all three validation layers against de-identified content.

    Args:
        content:     The de-identified text to audit.
        session_key: The anonymization key dict for this patient (used in Layer 3).

    Returns one of two shapes.

    All three layers ran::

        {
          "status": "complete",
          "passed": <bool>,          # True only if ALL three layers passed
          "confidence": <float>,     # 1.0 = all pass, 0.6667 = one fail
          "layers": {...},           # per-layer status + passed + hits
          "layers_skipped": [],
          "residual_pii_found": [...],
          "date_policy": <str>,
        }

    One or more layers could not run::

        {
          "status": "unavailable_in_dry_run" | "incomplete",
          "passed": None,            # never a verdict
          "confidence": None,
          "layers": {...},
          "layers_skipped": ["haiku_red_team"],
          "residual_pii_found": [...],   # hits from the layers that DID run
          "date_policy": <str>,
          "_VALIDATION_WARNING": "...",
        }
    """
    regex_passed, regex_hits = _run_regex_layer(content)
    key_passed, key_hits = _run_key_lookup_layer(content, session_key)
    haiku_status, haiku_passed, haiku_hits = await _run_haiku_layer(content)

    layers = {
        "haiku_red_team": {
            "status": haiku_status,
            "passed": haiku_passed,
            "hits": haiku_hits,
        },
        "regex_sweep": {"status": LAYER_RAN, "passed": regex_passed, "hits": regex_hits},
        "key_reverse_lookup": {
            "status": LAYER_RAN,
            "passed": key_passed,
            "hits": key_hits,
        },
    }

    all_hits = haiku_hits + regex_hits + key_hits
    skipped = [name for name, layer in layers.items() if layer["status"] != LAYER_RAN]

    if skipped:
        if haiku_status == LAYER_SKIPPED_DRY_RUN:
            status = "unavailable_in_dry_run"
            reason = (
                "DEIDENTIFY_DRY_RUN=true, so the Haiku red-team layer did not run. "
                "No validation verdict is available. Set DEIDENTIFY_DRY_RUN=false "
                "and provide ANTHROPIC_API_KEY to validate content."
            )
        else:
            status = "incomplete"
            reason = (
                "One or more validation layers failed to execute. No validation "
                "verdict is available. See server logs for the underlying error."
            )
        return {
            "status": status,
            "passed": None,
            "confidence": None,
            "layers": layers,
            "layers_skipped": skipped,
            "residual_pii_found": all_hits,
            "date_policy": config.DATE_POLICY,
            "_VALIDATION_WARNING": (
                f"NOT VALIDATED - {reason} Any hits listed in residual_pii_found "
                f"are real findings from the layers that did run, but their absence "
                f"does NOT indicate the content is clean."
            ),
        }

    layers_passed = [haiku_passed, regex_passed, key_passed]
    return {
        "status": "complete",
        "passed": all(layers_passed),
        "confidence": round(sum(1 for p in layers_passed if p) / 3, 4),
        "layers": layers,
        "layers_skipped": [],
        "residual_pii_found": all_hits,
        "date_policy": config.DATE_POLICY,
    }
