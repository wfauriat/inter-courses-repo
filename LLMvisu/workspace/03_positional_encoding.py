"""
03 - Positional Encoding: Why Word Order Matters
=================================================

Without positional encoding, a transformer treats "dog bites man" and
"man bites dog" as identical -- it is a bag-of-words model.  GPT-2 adds
a *learned* positional embedding to every token so that the model knows
where each word sits in the sequence.

This script produces two figures:

1. A heatmap of GPT-2's learned positional embeddings, revealing the
   wave-like patterns the model discovered during training.

2. A side-by-side comparison of next-token predictions for two prompts
   that share the same words in different order, proving the model is
   sensitive to position.
"""

import sys
import os

import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from transformers import AutoTokenizer, AutoModelForCausalLM

# ── shared helpers ──────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE
from shared.data import EXAMPLES                       # noqa: F401 (available if needed)

set_style()

# ── load model once ─────────────────────────────────────────────────────
print("Loading GPT-2 ...")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")
model.eval()


# ========================================================================
# Figure 1 -- Positional-embedding heatmap
# ========================================================================

def plot_positional_heatmap(n_positions=128, n_dims=64):
    """Visualize the first *n_positions* x *n_dims* slice of GPT-2's
    learned positional embedding matrix (shape 1024 x 768).

    Two side-by-side panels:
      Left   -- row 0 included, with its extreme outlier (dim ~55 ~ +4)
                clipping the colour scale.
      Right  -- row 0 excluded, so positions 1..n-1 can use a tight colour
                scale and the learned structure across dimensions is visible.
    """

    wpe = model.transformer.wpe.weight.detach().cpu().numpy()  # (1024, 768)
    data = wpe[:n_positions, :n_dims]

    # Robust vmax that ignores position 0 (which contains an outlier value
    # -- the same artifact that later becomes the runtime "attention sink").
    data_no_p0 = data[1:]
    vmax_robust = float(np.abs(data_no_p0).max())
    vmax_raw = float(np.abs(data).max())

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(14, 7))

    im0 = ax0.imshow(
        data,
        aspect="auto",
        cmap="RdBu_r",
        interpolation="nearest",
        vmin=-vmax_raw,
        vmax=vmax_raw,
        origin="upper",
    )
    ax0.set_xlabel("Embedding dimension")
    ax0.set_ylabel("Token position in sequence")
    ax0.set_title(
        f"All positions 0..{n_positions - 1}\n"
        f"(colour scale \u00b1{vmax_raw:.1f}  -- set by position-0 outlier)",
        fontsize=12, fontweight="bold",
    )
    ax0.xaxis.set_major_locator(ticker.MultipleLocator(8))
    ax0.yaxis.set_major_locator(ticker.MultipleLocator(16))
    fig.colorbar(im0, ax=ax0, fraction=0.035, pad=0.04).set_label(
        "Embedding value", fontsize=10)

    im1 = ax1.imshow(
        data_no_p0,
        aspect="auto",
        cmap="RdBu_r",
        interpolation="nearest",
        vmin=-vmax_robust,
        vmax=vmax_robust,
        origin="upper",
        extent=(-0.5, n_dims - 0.5, n_positions - 0.5, 0.5),  # y starts at 1
    )
    ax1.set_xlabel("Embedding dimension")
    ax1.set_ylabel("Token position in sequence")
    ax1.set_title(
        f"Positions 1..{n_positions - 1}  (row 0 excluded)\n"
        f"(colour scale \u00b1{vmax_robust:.2f}  -- learned structure now visible)",
        fontsize=12, fontweight="bold",
    )
    ax1.xaxis.set_major_locator(ticker.MultipleLocator(8))
    ax1.yaxis.set_major_locator(ticker.MultipleLocator(16))
    fig.colorbar(im1, ax=ax1, fraction=0.035, pad=0.04).set_label(
        "Embedding value", fontsize=10)

    fig.suptitle("GPT-2 Learned Positional Embeddings",
                 fontsize=16, fontweight="bold", y=1.0)

    fig.text(
        0.5, 0.02,
        "Each row is the 768-d vector added to a token at that position.  "
        "Position 0 carries an outlier value (dim ~55) that dominates the naive "
        f"colour scale (left, \u00b1{vmax_raw:.1f}).\n"
        "Clipping it (right) reveals structured vertical bands: some dimensions "
        "encode a monotonic position signal, others a periodic one.",
        ha="center", va="bottom", fontsize=10, color="#555555", style="italic",
    )

    fig.tight_layout(rect=[0, 0.07, 1, 0.96])
    save_fig(fig, "03_positional_heatmap")


# ========================================================================
# Figure 2 -- Same words, different order -> different predictions
# ========================================================================

def get_top_predictions(prompt, k=5):
    """Return the top-k next-token (token_str, probability) pairs."""
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits          # (1, seq_len, vocab)
    probs = torch.softmax(logits[0, -1, :], dim=-1)
    top_probs, top_ids = probs.topk(k)
    tokens = [tokenizer.decode(tid).strip() for tid in top_ids]
    return tokens, top_probs.numpy()


def plot_prediction_comparison():
    """Side-by-side horizontal bar charts for two reordered prompts."""

    prompt_a = "The dog chased the cat and then the"
    prompt_b = "The cat chased the dog and then the"

    tokens_a, probs_a = get_top_predictions(prompt_a)
    tokens_b, probs_b = get_top_predictions(prompt_b)

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(13, 5), sharey=False)

    # ── left panel ──────────────────────────────────────────────────────
    y_pos = np.arange(len(tokens_a))
    bars_a = ax_a.barh(y_pos, probs_a, color=COLOR_PALETTE[0], edgecolor="white", height=0.6)
    ax_a.set_yticks(y_pos)
    ax_a.set_yticklabels([f'"{t}"' for t in tokens_a], fontsize=12)
    ax_a.invert_yaxis()
    ax_a.set_xlabel("Probability")
    ax_a.set_title("... dog chased the cat ...", fontsize=13, fontweight="bold",
                    color=COLOR_PALETTE[0])

    # Probability labels on bars
    for bar, p in zip(bars_a, probs_a):
        ax_a.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                  f"{p:.1%}", va="center", fontsize=11)

    # ── right panel ─────────────────────────────────────────────────────
    y_pos = np.arange(len(tokens_b))
    bars_b = ax_b.barh(y_pos, probs_b, color=COLOR_PALETTE[3], edgecolor="white", height=0.6)
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels([f'"{t}"' for t in tokens_b], fontsize=12)
    ax_b.invert_yaxis()
    ax_b.set_xlabel("Probability")
    ax_b.set_title("... cat chased the dog ...", fontsize=13, fontweight="bold",
                    color=COLOR_PALETTE[3])

    for bar, p in zip(bars_b, probs_b):
        ax_b.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
                  f"{p:.1%}", va="center", fontsize=11)

    # Harmonise x-axes so the two panels are visually comparable
    x_max = max(ax_a.get_xlim()[1], ax_b.get_xlim()[1]) * 1.18
    ax_a.set_xlim(0, x_max)
    ax_b.set_xlim(0, x_max)

    fig.suptitle(
        "Same Words, Different Order  -->  Different Predictions",
        fontsize=15, fontweight="bold", y=1.02,
    )

    fig.text(
        0.5, -0.04,
        "GPT-2 predicts different continuations because positional encodings\n"
        "let it distinguish word order -- it knows who chased whom.",
        ha="center", fontsize=10, color="#555555",
    )

    fig.tight_layout()
    save_fig(fig, "03_positional_effect")


# ========================================================================
# Main
# ========================================================================

if __name__ == "__main__":
    plot_positional_heatmap()
    plot_prediction_comparison()
    print("Done -- both figures saved to workspace/output/")
