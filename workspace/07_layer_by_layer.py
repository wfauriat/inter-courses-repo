"""
07_layer_by_layer.py

Visualize how hidden states evolve across the 24 layers of GPT-2 medium on a
single short prompt. Three complementary views of the residual stream:

1. Logit lens — apply the final LayerNorm + unembedding to every layer's last
   hidden state, so we see what the model WOULD predict if it stopped at layer k.
   (Left panel: top-1 token per layer; right panel: probability of the eventual
   top-1 token tracked across layers — the "emergence" curve.)

2. PCA trajectories — fit a 2D PCA on all (layer, token) hidden states and draw
   each token as a polyline through the 25 snapshots. Shows that tokens MOVE in
   representation space as they flow through the stack.

3. Norm + cosine evolution — L2 norm of the residual stream per layer (grows)
   and cosine similarity of each layer to the final layer (converges to 1).

Model: GPT-2 medium (355M, 24 layers, d_model=1024). First run downloads ~1.5 GB.
"""

import numpy as np
import matplotlib.pyplot as plt
import torch
from sklearn.decomposition import PCA
from transformers import GPT2LMHeadModel, GPT2Tokenizer

from shared import COLOR_PALETTE, save_fig, set_style

set_style()

MODEL_NAME = "gpt2-medium"
PROMPT = "The Eiffel Tower is located in the city of"


def load_and_run(prompt):
    print(f"Loading {MODEL_NAME} ...")
    tokenizer = GPT2Tokenizer.from_pretrained(MODEL_NAME)
    model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)
    model.eval()

    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    tokens = [tokenizer.decode([int(tid)]) for tid in input_ids[0]]

    print(f"Prompt : {prompt!r}")
    print(f"Tokens ({len(tokens)}): {tokens}")

    with torch.no_grad():
        out = model(input_ids, output_hidden_states=True)

    # hidden_states: tuple of (n_layers + 1), each shape (1, seq_len, d_model).
    # Index 0 = embedding output (wte + wpe); 1..n_layers = transformer block outputs.
    hidden = torch.stack(out.hidden_states, dim=0).squeeze(1)  # (n_layers+1, seq, d)
    return model, tokenizer, tokens, hidden, out.logits


def compute_logit_lens(model, hidden, final_logits_ref):
    """Apply model.transformer.ln_f + model.lm_head to each layer's last position.

    In HuggingFace transformers, the LAST element of output_hidden_states is already
    post-ln_f, whereas the earlier ones are pre-ln_f. We detect that and skip the
    extra norm on the final entry so we don't double-normalize.
    """
    with torch.no_grad():
        h_last = hidden[:, -1, :]  # (n_layers+1, d_model)

        # Probe: does hidden[-1] need ln_f to reproduce the true logits?
        true = final_logits_ref[0, -1]
        diff_pre = (model.lm_head(model.transformer.ln_f(h_last[-1])) - true).abs().max().item()
        diff_post = (model.lm_head(h_last[-1]) - true).abs().max().item()
        last_is_post_lnf = diff_post < diff_pre
        print(f"Logit-lens probe: last hidden is "
              f"{'post' if last_is_post_lnf else 'pre'}-ln_f "
              f"(err pre={diff_pre:.2e}, post={diff_post:.2e})")

        if last_is_post_lnf:
            normed = torch.cat(
                [model.transformer.ln_f(h_last[:-1]), h_last[-1:]], dim=0
            )
        else:
            normed = model.transformer.ln_f(h_last)

        logits = model.lm_head(normed)
        probs = torch.softmax(logits, dim=-1).cpu().numpy()
    return probs


def _pretty_token(s):
    """Make tokens readable — show leading-space tokens as '␣foo'."""
    if s.startswith(" "):
        return "␣" + s[1:]
    return s or "∅"


def plot_logit_lens(probs, tokenizer, prompt, final_top_id):
    n_layers = probs.shape[0]
    top1_ids = probs.argmax(axis=-1)
    top1_probs = probs[np.arange(n_layers), top1_ids]
    top1_tokens = [_pretty_token(tokenizer.decode([int(tid)])) for tid in top1_ids]

    final_token = _pretty_token(tokenizer.decode([int(final_top_id)]))
    final_curve = probs[:, final_top_id]

    fig, axes = plt.subplots(
        1, 2, figsize=(14, 10), gridspec_kw={"width_ratios": [1.0, 1.1]}
    )

    # --- Left: top-1 token table ---
    ax = axes[0]
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, n_layers - 0.5)
    ax.invert_yaxis()
    ax.set_yticks(range(n_layers))
    ax.set_yticklabels(
        ["embed" if i == 0 else f"L{i:02d}" for i in range(n_layers)], fontsize=9
    )
    ax.set_xticks([])
    ax.set_title("Logit lens — top-1 prediction at each layer")
    ax.set_frame_on(False)
    ax.grid(False)

    for i in range(n_layers):
        p = float(top1_probs[i])
        color = plt.cm.Blues(min(0.12 + p * 1.4, 0.92))
        ax.add_patch(
            plt.Rectangle((0.05, i - 0.4), 0.9, 0.8, facecolor=color, edgecolor="#555", lw=0.6)
        )
        text_color = "white" if p > 0.35 else "#111"
        label = f"{top1_tokens[i]}   {p:5.1%}"
        ax.text(0.5, i, label, ha="center", va="center",
                fontsize=10, family="monospace", color=text_color)

    # --- Right: emergence curve ---
    ax = axes[1]
    layers = np.arange(n_layers)
    ax.plot(layers, final_curve, "-o", color=COLOR_PALETTE[0], lw=2.2, ms=6)
    ax.fill_between(layers, 0, final_curve, color=COLOR_PALETTE[0], alpha=0.12)
    ax.set_xlabel("layer")
    ax.set_ylabel(f"P( {final_token} )")
    ax.set_title(f"When does {final_token!r} emerge?")
    ax.set_xticks(layers[::2])
    xtl = ["embed"] + [f"L{i:02d}" for i in range(1, n_layers)]
    ax.set_xticklabels([xtl[i] for i in layers[::2]], rotation=0, fontsize=9)
    ax.set_ylim(0, max(final_curve.max() * 1.15, 0.05))
    ax.grid(True, alpha=0.3)

    fig.suptitle(
        f"GPT-2 medium — logit lens on prompt: {prompt!r}", fontsize=12, y=0.995
    )
    fig.tight_layout()
    return fig


def plot_pca_trajectories(hidden, tokens):
    """L2-normalize each hidden state before PCA so every vector sits on the
    unit sphere — directions only, magnitudes discarded. Without this, the
    position-0 token's huge 'attention sink' norm (≈ 4000 vs ≈ 300 for siblings)
    hijacks PC1 and pins every other trajectory into a corner."""
    n_layers, seq_len, d_model = hidden.shape
    h = hidden.cpu().numpy()
    h_unit = h / (np.linalg.norm(h, axis=-1, keepdims=True) + 1e-9)
    flat = h_unit.reshape(n_layers * seq_len, d_model)
    pca = PCA(n_components=2)
    xy = pca.fit_transform(flat).reshape(n_layers, seq_len, 2)

    fig, ax = plt.subplots(figsize=(11, 8))
    colors = [COLOR_PALETTE[i % len(COLOR_PALETTE)] for i in range(seq_len)]

    for t in range(seq_len):
        path = xy[:, t, :]
        ax.plot(path[:, 0], path[:, 1], "-", color=colors[t], alpha=0.55, lw=1.4)
        # intermediate layer dots
        ax.scatter(path[1:-1, 0], path[1:-1, 1], color=colors[t], s=12, alpha=0.6)
        # embedding marker (circle) and final marker (star)
        ax.scatter(path[0, 0], path[0, 1], color=colors[t], s=90, marker="o",
                   edgecolors="black", lw=0.8, zorder=3,
                   label=_pretty_token(tokens[t]))
        ax.scatter(path[-1, 0], path[-1, 1], color=colors[t], s=180, marker="*",
                   edgecolors="black", lw=0.8, zorder=3)

    ax.set_xlabel(f"PC 1  ({pca.explained_variance_ratio_[0]:.1%} var)")
    ax.set_ylabel(f"PC 2  ({pca.explained_variance_ratio_[1]:.1%} var)")
    ax.set_title(
        f"Token trajectories through {n_layers - 1} layers "
        "(unit-normalized;  ○ = embedding,  ★ = final)"
    )
    ax.legend(loc="best", fontsize=9, ncol=2, framealpha=0.92, title="token")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_norm_and_cosine(hidden, tokens):
    n_layers, seq_len, _ = hidden.shape
    h = hidden.cpu().numpy()

    norms = np.linalg.norm(h, axis=-1)  # (n_layers, seq_len)
    final = h[-1]                        # (seq_len, d_model)
    cos = np.einsum("lsd,sd->ls", h, final) / (
        np.linalg.norm(h, axis=-1)
        * np.linalg.norm(final, axis=-1)[None, :]
        + 1e-9
    )

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    layers = np.arange(n_layers)

    # Norm — log scale so the position-0 "attention sink" (~4000) doesn't hide
    # the other tokens (~300). Mean line excludes position 0 so it tracks the
    # typical-token trend, not the outlier.
    ax = axes[0]
    for t in range(seq_len):
        is_sink = (t == 0)
        ax.plot(layers, norms[:, t], "-o",
                color=COLOR_PALETTE[t % len(COLOR_PALETTE)],
                alpha=0.9 if is_sink else 0.65,
                lw=2.2 if is_sink else 1.2,
                ms=4 if is_sink else 3.5,
                label=_pretty_token(tokens[t]) + (" (sink)" if is_sink else ""))
    mean_excl_sink = norms[:, 1:].mean(axis=-1)
    ax.plot(layers, mean_excl_sink, "-", color="black", lw=2.6,
            label="mean (excl. pos 0)")
    ax.set_yscale("log")
    ax.set_xlabel("layer")
    ax.set_ylabel("‖h‖   (log)")
    ax.set_title("Residual stream norm — position 0 is an 'attention sink'")
    ax.legend(loc="lower right", fontsize=7.5, ncol=2, framealpha=0.92)
    ax.grid(True, which="both", alpha=0.3)

    # Cosine to final
    ax = axes[1]
    for t in range(seq_len):
        ax.plot(layers, cos[:, t], "-o",
                color=COLOR_PALETTE[t % len(COLOR_PALETTE)],
                alpha=0.7, lw=1.2, ms=3.5)
    ax.plot(layers, cos.mean(axis=-1), "-", color="black", lw=2.6, label="mean")
    ax.axhline(1.0, color="gray", ls="--", alpha=0.5)
    ax.set_xlabel("layer")
    ax.set_ylabel("cos( h_ℓ ,  h_final )")
    ax.set_title("Direction converges toward the final representation")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def print_top3_table(probs, tokenizer, k=3):
    """Dump per-layer top-k to stdout for user inspection."""
    topk = probs.argsort(axis=-1)[:, -k:][:, ::-1]
    print(f"\nLayer-by-layer top-{k} next-token predictions (last position):")
    print("-" * 70)
    for i, row in enumerate(topk):
        name = "embed" if i == 0 else f"L{i:02d}"
        pieces = [
            f"{_pretty_token(tokenizer.decode([int(tid)])):>10}  {probs[i, tid]:6.2%}"
            for tid in row
        ]
        print(f"  {name:>5}  |  " + "  |  ".join(pieces))
    print("-" * 70)


def main():
    model, tokenizer, tokens, hidden, final_logits = load_and_run(PROMPT)

    final_top_id = int(final_logits[0, -1].argmax())
    final_top_token = tokenizer.decode([final_top_id])
    final_top_prob = float(torch.softmax(final_logits[0, -1], dim=-1)[final_top_id])
    print(f"Model prediction: {final_top_token!r}  (p={final_top_prob:.1%})")

    probs = compute_logit_lens(model, hidden, final_logits)
    print_top3_table(probs, tokenizer, k=3)

    save_fig(plot_logit_lens(probs, tokenizer, PROMPT, final_top_id),
             "07_layer_logit_lens")
    save_fig(plot_pca_trajectories(hidden, tokens),
             "07_layer_pca_trajectories")
    save_fig(plot_norm_and_cosine(hidden, tokens),
             "07_layer_norm_cosine")


if __name__ == "__main__":
    main()
