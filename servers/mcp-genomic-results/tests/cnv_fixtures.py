"""SYNTHETIC fixtures for the copy-number tests.

Everything in this module is generated, not observed. No patient data appears
here and none may be added: this repository holds synthetic data only.

The fixtures reproduce the STATISTICAL SIGNATURES that the tools must react to —
a paralogous block whose sites disagree on deviation magnitude, an amplicon
whose primer covers the locus, a region with a genuine shared shift — without
carrying anyone's actual allele counts. A test that needs a real specimen's
numbers is documented as such and skipped rather than smuggling them in.
"""

from __future__ import annotations

import numpy as np

# Every fixture is built from this seed, so failures are reproducible.
SEED = 20260825

# A chemistry verdict shaped like detect_library_chemistry's `value` payload.
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


def make_site(
    chrom: str,
    pos: int,
    block: str,
    deviation: float,
    depth: int,
    gene: str = "SYNTH",
    arm: str | None = None,
    sign: int = 1,
    **extra,
) -> dict:
    """One synthetic heterozygous site with an exact |BAF - 0.5| of `deviation`.

    Counts are computed rather than sampled so a fixture's statistics are
    deterministic and a test failure means the code changed, not the dice.
    """
    baf = 0.5 + sign * deviation
    alt = int(round(baf * depth))
    return {
        "chrom": chrom,
        "pos": pos,
        "arm": arm or f"{chrom}p",
        "block": block,
        "gene": gene,
        "rsid": f"rs{pos}",
        "ref_count": depth - alt,
        "alt_count": alt,
        "depth": depth,
        "baf": alt / depth,
        **extra,
    }


def concordant_block(
    chrom: str = "chr9",
    block: str = "chr9_blk001",
    start: int = 1_000_000,
    n_sites: int = 4,
    deviation: float = 0.0,
    depth: int = 2500,
    gene: str = "CONCORD",
) -> list[dict]:
    """A block whose sites agree on deviation magnitude, as a real event would.

    Signs alternate, because which parental allele the VCF calls ALT flips from
    site to site. Rule A must not care about that.
    """
    return [
        make_site(
            chrom,
            start + i * 10_000,
            block,
            deviation,
            depth,
            gene=gene,
            sign=1 if i % 2 == 0 else -1,
        )
        for i in range(n_sites)
    ]


def discordant_paralog_block(
    chrom: str = "chr1",
    block: str = "chr1_blk004",
    start: int = 120_400_000,
    depth: int = 2500,
    gene: str = "PARALOG",
) -> list[dict]:
    """A block reporting a mapping problem, not a copy-number event.

    Modelled on the segmental-duplication failure mode: reads from a paralogous
    copy collapse onto the captured target and drag BAF away from 0.5 by amounts
    that vary site to site. The deviations below span a wide range at high
    depth, which is exactly what within-block concordance is built to catch —
    under a real arm-level event every site here would have to show the SAME
    magnitude.

    Left untreated, a block like this produces a confident and entirely false
    arm-level loss call. If a refactor makes this block pass Rule A, the
    refactor is wrong.
    """
    deviations = [
        0.004,
        0.011,
        0.019,
        0.028,
        0.041,
        0.057,
        0.079,
        0.104,
        0.131,
        0.163,
        0.198,
        0.242,
    ]
    return [
        make_site(
            chrom,
            start + i * 15_000,
            block,
            dev,
            depth,
            gene=gene,
            sign=1 if i % 3 else -1,
        )
        for i, dev in enumerate(deviations)
    ]


def neutral_pool(
    n_blocks: int = 40,
    sites_per_block: int = 2,
    depth: int = 2500,
    concentration: float = 838.0,
    seed: int = SEED,
) -> list[dict]:
    """A copy-neutral pool with realistic beta-binomial overdispersion.

    Sampled from a beta-binomial rather than a binomial, because read counts
    from a real library are not independent trials and a binomial pool would
    give every downstream test a null that is far too tight.
    """
    rng = np.random.default_rng(seed)
    sites: list[dict] = []
    for b in range(n_blocks):
        chrom = f"chr{(b % 18) + 4}"  # keeps clear of the arms tests use
        block = f"{chrom}_pool{b:03d}"
        for i in range(sites_per_block):
            p = rng.beta(0.5 * concentration, 0.5 * concentration)
            alt = int(rng.binomial(depth, p))
            sites.append(
                {
                    "chrom": chrom,
                    "pos": 5_000_000 + b * 2_000_000 + i * 10_000,
                    "arm": f"{chrom}q",
                    "block": block,
                    "gene": f"POOL{b}",
                    "rsid": f"rs9{b:03d}{i}",
                    "ref_count": depth - alt,
                    "alt_count": alt,
                    "depth": depth,
                    "baf": alt / depth,
                }
            )
    return sites


def imbalanced_region(
    chrom: str = "chr3",
    n_blocks: int = 4,
    deviation: float = 0.0439,
    depth: int = 2500,
    arm: str = "chr3p",
) -> list[dict]:
    """A region carrying a genuine shared deviation across several blocks."""
    sites = []
    for b in range(n_blocks):
        sites.append(
            make_site(
                chrom,
                10_000_000 + b * 30_000_000,
                f"{chrom}_blk{b:03d}",
                deviation,
                depth,
                gene=f"GENE{b}",
                arm=arm,
                sign=1 if b % 2 == 0 else -1,
            )
        )
    return sites


def segmented_region(
    chrom: str = "chr3",
    proximal_deviation: float = 0.059,
    distal_deviation: float = 0.0,
    depth: int = 3000,
) -> list[dict]:
    """A region with a real breakpoint: two segments at different deviations.

    The distal segment deliberately rests on a SINGLE block, so the caution flag
    has something real to fire on.
    """
    sites = [
        make_site(
            chrom, 10_000_000, f"{chrom}_blk001", proximal_deviation, depth, gene="PROX1", sign=1
        ),
        make_site(
            chrom, 20_000_000, f"{chrom}_blk002", proximal_deviation, depth, gene="PROX2", sign=-1
        ),
        make_site(
            chrom, 30_000_000, f"{chrom}_blk003", proximal_deviation, depth, gene="PROX3", sign=1
        ),
        make_site(
            chrom, 150_000_000, f"{chrom}_blk009", distal_deviation, depth, gene="DIST1", sign=1
        ),
    ]
    return sites


def site_with_amplicons(
    per_amplicon: list[tuple[int, int]],
    chrom: str = "chr2",
    pos: int = 198_267_484,
    block: str = "chr2_blk001",
    gene: str = "AMPLI",
    under_primer_index: int | None = None,
) -> dict:
    """A site carrying per-amplicon counts, for Rules B and C.

    `per_amplicon` is a list of (alt_count, depth). `under_primer_index` marks
    one amplicon as primer-covered — the signature where a locus sits beneath a
    primer, the primer sequence replaces the template, and that amplicon can
    only ever report reference.
    """
    amplicons = []
    for i, (alt, depth) in enumerate(per_amplicon):
        amplicons.append(
            {
                "amplicon_start": 198_267_000 + i * 200,
                "amplicon_end": 198_267_300 + i * 200,
                "ref_count": depth - alt,
                "alt_count": alt,
                "depth": depth,
                "vaf": (alt / depth) if depth else None,
                "reads_under_primer": depth if i == under_primer_index else 0,
                "under_primer": i == under_primer_index,
            }
        )
    total_alt = sum(a["alt_count"] for a in amplicons if not a["under_primer"])
    total_depth = sum(a["depth"] for a in amplicons if not a["under_primer"])
    return {
        "chrom": chrom,
        "pos": pos,
        "arm": f"{chrom}q",
        "block": block,
        "gene": gene,
        "rsid": f"rs{pos}",
        "ref_count": total_depth - total_alt,
        "alt_count": total_alt,
        "depth": total_depth,
        "baf": (total_alt / total_depth) if total_depth else 0.5,
        "amplicons": amplicons,
    }


# Signal patterns for detect_library_chemistry's classifier. These are the four
# measurements the classifier votes on, not BAM contents.
AMPLICON_SIGNALS = {
    "duplicate_fraction": 0.930,
    "distinct_starts_per_1000_fwd": 18.6,
    "top10_start_fraction": 0.983,
    "median_insert": 109,
    "median_read_length": 115,
    "duplicate_flags_present": True,
    "reads_examined": 200_000,
    "primary_reads": 198_400,
}

HYBRID_SIGNALS = {
    "duplicate_fraction": 0.18,
    "distinct_starts_per_1000_fwd": 812.0,
    "top10_start_fraction": 0.04,
    "median_insert": 310,
    "median_read_length": 150,
    "duplicate_flags_present": True,
    "reads_examined": 200_000,
    "primary_reads": 199_100,
}

# Signals that disagree: high duplicate fraction (amplicon) alongside a wide
# insert distribution and many distinct starts (capture).
CONFLICTING_SIGNALS = {
    "duplicate_fraction": 0.88,
    "distinct_starts_per_1000_fwd": 640.0,
    "top10_start_fraction": 0.35,
    "median_insert": 300,
    "median_read_length": 150,
    "duplicate_flags_present": True,
    "reads_examined": 200_000,
    "primary_reads": 198_000,
}
