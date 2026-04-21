# Interactive talk — specs

A keyboard-driven, single-page refinement viewer for a talk on LLMs. No build step, no framework: `index.html` loads `app.js` + `style.css`, `tree.json` is the content.

---

## Intent

Three overlapping goals, in decreasing obviousness:

1. **Pedagogy.** Take a lay audience by the hand. Start from a legible, zero-prerequisite statement; add weight gradually. The content is a tree with two meaningful axes: *down* a branch = the next refinement of the current thread (more precise, longer, more technical); *sideways* across siblings = an alternative framing of the same idea, or a zoom on a specific notion. No forced linear order — the speaker chooses the path live.

2. **Aesthetic.** Teletype writing, a single blinking cursor, one optional figure on the side, minimal chrome. Reads as a modern, sleek technical presentation rather than a deck of slides.

3. **Thematic.** The medium gestures at the subject. An LLM produces text one token at a time; this viewer produces the presentation one token at a time. The cursor is the most on-topic piece of UI possible. The point is not to make the talk feel magical — the talk exists to demystify — but to play with the tension: the audience is here to learn *how* the text is made, while watching a surface that winks at them as if it were being made the same way.

A refinement viewer, not a slide deck: each node restates its parent with something added or reworded, so what the audience sees is *thinking unfolding*, not a sequence of separate screens.

---

## Authoring contract

### Node schema

```jsonc
{
  "id":       "s3",              // unique, arbitrary
  "text":     "...",             // displayed text; may contain [[...]] markers
  "mode":     "rewrite",         // optional: "rewrite" | (default "diff")
  "figure":   "foo.png",         // optional: image path, placeholder text, or null
  "children": [ ... ]            // zero or more child nodes
}
```

### Highlight syntax

Wrap any word or phrase in `[[...]]` to mark it for the `.fresh` class. Brackets are stripped at render time. Works anywhere in a node's `text`. Legal inside JSON strings with no escaping (`[`/`]` are ordinary characters).

### Mode semantics

- **`diff`** (default). Between the previous on-stage text and this node's text, compute an LCS token diff. Animate as a single left-to-right cursor sweep: keeps pass through, deletions vanish char-by-char, insertions type char-by-char. Inserted letters/numbers render in `.fresh` on forward navigation; punctuation does not. `[[...]]` markers are stripped but ignored — the fresh set comes from the diff, not the author.

- **`rewrite`**. Ignore the diff. Phase 1: fade the stage to 0 opacity and clear it — the disappearance of the old text carries no pedagogical signal, so it's handled as a visual beat rather than a character-by-character chew. Phase 2: type out the new text, with `[[...]]`-marked ranges in `.fresh`. Use when more than ~30% of the text changes and LCS overlap would be noise rather than signal.

Mode is attached to the *target* node — going into a rewrite-mode node plays its rewrite animation regardless of direction. Backward is deliberately not a true inverse: you always see the target animated the way its author wanted it animated.

### Figures

Two shapes, discriminated by type:

- **Static**: `"figure": "path.png"` — a raw image rendered via `<img>` in the side panel. Extensions `.png .jpg .svg ...` are detected; anything else renders as a text placeholder. `null` or missing hides the panel.
- **Animated SVG** (see section below): `"figure": { "svg": "path.svg", "show": [ ... ] }` — an inline SVG whose layers can be revealed incrementally across nodes.

Both forms are just different values of the same `figure` field; the node shape is otherwise unchanged.

---

## Interaction model

- `→` next in DFS preorder
- `←` previous in DFS preorder
- `↑` / `↓` cycle siblings at the current level
- `space` replay the last transition
- `r` / `R` jump to root
- Any of the above pressed *during* an animation fast-forwards the current animation to its final state. The key is not queued — the user must press again to navigate further. This trades traversal speed for control.

The breadcrumb bottom-left shows the DFS path from root to current node. The help strip bottom-right summarizes the keys.

---

## Rendering pipeline

1. `init()` fetches `tree.json` (with `cache: 'no-store'` so local edits show up without hard-reload), renders the root via `renderWithHighlights` (honors `[[...]]`).
2. A keypress resolves to a target node and calls `goTo(node)`.
3. `goTo` calls `parseHighlights(node.text) → {clean, ranges}`, then dispatches to `animateTransition` (diff) or `animateRewrite` based on `node.mode`. In parallel it fires `updateFigure(node)` — a CSS-only layer toggle when the target shares the previous node's SVG, or an opacity-based panel swap otherwise.
4. Both animations reduce to sequential DOM mutations on two spans (`#before`, `#after`) with `await sleep(...)` between steps. A `skipRequested` flag collapses the current animation to its final state when a new key arrives; the triggering key is *not* queued — the user must press again to navigate further.
5. `CONFIG` at the top of `app.js` holds all tunable timings — per-char type delay, delete delay, segment pause, rewrite between-phase pause.

---

## Non-goals

- **No build step, no framework, no bundler.** A handful of plain files, browser APIs only. Edit and reload.
- **No persistence state.** The viewer is idempotent over `tree.json`; there is no session memory, no history, no URL state.
- **Backward ≠ inverse.** A rewrite-mode node replays its own animation; going back through it does not un-type it in reverse.
- **No WYSIWYG editor for the tree.** Authors edit `tree.json` by hand. This is intentional — it keeps the content format simple and diffable.
- **Highlights are author intent, not computed salience.** There is no NLP, no emphasis model. In rewrite mode the author chooses what's fresh; in diff mode the diff algorithm does.

---

## SVG overlay figures

**Status: implemented. First prototype lives in `embedding.svg`, exercised by the `s9…s13` branch of `tree.json`.**

A tree-driven Beamer-style overlay mechanism for figures. A figure has a fixed base and a pool of *layers*; navigating between nodes reveals, hides, or swaps layers, with a fade transition on appearance. Used when a diagram builds up — e.g. an embedding space that progressively populates with word clusters.

### Data shape

```jsonc
"figure": {
  "svg":  "embedding.svg",
  "show": ["axes", "animals", "stats"]
}
```

- **Absolute spec, not cumulative.** Every node that renders the figure lists the full set of layers to show. Slightly more verbose than Beamer-style cumulative specs, but unambiguous: the state of the figure at any node can be read off that node alone, with no dependence on the traversal path. Matches the overall "every node is self-contained" grain of the viewer.

### Authoring convention

- The SVG is loaded inline (`fetch` + `innerHTML` into the side panel) so its DOM is queryable.
- The **base** is every SVG element *not* marked as a layer — always visible.
- A **layer** is any element with `class="layer"`, identified by its `id`. Layers are hidden by default; those whose `id` appears in `show` are made visible.
- This convention lets authors draw in Inkscape/Illustrator, flag layer groups with the `layer` class, and give them semantic IDs. Non-layer elements (axes, labels, grid) need no annotation.

### Transition semantics

- **Text and figure animate in parallel.** Caption edits (diff or rewrite mode on `text`) run concurrently with layer changes; they don't serialize.
- **Layers fade in/out via CSS opacity**, duration matching `rewriteFadeMs` (~200 ms) for visual consistency with the text fade. No per-layer reveal animation beyond opacity.
- **Swapping SVGs** (a node whose `figure.svg` differs from the previous node's) fades the whole panel, loads the new SVG, fades back in — same as replacing a static image would.

### Scope notes

- Transition paths and node history remain the tree's responsibility. The figure has no memory of what was shown before; each node re-declares its `show` list.
- The `show` list is order-independent — it's a set.
- Back-navigation applies the target node's `show` just like forward. Symmetric with the text-side "backward ≠ inverse" rule.

### Prototype

`embedding.svg` — base with title, axes, grid, and a neutral scatter of small grey dots; four layers (`animals`, `verbs`, `stats-terms`, `royalty`) that reveal one at a time down the `s9…s13` branch. Exercises layer reveal, panel swap (from the static PNG on `s6` back to the inline SVG), and parallel caption animation on content that already has a place in the talk.
