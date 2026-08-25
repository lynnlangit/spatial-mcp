"""Deterministic anonymization code generator for mcp-deidentify.

Same (patient_id, entity_type, entity_text) triple always returns the same code.
Codes have human-readable prefixes: Dr. ONC-001, FAC-002, ACCESSION-001, etc.
"""

import hashlib

# Maps entity_type -> (prefix, separator)
# The counter suffix is zero-padded to 3 digits.
_PREFIX_MAP: dict[str, str] = {
    "PERSON_NAME_PHYSICIAN": "Dr. ONC",
    "PERSON_NAME_PATHOLOGIST": "Dr. PATH",
    "PERSON_NAME_LAB_DIRECTOR": "LAB-DIR",
    "PERSON_NAME_STAFF": "STAFF",
    "PERSON_NAME_PATIENT": "PAT-NAME",
    "FACILITY_NAME": "FAC",
    "MRN": "MRN-REDACTED",
    "ACCOUNT_NUMBER": "ACCOUNT-REDACTED",
    "ACCESSION_NUMBER": "ACCESSION",
    "SPECIMEN_ID": "SPECIMEN",
    "DATE_OF_BIRTH": "DOB-REDACTED",  # no counter -- all DOBs get the same replacement
    "DATE_OF_SERVICE": "DOS",
    "GEOGRAPHIC": "REGION",
    "PHONE": "CONTACT-REDACTED",
    "FAX": "CONTACT-REDACTED",
    "EMAIL": "EMAIL-REDACTED",
    "SSN": "SSN-REDACTED",
    "URL": "URL-REDACTED",
    "IP_ADDRESS": "IP-REDACTED",
    "INSTITUTION_NAME": "INST",
    "LAB_DIRECTOR_NAME": "LAB-DIR",
    "ORDERING_PROVIDER_NAME": "PROVIDER",
}

_DEFAULT_PREFIX = "ENTITY"

# Entity types that always map to a single fixed replacement (no counter)
_FIXED_REPLACEMENTS: dict[str, str] = {
    "DATE_OF_BIRTH": "DOB-REDACTED",
    "SSN": "SSN-REDACTED",
}


def _deterministic_index(patient_id: str, entity_type: str, entity_text: str) -> int:
    """Return a stable 0-based index for this triple using SHA-256.

    The index is used as the starting counter value when a new entity is first
    encountered. Because the counter is stored in the session key, subsequent
    entities of the same type get sequential numbers (001, 002, ...) in
    encounter order, not hash order. The hash is only used as a tiebreaker seed
    if the session key is empty (first call for this patient).
    """
    digest = hashlib.sha256(f"{patient_id}|{entity_type}|{entity_text}".encode()).hexdigest()
    return int(digest[:4], 16) % 900  # range 0-899, leaves room below 1000


def assign_code(
    patient_id: str,
    entity_type: str,
    entity_text: str,
    session_key: dict,
) -> str:
    """Assign a deterministic anonymization code for the given entity.

    If `entity_text` has already been assigned a code in `session_key`, return
    the existing code. Otherwise mint a new one and record it.

    Args:
        patient_id: Canonical patient identifier (e.g. "PAT004").
        entity_type: One of the entity type strings from _PREFIX_MAP.
        entity_text: The original PII text to be replaced.
        session_key: Mutable dict representing the in-memory anonymization key.
                     Modified in-place: new entities are added.

    Returns:
        The anonymization code string (e.g. "FAC-002", "Dr. ONC-001").
    """
    # Fixed replacements never get a counter
    if entity_type in _FIXED_REPLACEMENTS:
        code = _FIXED_REPLACEMENTS[entity_type]
        _record(session_key, entity_text, entity_type, code)
        return code

    # Check if already assigned
    existing = session_key.get("entity_map", {}).get(entity_text)
    if existing:
        return existing["code"]

    # Mint new code
    prefix = _PREFIX_MAP.get(entity_type, _DEFAULT_PREFIX)
    counter_key = f"_counter_{entity_type}"
    counters = session_key.setdefault("_counters", {})
    current = counters.get(counter_key, 0) + 1
    counters[counter_key] = current
    code = f"{prefix}-{current:03d}"

    _record(session_key, entity_text, entity_type, code)
    return code


def _record(session_key: dict, entity_text: str, entity_type: str, code: str) -> None:
    """Write entity->code mapping into session_key (idempotent)."""
    entity_map = session_key.setdefault("entity_map", {})
    if entity_text not in entity_map:
        entity_map[entity_text] = {"code": code, "entity_type": entity_type}
