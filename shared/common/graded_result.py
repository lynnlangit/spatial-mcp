"""The GradedResult envelope — every analytic tool returns one, patient-report consumes it.

Rationale (CNV_TOOLS_SPEC.md section 1)
---------------------------------------
A bare number must not be able to leave the platform. Three specific failures
motivated this envelope, all observed on real specimens:

  1. A confident copy-number call on a library that cannot support one.
  2. A plausible number with no patient-specific evidence behind it — a pathway
     score of 0.61 with a therapy recommendation attached, assembled almost
     entirely from tool defaults.
  3. A target-level database answering a therapy-level question.

The envelope carries the evidence grade, the assumptions, the limits, the
detectability analysis, and an explicit declaration of whether the result can
change clinical management. The invariants below are enforced in code rather
than documented, because a documented invariant is a suggestion.
"""

from __future__ import annotations

import hashlib
import json
from enum import Enum
from typing import Any, Iterable, Mapping

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "EvidenceGrade",
    "ClinicalActionability",
    "Detectability",
    "GradedResult",
    "compute_input_digest",
]


class EvidenceGrade(str, Enum):
    """How much weight this result can bear."""

    DEFINITIVE = "definitive"  # clinical laboratory result
    HIGH = "high"  # live API or reproducible computation on real data
    MODERATE = "moderate"  # computation with material assumptions
    LOW = "low"  # exploratory; requires clinician review
    NOT_ASSESSABLE = "not_assessable"  # the input cannot support this question


class ClinicalActionability(str, Enum):
    """What a care team may do with this result.

    The distinction that matters is PROGNOSTIC_ONLY vs PREDICTIVE. A prognostic
    marker estimates risk. A predictive marker bears on which therapy to give.
    Chromosome 3 status in uveal melanoma is the former and has been read as the
    latter.
    """

    NONE = "none"  # default; changes nothing
    INFORMATIONAL = "informational"  # context only
    PROGNOSTIC_ONLY = "prognostic_only"  # estimates risk; does NOT select therapy
    PREDICTIVE = "predictive"  # bears on therapy selection


class Detectability(BaseModel):
    """Attached to any result that could be a false negative.

    `independent_units` is the count that sets the standard error — haplotype
    blocks, not sites. Reporting a site count where an independent-observation
    count is meant overstates power by sqrt(sites / blocks).
    """

    measurable: bool
    min_detectable_effect: float | None = None
    observed_noise_sd: float | None = None
    independent_units: int = Field(..., ge=0)
    unit_type: str  # "haplotype_block", "capture_target", ...
    power_note: str


def compute_input_digest(payload: Any) -> str:
    """sha256 over a canonical JSON rendering of the tool's inputs.

    Sorted keys and a fixed separator so the digest is stable across runs and
    across dict insertion order. Non-JSON-serializable values fall back to
    ``repr``, which keeps the digest computable rather than raising inside a
    tool that was otherwise about to succeed.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class GradedResult(BaseModel):
    """The only object permitted to cross the analysis/reporting boundary."""

    tool: str
    tool_version: str
    grade: EvidenceGrade
    actionability: ClinicalActionability = ClinicalActionability.NONE
    confidence_note: str  # one sentence a clinician can read
    assumptions: list[str] = Field(default_factory=list)  # every assumption, stated
    limits: list[str] = Field(default_factory=list)  # what this specifically cannot show
    detectability: Detectability | None = None
    synthetic_inputs: bool = False  # real-data-only policy
    input_digest: str = ""  # sha256 of the input payload, for reproducibility
    value: dict[str, Any] = Field(default_factory=dict)  # the payload

    # ------------------------------------------------------------------ #
    # Invariants — enforced here, not in documentation.
    # ------------------------------------------------------------------ #

    @model_validator(mode="after")
    def _enforce_invariants(self) -> "GradedResult":
        # A NOT_ASSESSABLE grade must say what could not be assessed, and must
        # not smuggle a number out alongside the refusal. Returning both is the
        # exact failure this grade exists to prevent.
        if self.grade is EvidenceGrade.NOT_ASSESSABLE:
            if not self.limits:
                raise ValueError(
                    "grade=NOT_ASSESSABLE requires a non-empty `limits` list stating "
                    "what could not be determined"
                )
            if self.value:
                raise ValueError(
                    "grade=NOT_ASSESSABLE forbids a populated `value`; returning a "
                    "number alongside NOT_ASSESSABLE is a bug, not a convenience"
                )

        # DEFINITIVE is reserved for a clinical laboratory result, which is a
        # measurement rather than a computation and therefore carries no
        # analytic assumptions of ours. Every other grade is computational.
        if self.grade is not EvidenceGrade.DEFINITIVE and not self.assumptions:
            raise ValueError(
                f"grade={self.grade.value} is a computational result and requires a "
                "non-empty `assumptions` list. If you cannot name an assumption, you "
                "have not looked hard enough."
            )

        return self

    # ------------------------------------------------------------------ #
    # Synthetic-input propagation
    # ------------------------------------------------------------------ #

    @classmethod
    def derive(
        cls,
        parents: Iterable["GradedResult" | Mapping[str, Any] | None],
        **fields: Any,
    ) -> "GradedResult":
        """Build a result whose inputs include other results.

        `synthetic_inputs` is the OR of this result's own flag and every
        parent's. A result derived from a synthetic input is synthetic, and a
        caller cannot clear the flag by omitting it.
        """
        inherited = False
        for parent in parents:
            if parent is None:
                continue
            if isinstance(parent, GradedResult):
                inherited = inherited or parent.synthetic_inputs
            elif isinstance(parent, Mapping):
                inherited = inherited or bool(parent.get("synthetic_inputs", False))
        fields["synthetic_inputs"] = bool(fields.get("synthetic_inputs", False)) or inherited
        return cls(**fields)

    def propagate_synthetic(
        self, *parents: "GradedResult" | Mapping[str, Any] | None
    ) -> "GradedResult":
        """Mark this result synthetic if any parent was. Never clears the flag."""
        for parent in parents:
            if parent is None:
                continue
            if isinstance(parent, GradedResult):
                flag = parent.synthetic_inputs
            elif isinstance(parent, Mapping):
                flag = bool(parent.get("synthetic_inputs", False))
            else:
                flag = False
            if flag:
                self.synthetic_inputs = True
        return self

    def to_dict(self) -> dict[str, Any]:
        """Plain-dict rendering for the MCP boundary."""
        return self.model_dump(mode="json")
