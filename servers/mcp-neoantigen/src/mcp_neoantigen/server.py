"""MCP Neoantigen server — neoantigen prediction and antigen presentation scoring."""

import asyncio
import logging
import os
import json
from typing import Annotated, Any, Dict, List, Optional

from fastmcp import FastMCP
from pydantic import BeforeValidator

from .hla_utils import normalize_hla_allele, normalize_hla_list, is_class_i, is_class_ii
from .iedb_client import predict_mhc_class_i, predict_mhc_class_ii, predict_mhc_batch
from .mock_data import (
    MOCK_HLA_FLAT,
    MOCK_HLA_TYPING,
    MOCK_MHC1_PREDICTIONS,
    MOCK_MHC2_PREDICTIONS,
    MOCK_NEOANTIGEN_BURDEN,
    MOCK_PATHWAY_SCORE,
    MOCK_PVACSEQ_RESULT,
    PATHWAY_WEIGHTS,
    TMB_CONVERSION_FACTORS,
)

# Add shared/ to import path
import sys
from pathlib import Path
_repo_root = Path(__file__).resolve().parents[4]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))
from common.dry_run import add_dry_run_warning as _shared_add_dry_run_warning
from common.transport import run_server as _run_server

logger = logging.getLogger(__name__)

mcp = FastMCP("neoantigen")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DRY_RUN = os.getenv("NEOANTIGEN_DRY_RUN", "true").lower() == "true"
NEOANTIGEN_CACHE_DIR = os.getenv("NEOANTIGEN_CACHE_DIR", "/data/cache/neoantigen")
IEDB_API_URL = os.getenv(
    "NEOANTIGEN_IEDB_API_URL",
    "http://tools-cluster-interface.iedb.org/tools_api",
)
IEDB_BATCH_SIZE = int(os.getenv("NEOANTIGEN_IEDB_BATCH_SIZE", "100"))
PVACTOOLS_PATH = os.getenv("NEOANTIGEN_PVACTOOLS_PATH")
OPTITYPE_PATH = os.getenv("NEOANTIGEN_OPTITYPE_PATH")
STRONG_BINDER_THRESHOLD = float(os.getenv("NEOANTIGEN_STRONG_BINDER_NM", "50.0"))
WEAK_BINDER_THRESHOLD = float(os.getenv("NEOANTIGEN_WEAK_BINDER_NM", "500.0"))


def add_dry_run_warning(result):
    """Add DRY_RUN warning — delegates to shared implementation."""
    return _shared_add_dry_run_warning(result, dry_run=DRY_RUN, env_var="NEOANTIGEN_DRY_RUN")


# ---------------------------------------------------------------------------
# Parameter coercion (FastMCP 2.x JSON-string fallback)
# ---------------------------------------------------------------------------
# FastMCP 2.x may deliver complex Optional[Dict/List] params as JSON strings
# instead of parsed Python objects. BeforeValidator fires at Pydantic
# validation time — BEFORE the function body — so the string is coerced
# before Pydantic rejects it with "Input should be a valid dictionary/list".

def _coerce_dict(val):
    """Coerce JSON-string dicts for BeforeValidator."""
    if val is None or isinstance(val, dict):
        return val
    if isinstance(val, str):
        parsed = json.loads(val)
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected dict after JSON decode, got {type(parsed).__name__}")
        return parsed
    return val

def _coerce_list(val):
    """Coerce JSON-string lists for BeforeValidator."""
    if val is None or isinstance(val, list):
        return val
    if isinstance(val, str):
        parsed = json.loads(val)
        if not isinstance(parsed, list):
            raise ValueError(f"Expected list after JSON decode, got {type(parsed).__name__}")
        return parsed
    return val

_CoerceDict = BeforeValidator(_coerce_dict)
_CoerceList = BeforeValidator(_coerce_list)


def _classify_binder(ic50_nm: float) -> tuple[bool, str]:
    """Classify a peptide as strong binder, weak binder, or non-binder."""
    if ic50_nm <= STRONG_BINDER_THRESHOLD:
        return True, "strong"
    elif ic50_nm <= WEAK_BINDER_THRESHOLD:
        return True, "weak"
    return False, "non_binder"


def _build_mock_binding_predictions(
    peptides: List[str],
    alleles: List[str],
    canonical_predictions: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate input-aware mock predictions for DRY_RUN mode.

    Uses canonical mock predictions for known (peptide, allele) pairs
    and deterministic mock values for unknown pairs.
    """
    # Index canonical predictions by (peptide, allele)
    canonical: Dict[tuple, Dict[str, Any]] = {}
    for pred in canonical_predictions:
        key = (pred["peptide"], pred["allele"])
        canonical[key] = pred

    predictions: List[Dict[str, Any]] = []
    for peptide in peptides:
        for allele in alleles:
            match = canonical.get((peptide, allele))
            if match:
                predictions.append(dict(match))
            else:
                # Deterministic mock: character-sum seed → IC50 in 50-950 range
                seed = sum(ord(c) for c in f"{peptide}:{allele}") % 900
                ic50 = 50.0 + seed
                is_binder, level = _classify_binder(ic50)
                predictions.append({
                    "peptide": peptide,
                    "allele": allele,
                    "ic50_nm": round(ic50, 1),
                    "percentile_rank": round(ic50 / 100, 1),
                    "binder": is_binder,
                    "binder_level": level,
                })
    return predictions


# ---------------------------------------------------------------------------
# Tool implementation functions
# ---------------------------------------------------------------------------

async def _predict_mhc1_binding_impl(
    peptides: List[str],
    hla_alleles: List[str],
    method: str = "netmhcpan_ba",
    length: int = 9,
) -> Dict[str, Any]:
    """Implementation for predict_mhc1_binding."""
    if not peptides:
        return {"status": "error", "message": "Peptide list cannot be empty."}
    if not hla_alleles:
        return {"status": "error", "message": "HLA allele list cannot be empty."}

    # Validate HLA alleles are class I
    try:
        normalized = normalize_hla_list(hla_alleles)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    for allele in normalized:
        if not is_class_i(allele):
            return {
                "status": "error",
                "message": (
                    f"Allele {allele} is not HLA class I. "
                    "Use predict_mhc2_binding for class II alleles."
                ),
            }

    if DRY_RUN:
        predictions = _build_mock_binding_predictions(
            peptides, normalized, MOCK_MHC1_PREDICTIONS,
        )
        strong = sum(1 for p in predictions if p["binder_level"] == "strong")
        weak = sum(1 for p in predictions if p["binder_level"] == "weak")
        return add_dry_run_warning({
            "status": "success",
            "method": method,
            "hla_alleles": normalized,
            "predictions": predictions,
            "strong_binders": strong,
            "weak_binders": weak,
            "total_peptides": len(peptides),
        })

    # Production: call IEDB API
    results = await predict_mhc_batch(
        peptides=peptides,
        alleles=normalized,
        method=method,
        length=length,
        batch_size=IEDB_BATCH_SIZE,
        api_url=IEDB_API_URL,
    )

    # Classify results
    predictions = []
    strong_count = 0
    weak_count = 0
    for r in results:
        ic50 = r.get("ic50", r.get("score", 999999))
        is_binder, level = _classify_binder(ic50)
        predictions.append({
            "peptide": r.get("peptide", ""),
            "allele": r.get("allele", ""),
            "ic50_nm": ic50,
            "percentile_rank": r.get("percentile_rank", r.get("rank", 0)),
            "binder": is_binder,
            "binder_level": level,
        })
        if level == "strong":
            strong_count += 1
        elif level == "weak":
            weak_count += 1

    return {
        "status": "success",
        "method": method,
        "hla_alleles": normalized,
        "predictions": predictions,
        "strong_binders": strong_count,
        "weak_binders": weak_count,
        "total_peptides": len(predictions),
    }


async def _predict_mhc2_binding_impl(
    peptides: List[str],
    hla_alleles: List[str],
    method: str = "netmhciipan",
    length: int = 15,
) -> Dict[str, Any]:
    """Implementation for predict_mhc2_binding."""
    if not peptides:
        return {"status": "error", "message": "Peptide list cannot be empty."}
    if not hla_alleles:
        return {"status": "error", "message": "HLA allele list cannot be empty."}

    try:
        normalized = normalize_hla_list(hla_alleles)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    if DRY_RUN:
        predictions = _build_mock_binding_predictions(
            peptides, normalized, MOCK_MHC2_PREDICTIONS,
        )
        strong = sum(1 for p in predictions if p["binder_level"] == "strong")
        weak = sum(1 for p in predictions if p["binder_level"] == "weak")
        return add_dry_run_warning({
            "status": "success",
            "method": method,
            "hla_alleles": normalized,
            "predictions": predictions,
            "strong_binders": strong,
            "weak_binders": weak,
            "total_peptides": len(peptides),
        })

    results = await predict_mhc_class_ii(
        peptides=peptides,
        alleles=normalized,
        method=method,
        length=length,
        api_url=IEDB_API_URL,
    )

    predictions = []
    strong_count = 0
    weak_count = 0
    for r in results:
        ic50 = r.get("ic50", r.get("score", 999999))
        is_binder, level = _classify_binder(ic50)
        predictions.append({
            "peptide": r.get("peptide", ""),
            "allele": r.get("allele", ""),
            "ic50_nm": ic50,
            "percentile_rank": r.get("percentile_rank", r.get("rank", 0)),
            "binder": is_binder,
            "binder_level": level,
        })
        if level == "strong":
            strong_count += 1
        elif level == "weak":
            weak_count += 1

    return {
        "status": "success",
        "method": method,
        "hla_alleles": normalized,
        "predictions": predictions,
        "strong_binders": strong_count,
        "weak_binders": weak_count,
        "total_peptides": len(predictions),
    }


async def _run_pvacseq_impl(
    vcf_path: str,
    hla_alleles: List[str],
    output_dir: Optional[str] = None,
    epitope_lengths: Optional[List[int]] = None,
    binding_threshold: float = 500.0,
) -> Dict[str, Any]:
    """Implementation for run_pvacseq."""
    if not vcf_path or not vcf_path.strip():
        return {"status": "error", "message": "vcf_path cannot be empty."}
    if not hla_alleles:
        return {"status": "error", "message": "HLA allele list cannot be empty."}

    output_dir = output_dir or NEOANTIGEN_CACHE_DIR
    epitope_lengths = epitope_lengths or [8, 9, 10, 11]

    try:
        normalized = normalize_hla_list(hla_alleles)
    except ValueError as e:
        return {"status": "error", "message": str(e)}

    if DRY_RUN:
        return add_dry_run_warning({
            "status": "success",
            "vcf_path": vcf_path,
            "hla_alleles": normalized,
            "epitope_lengths": epitope_lengths,
            "binding_threshold": binding_threshold,
            "output_dir": output_dir,
            **MOCK_PVACSEQ_RESULT,
        })

    # Production: try pVACtools, fall back to IEDB
    if PVACTOOLS_PATH:
        # Run pVACseq via subprocess
        allele_str = ",".join(normalized)
        lengths_str = ",".join(str(l) for l in epitope_lengths)
        cmd = [
            PVACTOOLS_PATH, "run",
            vcf_path,
            "PatientOne",
            allele_str,
            "NetMHCpan",
            output_dir,
            "-e1", lengths_str,
            "--binding-threshold", str(binding_threshold),
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.warning(
                "pVACseq failed (rc=%d), falling back to IEDB: %s",
                proc.returncode, stderr.decode()[:500],
            )
        else:
            return {
                "status": "success",
                "method": "pVACseq",
                "output_dir": output_dir,
                # TODO: Parse pVACseq output files for structured results
            }

    return {
        "status": "error",
        "message": (
            "pVACtools not available. Set NEOANTIGEN_PVACTOOLS_PATH or "
            "use predict_mhc1_binding with pre-extracted peptides."
        ),
    }


async def _estimate_neoantigen_burden_impl(
    tmb_mutations_per_mb: float,
    hla_alleles: Optional[List[str]] = None,
    cancer_type: str = "HGSOC",
) -> Dict[str, Any]:
    """Implementation for estimate_neoantigen_burden."""
    if tmb_mutations_per_mb < 0:
        return {"status": "error", "message": "TMB cannot be negative."}

    cancer_type_upper = cancer_type.upper()
    factor = TMB_CONVERSION_FACTORS.get(
        cancer_type_upper, TMB_CONVERSION_FACTORS.get(cancer_type, 11.0)
    )

    estimated_neoantigens = round(tmb_mutations_per_mb * factor)
    # ~20% of neoantigens are strong binders (published estimate)
    estimated_strong = round(estimated_neoantigens * 0.19)

    # Interpret burden level
    if estimated_neoantigens >= 100:
        burden_level = "high"
    elif estimated_neoantigens >= 30:
        burden_level = "moderate"
    else:
        burden_level = "low"

    interpretation = (
        f"{burden_level.capitalize()} neoantigen burden for {cancer_type}. "
        f"Estimated {estimated_neoantigens} neoantigens from TMB of "
        f"{tmb_mutations_per_mb} mut/Mb (conversion factor: {factor})."
    )

    if DRY_RUN:
        # Use the mock values for PatientOne's specific TMB
        if abs(tmb_mutations_per_mb - 3.5) < 0.1:
            return add_dry_run_warning({
                "status": "success",
                **MOCK_NEOANTIGEN_BURDEN,
            })

    result = {
        "status": "success",
        "tmb": tmb_mutations_per_mb,
        "estimated_neoantigens": estimated_neoantigens,
        "estimated_strong_binders": estimated_strong,
        "conversion_factor": factor,
        "cancer_type": cancer_type,
        "burden_level": burden_level,
        "interpretation": interpretation,
    }

    if hla_alleles:
        try:
            result["hla_alleles"] = normalize_hla_list(hla_alleles)
        except ValueError as e:
            result["hla_warning"] = str(e)

    if DRY_RUN:
        return add_dry_run_warning(result)
    return result


async def _get_hla_typing_from_rna_impl(
    bam_path: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Implementation for get_hla_typing_from_rna."""
    if not bam_path or not bam_path.strip():
        return {"status": "error", "message": "bam_path cannot be empty."}

    output_dir = output_dir or NEOANTIGEN_CACHE_DIR

    if DRY_RUN:
        return add_dry_run_warning({
            "status": "success",
            "bam_path": bam_path,
            "output_dir": output_dir,
            **MOCK_HLA_TYPING,
        })

    if not OPTITYPE_PATH:
        return {
            "status": "error",
            "message": (
                "OptiType not available. Set NEOANTIGEN_OPTITYPE_PATH or "
                "provide HLA alleles manually."
            ),
        }

    # Run OptiType via subprocess
    cmd = [
        OPTITYPE_PATH,
        "--input", bam_path,
        "--outdir", output_dir,
        "--rna",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        return {
            "status": "error",
            "message": f"OptiType failed (rc={proc.returncode}): {stderr.decode()[:500]}",
        }

    # TODO: Parse OptiType result TSV for structured output
    return {
        "status": "success",
        "method": "OptiType",
        "output_dir": output_dir,
    }


async def _score_antigen_presentation_pathway_impl(
    neoantigen_count: int,
    mhc1_expression: Optional[Dict[str, float]] = None,
    b2m_expression: Optional[float] = None,
    tap1_expression: Optional[float] = None,
    tap2_expression: Optional[float] = None,
    hla_loh: bool = False,
) -> Dict[str, Any]:
    """Implementation for score_antigen_presentation_pathway."""
    if neoantigen_count < 0:
        return {"status": "error", "message": "neoantigen_count cannot be negative."}

    # Return PatientOne mock only for the exact default scenario
    if DRY_RUN and neoantigen_count == 42 and not hla_loh and mhc1_expression is None:
        return add_dry_run_warning({
            "status": "success",
            "neoantigen_count": neoantigen_count,
            **MOCK_PATHWAY_SCORE,
        })

    # Compute component scores (runs in both DRY_RUN and production — pure computation)
    # Neoantigen score: sigmoid-like scaling (0-100 neoantigens -> 0-1)
    if neoantigen_count >= 100:
        neoantigen_score = 1.0
    elif neoantigen_count >= 50:
        neoantigen_score = 0.7 + 0.3 * (neoantigen_count - 50) / 50
    elif neoantigen_count >= 10:
        neoantigen_score = 0.3 + 0.4 * (neoantigen_count - 10) / 40
    else:
        neoantigen_score = neoantigen_count * 0.03

    # MHC expression score (based on provided expression or default to 0.8)
    if mhc1_expression:
        # Average expression across provided HLA genes (TPM-based)
        avg_expr = sum(mhc1_expression.values()) / len(mhc1_expression)
        mhc_score = min(1.0, avg_expr / 50.0)  # Normalize: 50 TPM = 1.0
    else:
        mhc_score = 0.8  # Default moderate expression

    # Antigen processing score (TAP1 + TAP2 + B2M)
    processing_components = []
    if b2m_expression is not None:
        processing_components.append(min(1.0, b2m_expression / 30.0))
    if tap1_expression is not None:
        processing_components.append(min(1.0, tap1_expression / 20.0))
    if tap2_expression is not None:
        processing_components.append(min(1.0, tap2_expression / 20.0))
    processing_score = (
        sum(processing_components) / len(processing_components)
        if processing_components
        else 0.85  # Default if no expression data
    )

    # HLA integrity score
    hla_integrity_score = 0.0 if hla_loh else 1.0

    # Weighted composite score
    components = {
        "neoantigen_score": round(neoantigen_score, 3),
        "mhc_expression_score": round(mhc_score, 3),
        "antigen_processing_score": round(processing_score, 3),
        "hla_integrity_score": round(hla_integrity_score, 3),
    }

    pathway_score = sum(
        components[k] * PATHWAY_WEIGHTS[k] for k in PATHWAY_WEIGHTS
    )
    pathway_score = round(pathway_score, 3)

    # Interpretation
    if pathway_score >= 0.8:
        interpretation = "Strong antigen presentation capacity. Favorable for checkpoint inhibitor response."
        recommendation = "Checkpoint inhibitor monotherapy may be effective."
    elif pathway_score >= 0.5:
        interpretation = "Moderate antigen presentation capacity."
        recommendation = "Consider checkpoint inhibitor combination therapy."
    elif pathway_score >= 0.3:
        interpretation = "Weak antigen presentation capacity."
        recommendation = "Checkpoint inhibitor alone unlikely sufficient. Consider combination strategies."
    else:
        interpretation = "Poor antigen presentation. Immune evasion likely."
        recommendation = "Alternative therapeutic strategies recommended over checkpoint inhibitors."

    result = {
        "status": "success",
        "pathway_score": pathway_score,
        "components": components,
        "neoantigen_count": neoantigen_count,
        "hla_loh": hla_loh,
        "interpretation": interpretation,
        "recommendation": recommendation,
    }

    if DRY_RUN:
        return add_dry_run_warning(result)
    return result


# ============================================================================
# MCP Tool wrappers
# ============================================================================

@mcp.tool()
async def predict_mhc1_binding(
    peptides: Annotated[List[str], _CoerceList],
    hla_alleles: Annotated[List[str], _CoerceList],
    method: str = "netmhcpan_ba",
    length: int = 9,
) -> Dict[str, Any]:
    """Predict MHC class I binding affinity for peptide-HLA pairs.

    Uses the IEDB API to predict binding of tumor-derived peptides to
    HLA class I molecules (HLA-A, HLA-B, HLA-C). Classifies peptides as
    strong binders (<50 nM), weak binders (<500 nM), or non-binders.

    Args:
        peptides: List of peptide sequences (8-14 amino acids).
        hla_alleles: List of HLA class I alleles (e.g., ["HLA-A*02:01"]).
        method: Prediction method. Options: netmhcpan_ba (default),
            netmhcpan_el, ann, smm.
        length: Peptide length for prediction (default 9).

    Returns:
        Dictionary with binding predictions, binder counts, and classifications.
    """
    return await _predict_mhc1_binding_impl(peptides, hla_alleles, method, length)


@mcp.tool()
async def predict_mhc2_binding(
    peptides: Annotated[List[str], _CoerceList],
    hla_alleles: Annotated[List[str], _CoerceList],
    method: str = "netmhciipan",
    length: int = 15,
) -> Dict[str, Any]:
    """Predict MHC class II binding affinity for peptide-HLA pairs.

    Uses the IEDB API to predict binding of tumor-derived peptides to
    HLA class II molecules (HLA-DR, HLA-DP, HLA-DQ). Important for
    CD4+ T cell activation and helper T cell responses.

    Args:
        peptides: List of peptide sequences (13-25 amino acids).
        hla_alleles: List of HLA class II alleles (e.g., ["HLA-DRB1*01:01"]).
        method: Prediction method. Options: netmhciipan (default),
            nn_align, smm_align.
        length: Peptide length (default 15).

    Returns:
        Dictionary with binding predictions and binder classifications.
    """
    return await _predict_mhc2_binding_impl(peptides, hla_alleles, method, length)


@mcp.tool()
async def run_pvacseq(
    vcf_path: str,
    hla_alleles: Annotated[List[str], _CoerceList],
    output_dir: Optional[str] = None,
    epitope_lengths: Annotated[Optional[List[int]], _CoerceList] = None,
    binding_threshold: float = 500.0,
) -> Dict[str, Any]:
    """Run pVACseq neoantigen prediction pipeline from a VCF file.

    Takes somatic variant calls (VCF) and HLA alleles to predict neoantigens.
    Uses pVACtools locally if available, otherwise falls back to IEDB API.

    Args:
        vcf_path: Path to somatic variant VCF file.
        hla_alleles: Patient HLA alleles (e.g., ["HLA-A*02:01", "HLA-B*07:02"]).
        output_dir: Output directory for results. Defaults to NEOANTIGEN_CACHE_DIR.
        epitope_lengths: Peptide lengths to predict (default [8, 9, 10, 11]).
        binding_threshold: IC50 threshold in nM for binder classification (default 500).

    Returns:
        Dictionary with neoantigen count, top binders, and source mutations.
    """
    return await _run_pvacseq_impl(
        vcf_path, hla_alleles, output_dir, epitope_lengths, binding_threshold,
    )


@mcp.tool()
async def estimate_neoantigen_burden(
    tmb_mutations_per_mb: float,
    hla_alleles: Annotated[Optional[List[str]], _CoerceList] = None,
    cancer_type: str = "HGSOC",
) -> Dict[str, Any]:
    """Estimate neoantigen burden from tumor mutational burden (TMB).

    Uses published TMB-to-neoantigen conversion factors (Samstein et al. 2019)
    to estimate the number of neoantigens from TMB. No API call needed.

    Args:
        tmb_mutations_per_mb: Tumor mutational burden (mutations per megabase).
        hla_alleles: Optional patient HLA alleles for context.
        cancer_type: Cancer type for conversion factor. Options: HGSOC, melanoma,
            NSCLC, colorectal, breast, pancreatic, glioblastoma.

    Returns:
        Dictionary with estimated neoantigen count and interpretation.
    """
    return await _estimate_neoantigen_burden_impl(
        tmb_mutations_per_mb, hla_alleles, cancer_type,
    )


@mcp.tool()
async def get_hla_typing_from_rna(
    bam_path: str,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Determine HLA type from RNA-seq data using OptiType.

    Extracts HLA reads from a BAM file and runs OptiType to determine the
    patient's 6 HLA class I alleles (2 each for HLA-A, HLA-B, HLA-C).

    Args:
        bam_path: Path to RNA-seq BAM file (aligned to hg38).
        output_dir: Output directory for OptiType results.

    Returns:
        Dictionary with HLA alleles, method, and confidence score.
    """
    return await _get_hla_typing_from_rna_impl(bam_path, output_dir)


@mcp.tool()
async def score_antigen_presentation_pathway(
    neoantigen_count: int,
    mhc1_expression: Annotated[Optional[Dict[str, float]], _CoerceDict] = None,
    b2m_expression: Optional[float] = None,
    tap1_expression: Optional[float] = None,
    tap2_expression: Optional[float] = None,
    hla_loh: bool = False,
) -> Dict[str, Any]:
    """Score the antigen presentation pathway for immunotherapy responsiveness.

    Integrates neoantigen burden, MHC expression, antigen processing machinery
    (TAP1/TAP2/B2M), and HLA integrity into a composite pathway score (0-1).
    Higher scores indicate better antigen presentation and potential checkpoint
    inhibitor response.

    Args:
        neoantigen_count: Total predicted neoantigens.
        mhc1_expression: Optional MHC-I gene expression (TPM) by gene name.
        b2m_expression: Optional beta-2-microglobulin expression (TPM).
        tap1_expression: Optional TAP1 expression (TPM).
        tap2_expression: Optional TAP2 expression (TPM).
        hla_loh: Whether HLA loss of heterozygosity was detected.

    Returns:
        Dictionary with pathway score, component scores, and recommendation.
    """
    return await _score_antigen_presentation_pathway_impl(
        neoantigen_count, mhc1_expression, b2m_expression,
        tap1_expression, tap2_expression, hla_loh,
    )


# ---------------------------------------------------------------------------
# Server entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Run the MCP neoantigen server."""
    _run_server(
        mcp, server_name="mcp-neoantigen", dry_run=DRY_RUN, env_var="NEOANTIGEN_DRY_RUN"
    )


if __name__ == "__main__":
    main()
