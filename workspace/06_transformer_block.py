"""
06_transformer_block.py
=======================
Educational visualization: one transformer block in detail.

Produces two figures:
  - 06_transformer_block.png       Block diagram with tensor shapes and residual
                                   connections, tracing a token through GPT-2 small.
  - 06_residual_evolution.png      Cosine similarity of each layer's hidden state
                                   (last token) to the final layer, showing how
                                   representations progressively refine.

Usage:
    source ~/.venvDS/bin/activate
    python workspace/06_transformer_block.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ---------------------------------------------------------------------------
# Colour scheme  (aligned with 00_architecture_spine.py)
# ---------------------------------------------------------------------------
COL_BG       = "#FAFAFA"
COL_TEXT      = "#2B2B2B"
COL_DIM       = "#6B6B6B"
COL_ARROW     = "#555555"

COL_INPUT     = "#DD8452"
COL_INPUT_LT  = "#FAE3D2"

COL_LN        = "#8172B3"      # LayerNorm -- purple accent
COL_LN_LT     = "#E1DCED"

COL_ATTN      = "#4C72B0"      # Attention -- blue accent
COL_ATTN_LT   = "#D6E0F0"

COL_FFN       = "#55A868"      # FFN -- green accent
COL_FFN_LT    = "#D5EDDB"

COL_ADD       = "#C44E52"      # Residual add -- red accent
COL_ADD_LT    = "#F2D5D6"

COL_RESID     = "#C44E52"      # residual bypass arrows


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def _box(ax, cx, cy, w, h, label, dim_text=None,
         edge_col=COL_ATTN, fill_col=COL_ATTN_LT,
         fontsize=10.5, fontweight="bold", dim_side="right",
         radius=0.012, alpha=1.0, label_lines=None):
    """Draw a rounded box centred at (cx, cy)."""
    box = mpatches.FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=1.6, edgecolor=edge_col, facecolor=fill_col,
        zorder=2, alpha=alpha,
    )
    ax.add_patch(box)
    if label_lines:
        n = len(label_lines)
        line_gap = 0.28
        top_y = cy + (n - 1) * line_gap / 2
        for i, (txt, fs, fw) in enumerate(label_lines):
            ax.text(cx, top_y - i * line_gap, txt,
                    ha="center", va="center",
                    fontsize=fs, fontweight=fw, color=COL_TEXT, zorder=3)
    elif label:
        ax.text(cx, cy, label, ha="center", va="center",
                fontsize=fontsize, fontweight=fontweight, color=COL_TEXT,
                zorder=3)
    if dim_text:
        if dim_side == "right":
            ax.text(cx + w / 2 + 0.08, cy, dim_text,
                    ha="left", va="center",
                    fontsize=9, color=COL_DIM, style="italic",
                    fontfamily="monospace", zorder=3)
        else:
            ax.text(cx - w / 2 - 0.08, cy, dim_text,
                    ha="right", va="center",
                    fontsize=9, color=COL_DIM, style="italic",
                    fontfamily="monospace", zorder=3)


def _arrow_down(ax, x, y1, y2, color=COL_ARROW, lw=1.3):
    """Downward arrow from y1 to y2 at x."""
    ax.annotate("", xy=(x, y2), xytext=(x, y1),
                arrowprops=dict(arrowstyle="->,head_width=0.05,head_length=0.02",
                                color=color, lw=lw), zorder=1)


def _arrow_to(ax, x1, y1, x2, y2, color=COL_ARROW, lw=1.3,
              connectionstyle=None, style="-"):
    """General arrow between two points."""
    props = dict(arrowstyle="->,head_width=0.05,head_length=0.02",
                 color=color, lw=lw, linestyle=style)
    if connectionstyle:
        props["connectionstyle"] = connectionstyle
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=props, zorder=1)


# ---------------------------------------------------------------------------
# Figure 1 -- Block diagram with tensor shapes
# ---------------------------------------------------------------------------
def make_block_diagram():
    set_style()

    fig, ax = plt.subplots(figsize=(12, 18))
    ax.set_xlim(-2.5, 5.5)
    ax.set_ylim(-0.5, 19.0)
    ax.axis("off")
    fig.patch.set_facecolor(COL_BG)

    # Layout constants
    CX = 1.2            # main spine x
    BW = 3.0            # box width
    BH = 0.52           # standard box height
    BH_TALL = 0.72      # taller boxes (attention detail, FFN detail)
    GAP = 0.32          # vertical gap between boxes
    SMALL_GAP = 0.22

    # Residual bypass x offset
    RES_X = CX - BW / 2 - 0.55

    # ----- Title -----
    ax.text(CX, 18.65, "One Transformer Block  (GPT-2 small)",
            ha="center", va="center", fontsize=17, fontweight="bold",
            color=COL_TEXT)
    ax.text(CX, 18.30, "Pre-norm architecture  :  LayerNorm \u2192 Attention \u2192 Add \u2192 LayerNorm \u2192 FFN \u2192 Add",
            ha="center", va="center", fontsize=10.5, color=COL_DIM)

    y = 17.6

    # ===== INPUT =====
    _box(ax, CX, y, BW, BH, "Input  x", dim_text="(seq, 768)",
         edge_col=COL_INPUT, fill_col=COL_INPUT_LT, fontsize=12)
    input_y = y
    y -= BH / 2 + GAP

    _arrow_down(ax, CX, input_y - BH / 2, y + BH / 2)

    # ===== LAYERNORM 1 =====
    _box(ax, CX, y, BW, BH, "LayerNorm 1", dim_text="(seq, 768)",
         edge_col=COL_LN, fill_col=COL_LN_LT)
    ln1_y = y
    y -= BH / 2 + SMALL_GAP

    _arrow_down(ax, CX, ln1_y - BH / 2, y + BH_TALL / 2)

    # ===== Q, K, V PROJECTIONS =====
    proj_y = y
    proj_w = 0.88
    proj_h = BH_TALL
    proj_gap_x = 1.05
    for i, (letter, note) in enumerate([("Q", "W_Q"), ("K", "W_K"), ("V", "W_V")]):
        px = CX - proj_gap_x + i * proj_gap_x
        _box(ax, px, proj_y, proj_w, proj_h,
             f"{letter} = x \u00b7 {note}", dim_text=None,
             edge_col=COL_ATTN, fill_col=COL_ATTN_LT,
             fontsize=9, fontweight="semibold")
    # Dimension annotation spanning all three
    ax.text(CX + proj_gap_x + proj_w / 2 + 0.08, proj_y,
            "(seq, 12\u00d764)\n= (seq, 768)",
            ha="left", va="center", fontsize=9, color=COL_DIM,
            style="italic", fontfamily="monospace")
    # Fan-out arrows from LN to Q, K, V
    for i in range(3):
        px = CX - proj_gap_x + i * proj_gap_x
        _arrow_to(ax, CX, ln1_y - BH / 2, px, proj_y + proj_h / 2,
                  color=COL_ATTN, lw=1.0)
    y = proj_y - proj_h / 2 - SMALL_GAP

    # ===== MULTI-HEAD ATTENTION =====
    _arrow_down(ax, CX, proj_y - proj_h / 2, y + BH_TALL / 2, color=COL_ATTN)
    _box(ax, CX, y, BW, BH_TALL, None,
         dim_text="(seq, seq) per head",
         edge_col=COL_ATTN, fill_col=COL_ATTN_LT,
         label_lines=[
             ("Scaled Dot-Product Attention", 10.5, "bold"),
             ("softmax(QK\u1d40 / \u221a64) \u00b7 V   \u00d7 12 heads", 9.5, "normal"),
         ])
    attn_y = y
    y -= BH_TALL / 2 + SMALL_GAP

    # ===== OUTPUT PROJECTION =====
    _arrow_down(ax, CX, attn_y - BH_TALL / 2, y + BH / 2, color=COL_ATTN)
    _box(ax, CX, y, BW, BH,
         "Output Projection  W_O", dim_text="(seq, 768)",
         edge_col=COL_ATTN, fill_col=COL_ATTN_LT,
         fontsize=10)
    out_proj_y = y
    y -= BH / 2 + GAP

    # ===== RESIDUAL ADD 1 =====
    _arrow_down(ax, CX, out_proj_y - BH / 2, y + BH / 2)
    _box(ax, CX, y, BW, BH,
         "+   Residual Add", dim_text="(seq, 768)",
         edge_col=COL_ADD, fill_col=COL_ADD_LT,
         fontsize=11, fontweight="bold")
    add1_y = y

    # --- Draw residual bypass 1: from input, bypass attention, merge at add1 ---
    # Start: left side of input box
    res1_start_y = input_y
    res1_end_y = add1_y
    # Draw L-shaped bypass: left from input, down, then right into add
    _arrow_to(ax, CX - BW / 2, res1_start_y,
              RES_X, res1_start_y,
              color=COL_RESID, lw=2.0, style="--")
    ax.plot([RES_X, RES_X], [res1_start_y, res1_end_y],
            color=COL_RESID, lw=2.0, linestyle="--", zorder=1)
    _arrow_to(ax, RES_X, res1_end_y,
              CX - BW / 2, res1_end_y,
              color=COL_RESID, lw=2.0, style="--")
    # Label
    ax.text(RES_X - 0.12, (res1_start_y + res1_end_y) / 2,
            "skip\nconnection",
            ha="right", va="center", fontsize=8.5, color=COL_RESID,
            fontweight="bold", rotation=90)

    y -= BH / 2 + GAP

    # ===== LAYERNORM 2 =====
    _arrow_down(ax, CX, add1_y - BH / 2, y + BH / 2)
    _box(ax, CX, y, BW, BH, "LayerNorm 2", dim_text="(seq, 768)",
         edge_col=COL_LN, fill_col=COL_LN_LT)
    ln2_y = y
    y -= BH / 2 + SMALL_GAP

    # ===== FFN: Linear 1 =====
    _arrow_down(ax, CX, ln2_y - BH / 2, y + BH / 2, color=COL_FFN)
    _box(ax, CX, y, BW, BH,
         "Linear:  768 \u2192 3072", dim_text="(seq, 3072)",
         edge_col=COL_FFN, fill_col=COL_FFN_LT, fontsize=10.5)
    ffn1_y = y
    y -= BH / 2 + SMALL_GAP

    # ===== GELU =====
    _arrow_down(ax, CX, ffn1_y - BH / 2, y + BH / 2, color=COL_FFN)
    _box(ax, CX, y, BW, BH * 0.85,
         "GELU Activation", dim_text="(seq, 3072)",
         edge_col=COL_FFN, fill_col=COL_FFN_LT, fontsize=10)
    gelu_y = y
    y -= BH * 0.85 / 2 + SMALL_GAP

    # ===== FFN: Linear 2 =====
    _arrow_down(ax, CX, gelu_y - BH * 0.85 / 2, y + BH / 2, color=COL_FFN)
    _box(ax, CX, y, BW, BH,
         "Linear:  3072 \u2192 768", dim_text="(seq, 768)",
         edge_col=COL_FFN, fill_col=COL_FFN_LT, fontsize=10.5)
    ffn2_y = y
    y -= BH / 2 + GAP

    # ===== RESIDUAL ADD 2 =====
    _arrow_down(ax, CX, ffn2_y - BH / 2, y + BH / 2)
    _box(ax, CX, y, BW, BH,
         "+   Residual Add", dim_text="(seq, 768)",
         edge_col=COL_ADD, fill_col=COL_ADD_LT,
         fontsize=11, fontweight="bold")
    add2_y = y

    # --- Draw residual bypass 2: from add1 output, bypass FFN, merge at add2 ---
    res2_start_y = add1_y
    res2_end_y = add2_y
    RES2_X = CX + BW / 2 + 0.55   # right side for second residual
    _arrow_to(ax, CX + BW / 2, res2_start_y,
              RES2_X, res2_start_y,
              color=COL_RESID, lw=2.0, style="--")
    ax.plot([RES2_X, RES2_X], [res2_start_y, res2_end_y],
            color=COL_RESID, lw=2.0, linestyle="--", zorder=1)
    _arrow_to(ax, RES2_X, res2_end_y,
              CX + BW / 2, res2_end_y,
              color=COL_RESID, lw=2.0, style="--")
    # Label
    ax.text(RES2_X + 0.12, (res2_start_y + res2_end_y) / 2,
            "skip\nconnection",
            ha="left", va="center", fontsize=8.5, color=COL_RESID,
            fontweight="bold", rotation=270)

    y -= BH / 2 + GAP

    # ===== OUTPUT =====
    _arrow_down(ax, CX, add2_y - BH / 2, y + BH / 2)
    _box(ax, CX, y, BW, BH, "Output  (to next block)", dim_text="(seq, 768)",
         edge_col=COL_INPUT, fill_col=COL_INPUT_LT, fontsize=12)

    # ----- Legend / key insight box at the bottom -----
    legend_y = y - BH / 2 - 0.75
    insight_text = (
        "Key insight:  the input is ADDED back, not replaced.\n"
        "Each sub-layer (attention / FFN) only needs to learn the residual delta."
    )
    ax.text(CX, legend_y, insight_text,
            ha="center", va="center", fontsize=10.5, color=COL_TEXT,
            fontweight="semibold",
            bbox=dict(boxstyle="round,pad=0.45", facecolor="#FFF8F0",
                      edgecolor=COL_ADD, linewidth=1.5))

    # ----- GPT-2 specs footer -----
    footer_y = legend_y - 0.70
    ax.text(CX, footer_y,
            "GPT-2 small:  12 layers  \u00b7  12 heads  \u00b7  d_model = 768  "
            "\u00b7  d_ff = 3072  \u00b7  head_dim = 64",
            ha="center", va="center", fontsize=9, color=COL_DIM,
            fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#F0F0F0",
                      edgecolor="#CCCCCC", linewidth=0.8))

    # ----- Colour legend -----
    legend_items = [
        (COL_LN_LT, COL_LN, "LayerNorm"),
        (COL_ATTN_LT, COL_ATTN, "Attention"),
        (COL_FFN_LT, COL_FFN, "FFN"),
        (COL_ADD_LT, COL_ADD, "Residual Add"),
    ]
    lx_start = CX - 1.8
    ly = footer_y - 0.55
    for i, (fc, ec, label) in enumerate(legend_items):
        lx = lx_start + i * 1.55
        rect = mpatches.FancyBboxPatch(
            (lx, ly - 0.12), 0.24, 0.24,
            boxstyle="round,pad=0,rounding_size=0.04",
            facecolor=fc, edgecolor=ec, linewidth=1.2, zorder=2)
        ax.add_patch(rect)
        ax.text(lx + 0.34, ly, label, ha="left", va="center",
                fontsize=9, color=COL_TEXT, zorder=3)

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 2 -- Residual stream evolution (cosine similarity across layers)
# ---------------------------------------------------------------------------
def make_residual_evolution():
    """Run GPT-2 on a sentence and plot cosine similarity of each layer's
    last-token hidden state to the final layer's hidden state."""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM

    set_style()

    # --- Run the model ---
    print("  Loading GPT-2...")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_pretrained("gpt2", output_hidden_states=True)
    model.eval()

    sentence = "The cat sits on the mat"
    inputs = tokenizer(sentence, return_tensors="pt")
    tokens_str = [tokenizer.decode([tid]) for tid in inputs["input_ids"][0]]

    print(f"  Input: \"{sentence}\"")
    print(f"  Tokens: {tokens_str}")

    with torch.no_grad():
        outputs = model(**inputs)

    # hidden_states: tuple of (n_layers+1) tensors, each (1, seq_len, 768)
    # Index 0 = embedding output, indices 1..12 = after each transformer block
    hidden_states = outputs.hidden_states  # 13 tensors total

    n_layers = len(hidden_states) - 1  # 12
    seq_len = hidden_states[0].shape[1]
    last_tok_idx = seq_len - 1

    # Extract last-token hidden state at each layer
    final_hidden = hidden_states[-1][0, last_tok_idx, :]  # (768,)

    cos_sims = []
    for layer_idx in range(n_layers + 1):
        h = hidden_states[layer_idx][0, last_tok_idx, :]  # (768,)
        cos = torch.nn.functional.cosine_similarity(
            h.unsqueeze(0), final_hidden.unsqueeze(0)
        ).item()
        cos_sims.append(cos)

    layer_indices = list(range(n_layers + 1))  # 0..12

    # --- Also compute per-token at all layers for a heatmap-style context ---
    all_cos = np.zeros((n_layers + 1, seq_len))
    for li in range(n_layers + 1):
        for ti in range(seq_len):
            h = hidden_states[li][0, ti, :]
            ref = hidden_states[-1][0, ti, :]
            all_cos[li, ti] = torch.nn.functional.cosine_similarity(
                h.unsqueeze(0), ref.unsqueeze(0)
            ).item()

    # --- Plot ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.5, 6),
                                    gridspec_kw={"width_ratios": [1.2, 1]})
    fig.patch.set_facecolor(COL_BG)

    # --- Left panel: line chart (last token) ---
    ax1.plot(layer_indices, cos_sims, "o-",
             color=COLOR_PALETTE[0], linewidth=2.5, markersize=8,
             markerfacecolor="white", markeredgewidth=2.2,
             markeredgecolor=COLOR_PALETTE[0], zorder=3)

    # Shade under the curve
    ax1.fill_between(layer_indices, cos_sims, alpha=0.12,
                     color=COLOR_PALETTE[0])

    # Annotate first and last points
    ax1.annotate(f"{cos_sims[0]:.3f}",
                 (0, cos_sims[0]),
                 textcoords="offset points", xytext=(12, -18),
                 fontsize=10, color=COLOR_PALETTE[3], fontweight="bold")
    ax1.annotate(f"{cos_sims[-1]:.3f}",
                 (n_layers, cos_sims[-1]),
                 textcoords="offset points", xytext=(-12, -18),
                 fontsize=10, color=COLOR_PALETTE[2], fontweight="bold")

    ax1.set_xlabel("Layer  (0 = embedding, 1\u201312 = transformer blocks)")
    ax1.set_ylabel("Cosine similarity to final layer (layer 12)")
    ax1.set_title(f"Representation refinement: last token (\"{tokens_str[-1].strip()}\")",
                  fontsize=13, fontweight="bold")
    ax1.set_xticks(layer_indices)
    ax1.set_ylim(0, 1.05)
    ax1.set_xlim(-0.3, n_layers + 0.3)

    # Add insight annotation
    ax1.text(n_layers / 2, 0.15,
             "Early layers are far from the\n"
             "final representation; later layers\n"
             "converge progressively.",
             ha="center", va="center", fontsize=9.5, color=COL_DIM,
             fontstyle="italic",
             bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                       edgecolor="#CCCCCC", alpha=0.9))

    # --- Right panel: heatmap (all tokens) ---
    im = ax2.imshow(all_cos, aspect="auto", cmap="YlOrRd",
                    vmin=0, vmax=1, origin="lower",
                    interpolation="nearest")

    ax2.set_yticks(range(n_layers + 1))
    ax2.set_yticklabels([f"{i}" for i in range(n_layers + 1)])
    ax2.set_xticks(range(seq_len))
    # Clean up token labels
    clean_tokens = [t.strip() if t.strip() else t.replace(" ", "\u2423") for t in tokens_str]
    ax2.set_xticklabels(clean_tokens, fontsize=9, fontfamily="monospace",
                        rotation=45, ha="right")
    ax2.set_xlabel("Token")
    ax2.set_ylabel("Layer")
    ax2.set_title("Cosine sim. to final layer  (all tokens)",
                  fontsize=13, fontweight="bold")

    # Re-enable spines for heatmap
    for spine in ax2.spines.values():
        spine.set_visible(True)
        spine.set_color("#CCCCCC")
    ax2.grid(False)

    cbar = fig.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
    cbar.set_label("Cosine similarity", fontsize=10)

    fig.suptitle(
        f"Residual stream evolution through GPT-2    \u2014    \"{sentence}\"",
        fontsize=15, fontweight="bold", y=1.02,
    )

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Figure 1: Transformer block diagram ===")
    fig1 = make_block_diagram()
    save_fig(fig1, "06_transformer_block")

    print("\n=== Figure 2: Residual stream evolution ===")
    fig2 = make_residual_evolution()
    save_fig(fig2, "06_residual_evolution")

    print("\nDone.")
