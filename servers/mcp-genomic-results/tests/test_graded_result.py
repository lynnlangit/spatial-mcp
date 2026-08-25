"""Invariants of the GradedResult envelope (CNV_TOOLS_SPEC.md section 1).

Each invariant is tested in both directions. A rule that only ever gets its
happy path exercised is a rule nobody knows is broken.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "shared"))

from common.graded_result import (  # noqa: E402
    ClinicalActionability,
    Detectability,
    EvidenceGrade,
    GradedResult,
    compute_input_digest,
)


def _base(**overrides):
    payload = {
        "tool": "genomic-results.example",
        "tool_version": "1.0.0",
        "grade": EvidenceGrade.HIGH,
        "confidence_note": "An example result.",
        "assumptions": ["The input was what it claimed to be."],
    }
    payload.update(overrides)
    return payload


class TestActionabilityDefault:
    def test_defaults_to_none(self):
        """A tool must opt IN to a higher actionability, never inherit one."""
        assert GradedResult(**_base()).actionability is ClinicalActionability.NONE

    def test_can_be_raised_explicitly(self):
        result = GradedResult(**_base(actionability=ClinicalActionability.PROGNOSTIC_ONLY))
        assert result.actionability is ClinicalActionability.PROGNOSTIC_ONLY


class TestNotAssessable:
    def test_requires_limits(self):
        with pytest.raises(ValidationError, match="non-empty `limits`"):
            GradedResult(**_base(grade=EvidenceGrade.NOT_ASSESSABLE))

    def test_forbids_populated_value(self):
        """Returning a number alongside NOT_ASSESSABLE is the bug this grade prevents."""
        with pytest.raises(ValidationError, match="forbids a populated `value`"):
            GradedResult(
                **_base(
                    grade=EvidenceGrade.NOT_ASSESSABLE,
                    limits=["The library cannot support this question."],
                    value={"imbalance": 0.0439},
                )
            )

    def test_accepts_limits_with_empty_value(self):
        result = GradedResult(
            **_base(
                grade=EvidenceGrade.NOT_ASSESSABLE,
                limits=["The library cannot support this question."],
            )
        )
        assert result.value == {}
        assert result.limits


class TestAssumptions:
    @pytest.mark.parametrize(
        "grade",
        [EvidenceGrade.HIGH, EvidenceGrade.MODERATE, EvidenceGrade.LOW],
    )
    def test_computational_grades_require_assumptions(self, grade):
        with pytest.raises(ValidationError, match="non-empty `assumptions`"):
            GradedResult(**_base(grade=grade, assumptions=[]))

    def test_not_assessable_also_requires_assumptions(self):
        with pytest.raises(ValidationError, match="non-empty `assumptions`"):
            GradedResult(
                **_base(grade=EvidenceGrade.NOT_ASSESSABLE, assumptions=[], limits=["something"])
            )

    def test_definitive_is_exempt(self):
        """A clinical laboratory result is a measurement, not a computation of ours."""
        result = GradedResult(**_base(grade=EvidenceGrade.DEFINITIVE, assumptions=[]))
        assert result.assumptions == []


class TestSyntheticPropagation:
    def test_derive_inherits_synthetic_flag(self):
        parent = GradedResult(**_base(synthetic_inputs=True))
        child = GradedResult.derive([parent], **_base(tool="downstream"))
        assert child.synthetic_inputs is True

    def test_derive_from_real_parent_stays_real(self):
        parent = GradedResult(**_base(synthetic_inputs=False))
        child = GradedResult.derive([parent], **_base(tool="downstream"))
        assert child.synthetic_inputs is False

    def test_caller_cannot_clear_the_flag(self):
        """Passing synthetic_inputs=False must not launder a synthetic parent."""
        parent = GradedResult(**_base(synthetic_inputs=True))
        child = GradedResult.derive([parent], **_base(tool="downstream", synthetic_inputs=False))
        assert child.synthetic_inputs is True

    def test_derive_accepts_plain_dict_parents(self):
        child = GradedResult.derive([{"synthetic_inputs": True}, None], **_base(tool="downstream"))
        assert child.synthetic_inputs is True

    def test_propagate_never_clears(self):
        result = GradedResult(**_base(synthetic_inputs=True))
        result.propagate_synthetic({"synthetic_inputs": False})
        assert result.synthetic_inputs is True


class TestInputDigest:
    def test_is_order_independent(self):
        assert compute_input_digest({"a": 1, "b": 2}) == compute_input_digest({"b": 2, "a": 1})

    def test_distinguishes_different_inputs(self):
        assert compute_input_digest({"a": 1}) != compute_input_digest({"a": 2})

    def test_survives_unserializable_values(self):
        assert compute_input_digest({"path": Path("/tmp/x")})


class TestSerialization:
    def test_round_trips_through_dict(self):
        original = GradedResult(
            **_base(
                actionability=ClinicalActionability.INFORMATIONAL,
                detectability=Detectability(
                    measurable=True,
                    min_detectable_effect=0.0268,
                    observed_noise_sd=0.0191,
                    independent_units=4,
                    unit_type="haplotype_block",
                    power_note="4 blocks.",
                ),
                value={"imbalance": 0.0345},
            )
        )
        restored = GradedResult(**original.to_dict())
        assert restored.value == {"imbalance": 0.0345}
        assert restored.detectability.independent_units == 4
        assert restored.actionability is ClinicalActionability.INFORMATIONAL
