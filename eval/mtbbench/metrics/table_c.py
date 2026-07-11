"""
Table C: Ablation study — governance component contribution analysis.

Computes per-condition accuracy and governance metrics across the full
cohort, with bootstrap 95% CIs and paired statistical tests comparing
each ablation against the full_platform reference.

Conditions (M4):
  - full_platform:     All components active (reference)
  - no_hitl:           HITL gate removed
  - no_xai:            XAI metadata / evidence summary removed
  - no_deid:           De-identification check removed
  - base_llm_no_tools: ALL MCP tool calls removed

Paired test:
  Uses the sign test (non-parametric, no normality assumption) on
  per-case metric deltas. For binary metrics (0/1), this is equivalent
  to McNemar's test without continuity correction.

  In DRY_RUN mode, no_hitl/no_xai/no_deid have identical accuracy to
  full_platform (same coin-flip answers), so accuracy p-values are 1.0.
  Governance metrics differ by construction. In LIVE mode, base_llm_no_tools
  produces different accuracy (Claude with vs. without tool context).

Bootstrap methodology:
  - B=10000 resamples, seed=42 for reproducibility
  - Percentile-based 95% CI (2.5th and 97.5th percentiles)
  - Per-case accuracy and governance scores as unit of resampling

Cite: Jain et al., MTBBench, NeurIPS 2024, github.com/bunnelab/mtbbench
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

from eval.mtbbench.eval_runner import EvalTranscript, ToolCall
from eval.mtbbench.metrics.ablations import TABLE_C_CONDITIONS
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics
from eval.mtbbench.metrics.governance import compute_governance_metrics
from eval.mtbbench.metrics.table_b import bootstrap_ci


# ── Paired sign test ────────────────────────────────────────────────────

def _sign_test(deltas: list[float]) -> dict:
    """
    Two-sided sign test on a list of paired deltas.

    Counts how many deltas are positive vs. negative (ignoring zeros),
    then computes a p-value under the binomial(n, 0.5) null hypothesis.

    Returns:
        dict with n_positive, n_negative, n_tied, n_effective, p_value
    """
    n_pos = sum(1 for d in deltas if d > 0)
    n_neg = sum(1 for d in deltas if d < 0)
    n_tied = sum(1 for d in deltas if d == 0)
    n_eff = n_pos + n_neg  # effective sample size (ties excluded)

    if n_eff == 0:
        p_value = 1.0  # no differences observed
    else:
        # Two-sided binomial test: P(X >= max(n_pos, n_neg)) * 2
        k = max(n_pos, n_neg)
        # Compute using exact binomial CDF (no scipy dependency)
        p_value = 2.0 * _binomial_tail(n_eff, k)
        p_value = min(p_value, 1.0)  # clip at 1.0

    return {
        "n_positive": n_pos,
        "n_negative": n_neg,
        "n_tied": n_tied,
        "n_effective": n_eff,
        "p_value": p_value,
    }


def _binomial_tail(n: int, k: int) -> float:
    """P(X >= k) for X ~ Binomial(n, 0.5), computed exactly."""
    if k > n:
        return 0.0
    # Sum C(n, i) * 0.5^n for i = k..n
    total = 0.0
    for i in range(k, n + 1):
        total += _comb(n, i)
    return total * (0.5 ** n)


def _comb(n: int, k: int) -> int:
    """Exact binomial coefficient C(n, k)."""
    if k < 0 or k > n:
        return 0
    if k == 0 or k == n:
        return 1
    k = min(k, n - k)
    result = 1
    for i in range(k):
        result = result * (n - i) // (i + 1)
    return result


# ── Per-case result storage ─────────────────────────────────────────────

def case_result_to_dict(
    case_id: str,
    condition_transcripts: dict[str, EvalTranscript],
    case_metadata: dict | None = None,
) -> dict:
    """
    Serialize per-case ablation results to a JSON-safe dict.

    Stores per-condition accuracy and governance metrics (not full
    transcripts) to keep files small while supporting paired tests.
    """
    result: dict[str, Any] = {
        "case_id": case_id,
        "case_metadata": case_metadata or {},
        "conditions": {},
    }

    for condition, transcript in condition_transcripts.items():
        acc = compute_accuracy_metrics(transcript)
        gov = compute_governance_metrics(transcript)
        result["conditions"][condition] = {
            "accuracy": acc["question_accuracy"],
            "total_questions": acc["total_questions"],
            "correct_count": acc["correct_count"],
            "tool_grounding_rate": gov["tool_grounding_rate"],
            "guideline_attribution_valid": gov["guideline_attribution_valid"],
            "hitl_triggered": gov["hitl_triggered"],
            "deid_integrity": gov["deid_integrity"],
            "flagged_items_count": gov["flagged_items_count"],
            "n_tool_calls": len(transcript.tool_calls),
            "answers": [
                {
                    "question": a["question"],
                    "predicted": a["predicted"],
                    "ground_truth": a["ground_truth"],
                    "correct": a["correct"],
                }
                for a in transcript.answers
            ],
        }

    return result


# ── Table C aggregation ─────────────────────────────────────────────────

def compute_table_c(
    ablation_results_dir: str | Path | None = None,
) -> dict:
    """
    Compute Table C: ablation study with bootstrap CIs and paired tests.

    Loads per-case ablation result JSONs from ablation_results_dir,
    aggregates across the cohort.

    Returns dict with:
      - per_condition: {condition -> {accuracy_ci, governance_metrics_ci}}
      - paired_tests: {condition -> {metric -> sign_test_result}}
      - summary: cohort-level stats
    """
    if ablation_results_dir is None:
        ablation_results_dir = (
            Path(__file__).parent.parent / "results" / "ablations"
        )
    ablation_results_dir = Path(ablation_results_dir)

    # Load all per-case results
    case_results = []
    for path in sorted(ablation_results_dir.glob("*.json")):
        with open(path) as f:
            case_results.append(json.load(f))

    if not case_results:
        return {"error": "No ablation results found. Run: python -m eval.mtbbench.run_ablations"}

    n_cases = len(case_results)

    # ── Per-condition aggregation with bootstrap CIs ────────────────
    per_condition: dict[str, dict] = {}
    metrics_keys = [
        "accuracy", "tool_grounding_rate", "guideline_attribution_valid",
        "hitl_triggered", "deid_integrity", "flagged_items_count",
    ]

    for condition in TABLE_C_CONDITIONS:
        cond_data: dict[str, Any] = {}
        for metric in metrics_keys:
            values = [
                cr["conditions"][condition][metric]
                for cr in case_results
                if condition in cr["conditions"]
            ]
            if values:
                cond_data[metric] = bootstrap_ci(values)
            else:
                cond_data[metric] = {"mean": 0.0, "ci_low": 0.0, "ci_high": 0.0, "n": 0}
        per_condition[condition] = cond_data

    # ── Paired sign tests: each ablation vs. full_platform ──────────
    paired_tests: dict[str, dict] = {}
    for condition in TABLE_C_CONDITIONS[1:]:  # skip full_platform
        condition_tests: dict[str, Any] = {}
        for metric in metrics_keys:
            deltas = []
            for cr in case_results:
                full_val = cr["conditions"]["full_platform"][metric]
                abl_val = cr["conditions"].get(condition, {}).get(metric, 0.0)
                deltas.append(full_val - abl_val)
            condition_tests[metric] = _sign_test(deltas)
            # Also store mean delta
            condition_tests[metric]["mean_delta"] = (
                sum(deltas) / len(deltas) if deltas else 0.0
            )
        paired_tests[condition] = condition_tests

    # ── Summary ─────────────────────────────────────────────────────
    summary = {
        "n_cases": n_cases,
        "n_conditions": len(TABLE_C_CONDITIONS),
        "conditions": TABLE_C_CONDITIONS,
    }

    return {
        "per_condition": per_condition,
        "paired_tests": paired_tests,
        "summary": summary,
    }


def emit_table_c_markdown(table_c: dict) -> str:
    """Emit Table C as publication-ready Markdown."""
    if "error" in table_c:
        return f"ERROR: {table_c['error']}"

    lines = []
    summary = table_c.get("summary", {})
    n = summary.get("n_cases", 0)

    lines.append(f"## Table C — Ablation Study (n={n}, bootstrap 95% CI)")
    lines.append("")

    # Main table
    lines.append(
        "| Condition | Accuracy | Tool-ground | Guideline | "
        "HITL | De-id | Flagged |"
    )
    lines.append(
        "|-----------|----------|-------------|-----------|"
        "------|-------|---------|"
    )

    condition_labels = {
        "full_platform": "Full platform",
        "no_hitl": "− HITL gate",
        "no_xai": "− XAI layer",
        "no_deid": "− De-id check",
        "base_llm_no_tools": "Base LLM (no tools)",
    }

    per_cond = table_c.get("per_condition", {})
    for condition in TABLE_C_CONDITIONS:
        label = condition_labels.get(condition, condition)
        data = per_cond.get(condition, {})

        acc = data.get("accuracy", {})
        tg = data.get("tool_grounding_rate", {})
        ga = data.get("guideline_attribution_valid", {})
        hitl = data.get("hitl_triggered", {})
        deid = data.get("deid_integrity", {})
        flagged = data.get("flagged_items_count", {})

        lines.append(
            f"| {label} "
            f"| {acc.get('mean', 0):.1%} [{acc.get('ci_low', 0):.1%}, {acc.get('ci_high', 0):.1%}] "
            f"| {tg.get('mean', 0):.0%} "
            f"| {ga.get('mean', 0):.0%} "
            f"| {hitl.get('mean', 0):.1%} [{hitl.get('ci_low', 0):.1%}, {hitl.get('ci_high', 0):.1%}] "
            f"| {deid.get('mean', 0):.0%} "
            f"| {flagged.get('mean', 0):.2f} [{flagged.get('ci_low', 0):.2f}, {flagged.get('ci_high', 0):.2f}] |"
        )

    # Paired test results
    paired = table_c.get("paired_tests", {})
    if paired:
        lines.append("")
        lines.append("### Paired Sign Tests (vs. Full Platform)")
        lines.append("")
        lines.append("| Condition | Metric | Δ Mean | p-value | n+ / n− / tied |")
        lines.append("|-----------|--------|--------|---------|----------------|")

        # Only show metrics where there's an actual delta
        for condition in TABLE_C_CONDITIONS[1:]:
            label = condition_labels.get(condition, condition)
            tests = paired.get(condition, {})
            for metric, result in tests.items():
                delta = result.get("mean_delta", 0)
                if abs(delta) < 1e-10:
                    continue  # skip zero deltas
                p = result.get("p_value", 1.0)
                n_pos = result.get("n_positive", 0)
                n_neg = result.get("n_negative", 0)
                n_tied = result.get("n_tied", 0)

                metric_label = metric.replace("_", " ").title()
                sig = " *" if p < 0.05 else ""

                if metric == "flagged_items_count":
                    lines.append(
                        f"| {label} | {metric_label} | {delta:+.2f} "
                        f"| {p:.4f}{sig} | {n_pos}/{n_neg}/{n_tied} |"
                    )
                else:
                    lines.append(
                        f"| {label} | {metric_label} | {delta:+.1%} "
                        f"| {p:.4f}{sig} | {n_pos}/{n_neg}/{n_tied} |"
                    )

    # Note
    lines.append("")
    lines.append(
        "*Note: In DRY_RUN mode, accuracy is identical across governance ablations "
        "(same deterministic coin-flip). Governance metric deltas are by construction. "
        "In LIVE mode, base_llm_no_tools accuracy diverges (Claude without tool context).*"
    )

    return "\n".join(lines)


def generate_table_c(
    ablation_results_dir: str | Path | None = None,
) -> str:
    """High-level entry point: compute and emit Table C."""
    table_c = compute_table_c(ablation_results_dir)
    return emit_table_c_markdown(table_c)
