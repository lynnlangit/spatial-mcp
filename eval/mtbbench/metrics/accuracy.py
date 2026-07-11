"""
Table A: Accuracy metrics for MTBBench longitudinal track.

Metrics:
- Treatment recommendation match (%)
- Biomarker identification F1
- Guideline citation accuracy

Framing: "competitive/parity with SOTA" — do NOT claim to beat MTBBench numbers.
"""

from typing import Any


def compute_accuracy_metrics(transcript: Any) -> dict:
    """
    Compute Table A accuracy metrics for one case.

    Args:
        transcript: EvalTranscript from eval_runner

    Returns:
        dict with accuracy metrics for this case
    """
    if not transcript.answers:
        return {
            "question_accuracy": 0.0,
            "total_questions": 0,
            "correct_count": 0,
            "by_type": {},
        }

    correct = sum(1 for a in transcript.answers if a["correct"])
    total = len(transcript.answers)

    # Break down by question type
    by_type: dict[str, dict] = {}
    for a in transcript.answers:
        qtype = a.get("type", "unknown") if "type" in a else _infer_type(a["question"])
        if qtype not in by_type:
            by_type[qtype] = {"correct": 0, "total": 0}
        by_type[qtype]["total"] += 1
        if a["correct"]:
            by_type[qtype]["correct"] += 1

    for qtype in by_type:
        t = by_type[qtype]
        t["accuracy"] = t["correct"] / t["total"] if t["total"] > 0 else 0.0

    return {
        "question_accuracy": correct / total if total > 0 else 0.0,
        "total_questions": total,
        "correct_count": correct,
        "by_type": by_type,
    }


def aggregate_accuracy_metrics(all_transcripts: list) -> dict:
    """
    Aggregate Table A metrics across all MTBBench cases.

    Returns means and per-type breakdowns for the paper table.
    """
    per_case = [compute_accuracy_metrics(t) for t in all_transcripts]

    total_correct = sum(c["correct_count"] for c in per_case)
    total_questions = sum(c["total_questions"] for c in per_case)

    # Aggregate by question type
    all_types: dict[str, dict] = {}
    for case_metrics in per_case:
        for qtype, data in case_metrics["by_type"].items():
            if qtype not in all_types:
                all_types[qtype] = {"correct": 0, "total": 0}
            all_types[qtype]["correct"] += data["correct"]
            all_types[qtype]["total"] += data["total"]

    for qtype in all_types:
        t = all_types[qtype]
        t["accuracy"] = t["correct"] / t["total"] if t["total"] > 0 else 0.0

    return {
        "overall_accuracy": total_correct / total_questions if total_questions > 0 else 0.0,
        "total_questions": total_questions,
        "total_correct": total_correct,
        "n_cases": len(all_transcripts),
        "by_type": all_types,
    }


def _infer_type(question: str) -> str:
    """Infer question type from question text."""
    q = question.lower()
    if "recurrence" in q:
        return "recurrence"
    elif "alive" in q:
        return "survival"
    elif "progress" in q:
        return "progression"
    return "unknown"
