"""
09 - Softmax Temperature: Tuning Model Confidence
==================================================

Softmax converts raw model scores (logits) into a probability distribution
over the vocabulary.  Before applying softmax we can divide the logits by
a scalar *temperature* T:

    probs = softmax(logits / T)

* T < 1  sharpens the distribution  -->  model is "more confident"
* T = 1  standard softmax (no change)
* T > 1  flattens the distribution   -->  model is "less confident"

This is the simplest knob on a language model's output uncertainty and
maps directly to concepts familiar in UQ: a peaked distribution has low
entropy (like a tight posterior), while a flat distribution has high
entropy (like a diffuse prior).

This script produces three figures:

1. A 2x2 grid of bar charts showing how the top-15 token probabilities
   reshape as temperature changes from 0.1 to 2.0.

2. An overlay line plot of the top-10 probabilities at each temperature,
   making the sharpening/flattening effect visible in one glance.

3. A side-by-side text display of model completions at low (T=0.3) and
   high (T=1.5) temperature, showing how temperature affects generation
   diversity.
"""

import sys
import os

import torch
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from transformers import AutoTokenizer, AutoModelForCausalLM

# -- shared helpers --------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE

set_style()

# -- load model once -------------------------------------------------------
print("Loading GPT-2 ...")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")
model.eval()

# Needed for generation -- GPT-2 tokenizer has no default pad token
tokenizer.pad_token = tokenizer.eos_token


# =========================================================================
# Helper: get logits for the next token given a prompt
# =========================================================================

def next_token_logits(prompt: str) -> torch.Tensor:
    """Return the raw logit vector for the next-token position."""
    inputs = tokenizer(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits  # (1, seq_len, vocab_size)
    return logits[0, -1, :]  # (vocab_size,)


def softmax_with_temperature(logits: torch.Tensor, temperature: float) -> torch.Tensor:
    """Apply temperature-scaled softmax."""
    return torch.softmax(logits / temperature, dim=-1)


# =========================================================================
# Shared data: compute logits once, reuse across figures 1 & 2
# =========================================================================

PROMPT = "The capital of France is"
TEMPERATURES = [0.1, 0.5, 1.0, 2.0]
TOP_K_BARS = 15   # for the 2x2 bar chart
TOP_K_LINES = 10  # for the overlay plot

print(f"Running forward pass on: \"{PROMPT}\"")
logits = next_token_logits(PROMPT)

# Determine the union top-K tokens at T=1 (the natural ranking).
# We use the same token set across all temperatures so bar positions match.
probs_t1 = softmax_with_temperature(logits, 1.0)
top_values, top_indices = probs_t1.topk(TOP_K_BARS)
top_token_ids = top_indices.tolist()
top_token_labels = [tokenizer.decode(tid).strip() for tid in top_token_ids]

# Pre-compute probabilities for each temperature at these token positions
temp_probs = {}
for t in TEMPERATURES:
    probs = softmax_with_temperature(logits, t)
    temp_probs[t] = probs[top_indices].numpy()


# =========================================================================
# Figure 1 -- 2x2 bar charts: temperature comparison
# =========================================================================

def plot_temperature_bars():
    """One subplot per temperature, same tokens, vertical bar chart."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.ravel()

    bar_colors = [COLOR_PALETTE[0], COLOR_PALETTE[1],
                  COLOR_PALETTE[2], COLOR_PALETTE[3]]

    for idx, t in enumerate(TEMPERATURES):
        ax = axes[idx]
        probs = temp_probs[t]
        x = np.arange(TOP_K_BARS)

        ax.bar(x, probs, color=bar_colors[idx], edgecolor="white",
               width=0.7, alpha=0.9)
        ax.set_xticks(x)
        ax.set_xticklabels(top_token_labels, rotation=55, ha="right",
                           fontsize=8)
        ax.set_ylabel("Probability")
        ax.set_title(f"Temperature = {t}", fontsize=14, fontweight="bold",
                     color=bar_colors[idx])

        # y-axis: consistent across subplots so the visual comparison works
        ax.set_ylim(0, 1.05)

        # Annotate the top bar with its value
        peak_idx = int(np.argmax(probs))
        ax.annotate(
            f"{probs[peak_idx]:.2%}",
            xy=(peak_idx, probs[peak_idx]),
            xytext=(0, 6), textcoords="offset points",
            ha="center", fontsize=9, fontweight="bold",
            color=bar_colors[idx],
        )

    fig.suptitle(
        f"Softmax Temperature Effect on Next-Token Probabilities\n"
        f"Prompt: \"{PROMPT}\"",
        fontsize=16, fontweight="bold", y=1.02,
    )

    fig.text(
        0.5, -0.02,
        "Low temperature concentrates probability on the top token (high confidence).\n"
        "High temperature spreads probability across many tokens (high uncertainty).",
        ha="center", fontsize=10, color="#555555",
    )

    fig.tight_layout()
    save_fig(fig, "09_temperature_bars")


# =========================================================================
# Figure 2 -- Overlay line plot
# =========================================================================

def plot_temperature_overlay():
    """Single plot with one colored line per temperature."""
    fig, ax = plt.subplots(figsize=(10, 6))

    line_styles = ["-o", "-s", "-^", "-D"]
    line_colors = [COLOR_PALETTE[0], COLOR_PALETTE[1],
                   COLOR_PALETTE[2], COLOR_PALETTE[3]]

    x = np.arange(TOP_K_LINES)

    for idx, t in enumerate(TEMPERATURES):
        probs = temp_probs[t][:TOP_K_LINES]
        ax.plot(x, probs, line_styles[idx], color=line_colors[idx],
                label=f"T = {t}", linewidth=2, markersize=7, alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(top_token_labels[:TOP_K_LINES], rotation=40,
                       ha="right", fontsize=10)
    ax.set_ylabel("Probability", fontsize=12)
    ax.set_xlabel("Token (ranked by T=1.0 probability)", fontsize=12)
    ax.set_title(
        f"Temperature Reshapes the Probability Distribution\n"
        f"Prompt: \"{PROMPT}\"",
        fontsize=15, fontweight="bold",
    )
    ax.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
    ax.set_ylim(bottom=0)

    fig.text(
        0.5, -0.03,
        "Lower T sharpens the peak (deterministic); higher T flattens it (uniform).\n"
        "Temperature is a direct control on output entropy -- a knob on model uncertainty.",
        ha="center", fontsize=10, color="#555555",
    )

    fig.tight_layout()
    save_fig(fig, "09_temperature_overlay")


# =========================================================================
# Figure 3 -- Generation diversity at low vs high temperature
# =========================================================================

GENERATION_PROMPT = "The meaning of life is"
N_SAMPLES = 8
MAX_NEW_TOKENS = 30
T_LOW = 0.3
T_HIGH = 1.5


def generate_completions(prompt: str, temperature: float, n: int) -> list[str]:
    """Generate n completions of the prompt at the given temperature."""
    inputs = tokenizer(prompt, return_tensors="pt")
    input_len = inputs["input_ids"].shape[1]

    completions = []
    for _ in range(n):
        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=temperature,
                do_sample=True,
                top_k=50,
                pad_token_id=tokenizer.eos_token_id,
            )
        # Decode only the generated portion (not the prompt)
        generated_ids = output[0, input_len:]
        text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        completions.append(text.strip())
    return completions


def plot_generation_diversity():
    """Side-by-side text panels: low-T (repetitive) vs high-T (diverse)."""

    print(f"Generating {N_SAMPLES} completions at T={T_LOW} ...")
    comps_low = generate_completions(GENERATION_PROMPT, T_LOW, N_SAMPLES)
    print(f"Generating {N_SAMPLES} completions at T={T_HIGH} ...")
    comps_high = generate_completions(GENERATION_PROMPT, T_HIGH, N_SAMPLES)

    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(1, 2, wspace=0.08)

    # Shared formatting
    prompt_display = f"\"{GENERATION_PROMPT} ...\""

    for col, (temp, comps, color) in enumerate([
        (T_LOW, comps_low, COLOR_PALETTE[0]),
        (T_HIGH, comps_high, COLOR_PALETTE[3]),
    ]):
        ax = fig.add_subplot(gs[col])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")

        # Column header
        ax.text(0.5, 0.97, f"Temperature = {temp}",
                fontsize=15, fontweight="bold", color=color,
                ha="center", va="top",
                transform=ax.transAxes)

        label = "Low T  --  repetitive / confident" if temp < 1 else \
                "High T  --  diverse / creative"
        ax.text(0.5, 0.92, label,
                fontsize=10, color="#666666", ha="center", va="top",
                transform=ax.transAxes)

        # Draw each completion as a numbered text block
        y_start = 0.86
        line_spacing = 0.095

        for i, comp in enumerate(comps):
            # Truncate long completions for display
            display_text = comp if len(comp) <= 90 else comp[:87] + "..."
            y = y_start - i * line_spacing
            ax.text(0.04, y, f"{i+1}.", fontsize=10, fontweight="bold",
                    color=color, va="top", transform=ax.transAxes)
            ax.text(0.08, y, display_text, fontsize=9, color="#333333",
                    va="top", transform=ax.transAxes, wrap=True,
                    fontfamily="monospace")

        # Light border around the column
        rect = plt.Rectangle((0.01, 0.03), 0.98, 0.95,
                              transform=ax.transAxes,
                              linewidth=1.5, edgecolor=color,
                              facecolor="none", alpha=0.4,
                              clip_on=False)
        ax.add_patch(rect)

    fig.suptitle(
        f"Generation Diversity vs Temperature\n"
        f"Prompt: {prompt_display}   |   {N_SAMPLES} samples, "
        f"max {MAX_NEW_TOKENS} tokens each",
        fontsize=15, fontweight="bold", y=1.01,
    )

    fig.text(
        0.5, -0.01,
        "Low temperature produces near-identical outputs (low entropy sampling).\n"
        "High temperature yields varied, sometimes surprising text (high entropy sampling).",
        ha="center", fontsize=10, color="#555555",
    )

    fig.tight_layout()
    save_fig(fig, "09_temperature_generations")


# =========================================================================
# Main
# =========================================================================

if __name__ == "__main__":
    plot_temperature_bars()
    plot_temperature_overlay()
    plot_generation_diversity()
    print("Done -- all three figures saved to workspace/output/")
