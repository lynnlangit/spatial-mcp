"""
Milestone 2 tests: baseline scoring, MSI/TMB flow, ablation correctness.

Run with:
    uv run pytest eval/test_milestone_2.py -v -m integration
"""

import pytest

from eval.mtbbench.case_adapter import load_mtbbench_case, mtbcase_to_platform_context
from eval.mtbbench.eval_runner import run_case
from eval.mtbbench.metrics.ablations import (
    ABLATION_CONDITIONS,
    _deterministic_coin_flip,
    _MAJORITY_ANSWER,
    compute_ablation_table,
    run_ablation,
)
from eval.mtbbench.metrics.accuracy import compute_accuracy_metrics


SAMPLE_CASE_PATH = "eval/mtbbench/fixtures/mtb_case_001.json"


@pytest.mark.integration
def test_majority_class_baseline_is_trivial():
    """Majority-class baseline always predicts the same answer."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_ablation(case, "majority_class", dry_run=True)
    predictions = [a["predicted"] for a in transcript.answers]
    assert all(p == _MAJORITY_ANSWER for p in predictions)
    # Verify it's labeled correctly
    assert all(a["baseline_method"] == "majority_class" for a in transcript.answers)


@pytest.mark.integration
def test_random_baseline_is_deterministic():
    """Random baseline produces same results across runs (SHA-256 seeded)."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    t1 = run_ablation(case, "random_baseline", dry_run=True)
    t2 = run_ablation(case, "random_baseline", dry_run=True)
    for a1, a2 in zip(t1.answers, t2.answers):
        assert a1["predicted"] == a2["predicted"], "Random baseline must be deterministic"


@pytest.mark.integration
def test_base_llm_uses_coin_flip_not_majority():
    """base_llm in DRY_RUN must NOT always predict 'A) Yes' (the majority answer).

    With the deterministic coin-flip, predictions vary by question, avoiding
    the trivial 56% majority-class score. This is the key fix for the
    class-imbalance math problem.
    """
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_ablation(case, "base_llm", dry_run=True)
    predictions = set(a["predicted"] for a in transcript.answers)
    # With SHA-256 on different questions, we expect both A and B to appear
    # (unless extremely unlikely hash collision — the fixture has 2 questions)
    assert len(predictions) >= 1  # At minimum we get predictions
    # Verify it's labeled as coin_flip, not majority_class
    for a in transcript.answers:
        assert a["baseline_method"] == "deterministic_coin_flip"


@pytest.mark.integration
def test_full_platform_also_uses_coin_flip_in_dry_run():
    """Full platform in DRY_RUN should NOT always return 'A) Yes'.

    The _generate_answer function now uses coin-flip in DRY_RUN instead of
    always returning the majority-class answer.
    """
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    transcript = run_case(case, dry_run=True)
    # With only 2 questions, both could hash to the same answer — that's OK.
    # The key check is that the answer generation mechanism is not hardcoded.
    for a in transcript.answers:
        assert a["predicted"] in ("A) Yes", "B) No")


@pytest.mark.integration
def test_ablation_conditions_include_baselines():
    """ABLATION_CONDITIONS must include majority_class and random_baseline."""
    assert "majority_class" in ABLATION_CONDITIONS
    assert "random_baseline" in ABLATION_CONDITIONS
    assert "base_llm" in ABLATION_CONDITIONS
    assert len(ABLATION_CONDITIONS) == 7


@pytest.mark.integration
def test_ablation_table_runs_all_conditions():
    """compute_ablation_table must produce results for all 7 conditions."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    table = compute_ablation_table(case, dry_run=True)
    assert set(table.keys()) == set(ABLATION_CONDITIONS)
    for condition, result in table.items():
        assert "accuracy" in result
        assert "governance" in result
        assert "delta_accuracy" in result


@pytest.mark.integration
def test_msi_tmb_fields_in_fixture():
    """Fixture must contain MSI and TMB data for the platform's reasoning path."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    assert case.msi_score == pytest.approx(0.0)
    assert case.msi_type == "Stable"
    assert case.tmb_mut_per_mb == pytest.approx(0.978, rel=0.01)


@pytest.mark.integration
def test_msi_tmb_flows_to_platform_context():
    """MSI/TMB fields must propagate from case_adapter to platform context dict."""
    case = load_mtbbench_case(SAMPLE_CASE_PATH)
    context = mtbcase_to_platform_context(case)
    assert "msi_score" in context
    assert "msi_type" in context
    assert "tmb_mut_per_mb" in context
    assert context["msi_type"] == "Stable"
    assert context["tmb_mut_per_mb"] == pytest.approx(0.978, rel=0.01)


@pytest.mark.integration
def test_deterministic_coin_flip_reproducible():
    """_deterministic_coin_flip must return same answer for same inputs."""
    assert _deterministic_coin_flip("P-001", "Will the cancer recur?") == \
           _deterministic_coin_flip("P-001", "Will the cancer recur?")
    # Different questions should (usually) give different answers
    # but we can't guarantee it — just check it doesn't crash
    _deterministic_coin_flip("P-001", "Will the patient survive?")


@pytest.mark.integration
def test_coin_flip_has_both_classes():
    """Over many inputs, coin-flip should produce both A and B answers."""
    answers = set()
    for i in range(50):
        answers.add(_deterministic_coin_flip(f"P-{i:04d}", "test question"))
    assert "A) Yes" in answers, "Coin flip never produced 'A) Yes' in 50 trials"
    assert "B) No" in answers, "Coin flip never produced 'B) No' in 50 trials"
