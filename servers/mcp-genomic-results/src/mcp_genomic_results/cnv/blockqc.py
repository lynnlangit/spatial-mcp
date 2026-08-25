"""Quality control on heterozygous sites — the governance step.

Kept separate from extraction on purpose: which sites were admitted to a
copy-number inference, and why, has to be independently auditable.

Rule A — within-block concordance
---------------------------------
Under a real arm-level copy-number event, every heterozygous site inside one
haplotype block sits on the same pair of parental chromosomes and must show the
SAME deviation magnitude |BAF - 0.5|. The signs may differ, because which
parental allele is the VCF's ALT flips from site to site, but the magnitude
cannot. Sites in one block that disagree on magnitude are not reporting a
copy-number event — they are reporting a mapping problem.

This matters because panels capture paralogous regions. NOTCH2 at
chr1:120.4-120.6 Mb sits in the 1p11-p12 segmental duplication alongside
NOTCH2NL; reads from the paralogs collapse onto the NOTCH2 target and drag BAF
away from 0.5 by amounts that vary site to site. Without this rule that block
produces a confident, entirely false 1p loss call at p = 0.0002.

The rule is specifiable in advance and never looks at which arm a block is on,
so applying it is not cherry-picking against an unwanted result.

Rule B — within-amplicon concordance
------------------------------------
Rule A cannot test a block containing one site, and single-site blocks are
where the worst artifacts hide. When two or more distinct primer pairs cover the
same site, each is an independent estimate of the same allelic ratio, so
disagreement beyond sampling error means primer or mapping pathology. That vets
single-site blocks, which Rule A structurally cannot reach.

Rule C — per-site artifact screens
-----------------------------------
Cheap, local signatures of a locus that should not be trusted at all.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import numpy as np
from scipy import stats

from .stats import binomial_sd, fit_concentration, group_by_block, per_site_sd

# A block needs this many sites before its internal consistency can be tested.
MIN_SITES_FOR_BLOCK_TEST = 3

# Do NOT lower this. A 28-read amplicon passes the within-amplicon concordance
# test trivially — its confidence interval spans nearly everything, so it agrees
# with any other estimate by construction. That is a FALSE vetting, not a real
# one, and it is worse than leaving the site untested, because a false vetting
# promotes an artifact into the "corroborated" pile. Anyone tempted to relax
# this to recover sites should recover them with more depth instead.
MIN_AMPLICON_DEPTH_FLOOR = 50

# Sites below this depth are dropped before Rule A. At low depth the sampling
# scatter swamps any real deviation, so a shallow site cannot corroborate or
# contradict its block-mates; it only adds noise to the homogeneity test.
DEFAULT_MIN_SITE_DEPTH = 1000

# Rule C thresholds.
THIRD_ALLELE_FRACTION_MAX = 0.02
SOFTCLIP_FRACTION_MAX = 0.35
STRAND_BIAS_P_MIN = 1e-4
# An amplicon pinned at an extreme is the primer-dropout signature: the primer
# has replaced the template, so the amplicon can only report one allele.
AMPLICON_PINNED_LOW = 0.08
AMPLICON_PINNED_HIGH = 0.92


# --------------------------------------------------------------------------- #
# Rule A
# --------------------------------------------------------------------------- #


def block_concordance(
    sites: Sequence[dict],
    min_sites: int = MIN_SITES_FOR_BLOCK_TEST,
    alpha: float = 0.01,
) -> tuple[str, float, dict[str, Any]]:
    """Test whether |BAF - 0.5| is homogeneous within one haplotype block.

    Returns (verdict, p_value, detail). A block with fewer than `min_sites`
    sites is 'untestable' — retained, but flagged, because a single-site block
    can never be corroborated and downstream reporting must say so.

    The standard error uses the BINOMIAL term only, deliberately. Any scatter
    beyond binomial sampling is precisely the signal that the block is
    internally inconsistent; folding the fitted overdispersion in here would
    absorb the artifact this rule exists to detect.
    """
    if len(sites) < min_sites:
        return (
            "untestable",
            float("nan"),
            {
                "n_sites": len(sites),
                "mean_abs_deviation": float(np.mean([abs(s["baf"] - 0.5) for s in sites])),
            },
        )

    devs = np.array([abs(s["baf"] - 0.5) for s in sites], dtype=float)
    deps = np.array([s["depth"] for s in sites], dtype=float)

    shared = float(np.average(devs, weights=deps))
    se = np.sqrt(0.25 / deps)
    chi2 = float(np.sum(((devs - shared) / se) ** 2))
    dof = len(sites) - 1
    p = float(stats.chi2.sf(chi2, dof))

    verdict = "concordant" if p >= alpha else "DISCORDANT"
    return (
        verdict,
        p,
        {
            "n_sites": len(sites),
            "shared_deviation": shared,
            "spread": float(devs.max() - devs.min()),
            "chi2": chi2,
            "dof": dof,
        },
    )


# --------------------------------------------------------------------------- #
# Rule B
# --------------------------------------------------------------------------- #


def amplicon_concordance(
    site: dict,
    min_amplicon_depth: int = MIN_AMPLICON_DEPTH_FLOOR,
    alpha: float = 0.01,
) -> tuple[str, float, dict[str, Any]]:
    """Test whether independent primer pairs agree on the allelic ratio at a site."""
    if min_amplicon_depth < MIN_AMPLICON_DEPTH_FLOOR:
        raise ValueError(
            f"min_amplicon_depth={min_amplicon_depth} is below the floor of "
            f"{MIN_AMPLICON_DEPTH_FLOOR}. A shallow amplicon passes this test "
            "trivially, which vets an artifact instead of catching one."
        )

    amplicons = [
        a
        for a in site.get("amplicons", []) or []
        if a.get("depth", 0) >= min_amplicon_depth and not a.get("under_primer")
    ]
    if len(amplicons) < 2:
        return (
            "untestable",
            float("nan"),
            {
                "n_amplicons_usable": len(amplicons),
                "reason": "fewer than two independent primer pairs at sufficient depth",
            },
        )

    alts = np.array([a["alt_count"] for a in amplicons], dtype=float)
    deps = np.array([a["depth"] for a in amplicons], dtype=float)
    pooled = float(alts.sum() / deps.sum())
    if pooled <= 0.0 or pooled >= 1.0:
        return (
            "untestable",
            float("nan"),
            {
                "n_amplicons_usable": len(amplicons),
                "reason": "pooled allele fraction is degenerate",
            },
        )

    expected_var = pooled * (1.0 - pooled) / deps
    chi2 = float(np.sum(((alts / deps) - pooled) ** 2 / expected_var))
    dof = len(amplicons) - 1
    p = float(stats.chi2.sf(chi2, dof))

    verdict = "concordant" if p >= alpha else "DISCORDANT"
    return (
        verdict,
        p,
        {
            "n_amplicons_usable": len(amplicons),
            "pooled_vaf": pooled,
            "per_amplicon_vaf": [float(v) for v in (alts / deps)],
            "per_amplicon_depth": [int(d) for d in deps],
            "chi2": chi2,
            "dof": dof,
        },
    )


# --------------------------------------------------------------------------- #
# Rule C
# --------------------------------------------------------------------------- #


def artifact_screens(site: dict) -> list[str]:
    """Per-site artifact signatures. Returns the list of screens the site failed."""
    failures: list[str] = []

    third = site.get("third_allele_fraction")
    if third is not None and third > THIRD_ALLELE_FRACTION_MAX:
        failures.append(f"third_allele_fraction {third:.4f} > {THIRD_ALLELE_FRACTION_MAX}")

    softclip = site.get("softclip_fraction")
    if softclip is not None and softclip > SOFTCLIP_FRACTION_MAX:
        failures.append(f"softclip_fraction {softclip:.3f} > {SOFTCLIP_FRACTION_MAX}")

    sb = _strand_bias_p(site)
    if sb is not None and sb < STRAND_BIAS_P_MIN:
        failures.append(f"strand-bias Fisher p {sb:.2e} < {STRAND_BIAS_P_MIN:.0e}")

    for a in site.get("amplicons", []) or []:
        vaf = a.get("vaf")
        if vaf is None or a.get("depth", 0) < MIN_AMPLICON_DEPTH_FLOOR:
            continue
        if vaf < AMPLICON_PINNED_LOW or vaf > AMPLICON_PINNED_HIGH:
            failures.append(
                f"amplicon {a.get('amplicon_start')}-{a.get('amplicon_end')} pinned at "
                f"VAF {vaf:.3f} (primer-dropout signature)"
            )
            break

    return failures


def _strand_bias_p(site: dict) -> float | None:
    """Fisher exact p for ref/alt against forward/reverse, when counts exist."""
    needed = ("ref_fwd", "ref_rev", "alt_fwd", "alt_rev")
    if not all(k in site and site[k] is not None for k in needed):
        return None
    table = [[site["alt_fwd"], site["alt_rev"]], [site["ref_fwd"], site["ref_rev"]]]
    try:
        return float(stats.fisher_exact(table)[1])
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #


def run_qc(
    sites: Sequence[dict],
    chemistry: dict,
    min_amplicon_depth: int = MIN_AMPLICON_DEPTH_FLOOR,
    block_alpha: float = 0.01,
    amplicon_alpha: float = 0.01,
    min_site_depth: int = DEFAULT_MIN_SITE_DEPTH,
    neutral_pool_exclude_arms: Iterable[str] = (),
) -> dict[str, Any]:
    """Apply Rules A, B and C, then fit overdispersion on the survivors.

    Every stage reports its own site and block counts, so the attrition from raw
    calls to usable observations is legible rather than a single before/after
    pair.
    """
    from .chemistry import require_chemistry

    require_chemistry(chemistry, "qc_heterozygous_sites")

    excluded = set(neutral_pool_exclude_arms)
    stages: list[dict[str, Any]] = []
    sites = [dict(s) for s in sites]
    # Noise at each stage is measured on the COPY-NEUTRAL pool, not on every
    # site. Including the arms under test would let a real event inflate the
    # number that is supposed to describe the null.
    stages.append(_stage("raw_variant_calls", sites, excluded))

    # Depth pre-filter — a shallow site cannot corroborate or contradict its
    # block-mates, so admitting it only adds scatter to Rule A.
    deep = [s for s in sites if s["depth"] >= min_site_depth]
    shallow_dropped = len(sites) - len(deep)

    # ---- Rule A ----------------------------------------------------------
    block_report: list[dict[str, Any]] = []
    after_a: list[dict] = []
    for block_id, members in sorted(group_by_block(deep).items()):
        verdict, p, detail = block_concordance(members, alpha=block_alpha)
        block_report.append(
            {
                "block": block_id,
                "arm": members[0].get("arm", ""),
                "gene": members[0].get("gene", ""),
                "verdict": verdict,
                "p": None if p != p else p,
                **detail,
            }
        )
        if verdict == "DISCORDANT":
            for s in members:
                s["qc_drop_reason"] = f"rule_A_discordant_block (p={p:.2e})"
            continue
        for s in members:
            s["rule_a"] = verdict
        after_a.extend(members)
    stages.append(_stage("after_rule_A", after_a, excluded))

    # ---- Rule B ----------------------------------------------------------
    after_b: list[dict] = []
    amplicon_report: list[dict[str, Any]] = []
    for s in after_a:
        verdict, p, detail = amplicon_concordance(
            s, min_amplicon_depth=min_amplicon_depth, alpha=amplicon_alpha
        )
        s["rule_b"] = verdict
        if verdict != "untestable":
            amplicon_report.append(
                {
                    "chrom": s["chrom"],
                    "pos": s["pos"],
                    "gene": s.get("gene", ""),
                    "verdict": verdict,
                    "p": None if p != p else p,
                    **detail,
                }
            )
        if verdict == "DISCORDANT":
            s["qc_drop_reason"] = f"rule_B_discordant_amplicons (p={p:.2e})"
            continue
        after_b.append(s)
    stages.append(_stage("after_rule_B", after_b, excluded))

    # ---- Rule C ----------------------------------------------------------
    after_c: list[dict] = []
    screen_report: list[dict[str, Any]] = []
    for s in after_b:
        failures = artifact_screens(s)
        if failures:
            s["qc_drop_reason"] = "rule_C: " + "; ".join(failures)
            screen_report.append(
                {
                    "chrom": s["chrom"],
                    "pos": s["pos"],
                    "gene": s.get("gene", ""),
                    "failures": failures,
                }
            )
            continue
        after_c.append(s)
    stages.append(_stage("after_rule_C", after_c, excluded))

    # ---- Overdispersion --------------------------------------------------
    pool = [s for s in after_c if s.get("arm") not in excluded]
    overdispersion = _fit_overdispersion(sites, after_a, after_c, pool)

    dropped = [s for s in sites if s.get("qc_drop_reason")]

    return {
        "sites": after_c,
        "n_sites": len(after_c),
        "n_blocks": len(group_by_block(after_c)),
        "stages": stages,
        "shallow_sites_dropped": shallow_dropped,
        "blocks_failing_rule_a": sum(1 for b in block_report if b["verdict"] == "DISCORDANT"),
        "sites_failing_rule_b": sum(1 for r in amplicon_report if r["verdict"] == "DISCORDANT"),
        "sites_failing_rule_c": len(screen_report),
        "block_report": block_report,
        "amplicon_report": amplicon_report,
        "artifact_report": screen_report,
        "dropped_sites": [
            {
                "chrom": s["chrom"],
                "pos": s["pos"],
                "gene": s.get("gene", ""),
                "block": s.get("block", ""),
                "reason": s["qc_drop_reason"],
            }
            for s in dropped
        ],
        "overdispersion": overdispersion,
        "neutral_pool": {
            "n_sites": len(pool),
            "n_blocks": len(group_by_block(pool)),
            "excluded_arms": sorted(excluded),
        },
        "parameters": {
            "min_amplicon_depth": min_amplicon_depth,
            "block_alpha": block_alpha,
            "amplicon_alpha": amplicon_alpha,
            "min_site_depth": min_site_depth,
        },
        "rule_b_coverage": {
            "sites_testable": len(amplicon_report),
            "note": (
                "Rule B needs two or more independent primer pairs per site, which "
                "requires BAM-derived amplicon counts. With VCF-only input every site "
                "is untestable under Rule B and single-site blocks stay unvetted."
            ),
        },
    }


def _stage(name: str, sites: Sequence[dict], excluded_arms: set[str]) -> dict[str, Any]:
    """One row of the attrition table.

    `n_sites` and `n_blocks` describe everything that survived to this stage.
    The noise figures describe only the copy-neutral pool at this stage, which
    is the set whose scatter is supposed to be pure artifact.
    """
    row: dict[str, Any] = {
        "stage": name,
        "n_sites": len(sites),
        "n_blocks": len(group_by_block(sites)),
        "concentration_s": None,
        "median_depth": None,
        "per_site_sd": None,
        "noise_vs_binomial": None,
    }
    pool = [x for x in sites if x.get("arm") not in excluded_arms]
    if not pool:
        return row
    s = fit_concentration(pool)
    median_depth = float(np.median([x["depth"] for x in pool]))
    row.update(
        {
            "concentration_s": s,
            "median_depth": median_depth,
            "pool_n_sites": len(pool),
            "per_site_sd": per_site_sd(median_depth, s),
            "noise_vs_binomial": per_site_sd(median_depth, s) / binomial_sd(median_depth),
        }
    )
    return row


def _fit_overdispersion(raw, after_a, after_c, pool) -> dict[str, Any]:
    """Fit the beta-binomial concentration on the surviving copy-neutral pool.

    Read counts are not binomial: reads drawn from a PCR-amplified pool are not
    independent trials, and reference mapping bias adds allele-specific
    scatter on top. Fitting `s` on the null pool lets every downstream test
    inherit a null that already contains the systematic bias, instead of
    charging that bias to the region under test as signal.
    """
    if not pool:
        return {
            "fitted": False,
            "reason": "no sites survive QC in the copy-neutral pool",
        }
    s = fit_concentration(pool)
    median_depth = float(np.median([x["depth"] for x in pool]))
    sd = per_site_sd(median_depth, s)
    floor = binomial_sd(median_depth)
    return {
        "fitted": True,
        "concentration_s": s,
        "median_depth": median_depth,
        "per_site_sd": sd,
        "binomial_sd": floor,
        "noise_vs_binomial": sd / floor,
        "n_sites": len(pool),
        "n_blocks": len(group_by_block(pool)),
        "note": (
            "Beta-binomial concentration fitted on the copy-neutral pool after QC. "
            "Small s means heavy overdispersion; s -> infinity would be pure binomial."
        ),
    }


def noise_ratio(sites: Sequence[dict]) -> float:
    """Per-site SD relative to the binomial floor, at the set's median depth."""
    s = fit_concentration(sites)
    median_depth = float(np.median([x["depth"] for x in sites]))
    return per_site_sd(median_depth, s) / binomial_sd(median_depth)


__all__ = [
    "block_concordance",
    "amplicon_concordance",
    "artifact_screens",
    "run_qc",
    "noise_ratio",
    "MIN_AMPLICON_DEPTH_FLOOR",
    "MIN_SITES_FOR_BLOCK_TEST",
]
