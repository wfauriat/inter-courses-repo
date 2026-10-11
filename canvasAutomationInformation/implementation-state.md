# Implementation State — Argument Canvas

A snapshot of the running implementation, meant to be read in a later session to resume work (next phase: more opinionated rendering and interactivity — per-edge-type and per-node-role visuals, hover-sync between panels, walked-trace styling, spatial semantics, etc.).

This document captures **what is implemented, where it lives, and how it behaves** — not architectural intent. For intent and the broader contract, see `intent.md` and `synthesis.md`. The current implementation deliberately under-uses the contract from `synthesis.md` (no pages, no roles, no orientation-keyed content yet); those are upcoming work.

---

## 1. Repository layout

```
/home/ai-user/Documents/Sandbox/canvasAutomInfo/
├── intent.md
├── synthesis.md
├── corpora_content.md
├── friction_and_exposure.md
├── engineer_path_v0.json       # 10-node mockup graph, current load target
├── implementation-state.md     # this document
├── previous_docs/              # superseded specs and original source content
│   ├── argument-canvas-specs-v0.md
│   ├── card-authoring-contract-checkpoint.md
│   ├── engineer_path_v0.md     # YAML source of engineer_path_v0.json
│   ├── statistician_path_v0.md
│   ├── pedagogical-architecture-specs-v2.md
│   ├── Perspectival_trap.md
│   └── Precisely_wrong.md
└── app/                        # Vite + React + TypeScript SPA
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.app.json / tsconfig.json / tsconfig.node.json
    ├── vite.config.ts
    ├── eslint.config.js
    ├── index.html
    ├── public/
    └── src/
        ├── main.tsx            # React entry, imports index.css then App
        ├── App.tsx             # everything: types, components, state, render
        ├── index.css           # theme tokens, layout, component styles
        └── assets/             # vite default assets (unused)
```

Two source files do the work: `app/src/App.tsx` and `app/src/index.css`. No other components, hooks, or utility files yet.

## 2. Tech stack

- **React 19** (Vite scaffold default)
- **TypeScript**, strict mode
- **Vite 8** build tool
- **@xyflow/react v12** (React Flow), with `colorMode` prop wired to theme state
- **@dagrejs/dagre** for auto-layout
- No state manager — plain `useState`, `useRef`, `useCallback`, `useMemo`
- No router, no backend, no external CSS framework
- Persistence is purely client-side: JSON download/upload via browser
- Bundle: ~415 KB JS / ~22 KB CSS (gzipped ~133 KB / ~4 KB)

## 3. Dev commands

From `app/`:
```
npm run dev      # vite dev server
npm run build    # tsc -b && vite build (used for type-checking)
npm run preview  # serve the built bundle
```

## 4. Data model

### 4.1 In-memory types (top of `App.tsx`)

```ts
const EDGE_TYPES = [
  'supports', 'opposes', 'qualifies', 'instantiates',
  'responds-to', 'synthesizes', 'depends-on', 'defers-to',
] as const
type EdgeType = (typeof EDGE_TYPES)[number]

type CardNodeData = { label: string; body: string }
type CardEdgeData = {
  edgeType: EdgeType
  labelOffsetX?: number   // graph-coord offset from path midpoint
  labelOffsetY?: number
}
type CardNode = Node<CardNodeData>   // React Flow's generic
type CardEdge = Edge<CardEdgeData>
```

- **Node fields in use**: `id`, `position`, `data`, plus RF's internal `selected`.
- **Edge fields in use**: `id`, `source`, `target`, `sourceHandle` (always null), `targetHandle` (always null), `label` (top-level — the human teaser string), `data.edgeType`, `data.labelOffsetX/Y`.

On-canvas displayed text uses `data.label || data.id` (set in `styledNodes`) — empty labels fall back to the id.

### 4.2 JSON save format (`FILE_VERSION = '0.1'`)

Filename pattern: `argument-canvas-YYYY-MM-DD.json`.

```json
{
  "version": "0.1",
  "nodes": [
    {
      "id": "the_crossing",
      "position": { "x": 0, "y": 0 },
      "data": { "label": "the crossing", "body": "..." }
    }
  ],
  "edges": [
    {
      "id": "e_01",
      "source": "the_crossing",
      "target": "predictions_are_inherently_imperfect",
      "sourceHandle": null,
      "targetHandle": null,
      "label": "Why is the number conditional?",
      "data": { "edgeType": "supports", "labelOffsetX": 0, "labelOffsetY": 0 }
    }
  ]
}
```

Load is permissive: malformed entries are skipped (via `flatMap` returning `[]`); missing fields default (label/body → `''`, edgeType → `'supports'`, positions → `0,0`).

### 4.3 Deliberately omitted from the schema (vs `synthesis.md`)

- `role` (hook / spine / branch / support.example / landing)
- `thesis_role` (load_bearing / enriching)
- `pages` (page 0 / page 1 / page 2)
- `pages_key` (orientation-keyed pages: shared / engineer / statistician / …)
- Per-card `notes_to_self`
- Path manifest (per-path composition document)
- Inline-reference syntax `[display](kind:term_id)` for def / clarify / cite / xref
- Friction map, belief trajectory (path-level, not schema)
- Tab preconditions
- Walked state (not persisted in JSON — reload always starts fresh)

These are upcoming work, not bugs.

## 5. Components

Exactly two, both in `App.tsx`:

### 5.1 `App` (default export)

Holds all state, all callbacks, renders the entire UI. Single fat component.

### 5.2 `CardEdgeComponent`

Custom edge type registered as `'card-edge'` and set as the default in `defaultEdgeOptions`. Replaces React Flow's built-in step edge.

- Path via `getSmoothStepPath({ borderRadius: 0 })` → orthogonal step with sharp 90° corners.
- Path rendered via `<BaseEdge>`. Label rendered via `<EdgeLabelRenderer>` as a `<div>` positioned at the path's natural midpoint plus an offset from `data.labelOffsetX/Y`.
- Drag handler on the label `<div>`: `onMouseDown` captures starting client coords + current offsets; document-level `mousemove` updates offsets via `useReactFlow().setEdges`, dividing pixel delta by `getViewport().zoom`; `mouseup` cleans up.
- Receives RF's `selected: boolean` prop and applies `.edge-label-floating.selected` class (amber styling) when true.

Registered as:
```ts
const customEdgeTypes = { 'card-edge': CardEdgeComponent }
// <ReactFlow edgeTypes={customEdgeTypes} defaultEdgeOptions={{ type: 'card-edge', markerEnd: {...} }} />
```

## 6. State (all in `App`)

| Name | Type | Default | Purpose |
|---|---|---|---|
| `idRef` | `useRef<number>` | `2` | Counter for auto-generated `node_N` ids |
| `fileInputRef` | `useRef<HTMLInputElement>` | `null` | Hidden file input for Load |
| `fitViewRef` | `useRef<(opts?) => void>` | `null` | Captures RF instance's `fitView` after `onInit` |
| `nodes`, `setNodes`, `onNodesChange` | `useNodesState<CardNode>` | one initial node `central_claim` | RF nodes state |
| `edges`, `setEdges`, `onEdgesChange` | `useEdgesState<CardEdge>` | `[]` | RF edges state |
| `selectedNodeId` | `useState<string \| null>` | `'central_claim'` | Currently focused node (drives right panel + halo) |
| `selectedEdgeId` | `useState<string \| null>` | `null` | Currently selected edge (single-click) |
| `editingEdgeId` | `useState<string \| null>` | `null` | Edge whose label is being inline-edited (double-click) |
| `editingField` | `useState<'label' \| 'body' \| null>` | `null` | Which field of the focused node is being edited |
| `theme` | `useState<'light' \| 'dark'>` | from `prefers-color-scheme` | Theme toggle, also passed to RF's `colorMode` |
| `revealMode` | `useState<boolean>` | `true` | If true, only walked + suggested edges render |
| `walkedEdgeIds` | `useState<Set<string>>` | empty | Edges that have been traversed |

`editingField` resets to `null` whenever `selectedNodeId` changes (via `useEffect`).

## 7. Derived (memoized) state

```ts
selectedNode   = nodes.find(n => n.id === selectedNodeId) ?? null
outgoingEdges  = edges.filter(e => e.source === selectedNodeId)   // UNFILTERED by revealMode; drives the right panel list
visibleEdges   = revealMode
                   ? edges.filter(e => walkedEdgeIds.has(e.id) || e.source === selectedNodeId)
                   : edges
styledNodes    = nodes.map(n => ({
                   ...n,
                   className: n.id === selectedNodeId ? 'node-focused' : '',
                   data: { ...n.data, label: n.data.label || n.id },
                 }))
styledEdges    = visibleEdges.map(e => {
                   const isSuggested = e.source === selectedNodeId
                   const isSelected  = e.id === selectedEdgeId
                   const isWalked    = walkedEdgeIds.has(e.id)
                   return {
                     ...e,
                     className: [
                       isWalked    && 'edge-walked',
                       isSuggested && 'edge-suggested',
                       isSelected  && 'edge-selected',
                     ].filter(Boolean).join(' '),
                     animated: isSuggested,
                   }
                 })
```

## 8. Callbacks

### Node ops
- `addNode()` — generates `node_${idRef.current++}` at a random nearby position, focuses it (sets `selectedNodeId`).
- `updateNodeData(id, partial: Partial<CardNodeData>)` — merges into node's `data`.
- `deleteNode(id)` — removes node and all incident edges; clears focus if matching. No confirm.
- `onNodesDelete(deleted)` — RF callback; clears `selectedNodeId` if among deleted (used by Backspace path).

### Edge ops
- `onConnect(params)` — creates edge with id `e_${source}_${target}_${Date.now()}`, type `'supports'`, empty label; **auto-walks** it (adds to `walkedEdgeIds` so it's visible in reveal mode).
- `updateEdge(id, partial: { label?, edgeType? })` — merges label and/or `data.edgeType`.
- `deleteEdge(id)` — `window.confirm('Delete this edge?\n\n"<label>"')`, then removes; clears `selectedEdgeId` / `editingEdgeId` if matching.
- `walkEdge(edgeId, targetId)` — adds to `walkedEdgeIds`, sets `selectedNodeId = targetId`, clears edge selection/editing, AND `setNodes` to mark target with `selected: true` and all others with `selected: false`. This last step is **load-bearing**: it syncs RF's internal `.selected` class so the focus halo follows (the halo is painted by RF's `.selected` style via `--xy-node-boxshadow-selected: var(--halo)`).

### Layout / visibility
- `applyAutoLayout()` — runs `autoLayout(nodes, edges, 'TB')`, then schedules `fitViewRef.current({ duration: 400 })` on the next animation frame.
- `showAllLinks()` — `revealMode = false`.
- `resetWalk()` — `walkedEdgeIds = new Set()`, `revealMode = true`.
- `clearAll()` — `window.confirm`, then wipes nodes, edges, all focus / selection / editing / walked state, resets `idRef` to 2 and `revealMode` to true.

### File I/O
- `saveToFile()` — serializes nodes (`id`, `position`, `data`) and edges (`id`, `source`, `target`, `sourceHandle`, `targetHandle`, `label`, `data`) with `version: '0.1'`. Triggers a browser download.
- `onFileSelected(e)` — reads file, `JSON.parse`, validates permissively (flatMap-skipping malformed), replaces nodes / edges, clears focus / selection / editing / walked, sets `revealMode = true`, recomputes `idRef.current` from any `node_N` ids in the load, then `requestAnimationFrame(fitView({ duration: 300 }))`.

### Theme
- Theme toggle button switches `'light' ↔ 'dark'`.
- `useEffect` writes `document.documentElement.dataset.theme = theme`. Initial theme from `window.matchMedia('(prefers-color-scheme: dark)')`.

### React Flow handlers (on `<ReactFlow>`)
- `onNodeClick(_, node)` — `setSelectedNodeId(node.id)`, clears edge selection / editing field.
- `onEdgeClick(_, edge)` — `setSelectedEdgeId(edge.id)`.
- `onPaneClick()` — clears all selection / editing state.
- `onInit(instance)` — captures `instance.fitView` into `fitViewRef.current` for later use after load / layout.
- `onConnect`, `onNodesChange`, `onEdgesChange`, `onNodesDelete` — wired to the corresponding callbacks above.

## 9. Edge visibility / walk model

The most distinctive behavior. Edge states:

| State | Condition | Visual |
|---|---|---|
| **Hidden** | `revealMode === true` AND not walked AND source ≠ focus | Filtered out of `visibleEdges` |
| **Suggested** | source === focused node | Visible; class `edge-suggested`; animated dashes; accent (blue) stroke 2px |
| **Walked** | in `walkedEdgeIds` | Visible regardless of focus; class `edge-walked` applied but currently with no extra CSS rule (hook for future) |
| **Selected** | id === `selectedEdgeId` | Class `edge-selected`; amber stroke 4px + drop-shadow halo + bold amber label. Stacks with suggested. |

Combinations:
- **Suggested + walked** (user backtracked): both classes applied, animated takes visual lead.
- **Suggested + selected**: selected style wins on stroke (later in CSS source order).

Walk action lifecycle:
- User clicks the `→` button on an edge row in the right panel.
- `walkEdge(edge.id, edge.target)` runs → walked set grows, focus moves, halo follows (via the `selected: true` sync inside `setNodes`).
- The right panel re-renders with the new focus's `outgoingEdges`.
- The canvas now shows: walked edges + new focus's outgoings as suggested.

Failsafes:
- **Show all** button → `revealMode = false`. All edges show regardless of walked / focus state.
- **Reset walk** button → `walkedEdgeIds = ∅`, `revealMode = true`. Back to the empty exploration state.

Auto-reset triggers (force `revealMode = true` and empty `walkedEdgeIds`):
- File load
- `Clear` (wipe everything)
- `Reset walk`

## 10. Auto-layout

`autoLayout(nodes, edges, direction: 'LR' | 'TB' = 'LR')`:

```ts
const g = new dagre.graphlib.Graph()
g.setGraph({ rankdir: direction, nodesep: 60, ranksep: 140 })
g.setDefaultEdgeLabel(() => ({}))
nodes.forEach(n => g.setNode(n.id, { width: 210, height: 56 }))
edges.forEach(e => g.setEdge(e.source, e.target))
dagre.layout(g)
return nodes.map(n => {
  const pos = g.node(n.id)
  return { ...n, position: { x: pos.x - 210/2, y: pos.y - 56/2 } }
})
```

Constants: `LAYOUT_NODE_W = 210`, `LAYOUT_NODE_H = 56`. The half-subtraction translates dagre's center-anchored coords to React Flow's top-left-anchored coords.

The toolbar's `Auto-layout` button calls with `'TB'`. The function supports `'LR'` but no button is wired yet (one-line addition when wanted).

Back-edges (DAG cycles, e.g. `predictions → the_crossing` "back to the boat" in the engineer path) are handled by dagre internally (removed during ranking, re-added after layout). This can place anchor nodes at unexpected ranks; manual repositioning is fine.

## 11. Theme & palette

Defined in `index.css` under `:root` (light) and `:root[data-theme='dark']` (dark). Some user-tweaked alpha values in the halo and `node-body-input` font-size may have shifted from defaults — they are intentional.

**Functional palette** (use to express interaction states):
- `--accent` (blue) — focus halo, suggested edges, hovers, focused input borders, edge-type pill
- `--select` (amber) — selected edge, selected edge row in right panel
- `--ink` (cyan/teal) — default node border (the one color addition for node identity)
- `--danger` (red) — delete actions hover
- `--halo` — double-ring box-shadow used as the focus halo via `--xy-node-boxshadow-selected`

**Surface palette** (warm/cool play):
- `--bg` — canvas (cool slate-blue light / deep navy dark)
- `--surface` — right panel (warm cream light / warm dark)
- `--surface-2` — elevated surfaces (inputs, buttons) — pure white / cool dark
- `--node-bg` — RF node fill (warm cream-white / cool slate-dark)
- `--edge-stroke` — default edge color (slate)
- `--dot-color` — Background pattern dots
- `--text` / `--text-muted` / `--border`

**React Flow variable overrides** (in `.react-flow` selector):
- `--xy-node-boxshadow-selected: var(--halo)` — this is what makes the halo visible. Without it, RF's tiny `0 0 0 0.5px` ring shows instead.
- `--xy-node-background-color` / `-default`: `var(--node-bg)`
- `--xy-edge-stroke` / `-default`: `var(--edge-stroke)`
- `--xy-background-pattern-dots-color` / `-default`: `var(--dot-color)`

## 12. CSS structure (class names worth knowing)

```
.app                                   // outer grid (canvas | right-pane)
.canvas-pane                           // left column
.toolbar                               // absolutely positioned top-left of canvas
.right-pane                            // right column, grid-rows 70% / 30%
.content-pane                          // top of right-pane (focused-node content)
.content-header                        // label row + delete button
.node-label-display / .node-label-input
.node-body-display / .node-body-input
.edges-pane                            // bottom of right-pane (potential moves)
.edge-list / .edge-item                // edge rows
.edge-item.selected
.edge-label-display / .edge-label-input
.edge-type-select
.icon-button / .icon-button.danger
.placeholder / .placeholder-inline

.react-flow__node.react-flow__node-default  // node body styling overrides
.react-flow .react-flow__node.node-focused  // (currently unused; relies on RF's .selected)
.react-flow .react-flow__edge.edge-suggested .react-flow__edge-path
.react-flow .react-flow__edge.edge-selected .react-flow__edge-path
.react-flow .react-flow__edge.edge-walked   // hook, no rule yet
.edge-label-floating                    // EdgeLabelRenderer's dragable pill
.edge-label-floating.selected
```

## 13. UX surface

### 13.1 Toolbar (top-left of canvas pane)

```
[ Add node ] [ Save ] [ Load ] [ Clear ] [ Auto-layout ] [ Show all ] [ Reset walk ] [ Dark/Light mode ]   <hint text>
```

Plus a hidden `<input type="file" accept="application/json,.json">` triggered by Load.

### 13.2 Canvas pane (left, `minmax(0, 1fr)`)

- React Flow with custom `card-edge` for all edges, RF's default nodes, `<MiniMap pannable zoomable>`, `<Controls>`, `<Background>` (dots).
- Pan / zoom via mouse / trackpad.
- Click node → focuses (right panel + halo).
- Click empty pane → clears all selection.
- Click edge → selects it (amber path + label).
- Drag from a node's handle → creates a new `card-edge` to target; auto-walked so it stays visible.
- Backspace / Delete on canvas selection (node or edge) → deletes via RF's built-in. **Note**: bypasses the `×`-button delete confirm.

### 13.3 Right pane (right, `minmax(380px, 38%)`, grid-rows `70% 30%`)

**Content pane (top 70%) — display-first**:
- Label: `<h2>` at 30px monospace bold. Hover shows subtle border. Double-click → `<input>` at same size (autofocus). Enter / blur / Escape exit edit mode.
- Body: `<div>` at 19px / line-height 1.7, `white-space: pre-wrap` (multi-paragraph rendering), scrollable, min-height 260. Double-click → `<textarea>` at same size. Blur / Escape exit (Enter inserts newline). Display structure is a single `<div>` rendering plain text — ready to swap for parsed markdown / inline-tooltip JSX when that lands.
- Delete button (top-right of header): removes the focused node immediately, no confirm.

**Edges pane (bottom 30%) — "Potential moves"**:
- One row per `outgoingEdges` entry (i.e. UNFILTERED by reveal/walked).
- Row layout: `[ label ] [ type ▾ ] [ → ] [ × ]`.
- Label is read-only display by default; double-click → input. Updates as-typed.
- Type dropdown always interactive; lists all 8 `EDGE_TYPES`.
- `→` button: walks the edge (calls `walkEdge`).
- `×` button: deletes the edge with `window.confirm`.
- Single click on a row selects the edge (sets `selectedEdgeId`).

### 13.4 Edge labels on canvas

Rendered by `CardEdgeComponent` via `<EdgeLabelRenderer>`. Each is a small `<div>` pill with `pointer-events: all`.
- Hover: accent border.
- When RF marks the edge `selected`: amber border + soft amber bg + bold amber text.
- Drag the pill to reposition. Offset persists in `data.labelOffsetX/Y`, zoom-aware, round-trips through save/load.

## 14. Mockup data

`engineer_path_v0.json` at repo root is a 10-node / 29-edge graph derived from `previous_docs/engineer_path_v0.md` (9 authored cards + 1 stub `meta_no_free_lunch`). Each node has a humanized short `label` and full multi-paragraph `body` from the YAML face content. Edges carry teaser-shaped `label`s and the YAML `edgeType` values. Positions are roughly left-to-right (spine at y=0, branches above and below).

Load via the toolbar's **Load** button, navigating up one level from `app/`.

Edge types appearing in this dataset: `supports`, `qualifies`, `instantiates`, `responds-to`, `synthesizes` (no `opposes`, `depends-on`, or `defers-to` — the engineer path never stages an explicit opposition).

## 15. Known limitations / not implemented

### From the intent / synthesis contract
- **Spatial semantics carrying argumentative meaning** — supports dock below, opposes across, qualifies above, syntheses at apex. Not implemented; all edges look identical except for state-based styling.
- **Per-edge-type visual treatment** — color, line style, marker, dock direction tied to `edgeType`. The field is metadata only.
- **Per-node-role visual treatment** — `role` field doesn't exist yet. All nodes look identical.
- **Three-page card model** — body is one string; no Page 0 / 1 / 2 split.
- **Orientation-keyed pages** — no `pages_key`; one face per node.
- **Inline references in body** — `[display](kind:term_id)` syntax with `def`/`clarify`/`cite`/`xref` not parsed. Body renders as plain text.
- **Path manifest** — no per-path composition document; walking is ad-hoc within a single library.
- **Hover synchronization between panels** — hovering an edge row in the right panel does not highlight the corresponding edge on canvas, nor vice versa. Click does (via shared `selectedEdgeId`).
- **Trace panel** — toggle-on textual "path so far" not implemented; walked edges accumulate on canvas only.
- **Tab preconditions** — synthesis edges that require both parents walked, meta-claims that need motivation cards first, etc.
- **Walked-edge styling** — `.edge-walked` class applied but no CSS rule.
- **LR auto-layout** — function supports it; no button.
- **Walked state persistence** — `walkedEdgeIds` not saved in JSON; reload starts fresh.

### Smaller UX gaps
- Backspace deletes canvas selection without confirm; only `×` button on edges confirms.
- Node delete button has no confirm (only the `Clear` button does).
- Rich-text affordances in body intentionally absent for v0.
- Edge drag from handle works but RF's default handle dots are the only indicator.
- No undo/redo.
- Multi-select via shift-click works in RF but `selectedNodeId` tracks only one — visual focus only follows the last-clicked.

## 16. Natural extraction points (for the eventual refactor)

Not done yet. Cheap, low-risk candidates when the time comes:

- `src/CardEdge.tsx` — the custom edge component (~80 lines, already self-contained, will grow with edge-type styling).
- `src/layout.ts` — `autoLayout` + the layout dimension constants.
- `src/types.ts` — `EDGE_TYPES`, `EdgeType`, `CardNodeData`, `CardEdgeData`, `CardNode`, `CardEdge`, `FILE_VERSION`.
- `src/io.ts` — `saveToFile`, the load-side parsing/validation (the long `flatMap`s).

Worth leaving in `App.tsx` for now: state declarations, callbacks, memos, render JSX. These are entangled with each other and with upcoming features, so abstracting them prematurely risks wrong seams. The state machine should consolidate naturally once the next layer of behaviors is in place.

## 17. Suggested next directions

Roughly ordered impact-to-cost; not prescriptive:

1. **Edge-type visual semantics** — color and/or marker per `edgeType`. Cheapest unlock for the canvas reading as an argument graph rather than a generic DAG. Touches `CardEdgeComponent` and CSS.
2. **Walked-edge styling** — give `.edge-walked` a distinct muted look (no animation, slightly lower opacity, perhaps a non-accent stroke) so the trace reads as history rather than ambient.
3. **Hover sync between panels** — hovering an edge row highlights the canvas edge, and vice versa. Likely a new `hoveredEdgeId` state, plus styling.
4. **Node role / type field** — add `role` to `CardNodeData`; render a small role indicator on the node (color stripe, icon, or shape via a custom node component).
5. **Inline references** — parse `[display](kind:term_id)` in body; render `def`/`clarify`/`cite` as hover tooltips and `xref` as click-to-fly-to-target (using `getViewport` and `setCenter`).
6. **Three-page card model** — split `body` into pages; add page navigation in the content pane.
7. **Trace panel** — toggleable textual path-so-far at the bottom-right, showing walked sequence with page-0 condensations.
8. **Save walked state** — round-trip `walkedEdgeIds` through JSON so sessions can resume mid-walk.
9. **LR vs TB layout toggle** — one button addition.
10. **Refactor** — once 1–3 land, the `CardEdge.tsx` / `types.ts` / `io.ts` / `layout.ts` split becomes obvious and low-risk.

---

*End of state snapshot.*
