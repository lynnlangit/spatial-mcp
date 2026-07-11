"""
Table B: Governance metrics aggregator with bootstrap 95% CIs.

This is the paper's novel contribution — no existing system reports these
metrics. Computes per-case governance scores, aggregates with stratified
breakdown by cancer type, and emits the final Table B in Markdown format.

Bootstrap methodology:
  - B=10000 resamples, seed=42 for reproducibility
  - Percentile-based 95% CI (2.5th and 97.5th percentiles)
  - n=40 cases provides adequate bootstrap precision for binary metrics

Confidence calibration note:
  Given this cohort is 100% MSS and predominantly low-TMB (<5 mut/Mb for
  29/40 patients), the platform SHOULD report predominantly moderate/low
  confidence on immunotherapy-related reasoning. High confidence on
  immunotherapy eligibility for MSS/low-TMB patients would indicate
  miscalibration. This is correct governance behavior to report.

Cite: Jain et al., MTBBench, NeurIPS 2024, github.com/bunnelab/mtbbench
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from eval.mtbbench.eval_runner import EvalTranscript, ToolCall
from eval.mtbbench.metrics.governance import compute_governance_metrics


# Bootstrap parameters
BOOTSTRAP_B = 10000
BOOTSTRAP_SEED = 42

# TMB thresholds (KEYNOTE-158 / NCCN)
TMB_HIGH_THRESHOLD = 10.0  # mut/Mb


def bootstrap_ci(
    values: list[float], n_resamples: int = BOOTSTRAP_B, seed: int = BOOTSTRAP_SEED,
    ci: float = 0.95,
) -> dict:
    """
    Compute bootstrap confidence interval for a list of values.

    Returns dict with mean, ci_low, ci_high, std, n.
    Uses percentile method (Efron & Tibshirani, 1993).
    """
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "std": 0.0, "n": 0}
    if n == 1:
        return {
            "mean": values[0], "ci_low": values[0], "ci_high": values[0],
            "std": 0.0, "n": 1,
        }

    rng = random.Random(seed)
    means = []
    for _ in range(n_resamples):
        resample = [rng.choice(values) for _ in range(n)]
        means.append(sum(resample) / n)

    means.sort()
    alpha = (1 - ci) / 2
    ci_low_idx = int(n_resamples * alpha)
    ci_high_idx = int(n_resamples * (1 - alpha)) - 1

    mean_val = sum(values) / n
    variance = sum((x - mean_val) ** 2 for x in values) / n
    std_val = math.sqrt(variance)

    return {
        "mean": mean_val,
        "ci_low": means[ci_low_idx],
        "ci_high": means[ci_high_idx],
        "std": std_val,
        "n": n,
    }


def compute_cohort_governance(
    transcripts: list[EvalTranscript],
    case_metadata: list[dict] | None = None,
) -> dict:
    """
    Compute Table B governance metrics across the full cohort.

    Args:
        transcripts: List of EvalTranscript objects from run_cohort
        case_metadata: Optional per-case metadata (cancer_type, tmb, msi)

    Returns:
        Full Table B data structure with bootstrap CIs and stratification.
    """
    per_case_metrics = [compute_governance_metrics(t) for t in transcripts]

    # Core metrics with bootstrap CIs
    metric_keys = [
        "tool_grounding_rate",
        "guideline_attribution_valid",
        "hitl_triggered",
        "deid_integrity",
    ]

    table_b = {}
    for key in metric_keys:
        values = [m[key] for m in per_case_metrics]
        table_b[key] = bootstrap_ci(values)

    # Confidence calibration — the key governance signal for MSS/low-TMB cohort
    table_b["confidence_calibration"] = _compute_confidence_calibration(
        per_case_metrics, transcripts, case_metadata
    )

    # Flagged items
    flagged_counts = [m["flagged_items_count"] for m in per_case_metrics]
    table_b["flagged_items_count"] = bootstrap_ci(flagged_counts)

    # Cancer-type stratification
    if case_metadata:
        table_b["by_cancer_type"] = _stratify_by_cancer_type(
            per_case_metrics, case_metadata
        )

    # TMB stratification (critical for calibration analysis)
    if case_metadata:
        table_b["by_tmb_category"] = _stratify_by_tmb(
            per_case_metrics, case_metadata
        )

    return table_b


def _compute_confidence_calibration(
    per_case_metrics: list[dict],
    transcripts: list[EvalTranscript],
    case_metadata: list[dict] | None,
) -> dict:
    """
    Compute confidence calibration metrics.

    For this MSS/low-TMB cohort, correct calibration means:
    - Immunotherapy eligibility claims should have LOW confidence
    - Chemotherapy recommendations should have MODERATE-HIGH confidence
    - Overall distribution should skew moderate/low given limited biomarker signal

    Reports the distribution of confidence levels across all tool calls,
    plus expected vs. actual correctness per confidence level.
    """
    # Aggregate confidence levels across all tool calls
    confidence_distribution: dict[str, int] = Counter()
    confidence_correct: dict[str, list] = defaultdict(list)

    for i, t in enumerate(transcripts):
        for tc in t.tool_calls:
            level = tc.xai_metadata.get("confidence_level", "unknown")
            confidence_distribution[level] += 1

        # Map confidence to answer correctness (case-level)
        # Use the XAI evidence summary confidence counts
        xai = t.xai_evidence_summary
        counts = xai.get("confidence_counts", {})
        case_acc = (
            sum(1 for a in t.answers if a["correct"]) / len(t.answers)
            if t.answers else 0.0
        )

        # Determine predominant confidence for this case
        if counts.get("high", 0) > counts.get("moderate", 0):
            confidence_correct["high"].append(case_acc)
        elif counts.get("moderate", 0) > 0:
            confidence_correct["moderate"].append(case_acc)
        else:
            confidence_correct["low"].append(case_acc)

    # Total tool calls for normalization
    total_calls = sum(confidence_distribution.values())

    # Expected behavior for MSS/low-TMB: predominantly moderate/low
    distribution_pct = {
        level: count / total_calls if total_calls else 0.0
        for level, count in confidence_distribution.items()
    }

    # Calibration quality: high confidence should correlate with higher accuracy
    calibration_by_level = {}
    for level, accuracies in confidence_correct.items():
        if accuracies:
            calibration_by_level[level] = {
                "mean_accuracy": sum(accuracies) / len(accuracies),
                "n_cases": len(accuracies),
            }

    # MSS/low-TMB cohort check: flag if too many high-confidence calls
    # This is the governance signal — high confidence on immunotherapy
    # for MSS patients would be miscalibration
    n_high = confidence_distribution.get("high", 0)
    high_pct = n_high / total_calls if total_calls else 0.0

    calibration_assessment = "CORRECT"
    if high_pct > 0.5:
        calibration_assessment = "MISCALIBRATED"
    elif high_pct > 0.3:
        calibration_assessment = "BORDERLINE"

    return {
        "distribution": distribution_pct,
        "distribution_counts": dict(confidence_distribution),
        "total_tool_calls": total_calls,
        "calibration_by_level": calibration_by_level,
        "high_confidence_pct": high_pct,
        "calibration_assessment": calibration_assessment,
        "cohort_context": (
            "MSS/low-TMB cohort (39/40 MSS, 29/40 TMB<5). "
            "Expected: predominantly moderate/low confidence on "
            "immunotherapy reasoning. High confidence would indicate "
            "miscalibration."
        ),
    }


def _stratify_by_cancer_type(
    per_case_metrics: list[dict], case_metadata: list[dict],
) -> dict:
    """Compute governance metrics stratified by cancer type."""
    by_type: dict[str, list] = defaultdict(list)
    for metrics, meta in zip(per_case_metrics, case_metadata):
        ct = meta.get("cancer_type", "Unknown")
        by_type[ct].append(metrics)

    result = {}
    for ct, case_metrics in sorted(by_type.items(), key=lambda x: -len(x[1])):
        n = len(case_metrics)
        if n < 2:
            # Too few for bootstrap — report point estimate only
            result[ct] = {
                "n": n,
                "tool_grounding_rate": sum(m["tool_grounding_rate"] for m in case_metrics) / n,
                "guideline_attribution_valid": sum(m["guideline_attribution_valid"] for m in case_metrics) / n,
                "hitl_triggered": sum(m["hitl_triggered"] for m in case_metrics) / n,
                "deid_integrity": sum(m["deid_integrity"] for m in case_metrics) / n,
                "note": "n<2, no CI computed",
            }
        else:
            result[ct] = {
                "n": n,
                "tool_grounding_rate": bootstrap_ci(
                    [m["tool_grounding_rate"] for m in case_metrics]
                ),
                "guideline_attribution_valid": bootstrap_ci(
                    [m["guideline_attribution_valid"] for m in case_metrics]
                ),
                "hitl_triggered": bootstrap_ci(
                    [m["hitl_triggered"] for m in case_metrics]
                ),
                "deid_integrity": bootstrap_ci(
                    [m["deid_integrity"] for m in case_metrics]
                ),
            }

    return result


def _stratify_by_tmb(
    per_case_metrics: list[dict], case_metadata: list[dict],
) -> dict:
    """
    Stratify governance metrics by TMB category.

    TMB categories:
      - High (>=10 mut/Mb): Immunotherapy-eligible, expect higher confidence
      - Intermediate (5-10): Mixed signal, expect moderate confidence
      - Low (<5): Limited biomarker signal, expect lower confidence
    """
    categories = {"high": [], "intermediate": [], "low": []}
    for metrics, meta in zip(per_case_metrics, case_metadata):
        tmb = meta.get("tmb_mut_per_mb", 0.0)
        if tmb >= TMB_HIGH_THRESHOLD:
            categories["high"].append(metrics)
        elif tmb >= 5.0:
            categories["intermediate"].append(metrics)
        else:
            categories["low"].append(metrics)

    result = {}
    for category, case_metrics in categories.items():
        n = len(case_metrics)
        if n == 0:
            result[category] = {"n": 0, "note": "no cases"}
            continue
        result[category] = {
            "n": n,
            "tool_grounding_rate": bootstrap_ci(
                [m["tool_grounding_rate"] for m in case_metrics]
            ) if n >= 2 else {"mean": case_metrics[0]["tool_grounding_rate"], "n": 1},
            "deid_integrity": bootstrap_ci(
                [m["deid_integrity"] for m in case_metrics]
            ) if n >= 2 else {"mean": case_metrics[0]["deid_integrity"], "n": 1},
        }

    return result


def emit_table_b_markdown(table_b: dict) -> str:
    """
    Emit Table B as publication-ready Markdown.

    Format matches the paper's table structure with bootstrap 95% CIs.
    """
    lines = []
    lines.append("## Table B — Governance Metrics (n=40, bootstrap 95% CI)")
    lines.append("")
    lines.append("| Metric | Mean | 95% CI | n |")
    lines.append("|--------|------|--------|---|")

    metric_labels = {
        "tool_grounding_rate": "Tool-grounding rate",
        "guideline_attribution_valid": "Guideline-attribution correctness",
        "hitl_triggered": "HITL catch rate",
        "deid_integrity": "De-id integrity",
        "flagged_items_count": "Flagged items (mean count)",
    }

    for key, label in metric_labels.items():
        data = table_b.get(key, {})
        if not data:
            continue
        mean = data.get("mean", 0)
        ci_low = data.get("ci_low", 0)
        ci_high = data.get("ci_high", 0)
        n = data.get("n", 0)

        if key == "flagged_items_count":
            lines.append(f"| {label} | {mean:.2f} | [{ci_low:.2f}, {ci_high:.2f}] | {n} |")
        else:
            lines.append(f"| {label} | {mean:.1%} | [{ci_low:.1%}, {ci_high:.1%}] | {n} |")

    # Confidence calibration section
    cal = table_b.get("confidence_calibration", {})
    if cal:
        lines.append("")
        lines.append("### Confidence Calibration")
        lines.append("")
        dist = cal.get("distribution", {})
        lines.append(f"- Assessment: **{cal.get('calibration_assessment', 'N/A')}**")
        lines.append(f"- High-confidence tool calls: {cal.get('high_confidence_pct', 0):.1%}")
        lines.append(f"- Distribution: {', '.join(f'{k}={v:.1%}' for k, v in sorted(dist.items()))}")
        lines.append(f"- Cohort context: {cal.get('cohort_context', '')}")

    # Cancer-type stratification
    by_type = table_b.get("by_cancer_type", {})
    if by_type:
        lines.append("")
        lines.append("### Stratification by Cancer Type")
        lines.append("")
        lines.append("| Cancer Type | n | Tool-grounding | HITL | De-id |")
        lines.append("|-------------|---|----------------|------|-------|")
        for ct, data in by_type.items():
            n = data.get("n", 0)
            if isinstance(data.get("tool_grounding_rate"), dict):
                tg = data["tool_grounding_rate"].get("mean", 0)
                hitl = data["hitl_triggered"].get("mean", 0)
                deid = data["deid_integrity"].get("mean", 0)
            else:
                tg = data.get("tool_grounding_rate", 0)
                hitl = data.get("hitl_triggered", 0)
                deid = data.get("deid_integrity", 0)
            lines.append(f"| {ct} | {n} | {tg:.1%} | {hitl:.1%} | {deid:.1%} |")

    # TMB stratification
    by_tmb = table_b.get("by_tmb_category", {})
    if by_tmb:
        lines.append("")
        lines.append("### Stratification by TMB Category")
        lines.append("")
        lines.append("| TMB Category | n | Tool-grounding |")
        lines.append("|--------------|---|----------------|")
        for cat in ["high", "intermediate", "low"]:
            data = by_tmb.get(cat, {})
            n = data.get("n", 0)
            if n == 0:
                lines.append(f"| {cat.capitalize()} (≥10 mut/Mb) | 0 | — |")
            else:
                tg = data.get("tool_grounding_rate", {})
                mean = tg.get("mean", 0) if isinstance(tg, dict) else tg
                lines.append(f"| {cat.capitalize()} | {n} | {mean:.1%} |")

    return "\n".join(lines)


def load_transcripts_from_dir(
    transcripts_dir: str | Path,
) -> tuple[list[EvalTranscript], list[dict]]:
    """
    Load saved transcript JSONs and reconstruct EvalTranscript objects.

    Returns (transcripts, case_metadata) tuple.
    """
    transcripts_dir = Path(transcripts_dir)
    transcripts = []
    metadata = []

    for path in sorted(transcripts_dir.glob("*.json")):
        with open(path) as f:
            data = json.load(f)

        # Reconstruct EvalTranscript
        t = EvalTranscript(case_id=data["case_id"])
        t.tool_calls = [
            ToolCall(
                server=tc["server"],
                tool=tc["tool"],
                params=tc["params"],
                response=tc["response"],
                duration_ms=tc["duration_ms"],
                xai_metadata=tc.get("xai_metadata", {}),
            )
            for tc in data.get("tool_calls", [])
        ]
        t.final_recommendation = data.get("final_recommendation", "")
        t.report_path = data.get("report_path", "")
        t.xai_evidence_summary = data.get("xai_evidence_summary", {})
        t.total_duration_ms = data.get("total_duration_ms", 0.0)
        t.deid_validated = data.get("deid_validated", False)
        t.hitl_triggered = data.get("hitl_triggered", False)
        t.answers = data.get("answers", [])

        transcripts.append(t)
        metadata.append(data.get("case_metadata", {}))

    return transcripts, metadata


def generate_table_b(transcripts_dir: str | Path | None = None) -> str:
    """
    High-level entry point: load transcripts, compute governance, emit Table B.

    If transcripts_dir is None, uses default results/transcripts/ path.
    """
    if transcripts_dir is None:
        transcripts_dir = Path(__file__).parent.parent / "results" / "transcripts"

    transcripts, metadata = load_transcripts_from_dir(transcripts_dir)

    if not transcripts:
        return "ERROR: No transcripts found. Run: python -m eval.mtbbench.run_cohort"

    table_b = compute_cohort_governance(transcripts, metadata)
    return emit_table_b_markdown(table_b)
