"""Could we even have seen this effect? — power analysis for allelic imbalance.

This module exists because of a failure this platform has already produced: a
pathway score of 0.61 with "consider checkpoint inhibitor combination therapy"
attached, assembled almost entirely from tool defaults with no patient-specific
evidence behind it. A number with no power context is unreadable — a null result
from an underpowered test and a null result from a well-powered one mean
opposite things, and nothing on the page distinguishes them.

So detectability is computed BEFORE the test and embedded IN the test result.

Two things here are easy to get wrong and expensive to get wrong:

**The standard error uses the BLOCK count, not the site count.** Five sites
inside one gene are one observation. Dividing by sqrt(sites) instead of
sqrt(blocks) overstates power by sqrt(sites / blocks) — 1.5x on chr3 in the
specimen that motivated this, 1.7x on chr8q.

**Depth has a ceiling.** Per-site variance is 0.25 * (1 + (n-1)/(s+1)) / n,
which approaches 0.25 / (s + 1) as depth grows. No amount of sequencing crosses
that asymptote. A binomial model predicts 4x the reads halves the SD; the real
answer at s = 742 is a 1.23x improvement. Any recommendation to sequence deeper
has to say what the extra depth actually buys, or it is selling something.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .stats import (
    binomial_sd,
    depth_scaling_ceiling,
    expected_deviations,
    group_by_block,
    per_site_sd,
)

# z for a two-sided 95% interval; the minimum detectable effect is quoted at
# 80% power, the convention a clinician reading a power statement expects.
Z_ALPHA = 1.96
Z_POWER = 0.84


def assess_detectability(
    purity: float,
    region_sites: Sequence[dict],
    overdispersion_s: float,
    chemistry: dict,
    lane_multiples: Sequence[int] = (1, 4),
) -> dict[str, Any]:
    """Power analysis for detecting allelic imbalance in one region."""
    from .chemistry import require_chemistry

    require_chemistry(chemistry, "assess_cnv_detectability")

    if not region_sites:
        return {
            "measurable": False,
            "reason": "no sites in the region",
            "n_sites": 0,
            "n_blocks": 0,
        }

    blocks = group_by_block(region_sites)
    n_sites = len(region_sites)
    n_blocks = len(blocks)
    median_depth = float(np.median([s["depth"] for s in region_sites]))

    sd_site = per_site_sd(median_depth, overdispersion_s)
    sd_binomial = binomial_sd(median_depth)

    # THE line that matters: blocks, not sites.
    se = sd_site / np.sqrt(n_blocks)
    mde = float((Z_ALPHA + Z_POWER) * se)

    expected = expected_deviations(purity)
    detectable = {
        event: {
            "expected_deviation": dev,
            "detectable_at_80pct_power": bool(dev >= mde),
            "effect_over_se": float(dev / se) if se else float("inf"),
        }
        for event, dev in expected.items()
    }

    # What extra sequencing would actually buy, against the asymptote.
    ceiling = depth_scaling_ceiling(overdispersion_s)
    depth_scaling = []
    base_sd = None
    for mult in lane_multiples:
        depth = median_depth * mult
        sd = per_site_sd(depth, overdispersion_s)
        if base_sd is None:
            base_sd = sd
        depth_scaling.append(
            {
                "lane_multiple": mult,
                "median_depth": depth,
                "per_site_sd": sd,
                "improvement_over_current": float(base_sd / sd) if sd else None,
                "binomial_would_predict": float(np.sqrt(mult)),
            }
        )
    depth_scaling.append(
        {
            "lane_multiple": None,
            "median_depth": "infinite",
            "per_site_sd": ceiling,
            "improvement_over_current": float(base_sd / ceiling) if ceiling else None,
            "binomial_would_predict": None,
        }
    )

    # Separating the two events that matter clinically is a harder problem than
    # detecting either: they sit close together and the gap does not widen with
    # depth the way the effects themselves might suggest.
    gap = abs(expected["single_copy_loss"] - expected["single_copy_gain"])
    quadruple_gain = sd_site / per_site_sd(median_depth * 4, overdispersion_s)

    return {
        "measurable": any(v["detectable_at_80pct_power"] for v in detectable.values()),
        "purity": purity,
        "n_sites": n_sites,
        "n_blocks": n_blocks,
        "unit_type": "haplotype_block",
        "median_depth": median_depth,
        "overdispersion_s": overdispersion_s,
        "per_site_sd": sd_site,
        "binomial_sd": sd_binomial,
        "noise_vs_binomial": sd_site / sd_binomial,
        "standard_error": float(se),
        "min_detectable_effect": mde,
        "expected_deviation_by_event": expected,
        "detectability_by_event": detectable,
        "loss_gain_separation": {
            "gap": gap,
            "se": float(se),
            "separable_by_baf": bool(gap >= mde),
            "note": (
                f"Single-copy loss ({expected['single_copy_loss']:.4f}) and single-copy gain "
                f"({expected['single_copy_gain']:.4f}) differ by {gap:.4f}, against a standard "
                f"error of {se:.4f}. BAF magnitude cannot separate them; only depth evidence can, "
                f"and chemistry={chemistry['chemistry']} "
                f"{'permits' if chemistry['depth_cnv_permitted'] else 'does not permit'} "
                "depth-based copy-number inference."
            ),
        },
        "depth_scaling": depth_scaling,
        "depth_scaling_ceiling": ceiling,
        "depth_note": (
            f"Per-site variance approaches 0.25 / (s + 1) as depth grows, so SD cannot fall "
            f"below {ceiling:.4f} at s = {overdispersion_s:.0f} no matter how deep the "
            f"sequencing. Quadrupling depth from {median_depth:.0f} to {median_depth * 4:.0f} "
            f"improves SD by {quadruple_gain:.2f}x, "
            "not the 2x a binomial model predicts. Reducing the artifact floor raises s and is "
            "the only thing that moves the ceiling."
        ),
        "power_note": (
            f"{n_sites} sites in {n_blocks} independent haplotype blocks. The standard error "
            f"uses the block count; using the site count would overstate power by "
            f"{np.sqrt(n_sites / n_blocks):.2f}x. Minimum detectable |BAF - 0.5| at 80% power "
            f"is {mde:.4f}."
        ),
    }
