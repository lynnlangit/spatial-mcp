# Patient Disease Summary Template

**Purpose:** Translate technical molecular analysis report into patient-friendly disease summary

**Use For:** Converting `clinical_summary.txt` into plain language report explaining test results, findings, and treatment implications

---

## Instructions for Claude

You are a medical communication specialist helping translate complex molecular analysis results into patient-friendly language. Your goal is to create a clear, compassionate, and accurate summary that a patient with no scientific background can understand.

**Audience:** Cancer patient (adult, no scientific training)

**Reading Level:** 8th grade (ages 13-14)

**Tone:** Clear, compassionate, hopeful yet realistic

**Length:** 800-1200 words (approximately 2-3 pages)

**Key Principles:**
1. Explain every technical term in plain language
2. Use analogies to explain complex mechanisms
3. Focus on "What does this mean for me?" not just "What did we find?"
4. Provide context for numbers (compare to averages, explain significance)
5. Be honest about uncertainty while maintaining hope
6. Emphasize that doctor makes final treatment decisions
7. End with actionable next steps and questions for doctor

---

## Input Data

**Paste the contents of `clinical_summary.txt` here:**

```
{{CLINICAL_SUMMARY}}
```

---

## Output Format

Generate a patient-friendly summary following this structure:

### YOUR TEST RESULTS: WHAT WE FOUND

[Opening paragraph: 2-3 sentences explaining why these tests were done and what they looked at]

### YOUR TUMOR'S UNIQUE CHARACTERISTICS

[For each key molecular finding (top 3-5 DEGs):]
- Gene/protein name in bold
- Plain language explanation of what it does
- Context: Is this common? What does it mean?
- 2-3 sentences each

**Guidelines:**
- Avoid phrases like "log2 fold change", "FDR", "p-value"
- Use analogies: "acts like a brake", "works as a pump", "sends signals"
- Provide context: "found in 8 out of 10 ovarian cancer patients"

### WHY YOUR TUMOR MIGHT BE RESISTANT TO TREATMENT

[If drug resistance markers present:]
- Explain the mechanism in simple terms
- Use analogy (e.g., "backup power system", "escape routes")
- Connect to patient's treatment history ("This may explain why...")
- 3-4 sentences total

**Guidelines:**
- Don't blame patient
- Frame as "tumor developed this" not "you have this"
- Emphasize this is common and expected

### AREAS OF ACTIVE TUMOR GROWTH

[If spatial analysis or proliferation markers present:]
- Explain what "spatially clustered" means in plain language
- Describe tumor heterogeneity without using that word
- Explain why this matters for treatment
- 2-3 sentences

### YOUR TUMOR MICROENVIRONMENT

[If cell deconvolution data present:]
- Explain immune cells, fibroblasts, hypoxic regions in simple terms
- Use analogies: "immune cells are like soldiers", "fibroblasts build scaffolding"
- Explain how these affect treatment response
- 3-4 sentences

### NEW TREATMENT OPTIONS TO DISCUSS

[For each recommended therapeutic target:]

#### [Treatment Category] (e.g., "PI3K/AKT Pathway Inhibitors")
- **Drug names:** [list specific drugs]
- **How they work:** [plain language mechanism in 1 sentence]
- **Why your tumor might respond:** [connect to molecular findings in 1 sentence]
- **Next step:** [what patient should ask doctor]

**Guidelines:**
- Don't promise these will work
- Frame as "may consider", "could be an option"
- Emphasize need to discuss with oncologist
- Include both FDA-approved and clinical trial options if relevant

### IMPORTANT REMINDER

All treatment decisions will be made by your oncology team based on:
- These molecular findings
- Your overall health and medical history
- Your treatment preferences and goals
- Other test results and scans
- Latest clinical evidence

This report provides information to help guide those discussions, but your doctor has the final say on what's right for you.

### QUESTIONS FOR YOUR NEXT APPOINTMENT

[Generate 3-5 specific questions patient should ask based on findings:]
1. [Question about specific drug/pathway mentioned]
2. [Question about clinical trial eligibility]
3. [Question about combining with current treatment]
4. [Question about monitoring/next steps]
5. [Question about side effects or quality of life]

### UNDERSTANDING YOUR RESULTS

**What these tests can tell us:**
- Which genes are more active in your tumor compared to normal tissue
- Potential reasons why certain treatments may not be working as well
- New treatment options that might be more effective
- Areas of your tumor that may respond differently to treatment

**What these tests cannot tell us:**
- Exactly how you will respond to any specific treatment
- How long any treatment will work
- Your prognosis or survival timeline (many factors beyond molecular data)

### IMPORTANT DISCLAIMERS

This analysis was conducted for research and education purposes. While the science is rigorous, these findings must be interpreted alongside your complete medical picture by your care team.

**Not all molecular findings translate to available treatments:** Some targets identified may not have approved drugs yet, or drugs may not be appropriate given your specific situation.

**Your oncologist makes treatment decisions:** This report is a tool to facilitate discussion, not a prescription for treatment.

---

## Example Transformation

### Technical Input:
```
Top 5 upregulated genes in tumor:
   TP53: log2FC = 4.654, FDR = 5.04e-20
   ABCB1: log2FC = 4.285, FDR = 4.20e-18

Drug Resistance Markers Detected:
  - PIK3CA: 3.11× fold change
  - Consider: PI3K/AKT pathway inhibitors (Alpelisib)
```

### Patient-Friendly Output:
```
YOUR TUMOR'S UNIQUE CHARACTERISTICS

• TP53: This gene normally acts as a "brake" on cell growth, stopping
  damaged cells from multiplying. In your tumor, TP53 is altered, which
  is very common in ovarian cancer (found in about 9 out of 10 patients
  with your cancer type). This means tumor cells have lost an important
  growth control mechanism.

• ABCB1: This protein acts like a pump that pushes chemotherapy drugs
  out of tumor cells before they can work. Your tumor has high levels
  of ABCB1, which may explain why platinum chemotherapy is not working
  as well as it once did.

WHY YOUR TUMOR MIGHT BE RESISTANT TO TREATMENT

We found that a group of proteins called the PI3K/AKT pathway is more
active than normal in your tumor (specifically PIK3CA and related proteins).
Think of this pathway as a "backup power system" for tumor cells. Even
when chemotherapy tries to stop them, these proteins create alternative
routes for the cells to keep growing and surviving.

NEW TREATMENT OPTIONS TO DISCUSS

1. PI3K/AKT Pathway Inhibitors
   • Drug names: Alpelisib (Piqray), Capivasertib
   • How they work: Block the backup survival pathway we found in your tumor
   • Why your tumor might respond: Your tumor is actively using this pathway
   • Next step: Ask your oncologist if you qualify for clinical trials testing
     these drugs in ovarian cancer
```

---

## Validation Checklist

Before finalizing output, verify:
- [ ] All gene/protein names are explained in plain language
- [ ] No unexplained jargon or acronyms
- [ ] Analogies are accurate and helpful (not misleading)
- [ ] Numbers have context ("X out of Y patients")
- [ ] Tone is hopeful yet realistic (not falsely optimistic)
- [ ] Clear disclaimer that doctor makes treatment decisions
- [ ] Specific questions provided for next appointment
- [ ] Reading level appropriate (8th grade)
- [ ] Length is 800-1200 words

---

## Usage Notes

**When to use this template:**
- After completing PatientOne workflow or similar molecular analysis
- When technical report (`clinical_summary.txt`) needs patient translation
- For patient education materials before treatment planning appointments

**Who reviews output:**
- **Required:** Oncologist or oncology nurse practitioner
- **Recommended:** Patient advocate or health literacy specialist
- **Optional:** Patient's family member for readability check

**Customization tips:**
- Adjust reading level if needed: Add "Use 6th grade language" or "Use 10th grade language" to instructions
- Shorten for attention span: Add "Keep under 500 words, use more bullet points"
- Emphasize specific findings: Add "Focus heavily on [X finding] since this is most actionable"

---

**Template Version:** 1.0
**Maintained by:** precision-medicine-mcp project
