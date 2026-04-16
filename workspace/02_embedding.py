"""02 – Token Embeddings: from tokens to vectors in high-dimensional space.

Produces two figures:
  1. 02_embedding_clusters  – PCA scatter of GPT-2 embeddings for curated word
     groups, showing that semantically similar words cluster together.
  2. 02_embedding_arithmetic – The classic king - man + woman ≈ queen analogy
     illustrated with arrows in a 2D PCA projection.
"""

import sys
import os
import numpy as np
import torch
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from sklearn.decomposition import PCA

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE
from shared.data import WORD_GROUPS

# ---------------------------------------------------------------------------
# 1. Load model and tokenizer
# ---------------------------------------------------------------------------

from transformers import AutoTokenizer, AutoModelForCausalLM

print("Loading GPT-2 …")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
model = AutoModelForCausalLM.from_pretrained("gpt2")
model.eval()

# Full embedding table: (vocab_size, 768)
embedding_table = model.transformer.wte.weight.detach().cpu().numpy()
print(f"Embedding table shape: {embedding_table.shape}")


# ---------------------------------------------------------------------------
# Helper: word -> embedding (first token if the word is split)
# ---------------------------------------------------------------------------

def word_embedding(word: str) -> np.ndarray:
    """Return the embedding for *word*, using the first sub-token if needed."""
    token_ids = tokenizer.encode(word, add_special_tokens=False)
    return embedding_table[token_ids[0]]


def word_embedding_with_id(word: str):
    """Return (embedding, token_id) for *word*."""
    token_ids = tokenizer.encode(word, add_special_tokens=False)
    return embedding_table[token_ids[0]], token_ids[0]


# ---------------------------------------------------------------------------
# 2. Figure 1 – Embedding clusters
# ---------------------------------------------------------------------------

set_style()

# Collect all embeddings and metadata
words_all = []
embeddings_all = []
group_labels = []

group_names = list(WORD_GROUPS.keys())  # deterministic order
for group_name in group_names:
    for word in WORD_GROUPS[group_name]:
        words_all.append(word)
        embeddings_all.append(word_embedding(word))
        group_labels.append(group_name)

X = np.stack(embeddings_all)  # (n_words, 768)

# PCA to 2D
pca = PCA(n_components=2, random_state=42)
X_2d = pca.fit_transform(X)

# Pretty group labels for the legend
display_names = {
    "stats": "Stats / UQ",
    "animals": "Animals",
    "royalty": "Royalty",
    "verbs": "Verbs",
}

fig, ax = plt.subplots(figsize=(10, 7))

# Plot each group with its own color
for idx, group_name in enumerate(group_names):
    mask = [g == group_name for g in group_labels]
    xs = X_2d[mask, 0]
    ys = X_2d[mask, 1]
    color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
    ax.scatter(
        xs, ys,
        c=color,
        s=120,
        edgecolors="white",
        linewidths=0.8,
        zorder=3,
        label=display_names.get(group_name, group_name),
    )

# Label every point – use manual small offsets to reduce overlap
# We shift labels slightly and add a white outline for readability
texts = []
for i, word in enumerate(words_all):
    txt = ax.annotate(
        word,
        xy=(X_2d[i, 0], X_2d[i, 1]),
        xytext=(6, 6),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        color="#333333",
        zorder=4,
    )
    txt.set_path_effects([
        pe.withStroke(linewidth=3, foreground="white"),
    ])
    texts.append(txt)

# Try adjustText for automatic de-overlapping; fall back to static offsets
try:
    from adjustText import adjust_text
    adjust_text(
        texts,
        x=X_2d[:, 0],
        y=X_2d[:, 1],
        ax=ax,
        arrowprops=dict(arrowstyle="-", color="#999999", lw=0.5),
        force_text=(0.8, 0.8),
        expand=(1.2, 1.4),
        ensure_inside_axes=False,
    )
except ImportError:
    # Manual staggering: alternate offset direction per group to reduce clashes
    for i, txt in enumerate(texts):
        angle = (i * 47) % 360  # pseudo-random spread
        dx = 8 * np.cos(np.radians(angle))
        dy = 8 * np.sin(np.radians(angle))
        txt.set_position((dx, dy))

ax.set_xlabel(f"PC 1  ({pca.explained_variance_ratio_[0]:.1%} variance)")
ax.set_ylabel(f"PC 2  ({pca.explained_variance_ratio_[1]:.1%} variance)")
ax.set_title("GPT-2 Token Embeddings — Semantic Clusters in 2D (PCA)")
ax.legend(loc="best", framealpha=0.9, fontsize=10)
fig.tight_layout()

save_fig(fig, "02_embedding_clusters")


# ---------------------------------------------------------------------------
# 3. Figure 2 – Vector arithmetic: king - man + woman ≈ queen
# ---------------------------------------------------------------------------

# Gather the four key embeddings
emb_king = word_embedding("king")
emb_man = word_embedding("man")
emb_woman = word_embedding("woman")
emb_queen = word_embedding("queen")

# Compute the analogy vector
analogy_vec = emb_king - emb_man + emb_woman

# Find the nearest token in the full vocabulary (cosine similarity)
norms = np.linalg.norm(embedding_table, axis=1, keepdims=True)
norms = np.where(norms == 0, 1e-9, norms)  # avoid division by zero
analogy_norm = np.linalg.norm(analogy_vec)
if analogy_norm == 0:
    analogy_norm = 1e-9
cos_sim = (embedding_table @ analogy_vec) / (norms.squeeze() * analogy_norm)
nearest_id = int(np.argmax(cos_sim))
nearest_word = tokenizer.decode([nearest_id]).strip()
nearest_sim = cos_sim[nearest_id]
print(f"king - man + woman  ≈  '{nearest_word}'  (cosine similarity = {nearest_sim:.4f})")

# Also report similarity to "queen"
queen_id = tokenizer.encode("queen", add_special_tokens=False)[0]
queen_sim = cos_sim[queen_id]
print(f"Cosine similarity to 'queen' token: {queen_sim:.4f}")

# Prepare embeddings for PCA (include the analogy result)
arith_labels = ["king", "man", "woman", "queen", "king−man+woman"]
arith_embs = np.stack([emb_king, emb_man, emb_woman, emb_queen, analogy_vec])

pca2 = PCA(n_components=2, random_state=42)
A_2d = pca2.fit_transform(arith_embs)

fig2, ax2 = plt.subplots(figsize=(9, 7))

# Define colors for each role
role_colors = {
    "king": COLOR_PALETTE[0],
    "man": COLOR_PALETTE[1],
    "woman": COLOR_PALETTE[2],
    "queen": COLOR_PALETTE[3],
    "king−man+woman": COLOR_PALETTE[4],
}

# Plot the five points
for i, label in enumerate(arith_labels):
    marker = "D" if label == "king−man+woman" else "o"
    size = 160 if label == "king−man+woman" else 120
    ax2.scatter(
        A_2d[i, 0], A_2d[i, 1],
        c=role_colors[label],
        s=size,
        marker=marker,
        edgecolors="white",
        linewidths=0.8,
        zorder=5,
    )

# Annotate each point
for i, label in enumerate(arith_labels):
    display_label = label
    if label == "king−man+woman":
        display_label = f"king − man + woman\n≈ '{nearest_word}' (sim={nearest_sim:.2f})"
    txt = ax2.annotate(
        display_label,
        xy=(A_2d[i, 0], A_2d[i, 1]),
        xytext=(12, 12),
        textcoords="offset points",
        fontsize=10,
        fontweight="bold",
        color=role_colors[arith_labels[i]],
        zorder=6,
    )
    txt.set_path_effects([pe.withStroke(linewidth=3, foreground="white")])

# Draw arrows to show the arithmetic
arrow_kw = dict(
    arrowstyle="->,head_width=0.3,head_length=0.15",
    linewidth=1.8,
    connectionstyle="arc3,rad=0.1",
)

# Arrow: king -> king - man  (conceptually: subtract "man")
# We show the three operations as arrows
# king --(-man)--> intermediate  --(+woman)--> result
# For visual clarity, draw:
#   king -----> result   (the overall operation, dashed)
#   man  - - -> woman    (parallel relationship, dotted)

# Arrow: king to result (main operation)
ax2.annotate(
    "",
    xy=(A_2d[4, 0], A_2d[4, 1]),
    xytext=(A_2d[0, 0], A_2d[0, 1]),
    arrowprops=dict(
        **arrow_kw,
        color=COLOR_PALETTE[0],
        alpha=0.6,
    ),
    zorder=2,
)

# Arrow: man to woman (parallel shift)
ax2.annotate(
    "",
    xy=(A_2d[2, 0], A_2d[2, 1]),
    xytext=(A_2d[1, 0], A_2d[1, 1]),
    arrowprops=dict(
        **arrow_kw,
        color=COLOR_PALETTE[1],
        alpha=0.6,
    ),
    zorder=2,
)

# Dashed line: result to queen (showing proximity)
ax2.plot(
    [A_2d[4, 0], A_2d[3, 0]],
    [A_2d[4, 1], A_2d[3, 1]],
    linestyle="--",
    color="#888888",
    linewidth=1.2,
    alpha=0.7,
    zorder=1,
)

# Add a midpoint annotation on the dashed line
mid_x = (A_2d[4, 0] + A_2d[3, 0]) / 2
mid_y = (A_2d[4, 1] + A_2d[3, 1]) / 2
ax2.annotate(
    f"cosine sim = {queen_sim:.2f}",
    xy=(mid_x, mid_y),
    xytext=(0, -16),
    textcoords="offset points",
    fontsize=8,
    fontstyle="italic",
    color="#666666",
    ha="center",
    zorder=6,
    path_effects=[pe.withStroke(linewidth=2, foreground="white")],
)

# Add operation labels on the arrows
king_to_result_mid = ((A_2d[0] + A_2d[4]) / 2)
ax2.annotate(
    "− man + woman",
    xy=king_to_result_mid,
    xytext=(-10, 14),
    textcoords="offset points",
    fontsize=8,
    fontstyle="italic",
    color=COLOR_PALETTE[0],
    ha="center",
    zorder=6,
    path_effects=[pe.withStroke(linewidth=2, foreground="white")],
)

man_to_woman_mid = ((A_2d[1] + A_2d[2]) / 2)
ax2.annotate(
    "gender direction",
    xy=man_to_woman_mid,
    xytext=(-10, 14),
    textcoords="offset points",
    fontsize=8,
    fontstyle="italic",
    color=COLOR_PALETTE[1],
    ha="center",
    zorder=6,
    path_effects=[pe.withStroke(linewidth=2, foreground="white")],
)

ax2.set_xlabel(f"PC 1  ({pca2.explained_variance_ratio_[0]:.1%} variance)")
ax2.set_ylabel(f"PC 2  ({pca2.explained_variance_ratio_[1]:.1%} variance)")
ax2.set_title("Embedding Arithmetic:  king − man + woman  ≈  queen")
ax2.grid(True, alpha=0.3)
fig2.tight_layout()

save_fig(fig2, "02_embedding_arithmetic")

print("\nDone – both figures saved.")
