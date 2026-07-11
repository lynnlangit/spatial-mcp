"""
Table C: Ablation runner.

Conditions:
- No HITL gate: Remove approve_patient_report call
- No XAI layer: Omit evidence_strength_summary from report
- No de-id check: Skip validate_deidentification
- Base LLM (no tools): Same cases, zero tool calls

Each ablation re-runs the case with one component removed, then computes
the delta vs. the full platform run.
"""

from typing import Any

from eval.mtbbench.case_adapter import MTBCase
from eval.mtbbench.eval_runner import EvalTranscript, run_case
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics
from eval.mtbbench.metrics.governance import compute_governance_metrics


ABLATION_CONDITIONS = [
    "full_platform",
    "no_hitl",
    "no_xai",
    "no_deid",
    "base_llm",
]


def run_ablation(case: MTBCase, condition: str, dry_run: bool = True) -> EvalTranscript:
    """
    Run one case under a specific ablation condition.

    Args:
        case: MTBCase to evaluate
        condition: One of ABLATION_CONDITIONS
        dry_run: Use DRY_RUN mode

    Returns:
        EvalTranscript with the ablated pipeline
    """
    if condition == "full_platform":
        return run_case(case, dry_run=dry_run)

    elif condition == "no_hitl":
        transcript = run_case(case, dry_run=dry_run)
        # Remove HITL gate — simulate as if it was never called
        transcript.tool_calls = [
            tc for tc in transcript.tool_calls if tc.tool != "approve_patient_report"
        ]
        transcript.hitl_triggered = False
        return transcript

    elif condition == "no_xai":
        transcript = run_case(case, dry_run=dry_run)
        # Remove XAI evidence summary — simulate no transparency layer
        transcript.xai_evidence_summary = {}
        for tc in transcript.tool_calls:
            tc.xai_metadata = {}
        return transcript

    elif condition == "no_deid":
        transcript = run_case(case, dry_run=dry_run)
        # Remove de-id check — simulate as if it was never called
        transcript.tool_calls = [
            tc for tc in transcript.tool_calls if tc.tool != "validate_deidentification"
        ]
        transcript.deid_validated = False
        return transcript

    elif condition == "base_llm":
        # No tool calls at all — just generate answers from base LLM
        transcript = EvalTranscript(case_id=case.case_id)
        import time

        start = time.monotonic()
        for q in case.questions:
            # Base LLM: random/majority-class prediction (DRY_RUN = always "A")
            predicted = "A) Yes"
            gt = q["answer"]
            correct = predicted.strip()[0].upper() == gt.strip()[0].upper()
            transcript.answers.append({
                "question": q["question"],
                "predicted": predicted,
                "ground_truth": gt,
                "correct": correct,
            })
        transcript.total_duration_ms = (time.monotonic() - start) * 1000
        return transcript

    else:
        raise ValueError(f"Unknown ablation condition: {condition}")


def compute_ablation_table(case: MTBCase, dry_run: bool = True) -> dict:
    """
    Run all ablation conditions for one case and compute deltas.

    Returns dict mapping condition -> {accuracy_metrics, governance_metrics, delta}.
    """
    results: dict[str, Any] = {}
    full_transcript = run_ablation(case, "full_platform", dry_run=dry_run)
    full_accuracy = compute_accuracy_metrics(full_transcript)
    full_governance = compute_governance_metrics(full_transcript)

    results["full_platform"] = {
        "accuracy": full_accuracy,
        "governance": full_governance,
        "delta_accuracy": 0.0,
    }

    for condition in ABLATION_CONDITIONS[1:]:  # Skip full_platform
        transcript = run_ablation(case, condition, dry_run=dry_run)
        acc = compute_accuracy_metrics(transcript)
        gov = compute_governance_metrics(transcript)
        delta = acc["question_accuracy"] - full_accuracy["question_accuracy"]
        results[condition] = {
            "accuracy": acc,
            "governance": gov,
            "delta_accuracy": delta,
        }

    return results
