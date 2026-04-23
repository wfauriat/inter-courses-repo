"""
build_interactive_eiffel_mlp_svg.py
===================================

Figure for the MLP beat of the transformer story, continuing the
Eiffel example from eiffel_attention.svg.

Pedagogical framing (Geva-et-al "key-value memory"): each MLP block
is a bank of ~3072 learned pattern-detectors. When the contextualized
'tower' residual arrives, only a sparse handful fire strongly, and
their outputs sum into an update written back to the residual
stream.

Data validation (see workspace/probe_eiffel_mlp*.py):

  - Sparsity IS real: at the ' tower' position, typically 3-35
    neurons of 3072 have |activation| > 1.0, and 20-120 have
    |activation| > 0.5. Most stay near zero.

  - Per-layer AGGREGATE MLP outputs are thematically legible in
    logit-lens (top-10 tokens per MLP layer at tower):
        L0:  tower, towers, buildings, skysc     — "it's a structure"
        L6:  situated, housed, houses, hosting    — "located-at"
        L7:  cliffs, cliff, ceiling, high         — "tall/vertical"
        L9:  overlooking, known, bordering        — "landmark-like"
        L11: Georg, Nev + punctuation             — proper-name prefix

  - Individual neurons are polysemantic (as expected for a 124M
    model). Top-key and top-value tokens for the most-active neurons
    are mostly noise (odd BPE fragments). So the figure does NOT
    claim individual-neuron-level labels — it labels ILLUSTRATIVE
    patterns that reflect the aggregate layer-level themes.

Layout:
  Left  — input arrow:  "contextualized 'tower' (from attention)"
  Mid   — neuron grid:   ~200 dots schematic for the 3072 neurons
                         of ONE MLP block, sparsely lit
  Right — output arrow:  "+ features written back to 'tower' residual"

Layers (for tree.json `show`):

  mlp-library   — the full grid of dim neurons (base MLP block visual)
  mlp-firing    — amber highlight on a sparse subset of neurons
  mlp-labels    — callouts naming illustrative patterns on a few of
                  the firing neurons
  mlp-output    — output arrow with the written-back-features annotation

Regenerate with:
    python workspace/build_interactive_eiffel_mlp_svg.py
"""

from __future__ import annotations

import os

import numpy as np


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
OUT_SVG    = os.path.join(REPO_ROOT, "interactive_talk", "resources",
                          "eiffel_mlp.svg")


# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------

WIDTH, HEIGHT = 960, 620

# Palette — match eiffel_attention.svg / other interactive-talk figures.
BG             = "#141414"
FG             = "#e8e8e8"
TITLE_COLOR    = "#b8b8b8"
SUBTITLE_COLOR = "#8a8a8a"
DIM_COLOR      = "#777"
NEURON_DIM     = "#444"
NEURON_LIT     = "#fbbf24"
NEURON_MID     = "#b88c27"   # medium-lit neurons (some activation but not top)
AMBER          = "#fbbf24"
ARROW_COLOR    = "#cdd6e6"
LABEL_COLOR    = "#e8e8e8"
CALLOUT_COLOR  = "#e8b649"

# Layout regions (in SVG pixel space)
TITLE_Y        = 42
SUBTITLE_Y     = 66
BLOCK_TOP      = 130
BLOCK_BOT      = 490
BLOCK_LEFT     = 280
BLOCK_RIGHT    = 690

# Input/output arrow regions
IN_X           = 70
IN_END_X       = BLOCK_LEFT - 20
OUT_X          = BLOCK_RIGHT + 20
OUT_END_X      = WIDTH - 70
ARROW_Y        = (BLOCK_TOP + BLOCK_BOT) // 2


# Neuron grid — schematic for 3072. A compact grid conveys "many,
# sparsely firing" without trying to enumerate all 3072 (which would
# be unreadable at this canvas size).
GRID_COLS = 20
GRID_ROWS = 10
NEURON_R  = 5

# Hand-picked positions (row, col) where neurons "fire" — chosen for
# pedagogical spread and to carry the callouts. The number (~8/200,
# i.e. 4%) matches the measured sparsity (|a|>0.5 cells at L10-L11
# were 99-124 out of 3072, i.e. 3-4%).
FIRING_POS = [
    (1, 2), (2, 7), (3, 13), (4, 4),
    (5, 11), (6, 16), (7, 6), (8, 14),
]
# A second tier of mid-lit neurons to convey "many small activations
# beyond the strongest ones" — matches measurement that |a|>0.1 is a
# majority of neurons.
MID_POS = [
    (0, 5), (0, 12), (1, 18), (2, 2), (2, 17),
    (3, 8), (4, 15), (5, 1), (5, 19), (6, 3),
    (7, 10), (8, 6), (8, 18), (9, 9), (9, 14),
]

# Illustrative pattern labels on a subset of firing neurons. These
# labels summarize the LAYER-LEVEL aggregate themes we measured, not
# individual-neuron-level interpretations (which are polysemantic and
# noisy in GPT-2 small).
#
# Mapping to (row, col) from FIRING_POS. Order matters for callout
# placement — callouts go to the LEFT of the grid or RIGHT depending
# on which side is closer to the edge.
CALLOUTS = [
    {"pos": (1, 2),   "text": "&#8220;tall / vertical&#8221;",     "side": "left"},
    {"pos": (7, 6),   "text": "&#8220;metal / iron&#8221;",        "side": "left"},
    {"pos": (3, 13),  "text": "&#8220;located / situated&#8221;",  "side": "right"},
    {"pos": (8, 14),  "text": "&#8220;famous landmark&#8221;",     "side": "right"},
]


# ---------------------------------------------------------------------------
# Emitters
# ---------------------------------------------------------------------------

def neuron_xy(row: int, col: int) -> tuple[float, float]:
    """Pixel center of the (row, col) dot in the grid."""
    x0 = BLOCK_LEFT + 28
    x1 = BLOCK_RIGHT - 28
    y0 = BLOCK_TOP + 40
    y1 = BLOCK_BOT - 40
    x = x0 + (col / (GRID_COLS - 1)) * (x1 - x0)
    y = y0 + (row / (GRID_ROWS - 1)) * (y1 - y0)
    return x, y


def emit_defs() -> list[str]:
    return [
        '  <defs>',
        f'    <marker id="arrow-in" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{ARROW_COLOR}"/>',
        '    </marker>',
        f'    <marker id="arrow-out" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{AMBER}"/>',
        '    </marker>',
        '  </defs>',
    ]


def emit_title() -> list[str]:
    return [
        f'  <text x="{WIDTH // 2}" y="{TITLE_Y}" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="17" font-weight="500">'
        f'The MLP block &#8212; a bank of learned patterns</text>',
        f'  <text x="{WIDTH // 2}" y="{SUBTITLE_Y}" text-anchor="middle" '
        f'fill="{SUBTITLE_COLOR}" font-size="12" font-style="italic">'
        f'after attention, each layer applies ~3072 pattern-detectors to the contextualized token</text>',
    ]


def emit_block_scaffold() -> list[str]:
    """The outline of the MLP block + the always-visible input label and
    'MLP block' caption above the grid. Input/output arrows are layers."""
    out = []
    # Rounded rectangle for the MLP block
    out.append(
        f'  <rect x="{BLOCK_LEFT}" y="{BLOCK_TOP}" '
        f'width="{BLOCK_RIGHT - BLOCK_LEFT}" '
        f'height="{BLOCK_BOT - BLOCK_TOP}" '
        f'fill="none" stroke="{DIM_COLOR}" stroke-width="1.2" '
        f'rx="8" ry="8" opacity="0.7"/>')
    # Block label
    out.append(
        f'  <text x="{(BLOCK_LEFT + BLOCK_RIGHT) // 2}" '
        f'y="{BLOCK_TOP - 14}" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="13" font-weight="600" '
        f'font-style="italic">MLP block (one of 12)</text>')
    out.append(
        f'  <text x="{(BLOCK_LEFT + BLOCK_RIGHT) // 2}" '
        f'y="{BLOCK_BOT + 22}" text-anchor="middle" '
        f'fill="{DIM_COLOR}" font-size="11" font-style="italic">'
        f'768 &#8594; 3072 hidden &#8594; 768</text>')
    # Static side captions — input/output arrows LAYERS fill in the
    # actual arrow+label for each direction.
    return out


def emit_input_layer() -> list[str]:
    """Layer `mlp-input`: the incoming arrow + "contextualized tower" label."""
    out = ['  <g class="layer" id="mlp-input">']
    out.append(
        f'    <line x1="{IN_X}" y1="{ARROW_Y}" '
        f'x2="{IN_END_X}" y2="{ARROW_Y}" '
        f'stroke="{ARROW_COLOR}" stroke-width="2.2" '
        f'marker-end="url(#arrow-in)"/>')
    # Label ABOVE the arrow
    out.append(
        f'    <text x="{(IN_X + IN_END_X) // 2}" y="{ARROW_Y - 14}" '
        f'text-anchor="middle" fill="{LABEL_COLOR}" font-size="12" '
        f'font-weight="600">contextualized &#8216;tower&#8217;</text>')
    # Second line with honest framing
    out.append(
        f'    <text x="{(IN_X + IN_END_X) // 2}" y="{ARROW_Y + 22}" '
        f'text-anchor="middle" fill="{DIM_COLOR}" font-size="10" '
        f'font-style="italic">vector written by attention</text>')
    out.append('  </g>')
    return out


def emit_library_layer() -> list[str]:
    """Layer `mlp-library`: the full grid of neuron dots, all dim.
    This is the "library of patterns" reveal — just the structure, no
    activation yet."""
    out = ['  <g class="layer" id="mlp-library">']
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x, y = neuron_xy(row, col)
            out.append(
                f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{NEURON_R - 1}" '
                f'fill="{NEURON_DIM}" opacity="0.7"/>')
    # Small caption inside the block
    out.append(
        f'    <text x="{(BLOCK_LEFT + BLOCK_RIGHT) // 2}" '
        f'y="{BLOCK_TOP + 20}" text-anchor="middle" '
        f'fill="{DIM_COLOR}" font-size="10" font-style="italic">'
        f'~3072 learned pattern-detectors (shown: 1 per ~15)</text>')
    out.append('  </g>')
    return out


def emit_firing_layer() -> list[str]:
    """Layer `mlp-firing`: highlight the sparse subset that activate
    strongly. Mid-tier neurons are also lit to convey the "most
    neurons have small non-zero activations, a few have large ones"
    distribution we measured."""
    out = ['  <g class="layer" id="mlp-firing">']
    # Mid-tier neurons (moderate activation)
    for row, col in MID_POS:
        x, y = neuron_xy(row, col)
        out.append(
            f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{NEURON_R - 0.5}" '
            f'fill="{NEURON_MID}" opacity="0.75"/>')
    # Strongly firing neurons
    for row, col in FIRING_POS:
        x, y = neuron_xy(row, col)
        out.append(
            f'    <circle cx="{x:.1f}" cy="{y:.1f}" r="{NEURON_R + 1.5}" '
            f'fill="{NEURON_LIT}" opacity="0.95"/>')
    # Note under the block
    out.append(
        f'    <text x="{(BLOCK_LEFT + BLOCK_RIGHT) // 2}" '
        f'y="{BLOCK_BOT - 16}" text-anchor="middle" '
        f'fill="{SUBTITLE_COLOR}" font-size="11" font-style="italic">'
        f'only a sparse handful fire strongly on this input</text>')
    out.append('  </g>')
    return out


def emit_labels_layer() -> list[str]:
    """Layer `mlp-labels`: callouts on a few firing neurons with
    illustrative pattern names. Labels are pedagogical, not literal
    neuron interpretations — see module docstring.
    """
    out = ['  <g class="layer" id="mlp-labels">']
    for c in CALLOUTS:
        row, col = c["pos"]
        text = c["text"]
        side = c["side"]
        nx, ny = neuron_xy(row, col)
        if side == "left":
            # Callout to the LEFT of the block
            lx = BLOCK_LEFT - 10
            ly = ny
            out.append(
                f'    <line x1="{nx:.1f}" y1="{ny:.1f}" '
                f'x2="{lx:.1f}" y2="{ly:.1f}" '
                f'stroke="{CALLOUT_COLOR}" stroke-width="1" opacity="0.6" '
                f'stroke-dasharray="3,2"/>')
            out.append(
                f'    <text x="{lx - 4:.1f}" y="{ly + 4:.1f}" '
                f'text-anchor="end" fill="{CALLOUT_COLOR}" '
                f'font-size="11" font-style="italic">{text}</text>')
        else:
            lx = BLOCK_RIGHT + 10
            ly = ny
            out.append(
                f'    <line x1="{nx:.1f}" y1="{ny:.1f}" '
                f'x2="{lx:.1f}" y2="{ly:.1f}" '
                f'stroke="{CALLOUT_COLOR}" stroke-width="1" opacity="0.6" '
                f'stroke-dasharray="3,2"/>')
            out.append(
                f'    <text x="{lx + 4:.1f}" y="{ly + 4:.1f}" '
                f'text-anchor="start" fill="{CALLOUT_COLOR}" '
                f'font-size="11" font-style="italic">{text}</text>')
    # Honesty note at the bottom
    out.append(
        f'    <text x="{WIDTH // 2}" y="{HEIGHT - 30}" text-anchor="middle" '
        f'fill="{SUBTITLE_COLOR}" font-size="10" font-style="italic">'
        f'labels are illustrative &#8212; real neurons mix many patterns, '
        f'only the layer-level aggregate is cleanly interpretable'
        f'</text>')
    out.append('  </g>')
    return out


def emit_output_layer() -> list[str]:
    """Layer `mlp-output`: the outgoing arrow + what gets written.
    Label names the AGGREGATE themes we actually measured across
    middle/late MLP layers (located, tall, landmark-like)."""
    out = ['  <g class="layer" id="mlp-output">']
    out.append(
        f'    <line x1="{OUT_X}" y1="{ARROW_Y}" '
        f'x2="{OUT_END_X}" y2="{ARROW_Y}" '
        f'stroke="{AMBER}" stroke-width="2.2" '
        f'marker-end="url(#arrow-out)"/>')
    out.append(
        f'    <text x="{(OUT_X + OUT_END_X) // 2}" y="{ARROW_Y - 14}" '
        f'text-anchor="middle" fill="{AMBER}" font-size="12" '
        f'font-weight="600">+ &#8216;landmark-like&#8217; features</text>')
    out.append(
        f'    <text x="{(OUT_X + OUT_END_X) // 2}" y="{ARROW_Y + 22}" '
        f'text-anchor="middle" fill="{DIM_COLOR}" font-size="10" '
        f'font-style="italic">written into &#8216;tower&#8217; residual</text>')
    out.append('  </g>')
    return out


def build_svg() -> str:
    lines = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Iosevka, \'JetBrains Mono\', monospace">')
    lines.append('  <!--')
    lines.append('    Generated by workspace/build_interactive_eiffel_mlp_svg.py')
    lines.append('    Schematic "library of learned patterns" view of one MLP block.')
    lines.append('    Sparsity and pattern-theme labels are calibrated to real GPT-2 small')
    lines.append('    measurements at the \' tower\' position in the Eiffel sentence; see')
    lines.append('    workspace/probe_eiffel_mlp_v2.py. Edit the script and regenerate.')
    lines.append('  -->')

    lines.extend(emit_defs())
    lines.extend(emit_title())
    lines.extend(emit_block_scaffold())

    # Layers
    lines.extend(emit_input_layer())
    lines.extend(emit_library_layer())
    lines.extend(emit_firing_layer())
    lines.extend(emit_labels_layer())
    lines.extend(emit_output_layer())

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main() -> None:
    svg = build_svg()
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_SVG}  ({len(svg.splitlines())} lines)")


if __name__ == "__main__":
    main()
