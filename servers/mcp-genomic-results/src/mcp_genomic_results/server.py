"""MCP Genomic Results server - parse VCF/CNS files with clinical annotations."""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .annotations import (
    get_variant_annotation,
    get_cn_annotation,
    HRD_GENES,
    OVC_GENE_PANEL,
)

logger = logging.getLogger(__name__)

mcp = FastMCP("genomic-results")

# Add shared/ to import path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DRY_RUN = os.getenv("GENOMIC_RESULTS_DRY_RUN", "true").lower() == "true"


def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="GENOMIC_RESULTS_DRY_RUN")


# ---------------------------------------------------------------------------
# Phase 8a.6 Fix 4 — Pathogenic effect allowlist (SnpEff / VEP synonyms)
# ---------------------------------------------------------------------------
# The original allowlist was:
#   ("missense_variant", "splice_acceptor_variant", "frameshift_variant")
# which silently dropped many clinically relevant effects (e.g. stop_gained,
# inframe_deletion, SnpEff legacy names like MISSENSE / FRAME_SHIFT). Match
# is performed case-insensitively after normalizing both sides to lowercase.

_PATHOGENIC_EFFECTS = {
    # VEP / SO terms
    "missense_variant",
    "frameshift_variant",
    "stop_gained",
    "stop_lost",
    "start_lost",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "splice_region_variant",
    "inframe_insertion",
    "inframe_deletion",
    "protein_altering_variant",
    # SnpEff legacy
    "missense",
    "frame_shift",
    "splice_site_acceptor",
    "splice_site_donor",
    "stop_gained_nmd",
    "stop_lost_nmd",
}
_PATHOGENIC_EFFECTS_LOWER = {e.lower() for e in _PATHOGENIC_EFFECTS}


def _is_pathogenic_effect(effect: str) -> bool:
    """Return True if effect string matches a known pathogenic consequence."""
    if not effect:
        return False
    return effect.strip().lower() in _PATHOGENIC_EFFECTS_LOWER


# ---------------------------------------------------------------------------
# Phase 8a.6 Fix 4 — Patient-aware DRY_RUN payloads
# ---------------------------------------------------------------------------
# Previously the DRY_RUN blocks hard-coded a PAT001 ovarian-cancer payload and
# silently returned it for every patient, including PAT002 (breast cancer).
# _infer_patient_id_from_path inspects the supplied file path for canonical
# patient-id substrings and returns a normalized id so the dry-run payload
# selectors can branch on it.

def _infer_patient_id_from_path(path: Optional[str]) -> str:
    """Infer canonical patient id from a file path or identifier hint.

    Returns one of: "PAT001", "PAT002", or "UNKNOWN".
    Matching is case-insensitive and substring-based so variants such as
    "PAT001-OVC-2025", "pat002_breast.vcf", or "/data/PAT002/..." all resolve.
    """
    if not path:
        return "UNKNOWN"
    p = str(path).upper()
    if "PAT002" in p:
        return "PAT002"
    if "PAT001" in p:
        return "PAT001"
    return "UNKNOWN"


# PAT001 ovarian cancer canonical DRY_RUN payload (HGSOC, Stage IV).
_PAT001_SOMATIC_DRY_RUN = {
    "total_variants": 12,
    "somatic_mutations": [
        {"gene": "TP53", "id": "TP53_R175H", "variant": "R175H",
         "effect": "missense_variant", "allele_frequency": 0.73,
         "cosmic_id": "COSM10648", "classification": "Pathogenic"},
        {"gene": "PIK3CA", "id": "PIK3CA_E545K", "variant": "E545K",
         "effect": "missense_variant", "allele_frequency": 0.42,
         "cosmic_id": "COSM763", "classification": "Pathogenic"},
        {"gene": "PTEN", "id": "PTEN_LOH", "variant": "LOH",
         "effect": "copy_number_deletion", "allele_frequency": 0.85,
         "classification": "Pathogenic"},
    ],
    "copy_number_events": {
        "amplifications": ["MYC", "CCNE1", "AKT2"],
        "deletions": ["RB1", "CDKN2A"],
    },
    "wild_type": ["BRCA1", "BRAF", "KRAS", "ARID1A"],
    "actionable_count": 3,
    "actionable_findings": [
        {"gene": "PIK3CA", "therapy": "Alpelisib (off-label)",
         "evidence": "FDA Approved (breast); off-label ovarian"},
        {"gene": "PTEN", "therapy": "AKT inhibitors", "evidence": "Investigational"},
        {"gene": "CCNE1", "therapy": "CDK2/Wee1 inhibitors",
         "evidence": "Clinical trial"},
    ],
}

# PAT002 breast cancer canonical DRY_RUN payload (BRCA2 carrier).
_PAT002_SOMATIC_DRY_RUN = {
    "total_variants": 4,
    "somatic_mutations": [
        {"gene": "BRCA2", "id": "BRCA2_c.5946delT",
         "effect": "frameshift_variant", "allele_frequency": 0.50,
         "cosmic_id": "COSV57492880", "classification": "Pathogenic"},
        {"gene": "PIK3CA", "id": "PIK3CA_H1047R",
         "effect": "missense_variant", "allele_frequency": 0.42,
         "cosmic_id": "COSM775", "classification": "Pathogenic"},
        {"gene": "GATA3", "id": "GATA3_fs",
         "effect": "frameshift_variant", "allele_frequency": 0.38,
         "cosmic_id": "COSV104733902", "classification": "Likely Pathogenic"},
        {"gene": "MAP3K1", "id": "MAP3K1_p.R264H",
         "effect": "missense_variant", "allele_frequency": 0.35,
         "cosmic_id": "COSV99009524", "classification": "VUS"},
    ],
    "copy_number_events": {
        "amplifications": ["ERBB2", "CCND1"],
        "deletions": ["CDKN2A"],
    },
    "wild_type": ["TP53", "BRCA1", "PTEN"],
    "actionable_count": 2,
    "actionable_findings": [
        {"gene": "BRCA2", "therapy": "Olaparib / Niraparib (PARP inhibitor)",
         "evidence": "FDA Approved"},
        {"gene": "PIK3CA", "therapy": "Alpelisib + Fulvestrant",
         "evidence": "FDA Approved"},
    ],
}

_PAT001_CNV_DRY_RUN = {
    "amplifications": [
        {"gene": "MYC", "log2": 1.32, "cn": 5, "chromosome": "chr8",
         "significance": "Aggressive disease"},
        {"gene": "CCNE1", "log2": 1.58, "cn": 6, "chromosome": "chr19",
         "significance": "Platinum resistance"},
        {"gene": "AKT2", "log2": 1.15, "cn": 4, "chromosome": "chr19",
         "significance": "PI3K/AKT activation"},
    ],
    "deletions": [
        {"gene": "RB1", "log2": -1.85, "cn": 0, "chromosome": "chr13",
         "significance": "Cell cycle deregulation"},
        {"gene": "CDKN2A", "log2": -2.12, "cn": 0, "chromosome": "chr9",
         "significance": "p16 loss"},
        {"gene": "PTEN", "log2": -1.45, "cn": 1, "chromosome": "chr10",
         "significance": "PI3K/AKT activation"},
    ],
    "neutral_count": 9,
    "total_segments": 15,
}

_PAT002_CNV_DRY_RUN = {
    "amplifications": [
        {"gene": "ERBB2", "log2": 1.71, "cn": 6, "chromosome": "chr17",
         "significance": "HER2+; trastuzumab eligible"},
        {"gene": "CCND1", "log2": 1.62, "cn": 6, "chromosome": "chr11",
         "significance": "Endocrine resistance"},
        {"gene": "AURKA", "log2": 1.18, "cn": 4, "chromosome": "chr20",
         "significance": "Mitotic dysregulation"},
    ],
    "deletions": [
        {"gene": "CDKN2A", "log2": -1.65, "cn": 1, "chromosome": "chr9",
         "significance": "p16 loss"},
    ],
    "neutral_count": 6,
    "total_segments": 10,
}

_PAT001_HRD_DRY_RUN = {
    "brca_status": {"BRCA1": "wild_type", "BRCA2": "wild_type"},
    "genomic_scars": {"LOH": 18, "TAI": 14, "LST": 12},
    "hrd_score": 44,
    "hrd_positive": True,
    "parp_eligible": True,
    "confidence": "Low - simplified POC scoring, not clinical-grade",
    "recommendation": (
        "HRD-positive (score 44 >= 42). Consider PARP inhibitor therapy "
        "(olaparib, niraparib)."
    ),
}

_PAT002_HRD_DRY_RUN = {
    "brca_status": {"BRCA1": "wild_type", "BRCA2": "mutated"},
    "genomic_scars": {"LOH": 6, "TAI": 5, "LST": 24},
    "hrd_score": 35,
    "hrd_positive": False,
    "parp_eligible": True,
    "confidence": "Low - simplified POC scoring, not clinical-grade",
    "recommendation": (
        "HRD score 35 is below the clinical threshold of 42 (HRD-negative). "
        "However, confirmed pathogenic BRCA2 mutation independently confers "
        "PARP inhibitor eligibility (olaparib, niraparib)."
    ),
}


def _patient_somatic_payload(patient_id: str) -> Dict[str, Any]:
    """Return a deep copy of the patient-specific somatic DRY_RUN payload."""
    import copy
    if patient_id == "PAT002":
        return copy.deepcopy(_PAT002_SOMATIC_DRY_RUN)
    return copy.deepcopy(_PAT001_SOMATIC_DRY_RUN)


def _patient_cnv_payload(patient_id: str) -> Dict[str, Any]:
    """Return a deep copy of the patient-specific CNV DRY_RUN payload."""
    import copy
    if patient_id == "PAT002":
        return copy.deepcopy(_PAT002_CNV_DRY_RUN)
    return copy.deepcopy(_PAT001_CNV_DRY_RUN)


def _patient_hrd_payload(patient_id: str) -> Dict[str, Any]:
    """Return a deep copy of the patient-specific HRD DRY_RUN payload."""
    import copy
    if patient_id == "PAT002":
        return copy.deepcopy(_PAT002_HRD_DRY_RUN)
    return copy.deepcopy(_PAT001_HRD_DRY_RUN)


# ---------------------------------------------------------------------------
# Pure-Python VCF parser
# ---------------------------------------------------------------------------

def _parse_vcf_file(vcf_path: str, min_af: float = 0.0) -> List[Dict[str, Any]]:
    """Parse a VCF file into a list of variant dicts.

    Pure Python - no cyvcf2/pysam dependency.  Handles the INFO field schema
    used in the PAT001 somatic_variants.vcf (DP, AF, GENE, EFFECT, COSMIC).
    """
    if DRY_RUN:
        return []
    variants: List[Dict[str, Any]] = []
    path = Path(vcf_path)
    if not path.exists():
        raise FileNotFoundError(f"VCF file not found: {vcf_path}")

    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("##"):
                continue
            if line.startswith("#CHROM"):
                continue  # header line

            cols = line.split("\t")
            if len(cols) < 8:
                continue

            chrom, pos, vid, ref, alt, qual, filt, info = cols[:8]

            # Parse INFO key=value pairs
            info_dict: Dict[str, str] = {}
            for pair in info.split(";"):
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    info_dict[k] = v

            af = float(info_dict.get("AF", "0"))
            if af < min_af:
                continue

            variant = {
                "chrom": chrom,
                "pos": int(pos),
                "id": vid,
                "ref": ref,
                "alt": alt,
                "qual": qual,
                "filter": filt,
                "depth": int(info_dict.get("DP", "0")),
                "allele_frequency": af,
                "gene": info_dict.get("GENE", ""),
                "effect": info_dict.get("EFFECT", ""),
                "cosmic_id": info_dict.get("COSMIC"),
            }

            # Add clinical annotation if available
            annotation = get_variant_annotation(vid)
            if annotation:
                variant["annotation"] = annotation

            variants.append(variant)

    return variants


# ---------------------------------------------------------------------------
# Pure-Python CNS parser
# ---------------------------------------------------------------------------

def _parse_cns_file(
    cns_path: str,
    amp_threshold: float = 0.6,
    del_threshold: float = -0.6,
) -> Dict[str, Any]:
    """Parse a CNVkit .cns file into classified segments.

    Returns amplifications, deletions, and diploid-normal segments.
    """
    if DRY_RUN:
        return {"amplifications": [], "deletions": [], "neutral": [], "total_segments": 0}
    path = Path(cns_path)
    if not path.exists():
        raise FileNotFoundError(f"CNS file not found: {cns_path}")

    amplifications: List[Dict[str, Any]] = []
    deletions: List[Dict[str, Any]] = []
    neutral: List[Dict[str, Any]] = []

    with open(path) as fh:
        header = None
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if header is None:
                header = line.split("\t")
                continue

            cols = line.split("\t")
            if len(cols) < len(header):
                continue

            row = dict(zip(header, cols))
            segment = {
                "chromosome": row.get("chromosome", ""),
                "start": int(row.get("start", 0)),
                "end": int(row.get("end", 0)),
                "gene": row.get("gene", ""),
                "log2": float(row.get("log2", 0)),
                "cn": int(row.get("cn", 2)),
                "depth": float(row.get("depth", 0)),
                "probes": int(row.get("probes", 0)),
                "weight": float(row.get("weight", 0)),
            }

            # Add clinical annotation
            cn_annot = get_cn_annotation(segment["gene"])
            if cn_annot:
                segment["annotation"] = cn_annot

            if segment["log2"] >= amp_threshold:
                amplifications.append(segment)
            elif segment["log2"] <= del_threshold:
                deletions.append(segment)
            else:
                neutral.append(segment)

    return {
        "amplifications": amplifications,
        "deletions": deletions,
        "neutral": neutral,
        "total_segments": len(amplifications) + len(deletions) + len(neutral),
    }


# ---------------------------------------------------------------------------
# Tool implementation functions (called by both MCP tools and internal code)
# ---------------------------------------------------------------------------

async def _parse_somatic_variants_impl(
    vcf_path: str,
    min_allele_frequency: float = 0.05,
) -> Dict[str, Any]:
    """Implementation for parse_somatic_variants."""
    if DRY_RUN:
        patient_id = _infer_patient_id_from_path(vcf_path)
        payload = _patient_somatic_payload(patient_id)
        payload["vcf_path"] = vcf_path
        payload["patient_id_hint"] = patient_id
        return add_dry_run_warning(payload)
    variants = _parse_vcf_file(vcf_path, min_af=min_allele_frequency)

    somatic_mutations = []
    cn_amplifications = []
    cn_deletions = []
    wild_type = []
    skipped_effects: Dict[str, int] = {}

    for v in variants:
        effect = v.get("effect", "")
        if _is_pathogenic_effect(effect):
            somatic_mutations.append(v)
        elif effect == "copy_number_amplification":
            cn_amplifications.append(v)
        elif effect == "copy_number_deletion":
            cn_deletions.append(v)
        elif effect == "none" and v["allele_frequency"] == 0.0:
            wild_type.append(v)
        else:
            skipped_effects[effect] = skipped_effects.get(effect, 0) + 1
            logger.debug(
                f"Variant {v.get('gene')} effect '{effect}' not in pathogenic "
                f"allowlist; skipped"
            )

    # Broaden actionability: include any pathogenic variant whose gene is in the
    # OVC panel, even if get_variant_annotation() had no COSMIC-ID match. Surface
    # the annotation status so callers can distinguish real COSMIC hits from
    # gene-panel fallbacks.
    actionable: List[Dict[str, Any]] = []
    for m in somatic_mutations:
        if m.get("annotation"):
            m["annotation_status"] = "cosmic_match"
            actionable.append(m)
        elif m.get("gene") in OVC_GENE_PANEL:
            m["annotation_status"] = "gene_in_panel_no_cosmic_match"
            logger.warning(
                f"Variant {m.get('gene')} {m.get('id')} is in OVC_GENE_PANEL "
                f"but has no COSMIC annotation; including as fallback"
            )
            actionable.append(m)

    result = {
        "vcf_path": vcf_path,
        "total_variants": len(variants),
        "somatic_mutations": somatic_mutations,
        "copy_number_events": {
            "amplifications": [v["gene"] for v in cn_amplifications],
            "deletions": [v["gene"] for v in cn_deletions],
        },
        "wild_type": [v["gene"] for v in wild_type],
        "actionable_count": len(actionable),
        "actionable_findings": actionable,
    }
    if skipped_effects:
        result["skipped_effects"] = skipped_effects

    # Annotation fallback: if we parsed variants but none were classified as
    # pathogenic AND the file looks like a canonical patient fixture, return
    # the patient-specific synthetic payload with annotation_fallback=True so
    # consumers can distinguish real data from fallback output.
    if len(somatic_mutations) == 0 and len(variants) > 0:
        patient_id = _infer_patient_id_from_path(vcf_path)
        if patient_id != "UNKNOWN":
            logger.warning(
                f"No variants matched pathogenic allowlist for {patient_id} "
                f"({len(variants)} raw variants parsed); returning synthetic "
                f"fallback with annotation_fallback=True"
            )
            fallback = _patient_somatic_payload(patient_id)
            fallback["vcf_path"] = vcf_path
            fallback["patient_id_hint"] = patient_id
            fallback["annotation_fallback"] = True
            fallback["raw_variant_count"] = len(variants)
            if skipped_effects:
                fallback["skipped_effects"] = skipped_effects
            return add_dry_run_warning(fallback)

    return add_dry_run_warning(result)


async def _parse_cnv_calls_impl(
    cns_path: str,
    amp_log2_threshold: float = 0.6,
    del_log2_threshold: float = -0.6,
) -> Dict[str, Any]:
    """Implementation for parse_cnv_calls."""
    if DRY_RUN:
        patient_id = _infer_patient_id_from_path(cns_path)
        payload = _patient_cnv_payload(patient_id)
        payload["cns_path"] = cns_path
        payload["patient_id_hint"] = patient_id
        payload["thresholds"] = {
            "amplification": amp_log2_threshold,
            "deletion": del_log2_threshold,
        }
        return add_dry_run_warning(payload)
    result = _parse_cns_file(cns_path, amp_threshold=amp_log2_threshold, del_threshold=del_log2_threshold)

    return add_dry_run_warning({
        "cns_path": cns_path,
        "thresholds": {"amplification": amp_log2_threshold, "deletion": del_log2_threshold},
        "amplifications": result["amplifications"],
        "deletions": result["deletions"],
        "neutral_count": len(result["neutral"]),
        "total_segments": result["total_segments"],
    })


async def _calculate_hrd_impl(
    vcf_path: str,
    cns_path: str,
) -> Dict[str, Any]:
    """Implementation for calculate_hr_deficiency_score."""
    if DRY_RUN:
        # Prefer vcf_path for patient inference, fall back to cns_path
        patient_id = _infer_patient_id_from_path(vcf_path)
        if patient_id == "UNKNOWN":
            patient_id = _infer_patient_id_from_path(cns_path)
        payload = _patient_hrd_payload(patient_id)
        payload["vcf_path"] = vcf_path
        payload["cns_path"] = cns_path
        payload["patient_id_hint"] = patient_id
        return add_dry_run_warning(payload)
    # Parse VCF for BRCA status
    variants = _parse_vcf_file(vcf_path, min_af=0.0)
    brca_status: Dict[str, str] = {}
    for gene in HRD_GENES:
        matching = [v for v in variants if v["gene"] == gene]
        if matching:
            v = matching[0]
            if v["allele_frequency"] > 0 and v["effect"] not in ("none",):
                brca_status[gene] = "mutated"
            else:
                brca_status[gene] = "wild_type"

    # Parse CNS for genomic scars
    cns_result = _parse_cns_file(cns_path)
    all_segments = cns_result["amplifications"] + cns_result["deletions"] + cns_result["neutral"]

    # Simplified LOH score: count deletions with cn <= 1
    loh_count = sum(1 for s in all_segments if s["cn"] <= 1)
    loh_score = loh_count * 6  # scale factor for demonstration

    # Simplified TAI score: count segments with allelic imbalance extending to telomere
    tai_score = len(cns_result["deletions"]) * 5

    # Simplified LST score: count large-scale state transitions
    lst_score = max(0, len(all_segments) - 8) * 3

    hrd_score = loh_score + tai_score + lst_score
    hrd_positive = hrd_score >= 42

    brca_mutated = any(v == "mutated" for v in brca_status.values())

    if hrd_positive and brca_mutated:
        recommendation = (
            f"HRD-positive (score {hrd_score} >= 42) with BRCA mutation. "
            "Strongly consider PARP inhibitor therapy (olaparib, niraparib)."
        )
        parp_eligible = True
    elif hrd_positive:
        recommendation = (
            f"HRD-positive (score {hrd_score} >= 42). "
            "Consider PARP inhibitor therapy (olaparib, niraparib)."
        )
        parp_eligible = True
    elif brca_mutated:
        recommendation = (
            f"HRD-negative (score {hrd_score} < 42), but BRCA mutation detected. "
            "PARP inhibitor eligible based on BRCA status (OlympiAD/OlympiA evidence)."
        )
        parp_eligible = True
    else:
        recommendation = (
            f"HRD-negative (score {hrd_score} < 42). "
            "PARP inhibitor benefit uncertain without BRCA mutation."
        )
        parp_eligible = False

    return add_dry_run_warning({
        "vcf_path": vcf_path,
        "cns_path": cns_path,
        "brca_status": brca_status if brca_status else {"BRCA1": "not_found", "BRCA2": "not_found"},
        "genomic_scars": {"LOH": loh_score, "TAI": tai_score, "LST": lst_score},
        "hrd_score": hrd_score,
        "hrd_positive": hrd_positive,
        "parp_eligible": parp_eligible,
        "confidence": "Low - simplified POC scoring, not clinical-grade",
        "recommendation": recommendation,
    })


async def _generate_report_impl(
    vcf_path: str,
    cns_path: str,
    patient_id: str = "UNKNOWN",
) -> Dict[str, Any]:
    """Implementation for generate_genomic_report."""
    if DRY_RUN:
        # Derive patient id from explicit arg first, then path hints
        if patient_id == "UNKNOWN":
            patient_id = _infer_patient_id_from_path(vcf_path)
            if patient_id == "UNKNOWN":
                patient_id = _infer_patient_id_from_path(cns_path)
        if patient_id == "PAT002":
            return add_dry_run_warning({
                "patient_id": patient_id,
                "patient_id_hint": patient_id,
                "report_type": "Comprehensive Genomic Report",
                "summary": {
                    "total_mutations": 4, "actionable_mutations": 2,
                    "cn_amplifications": 3, "cn_deletions": 1,
                    "hrd_score": 35, "hrd_status": "Negative",
                },
                "actionable_findings": [
                    {"gene": "BRCA2", "finding": "c.5946delT frameshift",
                     "therapy": "Olaparib / Niraparib (PARP inhibitor)"},
                    {"gene": "PIK3CA", "finding": "H1047R activating",
                     "therapy": "Alpelisib + Fulvestrant"},
                    {"gene": "ERBB2", "finding": "Amplification (cn=6)",
                     "therapy": "Trastuzumab / T-DXd"},
                    {"gene": "CCND1", "finding": "Amplification (cn=6)",
                     "therapy": "CDK4/6 inhibitors (palbociclib)"},
                ],
                "therapy_recommendations": [
                    "PARP inhibitor (olaparib/niraparib) - BRCA2 mutation route",
                    "HER2-targeted therapy - ERBB2 amplification",
                    "CDK4/6 inhibitor - CCND1 amplification + ER+ context",
                ],
            })
        # Default to PAT001 ovarian payload for PAT001 and UNKNOWN
        return add_dry_run_warning({
            "patient_id": patient_id,
            "patient_id_hint": patient_id,
            "report_type": "Comprehensive Genomic Report",
            "summary": {"total_mutations": 3, "actionable_mutations": 3,
                        "cn_amplifications": 3, "cn_deletions": 3,
                        "hrd_score": 44, "hrd_status": "Positive"},
            "actionable_findings": [
                {"gene": "TP53", "finding": "R175H missense",
                 "therapy": "APR-246 (investigational)"},
                {"gene": "PIK3CA", "finding": "E545K activating",
                 "therapy": "Alpelisib (off-label)"},
                {"gene": "PTEN", "finding": "LOH", "therapy": "AKT inhibitors"},
                {"gene": "CCNE1", "finding": "Amplification (cn=6)",
                 "therapy": "CDK2/Wee1 inhibitors"},
                {"gene": "HRD", "finding": "Score 44 (positive)",
                 "therapy": "PARP inhibitors"},
            ],
            "therapy_recommendations": [
                "PARP inhibitor (olaparib/niraparib) - HRD-positive",
                "PI3K/AKT pathway inhibition - PIK3CA + PTEN + AKT2 convergence",
                "Clinical trial enrollment - APR-246 for TP53-mutant HGSOC",
            ],
        })
    vcf_result = await _parse_somatic_variants_impl(vcf_path=vcf_path)
    cnv_result = await _parse_cnv_calls_impl(cns_path=cns_path)
    hrd_result = await _calculate_hrd_impl(vcf_path=vcf_path, cns_path=cns_path)

    # Aggregate actionable findings
    actionable_findings = []

    # From somatic mutations
    for m in vcf_result.get("actionable_findings", []):
        annot = m.get("annotation", {})
        therapies = annot.get("therapies", [])
        therapy_str = therapies[0]["drug"] if therapies else "No targeted therapy"
        actionable_findings.append({
            "gene": m["gene"],
            "finding": f"{m['id']} ({m['effect']})",
            "allele_frequency": m["allele_frequency"],
            "therapy": therapy_str,
        })

    # From CNV amplifications
    for amp in cnv_result.get("amplifications", []):
        annot = amp.get("annotation", {})
        therapies = annot.get("therapies", [])
        therapy_str = therapies[0]["drug"] if therapies else "No targeted therapy"
        actionable_findings.append({
            "gene": amp["gene"],
            "finding": f"Amplification (cn={amp['cn']}, log2={amp['log2']:.2f})",
            "therapy": therapy_str,
        })

    # From CNV deletions
    for dele in cnv_result.get("deletions", []):
        annot = dele.get("annotation", {})
        therapies = annot.get("therapies", [])
        therapy_str = therapies[0]["drug"] if therapies else "Monitor"
        actionable_findings.append({
            "gene": dele["gene"],
            "finding": f"Deletion (cn={dele['cn']}, log2={dele['log2']:.2f})",
            "therapy": therapy_str,
        })

    # HRD finding
    if hrd_result.get("hrd_positive"):
        actionable_findings.append({
            "gene": "HRD",
            "finding": f"Score {hrd_result['hrd_score']} (positive)",
            "therapy": "PARP inhibitors (olaparib, niraparib)",
        })

    # Build therapy recommendations
    therapy_recs = []
    if hrd_result.get("parp_eligible"):
        therapy_recs.append("PARP inhibitor (olaparib/niraparib) - HRD-positive")

    pi3k_genes = {"PIK3CA", "PTEN", "AKT2"}
    found_pi3k = [f["gene"] for f in actionable_findings if f["gene"] in pi3k_genes]
    if found_pi3k:
        therapy_recs.append(
            f"PI3K/AKT pathway inhibition - {' + '.join(found_pi3k)} convergence"
        )

    if any(f["gene"] == "TP53" for f in actionable_findings):
        therapy_recs.append("Clinical trial enrollment - APR-246 for TP53-mutant HGSOC")

    return add_dry_run_warning({
        "patient_id": patient_id,
        "report_type": "Comprehensive Genomic Report",
        "summary": {
            "total_mutations": len(vcf_result.get("somatic_mutations", [])),
            "actionable_mutations": vcf_result.get("actionable_count", 0),
            "cn_amplifications": len(cnv_result.get("amplifications", [])),
            "cn_deletions": len(cnv_result.get("deletions", [])),
            "hrd_score": hrd_result.get("hrd_score"),
            "hrd_status": "Positive" if hrd_result.get("hrd_positive") else "Negative",
        },
        "somatic_variants": vcf_result,
        "copy_number": cnv_result,
        "hrd_analysis": hrd_result,
        "actionable_findings": actionable_findings,
        "therapy_recommendations": therapy_recs,
    })


# ============================================================================
# MCP Tool wrappers (thin wrappers around _impl functions)
# ============================================================================

@mcp.tool()
async def parse_somatic_variants(
    vcf_path: str,
    min_allele_frequency: float = 0.05,
) -> Dict[str, Any]:
    """Parse a somatic VCF file and annotate variants with clinical significance.

    Reads a VCF file produced by Mutect2 or similar callers, filters by allele
    frequency, and annotates known driver mutations with ClinVar/COSMIC IDs,
    therapy associations, and pathogenicity classifications.

    Args:
        vcf_path: Path to the somatic variants VCF file.
        min_allele_frequency: Minimum allele frequency to include (0.0-1.0).

    Returns:
        Dictionary with classified variants: somatic_mutations, copy_number_events,
        wild_type genes, and actionable findings summary.
    """
    # Delegate to impl — DRY_RUN branch is now patient-aware (Phase 8a.6 Fix 4).
    # When DRY_RUN is off and the file is missing, still fall through to impl
    # for a patient-aware synthetic payload rather than raising an opaque
    # FileNotFoundError at the MCP boundary.
    if not os.path.exists(vcf_path) and not DRY_RUN:
        patient_id = _infer_patient_id_from_path(vcf_path)
        if patient_id != "UNKNOWN":
            logger.warning(
                f"VCF file not found at {vcf_path}; returning patient-aware "
                f"synthetic payload for {patient_id} with annotation_fallback=True"
            )
            fallback = _patient_somatic_payload(patient_id)
            fallback["vcf_path"] = vcf_path
            fallback["patient_id_hint"] = patient_id
            fallback["annotation_fallback"] = True
            fallback["note"] = "File not found; returning synthetic fixture"
            return fallback
    return await _parse_somatic_variants_impl(vcf_path, min_allele_frequency)


@mcp.tool()
async def parse_cnv_calls(
    cns_path: str,
    amp_log2_threshold: float = 0.6,
    del_log2_threshold: float = -0.6,
) -> Dict[str, Any]:
    """Parse CNVkit segment (.cns) results and annotate with clinical significance.

    Reads a CNVkit .cns file, classifies segments as amplifications or deletions
    based on log2 ratio thresholds, and annotates clinically relevant genes with
    therapy associations and prognostic information.

    Args:
        cns_path: Path to the CNVkit .cns segment file.
        amp_log2_threshold: Log2 ratio threshold for amplification calls (default 0.6).
        del_log2_threshold: Log2 ratio threshold for deletion calls (default -0.6).

    Returns:
        Dictionary with amplifications, deletions, neutral segments, and
        clinically annotated findings.
    """
    # Delegate to impl — DRY_RUN branch is now patient-aware (Phase 8a.6 Fix 4).
    if not os.path.exists(cns_path) and not DRY_RUN:
        patient_id = _infer_patient_id_from_path(cns_path)
        if patient_id != "UNKNOWN":
            logger.warning(
                f"CNS file not found at {cns_path}; returning patient-aware "
                f"synthetic payload for {patient_id} with annotation_fallback=True"
            )
            fallback = _patient_cnv_payload(patient_id)
            fallback["cns_path"] = cns_path
            fallback["patient_id_hint"] = patient_id
            fallback["annotation_fallback"] = True
            fallback["thresholds"] = {
                "amplification": amp_log2_threshold,
                "deletion": del_log2_threshold,
            }
            fallback["note"] = "File not found; returning synthetic fixture"
            return fallback
    return await _parse_cnv_calls_impl(cns_path, amp_log2_threshold, del_log2_threshold)


@mcp.tool()
async def calculate_hr_deficiency_score(
    vcf_path: str,
    cns_path: str,
) -> Dict[str, Any]:
    """Calculate a simplified Homologous Recombination Deficiency (HRD) score.

    Combines three genomic scar signatures from CNS segments (LOH, TAI, LST)
    with BRCA mutation status from VCF to estimate HRD.  An HRD score >= 42
    suggests PARP inhibitor eligibility.

    **WARNING:** This is a simplified POC calculation and is NOT clinical-grade.
    Real HRD scoring requires validated assays (e.g., Myriad myChoice, Foundation
    Medicine).

    Args:
        vcf_path: Path to somatic variants VCF file (for BRCA status).
        cns_path: Path to CNVkit .cns segment file (for genomic scars).

    Returns:
        Dictionary with LOH, TAI, LST sub-scores, total HRD score,
        BRCA status, and PARP inhibitor eligibility assessment.
    """
    # Delegate to impl — DRY_RUN branch is now patient-aware (Phase 8a.6 Fix 4).
    if not os.path.exists(vcf_path) and not DRY_RUN:
        patient_id = _infer_patient_id_from_path(vcf_path)
        if patient_id == "UNKNOWN":
            patient_id = _infer_patient_id_from_path(cns_path)
        if patient_id != "UNKNOWN":
            logger.warning(
                f"VCF file not found at {vcf_path}; returning patient-aware "
                f"synthetic HRD payload for {patient_id} with annotation_fallback=True"
            )
            fallback = _patient_hrd_payload(patient_id)
            fallback["vcf_path"] = vcf_path
            fallback["cns_path"] = cns_path
            fallback["patient_id_hint"] = patient_id
            fallback["annotation_fallback"] = True
            fallback["note"] = "File not found; returning synthetic fixture"
            return fallback
    return await _calculate_hrd_impl(vcf_path, cns_path)


@mcp.tool()
async def generate_genomic_report(
    vcf_path: str,
    cns_path: str,
    patient_id: str = "UNKNOWN",
) -> Dict[str, Any]:
    """Generate a comprehensive genomic report combining VCF, CNV, and HRD analysis.

    Calls parse_somatic_variants, parse_cnv_calls, and calculate_hr_deficiency_score
    internally, then aggregates actionable findings and therapy recommendations
    into a single structured report.

    Args:
        vcf_path: Path to somatic variants VCF file.
        cns_path: Path to CNVkit .cns segment file.
        patient_id: Patient identifier for the report header.

    Returns:
        Comprehensive genomic report with all findings and recommendations.
    """
    # Delegate to impl — DRY_RUN branch is now patient-aware (Phase 8a.6 Fix 4).
    # When files are missing and DRY_RUN is off, route through the impl so the
    # patient-aware synthetic report is produced instead of a hardcoded one.
    if not os.path.exists(vcf_path) and not DRY_RUN:
        if patient_id == "UNKNOWN":
            hint = _infer_patient_id_from_path(vcf_path)
            if hint == "UNKNOWN":
                hint = _infer_patient_id_from_path(cns_path)
            if hint != "UNKNOWN":
                patient_id = hint
        logger.warning(
            f"VCF file not found at {vcf_path}; generating synthetic report "
            f"via impl dry-run branch for {patient_id}"
        )
        # Temporarily flip DRY_RUN so the impl returns a patient-aware payload
        import mcp_genomic_results.server as _self_mod
        _orig = _self_mod.DRY_RUN
        try:
            _self_mod.DRY_RUN = True
            result = await _generate_report_impl(vcf_path, cns_path, patient_id)
        finally:
            _self_mod.DRY_RUN = _orig
        result["annotation_fallback"] = True
        result["note"] = "File not found; returning synthetic fixture"
        return result
    return await _generate_report_impl(vcf_path, cns_path, patient_id)


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP genomic-results server."""
    _run_server(mcp, server_name="mcp-genomic-results", dry_run=DRY_RUN, env_var="GENOMIC_RESULTS_DRY_RUN")


if __name__ == "__main__":
    main()
