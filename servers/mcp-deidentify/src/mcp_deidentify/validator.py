"""Three-layer de-identification validator for mcp-deidentify.

Layer 1 -- Haiku red-team:    Aggressive Haiku prompt that assumes PII is present.
Layer 2 -- Regex sweep:       Deterministic structural pattern matching (9 patterns).
Layer 3 -- Key reverse lookup: Checks that no known entity_text from the anonymization
                              key appears verbatim in the content.

All three layers must pass independently for the overall result to be passed=True.

DRY_RUN=true: Haiku is not called; regex and key lookup run on synthetic content.
"""

import logging
import os
import re
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

DRY_RUN = os.getenv("DEIDENTIFY_DRY_RUN", "true").lower() == "true"

# ---------------------------------------------------------------------------
# Layer 2 -- Regex patterns for structural PII
# ---------------------------------------------------------------------------

_REGEX_PATTERNS: List[Tuple[str, str]] = [
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


def _run_regex_layer(content: str) -> Tuple[bool, List[Dict]]:
    """Run all regex patterns against content. Returns (passed, hits)."""
    hits = []
    for name, pattern in _COMPILED:
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


def _run_key_lookup_layer(content: str, session_key: Dict) -> Tuple[bool, List[Dict]]:
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


async def _run_haiku_layer(content: str) -> Tuple[bool, List[Dict]]:
    """Call Haiku with red-team prompt. In DRY_RUN always returns passed=True."""
    if DRY_RUN:
        return True, []

    from mcp_deidentify.engine import extract_entities

    entities = await extract_entities(content, red_team=True)
    hits = [
        {"layer": "haiku_red_team", **ent}
        for ent in entities
        if ent.get("entity_type", "UNKNOWN") != "UNKNOWN"
    ]
    return len(hits) == 0, hits


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def validate(content: str, session_key: Dict) -> Dict[str, Any]:
    """Run all three validation layers against de-identified content.

    Args:
        content:     The de-identified text to audit.
        session_key: The anonymization key dict for this patient (used in Layer 3).

    Returns:
        {
          "passed": <bool>,          # True only if ALL three layers pass
          "confidence": <float>,     # 1.0 = all pass, 0.67 = one fail, etc.
          "layers": {
            "haiku_red_team":    {"passed": <bool>, "hits": [...]},
            "regex_sweep":       {"passed": <bool>, "hits": [...]},
            "key_reverse_lookup":{"passed": <bool>, "hits": [...]},
          },
          "residual_pii_found": [...]   # flat list of all hits across all layers
        }
    """
    # Run regex and key lookup synchronously (no I/O)
    regex_passed, regex_hits = _run_regex_layer(content)
    key_passed, key_hits = _run_key_lookup_layer(content, session_key)

    # Run Haiku layer (async, may be no-op in DRY_RUN)
    haiku_passed, haiku_hits = await _run_haiku_layer(content)

    all_hits = haiku_hits + regex_hits + key_hits
    layers_passed = [haiku_passed, regex_passed, key_passed]
    overall_passed = all(layers_passed)
    confidence = round(sum(layers_passed) / 3, 4)

    return {
        "passed": overall_passed,
        "confidence": confidence,
        "layers": {
            "haiku_red_team": {"passed": haiku_passed, "hits": haiku_hits},
            "regex_sweep": {"passed": regex_passed, "hits": regex_hits},
            "key_reverse_lookup": {"passed": key_passed, "hits": key_hits},
        },
        "residual_pii_found": all_hits,
    }
