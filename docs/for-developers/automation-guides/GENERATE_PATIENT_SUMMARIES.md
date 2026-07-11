# Generating Patient-Facing Summaries

**Purpose:** Guide for creating patient-friendly reports from technical molecular analysis outputs using LLM-based translation.

**Use Case:** After running PatientOne workflow (or similar), you have technical outputs (DEGs, spatial analysis, pathway enrichment) that need translation into plain language for patient education.

---

## Overview

This guide provides **copy-paste prompt templates** for translating technical bioinformatics outputs into patient-friendly summaries. All templates use Claude (or any LLM) to automatically generate clear, accurate, and compassionate explanations at an 8th-grade reading level.

**What This Solves:**
- Technical molecular reports are incomprehensible to patients
- Manual writing is time-consuming and inconsistent
- Patients need clear explanations of test results and treatment implications
- Care teams need efficient way to create patient education materials

**What You Get:**
- 3 reusable prompt templates for common patient materials
- Guidelines for patient-appropriate content
- Side-by-side technical vs. patient-friendly examples
- Integration with existing automated report generation

---

## Quick Start

1. **Run your analysis** using PatientOne workflow or `generate_patient_report.py`
2. **Copy technical output** (e.g., `clinical_summary.txt`)
3. **Use prompt template** (see [Prompt Templates](#prompt-templates) below)
4. **Paste technical data** into template
5. **Run through Claude** to generate patient-friendly version
6. **Clinician reviews** output for accuracy before sharing with patient

---

## Patient-Friendly Content Guidelines

### Writing Standards

- **Reading Level:** 8th grade (13-14 years old)
- **Sentence Length:** 15-20 words average
- **Paragraph Length:** 3-5 sentences maximum
- **Tone:** Clear, compassionate, hopeful yet realistic

### What to Avoid

- Medical jargon without explanation
- Statistical terms (p-values, fold-change, FDR) without context
- Gene symbols without plain language descriptions
- Percentages/numbers without context ("What does this mean for me?")
- Overly technical pathway names

### What to Include

- Plain language explanations of molecular findings
- Context for why tests were done
- What the results mean for treatment options
- Action items or next steps
- Reassurance and hope where appropriate
- Explicit disclaimer that doctor makes final decisions

---

## Prompt Templates

### Template 1: Disease Summary Report

**Use For:** Translating technical `clinical_summary.txt` into patient education document

**Location:** [patient-disease-summary-template.md](prompts/patient-disease-summary-template.md)

**Input:** Technical report with DEGs, spatial analysis, pathway enrichment
**Output:** 2-3 page plain language report explaining test results

**Example Use Case:**
- Input: PatientOne clinical_summary.txt (TP53, ABCB1 overexpression, drug resistance pathways)
- Output: "Your Test Results Explained" document with sections on what was tested, what was found, and what it means for treatment

---

### Template 2: Medication Guide

**Use For:** Explaining therapeutic targets and potential new treatments based on molecular analysis

**Location:** [patient-medication-guide-template.md](prompts/patient-medication-guide-template.md)

**Input:** Drug resistance markers, pathway analysis, recommended therapeutic targets
**Output:** Plain language guide to potential treatment options

**Example Use Case:**
- Input: PIK3CA/AKT1/MTOR overexpression → PI3K inhibitor recommendations
- Output: "New Treatment Options Based on Your Tumor Analysis" with drug names, how they work, what to expect

---

### Template 3: Infographic Text

**Use For:** Creating concise bullet points for patient-facing visual materials

**Location:** [patient-infographic-text-template.md](prompts/patient-infographic-text-template.md)

**Input:** Key molecular findings (top DEGs, spatial patterns, cell types)
**Output:** 5-10 simple bullet points for infographic overlay

**Example Use Case:**
- Input: 31 spatially variable genes, 6 tumor regions, hypoxic and resistant signatures
- Output: "Your Tumor Profile: What We Learned" with 3-5 key takeaways in 1-2 sentences each

---

## Integration with Automated Reports

### Current Workflow (Technical Only)

```bash
# Existing: Generate technical outputs
python servers/mcp-patient-report/scripts/generate_patient_report.py \
  --patient-id patient-001 \
  --output-dir outputs/for-researchers/patient-001/
```

**Outputs:** `clinical_summary.txt`, `differential_expression.csv`, visualizations

### Enhanced Workflow (Technical + Patient-Friendly)

```bash
# Step 1: Generate technical outputs (unchanged)
python servers/mcp-patient-report/scripts/generate_patient_report.py \
  --patient-id patient-001 \
  --output-dir outputs/for-researchers/patient-001/

# Step 2: Use LLM prompt to translate clinical_summary.txt
# (Copy/paste template from docs/for-developers/automation-guides/prompts/, fill with data, run in Claude)

# Step 3: Clinician reviews patient-friendly output

# Step 4: Save to patient output directory
mv patient_friendly_summary.txt outputs/for-patient/patient-001/
```

**Outputs:** Technical reports + patient-friendly summaries ready for clinician review

---

## Example: PatientOne Translation

### Before (Technical)

From `clinical_summary.txt`:

```
1. DIFFERENTIAL EXPRESSION (tumor_core vs stroma):
   Total DEGs: 17
   Upregulated: 13
   Downregulated: 4

   Top 5 upregulated genes in tumor:
      TP53: log2FC = 4.654, FDR = 5.04e-20
      KRT8: log2FC = 4.345, FDR = 2.68e-18
      ABCB1: log2FC = 4.285, FDR = 4.20e-18
      BCL2L1: log2FC = 3.683, FDR = 2.95e-19
      MKI67: log2FC = 3.564, FDR = 1.22e-14

Drug Resistance Markers Detected:
  - PIK3CA: 3.11× fold change
  - AKT1: 3.24× fold change
  - MTOR: 3.17× fold change
  - ABCB1: 4.29× fold change

  ⚠️  Consider:
     - PI3K/AKT pathway inhibitors (Alpelisib, Capivasertib)
     - MDR reversal agents
```

### After (Patient-Friendly)

Generated using disease summary template:

```
YOUR TEST RESULTS: WHAT WE FOUND

We ran special tests on your tumor tissue to understand why the cancer
is not responding to current chemotherapy. Here's what we learned:

YOUR TUMOR'S UNIQUE CHARACTERISTICS

Your tumor cells are making high levels of certain proteins that help
them survive and resist treatment. The most important ones are:

• TP53: This gene helps control cell growth. Changes in TP53 are very
  common in ovarian cancer (found in 9 out of 10 patients).

• ABCB1: This acts like a "pump" that pushes chemotherapy drugs out of
  tumor cells before they can work. This may explain why platinum
  chemotherapy is no longer working as well.

• MKI67: This shows how fast tumor cells are dividing. Higher levels
  mean more active growth in certain areas of your tumor.

WHY YOUR TUMOR MIGHT BE RESISTANT TO TREATMENT

We found four proteins (PIK3CA, AKT1, MTOR, ABCB1) that are more active
than normal in your tumor. These work together in a cellular pathway
that helps cancer cells survive even when exposed to chemotherapy.

Think of it like a backup power system - even when one pathway is blocked
by treatment, these proteins create alternative routes for tumor cells
to keep growing.

NEW TREATMENT OPTIONS TO DISCUSS

Based on these findings, your care team may consider:

1. PI3K/AKT Pathway Inhibitors
   • Drug names: Alpelisib, Capivasertib
   • How they work: Block the survival pathways we found active in your tumor
   • Next step: Your oncologist will check if you qualify for clinical trials

2. Drugs That Overcome Resistance
   • How they work: Stop the ABCB1 "pump" that pushes chemotherapy out of cells
   • Next step: May be combined with your current treatment

IMPORTANT: This report shows promising targets for new treatments, but
your oncologist will make the final decision about what's right for you.
These findings need to be combined with other factors like your overall
health, treatment history, and personal preferences.

QUESTIONS FOR YOUR NEXT APPOINTMENT

1. Am I a candidate for PI3K inhibitor clinical trials?
2. Could we add a drug to overcome the ABCB1 resistance?
3. How do these findings change my treatment plan?
4. What are the potential side effects of these new options?

This analysis was done for research and education purposes. All
treatment decisions will be made by your oncology team based on your
complete medical situation.
```

**Key Differences:**
- Technical gene names explained in plain language
- Statistics removed or contextualized ("9 out of 10 patients")
- Mechanisms explained with analogies ("pump", "backup power system")
- Action items clearly stated ("discuss with oncologist")
- Tone is hopeful yet realistic
- Questions provided to facilitate doctor-patient conversation

---

## Prompt Template Structure

All three templates follow this format:

```markdown
# [Template Name]

## Instructions for Claude

[Role definition, audience, constraints]

## Input Data

[Structured format for pasting technical data]

## Output Format

[Detailed specification of desired output structure]

## Examples

[Before/after examples showing desired translation style]
```

**To Use:**
1. Open template file
2. Copy entire template
3. Fill in "Input Data" section with your technical output
4. Paste into Claude (or any LLM)
5. Review and refine output with clinician

---

## Quality Checks Before Sharing With Patients

### Accuracy
- [ ] No medical errors or misstatements
- [ ] Gene/drug names spelled correctly
- [ ] Mechanisms accurately described (even if simplified)
- [ ] Appropriate caveats included

### Clarity
- [ ] Passes 8th grade readability test ([readable.com](https://readable.com) or similar)
- [ ] No unexplained jargon
- [ ] Analogies are accurate and helpful
- [ ] Numbers provide context ("What does this mean for me?")

### Compassion
- [ ] Tone is hopeful yet realistic
- [ ] Avoids fear-inducing language
- [ ] Acknowledges patient agency and involvement in decisions
- [ ] Provides clear next steps

### Legal/Ethical
- [ ] Disclaimer clearly states this is not medical advice
- [ ] Emphasizes oncologist makes final treatment decisions
- [ ] Notes research/education purpose if applicable
- [ ] Follows institutional policies on patient communication

---

## Advanced: Automating Patient Summary Generation

### Option 1: Claude API Integration (Recommended)

Add to `servers/mcp-patient-report/scripts/generate_patient_report.py`:

```python
import anthropic
import os

def generate_patient_summary(clinical_summary_path: str, template_path: str) -> str:
    """
    Translate technical clinical summary to patient-friendly version.

    Args:
        clinical_summary_path: Path to technical clinical_summary.txt
        template_path: Path to prompt template (e.g., patient-disease-summary-template.md)

    Returns:
        Patient-friendly summary text
    """
    # Load template
    with open(template_path, 'r') as f:
        template = f.read()

    # Load technical summary
    with open(clinical_summary_path, 'r') as f:
        technical_data = f.read()

    # Fill template with data
    prompt = template.replace("{{CLINICAL_SUMMARY}}", technical_data)

    # Call Claude API
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

# Usage
if __name__ == "__main__":
    patient_summary = generate_patient_summary(
        clinical_summary_path="outputs/for-researchers/patient-001/clinical_summary.txt",
        template_path="docs/for-developers/automation-guides/prompts/patient-disease-summary-template.md"
    )

    # Save output
    with open("outputs/for-patient/patient-001/patient_summary.txt", 'w') as f:
        f.write(patient_summary)
```

### Option 2: Manual Claude Desktop Workflow

1. Open `clinical_summary.txt` in text editor
2. Open prompt template in browser
3. Copy template, paste into Claude Desktop
4. Fill in technical data from clinical_summary.txt
5. Run prompt
6. Copy output to new file
7. Send to clinician for review

**Estimated Time:**
- Option 1 (Automated): ~30 seconds per patient
- Option 2 (Manual): ~3-5 minutes per patient

---

## Related Documentation

- **[AUTOMATED_PATIENT_REPORTS.md](AUTOMATED_PATIENT_REPORTS.md)** - Technical report generation (Step 1)
- **[Prompt Templates](prompts/)** - Three fill-in-the-blank LLM prompts
- **[Example Workflow](examples/patient-summary-example.md)** - Complete PatientOne example

---

## Getting Help

**Common Issues:**

**Q: LLM output is still too technical**
A: Add to prompt: "Use even simpler language. Explain as if talking to a 12-year-old."

**Q: Output is too long**
A: Add to prompt: "Keep total length under 500 words. Use bullet points."

**Q: Medical accuracy concerns**
A: Always have oncologist review. Add specific constraints to prompt: "Only include information that is definitive from the data. Add uncertainty language for speculative findings."

**Q: Want to customize for different cancer types**
A: Edit prompt templates to include cancer-specific context. Example: For ovarian cancer, emphasize platinum resistance, CA-125 relevance, BRCA implications.

---

**Version:** 1.0
**Maintainer:** precision-medicine-mcp project

**Compliance Note:** These templates are designed for research and education. Institutions using this for clinical patient communication must ensure compliance with local regulations (HIPAA, institutional review board approval, etc.).
