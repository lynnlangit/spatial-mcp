"""The imbalance test and, above all, the direction guard (spec section 7)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cnv_fixtures import (  # noqa: E402
    AMPLICON_CHEMISTRY,
    HYBRID_CHEMISTRY,
    imbalanced_region,
    neutral_pool,
)
from mcp_genomic_results.cnv.imbalance import (  # noqa: E402
    DepthEvidenceRefused,
    expected_log2_depth_ratio,
    run_imbalance_test,
)
from mcp_genomic_results.cnv.tools import allelic_imbalance_impl  # noqa: E402

PURITY = 0.1664
S = 838.0
POOL = neutral_pool(n_blocks=40, sites_per_block=2)


def _run(region, chemistry=AMPLICON_CHEMISTRY, **kwargs):
    return run_imbalance_test(region, POOL, S, PURITY, chemistry, n_resample=2000, **kwargs)


class TestDirectionGuard:
    """The point of this module.

    An earlier analysis reported "chromosome 3 loss" from a magnitude. The type
    system now makes that impossible rather than relying on the analyst
    remembering.
    """

    def test_no_depth_evidence_means_undetermined(self):
        out = _run(imbalanced_region(deviation=0.0439))
        assert out["direction"] == "undetermined"
        assert "magnitude" in out["direction_note"]

    def test_undetermined_result_names_both_candidates(self):
        out = _run(imbalanced_region(deviation=0.0439))
        assert "single_copy_loss" in out["consistent_with"]
        assert "single_copy_gain" in out["consistent_with"]

    def test_depth_evidence_on_amplicon_chemistry_raises(self):
        """Refused, not ignored. A caller who passes evidence expects it to count."""
        with pytest.raises(DepthEvidenceRefused, match="depth_cnv_permitted=False"):
            _run(imbalanced_region(), depth_evidence={"log2_ratio": -0.125})

    def test_the_raise_is_not_swallowed_by_the_tool_wrapper(self):
        with pytest.raises(DepthEvidenceRefused):
            allelic_imbalance_impl(
                imbalanced_region(),
                POOL,
                S,
                PURITY,
                AMPLICON_CHEMISTRY,
                depth_evidence={"log2_ratio": -0.125},
                n_resample=500,
            )

    def test_depth_evidence_on_capture_chemistry_assigns_loss(self):
        out = _run(
            imbalanced_region(deviation=0.0439),
            chemistry=HYBRID_CHEMISTRY,
            depth_evidence={"log2_ratio": -0.125, "log2_ratio_ci95": [-0.20, -0.05]},
        )
        assert out["direction"] == "loss"

    def test_depth_evidence_can_assign_gain(self):
        out = _run(
            imbalanced_region(deviation=0.0384),
            chemistry=HYBRID_CHEMISTRY,
            depth_evidence={"log2_ratio": 0.110, "log2_ratio_ci95": [0.04, 0.18]},
        )
        assert out["direction"] == "gain"

    def test_depth_interval_spanning_zero_stays_undetermined(self):
        out = _run(
            imbalanced_region(deviation=0.0439),
            chemistry=HYBRID_CHEMISTRY,
            depth_evidence={"log2_ratio": -0.02, "log2_ratio_ci95": [-0.15, 0.11]},
        )
        assert out["direction"] == "undetermined"
        assert "spanning zero" in out["direction_note"]

    def test_depth_evidence_without_a_ratio_stays_undetermined(self):
        out = _run(
            imbalanced_region(),
            chemistry=HYBRID_CHEMISTRY,
            depth_evidence={"note": "coverage looked low"},
        )
        assert out["direction"] == "undetermined"


class TestStatistic:
    def test_real_imbalance_is_detected(self):
        out = _run(imbalanced_region(deviation=0.0439, n_blocks=4))
        assert out["imbalance"] == pytest.approx(0.0439, abs=0.008)
        assert out["p"] < 0.01
        assert out["n_blocks"] == 4

    def test_copy_neutral_region_returns_zero_and_excludes_monosomy(self):
        out = _run(imbalanced_region(deviation=0.0, n_blocks=4, depth=4000))
        assert out["imbalance"] == pytest.approx(0.0, abs=0.005)
        assert out["p"] > 0.05
        assert out["monosomy_excluded"] is True

    def test_sites_and_blocks_are_reported_separately(self):
        region = imbalanced_region(n_blocks=3)
        region += [dict(s, pos=s["pos"] + 5000) for s in region]
        out = _run(region)
        assert out["n_sites"] == 6
        assert out["n_blocks"] == 3

    def test_null_is_resampled_from_blocks(self):
        out = _run(imbalanced_region())
        assert out["null_distribution"]["unit"] == "haplotype_block"
        assert out["null_distribution"]["pool_blocks_available"] == 40

    def test_p_value_is_never_exactly_zero(self):
        """The observed statistic is itself one draw from the null under H0."""
        out = _run(imbalanced_region(deviation=0.30, depth=6000))
        assert out["p"] > 0.0

    def test_detectability_is_embedded_in_every_result(self):
        out = _run(imbalanced_region())
        assert "detectability" in out
        assert out["detectability"]["unit_type"] == "haplotype_block"

    def test_region_larger_than_the_pool_is_refused(self):
        big = imbalanced_region(n_blocks=4)
        with pytest.raises(ValueError, match="null cannot be resampled"):
            run_imbalance_test(big, POOL[:2], S, PURITY, AMPLICON_CHEMISTRY, n_resample=100)

    def test_empty_region_is_refused(self):
        with pytest.raises(ValueError, match="at least one site"):
            _run([])

    def test_empty_pool_is_refused(self):
        with pytest.raises(ValueError, match="copy-neutral pool"):
            run_imbalance_test(imbalanced_region(), [], S, PURITY, AMPLICON_CHEMISTRY)


class TestEnvelope:
    def test_result_carries_magnitude_warning_in_its_limits(self):
        result = allelic_imbalance_impl(
            imbalanced_region(), POOL, S, PURITY, AMPLICON_CHEMISTRY, n_resample=500
        )
        assert result["grade"] == "moderate"
        assert any("MAGNITUDE" in limit for limit in result["limits"])
        assert result["detectability"] is not None

    def test_actionability_is_never_predictive(self):
        """Nothing in this package selects a therapy."""
        result = allelic_imbalance_impl(
            imbalanced_region(), POOL, S, PURITY, AMPLICON_CHEMISTRY, n_resample=500
        )
        assert result["actionability"] != "predictive"

    def test_synthetic_flag_propagates_into_the_envelope(self):
        result = allelic_imbalance_impl(
            imbalanced_region(),
            POOL,
            S,
            PURITY,
            AMPLICON_CHEMISTRY,
            n_resample=500,
            synthetic_inputs=True,
        )
        assert result["synthetic_inputs"] is True


class TestDepthExpectation:
    def test_single_copy_loss_predicts_a_negative_log2_ratio(self):
        assert expected_log2_depth_ratio(PURITY, 1) == pytest.approx(-0.1253, abs=1e-3)

    def test_single_copy_gain_predicts_a_positive_log2_ratio(self):
        assert expected_log2_depth_ratio(PURITY, 3) > 0

    def test_copy_neutral_predicts_zero(self):
        assert expected_log2_depth_ratio(PURITY, 2) == pytest.approx(0.0, abs=1e-9)
