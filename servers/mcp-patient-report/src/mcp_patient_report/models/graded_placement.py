"""Placement rules for GradedResult objects inside a patient report.

The gap this closes
-------------------
`patient-report` previously accepted free-form content. A recent analysis
produced a document addressed to an oncology care team carrying no evidence
grades, no validation pass and no approval gate, because it was assembled
entirely outside this pipeline. Nothing in the server could have caught that.

Two rules are now enforced in code, not documentation:

  * A PROGNOSTIC_ONLY result may not appear in a treatment-hypotheses section.
    A prognostic marker estimates risk; it does not select therapy. Placing one
    under "treatment" is how a risk estimate becomes a recommendation.
  * A GradedResult with an empty `assumptions` list is rejected outright. Every
    computational result rests on assumptions, and a result that names none has
    not been examined, whatever its grade says.

The placement table (CNV_TOOLS_SPEC.md section 11) is a ceiling, not a slot: a
result may always be cited in Methods, and may appear in the section matching
its actionability or any less consequential one.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class ReportSection(str, Enum):
    """Sections a graded result may be placed in."""

    TREATMENT_HYPOTHESES = "treatment_hypotheses"
    PROGNOSTIC_FINDINGS = "prognostic_findings"
    CONTEXT = "context"
    METHODS = "methods"


class ReportEvidenceGrade(str, Enum):
    DEFINITIVE = "definitive"
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"
    NOT_ASSESSABLE = "not_assessable"


class ReportActionability(str, Enum):
    NONE = "none"
    INFORMATIONAL = "informational"
    PROGNOSTIC_ONLY = "prognostic_only"
    PREDICTIVE = "predictive"


# Which sections each actionability level is permitted to appear in.
ALLOWED_SECTIONS: dict[ReportActionability, set[ReportSection]] = {
    ReportActionability.PREDICTIVE: {
        ReportSection.TREATMENT_HYPOTHESES,
        ReportSection.CONTEXT,
        ReportSection.METHODS,
    },
    ReportActionability.PROGNOSTIC_ONLY: {
        # Deliberately excludes TREATMENT_HYPOTHESES. This is the rule.
        ReportSection.PROGNOSTIC_FINDINGS,
        ReportSection.CONTEXT,
        ReportSection.METHODS,
    },
    ReportActionability.INFORMATIONAL: {
        ReportSection.CONTEXT,
        ReportSection.METHODS,
    },
    ReportActionability.NONE: {
        ReportSection.METHODS,
    },
}


class ReportDetectability(BaseModel):
    """Power context, rendered adjacent to the number it qualifies."""

    measurable: bool
    min_detectable_effect: float | None = None
    observed_noise_sd: float | None = None
    independent_units: int = 0
    unit_type: str = ""
    power_note: str = ""


class PlacedGradedResult(BaseModel):
    """A GradedResult together with the report section it is placed in."""

    section: ReportSection = Field(
        ..., description="Where in the report this result appears"
    )
    tool: str
    tool_version: str = ""
    grade: ReportEvidenceGrade
    actionability: ReportActionability = ReportActionability.NONE
    confidence_note: str
    assumptions: list[str] = Field(default_factory=list)
    limits: list[str] = Field(default_factory=list)
    detectability: ReportDetectability | None = None
    synthetic_inputs: bool = False
    input_digest: str = ""
    value: dict = Field(default_factory=dict)
    title: str | None = Field(
        None, description="Optional human-readable heading for this result"
    )

    @field_validator("assumptions")
    @classmethod
    def _assumptions_not_empty(cls, v: list[str]) -> list[str]:
        # Rejected here rather than warned about. A result naming no assumptions
        # has not been examined, and a warning would let it into the document.
        if not v:
            raise ValueError(
                "a GradedResult placed in a report must state its assumptions; "
                "an empty `assumptions` list is rejected"
            )
        return v

    @model_validator(mode="after")
    def _enforce_placement(self) -> "PlacedGradedResult":
        allowed = ALLOWED_SECTIONS[self.actionability]
        if self.section not in allowed:
            if (
                self.actionability is ReportActionability.PROGNOSTIC_ONLY
                and self.section is ReportSection.TREATMENT_HYPOTHESES
            ):
                raise ValueError(
                    f"'{self.tool}' is PROGNOSTIC_ONLY and cannot appear in a treatment "
                    "hypotheses section. A prognostic marker estimates risk; it does not "
                    "select therapy. Place it under prognostic_findings."
                )
            raise ValueError(
                f"'{self.tool}' has actionability={self.actionability.value} and may appear "
                f"only in {sorted(s.value for s in allowed)}; it was placed in "
                f"'{self.section.value}'."
            )

        # Mirrors the envelope's own invariant, so a hand-assembled payload
        # cannot bypass it by arriving as plain JSON.
        if self.grade is ReportEvidenceGrade.NOT_ASSESSABLE:
            if not self.limits:
                raise ValueError(
                    f"'{self.tool}' is NOT_ASSESSABLE and must state in `limits` what could "
                    "not be determined."
                )
            if self.value:
                raise ValueError(
                    f"'{self.tool}' is NOT_ASSESSABLE but carries a populated `value`. A "
                    "refusal must not travel with a number."
                )
        return self

    @property
    def display_title(self) -> str:
        return self.title or self.tool

    @property
    def is_not_assessable(self) -> bool:
        return self.grade is ReportEvidenceGrade.NOT_ASSESSABLE


__all__ = [
    "ReportSection",
    "ReportEvidenceGrade",
    "ReportActionability",
    "ReportDetectability",
    "PlacedGradedResult",
    "ALLOWED_SECTIONS",
]
