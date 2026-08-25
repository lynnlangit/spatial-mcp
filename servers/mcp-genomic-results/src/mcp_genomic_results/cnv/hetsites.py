"""Germline heterozygous site extraction from a tumour-only panel VCF.

Four design decisions, each arrived at by getting it wrong first
---------------------------------------------------------------

1. **Germline/somatic separation rests on dbSNP membership plus a purity
   argument, not a population-frequency cutoff.** At 16.6% purity a clonal
   heterozygous somatic variant tops out near BAF 0.083 and a clonal homozygous
   one near 0.166. Nothing somatic reaches a 0.20-0.80 window. Low purity is a
   problem for copy-number detection and a gift for germline/somatic
   separation. A population-AF range filter was tried and discarded: it removed
   three genuine high-depth heterozygous sites (1000G AF 0.009-0.024) on the two
   arms least able to spare them, and it buys nothing the purity argument does
   not already provide.

2. **The BAF window must be several times wider than any achievable deviation.**
   The largest deviation reachable at this purity is about 0.083 (copy-neutral
   LOH). Selecting sites on a window that could truncate real imbalance biases
   the statistic toward the null — the analysis would discard exactly the sites
   carrying the signal it is looking for.

3. **Haplotype blocks, not variant counts.** Panel capture is clumped: five
   chr3q sites sit inside a 100 kb window in one gene. They share a chromosome
   and move together, so they are ONE observation, not five. `n_sites` and
   `n_blocks` are emitted separately, always. Using the site count where the
   block count is meant overstates power by sqrt(sites / blocks).

4. **Primer trimming is mandatory for amplicon libraries.** A variant under a
   primer is invisible: the primer sequence replaces the template, so that
   amplicon reports reference only. Observed on SF3B1 R625C — one amplicon with
   342 reads and zero mutant reads. Uncorrected it drags the whole-sample VAF
   down, and since purity is estimated as 2 x VAF, every downstream inference
   inherits the error.
"""

from __future__ import annotations

import gzip
from collections import Counter
from dataclasses import asdict, dataclass, field
from typing import Any, Iterator

from .chemistry import require_chemistry

# hg19 centromere midpoints (UCSC gap table) — used only for p/q arm assignment.
CENTROMERE_HG19 = {
    "chr1": 125_000_000,
    "chr2": 93_300_000,
    "chr3": 91_000_000,
    "chr4": 50_400_000,
    "chr5": 48_400_000,
    "chr6": 61_000_000,
    "chr7": 59_900_000,
    "chr8": 45_600_000,
    "chr9": 49_000_000,
    "chr10": 40_200_000,
    "chr11": 53_700_000,
    "chr12": 35_800_000,
    "chr13": 17_900_000,
    "chr14": 17_600_000,
    "chr15": 19_000_000,
    "chr16": 36_600_000,
    "chr17": 24_000_000,
    "chr18": 17_200_000,
    "chr19": 26_500_000,
    "chr20": 27_500_000,
    "chr21": 13_200_000,
    "chr22": 14_700_000,
    "chrX": 60_600_000,
}

AUTOSOMES = [f"chr{i}" for i in range(1, 23)]

# Default primer length assumed when no primer BED is supplied. Amplicon
# primers in clinical panels run roughly 18-30 bp; 30 is the conservative end,
# because under-trimming leaves the reference-only artifact in place and that
# is the failure this exists to prevent.
DEFAULT_PRIMER_LENGTH_BP = 30

# Template endpoints are rounded to this resolution before being used as an
# amplicon identity, so that a few bases of end-repair jitter do not split one
# amplicon into several.
AMPLICON_ENDPOINT_ROUND_BP = 5


@dataclass
class Site:
    chrom: str
    pos: int
    arm: str
    ref: str
    alt: str
    rsid: str
    gene: str
    ref_count: int
    alt_count: int
    depth: int
    baf: float  # alt_count / (ref_count + alt_count)
    pop_af: float  # 1000G alternate allele frequency, or -1 if unknown
    filt: str
    block: str = ""  # haplotype block id, assigned after extraction
    source: str = "vcf"  # "vcf" or "bam_amplicon" once recounted
    amplicons: list[dict[str, Any]] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# VCF parsing
# --------------------------------------------------------------------------- #


def parse_info(info: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for entry in info.split(";"):
        if "=" in entry:
            k, v = entry.split("=", 1)
            out[k] = v
        else:
            out[entry] = True
    return out


def gene_from_csqt(info: dict[str, Any]) -> str:
    """First HGNC symbol in the Nirvana consequence field."""
    csqt = info.get("CSQT")
    if not csqt or csqt is True:
        return ""
    genes = []
    for tx in csqt.split(","):
        parts = tx.split("|")
        if len(parts) > 1 and parts[1]:
            genes.append(parts[1])
    return sorted(set(genes))[0] if genes else ""


def arm_of(chrom: str, pos: int) -> str:
    cen = CENTROMERE_HG19.get(chrom)
    if cen is None:
        return f"{chrom}?"
    return f"{chrom}{'p' if pos < cen else 'q'}"


def load_records(path: str) -> Iterator[tuple]:
    """Yield (chrom, pos, rsid, ref, alt, filt, info, format) for every record."""
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as fh:
        for line in fh:
            if line.startswith("#"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) < 10:
                continue
            chrom, pos, rsid, ref, alt, _qual, filt, info, fmt, sample = f[:10]
            yield (
                chrom,
                int(pos),
                rsid,
                ref,
                alt,
                filt,
                parse_info(info),
                dict(zip(fmt.split(":"), sample.split(":"))),
            )


def assign_blocks(sites: list[Site], window: int = 1_000_000) -> list[Site]:
    """Cluster sites into haplotype blocks by physical proximity.

    Sites within `window` bp on the same chromosome are treated as ONE
    independent observation. This is a deliberately conservative proxy for LD:
    without phased data the true block structure is unknown, and over-merging
    costs power while under-merging inflates significance. Losing power is the
    error worth preferring.
    """
    ordered = sorted(sites, key=lambda s: (s.chrom, s.pos))
    prev: Site | None = None
    idx = 0
    for s in ordered:
        if prev is None or s.chrom != prev.chrom or (s.pos - prev.pos) > window:
            idx += 1
        s.block = f"{s.chrom}_blk{idx:03d}"
        prev = s
    return ordered


# --------------------------------------------------------------------------- #
# Amplicon-aware allele counting with primer trimming
# --------------------------------------------------------------------------- #


def _amplicon_key(read, round_bp: int = AMPLICON_ENDPOINT_ROUND_BP) -> tuple[int, int] | None:
    """Amplicon identity = (leftmost, rightmost) template endpoints, rounded.

    An amplicon is defined by its primer pair, and the primer pair fixes the
    template's two ends. Reads from one amplicon therefore share endpoints up to
    a few bases of jitter, which the rounding absorbs.
    """
    if not read.is_proper_pair or not read.template_length:
        return None
    left = min(read.reference_start, read.next_reference_start)
    right = left + abs(read.template_length)
    return (left // round_bp * round_bp, right // round_bp * round_bp)


def count_amplicon_alleles(
    bam_path: str,
    chrom: str,
    pos: int,
    ref: str,
    alt: str,
    primer_length_bp: int = DEFAULT_PRIMER_LENGTH_BP,
    min_base_quality: int = 20,
) -> dict[str, Any]:
    """Count ref/alt reads at one locus, per amplicon, with primers trimmed.

    `pos` is 1-based (VCF convention). Reads whose amplicon places `pos` within
    `primer_length_bp` of either template end are excluded from that amplicon's
    counts, because at those offsets the primer sequence has replaced the
    template and the read can only ever report reference.

    Returns per-amplicon counts alongside the trimmed and untrimmed totals, so a
    caller can see exactly what trimming changed.
    """
    from .chemistry import _load_pysam

    pysam = _load_pysam()
    pos0 = pos - 1

    per_amplicon: dict[tuple[int, int], dict[str, Any]] = {}
    untrimmed_ref = untrimmed_alt = 0

    with pysam.AlignmentFile(bam_path, "rb") as bam:
        for column in bam.pileup(
            chrom,
            pos0,
            pos0 + 1,
            truncate=True,
            min_base_quality=min_base_quality,
            stepper="samtools",
        ):
            for read_column in column.pileups:
                if read_column.is_del or read_column.is_refskip:
                    continue
                read = read_column.alignment
                base = read.query_sequence[read_column.query_position]
                if base == ref:
                    which = "ref"
                elif base == alt:
                    which = "alt"
                else:
                    continue

                if which == "ref":
                    untrimmed_ref += 1
                else:
                    untrimmed_alt += 1

                key = _amplicon_key(read)
                if key is None:
                    continue
                left, right = key
                entry = per_amplicon.setdefault(
                    key,
                    {
                        "amplicon_start": left,
                        "amplicon_end": right,
                        "ref_count": 0,
                        "alt_count": 0,
                        "reads_under_primer": 0,
                        "under_primer": False,
                    },
                )
                # The primer trim. Both ends, because either primer can cover
                # the locus depending on which side the amplicon starts.
                if (pos0 - left) < primer_length_bp or (right - pos0) <= primer_length_bp:
                    entry["reads_under_primer"] += 1
                    entry["under_primer"] = True
                    continue
                entry[f"{which}_count"] += 1

    amplicons = []
    for entry in sorted(per_amplicon.values(), key=lambda e: e["amplicon_start"]):
        depth = entry["ref_count"] + entry["alt_count"]
        entry["depth"] = depth
        entry["vaf"] = (entry["alt_count"] / depth) if depth else None
        amplicons.append(entry)

    kept = [a for a in amplicons if not a["under_primer"]]
    ref_count = sum(a["ref_count"] for a in kept)
    alt_count = sum(a["alt_count"] for a in kept)
    depth = ref_count + alt_count
    untrimmed_depth = untrimmed_ref + untrimmed_alt

    return {
        "chrom": chrom,
        "pos": pos,
        "ref_count": ref_count,
        "alt_count": alt_count,
        "depth": depth,
        "vaf": (alt_count / depth) if depth else None,
        "amplicons": amplicons,
        "n_amplicons": len(amplicons),
        "n_amplicons_dropped_to_primer": sum(1 for a in amplicons if a["under_primer"]),
        "untrimmed_depth": untrimmed_depth,
        "untrimmed_vaf": (untrimmed_alt / untrimmed_depth) if untrimmed_depth else None,
    }


# --------------------------------------------------------------------------- #
# Extraction
# --------------------------------------------------------------------------- #


def extract_sites(
    vcf_path: str,
    chemistry: dict,
    bam_path: str | None = None,
    min_depth: int = 200,
    baf_window: tuple[float, float] = (0.20, 0.80),
    block_window_bp: int = 1_000_000,
    purity_hint: float | None = None,
    primer_length_bp: int = DEFAULT_PRIMER_LENGTH_BP,
    include_chrx: bool = False,
) -> dict[str, Any]:
    """Extract informative germline heterozygous sites and group them into blocks."""
    require_chemistry(chemistry, "extract_heterozygous_sites")

    warnings: list[str] = []

    # The purity check. A germline window is only safe if nothing somatic can
    # reach it. A clonal HOMOZYGOUS somatic variant reaches BAF ~= purity, which
    # is the true ceiling; the spec's 2x margin over that ceiling is the check
    # applied here, so a thin margin is reported rather than assumed away.
    if purity_hint is not None:
        somatic_ceiling = purity_hint
        if baf_window[0] <= 2 * purity_hint:
            warnings.append(
                f"BAF window floor {baf_window[0]:.3f} does not clear 2 x purity "
                f"({2 * purity_hint:.3f}). The hard ceiling for a clonal homozygous "
                f"somatic variant is BAF {somatic_ceiling:.3f}, so the window is still "
                f"germline-only, but the safety margin is "
                f"{baf_window[0] / somatic_ceiling:.2f}x rather than 2x."
            )

    reasons = Counter()
    position_record_counts: Counter[tuple[str, int]] = Counter()
    staged: list[Site] = []
    # Every PASS biallelic SNV carrying an rs ID, counted before the depth,
    # BAF-window and multi-allelic filters. This is the denominator a caller
    # should quote when reporting how many candidates survived.
    n_candidates = 0

    for chrom, pos, rsid, ref, alt, filt, info, fmt in load_records(vcf_path):
        position_record_counts[(chrom, pos)] += 1

        if len(ref) != 1 or len(alt) != 1 or alt in (".", "<M>"):
            reasons["not_snv"] += 1
            continue
        if filt != "PASS":
            reasons["not_pass"] += 1
            continue
        if not include_chrx and chrom not in AUTOSOMES:
            reasons["non_autosome"] += 1
            continue

        # dbSNP membership is the germline evidence. No population-frequency
        # cutoff is applied — see design decision 1 in the module docstring.
        if not rsid.startswith("rs"):
            reasons["no_dbsnp_evidence"] += 1
            continue

        n_candidates += 1

        pop_af = -1.0
        raw_af = info.get("AF1000G")
        if raw_af and raw_af is not True:
            try:
                pop_af = float(str(raw_af).split(",")[0])
            except ValueError:
                pop_af = -1.0

        ad = fmt.get("AD", "")
        parts = [p for p in str(ad).split(",") if p != ""]
        if len(parts) != 2:
            reasons["bad_ad"] += 1
            continue
        # Counts come from AD (integers), not VF (rounded to 4dp). Binomial and
        # beta-binomial statistics need exact counts, not a reconstructed ratio.
        ref_count, alt_count = int(parts[0]), int(parts[1])
        depth = ref_count + alt_count
        if depth < min_depth:
            reasons["low_depth"] += 1
            continue

        baf = alt_count / depth
        if not (baf_window[0] <= baf <= baf_window[1]):
            reasons["baf_out_of_window"] += 1
            continue

        staged.append(
            Site(
                chrom=chrom,
                pos=pos,
                arm=arm_of(chrom, pos),
                ref=ref,
                alt=alt,
                rsid=rsid,
                gene=gene_from_csqt(info),
                ref_count=ref_count,
                alt_count=alt_count,
                depth=depth,
                baf=baf,
                pop_af=pop_af,
                filt=filt,
            )
        )

    # Multi-allelic records are split into separate rows by callers such as
    # Pisces (-CrushVcf False), so a position can appear more than once. A second
    # alt allele at the same locus makes BAF uninterpretable.
    sites: list[Site] = []
    for s in staged:
        if position_record_counts[(s.chrom, s.pos)] > 1:
            reasons["multiallelic_locus"] += 1
            continue
        sites.append(s)

    # BAM recount, when available. This is where primer trimming happens, and it
    # is the whole reason bam_path exists as a parameter.
    recount_summary: dict[str, Any] = {"performed": False}
    if bam_path:
        recount_summary = _recount_from_bam(
            sites, bam_path, chemistry, primer_length_bp, min_depth, baf_window, reasons
        )
        sites = recount_summary.pop("sites")

    sites = assign_blocks(sites, window=block_window_bp)
    blocks = {s.block for s in sites}

    per_chrom: dict[str, dict[str, int]] = {}
    per_arm: dict[str, dict[str, int]] = {}
    for s in sites:
        c = per_chrom.setdefault(s.chrom, {"n_sites": 0, "blocks": set()})
        c["n_sites"] += 1
        c["blocks"].add(s.block)
        a = per_arm.setdefault(s.arm, {"n_sites": 0, "blocks": set()})
        a["n_sites"] += 1
        a["blocks"].add(s.block)

    return {
        "sites": [asdict(s) for s in sites],
        "n_sites": len(sites),
        "n_blocks": len(blocks),
        "n_dbsnp_snv_candidates": n_candidates,
        "rejections": dict(reasons),
        "per_chromosome": {
            k: {"n_sites": v["n_sites"], "n_blocks": len(v["blocks"])}
            for k, v in sorted(per_chrom.items())
        },
        "per_arm": {
            k: {"n_sites": v["n_sites"], "n_blocks": len(v["blocks"])}
            for k, v in sorted(per_arm.items())
        },
        "bam_recount": recount_summary,
        "warnings": warnings,
        "parameters": {
            "min_depth": min_depth,
            "baf_window": list(baf_window),
            "block_window_bp": block_window_bp,
            "purity_hint": purity_hint,
            "primer_length_bp": primer_length_bp if bam_path else None,
        },
    }


def _recount_from_bam(
    sites: list[Site],
    bam_path: str,
    chemistry: dict,
    primer_length_bp: int,
    min_depth: int,
    baf_window: tuple[float, float],
    reasons: Counter,
) -> dict[str, Any]:
    """Replace VCF allele counts with amplicon-aware, primer-trimmed counts."""
    is_amplicon = chemistry["chemistry"] == "amplicon"
    trim = primer_length_bp if chemistry["primer_trimming_required"] else 0

    kept: list[Site] = []
    n_changed = 0
    n_primer_dropped = 0
    for s in sites:
        counts = count_amplicon_alleles(
            bam_path, s.chrom, s.pos, s.ref, s.alt, primer_length_bp=trim
        )
        if counts["depth"] < min_depth:
            reasons["low_depth_after_primer_trim"] += 1
            continue
        baf = counts["alt_count"] / counts["depth"]
        if not (baf_window[0] <= baf <= baf_window[1]):
            reasons["baf_out_of_window_after_recount"] += 1
            continue
        if counts["ref_count"] != s.ref_count or counts["alt_count"] != s.alt_count:
            n_changed += 1
        n_primer_dropped += counts["n_amplicons_dropped_to_primer"]
        s.ref_count = counts["ref_count"]
        s.alt_count = counts["alt_count"]
        s.depth = counts["depth"]
        s.baf = baf
        s.source = "bam_amplicon" if is_amplicon else "bam"
        s.amplicons = counts["amplicons"]
        kept.append(s)

    return {
        "performed": True,
        "sites": kept,
        "primer_trimming_applied": trim > 0,
        "primer_length_bp": trim,
        "sites_with_changed_counts": n_changed,
        "amplicons_dropped_to_primer_overlap": n_primer_dropped,
        "note": (
            "Counts recomputed per amplicon with primers trimmed. An amplicon whose "
            "primer covers the locus reports reference only and is excluded rather "
            "than diluting the VAF."
            if trim
            else "Counts recomputed from the BAM; chemistry does not require primer trimming."
        ),
    }
