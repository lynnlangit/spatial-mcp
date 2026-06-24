"""Haiku-based PII extraction engine for mcp-deidentify.

DRY_RUN=true  -> returns synthetic fixture (no Haiku calls, no API key needed)
DRY_RUN=false -> calls claude-haiku-4-5-20251001 via Anthropic SDK
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

DRY_RUN = os.getenv("DEIDENTIFY_DRY_RUN", "true").lower() == "true"
HAIKU_MODEL = "claude-haiku-4-5-20251001"
MAX_CHUNK_CHARS = 6000  # ~1800 tokens at 3.5 chars/token
OVERLAP_CHARS = 350  # ~100 tokens overlap for cross-boundary entities
MAX_RETRIES = 3

# ---------------------------------------------------------------------------
# Synthetic DRY_RUN fixture -- NO real PII
# ---------------------------------------------------------------------------

SYNTHETIC_ENTITIES: List[Dict[str, Any]] = [
    {
        "text": "Jane Doe Smith",
        "entity_type": "PERSON_NAME_PATIENT",
        "start": 12,
        "end": 26,
    },
    {
        "text": "Dr. Robert Sample",
        "entity_type": "PERSON_NAME_PHYSICIAN",
        "start": 40,
        "end": 57,
    },
    {
        "text": "City General Hospital",
        "entity_type": "FACILITY_NAME",
        "start": 70,
        "end": 91,
    },
    {
        "text": "12345678",
        "entity_type": "MRN",
        "start": 105,
        "end": 113,
    },
    {
        "text": "22X-SAMPLE-00001",
        "entity_type": "ACCESSION_NUMBER",
        "start": 130,
        "end": 147,
    },
    {
        "text": "1980-01-01",
        "entity_type": "DATE_OF_BIRTH",
        "start": 160,
        "end": 170,
    },
]

SYNTHETIC_TEXT = (
    "Patient: Jane Doe Smith | Physician: Dr. Robert Sample | "
    "Facility: City General Hospital | MRN: 12345678 | "
    "Accession: 22X-SAMPLE-00001 | DOB: 1980-01-01"
)

# ---------------------------------------------------------------------------
# PII extraction prompt
# ---------------------------------------------------------------------------

_EXTRACTION_PROMPT = """\
You are a HIPAA-compliant de-identification engine.
Extract ALL personally identifiable information (PII) from the clinical text below.

Return ONLY valid JSON with exactly this schema -- no commentary, no markdown fences:
{
  "entities": [
    {"text": "<exact_substring>", "entity_type": "<TYPE>", "start": <int>, "end": <int>}
  ]
}

Valid entity types:
  PERSON_NAME_PATIENT, PERSON_NAME_PHYSICIAN, PERSON_NAME_PATHOLOGIST,
  PERSON_NAME_LAB_DIRECTOR, PERSON_NAME_STAFF,
  FACILITY_NAME, INSTITUTION_NAME,
  MRN, ACCOUNT_NUMBER, ACCESSION_NUMBER, SPECIMEN_ID,
  DATE_OF_BIRTH, DATE_OF_SERVICE,
  GEOGRAPHIC, PHONE, FAX, EMAIL, SSN, URL, IP_ADDRESS,
  LAB_DIRECTOR_NAME, ORDERING_PROVIDER_NAME

Rules:
- "start" and "end" are character offsets within the provided chunk (0-indexed).
- If no PII is found, return {"entities": []}.
- Do NOT include gene names, drug names, diagnosis codes, or lab values.

Clinical text:
"""

_REDTEAM_PROMPT = """\
You are a HIPAA compliance auditor performing final verification.
ASSUME that PII was missed during de-identification. Your job is to FIND IT.
Be maximally suspicious. Flag anything that could possibly identify a person,
facility, or date -- even if it looks anonymized or partially replaced.

Return ONLY valid JSON with exactly this schema -- no commentary, no markdown fences:
{
  "entities": [
    {"text": "<exact_substring>", "entity_type": "<TYPE>", "start": <int>, "end": <int>}
  ]
}

Text to audit:
"""


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------


def _chunk_text(
    text: str, chunk_size: int = MAX_CHUNK_CHARS, overlap: int = OVERLAP_CHARS
) -> List[Dict]:
    """Split text into overlapping chunks. Returns list of {text, offset} dicts."""
    if len(text) <= chunk_size:
        return [{"text": text, "offset": 0}]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append({"text": text[start:end], "offset": start})
        if end == len(text):
            break
        start = end - overlap
    return chunks


# ---------------------------------------------------------------------------
# Haiku call (with retry)
# ---------------------------------------------------------------------------


async def _call_haiku(prompt_prefix: str, text_chunk: str) -> List[Dict]:
    """Call Haiku and parse entity list. Returns [] on failure (fail-safe)."""
    try:
        import anthropic
    except ImportError:
        logger.error("anthropic package not installed; run: uv pip install anthropic")
        return []

    client = anthropic.Anthropic()
    full_prompt = prompt_prefix + text_chunk

    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=HAIKU_MODEL,
                max_tokens=2048,
                messages=[{"role": "user", "content": full_prompt}],
            )
            raw = response.content[0].text.strip()
            parsed = json.loads(raw)
            return parsed.get("entities", [])
        except anthropic.RateLimitError:
            wait = 2**attempt
            logger.warning(
                f"Haiku rate limit hit; retrying in {wait}s "
                f"(attempt {attempt + 1}/{MAX_RETRIES})"
            )
            await asyncio.sleep(wait)
        except json.JSONDecodeError as e:
            logger.warning(f"Haiku returned malformed JSON: {e}. Skipping chunk.")
            return []
        except Exception as e:
            logger.error(f"Haiku call failed: {e}")
            return []

    logger.error("Haiku call failed after max retries.")
    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def extract_entities(text: str, red_team: bool = False) -> List[Dict]:
    """Extract PII entities from text.

    In DRY_RUN mode: returns SYNTHETIC_ENTITIES without calling Haiku.
    In live mode: chunks text, dispatches all chunks to Haiku in parallel,
    deduplicates overlapping entities, adjusts offsets back to original text.

    Args:
        text: The text to de-identify.
        red_team: If True, use the aggressive red-team prompt (for validate_deidentification).

    Returns:
        List of entity dicts with keys: text, entity_type, start, end.
    """
    if DRY_RUN:
        logger.info("DEIDENTIFY_DRY_RUN=true: returning synthetic entity fixture")
        return SYNTHETIC_ENTITIES

    prompt = _REDTEAM_PROMPT if red_team else _EXTRACTION_PROMPT
    chunks = _chunk_text(text)

    # Dispatch all chunks in parallel
    tasks = [_call_haiku(prompt, chunk["text"]) for chunk in chunks]
    chunk_results = await asyncio.gather(*tasks)

    # Flatten + adjust offsets back to original text coordinates
    all_entities: List[Dict] = []
    seen_spans = set()
    for chunk, entities in zip(chunks, chunk_results):
        offset = chunk["offset"]
        for ent in entities:
            abs_start = ent.get("start", 0) + offset
            abs_end = ent.get("end", 0) + offset
            span_key = (ent.get("text", ""), ent.get("entity_type", ""))
            if span_key in seen_spans:
                continue  # deduplicate overlap
            seen_spans.add(span_key)
            all_entities.append(
                {
                    "text": ent.get("text", ""),
                    "entity_type": ent.get("entity_type", "UNKNOWN"),
                    "start": abs_start,
                    "end": abs_end,
                }
            )

    return all_entities


def replace_entities(text: str, entities: List[Dict], session_key: Dict, patient_id: str) -> str:
    """Apply entity replacements to text using codes from code_generator.

    Processes entities in reverse order (by start offset) so substitutions
    don't shift the positions of earlier entities.

    Args:
        text: Original text.
        entities: List of entity dicts (output of extract_entities).
        session_key: Mutable anonymization key dict (modified in-place).
        patient_id: Patient identifier for code generation.

    Returns:
        De-identified text with all entity spans replaced by their codes.
    """
    from .code_generator import assign_code

    # Sort descending by start so replacements don't shift earlier offsets
    sorted_entities = sorted(entities, key=lambda e: e.get("start", 0), reverse=True)

    result = text
    for ent in sorted_entities:
        start = ent.get("start", 0)
        end = ent.get("end", 0)
        entity_text = ent.get("text", "")
        entity_type = ent.get("entity_type", "UNKNOWN")

        if not entity_text or start >= end:
            continue

        # Verify the text at this position actually matches
        if result[start:end] != entity_text:
            # Try a string search fallback
            idx = result.find(entity_text)
            if idx == -1:
                logger.debug(f"Entity '{entity_text}' not found at offset {start}; skipping")
                continue
            start, end = idx, idx + len(entity_text)

        code = assign_code(patient_id, entity_type, entity_text, session_key)
        result = result[:start] + code + result[end:]

    return result
