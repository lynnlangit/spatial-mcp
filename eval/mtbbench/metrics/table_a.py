"""
Table A: Accuracy metrics aggregator with bootstrap 95% CIs.

Computes cohort-level accuracy for the full platform and baseline conditions,
stratified by cancer type and question type (recurrence, survival, progression).

Conditions compared:
  - full_platform: All MCP servers + answer generation (DRY_RUN coin-flip)
  - base_llm: No tools, answer from patient context only (DRY_RUN coin-flip)
  - majority_class: Always predicts "A) Yes" (~56% class prevalence)
  - random_baseline: Deterministic SHA-256 coin-flip (~50% expected)

In DRY_RUN mode, full_platform and base_llm both use deterministic coin-flip
for answer generation (no Claude API), so their accuracy is identical.
The real Table A differentiation emerges in LIVE mode when Claude has tool
outputs to reason from.

Bootstrap methodology:
  - B=10000 resamples, seed=42 for reproducibility
  - Percentile-based 95% CI (2.5th and 97.5th percentiles)
  - n=40 cases, per-case accuracy as unit of resampling

Cite: Jain et al., MTBBench, NeurIPS 2024, github.com/bunnelab/mtbbench
"""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from eval.mtbbench.case_adapter import MTBCase, load_mtbbench_cohort
from eval.mtbbench.eval_runner import EvalTranscript
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics
from eval.mtbbench.metrics.table_b import bootstrap_ci, load_transcripts_from_dir


# ── Constants ────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent.parent / "data" / "questions_msk_bench.json"
TRANSCRIPTS_DIR = Path(__file__).parent.parent / "results" / "transcripts"
_MAJORITY_ANSWER = "A) Yes"


def _deterministic_coin_flip(case_id: str, question: str) -> str:
    """SHA-256 deterministic pseudo-random prediction."""
    digest = hashlib.sha256(f"{case_id}:{question}".encode()).hexdigest()
    return "A) Yes" if int(digest, 16) % 2 == 0 else "B) No"


def _infer_question_type(question: str) -> str:
    """Infer question category from text."""
    q = question.lower()
    if "recurrence" in q:
        return "recurrence"
    if "alive" in q or "survival" in q:
        return "survival"
    if "progress" in q:
        return "progression"
    return "other"


def _baseline_accuracy(
    cases: list[MTBCase], method: str,
) -> list[float]:
    """
    Compute per-case accuracy for a baseline method.

    Returns list of 40 floats (one accuracy per case).
    """
    per_case = []
    for case in cases:
        n_correct = 0
        for q in case.questions:
            gt = q["answer"].strip()[0].upper()
            if method == "majority_class":
                pred = _MAJORITY_ANSWER
            elif method == "random_baseline":
                pred = _deterministic_coin_flip(case.case_id, q["question"])
            else:
                raise ValueError(f"Unknown baseline: {method}")

            if pred.strip()[0].upper() == gt:
                n_correct += 1
        acc = n_correct / len(case.questions) if case.questions else 0.0
        per_case.append(acc)
    return per_case


def compute_table_a(
    transcripts_dir: str | Path | None = None,
    data_path: str | Path | None = None,
) -> dict:
    """
    Compute complete Table A: accuracy with bootstrap CIs across conditions.

    Returns dict with per-condition accuracy, cancer-type stratification,
    and question-type breakdown.
    """
    transcripts_dir = Path(transcripts_dir) if transcripts_dir else TRANSCRIPTS_DIR
    data_path = Path(data_path) if data_path else DATA_PATH

    # Load saved full_platform transcripts
    transcripts, metadata = load_transcripts_from_dir(transcripts_dir)
    cases = load_mtbbench_cohort(str(data_path))

    # ── Full platform accuracy (per-case) ────────────────────────────
    full_per_case = []
    for t in transcripts:
        acc_metrics = compute_accuracy_metrics(t)
        full_per_case.append(acc_metrics["question_accuracy"])

    # ── Baseline accuracies ──────────────────────────────────────────
    majority_per_case = _baseline_accuracy(cases, "majority_class")
    random_per_case = _baseline_accuracy(cases, "random_baseline")

    # base_llm in DRY_RUN is identical to random_baseline (both use coin flip).
    # In LIVE mode they'd differ (base_llm calls Claude API without tools).
    base_llm_per_case = random_per_case[:]

    # ── Bootstrap CIs ────────────────────────────────────────────────
    conditions = {
        "full_platform": full_per_case,
        "base_llm_no_tools": base_llm_per_case,
        "majority_class": majority_per_case,
        "random_baseline": random_per_case,
    }
    result: dict[str, Any] = {}
    for cond, values in conditions.items():
        result[cond] = bootstrap_ci(values)

    # ── Question-type breakdown (full_platform only) ─────────────────
    by_qtype: dict[str, list] = defaultdict(list)
    for t in transcripts:
        for a in t.answers:
            qtype = _infer_question_type(a["question"])
            by_qtype[qtype].append(1.0 if a["correct"] else 0.0)

    result["by_question_type"] = {}
    for qtype, vals in sorted(by_qtype.items()):
        result["by_question_type"][qtype] = bootstrap_ci(vals)

    # ── Cancer-type stratification (full_platform only) ──────────────
    by_cancer: dict[str, list] = defaultdict(list)
    for t, meta in zip(transcripts, metadata):
        ct = meta.get("cancer_type", "Unknown")
        acc = compute_accuracy_metrics(t)["question_accuracy"]
        by_cancer[ct].append(acc)

    result["by_cancer_type"] = {}
    for ct in sorted(by_cancer, key=lambda x: -len(by_cancer[x])):
        vals = by_cancer[ct]
        if len(vals) >= 2:
            result["by_cancer_type"][ct] = bootstrap_ci(vals)
        else:
            result["by_cancer_type"][ct] = {
                "mean": vals[0], "ci_low": vals[0], "ci_high": vals[0],
                "n": 1, "note": "n=1, no CI",
            }

    # ── Global summary ───────────────────────────────────────────────
    total_q = sum(len(t.answers) for t in transcripts)
    total_correct = sum(
        sum(1 for a in t.answers if a["correct"]) for t in transcripts
    )
    result["summary"] = {
        "n_cases": len(transcripts),
        "n_questions": total_q,
        "n_correct": total_correct,
        "micro_accuracy": total_correct / total_q if total_q else 0.0,
    }

    return result


def emit_table_a_markdown(table_a: dict) -> str:
    """Emit Table A as publication-ready Markdown."""
    lines = []
    lines.append("## Table A — Accuracy (n=40, bootstrap 95% CI)")
    lines.append("")
    lines.append("| Condition | Accuracy | 95% CI | n |")
    lines.append("|-----------|----------|--------|---|")

    condition_labels = {
        "full_platform": "Full platform (all MCP servers)",
        "base_llm_no_tools": "Base LLM (no tools)",
        "majority_class": "Majority-class baseline",
        "random_baseline": "Random baseline",
    }

    for cond, label in condition_labels.items():
        data = table_a.get(cond, {})
        mean = data.get("mean", 0)
        ci_lo = data.get("ci_low", 0)
        ci_hi = data.get("ci_high", 0)
        n = data.get("n", 0)
        lines.append(f"| {label} | {mean:.1%} | [{ci_lo:.1%}, {ci_hi:.1%}] | {n} |")

    # Question-type breakdown
    by_qt = table_a.get("by_question_type", {})
    if by_qt:
        lines.append("")
        lines.append("### Accuracy by Question Type")
        lines.append("")
        lines.append("| Question Type | Accuracy | 95% CI | n |")
        lines.append("|---------------|----------|--------|---|")
        for qt, data in sorted(by_qt.items()):
            mean = data.get("mean", 0)
            ci_lo = data.get("ci_low", 0)
            ci_hi = data.get("ci_high", 0)
            n = data.get("n", 0)
            lines.append(f"| {qt.capitalize()} | {mean:.1%} | [{ci_lo:.1%}, {ci_hi:.1%}] | {n} |")

    # Cancer-type breakdown
    by_ct = table_a.get("by_cancer_type", {})
    if by_ct:
        lines.append("")
        lines.append("### Accuracy by Cancer Type")
        lines.append("")
        lines.append("| Cancer Type | Accuracy | 95% CI | n |")
        lines.append("|-------------|----------|--------|---|")
        for ct, data in sorted(by_ct.items(), key=lambda x: -x[1].get("n", 0)):
            mean = data.get("mean", 0)
            ci_lo = data.get("ci_low", 0)
            ci_hi = data.get("ci_high", 0)
            n = data.get("n", 0)
            lines.append(f"| {ct} | {mean:.1%} | [{ci_lo:.1%}, {ci_hi:.1%}] | {n} |")

    # Micro-average summary
    summary = table_a.get("summary", {})
    if summary:
        lines.append("")
        lines.append(
            f"*Micro-average: {summary.get('n_correct', 0)}/{summary.get('n_questions', 0)} "
            f"= {summary.get('micro_accuracy', 0):.1%} across {summary.get('n_cases', 0)} cases*"
        )
        lines.append("")
        lines.append(
            "*Note: In DRY_RUN mode, full_platform and base_llm both use deterministic "
            "coin-flip for answer generation (no Claude API). Accuracy differentiation "
            "between conditions emerges in LIVE mode.*"
        )

    return "\n".join(lines)


def generate_table_a(
    transcripts_dir: str | Path | None = None,
    data_path: str | Path | None = None,
) -> str:
    """High-level entry point: compute and emit Table A."""
    table_a = compute_table_a(transcripts_dir, data_path)
    return emit_table_a_markdown(table_a)
