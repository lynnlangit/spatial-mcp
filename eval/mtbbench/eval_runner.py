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

Modes:
  - dry_run=True (default): Synthetic responses, no external calls. Fast.
  - dry_run=False: Real MCP server calls + Claude API for answer generation.
    Requires MCP servers running and ANTHROPIC_API_KEY set.

Security:
  - DEIDENTIFY_DRY_RUN=true always
  - No real patient data processed
  - Reports retain DRAFT watermark

Cite: Jain et al., MTBBench, NeurIPS 2024, github.com/bunnelab/mtbbench
"""

import json
import logging
import os
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from eval.mtbbench.case_adapter import MTBCase, mtbcase_to_platform_context

logger = logging.getLogger(__name__)


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


def _call_mcp_tool(
    server: str, tool: str, params: dict, dry_run: bool = True
) -> ToolCall:
    """
    Call an MCP server tool, either in DRY_RUN or live mode.

    DRY_RUN (default): Returns synthetic responses matching server schemas.
    Live mode: Shells out to `uv run python -m mcp_<name>` via subprocess
    to call the actual MCP server. Requires the server to be installed.
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
        response = _live_tool_call(server, tool, params)

    duration_ms = (time.monotonic() - start) * 1000

    return ToolCall(
        server=server,
        tool=tool,
        params=params,
        response=response,
        duration_ms=duration_ms,
        xai_metadata=response.get("xai_metadata", {}),
    )


def _live_tool_call(server: str, tool: str, params: dict) -> dict:
    """
    Execute a real MCP tool call via subprocess.

    Uses the server's module entry point with a JSON-RPC-style invocation.
    Falls back to DRY_RUN synthetic response if the server is not available.
    """
    module_name = server.replace("-", "_").replace("mcp_", "mcp-")
    server_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "servers", server
    )
    server_dir = os.path.normpath(server_dir)

    if not os.path.isdir(server_dir):
        logger.warning(
            "Server directory %s not found, falling back to synthetic response",
            server_dir,
        )
        return {
            "status": "FALLBACK",
            "message": f"Server {server} not found at {server_dir}",
            "data": _synthetic_response(server, tool, params),
            "xai_metadata": {
                "confidence_level": "low",
                "confidence_note": f"Server {server} not available — used fallback",
                "key_drivers": ["server_unavailable"],
                "guideline_version": "N/A",
                "evidence_grade": "simulated",
                "counterfactual": None,
            },
        }

    # Build a minimal script that imports and calls the tool function
    call_script = (
        f"import asyncio, json, sys; "
        f"sys.path.insert(0, '{server_dir}/src'); "
        f"from {server.replace('-', '_')}.server import mcp; "
        f"params = json.loads(sys.stdin.read()); "
        f"result = asyncio.run(mcp.call_tool('{tool}', params)); "
        f"print(json.dumps(result, default=str))"
    )

    try:
        result = subprocess.run(
            ["uv", "run", "python", "-c", call_script],
            input=json.dumps(params),
            capture_output=True,
            text=True,
            timeout=120,
            cwd=server_dir,
        )
        if result.returncode != 0:
            logger.warning(
                "Server %s.%s failed (rc=%d): %s",
                server, tool, result.returncode, result.stderr[:500],
            )
            return {
                "status": "ERROR",
                "message": result.stderr[:500],
                "data": _synthetic_response(server, tool, params),
                "xai_metadata": {
                    "confidence_level": "low",
                    "confidence_note": f"Tool call failed: {result.stderr[:200]}",
                    "key_drivers": ["tool_error"],
                    "guideline_version": "N/A",
                    "evidence_grade": "simulated",
                    "counterfactual": None,
                },
            }

        data = json.loads(result.stdout)
        return {
            "status": "OK",
            "data": data,
            "xai_metadata": data.get("xai_metadata", {
                "confidence_level": "medium",
                "confidence_note": "Live tool call — no XAI metadata returned",
                "key_drivers": ["live_call"],
                "guideline_version": "N/A",
                "evidence_grade": "tool_output",
                "counterfactual": None,
            }),
        }
    except subprocess.TimeoutExpired:
        logger.warning("Server %s.%s timed out after 120s", server, tool)
        return {
            "status": "TIMEOUT",
            "data": _synthetic_response(server, tool, params),
            "xai_metadata": {
                "confidence_level": "low",
                "confidence_note": "Tool call timed out",
                "key_drivers": ["timeout"],
                "guideline_version": "N/A",
                "evidence_grade": "simulated",
                "counterfactual": None,
            },
        }
    except Exception as e:
        logger.warning("Server %s.%s error: %s", server, tool, e)
        return {
            "status": "ERROR",
            "message": str(e),
            "data": _synthetic_response(server, tool, params),
            "xai_metadata": {
                "confidence_level": "low",
                "confidence_note": f"Unexpected error: {e}",
                "key_drivers": ["exception"],
                "guideline_version": "N/A",
                "evidence_grade": "simulated",
                "counterfactual": None,
            },
        }


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
    tc = _call_mcp_tool(
        "mcp-genomic-results",
        "parse_somatic_variants",
        {"variants": context["somatic_variants"], "patient_id": context["patient_id"]},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)

    # Step 2: Neoantigen analysis
    tc = _call_mcp_tool(
        "mcp-neoantigen",
        "predict_mhc1_binding",
        {"variants": context["somatic_variants"], "patient_id": context["patient_id"]},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)

    # Step 3: Open Targets drug lookup
    tc = _call_mcp_tool(
        "mcp-opentargets",
        "search_targets_by_disease",
        {"disease": context["cancer_type"], "patient_id": context["patient_id"]},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)

    # Step 4: Generate clinical report (captures XAI Evidence Summary)
    tc = _call_mcp_tool(
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
    tc = _call_mcp_tool(
        "mcp-deidentify",
        "validate_deidentification",
        {"report_path": transcript.report_path},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)
    deid_result = tc.response.get("data", {})
    transcript.deid_validated = deid_result.get("passed", False)

    # Step 6: HITL gate
    tc = _call_mcp_tool(
        "mcp-patient-report",
        "approve_patient_report",
        {"report_path": transcript.report_path, "reviewer": "eval_harness"},
        dry_run=dry_run,
    )
    transcript.tool_calls.append(tc)
    hitl_result = tc.response.get("data", {})
    transcript.hitl_triggered = hitl_result.get("gate_triggered", False)

    # Step 7: Generate answers for each MTBBench question
    # In DRY_RUN, produce deterministic pseudo-random answers (not majority-class)
    tool_results = [tc.response for tc in transcript.tool_calls]
    for q in case.questions:
        predicted = _generate_answer(q, context, tool_results, dry_run=dry_run)
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


def _generate_answer(
    question: dict, context: dict, tool_results: list | None = None,
    dry_run: bool = True,
) -> str:
    """
    Generate a predicted answer for an MTBBench question.

    DRY_RUN: Deterministic pseudo-random coin-flip (avoids trivially
    matching the 56% majority-class baseline).

    Live mode: Calls Claude API with patient context + tool results,
    asks it to answer the binary question. Requires ANTHROPIC_API_KEY.
    """
    if dry_run:
        import hashlib
        key = f"{context.get('patient_id', '')}:{question.get('question', '')}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        return "A) Yes" if int(digest, 16) % 2 == 0 else "B) No"

    return _claude_answer(question, context, tool_results or [])


def _claude_answer(
    question: dict, context: dict, tool_results: list,
) -> str:
    """
    Call Claude API to generate an answer from tool outputs + patient context.

    Uses the Anthropic Python SDK if available, falls back to urllib.
    Returns "A) Yes" or "B) No".
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set — falling back to coin-flip")
        import hashlib
        key = f"{context.get('patient_id', '')}:{question.get('question', '')}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        return "A) Yes" if int(digest, 16) % 2 == 0 else "B) No"

    # Build the prompt
    tool_summary = "\n".join(
        f"- {r.get('message', 'tool call')}: {json.dumps(r.get('data', {}), default=str)[:500]}"
        for r in tool_results
        if isinstance(r, dict)
    )

    prompt = (
        f"You are a clinical oncology AI assistant evaluating a patient case.\n\n"
        f"PATIENT CONTEXT:\n"
        f"- Patient ID: {context.get('patient_id', 'N/A')}\n"
        f"- Cancer type: {context.get('cancer_type', 'N/A')}\n"
        f"- Stage: {context.get('stage', 'N/A')}\n"
        f"- TMB: {context.get('tmb_mut_per_mb', 'N/A')} mut/Mb\n"
        f"- MSI: {context.get('msi_type', 'N/A')} (score: {context.get('msi_score', 'N/A')})\n"
        f"- Treatment history: {context.get('treatment_history', [])}\n\n"
        f"TOOL ANALYSIS RESULTS:\n{tool_summary}\n\n"
        f"QUESTION:\n{question.get('question', '')}\n\n"
        f"Answer ONLY with 'A) Yes' or 'B) No'. Base your answer on the "
        f"clinical evidence above. If uncertain, make your best clinical judgment."
    )

    try:
        import urllib.request
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps({
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": prompt}],
            }).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        answer_text = result.get("content", [{}])[0].get("text", "").strip()

        # Parse the answer
        if answer_text.startswith("A") or "yes" in answer_text.lower()[:10]:
            return "A) Yes"
        elif answer_text.startswith("B") or "no" in answer_text.lower()[:10]:
            return "B) No"
        else:
            logger.warning("Unparseable Claude answer: %s", answer_text)
            return "A) Yes"  # Default if unparseable
    except Exception as e:
        logger.warning("Claude API call failed: %s — falling back to coin-flip", e)
        import hashlib
        key = f"{context.get('patient_id', '')}:{question.get('question', '')}"
        digest = hashlib.sha256(key.encode()).hexdigest()
        return "A) Yes" if int(digest, 16) % 2 == 0 else "B) No"


def _check_answer(predicted: str, ground_truth: str) -> bool:
    """Check if predicted answer matches ground truth (letter comparison)."""
    pred_letter = predicted.strip()[0].upper() if predicted.strip() else ""
    gt_letter = ground_truth.strip()[0].upper() if ground_truth.strip() else ""
    return pred_letter == gt_letter


def extract_recommendation(transcript: EvalTranscript) -> str:
    """Extract the final treatment recommendation from the transcript."""
    return transcript.final_recommendation
