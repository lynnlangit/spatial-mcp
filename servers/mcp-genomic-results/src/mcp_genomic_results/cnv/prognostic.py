"""Uveal melanoma prognostic integration — and the boundary it refuses to cross.

Prognostic is not predictive
----------------------------
A PROGNOSTIC marker estimates the risk that a disease will progress. A
PREDICTIVE marker bears on which therapy to give. They are routinely conflated,
and the conflation is worst when the prognostic marker is strong, because a
strong risk signal feels like it ought to imply an action.

Chromosome 3 status in uveal melanoma is prognostic. The literature establishing
it is built on PRIMARY tumours and estimates the risk that a primary will
metastasise. No published evidence establishes chr3 or BAP1 status as a
biomarker for selecting therapy in established metastatic disease. So this tool
hard-codes `actionability = PROGNOSTIC_ONLY`, not as a default a caller may
override but as a property of the tool.

There is a further case worth naming explicitly: once metastasis is confirmed,
the question a metastatic-risk marker answers has been settled by events. The
marker is not wrong and is not uninformative about the past — it is simply no
longer forecasting anything.
"""

from __future__ import annotations

from typing import Any

DEFAULT_MANAGEMENT_IMPLICATION = (
    "None. Prognostic markers do not select therapy in established metastatic disease."
)

ALREADY_ANSWERED = "The prognostic question this marker addresses has been answered by events."

# Risk direction of each marker in PRIMARY uveal melanoma. "adverse" raises
# estimated metastatic risk, "favourable" lowers it.
MARKER_DIRECTION = {
    "chr3_loss": "adverse",
    "chr8q_gain": "adverse",
    "chr1p_loss": "adverse",
    "bap1_loss": "adverse",
    "chr6p_gain": "favourable",
    "eif1ax_mutated": "favourable",
    # SF3B1 marks an intermediate group characterised by late metastasis rather
    # than by low risk, so it is neither simply adverse nor simply favourable.
    "sf3b1_mutated": "intermediate",
}


def assess_prognostic_class(
    chr3_status: str | None = None,
    chr8q_status: str | None = None,
    chr6p_status: str | None = None,
    chr1p_status: str | None = None,
    bap1_status: str | None = None,
    sf3b1_status: str | None = None,
    eif1ax_status: str | None = None,
    gene_expression_class: str | None = None,
    metastasis_confirmed: bool = False,
    metastasis_interval_years: float | None = None,
) -> dict[str, Any]:
    """Integrate uveal-melanoma prognostic markers into a single statement.

    Status strings are free-form but interpreted case-insensitively; anything
    not recognised as present/absent is treated as undetermined, and an
    undetermined marker contributes nothing rather than being read as absent.
    """
    markers: dict[str, Any] = {}
    adverse: list[str] = []
    favourable: list[str] = []
    intermediate: list[str] = []
    undetermined: list[str] = []

    def record(key: str, raw: str | None, present_words: tuple[str, ...]) -> None:
        state = _interpret(raw, present_words)
        markers[key] = {"input": raw, "state": state}
        if state == "present":
            bucket = {"adverse": adverse, "favourable": favourable, "intermediate": intermediate}[
                MARKER_DIRECTION[key]
            ]
            bucket.append(key)
        elif state == "undetermined":
            undetermined.append(key)

    record("chr3_loss", chr3_status, ("loss", "monosomy", "monosomy_3", "lost"))
    record("chr8q_gain", chr8q_status, ("gain", "gained", "amplification"))
    record("chr6p_gain", chr6p_status, ("gain", "gained", "amplification"))
    record("chr1p_loss", chr1p_status, ("loss", "lost", "deletion"))
    record("bap1_loss", bap1_status, ("loss", "lost", "mutated", "mutant", "deficient"))
    record("sf3b1_mutated", sf3b1_status, ("mutated", "mutant", "positive"))
    record("eif1ax_mutated", eif1ax_status, ("mutated", "mutant", "positive"))

    risk_class, risk_note = _classify(adverse, favourable, intermediate, gene_expression_class)

    management_implication = DEFAULT_MANAGEMENT_IMPLICATION
    if metastasis_confirmed:
        management_implication = f"{DEFAULT_MANAGEMENT_IMPLICATION} {ALREADY_ANSWERED}"

    limits = [
        "Estimates the risk that a PRIMARY uveal melanoma will metastasise. It does not "
        "estimate response to any therapy.",
        "The evidence base for these markers is built on primary tumours; their behaviour "
        "as markers in established metastatic disease is not established.",
    ]
    if undetermined:
        limits.append(
            f"Markers not determined and therefore not counted: {', '.join(sorted(undetermined))}. "
            "An undetermined marker is not the same as an absent one."
        )
    if metastasis_confirmed:
        limits.append(
            "Metastasis is already confirmed in this record, so the risk this class "
            "estimates has been resolved by observation."
        )

    result: dict[str, Any] = {
        "risk_class": risk_class,
        "risk_note": risk_note,
        "markers": markers,
        "adverse_markers": sorted(adverse),
        "favourable_markers": sorted(favourable),
        "intermediate_markers": sorted(intermediate),
        "undetermined_markers": sorted(undetermined),
        "gene_expression_class": gene_expression_class,
        "metastasis_confirmed": metastasis_confirmed,
        "management_implication": management_implication,
        "limits": limits,
    }

    if metastasis_confirmed:
        result["already_answered"] = True
        result["already_answered_note"] = ALREADY_ANSWERED
        if metastasis_interval_years is not None:
            result["metastasis_interval_years"] = metastasis_interval_years
            result["prior_assay_note"] = (
                f"Metastasis was confirmed {metastasis_interval_years:.1f} years after primary "
                "treatment. A prior gene-expression class call predicting metastatic risk in "
                "that window was borne out by events."
                if gene_expression_class
                else f"Metastasis was confirmed {metastasis_interval_years:.1f} years after "
                "primary treatment."
            )

    return result


def _interpret(raw: str | None, present_words: tuple[str, ...]) -> str:
    """Map a free-form status string onto present / absent / undetermined."""
    if raw is None:
        return "undetermined"
    text = str(raw).strip().lower()
    if not text or text in ("unknown", "not_assessed", "undetermined", "na", "n/a"):
        return "undetermined"
    if any(w in text for w in present_words):
        return "present"
    if any(
        w in text
        for w in (
            "disomy",
            "normal",
            "neutral",
            "absent",
            "wild_type",
            "wildtype",
            "wt",
            "retained",
            "no loss",
            "no gain",
            "intact",
            "negative",
        )
    ):
        return "absent"
    return "undetermined"


def _classify(
    adverse: list[str],
    favourable: list[str],
    intermediate: list[str],
    gep_class: str | None,
) -> tuple[str, str]:
    """Assign a coarse risk class from the marker profile.

    The marker-derived label is computed FIRST and independently of any prior
    gene-expression call, so the two can be compared. Folding the expression
    call into the label before comparing would make it agree with itself by
    construction, and a disagreement between two assays measuring different
    things is information worth surfacing, not an error to resolve.
    """
    gep = (gep_class or "").strip().lower()
    gep_high = any(k in gep for k in ("class 2", "class_2", "class2"))
    gep_low = any(k in gep for k in ("class 1", "class_1", "class1"))

    # Step 1 — the label the chromosomal and mutational markers support on their own.
    if adverse:
        marker_label = "high_metastatic_risk"
        marker_note = (
            f"Adverse marker profile ({', '.join(sorted(adverse))}) consistent with the "
            "high-metastatic-risk group in primary uveal melanoma."
        )
    elif intermediate:
        marker_label = "intermediate_metastatic_risk"
        marker_note = (
            "SF3B1 mutation marks an intermediate group characterised by LATE metastasis "
            "rather than by low risk; the risk is deferred, not removed."
        )
    elif favourable:
        marker_label = "low_metastatic_risk"
        marker_note = (
            f"Favourable marker profile ({', '.join(sorted(favourable))}) with no adverse "
            "markers recorded."
        )
    else:
        marker_label = None
        marker_note = ""

    # Step 2 — fold in the expression call, which can supply a label on its own
    # when no marker reached a determined state.
    if marker_label is None:
        if gep_high:
            return "high_metastatic_risk", (
                "Gene expression class 2, consistent with the high-metastatic-risk group. "
                "No chromosomal or mutational marker reached a determined state."
            )
        if gep_low:
            return "low_metastatic_risk", (
                "Gene expression class 1, consistent with the low-metastatic-risk group. "
                "No chromosomal or mutational marker reached a determined state."
            )
        return "indeterminate", (
            "No marker reached a determined state; no risk class can be assigned."
        )

    label, note = marker_label, marker_note

    # Step 3 — an expression call that contradicts the markers. Both are
    # reported; neither overrides the other.
    disagrees = (
        (gep_high and marker_label == "low_metastatic_risk")
        or (gep_low and marker_label == "high_metastatic_risk")
        or (gep_high and marker_label == "intermediate_metastatic_risk")
    )
    if disagrees:
        note += (
            f" NOTE: the prior gene-expression call ({gep_class}) disagrees with the "
            "chromosomal/mutational profile. Both are reported; neither overrides the "
            "other, because they measure different things."
        )
        # A disagreement is not resolved by silently taking the worse of the two,
        # but the higher-risk reading is the safer one to carry forward.
        if gep_high:
            label = "high_metastatic_risk"
    elif gep_high and marker_label == "high_metastatic_risk":
        note += " The prior gene-expression call (class 2) agrees."
    elif gep_low and marker_label == "low_metastatic_risk":
        note += " The prior gene-expression call (class 1) agrees."

    return label, note


__all__ = [
    "assess_prognostic_class",
    "DEFAULT_MANAGEMENT_IMPLICATION",
    "ALREADY_ANSWERED",
]
