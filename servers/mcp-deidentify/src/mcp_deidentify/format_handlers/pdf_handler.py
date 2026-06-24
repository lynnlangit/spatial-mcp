"""PDF de-identification handler for mcp-deidentify.

Extracts text from a PDF via pdfplumber and de-identifies each page in parallel.
Returns de-identified plain text -- does not produce a de-identified PDF file.

DRY_RUN=true: no file reads, no Haiku calls; returns synthetic fixture output.
"""

import asyncio
import logging
import os
from typing import Dict, List, Tuple

from mcp_deidentify.engine import extract_entities, replace_entities

logger = logging.getLogger(__name__)

DRY_RUN = os.getenv("DEIDENTIFY_DRY_RUN", "true").lower() == "true"

_SYNTHETIC_PDF_TEXT = """\
[Page 1 — SYNTHETIC]
Patient: PAT-NAME-001 seen by Dr. ONC-001 at FAC-001.
MRN: MRN-REDACTED-001 | Accession: ACCESSION-001

[Page 2 — SYNTHETIC]
Specimen: SPECIMEN-001 | Director: LAB-DIR-001
DOS: DOS-2022-06

[Page 3 — SYNTHETIC]
All values are synthetic. No real patient data present.
"""


async def deidentify_pdf_file(
    pdf_path: str,
    patient_id: str,
    session_key: Dict,
) -> Tuple[str, str, int, List[Dict]]:
    """Extract and de-identify text from a PDF file.

    Args:
        pdf_path:    Path to the source PDF file.
        patient_id:  Patient identifier for code generation.
        session_key: Mutable anonymization key dict from KeyManager.

    Returns:
        Tuple of (extracted_raw_text, deidentified_text, page_count, entities_found).
    """
    if DRY_RUN:
        from mcp_deidentify.engine import SYNTHETIC_ENTITIES

        return _SYNTHETIC_PDF_TEXT, _SYNTHETIC_PDF_TEXT, 3, list(SYNTHETIC_ENTITIES)

    import pdfplumber

    page_texts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text() or ""
            page_texts.append(text)

    raw_text = "\n\n".join(page_texts)

    # De-identify all pages in parallel
    tasks = [extract_entities(t) for t in page_texts if t.strip()]
    results = await asyncio.gather(*tasks)

    all_entities: List[Dict] = []
    deid_pages: List[str] = []

    result_iter = iter(results)
    for page_text in page_texts:
        if page_text.strip():
            entities = next(result_iter)
            all_entities.extend(entities)
            deid_pages.append(replace_entities(page_text, entities, session_key, patient_id))
        else:
            deid_pages.append("")

    deidentified_text = "\n\n".join(deid_pages)
    return raw_text, deidentified_text, page_count, all_entities
