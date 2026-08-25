"""Regression tests for the two fgbio defects in CNV_TOOLS_SPEC.md section 10.

Both were found by using the tools on a real specimen, and both survived
because DRY_RUN defaults to true — the broken paths were never exercised.
These tests run against the non-dry-run code paths for that reason.
"""

import gzip
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mcp_fgbio.server import (  # noqa: E402
    REFERENCE_GENOMES,
    _chrom_sizes_url,
    _genome_url,
    _md5sum_url,
    _scan_fastq,
    _verification_block,
    _vcf_header_contigs,
)


class TestDefect1ReferenceGenomeURL:
    """The old implementation built an NCBI path that does not exist.

        https://ftp.ncbi.nlm.nih.gov/genomes/{genome}/genome.fna.gz

    It 404s for hg38, hg19 and mm10 alike. NCBI serves assemblies under
    /genomes/all/GCF/... by accession, and UCSC-style names like "hg19" are not
    NCBI identifiers at all.
    """

    @pytest.mark.parametrize("genome", ["hg38", "hg19", "mm10", "mm39", "rn6", "danRer11"])
    def test_every_advertised_genome_resolves_to_goldenpath(self, genome):
        url = _genome_url(genome)
        assert url == (
            f"https://hgdownload.soe.ucsc.edu/goldenPath/{genome}/bigZips/{genome}.fa.gz"
        )

    def test_no_genome_resolves_to_the_broken_ncbi_path(self):
        for genome in REFERENCE_GENOMES:
            assert "ftp.ncbi.nlm.nih.gov" not in _genome_url(genome)

    def test_checksum_manifest_sits_beside_the_assembly(self):
        assert _md5sum_url("hg19").endswith("/goldenPath/hg19/bigZips/md5sum.txt")

    def test_chrom_sizes_manifest_is_addressable(self):
        assert _chrom_sizes_url("hg19").endswith("/bigZips/hg19.chrom.sizes")

    def test_every_genome_declares_assembly_and_organism(self):
        for genome, info in REFERENCE_GENOMES.items():
            assert info["assembly"], f"{genome} has no assembly name"
            assert info["organism"], f"{genome} has no organism"


class TestChecksumVerification:
    def test_matching_checksum_passes(self):
        block = _verification_block("abc123", "abc123")
        assert block["checksum_match"] is True

    def test_mismatched_checksum_fails(self):
        block = _verification_block("abc123", "def456")
        assert block["checksum_match"] is False

    def test_absent_manifest_is_none_not_true(self):
        """"No checksum published" must not be recorded as "checksum verified"."""
        block = _verification_block("abc123", None)
        assert block["checksum_match"] is None
        assert "unverified" in block["note"]

    def test_note_distinguishes_intact_from_correct(self):
        block = _verification_block("abc123", "abc123")
        assert "does not confirm the genome is the right one" in block["note"]


class TestVCFContigParsing:
    def test_reads_contig_lengths_from_the_header(self, tmp_path):
        vcf = tmp_path / "specimen.vcf"
        vcf.write_text(
            "##fileformat=VCFv4.1\n"
            "##contig=<ID=chr1,length=249250621>\n"
            "##contig=<ID=chr2,length=243199373>\n"
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\n"
            "chr1\t100\t.\tA\tG\t50\tPASS\t.\n"
        )
        contigs = _vcf_header_contigs(str(vcf))
        assert contigs == {"chr1": 249250621, "chr2": 243199373}

    def test_header_without_contigs_returns_empty(self, tmp_path):
        vcf = tmp_path / "bare.vcf"
        vcf.write_text("##fileformat=VCFv4.1\n#CHROM\tPOS\tID\tREF\tALT\n")
        assert _vcf_header_contigs(str(vcf)) == {}


def _write_fastq(path: Path, n_reads: int, read_length: int = 100, gzipped: bool = False):
    """A synthetic FASTQ with an exactly known read count."""
    record = (
        "@synthetic_read_{i}\n"
        + "A" * read_length + "\n"
        + "+\n"
        + "I" * read_length + "\n"
    )
    body = "".join(record.format(i=i) for i in range(n_reads))
    if gzipped:
        with gzip.open(path, "wt") as fh:
            fh.write(body)
    else:
        path.write_text(body)


class TestDefect2FastqReadCount:
    """The old implementation returned the SAMPLE size in a field called
    `total_reads`, documented as "Number of reads in the file". On a lane of
    4,736,505 reads it reported 10,000 — a 474x error in a field that looks
    entirely plausible, sitting next to metadata.sampled_reads saying the same
    number.
    """

    def test_sampled_count_is_named_for_what_it_is(self, tmp_path):
        path = tmp_path / "reads.fastq"
        _write_fastq(path, 5000)
        stats = _scan_fastq(str(path), sample_size=1000, full_count=False)
        assert stats["sampled_reads"] == 1000
        assert stats["exact"] is False

    def test_estimated_total_is_not_the_sample_size(self, tmp_path):
        """The exact failure mode: the estimate must not simply echo the sample."""
        path = tmp_path / "reads.fastq"
        _write_fastq(path, 5000)
        stats = _scan_fastq(str(path), sample_size=1000, full_count=False)
        assert stats["estimated_total_reads"] != stats["sampled_reads"]
        assert stats["estimated_total_reads"] == pytest.approx(5000, rel=0.05)

    def test_full_count_is_exact(self, tmp_path):
        path = tmp_path / "reads.fastq"
        _write_fastq(path, 5000)
        stats = _scan_fastq(str(path), sample_size=1000, full_count=True)
        assert stats["estimated_total_reads"] == 5000
        assert stats["exact"] is True

    def test_gzipped_input_reports_the_right_total(self, tmp_path):
        """Whether estimated or counted exactly, the reported total must be right."""
        path = tmp_path / "reads.fastq.gz"
        _write_fastq(path, 20000, gzipped=True)
        stats = _scan_fastq(str(path), sample_size=2000, full_count=False)
        assert stats["sampled_reads"] == 2000
        assert stats["estimated_total_reads"] == pytest.approx(20000, rel=0.10)

    def test_small_gzip_falls_back_to_an_exact_count(self, tmp_path):
        """A decompressor's read-ahead skews the byte counter on a small file.

        Rather than extrapolate from a denominator known to be polluted, the
        scanner finishes the pass — which is cheap precisely because the file is
        small enough for read-ahead to have mattered.
        """
        path = tmp_path / "small.fastq.gz"
        _write_fastq(path, 20000, gzipped=True)
        stats = _scan_fastq(str(path), sample_size=2000, full_count=False)
        assert stats["exact"] is True
        assert stats["estimated_total_reads"] == 20000

    def test_uncompressed_input_extrapolates_without_the_fallback(self, tmp_path):
        """A plain file's text position is exact, so extrapolation is sound."""
        path = tmp_path / "plain.fastq"
        _write_fastq(path, 20000)
        stats = _scan_fastq(str(path), sample_size=2000, full_count=False)
        assert stats["exact"] is False
        assert stats["estimated_total_reads"] == pytest.approx(20000, rel=0.05)

    def test_full_count_on_gzipped_input_is_exact(self, tmp_path):
        path = tmp_path / "reads.fastq.gz"
        _write_fastq(path, 20000, gzipped=True)
        stats = _scan_fastq(str(path), sample_size=2000, full_count=True)
        assert stats["estimated_total_reads"] == 20000

    def test_file_shorter_than_the_sample_is_counted_exactly(self, tmp_path):
        path = tmp_path / "few.fastq"
        _write_fastq(path, 42)
        stats = _scan_fastq(str(path), sample_size=1000, full_count=False)
        assert stats["sampled_reads"] == 42
        assert stats["estimated_total_reads"] == pytest.approx(42, rel=0.05)

    def test_quality_statistics_are_preserved(self, tmp_path):
        """The QC values were always sound and must survive the fix."""
        path = tmp_path / "reads.fastq"
        _write_fastq(path, 500, read_length=115)
        stats = _scan_fastq(str(path), sample_size=500, full_count=False)
        # "I" is Phred+33 quality 40.
        assert stats["total_quality"] / stats["sampled_reads"] == pytest.approx(40.0)
        assert stats["total_length"] / stats["sampled_reads"] == pytest.approx(115.0)

    def test_malformed_record_raises(self, tmp_path):
        path = tmp_path / "bad.fastq"
        path.write_text("not_a_header\nACGT\n+\nIIII\n")
        with pytest.raises(ValueError, match="Invalid FASTQ header"):
            _scan_fastq(str(path), sample_size=10, full_count=False)
