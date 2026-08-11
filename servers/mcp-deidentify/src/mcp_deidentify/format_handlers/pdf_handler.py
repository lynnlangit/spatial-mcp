"""PDF text de-identification handler for mcp-deidentify.

Extracts the *text layer* of a PDF via pdfplumber and de-identifies each page.
Returns de-identified plain text. It does NOT produce a redacted PDF file, and
it cannot see text that exists only as pixels.

That second limitation matters clinically: most scanned lab reports, faxed
referrals and signed consent forms have no text layer at all. pdfplumber returns
an empty string for such a page, which previously flowed through as a successful
result with zero entities found -- indistinguishable from "this document contains
no PII". Pages with no extractable text are now reported explicitly via
``pages_without_text`` and, when no page yields text, ``status="no_text_layer"``.

DRY_RUN=true: no file reads, no Haiku calls; returns synthetic fixture output.
"""

import asyncio
import logging
from typing import Any, Dict, List

from mcp_deidentify import config
from mcp_deidentify.engine import extract_entities, replace_entities

logger = logging.getLogger(__name__)

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
) -> Dict[str, Any]:
    """Extract and de-identify the text layer of a PDF file.

    Args:
        pdf_path:    Path to the source PDF file.
        patient_id:  Patient identifier for code generation.
        session_key: Mutable anonymization key dict from KeyManager.

    Returns:
        {
          "status": "ok" | "no_text_layer",
          "raw_text": <str>,
          "deidentified_text": <str>,
          "page_count": <int>,
          "pages_without_text": [<int>, ...],   # 1-indexed
          "entities_found": [...],
        }
    """
    if config.DRY_RUN:
        from mcp_deidentify.engine import SYNTHETIC_ENTITIES

        return {
            "status": "ok",
            "raw_text": _SYNTHETIC_PDF_TEXT,
            "deidentified_text": _SYNTHETIC_PDF_TEXT,
            "page_count": 3,
            "pages_without_text": [],
            "entities_found": list(SYNTHETIC_ENTITIES),
        }

    import pdfplumber

    page_texts: List[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_texts.append(page.extract_text() or "")

    pages_without_text = [i for i, t in enumerate(page_texts, start=1) if not t.strip()]
    raw_text = "\n\n".join(page_texts)

    if len(pages_without_text) == page_count:
        logger.warning(
            "%s: no extractable text on any of %d pages (likely a scan)", pdf_path, page_count
        )
        return {
            "status": "no_text_layer",
            "error": (
                f"No extractable text on any of the {page_count} page(s). This PDF is "
                f"most likely a scan or image-only document. It has NOT been checked "
                f"for PII -- OCR is required before de-identification."
            ),
            "raw_text": "",
            "deidentified_text": "",
            "page_count": page_count,
            "pages_without_text": pages_without_text,
            "entities_found": [],
        }

    if pages_without_text:
        logger.warning(
            "%s: no extractable text on page(s) %s -- these were NOT de-identified",
            pdf_path,
            pages_without_text,
        )

    # De-identify all pages that have text, in parallel
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

    return {
        "status": "ok",
        "raw_text": raw_text,
        "deidentified_text": "\n\n".join(deid_pages),
        "page_count": page_count,
        "pages_without_text": pages_without_text,
        "entities_found": all_entities,
    }
