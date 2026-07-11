"""
Eval runner for MTBBench longitudinal track.

Protocol:
  The MTBBench Doctor-agent sends cases as a sequence of turns.
  Each turn may include new patient data (labs, imaging, progression notes).
  The platform must respond with a structured recommendation at each turn.
  The final recommendation is scored against the ground-truth expert answer.

This runner:
  1. Loads an MTBCase via case_adapter
  2. Drives our MCP servers in sequence (genomic -> neoantigen -> report)
  3. Captures every tool call and its response (the "transcript")
  4. Returns the transcript + final recommendation for scoring

Security:
  - DEIDENTIFY_DRY_RUN=true always
  - No real patient data processed
  - Reports retain DRAFT watermark

Cite: Jain et al., MTBBench, NeurIPS 2024, github.com/bunnelab/mtbbench
"""

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from eval.mtbbench.case_adapter import MTBCase, mtbcase_to_platform_context


@dataclass
class ToolCall:
    """Record of a single MCP tool invocation."""

    server: str
    tool: str
    params: dict
    response: Any
    duration_ms: float
    xai_metadata: dict = field(default_factory=dict)


@dataclass
class EvalTranscript:
    """Full transcript of one MTBBench case evaluation."""

    case_id: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    final_recommendation: str = ""
    report_path: str = ""
    xai_evidence_summary: dict = field(default_factory=dict)
    total_duration_ms: float = 0.0
    deid_validated: bool = False
    hitl_triggered: bool = False
    answers: list = field(default_factory=list)
    # Each: {question: str, predicted: str, ground_truth: str, correct: bool}


def _simulate_tool_call(
    server: str, tool: str, params: dict, dry_run: bool = True
) -> ToolCall:
    """
    Simulate an MCP tool call in DRY_RUN mode.

    In production (dry_run=False), this would use the MCP client to make
    real tool calls. For Milestone 1, we return synthetic DRY_RUN responses
    that match the expected response schema.
    """
    start = time.monotonic()

    if dry_run:
        response = {
            "status": "DRY_RUN",
            "message": f"Simulated {server}.{tool}",
            "data": _synthetic_response(server, tool, params),
            "xai_metadata": {
                "confidence_level": "medium",
                "confidence_note": "DRY_RUN mode — synthetic data",
                "key_drivers": ["simulated_input"],
                "guideline_version": "DRY_RUN",
                "evidence_grade": "simulated",
                "counterfactual": None,
            },
        }
    else:
        # TODO (Milestone 2): Real MCP client calls
        raise NotImplementedError(
            "Real MCP tool calls require MCP client setup. "
            "Use dry_run=True for Milestone 1."
        )

    duration_ms = (time.monotonic() - start) * 1000

    return ToolCall(
        server=server,
        tool=tool,
        params=params,
        response=response,
        duration_ms=duration_ms,
        xai_metadata=response.get("xai_metadata", {}),
    )


def _synthetic_response(server: str, tool: str, params: dict) -> dict:
    """Generate synthetic DRY_RUN response data matching server schemas."""
    if server == "mcp-genomic-results" and tool == "parse_somatic_variants":
        return {
            "variants": [
                {"gene": "KRAS", "aa_change": "G12D", "vaf": 0.35, "consequence": "missense"},
            ],
            "total_variants": 1,
        }
    elif server == "mcp-neoantigen" and tool == "predict_mhc1_binding":
        return {
            "neoantigens": [{"peptide": "KLVVVGADGV", "hla": "HLA-A*02:01", "ic50_nm": 45.2}],
            "strong_binders": 1,
        }
    elif server == "mcp-opentargets" and tool == "search_targets_by_disease":
        return {
            "targets": [{"gene": "KRAS", "score": 0.92, "drugs": ["sotorasib"]}],
        }
    elif server == "mcp-patient-report" and tool == "generate_patient_report":
        return {
            "report_path": "/tmp/eval_report_draft.pdf",
            "recommendations": ["Consider KRAS G12D-targeted therapy"],
            "evidence_strength_summary": {
                "high_confidence_count": 1,
                "medium_confidence_count": 1,
                "low_confidence_count": 0,
                "weakest_link": "Limited neoantigen data (DRY_RUN)",
                "overall_assessment": "Moderate evidence from genomic analysis",
                "confidence_counts": {"high": 1, "moderate": 1, "low": 0},
                "guideline_version": "NCCN Pancreatic 2024.1",
                "synthetic_data_items": ["All results are DRY_RUN simulated"],
                "action_required": [],
            },
        }
    elif server == "mcp-deidentify" and tool == "validate_deidentification":
        return {"passed": True, "phi_found": [], "validation_method": "DRY_RUN"}
    elif server == "mcp-patient-report" and tool == "approve_patient_report":
        return {"approved": True, "reviewer": "HITL_DRY_RUN", "gate_triggered": True}
    else:
        return {"message": f"No synthetic data defined for {server}.{tool}"}


def run_case(case: MTBCase, dry_run: bool = True) -> EvalTranscript:
    """
    Run one MTBBench case through the platform.

    Args:
        case: MTBCase from case_adapter
        dry_run: if True, use DRY_RUN mode (no real compute)

    Returns:
        EvalTranscript with full tool-call history and XAI summary
    """
    # Respect security constraints
    os.environ.setdefault("DEIDENTIFY_DRY_RUN", "true")
    os.environ.setdefault("CARDIOMETABOLIC_DRY_RUN", "true")

    transcript = EvalTranscript(case_id=case.case_id)
    start = time.monotonic()
    context = mtbcase_to_platform_context(case)

    # Step 1: Parse genomic data
    tc = _simulate_tool_call(
        "mcp-genomic-results",
        "parse_somatic_variants",
        {"variants": context["somatic_variants"], "patient_id": context["patient_id"]},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)

    # Step 2: Neoantigen analysis
    tc = _simulate_tool_call(
        "mcp-neoantigen",
        "predict_mhc1_binding",
        {"variants": context["somatic_variants"], "patient_id": context["patient_id"]},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)

    # Step 3: Open Targets drug lookup
    tc = _simulate_tool_call(
        "mcp-opentargets",
        "search_targets_by_disease",
        {"disease": context["cancer_type"], "patient_id": context["patient_id"]},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)

    # Step 4: Generate clinical report (captures XAI Evidence Summary)
    tc = _simulate_tool_call(
        "mcp-patient-report",
        "generate_patient_report",
        {"patient_id": context["patient_id"], "report_type": "clinical"},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)
    report_data = tc.response.get("data", {})
    transcript.report_path = report_data.get("report_path", "")
    transcript.xai_evidence_summary = report_data.get("evidence_strength_summary", {})

    # Step 5: De-id validation
    tc = _simulate_tool_call(
        "mcp-deidentify",
        "validate_deidentification",
        {"report_path": transcript.report_path},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)
    deid_result = tc.response.get("data", {})
    transcript.deid_validated = deid_result.get("passed", False)

    # Step 6: HITL gate
    tc = _simulate_tool_call(
        "mcp-patient-report",
        "approve_patient_report",
        {"report_path": transcript.report_path, "reviewer": "eval_harness"},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)
    hitl_result = tc.response.get("data", {})
    transcript.hitl_triggered = hitl_result.get("gate_triggered", False)

    # Step 7: Generate answers for each MTBBench question
    # In DRY_RUN, produce synthetic answers based on available data
    for q in case.questions:
        predicted = _generate_answer(q, context, dry_run=dry_run)
        correct = _check_answer(predicted, q["answer"])
        transcript.answers.append({
            "question": q["question"],
            "predicted": predicted,
            "ground_truth": q["answer"],
            "correct": correct,
        })

    # Set final recommendation from report
    transcript.final_recommendation = "; ".join(
        report_data.get("recommendations", ["No recommendation (DRY_RUN)"])
    )

    transcript.total_duration_ms = (time.monotonic() - start) * 1000
    return transcript


def _generate_answer(question: dict, context: dict, dry_run: bool = True) -> str:
    """
    Generate a predicted answer for an MTBBench question.

    In DRY_RUN, returns a synthetic answer. In production (Milestone 2+),
    this would use Claude to synthesize an answer from tool call results.
    """
    if dry_run:
        # DRY_RUN: always predict "A) Yes" as a baseline
        # (Real implementation will use Claude reasoning over tool outputs)
        return "A) Yes"
    raise NotImplementedError("Real answer generation requires Claude API (Milestone 2)")


def _check_answer(predicted: str, ground_truth: str) -> bool:
    """Check if predicted answer matches ground truth (letter comparison)."""
    pred_letter = predicted.strip()[0].upper() if predicted.strip() else ""
    gt_letter = ground_truth.strip()[0].upper() if ground_truth.strip() else ""
    return pred_letter == gt_letter


def extract_recommendation(transcript: EvalTranscript) -> str:
    """Extract the final treatment recommendation from the transcript."""
    return transcript.final_recommendation
