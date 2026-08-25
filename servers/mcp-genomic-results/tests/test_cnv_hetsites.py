"""Heterozygous site extraction and amplicon-aware counting (spec section 3).

The four design decisions in the module docstring are each asserted here, because
each one was arrived at by getting it wrong first and none of them is visible in
the output of a passing run:

  1. germline/somatic separation is dbSNP + purity, NOT a population-AF cutoff
  2. the BAF window must not truncate reachable imbalance
  3. n_sites and n_blocks are separate, always
  4. primer trimming is mandatory on amplicon libraries

`count_amplicon_alleles` reaches pysam, which is an optional extra
(`uv sync --extra bam`) and is not installed by default. Rather than skip the
most important assertions in this file, the tests below substitute a minimal
stand-in for pysam's read/pileup protocol. The code under test is the real
trimming arithmetic; only the iteration protocol is faked.
"""

import gzip
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_genomic_results.cnv import chemistry as _chemistry_mod  # noqa: E402
from mcp_genomic_results.cnv.chemistry import ChemistryGateError  # noqa: E402
from mcp_genomic_results.cnv.hetsites import (  # noqa: E402
    DEFAULT_PRIMER_LENGTH_BP,
    Site,
    _amplicon_key,
    arm_of,
    assign_blocks,
    count_amplicon_alleles,
    extract_sites,
    gene_from_csqt,
    load_records,
    parse_info,
)

AMPLICON = {
    "chemistry": "amplicon",
    "depth_cnv_permitted": False,
    "deduplication_recommended": False,
    "primer_trimming_required": True,
}
HYBRID = {
    "chemistry": "hybrid_capture",
    "depth_cnv_permitted": True,
    "deduplication_recommended": True,
    "primer_trimming_required": False,
}


# --------------------------------------------------------------------------- #
# VCF fixture helpers
# --------------------------------------------------------------------------- #


def _row(
    chrom="chr1",
    pos=1_000_000,
    rsid="rs100",
    ref="A",
    alt="G",
    filt="PASS",
    info="AF1000G=0.4",
    ref_count=120,
    alt_count=110,
    fmt="GT:AD",
    sample=None,
):
    if sample is None:
        sample = f"0/1:{ref_count},{alt_count}"
    return (chrom, pos, rsid, ref, alt, 100, filt, info, fmt, sample)


def _vcf(tmp_path, rows, name="panel.vcf", compress=False):
    lines = [
        "##fileformat=VCFv4.1",
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE",
    ]
    lines += ["\t".join(str(x) for x in r) for r in rows]
    body = "\n".join(lines) + "\n"
    path = tmp_path / (name + ".gz" if compress else name)
    if compress:
        with gzip.open(path, "wt") as fh:
            fh.write(body)
    else:
        path.write_text(body)
    return str(path)


# --------------------------------------------------------------------------- #
# Small pure helpers
# --------------------------------------------------------------------------- #


class TestParseInfo:
    def test_key_value_pairs(self):
        assert parse_info("AF1000G=0.4;DP=200") == {"AF1000G": "0.4", "DP": "200"}

    def test_flag_entries_become_true(self):
        assert parse_info("SOMATIC;DP=10") == {"SOMATIC": True, "DP": "10"}

    def test_value_containing_equals_is_not_split_twice(self):
        assert parse_info("CSQT=1|GENE|A=B")["CSQT"] == "1|GENE|A=B"


class TestGeneFromCsqt:
    def test_first_symbol_alphabetically(self):
        info = {"CSQT": "1|ZZZ3|tx1,1|ABCA4|tx2"}
        assert gene_from_csqt(info) == "ABCA4"

    def test_missing_csqt_returns_empty(self):
        assert gene_from_csqt({}) == ""

    def test_flag_only_csqt_returns_empty(self):
        assert gene_from_csqt({"CSQT": True}) == ""

    def test_entry_without_symbol_is_skipped(self):
        assert gene_from_csqt({"CSQT": "1||tx1"}) == ""


class TestArmOf:
    def test_p_arm_before_centromere(self):
        assert arm_of("chr1", 1_000_000) == "chr1p"

    def test_q_arm_after_centromere(self):
        assert arm_of("chr1", 200_000_000) == "chr1q"

    def test_boundary_is_q(self):
        # pos == centromere midpoint is not < cen, so it falls on q.
        assert arm_of("chr3", 91_000_000) == "chr3q"

    def test_unknown_contig_is_marked_not_guessed(self):
        assert arm_of("chrUn_gl000220", 500) == "chrUn_gl000220?"


class TestLoadRecords:
    def test_parses_fields_and_format_dict(self, tmp_path):
        path = _vcf(tmp_path, [_row(ref_count=10, alt_count=7)])
        ((chrom, pos, rsid, ref, alt, filt, info, fmt),) = list(load_records(path))
        assert (chrom, pos, rsid, ref, alt, filt) == ("chr1", 1_000_000, "rs100", "A", "G", "PASS")
        assert info["AF1000G"] == "0.4"
        assert fmt["AD"] == "10,7"

    def test_header_lines_skipped(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        assert len(list(load_records(path))) == 1

    def test_truncated_line_skipped_not_raised(self, tmp_path):
        path = tmp_path / "short.vcf"
        path.write_text("#CHROM\tPOS\nchr1\t100\trs1\tA\tG\n")
        assert list(load_records(str(path))) == []

    def test_gzipped_vcf_supported(self, tmp_path):
        path = _vcf(tmp_path, [_row()], compress=True)
        assert len(list(load_records(path))) == 1


# --------------------------------------------------------------------------- #
# Design decision 3 -- blocks, not variant counts
# --------------------------------------------------------------------------- #


def _site(chrom, pos, baf=0.5):
    return Site(
        chrom=chrom,
        pos=pos,
        arm=arm_of(chrom, pos),
        ref="A",
        alt="G",
        rsid="rs1",
        gene="",
        ref_count=100,
        alt_count=100,
        depth=200,
        baf=baf,
        pop_af=-1.0,
        filt="PASS",
    )


class TestAssignBlocks:
    def test_sites_within_window_are_one_observation(self):
        sites = assign_blocks([_site("chr3", 100_000), _site("chr3", 900_000)], window=1_000_000)
        assert len({s.block for s in sites}) == 1

    def test_gap_larger_than_window_starts_a_new_block(self):
        sites = assign_blocks([_site("chr3", 100_000), _site("chr3", 5_000_000)], window=1_000_000)
        assert len({s.block for s in sites}) == 2

    def test_different_chromosomes_never_share_a_block(self):
        sites = assign_blocks([_site("chr3", 100_000), _site("chr8", 100_000)], window=1_000_000)
        assert len({s.block for s in sites}) == 2

    def test_clumped_capture_collapses_five_sites_to_one_block(self):
        """The spec's example: five chr3q sites inside 100 kb are ONE observation."""
        sites = assign_blocks(
            [_site("chr3", 130_000_000 + i * 20_000) for i in range(5)], window=1_000_000
        )
        assert len(sites) == 5
        assert len({s.block for s in sites}) == 1

    def test_output_is_position_sorted(self):
        sites = assign_blocks([_site("chr3", 900), _site("chr3", 100)], window=1_000)
        assert [s.pos for s in sites] == [100, 900]


# --------------------------------------------------------------------------- #
# Design decision 4 -- primer trimming
# --------------------------------------------------------------------------- #


class _Read:
    def __init__(self, base, left, tlen, proper=True):
        self.query_sequence = base
        self.is_proper_pair = proper
        self.template_length = tlen
        self.reference_start = left
        self.next_reference_start = left


class _PileupRead:
    is_del = False
    is_refskip = False

    def __init__(self, read):
        self.alignment = read
        self.query_position = 0


def _fake_pysam(reads):
    class _AlignmentFile:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def pileup(self, *a, **k):
            return [SimpleNamespace(pileups=[_PileupRead(r) for r in reads])]

    return SimpleNamespace(AlignmentFile=_AlignmentFile)


class TestAmpliconKey:
    def test_endpoints_are_rounded_to_absorb_jitter(self):
        assert _amplicon_key(_Read("A", 1002, 301)) == (1000, 1300)

    def test_improper_pair_has_no_amplicon_identity(self):
        assert _amplicon_key(_Read("A", 1000, 300, proper=False)) is None

    def test_zero_template_length_has_no_amplicon_identity(self):
        assert _amplicon_key(_Read("A", 1000, 0)) is None

    def test_negative_template_length_uses_absolute_span(self):
        assert _amplicon_key(_Read("A", 1000, -300)) == (1000, 1300)


class TestPrimerTrimming:
    """The SF3B1 R625C signature: one amplicon reporting reference only.

    Amplicon A spans 1000-1300 and carries the locus 150 bp from either end, so
    it is informative. Amplicon B starts at 1140, putting the locus 10 bp inside
    its left primer, so every read reports reference. Including B drags the VAF
    down; since purity is estimated as 2 x VAF, the error propagates downstream.
    """

    POS = 1151  # 1-based; pos0 = 1150

    def _reads(self):
        reads = []
        reads += [_Read("A", 1000, 300) for _ in range(60)]  # amplicon A, ref
        reads += [_Read("G", 1000, 300) for _ in range(40)]  # amplicon A, alt
        reads += [_Read("A", 1140, 300) for _ in range(50)]  # amplicon B, under primer
        return reads

    def _run(self, monkeypatch, primer_length_bp):
        monkeypatch.setattr(_chemistry_mod, "_load_pysam", lambda: _fake_pysam(self._reads()))
        return count_amplicon_alleles(
            "unused.bam", "chr2", self.POS, "A", "G", primer_length_bp=primer_length_bp
        )

    def test_amplicon_under_primer_is_excluded_from_totals(self, monkeypatch):
        out = self._run(monkeypatch, DEFAULT_PRIMER_LENGTH_BP)
        assert out["n_amplicons"] == 2
        assert out["n_amplicons_dropped_to_primer"] == 1
        assert (out["ref_count"], out["alt_count"], out["depth"]) == (60, 40, 100)
        assert out["vaf"] == pytest.approx(0.40)

    def test_untrimmed_totals_show_what_trimming_removed(self, monkeypatch):
        out = self._run(monkeypatch, DEFAULT_PRIMER_LENGTH_BP)
        assert out["untrimmed_depth"] == 150
        assert out["untrimmed_vaf"] == pytest.approx(40 / 150)
        # The whole point: the untrimmed VAF understates the true one, and purity
        # is estimated as 2 x VAF.
        assert out["untrimmed_vaf"] < out["vaf"]

    def test_dropped_amplicon_is_reported_not_silently_discarded(self, monkeypatch):
        out = self._run(monkeypatch, DEFAULT_PRIMER_LENGTH_BP)
        dropped = [a for a in out["amplicons"] if a["under_primer"]]
        assert len(dropped) == 1
        assert dropped[0]["reads_under_primer"] == 50
        assert dropped[0]["depth"] == 0

    def test_zero_trim_length_keeps_the_artifact(self, monkeypatch):
        """With trimming disabled the reference-only amplicon dilutes the VAF."""
        out = self._run(monkeypatch, 0)
        assert out["n_amplicons_dropped_to_primer"] == 0
        assert out["depth"] == 150
        assert out["vaf"] == pytest.approx(out["untrimmed_vaf"])

    def test_locus_near_right_primer_is_also_trimmed(self, monkeypatch):
        """Either primer can cover the locus, depending on amplicon orientation."""
        reads = [_Read("A", 1000, 300) for _ in range(20)]  # spans 1000-1300
        monkeypatch.setattr(_chemistry_mod, "_load_pysam", lambda: _fake_pysam(reads))
        # pos0 = 1290, so right - pos0 = 10 <= 30
        out = count_amplicon_alleles("unused.bam", "chr2", 1291, "A", "G")
        assert out["n_amplicons_dropped_to_primer"] == 1
        assert out["depth"] == 0
        assert out["vaf"] is None


# --------------------------------------------------------------------------- #
# extract_sites -- the gate, the filters, and the counts
# --------------------------------------------------------------------------- #


class TestChemistryGate:
    def test_missing_chemistry_raises(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        with pytest.raises(ChemistryGateError):
            extract_sites(path, None)

    def test_empty_chemistry_raises(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        with pytest.raises(ChemistryGateError):
            extract_sites(path, {})

    def test_chemistry_is_positional_and_has_no_default(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        with pytest.raises(TypeError):
            extract_sites(path)


class TestGermlineSeparation:
    """Design decision 1: dbSNP membership + purity, never a population-AF cutoff."""

    def test_variant_without_rs_id_is_rejected(self, tmp_path):
        path = _vcf(tmp_path, [_row(rsid=".")])
        out = extract_sites(path, AMPLICON)
        assert out["n_sites"] == 0
        assert out["rejections"]["no_dbsnp_evidence"] == 1

    def test_rare_population_variant_is_kept(self, tmp_path):
        """A 1000G AF of 0.009 must survive. An AF filter removed exactly these."""
        path = _vcf(tmp_path, [_row(info="AF1000G=0.009")])
        out = extract_sites(path, AMPLICON)
        assert out["n_sites"] == 1
        assert out["sites"][0]["pop_af"] == pytest.approx(0.009)

    def test_common_population_variant_is_kept(self, tmp_path):
        path = _vcf(tmp_path, [_row(info="AF1000G=0.97")])
        assert extract_sites(path, AMPLICON)["n_sites"] == 1

    def test_absent_population_af_recorded_as_unknown_not_zero(self, tmp_path):
        path = _vcf(tmp_path, [_row(info="DP=200")])
        out = extract_sites(path, AMPLICON)
        assert out["sites"][0]["pop_af"] == -1.0

    def test_unparseable_population_af_degrades_to_unknown(self, tmp_path):
        path = _vcf(tmp_path, [_row(info="AF1000G=NA")])
        assert extract_sites(path, AMPLICON)["sites"][0]["pop_af"] == -1.0


class TestRecordFilters:
    def test_indel_rejected_as_not_snv(self, tmp_path):
        path = _vcf(tmp_path, [_row(ref="AT", alt="A")])
        out = extract_sites(path, AMPLICON)
        assert out["rejections"]["not_snv"] == 1

    def test_non_pass_rejected(self, tmp_path):
        path = _vcf(tmp_path, [_row(filt="LowQ")])
        assert extract_sites(path, AMPLICON)["rejections"]["not_pass"] == 1

    def test_non_autosome_excluded_by_default(self, tmp_path):
        path = _vcf(tmp_path, [_row(chrom="chrX", pos=50_000_000)])
        out = extract_sites(path, AMPLICON)
        assert out["n_sites"] == 0
        assert out["rejections"]["non_autosome"] == 1

    def test_chrx_included_when_requested(self, tmp_path):
        path = _vcf(tmp_path, [_row(chrom="chrX", pos=50_000_000)])
        assert extract_sites(path, AMPLICON, include_chrx=True)["n_sites"] == 1

    def test_low_depth_rejected(self, tmp_path):
        path = _vcf(tmp_path, [_row(ref_count=20, alt_count=18)])
        out = extract_sites(path, AMPLICON, min_depth=200)
        assert out["rejections"]["low_depth"] == 1

    def test_baf_outside_window_rejected(self, tmp_path):
        path = _vcf(tmp_path, [_row(ref_count=220, alt_count=10)])
        out = extract_sites(path, AMPLICON)
        assert out["rejections"]["baf_out_of_window"] == 1

    def test_malformed_ad_rejected_not_raised(self, tmp_path):
        path = _vcf(tmp_path, [_row(sample="0/1:120")])
        out = extract_sites(path, AMPLICON)
        assert out["rejections"]["bad_ad"] == 1

    def test_multiallelic_locus_dropped(self, tmp_path):
        """Two records at one position make BAF uninterpretable."""
        path = _vcf(
            tmp_path,
            [_row(pos=1_000_000, alt="G"), _row(pos=1_000_000, alt="T", rsid="rs101")],
        )
        out = extract_sites(path, AMPLICON)
        assert out["n_sites"] == 0
        assert out["rejections"]["multiallelic_locus"] == 2

    def test_counts_come_from_ad_not_a_rounded_ratio(self, tmp_path):
        """AD carries exact integers; VF is rounded to 4dp and must not be used."""
        path = _vcf(
            tmp_path,
            [_row(ref_count=123, alt_count=107, fmt="GT:AD:VF", sample="0/1:123,107:0.9999")],
        )
        out = extract_sites(path, AMPLICON)
        site = out["sites"][0]
        assert (site["ref_count"], site["alt_count"], site["depth"]) == (123, 107, 230)
        assert site["baf"] == pytest.approx(107 / 230)


class TestSiteAndBlockCounts:
    """Design decision 3: n_sites and n_blocks are emitted separately, always."""

    def test_both_counts_present_and_distinct(self, tmp_path):
        rows = [_row(chrom="chr3", pos=130_000_000 + i * 20_000, rsid=f"rs{i}") for i in range(5)]
        out = extract_sites(_vcf(tmp_path, rows), AMPLICON)
        assert out["n_sites"] == 5
        assert out["n_blocks"] == 1

    def test_per_chromosome_and_per_arm_carry_both_counts(self, tmp_path):
        rows = [
            _row(chrom="chr3", pos=10_000_000, rsid="rs1"),
            _row(chrom="chr3", pos=130_000_000, rsid="rs2"),
        ]
        out = extract_sites(_vcf(tmp_path, rows), AMPLICON)
        assert out["per_chromosome"]["chr3"] == {"n_sites": 2, "n_blocks": 2}
        assert out["per_arm"]["chr3p"] == {"n_sites": 1, "n_blocks": 1}
        assert out["per_arm"]["chr3q"] == {"n_sites": 1, "n_blocks": 1}

    def test_candidate_count_precedes_depth_and_window_filters(self, tmp_path):
        """n_dbsnp_snv_candidates is the denominator a caller should quote."""
        rows = [
            _row(pos=1_000_000, rsid="rs1"),
            _row(pos=2_000_000, rsid="rs2", ref_count=5, alt_count=4),  # low depth
            _row(pos=3_000_000, rsid="rs3", ref_count=220, alt_count=5),  # outside window
            _row(pos=4_000_000, rsid=".", ref_count=120, alt_count=110),  # not dbSNP
        ]
        out = extract_sites(_vcf(tmp_path, rows), AMPLICON)
        assert out["n_dbsnp_snv_candidates"] == 3
        assert out["n_sites"] == 1


class TestPurityWindowWarning:
    """Design decision 2: the window must clear anything somatic can reach."""

    def test_warns_when_window_floor_does_not_clear_twice_purity(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        out = extract_sites(path, AMPLICON, purity_hint=0.166, baf_window=(0.20, 0.80))
        assert out["warnings"]
        assert "2 x purity" in out["warnings"][0]

    def test_silent_when_window_clears_the_ceiling(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        out = extract_sites(path, AMPLICON, purity_hint=0.05, baf_window=(0.20, 0.80))
        assert out["warnings"] == []

    def test_no_warning_without_a_purity_hint(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        assert extract_sites(path, AMPLICON)["warnings"] == []


class TestParameterEcho:
    def test_primer_length_reported_only_when_a_bam_was_used(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        out = extract_sites(path, AMPLICON)
        assert out["parameters"]["primer_length_bp"] is None
        assert out["bam_recount"] == {"performed": False}

    def test_window_and_depth_echoed(self, tmp_path):
        path = _vcf(tmp_path, [_row()])
        out = extract_sites(path, HYBRID, min_depth=150, baf_window=(0.25, 0.75))
        assert out["parameters"]["min_depth"] == 150
        assert out["parameters"]["baf_window"] == [0.25, 0.75]
