"""
12_supervised_finetuning.py
===========================
Educational visualization: pre-trained base models do pattern completion;
supervised fine-tuning (SFT) on instruction/response pairs teaches them to
follow instructions.  Same architecture, different training data format,
different behavior.

Produces three figures:
  - 12_sft_comparison.png         Base-model vs instruction-tuned side-by-side
  - 12_sft_training_format.png    SFT training-data format (instruction/response cards)
  - 12_sft_probability_shift.png  Top-10 next-token probabilities for a QA prompt

Usage:
    source ~/.venvDS/bin/activate
    python workspace/12_supervised_finetuning.py
"""

import sys
import os
import textwrap

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE
from shared.data import PROMPTS

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


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

def generate_text(prompt, tokenizer, model, max_new_tokens=50):
    """Generate text continuation from a prompt using GPT-2."""
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.8,
            top_k=50,
            pad_token_id=tokenizer.eos_token_id,
        )
    # Decode only the new tokens
    generated = tokenizer.decode(output_ids[0][input_ids.shape[1]:],
                                 skip_special_tokens=True)
    return generated


def get_topk_next_tokens(prompt, tokenizer, model, k=10):
    """
    Run the model on `prompt` and return the top-k next-token predictions.

    Returns:
        tokens  -- list of decoded token strings (length k)
        probs   -- numpy array of probabilities (length k)
    """
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
        tok = "\u2581" + tok[1:]
    return tok


def wrap_text(text, width=52):
    """Wrap text to a fixed width for display in figures."""
    return "\n".join(textwrap.wrap(text, width=width))


# ---------------------------------------------------------------------------
# Figure 1 -- Base model vs instruction-tuned comparison
# ---------------------------------------------------------------------------

def make_comparison_figure(tokenizer, model):
    set_style()

    prompts = [
        "What is the capital of France?",
        "Explain what a Fourier transform does.",
        "Translate 'hello' to French.",
    ]

    # Expected instruction-tuned responses (hardcoded)
    sft_responses = [
        "The capital of France is Paris. It is the largest city "
        "in France and serves as the country's political, economic, "
        "and cultural center.",
        "A Fourier transform decomposes a signal into its constituent "
        "frequencies. It converts a function of time (or space) into "
        "a function of frequency, revealing the amplitude and phase "
        "of each frequency component.",
        "The French translation of 'hello' is 'bonjour'.",
    ]

    # Generate base-model completions
    print("  Generating base-model completions...")
    base_responses = []
    for prompt in prompts:
        resp = generate_text(prompt, tokenizer, model, max_new_tokens=50)
        base_responses.append(resp)
        print(f"    Prompt: {prompt[:40]}...")
        print(f"    GPT-2:  {resp[:60]}...")

    fig, axes = plt.subplots(3, 2, figsize=(20, 16))
    fig.suptitle(
        "Same Architecture, Different Behavior: Base Model vs Instruction-Tuned",
        fontsize=18, fontweight="bold", y=0.98,
    )
    fig.text(
        0.5, 0.945,
        "GPT-2 base was trained to predict the next token in web text.  "
        "It completes patterns but does not follow instructions.\n"
        "Supervised fine-tuning (SFT) on instruction/response pairs teaches "
        "a model to answer questions instead of continuing text.",
        ha="center", va="center", fontsize=11, color="#555555",
    )

    col_titles = [
        "Base Model (GPT-2): pattern completion",
        "After SFT: follows instructions",
    ]
    col_colors = [COLOR_PALETTE[3], COLOR_PALETTE[2]]  # red-ish, green-ish

    for col, title in enumerate(col_titles):
        axes[0, col].set_title(title, fontsize=14, fontweight="bold",
                               color=col_colors[col], pad=15)

    for row, (prompt, base_resp, sft_resp) in enumerate(
            zip(prompts, base_responses, sft_responses)):
        for col in range(2):
            ax = axes[row, col]
            ax.axis("off")

            response = base_resp if col == 0 else sft_resp

            # Prompt box at the top
            prompt_wrapped = wrap_text(prompt, width=48)
            prompt_box = ax.text(
                0.5, 0.92, f"Prompt:  {prompt_wrapped}",
                transform=ax.transAxes,
                ha="center", va="top",
                fontsize=11, fontfamily="monospace", fontweight="bold",
                color="#333333",
                bbox=dict(boxstyle="round,pad=0.5",
                          facecolor="#E8E8E8", edgecolor="#999999",
                          linewidth=1.2),
            )

            # Response box below
            response_wrapped = wrap_text(response, width=48)
            if col == 0:
                # Base model -- red-tinted box
                face_color = "#FDECEA"
                edge_color = COLOR_PALETTE[3]
                label = "GPT-2 output:"
            else:
                # SFT model -- green-tinted box
                face_color = "#E8F5E9"
                edge_color = COLOR_PALETTE[2]
                label = "SFT model output:"

            ax.text(
                0.5, 0.45,
                f"{label}\n{response_wrapped}",
                transform=ax.transAxes,
                ha="center", va="center",
                fontsize=10, fontfamily="monospace",
                color="#222222",
                bbox=dict(boxstyle="round,pad=0.6",
                          facecolor=face_color, edgecolor=edge_color,
                          linewidth=1.8),
                linespacing=1.5,
            )

    fig.tight_layout(rect=[0, 0.0, 1, 0.92])
    save_fig(fig, "12_sft_comparison")


# ---------------------------------------------------------------------------
# Figure 2 -- SFT training data format
# ---------------------------------------------------------------------------

def make_training_format_figure():
    set_style()

    training_pairs = [
        {
            "instruction": "What is the capital of France?",
            "response": "The capital of France is Paris.",
        },
        {
            "instruction": (
                "Summarize this in one sentence: The Fourier\n"
                "transform is a mathematical operation that\n"
                "decomposes a function into its constituent\n"
                "frequencies.  It is widely used in signal\n"
                "processing, physics, and engineering."
            ),
            "response": (
                "The Fourier transform decomposes a function\n"
                "into its frequency components and is widely\n"
                "used in science and engineering."
            ),
        },
        {
            "instruction": "Write a Python function to compute the mean.",
            "response": "def mean(values):\n    return sum(values) / len(values)",
        },
    ]

    fig, ax = plt.subplots(figsize=(16, 14))
    ax.axis("off")

    fig.suptitle(
        "SFT Training Data: Instruction / Response Pairs",
        fontsize=18, fontweight="bold", y=0.97,
    )
    fig.text(
        0.5, 0.935,
        "The model is fine-tuned on thousands of (instruction, response) examples.\n"
        "The architecture is unchanged -- only the training data format differs.",
        ha="center", va="center", fontsize=12, color="#555555",
    )

    # Layout parameters
    card_left = 0.08
    card_width = 0.84
    card_gap = 0.02
    n_cards = len(training_pairs)

    # Available vertical space: roughly 0.05 to 0.90 (in figure coords)
    total_height = 0.85
    card_height = (total_height - (n_cards - 1) * card_gap) / n_cards
    start_top = 0.90

    instr_color = "#D6EAF8"    # light blue
    instr_edge = COLOR_PALETTE[0]
    resp_color = "#D5F5E3"     # light green
    resp_edge = COLOR_PALETTE[2]

    for i, pair in enumerate(training_pairs):
        card_top = start_top - i * (card_height + card_gap)
        card_bottom = card_top - card_height

        # Each card is split: top half = instruction, bottom half = response
        split = card_top - card_height * 0.45

        # Instruction box
        instr_rect = mpatches.FancyBboxPatch(
            (card_left, split), card_width, card_top - split,
            boxstyle="round,pad=0.012",
            facecolor=instr_color, edgecolor=instr_edge,
            linewidth=2.0, transform=fig.transFigure,
        )
        fig.patches.append(instr_rect)

        # Response box
        resp_rect = mpatches.FancyBboxPatch(
            (card_left, card_bottom), card_width, split - card_bottom,
            boxstyle="round,pad=0.012",
            facecolor=resp_color, edgecolor=resp_edge,
            linewidth=2.0, transform=fig.transFigure,
        )
        fig.patches.append(resp_rect)

        # Instruction label + text
        fig.text(
            card_left + 0.02, (card_top + split) / 2 + 0.015,
            "[INSTRUCTION]",
            fontsize=11, fontweight="bold", color=instr_edge,
            fontfamily="monospace", va="center",
            transform=fig.transFigure,
        )
        fig.text(
            card_left + 0.17, (card_top + split) / 2 - 0.005,
            pair["instruction"],
            fontsize=10.5, color="#222222",
            fontfamily="monospace", va="center",
            transform=fig.transFigure,
            linespacing=1.4,
        )

        # Response label + text
        fig.text(
            card_left + 0.02, (split + card_bottom) / 2 + 0.015,
            "[RESPONSE]",
            fontsize=11, fontweight="bold", color=resp_edge,
            fontfamily="monospace", va="center",
            transform=fig.transFigure,
        )
        fig.text(
            card_left + 0.17, (split + card_bottom) / 2 - 0.005,
            pair["response"],
            fontsize=10.5, color="#222222",
            fontfamily="monospace", va="center",
            transform=fig.transFigure,
            linespacing=1.4,
        )

        # Pair number label
        fig.text(
            card_left - 0.025, (card_top + card_bottom) / 2,
            f"{i + 1}",
            fontsize=16, fontweight="bold", color="#AAAAAA",
            ha="center", va="center",
            transform=fig.transFigure,
        )

    # Arrow + annotation at the bottom
    fig.text(
        0.5, 0.025,
        "Same model weights  +  structured training data  =  instruction-following behavior",
        ha="center", va="center", fontsize=13, fontweight="bold",
        color=COLOR_PALETTE[0],
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F0F4FA",
                  edgecolor=COLOR_PALETTE[0], linewidth=1.5),
        transform=fig.transFigure,
    )

    save_fig(fig, "12_sft_training_format")


# ---------------------------------------------------------------------------
# Figure 3 -- Probability shift (top-10 next-token probabilities)
# ---------------------------------------------------------------------------

def make_probability_shift_figure(tokenizer, model):
    set_style()

    prompt = "What is the capital of France?"
    tokens, probs = get_topk_next_tokens(prompt, tokenizer, model, k=10)
    k = len(tokens)

    display_tokens = [escape_token(t) for t in tokens]

    # Check whether "Paris" appears anywhere in top-10
    paris_in_top = any("paris" in t.lower() or "Paris" in t
                       for t in tokens)

    fig, ax = plt.subplots(figsize=(14, 8))

    fig.suptitle(
        "Why Base GPT-2 Does Not Answer Questions",
        fontsize=18, fontweight="bold", y=0.97,
    )
    fig.text(
        0.5, 0.925,
        f'Top-10 next-token probabilities after: "{prompt}"',
        ha="center", va="center", fontsize=13, fontfamily="monospace",
        color="#444444",
    )

    # Horizontal bar chart (highest prob at top)
    y_pos = np.arange(k)
    display_tokens_r = display_tokens[::-1]
    probs_r = probs[::-1]

    # Color: highlight continuation-style tokens vs answer-style tokens
    answer_keywords = {"Paris", "paris", "\u2581Paris", "\u2581paris"}
    colors = []
    for tok in display_tokens_r:
        if tok.strip() in answer_keywords:
            colors.append(COLOR_PALETTE[2])  # green for "Paris"
        else:
            colors.append(COLOR_PALETTE[0])  # blue for all others

    bars = ax.barh(y_pos, probs_r, color=colors, edgecolor="white",
                   linewidth=0.5, height=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(display_tokens_r, fontfamily="monospace", fontsize=12)
    ax.set_xlabel("Probability", fontsize=12)

    # Probability labels on bars
    for bar, p in zip(bars, probs_r):
        w = bar.get_width()
        label = f"{p:.4f}" if p < 0.01 else f"{p:.3f}"
        ax.text(w + 0.003, bar.get_y() + bar.get_height() / 2,
                label, va="center", ha="left",
                fontsize=10, fontfamily="monospace", color="#333333")

    ax.set_xlim(0, min(probs[0] * 1.45, 1.0))
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", visible=False)

    # Annotation box explaining the key insight
    if not paris_in_top:
        insight = (
            '"Paris" does not even appear in the top 10.\n'
            "Base GPT-2 predicts continuation tokens\n"
            '(e.g. "\\n", "The", "What") because it was\n'
            "trained on web text, not Q&A pairs.\n\n"
            "SFT fixes this: after fine-tuning on\n"
            'instruction/response pairs, "Paris"\n'
            "would dominate the distribution."
        )
    else:
        insight = (
            '"Paris" appears but is not dominant.\n'
            "Base GPT-2 spreads probability across\n"
            "continuation tokens because it was trained\n"
            "on web text, not Q&A pairs.\n\n"
            "After SFT, the model learns to concentrate\n"
            'probability on answer tokens like "Paris".'
        )

    ax.text(
        0.97, 0.35,
        insight,
        transform=ax.transAxes,
        ha="right", va="center",
        fontsize=10, color="#333333",
        fontfamily="sans-serif",
        linespacing=1.5,
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#FFF9E6",
                  edgecolor=COLOR_PALETTE[1], linewidth=1.5, alpha=0.95),
    )

    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=COLOR_PALETTE[0], edgecolor="white",
                       label="Text-continuation tokens"),
        mpatches.Patch(facecolor=COLOR_PALETTE[2], edgecolor="white",
                       label='Answer token ("Paris")'),
    ]
    ax.legend(handles=legend_elements, loc="upper right", fontsize=10,
              frameon=True, fancybox=True, framealpha=0.9)

    fig.tight_layout(rect=[0, 0, 1, 0.90])
    save_fig(fig, "12_sft_probability_shift")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tokenizer, model = load_model()

    print("\n--- Figure 1: Base model vs instruction-tuned comparison ---")
    make_comparison_figure(tokenizer, model)

    print("\n--- Figure 2: SFT training data format ---")
    make_training_format_figure()

    print("\n--- Figure 3: Top-10 next-token probability shift ---")
    make_probability_shift_figure(tokenizer, model)

    print("\nDone.")
