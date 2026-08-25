"""A SYNTHETIC specimen for the copy-number end-to-end regression suite.

Everything here is generated from a fixed seed. No patient data appears in this
module and none may be added — this repository holds synthetic data only.

What it reproduces
------------------
Not any individual's numbers, but the four STRUCTURES the copy-number pipeline
has to react to, each of which caused a real error before the tools existed:

  1. A region carrying a genuine shared allelic deviation across several
     independent haplotype blocks (chr3 here).
  2. A paralogous block whose sites disagree on deviation magnitude — the
     segmental-duplication failure mode. Untreated, a block like this produces a
     confident and entirely false arm-level loss call. QC must drop it.
  3. Regions that are genuinely copy-neutral and must come back as such, with
     single-copy loss positively excluded rather than merely unproven.
  4. A copy-neutral pool with realistic beta-binomial overdispersion, so the
     null the tests resample from is not the binomial fantasy that made the
     original power estimate wrong by 4x.

The specimen is built at a purity of 1/6, which puts single-copy loss and
single-copy gain 0.0070 apart — close enough that the direction guard has
something real to refuse.
"""

from __future__ import annotations

import numpy as np

# ---------------------------------------------------------------------------
# Specimen parameters. Round synthetic numbers, deliberately not any specimen's.
# ---------------------------------------------------------------------------

SEED = 4242

PURITY = 1.0 / 6.0  # 0.16667

# Two clonal drivers on chromosomes that are NOT under test, both at VAF 1/12,
# so purity = 2 x VAF = 1/6 exactly.
DRIVERS = [
    {"label": "SYNTH_DRIVER_A", "alt_count": 200, "depth": 2400, "chrom": "chr11"},
    {"label": "SYNTH_DRIVER_B", "alt_count": 300, "depth": 3600, "chrom": "chr13"},
]

# Expected |BAF - 0.5| at this purity, from the event formulas.
EXPECTED_DEVIATIONS = {
    "single_copy_loss": PURITY / (2 * (2 - PURITY)),   # 0.045455
    "single_copy_gain": PURITY / (2 * (2 + PURITY)),   # 0.038462
    "copy_neutral_loh": PURITY / 2,                    # 0.083333
    "double_gain": PURITY / (2 + 2 * PURITY),          # 0.071429
}

# The chromosome carrying the real event, at single-copy-loss magnitude.
EVENT_CHROM = "chr3"
EVENT_DEVIATION = EXPECTED_DEVIATIONS["single_copy_loss"]

# Beta-binomial concentration of the synthetic library. Small enough to be
# realistically overdispersed, large enough that the event is detectable.
CONCENTRATION = 800.0

# hg19 centromere positions the extractor uses for p/q arm assignment, repeated
# here only so the fixture can place sites on the arm it intends.
CENTROMERES = {
    "chr1": 125_000_000, "chr3": 91_000_000, "chr6": 61_000_000,
    "chr8": 45_600_000,
}

DEFAULT_DEPTH = 2500


def _contig_header() -> list[str]:
    lengths = {
        "chr1": 249_250_621, "chr2": 243_199_373, "chr3": 198_022_430,
        "chr4": 191_154_276, "chr5": 180_915_260, "chr6": 171_115_067,
        "chr7": 159_138_663, "chr8": 146_364_022, "chr9": 141_213_431,
        "chr10": 135_534_747, "chr11": 135_006_516, "chr12": 133_851_895,
        "chr13": 115_169_878, "chr14": 107_349_540, "chr15": 102_531_392,
        "chr16": 90_354_753, "chr17": 81_195_210, "chr18": 78_077_248,
        "chr19": 59_128_983, "chr20": 63_025_520, "chr21": 48_129_895,
        "chr22": 51_304_566,
    }
    return [f"##contig=<ID={c},length={n}>" for c, n in lengths.items()]


class _Builder:
    """Accumulates VCF records and remembers what each one was meant to be."""

    def __init__(self, seed: int = SEED):
        self.rng = np.random.default_rng(seed)
        self.rows: list[tuple] = []
        self.n_informative = 0   # expected to survive extraction
        self.n_candidates = 0    # PASS biallelic autosomal SNVs carrying an rs id

    def _emit(self, chrom, pos, gene, alt, depth, *, filt="PASS", rsid=None,
              informative=True, candidate=True):
        rsid = rsid or f"rs{9_000_000 + len(self.rows)}"
        info = f"AF1000G=0.25;CSQT=1|{gene}|NM_999999.1|missense_variant"
        fmt_sample = f"{depth - alt},{alt}:{depth}"
        self.rows.append(
            (chrom, pos, rsid, "A", "G", "100", filt, info, "AD:DP", fmt_sample)
        )
        if candidate:
            self.n_candidates += 1
        if informative:
            self.n_informative += 1

    def add_block(self, chrom, gene, start, n_sites, deviation, depth=DEFAULT_DEPTH,
                  spacing=20_000):
        """A haplotype block whose sites share one deviation magnitude.

        Signs alternate, because which parental allele the VCF calls ALT flips
        from site to site. A real event produces exactly this: same magnitude,
        arbitrary sign.
        """
        for i in range(n_sites):
            sign = 1 if i % 2 == 0 else -1
            baf = 0.5 + sign * deviation
            alt = int(round(baf * depth))
            self._emit(chrom, start + i * spacing, gene, alt, depth)

    def add_noisy_block(self, chrom, gene, start, n_sites, deviation,
                        depth=DEFAULT_DEPTH, spacing=20_000):
        """Like add_block, but with beta-binomial sampling noise around the deviation."""
        for i in range(n_sites):
            sign = 1 if i % 2 == 0 else -1
            centre = 0.5 + sign * deviation
            p = self.rng.beta(centre * CONCENTRATION, (1 - centre) * CONCENTRATION)
            alt = int(self.rng.binomial(depth, p))
            self._emit(chrom, start + i * spacing, gene, alt, depth)

    def add_paralog_block(self, chrom, gene, start, depth=DEFAULT_DEPTH):
        """A block that must FAIL within-block concordance.

        Reads from a paralogous copy collapse onto the captured target and drag
        BAF away from 0.5 by amounts that vary site to site. Under a real
        arm-level event every site here would have to show the SAME magnitude,
        so this pattern is a mapping problem announcing itself.

        If a refactor ever lets this block through QC, the refactor is wrong.
        """
        deviations = [0.004, 0.012, 0.021, 0.033, 0.048, 0.066,
                      0.088, 0.115, 0.147, 0.184, 0.226, 0.274]
        for i, dev in enumerate(deviations):
            sign = 1 if i % 3 else -1
            alt = int(round((0.5 + sign * dev) * depth))
            # Informative for extraction (they pass the BAF window); QC drops them.
            self._emit(chrom, start + i * 15_000, gene, alt, depth)

    def add_rejects(self):
        """Records that must NOT survive extraction, so the filters are exercised."""
        # Fails the PASS filter — not a candidate at all.
        self._emit("chr5", 1_000_000, "REJECT_FILTER", 1250, 2500,
                   filt="LowQ", informative=False, candidate=False)
        # No rs id: no dbSNP evidence, so germline membership is unestablished.
        self.rows.append(
            ("chr5", 2_000_000, ".", "A", "G", "100", "PASS",
             "AF1000G=0.25", "AD:DP", "1250,1250:2500")
        )
        # Homozygous: outside the heterozygous BAF window.
        self._emit("chr5", 3_000_000, "REJECT_HOM", 2480, 2500, informative=False)
        # Too shallow to be informative.
        self._emit("chr5", 4_000_000, "REJECT_DEPTH", 50, 100, informative=False)

    def to_vcf(self) -> str:
        header = [
            "##fileformat=VCFv4.1",
            "##source=SYNTHETIC_FIXTURE_NOT_REAL_DATA",
            *_contig_header(),
            '##INFO=<ID=AF1000G,Number=A,Type=Float,Description="1000G allele frequency">',
            '##INFO=<ID=CSQT,Number=.,Type=String,Description="Consequence">',
            '##FORMAT=<ID=AD,Number=.,Type=Integer,Description="Allele depths">',
            '##FORMAT=<ID=DP,Number=1,Type=Integer,Description="Total depth">',
            "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSYNTHETIC",
        ]
        body = ["\t".join(str(f) for f in row) for row in sorted(
            self.rows, key=lambda r: (r[0], r[1])
        )]
        return "\n".join(header + body) + "\n"


def build_specimen() -> dict:
    """Generate the synthetic VCF text plus the values the pipeline should recover."""
    b = _Builder()

    # --- The event: chr3 carries a real deviation across four blocks. ---------
    # Three blocks on 3p, one on 3q. Two blocks have enough sites for Rule A to
    # test them, and they must PASS — a real event is internally concordant.
    b.add_block("chr3", "SYN3A", 10_000_000, 3, EVENT_DEVIATION)
    b.add_block("chr3", "SYN3B", 37_000_000, 3, EVENT_DEVIATION)
    b.add_block("chr3", "SYN3C", 47_000_000, 1, EVENT_DEVIATION)
    b.add_block("chr3", "SYN3D", 178_000_000, 1, EVENT_DEVIATION)

    # --- The artifact: a paralogous block on 1p that QC must drop. -----------
    b.add_paralog_block("chr1", "SYN_PARALOG", 120_400_000)

    # --- Genuinely copy-neutral arms, which must come back excluded. ---------
    for i, start in enumerate((10_000_000, 20_000_000, 30_000_000, 40_000_000)):
        b.add_block("chr8", "SYN8P", start, 2, 0.0, depth=4000)
    for i, start in enumerate((10_000_000, 25_000_000, 40_000_000, 55_000_000)):
        b.add_block("chr6", "SYN6P", start, 2, 0.0, depth=4000)

    # --- The copy-neutral pool the null is resampled from. -------------------
    # Overdispersed, because reads from a real library are not independent trials.
    pool_chroms = [f"chr{i}" for i in (2, 4, 5, 7, 9, 10, 12, 14, 15,
                                       16, 17, 18, 19, 20, 21, 22)]
    for c_index, chrom in enumerate(pool_chroms):
        for block_index in range(3):
            b.add_noisy_block(
                chrom, f"SYNPOOL{c_index}_{block_index}",
                5_000_000 + block_index * 20_000_000, 2, 0.0,
            )

    b.add_rejects()

    return {
        "vcf_text": b.to_vcf(),
        "purity": PURITY,
        "drivers": DRIVERS,
        "expected_deviations": EXPECTED_DEVIATIONS,
        "event_chrom": EVENT_CHROM,
        "event_deviation": EVENT_DEVIATION,
        "concentration": CONCENTRATION,
        "n_dbsnp_snv_candidates": b.n_candidates,
        "n_informative_sites": b.n_informative,
        "paralog_gene": "SYN_PARALOG",
        "paralog_block_chrom": "chr1",
        "neutral_arms": ["chr8p", "chr6p"],
        "arms_under_test": ["chr3p", "chr3q", "chr8p", "chr6p", "chr1p"],
    }


# The chemistry verdict shape that detect_library_chemistry emits. Declared here
# so the pipeline can be driven without a BAM, which the pysam-dependent gate
# would otherwise require.
AMPLICON_CHEMISTRY = {
    "chemistry": "amplicon",
    "depth_cnv_permitted": False,
    "deduplication_recommended": False,
    "primer_trimming_required": True,
}

HYBRID_CHEMISTRY = {
    "chemistry": "hybrid_capture",
    "depth_cnv_permitted": True,
    "deduplication_recommended": True,
    "primer_trimming_required": False,
}


def write_vcf(directory) -> str:
    """Write the synthetic VCF into `directory` and return its path."""
    from pathlib import Path

    path = Path(directory) / "synthetic_specimen.vcf"
    path.write_text(build_specimen()["vcf_text"])
    return str(path)


__all__ = [
    "build_specimen",
    "write_vcf",
    "AMPLICON_CHEMISTRY",
    "HYBRID_CHEMISTRY",
    "PURITY",
    "DRIVERS",
    "EXPECTED_DEVIATIONS",
    "EVENT_CHROM",
    "EVENT_DEVIATION",
    "CONCENTRATION",
]
