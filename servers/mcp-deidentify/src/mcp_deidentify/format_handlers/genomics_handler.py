"""Genomics file de-identification handler for mcp-deidentify.

Supported file types:
  vcf  -- strips PII from ## meta-information header lines only
  h5ad -- de-identifies string values in adata.uns only
  cns  -- strips PII from # comment lines at file top only

Data rows (variant records, cell x gene matrices, CNV segments) are never modified.

DRY_RUN=true: no file I/O; returns synthetic pre-built output.
"""

import logging
import re
from pathlib import Path

from mcp_deidentify import config
from mcp_deidentify.engine import extract_entities, replace_entities

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DRY_RUN synthetic outputs
# ---------------------------------------------------------------------------

_SYNTHETIC_VCF_HEADER = """\
##fileformat=VCFv4.2
##fileDate=DOS-2022-06
##source=LAB-DIR-001
##reference=GRCh37
##SAMPLE=<ID=SPECIMEN-001,Tissue=Tumor>
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
"""

_SYNTHETIC_H5AD_UNS = {
    "patient_id": "PAT-SYNTHETIC-001",
    "accession": "ACCESSION-001",
    "synthetic_data": True,
    "fields_modified": ["patient_id", "accession"],
}

_SYNTHETIC_CNS_HEADER = """\
# de-identified by mcp-deidentify
# sample: SPECIMEN-001
# source: LAB-DIR-001
"""

# ---------------------------------------------------------------------------
# VCF handler
# ---------------------------------------------------------------------------

# Fields in ## lines whose values should be replaced
_VCF_SCRUB_KEYS = {"source", "filedate", "reference", "created", "center", "sample"}
_VCF_SAMPLE_RE = re.compile(r"^##SAMPLE=", re.IGNORECASE)


async def deidentify_vcf(
    vcf_path: str,
    patient_id: str,
    session_key: dict,
) -> tuple[str, list[str], list[dict]]:
    """De-identify VCF ## header lines.

    Returns (deidentified_content, fields_modified, entities).
    """
    if config.DRY_RUN:
        from mcp_deidentify.engine import SYNTHETIC_ENTITIES

        return _SYNTHETIC_VCF_HEADER, ["fileDate", "source", "SAMPLE"], list(SYNTHETIC_ENTITIES)

    lines = Path(vcf_path).read_text().splitlines(keepends=True)
    out_lines: list[str] = []
    all_entities: list[dict] = []
    fields_modified: list[str] = []

    for line in lines:
        if line.startswith("##"):
            if _VCF_SAMPLE_RE.match(line):
                # Replace the whole SAMPLE line value
                entities = await extract_entities(line)
                if entities:
                    all_entities.extend(entities)
                    line = replace_entities(line, entities, session_key, patient_id)
                    fields_modified.append("SAMPLE")
            elif "=" in line:
                key_part = line[2 : line.index("=")].strip().lower()
                if key_part in _VCF_SCRUB_KEYS:
                    val_part = line[line.index("=") + 1 :]
                    entities = await extract_entities(val_part)
                    if entities:
                        all_entities.extend(entities)
                        new_val = replace_entities(val_part, entities, session_key, patient_id)
                        line = line[: line.index("=") + 1] + new_val
                        fields_modified.append(line[2 : line.index("=")].strip())
        out_lines.append(line)

    return "".join(out_lines), fields_modified, all_entities


# ---------------------------------------------------------------------------
# h5ad handler
# ---------------------------------------------------------------------------


async def deidentify_h5ad(
    h5ad_path: str,
    patient_id: str,
    session_key: dict,
) -> tuple[dict, list[str], list[dict]]:
    """De-identify string values in adata.uns. Writes modified h5ad back to same path.

    Returns (deidentified_uns_dict, fields_modified, entities_found).
    """
    if config.DRY_RUN:
        from mcp_deidentify.engine import SYNTHETIC_ENTITIES

        return _SYNTHETIC_H5AD_UNS, ["patient_id", "accession"], list(SYNTHETIC_ENTITIES)

    import anndata as ad

    adata = ad.read_h5ad(h5ad_path)
    all_entities: list[dict] = []
    fields_modified: list[str] = []

    for key, val in list(adata.uns.items()):
        if isinstance(val, str) and len(val) >= 4:
            entities = await extract_entities(val)
            if entities:
                all_entities.extend(entities)
                adata.uns[key] = replace_entities(val, entities, session_key, patient_id)
                fields_modified.append(key)

    adata.write_h5ad(h5ad_path)
    logger.info(
        f"De-identified h5ad written: {h5ad_path} " f"({len(fields_modified)} .uns fields modified)"
    )
    return dict(adata.uns), fields_modified, all_entities


# ---------------------------------------------------------------------------
# CNS handler
# ---------------------------------------------------------------------------


async def deidentify_cns(
    cns_path: str,
    patient_id: str,
    session_key: dict,
) -> tuple[str, list[str], list[dict]]:
    """De-identify # comment lines at the top of a CNVkit .cns file.

    Returns (deidentified_content, fields_modified, entities_found).
    """
    if config.DRY_RUN:
        from mcp_deidentify.engine import SYNTHETIC_ENTITIES

        return _SYNTHETIC_CNS_HEADER, ["sample", "source"], list(SYNTHETIC_ENTITIES)

    lines = Path(cns_path).read_text().splitlines(keepends=True)
    out_lines: list[str] = []
    all_entities: list[dict] = []
    fields_modified: list[str] = []

    for line in lines:
        if line.startswith("#"):
            entities = await extract_entities(line)
            if entities:
                all_entities.extend(entities)
                line = replace_entities(line, entities, session_key, patient_id)
                fields_modified.append(line.strip())
        out_lines.append(line)

    return "".join(out_lines), fields_modified, all_entities


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


async def deidentify_genomics_file(
    file_path: str,
    patient_id: str,
    session_key: dict,
    file_type: str = "vcf",
) -> tuple[str, list[str], list[dict]]:
    """Dispatch to the appropriate genomics handler by file_type.

    Args:
        file_path:   Path to the genomics file.
        patient_id:  Patient identifier.
        session_key: Mutable anonymization key dict.
        file_type:   One of "vcf", "h5ad", "cns".

    Returns:
        Tuple of (deidentified_content_or_repr, fields_modified, entities_found).
    """
    if file_type == "vcf":
        return await deidentify_vcf(file_path, patient_id, session_key)
    elif file_type == "h5ad":
        uns_dict, fields, entities = await deidentify_h5ad(file_path, patient_id, session_key)
        return str(uns_dict), fields, entities
    elif file_type == "cns":
        return await deidentify_cns(file_path, patient_id, session_key)
    else:
        raise ValueError(f"Unsupported file_type: '{file_type}'. Must be one of: vcf, h5ad, cns")
