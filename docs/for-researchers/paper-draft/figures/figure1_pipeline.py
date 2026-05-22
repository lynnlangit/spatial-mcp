import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(16, 7))
ax.set_xlim(0, 16)
ax.set_ylim(0, 7)
ax.axis('off')

stages = [
    {
        "num": "1",
        "title": "Data Acquisition",
        "servers": "mockepic \u00b7 fgbio\nmocktcga \u00b7 geodownload\ngenomic-results",
        "outputs": "Variant calls\nHRD score\nExpression matrix",
        "color": "#2E86AB",
        "x": 0.3
    },
    {
        "num": "2",
        "title": "Spatial\nDeconvolution",
        "servers": "spatialtools\ncibersortx",
        "outputs": "Cell-type fractions\nMoran's I",
        "color": "#A23B72",
        "x": 3.5
    },
    {
        "num": "3",
        "title": "Target\nProfiling",
        "servers": "opentargets\nmultiomics",
        "outputs": "Ranked targets\nDrug candidates",
        "color": "#F18F01",
        "x": 6.7
    },
    {
        "num": "4",
        "title": "Causal\nInference",
        "servers": "perturbation \u00b7 quantum\nneoantigen \u00b7 cell-classify\nopenimagedata",
        "outputs": "Perturbation predictions\nEvasion scores\nNeoantigens",
        "color": "#C73E1D",
        "x": 9.9
    },
    {
        "num": "5",
        "title": "Report\nSynthesis",
        "servers": "patient-report\nclinicaltrials",
        "outputs": "PDF report\nTrial matches",
        "color": "#3B1F2B",
        "x": 13.1
    }
]

BOX_W = 2.7
BOX_H = 5.5
TOP_H = 1.2
ARROW_Y = 3.5

for s in stages:
    x = s["x"]
    # Stage header box
    header = FancyBboxPatch((x, 5.5), BOX_W, TOP_H,
                             boxstyle="round,pad=0.05",
                             facecolor=s["color"], edgecolor='none')
    ax.add_patch(header)
    ax.text(x + BOX_W/2, 6.35, f"Stage {s['num']}", ha='center', va='center',
            fontsize=9, fontweight='bold', color='white')
    ax.text(x + BOX_W/2, 5.85, s["title"], ha='center', va='center',
            fontsize=8, color='white')

    # Body box
    body = FancyBboxPatch((x, 1.0), BOX_W, 4.4,
                           boxstyle="round,pad=0.05",
                           facecolor='#F5F5F5', edgecolor=s["color"], linewidth=1.5)
    ax.add_patch(body)

    # Servers label
    ax.text(x + BOX_W/2, 4.9, "Servers", ha='center', va='center',
            fontsize=7, color='#555555', style='italic')
    ax.text(x + BOX_W/2, 3.9, s["servers"], ha='center', va='center',
            fontsize=7.5, color='#222222', linespacing=1.5)

    # Divider
    ax.plot([x + 0.15, x + BOX_W - 0.15], [3.0, 3.0], color=s["color"],
            linewidth=0.8, linestyle='--', alpha=0.5)

    # Outputs label
    ax.text(x + BOX_W/2, 2.6, "Key Outputs", ha='center', va='center',
            fontsize=7, color='#555555', style='italic')
    ax.text(x + BOX_W/2, 1.8, s["outputs"], ha='center', va='center',
            fontsize=7.5, color='#222222', linespacing=1.5)

    # Arrow between stages
    if x < stages[-1]["x"]:
        ax.annotate('', xy=(x + BOX_W + 0.3, ARROW_Y),
                    xytext=(x + BOX_W + 0.05, ARROW_Y),
                    arrowprops=dict(arrowstyle='->', color='#888888', lw=1.5))

# PAT003 cardiometabolic note
ax.text(0.3, 0.55,
        "PAT003 (preventive CVD): parallel 5-tool cardiometabolic workflow at Stage 1 "
        "(Reynolds \u00b7 Framingham \u00b7 PCE \u00b7 biomarker panel \u00b7 statin decision logic)",
        fontsize=7.5, color='#555555', style='italic')

# Patient icons top-left
ax.text(0.3, 6.85, "PAT001 (HGSOC) \u00b7 PAT002 (ER+ BC) \u00b7 PAT003 (CVD)",
        fontsize=8, color='#333333', fontweight='bold')

plt.tight_layout(pad=0.3)
plt.savefig('docs/for-researchers/paper-v17/figures/figure1_pipeline.pdf', bbox_inches='tight', dpi=300)
plt.savefig('docs/for-researchers/paper-v17/figures/figure1_pipeline.png', bbox_inches='tight', dpi=300)
print("Figure 1 saved: docs/for-researchers/paper-v17/figures/figure1_pipeline.pdf + .png")
