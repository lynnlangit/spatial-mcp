"""Tests for mcp-neoantigen server (DRY_RUN mode)."""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Import and init tests
# ---------------------------------------------------------------------------

def test_imports():
    """Test that server module imports successfully."""
    from mcp_neoantigen import server

    assert server is not None


def test_dry_run_mode():
    """Test DRY_RUN mode is enabled by default in test environment."""
    from mcp_neoantigen.server import DRY_RUN

    assert DRY_RUN is True, "DRY_RUN should be enabled by default"


def test_server_initialization():
    """Test FastMCP server initializes correctly."""
    from mcp_neoantigen.server import mcp

    assert mcp is not None
    assert mcp.name == "neoantigen"


# ---------------------------------------------------------------------------
# Mock data completeness
# ---------------------------------------------------------------------------

def test_mock_data_completeness():
    """Test that mock data has required fields and consistent structure."""
    from mcp_neoantigen.mock_data import (
        MOCK_HLA_ALLELES,
        MOCK_HLA_FLAT,
        MOCK_MHC1_PREDICTIONS,
        MOCK_MHC2_PREDICTIONS,
        MOCK_NEOANTIGEN_BURDEN,
        MOCK_PATHWAY_SCORE,
        MOCK_PVACSEQ_RESULT,
        TMB_CONVERSION_FACTORS,
    )

    # HLA should have 3 class I genes with 2 alleles each
    assert len(MOCK_HLA_ALLELES) == 3
    for gene, alleles in MOCK_HLA_ALLELES.items():
        assert len(alleles) == 2
    assert len(MOCK_HLA_FLAT) == 6

    # MHC-I predictions should have required fields
    for pred in MOCK_MHC1_PREDICTIONS:
        assert "peptide" in pred
        assert "allele" in pred
        assert "ic50_nm" in pred
        assert "binder" in pred
        assert "binder_level" in pred

    # MHC-II predictions
    assert len(MOCK_MHC2_PREDICTIONS) > 0
    for pred in MOCK_MHC2_PREDICTIONS:
        assert "peptide" in pred
        assert "allele" in pred

    # Neoantigen burden
    assert MOCK_NEOANTIGEN_BURDEN["tmb"] > 0
    assert MOCK_NEOANTIGEN_BURDEN["estimated_neoantigens"] > 0

    # Pathway score should be between 0 and 1
    assert 0.0 <= MOCK_PATHWAY_SCORE["pathway_score"] <= 1.0
    for component, score in MOCK_PATHWAY_SCORE["components"].items():
        assert 0.0 <= score <= 1.0

    # TMB conversion factors should include HGSOC
    assert "HGSOC" in TMB_CONVERSION_FACTORS

    # pVACseq result
    assert MOCK_PVACSEQ_RESULT["total_neoantigens"] > 0
    assert len(MOCK_PVACSEQ_RESULT["top_neoantigens"]) > 0


# ---------------------------------------------------------------------------
# HLA utilities tests
# ---------------------------------------------------------------------------

def test_normalize_hla_canonical():
    """Test that canonical format passes through unchanged."""
    from mcp_neoantigen.hla_utils import normalize_hla_allele

    assert normalize_hla_allele("HLA-A*02:01") == "HLA-A*02:01"
    assert normalize_hla_allele("HLA-B*07:02") == "HLA-B*07:02"
    assert normalize_hla_allele("HLA-C*05:01") == "HLA-C*05:01"


def test_normalize_hla_no_prefix():
    """Test normalization with missing HLA- prefix."""
    from mcp_neoantigen.hla_utils import normalize_hla_allele

    assert normalize_hla_allele("A*02:01") == "HLA-A*02:01"
    assert normalize_hla_allele("B*44:02") == "HLA-B*44:02"


def test_normalize_hla_compact():
    """Test normalization of compact 4-digit format."""
    from mcp_neoantigen.hla_utils import normalize_hla_allele

    assert normalize_hla_allele("A0201") == "HLA-A*02:01"
    assert normalize_hla_allele("B0702") == "HLA-B*07:02"


def test_normalize_hla_no_asterisk():
    """Test normalization with missing asterisk."""
    from mcp_neoantigen.hla_utils import normalize_hla_allele

    assert normalize_hla_allele("HLA-A02:01") == "HLA-A*02:01"


def test_normalize_hla_lowercase():
    """Test case-insensitive normalization."""
    from mcp_neoantigen.hla_utils import normalize_hla_allele

    assert normalize_hla_allele("hla-a*02:01") == "HLA-A*02:01"
    assert normalize_hla_allele("a*02:01") == "HLA-A*02:01"


def test_normalize_hla_invalid():
    """Test that invalid alleles raise ValueError."""
    from mcp_neoantigen.hla_utils import normalize_hla_allele

    with pytest.raises(ValueError, match="Cannot parse"):
        normalize_hla_allele("INVALID")

    with pytest.raises(ValueError, match="Cannot parse"):
        normalize_hla_allele("")


def test_normalize_hla_list():
    """Test batch normalization of HLA allele lists."""
    from mcp_neoantigen.hla_utils import normalize_hla_list

    result = normalize_hla_list(["A0201", "B*07:02", "HLA-C*05:01"])
    assert result == ["HLA-A*02:01", "HLA-B*07:02", "HLA-C*05:01"]


def test_is_class_i():
    """Test HLA class I detection."""
    from mcp_neoantigen.hla_utils import is_class_i

    assert is_class_i("HLA-A*02:01") is True
    assert is_class_i("HLA-B*07:02") is True
    assert is_class_i("HLA-C*05:01") is True
    assert is_class_i("HLA-DRB1*01:01") is False


def test_is_class_ii():
    """Test HLA class II detection."""
    from mcp_neoantigen.hla_utils import is_class_ii

    assert is_class_ii("HLA-DRB1*01:01") is True
    assert is_class_ii("HLA-A*02:01") is False


# ---------------------------------------------------------------------------
# DRY_RUN smoke tests for all 6 tools
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_predict_mhc1_binding_dry_run():
    """Test predict_mhc1_binding returns input-aware mock predictions."""
    from mcp_neoantigen.server import _predict_mhc1_binding_impl

    result = await _predict_mhc1_binding_impl(
        peptides=["RMPEAAPPV", "HMTEVVRHC"],
        hla_alleles=["HLA-A*02:01", "HLA-A*03:01"],
    )

    assert result["status"] == "success"
    assert "predictions" in result
    # 2 peptides x 2 alleles = 4 predictions (cartesian product)
    assert result["total_peptides"] == 4
    assert len(result["predictions"]) == 4
    assert result["strong_binders"] >= 1
    assert "_DRY_RUN_WARNING" in result

    # Canonical RMPEAAPPV / HLA-A*02:01 must be a strong binder
    rmpeaappv = [
        p for p in result["predictions"]
        if p.get("peptide") == "RMPEAAPPV" and "A*02:01" in p.get("allele", "")
    ]
    assert len(rmpeaappv) == 1, "RMPEAAPPV/HLA-A*02:01 prediction missing"
    assert rmpeaappv[0]["ic50_nm"] < 50, (
        f"RMPEAAPPV IC50={rmpeaappv[0]['ic50_nm']} nM — expected <50 nM"
    )

    # No empty peptide or allele strings
    for pred in result["predictions"]:
        assert pred["peptide"] != "", "Empty peptide string"
        assert pred["allele"] != "", "Empty allele string"


@pytest.mark.asyncio
async def test_predict_mhc2_binding_dry_run():
    """Test predict_mhc2_binding returns class II predictions."""
    from mcp_neoantigen.server import _predict_mhc2_binding_impl

    result = await _predict_mhc2_binding_impl(
        peptides=["VVRCPHHERCSTHH"],
        hla_alleles=["HLA-DRB1*01:01"],
    )

    assert result["status"] == "success"
    assert "predictions" in result
    assert result["total_peptides"] > 0
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_run_pvacseq_dry_run():
    """Test run_pvacseq returns mock neoantigen results."""
    from mcp_neoantigen.server import _run_pvacseq_impl

    result = await _run_pvacseq_impl(
        vcf_path="/data/patient/somatic_variants.vcf",
        hla_alleles=["HLA-A*02:01", "HLA-B*07:02"],
    )

    assert result["status"] == "success"
    assert result["total_neoantigens"] == 45
    assert result["strong_binders"] == 12
    assert len(result["top_neoantigens"]) >= 3
    assert result["top_neoantigens"][0]["gene"] == "TP53"
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_estimate_neoantigen_burden_patient_one():
    """Test estimate_neoantigen_burden for PatientOne TMB=3.5."""
    from mcp_neoantigen.server import _estimate_neoantigen_burden_impl

    result = await _estimate_neoantigen_burden_impl(
        tmb_mutations_per_mb=3.5,
        cancer_type="HGSOC",
    )

    assert result["status"] == "success"
    assert result["tmb"] == 3.5
    assert result["estimated_neoantigens"] == 42
    assert result["conversion_factor"] == 12.0
    assert result["cancer_type"] == "HGSOC"
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_estimate_neoantigen_burden_other_cancer():
    """Test neoantigen estimation for melanoma (different conversion factor)."""
    from mcp_neoantigen.server import _estimate_neoantigen_burden_impl

    result = await _estimate_neoantigen_burden_impl(
        tmb_mutations_per_mb=10.0,
        cancer_type="melanoma",
    )

    assert result["status"] == "success"
    assert result["conversion_factor"] == 15.0
    assert result["estimated_neoantigens"] == 150
    assert result["burden_level"] == "high"


@pytest.mark.asyncio
async def test_get_hla_typing_from_rna_dry_run():
    """Test get_hla_typing_from_rna returns PatientOne HLA type."""
    from mcp_neoantigen.server import _get_hla_typing_from_rna_impl

    result = await _get_hla_typing_from_rna_impl(
        bam_path="/data/patient/rna_seq.bam"
    )

    assert result["status"] == "success"
    assert result["method"] == "OptiType"
    assert result["confidence"] == 0.95
    assert "HLA-A" in result["hla_alleles"]
    assert len(result["hla_alleles"]["HLA-A"]) == 2
    assert result["hla_alleles"]["HLA-A"][0] == "HLA-A*02:01"
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_score_antigen_presentation_dry_run():
    """Test score_antigen_presentation_pathway returns PatientOne score."""
    from mcp_neoantigen.server import _score_antigen_presentation_pathway_impl

    result = await _score_antigen_presentation_pathway_impl(
        neoantigen_count=42
    )

    assert result["status"] == "success"
    assert result["pathway_score"] == 0.72
    assert "components" in result
    assert result["components"]["neoantigen_score"] == 0.65
    assert result["components"]["hla_integrity_score"] == 1.0
    assert "interpretation" in result
    assert "recommendation" in result
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_score_antigen_presentation_with_expression():
    """Test pathway scoring with expression data in production mode logic."""
    from mcp_neoantigen.server import _score_antigen_presentation_pathway_impl

    # This exercises the production scoring logic even in DRY_RUN,
    # because we pass a non-mock neoantigen count
    result = await _score_antigen_presentation_pathway_impl(
        neoantigen_count=80,
        mhc1_expression={"HLA-A": 45.0, "HLA-B": 30.0, "HLA-C": 25.0},
        b2m_expression=40.0,
        tap1_expression=15.0,
        tap2_expression=18.0,
        hla_loh=False,
    )

    assert result["status"] == "success"
    # With high neoantigens and decent expression, score should be moderate-high
    assert result["pathway_score"] > 0.5
    assert result["components"]["hla_integrity_score"] == 1.0


@pytest.mark.asyncio
async def test_score_with_hla_loh():
    """Test that HLA-LOH severely reduces pathway score."""
    from mcp_neoantigen.server import _score_antigen_presentation_pathway_impl

    result = await _score_antigen_presentation_pathway_impl(
        neoantigen_count=80,
        hla_loh=True,
    )

    assert result["status"] == "success"
    assert result["components"]["hla_integrity_score"] == 0.0
    assert result["hla_loh"] is True


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_peptide_list():
    """Test that empty peptide list returns error."""
    from mcp_neoantigen.server import _predict_mhc1_binding_impl

    result = await _predict_mhc1_binding_impl(
        peptides=[], hla_alleles=["HLA-A*02:01"],
    )
    assert result["status"] == "error"
    assert "empty" in result["message"].lower()


@pytest.mark.asyncio
async def test_empty_allele_list():
    """Test that empty HLA allele list returns error."""
    from mcp_neoantigen.server import _predict_mhc1_binding_impl

    result = await _predict_mhc1_binding_impl(
        peptides=["RMPEAAPPV"], hla_alleles=[],
    )
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_class_ii_allele_in_mhc1():
    """Test that class II allele in MHC-I tool returns error."""
    from mcp_neoantigen.server import _predict_mhc1_binding_impl

    result = await _predict_mhc1_binding_impl(
        peptides=["RMPEAAPPV"], hla_alleles=["HLA-DRB1*01:01"],
    )
    assert result["status"] == "error"
    assert "class I" in result["message"]


@pytest.mark.asyncio
async def test_invalid_hla_allele():
    """Test that invalid HLA allele returns error."""
    from mcp_neoantigen.server import _predict_mhc1_binding_impl

    result = await _predict_mhc1_binding_impl(
        peptides=["RMPEAAPPV"], hla_alleles=["INVALID"],
    )
    assert result["status"] == "error"
    assert "parse" in result["message"].lower()


@pytest.mark.asyncio
async def test_negative_tmb():
    """Test that negative TMB returns error."""
    from mcp_neoantigen.server import _estimate_neoantigen_burden_impl

    result = await _estimate_neoantigen_burden_impl(tmb_mutations_per_mb=-1.0)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_negative_neoantigen_count():
    """Test that negative neoantigen count returns error."""
    from mcp_neoantigen.server import _score_antigen_presentation_pathway_impl

    result = await _score_antigen_presentation_pathway_impl(neoantigen_count=-5)
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_empty_vcf_path():
    """Test that empty VCF path returns error."""
    from mcp_neoantigen.server import _run_pvacseq_impl

    result = await _run_pvacseq_impl(
        vcf_path="", hla_alleles=["HLA-A*02:01"],
    )
    assert result["status"] == "error"


@pytest.mark.asyncio
async def test_empty_bam_path():
    """Test that empty BAM path returns error."""
    from mcp_neoantigen.server import _get_hla_typing_from_rna_impl

    result = await _get_hla_typing_from_rna_impl(bam_path="")
    assert result["status"] == "error"


# ---------------------------------------------------------------------------
# FastMCP 2.x JSON-string coercion regression tests
# ---------------------------------------------------------------------------
# These exercise the Pydantic BeforeValidator path by calling tool.run()
# which processes arguments through Pydantic validation before reaching
# the function body.

import asyncio
import json


def _get_tool(name: str):
    """Fetch FunctionTool from mcp registry (FastMCP 3.x returns raw fn from decorator)."""
    from mcp_neoantigen.server import mcp
    return asyncio.get_event_loop().run_until_complete(mcp.get_tool(name))


def _run_tool(name: str, arguments: dict):
    """Call tool.run() (Pydantic-validated path) and return parsed JSON result."""
    tool = _get_tool(name)
    result = asyncio.get_event_loop().run_until_complete(
        tool.run(arguments=arguments)
    )
    text = result.content[0].text
    return json.loads(text)


def test_estimate_neoantigen_burden_json_string_hla_alleles():
    """estimate_neoantigen_burden accepts hla_alleles as JSON string."""
    result = _run_tool("estimate_neoantigen_burden", {
        "tmb_mutations_per_mb": 47.3,
        "cancer_type": "HGSOC",
        "hla_alleles": json.dumps(["HLA-A*02:01", "HLA-B*07:02", "HLA-C*07:02"]),
    })
    assert result["status"] == "success"
    assert result["estimated_neoantigens"] > 0


def test_estimate_neoantigen_burden_native_hla_alleles():
    """estimate_neoantigen_burden accepts hla_alleles as native list."""
    result = _run_tool("estimate_neoantigen_burden", {
        "tmb_mutations_per_mb": 47.3,
        "cancer_type": "HGSOC",
        "hla_alleles": ["HLA-A*02:01", "HLA-B*07:02", "HLA-C*07:02"],
    })
    assert result["status"] == "success"


def test_score_antigen_presentation_json_string_mhc1():
    """score_antigen_presentation_pathway accepts mhc1_expression as JSON string."""
    result = _run_tool("score_antigen_presentation_pathway", {
        "neoantigen_count": 42,
        "mhc1_expression": json.dumps({
            "HLA-A": 8.5, "HLA-B": 6.2, "HLA-C": 4.1,
        }),
    })
    assert result["status"] == "success"
    assert "pathway_score" in result


def test_run_pvacseq_json_string_alleles_and_lengths():
    """run_pvacseq accepts hla_alleles and epitope_lengths as JSON strings."""
    result = _run_tool("run_pvacseq", {
        "vcf_path": "/data/patient/somatic.vcf",
        "hla_alleles": json.dumps(["HLA-A*02:01", "HLA-B*07:02"]),
        "epitope_lengths": json.dumps([8, 9, 10]),
    })
    assert result["status"] == "success"


def test_predict_mhc1_binding_json_string_params():
    """predict_mhc1_binding accepts peptides and hla_alleles as JSON strings."""
    result = _run_tool("predict_mhc1_binding", {
        "peptides": json.dumps(["RMPEAAPPV", "SLYNTVAVL"]),
        "hla_alleles": json.dumps(["HLA-A*02:01"]),
    })
    assert result["status"] == "success"


# ---------------------------------------------------------------------------
# Multi-peptide cartesian product regression tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mhc1_multi_peptide_cartesian():
    """3 peptides x 2 alleles must produce 6 predictions with correct fields."""
    from mcp_neoantigen.server import _predict_mhc1_binding_impl

    result = await _predict_mhc1_binding_impl(
        peptides=["RMPEAAPPV", "GILGFVFTL", "NLVPMVATV"],
        hla_alleles=["HLA-A*02:01", "HLA-B*07:02"],
    )

    assert result["status"] == "success"
    assert len(result["predictions"]) == 6, (
        f"Expected 6 predictions (3x2), got {len(result['predictions'])}"
    )
    assert result["total_peptides"] == 6

    for pred in result["predictions"]:
        assert pred["peptide"] != "", f"Empty peptide: {pred}"
        assert pred["allele"] != "", f"Empty allele: {pred}"
        assert pred["ic50_nm"] != 999999, f"Sentinel IC50: {pred}"

    # RMPEAAPPV + HLA-A*02:01 must be a strong binder
    rmpeaappv_a0201 = next(
        p for p in result["predictions"]
        if p["peptide"] == "RMPEAAPPV" and "A*02:01" in p["allele"]
    )
    assert rmpeaappv_a0201["ic50_nm"] < 50, (
        f"RMPEAAPPV/A*02:01 IC50={rmpeaappv_a0201['ic50_nm']:.1f} — expected <50 nM"
    )


@pytest.mark.asyncio
async def test_mhc2_multi_peptide_cartesian():
    """2 peptides x 2 alleles must produce 4 predictions."""
    from mcp_neoantigen.server import _predict_mhc2_binding_impl

    result = await _predict_mhc2_binding_impl(
        peptides=["VVRCPHHERCSTHH", "PKYVKQNTLKLAT"],
        hla_alleles=["HLA-DRB1*01:01", "HLA-DRB1*04:01"],
    )

    assert result["status"] == "success"
    assert len(result["predictions"]) == 4, (
        f"Expected 4 predictions (2x2), got {len(result['predictions'])}"
    )
    assert result["total_peptides"] == 4

    for pred in result["predictions"]:
        assert pred["peptide"] != "", f"Empty peptide: {pred}"
        assert pred["allele"] != "", f"Empty allele: {pred}"


@pytest.mark.asyncio
async def test_mhc1_single_peptide_single_allele():
    """1 peptide x 1 allele = 1 prediction (regression guard)."""
    from mcp_neoantigen.server import _predict_mhc1_binding_impl

    result = await _predict_mhc1_binding_impl(
        peptides=["RMPEAAPPV"],
        hla_alleles=["HLA-A*02:01"],
    )

    assert result["status"] == "success"
    assert result["total_peptides"] == 1
    assert len(result["predictions"]) == 1
    assert result["predictions"][0]["peptide"] == "RMPEAAPPV"
    assert result["predictions"][0]["allele"] == "HLA-A*02:01"
    assert result["predictions"][0]["ic50_nm"] < 50
