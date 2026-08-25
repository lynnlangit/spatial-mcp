"""Tumour purity from clonal driver VAFs.

For a clonal heterozygous somatic SNV at a copy-neutral locus, the tumour cells
carry one mutant allele in two, and the normal cells carry none. So

    VAF = purity / 2      and therefore      purity = 2 x VAF

That is a short derivation resting on three assumptions, and the number is
worthless without them. They are emitted with every result, every time:

  1. the variant is clonal (present in every tumour cell)
  2. the variant is heterozygous (one mutant allele per tumour genome)
  3. its locus is copy-neutral (two total copies in the tumour)

Assumption 3 is the one this module can actually check, because the allelic
imbalance tools produce per-chromosome copy-neutral verdicts. When the driver's
chromosome has NOT been verified copy-neutral, the grade drops from HIGH to
MODERATE and the limit is stated explicitly rather than left implied.

Purity scales every downstream inference — expected deviation under every
copy-number event is linear in it — so an unnoticed error here propagates
everywhere without ever looking like an error.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

from scipy import stats


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    Wilson rather than Wald: at the allele fractions involved here (VAF ~0.08)
    a Wald interval is noticeably asymmetric-in-the-wrong-direction and can run
    below zero.
    """
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, centre - half), min(1.0, centre + half))


def _purity_from_vaf(vaf: float, zygosity: str) -> float:
    """Convert an allele fraction to purity given the assumed driver zygosity."""
    if zygosity == "heterozygous":
        return min(1.0, 2.0 * vaf)
    if zygosity == "homozygous":
        # A homozygous somatic variant contributes two mutant alleles per tumour
        # genome, so the allele fraction already equals purity.
        return min(1.0, vaf)
    raise ValueError(f"assumed_zygosity must be 'heterozygous' or 'homozygous', got {zygosity!r}")


def two_proportion_p(k1: int, n1: int, k2: int, n2: int) -> float:
    """Two-sided two-proportion z test.

    Applied between drivers to ask whether they are consistent with a single
    truncal clone. A significant difference would mean at least one driver is
    subclonal or sits on non-neutral ground, and the combined estimate would be
    averaging two different quantities.
    """
    if n1 == 0 or n2 == 0:
        return float("nan")
    p_pool = (k1 + k2) / (n1 + n2)
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return 1.0
    z = (k1 / n1 - k2 / n2) / se
    return float(2 * stats.norm.sf(abs(z)))


def estimate_purity(
    drivers: Sequence[dict],
    copy_neutral_evidence: dict | None = None,
) -> dict[str, Any]:
    """Estimate tumour purity from one or more clonal driver observations.

    Each driver is a dict with keys: label, alt_count, depth, chrom, and
    optionally assumed_zygosity (default "heterozygous").
    """
    if not drivers:
        raise ValueError("estimate_tumor_purity requires at least one driver observation")

    evidence = copy_neutral_evidence or {}
    rows: list[dict[str, Any]] = []
    unverified: list[str] = []
    verified: list[str] = []

    for d in drivers:
        label = d.get("label", "unlabelled")
        alt = int(d["alt_count"])
        depth = int(d["depth"])
        if depth <= 0:
            raise ValueError(f"driver {label!r} has depth {depth}; cannot form a VAF")
        if alt > depth:
            raise ValueError(f"driver {label!r} has alt_count {alt} > depth {depth}")
        chrom = d.get("chrom", "")
        zygosity = d.get("assumed_zygosity", "heterozygous")

        vaf = alt / depth
        lo, hi = wilson_ci(alt, depth)
        status = _copy_neutral_status(chrom, evidence)
        (verified if status == "verified_copy_neutral" else unverified).append(
            f"{label} ({chrom or 'chromosome unknown'})"
        )

        rows.append(
            {
                "driver": label,
                "chrom": chrom,
                "alt_count": alt,
                "depth": depth,
                "vaf": vaf,
                "assumed_zygosity": zygosity,
                "purity": _purity_from_vaf(vaf, zygosity),
                "purity_ci95": [_purity_from_vaf(lo, zygosity), _purity_from_vaf(hi, zygosity)],
                "copy_neutral_status": status,
            }
        )

    # Combining on the pooled-count scale rather than averaging the per-driver
    # purities: the pooled estimate is the inverse-variance-weighted one, and it
    # gives an interval directly rather than needing the intervals recombined.
    zygosities = {r["assumed_zygosity"] for r in rows}
    if len(zygosities) > 1:
        raise ValueError(
            "cannot pool drivers with different assumed zygosities "
            f"({sorted(zygosities)}); estimate each separately"
        )
    zygosity = rows[0]["assumed_zygosity"]
    total_alt = sum(r["alt_count"] for r in rows)
    total_depth = sum(r["depth"] for r in rows)
    pooled_vaf = total_alt / total_depth
    lo, hi = wilson_ci(total_alt, total_depth)

    pairwise: list[dict[str, Any]] = []
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            a, b = rows[i], rows[j]
            p = two_proportion_p(
                a["alt_count"], a["depth"], b["alt_count"], b["depth"]
            )
            pairwise.append(
                {
                    "drivers": [a["driver"], b["driver"]],
                    "p": p,
                    "interpretation": (
                        "consistent with both truncal"
                        if p >= 0.05
                        else "VAFs differ; at least one driver is subclonal or sits "
                        "on non-neutral ground"
                    ),
                }
            )

    return {
        "purity": _purity_from_vaf(pooled_vaf, zygosity),
        "purity_ci95": [_purity_from_vaf(lo, zygosity), _purity_from_vaf(hi, zygosity)],
        "pooled_vaf": pooled_vaf,
        "total_alt_count": total_alt,
        "total_depth": total_depth,
        "per_driver": rows,
        "pairwise_consistency": pairwise,
        "copy_neutral_verified": verified,
        "copy_neutral_unverified": unverified,
        "all_loci_verified_copy_neutral": not unverified,
    }


def _copy_neutral_status(chrom: str, evidence: dict) -> str:
    """Read a per-chromosome copy-neutral verdict out of the imbalance evidence.

    Recognised shapes, in order of preference:
      {"chr2": {"copy_neutral": True, ...}}
      {"chr2": {"imbalance": 0.0, "monosomy_excluded": True, ...}}
      {"chr2": True}
    Anything unrecognised is treated as unverified. Silence is not confirmation.
    """
    if not chrom:
        return "chromosome_not_stated"
    entry = evidence.get(chrom)
    if entry is None:
        return "not_assessed"
    if isinstance(entry, bool):
        return "verified_copy_neutral" if entry else "not_copy_neutral"
    if isinstance(entry, dict):
        if "copy_neutral" in entry:
            return "verified_copy_neutral" if entry["copy_neutral"] else "not_copy_neutral"
        n_blocks = entry.get("n_blocks")
        if n_blocks is not None and n_blocks < 3:
            # Two informative loci cannot establish that a chromosome is
            # copy-neutral; they can only fail to show that it is not.
            return "insufficient_loci"
        if entry.get("monosomy_excluded") is True:
            return "verified_copy_neutral"
        return "not_copy_neutral" if entry.get("imbalance", 0) > 0 else "insufficient_evidence"
    return "not_assessed"
