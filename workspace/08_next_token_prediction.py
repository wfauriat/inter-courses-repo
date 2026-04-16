"""
08_next_token_prediction.py
===========================
Educational visualization: the model's ONLY task is to predict a probability
distribution over the next token.  Everything else (answering questions,
writing code, reasoning) emerges from this single mechanism.

Produces two figures:
  - 08_next_token_topk.png   Top-20 next-token probability bar charts (2x2 grid)
  - 08_next_token_tree.png   Autoregressive generation tree from "The cat"

Usage:
    source ~/.venvDS/bin/activate
    python workspace/08_next_token_prediction.py
"""

import sys
import os

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

def get_topk_next_tokens(prompt, tokenizer, model, k=20):
    """
    Run the model on `prompt` and return the top-k next-token predictions.

    Returns:
        tokens  -- list of decoded token strings (length k)
        probs   -- numpy array of probabilities (length k)
    """
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    with torch.no_grad():
        outputs = model(input_ids)
    # logits for the last position: shape (vocab_size,)
    logits = outputs.logits[0, -1, :]
    probabilities = torch.softmax(logits, dim=-1)
    topk = torch.topk(probabilities, k)

    tokens = [tokenizer.decode([idx]) for idx in topk.indices.tolist()]
    probs = topk.values.numpy()
    return tokens, probs


def escape_token(tok):
    """Make a token string safe and readable for display."""
    # Replace common invisible / confusing characters
    tok = tok.replace("\n", "\\n")
    tok = tok.replace("\t", "\\t")
    tok = tok.replace("\r", "\\r")
    # Show leading space explicitly
    if tok.startswith(" "):
        tok = "\u2581" + tok[1:]  # use underscore-like char for leading space
    return tok


# ---------------------------------------------------------------------------
# Figure 1 -- Top-k probability bar charts (2x2 grid)
# ---------------------------------------------------------------------------

def make_topk_figure(tokenizer, model):
    set_style()

    prompt_keys = ["capital", "uncertainty", "shakespeare", "pi"]
    titles = [
        '"The capital of France is"',
        '"The uncertainty in the measurement is"',
        '"To be or not to be, that is the"',
        '"The value of pi is 3.1"',
    ]

    fig, axes = plt.subplots(2, 2, figsize=(18, 16))
    fig.suptitle(
        "Next-Token Prediction: Top-20 Probabilities from GPT-2",
        fontsize=18, fontweight="bold", y=0.98,
    )
    fig.text(
        0.5, 0.945,
        "The model outputs a probability distribution over ~50,000 tokens. "
        "A peaked distribution = high confidence; a flat distribution = many plausible continuations.",
        ha="center", va="center", fontsize=12, color="#555555",
    )

    k = 20
    top1_color = COLOR_PALETTE[1]   # orange for top-1
    other_color = COLOR_PALETTE[0]  # blue for the rest

    for idx, (key, title) in enumerate(zip(prompt_keys, titles)):
        ax = axes[idx // 2][idx % 2]
        prompt = PROMPTS[key]
        tokens, probs = get_topk_next_tokens(prompt, tokenizer, model, k=k)

        display_tokens = [escape_token(t) for t in tokens]

        # Reverse order so highest probability is at the top
        y_pos = np.arange(k)
        display_tokens_r = display_tokens[::-1]
        probs_r = probs[::-1]

        colors = [other_color] * k
        colors[-1] = top1_color  # top-1 is last after reversal

        bars = ax.barh(y_pos, probs_r, color=colors, edgecolor="white",
                       linewidth=0.5, height=0.75)

        # Token labels on the y-axis
        ax.set_yticks(y_pos)
        ax.set_yticklabels(display_tokens_r, fontfamily="monospace",
                           fontsize=9.5)

        # Probability values on each bar
        for bar, p in zip(bars, probs_r):
            w = bar.get_width()
            if p >= 0.01:
                label = f"{p:.3f}"
            else:
                label = f"{p:.4f}"
            ax.text(w + 0.003, bar.get_y() + bar.get_height() / 2,
                    label, va="center", ha="left",
                    fontsize=8, fontfamily="monospace", color="#333333")

        ax.set_xlabel("Probability", fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold", pad=10,
                     fontfamily="monospace")

        # Annotate top-1 probability and entropy
        entropy = -np.sum(probs * np.log2(probs + 1e-12))
        # Note: this is entropy of top-k only, as an approximation
        ax.text(
            0.97, 0.05,
            f"Top-1: {probs[0]:.1%}\nH(top-20) = {entropy:.2f} bits",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=9, color="#444444",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f5f5f5",
                      edgecolor="#cccccc", alpha=0.9),
        )

        ax.set_xlim(0, min(probs[0] * 1.35, 1.0))
        ax.grid(axis="x", alpha=0.3)
        ax.grid(axis="y", visible=False)

    fig.tight_layout(rect=[0, 0, 1, 0.92])
    save_fig(fig, "08_next_token_topk")


# ---------------------------------------------------------------------------
# Figure 2 -- Autoregressive generation tree
# ---------------------------------------------------------------------------

def build_tree(prefix, tokenizer, model, depth=3, branch_top=3):
    """
    Recursively build a generation tree.

    Returns a nested dict:
        {"text": prefix, "children": [
            {"token": " sat", "prob": 0.12, "text": "The cat sat",
             "children": [...]},
            ...
        ]}

    At depth 3, only keep top-1 child to avoid explosion.
    """
    if depth == 0:
        return {"text": prefix, "children": []}

    tokens, probs = get_topk_next_tokens(prefix, tokenizer, model, k=branch_top)

    # At the deepest level, keep only top-1 to stay readable
    n_children = 1 if depth == 1 else branch_top

    children = []
    for i in range(n_children):
        child_text = prefix + tokens[i]
        child = build_tree(child_text, tokenizer, model,
                           depth=depth - 1, branch_top=branch_top)
        child["token"] = tokens[i]
        child["prob"] = float(probs[i])
        children.append(child)

    return {"text": prefix, "children": children}


def count_leaves(node):
    """Count the number of leaf nodes for layout spacing."""
    if not node.get("children"):
        return 1
    return sum(count_leaves(c) for c in node["children"])


def assign_positions(node, x, y_min, y_max, x_step):
    """
    Assign (x, y) positions to each node in the tree.
    Leaf nodes are spread evenly across [y_min, y_max].
    """
    y_center = (y_min + y_max) / 2
    node["x"] = x
    node["y"] = y_center

    children = node.get("children", [])
    if not children:
        return

    total_leaves = count_leaves(node)
    y_range = y_max - y_min

    current_y = y_min
    for child in children:
        child_leaves = count_leaves(child)
        child_span = (child_leaves / total_leaves) * y_range
        assign_positions(child, x + x_step, current_y,
                         current_y + child_span, x_step)
        current_y += child_span


def draw_tree(ax, node, tokenizer, is_root=True):
    """Recursively draw the generation tree on the given axes."""
    x, y = node["x"], node["y"]

    if is_root:
        # Root node: draw as a rounded box
        label = node["text"]
        bbox = dict(boxstyle="round,pad=0.4", facecolor=COLOR_PALETTE[1],
                    edgecolor="white", linewidth=2, alpha=0.9)
        ax.text(x, y, label, ha="center", va="center",
                fontsize=13, fontweight="bold", color="white",
                fontfamily="monospace", bbox=bbox, zorder=5)
    else:
        # Child node: show the token and its probability
        token_display = escape_token(node.get("token", ""))
        prob = node.get("prob", 0)
        label = f'{token_display}\n({prob:.1%})'

        # Color intensity based on probability
        alpha = 0.5 + 0.5 * min(prob / 0.5, 1.0)
        bbox = dict(boxstyle="round,pad=0.3", facecolor=COLOR_PALETTE[0],
                    edgecolor="white", linewidth=1.2, alpha=alpha)
        ax.text(x, y, label, ha="center", va="center",
                fontsize=9.5, fontweight="bold", color="white",
                fontfamily="monospace", bbox=bbox, zorder=5)

    # Draw edges to children
    for child in node.get("children", []):
        cx, cy = child["x"], child["y"]
        # Draw curved connection line
        ax.annotate(
            "", xy=(cx - 0.35, cy), xytext=(x + 0.35, y),
            arrowprops=dict(
                arrowstyle="->,head_width=0.12,head_length=0.06",
                color="#888888", lw=1.2,
                connectionstyle="arc3,rad=0.05",
            ),
            zorder=1,
        )
        draw_tree(ax, child, tokenizer, is_root=False)


def make_tree_figure(tokenizer, model):
    set_style()

    prefix = "The cat"
    print(f'  Building generation tree from "{prefix}"...')
    tree = build_tree(prefix, tokenizer, model, depth=3, branch_top=3)

    # Assign layout positions
    n_leaves = count_leaves(tree)
    fig_h = max(n_leaves * 1.1, 14)
    fig_w = 22
    x_step = 4.0

    assign_positions(tree, x=0, y_min=0, y_max=fig_h, x_step=x_step)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(-2.5, 4 * x_step + 2)
    ax.set_ylim(-0.5, fig_h + 1.5)
    ax.axis("off")

    fig.suptitle(
        'Autoregressive Generation: Many Possible Futures from "The cat"',
        fontsize=18, fontweight="bold", y=0.99,
    )
    fig.text(
        0.5, 0.975,
        "At each step the model predicts a distribution, samples one token, "
        "appends it, and repeats.  Top-3 branches shown per level.",
        ha="center", va="center", fontsize=12, color="#555555",
    )

    # Depth labels
    depth_labels = ["Prefix", "Step 1", "Step 2", "Step 3"]
    for i, lbl in enumerate(depth_labels):
        lx = i * x_step
        ax.text(lx, fig_h + 0.7, lbl, ha="center", va="center",
                fontsize=12, fontweight="bold", color=COLOR_PALETTE[4],
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#F0EEF8",
                          edgecolor=COLOR_PALETTE[4], linewidth=1.0))

    draw_tree(ax, tree, tokenizer, is_root=True)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save_fig(fig, "08_next_token_tree")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tokenizer, model = load_model()

    print("\n--- Figure 1: Top-k next-token probability bar charts ---")
    make_topk_figure(tokenizer, model)

    print("\n--- Figure 2: Autoregressive generation tree ---")
    make_tree_figure(tokenizer, model)

    print("\nDone.")
