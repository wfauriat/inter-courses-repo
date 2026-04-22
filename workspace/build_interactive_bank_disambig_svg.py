"""
build_interactive_bank_disambig_svg.py
======================================

Regenerate interactive_talk/resources/bank_disambig.svg.

Pedagogical payload: the word "bank" has two senses. We run two
sentences through GPT-2 small and — at every transformer layer —
project the hidden state sitting at the " bank" position back through
the unembedding (logit-lens). The top-k tokens at each layer show what
"bank" is internally similar to at that depth of the network.

The point of the figure: at layer 0 both contexts are identical.
Further up the stack, attention has accumulated context, and the two
representations of "bank" drift into different vocabulary
neighborhoods — geographical on the river side (ledge, floor,
overlooking) and financial on the money side (account, ATM, clerk).
Ties the attention chapter back to the embedding chapter: the
embedding figure put words in a space; this figure shows attention
moving them.

Design notes
------------
- Four layers displayed (0, 2, 6, 10). L0 is the identity baseline;
  L2 still dominated by the raw 'bank' family; L6 starts leaking
  context (money side picks up robbery/vault associations); L10 is
  the cleanest split. L11-L12 degrade into next-token-prediction
  continuation tokens ("of", ",", ".") — honest but off-topic for
  a "what does this word MEAN here" figure, so deliberately cut.

- Filter: stopwords, punctuation, BPE subword junk (`sters`, `rupt`,
  `ster`, `stown`, `notes` = 'bank*notes*') are dropped before
  top-k selection. Without this, the top rows are contaminated by
  function tokens and subword pieces that don't survive contact
  with a layman audience. Filtering is silent — the speaker can
  mention the caveat verbally.

- Layered SVG per tree.json `show` convention:
    layer-L0, layer-L2, layer-L6, layer-L10
  Each group contains BOTH columns (river + money) for that layer —
  they reveal together because the whole point is the comparison.

- Base (always visible): title, the two sentences with "bank"
  highlighted, the two column headers, the layer axis labels.

Caveats
-------
- gpt2-small (12 blocks) is enough to show the split — gpt2-medium
  would show it earlier but the small model is what the rest of the
  talk uses.
- The figure is illustration, not proof. See
  memory/feedback_attention_post_hoc_skepticism.md for the
  epistemic posture. Speaker framing: "look how the internal
  representation changes" — never "the model understands that bank
  has two meanings."
"""

from __future__ import annotations

import os

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
OUT_SVG    = os.path.join(REPO_ROOT, "interactive_talk", "resources",
                          "bank_disambig.svg")

SENTENCE_RIVER = "He sat fishing on the bank"
SENTENCE_MONEY = "He made a deposit at the bank"

# Layers to show — chosen for narrative (see header comment).
LAYERS_SHOWN = [0, 2, 6, 10]

TOP_K = 5            # tokens displayed per (layer, context) cell

# -----------------------------------------------------------------
# Canvas / palette
# -----------------------------------------------------------------
WIDTH, HEIGHT = 900, 620

FG           = "#e8e8e8"
TITLE_COLOR  = "#b8b8b8"
DIM_COLOR    = "#777"
AXIS_COLOR   = "#555"
DIVIDER      = "#3a3a3a"
AMBER        = "#fbbf24"       # "bank" highlight + top-1 token
RIVER_COLOR  = "#6aa3d5"       # cool blue — the "water" column
MONEY_COLOR  = "#d4a017"       # gold — the "money" column

# Layout anchors (SVG-y, top-down).
TITLE_Y        = 34
SENTENCE_Y     = 82
COL_HEADER_Y   = 130
LAYER_START_Y  = 180
LAYER_STEP_Y   = 102
LAYER_LABEL_X  = 52

COL_RIVER_X = 260
COL_MONEY_X = 700

# Vertical divider between columns.
DIVIDER_X = 480

# -----------------------------------------------------------------
# Filtering: drop stopwords, punctuation, and BPE junk
# -----------------------------------------------------------------
STOPWORDS = {
    "of", "and", "to", "in", "on", "at", "for", "by", "with", "as",
    "the", "a", "an", "is", "was", "be", "it", "its", "from", "or",
    "that", "this", "his", "her", "their", "who", "what", "when",
    "where", "why", "how", "if", "but", "not", "no", "yes",
    "had", "has", "have", "do", "does", "did", "will", "would",
    "can", "could", "should", "may", "might", "must", "about",
    "he", "she", "they", "we", "you", "i", "me", "him", "them", "us",
    "my", "your", "our", "off", "out", "up", "down",
}

# Subword pieces and compound-prefix artifacts that show up in
# logit-lens around "bank": 'notes' is the back half of 'banknotes',
# 'sters' of 'gangsters'/'mobsters', 'rupt' of 'bankrupt', etc.
BPE_JUNK = {
    "sters", "ster", "stown", "rupt", "notes", "note",
    "ness", "tion", "ings", "rolled", "mathemat",
}


def looks_like_content(token_str: str) -> bool:
    s = token_str.strip().lower()
    if not s:
        return False
    if not s[0].isalpha():
        return False
    if s in STOPWORDS:
        return False
    if s in BPE_JUNK:
        return False
    if len(s) <= 1:
        return False
    return True


# -----------------------------------------------------------------
# Model data: logit-lens top-k at the " bank" position per layer
# -----------------------------------------------------------------
def compute_topk_per_layer(model, tok, sentence: str,
                           layers: list[int], top_k: int
                           ) -> list[list[tuple[str, float]]]:
    """For each layer in `layers`, return a [(token, prob), ...]
    list of the top-`top_k` *content* tokens at the " bank" position,
    ranked by logit-lens softmax probability."""
    ids = tok.encode(sentence, return_tensors="pt")
    tokens = [tok.decode([int(t)]) for t in ids[0]]
    bank_idx = next(i for i, t in enumerate(tokens) if t.strip().lower() == "bank")

    with torch.no_grad():
        out = model(ids, output_hidden_states=True)

    # hidden[0] = post wte+wpe; hidden[L] = after block L for L=1..n_layers.
    hidden = torch.stack(out.hidden_states, dim=0).squeeze(1)   # (L+1, seq, d)
    bank_traj = hidden[:, bank_idx, :]                          # (L+1, d)

    # HF's final hidden state is already post-ln_f; earlier ones aren't.
    h_last = bank_traj[-1]
    true_logits = out.logits[0, bank_idx]
    with torch.no_grad():
        diff_pre  = (model.lm_head(model.transformer.ln_f(h_last)) - true_logits).abs().max().item()
        diff_post = (model.lm_head(h_last) - true_logits).abs().max().item()
    last_is_post = diff_post < diff_pre

    with torch.no_grad():
        if last_is_post:
            normed = torch.cat(
                [model.transformer.ln_f(bank_traj[:-1]), bank_traj[-1:]], dim=0)
        else:
            normed = model.transformer.ln_f(bank_traj)
        logits = model.lm_head(normed)            # (L+1, vocab)
        probs = torch.softmax(logits, dim=-1)

    result: list[list[tuple[str, float]]] = []
    for L in layers:
        # Pull a generous top band, filter, and dedupe by lowercase form.
        # Dedup matters at L0 especially — the top-5 there is dominated by
        # GPT-2's BPE variants of "bank" (' bank', 'bank', 'Bank', ...)
        # which all strip to the same visual word and would render as
        # five rows of "bank 100%, bank 0%, Bank 0%, ...".
        top_vals, top_ids = probs[L].topk(80)
        kept: list[tuple[str, float]] = []
        seen_forms: set[str] = set()
        for v, tid in zip(top_vals.tolist(), top_ids.tolist()):
            piece = tok.decode([tid])
            if not looks_like_content(piece):
                continue
            key = piece.strip().lower()
            if key in seen_forms:
                continue
            seen_forms.add(key)
            kept.append((piece.strip(), v))
            if len(kept) >= top_k:
                break
        result.append(kept)
    return result


# -----------------------------------------------------------------
# SVG rendering
# -----------------------------------------------------------------
def highlighted_sentence(sentence: str, cx: float, y: float,
                         fill: str, bank_fill: str,
                         size: int = 16) -> list[str]:
    """Render the sentence centered at (cx, y); 'bank' gets bank_fill.
    Done as one <text> with per-word <tspan>s so widths stay coherent."""
    words = sentence.split()
    parts = []
    for i, w in enumerate(words):
        is_bank = w.strip(".,!?").lower() == "bank"
        space = "" if i == 0 else " "
        color = bank_fill if is_bank else fill
        weight = "600" if is_bank else "500"
        parts.append(
            f'<tspan fill="{color}" font-weight="{weight}">{space}{w}</tspan>')
    # xml:space="preserve" so the single-space gaps between <tspan>s survive
    # SVG's default whitespace normalization. Without it, the sentence
    # renders as "Hesatfishingonthebank".
    return [
        f'  <text x="{cx:.1f}" y="{y:.1f}" text-anchor="middle" '
        f'xml:space="preserve" '
        f'font-size="{size}" font-style="italic">'
        + "".join(parts) +
        '</text>'
    ]


def render_cell(topk: list[tuple[str, float]], cx: float, y_top: float,
                top1_color: str) -> list[str]:
    """One (layer, context) cell: vertical stack of up to TOP_K tokens,
    centered on cx. Top-1 big+colored; subsequent ones smaller+dimmer.
    Probability shown to the right in a muted color, so viewers can
    read the stack as a ranked list rather than a word cloud."""
    lines: list[str] = []
    # Font sizes by rank.
    sizes = [21, 15, 13, 12, 11]
    weights = ["600", "500", "400", "400", "400"]
    colors = [top1_color, FG, FG, DIM_COLOR, DIM_COLOR]
    row_h = 18
    for rank, (tok_str, prob) in enumerate(topk):
        if rank >= len(sizes):
            break
        y = y_top + rank * row_h + sizes[rank]   # baseline
        # Honest rounding: values below 1% print as "<1%" rather than "0%".
        # The "<" must be escaped inside SVG text to avoid breaking the parser.
        pct_str = f'{prob * 100:.0f}%' if prob >= 0.01 else '&lt;1%'
        lines.append(
            f'    <text x="{cx:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'fill="{colors[rank]}" font-size="{sizes[rank]}" '
            f'font-weight="{weights[rank]}" xml:space="preserve" '
            f'font-family="Iosevka, \'JetBrains Mono\', monospace">'
            f'{tok_str}'
            f'  <tspan fill="{DIM_COLOR}" font-size="{max(9, sizes[rank] - 5)}">'
            f'{pct_str}</tspan>'
            f'</text>')
    return lines


def build_svg(topk_river: list[list[tuple[str, float]]],
              topk_money: list[list[tuple[str, float]]],
              layers: list[int]) -> str:
    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Iosevka, \'JetBrains Mono\', monospace">')
    lines.append('  <!--')
    lines.append('    Generated by workspace/build_interactive_bank_disambig_svg.py')
    lines.append('    Real GPT-2 small hidden states + logit-lens at the " bank" position.')
    lines.append('  -->')

    # --- Base: title ---
    lines.append(
        f'  <text x="{WIDTH // 2}" y="{TITLE_Y}" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="16" font-weight="500">'
        f'Same word, two contexts — attention shapes what &quot;bank&quot; '
        f'means at each layer'
        '</text>')

    # --- Base: the two sentences (with "bank" highlighted amber) ---
    lines.extend(highlighted_sentence(
        SENTENCE_RIVER, COL_RIVER_X, SENTENCE_Y,
        fill=FG, bank_fill=AMBER, size=16))
    lines.extend(highlighted_sentence(
        SENTENCE_MONEY, COL_MONEY_X, SENTENCE_Y,
        fill=FG, bank_fill=AMBER, size=16))

    # --- Base: column headers ---
    lines.append(
        f'  <text x="{COL_RIVER_X}" y="{COL_HEADER_Y}" text-anchor="middle" '
        f'fill="{RIVER_COLOR}" font-size="13" font-weight="600" '
        f'letter-spacing="1.5">RIVER CONTEXT</text>')
    lines.append(
        f'  <text x="{COL_MONEY_X}" y="{COL_HEADER_Y}" text-anchor="middle" '
        f'fill="{MONEY_COLOR}" font-size="13" font-weight="600" '
        f'letter-spacing="1.5">MONEY CONTEXT</text>')

    # --- Base: column divider (subtle) ---
    lines.append(
        f'  <line x1="{DIVIDER_X}" y1="{COL_HEADER_Y + 14}" '
        f'x2="{DIVIDER_X}" y2="{LAYER_START_Y + len(layers) * LAYER_STEP_Y - 10}" '
        f'stroke="{DIVIDER}" stroke-width="1"/>')

    # --- Base: layer-axis labels + row dividers ---
    #     Labels and dividers are base (always visible) so the axis
    #     "scaffolding" is present from the first frame. Only the
    #     token stacks inside each row are layered.
    lines.append(
        f'  <text x="{LAYER_LABEL_X - 8}" y="{COL_HEADER_Y}" text-anchor="end" '
        f'fill="{DIM_COLOR}" font-size="11" font-weight="600" '
        f'letter-spacing="1">LAYER</text>')
    for i, L in enumerate(layers):
        y = LAYER_START_Y + i * LAYER_STEP_Y
        name = "embed" if L == 0 else f"L{L}"
        lines.append(
            f'  <text x="{LAYER_LABEL_X}" y="{y + 26:.1f}" text-anchor="end" '
            f'fill="{AXIS_COLOR}" font-size="14" font-weight="500">'
            f'{name}</text>')
        # Row divider under each row (except the last).
        if i < len(layers) - 1:
            yy = y + LAYER_STEP_Y - 12
            lines.append(
                f'  <line x1="{LAYER_LABEL_X + 16}" y1="{yy}" '
                f'x2="{WIDTH - 30}" y2="{yy}" '
                f'stroke="{DIVIDER}" stroke-width="1" stroke-dasharray="2,4"/>')

    # --- Per-layer layer groups (the toggleable content) ---
    for i, L in enumerate(layers):
        y_top = LAYER_START_Y + i * LAYER_STEP_Y
        lid = f"layer-L{L}"
        lines.append(f'  <g class="layer" id="{lid}">')
        lines.extend(render_cell(topk_river[i], COL_RIVER_X, y_top, RIVER_COLOR))
        lines.extend(render_cell(topk_money[i], COL_MONEY_X, y_top, MONEY_COLOR))
        lines.append('  </g>')

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


# -----------------------------------------------------------------
# Main
# -----------------------------------------------------------------
def main() -> None:
    print("Loading gpt2 ...", flush=True)
    tok = AutoTokenizer.from_pretrained("gpt2")
    model = AutoModelForCausalLM.from_pretrained("gpt2")
    model.eval()

    print(f"Logit-lens on {SENTENCE_RIVER!r}")
    topk_river = compute_topk_per_layer(model, tok, SENTENCE_RIVER,
                                        LAYERS_SHOWN, TOP_K)
    print(f"Logit-lens on {SENTENCE_MONEY!r}")
    topk_money = compute_topk_per_layer(model, tok, SENTENCE_MONEY,
                                        LAYERS_SHOWN, TOP_K)

    # Echo the selected tokens so a future run can sanity-check without
    # opening the SVG.
    for i, L in enumerate(LAYERS_SHOWN):
        name = "embed" if L == 0 else f"L{L}"
        r = "  ".join(f"{t}({p*100:.0f}%)" for t, p in topk_river[i])
        m = "  ".join(f"{t}({p*100:.0f}%)" for t, p in topk_money[i])
        print(f"  {name:>6}  river: {r}")
        print(f"  {'':>6}  money: {m}")

    svg = build_svg(topk_river, topk_money, LAYERS_SHOWN)
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    with open(OUT_SVG, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
