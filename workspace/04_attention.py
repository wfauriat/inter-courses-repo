"""
04_attention.py
===============
Educational visualization: attention lets each token "look at" other tokens
with learned, context-dependent weights. This is how context flows through
the model.

Produces three figures:
  - 04_attention_heatmap.png       2x2 grid of attention heads (mid-layer)
  - 04_attention_coreference.png   What "it" attends to (bar chart)
  - 04_attention_winograd.png      Winograd comparison (side-by-side bar charts)

Usage:
    source ~/.venvDS/bin/activate
    python workspace/04_attention.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE
from shared.data import EXAMPLES

import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------

def load_model_and_tokenizer():
    """Load GPT-2 model and tokenizer once."""
    print("Loading GPT-2 model and tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_pretrained("gpt2", output_attentions=True)
    model.eval()
    return model, tokenizer


def get_attention_weights(model, tokenizer, text):
    """
    Run a forward pass and return attention weights and token labels.

    Returns:
        attentions: tuple of (num_layers) tensors, each (1, num_heads, seq_len, seq_len)
        token_labels: list of cleaned token strings
    """
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**inputs, output_attentions=True)

    attentions = outputs.attentions  # tuple of (1, 12, seq_len, seq_len)

    # Build readable token labels
    token_ids = inputs["input_ids"][0].tolist()
    token_labels = []
    for tid in token_ids:
        label = tokenizer.decode([tid]).strip()
        if not label:
            label = repr(tokenizer.decode([tid]))
        token_labels.append(label)

    return attentions, token_labels


def find_token_index(token_labels, word):
    """
    Find the index of a word in BPE token labels.
    Handles space-prefixed tokens (GPT-2 style) and partial matches for
    BPE-split words like "suitcase" -> ["suit", "case"].
    Returns the first matching index, or None.
    """
    # Exact match after stripping whitespace
    for i, t in enumerate(token_labels):
        if t.lower().strip() == word.lower():
            return i
    # Partial match: token starts with (or contains) the word
    for i, t in enumerate(token_labels):
        if t.lower().strip().startswith(word.lower()):
            return i
    # Last resort: word starts with the token (BPE split -- "suit" for "suitcase")
    for i, t in enumerate(token_labels):
        if word.lower().startswith(t.lower().strip()) and len(t.strip()) >= 3:
            return i
    return None


# ---------------------------------------------------------------------------
# Figure 1: Attention heatmap -- 2x2 grid of 4 heads from a mid-layer
# ---------------------------------------------------------------------------

def make_heatmap_figure(model, tokenizer):
    """Show 4 attention heads from a mid-layer as token x token heatmaps."""
    set_style()

    text = EXAMPLES["it_cat"]  # "The cat sat on the mat because it was tired"
    attentions, token_labels = get_attention_weights(model, tokenizer, text)

    # Try layers 5, 6, 7 -- pick the one that looks most interesting
    # (we use layer 5 as the default mid-layer; GPT-2 has layers 0-11)
    layer_idx = 5
    attn = attentions[layer_idx][0].numpy()  # (12, seq_len, seq_len)

    # Head selection: high variance EXCLUDING column 0, so we don't pick pure-sink
    # heads that just dump everything onto position 0.
    head_variances = [attn[h, :, 1:].var() for h in range(attn.shape[0])]
    sorted_heads = sorted(range(len(head_variances)),
                          key=lambda h: head_variances[h], reverse=True)
    selected_heads = sorted(sorted_heads[:4])  # top-4 by variance, sorted by index

    n_tokens = len(token_labels)
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(
        f"Attention Heatmaps -- Layer {layer_idx}, 4 Selected Heads\n"
        f'"{text}"',
        fontsize=14, fontweight="bold", y=0.98,
    )

    for idx, (ax, head_idx) in enumerate(zip(axes.flat, selected_heads)):
        head_weights = attn[head_idx]  # (seq_len, seq_len)

        # PowerNorm compresses the dynamic range so the attention-sink column
        # (position 0) doesn't drown out the secondary structure.
        im = ax.imshow(head_weights, cmap="Blues", aspect="auto",
                       norm=PowerNorm(gamma=0.4, vmin=0,
                                      vmax=float(head_weights.max())))

        # Token labels on axes
        ax.set_xticks(range(n_tokens))
        ax.set_xticklabels(token_labels, rotation=55, ha="right",
                           fontsize=9, fontfamily="monospace")
        ax.set_yticks(range(n_tokens))
        ax.set_yticklabels(token_labels, fontsize=9, fontfamily="monospace")

        ax.set_xlabel("Attends to (key)", fontsize=10)
        ax.set_ylabel("Token (query)", fontsize=10)
        ax.set_title(f"Head {head_idx}", fontsize=12, fontweight="bold")

        # Colorbar for each subplot
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=8)

        # Re-enable grid-like lines between cells
        ax.set_xticks(np.arange(-0.5, n_tokens, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, n_tokens, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=0.5)
        ax.grid(which="major", visible=False)
        ax.tick_params(which="minor", bottom=False, left=False)

        # Restore spines for heatmap
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color("#cccccc")

    fig.tight_layout(rect=[0, 0.07, 1, 0.93])

    # Add explanatory note at the bottom
    fig.text(
        0.5, 0.01,
        "Each cell (i, j) shows how much token i attends to token j. "
        "Rows sum to 1 (softmax). Causal mask: tokens can only attend leftward.\n"
        'Column 0 ("The") is bright in every head -- the "attention sink". '
        "PowerNorm (gamma=0.4) is used so secondary structure stays visible.",
        ha="center", va="bottom", fontsize=10, color="#555555",
        style="italic",
    )

    save_fig(fig, "04_attention_heatmap")


# ---------------------------------------------------------------------------
# Figure 2: Coreference -- what does "it" attend to?
# ---------------------------------------------------------------------------

def find_best_coreference_layer(attentions, token_labels, query_token="it",
                                target_token="cat"):
    """
    Scan all layers to find the one where 'query_token' attends most to
    'target_token' (averaged across heads). Returns (best_layer, best_score).
    """
    qi = find_token_index(token_labels, query_token)
    ti = find_token_index(token_labels, target_token)

    if qi is None or ti is None:
        return 5, 0.0  # fallback

    best_layer = 5
    best_score = -1.0

    for layer_idx, layer_attn in enumerate(attentions):
        # Average across heads: (seq_len, seq_len)
        avg_attn = layer_attn[0].numpy().mean(axis=0)
        score = avg_attn[qi, ti]
        if score > best_score:
            best_score = score
            best_layer = layer_idx

    return best_layer, best_score


def _color_for_coref_label(label):
    low = label.lower().strip()
    if low == "cat":
        return COLOR_PALETTE[2]   # green -- correct referent
    if low == "mat":
        return COLOR_PALETTE[3]   # red -- alt noun
    if low == "it":
        return COLOR_PALETTE[4]   # purple -- self
    return COLOR_PALETTE[0]       # blue -- other


def _draw_coref_panel(ax, labels, weights, title, xlabel):
    """Draw a single horizontal bar chart of attention weights."""
    order = np.argsort(weights)[::-1]
    sorted_labels = [labels[i] for i in order]
    sorted_weights = weights[order]
    colors = [_color_for_coref_label(l) for l in sorted_labels]

    y_pos = np.arange(len(sorted_labels))
    bars = ax.barh(y_pos, sorted_weights, color=colors, edgecolor="white",
                   linewidth=0.5, height=0.7)
    ax.set_yticks(y_pos)
    ax.set_yticklabels([f'"{l}"' for l in sorted_labels],
                       fontsize=10, fontfamily="monospace")
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold")

    for bar, w in zip(bars, sorted_weights):
        if w > 0.005:
            ax.text(bar.get_width() + sorted_weights.max() * 0.01,
                    bar.get_y() + bar.get_height() / 2,
                    f"{w:.3f}", va="center", fontsize=8, color="#444444")

    ax.set_xlim(0, max(sorted_weights.max() * 1.2, 1e-3))
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)


def make_coreference_figure(model, tokenizer):
    """Show what 'it' attends to, raw and with the attention sink removed."""
    set_style()

    text = EXAMPLES["it_cat"]  # "The cat sat on the mat because it was tired"
    attentions, token_labels = get_attention_weights(model, tokenizer, text)

    best_layer, best_score = find_best_coreference_layer(
        attentions, token_labels, "it", "cat"
    )
    print(f"  Best coreference layer: {best_layer} (avg attention to 'cat': {best_score:.4f})")

    it_idx = find_token_index(token_labels, "it")
    if it_idx is None:
        print("  WARNING: 'it' token not found!")
        return

    layer_attn = attentions[best_layer][0].numpy()  # (n_heads, seq, seq)
    avg_from_it = layer_attn.mean(axis=0)[it_idx, :]  # (seq,)

    display_len = it_idx + 1
    display_labels = token_labels[:display_len]
    raw_weights = avg_from_it[:display_len]

    # Sink-excluded: zero out position 0, then renormalize the remaining mass.
    no_sink = raw_weights.copy()
    no_sink[0] = 0.0
    remaining = no_sink.sum()
    if remaining > 0:
        no_sink = no_sink / remaining

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle(
        f'What does "it" attend to?  (Layer {best_layer}, all heads averaged)\n'
        f'"{text}"',
        fontsize=13, fontweight="bold", y=1.0,
    )

    _draw_coref_panel(
        ax1, display_labels, raw_weights,
        "Raw attention weights",
        "Attention weight (rows sum to 1)",
    )
    _draw_coref_panel(
        ax2, display_labels, no_sink,
        f'After removing "{display_labels[0]}" (attention sink) and renormalizing',
        "Attention weight (share of non-sink mass)",
    )

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLOR_PALETTE[2], label='"cat" (correct referent)'),
        Patch(facecolor=COLOR_PALETTE[3], label='"mat" (alternative noun)'),
        Patch(facecolor=COLOR_PALETTE[4], label='"it" (self)'),
        Patch(facecolor=COLOR_PALETTE[0], label="other tokens"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=4,
               fontsize=10, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

    fig.text(
        0.5, -0.06,
        "Left: the first token dominates (attention sink). "
        "Right: once that mass is set aside, the semantic preference for "
        '"cat" over "mat" becomes visible.',
        ha="center", va="top", fontsize=10, color="#555555", style="italic",
    )

    fig.tight_layout(rect=[0, 0.04, 1, 0.94])
    save_fig(fig, "04_attention_coreference")


# ---------------------------------------------------------------------------
# Figure 3: Winograd comparison
# ---------------------------------------------------------------------------

def _attention_from_token(attentions, query_idx, layer_idx):
    """Return (avg over heads) attention from query_idx at a given layer."""
    return attentions[layer_idx][0].numpy().mean(axis=0)[query_idx, :]


def make_winograd_figure(model, tokenizer):
    """Side-by-side bar charts of attention from the adjective ('big' / 'small')
    in the two Winograd sentences.

    Why the adjective, not 'it'?  Under causal masking, 'it' cannot see the
    adjective that follows it -- so the attention pattern from 'it' is
    identical in the two sentences up to the position of the adjective. The
    disambiguation signal lives in the adjective itself: from 'big' or
    'small', the model can already look back and 'decide' which noun is the
    referent.
    """
    set_style()

    text_big = EXAMPLES["trophy_big"]
    text_small = EXAMPLES["trophy_small"]

    attn_big, labels_big_full = get_attention_weights(model, tokenizer, text_big)
    attn_small, labels_small_full = get_attention_weights(model, tokenizer, text_small)

    qb = find_token_index(labels_big_full, "big")
    qs = find_token_index(labels_small_full, "small")
    trophy_b = find_token_index(labels_big_full, "trophy")
    suit_b = find_token_index(labels_big_full, "suit")  # BPE split
    trophy_s = find_token_index(labels_small_full, "trophy")
    suit_s = find_token_index(labels_small_full, "suit")

    if None in (qb, qs, trophy_b, suit_b, trophy_s, suit_s):
        print("  WARNING: missing key token in Winograd sentences!")
        return

    # Scan layers: pick the layer where the DIFFERENCE between the two
    # sentences (for attention onto trophy / suitcase) is largest. That is
    # where the model makes the disambiguation most visible.
    n_layers = len(attn_big)
    best_layer, best_diff = 0, -np.inf
    for L in range(n_layers):
        row_b = _attention_from_token(attn_big, qb, L)
        row_s = _attention_from_token(attn_small, qs, L)
        diff = (abs(row_b[trophy_b] - row_s[trophy_s]) +
                abs(row_b[suit_b]   - row_s[suit_s]))
        if diff > best_diff:
            best_diff = diff
            best_layer = L

    row_b = _attention_from_token(attn_big,   qb, best_layer)[:qb + 1]
    row_s = _attention_from_token(attn_small, qs, best_layer)[:qs + 1]
    labs_b = labels_big_full[:qb + 1]
    labs_s = labels_small_full[:qs + 1]

    print(f"  Winograd best layer: {best_layer} (differentiation score {best_diff:.4f})")
    print(f"    'big'   -> trophy={row_b[trophy_b]:.3f}  suitcase={row_b[suit_b]:.3f}")
    print(f"    'small' -> trophy={row_s[trophy_s]:.3f}  suitcase={row_s[suit_s]:.3f}")

    def winograd_colors(labels, query_label):
        colors = []
        for l in labels:
            low = l.lower().strip()
            if low == "trophy":
                colors.append(COLOR_PALETTE[1])   # orange
            elif low in ("suitcase", "suit", "case"):
                colors.append(COLOR_PALETTE[0])   # blue
            elif low == query_label:
                colors.append(COLOR_PALETTE[4])   # purple -- the query token
            elif low == "it":
                colors.append(COLOR_PALETTE[3])   # red -- the pronoun
            else:
                colors.append("#B0B0B0")
        return colors

    def draw(ax, labels, weights, query_label, title, xlabel):
        order = np.argsort(weights)[::-1]
        sorted_labels = [labels[i] for i in order]
        sorted_w = weights[order]
        colors = winograd_colors(sorted_labels, query_label)
        y = np.arange(len(sorted_labels))
        bars = ax.barh(y, sorted_w, color=colors, edgecolor="white",
                       linewidth=0.5, height=0.7)
        ax.set_yticks(y)
        ax.set_yticklabels([f'"{l}"' for l in sorted_labels],
                           fontsize=10, fontfamily="monospace")
        ax.invert_yaxis()
        ax.set_xlabel(xlabel, fontsize=11)
        ax.set_title(title, fontsize=12, fontweight="bold")
        for bar, w in zip(bars, sorted_w):
            if w > 0.005:
                ax.text(bar.get_width() + sorted_w.max() * 0.01,
                        bar.get_y() + bar.get_height() / 2,
                        f"{w:.3f}", va="center", fontsize=8, color="#444444")
        ax.set_xlim(0, max(sorted_w.max() * 1.2, 1e-3))
        ax.spines["right"].set_visible(False)
        ax.spines["top"].set_visible(False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle(
        'Winograd Schema: attention from the adjective back to the two nouns\n'
        "Same sentence up to 'it' -- the adjective carries the disambiguation signal",
        fontsize=14, fontweight="bold", y=1.0,
    )

    draw(
        ax1, labs_b, row_b, "big",
        f'Query = "big"   (Layer {best_layer})\n'
        f'{text_big}',
        "Attention weight (rows sum to 1)",
    )
    draw(
        ax2, labs_s, row_s, "small",
        f'Query = "small"   (Layer {best_layer})\n'
        f'{text_small}',
        "Attention weight (rows sum to 1)",
    )

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=COLOR_PALETTE[1], label='"trophy"'),
        Patch(facecolor=COLOR_PALETTE[0], label='"suitcase" (BPE: suit+case)'),
        Patch(facecolor=COLOR_PALETTE[3], label='"it"'),
        Patch(facecolor=COLOR_PALETTE[4], label='query adjective'),
        Patch(facecolor="#B0B0B0", label="other tokens"),
    ]
    fig.legend(handles=legend_elements, loc="lower center", ncol=5,
               fontsize=10, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

    fig.text(
        0.5, -0.07,
        '"too big" \u2192 trophy is too big (to fit)  |  '
        '"too small" \u2192 suitcase is too small (to hold it).  '
        "We pick the layer where the two attention patterns diverge the most.\n"
        "GPT-2 small does not perfectly resolve the ambiguity, but the shift "
        "in mass between 'trophy' and 'suitcase' across the two sentences is visible.",
        ha="center", va="top", fontsize=10, color="#555555", style="italic",
    )

    fig.tight_layout(rect=[0, 0.05, 1, 0.94])
    save_fig(fig, "04_attention_winograd")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    model, tokenizer = load_model_and_tokenizer()

    print("\n--- Figure 1: Attention heatmap (2x2 grid) ---")
    make_heatmap_figure(model, tokenizer)

    print("\n--- Figure 2: Coreference (what does 'it' attend to?) ---")
    make_coreference_figure(model, tokenizer)

    print("\n--- Figure 3: Winograd comparison ---")
    make_winograd_figure(model, tokenizer)

    print("\nDone. All figures saved.")
