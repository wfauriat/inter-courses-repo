"""
14_icl_vs_finetuning.py
=======================
Two fundamentally different ways to steer a language model:
  - **In-Context Learning (ICL):** change the *input* (prepend examples)
  - **Fine-tuning:** change the *weights* (gradient updates)

Produces three figures:
  1. 14_icl_fewshot.png           -- GPT-2 top-5 predictions with 0/1/3-shot prompts
  2. 14_icl_vs_ft_tradeoffs.png   -- Side-by-side tradeoff comparison table
  3. 14_icl_vs_ft_architecture.png -- Conceptual architecture diagram (frozen vs updated)

Usage:
    source ~/.venvDS/bin/activate
    python workspace/14_icl_vs_finetuning.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# ---------------------------------------------------------------------------
# Colour constants (consistent with the series)
# ---------------------------------------------------------------------------
COL_BLUE = COLOR_PALETTE[0]       # #4C72B0
COL_ORANGE = COLOR_PALETTE[1]     # #DD8452
COL_GREEN = COLOR_PALETTE[2]      # #55A868
COL_RED = COLOR_PALETTE[3]        # #C44E52
COL_PURPLE = COLOR_PALETTE[4]     # #8172B3
COL_GREY = COLOR_PALETTE[7]       # #8C8C8C
COL_TEXT = "#2B2B2B"
COL_DIM = "#6B6B6B"
COL_BG = "#FAFAFA"

# ICL highlight = orange (input is modified), FT highlight = green (weights updated)
COL_ICL = COL_ORANGE
COL_FT = COL_GREEN


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_model():
    """Load GPT-2 tokenizer and model (eval mode, no grad)."""
    print("Loading GPT-2 tokenizer and model...")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_pretrained("gpt2")
    model.eval()
    return tokenizer, model


# ---------------------------------------------------------------------------
# Inference helpers
# ---------------------------------------------------------------------------

def get_topk_next_tokens(prompt, tokenizer, model, k=5):
    """Return top-k next-token predictions as (token_strings, probabilities)."""
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model(input_ids)
    logits = outputs.logits[0, -1, :]
    probabilities = torch.softmax(logits, dim=-1)
    topk = torch.topk(probabilities, k)
    tokens = [tokenizer.decode([idx]) for idx in topk.indices.tolist()]
    probs = topk.values.numpy()
    return tokens, probs


def escape_token(tok):
    """Make a token string safe and readable for display."""
    tok = tok.replace("\n", "\\n")
    tok = tok.replace("\t", "\\t")
    tok = tok.replace("\r", "\\r")
    if tok.startswith(" "):
        tok = "\u2581" + tok[1:]   # underscore-like char for leading space
    return tok


# ---------------------------------------------------------------------------
# Figure 1 -- ICL few-shot bar charts
# ---------------------------------------------------------------------------

def make_icl_fewshot_figure(tokenizer, model):
    """Top-5 next-token predictions for zero/one/few-shot sentiment prompts.

    Two test texts x three shot-levels = 6 subplots (2 rows x 3 cols).
    """
    set_style()

    # -- Define prompts at each shot level -----------------------------------
    # Few-shot examples (diverse, unrelated to the test texts)
    examples = [
        ("I love this product, it works perfectly", "positive"),
        ("Terrible film, waste of time", "negative"),
        ("The food was delicious and the service outstanding", "positive"),
    ]

    test_texts = [
        ("Great movie!", "positive"),
        ("Absolutely terrible experience", "negative"),
    ]

    def build_prompt(n_examples, test_text):
        """Build a classification prompt with n in-context examples."""
        parts = []
        if n_examples == 0:
            parts.append(
                "Classify the sentiment as positive or negative."
            )
        for ex_text, ex_label in examples[:n_examples]:
            parts.append(f"Text: '{ex_text}'\nSentiment: {ex_label}")
        parts.append(f"Text: '{test_text}'\nSentiment:")
        return "\n".join(parts)

    shot_labels = ["Zero-shot (0 examples)", "One-shot (1 example)",
                   "Few-shot (3 examples)"]
    n_shots = [0, 1, 3]

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    fig.suptitle(
        "In-Context Learning: How Adding Examples Steers GPT-2's Predictions",
        fontsize=17, fontweight="bold", y=0.99,
    )
    fig.text(
        0.5, 0.945,
        "Top-5 next-token predictions after the prompt \"Sentiment:\". "
        "More examples push sentiment-related tokens higher.",
        ha="center", fontsize=12, color=COL_DIM,
    )

    k = 5

    for row_idx, (test_text, expected) in enumerate(test_texts):
        for col_idx, (n_ex, shot_lbl) in enumerate(zip(n_shots, shot_labels)):
            ax = axes[row_idx][col_idx]
            prompt = build_prompt(n_ex, test_text)
            tokens, probs = get_topk_next_tokens(prompt, tokenizer, model, k=k)

            display_tokens = [escape_token(t) for t in tokens]

            # Horizontal bars, highest at top
            y_pos = np.arange(k)
            display_r = display_tokens[::-1]
            probs_r = probs[::-1]

            # Highlight any token containing the expected sentiment word
            colors = []
            for t in display_r:
                t_lower = t.lower().replace("\u2581", "").strip()
                if expected in t_lower or t_lower in expected:
                    colors.append(COL_GREEN)
                else:
                    colors.append(COL_BLUE)
            # Always highlight top-1 differently
            colors[-1] = COL_ICL

            bars = ax.barh(y_pos, probs_r, color=colors, edgecolor="white",
                           linewidth=0.6, height=0.65)

            ax.set_yticks(y_pos)
            ax.set_yticklabels(display_r, fontfamily="monospace", fontsize=10)

            # Probability labels
            for bar, p in zip(bars, probs_r):
                w = bar.get_width()
                ax.text(w + 0.003, bar.get_y() + bar.get_height() / 2,
                        f"{p:.3f}", va="center", ha="left",
                        fontsize=9, fontfamily="monospace", color="#333333")

            ax.set_xlabel("Probability", fontsize=10)
            ax.set_xlim(0, max(probs[0] * 1.45, 0.15))
            ax.grid(axis="x", alpha=0.3)
            ax.grid(axis="y", visible=False)

            # Title: shot label on first row, test text on left column
            if row_idx == 0:
                ax.set_title(shot_lbl, fontsize=13, fontweight="bold",
                             color=COL_ICL, pad=8)
            if col_idx == 0:
                ax.set_ylabel(
                    f'"{test_text}"\n(expected: {expected})',
                    fontsize=11, fontweight="bold", color=COL_TEXT,
                    labelpad=10,
                )
            else:
                ax.set_ylabel("")

    # Legend
    legend_handles = [
        mpatches.Patch(color=COL_ICL, label="Top-1 prediction"),
        mpatches.Patch(color=COL_GREEN, label="Contains expected sentiment"),
        mpatches.Patch(color=COL_BLUE, label="Other tokens"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=3,
               fontsize=11, frameon=True, framealpha=0.9,
               bbox_to_anchor=(0.5, -0.01))

    fig.tight_layout(rect=[0, 0.03, 1, 0.92])
    save_fig(fig, "14_icl_fewshot")


# ---------------------------------------------------------------------------
# Figure 2 -- Tradeoff comparison table / infographic
# ---------------------------------------------------------------------------

def make_tradeoff_figure():
    """Styled two-column comparison: ICL vs Fine-Tuning."""
    set_style()

    rows = [
        ("What changes",   "Input (tokens prepended)",
                           "Weights (parameters updated)"),
        ("Data needed",    "0\u201320 examples in prompt",
                           "100s\u20131000s of labeled examples"),
        ("Compute cost",   "None (inference only)",
                           "GPU hours for training"),
        ("Persistence",    "Temporary (per-request)",
                           "Permanent (new model)"),
        ("Flexibility",    "Change task by changing prompt",
                           "Retrain for each new task"),
        ("Reliability",    "Variable, prompt-sensitive",
                           "More consistent"),
    ]

    n_rows = len(rows)

    fig, ax = plt.subplots(figsize=(16, 8))
    ax.axis("off")
    fig.patch.set_facecolor("white")

    # Layout parameters
    left_margin = 0.08
    col_axis_w = 0.18     # axis column width (fraction of fig)
    col_icl_w = 0.35      # ICL column width
    col_ft_w = 0.35       # FT column width
    top_y = 0.88
    header_h = 0.08
    row_h = 0.105

    # Coordinates in figure fraction
    col_axis_x = left_margin
    col_icl_x = col_axis_x + col_axis_w + 0.01
    col_ft_x = col_icl_x + col_icl_w + 0.01

    # ---- Title ----
    fig.text(0.5, 0.96,
             "In-Context Learning  vs  Fine-Tuning",
             ha="center", va="center", fontsize=20, fontweight="bold",
             color=COL_TEXT)
    fig.text(0.5, 0.915,
             "Two ways to adapt a pretrained model to a new task",
             ha="center", va="center", fontsize=13, color=COL_DIM)

    # ---- Column headers ----
    header_y = top_y

    # Axis header (blank, or "Axis")
    fig.patches.append(FancyBboxPatch(
        (col_axis_x, header_y - header_h), col_axis_w, header_h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        facecolor="#E8E8E8", edgecolor="#CCCCCC", linewidth=1.0,
        transform=fig.transFigure, zorder=2,
    ))
    fig.text(col_axis_x + col_axis_w / 2, header_y - header_h / 2,
             "Axis", ha="center", va="center",
             fontsize=13, fontweight="bold", color=COL_DIM,
             transform=fig.transFigure)

    # ICL header
    fig.patches.append(FancyBboxPatch(
        (col_icl_x, header_y - header_h), col_icl_w, header_h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        facecolor=COL_ICL, edgecolor=COL_ICL, linewidth=1.0,
        alpha=0.85, transform=fig.transFigure, zorder=2,
    ))
    fig.text(col_icl_x + col_icl_w / 2, header_y - header_h / 2,
             "In-Context Learning", ha="center", va="center",
             fontsize=14, fontweight="bold", color="white",
             transform=fig.transFigure)

    # FT header
    fig.patches.append(FancyBboxPatch(
        (col_ft_x, header_y - header_h), col_ft_w, header_h,
        boxstyle="round,pad=0.01,rounding_size=0.01",
        facecolor=COL_FT, edgecolor=COL_FT, linewidth=1.0,
        alpha=0.85, transform=fig.transFigure, zorder=2,
    ))
    fig.text(col_ft_x + col_ft_w / 2, header_y - header_h / 2,
             "Fine-Tuning", ha="center", va="center",
             fontsize=14, fontweight="bold", color="white",
             transform=fig.transFigure)

    # ---- Data rows ----
    icl_light = "#FFF0E5"   # light orange
    ft_light = "#E8F5E9"    # light green
    axis_light = "#F5F5F5"
    row_edge = "#DDDDDD"

    for i, (axis_label, icl_text, ft_text) in enumerate(rows):
        ry = header_y - header_h - 0.008 - i * (row_h + 0.006)

        # Axis cell
        fig.patches.append(FancyBboxPatch(
            (col_axis_x, ry - row_h), col_axis_w, row_h,
            boxstyle="round,pad=0.01,rounding_size=0.008",
            facecolor=axis_light, edgecolor=row_edge, linewidth=0.8,
            transform=fig.transFigure, zorder=2,
        ))
        fig.text(col_axis_x + col_axis_w / 2, ry - row_h / 2,
                 axis_label, ha="center", va="center",
                 fontsize=12, fontweight="bold", color=COL_TEXT,
                 transform=fig.transFigure)

        # ICL cell
        fig.patches.append(FancyBboxPatch(
            (col_icl_x, ry - row_h), col_icl_w, row_h,
            boxstyle="round,pad=0.01,rounding_size=0.008",
            facecolor=icl_light, edgecolor=row_edge, linewidth=0.8,
            transform=fig.transFigure, zorder=2,
        ))
        fig.text(col_icl_x + col_icl_w / 2, ry - row_h / 2,
                 icl_text, ha="center", va="center",
                 fontsize=11.5, color=COL_TEXT,
                 transform=fig.transFigure)

        # FT cell
        fig.patches.append(FancyBboxPatch(
            (col_ft_x, ry - row_h), col_ft_w, row_h,
            boxstyle="round,pad=0.01,rounding_size=0.008",
            facecolor=ft_light, edgecolor=row_edge, linewidth=0.8,
            transform=fig.transFigure, zorder=2,
        ))
        fig.text(col_ft_x + col_ft_w / 2, ry - row_h / 2,
                 ft_text, ha="center", va="center",
                 fontsize=11.5, color=COL_TEXT,
                 transform=fig.transFigure)

    # ---- Bottom summary ----
    bottom_y = header_y - header_h - 0.008 - n_rows * (row_h + 0.006) - 0.04
    fig.text(
        0.5, bottom_y,
        "ICL is fast and flexible (change the prompt, not the model). "
        "Fine-tuning is more reliable and permanent (update the weights once, use everywhere).",
        ha="center", va="center", fontsize=11.5, color=COL_DIM,
        style="italic", transform=fig.transFigure,
    )

    save_fig(fig, "14_icl_vs_ft_tradeoffs")


# ---------------------------------------------------------------------------
# Figure 3 -- Architecture conceptual diagram (ICL vs Fine-Tuning)
# ---------------------------------------------------------------------------

def make_architecture_figure():
    """Side-by-side architecture spines: ICL (frozen weights, modified input)
    vs Fine-Tuning (updated weights, normal input)."""
    set_style()

    fig, (ax_icl, ax_ft) = plt.subplots(1, 2, figsize=(16, 12))
    for ax in (ax_icl, ax_ft):
        ax.set_xlim(-1.5, 3.5)
        ax.set_ylim(-0.5, 12.5)
        ax.axis("off")

    fig.patch.set_facecolor(COL_BG)

    fig.suptitle(
        "Where the Change Happens: ICL vs Fine-Tuning",
        fontsize=18, fontweight="bold", y=0.97, color=COL_TEXT,
    )
    fig.text(
        0.5, 0.935,
        "Same architecture, different adaptation strategy",
        ha="center", fontsize=13, color=COL_DIM,
    )

    # -- Architecture stages (shared labels) --
    stages = [
        "Input Tokens",
        "Token + Positional\nEmbedding",
        "Transformer Block 1",
        "Transformer Block 2",
        "   ...  (x12 total)",
        "Final LayerNorm",
        "Linear Projection",
        "Softmax",
        "Next Token",
    ]

    # Layout
    CX = 1.0
    BOX_W = 2.8
    BOX_H = 0.72
    GAP = 0.30
    y_start = 11.5

    def _color_for_stage(stage_idx, mode):
        """Return (edge_color, fill_color, text_alpha) for a stage box."""
        is_input = stage_idx == 0
        is_output = stage_idx == len(stages) - 1

        if mode == "icl":
            if is_input:
                # Input is highlighted (modified)
                return COL_ICL, "#FFF0E5", 1.0
            else:
                # Model weights frozen -- grayed out
                return "#BBBBBB", "#F0F0F0", 0.55
        else:  # fine-tuning
            if is_input:
                # Normal input
                return "#BBBBBB", "#F0F0F0", 0.55
            elif is_output:
                return "#BBBBBB", "#F0F0F0", 0.55
            else:
                # Weights being updated -- highlighted
                return COL_FT, "#E8F5E9", 1.0

    def draw_spine(ax, mode):
        """Draw one architecture spine. mode = 'icl' or 'ft'."""
        y = y_start
        for i, label in enumerate(stages):
            edge, fill, alpha = _color_for_stage(i, mode)

            # Thicker edge for highlighted boxes
            lw = 2.2 if alpha > 0.8 else 1.2

            box = FancyBboxPatch(
                (CX - BOX_W / 2, y - BOX_H / 2), BOX_W, BOX_H,
                boxstyle="round,pad=0,rounding_size=0.04",
                linewidth=lw, edgecolor=edge, facecolor=fill,
                zorder=2, alpha=max(alpha, 0.4),
            )
            ax.add_patch(box)

            text_color = COL_TEXT if alpha > 0.8 else "#999999"
            fontw = "bold" if alpha > 0.8 else "normal"
            ax.text(CX, y, label, ha="center", va="center",
                    fontsize=11, fontweight=fontw, color=text_color,
                    zorder=3, alpha=max(alpha, 0.5))

            # Draw arrow to next box
            if i < len(stages) - 1:
                arrow_col = edge if alpha > 0.8 else "#CCCCCC"
                arrow_top = y - BOX_H / 2
                arrow_bot = y - BOX_H / 2 - GAP
                ax.annotate(
                    "", xy=(CX, arrow_bot),
                    xytext=(CX, arrow_top),
                    arrowprops=dict(
                        arrowstyle="->,head_width=0.15,head_length=0.06",
                        color=arrow_col, lw=1.3,
                    ),
                    zorder=1,
                )

            y -= BOX_H + GAP

        return y  # bottom y

    # -- Draw both spines --
    draw_spine(ax_icl, "icl")
    draw_spine(ax_ft, "ft")

    # -- Subtitles and labels --
    ax_icl.set_title("In-Context Learning / Prompting",
                     fontsize=14, fontweight="bold", color=COL_ICL, pad=15)
    ax_ft.set_title("Fine-Tuning",
                    fontsize=14, fontweight="bold", color=COL_FT, pad=15)

    # Bottom labels
    label_y = y_start - (len(stages)) * (BOX_H + GAP) + 0.1

    ax_icl.text(CX, label_y,
                "Weights frozen\nInput modified",
                ha="center", va="center", fontsize=13, fontweight="bold",
                color=COL_ICL,
                bbox=dict(boxstyle="round,pad=0.4", facecolor="#FFF0E5",
                          edgecolor=COL_ICL, linewidth=1.5))

    ax_ft.text(CX, label_y,
               "Weights updated\nArchitecture unchanged",
               ha="center", va="center", fontsize=13, fontweight="bold",
               color=COL_FT,
               bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8F5E9",
                         edgecolor=COL_FT, linewidth=1.5))

    # -- Annotations / decorations --
    # ICL side: small annotation arrow pointing to the Input box
    ax_icl.annotate(
        "Prepend examples\nhere (the only change)",
        xy=(CX + BOX_W / 2, y_start),
        xytext=(CX + BOX_W / 2 + 0.9, y_start + 0.6),
        fontsize=10, fontweight="bold", color=COL_ICL,
        ha="left", va="center",
        arrowprops=dict(arrowstyle="->", color=COL_ICL, lw=1.5),
        zorder=5,
    )

    # FT side: bracket / annotation over the model boxes
    mid_model_y = y_start - 3 * (BOX_H + GAP)  # roughly middle of model blocks
    ax_ft.annotate(
        "Gradients update\nall these layers",
        xy=(CX + BOX_W / 2, mid_model_y),
        xytext=(CX + BOX_W / 2 + 0.9, mid_model_y + 0.6),
        fontsize=10, fontweight="bold", color=COL_FT,
        ha="left", va="center",
        arrowprops=dict(arrowstyle="->", color=COL_FT, lw=1.5),
        zorder=5,
    )

    # -- Freeze / fire icons as simple text symbols --
    # Snowflake for frozen, flame for updating
    for i in range(1, len(stages) - 1):
        y_pos = y_start - i * (BOX_H + GAP)
        # ICL: snowflake (frozen)
        ax_icl.text(CX - BOX_W / 2 - 0.25, y_pos, "\u2744",
                    ha="center", va="center", fontsize=14,
                    color="#AADDEE", zorder=3, alpha=0.7)
        # FT: up-arrow (updating)
        ax_ft.text(CX - BOX_W / 2 - 0.25, y_pos, "\u2191",
                   ha="center", va="center", fontsize=14,
                   fontweight="bold", color=COL_FT, zorder=3, alpha=0.7)

    fig.tight_layout(rect=[0, 0.02, 1, 0.92])
    save_fig(fig, "14_icl_vs_ft_architecture")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tokenizer, model = load_model()

    print("\n--- Figure 1: ICL few-shot bar charts ---")
    make_icl_fewshot_figure(tokenizer, model)

    print("\n--- Figure 2: ICL vs Fine-Tuning tradeoff table ---")
    make_tradeoff_figure()

    print("\n--- Figure 3: Architecture comparison diagram ---")
    make_architecture_figure()

    print("\nDone -- all three figures saved to workspace/output/")
