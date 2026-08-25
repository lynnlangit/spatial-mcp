"""Model comparison for copy-number architecture within a region.

The question this answers
-------------------------
A reviewer asked whether conflicting loci on chromosome 3 pointed to a
localised structural change rather than whole-chromosome loss. That is a model
comparison, not an opinion, and answering it by eye is how a single deviant
locus becomes a breakpoint.

Three models, fitted with the same likelihood machinery the imbalance test uses:

  M0  neutral       — no event anywhere in the region        (k = 0)
  M1  whole-region  — one shared deviation across the region (k = 1)
  M2  breakpoint    — two segments, each with its own        (k = 2)

Ranked by AIC, with a likelihood-ratio test for the nested M2-vs-M1 comparison.

Why the breakpoint search is coarse
------------------------------------
Candidate breakpoints default to the midpoints between consecutive haplotype
BLOCKS, not to a fine positional grid. A breakpoint inside a block is
unidentifiable — the sites there move together — so a fine grid would only
manufacture apparent resolution. With a handful of independent loci this
comparison is easy to over-read, and the `caution` field exists to say so out
loud when the winning model rests on a single locus.
"""

from __future__ import annotations

from typing import Any, Sequence

from scipy import stats

from .stats import fit_deviation, group_by_block, region_loglik


def compare_architectures(
    region_sites: Sequence[dict],
    overdispersion_s: float,
    candidate_breakpoints: Sequence[int] | None = None,
) -> dict[str, Any]:
    """Fit and rank M0, M1 and M2 for one region."""
    if not region_sites:
        raise ValueError("compare_cnv_architectures requires at least one site")

    sites = sorted(region_sites, key=lambda s: s["pos"])
    blocks = group_by_block(sites)
    n_sites, n_blocks = len(sites), len(blocks)

    # ---- M0: neutral ------------------------------------------------------
    ll0 = region_loglik(sites, 0.0, overdispersion_s)
    m0 = _model("M0_neutral", ll0, k=0, detail={"deviation": 0.0})

    # ---- M1: one event across the whole region ---------------------------
    d1, _ = fit_deviation(sites, overdispersion_s)
    ll1 = region_loglik(sites, d1, overdispersion_s)
    m1 = _model("M1_whole_region", ll1, k=1, detail={"deviation": float(d1)})

    # ---- M2: two segments -------------------------------------------------
    m2, breakpoint_scan = _fit_breakpoint_model(
        sites, blocks, overdispersion_s, candidate_breakpoints
    )

    models = [m for m in (m0, m1, m2) if m is not None]
    best_aic = min(m["aic"] for m in models)
    for m in models:
        m["delta_aic"] = m["aic"] - best_aic
    ranked = sorted(models, key=lambda m: m["aic"])
    winner = ranked[0]

    # M2 nests M1 (one shared deviation is the two-segment model with both
    # segments equal), so the likelihood-ratio test is the right comparison.
    lr_test = None
    if m2 is not None:
        lr = 2.0 * (m2["log_likelihood"] - m1["log_likelihood"])
        lr_test = {
            "comparison": "M2_vs_M1",
            "likelihood_ratio": float(lr),
            "df": 1,
            "p": float(stats.chi2.sf(max(lr, 0.0), 1)),
            "note": (
                "Chi-square approximation on 1 df. With few independent blocks this p is "
                "indicative rather than exact, and the breakpoint position was chosen by "
                "search without being charged as a parameter — both push this p optimistically low."
            ),
        }

    caution = _build_caution(winner, m2, n_sites, n_blocks, breakpoint_scan)

    return {
        "models": ranked,
        "best_model": winner["model"],
        "n_sites": n_sites,
        "n_blocks": n_blocks,
        "overdispersion_s": overdispersion_s,
        "likelihood_ratio_test": lr_test,
        "breakpoint_scan": breakpoint_scan,
        "caution": caution,
        "region_span": {
            "chrom": sites[0].get("chrom", ""),
            "start": sites[0]["pos"],
            "end": sites[-1]["pos"],
        },
    }


def _model(name: str, ll: float, k: int, detail: dict) -> dict[str, Any]:
    return {
        "model": name,
        "log_likelihood": float(ll),
        "k": k,
        "aic": float(2 * k - 2 * ll),
        **detail,
    }


def _fit_breakpoint_model(
    sites: Sequence[dict],
    blocks: dict[str, list[dict]],
    s: float,
    candidate_breakpoints: Sequence[int] | None,
) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
    """Fit the best two-segment model over the candidate breakpoints."""
    if len(blocks) < 2:
        return None, []

    candidates = list(candidate_breakpoints or _default_breakpoints(blocks))
    scan: list[dict[str, Any]] = []
    best: dict[str, Any] | None = None

    for bp in candidates:
        proximal = [x for x in sites if x["pos"] < bp]
        distal = [x for x in sites if x["pos"] >= bp]
        if not proximal or not distal:
            continue
        d_prox, _ = fit_deviation(proximal, s)
        d_dist, _ = fit_deviation(distal, s)
        ll = region_loglik(proximal, d_prox, s) + region_loglik(distal, d_dist, s)
        row = {
            "breakpoint": int(bp),
            "log_likelihood": float(ll),
            "proximal": {
                "deviation": float(d_prox),
                "n_sites": len(proximal),
                "n_blocks": len(group_by_block(proximal)),
            },
            "distal": {
                "deviation": float(d_dist),
                "n_sites": len(distal),
                "n_blocks": len(group_by_block(distal)),
            },
        }
        scan.append(row)
        if best is None or ll > best["log_likelihood"]:
            best = row

    if best is None:
        return None, scan

    model = _model(
        "M2_breakpoint",
        best["log_likelihood"],
        k=2,
        detail={
            "breakpoint": best["breakpoint"],
            "proximal": best["proximal"],
            "distal": best["distal"],
            "n_candidate_breakpoints": len(scan),
        },
    )
    return model, scan


def _default_breakpoints(blocks: dict[str, list[dict]]) -> list[int]:
    """Midpoints between consecutive haplotype blocks.

    A breakpoint inside a block cannot be located — the sites there share a
    chromosome and move together — so the block boundary is the finest
    resolution the data actually supports.
    """
    positions = sorted(
        (min(x["pos"] for x in members), max(x["pos"] for x in members))
        for members in blocks.values()
    )
    return [(positions[i][1] + positions[i + 1][0]) // 2 for i in range(len(positions) - 1)]


def _build_caution(
    winner: dict[str, Any],
    m2: dict[str, Any] | None,
    n_sites: int,
    n_blocks: int,
    scan: list[dict[str, Any]],
) -> dict[str, Any]:
    """Fire when the winning model rests on a single locus in any segment."""
    reasons: list[str] = []

    if winner["model"] == "M2_breakpoint" and m2 is not None:
        for side in ("proximal", "distal"):
            seg = m2[side]
            if seg["n_blocks"] <= 1:
                reasons.append(
                    f"The {side} segment rests on {seg['n_blocks']} haplotype block "
                    f"({seg['n_sites']} site{'s' if seg['n_sites'] != 1 else ''}). A single "
                    "locus cannot be corroborated, and any local artifact reproduces this "
                    "exact result."
                )
        if len(scan) > 1:
            reasons.append(
                f"The breakpoint was selected by searching {len(scan)} candidate positions "
                "but is not charged as a fitted parameter in the AIC, so M2 is favoured "
                "somewhat more than the comparison states."
            )

    if n_blocks < 4:
        reasons.append(
            f"The region carries {n_blocks} independent haplotype blocks. Model comparison "
            "at this sample size distinguishes structures only when they differ grossly."
        )

    if n_sites > n_blocks:
        reasons.append(
            f"{n_sites} sites cluster into {n_blocks} blocks; the effective sample size is "
            f"{n_blocks}, not {n_sites}."
        )

    return {
        "fired": bool(reasons),
        "reasons": reasons,
    }


__all__ = ["compare_architectures"]
