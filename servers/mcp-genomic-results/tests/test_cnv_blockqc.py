"""Quality-control rules A, B and C, and the overdispersion fit (spec section 4)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cnv_fixtures import (  # noqa: E402
    AMPLICON_CHEMISTRY,
    concordant_block,
    discordant_paralog_block,
    neutral_pool,
    site_with_amplicons,
)
from mcp_genomic_results.cnv.blockqc import (  # noqa: E402
    MIN_AMPLICON_DEPTH_FLOOR,
    amplicon_concordance,
    artifact_screens,
    block_concordance,
    run_qc,
)
from mcp_genomic_results.cnv.tools import qc_heterozygous_sites_impl  # noqa: E402


class TestRuleA:
    def test_paralogous_block_fails_hard(self):
        """THE regression test.

        A block whose sites disagree on deviation magnitude is reporting a
        mapping problem, not a copy-number event. Untreated, a block like this
        produces a confident and entirely false arm-level loss call.

        If a refactor makes this block PASS, the refactor is wrong.
        """
        verdict, p, detail = block_concordance(discordant_paralog_block())
        assert verdict == "DISCORDANT"
        assert p < 1e-30, f"paralogous block passed concordance at p={p:.3e}"
        assert detail["spread"] > 0.2

    def test_sign_flips_do_not_cause_failure(self):
        """Signs may differ within a block; magnitudes may not.

        Which parental allele the VCF calls ALT flips site to site, so a rule
        that keyed on sign would reject every real event it was built to detect.
        """
        verdict, _p, _detail = block_concordance(concordant_block(deviation=0.045))
        assert verdict == "concordant"
        bafs = [s["baf"] for s in concordant_block(deviation=0.045)]
        assert min(bafs) < 0.5 < max(bafs), "fixture should straddle 0.5"

    def test_small_blocks_are_untestable_not_passing(self):
        """A single-site block cannot be corroborated, and must not read as vetted."""
        verdict, _p, detail = block_concordance(concordant_block(n_sites=1))
        assert verdict == "untestable"
        assert detail["n_sites"] == 1

    def test_two_site_block_is_also_untestable(self):
        verdict, _p, _d = block_concordance(concordant_block(n_sites=2))
        assert verdict == "untestable"


class TestRuleB:
    def test_independent_primer_pairs_that_disagree_fail(self):
        site = site_with_amplicons([(300, 600), (20, 600)])
        verdict, p, _detail = amplicon_concordance(site)
        assert verdict == "DISCORDANT"
        assert p < 0.01

    def test_agreeing_primer_pairs_pass(self):
        site = site_with_amplicons([(60, 600), (66, 620)])
        verdict, _p, _detail = amplicon_concordance(site)
        assert verdict == "concordant"

    def test_primer_covered_amplicon_is_excluded_from_the_test(self):
        """A primer-covered amplicon reports reference only; it is not evidence."""
        site = site_with_amplicons([(60, 600), (66, 620), (0, 342)], under_primer_index=2)
        verdict, _p, detail = amplicon_concordance(site)
        assert verdict == "concordant"
        assert detail["n_amplicons_usable"] == 2

    def test_single_amplicon_is_untestable(self):
        verdict, _p, _d = amplicon_concordance(site_with_amplicons([(60, 600)]))
        assert verdict == "untestable"

    def test_depth_floor_cannot_be_lowered(self):
        """A 28-read amplicon passes trivially. That is a false vetting.

        Lowering this floor promotes artifacts into the "corroborated" pile,
        which is worse than leaving them untested.
        """
        site = site_with_amplicons([(3, 28), (2, 25)])
        with pytest.raises(ValueError, match="below the floor"):
            amplicon_concordance(site, min_amplicon_depth=20)

    def test_shallow_amplicons_are_ignored_at_the_floor(self):
        site = site_with_amplicons([(3, 28), (2, 25)])
        verdict, _p, detail = amplicon_concordance(
            site, min_amplicon_depth=MIN_AMPLICON_DEPTH_FLOOR
        )
        assert verdict == "untestable"
        assert detail["n_amplicons_usable"] == 0


class TestRuleC:
    def test_third_allele_fraction(self):
        site = {"chrom": "chr1", "pos": 1, "third_allele_fraction": 0.05}
        assert any("third_allele" in f for f in artifact_screens(site))

    def test_softclip_fraction(self):
        site = {"chrom": "chr1", "pos": 1, "softclip_fraction": 0.6}
        assert any("softclip" in f for f in artifact_screens(site))

    def test_strand_bias(self):
        site = {
            "chrom": "chr1",
            "pos": 1,
            "alt_fwd": 200,
            "alt_rev": 2,
            "ref_fwd": 5,
            "ref_rev": 300,
        }
        assert any("strand-bias" in f for f in artifact_screens(site))

    def test_pinned_amplicon_is_the_primer_dropout_signature(self):
        site = site_with_amplicons([(6, 600), (300, 600)])
        assert any("primer-dropout" in f for f in artifact_screens(site))

    def test_clean_site_fails_nothing(self):
        site = site_with_amplicons([(60, 600), (66, 620)])
        assert artifact_screens(site) == []

    def test_absent_screens_are_skipped_not_failed(self):
        """A screen with no data must not silently pass or silently fail."""
        assert artifact_screens({"chrom": "chr1", "pos": 1}) == []


class TestRunQC:
    def _sites(self):
        return (
            neutral_pool(n_blocks=30, sites_per_block=3)
            + discordant_paralog_block()
            + concordant_block(
                chrom="chr3", block="chr3_blk001", deviation=0.044, n_sites=3, gene="REAL"
            )
        )

    def test_discordant_block_is_dropped_and_reported(self):
        out = run_qc(self._sites(), AMPLICON_CHEMISTRY)
        dropped_blocks = {d["block"] for d in out["dropped_sites"]}
        assert "chr1_blk004" in dropped_blocks, "the paralogous block must be dropped"
        assert all("rule_A" in d["reason"] for d in out["dropped_sites"])
        # A handful of copy-neutral pool blocks also fail, and should: Rule A
        # measures scatter against a BINOMIAL standard error, while a real
        # library is overdispersed relative to binomial. At alpha = 0.01 across
        # ~30 blocks a few failures are the rule working, not misfiring. What
        # matters is that the paralogous block is among them and that the rule
        # does not take most of the pool with it.
        assert out["blocks_failing_rule_a"] < 0.25 * len(out["block_report"])

    def test_concordant_real_event_survives(self):
        out = run_qc(self._sites(), AMPLICON_CHEMISTRY)
        assert any(s["block"] == "chr3_blk001" for s in out["sites"])

    def test_overdispersion_is_fitted_on_the_neutral_pool(self):
        out = run_qc(self._sites(), AMPLICON_CHEMISTRY, neutral_pool_exclude_arms=["chr3p"])
        od = out["overdispersion"]
        assert od["fitted"] is True
        assert od["noise_vs_binomial"] > 1.0, "a real library is never binomial"
        assert "chr3p" in out["neutral_pool"]["excluded_arms"]

    def test_removing_the_paralogous_block_lowers_the_noise_floor(self):
        """The whole point of Rule A: the artifact was inflating the null."""
        out = run_qc(self._sites(), AMPLICON_CHEMISTRY)
        stages = {s["stage"]: s for s in out["stages"]}
        assert (
            stages["after_rule_A"]["noise_vs_binomial"]
            < stages["raw_variant_calls"]["noise_vs_binomial"]
        )

    def test_stages_report_sites_and_blocks_separately(self):
        out = run_qc(self._sites(), AMPLICON_CHEMISTRY)
        for stage in out["stages"]:
            assert "n_sites" in stage and "n_blocks" in stage
            assert stage["n_blocks"] <= stage["n_sites"]

    def test_rule_b_blindness_is_declared_not_hidden(self):
        """With VCF-only input, single-site blocks stay unvetted. Say so."""
        out = run_qc(self._sites(), AMPLICON_CHEMISTRY)
        assert out["rule_b_coverage"]["sites_testable"] == 0
        assert "unvetted" in out["rule_b_coverage"]["note"]


class TestQCEnvelope:
    def test_rule_b_blindness_downgrades_the_grade(self):
        sites = neutral_pool(n_blocks=20, sites_per_block=3)
        result = qc_heterozygous_sites_impl(sites, AMPLICON_CHEMISTRY)
        assert result["grade"] == "moderate"
        assert any("Rule B could not be applied" in limit for limit in result["limits"])

    def test_no_survivors_is_not_assessable(self):
        result = qc_heterozygous_sites_impl(
            concordant_block(n_sites=1, depth=100), AMPLICON_CHEMISTRY
        )
        assert result["grade"] == "not_assessable"
        assert result["value"] == {}

    def test_missing_chemistry_is_refused(self):
        result = qc_heterozygous_sites_impl(neutral_pool(n_blocks=5), None)
        assert result["grade"] == "not_assessable"
        assert any("chemistry" in limit for limit in result["limits"])
