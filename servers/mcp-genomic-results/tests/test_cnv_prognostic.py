"""Uveal melanoma prognostic class, and the boundary it refuses to cross (spec section 9)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_genomic_results.cnv.prognostic import (  # noqa: E402
    ALREADY_ANSWERED,
    DEFAULT_MANAGEMENT_IMPLICATION,
    assess_prognostic_class,
)
from mcp_genomic_results.cnv.tools import assess_um_prognostic_class_impl  # noqa: E402


class TestActionabilityIsHardCoded:
    """The reason this tool exists.

    Chromosome 3 status estimates the risk that a PRIMARY tumour will
    metastasise. No published evidence makes it a therapy-selection biomarker in
    established metastatic disease.
    """

    def test_always_prognostic_only(self):
        result = assess_um_prognostic_class_impl(chr3_status="loss")
        assert result["actionability"] == "prognostic_only"

    def test_prognostic_only_even_for_a_favourable_profile(self):
        result = assess_um_prognostic_class_impl(chr6p_status="gain", chr3_status="disomy")
        assert result["actionability"] == "prognostic_only"

    def test_is_never_predictive(self):
        for kwargs in (
            {"chr3_status": "loss", "bap1_status": "loss"},
            {"eif1ax_status": "mutated"},
            {"sf3b1_status": "mutated"},
        ):
            assert assess_um_prognostic_class_impl(**kwargs)["actionability"] != "predictive"


class TestManagementImplication:
    def test_default_text(self):
        out = assess_prognostic_class(chr3_status="loss")
        assert out["management_implication"] == DEFAULT_MANAGEMENT_IMPLICATION
        assert "do not select therapy" in out["management_implication"]

    def test_confirmed_metastasis_appends_the_already_answered_sentence(self):
        out = assess_prognostic_class(chr3_status="loss", metastasis_confirmed=True)
        assert ALREADY_ANSWERED in out["management_implication"]
        assert out["already_answered"] is True

    def test_without_metastasis_the_sentence_is_absent(self):
        out = assess_prognostic_class(chr3_status="loss", metastasis_confirmed=False)
        assert ALREADY_ANSWERED not in out["management_implication"]
        assert "already_answered" not in out

    def test_interval_is_reported_when_supplied(self):
        out = assess_prognostic_class(
            chr3_status="loss",
            gene_expression_class="Class 2",
            metastasis_confirmed=True,
            metastasis_interval_years=4.6,
        )
        assert out["metastasis_interval_years"] == 4.6
        assert "4.6 years" in out["prior_assay_note"]
        assert "borne out by events" in out["prior_assay_note"]


class TestRiskClassification:
    def test_chr3_loss_is_high_risk(self):
        assert (
            assess_prognostic_class(chr3_status="monosomy")["risk_class"] == "high_metastatic_risk"
        )

    def test_bap1_loss_is_high_risk(self):
        assert assess_prognostic_class(bap1_status="loss")["risk_class"] == "high_metastatic_risk"

    def test_eif1ax_is_low_risk(self):
        assert (
            assess_prognostic_class(eif1ax_status="mutated")["risk_class"] == "low_metastatic_risk"
        )

    def test_sf3b1_is_intermediate_not_low(self):
        """SF3B1 marks LATE metastasis. The risk is deferred, not removed."""
        out = assess_prognostic_class(sf3b1_status="mutated")
        assert out["risk_class"] == "intermediate_metastatic_risk"
        assert "LATE metastasis" in out["risk_note"]

    def test_gene_expression_class_2_alone_is_high_risk(self):
        out = assess_prognostic_class(gene_expression_class="Class 2")
        assert out["risk_class"] == "high_metastatic_risk"

    def test_disagreement_between_assays_is_reported_not_resolved(self):
        out = assess_prognostic_class(eif1ax_status="mutated", gene_expression_class="Class 2")
        assert "disagrees" in out["risk_note"]


class TestMarkerInterpretation:
    def test_undetermined_marker_is_not_counted_as_absent(self):
        out = assess_prognostic_class(chr3_status="unknown", bap1_status="loss")
        assert "chr3_loss" in out["undetermined_markers"]
        assert "chr3_loss" not in out["adverse_markers"]

    def test_unparseable_status_is_undetermined(self):
        out = assess_prognostic_class(chr3_status="imbalance detected, direction unresolved")
        assert "chr3_loss" in out["undetermined_markers"]

    def test_explicit_absence_is_recorded_as_absent(self):
        out = assess_prognostic_class(chr3_status="disomy", eif1ax_status="mutated")
        assert out["markers"]["chr3_loss"]["state"] == "absent"
        assert "chr3_loss" not in out["undetermined_markers"]

    def test_undetermined_markers_are_named_in_the_limits(self):
        out = assess_prognostic_class(chr3_status="unknown", bap1_status="loss")
        assert any("not determined" in limit for limit in out["limits"])

    def test_nothing_determined_is_indeterminate(self):
        assert assess_prognostic_class()["risk_class"] == "indeterminate"


class TestEnvelope:
    def test_limits_state_the_prognostic_boundary(self):
        result = assess_um_prognostic_class_impl(chr3_status="loss")
        joined = " ".join(result["limits"])
        assert "PRIMARY" in joined
        assert "does not estimate response to any therapy" in joined

    def test_nothing_determined_is_not_assessable(self):
        result = assess_um_prognostic_class_impl()
        assert result["grade"] == "not_assessable"
        assert result["value"] == {}
        assert result["limits"]

    def test_metastasis_adds_a_limit_about_the_resolved_question(self):
        result = assess_um_prognostic_class_impl(chr3_status="loss", metastasis_confirmed=True)
        assert any("resolved by observation" in limit for limit in result["limits"])

    def test_confidence_note_carries_the_management_implication(self):
        result = assess_um_prognostic_class_impl(chr3_status="loss")
        assert "Management implication" in result["confidence_note"]
