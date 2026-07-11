"""
Run all 40 MTBBench cases through the eval pipeline and save transcripts.

Usage:
    python -m eval.mtbbench.run_cohort [--live]

Flags:
    --live  Use real MCP servers + Claude API (requires ANTHROPIC_API_KEY)
            Default is DRY_RUN mode (synthetic responses).

Output:
    eval/mtbbench/results/transcripts/  — one JSON per patient
    eval/mtbbench/results/cohort_summary.json — aggregate stats
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from eval.mtbbench.case_adapter import load_mtbbench_cohort
from eval.mtbbench.eval_runner import run_case, EvalTranscript, ToolCall


DATA_PATH = Path(__file__).parent / "data" / "questions_msk_bench.json"
RESULTS_DIR = Path(__file__).parent / "results"
TRANSCRIPTS_DIR = RESULTS_DIR / "transcripts"


def transcript_to_dict(t: EvalTranscript) -> dict:
    """Serialize an EvalTranscript to a JSON-safe dict."""
    return {
        "case_id": t.case_id,
        "tool_calls": [
            {
                "server": tc.server,
                "tool": tc.tool,
                "params": tc.params,
                "response": tc.response,
                "duration_ms": tc.duration_ms,
                "xai_metadata": tc.xai_metadata,
            }
            for tc in t.tool_calls
        ],
        "final_recommendation": t.final_recommendation,
        "report_path": t.report_path,
        "xai_evidence_summary": t.xai_evidence_summary,
        "total_duration_ms": t.total_duration_ms,
        "deid_validated": t.deid_validated,
        "hitl_triggered": t.hitl_triggered,
        "answers": t.answers,
    }


def run_cohort(dry_run: bool = True) -> list[dict]:
    """Run all 40 cases and return serialized transcripts."""
    if not DATA_PATH.exists():
        print(f"ERROR: {DATA_PATH} not found.")
        print("Run: python -m eval.mtbbench.scripts.fetch_msk_chord")
        sys.exit(1)

    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    cases = load_mtbbench_cohort(str(DATA_PATH))
    print(f"Loaded {len(cases)} cases from {DATA_PATH.name}")
    print(f"Mode: {'LIVE' if not dry_run else 'DRY_RUN'}")
    print()

    all_transcripts = []
    total_start = time.monotonic()

    for i, case in enumerate(cases, 1):
        case_start = time.monotonic()
        transcript = run_case(case, dry_run=dry_run)
        elapsed = (time.monotonic() - case_start) * 1000

        td = transcript_to_dict(transcript)
        td["case_metadata"] = {
            "cancer_type": case.cancer_type,
            "tmb_mut_per_mb": case.tmb_mut_per_mb,
            "msi_score": case.msi_score,
            "msi_type": case.msi_type,
            "n_questions": len(case.questions),
            "n_variants": len(case.somatic_variants),
            "n_cna": len(case.cnv_calls),
            "stage": case.stage,
        }
        all_transcripts.append(td)

        # Save individual transcript
        out_path = TRANSCRIPTS_DIR / f"{case.case_id}.json"
        with open(out_path, "w") as f:
            json.dump(td, f, indent=2, default=str)

        # Progress
        n_correct = sum(1 for a in transcript.answers if a["correct"])
        n_total = len(transcript.answers)
        acc = n_correct / n_total if n_total else 0
        print(
            f"  [{i:2d}/40] {case.case_id:<12} "
            f"{case.cancer_type:<30} "
            f"Q={n_total:2d}  Acc={acc:.0%}  "
            f"TMB={case.tmb_mut_per_mb:5.1f}  "
            f"MSI={case.msi_type:<12} "
            f"{elapsed:.0f}ms"
        )

    total_elapsed = (time.monotonic() - total_start) * 1000

    # Summary
    total_questions = sum(len(t["answers"]) for t in all_transcripts)
    total_correct = sum(
        sum(1 for a in t["answers"] if a["correct"]) for t in all_transcripts
    )
    overall_acc = total_correct / total_questions if total_questions else 0

    summary = {
        "n_cases": len(all_transcripts),
        "n_questions": total_questions,
        "n_correct": total_correct,
        "overall_accuracy": overall_acc,
        "total_elapsed_ms": total_elapsed,
        "mode": "DRY_RUN" if dry_run else "LIVE",
        "cancer_type_breakdown": {},
    }

    # Cancer-type breakdown
    from collections import Counter
    type_counts = Counter()
    type_correct = Counter()
    type_questions = Counter()
    for t in all_transcripts:
        ct = t["case_metadata"]["cancer_type"]
        n_q = len(t["answers"])
        n_c = sum(1 for a in t["answers"] if a["correct"])
        type_counts[ct] += 1
        type_questions[ct] += n_q
        type_correct[ct] += n_c

    for ct in sorted(type_counts, key=lambda x: -type_counts[x]):
        summary["cancer_type_breakdown"][ct] = {
            "n_patients": type_counts[ct],
            "n_questions": type_questions[ct],
            "n_correct": type_correct[ct],
            "accuracy": type_correct[ct] / type_questions[ct] if type_questions[ct] else 0,
        }

    summary_path = RESULTS_DIR / "cohort_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    print()
    print(f"{'='*70}")
    print(f"COHORT SUMMARY ({summary['mode']})")
    print(f"{'='*70}")
    print(f"  Cases: {summary['n_cases']}")
    print(f"  Questions: {summary['n_questions']}")
    print(f"  Overall accuracy: {overall_acc:.1%}")
    print(f"  Total time: {total_elapsed:.0f}ms")
    print()
    print(f"  Cancer Type Breakdown:")
    print(f"  {'Type':<32} {'Patients':<10} {'Accuracy':<10}")
    print(f"  {'-'*52}")
    for ct, data in summary["cancer_type_breakdown"].items():
        print(f"  {ct:<32} {data['n_patients']:<10} {data['accuracy']:.1%}")
    print()
    print(f"  Transcripts saved: {TRANSCRIPTS_DIR}/")
    print(f"  Summary saved: {summary_path}")

    return all_transcripts


def main():
    dry_run = "--live" not in sys.argv
    run_cohort(dry_run=dry_run)


if __name__ == "__main__":
    main()
