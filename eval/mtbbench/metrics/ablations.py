"""
Table C: Ablation runner.

Conditions:
- No HITL gate: Remove approve_patient_report call
- No XAI layer: Omit evidence_strength_summary from report
- No de-id check: Skip validate_deidentification
- Base LLM (no tools): Same cases, zero tool calls
- Majority-class baseline: Always predicts majority answer (reference floor)
- Random baseline: Coin-flip prediction (expected ~50%)

Each ablation re-runs the case with one component removed, then computes
the delta vs. the full platform run.

Baseline design note:
  With 56% Yes / 44% No class imbalance in the 180 MTBBench questions,
  a naive always-Yes predictor scores 56%. The majority_class and random
  baselines make this floor explicit so reviewers can verify the platform
  and base_llm both exceed trivial strategies.
"""

import hashlib
import time
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
    "majority_class",
    "random_baseline",
]

# Majority answer across the 180 MTBBench questions (56.1% = "A) Yes").
# Updated if the dataset changes.
_MAJORITY_ANSWER = "A) Yes"


def _deterministic_coin_flip(case_id: str, question: str) -> str:
    """Deterministic pseudo-random prediction seeded by case+question.

    Uses SHA-256 so results are reproducible across runs without importing
    random (which would make test output non-deterministic).
    """
    digest = hashlib.sha256(f"{case_id}:{question}".encode()).hexdigest()
    return "A) Yes" if int(digest, 16) % 2 == 0 else "B) No"


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
        transcript.tool_calls = [
            tc for tc in transcript.tool_calls if tc.tool != "approve_patient_report"
        ]
        transcript.hitl_triggered = False
        return transcript

    elif condition == "no_xai":
        transcript = run_case(case, dry_run=dry_run)
        transcript.xai_evidence_summary = {}
        for tc in transcript.tool_calls:
            tc.xai_metadata = {}
        return transcript

    elif condition == "no_deid":
        transcript = run_case(case, dry_run=dry_run)
        transcript.tool_calls = [
            tc for tc in transcript.tool_calls if tc.tool != "validate_deidentification"
        ]
        transcript.deid_validated = False
        return transcript

    elif condition == "base_llm":
        # Base LLM with no tools — in production uses Claude API with only
        # patient context (no MCP tool calls). In DRY_RUN, uses deterministic
        # coin flip to avoid trivially matching the majority-class baseline.
        transcript = EvalTranscript(case_id=case.case_id)
        start = time.monotonic()
        for q in case.questions:
            if dry_run:
                predicted = _deterministic_coin_flip(case.case_id, q["question"])
            else:
                # TODO (M2): Call Claude API with patient context only, no tools
                raise NotImplementedError(
                    "Real base_llm requires Claude API (no tools). Use dry_run=True."
                )
            gt = q["answer"]
            correct = predicted.strip()[0].upper() == gt.strip()[0].upper()
            transcript.answers.append({
                "question": q["question"],
                "predicted": predicted,
                "ground_truth": gt,
                "correct": correct,
                "type": q.get("type", "unknown"),
                "baseline_method": "deterministic_coin_flip" if dry_run else "claude_no_tools",
            })
        transcript.total_duration_ms = (time.monotonic() - start) * 1000
        return transcript

    elif condition == "majority_class":
        # Always predicts the majority answer. This is the trivial floor —
        # any useful model must beat this. Scores ~56% on current dataset.
        transcript = EvalTranscript(case_id=case.case_id)
        start = time.monotonic()
        for q in case.questions:
            predicted = _MAJORITY_ANSWER
            gt = q["answer"]
            correct = predicted.strip()[0].upper() == gt.strip()[0].upper()
            transcript.answers.append({
                "question": q["question"],
                "predicted": predicted,
                "ground_truth": gt,
                "correct": correct,
                "type": q.get("type", "unknown"),
                "baseline_method": "majority_class",
            })
        transcript.total_duration_ms = (time.monotonic() - start) * 1000
        return transcript

    elif condition == "random_baseline":
        # Deterministic pseudo-random baseline (~50% expected accuracy).
        # Uses SHA-256 for reproducibility.
        transcript = EvalTranscript(case_id=case.case_id)
        start = time.monotonic()
        for q in case.questions:
            predicted = _deterministic_coin_flip(case.case_id, q["question"])
            gt = q["answer"]
            correct = predicted.strip()[0].upper() == gt.strip()[0].upper()
            transcript.answers.append({
                "question": q["question"],
                "predicted": predicted,
                "ground_truth": gt,
                "correct": correct,
                "type": q.get("type", "unknown"),
                "baseline_method": "random_deterministic",
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
