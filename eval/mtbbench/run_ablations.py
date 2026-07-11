"""
Run M4 ablation study: all 40 MTBBench cases under all 5 Table C conditions.

Usage:
    python -m eval.mtbbench.run_ablations [--live]

Flags:
    --live  Use real MCP servers + Claude API (requires ANTHROPIC_API_KEY)
            Default is DRY_RUN mode (synthetic responses).

Output:
    eval/mtbbench/results/ablations/  — one JSON per patient (all conditions)
    eval/mtbbench/results/transcripts/ — full_platform transcripts (for Table A)
    eval/mtbbench/results/ablation_summary.json — aggregate stats

Design:
    Runs full_platform ONCE per case, derives no_hitl/no_xai/no_deid from
    deep copies (they only modify governance fields). Only base_llm_no_tools
    runs a separate answer-generation path.

    Same 40 cases, same order as run_cohort. Same random seed (SHA-256
    deterministic coin-flip) ensures reproducibility.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from eval.mtbbench.case_adapter import load_mtbbench_cohort
from eval.mtbbench.metrics.ablations import TABLE_C_CONDITIONS, run_table_c_case
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics
from eval.mtbbench.metrics.governance import compute_governance_metrics
from eval.mtbbench.metrics.table_c import case_result_to_dict
from eval.mtbbench.run_cohort import transcript_to_dict


DATA_PATH = Path(__file__).parent / "data" / "questions_msk_bench.json"
RESULTS_DIR = Path(__file__).parent / "results"
ABLATIONS_DIR = RESULTS_DIR / "ablations"
TRANSCRIPTS_DIR = RESULTS_DIR / "transcripts"


def run_ablation_cohort(dry_run: bool = True) -> list[dict]:
    """Run all 40 cases under all Table C conditions and save per-case results."""
    if not DATA_PATH.exists():
        print(f"ERROR: {DATA_PATH} not found.")
        print("Run: python -m eval.mtbbench.scripts.fetch_msk_chord")
        sys.exit(1)

    ABLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    cases = load_mtbbench_cohort(str(DATA_PATH))
    print(f"Loaded {len(cases)} cases from {DATA_PATH.name}")
    print(f"Mode: {'LIVE' if not dry_run else 'DRY_RUN'}")
    print(f"Conditions: {', '.join(TABLE_C_CONDITIONS)}")
    print()

    all_results = []
    total_start = time.monotonic()

    for i, case in enumerate(cases, 1):
        case_start = time.monotonic()

        # Run all 5 conditions (full_platform once, 3 derived, 1 separate)
        condition_transcripts = run_table_c_case(case, dry_run=dry_run)

        # Build case metadata
        case_metadata = {
            "cancer_type": case.cancer_type,
            "tmb_mut_per_mb": case.tmb_mut_per_mb,
            "msi_score": case.msi_score,
            "msi_type": case.msi_type,
            "n_questions": len(case.questions),
            "stage": case.stage,
        }

        # Serialize per-case results
        case_result = case_result_to_dict(
            case.case_id, condition_transcripts, case_metadata,
        )
        all_results.append(case_result)

        # Save individual case result (ablations)
        out_path = ABLATIONS_DIR / f"{case.case_id}.json"
        with open(out_path, "w") as f:
            json.dump(case_result, f, indent=2, default=str)

        # Also save full_platform transcript for Table A computation
        full_td = transcript_to_dict(condition_transcripts["full_platform"])
        full_td["case_metadata"] = case_metadata
        t_path = TRANSCRIPTS_DIR / f"{case.case_id}.json"
        with open(t_path, "w") as f:
            json.dump(full_td, f, indent=2, default=str)

        elapsed = (time.monotonic() - case_start) * 1000

        # Progress line: show accuracy for full_platform and base_llm
        full_acc = case_result["conditions"]["full_platform"]["accuracy"]
        base_acc = case_result["conditions"]["base_llm_no_tools"]["accuracy"]
        print(
            f"  [{i:2d}/40] {case.case_id:<12} "
            f"{case.cancer_type:<30} "
            f"Full={full_acc:.0%}  Base={base_acc:.0%}  "
            f"TMB={case.tmb_mut_per_mb:5.1f}  "
            f"{elapsed:.0f}ms"
        )

    total_elapsed = (time.monotonic() - total_start) * 1000

    # Aggregate summary
    summary = _build_summary(all_results, dry_run, total_elapsed)
    summary_path = RESULTS_DIR / "ablation_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    _print_summary(summary, total_elapsed)

    return all_results


def _build_summary(
    all_results: list[dict], dry_run: bool, total_elapsed: float,
) -> dict:
    """Build cohort-level ablation summary."""
    summary = {
        "n_cases": len(all_results),
        "mode": "DRY_RUN" if dry_run else "LIVE",
        "total_elapsed_ms": total_elapsed,
        "conditions": {},
    }

    for condition in TABLE_C_CONDITIONS:
        accuracies = [
            r["conditions"][condition]["accuracy"]
            for r in all_results
        ]
        tool_grounding = [
            r["conditions"][condition]["tool_grounding_rate"]
            for r in all_results
        ]
        hitl = [
            r["conditions"][condition]["hitl_triggered"]
            for r in all_results
        ]
        deid = [
            r["conditions"][condition]["deid_integrity"]
            for r in all_results
        ]

        n = len(accuracies)
        summary["conditions"][condition] = {
            "mean_accuracy": sum(accuracies) / n if n else 0,
            "mean_tool_grounding": sum(tool_grounding) / n if n else 0,
            "mean_hitl": sum(hitl) / n if n else 0,
            "mean_deid": sum(deid) / n if n else 0,
        }

    return summary


def _print_summary(summary: dict, total_elapsed: float) -> None:
    """Print cohort ablation summary to stdout."""
    print()
    print(f"{'=' * 75}")
    print(f"ABLATION SUMMARY ({summary['mode']})")
    print(f"{'=' * 75}")
    print(f"  Cases: {summary['n_cases']}")
    print(f"  Time: {total_elapsed:.0f}ms")
    print()
    print(
        f"  {'Condition':<22} {'Accuracy':>10} {'Tool-grnd':>10} "
        f"{'HITL':>10} {'De-id':>10}"
    )
    print(f"  {'-' * 62}")

    for condition in TABLE_C_CONDITIONS:
        data = summary["conditions"].get(condition, {})
        print(
            f"  {condition:<22} "
            f"{data.get('mean_accuracy', 0):>9.1%} "
            f"{data.get('mean_tool_grounding', 0):>9.1%} "
            f"{data.get('mean_hitl', 0):>9.1%} "
            f"{data.get('mean_deid', 0):>9.1%}"
        )

    print()
    print(f"  Results saved: {ABLATIONS_DIR}/")
    print(f"  Summary saved: {RESULTS_DIR / 'ablation_summary.json'}")


def main():
    dry_run = "--live" not in sys.argv
    run_ablation_cohort(dry_run=dry_run)


if __name__ == "__main__":
    main()
