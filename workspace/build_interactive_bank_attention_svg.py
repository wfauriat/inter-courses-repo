"""
build_interactive_bank_attention_svg.py
=======================================

Schematic figure for INTRODUCING attention — at the point in the talk
where transformer architecture, layers, and heads have not been
unpacked yet. The job of this figure is to carry one idea:

    A word's meaning is shaped by the other words it looks at.

Two sentences, both ending in "bank". Above each, curved arcs run
from "bank" back to each of its preceding tokens — arc thickness is
attention strength. In each sentence, one arc is dominant:
fishing → bank (river) / deposit → bank (money). Below each "bank",
a small italic cluster names the resulting contextual sense.

No GPT-2 backend. The weights are hand-picked for narrative.

Reasons this is schematic, not model-data-backed:

  1. Pedagogical timing: attention is being introduced BEFORE
     transformer internals. Per-layer, per-head attention readings
     would land in an audience that has nothing to hang them on.
     (The logit-lens sibling figure `bank_disambig.svg` is a later,
     more technical beat — it assumes layers.)

  2. Skepticism about post-hoc attention interpretation (see memory
     `feedback_attention_post_hoc_skepticism.md`). Real per-head
     weights don't consistently show the clean "pronoun → antecedent"
     pattern you'd want for a layman figure; picking the head that
     happens to work overclaims interpretability. A clearly
     hand-drawn schematic sidesteps the problem honestly.

Layer groups (for tree.json `show`):
    attention-river    arcs above "He sat fishing on the bank"
                       + "fishing" re-highlighted amber
                       + "↓ water · shore · fishing" sense cluster
    attention-money    same for "He made a deposit at the bank"
"""

from __future__ import annotations

import os


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
OUT_SVG    = os.path.join(REPO_ROOT, "interactive_talk", "resources",
                          "bank_attention.svg")

SENTENCE_RIVER = ["He", "sat", "fishing", "on", "the", "bank"]
SENTENCE_MONEY = ["He", "made", "a", "deposit", "at", "the", "bank"]

# Schematic attention weights from "bank" back to each preceding token.
# Hand-picked to tell the story; the numbers are never shown. The
# non-dominant words are kept to only 2 each so the figure doesn't
# become a cluttered fan of arcs.
WEIGHTS_RIVER = {"fishing": 0.55, "sat": 0.15, "on": 0.08}
WEIGHTS_MONEY = {"deposit": 0.55, "made": 0.15, "at": 0.08}

# Sense cluster shown below "bank" in each context. Middle dot used as
# separator — reads as a small constellation of associated concepts,
# echoing the cluster metaphor from the embedding chapter.
SENSE_RIVER = "water · shore · fishing"
SENSE_MONEY = "money · account · deposit"

# -----------------------------------------------------------------
# Canvas / palette
# -----------------------------------------------------------------
WIDTH, HEIGHT = 900, 500

FG             = "#e8e8e8"
TITLE_COLOR    = "#b8b8b8"
DIM_COLOR      = "#777"
ARC_WEAK       = "#555"
AMBER          = "#fbbf24"     # "bank" + dominant-neighbor + dominant-arc
SENSE_COLOR    = "#b8b8b8"
SUBTITLE_COLOR = "#8a8a8a"

# Layout
TITLE_Y      = 40
SUBTITLE_Y   = 68
RIVER_Y      = 210
MONEY_Y      = 380
SENSE_DY     = 38              # vertical offset from sentence to sense cluster

# Arc geometry — peak height is a fraction of the horizontal span, so
# short arcs (bank → the) stay short and long arcs (bank → fishing)
# sweep up dramatically. Capped so the longest arcs don't overshoot.
ARC_PEAK_FRAC = 0.38
MAX_ARC_PEAK  = 95

# Text metrics (for right-justified sentence layout in Iosevka)
CHAR_W         = 11.0          # approx per-char width at 20pt
WORD_GAP_CHARS = 1.3           # visual gap between words (space char width + a bit)
# "bank" ends at this x in both sentences. Chosen so the sense cluster
# (centered under bank) fits inside the canvas.
RIGHT_EDGE     = 650


# -----------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------
def layout_tokens(words: list[str]) -> list[tuple[str, float]]:
    """Right-justify the sentence so both contexts' 'bank' end at the
    same x. Returns [(word, center_x), ...]."""
    total = sum(len(w) for w in words) + WORD_GAP_CHARS * (len(words) - 1)
    x_cursor = RIGHT_EDGE - total * CHAR_W
    out: list[tuple[str, float]] = []
    for i, w in enumerate(words):
        cx = x_cursor + len(w) * CHAR_W / 2
        out.append((w, cx))
        x_cursor += len(w) * CHAR_W
        if i < len(words) - 1:
            x_cursor += WORD_GAP_CHARS * CHAR_W
    return out


def arc_path(x1: float, x2: float, y: float, peak_h: float) -> str:
    """Quadratic bezier from (x1, y) to (x2, y) peaking at y - peak_h.
    Control point y = y - 2*peak_h so the curve's apex lands at y -
    peak_h (bezier midpoint is halfway between endpoint and control)."""
    midx = (x1 + x2) / 2
    ctrly = y - 2 * peak_h
    return f"M {x1:.1f} {y:.1f} Q {midx:.1f} {ctrly:.1f} {x2:.1f} {y:.1f}"


def render_token(word: str, cx: float, y: float, color: str,
                 weight: str = "500") -> str:
    return (f'  <text x="{cx:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'fill="{color}" font-size="20" font-weight="{weight}" '
            f'font-style="italic" '
            f'font-family="Iosevka, \'JetBrains Mono\', monospace">'
            f'{word}</text>')


def render_sentence_base(words: list[str], y: float) -> list[str]:
    """Base rendering: all tokens in FG except 'bank' in amber."""
    lines = []
    for w, cx in layout_tokens(words):
        is_bank = (w == "bank")
        color = AMBER if is_bank else FG
        weight = "700" if is_bank else "500"
        lines.append(render_token(w, cx, y, color, weight))
    return lines


def render_attention_layer(layer_id: str, words: list[str], y: float,
                           weights: dict[str, float], dominant: str,
                           sense: str) -> list[str]:
    """Arcs + dominant re-highlight + sense cluster for one context."""
    positions = {w: cx for w, cx in layout_tokens(words)}
    bank_x = positions["bank"]

    lines = [f'  <g class="layer" id="{layer_id}">']

    # Arcs — draw weakest first so the dominant sits on top.
    for w, weight in sorted(weights.items(), key=lambda kv: kv[1]):
        if w not in positions:
            continue
        tx = positions[w]
        span = abs(bank_x - tx)
        peak = min(span * ARC_PEAK_FRAC, MAX_ARC_PEAK)
        is_dom = (w == dominant)
        stroke = AMBER if is_dom else ARC_WEAK
        # Thickness scales with weight; dominant gets a strong floor.
        sw = 4.2 if is_dom else (1.0 + weight * 5)
        opacity = 0.95 if is_dom else 0.55
        # Arc sits 14px above baseline so it clears the ascenders.
        lines.append(
            f'    <path d="{arc_path(tx, bank_x, y - 14, peak)}" '
            f'stroke="{stroke}" stroke-width="{sw:.2f}" fill="none" '
            f'opacity="{opacity}" stroke-linecap="round"/>')

    # Overlay: re-render the dominant neighbor in amber so its color
    # turns on when the layer fires.
    if dominant in positions:
        lines.append(render_token(dominant, positions[dominant], y, AMBER, "600"))

    # Sense cluster: one italic line below the bank position.
    lines.append(
        f'    <text x="{bank_x:.1f}" y="{y + SENSE_DY:.1f}" '
        f'text-anchor="middle" fill="{SENSE_COLOR}" '
        f'font-size="13" font-style="italic" letter-spacing="0.5">'
        f'↓ {sense}</text>')

    lines.append('  </g>')
    return lines


# -----------------------------------------------------------------
# SVG assembly
# -----------------------------------------------------------------
def build_svg() -> str:
    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Iosevka, \'JetBrains Mono\', monospace">')
    lines.append('  <!--')
    lines.append('    Generated by workspace/build_interactive_bank_attention_svg.py')
    lines.append('    Schematic figure — attention weights hand-chosen, not model output.')
    lines.append('  -->')

    # Title
    lines.append(
        f'  <text x="{WIDTH // 2}" y="{TITLE_Y}" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="17" font-weight="500">'
        'Attention — a word takes on meaning from the neighbors it looks at'
        '</text>')
    # Subtitle
    lines.append(
        f'  <text x="{WIDTH // 2}" y="{SUBTITLE_Y}" text-anchor="middle" '
        f'fill="{SUBTITLE_COLOR}" font-size="12" font-style="italic">'
        'same word, two sentences — different neighbors, different meaning'
        '</text>')

    # Base sentences (both, with "bank" amber)
    lines.extend(render_sentence_base(SENTENCE_RIVER, RIVER_Y))
    lines.extend(render_sentence_base(SENTENCE_MONEY, MONEY_Y))

    # Layers
    lines.extend(render_attention_layer(
        "attention-river", SENTENCE_RIVER, RIVER_Y,
        WEIGHTS_RIVER, "fishing", SENSE_RIVER))
    lines.extend(render_attention_layer(
        "attention-money", SENTENCE_MONEY, MONEY_Y,
        WEIGHTS_MONEY, "deposit", SENSE_MONEY))

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main() -> None:
    svg = build_svg()
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
