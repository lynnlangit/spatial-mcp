# Patient Infographic Text Template

**Purpose:** Generate concise, impactful text for patient-facing visual materials (infographics, one-pagers, visual summaries)

**Use For:** Creating short bullet points or text blocks to overlay on infographic designs, perfect for patient education handouts or digital materials

---

## Instructions for Claude

You are creating SHORT, punchy text for an infographic that will use visual design elements (icons, charts, illustrations) to tell the story. Text should be minimal, memorable, and meaningful.

**Audience:** Cancer patient and their family (all ages, no scientific training)

**Reading Level:** 6th-8th grade (ages 11-14)

**Tone:** Clear, empowering, hopeful

**Length:** 5-10 bullet points, each 1-2 sentences maximum (10-25 words per point)

**Key Principles:**
1. Use active voice and strong verbs
2. Make every word count - no filler
3. Focus on the "so what?" not just the "what"
4. Use metaphors sparingly but effectively
5. Numbers should be simple and contextual
6. Each bullet should stand alone (patient may only read 1-2)

---

## Input Data

**Paste key molecular findings and spatial analysis results:**

```
{{KEY_FINDINGS}}
```

**Example format:**
```
Differential Expression:
  - 17 DEGs total (13 up, 4 down)
  - Top genes: TP53, ABCB1, BCL2L1, MKI67

Spatial Organization:
  - 31 spatially variable genes
  - 6 distinct tumor regions identified
  - Hypoxic regions detected (HIF1A, VEGFA clustered)

Tumor Microenvironment:
  - Resistant signature in tumor core (score: 716)
  - Immune infiltration in stroma (score: 603)
  - Hypoxic areas in necrotic regions (score: 607)

Therapeutic Targets:
  - PI3K/AKT pathway active (3.1-3.2× normal)
  - VEGF inhibitors (current therapy)
  - Consider PI3K inhibitors
```

---

## Output Format

Generate infographic text following this structure:

### YOUR TUMOR PROFILE: WHAT WE LEARNED

[Title section - 1 sentence, 15-20 words]
"Advanced molecular testing revealed why your tumor resists treatment and identified new options to try."

---

### KEY FINDINGS

[5-8 bullet points, each 10-25 words]

**Format each bullet as:**
- **[Bold lead-in phrase]:** [Plain language explanation with impact]

**Examples:**

- **Multiple tumor regions:** Your tumor has 6 different areas, each with unique characteristics that may respond differently to treatment.

- **Active resistance pathways:** Cancer cells are using backup survival routes (PI3K/AKT pathway) that help them escape chemotherapy.

- **Drug pump detected:** Tumor cells have high levels of ABCB1, a protein that pushes chemotherapy drugs out before they can work.

- **Hypoxic zones identified:** Low-oxygen areas in your tumor may resist standard treatment but could respond to specialized drugs.

- **Immune activity present:** Areas of immune cell infiltration suggest your immune system is fighting back and may respond to immunotherapy.

**Guidelines for bullets:**
- Start with impact word: "Active", "Detected", "Identified", "Found"
- Use present tense
- Avoid passive voice ("was found" → "detected")
- Include one actionable implication when possible
- Mix findings (what we saw) with meaning (what it means for treatment)

---

### WHAT THIS MEANS FOR YOUR TREATMENT

[2-3 bullet points, each 15-25 words]

**Format:**
- **[Treatment category]:** [Plain language explanation of why this might work]

**Examples:**

- **PI3K inhibitors:** Drugs that block the backup survival pathway we found active in your tumor (clinical trials available).

- **Resistance reversal agents:** Medications that stop the drug pump (ABCB1) from pushing chemotherapy out of tumor cells.

- **Hypoxia-targeting drugs:** Specialized treatments designed to kill cancer cells in low-oxygen areas where standard drugs don't reach.

---

### NEXT STEPS

[2-3 action items, each 10-15 words]

**Examples:**

- Discuss PI3K inhibitor clinical trials with your oncologist at next visit
- Ask about combining resistance reversal drugs with current chemotherapy
- Review all options considering your treatment goals and quality of life

---

### [Optional: STATISTICS TO VISUALIZE]

[If infographic includes charts/graphs, provide 2-4 data points with context]

**Format:**
- [Number] → [Plain language context label]

**Examples:**

- 17 genes → Significantly different in tumor vs. normal tissue
- 6 regions → Distinct areas within your tumor, each unique
- 3× higher → Activity level of resistance pathway compared to normal
- 31 genes → Show spatial clustering (concentrated in specific tumor areas)

---

### [Optional: BOTTOM DISCLAIMER]

[Single sentence, 20-30 words, required for legal/ethical compliance]

"This analysis is for education and research. Your oncology team will determine the best treatment plan for your specific situation."

---

## Complete Example Output

### YOUR TUMOR PROFILE: WHAT WE LEARNED

"Molecular testing revealed why your tumor resists platinum chemotherapy and identified three new treatment pathways to discuss with your doctor."

---

### KEY FINDINGS

- **Multiple survival routes detected:** Your tumor uses the PI3K/AKT pathway as a backup system to survive even when chemotherapy blocks other growth signals.

- **Drug resistance pump active:** High ABCB1 levels mean tumor cells push chemotherapy out before it can work, explaining resistance to platinum drugs.

- **Six distinct tumor regions:** Different areas of your tumor have unique characteristics, including active growth zones, low-oxygen areas, and immune-infiltrated regions.

- **Hypoxic zones identified:** Low-oxygen areas resist standard chemotherapy but may respond to specialized drugs that target hypoxic cells.

- **Immune cells present:** Areas with high immune activity suggest your body is fighting back and may respond to immunotherapy approaches.

---

### WHAT THIS MEANS FOR YOUR TREATMENT

- **PI3K/AKT inhibitors:** Block the backup survival pathway we found (drugs like Alpelisib are available in clinical trials).

- **Resistance reversal agents:** Stop the ABCB1 pump from ejecting chemotherapy, making your tumor more vulnerable to existing drugs.

- **Hypoxia-targeting drugs:** Specialized treatments designed to kill cancer cells in low-oxygen zones where regular chemo doesn't reach.

---

### NEXT STEPS

- Ask your oncologist about PI3K inhibitor clinical trials for platinum-resistant ovarian cancer
- Discuss combining resistance reversal drugs with your current bevacizumab (Avastin) therapy
- Review options considering your treatment goals, quality of life, and personal preferences

---

### BY THE NUMBERS

- **17 genes** significantly different between tumor and normal tissue
- **6 regions** within tumor, each with unique treatment vulnerabilities
- **3× higher** resistance pathway activity compared to healthy cells
- **31 genes** showing spatial patterns revealing tumor organization

---

*This analysis is for education and research. Your oncology team will determine the best treatment plan for your specific situation.*

---

## Visual Design Suggestions

[Optional: Add suggestions for how designers should treat this text]

### Layout Recommendations:

**Title:** Large, bold, top of page

**Key Findings:**
- Use icons for each bullet (e.g., 🔬 for molecular, 🎯 for targeting, 💊 for drugs)
- Stagger bullets or use circular layout
- Each bullet in separate visual block

**What This Means:**
- Use different color (e.g., blue for findings, green for treatments)
- Arrow or bridge graphic connecting "findings" to "treatment"
- Box or highlight to emphasize actionable items

**Next Steps:**
- Numbered list or checklist visual
- Calendar icon or "appointment prep" theme
- Separate tear-off section if printed

**Statistics:**
- Bar charts or circular progress indicators
- Large numbers with small context labels
- Visual comparison (normal vs. tumor)

---

## Validation Checklist

Before finalizing output, verify:
- [ ] Each bullet is 10-25 words (not longer)
- [ ] Bold lead-in phrases are scannable (patient can skim just bold parts)
- [ ] No unexplained jargon or acronyms
- [ ] Every bullet answers "so what?" not just "what?"
- [ ] Active voice throughout ("detected" not "was detected")
- [ ] Numbers include context ("3× higher" not just "3×")
- [ ] Total text is under 300 words (leaves room for visual design)
- [ ] Disclaimer included at bottom
- [ ] Reading level is 6th-8th grade

---

## Usage Notes

**When to use this template:**
- Creating patient handouts or take-home summaries
- Designing waiting room educational posters
- Building digital infographics for patient portals
- Making visual aids for doctor-patient consultations

**Who creates the visual design:**
- Medical illustrator or graphic designer (NOT generated by LLM)
- Use tools like Canva, Adobe Illustrator, or medical design templates
- Consult with patient advocates on accessibility (colorblind-friendly palettes, readable fonts)

**Text + Visual workflow:**
1. Generate text using this template → LLM output
2. Share text with graphic designer → Designer creates visual mockup
3. Oncologist reviews for accuracy → Medical approval
4. Patient advocate reviews for clarity → Readability check
5. Finalize design → Ready for patient use

**Customization tips:**
- Add statistics: If you have compelling numbers, include "By the Numbers" section for visual charts
- Shorten further: For poster format, use only 3-4 bullets in "Key Findings"
- Add photos: Consider space for patient's actual spatial heatmap or microscopy images (with labels)
- Multiple languages: Generate text in Spanish, Mandarin, etc. using same template structure

---

## Common Visual Pairings

**These text bullets pair well with:**

| Text Topic | Visual Element |
|------------|----------------|
| Multiple tumor regions | Spatial heatmap with labeled regions |
| Drug resistance pump | Illustration of cell with "pump" ejecting drug |
| PI3K/AKT pathway | Flowchart showing pathway and where drug blocks |
| Hypoxic zones | Color-coded map showing low-oxygen areas |
| Immune infiltration | Cell illustrations showing immune cells attacking tumor |
| Statistics | Bar charts, circular progress, comparison graphics |

---

## Accessibility Considerations

**For printed materials:**
- Font size ≥14pt for bullet text, ≥18pt for bold lead-ins
- High contrast (black text on white, or dark blue on light yellow)
- Sans-serif fonts (Arial, Helvetica, Calibri)
- Leave white space between bullets

**For digital materials:**
- Alt text for all images (describe visual elements)
- Screen reader compatible PDF format
- Clickable "Read Aloud" option if possible
- Mobile-responsive design (stack elements vertically)

**For non-English speakers:**
- Provide translations in common languages for your patient population
- Use universal icons (not culturally specific symbols)
- Consider health literacy levels in translation (simpler than English version)

---

## Example: Side-by-Side Comparison

### ❌ Too Technical (Original):
```
• TP53 mutation: log2FC = 4.654, FDR = 5.04e-20
• 31 genes with significant spatial autocorrelation (Moran's I > 0.1, p < 0.001)
• PIK3CA/AKT1/MTOR dysregulation suggests PI3K pathway dependency
```

### ✅ Patient-Friendly (Template Output):
```
• Multiple survival routes detected: Your tumor uses the PI3K/AKT pathway
  as a backup to survive even when chemotherapy blocks other growth signals.

• Six distinct tumor regions: Different areas have unique characteristics
  including active growth zones and low-oxygen regions.

• New treatment targets identified: PI3K inhibitor drugs may block the
  backup survival pathway we found active in your tumor.
```

---

**Template Version:** 1.0
**Maintained by:** precision-medicine-mcp project

**Design Resources:**
- [CDC Clear Communication Index](https://www.cdc.gov/ccindex/) - Health literacy principles
- [Cancer.Net Patient Infographic Gallery](https://www.cancer.net/research-and-advocacy/cancer-infographics) - Examples
- [NCI Visuals Online](https://visualsonline.cancer.gov) - Medical illustrations
