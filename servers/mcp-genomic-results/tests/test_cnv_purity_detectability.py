"""Purity and detectability (spec sections 5 and 6).

The acceptance values in this module are closed-form consequences of allele
counts and a concentration parameter. They need no specimen data, so they are
checked here directly rather than against a fixture that only approximates them.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cnv_fixtures import AMPLICON_CHEMISTRY, imbalanced_region  # noqa: E402
from mcp_genomic_results.cnv.detectability import assess_detectability  # noqa: E402
from mcp_genomic_results.cnv.purity import (  # noqa: E402
    estimate_purity,
    two_proportion_p,
    wilson_ci,
)
from mcp_genomic_results.cnv.stats import (  # noqa: E402
    depth_scaling_ceiling,
    expected_deviation,
    expected_deviations,
    per_site_sd,
)
from mcp_genomic_results.cnv.tools import estimate_tumor_purity_impl  # noqa: E402

# Two driver observations at a purity around 16.6%. These are allele counts, not
# a specimen: any pair of counts with these ratios reproduces every number below.
DRIVER_A = {"label": "DRIVER_A", "alt_count": 169, "depth": 2163, "chrom": "chr19"}
DRIVER_B = {"label": "DRIVER_B", "alt_count": 359, "depth": 4184, "chrom": "chr2"}

PURITY = 0.1664


class TestPurity:
    def test_pooled_purity_and_interval(self):
        out = estimate_purity([DRIVER_A, DRIVER_B])
        assert out["purity"] == pytest.approx(0.1664, abs=5e-5)
        assert out["purity_ci95"][0] == pytest.approx(0.1533, abs=5e-4)
        assert out["purity_ci95"][1] == pytest.approx(0.1805, abs=5e-4)

    def test_per_driver_estimates(self):
        out = estimate_purity([DRIVER_A, DRIVER_B])
        by_label = {r["driver"]: r for r in out["per_driver"]}
        assert by_label["DRIVER_A"]["purity"] == pytest.approx(0.1563, abs=5e-4)
        assert by_label["DRIVER_B"]["purity"] == pytest.approx(0.1716, abs=5e-4)

    def test_drivers_are_consistent_with_both_truncal(self):
        p = two_proportion_p(169, 2163, 359, 4184)
        assert p == pytest.approx(0.294, abs=2e-3)
        assert p >= 0.05

    def test_purity_is_twice_the_vaf_for_a_heterozygous_driver(self):
        out = estimate_purity([{"label": "D", "alt_count": 100, "depth": 1000}])
        assert out["purity"] == pytest.approx(0.2)

    def test_homozygous_driver_uses_vaf_directly(self):
        """A homozygous somatic variant contributes two mutant alleles per genome."""
        out = estimate_purity(
            [{"label": "D", "alt_count": 100, "depth": 1000, "assumed_zygosity": "homozygous"}]
        )
        assert out["purity"] == pytest.approx(0.1)

    def test_mixed_zygosity_pooling_is_refused(self):
        with pytest.raises(ValueError, match="different assumed zygosities"):
            estimate_purity(
                [
                    {"label": "A", "alt_count": 100, "depth": 1000},
                    {
                        "label": "B",
                        "alt_count": 100,
                        "depth": 1000,
                        "assumed_zygosity": "homozygous",
                    },
                ]
            )

    def test_wilson_interval_stays_in_range(self):
        lo, hi = wilson_ci(0, 100)
        assert lo == 0.0 and 0.0 < hi < 1.0


class TestPurityEnvelope:
    def test_three_assumptions_are_always_emitted(self):
        """Clonal, heterozygous, copy-neutral locus. Every time, without exception."""
        result = estimate_tumor_purity_impl([DRIVER_A, DRIVER_B])
        joined = " ".join(result["assumptions"]).lower()
        assert "clonal" in joined
        assert "heterozygous" in joined
        assert "copy-neutral" in joined

    def test_grade_is_high_when_all_loci_are_verified_copy_neutral(self):
        result = estimate_tumor_purity_impl(
            [DRIVER_A, DRIVER_B],
            copy_neutral_evidence={"chr19": {"copy_neutral": True}, "chr2": {"copy_neutral": True}},
        )
        assert result["grade"] == "high"

    def test_grade_degrades_when_copy_neutrality_is_unverified(self):
        """Silence is not confirmation."""
        result = estimate_tumor_purity_impl([DRIVER_A, DRIVER_B])
        assert result["grade"] == "moderate"
        assert any("NOT verified" in limit for limit in result["limits"])

    def test_two_informative_loci_do_not_verify_copy_neutrality(self):
        result = estimate_tumor_purity_impl(
            [DRIVER_A, DRIVER_B],
            copy_neutral_evidence={
                "chr2": {"copy_neutral": True},
                "chr19": {"n_blocks": 2, "imbalance": 0.0},
            },
        )
        assert result["grade"] == "moderate"
        assert result["value"]["copy_neutral_unverified"]

    def test_discordant_drivers_degrade_the_grade(self):
        result = estimate_tumor_purity_impl(
            [
                {"label": "A", "alt_count": 400, "depth": 2000, "chrom": "chr1"},
                {"label": "B", "alt_count": 100, "depth": 2000, "chrom": "chr2"},
            ],
            copy_neutral_evidence={"chr1": {"copy_neutral": True}, "chr2": {"copy_neutral": True}},
        )
        assert result["grade"] == "moderate"
        assert any("differ significantly" in limit for limit in result["limits"])

    def test_bad_input_is_not_assessable(self):
        result = estimate_tumor_purity_impl([{"label": "A", "alt_count": 10, "depth": 0}])
        assert result["grade"] == "not_assessable"
        assert result["value"] == {}


class TestExpectedDeviations:
    @pytest.mark.parametrize(
        "event,expected",
        [
            ("single_copy_loss", 0.0454),
            ("single_copy_gain", 0.0384),
            ("copy_neutral_loh", 0.0832),
            ("double_gain", 0.0713),
        ],
    )
    def test_expected_deviation_at_purity(self, event, expected):
        assert expected_deviation(PURITY, event) == pytest.approx(expected, abs=5e-5)

    def test_loss_and_gain_are_barely_separated(self):
        """0.0070 apart. This is why direction cannot come from BAF magnitude."""
        e = expected_deviations(PURITY)
        gap = abs(e["single_copy_loss"] - e["single_copy_gain"])
        assert gap == pytest.approx(0.0070, abs=5e-5)

    def test_legacy_aliases_resolve(self):
        assert expected_deviation(PURITY, "monosomy") == expected_deviation(
            PURITY, "single_copy_loss"
        )

    def test_unknown_event_raises(self):
        with pytest.raises(ValueError, match="unknown copy-number event"):
            expected_deviation(PURITY, "tetrasomy")


class TestDepthScaling:
    """Depth has a ceiling, and a binomial model does not know that."""

    def test_sd_at_one_lane(self):
        assert per_site_sd(894, 742) == pytest.approx(0.0248, abs=5e-5)

    def test_sd_at_four_lanes(self):
        assert per_site_sd(3576, 742) == pytest.approx(0.0202, abs=5e-5)

    def test_quadrupling_depth_buys_1_23x_not_2x(self):
        gain = per_site_sd(894, 742) / per_site_sd(3576, 742)
        assert gain == pytest.approx(1.23, abs=5e-3)
        assert gain < 2.0, "a binomial model would predict 2x and be wrong"

    def test_infinite_depth_ceiling(self):
        assert depth_scaling_ceiling(742) == pytest.approx(0.0183, abs=5e-5)

    def test_no_depth_crosses_the_ceiling(self):
        ceiling = depth_scaling_ceiling(742)
        assert per_site_sd(10_000_000, 742) > ceiling


class TestDetectability:
    def test_standard_error_uses_blocks_not_sites(self):
        """Using sites would overstate power by sqrt(sites / blocks)."""
        sites = imbalanced_region(n_blocks=2)
        # Two blocks, four sites: two sites share each block.
        sites = sites + [dict(s, pos=s["pos"] + 1000) for s in sites]
        out = assess_detectability(PURITY, sites, 838.0, AMPLICON_CHEMISTRY)
        assert out["n_sites"] == 4
        assert out["n_blocks"] == 2
        assert out["unit_type"] == "haplotype_block"
        expected_se = out["per_site_sd"] / (2**0.5)
        assert out["standard_error"] == pytest.approx(expected_se)

    def test_reports_the_depth_ceiling(self):
        out = assess_detectability(PURITY, imbalanced_region(), 742.0, AMPLICON_CHEMISTRY)
        assert out["depth_scaling_ceiling"] == pytest.approx(0.0183, abs=5e-5)
        assert "0.25 / (s + 1)" in out["depth_note"]

    def test_declares_loss_gain_inseparable_on_amplicon_chemistry(self):
        out = assess_detectability(PURITY, imbalanced_region(), 838.0, AMPLICON_CHEMISTRY)
        assert out["loss_gain_separation"]["separable_by_baf"] is False
        assert "does not permit" in out["loss_gain_separation"]["note"]

    def test_underpowered_region_is_flagged_unmeasurable(self):
        tiny = imbalanced_region(n_blocks=1, depth=120)
        out = assess_detectability(PURITY, tiny, 50.0, AMPLICON_CHEMISTRY)
        assert out["measurable"] is False

    def test_empty_region_reports_no_power(self):
        out = assess_detectability(PURITY, [], 838.0, AMPLICON_CHEMISTRY)
        assert out["measurable"] is False
        assert out["n_blocks"] == 0
