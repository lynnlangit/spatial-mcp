"""Copy-number architecture model comparison (spec section 8)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cnv_fixtures import (  # noqa: E402
    imbalanced_region,
    make_site,
    segmented_region,
)
from mcp_genomic_results.cnv.architecture import compare_architectures  # noqa: E402
from mcp_genomic_results.cnv.tools import compare_cnv_architectures_impl  # noqa: E402

S = 838.0


def _models(result):
    return {m["model"]: m for m in result["models"]}


class TestModelRanking:
    def test_neutral_region_prefers_m0(self):
        region = imbalanced_region(deviation=0.0, n_blocks=4, depth=4000)
        result = compare_architectures(region, S)
        assert result["best_model"] == "M0_neutral"

    def test_uniform_event_prefers_m1_over_m0(self):
        region = imbalanced_region(deviation=0.06, n_blocks=5, depth=4000)
        result = compare_architectures(region, S)
        models = _models(result)
        assert models["M1_whole_region"]["aic"] < models["M0_neutral"]["aic"]

    def test_segmented_region_prefers_m2(self):
        result = compare_architectures(segmented_region(), S)
        assert result["best_model"] == "M2_breakpoint"

    def test_aic_follows_its_definition(self):
        """AIC = 2k - 2 logL. M2 charges two segment deviations, M1 one, M0 none."""
        result = compare_architectures(segmented_region(), S)
        for model in result["models"]:
            assert model["aic"] == pytest.approx(2 * model["k"] - 2 * model["log_likelihood"])
        models = _models(result)
        assert models["M0_neutral"]["k"] == 0
        assert models["M1_whole_region"]["k"] == 1
        assert models["M2_breakpoint"]["k"] == 2

    def test_delta_aic_is_zero_for_the_winner(self):
        result = compare_architectures(segmented_region(), S)
        assert result["models"][0]["delta_aic"] == 0.0
        assert all(m["delta_aic"] >= 0 for m in result["models"])

    def test_likelihood_ratio_compares_m2_against_m1_on_one_df(self):
        result = compare_architectures(segmented_region(), S)
        lrt = result["likelihood_ratio_test"]
        models = _models(result)
        expected = 2 * (
            models["M2_breakpoint"]["log_likelihood"] - models["M1_whole_region"]["log_likelihood"]
        )
        assert lrt["df"] == 1
        assert lrt["likelihood_ratio"] == pytest.approx(expected)
        assert 0.0 <= lrt["p"] <= 1.0


class TestBreakpointSearch:
    def test_breakpoint_lands_between_the_two_segments(self):
        result = compare_architectures(segmented_region(), S)
        models = _models(result)
        bp = models["M2_breakpoint"]["breakpoint"]
        assert 30_000_000 < bp < 150_000_000

    def test_candidates_default_to_block_boundaries(self):
        """A breakpoint inside a block is unidentifiable; a fine grid would fake resolution."""
        region = segmented_region()
        result = compare_architectures(region, S)
        # Four blocks give three inter-block boundaries.
        assert len(result["breakpoint_scan"]) == 3

    def test_explicit_candidates_are_honoured(self):
        result = compare_architectures(segmented_region(), S, candidate_breakpoints=[100_000_000])
        assert len(result["breakpoint_scan"]) == 1
        assert _models(result)["M2_breakpoint"]["breakpoint"] == 100_000_000

    def test_single_block_region_cannot_fit_a_breakpoint(self):
        region = [make_site("chr3", 10_000_000, "chr3_blk001", 0.05, 3000)]
        result = compare_architectures(region, S)
        assert "M2_breakpoint" not in _models(result)
        assert result["likelihood_ratio_test"] is None


class TestCaution:
    def test_fires_when_a_segment_rests_on_one_block(self):
        """With few loci this comparison is easy to over-read. Say so out loud."""
        result = compare_architectures(segmented_region(), S)
        assert result["caution"]["fired"] is True
        assert any("rests on 1 haplotype block" in r for r in result["caution"]["reasons"])

    def test_notes_the_unpriced_breakpoint_search(self):
        result = compare_architectures(segmented_region(), S)
        assert any("not charged as a fitted parameter" in r for r in result["caution"]["reasons"])

    def test_notes_when_sites_outnumber_blocks(self):
        region = imbalanced_region(n_blocks=4)
        region += [dict(s, pos=s["pos"] + 5000) for s in region]
        result = compare_architectures(region, S)
        assert any("effective sample size" in r for r in result["caution"]["reasons"])


class TestEnvelope:
    def test_caution_downgrades_the_grade_to_low(self):
        """A comparison that has told you it may rest on one locus is exploratory."""
        result = compare_cnv_architectures_impl(segmented_region(), S)
        assert result["grade"] == "low"
        assert any("rests on 1 haplotype block" in limit for limit in result["limits"])

    def test_clean_comparison_is_moderate(self):
        region = imbalanced_region(deviation=0.05, n_blocks=6, depth=4000)
        result = compare_cnv_architectures_impl(region, S)
        if not result["value"]["caution"]["fired"]:
            assert result["grade"] == "moderate"

    def test_empty_region_is_not_assessable(self):
        result = compare_cnv_architectures_impl([], S)
        assert result["grade"] == "not_assessable"
        assert result["value"] == {}

    def test_assumptions_name_the_breakpoint_accounting(self):
        result = compare_cnv_architectures_impl(segmented_region(), S)
        joined = " ".join(result["assumptions"])
        assert "breakpoint" in joined
        assert "AIC" in joined
