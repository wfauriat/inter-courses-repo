"""
01_tokenization.py
==================
Educational visualization: how text is split into subword tokens,
and how different tokenizers produce different splits.

Produces two figures:
  - 01_tokenization_splits.png      Colored token boxes for five example sentences
  - 01_tokenization_comparison.png  GPT-2 vs cl100k_base on the same sentence

Usage:
    source ~/.venvDS/bin/activate
    python workspace/01_tokenization.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE
from shared.data import EXAMPLES

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from transformers import AutoTokenizer

# Optional: tiktoken for cl100k_base comparison
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False
    print("tiktoken not installed -- cl100k_base comparison will be skipped.")


# ---------------------------------------------------------------------------
# Tokenizer helpers
# ---------------------------------------------------------------------------

def tokenize_gpt2(text, tokenizer):
    """Return list of (token_string, token_id) for GPT-2 BPE."""
    ids = tokenizer.encode(text)
    tokens = []
    for tid in ids:
        token_str = tokenizer.decode([tid])
        tokens.append((token_str, tid))
    return tokens


def tokenize_cl100k(text):
    """Return list of (token_string, token_id) for cl100k_base via tiktoken."""
    enc = tiktoken.get_encoding("cl100k_base")
    ids = enc.encode(text)
    tokens = []
    for tid in ids:
        token_str = enc.decode([tid])
        tokens.append((token_str, tid))
    return tokens


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------

def draw_token_boxes(ax, tokens, y_center, box_height=0.7,
                     text_fontsize=13, id_fontsize=9, gap=0.15,
                     palette=None):
    """
    Draw a row of colored boxes, each containing token text (inside)
    and token ID (below).

    Returns the total width consumed so figures can be sized appropriately.
    """
    if palette is None:
        palette = COLOR_PALETTE

    x = 0.0
    for i, (tok_str, tok_id) in enumerate(tokens):
        color = palette[i % len(palette)]

        # Box width proportional to character count, with a minimum
        display = tok_str.replace("\n", "\\n")
        char_width = max(len(display), 1) * 0.22 + 0.35
        box_w = max(char_width, 0.6)

        rect = mpatches.FancyBboxPatch(
            (x, y_center - box_height / 2),
            box_w, box_height,
            boxstyle="round,pad=0.05",
            facecolor=color, edgecolor="white", linewidth=1.5,
            alpha=0.85,
        )
        ax.add_patch(rect)

        # Token text (white, centered in box)
        ax.text(
            x + box_w / 2, y_center,
            display,
            ha="center", va="center",
            fontsize=text_fontsize, fontweight="bold",
            color="white", family="monospace",
        )

        # Token ID (below box)
        ax.text(
            x + box_w / 2, y_center - box_height / 2 - 0.18,
            str(tok_id),
            ha="center", va="top",
            fontsize=id_fontsize, color="#555555", family="monospace",
        )

        x += box_w + gap

    return x  # total width


# ---------------------------------------------------------------------------
# Figure 1 -- Tokenization splits for five example sentences
# ---------------------------------------------------------------------------

def make_splits_figure(tokenizer):
    set_style()

    sentences = [
        ("Simple English",          EXAMPLES["simple"]),
        ("Scientific domain",       "Uncertainty quantification in computational mechanics"),
        ("French with contractions", EXAMPLES["fr_incertitude"]),
        ("Numerical value",         "3.14159265"),
        ("Python code",             EXAMPLES["code"]),
    ]

    # Tokenize everything to figure out layout
    all_tokens = []
    for label, text in sentences:
        toks = tokenize_gpt2(text, tokenizer)
        all_tokens.append((label, text, toks))

    n_rows = len(sentences)
    row_height = 1.8  # vertical space per sentence

    # Estimate figure width from the widest row
    max_width = 0
    for _, _, toks in all_tokens:
        w = sum(max(len(t.replace("\n", "\\n")) * 0.22 + 0.35, 0.6) + 0.15 for t, _ in toks)
        max_width = max(max_width, w)

    fig_w = max(max_width + 4.5, 16)
    fig_h = n_rows * row_height + 1.6

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(-4.5, max_width + 1)
    ax.set_ylim(-0.5, n_rows * row_height + 0.6)
    ax.axis("off")

    fig.suptitle(
        "Tokenization: how text is split into subword units (GPT-2 BPE)",
        fontsize=16, fontweight="bold", y=0.97,
    )

    for row_idx, (label, raw_text, toks) in enumerate(all_tokens):
        y = (n_rows - 1 - row_idx) * row_height + row_height / 2

        # Row label on the left
        ax.text(
            -4.3, y, label,
            ha="left", va="center",
            fontsize=11, fontstyle="italic", color="#333333",
        )

        # Token count on the far left
        ax.text(
            -0.3, y, f"({len(toks)} tok)",
            ha="right", va="center",
            fontsize=10, color="#888888",
        )

        # Draw boxes
        draw_token_boxes(ax, toks, y, box_height=0.7,
                         text_fontsize=12, id_fontsize=8)

    save_fig(fig, "01_tokenization_splits")


# ---------------------------------------------------------------------------
# Figure 2 -- Tokenizer comparison on the same sentence
# ---------------------------------------------------------------------------

def make_comparison_figure(tokenizer):
    set_style()

    sentence = "Uncertainty quantification in computational mechanics"

    gpt2_toks = tokenize_gpt2(sentence, tokenizer)
    rows = [("GPT-2 BPE (r50k_base)", gpt2_toks)]

    if HAS_TIKTOKEN:
        cl100k_toks = tokenize_cl100k(sentence)
        rows.append(("cl100k_base (GPT-3.5 / GPT-4)", cl100k_toks))

    n_rows = len(rows)
    row_height = 2.2

    # Width estimate
    max_width = 0
    for _, toks in rows:
        w = sum(max(len(t.replace("\n", "\\n")) * 0.22 + 0.35, 0.6) + 0.15 for t, _ in toks)
        max_width = max(max_width, w)

    fig_w = max(max_width + 5, 16)
    fig_h = n_rows * row_height + 2.8

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(-5, max_width + 1.5)
    ax.set_ylim(-1.0, n_rows * row_height + 1.2)
    ax.axis("off")

    fig.suptitle(
        "Tokenizer comparison on the same input",
        fontsize=16, fontweight="bold", y=0.96,
    )
    ax.text(
        (max_width - 5) / 2, n_rows * row_height + 0.6,
        f'"{sentence}"',
        ha="center", va="center",
        fontsize=13, fontstyle="italic", color="#444444",
    )

    for row_idx, (label, toks) in enumerate(rows):
        y = (n_rows - 1 - row_idx) * row_height + row_height / 2

        # Tokenizer name
        ax.text(
            -4.8, y + 0.15, label,
            ha="left", va="center",
            fontsize=12, fontweight="bold", color="#333333",
        )
        ax.text(
            -4.8, y - 0.25,
            f"{len(toks)} tokens",
            ha="left", va="center",
            fontsize=11, color=COLOR_PALETTE[0] if row_idx == 0 else COLOR_PALETTE[1],
            fontweight="bold",
        )

        # Use different palette slice per tokenizer so they are visually distinct
        pal = COLOR_PALETTE if row_idx == 0 else COLOR_PALETTE[1:] + COLOR_PALETTE[:1]
        draw_token_boxes(ax, toks, y, box_height=0.75,
                         text_fontsize=12, id_fontsize=8, palette=pal)

    # Summary note at the bottom
    if n_rows == 2:
        diff = len(rows[0][1]) - len(rows[1][1])
        if diff > 0:
            note = f"cl100k_base uses {abs(diff)} fewer token(s) than GPT-2 for this input"
        elif diff < 0:
            note = f"GPT-2 uses {abs(diff)} fewer token(s) than cl100k_base for this input"
        else:
            note = "Both tokenizers use the same number of tokens for this input"
    else:
        note = "Install tiktoken to compare with cl100k_base (GPT-3.5/GPT-4 tokenizer)"

    ax.text(
        (max_width - 5) / 2, -0.6,
        note,
        ha="center", va="center",
        fontsize=11, color="#666666",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="#f0f0f0", edgecolor="#cccccc"),
    )

    save_fig(fig, "01_tokenization_comparison")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Loading GPT-2 tokenizer...")
    gpt2_tokenizer = AutoTokenizer.from_pretrained("gpt2")

    print("\n--- Figure 1: Tokenization splits ---")
    make_splits_figure(gpt2_tokenizer)

    print("\n--- Figure 2: Tokenizer comparison ---")
    make_comparison_figure(gpt2_tokenizer)

    print("\nDone.")
