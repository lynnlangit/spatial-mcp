"""Tests for mcp-opentargets server (DRY_RUN mode)."""

import pytest
import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_imports():
    """Test that server module imports successfully."""
    from mcp_opentargets import server

    assert server is not None


def test_dry_run_mode():
    """Test DRY_RUN mode is enabled by default in test environment."""
    from mcp_opentargets.server import DRY_RUN

    assert DRY_RUN is True, "DRY_RUN should be enabled by default"


def test_server_initialization():
    """Test FastMCP server initializes correctly."""
    from mcp_opentargets.server import mcp

    assert mcp is not None
    assert mcp.name == "opentargets"


def test_disease_ontology_ids():
    """Test EFO disease ID mappings."""
    from mcp_opentargets.disease_ontology import DISEASE_IDS

    assert DISEASE_IDS["ovarian carcinoma"] == "EFO_0001071"
    assert DISEASE_IDS["HGSOC"] == "EFO_0001071"
    assert "breast carcinoma" in DISEASE_IDS


def test_gene_symbol_to_ensembl():
    """Test HGSOC gene symbol -> Ensembl ID mappings."""
    from mcp_opentargets.disease_ontology import HGSOC_GENE_SYMBOL_TO_ENSEMBL

    assert HGSOC_GENE_SYMBOL_TO_ENSEMBL["TP53"] == "ENSG00000141510"
    assert HGSOC_GENE_SYMBOL_TO_ENSEMBL["PIK3CA"] == "ENSG00000121879"
    assert HGSOC_GENE_SYMBOL_TO_ENSEMBL["BRCA1"] == "ENSG00000012048"
    assert HGSOC_GENE_SYMBOL_TO_ENSEMBL["VEGFA"] == "ENSG00000112715"
    # Check all 20 HGSOC driver genes are present
    hgsoc_genes = [
        "TP53", "PIK3CA", "PTEN", "BRCA1", "BRCA2", "MYC", "CCNE1",
        "AKT2", "RB1", "CDKN2A", "BRAF", "KRAS", "ARID1A", "VEGFA",
        "CDK12", "NF1", "EMSY", "RAD51C", "RAD51D", "CD274",
    ]
    for gene in hgsoc_genes:
        assert gene in HGSOC_GENE_SYMBOL_TO_ENSEMBL, f"Missing gene: {gene}"

    # Check all 30 immunotherapy target genes are present
    immunotherapy_genes = [
        "PDCD1", "CTLA4", "TIGIT", "LAG3", "HAVCR2",
        "CD47", "SIRPA", "CD36",
        "CSF1R", "IL10", "CD163", "PPARG",
        "TGFB1", "PTK2", "COL6A3",
        "CCL22", "CCR4", "FOXP3", "IL2RA",
        "KLRC1", "MICA", "MICB", "NCR1",
        "DNMT1", "DNMT3A", "HDAC1", "HDAC2",
        "B2M", "TAP1", "TAP2",
    ]
    for gene in immunotherapy_genes:
        assert gene in HGSOC_GENE_SYMBOL_TO_ENSEMBL, f"Missing gene: {gene}"
    assert len(HGSOC_GENE_SYMBOL_TO_ENSEMBL) >= 50


def test_mock_data_completeness():
    """Test that mock data dicts have consistent keys."""
    from mcp_opentargets.disease_ontology import (
        MOCK_TARGET_INFO,
        MOCK_ASSOCIATION_SCORES,
        MOCK_DRUGS,
        MOCK_SAFETY,
    )

    # Target info should have required fields
    for symbol, info in MOCK_TARGET_INFO.items():
        assert "id" in info
        assert "symbol" in info
        assert "name" in info
        assert "tractability" in info

    # Association scores should have overall_score and evidence_scores
    for symbol, scores in MOCK_ASSOCIATION_SCORES.items():
        assert "overall_score" in scores
        assert "evidence_scores" in scores
        assert 0.0 <= scores["overall_score"] <= 1.0

    # Drugs should be lists
    for symbol, drugs in MOCK_DRUGS.items():
        assert isinstance(drugs, list)
        for drug in drugs:
            assert "name" in drug
            assert "phase" in drug

    # Safety should have required keys
    for symbol, safety in MOCK_SAFETY.items():
        assert "safety_liabilities" in safety
        assert "adverse_events" in safety
        assert "risk_level" in safety


@pytest.mark.asyncio
async def test_get_target_info_dry_run():
    """Test get_target_info in DRY_RUN mode."""
    from mcp_opentargets.server import _get_target_info_impl

    result = await _get_target_info_impl(gene_symbol="TP53")

    assert result["status"] == "success"
    assert "target" in result
    assert result["target"]["symbol"] == "TP53"
    assert result["target"]["name"] == "Tumor protein p53"
    assert "tractability" in result["target"]
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_get_target_info_unknown_gene():
    """Test get_target_info with unknown gene falls back to defaults."""
    from mcp_opentargets.server import _get_target_info_impl

    result = await _get_target_info_impl(gene_symbol="FAKEGENE")

    assert result["status"] == "success"
    assert result["target"]["symbol"] == "FAKEGENE"
    assert "tractability" in result["target"]


@pytest.mark.asyncio
async def test_get_target_info_by_ensembl_id():
    """Test get_target_info with Ensembl ID."""
    from mcp_opentargets.server import _get_target_info_impl

    result = await _get_target_info_impl(ensembl_id="ENSG00000141510")

    assert result["status"] == "success"
    assert "target" in result


@pytest.mark.asyncio
async def test_get_target_disease_associations_dry_run():
    """Test get_target_disease_associations in DRY_RUN mode."""
    from mcp_opentargets.server import _get_target_disease_associations_impl

    result = await _get_target_disease_associations_impl(gene_symbol="TP53")

    assert result["status"] == "success"
    assert result["target"] == "TP53"
    assert result["disease_id"] == "EFO_0001071"
    assert "overall_score" in result
    assert result["overall_score"] == 0.87
    assert "evidence_scores" in result
    assert "somatic_mutation" in result["evidence_scores"]
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_get_target_disease_associations_custom_disease():
    """Test associations with a non-default disease ID."""
    from mcp_opentargets.server import _get_target_disease_associations_impl

    result = await _get_target_disease_associations_impl(
        gene_symbol="PIK3CA", disease_id="EFO_0000305"
    )

    assert result["status"] == "success"
    assert result["disease_id"] == "EFO_0000305"


@pytest.mark.asyncio
async def test_get_target_drugs_dry_run():
    """Test get_target_drugs in DRY_RUN mode."""
    from mcp_opentargets.server import _get_target_drugs_impl

    result = await _get_target_drugs_impl(gene_symbol="PIK3CA")

    assert result["status"] == "success"
    assert result["target"] == "PIK3CA"
    assert "drugs" in result
    assert len(result["drugs"]) > 0
    assert result["drugs"][0]["name"] == "Alpelisib"
    assert result["total_drugs"] > 0
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_get_target_drugs_phase_filter():
    """Test get_target_drugs with phase_min filter."""
    from mcp_opentargets.server import _get_target_drugs_impl

    result = await _get_target_drugs_impl(gene_symbol="TP53", phase_min=4)

    assert result["status"] == "success"
    # TP53 mock drugs are all phase 3, so filtering at 4 should return none
    assert result["total_drugs"] == 0


@pytest.mark.asyncio
async def test_get_target_drugs_no_drugs():
    """Test get_target_drugs for gene with no known drugs."""
    from mcp_opentargets.server import _get_target_drugs_impl

    result = await _get_target_drugs_impl(gene_symbol="MYC")

    assert result["status"] == "success"
    assert result["total_drugs"] == 0


@pytest.mark.asyncio
async def test_search_targets_by_disease_dry_run():
    """Test search_targets_by_disease in DRY_RUN mode."""
    from mcp_opentargets.server import _search_targets_by_disease_impl

    result = await _search_targets_by_disease_impl()

    assert result["status"] == "success"
    assert result["disease_id"] == "EFO_0001071"
    assert "targets" in result
    assert len(result["targets"]) > 0
    # Should be sorted by score descending
    assert result["targets"][0]["symbol"] == "TP53"
    assert result["targets"][0]["score"] == 0.87
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_search_targets_by_disease_with_evidence_filter():
    """Test search_targets_by_disease with evidence type filter."""
    from mcp_opentargets.server import _search_targets_by_disease_impl

    result = await _search_targets_by_disease_impl(evidence_type="known_drug")

    assert result["status"] == "success"
    for target in result["targets"]:
        assert target["top_evidence"] == "known_drug"


@pytest.mark.asyncio
async def test_search_targets_by_disease_top_n():
    """Test search_targets_by_disease with top_n limit."""
    from mcp_opentargets.server import _search_targets_by_disease_impl

    result = await _search_targets_by_disease_impl(top_n=5)

    assert result["status"] == "success"
    assert len(result["targets"]) <= 5


@pytest.mark.asyncio
async def test_get_target_safety_dry_run():
    """Test get_target_safety in DRY_RUN mode."""
    from mcp_opentargets.server import _get_target_safety_impl

    result = await _get_target_safety_impl(gene_symbol="VEGFA")

    assert result["status"] == "success"
    assert result["target"] == "VEGFA"
    assert "safety_liabilities" in result
    assert len(result["safety_liabilities"]) > 0
    assert result["risk_level"] == "moderate"
    assert "adverse_events" in result
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_get_target_safety_no_liabilities():
    """Test get_target_safety for gene with no known safety issues."""
    from mcp_opentargets.server import _get_target_safety_impl

    result = await _get_target_safety_impl(gene_symbol="TP53")

    assert result["status"] == "success"
    assert result["risk_level"] == "low"
    assert len(result["safety_liabilities"]) == 0


@pytest.mark.asyncio
async def test_get_target_safety_unknown_gene():
    """Test get_target_safety for gene not in safety mock data."""
    from mcp_opentargets.server import _get_target_safety_impl

    result = await _get_target_safety_impl(gene_symbol="MYC")

    assert result["status"] == "success"
    assert result["risk_level"] == "unknown"


@pytest.mark.asyncio
async def test_batch_score_targets_dry_run():
    """Test batch_score_targets in DRY_RUN mode."""
    from mcp_opentargets.server import _batch_score_targets_impl

    result = await _batch_score_targets_impl(
        gene_symbols=["TP53", "PIK3CA", "VEGFA", "MYC", "CDK12"]
    )

    assert result["status"] == "success"
    assert result["disease_id"] == "EFO_0001071"
    assert "scores" in result
    assert len(result["scores"]) == 5
    assert result["scores"]["TP53"] == 0.87
    assert result["scores"]["PIK3CA"] == 0.72
    assert "druggable_targets" in result
    assert "PIK3CA" in result["druggable_targets"]
    assert "novel_targets" in result
    assert result["total_queried"] == 5
    assert "_DRY_RUN_WARNING" in result


@pytest.mark.asyncio
async def test_batch_score_targets_empty_list():
    """Test batch_score_targets with empty gene list."""
    from mcp_opentargets.server import _batch_score_targets_impl

    result = await _batch_score_targets_impl(gene_symbols=[])

    assert result["status"] == "success"
    assert result["total_queried"] == 0
    assert len(result["scores"]) == 0


@pytest.mark.asyncio
async def test_resolve_gene_symbol_from_table():
    """Test gene symbol resolution from local lookup table."""
    from mcp_opentargets.graphql_client import resolve_gene_symbol

    # In DRY_RUN, we just need the local table to work
    eid = await resolve_gene_symbol("TP53", "https://fake.url/graphql")
    assert eid == "ENSG00000141510"

    eid = await resolve_gene_symbol("brca1", "https://fake.url/graphql")
    assert eid == "ENSG00000012048"


@pytest.mark.asyncio
async def test_resolve_gene_symbol_case_insensitive():
    """Test that gene symbol resolution is case-insensitive."""
    from mcp_opentargets.graphql_client import resolve_gene_symbol

    eid_upper = await resolve_gene_symbol("VEGFA", "https://fake.url/graphql")
    eid_lower = await resolve_gene_symbol("vegfa", "https://fake.url/graphql")
    assert eid_upper == eid_lower == "ENSG00000112715"


@pytest.mark.asyncio
async def test_resolve_immunotherapy_gene_symbols():
    """Test that immunotherapy target genes resolve correctly."""
    from mcp_opentargets.graphql_client import resolve_gene_symbol

    test_cases = {
        "PDCD1": "ENSG00000188389",
        "CTLA4": "ENSG00000163599",
        "CD47": "ENSG00000196776",
        "TIGIT": "ENSG00000181847",
        "KLRC1": "ENSG00000204592",
        "DNMT3A": "ENSG00000119772",
        "B2M": "ENSG00000166710",
    }
    for symbol, expected_id in test_cases.items():
        eid = await resolve_gene_symbol(symbol, "https://fake.url/graphql")
        assert eid == expected_id, f"{symbol} resolved to {eid}, expected {expected_id}"
