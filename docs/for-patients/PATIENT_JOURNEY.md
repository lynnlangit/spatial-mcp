<!-- REVIEW CHECKLIST: [ ] Reviewed by patient advocate [ ] Reviewed by oncology nurse [ ] Approved by PatientOne — do NOT publish without all three checkboxes filled -->

# Your Journey Through Precision Medicine Analysis

This page walks you through what happens when your cancer data is analyzed by
the Precision Medicine MCP Platform. Every step is explained in plain language.

---

## What Is This Platform?

When doctors treat cancer, they look at many types of information: blood tests,
genetic tests, tissue samples, and imaging scans. Normally, pulling all of this
together takes a team of specialists many hours of work.

This platform uses artificial intelligence (AI) to analyze all of your data
together, in a fraction of the time. It does not replace your doctors -- it helps
them see patterns they might otherwise miss, and suggests treatment options
backed by scientific evidence.

---

## The Five Steps of Your Analysis

### Step 1: Gathering Your Data

Your medical team collects information from your medical records (things like
your diagnosis, treatment history, and lab results) along with any genetic
tests and tissue samples that have been processed.

**What you might see:** A summary of your medical history and the data that
will be analyzed.

### Step 2: Understanding Your Tumor's Biology

The platform maps gene activity across your tissue sample. This is called
*spatial transcriptomics* -- it shows which genes are active and where they
are active within the tumor.

It also estimates which types of cells are present in your tumor. For example,
are there immune cells nearby that might be fighting the cancer? Are there
support cells that might be helping the cancer grow?

**What you might see:** A color-coded map of your tissue and a table listing
cell types and counts (for example: immune cells, tumor cells, support cells).

### Step 3: Finding Targets

The platform looks for specific weak points in your cancer:

- **Genetic vulnerabilities** -- Mutations that make your cancer susceptible to
  certain drugs. For example, a high HRD (Homologous Recombination Deficiency)
  score means the cancer has trouble repairing its own DNA, which makes it
  vulnerable to a class of drugs called PARP inhibitors.

- **Neoantigens** -- Tiny pieces of mutated protein on the surface of cancer
  cells that the immune system might be able to recognize. The platform predicts
  which of these bind most tightly to your immune cells (measured by a number
  called IC50 -- lower is better).

**What you might see:** A list of mutations with their clinical significance and
a ranking of neoantigen peptides by binding strength.

### Step 4: Predicting Treatment Effects

Using a machine-learning model called GEARS, the platform predicts what would
happen if specific genes were turned off in the cancer cells. This helps
researchers identify which gene targets might make the cancer more treatable.

**What you might see:** A prediction of how gene activity would change if a
specific gene were knocked down, and whether immune markers would recover.

### Step 5: Your Report

All findings are compiled into a report for your oncology team. The report
includes:

- A plain-language summary of key findings
- Ranked treatment recommendations with evidence levels
- Visualizations (tissue maps, charts, graphs)
- References to relevant clinical trials

Your oncologist reviews the report, discusses it with the tumor board, and then
meets with you to explain the findings and agree on next steps.

---

## What the Numbers Mean

Your report may include some of these measurements. Here is what they mean in
everyday terms:

| Measurement | What It Tells You | Example |
|-------------|-------------------|---------|
| HRD score | How broken the cancer's DNA-repair system is. Higher = more broken, which can be good for treatment. | 54 (high -- PARP inhibitor candidate) |
| TMB | How many mutations the cancer has per unit of DNA. More mutations can mean more targets for the immune system. | 47.3 mutations per megabase |
| IC50 | How tightly a neoantigen binds to immune cells. Lower = tighter = better for immune recognition. | 7.8 nM (very strong binding) |
| CD8+ T cells | A count of immune "killer" cells near the tumor. More of these cells may mean your immune system is actively fighting. | 30 cells detected |

---

## Your Privacy

Your data is protected at every step:

- **De-identification:** Names, dates, and other personal identifiers are
  removed before analysis.
- **Encryption:** Data is encrypted when stored and when transmitted.
- **Access controls:** Only your authorized medical team can see your data.
- **Audit trail:** Every access to your data is logged and retained for 10 years.

For more details, see [Your Privacy & Data Security](README.md#your-privacy--data-security).

---

## What Happens Next

After the analysis:

1. **Your oncologist reviews the results** and discusses them with the tumor board.
2. **You meet with your doctor** to go over the findings in person.
3. **Together, you decide** on the best treatment path.
4. **If your cancer changes**, the analysis can be repeated with updated data.

---

## Questions to Bring to Your Appointment

- "What did the analysis find about my cancer's genetic makeup?"
- "Are there treatments specifically matched to my tumor's characteristics?"
- "Are there clinical trials I might qualify for based on these results?"
- "What are the next steps, and when will we start?"

---

## A Note About This Platform

This platform was built in memory of a dear friend -- PatientOne -- who fought
High-Grade Serous Ovarian Carcinoma with extraordinary courage. Her journey
inspired every tool and every line of code. See
[ACKNOWLEDGMENTS.md](../../ACKNOWLEDGMENTS.md) for more about her story.

---

*This is not a clinical report. Discuss all findings with your oncology team.*
