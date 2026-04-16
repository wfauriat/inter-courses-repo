"""
00_architecture_spine.py
========================
End-to-end architecture diagram of a decoder-only transformer (GPT-2 small)
with dimensionality annotations at every stage.

Pure matplotlib diagram -- no model loading required.
Run:  python 00_architecture_spine.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------------------
# Colour scheme
# ---------------------------------------------------------------------------
COL_BG = "#FAFAFA"           # overall background
COL_BOX = "#4C72B0"          # standard stage boxes
COL_BOX_LIGHT = "#D6E0F0"    # standard box fill
COL_BLOCK = "#55A868"        # transformer-block accent
COL_BLOCK_LIGHT = "#D5EDDB"  # transformer-block fill
COL_BLOCK_INNER = "#E8F4EC"  # inner sub-step fill
COL_INPUT = "#DD8452"         # input / output accent
COL_INPUT_LIGHT = "#FAE3D2"  # input / output fill
COL_TEXT = "#2B2B2B"         # primary text
COL_DIM = "#6B6B6B"          # dimension annotations
COL_ARROW = "#555555"        # arrows


# ---------------------------------------------------------------------------
# Layout helpers
# ---------------------------------------------------------------------------
def draw_box(ax, cx, cy, w, h, label, dim_text=None,
             edge_col=COL_BOX, fill_col=COL_BOX_LIGHT,
             fontsize=11, fontweight="bold", dim_fontsize=9.5,
             text_col=COL_TEXT, radius=0.015):
    """Draw a rounded box centred at (cx, cy) with a label and optional
    dimension annotation to the right."""
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=1.6, edgecolor=edge_col, facecolor=fill_col,
        zorder=2,
    )
    ax.add_patch(box)
    ax.text(cx, cy, label, ha="center", va="center",
            fontsize=fontsize, fontweight=fontweight, color=text_col,
            zorder=3)
    if dim_text:
        ax.text(cx + w / 2 + 0.12, cy, dim_text,
                ha="left", va="center",
                fontsize=dim_fontsize, color=COL_DIM, style="italic",
                fontfamily="monospace", zorder=3)
    return cy - h / 2  # return bottom y for arrow drawing


def draw_arrow(ax, x, y_top, y_bot, color=COL_ARROW, lw=1.4,
               head_w=0.06, head_l=0.025):
    """Draw a downward arrow from y_top to y_bot at x-coordinate x."""
    ax.annotate(
        "", xy=(x, y_bot), xytext=(x, y_top),
        arrowprops=dict(
            arrowstyle=f"->,head_width={head_w},head_length={head_l}",
            color=color, lw=lw,
        ),
        zorder=1,
    )


# ---------------------------------------------------------------------------
# Main figure
# ---------------------------------------------------------------------------
def make_figure():
    set_style()

    fig, ax = plt.subplots(figsize=(10, 17))
    ax.set_xlim(-1.2, 3.8)
    ax.set_ylim(-0.3, 16.8)
    ax.axis("off")
    fig.patch.set_facecolor(COL_BG)

    # Centre line for the spine
    CX = 1.0
    BOX_W = 2.6
    BOX_H = 0.52
    GAP = 0.24          # arrow gap between boxes
    INNER_GAP = 0.16    # gap inside transformer block

    # ----- Title -----
    ax.text(CX, 16.55, "Decoder-Only Transformer  (GPT-2 small)",
            ha="center", va="center", fontsize=16, fontweight="bold",
            color=COL_TEXT)
    ax.text(CX, 16.2, "End-to-end data flow with tensor shapes",
            ha="center", va="center", fontsize=11, color=COL_DIM)

    # Track current y position (top-down)
    y = 15.6

    # ===== 1. Input text =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             'Input text:  "The cat sits"', dim_text="string",
             edge_col=COL_INPUT, fill_col=COL_INPUT_LIGHT,
             fontsize=11, fontweight="semibold")
    arrow_top = y - BOX_H / 2
    y -= BOX_H + GAP

    draw_arrow(ax, CX, arrow_top, y + BOX_H / 2)

    # ===== 2. Tokenizer =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             "Tokenizer  \u2192  [464, 3797, 13015]",
             dim_text="(3,)  int",
             edge_col=COL_BOX, fill_col=COL_BOX_LIGHT)
    arrow_top = y - BOX_H / 2
    y -= BOX_H + GAP

    draw_arrow(ax, CX, arrow_top, y + BOX_H / 2)

    # ===== 3. Token embedding =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             "Token Embedding Table",
             dim_text="(3, 768)",
             edge_col=COL_BOX, fill_col=COL_BOX_LIGHT)
    arrow_top = y - BOX_H / 2
    y -= BOX_H + GAP

    draw_arrow(ax, CX, arrow_top, y + BOX_H / 2)

    # ===== 4. + Positional encoding =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             "+ Positional Encoding",
             dim_text="(3, 768)",
             edge_col=COL_BOX, fill_col=COL_BOX_LIGHT)
    arrow_top = y - BOX_H / 2
    y -= BOX_H + GAP + 0.05

    draw_arrow(ax, CX, arrow_top, y + 0.05)

    # ===== 5. Transformer block (large grouped box) =====
    BLOCK_W = BOX_W + 0.50
    # Pre-compute inner heights
    inner_h = 0.42
    n_inner = 4            # LN+Attn, +Residual, LN+FFN, +Residual
    block_inner_height = n_inner * inner_h + (n_inner - 1) * INNER_GAP
    block_pad_top = 0.62
    block_pad_bot = 0.38
    BLOCK_H = block_inner_height + block_pad_top + block_pad_bot

    block_top = y + 0.05
    block_bot = block_top - BLOCK_H

    # Outer block rectangle
    outer_box = FancyBboxPatch(
        (CX - BLOCK_W / 2, block_bot), BLOCK_W, BLOCK_H,
        boxstyle="round,pad=0,rounding_size=0.03",
        linewidth=2.2, edgecolor=COL_BLOCK, facecolor=COL_BLOCK_LIGHT,
        zorder=1, linestyle="-",
    )
    ax.add_patch(outer_box)

    # Block header label
    ax.text(CX, block_top - 0.25,
            "Transformer Block   (\u00d712)",
            ha="center", va="center", fontsize=12.5, fontweight="bold",
            color=COL_BLOCK, zorder=3)

    # Dimension annotation to the right of the block
    ax.text(CX + BLOCK_W / 2 + 0.12, (block_top + block_bot) / 2,
            "(3, 768)\nthroughout",
            ha="left", va="center", fontsize=9.5, color=COL_DIM,
            style="italic", fontfamily="monospace", zorder=3)

    # Inner sub-steps
    inner_labels = [
        "LayerNorm  \u2192  Multi-Head Attention (12 heads)",
        "+ Residual Connection",
        "LayerNorm  \u2192  FFN:  768 \u2192 3072 \u2192 768",
        "+ Residual Connection",
    ]
    inner_w = BOX_W - 0.10
    iy = block_top - block_pad_top

    for i, lbl in enumerate(inner_labels):
        is_residual = "Residual" in lbl
        ec = "#7CB68A" if is_residual else COL_BLOCK
        fc = COL_BLOCK_INNER
        fw = "normal" if is_residual else "semibold"
        fs = 9.5 if is_residual else 10
        draw_box(ax, CX, iy, inner_w, inner_h, lbl,
                 edge_col=ec, fill_col=fc,
                 fontsize=fs, fontweight=fw,
                 radius=0.012)
        if i < n_inner - 1:
            draw_arrow(ax, CX, iy - inner_h / 2,
                       iy - inner_h / 2 - INNER_GAP,
                       color=COL_BLOCK, lw=1.0,
                       head_w=0.04, head_l=0.018)
        iy -= inner_h + INNER_GAP

    # Arrow out of the block
    y = block_bot - GAP
    draw_arrow(ax, CX, block_bot, y + BOX_H / 2,
               color=COL_ARROW, lw=1.4)

    # Repeat annotation (loop arrow on the left side of the block)
    loop_x = CX - BLOCK_W / 2 - 0.15
    mid_y = (block_top + block_bot) / 2
    ax.annotate(
        "", xy=(loop_x, block_top - 0.15),
        xytext=(loop_x, block_bot + 0.15),
        arrowprops=dict(
            arrowstyle=f"->,head_width=0.06,head_length=0.03",
            color=COL_BLOCK, lw=1.6,
            connectionstyle="arc3,rad=0.4",
        ),
        zorder=1,
    )
    ax.text(loop_x - 0.28, mid_y, "repeat\n\u00d712",
            ha="center", va="center", fontsize=9.5,
            color=COL_BLOCK, fontweight="bold", zorder=3)

    # ===== 6. Final LayerNorm =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             "Final LayerNorm",
             dim_text="(3, 768)",
             edge_col=COL_BOX, fill_col=COL_BOX_LIGHT)
    arrow_top = y - BOX_H / 2
    y -= BOX_H + GAP

    draw_arrow(ax, CX, arrow_top, y + BOX_H / 2)

    # ===== 7. Linear projection =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             "Linear Projection  (unembedding)",
             dim_text="(3, 50257)",
             edge_col=COL_BOX, fill_col=COL_BOX_LIGHT)
    arrow_top = y - BOX_H / 2
    y -= BOX_H + GAP

    draw_arrow(ax, CX, arrow_top, y + BOX_H / 2)

    # ===== 8. Softmax =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             "Softmax  \u2192  probabilities",
             dim_text="(3, 50257)",
             edge_col=COL_BOX, fill_col=COL_BOX_LIGHT)
    arrow_top = y - BOX_H / 2
    y -= BOX_H + GAP

    draw_arrow(ax, CX, arrow_top, y + BOX_H / 2)

    # ===== 9. Next token =====
    draw_box(ax, CX, y, BOX_W, BOX_H,
             'Next token:  " on"   (argmax of last position)',
             dim_text="int",
             edge_col=COL_INPUT, fill_col=COL_INPUT_LIGHT,
             fontsize=10.5, fontweight="semibold")

    # ---- Small legend at bottom ----
    legend_y = y - BOX_H / 2 - 0.45
    ax.text(CX, legend_y,
            "GPT-2 small:  12 layers  \u00b7  12 heads  \u00b7  d_model = 768  "
            "\u00b7  d_ff = 3072  \u00b7  vocab = 50 257",
            ha="center", va="center", fontsize=9, color=COL_DIM,
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#F0F0F0",
                      edgecolor="#CCCCCC", linewidth=0.8))

    fig.tight_layout()
    return fig


if __name__ == "__main__":
    fig = make_figure()
    save_fig(fig, "00_architecture_spine")
