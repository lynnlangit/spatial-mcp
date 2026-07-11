"""
Milestone 3 tests: governance aggregator, bootstrap CIs, Table B emitter.

Run with:
    uv run pytest eval/test_milestone_3.py -v -m integration
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from eval.mtbbench.case_adapter import load_mtbbench_cohort
from eval.mtbbench.eval_runner import run_case, EvalTranscript
from eval.mtbbench.metrics.governance import compute_governance_metrics
from eval.mtbbench.metrics.table_b import (
    bootstrap_ci,
    compute_cohort_governance,
    emit_table_b_markdown,
    generate_table_b,
    load_transcripts_from_dir,
)


TRANSCRIPTS_DIR = Path("eval/mtbbench/results/transcripts")
DATA_PATH = Path("eval/mtbbench/data/questions_msk_bench.json")


@pytest.mark.integration
def test_bootstrap_ci_basic():
    """Bootstrap CI produces valid statistics."""
    values = [1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0]
    result = bootstrap_ci(values)
    assert result["n"] == 10
    assert 0.5 <= result["mean"] <= 1.0
    assert result["ci_low"] <= result["mean"]
    assert result["ci_high"] >= result["mean"]
    assert result["ci_low"] >= 0.0
    assert result["ci_high"] <= 1.0


@pytest.mark.integration
def test_bootstrap_ci_all_ones():
    """All-ones input should give CI of [1.0, 1.0]."""
    values = [1.0] * 40
    result = bootstrap_ci(values)
    assert result["mean"] == 1.0
    assert result["ci_low"] == 1.0
    assert result["ci_high"] == 1.0


@pytest.mark.integration
def test_bootstrap_ci_empty():
    """Empty input should return zeros."""
    result = bootstrap_ci([])
    assert result["mean"] == 0.0
    assert result["n"] == 0


@pytest.mark.integration
def test_bootstrap_ci_single_value():
    """Single value should return that value for all stats."""
    result = bootstrap_ci([0.75])
    assert result["mean"] == 0.75
    assert result["ci_low"] == 0.75
    assert result["ci_high"] == 0.75
    assert result["n"] == 1


@pytest.mark.integration
def test_bootstrap_ci_deterministic():
    """Same seed produces same CI (reproducibility)."""
    values = [0.5, 0.7, 0.3, 0.9, 0.1, 0.6, 0.8, 0.2, 0.4, 0.6]
    r1 = bootstrap_ci(values, seed=42)
    r2 = bootstrap_ci(values, seed=42)
    assert r1["ci_low"] == r2["ci_low"]
    assert r1["ci_high"] == r2["ci_high"]


@pytest.mark.integration
@pytest.mark.skipif(not TRANSCRIPTS_DIR.exists(), reason="Run run_cohort first")
def test_load_transcripts_from_dir():
    """Load saved transcripts and verify structure."""
    transcripts, metadata = load_transcripts_from_dir(TRANSCRIPTS_DIR)
    assert len(transcripts) == 40
    assert len(metadata) == 40
    for t in transcripts:
        assert isinstance(t, EvalTranscript)
        assert t.case_id.startswith("P-")
        assert len(t.tool_calls) == 6  # genomic, neoantigen, opentargets, report, deid, hitl
        assert len(t.answers) > 0


@pytest.mark.integration
@pytest.mark.skipif(not TRANSCRIPTS_DIR.exists(), reason="Run run_cohort first")
def test_confidence_calibration_correct_for_mss_cohort():
    """Confidence calibration should show CORRECT for MSS/low-TMB cohort.

    The platform should NOT report high confidence on immunotherapy
    eligibility for MSS/low-TMB patients. This is the key governance signal.
    """
    transcripts, metadata = load_transcripts_from_dir(TRANSCRIPTS_DIR)
    table_b = compute_cohort_governance(transcripts, metadata)

    cal = table_b["confidence_calibration"]
    assert cal["calibration_assessment"] == "CORRECT"
    # High confidence should be < 30% of total calls (MSS cohort)
    assert cal["high_confidence_pct"] < 0.30


@pytest.mark.integration
@pytest.mark.skipif(not TRANSCRIPTS_DIR.exists(), reason="Run run_cohort first")
def test_confidence_distribution_skews_low_for_mss():
    """For MSS/low-TMB, confidence should be predominantly moderate+low."""
    transcripts, metadata = load_transcripts_from_dir(TRANSCRIPTS_DIR)
    table_b = compute_cohort_governance(transcripts, metadata)

    dist = table_b["confidence_calibration"]["distribution"]
    low_plus_medium = dist.get("low", 0) + dist.get("medium", 0)
    # At least 70% of tool calls should be medium or low confidence
    assert low_plus_medium >= 0.70, (
        f"Expected >=70% low+medium confidence for MSS cohort, got {low_plus_medium:.1%}"
    )


@pytest.mark.integration
@pytest.mark.skipif(not TRANSCRIPTS_DIR.exists(), reason="Run run_cohort first")
def test_cancer_type_stratification():
    """Table B must include per-cancer-type governance breakdown."""
    transcripts, metadata = load_transcripts_from_dir(TRANSCRIPTS_DIR)
    table_b = compute_cohort_governance(transcripts, metadata)

    by_type = table_b.get("by_cancer_type", {})
    assert len(by_type) == 8  # 8 cancer types
    assert "Pancreatic Adenocarcinoma" in by_type
    assert by_type["Pancreatic Adenocarcinoma"]["n"] == 13
    assert "Colon Adenocarcinoma" in by_type
    assert by_type["Colon Adenocarcinoma"]["n"] == 7


@pytest.mark.integration
@pytest.mark.skipif(not TRANSCRIPTS_DIR.exists(), reason="Run run_cohort first")
def test_tmb_stratification():
    """Table B must include TMB-category stratification."""
    transcripts, metadata = load_transcripts_from_dir(TRANSCRIPTS_DIR)
    table_b = compute_cohort_governance(transcripts, metadata)

    by_tmb = table_b.get("by_tmb_category", {})
    assert "high" in by_tmb
    assert "intermediate" in by_tmb
    assert "low" in by_tmb
    # Cohort has 3 TMB-High, 10 intermediate, 27 low
    assert by_tmb["high"]["n"] == 3
    assert by_tmb["intermediate"]["n"] == 10
    assert by_tmb["low"]["n"] == 27


@pytest.mark.integration
@pytest.mark.skipif(not TRANSCRIPTS_DIR.exists(), reason="Run run_cohort first")
def test_table_b_emitter_produces_markdown():
    """Table B emitter must produce valid Markdown with expected sections."""
    md = generate_table_b()
    assert "## Table B" in md
    assert "bootstrap 95% CI" in md
    assert "Tool-grounding rate" in md
    assert "HITL catch rate" in md
    assert "De-id integrity" in md
    assert "Confidence Calibration" in md
    assert "Stratification by Cancer Type" in md
    assert "Stratification by TMB Category" in md
    # Should have pipe-delimited table rows
    assert "| Pancreatic Adenocarcinoma |" in md


@pytest.mark.integration
@pytest.mark.skipif(not TRANSCRIPTS_DIR.exists(), reason="Run run_cohort first")
def test_all_transcripts_have_xai_metadata():
    """Every tool call in every transcript must have xai_metadata."""
    transcripts, _ = load_transcripts_from_dir(TRANSCRIPTS_DIR)
    for t in transcripts:
        for tc in t.tool_calls:
            assert tc.xai_metadata, (
                f"Missing xai_metadata for {tc.server}.{tc.tool} in {t.case_id}"
            )
            assert tc.xai_metadata["confidence_level"] in ("high", "medium", "low")
            assert 1 <= len(tc.xai_metadata["key_drivers"]) <= 3


@pytest.mark.integration
@pytest.mark.skipif(not DATA_PATH.exists(), reason="Run fetch_msk_chord first")
def test_cohort_loader_all_40_cases():
    """Cohort loader must produce 40 MTBCase objects with correct fields."""
    cases = load_mtbbench_cohort(str(DATA_PATH))
    assert len(cases) == 40
    for case in cases:
        assert case.case_id.startswith("P-")
        assert case.cancer_type != ""
        assert len(case.questions) > 0
        # Verify MSI/TMB populated from specimen data
        assert case.msi_type in ("Stable", "Instable", "Indeterminate", "Do not report")
