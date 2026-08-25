"""Arm- and region-level allelic imbalance — the core statistic.

What this measures, and what it does not
----------------------------------------
It measures a MAGNITUDE: how far |BAF - 0.5| departs from zero across a region.
It is structurally blind to direction. At 16.6% purity a single-copy loss
predicts a deviation of 0.0454 and a single-copy gain predicts 0.0384 — 0.0070
apart, well inside the standard error. No amount of BAF data separates them.

An earlier analysis reported "chromosome 3 loss" from this statistic. It was
wrong to, and the fix is not a note in the docstring: `direction` is
"undetermined" unless orthogonal depth evidence is supplied AND the library
chemistry permits depth-based copy-number inference. Supplying depth evidence
on a chemistry that cannot support it raises, rather than being quietly
ignored — a caller who passes evidence expects it to be used.

Two methodological choices carried over from the prototype
----------------------------------------------------------
**Latent-sign mixture, not absolute values.** |BAF - 0.5| carries a
depth-dependent positive bias under the null; a mixture likelihood over the
unknown sign does not. See `stats.site_loglik`.

**Resampling whole blocks, not an asymptotic test.** With four independent
blocks the chi-square approximation to the likelihood-ratio statistic is not
trustworthy, and the block is the correct exchangeable unit — sites inside one
block move together, and a site-level resample would destroy exactly the
correlation the null needs to reproduce.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np

from .detectability import assess_detectability
from .stats import (
    EVENT_DEVIATION,
    block_resample_null,
    expected_deviations,
    fit_deviation,
    group_by_block,
    per_site_sd,
)


class DepthEvidenceRefused(ValueError):
    """Depth evidence was supplied on a chemistry that cannot support it."""


# Deliberately NOT named `test_imbalance`: pytest collects any module-level
# callable whose name starts with "test_", so a helper named that way is picked
# up as a broken test wherever it is imported. The MCP tool this backs is still
# called `test_allelic_imbalance`, as the spec requires.
def run_imbalance_test(
    region_sites: Sequence[dict],
    neutral_pool: Sequence[dict],
    overdispersion_s: float,
    purity: float,
    chemistry: dict,
    depth_evidence: dict | None = None,
    n_resample: int = 10_000,
    seed: int = 20260825,
) -> dict[str, Any]:
    """Test one region for allelic imbalance against a copy-neutral null."""
    from .chemistry import require_chemistry

    require_chemistry(chemistry, "test_allelic_imbalance")

    # The guard, enforced before any computation so a caller cannot get a
    # partial result out of a call that was invalid to make.
    if depth_evidence is not None and not chemistry["depth_cnv_permitted"]:
        raise DepthEvidenceRefused(
            f"depth_evidence was supplied but chemistry={chemistry['chemistry']!r} sets "
            "depth_cnv_permitted=False. Per-amplicon read depth on an amplicon library "
            "reflects PCR amplification efficiency, not input copy number, so this "
            "evidence cannot be used to assign direction. Refusing rather than ignoring "
            "it, because a caller who passes evidence expects it to count."
        )

    if not region_sites:
        raise ValueError("test_allelic_imbalance requires at least one site in the region")
    if not neutral_pool:
        raise ValueError(
            "test_allelic_imbalance requires a copy-neutral pool to resample the null from"
        )

    blocks = group_by_block(region_sites)
    n_sites, n_blocks = len(region_sites), len(blocks)

    pool_blocks = group_by_block(neutral_pool)
    if n_blocks > len(pool_blocks):
        raise ValueError(
            f"region has {n_blocks} blocks but the copy-neutral pool has only "
            f"{len(pool_blocks)}; the null cannot be resampled at this size"
        )

    d_hat, lrt = fit_deviation(region_sites, overdispersion_s)

    null = block_resample_null(
        pool_blocks, n_blocks, overdispersion_s, n_iter=n_resample, seed=seed
    )
    # (count + 1) / (n + 1): the observed statistic is itself one draw from the
    # null under H0, so a p of exactly zero is not available and should not be
    # reported.
    p = float((np.sum(null >= d_hat) + 1) / (n_resample + 1))

    median_depth = float(np.median([s["depth"] for s in region_sites]))
    se = per_site_sd(median_depth, overdispersion_s) / np.sqrt(n_blocks)
    ci_lo = max(0.0, d_hat - 1.96 * se)
    ci_hi = d_hat + 1.96 * se

    expected = expected_deviations(purity)
    consistent_with = sorted(event for event, dev in expected.items() if ci_lo <= dev <= ci_hi)
    if ci_lo <= 0.0 <= ci_hi:
        consistent_with = ["copy_neutral", *consistent_with]

    direction, direction_note = _resolve_direction(
        d_hat, ci_lo, ci_hi, expected, chemistry, depth_evidence
    )

    detectability = assess_detectability(purity, region_sites, overdispersion_s, chemistry)

    return {
        "imbalance": float(d_hat),
        "ci95": [float(ci_lo), float(ci_hi)],
        "se": float(se),
        "p": p,
        "likelihood_ratio": float(lrt),
        "n_sites": n_sites,
        "n_blocks": n_blocks,
        "median_depth": median_depth,
        "direction": direction,
        "direction_note": direction_note,
        "consistent_with": consistent_with,
        "expected_deviation_by_event": expected,
        "monosomy_excluded": bool(ci_hi < expected["single_copy_loss"]),
        "null_distribution": {
            "n_resample": n_resample,
            "median": float(np.median(null)),
            "p95": float(np.percentile(null, 95)),
            "unit": "haplotype_block",
            "pool_blocks_available": len(pool_blocks),
        },
        "detectability": detectability,
        "blocks": [
            {
                "block": bid,
                "gene": members[0].get("gene", ""),
                "arm": members[0].get("arm", ""),
                "n_sites": len(members),
                "mean_abs_deviation": float(np.mean([abs(s["baf"] - 0.5) for s in members])),
            }
            for bid, members in sorted(blocks.items())
        ],
    }


def _resolve_direction(
    d_hat: float,
    ci_lo: float,
    ci_hi: float,
    expected: dict[str, float],
    chemistry: dict,
    depth_evidence: dict | None,
) -> tuple[str, str]:
    """Assign direction only when something other than BAF magnitude can support it.

    Reaching "loss" or "gain" requires BOTH depth evidence and a chemistry on
    which depth means copy number. Neither alone is enough, and the magnitude
    itself is never enough.
    """
    loss, gain = expected["single_copy_loss"], expected["single_copy_gain"]
    gap = abs(loss - gain)

    if depth_evidence is None:
        candidates = [
            e for e in ("single_copy_loss", "single_copy_gain") if ci_lo <= expected[e] <= ci_hi
        ]
        if len(candidates) < 2 and d_hat <= 0.0:
            return "undetermined", ("No imbalance detected, so there is no direction to assign.")
        return "undetermined", (
            f"Loss ({loss:.4f}) and gain ({gain:.4f}) are {gap:.4f} apart, which this "
            f"measurement cannot resolve — it is a magnitude, not a signed quantity. "
            f"Only orthogonal depth evidence separates them, and none was supplied."
        )

    # depth_evidence is present and chemistry permits it (the caller-facing guard
    # already refused the other combination).
    log2_ratio = depth_evidence.get("log2_ratio")
    if log2_ratio is None:
        return "undetermined", (
            "Depth evidence was supplied but carries no `log2_ratio`, so it cannot "
            "assign a direction."
        )
    ci = depth_evidence.get("log2_ratio_ci95")
    if ci and ci[0] <= 0.0 <= ci[1]:
        return "undetermined", (
            f"Depth evidence log2 ratio {log2_ratio:+.4f} has a 95% interval "
            f"[{ci[0]:+.4f}, {ci[1]:+.4f}] spanning zero, so it does not distinguish "
            "loss from gain."
        )
    if log2_ratio < 0:
        return "loss", (
            f"Depth evidence log2 tumour/normal ratio {log2_ratio:+.4f} on a "
            f"{chemistry['chemistry']} library, where read depth tracks input copy "
            f"number. Combined with a BAF magnitude of {d_hat:.4f}, this is a loss."
        )
    return "gain", (
        f"Depth evidence log2 tumour/normal ratio {log2_ratio:+.4f} on a "
        f"{chemistry['chemistry']} library, where read depth tracks input copy number. "
        f"Combined with a BAF magnitude of {d_hat:.4f}, this is a gain."
    )


def expected_log2_depth_ratio(purity: float, tumour_cn: int) -> float:
    """log2 tumour/normal depth ratio for a given copy state at a given purity.

    Provided so a caller assembling `depth_evidence` from a hybrid-capture BAM
    has the same expectation the BAF side uses, rather than a separately derived
    one that might not agree.
    """
    ratio = (2 * (1 - purity) + tumour_cn * purity) / 2
    return float(np.log2(ratio))


__all__ = [
    "run_imbalance_test",
    "DepthEvidenceRefused",
    "expected_log2_depth_ratio",
    "EVENT_DEVIATION",
]
