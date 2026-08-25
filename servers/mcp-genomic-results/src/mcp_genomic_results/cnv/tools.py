"""The eight copy-number tools, each returning a GradedResult.

On DRY_RUN
----------
These tools deliberately do NOT honour GENOMIC_RESULTS_DRY_RUN by returning a
synthetic payload. The entire purpose of this package is to stop a plausible
number with no patient-specific evidence behind it from reaching a report, and
a dry-run fixture is exactly such a number wearing the same envelope as a real
one. When an input is missing or unreadable these tools return
grade=NOT_ASSESSABLE with the reason stated, which is the honest answer.

The pure-computation tools (purity, detectability, imbalance, architecture,
prognostic class) operate on caller-supplied observations rather than on files,
so they run real logic on whatever they are given and set `synthetic_inputs`
when the caller declares the inputs synthetic.

Nothing in this package emits actionability=PREDICTIVE. None of these
measurements bears on therapy selection, and the one that comes closest —
uveal-melanoma prognostic class — is hard-coded PROGNOSTIC_ONLY.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Sequence

# The shared envelope lives at repo-root/shared/common/, reached the same way
# the rest of this server reaches shared code.
_repo_root = Path(__file__).resolve().parents[5]
if str(_repo_root / "shared") not in sys.path:
    sys.path.insert(0, str(_repo_root / "shared"))

from common.graded_result import (  # noqa: E402
    ClinicalActionability,
    Detectability,
    EvidenceGrade,
    GradedResult,
    compute_input_digest,
)

from . import architecture as _architecture  # noqa: E402
from . import blockqc as _blockqc  # noqa: E402
from . import chemistry as _chemistry  # noqa: E402
from . import detectability as _detectability  # noqa: E402
from . import hetsites as _hetsites  # noqa: E402
from . import imbalance as _imbalance  # noqa: E402
from . import prognostic as _prognostic  # noqa: E402
from . import purity as _purity  # noqa: E402

TOOL_VERSION = "1.0.0"


def _not_assessable(
    tool: str,
    note: str,
    limits: list[str],
    digest: str,
    assumptions: list[str] | None = None,
    synthetic: bool = False,
) -> dict[str, Any]:
    """A refusal, carrying its reasons and no number."""
    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=EvidenceGrade.NOT_ASSESSABLE,
        actionability=ClinicalActionability.NONE,
        confidence_note=note,
        assumptions=assumptions or ["The input was inspected before any inference was attempted."],
        limits=limits,
        synthetic_inputs=synthetic,
        input_digest=digest,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 1. detect_library_chemistry
# --------------------------------------------------------------------------- #


def detect_library_chemistry_impl(
    bam_path: str,
    sample_region: str | None = None,
    max_reads: int = _chemistry.DEFAULT_MAX_READS,
) -> dict[str, Any]:
    tool = "genomic-results.detect_library_chemistry"
    digest = compute_input_digest(
        {"bam_path": bam_path, "sample_region": sample_region, "max_reads": max_reads}
    )

    try:
        evidence = _chemistry.scan_bam_signals(bam_path, sample_region, max_reads)
    except _chemistry.PysamUnavailable as exc:
        return _not_assessable(
            tool,
            "The BAM could not be inspected, so no chemistry verdict is available.",
            [
                str(exc),
                "Without a chemistry verdict, no copy-number tool in this package may run.",
            ],
            digest,
        )
    except (FileNotFoundError, ValueError) as exc:
        return _not_assessable(
            tool,
            "The BAM could not be inspected, so no chemistry verdict is available.",
            [
                str(exc),
                "Without a chemistry verdict, no copy-number tool in this package may run.",
            ],
            digest,
        )

    verdict = _chemistry.classify_signals(evidence)
    chemistry = verdict["chemistry"]

    if chemistry == "indeterminate":
        dissent = [
            f"{name}: observed {v['observed']}, {v['reason']}"
            for name, v in verdict["votes"].items()
        ]
        return _not_assessable(
            tool,
            "The four library signals do not agree, so the chemistry cannot be called.",
            [
                "Chemistry is indeterminate: "
                f"{verdict['n_amplicon_votes']} signals point to amplicon, "
                f"{verdict['n_hybrid_votes']} to hybrid capture, "
                f"{verdict['n_abstentions']} abstain.",
                "No copy-number tool may run without a chemistry verdict, because "
                "depth-ratio copy-number calling is invalid on an amplicon library and "
                "nothing else can rule that out.",
                *dissent,
            ],
            digest,
            assumptions=[
                "Library chemistry is uniform across the sampled reads.",
                "The sampled regions are representative of the whole library.",
            ],
        )

    flags = _chemistry.chemistry_flags(chemistry)
    value = {"chemistry": chemistry, **flags, "evidence": evidence, "votes": verdict["votes"]}

    limits = [
        "Describes the library preparation only. It says nothing about specimen quality, "
        "tumour content, or whether any particular locus is well covered.",
    ]
    if chemistry == "amplicon":
        limits += [
            "Depth-ratio copy-number calling is INVALID on this library: per-amplicon read "
            "depth reflects PCR amplification efficiency, not input copy number.",
            "Deduplication must NOT be run. Amplicon reads sharing a start coordinate are "
            "independent molecules that share a primer, not PCR duplicates; marking them "
            f"would discard roughly {evidence['duplicate_fraction']:.0%} of the reads.",
            "Allele counts are only trustworthy after primer trimming. A variant under a "
            "primer is invisible, because the primer sequence replaces the template.",
        ]

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=EvidenceGrade.HIGH,
        actionability=ClinicalActionability.INFORMATIONAL,
        confidence_note=(
            f"Library is {chemistry}: "
            f"{verdict['n_amplicon_votes'] or verdict['n_hybrid_votes']} of four signals agree "
            f"with none dissenting (duplicate fraction {evidence['duplicate_fraction']:.3f}, "
            f"{evidence['distinct_starts_per_1000_fwd']:.1f} distinct starts per 1000 forward "
            f"reads, {evidence['top10_start_fraction']:.3f} of reads in the top 10 "
            f"start positions)."
        ),
        assumptions=[
            "Library chemistry is uniform across the sampled reads.",
            f"The {evidence['reads_examined']} sampled reads are representative of the library.",
            "Duplicate flags, where present, were set by an aligner or marking tool on this BAM.",
        ],
        limits=limits,
        input_digest=digest,
        value=value,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 2. extract_heterozygous_sites
# --------------------------------------------------------------------------- #


def extract_heterozygous_sites_impl(
    vcf_path: str,
    chemistry: dict,
    bam_path: str | None = None,
    min_depth: int = 200,
    baf_window: tuple[float, float] = (0.20, 0.80),
    block_window_bp: int = 1_000_000,
    purity_hint: float | None = None,
    synthetic_inputs: bool = False,
) -> dict[str, Any]:
    tool = "genomic-results.extract_heterozygous_sites"
    digest = compute_input_digest(
        {
            "vcf_path": vcf_path,
            "bam_path": bam_path,
            "chemistry": chemistry,
            "min_depth": min_depth,
            "baf_window": list(baf_window),
            "block_window_bp": block_window_bp,
            "purity_hint": purity_hint,
        }
    )

    try:
        _chemistry.require_chemistry(chemistry, tool)
    except _chemistry.ChemistryGateError as exc:
        return _not_assessable(
            tool,
            "No usable library-chemistry verdict was supplied.",
            [str(exc)],
            digest,
            synthetic=synthetic_inputs,
        )

    if not os.path.exists(vcf_path):
        return _not_assessable(
            tool,
            "The VCF could not be read.",
            [f"VCF not found: {vcf_path}"],
            digest,
            synthetic=synthetic_inputs,
        )

    try:
        out = _hetsites.extract_sites(
            vcf_path,
            chemistry,
            bam_path=bam_path,
            min_depth=min_depth,
            baf_window=baf_window,
            block_window_bp=block_window_bp,
            purity_hint=purity_hint,
        )
    except _chemistry.PysamUnavailable as exc:
        return _not_assessable(
            tool,
            "A BAM recount was requested but the BAM could not be read.",
            [str(exc)],
            digest,
            synthetic=synthetic_inputs,
        )

    if out["n_sites"] == 0:
        return _not_assessable(
            tool,
            "No informative germline heterozygous sites survived extraction.",
            [
                "No site met the depth and BAF-window criteria, so no copy-number "
                "inference is possible from this input.",
                f"Rejection counts: {out['rejections']}",
            ],
            digest,
            synthetic=synthetic_inputs,
        )

    needs_trimming = chemistry["primer_trimming_required"]
    recounted = out["bam_recount"]["performed"]

    assumptions = [
        "Sites carrying a dbSNP rs identifier are germline, not somatic.",
        f"At the purity involved, no somatic variant can reach the "
        f"{baf_window[0]:.2f}-{baf_window[1]:.2f} BAF window: a clonal heterozygous somatic "
        f"variant caps near purity/2 and a clonal homozygous one near purity.",
        f"Sites within {block_window_bp:,} bp on one chromosome share a haplotype and are "
        "one independent observation.",
        "Allele counts come from the AD field as exact integers, not from a rounded "
        "allele-fraction field.",
    ]
    limits = [
        "Germline heterozygous sites only. This says nothing about somatic variants.",
        f"{out['n_sites']} sites cluster into {out['n_blocks']} independent haplotype blocks. "
        f"The effective sample size is {out['n_blocks']}; quoting {out['n_sites']} would "
        "overstate power.",
        "Haplotype blocks are inferred from physical proximity, not from phasing. Without "
        "phased data the true block structure is unknown.",
    ]

    grade = EvidenceGrade.HIGH
    if needs_trimming and not recounted:
        grade = EvidenceGrade.MODERATE
        limits.append(
            "Chemistry requires primer trimming but no BAM was supplied, so allele counts "
            "come from the VCF untrimmed. Any locus sitting under a primer on one amplicon "
            "reports reference only there, biasing its allele fraction toward reference."
        )
        assumptions.append(
            "VCF allele counts are assumed unaffected by primer overlap — this is the "
            "assumption a BAM recount would remove."
        )

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=grade,
        actionability=ClinicalActionability.NONE,
        confidence_note=(
            f"{out['n_dbsnp_snv_candidates']} dbSNP SNV candidates reduced to {out['n_sites']} "
            f"heterozygous sites in {out['n_blocks']} independent haplotype blocks"
            + (
                ", with per-amplicon counts and primers trimmed."
                if recounted and needs_trimming
                else ", from VCF allele counts."
            )
        ),
        assumptions=assumptions,
        limits=limits + list(out["warnings"]),
        synthetic_inputs=synthetic_inputs,
        input_digest=digest,
        value=out,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 3. qc_heterozygous_sites
# --------------------------------------------------------------------------- #


def qc_heterozygous_sites_impl(
    sites: Sequence[dict],
    chemistry: dict,
    min_amplicon_depth: int = _blockqc.MIN_AMPLICON_DEPTH_FLOOR,
    block_alpha: float = 0.01,
    amplicon_alpha: float = 0.01,
    min_site_depth: int = _blockqc.DEFAULT_MIN_SITE_DEPTH,
    neutral_pool_exclude_arms: Sequence[str] = (),
    synthetic_inputs: bool = False,
) -> dict[str, Any]:
    tool = "genomic-results.qc_heterozygous_sites"
    digest = compute_input_digest(
        {
            "n_sites": len(sites),
            "chemistry": chemistry,
            "min_amplicon_depth": min_amplicon_depth,
            "block_alpha": block_alpha,
            "amplicon_alpha": amplicon_alpha,
            "min_site_depth": min_site_depth,
            "neutral_pool_exclude_arms": list(neutral_pool_exclude_arms),
        }
    )

    try:
        out = _blockqc.run_qc(
            sites,
            chemistry,
            min_amplicon_depth=min_amplicon_depth,
            block_alpha=block_alpha,
            amplicon_alpha=amplicon_alpha,
            min_site_depth=min_site_depth,
            neutral_pool_exclude_arms=neutral_pool_exclude_arms,
        )
    except (_chemistry.ChemistryGateError, ValueError) as exc:
        return _not_assessable(
            tool,
            "Quality control could not be applied.",
            [str(exc)],
            digest,
            synthetic=synthetic_inputs,
        )

    if out["n_sites"] == 0 or not out["overdispersion"]["fitted"]:
        return _not_assessable(
            tool,
            "No sites survived quality control, so no copy-neutral baseline could be fitted.",
            [
                f"{len(sites)} sites entered QC and {out['n_sites']} survived.",
                "Without a copy-neutral pool there is no null to test any region against.",
            ],
            digest,
            synthetic=synthetic_inputs,
        )

    od = out["overdispersion"]
    rule_b_blind = out["rule_b_coverage"]["sites_testable"] == 0
    single_site_blocks = sum(1 for b in out["block_report"] if b["verdict"] == "untestable")

    limits = [
        f"{single_site_blocks} blocks carry fewer than {_blockqc.MIN_SITES_FOR_BLOCK_TEST} "
        "sites and are structurally untestable under Rule A. They are retained but "
        "uncorroborated — a local artifact at such a locus is indistinguishable from a "
        "real event.",
        f"Read counts carry {od['noise_vs_binomial']:.1f}x the binomial scatter after QC. "
        "The residual is systematic, not sampling, and no additional depth removes it.",
        "Rule A tests magnitude homogeneity within a block. It cannot detect an artifact "
        "that shifts every site in a block by the same amount.",
    ]
    grade = EvidenceGrade.HIGH
    if rule_b_blind:
        grade = EvidenceGrade.MODERATE
        limits.append(
            "Rule B could not be applied to any site: it needs two or more independent "
            "primer pairs per locus, which requires BAM-derived amplicon counts. "
            "Single-site blocks therefore remain entirely unvetted."
        )

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=grade,
        actionability=ClinicalActionability.NONE,
        confidence_note=(
            f"{len(sites)} sites reduced to {out['n_sites']} in {out['n_blocks']} blocks; "
            f"{out['blocks_failing_rule_a']} blocks failed within-block concordance. "
            f"Noise fell to {od['noise_vs_binomial']:.1f}x the binomial floor "
            f"(concentration s = {od['concentration_s']:.0f})."
        ),
        assumptions=[
            "Sites within one haplotype block share a pair of parental chromosomes, so a "
            "real copy-number event gives them all the same |BAF - 0.5| magnitude.",
            "Scatter beyond the binomial term within a block indicates mapping pathology "
            "rather than a copy-number event.",
            "The arms excluded from the copy-neutral pool are the only ones plausibly "
            "carrying an event; the remainder is treated as null.",
            "The fitted beta-binomial concentration is constant genome-wide.",
        ],
        limits=limits,
        synthetic_inputs=synthetic_inputs,
        input_digest=digest,
        value=out,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 4. estimate_tumor_purity
# --------------------------------------------------------------------------- #


def estimate_tumor_purity_impl(
    drivers: Sequence[dict],
    copy_neutral_evidence: dict | None = None,
    synthetic_inputs: bool = False,
) -> dict[str, Any]:
    tool = "genomic-results.estimate_tumor_purity"
    digest = compute_input_digest(
        {
            "drivers": list(drivers),
            "copy_neutral_evidence": copy_neutral_evidence,
        }
    )

    try:
        out = _purity.estimate_purity(drivers, copy_neutral_evidence)
    except ValueError as exc:
        return _not_assessable(
            tool,
            "Purity could not be estimated from the supplied drivers.",
            [str(exc)],
            digest,
            synthetic=synthetic_inputs,
        )

    # The three assumptions. Emitted every time, without exception, because the
    # number is meaningless without them and looks entirely reasonable with them
    # missing.
    assumptions = [
        "Each driver variant is clonal — present in every tumour cell.",
        (
            "Each driver variant is heterozygous — one mutant allele per tumour genome."
            if drivers[0].get("assumed_zygosity", "heterozygous") == "heterozygous"
            else "Each driver variant is homozygous — two mutant alleles per tumour genome."
        ),
        "Each driver's locus is copy-neutral — two total copies in the tumour.",
    ]

    limits = [
        "An estimate from driver allele fractions, not a measured tumour cell fraction. "
        "A pathologist's estimate measures a different quantity and need not agree.",
        "Purity scales every downstream copy-number expectation linearly, so an error "
        "here propagates to every deviation threshold without appearing as an error.",
    ]

    grade = EvidenceGrade.HIGH
    if not out["all_loci_verified_copy_neutral"]:
        grade = EvidenceGrade.MODERATE
        limits.append(
            "Copy-neutrality is NOT verified for: "
            + "; ".join(out["copy_neutral_unverified"])
            + ". If such a locus sits on gained or lost ground, its allele fraction is not "
            "purity/2 and the estimate is biased in a direction this tool cannot determine."
        )

    inconsistent = [pw for pw in out["pairwise_consistency"] if pw["p"] < 0.05]
    if inconsistent:
        grade = EvidenceGrade.MODERATE
        limits.append(
            "Driver allele fractions differ significantly ("
            + "; ".join(f"{'/'.join(pw['drivers'])} p = {pw['p']:.3f}" for pw in inconsistent)
            + "), so at least one driver is subclonal or not on copy-neutral ground and the "
            "pooled estimate averages two different quantities."
        )

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=grade,
        actionability=ClinicalActionability.INFORMATIONAL,
        confidence_note=(
            f"Purity {out['purity']:.4f} (95% CI {out['purity_ci95'][0]:.4f}-"
            f"{out['purity_ci95'][1]:.4f}) from {len(out['per_driver'])} driver"
            f"{'s' if len(out['per_driver']) != 1 else ''} totalling "
            f"{out['total_alt_count']}/{out['total_depth']} reads"
            + (
                ", all on verified copy-neutral ground."
                if out["all_loci_verified_copy_neutral"]
                else ", not all of which sit on verified copy-neutral ground."
            )
        ),
        assumptions=assumptions,
        limits=limits,
        synthetic_inputs=synthetic_inputs,
        input_digest=digest,
        value=out,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 5. assess_cnv_detectability
# --------------------------------------------------------------------------- #


def assess_cnv_detectability_impl(
    purity: float,
    region_sites: Sequence[dict],
    overdispersion_s: float,
    chemistry: dict,
    synthetic_inputs: bool = False,
) -> dict[str, Any]:
    tool = "genomic-results.assess_cnv_detectability"
    digest = compute_input_digest(
        {
            "purity": purity,
            "n_sites": len(region_sites),
            "overdispersion_s": overdispersion_s,
            "chemistry": chemistry,
        }
    )

    try:
        out = _detectability.assess_detectability(purity, region_sites, overdispersion_s, chemistry)
    except (_chemistry.ChemistryGateError, ValueError) as exc:
        return _not_assessable(
            tool,
            "Detectability could not be assessed.",
            [str(exc)],
            digest,
            synthetic=synthetic_inputs,
        )

    if not out.get("n_sites"):
        return _not_assessable(
            tool,
            "The region carries no sites, so its power cannot be assessed.",
            ["No heterozygous sites in the region after quality control."],
            digest,
            synthetic=synthetic_inputs,
        )

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=EvidenceGrade.HIGH,
        actionability=ClinicalActionability.INFORMATIONAL,
        confidence_note=out["power_note"],
        assumptions=[
            f"Tumour purity is {purity:.4f}; every expected deviation is linear in it.",
            f"Beta-binomial concentration s = {overdispersion_s:.0f} applies to this region "
            "as fitted on the copy-neutral pool.",
            "Haplotype blocks are independent of one another.",
            "Power is quoted at 80% against a two-sided 5% test.",
        ],
        limits=[
            out["depth_note"],
            out["loss_gain_separation"]["note"],
            "Describes the power to detect a deviation of a given size. It does not make "
            "any statement about whether one is present.",
        ],
        detectability=Detectability(
            measurable=out["measurable"],
            min_detectable_effect=out["min_detectable_effect"],
            observed_noise_sd=out["per_site_sd"],
            independent_units=out["n_blocks"],
            unit_type="haplotype_block",
            power_note=out["power_note"],
        ),
        synthetic_inputs=synthetic_inputs,
        input_digest=digest,
        value=out,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 6. test_allelic_imbalance
# --------------------------------------------------------------------------- #


def allelic_imbalance_impl(
    region_sites: Sequence[dict],
    neutral_pool: Sequence[dict],
    overdispersion_s: float,
    purity: float,
    chemistry: dict,
    depth_evidence: dict | None = None,
    n_resample: int = 10_000,
    synthetic_inputs: bool = False,
) -> dict[str, Any]:
    tool = "genomic-results.test_allelic_imbalance"
    digest = compute_input_digest(
        {
            "n_region_sites": len(region_sites),
            "n_pool_sites": len(neutral_pool),
            "overdispersion_s": overdispersion_s,
            "purity": purity,
            "chemistry": chemistry,
            "depth_evidence": depth_evidence,
            "n_resample": n_resample,
        }
    )

    try:
        out = _imbalance.run_imbalance_test(
            region_sites,
            neutral_pool,
            overdispersion_s,
            purity,
            chemistry,
            depth_evidence=depth_evidence,
            n_resample=n_resample,
        )
    except _imbalance.DepthEvidenceRefused:
        # Deliberately not swallowed into a NOT_ASSESSABLE result. The caller
        # made an invalid call and needs to see that, not a graded refusal that
        # reads like a property of the specimen.
        raise
    except (_chemistry.ChemistryGateError, ValueError) as exc:
        return _not_assessable(
            tool,
            "The imbalance test could not be run.",
            [str(exc)],
            digest,
            synthetic=synthetic_inputs,
        )

    det = out["detectability"]
    limits = [
        f"This is a MAGNITUDE. {out['direction_note']}",
        det["depth_note"],
        f"Rests on {out['n_blocks']} independent haplotype blocks. Significance comes from "
        f"resampling whole blocks from a copy-neutral pool of "
        f"{out['null_distribution']['pool_blocks_available']}, not from an asymptotic test.",
    ]
    if not det["measurable"]:
        limits.append(
            f"No copy-number event is detectable at 80% power in this region: the minimum "
            f"detectable |BAF - 0.5| is {det['min_detectable_effect']:.4f} and the largest "
            f"expected deviation is {max(det['expected_deviation_by_event'].values()):.4f}. "
            "A null result here is uninformative."
        )

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=EvidenceGrade.MODERATE,
        actionability=ClinicalActionability.INFORMATIONAL,
        confidence_note=(
            f"Allelic imbalance {out['imbalance']:.4f} (95% CI {out['ci95'][0]:.4f}-"
            f"{out['ci95'][1]:.4f}, p = {out['p']:.4f}) across {out['n_sites']} sites in "
            f"{out['n_blocks']} independent blocks; direction {out['direction']}."
        ),
        assumptions=[
            f"Tumour purity is {purity:.4f}.",
            f"The copy-neutral pool is exchangeable with the region under test and its "
            f"fitted concentration s = {overdispersion_s:.0f} applies here.",
            "Each site's true shift is +d or -d with equal prior; the sign is unknowable "
            "because it depends on which parental allele the VCF happens to call ALT.",
            "Haplotype blocks are independent; sites within a block are not.",
        ],
        limits=limits,
        detectability=Detectability(
            measurable=det["measurable"],
            min_detectable_effect=det["min_detectable_effect"],
            observed_noise_sd=det["per_site_sd"],
            independent_units=out["n_blocks"],
            unit_type="haplotype_block",
            power_note=det["power_note"],
        ),
        synthetic_inputs=synthetic_inputs,
        input_digest=digest,
        value=out,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 7. compare_cnv_architectures
# --------------------------------------------------------------------------- #


def compare_cnv_architectures_impl(
    region_sites: Sequence[dict],
    overdispersion_s: float,
    candidate_breakpoints: Sequence[int] | None = None,
    synthetic_inputs: bool = False,
) -> dict[str, Any]:
    tool = "genomic-results.compare_cnv_architectures"
    digest = compute_input_digest(
        {
            "n_sites": len(region_sites),
            "overdispersion_s": overdispersion_s,
            "candidate_breakpoints": list(candidate_breakpoints or []),
        }
    )

    try:
        out = _architecture.compare_architectures(
            region_sites, overdispersion_s, candidate_breakpoints
        )
    except ValueError as exc:
        return _not_assessable(
            tool,
            "Architecture comparison could not be run.",
            [str(exc)],
            digest,
            synthetic=synthetic_inputs,
        )

    caution = out["caution"]
    limits = [
        "Ranks three candidate structures against each other. It does not establish that "
        "the winner is correct, only that it fits better than the two alternatives offered.",
        f"Fitted on {out['n_blocks']} independent haplotype blocks.",
    ]
    limits.extend(caution["reasons"])

    # A model comparison that fires its own caution is exploratory by
    # construction: it has told you the winner may rest on one locus.
    grade = EvidenceGrade.LOW if caution["fired"] else EvidenceGrade.MODERATE

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=grade,
        actionability=ClinicalActionability.INFORMATIONAL,
        confidence_note=(
            f"{out['best_model']} fits best (AIC {out['models'][0]['aic']:.2f}; next best "
            f"{out['models'][1]['model']} at delta-AIC {out['models'][1]['delta_aic']:.2f})"
            + (
                f", but the caution flag fired: {caution['reasons'][0]}"
                if caution["fired"]
                else "."
            )
        ),
        assumptions=[
            f"Beta-binomial concentration s = {overdispersion_s:.0f}, fitted elsewhere on "
            "the copy-neutral pool, applies within this region.",
            "At most one breakpoint exists in the region.",
            "A breakpoint falls between haplotype blocks, not inside one — a breakpoint "
            "within a block is not identifiable from these data.",
            "AIC charges the two segment deviations but not the searched breakpoint position.",
        ],
        limits=limits,
        synthetic_inputs=synthetic_inputs,
        input_digest=digest,
        value=out,
    ).to_dict()


# --------------------------------------------------------------------------- #
# 8. assess_um_prognostic_class
# --------------------------------------------------------------------------- #


def assess_um_prognostic_class_impl(
    chr3_status: str | None = None,
    chr8q_status: str | None = None,
    chr6p_status: str | None = None,
    chr1p_status: str | None = None,
    bap1_status: str | None = None,
    sf3b1_status: str | None = None,
    eif1ax_status: str | None = None,
    gene_expression_class: str | None = None,
    metastasis_confirmed: bool = False,
    metastasis_interval_years: float | None = None,
    synthetic_inputs: bool = False,
) -> dict[str, Any]:
    tool = "genomic-results.assess_um_prognostic_class"
    digest = compute_input_digest(
        {
            "chr3_status": chr3_status,
            "chr8q_status": chr8q_status,
            "chr6p_status": chr6p_status,
            "chr1p_status": chr1p_status,
            "bap1_status": bap1_status,
            "sf3b1_status": sf3b1_status,
            "eif1ax_status": eif1ax_status,
            "gene_expression_class": gene_expression_class,
            "metastasis_confirmed": metastasis_confirmed,
            "metastasis_interval_years": metastasis_interval_years,
        }
    )

    out = _prognostic.assess_prognostic_class(
        chr3_status=chr3_status,
        chr8q_status=chr8q_status,
        chr6p_status=chr6p_status,
        chr1p_status=chr1p_status,
        bap1_status=bap1_status,
        sf3b1_status=sf3b1_status,
        eif1ax_status=eif1ax_status,
        gene_expression_class=gene_expression_class,
        metastasis_confirmed=metastasis_confirmed,
        metastasis_interval_years=metastasis_interval_years,
    )

    if out["risk_class"] == "indeterminate":
        return _not_assessable(
            tool,
            "No prognostic marker reached a determined state, so no risk class can be assigned.",
            [
                "Every supplied marker was absent or undetermined.",
                *out["limits"],
            ],
            digest,
            assumptions=["Marker statuses were read as supplied, without imputation."],
            synthetic=synthetic_inputs,
        )

    confidence = (
        f"{out['risk_class'].replace('_', ' ')} in primary uveal melanoma. {out['risk_note']} "
        f"Management implication: {out['management_implication']}"
    )

    return GradedResult(
        tool=tool,
        tool_version=TOOL_VERSION,
        grade=EvidenceGrade.MODERATE,
        # Hard-coded, not a default. Chromosome 3 status estimates the risk that
        # a PRIMARY tumour will metastasise; it is not a therapy-selection
        # biomarker in established metastatic disease, and no caller may declare
        # otherwise through this tool.
        actionability=ClinicalActionability.PROGNOSTIC_ONLY,
        confidence_note=confidence,
        assumptions=[
            "Marker statuses are read as supplied; an undetermined marker is not counted "
            "as absent.",
            "Risk-class boundaries follow the primary-tumour uveal melanoma literature.",
            "A prior gene-expression class call, if supplied, measures a different quantity "
            "and is reported alongside rather than reconciled.",
        ],
        limits=out["limits"],
        synthetic_inputs=synthetic_inputs,
        input_digest=digest,
        value=out,
    ).to_dict()


__all__ = [
    "detect_library_chemistry_impl",
    "extract_heterozygous_sites_impl",
    "qc_heterozygous_sites_impl",
    "estimate_tumor_purity_impl",
    "assess_cnv_detectability_impl",
    "allelic_imbalance_impl",
    "compare_cnv_architectures_impl",
    "assess_um_prognostic_class_impl",
    "TOOL_VERSION",
]
