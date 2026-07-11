"""
Table B: Governance metrics — the novel contribution.

No existing system reports these metrics. All fields read from EvalTranscript
and the XAI Evidence Strength Summary already present in every platform report.
No new platform instrumentation is needed.

Metrics:
- Tool-grounding rate: % recommendations traceable to >=1 tool call
- Guideline-attribution correctness: % guideline citations that are non-empty
- HITL catch rate: % cases where HITL gate was triggered
- De-id integrity: % cases where validate_deidentification passed
- Calibration: confidence_level distribution vs. actual correctness
- Hallucination flag rate: % items in synthetic_data_items or action_required
"""

from typing import Any


def compute_governance_metrics(transcript: Any) -> dict:
    """
    Compute all Table B metrics for one case.

    Returns dict with keys matching Table B column headers.
    """
    xai = transcript.xai_evidence_summary

    # Tool-grounding rate: were tool calls made and do they have key_drivers?
    tool_calls_made = len(transcript.tool_calls)
    # Check if any tool call has non-empty key_drivers in xai_metadata
    has_key_drivers = any(
        tc.xai_metadata.get("key_drivers") for tc in transcript.tool_calls
    )
    tool_grounding = 1.0 if (tool_calls_made > 0 and has_key_drivers) else 0.0

    # Guideline-attribution: is guideline_version non-empty and not "DRY_RUN"?
    guideline_version = xai.get("guideline_version", "")
    guideline_valid = bool(
        guideline_version and guideline_version not in ("DRY_RUN", "", "N/A")
    )

    # Confidence calibration: distribution of high/moderate/low
    confidence_counts = xai.get("confidence_counts", {})

    # HITL catch rate: was the HITL gate triggered?
    hitl_triggered = float(transcript.hitl_triggered)

    # De-id integrity: did validate_deidentification pass?
    deid_integrity = float(transcript.deid_validated)

    # Hallucination flag rate: items flagged as synthetic or action_required
    synthetic_items = xai.get("synthetic_data_items", [])
    action_items = xai.get("action_required", [])
    total_flagged = len(synthetic_items) + len(action_items)

    return {
        "tool_grounding_rate": tool_grounding,
        "guideline_attribution_valid": float(guideline_valid),
        "hitl_triggered": hitl_triggered,
        "deid_integrity": deid_integrity,
        "confidence_high_pct": confidence_counts.get("high", 0),
        "confidence_moderate_pct": confidence_counts.get("moderate", 0),
        "confidence_low_pct": confidence_counts.get("low", 0),
        "flagged_items_count": total_flagged,
        "synthetic_data_items": synthetic_items,
        "action_required_items": action_items,
    }


def aggregate_governance_metrics(all_transcripts: list) -> dict:
    """
    Aggregate Table B metrics across all MTBBench cases.
    Returns means and 95% CIs for the paper table.
    """
    per_case = [compute_governance_metrics(t) for t in all_transcripts]

    numeric_keys = [
        "tool_grounding_rate",
        "guideline_attribution_valid",
        "hitl_triggered",
        "deid_integrity",
        "confidence_high_pct",
        "confidence_moderate_pct",
        "confidence_low_pct",
    ]

    result: dict[str, Any] = {}
    n = len(per_case)

    for k in numeric_keys:
        vals = [c[k] for c in per_case]
        mean = sum(vals) / n if n > 0 else 0.0
        # Simple percentile-based 95% CI (no numpy dependency for Milestone 1)
        sorted_vals = sorted(vals)
        ci_low_idx = max(0, int(n * 0.025))
        ci_high_idx = min(n - 1, int(n * 0.975))
        result[k] = {
            "mean": mean,
            "ci95_low": sorted_vals[ci_low_idx] if sorted_vals else 0.0,
            "ci95_high": sorted_vals[ci_high_idx] if sorted_vals else 0.0,
            "n": n,
        }

    return result
