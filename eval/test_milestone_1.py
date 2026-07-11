"""
Milestone 1 smoke test: one MTBBench case runs end-to-end.
Confirms the harness wiring, not accuracy.

Run with:
    uv run pytest eval/test_milestone_1.py -v -m integration
"""

import pytest

from eval.mtbbench.case_adapter import load_mtbbench_case, mtbcase_to_platform_context
from eval.mtbbench.eval_runner import run_case
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics
from eval.mtbbench.metrics.governance import compute_governance_metrics


SAMPLE_CASE_PATH = "eval/mtbbench/fixtures/mtb_case_001.json"


@pytest.mark.integration
def test_case_adapter_loads():
    """Case adapter loads the fixture without exception."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    assert case.case_id == "P-SYNTH-001"
    assert case.cancer_type == "Pancreatic Adenocarcinoma"
    assert len(case.questions) == 2
    assert case.stage == "III"
    assert case.tmb_mut_per_mb == pytest.approx(0.978, rel=0.01)


@pytest.mark.integration
def test_platform_context_conversion():
    """MTBCase converts to platform context dict with expected fields."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    context = mtbcase_to_platform_context(case)
    assert context["patient_id"] == "MTB-P-SYNTH-001"
    assert context["cancer_type"] == "Pancreatic Adenocarcinoma"
    assert context["source"] == "MTBBench-MSK-CHORD"


@pytest.mark.integration
def test_one_case_end_to_end():
    """One case must complete without exception in DRY_RUN mode."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)

    assert transcript.case_id == case.case_id
    assert len(transcript.tool_calls) > 0, "No tool calls recorded"
    assert transcript.total_duration_ms > 0


@pytest.mark.integration
def test_tool_calls_have_xai_metadata():
    """Every tool call must return xai_metadata in DRY_RUN mode."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)

    for tc in transcript.tool_calls:
        assert tc.xai_metadata, f"Missing xai_metadata for {tc.server}.{tc.tool}"
        assert tc.xai_metadata["confidence_level"] in ("high", "medium", "low")
        assert 1 <= len(tc.xai_metadata["key_drivers"]) <= 3


@pytest.mark.integration
def test_governance_metrics_populated():
    """All Table B fields must be present after one run."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)
    metrics = compute_governance_metrics(transcript)

    required_keys = [
        "tool_grounding_rate",
        "guideline_attribution_valid",
        "hitl_triggered",
        "deid_integrity",
        "confidence_high_pct",
        "confidence_moderate_pct",
        "confidence_low_pct",
    ]
    for k in required_keys:
        assert k in metrics, f"Missing governance metric: {k}"


@pytest.mark.integration
def test_accuracy_metrics_populated():
    """Table A accuracy metrics must be computable after one run."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)
    metrics = compute_accuracy_metrics(transcript)

    assert metrics["total_questions"] == 2
    assert 0.0 <= metrics["question_accuracy"] <= 1.0


@pytest.mark.integration
def test_deid_dry_run_respected():
    """DEIDENTIFY_DRY_RUN must be true — no real de-id writes should occur."""
    import os

    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)

    # In dry_run=True, de-id should still be called but not write real output
    assert transcript.deid_validated is True
    assert os.environ.get("DEIDENTIFY_DRY_RUN") == "true"


@pytest.mark.integration
def test_hitl_gate_triggered():
    """HITL gate should be triggered in full platform run."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)
    assert transcript.hitl_triggered is True


@pytest.mark.integration
def test_answers_generated_for_all_questions():
    """Each MTBBench question gets a predicted answer."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)
    assert len(transcript.answers) == len(case.questions)
    for a in transcript.answers:
        assert "predicted" in a
        assert "ground_truth" in a
        assert "correct" in a
