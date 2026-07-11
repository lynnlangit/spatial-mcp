"""
Table C: Ablation runner.

Two sets of conditions:

  ABLATION_CONDITIONS (M2 — backward compat):
    7 conditions including majority_class and random_baseline for Table A.

  TABLE_C_CONDITIONS (M4 — governance ablations):
    5 conditions where exactly one governance component is removed.
    Used for the paired ablation study (Table C in the paper).

    | Condition         | Removes                        | Primary delta            |
    |-------------------|--------------------------------|--------------------------|
    | full_platform     | (nothing — reference)          | —                        |
    | no_hitl           | approve_patient_report         | HITL catch → 0%          |
    | no_xai            | evidence_strength_summary      | Calibration undefined    |
    | no_deid           | validate_deidentification      | De-id integrity → 0%    |
    | base_llm_no_tools | ALL MCP tool calls             | Accuracy + governance ↓  |

Efficiency:
  run_table_c_case() runs full_platform ONCE per case, then derives the 3
  governance ablations from deep copies of the same transcript (they modify
  governance fields only, not answers). Only base_llm_no_tools runs a
  separate answer-generation path.

Baseline design note:
  With 56% Yes / 44% No class imbalance in the 180 MTBBench questions,
  a naive always-Yes predictor scores 56%. The majority_class and random
  baselines make this floor explicit so reviewers can verify the platform
  and base_llm both exceed trivial strategies.

Cite: Jain et al., MTBBench, NeurIPS 2024, github.com/bunnelab/mtbbench
"""

import copy
import hashlib
import time
from typing import Any

from eval.mtbbench.case_adapter import MTBCase, mtbcase_to_platform_context
from eval.mtbbench.eval_runner import EvalTranscript, run_case, _generate_answer
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics
from eval.mtbbench.metrics.governance import compute_governance_metrics


# M2 conditions (backward compat)
ABLATION_CONDITIONS = [
    "full_platform",
    "no_hitl",
    "no_xai",
    "no_deid",
    "base_llm",
    "majority_class",
    "random_baseline",
]

# M4 Table C conditions — each removes exactly one governance component
TABLE_C_CONDITIONS = [
    "full_platform",
    "no_hitl",
    "no_xai",
    "no_deid",
    "base_llm_no_tools",
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
        condition: One of ABLATION_CONDITIONS or TABLE_C_CONDITIONS
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

    elif condition in ("base_llm", "base_llm_no_tools"):
        # Base LLM with no tools — in production uses Claude API with only
        # patient context (no MCP tool calls). In DRY_RUN, uses deterministic
        # coin flip to avoid trivially matching the majority-class baseline.
        transcript = EvalTranscript(case_id=case.case_id)
        context = mtbcase_to_platform_context(case)
        start = time.monotonic()
        for q in case.questions:
            predicted = _generate_answer(
                q, context, tool_results=[], dry_run=dry_run,
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


def run_table_c_case(
    case: MTBCase, dry_run: bool = True,
) -> dict[str, EvalTranscript]:
    """
    Run one case under all Table C conditions efficiently.

    Runs full_platform ONCE, derives governance ablations (no_hitl, no_xai,
    no_deid) from deep copies of the same transcript. Only base_llm_no_tools
    runs a separate answer-generation path.

    This avoids 4× redundant server calls: in DRY_RUN the governance
    ablations don't change answers, only governance fields.

    Args:
        case: MTBCase to evaluate
        dry_run: Use DRY_RUN mode

    Returns:
        dict mapping condition name -> EvalTranscript
    """
    # Run full_platform once — the reference condition
    full_transcript = run_case(case, dry_run=dry_run)

    results: dict[str, EvalTranscript] = {"full_platform": full_transcript}

    # ── no_hitl: remove approve_patient_report, clear HITL flag ─────────
    t = copy.deepcopy(full_transcript)
    t.tool_calls = [tc for tc in t.tool_calls if tc.tool != "approve_patient_report"]
    t.hitl_triggered = False
    results["no_hitl"] = t

    # ── no_xai: clear all XAI metadata and evidence summary ─────────────
    t = copy.deepcopy(full_transcript)
    t.xai_evidence_summary = {}
    for tc in t.tool_calls:
        tc.xai_metadata = {}
    results["no_xai"] = t

    # ── no_deid: remove validate_deidentification, clear de-id flag ─────
    t = copy.deepcopy(full_transcript)
    t.tool_calls = [tc for tc in t.tool_calls if tc.tool != "validate_deidentification"]
    t.deid_validated = False
    results["no_deid"] = t

    # ── base_llm_no_tools: separate answer path, no tool calls ──────────
    results["base_llm_no_tools"] = run_ablation(
        case, "base_llm_no_tools", dry_run=dry_run,
    )

    return results


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
