"""Shared Pydantic models for mcp-deidentify."""

from typing import Dict, List, Optional

from pydantic import BaseModel


class DetectedEntity(BaseModel):
    """A single PII entity detected by the engine."""

    text: str  # original text matched
    entity_type: str  # e.g. PERSON_NAME, MRN, ACCESSION_NUMBER
    start: int  # character offset in source string
    end: int  # character offset in source string
    replacement_code: str  # assigned anonymization code


class AnonymizationKey(BaseModel):
    """Maps original entity text -> anonymization code for one patient."""

    patient_id: str
    entity_map: Dict[str, Dict[str, str]]  # entity_text -> {code, entity_type}
    generated_at: str


class DeidentifyResult(BaseModel):
    """Output of any de-identification operation."""

    patient_id: str
    entities_found: List[DetectedEntity]
    synthetic_data: bool = True  # always True in DRY_RUN; False in live mode
    dry_run: bool = True
    warning: Optional[str] = None
