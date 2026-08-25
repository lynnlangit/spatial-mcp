"""Library chemistry detection — the gate every copy-number tool depends on.

Why this is a gate and not advice
---------------------------------
The 2022 panel that prompted this module is amplicon-based. Per-amplicon read
depth on an amplicon library reflects PCR amplification efficiency, not input
copy number, so depth-ratio CNV on such a specimen is meaningless. Nothing in
the platform stopped anyone running it. The specimen record even said
"PCR-amplified fragment library" — it was knowable, and no tool checked.

So this verdict is a REQUIRED input to every CNV tool in this package. A tool
that would produce an invalid result refuses to run rather than producing it
with a caveat attached.

Two consequences of an amplicon verdict are easy to get backwards:

  * `deduplication_recommended` is FALSE. `samtools markdup` flags ~93% of
    reads on such a specimen. Removing them destroys the data. Amplicon reads
    sharing a start coordinate are independent molecules, not PCR duplicates —
    they share a start because they share a primer.

  * `primer_trimming_required` is TRUE. A variant sitting under a primer is
    invisible: the primer sequence replaces the template, so that amplicon
    reports reference only.
"""

from __future__ import annotations

import os
from collections import Counter
from typing import Any

# Signal thresholds from CNV_TOOLS_SPEC.md section 2. The gaps between the
# amplicon and hybrid-capture bands are deliberate: a value that falls in the
# gap abstains rather than guessing, and enough abstentions produce
# NOT_ASSESSABLE.
DUP_FRACTION_AMPLICON_MIN = 0.70
DUP_FRACTION_HYBRID_MAX = 0.30
DISTINCT_STARTS_AMPLICON_MAX = 50.0
DISTINCT_STARTS_HYBRID_MIN = 500.0
TOP10_FRACTION_AMPLICON_MIN = 0.60
TOP10_FRACTION_HYBRID_MAX = 0.10
# Amplicon mates overlap, so the insert is no longer than one read. Hybrid
# capture inserts run well past read length; 1.5x keeps a band of abstention
# between the two rather than splitting on a hairline.
INSERT_HYBRID_MULTIPLE = 1.5

# A verdict needs at least this many signals agreeing, with none dissenting.
MIN_CONCORDANT_SIGNALS = 3

DEFAULT_MAX_READS = 200_000


class PysamUnavailable(RuntimeError):
    """Raised when BAM inspection is requested but pysam is not installed."""


def _load_pysam():
    try:
        import pysam  # noqa: PLC0415 — optional dependency, imported on demand
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise PysamUnavailable(
            "pysam is required to inspect a BAM. Install the optional extra: "
            "`uv sync --extra bam` in servers/mcp-genomic-results."
        ) from exc
    return pysam


# --------------------------------------------------------------------------- #
# Signal extraction
# --------------------------------------------------------------------------- #


def scan_bam_signals(
    bam_path: str,
    sample_region: str | None = None,
    max_reads: int = DEFAULT_MAX_READS,
) -> dict[str, Any]:
    """Collect the four chemistry signals from a BAM.

    Reads are sampled from the densest mapped contigs rather than scanned
    end to end — the signals are properties of the library preparation and are
    stable across any region with enough coverage to measure them.
    """
    if not os.path.exists(bam_path):
        raise FileNotFoundError(f"BAM not found: {bam_path}")

    pysam = _load_pysam()

    n_reads = 0
    n_primary = 0
    n_dup_flagged = 0
    fwd_starts: Counter[tuple[str, int]] = Counter()
    n_fwd = 0
    insert_sizes: list[int] = []
    read_lengths: list[int] = []

    with pysam.AlignmentFile(bam_path, "rb") as bam:
        if sample_region:
            regions = [sample_region]
        else:
            regions = _dense_regions(bam)

        for region in regions:
            if n_reads >= max_reads:
                break
            try:
                iterator = bam.fetch(region=region) if region else bam.fetch(until_eof=True)
            except ValueError:
                # No index, or a contig name the header does not carry.
                iterator = bam.fetch(until_eof=True)

            for read in iterator:
                if n_reads >= max_reads:
                    break
                n_reads += 1
                if read.is_unmapped or read.is_secondary or read.is_supplementary:
                    continue
                n_primary += 1
                if read.is_duplicate:
                    n_dup_flagged += 1
                if read.query_length:
                    read_lengths.append(read.query_length)
                if not read.is_reverse:
                    n_fwd += 1
                    fwd_starts[(read.reference_name, read.reference_start)] += 1
                if read.is_proper_pair and read.template_length:
                    insert_sizes.append(abs(read.template_length))

    if n_primary == 0:
        raise ValueError(f"no primary aligned reads found in {bam_path}")

    top10 = sum(count for _, count in fwd_starts.most_common(10))
    return {
        "reads_examined": n_reads,
        "primary_reads": n_primary,
        "duplicate_flagged_reads": n_dup_flagged,
        "duplicate_fraction": n_dup_flagged / n_primary,
        "forward_reads": n_fwd,
        "distinct_start_positions": len(fwd_starts),
        "distinct_starts_per_1000_fwd": (
            (len(fwd_starts) / n_fwd * 1000.0) if n_fwd else float("nan")
        ),
        "top10_start_fraction": (top10 / n_fwd) if n_fwd else float("nan"),
        "median_insert": _median(insert_sizes),
        "median_read_length": _median(read_lengths),
        "duplicate_flags_present": n_dup_flagged > 0,
    }


def _dense_regions(bam, n_regions: int = 3) -> list[str]:
    """Pick the most densely mapped contigs, or fall back to a full pass."""
    try:
        stats = bam.get_index_statistics()
    except (ValueError, AttributeError):
        return [""]  # no index — caller falls back to until_eof
    ranked = sorted(stats, key=lambda s: s.mapped, reverse=True)
    return [s.contig for s in ranked[:n_regions] if s.mapped > 0] or [""]


def _median(values: list[int]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


# --------------------------------------------------------------------------- #
# Classification — pure, so it is testable without a BAM
# --------------------------------------------------------------------------- #


def classify_signals(evidence: dict[str, Any]) -> dict[str, Any]:
    """Turn raw signals into a chemistry verdict plus a per-signal vote record.

    Each signal votes "amplicon", "hybrid_capture", or abstains. A verdict needs
    MIN_CONCORDANT_SIGNALS agreeing with zero dissent; anything else is
    indeterminate, which the caller must surface as NOT_ASSESSABLE.
    """
    votes: dict[str, dict[str, Any]] = {}

    dup = evidence.get("duplicate_fraction")
    if not evidence.get("duplicate_flags_present", True):
        # No read carries the duplicate flag. That is not evidence of a
        # low-duplication library; it is evidence that nothing ever marked
        # duplicates. Voting "hybrid_capture" here would be reading an absent
        # annotation as a measurement.
        votes["duplicate_fraction"] = _vote(
            None, dup, "no duplicate flags present in the BAM; library was never marked"
        )
    elif dup is None:
        votes["duplicate_fraction"] = _vote(None, dup, "not measured")
    elif dup >= DUP_FRACTION_AMPLICON_MIN:
        votes["duplicate_fraction"] = _vote("amplicon", dup, f">= {DUP_FRACTION_AMPLICON_MIN}")
    elif dup <= DUP_FRACTION_HYBRID_MAX:
        votes["duplicate_fraction"] = _vote("hybrid_capture", dup, f"<= {DUP_FRACTION_HYBRID_MAX}")
    else:
        votes["duplicate_fraction"] = _vote(
            None, dup, f"between {DUP_FRACTION_HYBRID_MAX} and {DUP_FRACTION_AMPLICON_MIN}"
        )

    starts = evidence.get("distinct_starts_per_1000_fwd")
    if starts is None or starts != starts:  # NaN check
        votes["distinct_starts_per_1000_fwd"] = _vote(None, starts, "not measured")
    elif starts < DISTINCT_STARTS_AMPLICON_MAX:
        votes["distinct_starts_per_1000_fwd"] = _vote(
            "amplicon", starts, f"< {DISTINCT_STARTS_AMPLICON_MAX}"
        )
    elif starts > DISTINCT_STARTS_HYBRID_MIN:
        votes["distinct_starts_per_1000_fwd"] = _vote(
            "hybrid_capture", starts, f"> {DISTINCT_STARTS_HYBRID_MIN}"
        )
    else:
        votes["distinct_starts_per_1000_fwd"] = _vote(
            None, starts, f"between {DISTINCT_STARTS_AMPLICON_MAX} and {DISTINCT_STARTS_HYBRID_MIN}"
        )

    top10 = evidence.get("top10_start_fraction")
    if top10 is None or top10 != top10:
        votes["top10_start_fraction"] = _vote(None, top10, "not measured")
    elif top10 > TOP10_FRACTION_AMPLICON_MIN:
        votes["top10_start_fraction"] = _vote("amplicon", top10, f"> {TOP10_FRACTION_AMPLICON_MIN}")
    elif top10 < TOP10_FRACTION_HYBRID_MAX:
        votes["top10_start_fraction"] = _vote(
            "hybrid_capture", top10, f"< {TOP10_FRACTION_HYBRID_MAX}"
        )
    else:
        votes["top10_start_fraction"] = _vote(
            None, top10, f"between {TOP10_FRACTION_HYBRID_MAX} and {TOP10_FRACTION_AMPLICON_MIN}"
        )

    insert = evidence.get("median_insert")
    read_len = evidence.get("median_read_length")
    if not insert or not read_len:
        votes["insert_vs_read_length"] = _vote(None, None, "not measured")
    elif insert <= read_len:
        votes["insert_vs_read_length"] = _vote(
            "amplicon", insert / read_len, "insert <= read length; mates overlap"
        )
    elif insert > INSERT_HYBRID_MULTIPLE * read_len:
        votes["insert_vs_read_length"] = _vote(
            "hybrid_capture", insert / read_len, f"insert > {INSERT_HYBRID_MULTIPLE}x read length"
        )
    else:
        votes["insert_vs_read_length"] = _vote(
            None, insert / read_len, "insert between 1x and 1.5x read length"
        )

    tally = Counter(v["vote"] for v in votes.values() if v["vote"])
    n_amplicon = tally.get("amplicon", 0)
    n_hybrid = tally.get("hybrid_capture", 0)

    if n_amplicon >= MIN_CONCORDANT_SIGNALS and n_hybrid == 0:
        chemistry = "amplicon"
    elif n_hybrid >= MIN_CONCORDANT_SIGNALS and n_amplicon == 0:
        chemistry = "hybrid_capture"
    else:
        chemistry = "indeterminate"

    return {
        "chemistry": chemistry,
        "votes": votes,
        "n_amplicon_votes": n_amplicon,
        "n_hybrid_votes": n_hybrid,
        "n_abstentions": sum(1 for v in votes.values() if v["vote"] is None),
    }


def _vote(vote: str | None, observed: Any, reason: str) -> dict[str, Any]:
    return {"vote": vote, "observed": observed, "reason": reason}


def chemistry_flags(chemistry: str) -> dict[str, bool]:
    """The three downstream consequences of a chemistry verdict.

    An amplicon library forbids depth-ratio CNV, forbids deduplication, and
    requires primer trimming. Getting the middle one backwards throws away 93%
    of the reads on a real specimen.
    """
    if chemistry == "amplicon":
        return {
            "depth_cnv_permitted": False,
            "deduplication_recommended": False,
            "primer_trimming_required": True,
        }
    if chemistry == "hybrid_capture":
        return {
            "depth_cnv_permitted": True,
            "deduplication_recommended": True,
            "primer_trimming_required": False,
        }
    raise ValueError(f"no flags defined for chemistry={chemistry!r}")


# --------------------------------------------------------------------------- #
# Chemistry payload validation — what every downstream CNV tool calls first
# --------------------------------------------------------------------------- #

REQUIRED_CHEMISTRY_KEYS = (
    "chemistry",
    "depth_cnv_permitted",
    "deduplication_recommended",
    "primer_trimming_required",
)


class ChemistryGateError(ValueError):
    """A CNV tool was called without a usable chemistry verdict."""


def require_chemistry(chemistry: dict | None, tool: str) -> dict:
    """Validate the chemistry payload a CNV tool was handed.

    Raises rather than defaulting. A default here would reintroduce exactly the
    failure this gate exists to prevent: an analysis proceeding on an unstated
    assumption about the library.
    """
    if not chemistry:
        raise ChemistryGateError(
            f"{tool} requires the `chemistry` payload from detect_library_chemistry. "
            "Copy-number inference is invalid without knowing the library preparation, "
            "and this tool will not assume one."
        )
    missing = [k for k in REQUIRED_CHEMISTRY_KEYS if k not in chemistry]
    if missing:
        raise ChemistryGateError(
            f"{tool} received an incomplete chemistry payload; missing {missing}. "
            "Pass the `value` payload of detect_library_chemistry unmodified."
        )
    if chemistry["chemistry"] not in ("amplicon", "hybrid_capture"):
        raise ChemistryGateError(
            f"{tool} cannot run on chemistry={chemistry['chemistry']!r}. "
            "detect_library_chemistry did not reach a verdict, so no copy-number "
            "tool may proceed."
        )
    return chemistry
