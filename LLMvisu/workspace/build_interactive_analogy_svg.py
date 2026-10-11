"""
build_interactive_analogy_svg.py
================================

Regenerate the analogy figures used in the interactive talk:

  - interactive_talk/resources/embedding_analogy_capital.svg
        paris − france + germany ≈ berlin
  - interactive_talk/resources/embedding_analogy_vehicle.svg
        plane − air + sea ≈ boat

Each figure has its OWN curated PCA fit — on just the pairs relevant to
its analogy — so the top-2 PCs line up with the analogy direction and
the parallelogram looks geometrically clean. Trying to share one basis
across chains left ~60% of the relevant variance out of the view and
made the chains trace long detours.

Each SVG exposes four layers keyed to `tree.json`'s `show` lists:

    {key}-words     the 4 labeled points (A, B, C, D)
    {key}-sub       the A → A−B arrow + faint gray B-vector from origin
    {key}-add       the A−B → A−B+C arrow + faint gray C-vector from origin
    {key}-resolve   gold star at endpoint + dashed residual + "≈ D?"

The origin-anchored gray dashed arrows in -sub / -add reify the "−B" and
"+C" operations as vectors: what they look like when drawn from 0 is the
thing being subtracted / added.
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from embedding_workshop import EmbeddingBackend


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
OUT_DIR    = os.path.join(REPO_ROOT, "interactive_talk", "resources")

# One figure per chain. `fit_words` is the PCA training set — pairs that
# align along the relevant semantic direction. `words` is the specific
# (A, B, C, D) for the chain itself. Background dots use the remaining
# fit words so the viewer can see the analogy pattern replicated by
# other pairs (brother/sister, italy/rome, ...) without clutter from
# labels.
CHAINS: list[dict] = [
    {
        "key":       "capital",
        "words":     ("paris", "france", "germany", "berlin"),
        "color":     "#4C9BD1",
        "out_file":  "embedding_analogy_capital.svg",
        "title":     "Vector arithmetic — capital analogy",
        "fit_words": [
            "france", "paris", "germany", "berlin", "italy", "rome",
            "spain", "madrid", "japan", "tokyo", "england", "london",
            "russia", "moscow", "greece", "athens",
            "portugal", "lisbon", "china", "beijing",
        ],
        "label_offsets": {},
    },
    {
        "key":       "vehicle",
        "words":     ("plane", "air", "sea", "boat"),
        "color":     "#E8935E",
        "out_file":  "embedding_analogy_vehicle.svg",
        "title":     "Vector arithmetic — vehicle / medium",
        # Deliberately narrow: air- and water-vehicle pairs only. Earlier
        # draft mixed in car/road, train/track, truck/highway — the
        # land-vehicle variance pulled PC1/PC2 off the air↔water axis
        # that the plane−air+sea≈boat analogy actually lives on.
        "fit_words": [
            "plane", "air", "boat", "sea",
            "ship", "ocean", "helicopter", "sky",
            "submarine", "water", "jet", "atmosphere",
            "yacht", "lake", "airliner", "clouds",
            "canoe", "river",
        ],
        "label_offsets": {},
    },
]

WIDTH, HEIGHT = 720, 500
MARGIN_L, MARGIN_R = 60, 40
MARGIN_T, MARGIN_B = 50, 50
PAD_FRAC = 0.10

GRID_COLOR      = "#2a2a2a"
AXIS_COLOR      = "#777"
TITLE_COLOR     = "#b8b8b8"
BG_POINT_COLOR  = "#555"
LABEL_COLOR     = "#e8e8e8"
STAR_FILL       = "gold"
STAR_EDGE       = "#222"
RESIDUAL_COLOR  = "#bbb"
ORIGIN_VEC_COLOR = "#888"   # dashed arrows for B / C vectors drawn from 0


# ---------------------------------------------------------------------------
# Compute positions in PCA space
# ---------------------------------------------------------------------------

def run_pca(backend: EmbeddingBackend, chain: dict
            ) -> tuple[dict[str, np.ndarray], list[str]]:
    """Fit PCA on the chain's curated pair corpus, transform the chain
    words + the remaining fit words (used as unlabeled background dots),
    and add the intermediate chain points to the position map.
    """
    from sklearn.decomposition import PCA

    fit_kept, fit_V = backend.vectors_for(chain["fit_words"])
    fit_oov = [w for w in chain["fit_words"] if w not in set(fit_kept)]
    if fit_oov:
        print(f"  [WARN] fit OOV in {chain['key']}: {fit_oov}")
    pca = PCA(n_components=2).fit(fit_V)
    ev = pca.explained_variance_ratio_
    print(f"  [{chain['key']}] PCA on {len(fit_kept)} words  "
          f"PC1 {ev[0]*100:.1f}%   PC2 {ev[1]*100:.1f}%")

    # Project every fit word — chain words we'll label + color, the rest
    # go down as neutral background dots.
    proj = pca.transform(fit_V).astype(np.float32)
    pos: dict[str, np.ndarray] = {w: proj[i] for i, w in enumerate(fit_kept)}

    a, b, c, d = chain["words"]
    if all(w in pos for w in (a, b, c, d)):
        pos[f"{chain['key']}-sub-end"] = pos[a] - pos[b]
        pos[f"{chain['key']}-add-end"] = pos[a] - pos[b] + pos[c]

    chain_word_set = set(chain["words"])
    background_words = [w for w in fit_kept if w not in chain_word_set]
    return pos, background_words


def map_to_pixels(pos: dict[str, np.ndarray]
                  ) -> tuple[dict[str, tuple[float, float]],
                             tuple[float, float]]:
    arr = np.array(list(pos.values()))
    xmin, ymin = arr.min(axis=0)
    xmax, ymax = arr.max(axis=0)
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
        py = px_y_max - (y - ymin) / (ymax - ymin) * (px_y_max - px_y_min)
        return px, py

    mapped = {w: to_px(float(p[0]), float(p[1])) for w, p in pos.items()}
    origin_px = to_px(0.0, 0.0)
    return mapped, origin_px


# ---------------------------------------------------------------------------
# SVG emission
# ---------------------------------------------------------------------------

def perp_offset(x1: float, y1: float, x2: float, y2: float,
                offset: float = 12.0) -> tuple[float, float]:
    """Perpendicular offset from an arrow midpoint, picking the 'upper'
    side (smaller y in SVG) so midpoint labels stay off the line."""
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    ox = -dy / length * offset
    oy = dx / length * offset
    if oy > 0:
        ox, oy = -ox, -oy
    return ox, oy


def star_polygon(cx: float, cy: float, r_outer: float,
                 fill: str, stroke: str) -> str:
    pts = []
    for i in range(10):
        angle = -np.pi / 2 + i * np.pi / 5
        rad = r_outer if i % 2 == 0 else r_outer * 0.45
        x = cx + rad * np.cos(angle)
        y = cy + rad * np.sin(angle)
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'    <polygon points="{" ".join(pts)}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1.2"/>')


def arrow_marker_def(key: str, color: str) -> list[str]:
    return [
        '  <defs>',
        f'    <marker id="arrow-{key}" viewBox="0 0 10 10" '
        f'refX="9" refY="5" markerWidth="6" markerHeight="6" '
        f'orient="auto-start-reverse">',
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/>',
        '    </marker>',
        f'    <marker id="arrow-origin" viewBox="0 0 10 10" '
        f'refX="9" refY="5" markerWidth="5" markerHeight="5" '
        f'orient="auto-start-reverse">',
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{ORIGIN_VEC_COLOR}"/>',
        '    </marker>',
        '  </defs>',
    ]


def shorten_endpoint(x1: float, y1: float, x2: float, y2: float,
                     shrink: float = 9.0) -> tuple[float, float]:
    """Pull the endpoint back along the line by `shrink` pixels so the
    arrowhead doesn't disappear inside the target dot."""
    dx = x2 - x1
    dy = y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1e-6)
    return (x2 - dx / length * shrink, y2 - dy / length * shrink)


def build_chain_layers(chain: dict,
                       pos: dict[str, tuple[float, float]],
                       origin_px: tuple[float, float]
                       ) -> list[str]:
    a, b, c, d = chain["words"]
    key    = chain["key"]
    color  = chain["color"]
    marker = f"url(#arrow-{key})"
    origin_marker = "url(#arrow-origin)"

    if any(w not in pos for w in (a, b, c, d)):
        print(f"  [WARN] chain '{key}' has OOV words; no layers emitted")
        return []

    p_a        = pos[a]
    p_sub_end  = pos[f"{key}-sub-end"]
    p_add_end  = pos[f"{key}-add-end"]
    p_d        = pos[d]

    label_offsets = chain.get("label_offsets", {})
    out: list[str] = []

    def origin_arrow(target_word: str) -> str:
        """Faint dashed gray arrow from PC-origin to the target word's
        dot, stopped short of the dot so the arrowhead sits cleanly."""
        ox_, oy_ = origin_px
        tx, ty = pos[target_word]
        ex, ey = shorten_endpoint(ox_, oy_, tx, ty, shrink=9)
        return (
            f'    <line x1="{ox_:.1f}" y1="{oy_:.1f}" '
            f'x2="{ex:.1f}" y2="{ey:.1f}" '
            f'stroke="{ORIGIN_VEC_COLOR}" stroke-width="1.2" '
            f'stroke-dasharray="4,3" opacity="0.75" '
            f'marker-end="{origin_marker}"/>')

    # -- words: 4 labeled points
    out.append(f'  <g class="layer" id="{key}-words">')
    out.append(f'    <g fill="{color}">')
    for w in (a, b, c, d):
        x, y = pos[w]
        out.append(f'      <circle cx="{x:.1f}" cy="{y:.1f}" r="7"/>')
    out.append('    </g>')
    out.append(
        f'    <g fill="{LABEL_COLOR}" font-size="13" font-weight="600" '
        f'text-anchor="middle">')
    for w in (a, b, c, d):
        x, y = pos[w]
        ox, oy = label_offsets.get(w, (0, 22))
        out.append(f'      <text x="{x + ox:.1f}" y="{y + oy:.1f}">{w}</text>')
    out.append('    </g>')
    out.append('  </g>')

    # -- sub arrow: A → A−B, plus the B vector drawn from origin
    x1, y1 = p_a; x2, y2 = p_sub_end
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ox, oy = perp_offset(x1, y1, x2, y2)
    out.append(f'  <g class="layer" id="{key}-sub">')
    out.append(origin_arrow(b))
    out.append(
        f'    <line x1="{x1:.1f}" y1="{y1:.1f}" '
        f'x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
        f'stroke-width="2.4" marker-end="{marker}"/>')
    out.append(
        f'    <text x="{mx + ox:.1f}" y="{my + oy:.1f}" text-anchor="middle" '
        f'fill="{color}" font-size="12" font-style="italic">−{b}</text>')
    out.append('  </g>')

    # -- add arrow: A−B → A−B+C, plus the C vector drawn from origin
    x1, y1 = p_sub_end; x2, y2 = p_add_end
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    ox, oy = perp_offset(x1, y1, x2, y2)
    out.append(f'  <g class="layer" id="{key}-add">')
    out.append(origin_arrow(c))
    out.append(
        f'    <line x1="{x1:.1f}" y1="{y1:.1f}" '
        f'x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
        f'stroke-width="2.4" marker-end="{marker}"/>')
    out.append(
        f'    <text x="{mx + ox:.1f}" y="{my + oy:.1f}" text-anchor="middle" '
        f'fill="{color}" font-size="12" font-style="italic">+{c}</text>')
    out.append('  </g>')

    # -- resolve: star + dashed residual + "≈ D?" label
    sx, sy = p_add_end
    dx, dy = p_d
    out.append(f'  <g class="layer" id="{key}-resolve">')
    out.append(
        f'    <line x1="{sx:.1f}" y1="{sy:.1f}" '
        f'x2="{dx:.1f}" y2="{dy:.1f}" stroke="{RESIDUAL_COLOR}" '
        f'stroke-width="1.4" stroke-dasharray="4,3" opacity="0.85"/>')
    out.append(star_polygon(sx, sy, 9, STAR_FILL, STAR_EDGE))
    out.append(
        f'    <text x="{dx + 12:.1f}" y="{dy - 10:.1f}" '
        f'fill="{RESIDUAL_COLOR}" font-size="13" font-style="italic">'
        f'≈ {d}?</text>')
    out.append('  </g>')

    return out


def build_svg(chain: dict,
              pos: dict[str, tuple[float, float]],
              origin_px: tuple[float, float],
              background_words: list[str]) -> str:
    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Iosevka, \'JetBrains Mono\', monospace">')
    lines.append('  <!--')
    lines.append(
        f'    Generated by workspace/build_interactive_analogy_svg.py')
    lines.append(
        f'    Chain: {chain["key"]}   '
        f'{" − ".join(chain["words"][:2])} + {chain["words"][2]} '
        f'≈ {chain["words"][3]}')
    lines.append(
        '    PCA fit on a curated corpus of analogy-aligned word pairs.')
    lines.append('    Edit the script and regenerate; do not hand-edit.')
    lines.append('  -->')
    lines.extend(arrow_marker_def(chain["key"], chain["color"]))

    # Title
    lines.append(
        f'  <text x="{WIDTH // 2}" y="28" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="15" font-weight="500">')
    lines.append(f'    {chain["title"]}')
    lines.append('  </text>')

    # Grid
    lines.append(f'  <g stroke="{GRID_COLOR}" stroke-width="1" fill="none">')
    for x in range(MARGIN_L, WIDTH - MARGIN_R + 1, 120):
        lines.append(
            f'    <line x1="{x}" y1="{MARGIN_T}" '
            f'x2="{x}" y2="{HEIGHT - MARGIN_B}"/>')
    for y in range(MARGIN_T, HEIGHT - MARGIN_B + 1, 100):
        lines.append(
            f'    <line x1="{MARGIN_L}" y1="{y}" '
            f'x2="{WIDTH - MARGIN_R}" y2="{y}"/>')
    lines.append('  </g>')

    # Axes at PC=0
    ox, oy = origin_px
    lines.append(f'  <g stroke="{AXIS_COLOR}" stroke-width="1.2" fill="none">')
    lines.append(
        f'    <line x1="{MARGIN_L}" y1="{oy:.1f}" '
        f'x2="{WIDTH - MARGIN_R}" y2="{oy:.1f}"/>')
    lines.append(
        f'    <line x1="{ox:.1f}" y1="{MARGIN_T}" '
        f'x2="{ox:.1f}" y2="{HEIGHT - MARGIN_B}"/>')
    lines.append('  </g>')
    lines.append(
        f'  <text x="{WIDTH - MARGIN_R - 8}" y="{oy + 16:.1f}" '
        f'text-anchor="end" fill="#999" font-size="11">PC 1</text>')
    lines.append(
        f'  <text x="{ox + 8:.1f}" y="{MARGIN_T + 12}" '
        f'text-anchor="start" fill="#999" font-size="11">PC 2</text>')

    # Background: the other fit pairs, as faint unlabeled dots. Same
    # semantic neighborhood as the chain — subtly shows the pattern
    # extends beyond the 4 words we name.
    lines.append(f'  <g fill="{BG_POINT_COLOR}" opacity="0.65">')
    for w in background_words:
        if w in pos:
            x, y = pos[w]
            lines.append(f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="2.5"/>')
    lines.append('  </g>')

    # The chain's own layers
    lines.extend(build_chain_layers(chain, pos, origin_px))

    lines.append('</svg>')
    return '\n'.join(lines) + '\n'


# ---------------------------------------------------------------------------

def main() -> None:
    backend = EmbeddingBackend()
    os.makedirs(OUT_DIR, exist_ok=True)
    for chain in CHAINS:
        pos_pca, background_words = run_pca(backend, chain)
        pos_px, origin_px = map_to_pixels(pos_pca)
        svg = build_svg(chain, pos_px, origin_px, background_words)
        out_path = os.path.join(OUT_DIR, chain["out_file"])
        with open(out_path, "w") as f:
            f.write(svg)
        print(f"  wrote {out_path}  ({len(pos_px)} positions)")


if __name__ == "__main__":
    main()
