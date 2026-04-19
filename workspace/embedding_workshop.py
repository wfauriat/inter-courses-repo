"""
embedding_workshop.py
=====================
Standalone Qt app that makes "meaning as direction" visible in word
embedding space — using GloVe (glove.6B.100d), disconnected from any
GPT-2 mechanics. The other two workshops cover GPT-2; this one is the
clean version of the embedding story.

What it teaches:
  1. Words are vectors; similar meanings sit close together.
  2. Categories form clusters in 2D (PCA / t-SNE).
  3. Pairwise cosine similarities encode taxonomy.
  4. Vector arithmetic recovers analogies (king − man + woman ≈ queen).
  5. Cosine vs Euclidean rank words very differently — frequency-driven
     norm differences are the reason the field uses cosine.

GloVe is required as a one-time download (~862 MB).

  Easy path (Hugging Face mirror, uses huggingface_hub + ~/.cache/huggingface):
      python workspace/embedding_workshop.py --fetch-glove
  → downloads glove.6B.zip from stanfordnlp/glove and extracts only the
    100d file into workspace/data/glove.6B.100d.txt. Idempotent.

  Manual fallback:
      Download https://nlp.stanford.edu/data/glove.6B.zip, unzip, and
      place glove.6B.100d.txt at workspace/data/.

  After the file is in place, the first launch parses it and caches a
  .npz next to it for fast subsequent loads (the .txt can be deleted
  once the .npz exists).

Usage:
    source ~/.venvDS/bin/activate
    python workspace/embedding_workshop.py --fetch-glove   # one-time
    python workspace/embedding_workshop.py                 # launch UI
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import zipfile
from dataclasses import dataclass, field

import numpy as np

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMainWindow,
    QPlainTextEdit, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget,
)

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import COLOR_PALETTE


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GLOVE_TXT = os.path.join(DATA_DIR, "glove.6B.100d.txt")
GLOVE_NPZ = os.path.join(DATA_DIR, "glove.6B.100d.npz")
GLOVE_FILENAME_IN_ZIP = "glove.6B.100d.txt"
HF_GLOVE_REPO = "stanfordnlp/glove"
HF_GLOVE_ZIP = "glove.6B.zip"
GLOVE_URL_FALLBACK = "https://nlp.stanford.edu/data/glove.6B.zip"


def _missing_glove_message() -> str:
    return (
        "\nGloVe vectors not found.\n\n"
        "This app needs glove.6B.100d.txt. Easiest install:\n\n"
        "    python workspace/embedding_workshop.py --fetch-glove\n\n"
        f"  → downloads {HF_GLOVE_ZIP} (~862 MB) once from "
        f"the Hugging Face mirror\n"
        f"    ({HF_GLOVE_REPO}, cached under ~/.cache/huggingface)\n"
        f"  → extracts only the 100d file into\n"
        f"    {GLOVE_TXT}\n\n"
        f"Or do it manually: download {GLOVE_URL_FALLBACK}, unzip, and\n"
        f"place glove.6B.100d.txt at the path above.\n"
    )


def fetch_glove_from_hf() -> None:
    """Download glove.6B.zip from the Hugging Face mirror, extract just
    the 100d file into workspace/data/. Idempotent: if the .txt is
    already present, does nothing. The 862 MB zip stays in the HF cache,
    not in workspace/data/."""
    if os.path.exists(GLOVE_TXT):
        print(f"Already present: {GLOVE_TXT}  (nothing to do)")
        return
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise RuntimeError(
            "huggingface_hub is not installed. Either `pip install "
            "huggingface_hub` or do the manual download — see "
            f"{GLOVE_URL_FALLBACK}") from exc

    print(f"Downloading {HF_GLOVE_ZIP} from {HF_GLOVE_REPO} via "
          "huggingface_hub ... (~862 MB, cached for next time)",
          flush=True)
    zip_path = hf_hub_download(repo_id=HF_GLOVE_REPO,
                               filename=HF_GLOVE_ZIP)
    print(f"Zip cached at: {zip_path}")

    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Extracting {GLOVE_FILENAME_IN_ZIP} into {DATA_DIR} ...",
          flush=True)
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if GLOVE_FILENAME_IN_ZIP not in names:
            raise RuntimeError(
                f"{GLOVE_FILENAME_IN_ZIP} not found in {zip_path}; "
                f"contents = {names}")
        with zf.open(GLOVE_FILENAME_IN_ZIP) as src, \
                open(GLOVE_TXT, "wb") as dst:
            shutil.copyfileobj(src, dst)
    size_mb = os.path.getsize(GLOVE_TXT) / 1024 / 1024
    print(f"Done. {GLOVE_TXT}  ({size_mb:.0f} MB)")
    print("Run the app again (without --fetch-glove) to launch it.")


DEFAULT_GROUPS = [
    # Canonical word2vec / GloVe demo clusters: a clean animal cluster, a
    # clean construction cluster, and a country cluster (Mikolov et al. 2013
    # used countries/capitals as the showcase for linear semantic structure).
    ("animals",       "cat, dog, sheep, horse, cow"),
    ("constructions", "tower, building, bridge, house"),
    ("countries",     "france, germany, italy, japan, spain"),
]

# Two canonical analogies the user can try in the UI:
#   1. king − man + woman ≈ queen           (gender, Mikolov 2013 — the famous one)
#   2. paris − france + germany ≈ berlin    (capital-country, also Mikolov 2013)
ANALOGY_EXAMPLES = [
    ("king",  "man",    "woman",   "queen"),
    ("paris", "france", "germany", "berlin"),
]

# Mutually-exclusive presets that temporarily swap the word-groups table
# for analogy-focused sets and overlay the chain arrow on the 2D scatter.
# Checking one snapshots the user's current groups; unchecking restores
# them. Groups are chosen to keep A, B, C, D all on-screen.
ANALOGY_PRESETS = [
    {
        "key":     "king",
        "label":   "king − man + woman",
        "groups":  [
            ("titles",  "king, queen, prince, princess"),
            ("persona", "man, woman, dad, mom, son, girl"),
        ],
        "analogy": ANALOGY_EXAMPLES[0],   # king − man + woman ≈ queen
    },
    {
        "key":     "paris",
        "label":   "paris − france + germany",
        "groups":  [
            ("cities",    "paris, berlin"),
            ("countries", "france, germany"),
        ],
        "analogy": ANALOGY_EXAMPLES[1],   # paris − france + germany ≈ berlin
    },
]


# In-app reference shown when the user clicks the "Theory" button.
# Static facts about the GloVe-6B-100d release the app loads.
THEORY_HTML = """
<h2>GloVe 100d — quick reference</h2>

<h3>What is "100d"?</h3>
<p>Embedding dimension = <b>100</b>. A hyperparameter chosen at training
time (the same release also ships 50d / 200d / 300d). Same idea as
GPT-2's <code>n_embd = 768</code>: picked, not derived.</p>

<h3>Training corpus ("6B")</h3>
<p>≈ <b>6 billion tokens</b>, concatenation of <b>Wikipedia 2014</b> +
<b>Gigaword 5</b> (English news). Lowercased, tokenized, then trimmed
to the top <b>400 000 most frequent words</b> — that's the vocabulary
this app loads.</p>

<h3>Database size on disk</h3>
<ul>
  <li><code>glove.6B.100d.txt</code> ≈ 347 MB plain text</li>
  <li><code>glove.6B.100d.npz</code> ≈ 165 MB cached
      (= 400 000 × 100 × 4 bytes float32 + word list)</li>
</ul>

<h3>How are the dimensions determined?</h3>
<p>Not analytically — <b>learned by optimization</b>. GloVe builds a
co-occurrence matrix <code>X</code>, where <code>X<sub>ij</sub></code>
counts how often word j appears within a ±10 window of word i across
the entire corpus. Then it learns word vectors <code>w<sub>i</sub></code>
and context vectors <code>w̃<sub>j</sub></code> (plus biases) that
minimize:</p>

<p style="margin-left: 20px;">
<b>Σ<sub>ij</sub>  f(X<sub>ij</sub>) · ( w<sub>i</sub> · w̃<sub>j</sub>
+ b<sub>i</sub> + b̃<sub>j</sub>  −  log X<sub>ij</sub> )²</b>
</p>

<p>So the dot product of two word vectors approximates the log
co-occurrence count. <code>f(X<sub>ij</sub>)</code> is a saturating
weight that prevents "the" / "a" from dominating the loss. AdaGrad
does the optimization. The released embedding is the sum of word +
context vector.</p>

<h3>Why does the geometry work?</h3>
<p><b>Individual dimensions have no preset meaning.</b> Their values
fall out of fitting the objective. The <i>geometry</i> — similar
words near each other,
<code>king − man + woman ≈ queen</code> — is an emergent property of
optimizing log-co-occurrence. Nobody coded a "gender axis" anywhere;
that direction just happens to align with one of the strongest
linear regularities in the corpus.</p>

<p style="color: #888; font-size: 11px;">
Reference: Pennington, Socher &amp; Manning (2014), "GloVe: Global
Vectors for Word Representation". &nbsp;Project page:
nlp.stanford.edu/projects/glove
</p>
"""


# ---------------------------------------------------------------------------
# Backend: GloVe loader + nearest / analogy / projection / pairwise
# ---------------------------------------------------------------------------

@dataclass
class GroupSpec:
    name: str
    words: list[str]   # already filtered to in-vocab, lowercased
    color: str         # hex


class EmbeddingBackend:
    def __init__(self, txt_path: str = GLOVE_TXT, npz_path: str = GLOVE_NPZ):
        if os.path.exists(npz_path):
            print(f"Loading cached GloVe from {npz_path} ...", flush=True)
            with np.load(npz_path, allow_pickle=True) as z:
                self.words: list[str] = list(z["words"])
                self.vectors: np.ndarray = z["vectors"].astype(np.float32)
        elif os.path.exists(txt_path):
            print(f"Parsing GloVe text {txt_path} (one-time, will cache) ...",
                  flush=True)
            self.words, self.vectors = self._parse_txt(txt_path)
            os.makedirs(os.path.dirname(npz_path), exist_ok=True)
            np.savez(npz_path,
                     words=np.array(self.words, dtype=object),
                     vectors=self.vectors)
            print(f"Cached numpy version → {npz_path}", flush=True)
        else:
            os.makedirs(DATA_DIR, exist_ok=True)
            raise FileNotFoundError(_missing_glove_message())

        self.dim = int(self.vectors.shape[1])
        self.idx: dict[str, int] = {w: i for i, w in enumerate(self.words)}
        # Precompute L2-normalized vectors for fast cosine.
        norms = np.linalg.norm(self.vectors, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        self.unit = (self.vectors / norms).astype(np.float32)
        print(f"GloVe ready: vocab={len(self.words)} dim={self.dim}",
              flush=True)

    @staticmethod
    def _parse_txt(path: str) -> tuple[list[str], np.ndarray]:
        words: list[str] = []
        rows: list[np.ndarray] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip().split(" ")
                # Format: word v1 v2 ... vN
                words.append(parts[0])
                rows.append(np.asarray(parts[1:], dtype=np.float32))
        return words, np.stack(rows)

    # -- lookup / similarity ----------------------------------------------

    def vector(self, word: str) -> np.ndarray | None:
        i = self.idx.get(word.lower())
        return None if i is None else self.vectors[i]

    def nearest(self, word: str, k: int = 8,
                metric: str = "cosine") -> list[tuple[str, float]]:
        v = self.vector(word)
        if v is None:
            return []
        if metric == "cosine":
            uv = v / (np.linalg.norm(v) + 1e-12)
            scores = self.unit @ uv          # (vocab,) higher = closer
            return self._top_excluding(scores, k, {word.lower()},
                                       descending=True)
        if metric == "euclidean":
            dists = np.linalg.norm(self.vectors - v, axis=1)
            return self._top_excluding(dists, k, {word.lower()},
                                       descending=False)
        raise ValueError(f"unknown metric: {metric}")

    def analogy(self, a: str, b: str, c: str,
                k: int = 5) -> list[tuple[str, float]]:
        va, vb, vc = self.vector(a), self.vector(b), self.vector(c)
        if va is None or vb is None or vc is None:
            return []
        target = va - vb + vc
        u = target / (np.linalg.norm(target) + 1e-12)
        scores = self.unit @ u
        return self._top_excluding(
            scores, k, {a.lower(), b.lower(), c.lower()}, descending=True)

    def _top_excluding(self, scores: np.ndarray, k: int,
                       exclude: set[str],
                       descending: bool) -> list[tuple[str, float]]:
        # Grab a generous candidate pool (k + |exclude|) then filter.
        pool = k + len(exclude) + 2
        if descending:
            cand = np.argpartition(-scores, pool)[:pool]
            cand = cand[np.argsort(-scores[cand])]
        else:
            cand = np.argpartition(scores, pool)[:pool]
            cand = cand[np.argsort(scores[cand])]
        out: list[tuple[str, float]] = []
        for i in cand:
            w = self.words[i]
            if w in exclude:
                continue
            out.append((w, float(scores[i])))
            if len(out) == k:
                break
        return out

    # -- batch projection helpers -----------------------------------------

    def vectors_for(self, words: list[str]) -> tuple[list[str], np.ndarray]:
        """Return (kept_words, stacked_vectors). Drops OOV silently."""
        kept, rows = [], []
        for w in words:
            v = self.vector(w)
            if v is not None:
                kept.append(w)
                rows.append(v)
        if not rows:
            return [], np.zeros((0, self.dim), dtype=np.float32)
        return kept, np.stack(rows)

    def pca_2d(self, words: list[str]) -> tuple[list[str], np.ndarray]:
        kept, V = self.vectors_for(words)
        if V.shape[0] < 2:
            return kept, np.zeros((V.shape[0], 2), dtype=np.float32)
        from sklearn.decomposition import PCA
        return kept, PCA(n_components=2).fit_transform(V).astype(np.float32)

    def tsne_2d(self, words: list[str], seed: int = 0
                ) -> tuple[list[str], np.ndarray]:
        kept, V = self.vectors_for(words)
        n = V.shape[0]
        if n < 2:
            return kept, np.zeros((n, 2), dtype=np.float32)
        from sklearn.manifold import TSNE
        # t-SNE requires perplexity < n. For small n, scale it down.
        perplexity = max(2.0, min(30.0, (n - 1) / 3))
        proj = TSNE(n_components=2, random_state=seed,
                    perplexity=perplexity, init="pca",
                    learning_rate="auto").fit_transform(V)
        return kept, proj.astype(np.float32)

    def pairwise_cosine(self, words: list[str]
                        ) -> tuple[list[str], np.ndarray]:
        kept, V = self.vectors_for(words)
        if V.shape[0] == 0:
            return kept, np.zeros((0, 0), dtype=np.float32)
        norms = np.linalg.norm(V, axis=1, keepdims=True)
        U = V / np.where(norms == 0, 1.0, norms)
        return kept, (U @ U.T).astype(np.float32)


# ---------------------------------------------------------------------------
# Panel renderers
# ---------------------------------------------------------------------------

def render_scatter(backend: EmbeddingBackend, groups: list[GroupSpec],
                   method: str, fig: Figure,
                   analogy: tuple[str, str, str, str] | None = None,
                   analogy_style: str = "colored") -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    all_words = [w for g in groups for w in g.words]
    if not all_words:
        ax.text(0.5, 0.5, "(no words configured)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="#888")
        ax.set_axis_off()
        return

    if method == "PCA":
        kept, proj = backend.pca_2d(all_words)
        subtitle = "linear projection — distances and angles are honest"
    else:
        kept, proj = backend.tsne_2d(all_words)
        subtitle = ("non-linear; clusters look cleaner but distances "
                    "between clusters are NOT meaningful")

    pos = {w: proj[i] for i, w in enumerate(kept)}
    for g in groups:
        pts = np.array([pos[w] for w in g.words if w in pos])
        if pts.size == 0:
            continue
        ax.scatter(pts[:, 0], pts[:, 1], c=g.color, s=110,
                   label=g.name, edgecolor="black", lw=0.6, zorder=3)
        for w in g.words:
            if w in pos:
                p = pos[w]
                ax.annotate(w, (p[0], p[1]), xytext=(6, 6),
                            textcoords="offset points",
                            fontsize=10, fontweight="bold",
                            color=g.color)

    if analogy is not None:
        _draw_analogy_chain(ax, pos, analogy, method, style=analogy_style)

    ax.legend(loc="best", framealpha=0.9, fontsize=10)
    ax.set_title(f"2D projection of configured words  ({method})\n{subtitle}",
                 fontweight="bold", loc="left", fontsize=11)
    ax.grid(alpha=0.3)
    fig.tight_layout()


def _draw_analogy_chain(ax, pos: dict[str, np.ndarray],
                        analogy: tuple[str, str, str, str],
                        method: str, style: str = "colored") -> None:
    """Overlay A − B + C decomposed as three tail-to-head arrows
    (origin → A, A → A−B, A−B → A−B+C). Only meaningful in PCA: the
    projection is linear, so `proj(A) − proj(B) + proj(C)` equals
    `proj(A − B + C)` up to centering, and the chain endpoint lands
    near proj(D) exactly when the analogy holds. t-SNE is non-linear,
    so the arithmetic would mislead — draw a faint A↔D pointer instead.

    style:
      "colored" — preset palette (grey / red / green) with a legend entry.
      "mono"    — all-grey arrows, no legend entry. Used for the ad-hoc
                  chain driven by the Compute button.
    """
    a, b, c, d = analogy
    if any(w not in pos for w in (a, b, c, d)):
        return
    pA = np.asarray(pos[a], dtype=float)
    pB = np.asarray(pos[b], dtype=float)
    pC = np.asarray(pos[c], dtype=float)
    pD = np.asarray(pos[d], dtype=float)

    if method != "PCA":
        ax.plot([pA[0], pD[0]], [pA[1], pD[1]],
                linestyle=":", color="#888", lw=1.2, alpha=0.8, zorder=2)
        return

    p1 = pA - pB
    p2 = pA - pB + pC
    origin = np.zeros(2)

    # Scatter-only autoscale doesn't see annotate() arrow endpoints, so
    # chain points outside the current view get clipped. Expand limits
    # to contain origin, both intermediate points, and the endpoint.
    chain_pts = np.stack([origin, pA, p1, p2, pD])
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    xs, ys = chain_pts[:, 0], chain_pts[:, 1]
    pad_x = 0.08 * max(xs.max() - xs.min(), 1e-6)
    pad_y = 0.08 * max(ys.max() - ys.min(), 1e-6)
    ax.set_xlim(min(xmin, xs.min() - pad_x), max(xmax, xs.max() + pad_x))
    ax.set_ylim(min(ymin, ys.min() - pad_y), max(ymax, ys.max() + pad_y))

    if style == "mono":
        c_base = c_sub = c_add = "#888"
        lw_base, lw_sub, lw_add = 1.4, 1.6, 1.6
        alpha_base = 0.65
        star_face, star_edge = "#bbb", "#666"
        star_label: str | None = None
        link_color = "#888"
        label_color = "#444"
    else:
        c_base, c_sub, c_add = "#666", "#C44E52", "#55A868"
        lw_base, lw_sub, lw_add = 1.4, 2.2, 2.2
        alpha_base = 0.65
        star_face, star_edge = "gold", "black"
        star_label = f"{a} − {b} + {c}"
        link_color = "#333"
        label_color = "#333"

    # Arrow 1: origin → A. Thinner so the +/− steps stand out.
    ax.annotate("", xy=pA, xytext=origin,
                arrowprops=dict(arrowstyle="-|>", color=c_base,
                                lw=lw_base, alpha=alpha_base,
                                mutation_scale=16),
                zorder=4)
    _chain_label(ax, origin, pA, f"+{a}", c_base,
                 italic=True, fontweight="normal")

    # Arrow 2: A → A−B (subtraction).
    ax.annotate("", xy=p1, xytext=pA,
                arrowprops=dict(arrowstyle="-|>", color=c_sub,
                                lw=lw_sub, mutation_scale=20),
                zorder=5)
    _chain_label(ax, pA, p1, f"−{b}", c_sub)

    # Arrow 3: A−B → A−B+C (addition).
    ax.annotate("", xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle="-|>", color=c_add,
                                lw=lw_add, mutation_scale=20),
                zorder=5)
    _chain_label(ax, p1, p2, f"+{c}", c_add)

    star_kwargs = dict(marker="*", markersize=22,
                       markerfacecolor=star_face, markeredgecolor=star_edge,
                       markeredgewidth=1.3, zorder=10)
    if star_label is not None:
        star_kwargs["label"] = star_label
    ax.plot(p2[0], p2[1], **star_kwargs)
    # Residual: chain endpoint vs. the real D vector.
    ax.plot([p2[0], pD[0]], [p2[1], pD[1]],
            linestyle="--", color=link_color, lw=1.2, alpha=0.8, zorder=4)
    ax.annotate(f"≈ {d}?", xy=pD, xytext=(10, -12),
                textcoords="offset points", fontsize=10,
                fontweight="bold", color=label_color,
                bbox=dict(boxstyle="round,pad=0.25",
                          facecolor="white", alpha=0.85,
                          edgecolor="#888"),
                zorder=11)


def _chain_label(ax, p_from: np.ndarray, p_to: np.ndarray,
                 text: str, color: str,
                 italic: bool = False, fontweight: str = "bold") -> None:
    mid = (np.asarray(p_from, float) + np.asarray(p_to, float)) / 2
    ax.text(mid[0], mid[1], f" {text}", fontsize=10, color=color,
            fontweight=fontweight,
            fontstyle="italic" if italic else "normal",
            ha="left", va="bottom", zorder=11)


def render_similarity_matrix(backend: EmbeddingBackend,
                             groups: list[GroupSpec], fig: Figure) -> None:
    fig.clear()
    ax = fig.add_subplot(111)

    ordered_words: list[str] = []
    word_colors: list[str] = []
    breaks = [0]
    for g in groups:
        for w in g.words:
            ordered_words.append(w)
            word_colors.append(g.color)
        breaks.append(len(ordered_words))

    if not ordered_words:
        ax.text(0.5, 0.5, "(no words configured)",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color="#888")
        ax.set_axis_off()
        return

    _, M = backend.pairwise_cosine(ordered_words)
    n = len(ordered_words)
    im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1,
                   interpolation="nearest")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(ordered_words, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(ordered_words, fontsize=9)
    for tick, c in zip(ax.get_xticklabels(), word_colors):
        tick.set_color(c)
        tick.set_fontweight("bold")
    for tick, c in zip(ax.get_yticklabels(), word_colors):
        tick.set_color(c)
        tick.set_fontweight("bold")
    # Group separators between blocks (not at the borders).
    for b in breaks[1:-1]:
        ax.axhline(b - 0.5, color="black", lw=1.4)
        ax.axvline(b - 0.5, color="black", lw=1.4)
    if n <= 16:
        for i in range(n):
            for j in range(n):
                v = M[i, j]
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        fontsize=7,
                        color="white" if abs(v) > 0.55 else "black")
    fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02,
                 label="cosine similarity")
    ax.set_title("Pairwise cosine similarity  —  blocks reveal taxonomy",
                 fontweight="bold", loc="left", fontsize=11)
    fig.tight_layout()


def render_cos_vs_euc(backend: EmbeddingBackend, anchor: str,
                      k: int, fig: Figure) -> None:
    fig.clear()
    if backend.vector(anchor) is None:
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, f"OOV anchor: {anchor!r}",
                ha="center", va="center", transform=ax.transAxes)
        ax.set_axis_off()
        return

    cos_top = backend.nearest(anchor, k, metric="cosine")
    euc_top = backend.nearest(anchor, k, metric="euclidean")
    ax1 = fig.add_subplot(121)
    ax2 = fig.add_subplot(122)

    def _bar(ax, top, title, xlabel, color):
        ws = [w for w, _ in top]
        ss = [s for _, s in top]
        y = np.arange(len(ws))
        ax.barh(y, ss, color=color, edgecolor="black", lw=0.4)
        ax.set_yticks(y)
        ax.set_yticklabels(ws, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_title(title, fontsize=10, fontweight="bold", loc="left")
        for yi, si in zip(y, ss):
            ax.text(si, yi, f"  {si:.2f}", va="center", fontsize=8)
        ax.grid(axis="x", alpha=0.3)

    _bar(ax1, cos_top, f"cosine — nearest to {anchor!r}",
         "cosine similarity", "#4C72B0")
    _bar(ax2, euc_top, f"euclidean — nearest to {anchor!r}",
         "L2 distance",       "#DD8452")
    fig.suptitle(
        "Cosine ranks by direction; Euclidean is dragged around by the "
        "norm.\nThat's why transformer-era work uses cosine.",
        fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.88))


# ---------------------------------------------------------------------------
# Qt app
# ---------------------------------------------------------------------------

class EmbeddingWorkshop(QMainWindow):
    def __init__(self, backend: EmbeddingBackend):
        super().__init__()
        self.backend = backend
        self.setWindowTitle("Embedding Workshop  —  GloVe 100d")
        self.resize(1500, 1000)
        # Preset state: None while user-edited groups are shown; a preset
        # key while one is active. The snapshot holds the user's table
        # contents verbatim so unchecking restores them exactly.
        self._active_preset: str | None = None
        self._saved_groups: list[tuple[str, str]] | None = None
        # Ad-hoc analogy chain driven by the Compute button: (a, b, c, d)
        # with d = top-1 candidate. Click again with identical inputs to
        # hide; different inputs refresh. Preset takes display priority.
        self._compute_analogy: tuple[str, str, str, str] | None = None
        self._build_ui()
        self._on_update()

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        outer = QHBoxLayout(central)
        outer.setContentsMargins(4, 4, 4, 4)

        splitter = QSplitter(Qt.Horizontal)
        outer.addWidget(splitter, stretch=1)

        # ---------- left column: inputs ----------
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(8, 8, 8, 8)
        splitter.addWidget(left)

        # 1. Word groups table — header row pairs the title with the Theory button
        header_row = QHBoxLayout()
        header_row.addWidget(QLabel("<b>Word groups</b>  "
                                    "<span style='color:#888'>"
                                    "(colors auto-assigned by row)</span>"))
        header_row.addStretch(1)
        theory_btn = QPushButton("ℹ Theory")
        theory_btn.setToolTip("What GloVe is, how it was trained, "
                              "what '100d' / '6B' mean.")
        theory_btn.clicked.connect(self._show_theory)
        header_row.addWidget(theory_btn)
        left_layout.addLayout(header_row)
        self._theory_dialog: QDialog | None = None
        self.groups_table = QTableWidget(0, 3)
        self.groups_table.setHorizontalHeaderLabels(
            ["name", "words (comma-separated)", "color"])
        hdr = self.groups_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        for name, words in DEFAULT_GROUPS:
            self._append_group_row(name, words)
        left_layout.addWidget(self.groups_table, stretch=2)

        # Row buttons
        bb = QHBoxLayout()
        add_btn = QPushButton("+ Add row")
        add_btn.clicked.connect(self._on_add_row)
        rm_btn = QPushButton("− Remove selected")
        rm_btn.clicked.connect(self._on_remove_row)
        upd_btn = QPushButton("Update visualizations")
        upd_btn.setStyleSheet("font-weight: bold;")
        upd_btn.clicked.connect(self._on_update)
        bb.addWidget(add_btn)
        bb.addWidget(rm_btn)
        bb.addStretch(1)
        bb.addWidget(upd_btn)
        left_layout.addLayout(bb)

        # Analogy presets — mutually exclusive checkboxes. Checking one
        # snapshots the user's groups, loads the preset set, and enables
        # the chain-arrow overlay on the scatter. Unchecking restores.
        presets_row = QHBoxLayout()
        presets_row.addWidget(QLabel("<b>Analogy preset:</b>"))
        self.preset_checks: dict[str, QCheckBox] = {}
        for preset in ANALOGY_PRESETS:
            cb = QCheckBox(preset["label"])
            cb.setToolTip(
                f"Swap the table for the {preset['label']} groups and "
                "draw the chain arrow on the 2D scatter. "
                "Uncheck to restore the previous groups.")
            cb.stateChanged.connect(
                lambda _s, k=preset["key"]: self._on_preset_toggle(k))
            presets_row.addWidget(cb)
            self.preset_checks[preset["key"]] = cb
        presets_row.addStretch(1)
        left_layout.addLayout(presets_row)

        # Reduction method + cosine-vs-euclidean toggle
        meth = QHBoxLayout()
        meth.addWidget(QLabel("2D projection:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["PCA", "t-SNE"])
        self.method_combo.currentIndexChanged.connect(self._on_update)
        meth.addWidget(self.method_combo)
        meth.addStretch(1)
        self.cve_check = QCheckBox("Cosine vs Euclidean")
        self.cve_check.stateChanged.connect(self._on_cve_toggle)
        meth.addWidget(self.cve_check)
        left_layout.addLayout(meth)

        # OOV / status line
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #b35900; font-size: 11px;")
        self.status_label.setWordWrap(True)
        left_layout.addWidget(self.status_label)

        left_layout.addSpacing(10)

        # 2. Word inspector
        left_layout.addWidget(QLabel("<b>Word inspector</b>  "
                                     "<span style='color:#888'>"
                                     "(top-k nearest by cosine)</span>"))
        ins = QHBoxLayout()
        self.inspector_edit = QLineEdit("cat")
        self.inspector_edit.returnPressed.connect(self._on_inspect)
        ins.addWidget(self.inspector_edit)
        self.k_combo = QComboBox()
        for v in (5, 8, 10, 15, 20):
            self.k_combo.addItem(f"top-{v}", v)
        self.k_combo.setCurrentIndex(1)
        ins.addWidget(self.k_combo)
        ins_btn = QPushButton("Lookup")
        ins_btn.clicked.connect(self._on_inspect)
        ins.addWidget(ins_btn)
        left_layout.addLayout(ins)
        self.inspector_output = QPlainTextEdit("(neighbors will appear here)")
        self.inspector_output.setReadOnly(True)
        self.inspector_output.setStyleSheet(
            "QPlainTextEdit { font-family: monospace; font-size: 11px; "
            "background: #fafafa; color: #222; }")
        self.inspector_output.setMinimumHeight(160)
        left_layout.addWidget(self.inspector_output)

        left_layout.addSpacing(10)

        # 3. Analogy
        left_layout.addWidget(QLabel("<b>Analogy:</b>  "
                                     "<span style='color:#888'>"
                                     "A − B + C = ?</span>"))
        an = QHBoxLayout()
        self.an_a = QLineEdit("king")
        self.an_b = QLineEdit("man")
        self.an_c = QLineEdit("woman")
        for w in (self.an_a, self.an_b, self.an_c):
            w.setMaximumWidth(90)
            w.returnPressed.connect(self._on_analogy)
        an.addWidget(self.an_a)
        an.addWidget(QLabel(" − "))
        an.addWidget(self.an_b)
        an.addWidget(QLabel(" + "))
        an.addWidget(self.an_c)
        an.addWidget(QLabel(" = ?"))
        an.addStretch(1)
        an_btn = QPushButton("Compute")
        an_btn.clicked.connect(self._on_analogy)
        an.addWidget(an_btn)
        left_layout.addLayout(an)

        # Inline hints — two canonical analogies (Mikolov 2013).
        examples_text = "  ·  ".join(
            f"{a} − {b} + {c} ≈ {d}" for a, b, c, d in ANALOGY_EXAMPLES)
        ex_label = QLabel(f"e.g.  {examples_text}")
        ex_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        ex_label.setWordWrap(True)
        left_layout.addWidget(ex_label)
        self.analogy_output = QPlainTextEdit("(answers will appear here)")
        self.analogy_output.setReadOnly(True)
        self.analogy_output.setStyleSheet(
            "QPlainTextEdit { font-family: monospace; font-size: 11px; "
            "background: #fafafa; color: #222; }")
        self.analogy_output.setMinimumHeight(120)
        left_layout.addWidget(self.analogy_output)

        left_layout.addStretch(1)

        # ---------- right column: visualizations ----------
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 4, 4, 4)
        splitter.addWidget(right)

        self.fig_scatter = Figure(figsize=(8, 5), dpi=100)
        self.canvas_scatter = FigureCanvas(self.fig_scatter)
        right_layout.addWidget(self.canvas_scatter, stretch=3)

        self.fig_sim = Figure(figsize=(8, 5), dpi=100)
        self.canvas_sim = FigureCanvas(self.fig_sim)
        right_layout.addWidget(self.canvas_sim, stretch=3)

        self.fig_cve = Figure(figsize=(8, 3), dpi=100)
        self.canvas_cve = FigureCanvas(self.fig_cve)
        right_layout.addWidget(self.canvas_cve, stretch=2)
        self.canvas_cve.setVisible(False)

        splitter.setSizes([420, 1080])

    # -- table helpers ----------------------------------------------------

    def _append_group_row(self, name: str, words: str) -> None:
        row = self.groups_table.rowCount()
        self.groups_table.insertRow(row)
        self.groups_table.setItem(row, 0, QTableWidgetItem(name))
        self.groups_table.setItem(row, 1, QTableWidgetItem(words))
        self._set_color_cell(row)

    def _set_color_cell(self, row: int) -> None:
        color = COLOR_PALETTE[row % len(COLOR_PALETTE)]
        item = QTableWidgetItem(color)
        item.setBackground(QColor(color))
        item.setForeground(QColor("white"))
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setTextAlignment(Qt.AlignCenter)
        self.groups_table.setItem(row, 2, item)

    def _refresh_color_cells(self) -> None:
        for row in range(self.groups_table.rowCount()):
            self._set_color_cell(row)

    def _read_groups(self) -> list[GroupSpec]:
        groups: list[GroupSpec] = []
        all_oov: list[str] = []
        for row in range(self.groups_table.rowCount()):
            name_item = self.groups_table.item(row, 0)
            words_item = self.groups_table.item(row, 1)
            if name_item is None or words_item is None:
                continue
            name = name_item.text().strip() or f"group{row}"
            raw = words_item.text()
            words = [w.strip().lower() for w in raw.split(",") if w.strip()]
            if not words:
                continue
            color = COLOR_PALETTE[row % len(COLOR_PALETTE)]
            kept: list[str] = []
            for w in words:
                if self.backend.vector(w) is None:
                    all_oov.append(w)
                else:
                    kept.append(w)
            if kept:
                groups.append(GroupSpec(name=name, words=kept, color=color))
        if all_oov:
            self.status_label.setText(
                f"OOV (skipped): {', '.join(repr(w) for w in all_oov)}")
        else:
            self.status_label.setText("")
        return groups

    # -- handlers ---------------------------------------------------------

    def _on_add_row(self) -> None:
        self._append_group_row("group", "")

    def _on_remove_row(self) -> None:
        row = self.groups_table.currentRow()
        if row < 0:
            row = self.groups_table.rowCount() - 1
        if row >= 0:
            self.groups_table.removeRow(row)
            self._refresh_color_cells()

    # -- analogy preset handlers -----------------------------------------

    def _on_preset_toggle(self, key: str) -> None:
        checked = self.preset_checks[key].isChecked()
        if checked:
            # Snapshot the user's groups on first activation only — if a
            # different preset is already on, we want the ORIGINAL user
            # table back when everything is unchecked, not the previous
            # preset.
            if self._active_preset is None:
                self._saved_groups = self._snapshot_groups()
            for k, cb in self.preset_checks.items():
                if k != key and cb.isChecked():
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)
            self._load_preset_groups(key)
            self._active_preset = key
        else:
            if self._active_preset == key:
                self._restore_saved_groups()
                self._active_preset = None
        self._on_update()

    def _snapshot_groups(self) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = []
        for r in range(self.groups_table.rowCount()):
            name_item = self.groups_table.item(r, 0)
            words_item = self.groups_table.item(r, 1)
            name = name_item.text() if name_item is not None else ""
            words = words_item.text() if words_item is not None else ""
            rows.append((name, words))
        return rows

    def _load_preset_groups(self, key: str) -> None:
        preset = next(p for p in ANALOGY_PRESETS if p["key"] == key)
        self.groups_table.setRowCount(0)
        for name, words in preset["groups"]:
            self._append_group_row(name, words)

    def _restore_saved_groups(self) -> None:
        self.groups_table.setRowCount(0)
        for name, words in (self._saved_groups or []):
            self._append_group_row(name, words)
        self._saved_groups = None

    def _active_analogy(self) -> tuple[tuple[str, str, str, str], str] | None:
        """Return (analogy_tuple, style) for the scatter overlay, or None.

        Preset takes display priority; otherwise a Compute-driven chain
        renders in mono-grey without a legend entry.
        """
        if self._active_preset is not None:
            preset = next(p for p in ANALOGY_PRESETS
                          if p["key"] == self._active_preset)
            return preset["analogy"], "colored"
        if self._compute_analogy is not None:
            return self._compute_analogy, "mono"
        return None

    # -- main refresh ----------------------------------------------------

    def _on_update(self) -> None:
        groups = self._read_groups()
        method = self.method_combo.currentText()
        active = self._active_analogy()
        analogy, style = (None, "colored") if active is None else active

        # Auto-inject A, B, C, D into the scatter if they aren't already
        # in a user group — otherwise the chain has no anchor points to
        # draw to. Preset groups already include everything.
        if analogy is not None:
            present = {w for g in groups for w in g.words}
            extra = [w for w in analogy
                     if w not in present
                     and self.backend.vector(w) is not None]
            if extra:
                color = COLOR_PALETTE[len(groups) % len(COLOR_PALETTE)]
                groups.append(GroupSpec(name="analogy",
                                        words=extra, color=color))

        render_scatter(self.backend, groups, method, self.fig_scatter,
                       analogy=analogy, analogy_style=style)
        render_similarity_matrix(self.backend, groups, self.fig_sim)
        self.canvas_scatter.draw_idle()
        self.canvas_sim.draw_idle()
        if self.cve_check.isChecked():
            self._refresh_cve(groups)

    def _on_inspect(self) -> None:
        word = self.inspector_edit.text().strip().lower()
        k = int(self.k_combo.currentData())
        if not word:
            return
        if self.backend.vector(word) is None:
            self.inspector_output.setPlainText(f"OOV:  {word!r}")
            return
        top = self.backend.nearest(word, k, metric="cosine")
        lines = [f"Top-{k} nearest to {word!r}  (cosine):", ""]
        for w, s in top:
            lines.append(f"  {w:20s}  {s:.3f}")
        self.inspector_output.setPlainText("\n".join(lines))

    def _on_analogy(self) -> None:
        a = self.an_a.text().strip().lower()
        b = self.an_b.text().strip().lower()
        c = self.an_c.text().strip().lower()
        missing = [w for w in (a, b, c) if not w
                   or self.backend.vector(w) is None]
        if missing:
            self.analogy_output.setPlainText(
                f"OOV / empty:  {', '.join(repr(w) for w in missing)}")
            return
        top = self.backend.analogy(a, b, c, k=5)
        lines = [f"{a!r} − {b!r} + {c!r}  ≈", ""]
        for w, s in top:
            lines.append(f"  {w:20s}  {s:.3f}")
        self.analogy_output.setPlainText("\n".join(lines))

        # Toggle the ad-hoc chain overlay on the 2D scatter. Same (a, b, c)
        # twice → hide; different inputs → refresh. Kept independent of
        # the preset chain (preset wins when both are "active"), so
        # playing with Compute doesn't silently clobber a preset choice.
        current = (a, b, c)
        if (self._compute_analogy is not None
                and self._compute_analogy[:3] == current):
            self._compute_analogy = None
        else:
            d = top[0][0] if top else ""
            self._compute_analogy = (a, b, c, d)
        self._on_update()

    def _on_cve_toggle(self) -> None:
        on = self.cve_check.isChecked()
        self.canvas_cve.setVisible(on)
        if on:
            self._refresh_cve(self._read_groups())

    def _show_theory(self) -> None:
        # Re-show the same dialog if it's still around (so multiple clicks
        # don't stack windows). Otherwise build it fresh.
        if self._theory_dialog is not None:
            self._theory_dialog.show()
            self._theory_dialog.raise_()
            self._theory_dialog.activateWindow()
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("GloVe — quick reference")
        dlg.resize(620, 720)
        dlg.setModal(False)
        v = QVBoxLayout(dlg)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(THEORY_HTML)
        v.addWidget(browser)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(dlg.reject)
        bb.accepted.connect(dlg.accept)
        v.addWidget(bb)

        def _clear():
            self._theory_dialog = None
        dlg.finished.connect(lambda _code: _clear())
        self._theory_dialog = dlg
        dlg.show()

    def _refresh_cve(self, groups: list[GroupSpec]) -> None:
        # Use the first word of the first non-empty group as anchor.
        anchor = next((g.words[0] for g in groups if g.words), None)
        if anchor is None:
            return
        render_cos_vs_euc(self.backend, anchor, k=8, fig=self.fig_cve)
        self.canvas_cve.draw_idle()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embedding workshop (GloVe 100d).")
    parser.add_argument(
        "--fetch-glove", action="store_true",
        help=("Download glove.6B.zip from the HF mirror "
              f"({HF_GLOVE_REPO}) and extract glove.6B.100d.txt into "
              f"{DATA_DIR}. Skips if the file is already present."))
    args = parser.parse_args()

    if args.fetch_glove:
        fetch_glove_from_hf()
        return

    try:
        backend = EmbeddingBackend()
    except FileNotFoundError as exc:
        print(str(exc))
        sys.exit(1)
    app = QApplication(sys.argv)
    win = EmbeddingWorkshop(backend)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
