"""
02b_embedding_views.py

Four complementary ways to visualize the output of a single transformer layer,
using GPT-2 small's TOKEN embedding layer on the 3-token prompt 'the cat sits'
as a concrete example. Output shape is (3 tokens, 768 dims).

    1. Raw heatmap          — 3 rows × 768 columns of colored values.
                              Most literal: 'an embedding is just numbers'.
    2. PCA in vocab space   — fit PCA(2) on a sample of the full vocabulary,
                              then project our 3 tokens onto it. Shows WHERE
                              our tokens sit in the whole embedding landscape.
    3. Cosine similarity    — 3×3 relational view: how similar are the vectors?
    4. Per-dim line plot    — overlay 3 curves (x=dim 0..767); shows which
                              dimensions distinguish the tokens.

For focus, we use the raw TOKEN embedding (wte lookup), not tok+pos.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import torch
from sklearn.decomposition import PCA
from transformers import GPT2LMHeadModel, GPT2Tokenizer

from shared import COLOR_PALETTE, save_fig, set_style

set_style()

MODEL_NAME = "gpt2"          # small: d_model=768
PROMPT = "the cat sits"
N_REF = 2000                  # sample of vocab embeddings to fit PCA reference


def main():
    print(f"Loading {MODEL_NAME} ...")
    tok = GPT2Tokenizer.from_pretrained(MODEL_NAME)
    model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)
    model.eval()

    input_ids = tok.encode(PROMPT, return_tensors="pt")
    tokens = [tok.decode([int(tid)]) for tid in input_ids[0]]
    print(f"Prompt    : {PROMPT!r}")
    print(f"Token IDs : {input_ids[0].tolist()}")
    print(f"Tokens    : {tokens}")

    # Just the token embedding lookup — no positional, no blocks.
    with torch.no_grad():
        emb = model.transformer.wte(input_ids).squeeze(0).cpu().numpy()  # (3, 768)

    # Reference embedding matrix: a random sample of 2000 vocab rows.
    rng = np.random.default_rng(42)
    wte = model.transformer.wte.weight.detach().cpu().numpy()  # (50257, 768)
    ref_ids = rng.choice(wte.shape[0], size=N_REF, replace=False)
    ref_emb = wte[ref_ids]

    pca = PCA(n_components=2)
    ref_xy = pca.fit_transform(ref_emb)     # (N_REF, 2)
    our_xy = pca.transform(emb)              # (3, 2)

    norms = np.linalg.norm(emb, axis=-1, keepdims=True)
    cos = (emb @ emb.T) / (norms @ norms.T + 1e-9)  # (3, 3)

    # ---------------- plotting ----------------
    fig = plt.figure(figsize=(14, 12))
    gs = gridspec.GridSpec(3, 2, figure=fig, height_ratios=[0.9, 1.3, 0.9])

    token_colors = [COLOR_PALETTE[i] for i in range(len(tokens))]

    # 1. Raw heatmap — full width
    ax = fig.add_subplot(gs[0, :])
    vmax = float(np.abs(emb).max())
    im = ax.imshow(emb, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                   interpolation="nearest")
    ax.set_yticks(range(len(tokens)))
    ax.set_yticklabels([repr(t) for t in tokens], family="monospace")
    ax.set_xlabel("embedding dimension  (0 … 767)")
    ax.set_title(
        f"1. Raw heatmap — the (seq={len(tokens)},  d=768) matrix itself, "
        "each row = one token's vector"
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    cbar.set_label("value", fontsize=9)

    # 2. PCA in vocab-reference space — bottom-left
    ax = fig.add_subplot(gs[1, 0])
    ax.scatter(ref_xy[:, 0], ref_xy[:, 1], s=6, alpha=0.22, color="gray",
               label=f"{N_REF} random vocab tokens")
    for i, (t, (x, y)) in enumerate(zip(tokens, our_xy)):
        ax.scatter(x, y, s=220, color=token_colors[i],
                   edgecolors="black", lw=1.2, zorder=3)
        ax.annotate(f"  {t!r}", (x, y), fontsize=12, fontweight="bold",
                    zorder=4, family="monospace")
    ax.set_xlabel(f"PC1  ({pca.explained_variance_ratio_[0]:.1%} of vocab var)")
    ax.set_ylabel(f"PC2  ({pca.explained_variance_ratio_[1]:.1%} of vocab var)")
    ax.set_title("2. PCA with vocabulary as reference")
    ax.legend(fontsize=9, loc="best")
    ax.grid(True, alpha=0.3)

    # 3. Cosine similarity 3×3 — bottom-right
    ax = fig.add_subplot(gs[1, 1])
    im = ax.imshow(cos, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(tokens)))
    ax.set_yticks(range(len(tokens)))
    ax.set_xticklabels([repr(t) for t in tokens], family="monospace")
    ax.set_yticklabels([repr(t) for t in tokens], family="monospace")
    for i in range(len(tokens)):
        for j in range(len(tokens)):
            v = cos[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    color="white" if abs(v) > 0.55 else "#111",
                    fontsize=13, fontweight="bold")
    ax.set_title("3. Cosine similarity (3×3)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    # 4. Per-dim line plot — full width
    ax = fig.add_subplot(gs[2, :])
    dims = np.arange(emb.shape[1])
    for i, t in enumerate(tokens):
        ax.plot(dims, emb[i], color=token_colors[i], alpha=0.75, lw=0.9,
                label=repr(t))
    ax.set_xlabel("embedding dimension")
    ax.set_ylabel("value")
    ax.set_title("4. Per-dimension overlay — each token is one curve across 768 dims")
    ax.legend(loc="upper right", fontsize=10, ncol=3, framealpha=0.92)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, emb.shape[1] - 1)

    fig.suptitle(
        f"Four views of the token embedding output for {PROMPT!r}   "
        "(GPT-2 small, d=768)",
        fontsize=13, y=0.995,
    )
    fig.tight_layout()
    save_fig(fig, "02b_embedding_views")

    # Companion stdout print
    print(f"\nEmbedding stats (min / mean / max):")
    for i, t in enumerate(tokens):
        print(f"  {t!r:>10}  "
              f"min={emb[i].min():+.3f}  mean={emb[i].mean():+.3f}  "
              f"max={emb[i].max():+.3f}  ‖·‖={np.linalg.norm(emb[i]):.2f}")
    print(f"\nCosine similarity matrix:")
    print(f"              " + "  ".join(f"{t!r:>10}" for t in tokens))
    for i, t in enumerate(tokens):
        print(f"  {t!r:>10}  " + "  ".join(f"{cos[i, j]:>+10.3f}" for j in range(len(tokens))))


if __name__ == "__main__":
    main()
