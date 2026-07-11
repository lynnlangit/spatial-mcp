# Patient Medication Guide Template

**Purpose:** Translate therapeutic target recommendations into patient-friendly medication guide

**Use For:** Explaining potential new treatments based on molecular findings, including mechanism of action, clinical status, and what to expect

---

## Instructions for Claude

You are creating a medication guide to help patients understand potential new treatment options identified through molecular analysis. This is NOT a prescription - it's educational material to prepare patients for informed discussions with their oncologist.

**Audience:** Cancer patient considering treatment options (adult, no scientific training)

**Reading Level:** 8th grade (ages 13-14)

**Tone:** Informative, empowering, realistic about benefits and side effects

**Length:** 600-800 words

**Key Principles:**
1. Explain WHY these drugs are being considered (connection to molecular findings)
2. Describe HOW each drug works in simple terms
3. Be honest about whether drugs are FDA-approved or in clinical trials
4. Include realistic information about side effects
5. Emphasize need to discuss with oncologist before any treatment changes
6. Provide specific questions to ask about each drug

---

## Input Data

**Paste drug resistance markers, pathway findings, and treatment recommendations:**

```
{{DRUG_RESISTANCE_MARKERS}}
{{PATHWAY_FINDINGS}}
{{THERAPEUTIC_RECOMMENDATIONS}}
```

**Example format:**
```
Drug Resistance Markers:
  - PIK3CA: 3.11× fold change
  - AKT1: 3.24× fold change
  - ABCB1: 4.29× fold change

Recommended Therapeutic Targets:
  - PI3K/AKT pathway inhibitors (Alpelisib, Capivasertib)
  - MDR reversal agents
  - VEGF inhibitors (Bevacizumab - currently taking)

Hypoxic Markers:
  - HIF1A: spatially clustered
  - Consider: Hypoxia-targeting agents (Evofosfamide, TH-302)
```

---

## Output Format

Generate a medication guide following this structure:

### NEW TREATMENT OPTIONS BASED ON YOUR TUMOR ANALYSIS

[Opening paragraph: 2-3 sentences explaining why molecular testing helps identify better treatment options]

**Important:** This guide describes potential treatments your care team may discuss with you. It is NOT a prescription. Your oncologist will decide which options are right for you based on your complete medical situation.

---

### OPTION 1: [Drug Category Name]

**Drug Names:** [Generic name (Brand name if available)]

**Why we're considering this:**
[2-3 sentences connecting molecular findings to this drug. Example: "Your tumor analysis showed high activity in a pathway called PI3K/AKT. This pathway helps tumor cells survive even when exposed to chemotherapy. Drugs that block this pathway might help overcome this resistance."]

**How it works:**
[2-3 sentences with clear analogy. Example: "Think of cancer cells as having multiple 'survival switches'. Your current chemotherapy turns off one switch, but the PI3K/AKT pathway acts as a backup switch. This drug is designed to turn off that backup switch, making tumor cells more vulnerable to treatment."]

**Current status:**
- [ ] FDA-approved for your cancer type
- [ ] FDA-approved for other cancers (could be used off-label)
- [ ] Available in clinical trials only
- [ ] Experimental (early research)

**What to expect:**
- **How it's given:** [IV infusion / oral pill / injection]
- **How often:** [daily / weekly / every 3 weeks]
- **Typical duration:** [until progression / fixed number of cycles]
- **Often combined with:** [other drugs patient may know]

**Possible side effects:**
[List 3-5 most common side effects in plain language. Be honest but not alarming.]
- Most common: [Example: fatigue, nausea, diarrhea]
- Less common but important: [Example: blood sugar changes, liver enzyme elevations]
- **Note:** Side effects vary widely. Your doctor can explain what to watch for and how to manage them.

**Questions to ask your oncologist:**
1. Is this drug FDA-approved for ovarian cancer, or would this be off-label use?
2. Are there clinical trials available testing this drug?
3. How would this fit with my current treatment plan?
4. What side effects are most common, and how are they managed?
5. What results have other patients seen with this treatment?

---

### OPTION 2: [Drug Category Name]

[Repeat same structure as Option 1]

---

### OPTION 3: [Drug Category Name]

[Repeat same structure as Option 1]

---

### COMPARING YOUR OPTIONS

[If multiple drugs recommended, create simple comparison]

| What matters to you | Option 1 | Option 2 | Option 3 |
|---------------------|----------|----------|----------|
| **Availability** | Clinical trial only | FDA-approved | Off-label use |
| **How it's given** | Oral pill | IV infusion | Oral pill |
| **Schedule** | Daily at home | Every 3 weeks at clinic | Daily at home |
| **Common side effects** | [Brief list] | [Brief list] | [Brief list] |
| **May be combined with** | Current chemo | Used alone | Current chemo |

**Note:** This comparison is simplified. Your oncologist will provide complete information about risks, benefits, and logistics for each option.

---

### WHAT HAPPENS NEXT

**Step 1: Discuss with your oncologist**
Bring this guide and your questions to your next appointment. Your doctor will:
- Review your complete medical history and current health status
- Check if you qualify for specific treatments or clinical trials
- Explain more details about risks and benefits
- Help you weigh the options based on your goals and preferences

**Step 2: Consider your goals**
Think about what matters most to you:
- Quality of life vs. aggressive treatment
- Convenience (pills at home vs. infusions at clinic)
- Side effect tolerance
- Clinical trial participation vs. standard treatments

**Step 3: Make a decision together**
Your oncologist will recommend what they think is best, but the final decision is made TOGETHER with you. There are no wrong questions, and you can take time to decide.

---

### UNDERSTANDING CLINICAL TRIALS

[If any recommended drugs are trial-only, include this section]

Some of the treatments mentioned are available only through clinical trials. This means:

**What clinical trials are:**
- Research studies testing new drugs or new uses for existing drugs
- Carefully monitored with strict safety protocols
- May offer access to cutting-edge treatments
- Participation is always voluntary

**Benefits:**
- Access to treatments not yet FDA-approved
- Close monitoring by research team
- Contributing to cancer research that helps future patients

**Considerations:**
- May require extra appointments or tests
- Might receive placebo (inactive treatment) in some trials
- Unknown risks since drugs are newer
- May need to travel to specific research centers

**Questions to ask about clinical trials:**
1. What is this trial trying to learn?
2. What are my chances of getting the actual drug vs. placebo?
3. What extra appointments or tests are required?
4. Who pays for the trial drug and related medical care?
5. Can I leave the trial if I want to?

---

### RESOURCES FOR LEARNING MORE

**About specific drugs:**
- [DrugName].com (manufacturer website)
- ClinicalTrials.gov (search by drug name)
- Cancer.Net Drug Information (ASCO patient resource)

**About your cancer type:**
- [Cancer Type] Research Foundation
- National Cancer Institute (cancer.gov)
- American Cancer Society (cancer.org)

**Financial assistance:**
- Patient Access Network Foundation (panfoundation.org)
- HealthWell Foundation (healthwellfoundation.org)
- Manufacturer patient assistance programs

---

### IMPORTANT REMINDERS

**This is not medical advice:** This guide is educational only. Your oncologist has access to information beyond this molecular analysis (imaging, blood work, your medical history, current research) that all factor into treatment decisions.

**Every patient is different:** Even if another patient had similar molecular findings, their treatment plan might be different based on other factors.

**You are not obligated to try these options:** If new treatments don't align with your goals or you want to continue current therapy, that's a valid choice. Discuss all options with your care team.

**Molecular findings can change:** Tumors evolve over time. What's true today might change with disease progression or treatment response. Your team may recommend repeat testing in the future.

---

### YOUR NOTES

[Leave blank space for patient to write notes during doctor appointment]

**Questions I want to ask:**
1. ______________________________________________________________________
2. ______________________________________________________________________
3. ______________________________________________________________________

**My concerns:**
______________________________________________________________________
______________________________________________________________________

**What matters most to me in choosing treatment:**
______________________________________________________________________
______________________________________________________________________

---

## Example Transformation

### Technical Input:
```
Drug Resistance Markers:
  - ABCB1: 4.29× fold change

Recommended:
  - PI3K/AKT pathway inhibitors (Alpelisib, Capivasertib)
```

### Patient-Friendly Output:
```
OPTION 1: PI3K/AKT PATHWAY INHIBITORS

Drug Names: Alpelisib (Piqray), Capivasertib (experimental)

Why we're considering this:
Your tumor analysis showed high activity in proteins called PIK3CA, AKT1,
and MTOR. These work together in a cellular pathway that helps tumor cells
survive even when exposed to chemotherapy. Blocking this pathway might help
overcome the resistance your tumor has developed to platinum drugs.

How it works:
Think of cancer cells as having multiple "survival switches". Your current
chemotherapy turns off one switch, but the PI3K/AKT pathway acts as a backup
switch that keeps tumor cells alive. These drugs are designed to turn off
that backup switch, making tumor cells more vulnerable to other treatments.

Current status:
☑ Alpelisib is FDA-approved for breast cancer (could be used off-label for ovarian)
☐ Capivasertib is available in clinical trials only

What to expect:
- How it's given: Alpelisib is an oral pill taken daily
- How often: Once daily, usually in 28-day cycles
- Typical duration: Continue as long as it's working and side effects are tolerable
- Often combined with: Can be added to your current chemotherapy regimen

Possible side effects:
- Most common: High blood sugar, diarrhea, nausea, rash, fatigue
- Less common but important: Severe rash, kidney problems, mood changes
- Note: Blood sugar monitoring is important - your team may adjust diabetes
  medications if needed, even if you don't currently have diabetes

Questions to ask your oncologist:
1. Is Alpelisib approved for ovarian cancer, or would this be off-label use?
2. Are there clinical trials testing these drugs specifically for platinum-
   resistant ovarian cancer?
3. How would this be scheduled with my current bevacizumab (Avastin) infusions?
4. What blood sugar levels would require dose adjustment or stopping the drug?
5. Have you treated other patients with this combination, and what were their
   experiences?
```

---

## Validation Checklist

Before finalizing output, verify:
- [ ] Each drug's FDA status is clearly stated (approved / off-label / trial-only)
- [ ] Mechanism of action explained with helpful analogy
- [ ] Side effects are honest but not fear-inducing
- [ ] Clear connection between molecular findings and drug recommendations
- [ ] Specific questions provided for each treatment option
- [ ] Disclaimer that oncologist makes final decisions
- [ ] Resources provided for patient to learn more
- [ ] Reading level appropriate (8th grade)

---

## Usage Notes

**When to use this template:**
- After molecular analysis identifies targetable pathways
- When patient asks "What are my other treatment options?"
- To prepare patient for treatment planning appointment
- When clinical trial options are available

**Who reviews output:**
- **Required:** Oncologist (must verify drug information and appropriateness)
- **Recommended:** Oncology pharmacist (for drug details and interactions)
- **Optional:** Patient navigator or social worker (for clarity and support resources)

**Customization tips:**
- Add financial information: Include "Estimated cost: $X/month" if relevant to patient
- Emphasize specific option: If one drug is clearly preferred, put it first and add "(Doctor recommends discussing this one first)"
- Adjust for treatment goals: If patient prioritizes quality of life, emphasize "lower side effect profile" drugs

---

**Template Version:** 1.0
**Maintained by:** precision-medicine-mcp project
