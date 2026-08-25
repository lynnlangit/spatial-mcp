"""Beta-binomial likelihood machinery shared by the copy-number tools.

Why a latent-sign mixture rather than |BAF - 0.5|
-------------------------------------------------
A somatic copy-number change shifts BAF away from 0.5 by an amount set by tumor
purity. The DIRECTION of the shift depends on which parental haplotype was lost
or gained and on which allele happens to be the VCF's ALT — both unknown and
effectively random per site. So the signed shift is uninformative and the
magnitude is the statistic.

Taking absolute values to get that magnitude is the obvious move and it is
wrong: |BAF - 0.5| has a depth-dependent positive bias under the null, so a
shallow region looks imbalanced purely because it is shallow. A mixture
likelihood — each site's true shift is +d or -d with equal prior — recovers the
magnitude without inheriting that bias.

Why beta-binomial rather than binomial
--------------------------------------
Read counts are NOT binomial around the true BAF. Reference mapping bias and
capture-efficiency differences between alleles add overdispersion, and reads
drawn from a PCR-amplified pool are not independent trials. The concentration
parameter `s` is fitted genome-wide on the copy-neutral pool and carried into
every per-region test, so the null absorbs systematic bias instead of the
region-level result inheriting it as false signal.
"""

from __future__ import annotations

import math
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import betaln

# Every copy-number event this platform models, with its expected |BAF - 0.5|
# as a function of tumor purity p. Derived from allele fractions in a mixture of
# `p` tumor cells at the stated copy state and `1 - p` diploid normal cells.
EVENT_DEVIATION = {
    # tumor CN 1, one parental allele lost
    "single_copy_loss": lambda p: p / (2 * (2 - p)),
    # tumor CN 3, one parental allele gained
    "single_copy_gain": lambda p: p / (2 * (2 + p)),
    # tumor CN 2 but both copies from one parent
    "copy_neutral_loh": lambda p: p / 2,
    # tumor CN 4 in a 3:1 allelic configuration
    "double_gain": lambda p: p / (2 + 2 * p),
}

# Legacy aliases kept because the prototype and the clinical literature use them.
EVENT_ALIASES = {
    "monosomy": "single_copy_loss",
    "loss": "single_copy_loss",
    "gain": "single_copy_gain",
    "cn_loh": "copy_neutral_loh",
    "loh": "copy_neutral_loh",
}


def expected_deviation(purity: float, event: str) -> float:
    """Expected |BAF - 0.5| for a copy-number event at a given tumor purity."""
    key = EVENT_ALIASES.get(event, event)
    try:
        return float(EVENT_DEVIATION[key](purity))
    except KeyError:
        raise ValueError(
            f"unknown copy-number event {event!r}; known events: "
            f"{sorted(EVENT_DEVIATION)} (aliases: {sorted(EVENT_ALIASES)})"
        ) from None


def expected_deviations(purity: float) -> dict[str, float]:
    """All four event expectations at one purity, for detectability reporting."""
    return {name: float(fn(purity)) for name, fn in EVENT_DEVIATION.items()}


def betabinom_logpmf(k: int, n: int, a: float, b: float) -> float:
    """log P(k successes in n trials) under a beta-binomial with shape (a, b)."""
    return (
        betaln(k + a, n - k + b)
        - betaln(a, b)
        + math.lgamma(n + 1)
        - math.lgamma(k + 1)
        - math.lgamma(n - k + 1)
    )


def site_loglik(k: int, n: int, d: float, s: float) -> float:
    """Latent-sign mixture: the site's shift is +d or -d with equal prior.

    Computed in log space with the max factored out, so a site with a strongly
    favoured sign does not underflow the disfavoured branch to zero and lose the
    mixture entirely.
    """
    hi, lo = 0.5 + d, 0.5 - d
    la = betabinom_logpmf(k, n, hi * s, lo * s)
    lb = betabinom_logpmf(k, n, lo * s, hi * s)
    m = max(la, lb)
    return m + math.log(0.5 * math.exp(la - m) + 0.5 * math.exp(lb - m))


def region_loglik(sites: Sequence[Mapping], d: float, s: float) -> float:
    """Total log-likelihood of a set of sites under shared deviation `d`."""
    return sum(site_loglik(x["alt_count"], x["depth"], d, s) for x in sites)


def fit_concentration(sites: Sequence[Mapping]) -> float:
    """Fit the beta-binomial concentration `s` on the null (d = 0).

    Small `s` means heavy overdispersion; `s` -> infinity is pure binomial. The
    bounds are wide on purpose: a clean library really can approach the binomial
    limit, and pinning the upper bound too low would manufacture overdispersion
    that is not there.
    """
    if not sites:
        raise ValueError("cannot fit concentration on an empty site set")

    def nll(log_s: float) -> float:
        s = math.exp(log_s)
        return -sum(betabinom_logpmf(x["alt_count"], x["depth"], 0.5 * s, 0.5 * s) for x in sites)

    r = minimize_scalar(nll, bounds=(math.log(2), math.log(5e5)), method="bounded")
    return float(math.exp(r.x))


def fit_deviation(sites: Sequence[Mapping], s: float) -> tuple[float, float]:
    """MLE of the imbalance magnitude `d`. Returns (d_hat, likelihood_ratio)."""
    if not sites:
        return 0.0, 0.0

    def nll(d: float) -> float:
        return -region_loglik(sites, d, s)

    r = minimize_scalar(nll, bounds=(0.0, 0.45), method="bounded")
    ll_alt = -float(r.fun)
    ll_null = -nll(0.0)
    return float(r.x), 2.0 * (ll_alt - ll_null)


def per_site_sd(depth: float, s: float) -> float:
    """Per-site SD of BAF under the beta-binomial at a given depth.

    var = 0.25 * (1 + (n - 1) / (s + 1)) / n

    As n grows this approaches 0.25 / (s + 1) and no sequencing depth crosses
    that ceiling. Any recommendation to sequence deeper has to be stated against
    this asymptote, not against the binomial 0.25/n it does not obey.
    """
    n = float(depth)
    if n <= 0:
        return float("nan")
    return math.sqrt(0.25 * (1.0 + (n - 1.0) / (s + 1.0)) / n)


def binomial_sd(depth: float) -> float:
    """Per-site SD of BAF if reads were independent trials. The floor, not the truth."""
    n = float(depth)
    if n <= 0:
        return float("nan")
    return math.sqrt(0.25 / n)


def depth_scaling_ceiling(s: float) -> float:
    """SD(BAF) at infinite depth: sqrt(0.25 / (s + 1))."""
    return math.sqrt(0.25 / (s + 1.0))


def group_by_block(sites: Iterable[Mapping]) -> dict[str, list[Mapping]]:
    """Group sites by haplotype block id.

    The block is the exchangeable unit for every downstream test. Sites inside
    one block share a chromosome and move together, so they are one observation.
    """
    blocks: dict[str, list[Mapping]] = {}
    for x in sites:
        blocks.setdefault(x["block"], []).append(x)
    return blocks


def block_resample_null(
    pool_blocks: Mapping[str, Sequence[Mapping]],
    n_blocks: int,
    s: float,
    n_iter: int = 10_000,
    seed: int = 20260825,
) -> np.ndarray:
    """Null distribution of d_hat from sets of `n_blocks` copy-neutral blocks.

    Blocks are drawn, not sites. Drawing sites would break the within-block
    correlation the null needs to reproduce, and would make a region of five
    sites in one gene look like five independent observations — which is the
    error the block structure exists to prevent.
    """
    keys = list(pool_blocks.keys())
    if n_blocks > len(keys):
        raise ValueError(f"cannot draw {n_blocks} blocks from a copy-neutral pool of {len(keys)}")
    rng = np.random.default_rng(seed)
    out = np.empty(n_iter)
    for i in range(n_iter):
        pick = rng.choice(len(keys), size=n_blocks, replace=False)
        drawn = [x for j in pick for x in pool_blocks[keys[j]]]
        out[i], _ = fit_deviation(drawn, s)
    return out
