"""
Fetch MSK-CHORD data from cBioPortal API and generate questions_msk_bench.json.

This script:
1. Fetches clinical, sample, timeline, mutation, and CNA data from cBioPortal
2. Applies the MTBBench datapoints (question definitions for 40 patients)
3. Generates questions_msk_bench.json in the eval/mtbbench/data/ directory

Requirements:
  - Network access to cBioPortal API (https://www.cbioportal.org/api)
  - No authentication required (public study)

License note:
  MSK-CHORD is CC BY-NC-ND 4.0 — generated data must not be redistributed.
  The questions_msk_bench.json file is gitignored.

Usage:
  python3 -m eval.mtbbench.scripts.fetch_msk_chord

Cite:
  - MSK-CHORD: Jee, Justin et al. Nature 2024 (PMID: 39506116)
  - MTBBench: Jain et al., NeurIPS 2024, github.com/bunnelab/mtbbench
"""

import json
import os
import time
import urllib.request
import urllib.error
from collections import Counter
from pathlib import Path

BASE = "https://www.cbioportal.org/api"
STUDY = "msk_chord_2024"
OUTPUT_DIR = Path(__file__).parent.parent / "data"

# The 40 MTBBench patients (from bunnelab/mtbbench msk_question_generation.py)
PATIENT_IDS = [
    "P-0004727", "P-0024579", "P-0005708", "P-0006191", "P-0006687",
    "P-0006691", "P-0007637", "P-0005014", "P-0009786", "P-0022292",
    "P-0022653", "P-0022826", "P-0022916", "P-0027883",
    "P-0028198", "P-0031600", "P-0032535", "P-0035737", "P-0039020",
    "P-0039147", "P-0040042", "P-0040055", "P-0040144", "P-0040302",
    "P-0040923", "P-0040957", "P-0041210", "P-0041381", "P-0041506",
    "P-0042090", "P-0042530", "P-0042652", "P-0043363", "P-0043580",
    "P-0043590", "P-0044015", "P-0044063", "P-0044328", "P-0044449",
    "P-0044903",
]

# MTBBench datapoints: {patient_id: [((start_age, end_age), [questions])]}
DATAPOINTS = {
    "P-0004727": [((60, 61.7), [{"recurrence": 24, "answer": "yes"}]), ((61.7, 63), [{"alive": 12, "answer": "no"}])],
    "P-0024579": [((71, 73.1), [{"recurrence": 24, "answer": "yes"}]), ((73.1, 74.1), [{"alive": 12, "answer": "no"}])],
    "P-0005708": [((58, 58.6), [{"recurrence": 12, "answer": "yes"}, {"alive": 12, "answer": "no"}])],
    "P-0006191": [((55, 56.1), [{"recurrence": 12, "answer": "yes"}, {"alive": 24, "answer": "yes"}]), ((56.1, 59.8), [{"alive": 12, "answer": "yes"}, {"progress": 12, "answer": "no"}])],
    "P-0006687": [((53, 54.5), [{"recurrence": 12, "answer": "yes"}]), ((54.5, 56), [{"recurrence": 12, "answer": "no"}, {"recurrence": 24, "answer": "yes"}]), ((56, 59.1), [{"alive": 12, "answer": "no"}])],
    "P-0006691": [((63, 64), [{"progress": 6, "answer": "no"}, {"recurrence": 6, "answer": "no"}]), ((64, 65.5), [{"progress": 6, "answer": "no"}, {"alive": 12, "answer": "yes"}]), ((65.5, 66.6), [{"alive": 12, "answer": "no"}])],
    "P-0007637": [((53, 55.8), [{"recurrence": 18, "answer": "no"}]), ((55.8, 58.1), [{"alive": 12, "answer": "yes"}, {"progress": 6, "answer": "yes"}]), ((58.1, 59), [{"alive": 9, "answer": "no"}])],
    "P-0005014": [((75.5, 80.1), [{"recurrence": 24, "answer": "no"}, {"progress": 24, "answer": "no"}, {"alive": 36, "answer": "yes"}]), ((80.1, 85), [{"alive": 24, "answer": "yes"}, {"progress": 12, "answer": "yes"}])],
    "P-0009786": [((51.9, 53), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}]), ((53, 57), [{"alive": 12, "answer": "yes"}, {"recurrence": 12, "answer": "yes"}]), ((57, 58), [{"alive": 24, "answer": "yes"}])],
    "P-0022292": [((65.5, 66.4), [{"progress": 12, "answer": "no"}, {"recurrence": 12, "answer": "yes"}]), ((66.4, 67.8), [{"progress": 12, "answer": "yes"}, {"recurrence": 12, "answer": "yes"}, {"alive": 12, "answer": "yes"}]), ((67.8, 68.9), [{"alive": 6, "answer": "no"}])],
    "P-0022653": [((40.6, 47.1), [{"progress": 24, "answer": "no"}, {"alive": 24, "answer": "yes"}]), ((47.1, 50), [{"progress": 12, "answer": "no"}, {"alive": 24, "answer": "yes"}]), ((50, 52), [{"alive": 12, "answer": "yes"}])],
    "P-0022826": [((60.8, 61), [{"recurrence": 6, "answer": "no"}, {"alive": 6, "answer": "yes"}]), ((61, 62), [{"alive": 12, "answer": "no"}, {"recurrence": 12, "answer": "yes"}, {"progress": 12, "answer": "yes"}])],
    "P-0022916": [((54.8, 56), [{"recurrence": 9, "answer": "yes"}]), ((56, 57.8), [{"alive": 12, "answer": "yes"}]), ((57.8, 59), [{"alive": 12, "answer": "yes"}]), ((59, 60), [{"alive": 12, "answer": "yes"}])],
    "P-0027883": [((48.5, 49.1), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "yes"}]), ((49.1, 50.2), [{"alive": 12, "answer": "yes"}, {"progress": 12, "answer": "no"}]), ((50.2, 51.3), [{"alive": 12, "answer": "yes"}, {"progress": 12, "answer": "no"}, {"recurrence": 12, "answer": "no"}]), ((51.3, 53), [{"alive": 12, "answer": "yes"}, {"progress": 12, "answer": "yes"}])],
    "P-0028198": [((73.5, 74.7), [{"recurrence": 12, "answer": "no"}]), ((74.7, 75.7), [{"recurrence": 12, "answer": "yes"}]), ((75.7, 77), [{"alive": 12, "answer": "yes"}, {"progress": 12, "answer": "no"}])],
    "P-0031600": [((67.7, 71.6), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 18, "answer": "yes"}])],
    "P-0032535": [((61.5, 62.3), [{"recurrence": 6, "answer": "no"}, {"progress": 6, "answer": "no"}]), ((62.3, 63.2), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "yes"}, {"alive": 12, "answer": "yes"}]), ((63.2, 64.6), [{"alive": 12, "answer": "no"}])],
    "P-0035737": [((70, 71.2), [{"recurrence": 6, "answer": "yes"}, {"progress": 12, "answer": "yes"}, {"alive": 12, "answer": "yes"}])],
    "P-0039020": [((62.2, 63.1), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "yes"}]), ((63.1, 63.8), [{"alive": 6, "answer": "no"}])],
    "P-0039147": [((71, 72.7), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "yes"}]), ((72.7, 73.9), [{"progress": 6, "answer": "yes"}, {"alive": 6, "answer": "yes"}])],
    "P-0040042": [((60.3, 61.5), [{"recurrence": 12, "answer": "yes"}, {"progress": 12, "answer": "yes"}]), ((61.5, 64.2), [{"alive": 12, "answer": "yes"}]), ((64.2, 65.2), [{"alive": 12, "answer": "yes"}]), ((65.2, 65.8), [{"alive": 12, "answer": "no"}])],
    "P-0040055": [((62.3, 63.3), [{"recurrence": 12, "answer": "yes"}, {"progress": 12, "answer": "yes"}]), ((63.3, 63.7), [{"alive": 18, "answer": "yes"}])],
    "P-0040144": [((67.9, 69.5), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 18, "answer": "yes"}])],
    "P-0040302": [((50.8, 51.6), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "yes"}]), ((51.6, 52.4), [{"progress": 4, "answer": "yes"}, {"alive": 12, "answer": "no"}])],
    "P-0040923": [((69, 70), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}]), ((70, 72), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 12, "answer": "yes"}])],
    "P-0040957": [((69.5, 70.5), [{"recurrence": 12, "answer": "yes"}, {"progress": 12, "answer": "yes"}, {"alive": 18, "answer": "yes"}]), ((70.5, 72.5), [{"alive": 12, "answer": "yes"}])],
    "P-0041210": [((78.7, 79.3), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}]), ((79.3, 80.5), [{"recurrence": 9, "answer": "no"}, {"progress": 9, "answer": "no"}]), ((80.5, 81.5), [{"alive": 12, "answer": "yes"}]), ((81.5, 81.7), [{"alive": 12, "answer": "no"}])],
    "P-0041381": [((50.4, 52), [{"recurrence": 12, "answer": "yes"}, {"alive": 12, "answer": "yes"}]), ((52, 54), [{"progress": 12, "answer": "no"}, {"alive": 12, "answer": "yes"}]), ((54, 55), [{"alive": 12, "answer": "no"}]), ((55, 56), [{"alive": 12, "answer": "yes"}]), ((56, 57.4), [{"progress": 12, "answer": "yes"}, {"recurrence": 12, "answer": "yes"}, {"alive": 12, "answer": "yes"}]), ((57.4, 59), [{"alive": 15, "answer": "yes"}]), ((59, 60.7), [{"alive": 9, "answer": "no"}])],
    "P-0041506": [((65.3, 66.6), [{"recurrence": 6, "answer": "yes"}]), ((66.6, 68), [{"progress": 12, "answer": "yes"}, {"alive": 12, "answer": "no"}])],
    "P-0042090": [((50.8, 51.5), [{"progress": 12, "answer": "no"}, {"alive": 12, "answer": "yes"}]), ((51.8, 53.1), [{"recurrence": 12, "answer": "yes"}, {"alive": 12, "answer": "yes"}])],
    "P-0042530": [((60.5, 61.6), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 12, "answer": "yes"}]), ((61.6, 62.6), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 12, "answer": "yes"}])],
    "P-0042652": [((75.3, 77.4), [{"recurrence": 12, "answer": "yes"}, {"progress": 12, "answer": "yes"}]), ((77.4, 78.8), [{"alive": 12, "answer": "no"}])],
    "P-0043363": [((60, 61.3), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}]), ((61.3, 63), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 12, "answer": "no"}])],
    "P-0043580": [((66.4, 67.3), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}]), ((67.3, 69), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "yes"}, {"alive": 6, "answer": "yes"}]), ((69, 69.9), [{"progress": 6, "answer": "yes"}, {"alive": 6, "answer": "no"}])],
    "P-0043590": [((59.6, 61), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "no"}])],
    "P-0044015": [((47.6, 48.3), [{"recurrence": 6, "answer": "yes"}, {"progress": 6, "answer": "no"}]), ((48.3, 50), [{"alive": 12, "answer": "yes"}, {"progress": 12, "answer": "no"}]), ((50, 50.8), [{"alive": 12, "answer": "yes"}, {"progress": 12, "answer": "no"}, {"recurrence": 12, "answer": "no"}])],
    "P-0044063": [((44.4, 45.5), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 12, "answer": "yes"}])],
    "P-0044328": [((49.7, 52), [{"recurrence": 12, "answer": "no"}, {"progress": 12, "answer": "no"}, {"alive": 12, "answer": "yes"}]), ((52, 53), [{"recurrence": 6, "answer": "no"}, {"progress": 6, "answer": "no"}, {"alive": 9, "answer": "yes"}])],
    "P-0044449": [((58, 61.4), [{"progress": 3, "answer": "yes"}, {"alive": 12, "answer": "yes"}]), ((61.4, 64.1), [{"recurrence": 24, "answer": "no"}, {"progress": 24, "answer": "no"}, {"alive": 24, "answer": "yes"}])],
    "P-0044903": [((66, 67.3), [{"recurrence": 24, "answer": "no"}, {"progress": 24, "answer": "no"}, {"alive": 24, "answer": "yes"}])],
}


def api_get(path: str) -> list | dict:
    """GET request to cBioPortal API."""
    url = f"{BASE}{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/json")
    resp = urllib.request.urlopen(req, timeout=60)
    return json.loads(resp.read())


def api_post(path: str, body: dict) -> list | dict:
    """POST request to cBioPortal API."""
    url = f"{BASE}{path}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read())


def fetch_all_data():
    """Fetch all necessary data from cBioPortal API."""
    print(f"Fetching data for {len(PATIENT_IDS)} MTBBench patients from cBioPortal...")

    # 1. Clinical patient data
    print("  [1/5] Patient clinical attributes...")
    patient_clinical = {}
    for pid in PATIENT_IDS:
        attrs = api_get(f"/studies/{STUDY}/patients/{pid}/clinical-data?projection=DETAILED")
        patient_clinical[pid] = {a["clinicalAttributeId"]: a["value"] for a in attrs}
        patient_clinical[pid]["PATIENT_ID"] = pid
        time.sleep(0.1)

    # 2. Sample clinical data
    print("  [2/5] Sample clinical attributes...")
    sample_clinical = {}
    for pid in PATIENT_IDS:
        samples = api_get(f"/studies/{STUDY}/patients/{pid}/samples")
        for s in samples:
            sid = s["sampleId"]
            attrs = api_get(f"/studies/{STUDY}/samples/{sid}/clinical-data?projection=DETAILED")
            sample_clinical[sid] = {a["clinicalAttributeId"]: a["value"] for a in attrs}
            sample_clinical[sid]["SAMPLE_ID"] = sid
            sample_clinical[sid]["PATIENT_ID"] = pid
        time.sleep(0.1)

    # 3. Timeline events
    print("  [3/5] Timeline events...")
    all_timelines = {}
    for pid in PATIENT_IDS:
        events = api_get(f"/studies/{STUDY}/patients/{pid}/clinical-events?projection=DETAILED")
        all_timelines[pid] = events
        time.sleep(0.1)

    # 4. Mutations
    print("  [4/5] Mutations...")
    sample_ids = list(sample_clinical.keys())
    all_mutations = {}
    for i in range(0, len(sample_ids), 10):
        batch = sample_ids[i:i + 10]
        url = f"/molecular-profiles/{STUDY}_mutations/mutations/fetch?projection=DETAILED"
        muts = api_post(url, {"sampleIds": batch})
        for m in muts:
            sid = m.get("sampleId", "UNKNOWN")
            if sid not in all_mutations:
                all_mutations[sid] = []
            all_mutations[sid].append({
                "gene": m.get("gene", {}).get("hugoGeneSymbol", ""),
                "proteinChange": m.get("proteinChange", ""),
                "mutationType": m.get("mutationType", ""),
            })
        time.sleep(0.5)

    # 5. CNAs
    print("  [5/5] Copy number alterations...")
    all_cna = {}
    url = f"/molecular-profiles/{STUDY}_cna/discrete-copy-number/fetch?projection=DETAILED&discreteCopyNumberEventType=ALL"
    for i in range(0, len(sample_ids), 10):
        batch = sample_ids[i:i + 10]
        cnas = api_post(url, {"sampleIds": batch})
        for c in cnas:
            sid = c.get("sampleId", "UNKNOWN")
            if sid not in all_cna:
                all_cna[sid] = []
            all_cna[sid].append({
                "gene": c.get("gene", {}).get("hugoGeneSymbol", ""),
                "alteration": c.get("alteration"),
            })
        time.sleep(0.5)

    return patient_clinical, sample_clinical, all_timelines, all_mutations, all_cna


def format_timeline_event(ev, diagnosis_age):
    """Format a cBioPortal clinical event into MTBBench timeline text."""
    start_days = ev.get("startNumberOfDaysSinceDiagnosis", 0)
    age = diagnosis_age + (start_days / 365.25)
    event_type = ev.get("eventType", "")
    attrs = {a["key"]: a["value"] for a in ev.get("attributes", [])}

    lines = []
    if event_type == "Treatment":
        agent = attrs.get("AGENT", attrs.get("TREATMENT_TYPE", ""))
        lines.append(
            f"AGE: {age:.3f}, treatment > treatment --> "
            f"SUBTYPE: {attrs.get('SUBTYPE', 'Chemo')}, AGENT: {agent},"
        )
    elif event_type == "Lab_Test":
        test = attrs.get("TEST", "")
        result = attrs.get("RESULT", "")
        unit = attrs.get("LR_UNIT_MEASURE", "")
        if "CA 19-9" in test:
            lines.append(f"AGE: {age:.3f}, labtest > ca_19-9_labs --> RESULT: {result}, LR_UNIT_MEASURE: {unit},")
        elif "CEA" in test.upper():
            lines.append(f"AGE: {age:.3f}, labtest > cea_labs --> CEA: {result} {unit}")
        else:
            lines.append(f"AGE: {age:.3f}, labtest > {test.lower()} --> RESULT: {result},")
    elif event_type == "Diagnosis":
        if "PROGRESSION" in attrs:
            proc = attrs.get("PROCEDURE_TYPE", "")
            prog = attrs.get("PROGRESSION", "")
            if proc in ("CT", "CT scan"):
                msg = "progressed" if prog == "Y" else "NOT progressed"
                lines.append(f"AGE: {age:.3f}, diagnosis > progression --> CT scan reveals cancer has {msg}.")
            else:
                lines.append(f"AGE: {age:.3f}, diagnosis > progression --> PROGRESSION: {prog}, PROCEDURE_TYPE: {proc},")
        elif "HAS_CANCER" in attrs:
            lines.append(f"AGE: {age:.3f}, diagnosis > cancer_presence --> HAS CANCER: {attrs['HAS_CANCER']},")
    elif event_type == "Surgery":
        lines.append(f"AGE: {age:.3f}, surgery --> SUBTYPE: {attrs.get('SUBTYPE', 'SAMPLE')},")
    elif event_type in ("Sample acquisition", "Sequencing"):
        lines.append(f"AGE: {age:.3f}, specimen --> SAMPLE_ID: {attrs.get('SAMPLE_ID', '')},")

    return age, lines


def generate_questions(patient_clinical, sample_clinical, all_timelines, all_mutations, all_cna):
    """Generate questions_msk_bench.json from fetched data."""
    dataset = {}
    question_count = 0

    for pid in DATAPOINTS:
        dataset[pid] = []
        diagnosis_age = DATAPOINTS[pid][0][0][0]
        pid_samples = [sid for sid, s in sample_clinical.items() if s.get("PATIENT_ID") == pid]
        specimen = sample_clinical.get(pid_samples[0], {}) if pid_samples else {}
        cancer_type = specimen.get("CANCER_TYPE_DETAILED", "cancer")
        gender = patient_clinical.get(pid, {}).get("SEX", "")
        race = patient_clinical.get(pid, {}).get("RACE", "")
        ethnicity = patient_clinical.get(pid, {}).get("ETHNICITY", "")

        for idx, ((start, end), questions) in enumerate(DATAPOINTS[pid]):
            # Context
            if idx == 0:
                eth_str = f" of {ethnicity} ethnicity" if ethnicity else ""
                context = (
                    f"The patient is a {start}-year-old {race} {gender.lower()}"
                    f"{eth_str} with a diagnosis of {cancer_type.lower()}. "
                    f"Comprehensive patient history, including details of diagnosis, "
                    f"treatments, and lab tests, is available for the period between "
                    f"the ages of {start} and {end} years."
                )
            else:
                context = (
                    f"Additional patient history is documented for the period between "
                    f"the ages of {start} and {end} years."
                )
            dataset[pid].append({"context": context})

            # Timeline
            timeline_lines = []
            for ev in all_timelines.get(pid, []):
                age, lines = format_timeline_event(ev, diagnosis_age)
                if start <= age <= end:
                    timeline_lines.extend(lines)
            timeline_lines.sort()
            timeline_text = "\n".join(timeline_lines)

            file_data = {f"timeline{idx}.txt": timeline_text}
            if idx == 0 and specimen:
                file_data["specimen.txt"] = json.dumps(specimen)
                if pid_samples and pid_samples[0] in all_mutations:
                    file_data["mutation.csv"] = all_mutations[pid_samples[0]]
                if pid_samples and pid_samples[0] in all_cna:
                    file_data["cna.csv"] = all_cna[pid_samples[0]]
            dataset[pid].append({"file_data": file_data})

            # Questions
            for q in questions:
                if "recurrence" in q:
                    qt = f"Given that the patient is {end} years old, will the cancer have a recurrence in the next {q['recurrence']} months?\nA) Yes\nB) No"
                    ans = "A) Yes" if q["answer"] == "yes" else "B) No"
                    dataset[pid].append({"question": qt, "answer": ans})
                    question_count += 1
                if "alive" in q:
                    qt = f"Given that the patient is {end} years old, will the patient be still alive in the next {q['alive']} months?\nA) Yes\nB) No"
                    ans = "A) Yes" if q["answer"] == "yes" else "B) No"
                    dataset[pid].append({"question": qt, "answer": ans})
                    question_count += 1
                if "progress" in q:
                    qt = f"Given that the patient is {end} years old, will the cancer progress in the next {q['progress']} months?\nA) Yes\nB) No"
                    ans = "A) Yes" if q["answer"] == "yes" else "B) No"
                    dataset[pid].append({"question": qt, "answer": ans})
                    question_count += 1

    return dataset, question_count


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    patient_clinical, sample_clinical, all_timelines, all_mutations, all_cna = fetch_all_data()
    dataset, question_count = generate_questions(
        patient_clinical, sample_clinical, all_timelines, all_mutations, all_cna
    )

    output_path = OUTPUT_DIR / "questions_msk_bench.json"
    with open(output_path, "w") as f:
        json.dump(dataset, f)

    print(f"\nGenerated {output_path}")
    print(f"  Patients: {len(dataset)}")
    print(f"  Questions: {question_count}")

    # Summary table
    type_counts = Counter()
    for pid in dataset:
        pid_samples = [sid for sid, s in sample_clinical.items() if s.get("PATIENT_ID") == pid]
        ct = sample_clinical.get(pid_samples[0], {}).get("CANCER_TYPE_DETAILED", "UNKNOWN") if pid_samples else "UNKNOWN"
        type_counts[ct] += 1

    print(f"\n  Cancer Type Breakdown:")
    for ct, count in type_counts.most_common():
        print(f"    {count:>3d}  {ct}")


if __name__ == "__main__":
    main()
