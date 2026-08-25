"""The reporting handoff: placement enforcement and adjacent rendering (spec section 11).

Every rejection path is tested. A rejection that does not fire is worse than no
check, because it advertises a guarantee it does not provide.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_patient_report.models import (  # noqa: E402
    ALLOWED_SECTIONS,
    PatientReportData,
    PlacedGradedResult,
    ReportActionability,
    ReportSection,
)
from mcp_patient_report.report.report_generator import ReportGenerator  # noqa: E402


def _result(**overrides):
    payload = {
        "section": "methods",
        "tool": "genomic-results.example",
        "tool_version": "1.0.0",
        "grade": "moderate",
        "actionability": "none",
        "confidence_note": "An example finding.",
        "assumptions": ["The input was what it claimed to be."],
        "limits": ["It cannot show everything."],
        "value": {"number": 1},
    }
    payload.update(overrides)
    return payload


class TestPrognosticMayNotEnterTreatment:
    """The rule that matters most.

    A prognostic marker estimates risk. Placing one under "treatment" is how a
    risk estimate silently becomes a recommendation.
    """

    def test_prognostic_only_in_treatment_is_rejected(self):
        with pytest.raises(ValidationError, match="does not select therapy"):
            PlacedGradedResult(**_result(
                section="treatment_hypotheses", actionability="prognostic_only"
            ))

    def test_prognostic_only_in_prognostic_findings_is_accepted(self):
        result = PlacedGradedResult(**_result(
            section="prognostic_findings", actionability="prognostic_only"
        ))
        assert result.section is ReportSection.PROGNOSTIC_FINDINGS

    def test_treatment_hypotheses_is_never_allowed_for_prognostic_only(self):
        assert ReportSection.TREATMENT_HYPOTHESES not in ALLOWED_SECTIONS[
            ReportActionability.PROGNOSTIC_ONLY
        ]

    def test_rejection_survives_the_full_report_model(self):
        """The rule must hold at the boundary a report actually crosses."""
        with pytest.raises(ValidationError, match="does not select therapy"):
            PatientReportData(**_minimal_report(graded_results=[
                _result(section="treatment_hypotheses", actionability="prognostic_only")
            ]))


class TestAssumptionsRequired:
    def test_empty_assumptions_are_rejected(self):
        with pytest.raises(ValidationError, match="must state its assumptions"):
            PlacedGradedResult(**_result(assumptions=[]))

    def test_rejection_survives_the_full_report_model(self):
        with pytest.raises(ValidationError, match="must state its assumptions"):
            PatientReportData(**_minimal_report(graded_results=[_result(assumptions=[])]))

    def test_a_stated_assumption_is_accepted(self):
        assert PlacedGradedResult(**_result(assumptions=["Purity is 0.1664."])).assumptions


class TestPlacementTable:
    @pytest.mark.parametrize(
        "actionability,section",
        [
            ("predictive", "treatment_hypotheses"),
            ("prognostic_only", "prognostic_findings"),
            ("informational", "context"),
            ("none", "methods"),
        ],
    )
    def test_each_actionability_reaches_its_own_section(self, actionability, section):
        assert PlacedGradedResult(**_result(section=section, actionability=actionability))

    @pytest.mark.parametrize(
        "actionability,section",
        [
            ("none", "context"),
            ("none", "treatment_hypotheses"),
            ("informational", "treatment_hypotheses"),
            ("informational", "prognostic_findings"),
            ("predictive", "prognostic_findings"),
        ],
    )
    def test_over_placement_is_rejected(self, actionability, section):
        with pytest.raises(ValidationError):
            PlacedGradedResult(**_result(section=section, actionability=actionability))

    @pytest.mark.parametrize(
        "actionability", ["predictive", "prognostic_only", "informational", "none"]
    )
    def test_anything_may_be_cited_in_methods(self, actionability):
        assert PlacedGradedResult(**_result(section="methods", actionability=actionability))


class TestNotAssessableAtTheBoundary:
    def test_value_alongside_not_assessable_is_rejected(self):
        with pytest.raises(ValidationError, match="must not travel with a number"):
            PlacedGradedResult(**_result(grade="not_assessable", value={"n": 1}))

    def test_missing_limits_is_rejected(self):
        with pytest.raises(ValidationError, match="must state in `limits`"):
            PlacedGradedResult(**_result(grade="not_assessable", limits=[], value={}))

    def test_clean_refusal_is_accepted(self):
        result = PlacedGradedResult(**_result(
            grade="not_assessable", limits=["The library cannot support this."], value={}
        ))
        assert result.is_not_assessable is True


def _minimal_report(**overrides):
    payload = {
        "report_category": "oncology",
        "patient_info": {
            "name": "Synthetic Patient", "age": 60, "sex": "Female",
            "patient_id": "SYNTH001", "diagnosis": "Synthetic diagnosis",
        },
        "diagnosis_summary": {"plain_language_description": "A synthetic description."},
        "genomic_findings": [],
        "treatment_options": [],
        "monitoring_plan": {
            "schedule": [{"test_name": "Scan", "frequency": "Every 3 months",
                          "purpose": "Watch for change"}],
            "warning_signs": ["New symptoms"],
        },
    }
    payload.update(overrides)
    return payload


class TestRendering:
    """Limits and detectability must sit next to the number, not in a footnote."""

    def _html(self):
        report = PatientReportData(**_minimal_report(graded_results=[
            _result(
                section="prognostic_findings", actionability="prognostic_only",
                tool="genomic-results.assess_um_prognostic_class",
                confidence_note="High metastatic risk in primary uveal melanoma.",
                limits=["Estimates the risk that a PRIMARY tumour will metastasise."],
                value={"management_implication":
                       "None. Prognostic markers do not select therapy."},
            ),
            _result(
                section="context", actionability="informational",
                tool="genomic-results.test_allelic_imbalance",
                confidence_note="Allelic imbalance 0.0345; direction undetermined.",
                limits=["This is a MAGNITUDE and cannot separate loss from gain."],
                detectability={
                    "measurable": True, "min_detectable_effect": 0.0268,
                    "observed_noise_sd": 0.0191, "independent_units": 4,
                    "unit_type": "haplotype_block",
                    "power_note": "7 sites in 4 independent haplotype blocks.",
                },
            ),
            _result(
                section="methods", actionability="none",
                tool="genomic-results.detect_library_chemistry",
                grade="not_assessable",
                confidence_note="The four library signals do not agree.",
                limits=["Chemistry is indeterminate."], value={},
            ),
        ]))
        return ReportGenerator().render(report, report_type="full")

    def test_limits_are_rendered(self):
        html = self._html()
        assert "What this cannot show" in html
        assert "This is a MAGNITUDE and cannot separate loss from gain." in html

    def test_detectability_is_rendered_with_the_finding(self):
        html = self._html()
        assert "Could this have been detected?" in html
        assert "7 sites in 4 independent haplotype blocks." in html

    def test_limits_appear_after_their_own_finding_not_at_the_end(self):
        """Adjacency, checked by position: the caveat sits inside its own block."""
        html = self._html()
        finding = html.index("Allelic imbalance 0.0345")
        its_limit = html.index("This is a MAGNITUDE and cannot separate loss from gain.")
        disclaimer = html.index("Important Notice")
        assert finding < its_limit < disclaimer

    def test_not_assessable_renders_as_a_statement_not_an_omission(self):
        html = self._html()
        assert "Could not be determined" in html
        assert "The four library signals do not agree." in html

    def test_prognostic_notice_is_rendered(self):
        html = self._html()
        assert "does not select therapy" in html

    def test_assumptions_are_rendered(self):
        assert "Assumptions this rests on" in self._html()

    def test_sections_without_content_are_omitted(self):
        """No PREDICTIVE result was supplied, so no treatment section appears."""
        assert "Treatment Hypotheses" not in self._html()


class TestValidateReportDataTool:
    """The rejections must fire at the MCP boundary, not only in the model."""

    @staticmethod
    async def _validate(payload):
        import json

        from mcp_patient_report.server import validate_report_data

        return await validate_report_data.fn(json.dumps(payload))

    @pytest.mark.asyncio
    async def test_rejects_prognostic_result_in_treatment_section(self):
        out = await self._validate(_minimal_report(graded_results=[
            _result(section="treatment_hypotheses", actionability="prognostic_only")
        ]))
        assert out["valid"] is False
        assert any("does not select therapy" in e for e in out["errors"])

    @pytest.mark.asyncio
    async def test_rejects_result_with_no_assumptions(self):
        out = await self._validate(_minimal_report(graded_results=[
            _result(assumptions=[])
        ]))
        assert out["valid"] is False
        assert any("must state its assumptions" in e for e in out["errors"])

    @pytest.mark.asyncio
    async def test_accepts_a_correctly_placed_report(self):
        out = await self._validate(_minimal_report(graded_results=[
            _result(section="prognostic_findings", actionability="prognostic_only")
        ]))
        assert out["valid"] is True
        assert out["summary"]["graded_results_count"] == 1
        assert out["summary"]["graded_results_by_actionability"] == {"prognostic_only": 1}

    @pytest.mark.asyncio
    async def test_warns_when_no_graded_results_are_supplied(self):
        """Content assembled outside the graded pipeline carries no grades at all."""
        out = await self._validate(_minimal_report())
        assert out["valid"] is True
        assert any("No GradedResult objects supplied" in w for w in out["warnings"])

    @pytest.mark.asyncio
    async def test_warns_on_synthetic_inputs(self):
        out = await self._validate(_minimal_report(graded_results=[
            _result(synthetic_inputs=True)
        ]))
        assert any("synthetic inputs" in w for w in out["warnings"])

    @pytest.mark.asyncio
    async def test_not_assessable_results_are_listed_in_the_summary(self):
        out = await self._validate(_minimal_report(graded_results=[
            _result(grade="not_assessable", limits=["Indeterminate."], value={})
        ]))
        assert out["summary"]["not_assessable_results"] == ["genomic-results.example"]
