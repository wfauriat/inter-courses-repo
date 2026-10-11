# Argument Canvas — Specs (v0)

A first-pass specification for an interactive presentation app where arguments unfold spatially on an infinite canvas, materializing card-by-card in response to user or speaker action. Cards exist as a latent library; edges between them are *potential* at start and become real (visually drawn) only as the path is walked.

This is a working draft. Items marked **(open)** are not yet locked — they will settle through prototyping. The document complements the higher-level methodology in `pedagogical-architecture-specs-v2.md`; where conventions differ from v2, the difference is intentional and noted.

**Working name.** "Argument Canvas" (placeholder).

**How to use this document.** As a starting reference for the first prototype build; as a contract between authoring (card content) and rendering (canvas behavior); as a record of decisions and known unknowns. Update in place as decisions firm up.

---

## 1. Purpose and scope

Build an interactive presentation engine that lets a *single artifact* serve two distinct delivery modes:

1. **Speaker mode.** A presenter follows a pre-edited path with permission to take side steps and return to the script.
2. **Self-paced mode.** An individual user explores the argument by clicking, choosing which threads to pull.

Both modes use the same rendering engine. The mode toggle changes who drives clicks, not what the engine does.

The artifact's central claim — provocative, possibly contested — is presented immediately at session start. The audience either accepts it and explores depth, or resists it and engages stated oppositions. Either way the path is recorded; the canvas grows; the argument is built spatially as it is walked.

A core hypothesis: when an audience pulls the thread themselves rather than being walked through it, defense mechanisms (identity-protection, motivated dismissal) bypass. Conclusions feel earned rather than imposed. The interactive design is not just ergonomic — it is the mechanism by which resistance is reduced.

---

## 2. Conceptual model

### 2.1 Two graphs sharing node identity

Cards in the system participate in two layered graphs:

- **Argument graph.** Nodes are claims/supports/oppositions/etc.; edges are typed argumentative relations (supports, opposes, qualifies, etc.). Traversed via *border tabs* on cards. Clicking a tab advances the argument and the canvas.
- **Knowledge graph.** Nodes overlap with argument-graph nodes; edges are typed inline references (definitions, citations, cross-references) embedded in card body text. Traversed via *inline terms*. Hovering or clicking a term clarifies the current claim without leaving it.

Single-instance principle: each card exists exactly once on the canvas regardless of how many incoming edges (argumentative or knowledge) point to it. A card reached via an argumentative tab and a card reached via an inline `xref` may be the same node.

### 2.2 Latent graph, emergent layout

At session start, only the central claim is visible. The full set of cards exists in a library; the full set of *potential* edges exists in declarations; but neither is laid out on the canvas. Layout is a function of the path taken — the same library produces different visual artifacts depending on the session.

This is a deliberate departure from v2's "spine + ambient canvas" pattern (v2 §2). v2 pre-shows the topology for orientation; this design hides it for narrative drive. The audience feels the structure emerge rather than consulting it.

### 2.3 Two modes, one engine

A path is a sequence of `(card_id, tab_id)` tuples (with optional `(card_id, term_id)` for inline interactions).

- **Speaker mode** loads a pre-edited path and steps through it on speaker advance. The speaker may take an unscripted tab (a *side step*); the engine records the deviation and offers a "return to script" affordance.
- **Self-paced mode** runs the same engine without a script. The user clicks tabs; the path is recorded.

A path is itself an artifact: a delivered talk, a user's exploration, or a saved tour can all be replayed later.

---

## 3. Card system

### 3.1 Card roles

Each card declares a `role`. The role determines visual treatment and default dock direction.

| Role | Description |
|------|-------------|
| `claim` | An assertion or punchline. The artifact's central claim is the entry card. |
| `support.theoretical` | Theoretical development of a claim. |
| `support.mechanistic` | Mechanism-level explanation. |
| `support.empirical` | Empirical evidence. |
| `support.example` | Concrete instantiation; often referenced from multiple claim cards. |
| `support.authority` | Citation, quote, or appeal to recognized authority. |
| `opposition.stated` | A steel-manned counter-position to be debated. |
| `opposition.counter` | Counter-evidence to a claim. |
| `opposition.reductio` | Reductio ad absurdum of a claim. |
| `concession` | Granting partial validity to an opposition. |
| `synthesis` | Reconciliation of claim and opposition. |
| `punchline` | Condensed rhetorical landing of a prior claim; timing-critical. |
| `hook` | Opening move; motivates the central claim. |
| `definition` | Satellite card defining a term (knowledge graph). |
| `citation` | Satellite card holding a quote with attribution (knowledge graph). |

**(open)** Final list of roles. Likely to grow or merge during prototyping.

### 3.2 Edge types (argumentative graph)

| Type | Reading |
|------|---------|
| `supports` | The child supports/develops/evidences the parent. |
| `opposes` | The child contests the parent. |
| `qualifies` | The child restricts the scope of the parent. |
| `instantiates` | The child is a concrete example of the parent. |
| `depends-on` | The parent requires the child to be understood first. |
| `responds-to` | The child addresses an opposition raised earlier. |
| `synthesizes` | The child reconciles two earlier cards. |
| `defers-to` | The child is a "we'll return to this" promise. |

Each declared edge becomes an available *border tab* on the parent card. Tab visibility may be gated by *preconditions* (e.g., a `synthesizes` tab is only available after both the claim and at least one opposition have been visited on this path).

**(open)** Final list of edge types. Final tab-precondition language.

### 3.3 Inline reference types (knowledge graph)

| Type | Behavior |
|------|----------|
| `def` | Definition. Hover → tooltip; click → pin a small definition card. |
| `clarify` | Disambiguates how a term is used here. Hover → tooltip. |
| `cite` | Citation/quote/authority. Hover → tooltip with attribution; click → expand quote. |
| `xref` | Cross-reference to another card in the library. Click flies camera to that card; draws a thin "referenced" edge. |

Each type has a distinct visual mark on the term so the audience can predict the click contract before clicking.

**(open)** Final list of inline reference types. Final visual treatments.

### 3.4 Card schema (proposed)

Cards are stored as YAML files, one per card.

```yaml
id: bayesian_foil
role: opposition.stated
thesis_role: load_bearing            # load_bearing | enriching
summary: |
  Bayesian decision theory as the elegant unification that
  appears to dissolve the prior indeterminacies.
faces:
  layperson: |
    Bayesian decision theory dissolves the [frame problem](xref:frame_problem)
    via subjective priors and [maximum expected utility](def:max_eu).
    McCarthy [(1969)](cite:mccarthy1969) framed it this way.
  statistician: |
    ...
  mathematician: |
    ...
edges:
  - to: priors_are_values
    type: opposes
    label: But priors are themselves a value choice
    precondition: null               # always available
  - to: dutch_book_argument
    type: supports
    label: Dutch book coherence argument
  - to: triage_under_bayes
    type: instantiates
    label: Bayesian triage as the dream
  - to: bayesian_synthesis
    type: synthesizes
    label: So how do we live with this?
    precondition:
      visited_all: [priors_are_values, bayesian_foil]
inline_terms:
  max_eu:
    kind: def
    tooltip: |
      The decision rule selecting the action that maximizes
      expected utility under one's posterior beliefs.
  mccarthy1969:
    kind: cite
    tooltip: |
      McCarthy & Hayes 1969, "Some Philosophical Problems from
      the Standpoint of Artificial Intelligence."
  frame_problem:
    kind: xref
    target: frame_problem            # card id; tooltip uses target's `summary`
notes_to_self: |
  Foil card — keep it presented at full strength before any
  knockdown. The synthesis edge is only meaningful after the
  audience has seen both this and the priors_are_values opposition.
```

**Required fields:** `id`, `role`, `faces` (at least one face), `edges` (possibly empty).

**Body markup.** Body text in `faces` is markdown-flavored with custom inline-reference syntax: `[display text](kind:term_id)` where `kind` is one of `def`, `clarify`, `cite`, `xref`. The renderer parses these as interactive spans with type-specific visual treatment.

**(open)** Final body markup syntax. Final list of required fields. Final precondition expression language (plausible options: `visited_all`, `visited_any`, `not_visited`).

---

## 4. Interaction model

### 4.1 Border tabs (argumentative graph)

Each declared edge whose precondition is satisfied appears as a border tab on the parent card. Tabs carry:

- A **type icon** — predicts the move type at a glance.
- A **teaser label** — the author's lead-in to where the edge goes; pulls curiosity.

Visible tab cap: probably 3–5 visible at once with overflow ("more") if more edges qualify. **(open)**

Clicking a tab:

1. Spawns the target card if it has not been visited; flies camera to it if it has.
2. Docks the new card to the parent at an angle determined by edge type (see §5.1).
3. Records `(parent_id, tab_id)` in the session path.
4. Updates available tabs on the new current card.

### 4.2 Inline terms (knowledge graph)

Inline-marked terms in card body are interactive:

- **Hover.** Shows a tooltip near the term. Tooltip content comes from the term's declared `tooltip` text (for `def`, `clarify`, `cite`) or from the target card's `summary` (for `xref`). Dismisses on mouse-out.
- **Click.** Behavior depends on type:
  - `def` / `cite` / `clarify` — pins a small satellite card next to the host (smaller than argument cards). The pinned card persists on canvas.
  - `xref` — flies camera to the existing target card; draws a thin "referenced" edge. No new card spawned.

Authoring discipline: ~3–4 annotated terms per card maximum. Over-annotation creates click-distractor noise.

### 4.3 Revisit policy

A card with multiple incoming references is reached at most once visually:

- On argumentative revisit (a tab points to an already-visited card): fly camera to the existing card; draw a new edge from the source.
- On knowledge revisit (an `xref` points to an already-visible card): same — fly + new edge.

This preserves spatial memory: the audience always knows where things "are."

### 4.4 Termination affordances

Self-paced mode has no inherent end. Two affordances:

- **Home pin.** A persistent affordance returns camera to the central claim card.
- **Destination cards.** Synthesis or thesis-restatement cards are flagged in their schema as destinations; reaching one signals "you've earned this resolution." A subtle visual completion cue surfaces on arrival.

In speaker mode, the script defines the end.

**(open)** Whether self-paced sessions count as "complete" only when a destination is reached.

---

## 5. Spatial semantics and rendering

### 5.1 Docking by edge type

Position encodes argumentative relationship. Default angle conventions:

| Edge type | Dock direction relative to parent |
|-----------|-----------------------------------|
| `supports` | Below or behind (foundation metaphor) |
| `opposes` | Across — left or right (visible confrontation) |
| `qualifies` | Above (a hat / restriction metaphor) |
| `instantiates` | Off-axis satellite (dotted edge, smaller) |
| `depends-on` | Behind / below (prerequisite metaphor) |
| `responds-to` | Curve back toward the addressed card |
| `synthesizes` | At apex between the synthesized parents |
| `defers-to` | Side-shelf with "promised" visual treatment |

**(open)** Whether these are locked by edge type or author-overridable per edge.

### 5.2 Layout policy (collisions)

When multiple children dock at the same parent and direction:

- **Stratify by ring.** Each generation gets its layer at increasing radial distance from the central claim.
- **Within a ring, spread.** Existing siblings push slightly to make room; edge curvature adjusts.

This preserves a "depth from start" reading at zoom-out.

**(open)** Exact spread algorithm. Pixel constants for ring radii.

### 5.3 Persistence and fade

Past cards remain on canvas, never erased.

- Current card: full opacity, centered.
- Recent cards (last few): full opacity, normal size.
- Older cards: reduced opacity; smaller on zoom-out.
- The session's whole path is always visible at zoom-out.

**(open)** Fade curve / zoom thresholds.

### 5.4 Camera moves

- **On tab click.** Animated pan + zoom to the dock position of the new card.
- **At branch points.** **(open)** brief zoom-out to show available tabs, then zoom-in on chosen branch — automatic, or only on explicit "show me what's near" affordance.
- **Persistent overlay.** Small "you are here" pin and a breadcrumb of the last 1–2 cards.

**(open)** Animation timing constants.

### 5.5 Visual sketch of a card with both interaction tiers

```
┌──────────────────────────────────────────────────┐
│  Bayesian decision theory dissolves the          │
│  [frame problem]↗ via subjective priors and      │
│  [maximum expected utility]ⁱ.                    │
│  McCarthy [(1969)]ⁿ framed it this way.          │
│                                                   │
│  [⊃ unpack]      [⚔ But priors are values]      │
│  [✦ triage]      [⚖ concede partial...]         │
└──────────────────────────────────────────────────┘

  ↗ = xref       (camera flies to existing card)
  ⁱ = def        (info tooltip on hover)
  ⁿ = cite       (note tooltip with attribution)
  ⊃ ⚔ ✦ ⚖       = edge type icons on border tabs
```

In real CSS: dotted underline for `def`, dashed-with-arrow for `xref`, superscript glyph for `cite`, wavy underline for `clarify`. **(open)**

---

## 6. Speaker mode mechanics

A speaker path is a YAML/JSON sequence of `(card_id, tab_id)` tuples plus per-step display preferences (e.g., dwell hints).

```yaml
path_id: 30min_mixed_audience
audience: layperson
steps:
  - card: central_claim
    dwell_hint: 30s
  - card: central_claim
    tab: unpack_claim
  - card: indeterminacy_intro
    tab: triage_example
  ...
```

Speaker UI (early sketch, **(open)**):

- Main canvas (audience-facing).
- Speaker console (presenter-only): preview of upcoming step; "next step" affordance; visible side-step options on the current card; "return to script" button when off-script.
- Optional teleprompter pane with the active card's body in the chosen audience face.

A side step is just a tab click that's not the next scripted step. The engine records it; the "return to script" button replays the script's next step from wherever the speaker is now.

**(open)** Whether unscripted side-step paths flow back automatically (camera animates back to the spine card) or wait for explicit user action.

---

## 7. Authoring artifacts

Beyond the card library, authors maintain:

- **Friction map.** Per audience profile, a paragraph: walk-in beliefs, resistance points, defense mechanisms, counter-moves. Promoted from v2's lightweight artifact to first-class — used to tune tab labels and ordering. (See v2 §5.5 for a worked example.)
- **Belief trajectory.** Per audience, a paragraph: by what point in a typical path each load-bearing claim should be accepted, made uneasy, or committed to. Used during the review pass.
- **Audience faces.** Per card, multiple body renderings. Runtime config picks which face renders.
- **Saved paths.** Pre-edited speaker paths and notable user explorations, both serializable and replayable.

Friction maps and belief trajectories remain free prose, not per-card metadata (per v2 §1.4 — the lightness is deliberate even though they're more central here than in v2).

---

## 8. Tech stack

**Locked for v0:**

- **React** — component framework.
- **React Flow (xyflow)** — canvas substrate. Provides pannable/zoomable infinite canvas, custom node components, custom edge components, and animated camera APIs.
- **TypeScript** — type discipline across cards and engine.
- **Vite** — bundler / dev server.
- Client-side bundle only. No backend.

**Conventions:**

- All cards are React components rendered as React Flow custom nodes.
- All edges are React Flow custom edges, rendered with type-specific styling.
- All state (current card, path, canvas nodes, available tabs, tooltips) is React state.
- Card library and edge declarations loaded as static YAML or JSON at build/load time.
- Markdown rendering for card body via `react-markdown` with a custom plugin that parses the `[text](kind:id)` inline-reference syntax into interactive React components.

**Storage:**

- Cards: one YAML file per card in `cards/`.
- Friction maps and belief trajectories: free-form Markdown in `audience-notes/`.
- Saved paths: JSON in `paths/`.

**Build:**

- A small build step concatenates card YAML into a JSON bundle (or imports them via Vite glob imports) so the SPA is fully static.

**(open)** Whether to use a state library (Zustand, Jotai) or stick to React context + reducer for v0. Default: start with context + reducer; switch if state coordination grows painful.

---

## 9. Open decisions

Tracking what is not yet locked:

1. Final list of card roles, edge types, and inline reference types.
2. Tab visibility cap (3–5? overflow strategy?).
3. Tab precondition expression language.
4. Layout angle conventions per edge type — locked vs. author-overridable.
5. Layout collision algorithm (within-ring spreading specifics).
6. Persistence/fade visual specifics (opacity, scale, distance curves).
7. Camera animation timing and zoom-out-at-branch behavior.
8. Pinned definition cards: forever-on-canvas or fade like argument cards.
9. Speaker console UI specifics.
10. Unscripted side-step flowback — automatic or manual return.
11. Path recording fidelity — tuples only, or include timestamps and dwell.
12. State management library choice.
13. Whether to support multiple destinations or insist on one thesis (per v2 §1.3).
14. Recursion depth cap on argument trees (counter-counter-counter limits).
15. Final visual language for inline term marks and tab icons.

---

## 10. First prototype scope

Goal: validate the core spatial mechanics on a small, real example (to be supplied by content author).

**In scope:**

- React + React Flow + Vite project skeleton.
- Card schema implemented for: `claim`, `opposition.stated`, `support.*` (one or two subtypes), `concession`, `synthesis` — five to seven cards minimum.
- Edge types implemented: `opposes`, `supports`, `concedes` (likely an alias for a specific edge use), `synthesizes`, `instantiates` — four to five edge types minimum.
- Border tab interaction: click → spawn (or fly-to) child card → dock at edge-type angle → camera animates.
- One inline reference type: `def` with hover tooltip.
- Persistence: past cards remain on canvas; basic fade only.
- Self-paced mode only.
- One audience face per card.
- Hand-authored YAML cards loaded at build time.

**Out of scope (deferred to v0.2+):**

- Speaker mode and saved paths.
- Inline reference types beyond `def` (`clarify`, `cite`, `xref`).
- Multiple audience faces with runtime switching.
- Tab preconditions.
- Friction-map / belief-trajectory tooling.
- Polished visual design — function over form for v0.

**Success criteria for v0:**

- Audience starts at the central claim. Border tabs are visible and labeled.
- Clicking an `opposes` tab spawns the opposition card, docks it across from the claim, camera follows.
- Clicking a `concedes`-style tab spawns the concession card, docks it between claim and opposition.
- Clicking a `synthesizes` tab spawns the synthesis card at apex.
- Camera follows smoothly throughout; past cards remain visible.
- Hovering an inline `def` term shows a tooltip near the term.
- Path is recorded internally and inspectable (e.g., a small dev panel showing the `(card, tab)` sequence).

This minimum validates the spatial semantics and the gestural model. Everything else builds on top.

---

## 11. Iteration plan

Build in tight loops with concrete content:

1. Scaffold project + minimum schema + one rendered card.
2. Add docking on tab click for one edge type (`opposes` is the visually cleanest first case).
3. Add the second edge type (`supports`); validate that two simultaneously docked children behave well.
4. Add concession + synthesis to validate apex docking and `synthesizes` precondition.
5. Add `def` inline tooltip.
6. Pause and review on real content (provided by author) before adding more roles, faces, or speaker mode.

Spec updates happen in this file as decisions firm up. Open items move from §9 into the relevant section as they get locked.
