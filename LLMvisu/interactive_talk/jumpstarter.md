# Interactive talk — jumpstarter

For a fresh Claude picking up this project: read **this** file + `specs.md`
and you're oriented. Don't read `app.js` / `style.css` unless you need to
edit them — their load-bearing internals are summarized below.

---

## What this is

A keyboard-driven, browser-based presentation viewer for a talk on how
LLMs work. Lives at `interactive_talk/`. No build step, no framework —
open `index.html` in a browser, hit `← / → / ↑ / ↓`.

Pedagogical goal: refinement viewer, not slide deck. Each node rewords
or extends its parent; DFS-preorder is the default reading path, but the
speaker can branch live.

---

## Files and what to edit

**Content (the stuff you'll actually touch):**
- `tree.json` — all talk content. Flat `nodes` map + nested `tree`
  outline. Authoring contract is fully specified in `specs.md` §
  "Authoring contract" — read that before editing node shape.
- `resources/*.svg` — layered figures rendered in the side panel.
  Generated from `workspace/build_interactive_*.py` (see § "Building SVG
  figures" below). **Do not regenerate existing SVGs without explicit
  user approval** — some have been hand-tuned after generation and
  re-running the script would clobber those edits. New figures: fine
  to generate. Existing figures: ask first.

**Viewer (don't touch unless you need to):**
- `index.html` — minimal shell; loads `app.js` + `style.css`.
- `app.js` (~990 lines) — all logic, minimap included. Summary below.
- `style.css` (~215 lines) — teletype aesthetic + figure panel + minimap. Summary below.
- `old_index.html` + `old_app.js` — archival pre-minimap shell, kept as
  a read-only fallback. There used to be a v1/v2 split; v2 has been
  folded into `app.js` as the single viewer.

**Design:**
- `specs.md` — **source of truth for viewer behavior and authoring
  contract.** Covers: `tree.json` shape, `diff` vs `rewrite` mode,
  `[[...]]` highlight syntax, figure types (static image vs layered
  SVG), keyboard bindings, SVG layer convention. Read this first when
  editing nodes or adding figures.

---

## tree.json at a glance

Node fields: `text` (required), `mode` (`"rewrite"` or default `"diff"`),
`figure` (optional — `"foo.png"` for static, or
`{ "svg": "foo.svg", "show": ["layer-id", ...] }` for layered),
`technical` (optional `true` — hides the subtree in light mode; see
§ "Mode filter").

Top-level fields: `root` (id), `nodes` (map), `tree` (outline),
`tips` (optional array — chapter markers used by the minimap; see
§ "Minimap").

`[[word or phrase]]` marks highlights (rendered via `.fresh` class).
Avoid pure integer keys (`"0"`, `"1"`) — JSON parsers reorder those.
See the naming convention below.

**Naming convention.** Node ids are short semantic tags tied to what
the node says: `sRoot`, `sNextWord`, `sMachin`, `sTok`, `sEmb`,
`sSpace`, `sArithm`. Sequential refinements of the same idea take
`b`, `c`, `d` suffixes: `sNextWord → sNextWordb → sNextWordc`.
Positional names like `s0`, `s1` are technically safe but lose
meaning as the tree gets reshuffled — semantic names stay stable and
read cleanly in diffs. Pure integer keys (`"0"`, `"42"`) are the one
thing to avoid: JSON parsers reorder them ahead of strings.

**Current tree shape** (as of 2026-04-25; regenerate with
`python3 -c "import json; d=json.load(open('tree.json'))" ...` or just
walk the outline if unsure — it drifts often):
```
sRoot
├── sUse → sUseb → sUsec → sUE1..sUE4 (each with b-variant) + sUTrans
│   (chatbot intro + concrete examples + transition)
├── sNextWord → sNextWordb → sNextWordc
│       → sGen → sGenb → sGenc → sGend
│       → sStats → sStatsb → sStatsc
│       → sNTP
│   (next-token-prediction backbone)
├── sMachin → sInWork → sInWorkb
│    ├── sTok → sTokb → sTokSol → sTokSolb
│    │   (tokenization chapter, text-only)
│    ├── sEmb
│    │   ├── sSpace → sSpaceb → sMatrix → sMatrixb → sMatrixc
│    │   │   (vector coords + matrix-of-vectors intro)
│    │   ├── sEmbLogic → sClust → sClustb → sClust1..sClust4
│    │   │   (what embeddings encode → 2D projection, cluster reveal)
│    │   ├── sArithm → sCap1..sCap4
│    │   │   (analogy geometry — country/capital)
│    │   ├── sVeh1..sVeh4 → sEmbConcl → sEmbConclb → sEmbConclc
│    │   │   (vehicle analogy + embedding-chapter wrap-up)
│    │   └── sPos → sPosb
│    │       (positional embedding, text-only)
│    ├── sAttn → sAttnb → sAttnLogic
│    │         ├── sAttnBank → sAttnBankR → sAttnBankM
│    │         ├── sAttnCas → sAttnCasb
│    │         ├── sAttnBankH → sAttnBankHb → sAttnBankHc → sAttnForm  [technical]
│    │         └── sAttnWrap
│    │   (attention setup → ambiguous-bank example → causal masking →
│    │    heads as subspace filters + QKV formula [technical] → synthesis.
│    │    sAttnWrap is the light-mode synthesis, outside the technical subtree)
│    ├── sTrans
│    │    ├── sTransEif → sTransEifArc → sTransEifDrift  [technical]
│    │    └── sTransMLP → sTransMLPBank → sTransMLPFire
│    │                → sTransMLPWrite → sTransWrap → sTransProb
│    │   (Eiffel attention [technical] + MLP "bank of learned patterns"
│    │    → three-mechanic block wrap-up → top-of-stack probability.
│    │    sTransProb is terminal in the MLP chain, not a bridge above it)
│    ├── sArch → sArchShapes
│    │          ├── sArchParams → sArchZoom  [technical]
│    │          └── sArchNature
│    │   (whole-pipeline capstone → shapes → param counts + optional
│    │    block-zoom → "it's mostly parameters" bridge to training)
│    └── sTrain → sTrainData
│         ├── sTrainStep → sTrainStepb
│         └── sTrainEmerge → sTrainEmergeb → sTrainEff → sAlign → sAlignb
│        (pretraining: what it does + why the weird machinery works
│         → sAlign bridges base-model NTP to chat-assistant via SFT+RLHF)
└── sComput
     ├── sComputTrain → sComputTrainGPU → sComputTrainAutodiff  [technical]
     ├── sComputInfer → sComputInferCost → sComputInferKV       [technical]
     └── sComputWrap
     (training vs inference compute — scale, GPUs, auto-regressive
      inference, latency; autodiff/KV-cache are technical refinements.
      sComput is a top-level sibling of sMachin, not nested inside it)
```

Embedding fans out into five sub-branches under `sEmb`:
- `sSpace → … → sMatrixc` — vector-coords intro and the matrix of
  stacked token vectors (what the model actually reads).
- `sEmbLogic → sClust → sClustb → sClust1..sClust4` — what embeddings
  encode, then 2D-projected cluster reveal.
- `sArithm → sCap1..sCap4` — analogy geometry via country/capital.
- `sVeh1..sVeh4 → sEmbConcl*` — vehicle analogy + chapter wrap-up.
- `sPos → sPosb` — positional embedding (technical sibling).

`sClust1` used to sit at the tail of the `sSpace → sMatrix` chain —
it was split out into its own sub-branch so the minimap (and the talk
flow) treats 2D clusters as a first-class stop rather than buried in
the matrix chain. `sArithm`, `sVeh*`, and `sPos` are intentionally
skippable for a layman audience.

The `sTrans → sTransEif*` chain uses the Eiffel example sentence
("In Paris today, I climbed the 1000+ steps of the famous old iron
tower.") to make attention concrete. See the generator for the
honesty caveats — the drift trajectory is a pedagogical summary
curve, not a literal 2D projection of residuals, because residual
direction in cosine-space doesn't cleanly align with wte[' Eiffel']
even though the logit-lens rank of ' Eiffel' at ' tower' drops from
~42,000 to 146.

The `sTransMLP*` chain continues the same example through the MLP
block. Sparsity shown is real (3-5% of 3072 neurons fire strongly at
' tower' per layer, per `probe_eiffel_mlp_v2.py`), and the
aggregate layer-level themes (tower/structure at L0, situated/housed
at L6, overlooking/known at L9) are real measurements. What's
schematic: the per-neuron callout labels — individual GPT-2 small
neurons are polysemantic and their top key/value tokens are
noise-like BPE fragments, so we label *illustrative* patterns
instead. The figure notes this honestly in its footer.

---

## app.js — internals summary

**Timing knobs at top (`CONFIG` object):**
`typeMs: 12`, `deleteMs`, `keepPauseMs`, `segmentPauseMs: 6`,
`rewriteFadeMs: 100`, `rewritePauseMs: 50`, `figureFadeInMs: 1000`,
`figureFadeOutMs: 150`. Change and reload.

**Load-bearing functions to grep for:**
- `reifyTree(data)` — inflates flat `nodes` + `tree` form into the
  nested traversable structure used at runtime.
- `parseHighlights(text)` → `{clean, ranges}`. Strips `[[...]]`.
- `renderWithHighlights(el, clean, ranges)` — one-shot render (root).
- `goTo(node)` — main entry. Guards `animating`, dispatches to
  `animateTransition` (diff) or `animateRewrite`, fires
  `updateFigure()` in parallel, updates breadcrumb.
- `animateTransition(...)` — diff mode. LCS token diff →
  char-by-char keep/delete/insert. Forward-direction inserts get `.fresh`.
- `animateRewrite(...)` — rewrite mode. Fade-out old → pause → type
  new with author-marked highlight ranges in `.fresh`.
- `updateFigure(node)` — same SVG as current → CSS-only layer toggle
  via `applyShowList`. Different figure → fade out, fetch+inline,
  fade in. Uses `figureToken` to reject stale async results.
- `applyShowList(show)` — toggles `.layer-visible` class on SVG
  `.layer` elements.

**DOM hooks:** `#before` + `#after` (text split; `beforeEl` accumulates
typed/kept chars, `afterEl` shrinks), `#cursor`, `#figure` (side
panel), `#breadcrumb`.

**Skip mechanism:** Any keypress during animation sets `skipRequested
= true`, which tight-loop branches check to bail to final state. The
triggering keypress is **not queued** — user presses again to
navigate. This trades speed for control.

**Non-obvious:**
- SVGs are loaded **inline** (`fetch` + `innerHTML`) so layer toggles
  operate on live DOM nodes.
- Highlight character-ranges survive the animation — in rewrite mode
  they're author-declared, in diff mode the diff algorithm computes them.
- `figureFadeInMs` / `figureFadeOutMs` propagate to CSS via custom
  properties on `#figure` — tuning `CONFIG` also tunes the CSS.

---

## style.css — internals summary

**CSS vars:** `--bg` (#141414), `--fg` (#e8e8e8), `--fg-dim` (#666),
`--fresh` (#fbbf24 amber), `--cursor`, `--divider`.

**Font:** `Iosevka`, monospace fallback.

**`.fresh`** — amber color; applied to author-marked ranges (rewrite)
or diff-inserted chars (diff, forward only).

**Layout:** `.stage-wrap` flex row, `.stage` (text column, max 720px,
1.55rem font), `.figure` (hidden by default, 620px wide when visible).

**Figure panel:** `.figure.visible` → `display: flex` + `figure-appear`
keyframe (fade 0→1). Asymmetric fade-in / fade-out via
`var(--panel-fade-in-ms)` synced from CONFIG.

**Layer toggle:** `.figure svg .layer { opacity: 0; transition 200ms }`,
`.layer.layer-visible { opacity: 1 }`. The only way layers become
visible.

**Cursor:** `#cursor` blinks via CSS animation (1.06s cycle).

---

## Mode filter (light / technical)

Two-mode talk filter on top of the DFS tree. `light` (default) hides
subtrees whose root is marked `"technical": true` in `tree.json`;
`technical` shows everything. Lives in `app.js` as the module-level
`talkMode` variable.

**Authoring.** Mark the root of a technical sub-branch:
`"sAttnBankH": { ..., "technical": true }`. The flag inherits in
`reifyTree` — every descendant is hidden in light mode. Current
technical roots: `sAttnBankH` (heads + QKV formula), `sTransEif`
(Eiffel attention case study), `sArchZoom` (transformer-block
internals), `sComputTrainAutodiff` (backprop / autodiff),
`sComputInferKV` (KV cache).

**Runtime.** `t` toggles the mode. `?mode=light|technical` in the URL
seeds the initial value (non-locking — `t` still works after). The
help strip shows current mode via `#modeValue`.

**What it affects.** `computePreorder` filters the preorder list, so
`preorderNext/Prev` and the ↑/↓ sibling cycle skip hidden nodes. The
minimap rebuilds on toggle (`setupMinimap(rawData)`): hidden tips
drop from the dot set, and trailing-content counts skip hidden
subtrees. If the current node becomes hidden on flip, `toggleMode`
snaps to the nearest visible ancestor via `goTo`.

---

## Minimap

A compact navigation skeleton above the breadcrumb. The minimap module
sits at the bottom of `app.js`; styling is scoped under `#minimap` in
`style.css`. Previously a v2-only opt-in — v2 has been folded into
`app.js` as the single viewer.

**What it shows.** Only "tip" nodes as dots. Tips come from the
`tips` field in `tree.json` (user-curated list of chapter markers):

```json
"tips": ["sRoot", "sUse", "sUTrans", "sNextWord", "sNTP",
         "sMachin", "sTok", "sEmb", "sEmbLogic", "sEmbConcl",
         "sArithm", "sVeh1", "sPos", "sAttn", "sAttnCas",
         "sAttnBankH", "sAttnWrap", "sTrans", "sTransEif",
         "sTransMLP", "sArch", "sArchNature", "sTrain",
         "sTrainStep", "sTrainEmerge", "sAlign", "sComput",
         "sComputTrain", "sComputInfer"]
```

(Tips drift — this is a 2026-04-25 snapshot. `sAttnBankH` and
`sTransEif` are technical tips; in light mode they're filtered out
of the minimap along with their subtrees.)

Content nodes (refinements between tips) are **not rendered as dots**.
They collapse into:
- **Inter-tip edges** whose length ∝ count of countable content nodes
  between parent tip and child tip. Typically short (0–1).
- **Trailing lines** past leaf tips whose length ∝ countable content
  in the tip's sub-tree. This is where the "big chapter = long branch"
  visual comes from (e.g. `sTrans` has 8 trailing content nodes in
  technical mode, 5 in light — `sTransEif`'s subtree is hidden).

A node is "countable" iff `node.mode === 'rewrite'` (see
`countsAsContent` in `app.js`). Diff-mode nodes are skipped. This
includes rewrites that reuse an SVG via `show` changes (e.g. `sClust2-4`,
`sCap*`, `sArchShapes/Params/Zoom`) — those *are* real content steps
even though they share a figure.

**Cursor.** Closest tip ancestor of `currentId` gets amber fill + glow.
For leaf tips, a second amber line (progress overlay) extends along
the trail to `tip.x + (preorderPos / (subtreeSize-1)) × trailLen`,
giving a smooth slide as the user steps through the chapter's content.
Non-leaf tips don't get a trail yet — their cursor sits on the tip dot.

**Navigation feedback is eager.** `goTo` commits `currentId`, path,
breadcrumb, and minimap *before* the text animation starts (see
`app.js:goTo`). The cursor jumps to target on keypress/click; the
text types out behind it.

**Click-to-jump.** Each tip dot is clickable → jumps directly to that
tip. Same animation guard as keyboard.

**Sibling-tip border.** When the user is *exactly at* a tip whose
full-tree visible siblings include another tip (so ↑/↓ would jump to
a sibling chapter), the tip dot gets a lighter-amber ring via
`mm-tip-sibling`. Applied dynamically in `updateMinimap`, not at
render time — the ring vanishes the moment the user steps into the
tip's subtree, so it tracks "can I sibling-jump from here?" rather
than the static structural property. `hasTipSibling` is precomputed
per tip on the layout position; visibility of the sibling follows the
current `talkMode` (so e.g. `sAttnBankH` never rings in technical mode
because its only sibling `sAttnBank` isn't a tip).

**Mode-filter interaction.** `talkMode` flips rebuild the minimap
via `setupMinimap(rawData)`: hidden tips drop out of `computeTipsSet`,
trails shorten because `countTrailingContent` skips hidden subtrees,
and `subtreeSize` uses visible-only counts (so in-trail progress
still maps cleanly). See § "Mode filter".

**Layout knobs** (top of `computeMinimapLayout` in `app.js`):
- `COLW` (viewBox units per content-step) — scales inter-tip edges
  *and* trails. Bigger = stretched branches.
- `laneH` — vertical spacing between sibling lanes.
- `MIN_EDGE` — floor on inter-tip edge length so 0-content edges still
  render as visible connectors.

**Styling knobs** (`#minimap` in `style.css`):
- `width: min(420px, 60vw)` caps display size; viewBox scales to fit.
- `opacity: 0.35` default / `0.9` on hover — kept quiet so it doesn't
  compete with the stage during presentation.
- `.mm-trail` (dim base), `.mm-trail-progress` (amber overlay).
- `.mm-node.mm-current { r: 3.4 }` — bump dot radius for the current.
- `.mm-node.mm-tip-sibling` — lighter-amber ring (`#fde68a`,
  stroke-width `2`, `paint-order: stroke fill`) for the current
  tip-with-tip-sibling.

**Known not-done.** `sEmb` is a non-leaf tip (child tips `sEmbLogic`,
`sArithm`, `sVeh1`, `sPos`) so it doesn't draw a trail. The `sSpace`
chain under `sEmb` is orphan content — not on any child-tip path —
and currently renders as nothing. Two fixes: (a) promote `sSpace` to
a leaf tip with its own trail, or (b) extend the minimap to render
orphan trails on non-leaf tips (short perpendicular ticks, say).

---

## Building SVG figures — the workshop → talk pattern

**Don't hand-author SVG.** Write a generator script at
`workspace/build_interactive_<name>.py` that emits to
`interactive_talk/resources/<name>.svg`. Regenerate by running the
script.

**Why this pattern.** Figures backed by real model/data belong on top
of code that already loads the model / runs the math — the workshops
in `workspace/`. The generator sits on top, projects or extracts what
it needs, and emits a layered SVG. Script-generated SVGs stay in sync
with data; hand-edited SVGs drift.

**Workshop backends** (reusable compute layer, in `workspace/`):
- `embedding_workshop.py` → `EmbeddingBackend` (GloVe-100d loader,
  `vectors`, `vectors_for(words)`, etc.). Used by
  `build_interactive_embedding_svg.py` (2D PCA scatter) and
  `build_interactive_analogy_svg.py` (per-chain PCA for vector
  arithmetic).
- `attention_workshop.py` — GPT-2 attention probing. Not used by the
  current schematic `sAttn` figure (which is hand-picked, no backend);
  available if a data-backed attention figure lands later (e.g. `sTrans`).
- `GPT_arch_workshop.py` — GPT-2 architecture internals. Also the
  source model (tokenizer + `wte`) for
  `build_interactive_embedding_matrix_svg.py` — that generator
  skips the `ModelBackend` wrapper and talks to `transformers`
  directly since it only needs `tok.encode` and one `wte[ids]`
  slice (no forward pass).

**Mock-geometry generators** are allowed too — no backend, hand-picked
coordinates, for pedagogical anchors where real data isn't useful.
Example: `build_interactive_token_vector_svg.py` draws a 3D triad
with two arbitrary mock vectors, no embedding lookup.

**Layered SVG contract** (also in `specs.md`):
- Toggleable groups wrapped in `<g class="layer" id="semantic-name">`.
- Non-`.layer` SVG elements = always-on base (axes, titles, grid,
  neutral scatter).
- `show` list in `tree.json` is **absolute, not cumulative** — each
  node fully declares its state.
- IDs must match `show` list entries in `tree.json`.

**Existing generators + what they produce:**
| Generator | Output | Layer ids |
|---|---|---|
| `build_interactive_embedding_svg.py` | `embedding.svg` | `animals`, `verbs`, `stats-terms`, `royalty` |
| `build_interactive_analogy_svg.py` | `embedding_analogy_capital.svg`, `embedding_analogy_vehicle.svg` | `capital-words`, `capital-sub`, `capital-add`, `capital-resolve`; same pattern with `vehicle-*` |
| `build_interactive_token_vector_svg.py` | `token_vector.svg` | `id1`, `id2` |
| `build_interactive_embedding_matrix_svg.py` | `embedding_matrix.svg` | `token-ids`, `matrix-numbers` (prompt text is base) |
| `build_interactive_bank_attention_svg.py` | `bank_attention.svg` | `attention-river`, `attention-money` (schematic, no backend — hand-picked weights) |
| `build_interactive_eiffel_attention_svg.py` | `eiffel_attention.svg` | `sentence-amber`, `attn-arcs`, `landmarks`, `drift-start`, `drift-trajectory` (GPT-2 small backend; attention arcs and Eiffel-rank annotation are real data; drift curve is pedagogical summary) |
| `build_interactive_eiffel_mlp_svg.py` | `eiffel_mlp.svg` | `mlp-input`, `mlp-library`, `mlp-firing`, `mlp-labels`, `mlp-output` (schematic; sparsity ~4% and aggregate layer themes are measured, per-neuron callouts are illustrative — no model backend used, the script just draws from the probe findings) |
| *(hand-authored, no generator)* | `gpt2_architecture.svg` | `shapes`, `params`, `block-zoom` (GPT-2 small data-flow capstone — pipeline + shape annotations + param counts + expanded transformer-block view. All numbers static; hand-written SVG, not script-generated) |

**Unwired (deferred) figure:** `build_interactive_bank_disambig_svg.py` →
`bank_disambig.svg` exists but isn't referenced in `tree.json`. It's the
logit-lens sibling of the attention figure — technical, assumes layers,
still available for reuse deeper in the `sTrans` chain if we want to
show the "what token would this residual decode to" view.

**Empirical-probe scripts** (not figure generators, but worth knowing):
- `workspace/probe_eiffel_attention.py`, `_v3.py`, `_v4.py` —
  attention weights, logit-lens ranks, contrastive sentence tests.
  Validated the attention figure's claims before building.
- `workspace/probe_eiffel_mlp.py`, `_v2.py` — MLP neuron
  interpretations (key/value top tokens), sparsity counts, and
  per-layer aggregate MLP output logit-lens. Showed that individual
  neurons are polysemantic but layer-level aggregates are clean.

**Typical workflow to add a new figure:**
1. Pick the workshop that has the data/math (or decide it's mock).
2. Write `workspace/build_interactive_<name>.py` — see existing ones
   as templates. Emit to `interactive_talk/resources/<name>.svg`.
3. Add node(s) to `tree.json` referencing `resources/<name>.svg` with
   `show` lists that match your layer ids.
4. Regenerate: `python workspace/build_interactive_<name>.py`.
5. Preview: open `index.html` in a browser, or quick-rasterize with
   `inkscape --export-type=png --export-filename=workspace/output/<name>.png
   interactive_talk/resources/<name>.svg`.

---

## Design invariants (don't violate without reason)

- **Figures generate from source, but existing SVGs may have hand
  tweaks on top.** Do not re-run `build_interactive_*.py` against an
  already-shipped SVG without explicit user approval — regeneration
  clobbers post-hoc edits. New figures are fine to generate freely.
  The generator's header comment captures design rationale (e.g. why
  PCA is fit on top-10k GloVe and not the full vocab).
- **Workshops keep scope.** GloVe-based embedding work and GPT-2-based
  attention/arch work stay separate in `workspace/` (see memory
  `feedback_glove_gpt2_disconnected.md`). The interactive talk is
  explicitly allowed to mix them for pedagogical flow — that's not a
  bug, it's the point.
- **Semantic ids in `tree.json`** (`sSpace`, `sArithm`) — not numeric.
- **Always-on base** of each SVG (title, axes, grid, neutral scatter)
  sits outside any `.layer` group.
- **`show` is absolute per node** — every node restates its full
  layer state. No cumulative Beamer-style overlays.

---

## Where to look for deeper context

- `specs.md` — viewer design + authoring contract. The canonical spec.
- `../workspace/*_workshop.py` — the three workshop backends that feed
  real data into SVG figures.
- Memory file `project_interactive_talk_svg_pattern.md` — original
  design notes on the workshop → SVG pattern, plus the PCA-fit-scope
  rationale for the embedding figure.
- Memory file `project_llm_mechanics_workshops.md` — the three-workshop
  architecture at the broader project level.
