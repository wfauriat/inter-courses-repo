"""
build_interactive_embedding_svg.py
==================================

Regenerate interactive_talk/resources/embedding.svg from GloVe-100d vectors.

Four semantic clusters (animals, action-verbs, stats-terms, royalty) are
toggled as SVG layers by the interactive viewer — their `id`s must match
the `show` lists in interactive_talk/tree.json.

PCA is fit once on a large corpus sample (top-N most frequent GloVe words),
then the display words (clusters + background) are *transformed* through
those frozen axes. This matters: refitting PCA when you add/remove display
words rotates the view. Fixing the axes on a representative corpus gives
a stable, vocabulary-wide coordinate system that isn't over-fit to the
handful of words we happen to be plotting.
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from embedding_workshop import EmbeddingBackend


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
OUT_SVG    = os.path.join(REPO_ROOT, "interactive_talk", "resources",
                          "embedding.svg")

# (layer_id, words, fill color). IDs must match tree.json `show` lists.
CLUSTERS: list[tuple[str, list[str], str]] = [
    ("animals",     ["cat", "dog", "fish", "bird"],                           "#DD8452"),
    ("verbs",       ["predict", "simulate", "compute", "estimate"],           "#C44E52"),
    ("stats-terms", ["probability", "variance", "posterior", "distribution"], "#4C72B0"),
    ("royalty",     ["king", "queen", "prince", "princess"],                  "#55A868"),
]

# Diverse, non-overlapping-with-clusters words to populate the background.
# Avoid high-frequency function words ("the", "and") — they collapse
# toward the corpus mean and squash the PCA spread of everything else.
BACKGROUND_WORDS = [
    "building", "river", "music", "color", "mountain", "chair", "window",
    "silence", "paper", "machine", "garden", "storm", "bread", "road",
    "painting", "forest", "stone", "metal", "ocean", "shadow",
    "engine", "clock", "book", "letter", "star", "glass", "harvest",
    "copper", "marble", "thread",
]

WIDTH, HEIGHT = 720, 500
MARGIN_L, MARGIN_R = 60, 40
MARGIN_T, MARGIN_B = 50, 50
PAD_FRAC = 0.08    # extra padding around data bounds, fraction of span

# Number of most-frequent GloVe words used to fit the PCA axes. GloVe's
# vocabulary file is sorted by corpus frequency (row 0 = "the"), so
# vectors[:N] gives the top-N words. The full 400k vocab is dominated by
# numbers, proper nouns, and rare tokens — fitting on it gives a PC1 that
# mostly separates common-English content words from that tail, which
# collapses all our display words onto one side. Top-10k is a more natural
# "English vocabulary" subset, and the first couple of PCs land on
# semantically interpretable directions.
PCA_FIT_N = 10_000

BG_COLOR        = "#2a2a2a"
AXIS_COLOR      = "#777"
TITLE_COLOR     = "#b8b8b8"
BG_POINT_COLOR  = "#555"
LABEL_COLOR     = "#e8e8e8"


def run_pca(backend: EmbeddingBackend) -> tuple[dict[str, np.ndarray], list[str]]:
    """Fit PCA on the top-N GloVe vocabulary, then transform the display
    words through those frozen axes. Returns (word → 2D position,
    OOV-words-dropped).
    """
    from sklearn.decomposition import PCA

    n_fit = min(PCA_FIT_N, backend.vectors.shape[0])
    print(f"Fitting PCA on top-{n_fit} GloVe vocab ...", flush=True)
    pca = PCA(n_components=2).fit(backend.vectors[:n_fit])
    ev = pca.explained_variance_ratio_
    print(f"  PC1 explains {ev[0]*100:.1f}% of variance; "
          f"PC2 explains {ev[1]*100:.1f}%.")

    all_words: list[str] = list(BACKGROUND_WORDS)
    for _, words, _ in CLUSTERS:
        all_words.extend(words)
    kept, V = backend.vectors_for(all_words)
    oov = [w for w in all_words if w not in set(kept)]

    proj = pca.transform(V).astype(np.float32)
    return {w: proj[i] for i, w in enumerate(kept)}, oov


def map_to_pixels(pos: dict[str, np.ndarray]
                  ) -> tuple[dict[str, tuple[float, float]], tuple[float, float]]:
    """Map PCA-space to SVG pixels. Returns (pixel positions, origin pixel).

    x and y are independently rescaled to fill the plot rectangle (distorts
    aspect ratio, same as matplotlib's default); origin-of-PCA-space is
    mapped through so axes can be drawn at the true PC=0 lines.
    """
    arr = np.array(list(pos.values()))
    xmin, ymin = arr.min(axis=0)
    xmax, ymax = arr.max(axis=0)
    # Guarantee origin (PC=0) sits inside the viewport so the PC1/PC2 axis
    # lines we draw don't clip off the edge of the plot.
    xmin = min(xmin, 0.0); xmax = max(xmax, 0.0)
    ymin = min(ymin, 0.0); ymax = max(ymax, 0.0)
    xpad = (xmax - xmin) * PAD_FRAC
    ypad = (ymax - ymin) * PAD_FRAC
    xmin -= xpad; xmax += xpad
    ymin -= ypad; ymax += ypad

    px_x_min = MARGIN_L
    px_x_max = WIDTH - MARGIN_R
    px_y_min = MARGIN_T
    px_y_max = HEIGHT - MARGIN_B

    def to_px(x: float, y: float) -> tuple[float, float]:
        px = px_x_min + (x - xmin) / (xmax - xmin) * (px_x_max - px_x_min)
        # SVG y grows downward; PCA y grows upward — flip.
        py = px_y_max - (y - ymin) / (ymax - ymin) * (px_y_max - px_y_min)
        return px, py

    mapped = {w: to_px(float(p[0]), float(p[1])) for w, p in pos.items()}
    origin_px = to_px(0.0, 0.0)
    return mapped, origin_px


def build_svg(pos: dict[str, tuple[float, float]],
              origin_px: tuple[float, float]) -> str:
    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Iosevka, \'JetBrains Mono\', monospace">')
    lines.append('  <!--')
    lines.append('    Generated by workspace/build_interactive_embedding_svg.py from')
    lines.append('    GloVe-100d (Pennington, Socher & Manning 2014). Projected to 2D')
    lines.append('    via PCA over the union of clusters + a neutral background word')
    lines.append('    list. Edit the script and regenerate; do not hand-edit this SVG.')
    lines.append('  -->')
    lines.append(
        f'  <text x="{WIDTH // 2}" y="28" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="15" font-weight="500">')
    lines.append('    Token embedding space (2D projection)')
    lines.append('  </text>')

    # Background grid
    lines.append(f'  <g stroke="{BG_COLOR}" stroke-width="1" fill="none">')
    for x in range(MARGIN_L, WIDTH - MARGIN_R + 1, 120):
        lines.append(f'    <line x1="{x}" y1="{MARGIN_T}" x2="{x}" y2="{HEIGHT - MARGIN_B}"/>')
    for y in range(MARGIN_T, HEIGHT - MARGIN_B + 1, 100):
        lines.append(f'    <line x1="{MARGIN_L}" y1="{y}" x2="{WIDTH - MARGIN_R}" y2="{y}"/>')
    lines.append('  </g>')

    # Axes at PC=0
    ox, oy = origin_px
    lines.append(f'  <g stroke="{AXIS_COLOR}" stroke-width="1.2" fill="none">')
    lines.append(f'    <line x1="{MARGIN_L}" y1="{oy:.1f}" x2="{WIDTH - MARGIN_R}" y2="{oy:.1f}"/>')
    lines.append(f'    <line x1="{ox:.1f}" y1="{MARGIN_T}" x2="{ox:.1f}" y2="{HEIGHT - MARGIN_B}"/>')
    lines.append('  </g>')
    lines.append(
        f'  <text x="{WIDTH - MARGIN_R - 8}" y="{oy + 16:.1f}" text-anchor="end" '
        f'fill="#999" font-size="11">PC 1</text>')
    lines.append(
        f'  <text x="{ox + 8:.1f}" y="{MARGIN_T + 12}" text-anchor="start" '
        f'fill="#999" font-size="11">PC 2</text>')

    # Neutral background scatter
    lines.append(f'  <g fill="{BG_POINT_COLOR}" opacity="0.55">')
    for w in BACKGROUND_WORDS:
        if w in pos:
            x, y = pos[w]
            lines.append(f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>')
    lines.append('  </g>')

    # Cluster layers
    for cid, words, color in CLUSTERS:
        lines.append(f'  <g class="layer" id="{cid}">')
        lines.append(f'    <g fill="{color}">')
        for w in words:
            if w in pos:
                x, y = pos[w]
                lines.append(f'      <circle cx="{x:.1f}" cy="{y:.1f}" r="7"/>')
        lines.append('    </g>')
        lines.append(f'    <g fill="{LABEL_COLOR}" font-size="13" font-weight="600">')
        for w in words:
            if w in pos:
                x, y = pos[w]
                lines.append(f'      <text x="{x + 11:.1f}" y="{y + 4:.1f}">{w}</text>')
        lines.append('    </g>')
        lines.append('  </g>')

    lines.append('</svg>')
    return '\n'.join(lines) + '\n'


def main() -> None:
    backend = EmbeddingBackend()
    pos_pca, oov = run_pca(backend)
    if oov:
        print(f"WARN: dropped OOV words: {oov}")
    pos_px, origin_px = map_to_pixels(pos_pca)
    svg = build_svg(pos_px, origin_px)
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_SVG}  "
          f"({len(pos_px)} words, origin at {origin_px[0]:.0f},{origin_px[1]:.0f})")


if __name__ == "__main__":
    main()
