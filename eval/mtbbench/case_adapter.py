"""
MTBBench case adapter — converts MTBBench longitudinal cases to platform schema.

The MTBBench Doctor-agent protocol sends cases as a list of dicts, each containing
one of: 'context' (str), 'file_paths' (list[str]), or 'question'+'answer' (str).
The context is revealed incrementally across turns, mimicking clinical timelines.

Data source: MSK-CHORD via cBioPortal (questions_msk_bench.json).
Cite: Jain et al., MTBBench, NeurIPS 2024, github.com/bunnelab/mtbbench
"""

from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class MTBCase:
    """Normalized MTBBench longitudinal case."""

    case_id: str
    cancer_type: str  # from MSK-CHORD specimen (CANCER_TYPE_DETAILED)

    # Genomic fields (from specimen.txt / mutation.csv / cna.csv)
    somatic_variants: list = field(default_factory=list)
    cnv_calls: list = field(default_factory=list)
    tmb_mut_per_mb: float = 0.0
    msi_score: float = 0.0
    msi_type: str = "Stable"
    tumor_purity: float = 0.0

    # Clinical fields (from context + timeline files)
    stage: str = ""
    age_at_diagnosis: float = 0.0
    gender: str = ""
    race: str = ""
    treatment_history: list = field(default_factory=list)

    # MTBBench evaluation fields (from question/answer pairs)
    questions: list = field(default_factory=list)
    # Each question: {question: str, answer: str, type: str, months: int}

    # Timeline data (raw text from timeline files, for feeding to platform)
    timelines: list = field(default_factory=list)
    # Each: {index: int, content: str}

    # Specimen data (raw JSON dict from specimen.txt)
    specimen_data: dict = field(default_factory=dict)

    # Metadata
    mtbbench_track: str = "longitudinal"
    source_cohort: str = "MSK-CHORD"


def load_mtbbench_case(case_json_path: str) -> MTBCase:
    """
    Load an MTBBench longitudinal case and normalize to platform schema.

    The MTBBench case format (from questions_msk_bench.json) is a list of dicts:
      [
        {"context": "The patient is a 60-year-old..."},
        {"file_paths": ["path/to/timeline0.txt", "path/to/specimen.txt", ...]},
        {"question": "Given that...", "answer": "A) Yes"},
        {"context": "The patient experienced..."},
        {"file_paths": [...]},
        {"question": "...", "answer": "..."},
        ...
      ]

    This adapter extracts structured fields from the context/file data and
    collects all question/answer pairs for scoring.
    """
    with open(case_json_path) as f:
        raw = json.load(f)

    case_id = raw.get("case_id", "UNKNOWN")
    cancer_type = ""
    stage = ""
    age_at_diagnosis = 0.0
    gender = ""
    race = ""
    tmb_mut_per_mb = 0.0
    msi_score = 0.0
    msi_type = "Stable"
    tumor_purity = 0.0
    somatic_variants = []
    cnv_calls = []
    treatment_history = []
    questions = []
    timelines = []
    specimen_data = {}

    turns = raw.get("turns", [])
    timeline_idx = 0

    for entry in turns:
        if "context" in entry:
            # Extract demographic info from initial context
            ctx = entry["context"]
            if not gender:
                _extract_demographics(ctx, locals())

        elif "file_data" in entry:
            # Inline file contents (our fixture format embeds file data)
            for filename, content in entry["file_data"].items():
                if filename.startswith("timeline"):
                    timelines.append({"index": timeline_idx, "content": content})
                    timeline_idx += 1
                    # Extract treatment agents from timeline
                    for line in content.split("\n"):
                        if "treatment > treatment" in line and "AGENT:" in line:
                            agent = line.split("AGENT:")[1].split(",")[0].strip()
                            if agent and agent not in treatment_history:
                                treatment_history.append(agent)
                elif filename == "specimen.txt":
                    if isinstance(content, str):
                        specimen_data = json.loads(content)
                    else:
                        specimen_data = content
                    cancer_type = specimen_data.get(
                        "CANCER_TYPE_DETAILED", specimen_data.get("CANCER_TYPE", "")
                    )
                    stage = specimen_data.get("AJCC", "")
                    tmb_mut_per_mb = specimen_data.get("TMB_NONSYNONYMOUS", 0.0)
                    msi_score = specimen_data.get("MSI_SCORE", 0.0)
                    msi_type = specimen_data.get("MSI_TYPE", "Stable")
                    tumor_purity = specimen_data.get("TUMOR_PURITY", 0.0)
                elif filename == "mutation.csv":
                    # mutation data as list of dicts or CSV string
                    if isinstance(content, list):
                        somatic_variants = content
                    # Otherwise skip — will be populated from real MSK-CHORD data
                elif filename == "cna.csv":
                    if isinstance(content, list):
                        cnv_calls = content

        elif "question" in entry:
            q = entry["question"]
            a = entry["answer"]
            # Classify question type
            qtype = "unknown"
            months = 0
            if "recurrence" in q.lower():
                qtype = "recurrence"
            elif "alive" in q.lower():
                qtype = "survival"
            elif "progress" in q.lower():
                qtype = "progression"
            # Extract months from question text
            import re
            m = re.search(r"next (\d+) months", q)
            if m:
                months = int(m.group(1))
            questions.append({
                "question": q,
                "answer": a,
                "type": qtype,
                "months": months,
            })

    return MTBCase(
        case_id=case_id,
        cancer_type=cancer_type,
        somatic_variants=somatic_variants,
        cnv_calls=cnv_calls,
        tmb_mut_per_mb=tmb_mut_per_mb,
        msi_score=msi_score,
        msi_type=msi_type,
        tumor_purity=tumor_purity,
        stage=stage,
        age_at_diagnosis=age_at_diagnosis,
        gender=gender,
        race=race,
        treatment_history=treatment_history,
        questions=questions,
        timelines=timelines,
        specimen_data=specimen_data,
    )


def _extract_demographics(context: str, local_vars: dict) -> None:
    """Extract age, gender, race from MTBBench context string."""
    import re

    # Pattern: "The patient is a 60-year-old White male"
    age_match = re.search(r"(\d+[\.\d]*)-year-old", context)
    if age_match:
        local_vars["age_at_diagnosis"] = float(age_match.group(1))

    gender_match = re.search(r"\b(male|female)\b", context, re.IGNORECASE)
    if gender_match:
        local_vars["gender"] = gender_match.group(1).capitalize()

    race_match = re.search(
        r"(White|Black|Asian|Hispanic|Latino|Other)", context, re.IGNORECASE
    )
    if race_match:
        local_vars["race"] = race_match.group(1).capitalize()


def load_mtbbench_cohort(cohort_json_path: str) -> list[MTBCase]:
    """
    Load all MTBBench cases from questions_msk_bench.json (cohort format).

    The cohort format is: {patient_id: [items]} where items are dicts with
    one of: 'context' (str), 'file_data' (dict), or 'question'+'answer' (str).

    Returns list of MTBCase objects, one per patient.
    """
    with open(cohort_json_path) as f:
        cohort = json.load(f)

    cases = []
    for patient_id, items in cohort.items():
        case = _parse_cohort_patient(patient_id, items)
        cases.append(case)
    return cases


def _parse_cohort_patient(patient_id: str, items: list) -> MTBCase:
    """Parse one patient's item list into an MTBCase."""
    import re

    cancer_type = ""
    stage = ""
    age_at_diagnosis = 0.0
    gender = ""
    race = ""
    tmb_mut_per_mb = 0.0
    msi_score = 0.0
    msi_type = "Stable"
    tumor_purity = 0.0
    somatic_variants: list = []
    cnv_calls: list = []
    treatment_history: list = []
    questions: list = []
    timelines: list = []
    specimen_data: dict = {}
    timeline_idx = 0

    for item in items:
        if "context" in item:
            ctx = item["context"]
            # Parse demographics from first context
            if not gender:
                age_match = re.search(r"(\d+[\.\d]*)-year-old", ctx)
                if age_match:
                    age_at_diagnosis = float(age_match.group(1))
                gender_match = re.search(r"\b(male|female)\b", ctx, re.IGNORECASE)
                if gender_match:
                    gender = gender_match.group(1).capitalize()
                race_match = re.search(
                    r"(White|Black|Asian|Hispanic|Latino|Other)", ctx, re.IGNORECASE
                )
                if race_match:
                    race = race_match.group(1).capitalize()
            # Parse cancer type from context
            if not cancer_type:
                ct_match = re.search(
                    r"diagnosis of (.+?)(?:\.|,| Comprehensive)", ctx, re.IGNORECASE
                )
                if ct_match:
                    cancer_type = ct_match.group(1).strip()

        elif "file_data" in item:
            for filename, content in item["file_data"].items():
                if filename.startswith("timeline"):
                    timelines.append({"index": timeline_idx, "content": content})
                    timeline_idx += 1
                    # Extract treatment agents
                    if isinstance(content, str):
                        for line in content.split("\n"):
                            if "AGENT:" in line:
                                parts = line.split("AGENT:")
                                if len(parts) > 1:
                                    agent = parts[1].split(",")[0].strip()
                                    if agent and agent not in treatment_history:
                                        treatment_history.append(agent)
                elif filename == "specimen.txt":
                    if isinstance(content, str):
                        specimen_data = json.loads(content)
                    else:
                        specimen_data = content
                    cancer_type = specimen_data.get(
                        "CANCER_TYPE_DETAILED",
                        specimen_data.get("CANCER_TYPE", cancer_type),
                    )
                    stage = specimen_data.get("AJCC", stage)
                    tmb_mut_per_mb = float(
                        specimen_data.get("TMB_NONSYNONYMOUS", tmb_mut_per_mb)
                    )
                    msi_score = float(specimen_data.get("MSI_SCORE", msi_score))
                    msi_type = specimen_data.get("MSI_TYPE", msi_type)
                    tumor_purity = float(
                        specimen_data.get("TUMOR_PURITY", tumor_purity)
                    )
                elif filename == "mutation.csv":
                    if isinstance(content, list):
                        somatic_variants = content
                elif filename == "cna.csv":
                    if isinstance(content, list):
                        cnv_calls = content

        elif "question" in item:
            q_text = item["question"]
            answer = item["answer"]
            qtype = "unknown"
            months = 0
            if "recurrence" in q_text.lower():
                qtype = "recurrence"
            elif "alive" in q_text.lower():
                qtype = "survival"
            elif "progress" in q_text.lower():
                qtype = "progression"
            m = re.search(r"next (\d+) months", q_text)
            if m:
                months = int(m.group(1))
            questions.append({
                "question": q_text,
                "answer": answer,
                "type": qtype,
                "months": months,
            })

    return MTBCase(
        case_id=patient_id,
        cancer_type=cancer_type,
        somatic_variants=somatic_variants,
        cnv_calls=cnv_calls,
        tmb_mut_per_mb=tmb_mut_per_mb,
        msi_score=msi_score,
        msi_type=msi_type,
        tumor_purity=tumor_purity,
        stage=stage,
        age_at_diagnosis=age_at_diagnosis,
        gender=gender,
        race=race,
        treatment_history=treatment_history,
        questions=questions,
        timelines=timelines,
        specimen_data=specimen_data,
    )


def mtbcase_to_platform_context(case: MTBCase) -> dict:
    """
    Convert MTBCase to the context dict expected by generate_patient_report.

    Reuses the same field structure as pat001_canonical.py / pat002_canonical.py.
    """
    return {
        "patient_id": f"MTB-{case.case_id}",
        "cancer_type": case.cancer_type,
        "somatic_variants": case.somatic_variants,
        "cnv_calls": case.cnv_calls,
        "tmb_mut_per_mb": case.tmb_mut_per_mb,
        "msi_score": case.msi_score,
        "msi_type": case.msi_type,
        "tumor_purity": case.tumor_purity,
        "stage": case.stage,
        "treatment_history": case.treatment_history,
        "timelines": case.timelines,
        "specimen_data": case.specimen_data,
        "source": "MTBBench-MSK-CHORD",
    }
