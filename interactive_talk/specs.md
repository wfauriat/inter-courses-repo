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

### File shape

`tree.json` has three top-level fields:

```jsonc
{
  "root":  "sRoot", // id of the root node
  "nodes": { ... }, // flat map of id → node content (text, mode, figure)
  "tree":  { ... }  // nested id-only outline of parent → children
}
```

Content and structure are stored separately: editing a node's text never drags along indentation, and restructuring the talk never forces re-typing node content.

### Node content

Each entry in `nodes` is keyed by id and holds only per-node fields:

```jsonc
"sTok": {
  "text":      "...",        // displayed text; may contain [[...]] markers and \n newlines
  "mode":      "rewrite",    // optional: "rewrite" | (default "diff")
  "figure":    "foo.png",    // optional: image path, placeholder text, SVG spec, or omitted
  "technical": true          // optional: hides this subtree in light mode (see Light/technical mode)
}
```

The id lives in the outer key, not inside the object. There is no `children` field — connectivity lives in `tree`.

### Tree outline

`tree` is a nested object-of-objects over ids. Every key is a parent id; its value is that node's children map, same shape recursively. `{}` marks a leaf.

```jsonc
"tree": {
  "sRoot": {
    "sIntro": { "sDetail": { "sDetailb": {} } },
    "sAlt":   { "sAltLeaf": {} }
  }
}
```

Sibling order = key insertion order in the JSON file. Reordering siblings = swapping keys; re-parenting a subtree = cut-and-paste of one entry, with node content untouched. Use short semantic ids tied to the node's meaning (`sRoot`, `sNextWord`, `sTok`, …); sequential refinements of the same idea take `b`, `c`, `d` suffixes (`sNextWord → sNextWordb → sNextWordc`). Avoid pure integer keys (`"0"`, `"42"`) — JSON parsers reorder those ahead of strings and scramble sibling order. Any non-integer id is technically safe, but positional names (`s0`, `s1`) lose meaning once the tree is reshuffled — semantic names stay stable through edits and read cleanly in diffs. Nodes reachable from `root` via `tree` render in the viewer; entries in `nodes` without a `tree` parent are dead content.

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

### Light / technical mode

A tree-wide filter on top of the DFS structure. Two modes:

- **`light`** (default) hides every node whose root-of-subtree carries `"technical": true` (the flag inherits to all descendants).
- **`technical`** shows everything.

Authoring: set `"technical": true` only on the *root* of a branch meant to be skippable; descendants inherit. Don't flag the root node — the whole tree would vanish.

Runtime: `t` / `T` toggles the mode. `?mode=light|technical` in the URL seeds the initial value; it is non-locking — `t` still flips the mode after load, so the URL param is for sharing a presentation flavour, not for locking it. The help strip shows the current mode.

Effects:

- Navigation (preorder, sibling cycle) skips hidden subtrees.
- The minimap rebuilds: hidden tips drop from the dot set, trailing-content counts skip hidden subtrees.
- If the current node becomes hidden on flip, the viewer snaps to the nearest visible ancestor via an animated `goTo`.

---

## Interaction model

- `→` next in (visible) DFS preorder
- `←` previous in (visible) DFS preorder
- `↑` / `↓` cycle visible siblings at the current level
- `space` replay the last transition
- `r` / `R` jump to root
- `a` / `A` toggle auto-advance (steps `→` every `CONFIG.autoAdvanceMs` ms)
- `t` / `T` toggle light / technical mode
- Any of the navigation keys (arrows, space, r) pressed *during* an animation fast-forwards the current animation to its final state. The key is not queued — the user must press again to navigate further. This trades traversal speed for control. `a` and `t` are modal keys, not navigation, so they don't skip — they apply immediately.

The breadcrumb bottom-left shows the DFS path from root to current node. The help strip bottom-right summarizes the keys and current mode.

---

## Rendering pipeline

1. `init()` fetches `tree.json` (with `cache: 'no-store'` so local edits show up without hard-reload), inflates the split `nodes` + `tree` form into the internal nested shape via `reifyTree`, and renders the root via `renderWithHighlights` (honors `[[...]]`).
2. A keypress resolves to a target node and calls `goTo(node)`.
3. `goTo` calls `parseHighlights(node.text) → {clean, ranges}`, then dispatches to `animateTransition` (diff) or `animateRewrite` based on `node.mode`. In parallel it fires `updateFigure(node)` — a CSS-only layer toggle when the target shares the previous node's SVG, or an opacity-based panel swap otherwise.
4. Both animations reduce to sequential DOM mutations on two spans (`#before`, `#after`) with `await sleep(...)` between steps. A `skipRequested` flag collapses the current animation to its final state when a new key arrives; the triggering key is *not* queued — the user must press again to navigate further.
5. `CONFIG` at the top of `app.js` holds all tunable timings: `typeMs` / `deleteMs` (per-char), `keepPauseMs` / `segmentPauseMs` (between diff ops), `rewriteFadeMs` / `rewritePauseMs` (text rewrite phases, also drives SVG layer fade), and `figureFadeInMs` / `figureFadeOutMs` (figure panel, independent in/out durations).

---

## Non-goals

- **No build step, no framework, no bundler.** A handful of plain files, browser APIs only. Edit and reload.
- **No persistence state.** The viewer is idempotent over `tree.json`; there is no session memory and no history. The only URL state is the optional `?mode=light|technical` seed for the light/technical filter.
- **Backward ≠ inverse.** A rewrite-mode node replays its own animation; going back through it does not un-type it in reverse.
- **No WYSIWYG editor for the tree.** Authors edit `tree.json` by hand. This is intentional — it keeps the content format simple and diffable.
- **Highlights are author intent, not computed salience.** There is no NLP, no emphasis model. In rewrite mode the author chooses what's fresh; in diff mode the diff algorithm does.

---

## SVG overlay figures

**Status: implemented. Several SVGs in `resources/` are exercised across `tree.json`.**

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

### Marking layers in Inkscape

Inkscape's main UI doesn't expose SVG `class` attributes — setting `class="layer"` requires the XML editor (`Edit → XML Editor`, or `Ctrl+Shift+X`). Workflow:

1. Group the shapes that should toggle together (`Ctrl+G`).
2. Select the group on the canvas; it highlights in the XML panel as a `<g>` node.
3. In the attributes list, click `+`, type attribute name `class`, value `layer`, and commit.
4. Rename the `id` to whatever your node's `show` list references (e.g. `animals`, `prompt`). Semantic ids are the whole point — they're what tree.json names.
5. Save as Plain SVG or Inkscape SVG; both work. Inkscape-specific attributes (`inkscape:groupmode`, `inkscape:label`, `sodipodi:*`) are ignored by the viewer and safe to leave alone.

A group without `class="layer"` is part of the base and always visible — useful for scaffolding (axes, always-on labels, a central figure) that shouldn't toggle.

### Transition semantics

- **Text and figure animate in parallel.** Caption edits (diff or rewrite mode on `text`) run concurrently with layer changes; they don't serialize.
- **Layers fade in/out via CSS opacity**, duration matching `rewriteFadeMs` (~200 ms) for visual consistency with the text fade. No per-layer reveal animation beyond opacity.
- **Panel fade is asymmetric.** `figureFadeInMs` and `figureFadeOutMs` are independent knobs — defaults favor a slower in / quicker out ("the arrival is worth looking at; the departure is just a beat"). First render of a figure — including the initial page load if the root node has one, or the first figure-bearing node along a branch — uses the same fade-in as a swap. Implementation: fade-in is driven by a CSS keyframe animation attached to `.figure.visible`; fade-out and swap-fades use a CSS transition with the duration set inline per direction.
- **Swapping figures** (an SVG replaced by another SVG, a static image, a placeholder, or vice versa) fades the panel out, loads the new content, fades it back in. Same machinery covers all combinations.

### Scope notes

- Transition paths and node history remain the tree's responsibility. The figure has no memory of what was shown before; each node re-declares its `show` list.
- The `show` list is order-independent — it's a set.
- Back-navigation applies the target node's `show` just like forward. Symmetric with the text-side "backward ≠ inverse" rule.

---

## Minimap

**Status: implemented.** A compact navigation skeleton above the breadcrumb. Lives in `app.js` with styling scoped under `#minimap` in `style.css`.

### Data shape

A top-level `tips` array in `tree.json` lists chapter-marker ids. Everything else — trails, edges, cursor progression — is derived from the tree plus `tips`.

```jsonc
"tips": ["sRoot", "sUse", "sNextWord", "sMachin", "sTok", "sEmb", ...]
```

### What it shows

- **Tip dots.** One dot per visible id in `tips`. Hidden tips (tip whose subtree root is `technical` in light mode) drop out.
- **Inter-tip edges.** Length proportional to the count of countable content nodes (rewrite-mode, not hidden) on the tree path from parent tip to child tip. A small `MIN_EDGE` floor keeps zero-content edges visible.
- **Trails.** Leaf tips (tips with no descendant tip in the visible set) get a dim trailing line whose length is proportional to their trailing content count. An amber "progress overlay" on top grows as the user navigates the chapter.
- **Non-leaf tips** draw no trail yet; orphan content under a non-leaf tip currently renders as nothing (known limitation).

### Cursor and path highlighting

The closest visible tip ancestor of `currentId` is the "current tip." It receives amber fill + glow (`.mm-current`). Every tip on the tips-tree path from root to current tip gets `.mm-path`. The current tip's trail progress extends to `tip.x + (preorderOffset / (subtreeSize − 1)) × trailLen`, giving a smooth slide through the chapter.

### Sibling-tip border

When the user is exactly at a tip whose visible full-tree siblings include at least one other tip (so `↑/↓` would jump to a sibling chapter), the tip dot gets a lighter-amber ring via `.mm-tip-sibling`. Applied dynamically — the ring disappears the moment the user steps into the tip's subtree, so it reflects "sibling-jump is actually possible right now" rather than a static structural property.

### Interaction

- **Click-to-jump.** Each tip dot is clickable; same animation guard as keyboard nav.
- **Mode filter.** `talkMode` flips rebuild the minimap: hidden tips drop, trails shorten.

### Scope notes

- The minimap is derived state. `tree.json` remains the source of truth; the minimap never stores navigation history beyond reading `currentId`.
- Markers are restricted to tip dots. Non-tip nodes are never rendered as dots — intermediate content (`sInWork` between `sMachin` and `sTok`, diff-mode refinements, etc.) is visible only via the progress overlay and the breadcrumb.
- Tips list drift is expected. The author adds/removes tips to shape the chapter pacing without touching the viewer code.

