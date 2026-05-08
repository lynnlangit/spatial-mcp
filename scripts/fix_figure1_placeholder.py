import fitz  # PyMuPDF
import os

PDF_IN  = "docs/HGSOC_Platform_Paper_v17.pdf"
PDF_TMP = "docs/HGSOC_Platform_Paper_v17_tmp.pdf"
PDF_OUT = "docs/HGSOC_Platform_Paper_v17.pdf"
FIG_PNG = "docs/figures/figure1_pipeline.png"

# Page layout (US Letter 612x792)
# Body text column: 73.7 - 525.0
# Table cells extend to x=541, so redaction must go wider
COL_LEFT  = 73.7
COL_RIGHT = 525.0
REDACT_LEFT  = 60
REDACT_RIGHT = 550

CAPTION = (
    "Figure 1. Five-stage MCP precision oncology pipeline. "
    "Patient data flows left to right from intake through report "
    "generation. PAT003 (preventive cardiovascular health) executes "
    "a parallel 5-tool cardiometabolic workflow at Stage 1."
)

doc = fitz.open(PDF_IN)

# ── Page 2 ──
page = doc[1]
blocks = page.get_text("blocks")
placeholder_block = None
for b in blocks:
    if "FIGURE 1 PLACEHOLDER" in b[4]:
        placeholder_block = b
        break

if not placeholder_block:
    print("ERROR: Placeholder not found on page 2")
    doc.close()
    exit(1)

ph_top = placeholder_block[1]
print(f"Placeholder at y={ph_top:.1f}-{placeholder_block[3]:.1f}")

# Redact everything from placeholder to just above the footer (y=755)
# Wide enough to cover table cell borders (x=71 to x=541)
redact_p2 = fitz.Rect(REDACT_LEFT, ph_top - 5, REDACT_RIGHT, 755)
page.add_redact_annot(redact_p2, fill=(1, 1, 1))
page.apply_redactions(graphics=1)  # 1 = remove vector graphics that overlap
print(f"Page 2 redacted: {redact_p2}")

# Insert figure — full column width
fig_rect = fitz.Rect(COL_LEFT, ph_top, COL_RIGHT, 718)
page.insert_image(fig_rect, filename=FIG_PNG, keep_proportion=True)
print(f"Figure inserted at: {fig_rect}")

# Insert caption using textbox for proper wrapping
caption_rect = fitz.Rect(COL_LEFT, 722, COL_RIGHT, 752)
page.insert_textbox(
    caption_rect,
    CAPTION,
    fontsize=8,
    fontname="helv",
    color=(0, 0, 0),
    align=fitz.TEXT_ALIGN_LEFT,
)
print(f"Caption textbox at: {caption_rect}")

# ── Page 3: redact the stage table continuation ──
page3 = doc[2]
# Stage table body: drawings 2-21 span y=43 to y=291
# Redact generously to cover all table cells and borders
redact_p3 = fitz.Rect(REDACT_LEFT, 30, REDACT_RIGHT, 305)
page3.add_redact_annot(redact_p3, fill=(1, 1, 1))
page3.apply_redactions(graphics=1)
print(f"Page 3 redacted: {redact_p3}")

doc.save(PDF_TMP, garbage=4, deflate=True)
doc.close()
os.replace(PDF_TMP, PDF_OUT)
print(f"Saved: {PDF_OUT}")
