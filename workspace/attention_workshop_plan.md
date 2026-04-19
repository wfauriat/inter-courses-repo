# Attention / Q-K-V Workshop — Plan

A standalone PySide app, separate from `GPT_arch_workshop.py`. Its only job is
to make the **construction** of attention legible: how Q, K, V come out of a
single hidden state and a single bundled weight, and how the score row →
softmax → weighted V pipeline produces the per-token attention output.

The existing GPT-arch workshop already shows the *output* of attention as a
heatmap. This workshop shows the *machinery upstream* of that heatmap.

---

## What it teaches

The user should walk away able to answer, unprompted:

1. Where do Q, K, V come from? (One bundled `c_attn` weight, sliced into
   three n_embd-wide blocks; each token's hidden state is multiplied by them
   independently.)
2. What does "12 heads of dim 64" actually mean? (The 768-d output of each of
   W_Q/W_K/W_V is reshaped into 12 contiguous 64-d slices; one head sees
   only its own slice.)
3. Why does Q come from the *query* token but K/V come from *all* tokens?
   (Q asks "what am I looking for"; K/V are answered by every token in
   context. The same hidden state plays both roles, just under different
   matrices.)
4. What is the score row? (`Q_q · K_j / √d_head` for every j ≤ q under
   causal masking — one scalar per candidate key.)
5. What does softmax do, and what does the output vector represent?
   (Weighted average of V vectors; the attention layer's contribution to
   the residual stream for token q comes from this, after the c_proj output
   projection.)

Out of scope (explicitly): MLP, LayerNorm internals, output projection
mechanics, multi-head fusion as an interactive feature (mentioned, not
explored), cross-prompt comparisons.

---

## Backend

Reuse model loading from `GPT_arch_workshop.py` (HuggingFace GPT-2 small,
`attn_implementation="eager"`). Add a small helper module that, for a given
`(prompt, layer, head)`:

- Captures the input to the attention sublayer — i.e. `ln_1(h_prev)` — via
  a forward hook on `block.attn.c_attn` (input is post-ln_1 already).
- Pulls `W_c_attn = block.attn.c_attn.weight` (shape `(768, 2304)`) and
  splits into `W_Q, W_K, W_V` each `(768, 768)`. Skip biases for the visual
  story; mention they exist in a small footnote.
- Slices the chosen head's columns: `W_Q_h = W_Q[:, h*64:(h+1)*64]`, same
  for W_K, W_V. Verify this matches HF's internal reshape order — there is
  one gotcha here, the order is `(n_heads, d_head)` contiguous, so
  per-head slicing on the *output* dim is correct.
- Computes Q (1×64) for the chosen query token, K and V (seq×64) for all
  tokens, score row (1×seq), softmax weights (1×seq), and output (1×64).
- Optionally also projects the output through `c_proj` to show the
  resulting residual contribution back in 768-d.

Sanity: cross-check the manually computed softmax weights against the
attention weights HF returns. They must match to fp32 noise. This goes in
the test/probe alongside the app, not in the UI.

---

## Panel layout (sketch)

Top control bar:
- Prompt input (text field, default `"The Eiffel Tower is in the city of"`).
- Layer selector (0..11).
- Head selector (0..11). No "all heads avg" — this app is about looking at
  one head.
- Query-token selector (combo of decoded tokens; default = last token).
- Toggle: "Show c_proj output" (default OFF — see stage 7).
- Toggle: "Soften" (drop position-0 sink in bar charts, off by default).

Each stage carries a compact formula in its subtitle so the math is always
on screen alongside the picture (e.g., `Q = h · W_Q   (1×64)`). Shapes are
labeled on every panel so the dimension changes are visible.

Main area, vertical pipeline (top → bottom):

1. **Hidden state h_q** — the input to attention for the query token.
   Compact bar/heatmap of the 768-d vector.
   Subtitle: `h_q ∈ ℝ^768`.
2. **Bundled c_attn weight** — schematic of `(768 × 2304)` shown as three
   stacked blocks `[ W_Q | W_K | W_V ]`, with the chosen head's 64-column
   slice highlighted in each block. This is the "one matrix doing three
   jobs" picture. Tooltip on the schematic notes that biases are also
   added but omitted from the visualization for clarity.
   Subtitle: `c_attn ∈ ℝ^(768 × 2304) = [W_Q | W_K | W_V]`.
3. **Q, K, V vectors** — three side-by-side panels:
   - Q: just the query token's 64-d vector.    `Q = h_q · W_Q   (1×64)`
   - K: all tokens stacked, `(seq × 64)` heatmap.   `K = H · W_K   (seq×64)`
   - V: same, `(seq × 64)` heatmap.                 `V = H · W_V   (seq×64)`
4. **Score row** — bar chart of `Q · K_jᵀ / √64` for every key j. Causal
   mask shown as greyed-out bars, not removed (so the reader sees what's
   being suppressed).
   Subtitle: `s_j = Q · K_jᵀ / √64`.
5. **Softmax weights** — bar chart, same x-axis as the score row, with the
   masked positions at zero. Annotate the top-1 and top-3 weights.
   Stacked directly under the score row (same width) so the
   before-mask vs after-softmax comparison is obvious.
   Subtitle: `α_j = softmax(s)_j`.
6. **Per-head output** — `Σ_j α_j · V_j`, shown as a 64-d vector panel.
   This is what one head produces.
   Subtitle: `out_h = Σ_j α_j · V_j   ∈ ℝ^64`.
7. **Residual contribution** (toggle, default OFF) — the post-`c_proj`
   768-d vector that actually gets added to the residual stream for token
   q. This includes contributions from *all 12 heads*, not just the
   selected one — concatenating per-head outputs and applying `c_proj` is
   the closing step of the attention sublayer. Captured via a forward
   hook on `block.attn` (matches the existing explorer's `attn_deltas`).
   Subtitle: `Δ_attn = c_proj([out_0 ⊕ ... ⊕ out_11])   ∈ ℝ^768`.

Layout shape: PySide `QScrollArea` containing a `QWidget` with a
`QVBoxLayout`. Each stage is a matplotlib `FigureCanvas` of fixed height.
Resize behavior is "scroll, not shrink" — the panels need consistent
height to be readable.

---

## Controls

- Prompt: text field + "Run" button. Recompute on submit only (not live).
- Layer / Head / Query-token: combo boxes; auto-recompute on change.
- Toggles:
  - "Show c_proj output" (default off) — adds the residual-contribution
    panel.
  - "Highlight top-k attended tokens" (default 3).
  - "Soften" (drop the position-0 sink in the bar charts) — same idea as
    the existing explorer.

No view radios, no PCA axis selector, no logit-lens. This app does *one*
thing.

---

## Confirmed design decisions

1. Layer / head / query-token are all **selectable** — exploration is the
   point of an interactive app. Comparing different heads at the same layer
   is one of the great teaching moments here.
2. **No compare-two-heads mode in v1.** Defer to v2 once the
   single-head story works.
3. **Biases omitted from the visualization**, mentioned in a tooltip on
   the c_attn schematic. Biases are a token-independent DC offset that
   would visually dominate the small Q/K/V panels without adding insight.
4. **Score row and softmax stacked vertically**, same width, same x-axis.
   The before-mask vs after-softmax comparison is the main reveal; it
   should be unmissable.
5. **Compact formulas in every panel subtitle**, not in axis labels or per
   cell. The math is the actual language and anchors the picture for a
   talk audience.
6. **Pipeline ends at the c_proj 768-d residual contribution**, behind a
   default-off toggle. Without it the user is left thinking "and then
   what"; with it there's a clean bridge to the residual-stream
   trajectory in the GPT-arch workshop. Default off so v1 stays focused
   on Q/K/V; flip on for the closing beat.

---

## File structure

- `workspace/GPT_arch_workshop.py` — the existing all-views explorer
  (previously `interactive_explorer_v2.py`, now renamed).
- `workspace/attention_workshop.py` — the new app described here.
- `workspace/_attn_backend.py` — small shared module for Q/K/V
  computation and the sanity probe, importable by both the app and any
  one-off scripts. Optional; can also be inlined.

---

## Build order, if greenlit

1. Backend helper: load GPT-2 once, expose `compute_qkv(prompt, layer,
   head, query_idx) -> namedtuple` with everything the UI needs. Probe
   script verifies softmax weights match HF's reported attention.
2. Skeleton app: prompt + selectors + one placeholder panel that prints
   shapes. Confirm the layer/head/token selection plumbing works.
3. Add panels in order: hidden state → c_attn schematic → Q/K/V → score
   row → softmax → output. Stop after each one and look at it before
   building the next.
4. Polish pass: titles, axis labels, the "soften" toggle, optional
   c_proj.
