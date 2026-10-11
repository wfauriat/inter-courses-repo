"""
05_feedforward.py
=================
Educational visualization: the feedforward network (MLP) inside each
transformer block performs a 4x expand-then-compress transformation
(768 -> 3072 -> 768 in GPT-2 small).

Produces two figures:
  - 05_ffn_shape.png         Schematic of the expand/compress geometry
  - 05_ffn_activations.png   Heatmap of intermediate neuron activations
                              across 8 diverse sentences

Usage:
    source ~/.venvDS/bin/activate
    python workspace/05_feedforward.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.colors as mcolors
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ---------------------------------------------------------------------------
# Colour scheme (consistent with the rest of the series)
# ---------------------------------------------------------------------------
COL_BG = "#FAFAFA"
COL_TEXT = "#2B2B2B"
COL_DIM = "#6B6B6B"
COL_ARROW = "#555555"
COL_INPUT = "#4C72B0"       # 768-dim layers
COL_INPUT_FILL = "#D6E0F0"
COL_EXPAND = "#DD8452"      # 3072-dim expansion
COL_EXPAND_FILL = "#FAE3D2"
COL_GELU = "#55A868"        # GELU activation
COL_GELU_FILL = "#D5EDDB"

LAYER_INDEX = 8  # which transformer block to hook into


# ---------------------------------------------------------------------------
# Figure 1 -- FFN expand / compress schematic
# ---------------------------------------------------------------------------

def make_shape_figure():
    """Diamond-shaped schematic showing 768 -> 3072 -> 768."""
    set_style()

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(-1.5, 11.5)
    ax.set_ylim(-0.5, 9.0)
    ax.axis("off")
    fig.patch.set_facecolor(COL_BG)

    # -- Title --
    ax.text(5.0, 8.5,
            "Feedforward Network (MLP) in Each Transformer Block",
            ha="center", va="center", fontsize=15, fontweight="bold",
            color=COL_TEXT)
    ax.text(5.0, 8.05,
            "GPT-2 small:  768  \u2192  3072  \u2192  768   (4\u00d7 expansion ratio)",
            ha="center", va="center", fontsize=11, color=COL_DIM,
            fontfamily="monospace")

    # -- Diamond shape via a filled polygon --
    # Three stages laid out vertically: input at top, expansion in middle,
    # output at bottom.  We draw a symmetric diamond whose width at each
    # stage is proportional to the dimensionality.

    cx = 5.0            # horizontal centre
    bar_h = 1.1         # height of each stage bar
    gap = 0.55          # vertical gap between bars

    # Widths proportional to dimension (768 vs 3072)
    w_narrow = 2.4      # represents 768
    w_wide = 8.0        # represents 3072

    # Vertical positions (top to bottom)
    y_input_top = 7.2
    y_input_bot = y_input_top - bar_h

    y_expand_top = y_input_bot - gap
    y_expand_bot = y_expand_top - bar_h

    y_gelu_top = y_expand_bot - gap
    y_gelu_bot = y_gelu_top - 0.5  # thinner bar for GELU

    y_output_top = y_gelu_bot - gap
    y_output_bot = y_output_top - bar_h

    # --- Draw the trapezoidal connectors (expansion fan and compression fan) ---
    # Expansion fan: connects narrow input to wide hidden
    fan_expand = plt.Polygon(
        [
            (cx - w_narrow / 2, y_input_bot),
            (cx + w_narrow / 2, y_input_bot),
            (cx + w_wide / 2,   y_expand_top),
            (cx - w_wide / 2,   y_expand_top),
        ],
        closed=True, facecolor="#E8E8E8", edgecolor="#BBBBBB",
        linewidth=0.8, alpha=0.5, zorder=0,
    )
    ax.add_patch(fan_expand)

    # Compression fan: connects wide hidden to narrow output
    fan_compress = plt.Polygon(
        [
            (cx - w_wide / 2,   y_gelu_bot),
            (cx + w_wide / 2,   y_gelu_bot),
            (cx + w_narrow / 2, y_output_top),
            (cx - w_narrow / 2, y_output_top),
        ],
        closed=True, facecolor="#E8E8E8", edgecolor="#BBBBBB",
        linewidth=0.8, alpha=0.5, zorder=0,
    )
    ax.add_patch(fan_compress)

    # --- Helper to draw a rounded bar ---
    def draw_bar(y_top, width, height, label, dim_label, edge_col, fill_col,
                 label_fs=12, dim_fs=11):
        box = FancyBboxPatch(
            (cx - width / 2, y_top - height), width, height,
            boxstyle="round,pad=0,rounding_size=0.08",
            linewidth=2.0, edgecolor=edge_col, facecolor=fill_col,
            zorder=2,
        )
        ax.add_patch(box)
        y_mid = y_top - height / 2
        ax.text(cx, y_mid, label,
                ha="center", va="center", fontsize=label_fs,
                fontweight="bold", color=COL_TEXT, zorder=3)
        # Dimension annotation to the right
        ax.text(cx + width / 2 + 0.2, y_mid, dim_label,
                ha="left", va="center", fontsize=dim_fs,
                color=edge_col, fontweight="bold",
                fontfamily="monospace", zorder=3)

    # 1) Input bar  (768)
    draw_bar(y_input_top, w_narrow, bar_h,
             "Input\n(from attention + residual)",
             "768",
             COL_INPUT, COL_INPUT_FILL, label_fs=11)

    # 2) First linear layer + expansion  (3072)
    draw_bar(y_expand_top, w_wide, bar_h,
             "First Linear Layer   (W\u2081x + b\u2081)",
             "3072",
             COL_EXPAND, COL_EXPAND_FILL)

    # 3) GELU activation (same width, thin bar)
    gelu_box = FancyBboxPatch(
        (cx - w_wide / 2, y_gelu_bot), w_wide, y_gelu_top - y_gelu_bot,
        boxstyle="round,pad=0,rounding_size=0.06",
        linewidth=1.5, edgecolor=COL_GELU, facecolor=COL_GELU_FILL,
        zorder=2,
    )
    ax.add_patch(gelu_box)
    ax.text(cx, (y_gelu_top + y_gelu_bot) / 2,
            "GELU activation  (element-wise nonlinearity)",
            ha="center", va="center", fontsize=10.5, fontweight="bold",
            color=COL_TEXT, zorder=3)
    ax.text(cx + w_wide / 2 + 0.2, (y_gelu_top + y_gelu_bot) / 2,
            "3072", ha="left", va="center", fontsize=11,
            color=COL_GELU, fontweight="bold", fontfamily="monospace",
            zorder=3)

    # 4) Output bar  (768)
    draw_bar(y_output_top, w_narrow, bar_h,
             "Second Linear Layer   (W\u2082h + b\u2082)\n\u2192 output (added to residual)",
             "768",
             COL_INPUT, COL_INPUT_FILL, label_fs=10.5)

    # --- Annotations ---
    # Left: "4x expansion" arrow
    arr_x = cx - w_wide / 2 - 0.4
    ax.annotate(
        "", xy=(arr_x, y_expand_top - bar_h / 2),
        xytext=(arr_x, y_input_top - bar_h / 2),
        arrowprops=dict(
            arrowstyle="<->", color=COL_EXPAND, lw=2.0,
        ), zorder=3,
    )
    ax.text(arr_x - 0.15,
            (y_input_top - bar_h / 2 + y_expand_top - bar_h / 2) / 2,
            "4\u00d7\nexpand",
            ha="right", va="center", fontsize=11, fontweight="bold",
            color=COL_EXPAND, zorder=3)

    # Right: "4x compress" arrow
    arr_x2 = cx + w_wide / 2 + 1.3
    ax.annotate(
        "", xy=(arr_x2, y_output_top - bar_h / 2),
        xytext=(arr_x2, y_gelu_bot - 0.0),
        arrowprops=dict(
            arrowstyle="<->", color=COL_INPUT, lw=2.0,
        ), zorder=3,
    )
    ax.text(arr_x2 + 0.15,
            (y_gelu_bot + y_output_top - bar_h / 2) / 2,
            "4\u00d7\ncompress",
            ha="left", va="center", fontsize=11, fontweight="bold",
            color=COL_INPUT, zorder=3)

    # Bottom note
    ax.text(cx, y_output_bot - 0.55,
            "Each of the 12 transformer blocks contains one FFN with this structure.\n"
            "Parameters per FFN:  768\u00d73072 + 3072 + 3072\u00d7768 + 768  \u2248  4.7M",
            ha="center", va="center", fontsize=9.5, color=COL_DIM,
            fontfamily="monospace", linespacing=1.6,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F0F0F0",
                      edgecolor="#CCCCCC", linewidth=0.8))

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Figure 2 -- Neuron activation heatmap from GPT-2
# ---------------------------------------------------------------------------

SENTENCES = [
    "The capital of France is Paris",
    "The capital of Germany is Berlin",
    "The cat sits on the mat",
    "The dog chased the cat",
    "Monte Carlo simulation estimates expectations",
    "The posterior distribution captures beliefs",
    "The value of pi is 3.14159",
    "To be or not to be",
]


def capture_ffn_activations(model, tokenizer, sentences, layer_idx=LAYER_INDEX):
    """
    Run each sentence through GPT-2 and capture the intermediate FFN
    activations (output of the first linear layer c_fc, after GELU) at
    the specified layer.

    For each sentence we take the mean activation across token positions
    to get a single 3072-dim vector per sentence.

    Returns:
        activations: np.ndarray of shape (n_sentences, 3072)
    """
    model.eval()
    activations = []

    for sentence in sentences:
        captured = {}

        def hook_fn(module, input, output):
            # c_fc output is (batch, seq_len, 3072)
            # Apply GELU to match the actual intermediate hidden state
            captured["act"] = torch.nn.functional.gelu(output).detach()

        # Register hook on the first linear layer of the MLP
        handle = model.transformer.h[layer_idx].mlp.c_fc.register_forward_hook(hook_fn)

        inputs = tokenizer(sentence, return_tensors="pt")
        with torch.no_grad():
            model(**inputs)

        handle.remove()

        # Mean-pool across token positions -> shape (3072,)
        act = captured["act"].squeeze(0).mean(dim=0).numpy()
        activations.append(act)

    return np.array(activations)


def make_activations_figure(model, tokenizer):
    """Heatmap: rows = sentences, columns = top-variance neurons."""
    set_style()

    print("  Capturing FFN intermediate activations (layer %d)..." % LAYER_INDEX)
    activations = capture_ffn_activations(model, tokenizer, SENTENCES,
                                          layer_idx=LAYER_INDEX)
    # activations shape: (8, 3072)

    # Select the 50 neurons with highest variance across sentences
    n_select = 50
    variances = np.var(activations, axis=0)
    top_indices = np.argsort(variances)[-n_select:][::-1]  # descending variance
    selected = activations[:, top_indices]  # shape (8, 50)

    # Truncate sentence labels for display
    labels = []
    for s in SENTENCES:
        if len(s) > 42:
            labels.append(s[:39] + "...")
        else:
            labels.append(s)

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(COL_BG)

    # Symmetric colour scale centred at zero
    vmax = np.percentile(np.abs(selected), 97)
    im = ax.imshow(selected, aspect="auto",
                   cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                   interpolation="nearest")

    # Axes
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=10, fontfamily="monospace")

    # Show every 5th neuron index on x-axis
    xtick_positions = list(range(0, n_select, 5))
    ax.set_xticks(xtick_positions)
    ax.set_xticklabels([str(top_indices[i]) for i in xtick_positions],
                       fontsize=8, fontfamily="monospace", rotation=45,
                       ha="right")
    ax.set_xlabel("Neuron index (50 highest-variance neurons out of 3072)",
                  fontsize=11)
    ax.set_ylabel("")

    # Colorbar
    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Activation (post-GELU, mean over positions)", fontsize=10)

    # Title
    ax.set_title(
        "FFN Intermediate Activations  \u2014  Layer %d,  "
        "50 highest-variance neurons" % LAYER_INDEX,
        fontsize=13, fontweight="bold", pad=12,
    )

    # Annotation box
    fig.text(
        0.5, -0.02,
        "Each row is one sentence passed through GPT-2.  "
        "Specific neurons activate for specific content patterns \u2014\n"
        "e.g., geography sentences share activation patterns distinct "
        "from animal or statistical sentences.",
        ha="center", va="top", fontsize=9.5, color=COL_DIM,
        fontfamily="sans-serif", linespacing=1.5,
    )

    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=== Figure 1: FFN shape schematic ===")
    fig1 = make_shape_figure()
    save_fig(fig1, "05_ffn_shape")

    print("\n=== Figure 2: FFN activation heatmap ===")
    print("Loading GPT-2 model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_pretrained("gpt2")

    fig2 = make_activations_figure(model, tokenizer)
    save_fig(fig2, "05_ffn_activations")

    print("\nDone.")
