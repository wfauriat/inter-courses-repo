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
- `app.js` (~550 lines) — all logic. Summary below.
- `style.css` (~200 lines) — teletype aesthetic + figure panel + minimap. Summary below.
- `index_v2.html` + `app_v2.js` — **v2 variant** with a tips-only minimap
  above the breadcrumb. Same shell, same content, extra nav widget.
  `app.js` stays untouched so v1 is always a working fallback.
  See § "Minimap (v2)" below.

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
`{ "svg": "foo.svg", "show": ["layer-id", ...] }` for layered).

Top-level fields: `root` (id), `nodes` (map), `tree` (outline),
`tips` (optional array — used by the v2 minimap; see § "Minimap (v2)").

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

**Current tree shape** (as of 2026-04-24; regenerate with
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
└── sMachin → sInWork → sInWorkb
    ├── sTok → sTokb → sTokSol → sTokSolb
    │   (tokenization chapter, text-only)
    ├── sEmb
    │   ├── sSpace → sSpaceb → sMatrix → sMatrixb → sMatrixc
    │   │   (vector coords + matrix-of-vectors intro)
    │   ├── sEmbLogic → sClust → sClustb → sClust1..sClust4
    │   │   (what embeddings encode → 2D projection, cluster reveal)
    │   ├── sArithm → sCap1..sCap4
    │   │   (analogy geometry — country/capital)
    │   ├── sVeh1..sVeh4 → sEmbConcl → sEmbConclb → sEmbConclc
    │   │   (vehicle analogy + embedding-chapter wrap-up)
    │   └── sPos → sPosb
    │       (positional embedding, text-only)
    ├── sAttn → sAttnb → sAttnc
    │        → sAttnBank → sAttnBankR → sAttnBankM
    │        → sAttnBankH → sAttnBankHb → sAttnBankHc → sAttnWrap
    │   (attention setup → schematic "bank" example → heads as subspace
    │    filters → synthesis)
    ├── sTrans → sTransEif → sTransEifArc → sTransEifDrift
    │          → sTransMLP → sTransMLPBank → sTransMLPFire → sTransMLPWrite
    │          → sTransWrap
    │          → sArch → sArchShapes → sArchParams → sArchZoom
    │   (transformer intro → Eiffel attention → MLP "bank of
    │    learned patterns" → three-mechanic wrap-up → architecture
    │    capstone. Data-driven where clean, schematic-with-real-
    │    measurements where individual interpretation breaks down)
    └── sTrain → sTrainData → sTrainStep → sTrainEmerge → sTrainEff
        (what training does + why the weird machinery works; text-only)
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

## Minimap (v2 viewer)

A compact navigation skeleton above the breadcrumb, opt-in via
`index_v2.html` (which loads `app_v2.js`). `app.js` stays untouched —
`app_v2.js` is `app.js` + a minimap module at the bottom (~200 lines).
CSS lives in the shared `style.css` under a scoped `#minimap` block; it
has no effect when the v1 shell is loaded (the element doesn't exist).

**What it shows.** Only "tip" nodes as dots. Tips come from the
`tips` field in `tree.json` (user-curated list of chapter markers):

```json
"tips": ["sRoot", "sUse", "sNextWord", "sMachin",
         "sTok", "sEmb", "sClust1", "sArithm", "sPos",
         "sAttn", "sTrans", "sTrain"]
```

Content nodes (refinements between tips) are **not rendered as dots**.
They collapse into:
- **Inter-tip edges** whose length ∝ count of countable content nodes
  between parent tip and child tip. Typically short (0–1).
- **Trailing lines** past leaf tips whose length ∝ countable content
  in the tip's sub-tree. This is where the "big chapter = long branch"
  visual comes from (e.g. `sTrans` has 12 trailing content nodes).

A node is "countable" iff `node.mode === 'rewrite'` (see
`countsAsContent` in `app_v2.js`). Diff-mode nodes are skipped. This
includes rewrites that reuse an SVG via `show` changes (e.g. `sClust2-4`,
`sCap*`, `sArchShapes/Params/Zoom`) — those *are* real content steps
even though they share a figure.

**Cursor.** Closest tip ancestor of `currentId` gets amber fill + glow.
For leaf tips, a second amber line (progress overlay) extends along
the trail to `tip.x + (preorderPos / (subtreeSize-1)) × trailLen`,
giving a smooth slide as the user steps through the chapter's content.
Non-leaf tips don't get a trail yet — their cursor sits on the tip dot.

**Navigation feedback is eager.** `goTo` commits `currentId`, path,
breadcrumb, and minimap *before* the text animation starts (edit in
`app_v2.js:goTo`). The cursor jumps to target on keypress/click; the
text types out behind it.

**Click-to-jump.** Each tip dot is clickable → jumps directly to that
tip. Same animation guard as keyboard.

**Layout knobs** (top of `computeMinimapLayout` in `app_v2.js`):
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

**Falling back to v1.** If something breaks in v2, open `index.html`
instead. The two entry points share `tree.json`, `style.css`, and
`resources/`, so content edits land in both.

**Known not-done.** `sEmb` is a non-leaf tip (has child tips
`sClust1`, `sArithm`, `sPos`) so it doesn't draw a trail. The `sSpace`
and `sVeh1` chains under `sEmb` are orphan content — not on any
child-tip path — and currently render as nothing. Two fixes: (a) add
`sSpace` and/or `sVeh1` to `tips` to promote them to leaf tips with
their own trails, or (b) extend the minimap to render orphan trails on
non-leaf tips (short perpendicular ticks, say).

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
