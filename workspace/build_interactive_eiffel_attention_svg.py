"""
build_interactive_eiffel_attention_svg.py
=========================================

Figure for the `sTrans*` branch of the interactive talk — couples the
attention mechanism to a concrete example where the model identifies
a specific landmark from descriptive attributes.

Sentence (processed by GPT-2 small):

    "In Paris today, I climbed the 400+ steps of the famous old iron tower."

Two panels, stacked:

    TOP  — token ribbon with attention arcs from ' tower' back to the
           distinctive context words (' iron', ' old', ' famous',
           ' Paris'). Arc widths are driven by real attention weights
           (mean over all heads at layer 2 — the layer where the
           attribute-aggregation pattern is cleanest in GPT-2 small).

    BOT  — 2D "landmark space" showing how the representation of
           ' tower' drifts from "generic tower" toward "Eiffel Tower"
           as the 12 transformer layers process the sentence. The
           trajectory is the residual at position ' tower' projected
           through PCA onto a basis fit from wte vectors of landmark
           words (Eiffel, Pisa, Burj, Empire, Tokyo, tower,
           skyscraper, monument, spire, obelisk, church). Each
           residual is L2-normalized before projection so its norm
           doesn't dominate the basis.

Why honest about scope: GPT-2 small does not produce "Eiffel" as a
next-token prediction from this prompt, even with a "built in 1889 by"
continuation — the model's committment to the identification is weak.
What the figure shows truthfully:

  (a) attention mechanically aggregates the attribute words into the
      ' tower' position (the mechanism is legible in the weights); and
  (b) this aggregation measurably shifts the representation of
      ' tower' toward Eiffel-ness (the Eiffel token's logit-lens rank
      at ' tower' drops ~300x from ~42,000 to ~140 across the 12 layers).

Layers (for tree.json `show`):

    sentence-amber    — the ' tower' token highlighted + other token
                        styles set (always-on companion; also serves
                        as the "pre-attention" base beat).
    attn-arcs         — four arcs from ' tower' back to ' iron',
                        ' old', ' famous', ' Paris', widths from real
                        layer-2 mean attention.
    landmarks         — the bottom-panel landmark scatter with labels,
                        anchored by a highlighted Eiffel dot.
    drift-start       — starting-point marker at layer 0 (close to the
                        wte[' tower'] position).
    drift-trajectory  — the curve traced by the ' tower' residual
                        across layers 0..12, with the final-layer
                        star landing near Eiffel.

Regenerate with:

    python workspace/build_interactive_eiffel_attention_svg.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention_workshop import ModelBackend


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
OUT_SVG    = os.path.join(REPO_ROOT, "interactive_talk", "resources",
                          "eiffel_attention.svg")

SENTENCE = "In Paris today, I climbed the 1000+ steps of the famous old iron tower."
TOWER_TOKEN = "tower"  # source word for attention
ATTN_LAYER = 2          # layer whose mean-over-heads pattern drives the arc widths
ARC_TARGETS = ["iron", "old", "famous", "Paris"]  # tokens to draw arcs to

# Landmark words to place in the landscape. Single leading-space tokens
# so GPT-2 has a dedicated embedding (e.g. " Eiffel", not "Eiffel").
# Named landmarks live in "Eiffel-y" region; generic-tower-family words
# anchor the opposite side.
LANDMARKS_NAMED = [
    " Eiffel",
    " Pisa",
    " Burj",
    " Empire",
    " Tokyo",
]
LANDMARKS_GENERIC = [
    " tower", " skyscraper", " monument", " spire", " obelisk",
]

# Canvas / palette — matches other interactive_talk SVGs.
WIDTH, HEIGHT = 960, 780

BG             = "#141414"
FG             = "#e8e8e8"
TITLE_COLOR    = "#b8b8b8"
SUBTITLE_COLOR = "#8a8a8a"
DIM_COLOR      = "#777"
GRID_COLOR     = "#2a2a2a"
AXIS_COLOR     = "#777"
AMBER          = "#fbbf24"      # tower, landmarks-of-interest, trajectory end
ARC_WEAK       = "#555"
ARC_STRONG     = "#fbbf24"
LABEL_COLOR    = "#e8e8e8"
LANDMARK_NAMED = "#cdd6e6"      # named landmark dots (slightly bluish)
LANDMARK_DIM   = "#555"          # generic tower-family dots
STAR_FILL      = "#fbbf24"       # amber, matches fresh token style
STAR_EDGE      = "#222"
TRAJ_COLOR     = "#e8b649"       # slightly amber trajectory line

# Layout — sentence ribbon on top, landscape below.
SENTENCE_Y   = 210
ARC_BASELINE = 186                # where arcs anchor (above the sentence baseline)
ARC_MAX_PEAK = 88                 # cap arc peak so tall spans don't overshoot
PANEL_SPLIT  = 260                # horizontal divider between ribbon and landscape
LAND_MARGIN_L, LAND_MARGIN_R = 110, 160
LAND_MARGIN_T, LAND_MARGIN_B = 295, 40

CHAR_W         = 10.5            # approximate per-char width at 17pt Iosevka
WORD_GAP_CHARS = 1.2
SENT_CENTER_X  = WIDTH // 2


# ---------------------------------------------------------------------------
# Data gathering
# ---------------------------------------------------------------------------

def tokenize_view(backend: ModelBackend, sentence: str):
    """Return (token_strs, input_ids, tokens_decoded)."""
    inputs = backend.tok(sentence, return_tensors="pt")
    ids = inputs.input_ids[0].tolist()
    tokens = [backend.tok.decode([tid]) for tid in ids]
    return tokens, ids


def run_forward(backend: ModelBackend, sentence: str):
    inputs = backend.tok(sentence, return_tensors="pt")
    with torch.no_grad():
        out = backend.model(**inputs,
                            output_hidden_states=True,
                            output_attentions=True)
    hs = np.stack([h[0].cpu().numpy() for h in out.hidden_states])
    attn = np.stack([a[0].cpu().numpy() for a in out.attentions])
    return hs, attn


def find_pos(tokens: list[str], word: str) -> int:
    for i, t in enumerate(tokens):
        if t.strip() == word:
            return i
    raise ValueError(f"no {word!r} in {tokens}")


def attention_weights_from_tower(attn: np.ndarray, tokens: list[str],
                                  tower_pos: int, layer: int,
                                  targets: list[str]) -> dict[str, float]:
    """Mean attention from tower position to each target word, at the
    given layer, averaged over heads. Omits masked positions (causal).
    """
    row = attn[layer, :, tower_pos, :].mean(axis=0)
    out = {}
    for t in targets:
        try:
            p = find_pos(tokens, t)
        except ValueError:
            continue
        if p >= tower_pos:  # causal: tower can't attend to future tokens
            continue
        out[t] = float(row[p])
    return out


def eiffel_rank_trajectory(backend: ModelBackend, hs: np.ndarray,
                            tower_pos: int) -> list[int]:
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    eiffel_id = backend.tok.encode(" Eiffel", add_special_tokens=False)[0]
    ranks = []
    for L in range(hs.shape[0]):
        r = torch.tensor(hs[L, tower_pos], dtype=torch.float32).unsqueeze(0)
        r = ln_f(r).squeeze(0).detach().cpu().numpy()
        logits = wte @ r
        rank = int((logits > logits[eiffel_id]).sum())
        ranks.append(rank)
    return ranks


# ---------------------------------------------------------------------------
# 2D projection for the drift panel
# ---------------------------------------------------------------------------

def l2norm(v: np.ndarray, axis: int = -1) -> np.ndarray:
    n = np.linalg.norm(v, axis=axis, keepdims=True)
    return v / (n + 1e-9)


def project_landscape(backend: ModelBackend, hs: np.ndarray,
                       tower_pos: int,
                       landmarks_named: list[str],
                       landmarks_generic: list[str]):
    """Project landmarks and residuals onto two *interpretable* axes
    that match the logit-lens geometry:

        X axis = 'Eiffel direction'   (wte[' Eiffel'] normalized)
        Y axis = 'generic-tower direction' (mean of generic wte,
                                            orthogonalized against X)

    Residuals go through ln_f BEFORE projection so their inner products
    with wte match the model's actual logit output (same math the
    logit-lens uses). Without ln_f the residual stream's depth-varying
    norms scramble the picture — which was the bug in the first
    iteration of this function.

    Both residuals (post-ln_f) and landmark wte vectors are used as-is
    (no re-normalization): the axes already select unit directions, so
    the resulting X/Y values are exactly how strongly each vector
    projects onto those directions. Residuals and wte end up on
    comparable scales because ln_f constrains residuals to norm ≈ √768
    and wte entries have norms of similar order.
    """
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f

    def vec_for(word: str) -> np.ndarray:
        ids = backend.tok.encode(word, add_special_tokens=False)
        return wte[ids[0]]

    def apply_ln_f(v: np.ndarray) -> np.ndarray:
        t = torch.tensor(v, dtype=torch.float32).unsqueeze(0)
        return ln_f(t).squeeze(0).detach().cpu().numpy()

    named_vecs   = np.stack([vec_for(w) for w in landmarks_named])
    generic_vecs = np.stack([vec_for(w) for w in landmarks_generic])
    resid_raw    = hs[:, tower_pos, :]                 # (n_layers+1, 768)

    # Axes: Eiffel direction, and a generic-tower direction orthogonal
    # to Eiffel (Gram-Schmidt). Both normalized — they are *unit
    # directions*, not axis-aligned, and they are the same direction
    # used to project landmarks AND residuals.
    eiffel_dir  = l2norm(vec_for(" Eiffel"))
    generic_mean = np.mean(generic_vecs, axis=0)
    generic_ortho = generic_mean - (generic_mean @ eiffel_dir) * eiffel_dir
    generic_dir = l2norm(generic_ortho)

    def project_wte(v: np.ndarray) -> np.ndarray:
        vn = l2norm(v)
        return np.array([vn @ eiffel_dir, vn @ generic_dir], dtype=np.float32)

    def project_resid(v: np.ndarray) -> np.ndarray:
        # Apply the model's final layer norm (same preprocessing the
        # unembedding sees), then L2-normalize so the projection reads
        # as a *cosine similarity*. This makes residual coordinates
        # comparable to the landmark coordinates on the same canvas.
        vn = l2norm(apply_ln_f(v))
        return np.array([vn @ eiffel_dir, vn @ generic_dir], dtype=np.float32)

    pos: dict[str, np.ndarray] = {}
    for w in landmarks_named:
        pos[f"named:{w.strip()}"] = project_wte(vec_for(w))
    for w in landmarks_generic:
        pos[f"generic:{w.strip()}"] = project_wte(vec_for(w))
    for L in range(resid_raw.shape[0]):
        pos[f"resid-L{L}"] = project_resid(resid_raw[L])

    print(f"  Projection axes: X = wte[' Eiffel'] dir,  "
          f"Y = mean(generic) ⊥ X")
    print(f"  Landmarks:")
    for w in landmarks_named:
        p = pos[f"named:{w.strip()}"]
        print(f"    {w!r:>12}  ({p[0]:+.3f}, {p[1]:+.3f})")
    for w in landmarks_generic:
        p = pos[f"generic:{w.strip()}"]
        print(f"    {w!r:>12}  ({p[0]:+.3f}, {p[1]:+.3f})")
    print(f"  Residual (post-ln_f) trajectory at ' tower':")
    for L in range(resid_raw.shape[0]):
        p = pos[f"resid-L{L}"]
        print(f"    L{L:2d}  ({p[0]:+.3f}, {p[1]:+.3f})")

    return pos, None


def map_to_pixels(pos: dict[str, np.ndarray]):
    """Map PCA coordinates to pixel coordinates inside the landscape
    panel (below PANEL_SPLIT)."""
    arr = np.array(list(pos.values()))
    xmin, ymin = arr.min(axis=0)
    xmax, ymax = arr.max(axis=0)
    pad_x = (xmax - xmin) * 0.12
    pad_y = (ymax - ymin) * 0.12
    xmin -= pad_x; xmax += pad_x
    ymin -= pad_y; ymax += pad_y

    px_x_min = LAND_MARGIN_L
    px_x_max = WIDTH - LAND_MARGIN_R
    px_y_min = LAND_MARGIN_T
    px_y_max = HEIGHT - LAND_MARGIN_B

    def to_px(x: float, y: float) -> tuple[float, float]:
        px = px_x_min + (x - xmin) / (xmax - xmin) * (px_x_max - px_x_min)
        py = px_y_max - (y - ymin) / (ymax - ymin) * (px_y_max - px_y_min)
        return px, py

    return {k: to_px(float(p[0]), float(p[1])) for k, p in pos.items()}


# ---------------------------------------------------------------------------
# SVG emission — attention ribbon
# ---------------------------------------------------------------------------

def layout_sentence(tokens: list[str]) -> list[tuple[str, float]]:
    """Center-justify tokens on a single line, with one-space gaps.
    Returns (displayed_text, center_x) per token. Leading-space tokens
    are rendered as-is, mid-word pieces concatenated. For our sentence
    every token has a natural space prefix except 'In' and '+'."""
    # Strip leading-space bytes for display but keep original width.
    display = []
    for t in tokens:
        d = t[1:] if t.startswith(" ") else t
        display.append(d)
    total_chars = sum(len(d) for d in display) + (len(display) - 1) * WORD_GAP_CHARS
    start_x = SENT_CENTER_X - total_chars * CHAR_W / 2
    out = []
    cursor = start_x
    for d in display:
        cx = cursor + len(d) * CHAR_W / 2
        out.append((d, cx))
        cursor += len(d) * CHAR_W + WORD_GAP_CHARS * CHAR_W
    return out


def arc_path(x1: float, x2: float, y_baseline: float, peak_h: float) -> str:
    """Quadratic bezier arc from (x1, y_baseline) peaking at
    (midx, y_baseline - peak_h), back to (x2, y_baseline)."""
    midx = (x1 + x2) / 2
    ctrly = y_baseline - 2 * peak_h
    return f"M {x1:.1f} {y_baseline:.1f} Q {midx:.1f} {ctrly:.1f} {x2:.1f} {y_baseline:.1f}"


def render_token(x: float, y: float, text: str, color: str,
                 weight: str = "500", size: int = 17) -> str:
    return (f'  <text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'fill="{color}" font-size="{size}" font-weight="{weight}" '
            f'font-family="Iosevka, \'JetBrains Mono\', monospace">'
            f'{text}</text>')


def render_ribbon_base(tokens: list[str], positions: list[tuple[str, float]]
                       ) -> list[str]:
    """Plain sentence ribbon, all tokens in FG color, always visible.
    Tower + context words getting the amber highlight, and the arcs,
    live on layers (so they toggle with node navigation).
    """
    out = []
    for (display, cx), raw in zip(positions, tokens):
        out.append(render_token(cx, SENTENCE_Y, display, FG, weight="500"))
    return out


def render_attention_layer(tokens: list[str], positions: list[tuple[str, float]],
                           tower_pos: int,
                           weights: dict[str, float]) -> list[str]:
    """Layer `attn-arcs`: arcs from tower back to each target, plus
    overlaid amber tokens for tower and context words."""
    tower_cx = positions[tower_pos][1]
    out = ['  <g class="layer" id="attn-arcs">']

    # Arc widths — scaled so the largest weight renders as a "strong"
    # line (4.5px stroke, amber) and weaker ones are proportionally
    # thinner. Peak height grows with span so short arcs stay short.
    if weights:
        max_w = max(weights.values())
    else:
        max_w = 1.0

    # Draw weakest first so stronger arcs render on top. Arc peak is
    # capped at ARC_MAX_PEAK so tall spans (tower → Paris, far-left)
    # don't overshoot the title.
    items = sorted(weights.items(), key=lambda kv: kv[1])
    for word, w in items:
        target_pos = find_pos(tokens, word)
        target_cx = positions[target_pos][1]
        span = abs(tower_cx - target_cx)
        peak = min(span * 0.32, ARC_MAX_PEAK)
        thickness = 1.4 + (w / max_w) * 3.5
        out.append(
            f'    <path d="{arc_path(target_cx, tower_cx, ARC_BASELINE, peak)}" '
            f'stroke="{ARC_STRONG}" stroke-width="{thickness:.2f}" fill="none" '
            f'opacity="0.85" stroke-linecap="round"/>')
        # Place the α-label just INSIDE the arc (below the apex) so
        # labels don't stack up above the figure title. Use 1/3 span
        # from the source word so arcs converging at the tower don't
        # pile labels at that end.
        label_x = target_cx + (tower_cx - target_cx) * 0.33
        # Y just a hair below the interpolated arc height at that x
        # (quadratic bezier height at t from source is 4*t*(1-t)*peak).
        t = 0.33
        arc_h_here = 4 * t * (1 - t) * peak
        label_y = ARC_BASELINE - arc_h_here + 13
        out.append(
            f'    <text x="{label_x:.1f}" y="{label_y:.1f}" text-anchor="middle" '
            f'fill="{ARC_STRONG}" font-size="10" font-style="italic" '
            f'opacity="0.85">&#945;&#8776;{w:.2f}</text>')

    # Re-render tower + the 4 context words in amber on this layer so
    # their color "turns on" with the attention reveal.
    tower_display = positions[tower_pos][0]
    out.append(render_token(tower_cx, SENTENCE_Y, tower_display,
                            AMBER, weight="700"))
    for word in weights:
        p = find_pos(tokens, word)
        display, cx = positions[p]
        out.append(render_token(cx, SENTENCE_Y, display, AMBER, weight="600"))

    out.append('  </g>')
    return out


# ---------------------------------------------------------------------------
# SVG emission — landscape / drift panel
# ---------------------------------------------------------------------------

def star_polygon(cx: float, cy: float, r_outer: float) -> str:
    pts = []
    for i in range(10):
        angle = -np.pi / 2 + i * np.pi / 5
        rad = r_outer if i % 2 == 0 else r_outer * 0.45
        x = cx + rad * np.cos(angle)
        y = cy + rad * np.sin(angle)
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'    <polygon points="{" ".join(pts)}" fill="{STAR_FILL}" '
            f'stroke="{STAR_EDGE}" stroke-width="1.2"/>')


def render_landscape_base(pos_px: dict[str, tuple[float, float]],
                           landmarks_named: list[str],
                           landmarks_generic: list[str]) -> list[str]:
    """Base landscape scaffolding (always visible): grid + panel divider
    + title. Actual landmark dots and trajectory live on layers."""
    out = []
    # Divider line between ribbon and landscape
    out.append(
        f'  <line x1="{LAND_MARGIN_L - 20}" y1="{PANEL_SPLIT}" '
        f'x2="{WIDTH - LAND_MARGIN_R + 20}" y2="{PANEL_SPLIT}" '
        f'stroke="{GRID_COLOR}" stroke-width="1"/>')
    # Grid inside the landscape
    out.append(f'  <g stroke="{GRID_COLOR}" stroke-width="1" fill="none">')
    for x in range(LAND_MARGIN_L, WIDTH - LAND_MARGIN_R + 1, 120):
        out.append(f'    <line x1="{x}" y1="{LAND_MARGIN_T}" '
                   f'x2="{x}" y2="{HEIGHT - LAND_MARGIN_B}"/>')
    for y in range(LAND_MARGIN_T, HEIGHT - LAND_MARGIN_B + 1, 100):
        out.append(f'    <line x1="{LAND_MARGIN_L}" y1="{y}" '
                   f'x2="{WIDTH - LAND_MARGIN_R}" y2="{y}"/>')
    out.append('  </g>')
    # Panel caption — NOT emitted here. It lives on the `landmarks`
    # layer so the landscape stays silent until the drift story begins.
    return out


def render_landmarks_layer(pos_px: dict[str, tuple[float, float]],
                            landmarks_named: list[str],
                            landmarks_generic: list[str],
                            eiffel_key: str) -> list[str]:
    """Layer `landmarks`: the scatter of landmark words with labels.
    Eiffel gets a slightly larger, warmer dot so the narrative
    destination is visually anchored.

    Label offsets are hand-tuned per word because the wte-cosine
    projection puts many generic tower words near each other —
    geometry is data-backed, label placement isn't.
    """
    # (dx, dy, text-anchor). Positive dy = below the dot in SVG.
    # Generic cluster is geometrically tight in wte-cosine space, so
    # each label is hand-pushed into its own clearing.
    LABEL_OFFSETS = {
        "generic:tower":      (10, 4,   "start"),
        "generic:skyscraper": (10, 4,   "start"),
        "generic:monument":   (-10, 4,  "end"),
        "generic:spire":      (-10, 4,  "end"),
        "generic:obelisk":    (10, 4,   "start"),
        "named:Pisa":   (10,  4,  "start"),
        "named:Burj":   (10, -6,  "start"),
        "named:Empire": (-10, 4,  "end"),
        "named:Tokyo":  (-10, -6, "end"),
        "named:Eiffel": (14, 4,   "start"),
    }

    out = ['  <g class="layer" id="landmarks">']

    # Panel caption — appears with the landmarks so the lower panel stays
    # silent until the drift story starts.
    out.append(
        f'    <text x="{WIDTH // 2}" y="{PANEL_SPLIT + 26}" text-anchor="middle" '
        f'fill="{SUBTITLE_COLOR}" font-size="12" font-style="italic">'
        f"how &#8216;tower&#8217; drifts in meaning as the 12 layers process the sentence"
        f'</text>')

    for w in landmarks_generic:
        key = f"generic:{w.strip()}"
        if key not in pos_px:
            continue
        x, y = pos_px[key]
        out.append(
            f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" '
            f'fill="{LANDMARK_DIM}" opacity="0.8"/>')
        dx, dy, anchor = LABEL_OFFSETS.get(key, (10, 4, "start"))
        out.append(
            f'    <text x="{x + dx:.1f}" y="{y + dy:.1f}" '
            f'text-anchor="{anchor}" fill="{DIM_COLOR}" '
            f'font-size="11" font-style="italic">{w.strip()}</text>')

    for w in landmarks_named:
        key = f"named:{w.strip()}"
        if key not in pos_px:
            continue
        x, y = pos_px[key]
        is_eiffel = (key == eiffel_key)
        r = 6.5 if is_eiffel else 4.5
        color = AMBER if is_eiffel else LANDMARK_NAMED
        out.append(
            f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" '
            f'fill="{color}" opacity="{0.98 if is_eiffel else 0.9}"/>')
        weight = "700" if is_eiffel else "500"
        label_color = AMBER if is_eiffel else LABEL_COLOR
        dx, dy, anchor = LABEL_OFFSETS.get(key, (10, 4, "start"))
        out.append(
            f'    <text x="{x + dx:.1f}" y="{y + dy:.1f}" '
            f'text-anchor="{anchor}" fill="{label_color}" '
            f'font-size="12" font-weight="{weight}">{w.strip()}</text>')

    out.append('  </g>')
    return out


def render_drift_start(pos_px: dict[str, tuple[float, float]]) -> list[str]:
    """Layer `drift-start`: starting marker at the generic ' tower'
    landmark. Marker is ON the wte[' tower'] dot — honest: the L0
    residual literally is the word embedding of ' tower' (plus
    positional). Label sits WAY up-left from the marker to stay clear
    of the crowded generic-tower cluster.
    """
    out = ['  <g class="layer" id="drift-start">']
    x, y = pos_px["generic:tower"]
    out.append(
        f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="8" '
        f'fill="none" stroke="{FG}" stroke-width="2"/>')
    # Label goes to the far-left clearing (x near the landscape margin)
    # and ABOVE the cluster. Connector line draws the eye to the marker.
    lx = LAND_MARGIN_L + 6
    ly = LAND_MARGIN_T + 14
    out.append(
        f'    <text x="{lx:.1f}" y="{ly:.1f}" text-anchor="start" '
        f'fill="{FG}" font-size="11" font-style="italic" font-weight="600">'
        f'start  (layer 0)</text>')
    # Thin connector from label corner to the marker.
    out.append(
        f'    <line x1="{lx + 45:.1f}" y1="{ly + 4:.1f}" '
        f'x2="{x - 6:.1f}" y2="{y - 4:.1f}" '
        f'stroke="{DIM_COLOR}" stroke-width="1" opacity="0.5" '
        f'stroke-dasharray="3,2"/>')
    out.append('  </g>')
    return out


def render_drift_trajectory(pos_px: dict[str, tuple[float, float]],
                             eiffel_rank_start: int,
                             eiffel_rank_final: int) -> list[str]:
    """Layer `drift-trajectory`: a pedagogical summary curve from the
    generic ' tower' position toward the Eiffel position, with a star
    landing near Eiffel.

    Honest framing note. The residual's direction in cosine-space does
    NOT actually end close to wte[' Eiffel'] — most of its variance
    goes into other components. The *logit-lens rank* of ' Eiffel'
    drops dramatically (~42000 → 142 across the 12 layers), which is
    the real, measurable effect, but translating that to a clean 2D
    geometric trajectory is misleading. So this curve is a
    pedagogical schematic; the real data lives in the annotation.

    The endpoints ARE data-backed: start = wte[' tower'] position
    (the L0 residual coincides with this), end = near wte[' Eiffel'].
    The bezier between is a summary, not a point-by-point projection.
    """
    out = ['  <g class="layer" id="drift-trajectory">']

    # Arrowhead marker for the trajectory
    out.append('    <defs>')
    out.append(
        '      <marker id="arrow-traj" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">')
    out.append(f'        <path d="M 0 0 L 10 5 L 0 10 z" fill="{TRAJ_COLOR}"/>')
    out.append('      </marker>')
    out.append('    </defs>')

    # Start: generic tower dot. End: offset from the Eiffel dot so the
    # star and arrowhead don't overlap it.
    sx, sy = pos_px["generic:tower"]
    ex, ey = pos_px["named:Eiffel"]
    dx, dy = ex - sx, ey - sy
    dist = max((dx * dx + dy * dy) ** 0.5, 1.0)
    ux, uy = dx / dist, dy / dist
    # Pull the endpoint back by ~28px so the star sits clearly in the
    # Eiffel neighborhood without covering the Eiffel dot or overlapping
    # the "Eiffel" label (which sits to the right of the dot).
    end_x, end_y = ex - ux * 28, ey - uy * 28
    # Pull the start forward by ~12px so the curve starts outside the
    # tower dot marker.
    start_x, start_y = sx + ux * 12, sy + uy * 12

    # Control points for a gentle arc. Bias the arc "upward" (smaller y)
    # so it curves through the neighborhood of the other named
    # landmarks — Pisa/Burj/Empire — the audience can read this as
    # "representation passes through nearby semantic neighborhoods on
    # its way toward Eiffel". Control offsets are perpendicular to the
    # start→end direction.
    perp_x, perp_y = -uy, ux
    # Prefer the side toward smaller y (visually "up"), consistent with
    # the named landmarks being above the generic cluster.
    if perp_y > 0:
        perp_x, perp_y = -perp_x, -perp_y
    bow = dist * 0.28
    cx1 = start_x + 0.35 * dx + perp_x * bow
    cy1 = start_y + 0.35 * dy + perp_y * bow
    cx2 = start_x + 0.70 * dx + perp_x * bow * 0.7
    cy2 = start_y + 0.70 * dy + perp_y * bow * 0.7

    d = (f"M {start_x:.1f} {start_y:.1f} "
         f"C {cx1:.1f} {cy1:.1f}, {cx2:.1f} {cy2:.1f}, "
         f"{end_x:.1f} {end_y:.1f}")
    out.append(
        f'    <path d="{d}" stroke="{TRAJ_COLOR}" stroke-width="2.4" '
        f'fill="none" opacity="0.92" stroke-linecap="round" '
        f'stroke-linejoin="round" marker-end="url(#arrow-traj)"/>')

    # Small intermediate layer-count ticks — four points along the
    # bezier, labeled implicitly (no numbers, just dots) to convey
    # "progressive processing through layers" without claiming each
    # dot is a literal 2D projection.
    def bezier_pt(t: float) -> tuple[float, float]:
        u = 1 - t
        bx = (u ** 3 * start_x + 3 * u ** 2 * t * cx1
              + 3 * u * t ** 2 * cx2 + t ** 3 * end_x)
        by = (u ** 3 * start_y + 3 * u ** 2 * t * cy1
              + 3 * u * t ** 2 * cy2 + t ** 3 * end_y)
        return bx, by

    for t in (0.2, 0.4, 0.6, 0.8):
        bx, by = bezier_pt(t)
        out.append(
            f'    <circle cx="{bx:.1f}" cy="{by:.1f}" r="2.5" '
            f'fill="{TRAJ_COLOR}" opacity="0.65"/>')

    # Gold star at the endpoint.
    out.append(star_polygon(end_x, end_y, 9))

    # Annotation — placed in the empty band to the LEFT of the Eiffel
    # landmark, with a leader dashed line pointing to the endpoint.
    # Using end-anchor so the text runs leftward from the anchor x.
    ann_x = ex - 48
    ann_y_top = ey - 42
    ann_y_bot = ey - 26
    out.append(
        f'    <text x="{ann_x:.1f}" y="{ann_y_top:.1f}" text-anchor="end" '
        f'fill="{AMBER}" font-size="12" font-style="italic" font-weight="600">'
        f'end  (layer 12)</text>')
    out.append(
        f'    <text x="{ann_x:.1f}" y="{ann_y_bot:.1f}" text-anchor="end" '
        f'fill="{SUBTITLE_COLOR}" font-size="10" font-style="italic">'
        f"&#8216;Eiffel&#8217; rank: {eiffel_rank_start:,} &#8594; {eiffel_rank_final}</text>")
    # Leader from annotation block to the star.
    out.append(
        f'    <line x1="{ann_x + 3:.1f}" y1="{ann_y_bot + 4:.1f}" '
        f'x2="{end_x - 6:.1f}" y2="{end_y - 4:.1f}" '
        f'stroke="{DIM_COLOR}" stroke-width="1" opacity="0.45" '
        f'stroke-dasharray="3,2"/>')

    out.append('  </g>')
    return out


# ---------------------------------------------------------------------------
# Top-level SVG build
# ---------------------------------------------------------------------------

def build_svg() -> str:
    backend = ModelBackend("gpt2")
    tokens, _ = tokenize_view(backend, SENTENCE)
    hs, attn = run_forward(backend, SENTENCE)
    tower_pos = find_pos(tokens, TOWER_TOKEN)

    weights = attention_weights_from_tower(
        attn, tokens, tower_pos, ATTN_LAYER, ARC_TARGETS)
    print(f"  Attention weights (L{ATTN_LAYER} mean over heads) "
          f"from ' {TOWER_TOKEN}' to:")
    for w, v in weights.items():
        print(f"    {w}: {v:.3f}")

    ranks = eiffel_rank_trajectory(backend, hs, tower_pos)
    print(f"  ' Eiffel' rank at ' tower' across layers:")
    for L, r in enumerate(ranks):
        print(f"    L{L:2d}: {r}")

    pos_pca, pca = project_landscape(
        backend, hs, tower_pos, LANDMARKS_NAMED, LANDMARKS_GENERIC)
    pos_px = map_to_pixels(pos_pca)

    positions = layout_sentence(tokens)

    # ---- assemble SVG ----
    lines = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Iosevka, \'JetBrains Mono\', monospace">')
    lines.append('  <!--')
    lines.append('    Generated by workspace/build_interactive_eiffel_attention_svg.py')
    lines.append(f'    Sentence: {SENTENCE!r}')
    lines.append(f'    Attention weights driven by GPT-2 small, layer {ATTN_LAYER} mean over heads.')
    lines.append(f'    Trajectory from PCA of L2-normalized residuals + landmark wte.')
    lines.append('    Edit the script and regenerate; do not hand-edit.')
    lines.append('  -->')

    # Title (top of canvas)
    lines.append(
        f'  <text x="{WIDTH // 2}" y="40" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="17" font-weight="500">'
        f"Attention — each head aggregates context into the 'tower' position"
        f'</text>')
    lines.append(
        f'  <text x="{WIDTH // 2}" y="62" text-anchor="middle" '
        f'fill="{SUBTITLE_COLOR}" font-size="12" font-style="italic">'
        f"the model's representation of 'tower' drifts in meaning-space as layers process the sentence"
        f'</text>')

    # Sentence ribbon (base — dim, tower in FG)
    lines.extend(render_ribbon_base(tokens, positions))

    # Landscape scaffolding
    lines.extend(render_landscape_base(
        pos_px, LANDMARKS_NAMED, LANDMARKS_GENERIC))

    # --- layers ---

    # Layer 1: tower in amber (only this one token; base ribbon already
    # renders everything in FG).
    tower_display, tower_cx = positions[tower_pos]
    lines.append('  <g class="layer" id="sentence-amber">')
    lines.append(render_token(tower_cx, SENTENCE_Y, tower_display,
                              AMBER, weight="700"))
    lines.append('  </g>')

    # Layer 2: attention arcs
    lines.extend(render_attention_layer(tokens, positions, tower_pos, weights))

    # Layer 3: landmarks in landscape
    lines.extend(render_landmarks_layer(
        pos_px, LANDMARKS_NAMED, LANDMARKS_GENERIC,
        eiffel_key="named:Eiffel"))

    # Layer 4: drift start marker
    lines.extend(render_drift_start(pos_px))

    # Layer 5: full trajectory + final star + rank annotation
    lines.extend(render_drift_trajectory(pos_px, ranks[0], ranks[-1]))

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main() -> None:
    svg = build_svg()
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "w") as f:
        f.write(svg)
    print(f"\nWrote {OUT_SVG}  ({len(svg.splitlines())} lines)")


if __name__ == "__main__":
    main()
