# Project Synthesis

A consolidated working document for the Argument Canvas project, capturing intent, content, and the first authoring contract. This document is the starting input for the design sessions that follow; it summarizes prior artifacts and does not introduce decisions beyond what they have already established. Open questions are listed at each layer as work for those sessions.

---

## 1. Intent

### 1.1 Overall objective

An interactive, on-demand argument display — an infinite spatial canvas — designed for **efficient convincing on a set of load-bearing claims**. The audience reaches conclusions by walking the argument themselves, with cards materializing one at a time as the path is walked.

The bet underneath: an audience that pulls the thread bypasses more defenses than one that is led through it. Identity-protective, motivated-dismissal, and "this-is-not-my-field" reactions partially dissolve when the walker chooses each next step. Conclusions feel earned rather than imposed. Interactivity is the *mechanism* of reduced resistance, not just an ergonomic flourish.

### 1.2 Two modes, one engine

The same engine supports two delivery modes:

- **Speaker mode** — a presenter walks a prepared path with room to step aside and return.
- **Self-paced mode** — an explorer clicks their way through their own walk.

The mode changes who is driving; it does not change what the engine does.

### 1.3 What the artifact is and isn't

It is **not** a slide deck with branching, not a concept map shown all at once, and not bound to a single thesis, a single arc, or a single opening. The same library admits several plausible paths for different audiences, several legitimate destinations, and several possible hooks into the material.

Specific paths are *proposed* (via suggested connections from each card), and load-bearing passage points (central claims and the moves that earn them) are expected to be visited. Side excursions are permitted around that backbone rather than instead of it.

### 1.4 Core commitments

- **Latent graph, emergent layout.** Cards and the relations between them exist in the library; the canvas only shows what has been walked. Past cards persist; the spatial trace *is* the record of the walk.
- **Spatial semantics carry argumentative meaning.** The position of a card relative to its parent says something about how it relates — supporting, opposing, qualifying, reconciling. The exact orientations are not pre-locked; they are choices left open for the design to instantiate.
- **Path as first-class artifact.** A walked path — a talk delivered, an exploration completed, a saved tour — is itself an object that can be recorded, replayed, compared.
- **Argument made by walking it.** The audience reaching a conclusion through their own clicks experiences the argument differently than one led through it. This is the central design bet on lowering defended resistance.

### 1.5 Tensions to keep visible

- *Emergence vs orientation.* Hiding the map gives the walk its drive; it also makes losing one's place possible. Wayfinding has to do work the map would otherwise do.
- *Audience-driven vs author-led.* More walker freedom means less rhetorical control. Multiple legitimate destinations is the resolution, not a workaround.
- *Coherence vs plurality.* Many audiences, destinations, openings — but it must still feel like one artifact. The unity comes from the shared library and the meaning of the spatial relations, not from a forced single thesis.
- *Resistance vs guidance.* The walk is suggested rather than free. Suggestions must be strong enough to be taken without collapsing back into the linear form, and weak enough that the audience experiences the walk as their own.

---

## 2. Content

### 2.1 The corpus

A raw, unsorted body of claims and ideas, tagged loosely by type (central claim, structuring remark, tool definition, framing move) and by domain (mathematics, statistics, epistemology, decision-making, engineering, computing). The corpus spans:

- *Disposition and epistemic stance.* "What could be" over "what is"; epistemic humility as a virtue; structural and psychological pressures against humility; vaguely right vs precisely wrong.
- *The act of decision.* The world responds to the action, not to the picture; decisions implicitly rest on expectations; calibration of those expectations is often not possible.
- *Inference.* Deduction vs induction; probability as judgment-given-knowledge, not as a property of nature; conditional probability and the law of total probability as the proper framing for prediction under uncertainty.
- *The frame problem.* Indeterminacy of relevance as a circular issue; finite specification as the structural source of uncertainty; the frame applies to deduction and induction equally; aleatory / epistemic / ontological uncertainty as three categories, the third being the one practice underweights; Russell's turkey as the worked illustration.
- *Exploration, agency, blind spots.* Two ways to discover relevance (told, or bumped into); exploration as a way to expand the ontology; agents as formal systems with frames that cannot self-audit; "structurally blind to its own blind spots."
- *Decision-making under uncertainty.* Robustness vs optimization-for-anticipated; no formal solution to reasoning from a finite position; meta-level no-free-lunch as the foreclosure of "we just need a better methodology."
- *Contemporary automation context.* Complexity with AI; opacity from layered abstraction; model-free vs model-based drift; throughput of confident outputs outpacing the resource to evaluate them; surveillance vs scrutiny.
- *Data-driven limits.* Extrapolation in high-dimensional space; "the data we don't have" as the paradigmatic decision-under-uncertainty problem.

### 2.2 First structuring attempt — the friction map

A cross-read of the corpus that identifies:

**The structural floor — five commitments every legitimate path is expected to make visible:**

- **C1.** Acting on the world is mediated by a picture of the world.
- **C2.** Relevance requires a frame, and the frame is structurally invisible from inside.
- **C3.** Specification is finite; what isn't specified is aleatory, epistemic, or ontological.
- **C4.** Rigor within a frame and adequacy of the frame are different things.
- **C5.** The meta-level no-free-lunch — no procedure decides when a frame is adequate.

**Five orientation profiles** — engineer, statistician, mathematician, CS/ML practitioner, layperson — each with: a legitimate starting point, a natural question, an earned-vs-asserted ledger, a defense mechanism, an *exposure set* of three to four claims most likely to question that audience's practice, and a likely path shape.

**The path-completion criterion is exposure, not assent.** A path is complete when it has visited the structural floor and the orientation-specific exposure set, regardless of whether it ends at a shared destination. Coherent paths may disagree across orientations; that is by design.

### 2.3 Two essays as instances, not templates

Two finished long-form essays exist as evidence of what a structurally consistent walk through the territory can look like. They are broadly addressed to the engineer / decision-maker register (with the statistician implied). They are useful as instances and as sources for some of the sharpest phrasings ("transfer of responsibility dressed as information"; "precisely wrong"; "surveillance, not scrutiny").

They are **not** the canonical structuration. A mathematician's walk or a layperson's walk would visit the same floor and exposure set through different territory, in a different order, anchored on different scenarios.

### 2.4 Content-side open questions for design sessions

- Whether C5 (meta no-free-lunch) is a floor-visited commitment or a destination card whose load varies by orientation.
- Whether "exploration as a way to discover relevance" is a bridge concept or a sixth structural commitment.
- Whether the "honest communication" claim is one card or several (it plays different roles for engineer, statistician, and layperson).
- Whether the initial five orientations want to be extended (risk professional, policy analyst, philosopher of science) and what their exposure sets would be.
- How sharply the "central claim" entry point should be drawn for each orientation (the more provocative the opening, the higher the bypass-of-defenses payoff and the higher the bounce risk).

---

## 3. First authoring contract

Derived retrospectively from authoring two paths (engineer, statistician). The contract separates *what the corpus contains* (cards) from *how a walk uses it* (path manifests).

### 3.1 Cards are fact-about-themselves; paths are fact-about-composition

A card declares everything it is, independent of any path: identity, pages, declared edges to other cards, inline terms, notes-to-self. A path manifest declares the walk: which cards appear, with what `role`, `thesis_role`, `pages_key`, and `surfaced_edges`.

Rationale: the same card can be load-bearing in one orientation and enriching in another; can surface different tabs depending on which path is walking; can render different pages for different audiences. Encoding any of this on the card itself would force one path to misrepresent the card.

### 3.2 Required card fields

```yaml
id: snake_case_unique_id
pages:         # see 3.3
edges:         # see 3.4
inline_terms:  # see 3.5, present when applicable
notes_to_self: # see 3.7, required
```

Not on the card: `role`, `thesis_role`. These belong to the path manifest.

### 3.3 Pages — three in fixed roles, orientation-keyed

Each card has three pages with fixed semantic functions:

- **Page 0 — the durable condensation.** One short paragraph, 2–4 sentences. The version of the claim that remains on the canvas after the receiver moves on, that fills tab-preview tooltips, that survives a week in the receiver's memory. Quotable sentences live here.
- **Page 1 — the unfolding.** Two to four paragraphs. Mechanism, worked illustration, the move the card actually makes. May stage a steel-manned opposition and respond to it.
- **Page 2 — the consolidation.** One to three paragraphs. The "what this means" or "what follows" beat. Often returns to the anchor. Sometimes names what the card is *not* doing — closing off available misreadings.

Pages are keyed by orientation:

```yaml
pages:
  shared:
    - <page 0>
    - <page 1>
    - <page 2>
  engineer:        # orientation-specific
    - <page 0>
    - <page 1>
    - <page 2>
  statistician:    # orientation-specific
    - ...
```

**Resolution rules.** A card with only `shared` is identical for every path. A card with orientation-keyed pages uses the keyed version when present, falling back to `shared`. Cards **merge** (carry multiple page keys on one card) when page 0 is the same claim across orientations; cards **split** into separate IDs when page 0 itself differs.

### 3.4 Edges — card-intrinsic, path-filtered

Each card declares edges to other cards. Edges are the truth about the argumentative graph; the path manifest then selects which edges become tabs on the canvas for that walk.

```yaml
edges:
  - to: target_card_id
    type: supports | opposes | qualifies | instantiates
        | depends-on | responds-to | synthesizes | defers-to
    label: <teaser shown on the tab>
    precondition: <optional, see 3.6>
```

**Authoring discipline:**

- Outgoing edges go *forward and outward* — toward cards that open new territory. Back-edges to already-visited cards are pruned because the single-instance principle does that work spatially.
- Typically 2–4 edges per card, occasionally 5. More than that is a signal to reconsider.
- Edge labels are **teaser-shaped**, pulling curiosity toward what the linked card opens, not summarizing what it contains. "Why is the number conditional?" beats "Predictions are conditional."

**Edge types in active use:** `supports`, `qualifies`, `instantiates`, `responds-to`, `synthesizes`, `opposes`.

**Declared but unexercised:** `depends-on`, `defers-to`. Pruning them from the schema is not warranted; declarations cost nothing and they may be needed by future paths.

### 3.5 Inline terms — the knowledge graph inside card bodies

Body markdown supports inline-reference syntax: `[display text](kind:term_id)`, where `kind` is one of:

- `def` — definition (hover tooltip; click pins a small satellite card).
- `clarify` — disambiguates how the term is used here (hover tooltip).
- `cite` — citation or attribution (hover tooltip; click expands quote).
- `xref` — cross-reference to another card in the library (click flies camera to that card; draws a thin "referenced" edge; no new card spawned).

Term definitions live in the card's `inline_terms` block:

```yaml
inline_terms:
  term_id:
    kind: def | clarify | cite | xref
    tooltip: |
      <tooltip content; for xref, the target card's page 0 is used by default>
    target: <card_id, only for xref>
```

**Authoring discipline:** ~3 terms per card maximum where used. Over-annotation creates click-distractor noise. The page-0 statement is sometimes the place an inline term lands — acceptable when the term is the actual content of the claim, not when it is decorative.

Only `def` has been exercised so far. The other kinds are ready in the contract but unused.

### 3.6 Tab preconditions (optional, deferred)

An edge may be gated by a precondition on the session's walked history:

```yaml
precondition:
  visited_all: [card_a, card_b]
```

Candidate expression forms include `visited_all`, `visited_any`, `not_visited` (final language deferred).

Preconditions are not in the current cards. Two cases the paths have already identified as candidates: synthesis-edges where both synthesized parents must have been walked, and meta-level cards (like the no-free-lunch landing) that should not surface until the practice-implicating cards have built motivation for them. Defer locking until prototype walks surface the need.

### 3.7 Notes-to-self — required, author-facing

Every card carries a `notes_to_self` block recording:

- The structural function the card plays in the path(s) that use it.
- The authoring choices and what they trade against ("avoid the word *subjective* deliberately"; "the engineer experiences C3 and C4 as one move, splitting them feels artificial at first contact").
- Open questions the card hasn't fully resolved.
- Cross-references to the corpus or articles where specific phrasings are sourced.

This field is **not consumed by the renderer**; it is consumed by future authoring, including by the author six months later. It is the durable record of *why the card is the way it is*.

### 3.8 Roles (path-manifest-level)

Roles in active use:

- `hook` — opening card; motivates the walk.
- `spine` — load-bearing argumentative move on the canonical walk.
- `branch` — reachable but not required for path completion.
- `support.example` — concrete instantiation, often referenced from multiple spine cards.
- `landing` — closing card; the place a path *earns*. Distinct from the last spine beat.

**Declared but unexercised:** `support.theoretical`, `support.mechanistic`, `support.empirical`, `support.authority`, `opposition.stated`, `opposition.counter`, `opposition.reductio`, `concession`, `synthesis`, `punchline`, `foil`, `definition`, `citation`. Kept available for paths that will need them (the mathematician path will likely exercise `opposition.stated`, for example).

**A note on opposition.** The statistician path folds a steel-manned opposition into page 1 of the responding card rather than authoring it as a freestanding `opposition.stated`. Whether opposition wants to be freestanding or folded is path-dependent and open.

### 3.9 The anchor pattern

Each path has one recurring concrete scenario — authored as a card with `role: hook` and referenced via `instantiates` edges from subsequent cards. The anchor has its own three-page treatment (scenario in two sentences; scenario expanded with stakes and the path's question; meta-claim that the scenario will keep returning).

**Anchors are typically path-specific.** The crossing works for the engineer because their working life is concrete decisions; the handoff works for the statistician because their working life is methods deployed in chains. The single-instance principle plus `instantiates` edges keep the anchor alive on the canvas as the walk proceeds — camera flies to the existing anchor on revisit rather than respawning it.

### 3.10 Path manifest — companion schema

A path manifest is the artifact the composer reads. Sketch:

```yaml
path_id: engineer_v0
orientation: engineer
anchor: the_crossing
landing: vaguely_right_precisely_wrong

cards:
  - id: <card_id>
    role: hook | spine | branch | support.example | landing
    thesis_role: load_bearing | enriching
    pages_key: shared | engineer | statistician | ...
    surfaced_edges:
      - to: <target_card_id>
      - to: <target_card_id>
  - id: <card_id>
    ...
```

Alongside the manifest, two short prose documents live at the path level:

- **Friction map** — for each orientation served, a paragraph: walk-in beliefs, resistance points, defense mechanisms, counter-moves. Consulted during card authoring and reviewed before rendering.
- **Belief trajectory** — for each orientation, a paragraph: by what point in a typical path each load-bearing claim should be accepted, made uneasy, or committed to. Informs sequencing without dictating it.

Both stay **free prose, not per-card schema fields.** The lightness is deliberate (a maximalist per-card encoding would add authoring work without reducing it elsewhere).

### 3.11 Deliberately omitted from the schema

- **No `time_cost` field.** The paged-card model bounds card length per page; total time per card is roughly page count × dwell. Reintroduce if speaker-mode scripting demands it.
- **No `prerequisites` DAG.** Prerequisites are emergent from edge topology rather than declared. May want revisiting if the composer enforces prerequisites at compose-time.
- **No audience-side per-card metadata.** No `assumed_priors`, `target_update`, `anticipated_resistance` on cards. These live in the friction map at path level; mechanizing them into card fields is the over-engineering the architecture is built to avoid.

### 3.12 Contract-side open questions for design sessions

- Whether `surfaced_edges` is **opt-in** (list what to surface) or **opt-out** (surface all declared, list exclusions). Opt-in is currently in use; may become burdensome at scale.
- Whether the meta-level commitment (C5) is enriching or load-bearing for the engineer path, and whether its tab should be precondition-gated from earlier cards.
- Whether `honest_communication` and `responsibility_in_the_chain` merge into one card with orientation-keyed pages or stay as separate cards.
- Whether `opposition.stated` wants to be freestanding (per the earlier spec) or whether folding into the responding card's page 1 (per `bounded_robustness_is_not_framing`) is the better default.
- Whether `xref` inline references warrant authoring treatment distinct from same-card `def` terms, given they fly the camera rather than spawn a tooltip.
- Whether tab preconditions get added now or after prototype walks surface the need.
- Whether the engineer YAMLs (which pre-date this checkpoint and still use a single-face `engineer:` block plus a `summary` field) get refactored to the page 0/1/2 structure now or after the first canvas walk is rendered.
- **Spatial-semantics conventions** — which edge type docks in which direction relative to the parent (supports below, opposes across, qualifies above, synthesizes at apex, etc.). The intent commits to "spatial semantics carry meaning" but leaves the specific orientations open. The prototype will exercise the conventions; locking is deferred until then.

### 3.13 What the contract gives the prototype

A walkable structure consisting of:

- A **card library** where each card is a complete fact-about-itself (id, pages, edges, inline_terms, notes_to_self).
- A **path manifest** that selects, weights, and filters that library for a specific walk (role / thesis_role / pages_key / surfaced_edges per card).
- A **renderer** that reads the composition, spawns cards on tab clicks, docks them with edge-type-semantic positioning, preserves spatial memory of past cards, and flies camera to existing cards on revisit rather than respawning them.
- **Authoring artifacts** (friction map, belief trajectory) consulted during card authoring and during a review pass before rendering.

The first canvas walk is what tells us whether the contract holds. Documents past this synthesis should be revised against rendered evidence, not against further document iteration.
