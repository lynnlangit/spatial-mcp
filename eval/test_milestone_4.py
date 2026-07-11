"""
Milestone 4 tests: Table C ablation study structure and correctness.

Tests verify:
  - TABLE_C_CONDITIONS has 5 items
  - run_table_c_case runs efficiently (full_platform once, derives 3 ablations)
  - Governance deltas are correct (HITL→0 for no_hitl, de-id→0 for no_deid, etc.)
  - Accuracy is identical across governance ablations in DRY_RUN
  - base_llm_no_tools has no tool calls
  - Per-case results can be serialized and loaded
  - Paired sign test produces valid p-values
  - Table C Markdown emitter works

Run with:
    uv run pytest eval/test_milestone_4.py -v -m integration
"""

import json
import tempfile
from pathlib import Path

import pytest

from eval.mtbbench.case_adapter import load_mtbbench_case
from eval.mtbbench.metrics.ablations import (
    ABLATION_CONDITIONS,
    TABLE_C_CONDITIONS,
    run_ablation,
    run_table_c_case,
)
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics
from eval.mtbbench.metrics.governance import compute_governance_metrics
from eval.mtbbench.metrics.table_c import (
    _sign_test,
    case_result_to_dict,
    compute_table_c,
    emit_table_c_markdown,
)


SAMPLE_CASE_PATH = "eval/mtbbench/fixtures/mtb_case_001.json"
ABLATIONS_DIR = Path("eval/mtbbench/results/ablations")


# ── Structure tests ─────────────────────────────────────────────────────

@pytest.mark.integration
def test_table_c_conditions_has_5_items():
    """TABLE_C_CONDITIONS must have exactly 5 conditions."""
    assert len(TABLE_C_CONDITIONS) == 5
    assert TABLE_C_CONDITIONS[0] == "full_platform"
    assert "no_hitl" in TABLE_C_CONDITIONS
    assert "no_xai" in TABLE_C_CONDITIONS
    assert "no_deid" in TABLE_C_CONDITIONS
    assert "base_llm_no_tools" in TABLE_C_CONDITIONS


@pytest.mark.integration
def test_ablation_conditions_backward_compat():
    """Original ABLATION_CONDITIONS still has 7 items (M2 backward compat)."""
    assert len(ABLATION_CONDITIONS) == 7
    assert "majority_class" in ABLATION_CONDITIONS
    assert "random_baseline" in ABLATION_CONDITIONS


# ── Single-case ablation tests ──────────────────────────────────────────

@pytest.mark.integration
def test_run_table_c_case_returns_all_conditions():
    """run_table_c_case must return transcripts for all 5 conditions."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)
    assert set(results.keys()) == set(TABLE_C_CONDITIONS)


@pytest.mark.integration
def test_no_hitl_removes_hitl():
    """no_hitl must set hitl_triggered=False and remove approve_patient_report."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)

    full = results["full_platform"]
    no_hitl = results["no_hitl"]

    # HITL flag must be False
    assert no_hitl.hitl_triggered is False

    # approve_patient_report tool call must be removed
    hitl_calls = [tc for tc in no_hitl.tool_calls if tc.tool == "approve_patient_report"]
    assert len(hitl_calls) == 0

    # Other tool calls should still be present
    assert len(no_hitl.tool_calls) == len(full.tool_calls) - 1


@pytest.mark.integration
def test_no_xai_clears_metadata():
    """no_xai must clear xai_evidence_summary and all tool xai_metadata."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)

    no_xai = results["no_xai"]

    # Evidence summary must be empty
    assert no_xai.xai_evidence_summary == {}

    # All tool calls must have empty xai_metadata
    for tc in no_xai.tool_calls:
        assert tc.xai_metadata == {}


@pytest.mark.integration
def test_no_deid_removes_validation():
    """no_deid must set deid_validated=False and remove validate_deidentification."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)

    full = results["full_platform"]
    no_deid = results["no_deid"]

    # De-id flag must be False
    assert no_deid.deid_validated is False

    # validate_deidentification tool call must be removed
    deid_calls = [tc for tc in no_deid.tool_calls if tc.tool == "validate_deidentification"]
    assert len(deid_calls) == 0

    # Other tool calls should still be present
    assert len(no_deid.tool_calls) == len(full.tool_calls) - 1


@pytest.mark.integration
def test_base_llm_has_no_tool_calls():
    """base_llm_no_tools must have zero tool calls."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)

    base = results["base_llm_no_tools"]
    assert len(base.tool_calls) == 0


@pytest.mark.integration
def test_base_llm_has_answers():
    """base_llm_no_tools must produce answers for all questions."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)

    base = results["base_llm_no_tools"]
    assert len(base.answers) == len(case.questions)
    for a in base.answers:
        assert a["predicted"] in ("A) Yes", "B) No")
        assert "correct" in a


@pytest.mark.integration
def test_governance_ablations_preserve_answers():
    """no_hitl, no_xai, no_deid must have identical answers to full_platform."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)

    full_answers = [a["predicted"] for a in results["full_platform"].answers]

    for condition in ["no_hitl", "no_xai", "no_deid"]:
        ablation_answers = [a["predicted"] for a in results[condition].answers]
        assert ablation_answers == full_answers, (
            f"{condition} changed answers (should be identical in DRY_RUN)"
        )


@pytest.mark.integration
def test_governance_deltas_are_correct():
    """Each governance ablation must zero out exactly one governance metric."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    results = run_table_c_case(case, dry_run=True)

    full_gov = compute_governance_metrics(results["full_platform"])

    # no_hitl: HITL → 0
    no_hitl_gov = compute_governance_metrics(results["no_hitl"])
    assert no_hitl_gov["hitl_triggered"] == 0.0
    assert no_hitl_gov["tool_grounding_rate"] == full_gov["tool_grounding_rate"]
    assert no_hitl_gov["deid_integrity"] == full_gov["deid_integrity"]

    # no_deid: de-id → 0
    no_deid_gov = compute_governance_metrics(results["no_deid"])
    assert no_deid_gov["deid_integrity"] == 0.0
    assert no_deid_gov["tool_grounding_rate"] == full_gov["tool_grounding_rate"]

    # no_xai: tool-grounding → 0 (key_drivers cleared)
    no_xai_gov = compute_governance_metrics(results["no_xai"])
    assert no_xai_gov["tool_grounding_rate"] == 0.0
    assert no_xai_gov["guideline_attribution_valid"] == 0.0

    # base_llm: everything → 0
    base_gov = compute_governance_metrics(results["base_llm_no_tools"])
    assert base_gov["tool_grounding_rate"] == 0.0
    assert base_gov["hitl_triggered"] == 0.0
    assert base_gov["deid_integrity"] == 0.0


# ── Per-case result serialization ───────────────────────────────────────

@pytest.mark.integration
def test_case_result_serialization():
    """Per-case results must be JSON-serializable and contain all conditions."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcripts = run_table_c_case(case, dry_run=True)

    result = case_result_to_dict(case.case_id, transcripts, {"cancer_type": "Test"})

    # Must be JSON-serializable
    json_str = json.dumps(result, default=str)
    loaded = json.loads(json_str)

    assert loaded["case_id"] == case.case_id
    assert set(loaded["conditions"].keys()) == set(TABLE_C_CONDITIONS)

    # Each condition must have accuracy and governance fields
    for condition in TABLE_C_CONDITIONS:
        cond_data = loaded["conditions"][condition]
        assert "accuracy" in cond_data
        assert "tool_grounding_rate" in cond_data
        assert "hitl_triggered" in cond_data
        assert "deid_integrity" in cond_data
        assert "answers" in cond_data
        assert len(cond_data["answers"]) == len(case.questions)


# ── Paired sign test ────────────────────────────────────────────────────

@pytest.mark.integration
def test_sign_test_all_zeros():
    """All-zero deltas → p=1.0 (no differences)."""
    result = _sign_test([0.0] * 40)
    assert result["p_value"] == 1.0
    assert result["n_tied"] == 40
    assert result["n_effective"] == 0


@pytest.mark.integration
def test_sign_test_all_positive():
    """All-positive deltas → p ≈ 0 (strong signal)."""
    result = _sign_test([1.0] * 20)
    assert result["p_value"] < 0.001
    assert result["n_positive"] == 20
    assert result["n_negative"] == 0


@pytest.mark.integration
def test_sign_test_balanced():
    """Equal positive and negative → p ≈ 1.0."""
    result = _sign_test([1.0, -1.0] * 10)
    assert result["p_value"] > 0.5
    assert result["n_positive"] == 10
    assert result["n_negative"] == 10


@pytest.mark.integration
def test_sign_test_valid_p_range():
    """p-value must be in [0, 1]."""
    for deltas in [[1.0], [-1.0, 1.0, 0.5], [0.0, 0.0], [0.1] * 5]:
        result = _sign_test(deltas)
        assert 0.0 <= result["p_value"] <= 1.0


# ── Table C aggregation (requires saved results) ───────────────────────

@pytest.mark.integration
def test_table_c_from_single_case():
    """Table C computation works with a single case saved to temp dir."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcripts = run_table_c_case(case, dry_run=True)
    result = case_result_to_dict(case.case_id, transcripts)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Save one case result
        path = Path(tmpdir) / f"{case.case_id}.json"
        with open(path, "w") as f:
            json.dump(result, f, default=str)

        # Compute Table C from it
        table_c = compute_table_c(tmpdir)

    assert "per_condition" in table_c
    assert "paired_tests" in table_c
    assert "summary" in table_c
    assert table_c["summary"]["n_cases"] == 1
    assert table_c["summary"]["n_conditions"] == 5

    # All conditions must be present
    for condition in TABLE_C_CONDITIONS:
        assert condition in table_c["per_condition"]


@pytest.mark.integration
def test_table_c_markdown_emitter():
    """Table C Markdown emitter produces valid output."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcripts = run_table_c_case(case, dry_run=True)
    result = case_result_to_dict(case.case_id, transcripts)

    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / f"{case.case_id}.json"
        with open(path, "w") as f:
            json.dump(result, f, default=str)

        table_c = compute_table_c(tmpdir)

    md = emit_table_c_markdown(table_c)
    assert "## Table C" in md
    assert "Ablation Study" in md
    assert "Full platform" in md
    assert "HITL gate" in md
    assert "XAI layer" in md
    assert "De-id check" in md
    assert "Base LLM" in md
    assert "Paired Sign Tests" in md


# ── Full cohort tests (require run_ablations output) ────────────────────

@pytest.mark.integration
@pytest.mark.skipif(not ABLATIONS_DIR.exists(), reason="Run run_ablations first")
def test_ablation_results_40_cases():
    """Ablation results directory must contain 40 case files."""
    files = list(ABLATIONS_DIR.glob("*.json"))
    assert len(files) == 40


@pytest.mark.integration
@pytest.mark.skipif(not ABLATIONS_DIR.exists(), reason="Run run_ablations first")
def test_table_c_full_cohort():
    """Table C from full cohort must have valid structure."""
    table_c = compute_table_c(ABLATIONS_DIR)

    assert table_c["summary"]["n_cases"] == 40
    assert table_c["summary"]["n_conditions"] == 5

    # Full platform accuracy should match Table A (53.3% in DRY_RUN)
    full_acc = table_c["per_condition"]["full_platform"]["accuracy"]
    assert 0.40 <= full_acc["mean"] <= 0.70

    # Governance ablation accuracy should equal full_platform in DRY_RUN
    for condition in ["no_hitl", "no_xai", "no_deid"]:
        abl_acc = table_c["per_condition"][condition]["accuracy"]
        assert abs(abl_acc["mean"] - full_acc["mean"]) < 1e-10, (
            f"{condition} accuracy differs from full_platform in DRY_RUN"
        )


@pytest.mark.integration
@pytest.mark.skipif(not ABLATIONS_DIR.exists(), reason="Run run_ablations first")
def test_table_c_governance_deltas_cohort():
    """Governance deltas must be non-zero for the correct metrics."""
    table_c = compute_table_c(ABLATIONS_DIR)
    paired = table_c["paired_tests"]

    # no_hitl: HITL delta should be significant (3/40 cases trigger HITL)
    hitl_delta = paired["no_hitl"]["hitl_triggered"]["mean_delta"]
    assert hitl_delta > 0, "no_hitl should reduce HITL metric"

    # no_deid: de-id delta should be 1.0 (all cases have de-id)
    deid_delta = paired["no_deid"]["deid_integrity"]["mean_delta"]
    assert abs(deid_delta - 1.0) < 1e-10, "no_deid should reduce de-id by 100%"

    # no_xai: tool_grounding delta should be 1.0
    tg_delta = paired["no_xai"]["tool_grounding_rate"]["mean_delta"]
    assert abs(tg_delta - 1.0) < 1e-10, "no_xai should reduce tool-grounding by 100%"


@pytest.mark.integration
@pytest.mark.skipif(not ABLATIONS_DIR.exists(), reason="Run run_ablations first")
def test_table_c_markdown_full_cohort():
    """Full cohort Table C Markdown must be complete."""
    md = emit_table_c_markdown(compute_table_c(ABLATIONS_DIR))
    assert "n=40" in md
    assert "Full platform" in md
    assert "Base LLM" in md
    assert "DRY_RUN" in md
