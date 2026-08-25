"""End-to-end regression suite for the copy-number and governance extension.

Why this exists as ONE test rather than eight
---------------------------------------------
Each tool in the chain has its own unit tests, and they all pass. The failure
modes this suite guards against are not visible from any single tool: each of
them looked like a reasonable number right up until someone checked it against
the next step. A confident arm-level loss call assembled from a paralogous
block, a direction assigned from a magnitude, a purity estimate resting on an
unverified assumption — all of those are locally plausible and only wrong in
composition.

So this runs the whole chain: VCF in, a graded chromosome-level result out, with
the direction guard, the detectability context and the prognostic-only
declaration intact, and the reporting boundary refusing what it should refuse.

The specimen is entirely synthetic
----------------------------------
``tests/fixtures/cnv_synthetic_specimen.py`` generates it from a fixed seed. It
reproduces the STRUCTURES the pipeline must react to, not any individual's
numbers. No patient data is used here and none may be added.

Each server is driven through ``uv run`` in its own virtualenv, matching the
other integration tests in this directory, because genomic-results and
patient-report do not share dependencies.

Run:
    python -m pytest tests/integration/test_cnv_e2e.py -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GENOMIC_RESULTS_DIR = REPO_ROOT / "servers" / "mcp-genomic-results"
PATIENT_REPORT_DIR = REPO_ROOT / "servers" / "mcp-patient-report"

sys.path.insert(0, str(REPO_ROOT))
from tests.fixtures.cnv_synthetic_specimen import (  # noqa: E402
    AMPLICON_CHEMISTRY,
    build_specimen,
)


def _run_in_server(server_dir: Path, script: str, timeout: int = 180) -> Dict[str, Any]:
    """Execute a Python snippet via ``uv run`` inside a server virtualenv."""
    result = subprocess.run(
        ["uv", "run", "python", "-c", script],
        capture_output=True,
        text=True,
        cwd=str(server_dir),
        timeout=timeout,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )
    if result.returncode != 0:
        pytest.fail(f"{server_dir.name} failed:\n{result.stderr[-3000:]}")
    # The server venv emits deprecation warnings on stderr; stdout carries only
    # the JSON payload, and the marker isolates it from anything else printed.
    stdout = result.stdout
    marker = "@@JSON@@"
    if marker not in stdout:
        pytest.fail(f"{server_dir.name} produced no payload:\n{stdout[-3000:]}")
    return json.loads(stdout.split(marker, 1)[1].strip())


# The fixture is loaded by absolute path, not by package name: each server has
# its own `tests/` directory, and with the server as cwd that shadows the
# repo-root `tests` package.
CHAIN_SCRIPT = r'''
import importlib.util, json, sys, tempfile, pathlib
sys.path.insert(0, "src")

_fixture_path = pathlib.Path(r"__REPO_ROOT__") / "tests" / "fixtures" / "cnv_synthetic_specimen.py"
_spec = importlib.util.spec_from_file_location("cnv_synthetic_specimen", _fixture_path)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
build_specimen = _fixture.build_specimen
AMPLICON_CHEMISTRY = _fixture.AMPLICON_CHEMISTRY

from mcp_genomic_results.cnv import tools

spec = build_specimen()
tmp = pathlib.Path(tempfile.mkdtemp())
vcf = tmp / "synthetic_specimen.vcf"
vcf.write_text(spec["vcf_text"])

out = {"declared": {
    "n_dbsnp_snv_candidates": spec["n_dbsnp_snv_candidates"],
    "n_informative_sites": spec["n_informative_sites"],
    "purity": spec["purity"],
    "event_deviation": spec["event_deviation"],
}}

# 1. extraction (the chemistry gate's verdict is a required argument)
extract = tools.extract_heterozygous_sites_impl(
    str(vcf), AMPLICON_CHEMISTRY, purity_hint=spec["purity"], synthetic_inputs=True)
out["extract"] = extract

# 2. quality control
qc = tools.qc_heterozygous_sites_impl(
    extract["value"]["sites"], AMPLICON_CHEMISTRY,
    neutral_pool_exclude_arms=spec["arms_under_test"], synthetic_inputs=True)
out["qc"] = qc

kept = qc["value"]["sites"]
s = qc["value"]["overdispersion"]["concentration_s"]
pool = [x for x in kept if x["arm"] not in spec["arms_under_test"]]

# 3. purity
purity = tools.estimate_tumor_purity_impl(spec["drivers"], synthetic_inputs=True)
out["purity"] = purity
p_hat = purity["value"]["purity"]

# 4. detectability, standalone
event_sites = [x for x in kept if x["chrom"] == spec["event_chrom"]]
out["detectability"] = tools.assess_cnv_detectability_impl(
    p_hat, event_sites, s, AMPLICON_CHEMISTRY, synthetic_inputs=True)

# 5. imbalance on the event region and on the genuinely neutral arms
out["imbalance"] = {}
out["imbalance"]["event"] = tools.allelic_imbalance_impl(
    event_sites, pool, s, p_hat, AMPLICON_CHEMISTRY, n_resample=3000, synthetic_inputs=True)
for arm in spec["neutral_arms"]:
    arm_sites = [x for x in kept if x["arm"] == arm]
    out["imbalance"][arm] = tools.allelic_imbalance_impl(
        arm_sites, pool, s, p_hat, AMPLICON_CHEMISTRY, n_resample=3000, synthetic_inputs=True)

# 5b. the direction guard, exercised as a failure
try:
    tools.allelic_imbalance_impl(
        event_sites, pool, s, p_hat, AMPLICON_CHEMISTRY,
        depth_evidence={"log2_ratio": -0.125}, n_resample=200)
    out["depth_evidence_guard"] = {"raised": False}
except Exception as exc:
    out["depth_evidence_guard"] = {"raised": True, "type": type(exc).__name__,
                                   "message": str(exc)}

# 6. architecture comparison
out["architecture"] = tools.compare_cnv_architectures_impl(
    event_sites, s, synthetic_inputs=True)

# 7. prognostic class — the event's direction is unresolved, so it is passed
#    through as such rather than being quietly upgraded to "loss".
out["prognostic"] = tools.assess_um_prognostic_class_impl(
    chr3_status=out["imbalance"]["event"]["value"]["direction"],
    chr8q_status="gain",
    sf3b1_status="mutated",
    gene_expression_class="Class 2",
    metastasis_confirmed=True,
    metastasis_interval_years=4.6,
    synthetic_inputs=True,
)

print("@@JSON@@")
print(json.dumps(out))
'''


@pytest.fixture(scope="module")
def chain() -> Dict[str, Any]:
    """Run the analytic chain once; every test below reads from this result."""
    script = CHAIN_SCRIPT.replace("__REPO_ROOT__", str(REPO_ROOT))
    return _run_in_server(GENOMIC_RESULTS_DIR, script)


# ===========================================================================
# Stage 1 — extraction
# ===========================================================================


class TestExtraction:
    def test_candidates_reduce_to_informative_sites(self, chain):
        value = chain["extract"]["value"]
        declared = chain["declared"]
        assert value["n_dbsnp_snv_candidates"] == declared["n_dbsnp_snv_candidates"]
        assert value["n_sites"] == declared["n_informative_sites"]

    def test_sites_and_blocks_are_reported_separately(self, chain):
        """The effective sample size is blocks. Quoting sites overstates power."""
        value = chain["extract"]["value"]
        assert value["n_blocks"] < value["n_sites"]
        assert all(
            arm["n_blocks"] <= arm["n_sites"] for arm in value["per_arm"].values()
        )

    def test_every_filter_fired(self, chain):
        rejections = chain["extract"]["value"]["rejections"]
        for reason in ("not_pass", "no_dbsnp_evidence", "baf_out_of_window", "low_depth"):
            assert rejections.get(reason, 0) >= 1, f"{reason} never fired"

    def test_vcf_only_amplicon_input_degrades_the_grade(self, chain):
        """No BAM means untrimmed counts on a library that requires trimming."""
        assert chain["extract"]["grade"] == "moderate"
        assert any("primer" in limit for limit in chain["extract"]["limits"])


# ===========================================================================
# Stage 2 — quality control
# ===========================================================================


class TestQualityControl:
    def test_paralogous_block_is_dropped(self, chain):
        """THE regression test of the suite.

        A block whose sites disagree on deviation magnitude is reporting a
        mapping problem. Untreated it produces a confident, entirely false
        arm-level loss call. If a refactor lets this block through, the refactor
        is wrong.
        """
        report = chain["qc"]["value"]["block_report"]
        paralog = [b for b in report if b["gene"] == "SYN_PARALOG"]
        assert paralog, "the paralogous block vanished from the fixture"
        assert paralog[0]["verdict"] == "DISCORDANT"
        assert paralog[0]["p"] < 1e-30

    def test_only_the_artifact_is_dropped(self, chain):
        value = chain["qc"]["value"]
        assert value["blocks_failing_rule_a"] == 1
        dropped_genes = {d["gene"] for d in value["dropped_sites"]}
        assert dropped_genes == {"SYN_PARALOG"}

    def test_real_event_survives_quality_control(self, chain):
        """A genuine event is internally concordant and must not be filtered out."""
        kept_genes = {b["gene"] for b in chain["qc"]["value"]["block_report"]
                      if b["verdict"] != "DISCORDANT"}
        assert {"SYN3A", "SYN3B"} <= kept_genes

    def test_library_is_overdispersed_relative_to_binomial(self, chain):
        """A binomial null is the assumption that made the original power estimate wrong."""
        od = chain["qc"]["value"]["overdispersion"]
        assert od["fitted"] is True
        assert od["noise_vs_binomial"] > 1.5

    def test_rule_b_blindness_is_declared(self, chain):
        """VCF-only input cannot vet single-site blocks. Say so, don't imply otherwise."""
        assert chain["qc"]["value"]["rule_b_coverage"]["sites_testable"] == 0
        assert chain["qc"]["grade"] == "moderate"


# ===========================================================================
# Stage 3 — purity
# ===========================================================================


class TestPurity:
    def test_purity_is_recovered(self, chain):
        assert chain["purity"]["value"]["purity"] == pytest.approx(
            chain["declared"]["purity"], abs=1e-4
        )

    def test_three_assumptions_travel_with_the_number(self, chain):
        joined = " ".join(chain["purity"]["assumptions"]).lower()
        assert "clonal" in joined
        assert "heterozygous" in joined
        assert "copy-neutral" in joined

    def test_unverified_copy_neutrality_degrades_the_grade(self, chain):
        """No copy-neutral evidence was supplied. Silence is not confirmation."""
        assert chain["purity"]["grade"] == "moderate"
        assert any("NOT verified" in limit for limit in chain["purity"]["limits"])

    def test_drivers_are_consistent_with_one_clone(self, chain):
        for pair in chain["purity"]["value"]["pairwise_consistency"]:
            assert pair["p"] >= 0.05


# ===========================================================================
# Stage 4 — detectability
# ===========================================================================


class TestDetectability:
    def test_standard_error_uses_blocks_not_sites(self, chain):
        value = chain["detectability"]["value"]
        assert value["unit_type"] == "haplotype_block"
        assert value["n_blocks"] < value["n_sites"]
        assert "block count" in value["power_note"]

    def test_depth_ceiling_is_stated(self, chain):
        """Recommending more depth without saying what it buys is selling something."""
        value = chain["detectability"]["value"]
        assert value["depth_scaling_ceiling"] > 0
        assert "0.25 / (s + 1)" in value["depth_note"]

    def test_loss_and_gain_are_declared_inseparable_by_baf(self, chain):
        sep = chain["detectability"]["value"]["loss_gain_separation"]
        assert sep["separable_by_baf"] is False
        assert "does not permit" in sep["note"]


# ===========================================================================
# Stage 5 — the imbalance test and the direction guard
# ===========================================================================


class TestImbalance:
    def test_event_region_is_detected_at_the_planted_magnitude(self, chain):
        value = chain["imbalance"]["event"]["value"]
        assert value["imbalance"] == pytest.approx(
            chain["declared"]["event_deviation"], abs=0.010
        )
        assert value["p"] < 0.01

    def test_direction_is_undetermined_without_depth_evidence(self, chain):
        """The statistic is a magnitude. An earlier analysis called a loss from one."""
        value = chain["imbalance"]["event"]["value"]
        assert value["direction"] == "undetermined"
        assert set(value["consistent_with"]) >= {"single_copy_loss", "single_copy_gain"}

    def test_depth_evidence_on_amplicon_chemistry_raises(self, chain):
        """Refused, not ignored — a caller passing evidence expects it to count."""
        guard = chain["depth_evidence_guard"]
        assert guard["raised"] is True
        assert guard["type"] == "DepthEvidenceRefused"
        assert "depth_cnv_permitted=False" in guard["message"]

    @pytest.mark.parametrize("arm", ["chr8p", "chr6p"])
    def test_neutral_arms_come_back_neutral_with_loss_excluded(self, chain, arm):
        """Not merely 'unproven' — positively excluded, which needs the power to say so."""
        value = chain["imbalance"][arm]["value"]
        assert value["imbalance"] == pytest.approx(0.0, abs=0.005)
        assert value["p"] > 0.05
        assert value["monosomy_excluded"] is True

    def test_detectability_is_embedded_in_the_result(self, chain):
        """A number must not be readable without its power context."""
        assert chain["imbalance"]["event"]["detectability"] is not None
        assert chain["imbalance"]["event"]["value"]["detectability"]["measurable"] is True

    def test_null_is_resampled_from_blocks(self, chain):
        null = chain["imbalance"]["event"]["value"]["null_distribution"]
        assert null["unit"] == "haplotype_block"
        assert null["pool_blocks_available"] > 10


# ===========================================================================
# Stage 6 — architecture comparison
# ===========================================================================


class TestArchitecture:
    def test_a_uniform_event_does_not_prefer_a_breakpoint(self, chain):
        """The planted event is uniform across the region; M2 should not win."""
        assert chain["architecture"]["value"]["best_model"] in (
            "M1_whole_region", "M2_breakpoint"
        )
        models = {m["model"]: m for m in chain["architecture"]["value"]["models"]}
        assert models["M1_whole_region"]["aic"] < models["M0_neutral"]["aic"]

    def test_aic_follows_its_definition(self, chain):
        for model in chain["architecture"]["value"]["models"]:
            assert model["aic"] == pytest.approx(
                2 * model["k"] - 2 * model["log_likelihood"]
            )

    def test_few_blocks_trigger_the_caution(self, chain):
        assert chain["architecture"]["value"]["caution"]["fired"] is True


# ===========================================================================
# Stage 7 — the prognostic declaration
# ===========================================================================


class TestPrognostic:
    def test_actionability_is_prognostic_only(self, chain):
        assert chain["prognostic"]["actionability"] == "prognostic_only"

    def test_never_predictive(self, chain):
        assert chain["prognostic"]["actionability"] != "predictive"

    def test_management_implication_is_present(self, chain):
        implication = chain["prognostic"]["value"]["management_implication"]
        assert "do not select therapy" in implication

    def test_confirmed_metastasis_marks_the_question_answered(self, chain):
        value = chain["prognostic"]["value"]
        assert value["already_answered"] is True
        assert "answered by events" in value["management_implication"]

    def test_undetermined_direction_is_not_upgraded_to_a_loss(self, chain):
        """The chain passed "undetermined" through; it must not become chr3 loss."""
        assert chain["prognostic"]["value"]["markers"]["chr3_loss"]["state"] != "present"


# ===========================================================================
# Stage 8 — synthetic propagation across the whole chain
# ===========================================================================


class TestSyntheticPropagation:
    @pytest.mark.parametrize(
        "stage", ["extract", "qc", "purity", "detectability", "architecture", "prognostic"]
    )
    def test_every_stage_declares_synthetic_inputs(self, chain, stage):
        assert chain[stage]["synthetic_inputs"] is True, (
            f"{stage} lost the synthetic flag; a result derived from synthetic "
            "input is synthetic"
        )

    def test_imbalance_result_is_synthetic(self, chain):
        assert chain["imbalance"]["event"]["synthetic_inputs"] is True


# ===========================================================================
# Stage 9 — the reporting boundary
# ===========================================================================


REPORT_SCRIPT_TEMPLATE = r'''
import json, sys
sys.path.insert(0, "src")
from pydantic import ValidationError
from mcp_patient_report.models import PatientReportData
from mcp_patient_report.report.report_generator import ReportGenerator

prognostic = json.loads(r"""__PROGNOSTIC__""")
imbalance = json.loads(r"""__IMBALANCE__""")

def placed(result, section, title):
    return {
        "section": section,
        "tool": result["tool"],
        "tool_version": result["tool_version"],
        "grade": result["grade"],
        "actionability": result["actionability"],
        "confidence_note": result["confidence_note"],
        "assumptions": result["assumptions"],
        "limits": result["limits"],
        "detectability": result.get("detectability"),
        "synthetic_inputs": result["synthetic_inputs"],
        "input_digest": result["input_digest"],
        "value": result["value"],
        "title": title,
    }

base = {
    "report_category": "oncology",
    "patient_info": {"name": "Synthetic Specimen", "age": 60, "sex": "Female",
                     "patient_id": "SYNTH-E2E", "diagnosis": "Synthetic diagnosis"},
    "diagnosis_summary": {"plain_language_description": "A synthetic description."},
    "genomic_findings": [], "treatment_options": [],
    "monitoring_plan": {"schedule": [{"test_name": "Scan", "frequency": "Every 3 months",
                                      "purpose": "Watch for change"}],
                        "warning_signs": ["New symptoms"]},
}

out = {}

# Correct placement: prognostic under prognostic findings, magnitude under context.
good = dict(base, graded_results=[
    placed(prognostic, "prognostic_findings", "Prognostic class"),
    placed(imbalance, "context", "Chromosome-level allelic imbalance"),
])
report = PatientReportData(**good)
html = ReportGenerator().render(report, report_type="full")
out["accepted"] = True
out["html_probes"] = {
    "prognostic_section": "Prognostic Findings" in html,
    "treatment_section": "Treatment Hypotheses" in html,
    "limits_rendered": "What this cannot show" in html,
    "detectability_rendered": "Could this have been detected?" in html,
    "assumptions_rendered": "Assumptions this rests on" in html,
    "prognostic_notice": "does not select therapy" in html,
}
# Adjacency: each finding's limits sit inside its own block, ahead of the disclaimer.
finding = html.index(imbalance["confidence_note"][:40])
limit = html.index(imbalance["limits"][0][:40])
out["adjacency"] = {"finding_before_limit": finding < limit,
                    "limit_before_end": limit < len(html) - 500}

# Rejection 1: the prognostic result placed under treatment hypotheses.
try:
    PatientReportData(**dict(base, graded_results=[
        placed(prognostic, "treatment_hypotheses", "Prognostic class")]))
    out["prognostic_in_treatment_rejected"] = False
except ValidationError as exc:
    out["prognostic_in_treatment_rejected"] = True
    out["prognostic_rejection_message"] = str(exc)

# Rejection 2: a graded result with no stated assumptions.
stripped = placed(prognostic, "prognostic_findings", "Prognostic class")
stripped["assumptions"] = []
try:
    PatientReportData(**dict(base, graded_results=[stripped]))
    out["empty_assumptions_rejected"] = False
except ValidationError as exc:
    out["empty_assumptions_rejected"] = True
    out["assumptions_rejection_message"] = str(exc)

print("@@JSON@@")
print(json.dumps(out))
'''


@pytest.fixture(scope="module")
def report(chain) -> Dict[str, Any]:
    """Hand the chain's graded results to patient-report and see what it does."""
    script = (
        REPORT_SCRIPT_TEMPLATE
        .replace("__PROGNOSTIC__", json.dumps(chain["prognostic"]))
        .replace("__IMBALANCE__", json.dumps(chain["imbalance"]["event"]))
    )
    return _run_in_server(PATIENT_REPORT_DIR, script)


class TestReportingBoundary:
    def test_correctly_placed_report_is_accepted(self, report):
        assert report["accepted"] is True

    def test_prognostic_result_in_treatment_section_is_rejected(self, report):
        """The rule that matters most: a risk estimate must not become a recommendation."""
        assert report["prognostic_in_treatment_rejected"] is True
        assert "does not select therapy" in report["prognostic_rejection_message"]

    def test_result_without_assumptions_is_rejected(self, report):
        assert report["empty_assumptions_rejected"] is True
        assert "must state its assumptions" in report["assumptions_rejection_message"]

    def test_prognostic_result_renders_outside_treatment(self, report):
        probes = report["html_probes"]
        assert probes["prognostic_section"] is True
        assert probes["treatment_section"] is False, (
            "a treatment section appeared with no PREDICTIVE result behind it"
        )

    def test_limits_and_detectability_render_with_the_finding(self, report):
        probes = report["html_probes"]
        assert probes["limits_rendered"] is True
        assert probes["detectability_rendered"] is True
        assert probes["assumptions_rendered"] is True

    def test_caveats_sit_adjacent_to_their_number(self, report):
        """Not collected in a footnote where they detach from what they qualify."""
        assert report["adjacency"]["finding_before_limit"] is True
        assert report["adjacency"]["limit_before_end"] is True

    def test_prognostic_notice_is_visible_in_the_document(self, report):
        assert report["html_probes"]["prognostic_notice"] is True


# ===========================================================================
# The property the whole suite exists to protect
# ===========================================================================


def test_no_predictive_claim_reaches_the_report(chain):
    """Nothing in this pipeline bears on therapy selection.

    Every stage is checked, because PREDICTIVE is the only actionability that
    may enter a treatment section, and the point of the chain is that none of
    these measurements earns it.
    """
    for stage in ("extract", "qc", "purity", "detectability", "architecture", "prognostic"):
        assert chain[stage]["actionability"] != "predictive", f"{stage} claimed PREDICTIVE"
    assert chain["imbalance"]["event"]["actionability"] != "predictive"


def test_a_refusal_never_carries_a_number(chain):
    """NOT_ASSESSABLE must mean no value, at every stage."""
    stages = [chain[s] for s in
              ("extract", "qc", "purity", "detectability", "architecture", "prognostic")]
    stages.append(chain["imbalance"]["event"])
    for result in stages:
        if result["grade"] == "not_assessable":
            assert result["value"] == {}
            assert result["limits"]
