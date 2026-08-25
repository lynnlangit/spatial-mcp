"""Library chemistry detection and the gate it enforces (spec section 2)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cnv_fixtures import (  # noqa: E402
    AMPLICON_CHEMISTRY,
    AMPLICON_SIGNALS,
    CONFLICTING_SIGNALS,
    HYBRID_CHEMISTRY,
    HYBRID_SIGNALS,
)
from mcp_genomic_results.cnv.chemistry import (  # noqa: E402
    ChemistryGateError,
    chemistry_flags,
    classify_signals,
    require_chemistry,
)
from mcp_genomic_results.cnv.tools import detect_library_chemistry_impl  # noqa: E402


class TestClassifier:
    def test_amplicon_signal_pattern(self):
        verdict = classify_signals(AMPLICON_SIGNALS)
        assert verdict["chemistry"] == "amplicon"
        assert verdict["n_amplicon_votes"] == 4
        assert verdict["n_hybrid_votes"] == 0

    def test_hybrid_capture_signal_pattern(self):
        verdict = classify_signals(HYBRID_SIGNALS)
        assert verdict["chemistry"] == "hybrid_capture"
        assert verdict["n_hybrid_votes"] == 4

    def test_conflicting_signals_do_not_produce_a_verdict(self):
        verdict = classify_signals(CONFLICTING_SIGNALS)
        assert verdict["chemistry"] == "indeterminate"

    def test_unmarked_duplicates_abstain_rather_than_voting_capture(self):
        """A BAM with no duplicate flags has not been measured, only unannotated.

        Reading an absent annotation as a low duplication rate would vote
        hybrid_capture on a library nothing ever marked.
        """
        signals = {**AMPLICON_SIGNALS, "duplicate_fraction": 0.0, "duplicate_flags_present": False}
        verdict = classify_signals(signals)
        assert verdict["votes"]["duplicate_fraction"]["vote"] is None
        assert verdict["chemistry"] == "amplicon"  # the other three still agree

    def test_missing_signals_abstain(self):
        verdict = classify_signals({"duplicate_flags_present": True})
        assert verdict["chemistry"] == "indeterminate"
        assert verdict["n_abstentions"] == 4


class TestFlags:
    def test_amplicon_forbids_depth_cnv_and_deduplication(self):
        """Deduplication on an amplicon library destroys the data.

        Reads sharing a start coordinate share a primer; they are independent
        molecules, not PCR duplicates.
        """
        flags = chemistry_flags("amplicon")
        assert flags["depth_cnv_permitted"] is False
        assert flags["deduplication_recommended"] is False
        assert flags["primer_trimming_required"] is True

    def test_hybrid_capture_permits_both(self):
        flags = chemistry_flags("hybrid_capture")
        assert flags["depth_cnv_permitted"] is True
        assert flags["deduplication_recommended"] is True
        assert flags["primer_trimming_required"] is False

    def test_indeterminate_has_no_flags(self):
        with pytest.raises(ValueError):
            chemistry_flags("indeterminate")


class TestGate:
    def test_missing_chemistry_raises(self):
        with pytest.raises(ChemistryGateError, match="requires the `chemistry` payload"):
            require_chemistry(None, "some_tool")

    def test_incomplete_payload_raises(self):
        with pytest.raises(ChemistryGateError, match="incomplete chemistry payload"):
            require_chemistry({"chemistry": "amplicon"}, "some_tool")

    def test_indeterminate_verdict_blocks_downstream_tools(self):
        payload = {
            "chemistry": "indeterminate",
            "depth_cnv_permitted": False,
            "deduplication_recommended": False,
            "primer_trimming_required": True,
        }
        with pytest.raises(ChemistryGateError, match="did not reach a verdict"):
            require_chemistry(payload, "some_tool")

    @pytest.mark.parametrize("payload", [AMPLICON_CHEMISTRY, HYBRID_CHEMISTRY])
    def test_valid_verdicts_pass(self, payload):
        assert require_chemistry(payload, "some_tool") is payload


class TestToolEnvelope:
    def test_missing_bam_is_not_assessable_and_carries_no_value(self):
        result = detect_library_chemistry_impl("/definitely/not/a/real.bam")
        assert result["grade"] == "not_assessable"
        assert result["value"] == {}
        assert result["limits"]
        assert any("not found" in limit for limit in result["limits"])
