"""Regression tests for Phase 8a.6 Fix 4 (mcp-genomic-results).

Covers:
1. Broadened pathogenic-effect allowlist (SnpEff / VEP synonyms, case-insensitive)
2. Patient-aware DRY_RUN payloads (PAT001 ovarian vs PAT002 breast)
3. Annotation-fallback flag when real VCF parses but classifier finds nothing
4. OVC_GENE_PANEL fallback for variants without COSMIC annotation
"""
import os
from pathlib import Path

import pytest

# Force DRY_RUN default before importing the server module so module-level
# constants pick it up. Tests that need the live parser flip DRY_RUN locally.
os.environ.setdefault("GENOMIC_RESULTS_DRY_RUN", "true")

from mcp_genomic_results.server import (  # noqa: E402
    _PATHOGENIC_EFFECTS_LOWER,
    _calculate_hrd_impl,
    _generate_report_impl,
    _infer_patient_id_from_path,
    _is_pathogenic_effect,
    _parse_cnv_calls_impl,
    _parse_somatic_variants_impl,
    _parse_vcf_file,
)


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestInferPatientIdFromPath:
    def test_pat001_canonical(self):
        assert _infer_patient_id_from_path(
            "/data/patient-data/PAT001-OVC-2025/genomics/somatic.vcf"
        ) == "PAT001"

    def test_pat002_underscore(self):
        assert _infer_patient_id_from_path("/tmp/pat002_breast.vcf") == "PAT002"

    def test_pat002_uppercase(self):
        assert _infer_patient_id_from_path("/data/PAT002/genomics/") == "PAT002"

    def test_pat001_substring(self):
        assert _infer_patient_id_from_path("somewhere/PAT001.cns") == "PAT001"

    def test_unknown_path(self):
        assert _infer_patient_id_from_path("/tmp/generic.vcf") == "UNKNOWN"

    def test_none_path(self):
        assert _infer_patient_id_from_path(None) == "UNKNOWN"

    def test_empty_path(self):
        assert _infer_patient_id_from_path("") == "UNKNOWN"


class TestIsPathogenicEffect:
    def test_missense_variant(self):
        assert _is_pathogenic_effect("missense_variant") is True

    def test_frameshift_variant(self):
        assert _is_pathogenic_effect("frameshift_variant") is True

    def test_stop_gained(self):
        # Previously missing from narrow allowlist
        assert _is_pathogenic_effect("stop_gained") is True

    def test_inframe_deletion(self):
        # Previously missing from narrow allowlist
        assert _is_pathogenic_effect("inframe_deletion") is True

    def test_splice_donor_variant(self):
        assert _is_pathogenic_effect("splice_donor_variant") is True

    def test_case_insensitive_snpeff(self):
        assert _is_pathogenic_effect("MISSENSE") is True
        assert _is_pathogenic_effect("FRAME_SHIFT") is True

    def test_mixed_case(self):
        assert _is_pathogenic_effect("Missense_Variant") is True

    def test_whitespace(self):
        assert _is_pathogenic_effect("  missense_variant  ") is True

    def test_intronic_not_pathogenic(self):
        assert _is_pathogenic_effect("intron_variant") is False

    def test_empty_string(self):
        assert _is_pathogenic_effect("") is False

    def test_none(self):
        assert _is_pathogenic_effect(None) is False

    def test_allowlist_size(self):
        # Broadened from 3 to a much larger set
        assert len(_PATHOGENIC_EFFECTS_LOWER) >= 12


# ---------------------------------------------------------------------------
# Patient-aware DRY_RUN payload tests
# ---------------------------------------------------------------------------


class TestPatientAwareDryRunSomatic:
    """DRY_RUN payloads should branch on patient hint in vcf_path."""

    @pytest.mark.asyncio
    async def test_pat001_returns_ovarian_markers(self):
        result = await _parse_somatic_variants_impl(
            vcf_path="/data/PAT001-OVC-2025/genomics/somatic_variants.vcf"
        )
        assert result["patient_id_hint"] == "PAT001"
        genes = [m["gene"] for m in result["somatic_mutations"]]
        assert "TP53" in genes
        assert "PIK3CA" in genes
        assert "PTEN" in genes
        # Ovarian canonical amplifications
        assert "MYC" in result["copy_number_events"]["amplifications"]
        assert "CCNE1" in result["copy_number_events"]["amplifications"]
        assert "_DRY_RUN_WARNING" in result

    @pytest.mark.asyncio
    async def test_pat002_returns_breast_markers(self):
        result = await _parse_somatic_variants_impl(
            vcf_path="/data/PAT002_breast/somatic.vcf"
        )
        assert result["patient_id_hint"] == "PAT002"
        genes = [m["gene"] for m in result["somatic_mutations"]]
        assert "BRCA2" in genes
        assert "PIK3CA" in genes
        # Breast canonical amplifications
        assert "ERBB2" in result["copy_number_events"]["amplifications"]
        # TP53 should be in wild_type for PAT002
        assert "TP53" in result["wild_type"]
        # Ovarian-only markers should NOT be in PAT002 payload
        assert "MYC" not in result["copy_number_events"]["amplifications"]

    @pytest.mark.asyncio
    async def test_unknown_patient_defaults_to_pat001(self):
        """Unknown paths default to PAT001 ovarian payload for backwards compat."""
        result = await _parse_somatic_variants_impl(vcf_path="/tmp/generic.vcf")
        assert result["patient_id_hint"] == "UNKNOWN"
        genes = [m["gene"] for m in result["somatic_mutations"]]
        assert "TP53" in genes  # Defaults to PAT001


class TestPatientAwareDryRunCnv:
    @pytest.mark.asyncio
    async def test_pat001_cnv_ovarian_segments(self):
        result = await _parse_cnv_calls_impl(
            cns_path="/data/PAT001-OVC-2025/cnv.cns"
        )
        assert result["patient_id_hint"] == "PAT001"
        amp_genes = [a["gene"] for a in result["amplifications"]]
        assert "CCNE1" in amp_genes
        assert "MYC" in amp_genes
        del_genes = [d["gene"] for d in result["deletions"]]
        assert "RB1" in del_genes
        assert "PTEN" in del_genes

    @pytest.mark.asyncio
    async def test_pat002_cnv_breast_segments(self):
        result = await _parse_cnv_calls_impl(cns_path="/data/PAT002/cnv.cns")
        assert result["patient_id_hint"] == "PAT002"
        amp_genes = [a["gene"] for a in result["amplifications"]]
        assert "ERBB2" in amp_genes
        assert "CCND1" in amp_genes
        # Ovarian-only markers should NOT be in PAT002 payload
        assert "CCNE1" not in amp_genes


class TestPatientAwareDryRunHrd:
    @pytest.mark.asyncio
    async def test_pat001_hrd_positive(self):
        result = await _calculate_hrd_impl(
            vcf_path="/data/PAT001-OVC-2025/somatic.vcf",
            cns_path="/data/PAT001-OVC-2025/cnv.cns",
        )
        assert result["patient_id_hint"] == "PAT001"
        assert result["hrd_positive"] is True
        assert result["brca_status"]["BRCA2"] == "wild_type"

    @pytest.mark.asyncio
    async def test_pat002_hrd_brca2_route(self):
        result = await _calculate_hrd_impl(
            vcf_path="/data/PAT002/somatic.vcf",
            cns_path="/data/PAT002/cnv.cns",
        )
        assert result["patient_id_hint"] == "PAT002"
        assert result["hrd_positive"] is False  # HRD-negative
        assert result["brca_status"]["BRCA2"] == "mutated"
        assert result["parp_eligible"] is True  # BRCA2 route


class TestPatientAwareDryRunReport:
    @pytest.mark.asyncio
    async def test_pat001_report_ovarian_therapies(self):
        result = await _generate_report_impl(
            vcf_path="/data/PAT001-OVC-2025/somatic.vcf",
            cns_path="/data/PAT001-OVC-2025/cnv.cns",
        )
        assert result["patient_id_hint"] == "PAT001"
        assert result["summary"]["hrd_status"] == "Positive"
        genes = [f["gene"] for f in result["actionable_findings"]]
        assert "TP53" in genes
        assert "PIK3CA" in genes

    @pytest.mark.asyncio
    async def test_pat002_report_breast_therapies(self):
        result = await _generate_report_impl(
            vcf_path="/data/PAT002/somatic.vcf",
            cns_path="/data/PAT002/cnv.cns",
            patient_id="PAT002",
        )
        assert result["patient_id_hint"] == "PAT002"
        assert result["summary"]["hrd_status"] == "Negative"
        genes = [f["gene"] for f in result["actionable_findings"]]
        assert "BRCA2" in genes
        assert "ERBB2" in genes  # HER2+
        # Confirm ovarian-only therapies are NOT in breast report
        assert not any("APR-246" in t for t in result["therapy_recommendations"])


# ---------------------------------------------------------------------------
# Real VCF parsing with broadened allowlist
# ---------------------------------------------------------------------------


@pytest.fixture
def synthetic_vcf(tmp_path):
    """Create a tiny synthetic VCF with one variant per effect category."""
    vcf = tmp_path / "synth.vcf"
    vcf.write_text(
        "##fileformat=VCFv4.2\n"
        "##INFO=<ID=DP,Number=1,Type=Integer>\n"
        "##INFO=<ID=AF,Number=1,Type=Float>\n"
        "##INFO=<ID=GENE,Number=1,Type=String>\n"
        "##INFO=<ID=EFFECT,Number=1,Type=String>\n"
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
        "chr17\t7577120\tTP53_R175H\tG\tA\t99\tPASS\t"
        "DP=50;AF=0.5;GENE=TP53;EFFECT=missense_variant\n"
        "chr3\t178936091\tPIK3CA_E545K\tG\tA\t99\tPASS\t"
        "DP=40;AF=0.4;GENE=PIK3CA;EFFECT=missense_variant\n"
        "chr17\t41245466\tBRCA1_stop\tC\tT\t99\tPASS\t"
        "DP=30;AF=0.3;GENE=BRCA1;EFFECT=stop_gained\n"
        "chr10\t89720633\tPTEN_delIns\tAGC\tA\t99\tPASS\t"
        "DP=60;AF=0.6;GENE=PTEN;EFFECT=inframe_deletion\n"
        "chr7\t140453136\tBRAF_splice\tA\tG\t99\tPASS\t"
        "DP=25;AF=0.25;GENE=BRAF;EFFECT=splice_donor_variant\n"
        "chr1\t12345678\tGENE1_intron\tA\tG\t99\tPASS\t"
        "DP=20;AF=0.2;GENE=GENE1;EFFECT=intron_variant\n"
    )
    return vcf


class TestRealVcfParsing:
    """Tests that hit the live parser with DRY_RUN=false."""

    @pytest.mark.asyncio
    async def test_broadened_allowlist_captures_stop_gained(
        self, synthetic_vcf, monkeypatch
    ):
        """A VCF with stop_gained / inframe_deletion / splice_donor_variant
        should produce pathogenic hits, not silently drop them like the old
        3-item allowlist did."""
        import mcp_genomic_results.server as srv
        monkeypatch.setattr(srv, "DRY_RUN", False)

        result = await _parse_somatic_variants_impl(
            vcf_path=str(synthetic_vcf),
            min_allele_frequency=0.0,
        )
        # All five pathogenic-effect variants should be classified
        assert result["total_variants"] == 6
        somatic_genes = {m["gene"] for m in result["somatic_mutations"]}
        assert "TP53" in somatic_genes
        assert "PIK3CA" in somatic_genes
        assert "BRCA1" in somatic_genes  # stop_gained
        assert "PTEN" in somatic_genes  # inframe_deletion
        assert "BRAF" in somatic_genes  # splice_donor_variant
        assert "GENE1" not in somatic_genes  # intron_variant correctly skipped

        # skipped_effects should record the intron skip
        assert "skipped_effects" in result
        assert "intron_variant" in result["skipped_effects"]

    @pytest.mark.asyncio
    async def test_ovc_panel_fallback_annotation_status(
        self, synthetic_vcf, monkeypatch
    ):
        """Variants in OVC_GENE_PANEL without a COSMIC match should still
        appear in actionable_findings with annotation_status set."""
        import mcp_genomic_results.server as srv
        monkeypatch.setattr(srv, "DRY_RUN", False)

        result = await _parse_somatic_variants_impl(
            vcf_path=str(synthetic_vcf),
            min_allele_frequency=0.0,
        )

        actionable_genes = {a["gene"] for a in result["actionable_findings"]}
        actionable_statuses = {
            a.get("annotation_status") for a in result["actionable_findings"]
        }
        # Every actionable finding should have an annotation_status
        assert None not in actionable_statuses
        assert actionable_statuses.issubset(
            {"cosmic_match", "gene_in_panel_no_cosmic_match"}
        )
        # TP53 / PIK3CA / PTEN are in OVC_GENE_PANEL → expect at least these
        # to surface as actionable (either via COSMIC hit or panel fallback)
        assert actionable_genes & {"TP53", "PIK3CA", "PTEN"}


class TestAnnotationFallback:
    """When real VCF parses 0 pathogenic variants but path is a known patient
    fixture, return a patient-aware synthetic payload with annotation_fallback=True.
    """

    @pytest.mark.asyncio
    async def test_pat001_empty_vcf_triggers_fallback(self, tmp_path, monkeypatch):
        # Empty VCF with only intron_variant effects → 0 somatic mutations
        vcf = tmp_path / "PAT001-OVC-2025_empty.vcf"
        vcf.write_text(
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "chr1\t100\tG1_intron\tA\tG\t99\tPASS\t"
            "DP=10;AF=0.1;GENE=G1;EFFECT=intron_variant\n"
        )
        import mcp_genomic_results.server as srv
        monkeypatch.setattr(srv, "DRY_RUN", False)

        result = await _parse_somatic_variants_impl(vcf_path=str(vcf))
        assert result.get("annotation_fallback") is True
        assert result.get("patient_id_hint") == "PAT001"
        # Synthetic PAT001 payload fields should be present
        genes = [m["gene"] for m in result["somatic_mutations"]]
        assert "TP53" in genes

    @pytest.mark.asyncio
    async def test_pat002_empty_vcf_triggers_breast_fallback(
        self, tmp_path, monkeypatch
    ):
        vcf = tmp_path / "PAT002_empty.vcf"
        vcf.write_text(
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "chr1\t100\tG1_intron\tA\tG\t99\tPASS\t"
            "DP=10;AF=0.1;GENE=G1;EFFECT=intron_variant\n"
        )
        import mcp_genomic_results.server as srv
        monkeypatch.setattr(srv, "DRY_RUN", False)

        result = await _parse_somatic_variants_impl(vcf_path=str(vcf))
        assert result.get("annotation_fallback") is True
        assert result.get("patient_id_hint") == "PAT002"
        genes = [m["gene"] for m in result["somatic_mutations"]]
        assert "BRCA2" in genes  # Breast-cancer payload

    @pytest.mark.asyncio
    async def test_unknown_patient_empty_vcf_no_fallback(self, tmp_path, monkeypatch):
        """Unknown paths should NOT trigger the fallback — they return real
        (empty) parse results."""
        vcf = tmp_path / "generic.vcf"
        vcf.write_text(
            "##fileformat=VCFv4.2\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "chr1\t100\tG1_intron\tA\tG\t99\tPASS\t"
            "DP=10;AF=0.1;GENE=G1;EFFECT=intron_variant\n"
        )
        import mcp_genomic_results.server as srv
        monkeypatch.setattr(srv, "DRY_RUN", False)

        result = await _parse_somatic_variants_impl(vcf_path=str(vcf))
        # Should NOT have the fallback flag
        assert "annotation_fallback" not in result
        assert result["total_variants"] == 1
        assert len(result["somatic_mutations"]) == 0
