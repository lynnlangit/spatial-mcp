"""JSON clinical record de-identification handler.

Recursively walks all string leaves in a JSON dict and replaces detected
PII entities with anonymization codes.

Usage:
    from mcp_deidentify.format_handlers.json_handler import deidentify_json_dict

    deidentified, entities = await deidentify_json_dict(
        record_dict, patient_id="PAT004", session_key=key_manager.session_key
    )
"""

import copy
import logging
import re
from typing import Any, Dict, List, Tuple

from mcp_deidentify.engine import extract_entities, replace_entities

logger = logging.getLogger(__name__)

# Minimum length for a string value to be sent for entity extraction
_MIN_LEN = 4

# Regex patterns for values that look like existing codes -- skip these
_CODE_PATTERN = re.compile(
    r"^("
    r"PAT\d+|FAC-\d+|Dr\.\s[A-Z]+-\d+|LAB-DIR-\d+|ACCESSION-\d+|SPECIMEN-\d+|"
    r"MRN-REDACTED-\d+|DOB-REDACTED|DOS-\d{4}-\d{2}|REGION-\d+|"
    r"CONTACT-REDACTED-\d+|EMAIL-REDACTED-\d+|STAFF-\d+|PROVIDER-\d+|"
    r"[A-Z]{2,}-\d{3}|true|false|null"
    r")$",
    re.IGNORECASE,
)


def _should_skip(value: str) -> bool:
    """Return True if this string value should not be sent for entity extraction."""
    if len(value) < _MIN_LEN:
        return True
    if _CODE_PATTERN.match(value.strip()):
        return True
    return False


async def deidentify_json_dict(
    record: Dict[str, Any],
    patient_id: str,
    session_key: Dict,
) -> Tuple[Dict[str, Any], List[Dict]]:
    """Recursively de-identify all string leaves in a JSON dict.

    Args:
        record:      The JSON dict to de-identify (not modified in-place).
        patient_id:  Patient identifier for code generation.
        session_key: Mutable anonymization key dict from KeyManager.

    Returns:
        Tuple of (deidentified_dict, all_entities_found).
        deidentified_dict has the same structure as record; string leaves
        containing PII are replaced with anonymization codes.
        all_entities_found is a flat list of all DetectedEntity-like dicts.
    """
    result = copy.deepcopy(record)
    all_entities: List[Dict] = []

    await _walk(result, patient_id, session_key, all_entities)
    return result, all_entities


async def _walk(
    node: Any,
    patient_id: str,
    session_key: Dict,
    all_entities: List[Dict],
    parent_key: str = "",
) -> Any:
    """Recursive in-place walker. Modifies node in-place for dict/list nodes."""
    if isinstance(node, dict):
        for k, v in node.items():
            node[k] = await _walk(v, patient_id, session_key, all_entities, parent_key=k)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            node[i] = await _walk(
                item, patient_id, session_key, all_entities, parent_key=parent_key
            )
    elif isinstance(node, str):
        if not _should_skip(node):
            entities = await extract_entities(node)
            if entities:
                all_entities.extend(entities)
                node = replace_entities(node, entities, session_key, patient_id)
    return node
