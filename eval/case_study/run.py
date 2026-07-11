"""
Case Study Validation — PAT001 & PAT002

Asks Claude Sonnet 4.6 twelve clinically unambiguous binary questions under
two conditions:
  - full_platform: patient narrative + structured tool outputs
  - base_llm: patient narrative only (no tool outputs)

Scores accuracy in both conditions. Prints and saves the result table.

Usage:
    ANTHROPIC_API_KEY=sk-... python eval/case_study/run.py

Or with the env already set:
    python eval/case_study/run.py

Model is always claude-sonnet-4-6 (set via EVAL_MODEL env override if needed).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Optional

# ── Configuration ───────────────────────────────────────────────────────

MODEL = os.environ.get("EVAL_MODEL", "claude-sonnet-4-6")
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
RESULTS_DIR = Path(__file__).parent / "results"

# ── Patient narratives ──────────────────────────────────────────────────

PAT001_NARRATIVE = (
    "Sarah Anderson, 58F, Stage IV high-grade serous ovarian carcinoma (HGSOC). "
    "Diagnosed 2024, post-debulking surgery + carboplatin/paclitaxel x6 cycles. "
    "Germline BRCA1 pathogenic variant confirmed. Family history: mother ovarian "
    "cancer age 52, maternal aunt breast cancer age 47."
)

PAT002_NARRATIVE = (
    "Michelle Thompson, 42F, Stage IIA (T2N0M0) ER+/PR+/HER2- invasive ductal "
    "carcinoma (IDC). Diagnosed 2026, post-lumpectomy + sentinel node biopsy "
    "(0/3 positive). BRCA2 c.5946delT germline pathogenic variant confirmed. "
    "ER 85%, PR 70%, HER2 negative (IHC 1+). Ki-67 28%."
)

# ── Canonical tool outputs (from fixtures) ──────────────────────────────

PAT001_TOOL_OUTPUTS = """
Genomic Results (mcp-genomic-results):
  brca1_status: germline pathogenic variant
  hrd_score: 54
  tmb_mut_per_mb: 47.3 (POLE-corrected)
  somatic_variants: TP53 R175H (VAF 0.82)
  cnv_calls: CCNE1 amplification (log2 ratio = 2.1)

Neoantigen Prediction (mcp-neoantigen):
  top_peptide: RMPEAAPPV (from TP53 R175H)
  hla_allele: HLA-A*02:01
  ic50_nm: 7.8 (strong binder, threshold <50nM)
  binding_rank: 0.12%

Immune Deconvolution (mcp-cibersortx):
  cd8_t_cells: 30%
  regulatory_t_cells: 25.6%
  cd8_treg_ratio: 1.17
  macrophages: 43%

Spatial Transcriptomics (mcp-spatialtools):
  spot_count: 900
  morans_i_global: -0.0033
"""

PAT002_TOOL_OUTPUTS = """
Genomic Results (mcp-genomic-results):
  brca2_germline: c.5946delT (pathogenic)
  hrd_score: 35
  tmb_mut_per_mb: 3.8
  somatic_variants: PIK3CA H1047R (VAF 0.31)
  cnv_calls: CCND1 amplification (log2 ratio = 1.62)

Spatial Transcriptomics (mcp-spatialtools):
  spot_count: 900
  esr1_moran_i: 0.42 (spatially clustered, threshold >0.3)
  spatial_regions: 7

Immune Deconvolution (mcp-cibersortx):
  immune_evasion_score: 0.41
  luminal_stability_score: 0.78

Perturbation Prediction (mcp-perturbation):
  most_actionable_target: CDK4
  perturbations_tested: 5
"""

# ── Questions ───────────────────────────────────────────────────────────

QUESTIONS = [
    # PAT001 (Q1-Q6)
    {
        "id": "Q1", "patient": "PAT001",
        "question": "Is this patient eligible for olaparib based on germline BRCA1 status?",
        "ground_truth": "Yes",
        "guideline": "FDA 2018; NCCN Ovarian v2024",
    },
    {
        "id": "Q2", "patient": "PAT001",
        "question": "Does TMB exceed the pembrolizumab 10 mut/Mb threshold?",
        "ground_truth": "Yes",
        "guideline": "FDA 2020 TMB-H approval",
    },
    {
        "id": "Q3", "patient": "PAT001",
        "question": "Does HRD score meet myChoice CDx eligibility (≥42)?",
        "ground_truth": "Yes",
        "guideline": "myChoice CDx FDA 2020",
    },
    {
        "id": "Q4", "patient": "PAT001",
        "question": "Does the top neoantigen meet strong MHC-I binder threshold (IC50 < 50nM)?",
        "ground_truth": "Yes",
        "guideline": "IEDB/NetMHCpan 4.1",
    },
    {
        "id": "Q5", "patient": "PAT001",
        "question": "Is CD8:Treg ratio above 1.0 (immunologically active)?",
        "ground_truth": "Yes",
        "guideline": "Galon et al. 2006 Science",
    },
    {
        "id": "Q6", "patient": "PAT001",
        "question": "Is CCNE1 amplification present?",
        "ground_truth": "Yes",
        "guideline": "TCGA HGSOC 2011",
    },
    # PAT002 (Q7-Q12)
    {
        "id": "Q7", "patient": "PAT002",
        "question": "Does HRD score meet myChoice CDx eligibility (≥42)?",
        "ground_truth": "No",
        "guideline": "myChoice CDx FDA 2020",
    },
    {
        "id": "Q8", "patient": "PAT002",
        "question": "Is patient eligible for olaparib based on BRCA2 pathogenic variant despite HRD<42?",
        "ground_truth": "Yes",
        "guideline": "FDA 2022 OlympiA; NCCN Breast v2024",
    },
    {
        "id": "Q9", "patient": "PAT002",
        "question": "Is PIK3CA H1047R present?",
        "ground_truth": "Yes",
        "guideline": "COSMIC hotspot; FDA 2019 SOLAR-1",
    },
    {
        "id": "Q10", "patient": "PAT002",
        "question": "Does TMB exceed the pembrolizumab 10 mut/Mb threshold?",
        "ground_truth": "No",
        "guideline": "FDA 2020 TMB-H approval",
    },
    {
        "id": "Q11", "patient": "PAT002",
        "question": "Is ESR1 expression spatially clustered (Moran's I > 0.3)?",
        "ground_truth": "Yes",
        "guideline": "Spatial autocorrelation; Galon 2006",
    },
    {
        "id": "Q12", "patient": "PAT002",
        "question": "Is CCND1 amplification present?",
        "ground_truth": "Yes",
        "guideline": "TCGA BRCA; CDK4/6 inhibitor evidence",
    },
]

# ── Claude API call ─────────────────────────────────────────────────────


def call_claude(system: str, user: str) -> str:
    """Call Claude API, return raw text response."""
    if not API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": MODEL,
            "max_tokens": 50,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }).encode(),
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
            "anthropic-version": "2023-06-01",
        },
    )
    resp = urllib.request.urlopen(req, timeout=30)
    result = json.loads(resp.read())
    return result.get("content", [{}])[0].get("text", "").strip()


def parse_yes_no(text: str) -> str | None:
    """Parse a Yes/No answer from Claude's response."""
    t = text.strip().lower()
    if t.startswith("yes"):
        return "Yes"
    if t.startswith("no"):
        return "No"
    # Check first word
    first = t.split()[0] if t.split() else ""
    if first in ("yes", "yes.", "yes,"):
        return "Yes"
    if first in ("no", "no.", "no,"):
        return "No"
    return None


# ── Run eval ────────────────────────────────────────────────────────────


def run_eval():
    """Run all 12 questions under both conditions."""
    system_prompt = "You are a clinical genomics assistant. Answer only Yes or No."

    narratives = {"PAT001": PAT001_NARRATIVE, "PAT002": PAT002_NARRATIVE}
    tool_outputs = {"PAT001": PAT001_TOOL_OUTPUTS, "PAT002": PAT002_TOOL_OUTPUTS}

    results = []

    for q in QUESTIONS:
        patient = q["patient"]
        narrative = narratives[patient]
        tools = tool_outputs[patient]

        # ── full_platform ───────────────────────────────────────────
        fp_user = (
            f"Patient: {narrative}\n\n"
            f"Tool outputs:\n{tools}\n\n"
            f"Question: {q['question']}\n"
            f"Answer (Yes or No):"
        )
        fp_raw = call_claude(system_prompt, fp_user)
        fp_answer = parse_yes_no(fp_raw)

        # ── base_llm ───────────────────────────────────────────────
        bl_user = (
            f"Patient: {narrative}\n\n"
            f"Question: {q['question']}\n"
            f"Answer (Yes or No):"
        )
        bl_raw = call_claude(system_prompt, bl_user)
        bl_answer = parse_yes_no(bl_raw)

        gt = q["ground_truth"]
        fp_correct = fp_answer == gt if fp_answer else False
        bl_correct = bl_answer == gt if bl_answer else False

        results.append({
            "id": q["id"],
            "patient": patient,
            "question": q["question"],
            "ground_truth": gt,
            "guideline": q["guideline"],
            "full_platform_raw": fp_raw,
            "full_platform_answer": fp_answer,
            "full_platform_correct": fp_correct,
            "base_llm_raw": bl_raw,
            "base_llm_answer": bl_answer,
            "base_llm_correct": bl_correct,
        })

        mark_fp = "correct" if fp_correct else ("WRONG" if fp_answer else "UNPARSEABLE")
        mark_bl = "correct" if bl_correct else ("WRONG" if bl_answer else "UNPARSEABLE")
        print(f"  [{q['id']}] GT={gt:3s}  FP={fp_answer or '?':3s} ({mark_fp})  BL={bl_answer or '?':3s} ({mark_bl})")

    return results


def format_table(results: list) -> str:
    """Format results as the output table."""
    fp_correct = sum(1 for r in results if r["full_platform_correct"])
    bl_correct = sum(1 for r in results if r["base_llm_correct"])
    n = len(results)

    pat001 = [r for r in results if r["patient"] == "PAT001"]
    pat002 = [r for r in results if r["patient"] == "PAT002"]
    fp_pat001 = sum(1 for r in pat001 if r["full_platform_correct"])
    bl_pat001 = sum(1 for r in pat001 if r["base_llm_correct"])
    fp_pat002 = sum(1 for r in pat002 if r["full_platform_correct"])
    bl_pat002 = sum(1 for r in pat002 if r["base_llm_correct"])

    lines = []
    lines.append(f"Table A (Case Study) — Accuracy on Clinically Unambiguous Questions (n={n})")
    lines.append(f"Model: {MODEL}")
    lines.append("")
    lines.append(f"{'Condition':<42} {'Accuracy':>10}")
    lines.append(f"{'-'*52}")
    lines.append(f"{'Full platform (Sonnet 4.6 + tools)':<42} {fp_correct}/{n} ({fp_correct/n*100:.1f}%)")
    lines.append(f"{'Base LLM (Sonnet 4.6, no tools)':<42} {bl_correct}/{n} ({bl_correct/n*100:.1f}%)")
    lines.append(f"{'Majority-class baseline (always Yes)':<42} 10/{n} (83.3%)")
    lines.append("")
    lines.append("By patient:")
    lines.append(f"  PAT001 (n=6): full_platform={fp_pat001}/6, base_llm={bl_pat001}/6")
    lines.append(f"  PAT002 (n=6): full_platform={fp_pat002}/6, base_llm={bl_pat002}/6")
    lines.append("")
    lines.append("Per-question breakdown:")

    for r in results:
        fp_mark = "\u2713" if r["full_platform_correct"] else "\u2717"
        bl_mark = "\u2713" if r["base_llm_correct"] else "\u2717"
        fp_ans = r["full_platform_answer"] or "?"
        bl_ans = r["base_llm_answer"] or "?"
        q_short = r["question"][:60]
        lines.append(
            f"  [{r['id']:>3}] {q_short:<60}  "
            f"GT={r['ground_truth']:3s}  FP={fp_ans:3s}({fp_mark})  BL={bl_ans:3s}({bl_mark})"
        )

    return "\n".join(lines)


def main():
    print(f"Case Study Validation — PAT001 & PAT002")
    print(f"Model: {MODEL}")
    print(f"Questions: 12 (6 per patient)")
    print()

    results = run_eval()

    print()
    table = format_table(results)
    print(table)

    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    table_path = RESULTS_DIR / "table_a_case_study.txt"
    with open(table_path, "w") as f:
        f.write(table + "\n")
    print(f"\nSaved to: {table_path}")

    # Save raw JSON for debugging
    json_path = RESULTS_DIR / "case_study_raw.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
