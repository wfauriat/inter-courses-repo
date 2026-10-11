# Card Authoring Contract — Checkpoint

Working version of the card and topology contract, derived from the
engineer and statistician paths as authored. This document captures
the schema decisions that the act of authoring two paths has surfaced,
and the conventions both paths follow consistently.

This is a checkpoint, not a finished spec. Items marked **(decision)**
are proposed commitments; items marked **(observed)** are descriptions
of what the existing cards already do consistently. Open questions are
listed at the end.

---

## 1. The card is a fact-about-itself, not a fact-about-a-path

**(decision)** A card declares everything it is, independent of any
path: its identity, its relations to other cards, its full set of
pages, its inline terms. A *path manifest* — separate file — declares
composition: which cards appear in this walk, in what role, with what
weight, rendering which pages, surfacing which edges as tabs.

Rationale: the engineer path and the statistician path want to give
the same card different `role`, different `thesis_role`, sometimes
different pages, and sometimes different surfaced edges. Encoding any
of this on the card itself forces one path to misrepresent the card.

The card is the durable object across orientations. The path is the
composition over it. This is v2's authoring/composition separation,
made path-specific.

---

## 2. Required fields

```yaml
id: snake_case_unique_id
pages: <see §3>
edges: <see §4>
```

Optional but present-when-applicable:

```yaml
inline_terms: <see §5>
notes_to_self: <free prose>
```

Notably **not** on the card itself: `role`, `thesis_role`. These move
to the path manifest. The current YAMLs carry them; for backward
compatibility the contract can permit them as a default (used when no
path manifest entry overrides), but the canonical location is the
path.

---

## 3. Pages

**(observed across both paths)** Three pages, in fixed roles:

- **Page 0** — the durable condensation. One short paragraph, 2–4
  sentences. This is what remains visible on the canvas after the
  receiver moves on. This is what appears in tab-preview tooltips.
  This is the version of the claim the receiver can paraphrase a week
  later.
- **Page 1** — the unfolding. The mechanism, the illustration, the
  move the card actually makes. Two to four paragraphs. Uses concrete
  language and worked illustration. May use italics for emphasized
  terms. May stage and respond to an opposition.
- **Page 2** — the consolidation. The "what this means" or "what
  follows" beat. One to three paragraphs. Often returns to the
  recurring anchor (the crossing, the handoff). Sometimes names what
  the card is *not* doing — closing off available misreadings.

**(decision)** Pages are orientation-keyed:

```yaml
pages:
  shared:
    - <page 0>
    - <page 1>
    - <page 2>
  engineer:
    - <page 0 engineer-specific>
    - <page 1 engineer-specific>
    - <page 2 engineer-specific>
  statistician:
    - <page 0 statistician-specific>
    - <page 1 statistician-specific>
    - <page 2 statistician-specific>
```

A card with only `shared` is the same content for every path that
visits it. A card with `engineer` and `statistician` entries (and no
`shared`) is orientation-specific throughout. A card with `shared`
plus orientation keys uses the orientation-keyed version when
available, falls back to `shared` otherwise.

**Rule for whether a card splits or has orientation-keyed pages:**
*cards merge (have multiple page-keys) when page 0 is the same claim
across orientations; cards split (have separate IDs) when page 0 is a
different claim, even if the territory is shared.*

The current evidence:

- `frame_is_invisible_from_inside` and `probability_as_judgment`
  should have engineer and statistician pages on the same card — page
  0 is the same claim.
- `three_kinds_of_uncertainty` and `three_kinds_of_uncertainty_stats`
  are separate cards — page 0 makes a different move (engineer: "here
  is a trio"; statistician: "the first two are home territory, the
  third is outside the machinery").
- `the_crossing` and `the_handoff` are separate cards — different
  anchor, different page 0.
- `predictions_are_inherently_imperfect` and
  `conditioning_is_load_bearing` are separate cards — engineer
  collapses C3+C4; statistician separates them.
- `honest_communication` and `responsibility_in_the_chain` — current
  call is separate, but their page 0s are close enough that this is a
  candidate for merge into one card with two page-1/page-2 sequences.
  Decision deferred.

---

## 4. Edges

**(decision)** Edges are *card-intrinsic* — they declare the
argumentative graph as a fact about the corpus, not about any path.
The path manifest then selects which edges to *surface as tabs* on
the canvas for that walk.

```yaml
edges:
  - to: target_card_id
    type: supports | opposes | qualifies | instantiates | depends-on | responds-to | synthesizes | defers-to
    label: <teaser shown on the tab>
```

This means a card may declare more edges than any single path uses.
That is correct: the card is honest about its place in the network;
the path filters.

**(observed)** Edge authoring discipline across both paths:

- Outgoing edges go *forward and outward*, toward cards that open new
  territory. Back-edges to already-visited cards are pruned because
  the single-instance principle does the work spatially.
- Edges declared on a card are typically 2–4, occasionally 5. More
  than 4 is a signal to reconsider.
- Edge labels are *teaser-shaped* — they pull curiosity toward what
  the linked card opens, not summaries of what the linked card
  contains. "Why is the number conditional?" not "Predictions are
  conditional." "What about sensitivity analysis?" not "Sensitivity
  analysis is bounded robustness."
- Edge types: `supports`, `qualifies`, `instantiates`, `responds-to`,
  `synthesizes`, and `opposes` are all in active use. `depends-on`
  and `defers-to` are declared in the schema but not yet exercised.
- `instantiates` edges that return to the anchor card (the crossing,
  the handoff) are deliberate — they keep the anchor alive across the
  walk and trigger the single-instance fly-to.

**(decision, optional)** Tab preconditions on edges:

```yaml
edges:
  - to: target_card_id
    type: synthesizes
    label: <teaser>
    precondition:
      visited_all: [card_a, card_b]
```

The current YAMLs don't use these; the path overviews flag two cases
that probably want them (`meta_no_free_lunch` from any card other
than the landing; synthesis-edges where both synthesized parents must
be visited). Defer adding preconditions until the prototype walks —
they're easier to motivate from observed misfires than from
anticipated ones.

---

## 5. Inline terms

**(observed)** Inline references in page text use the
`[display](kind:term_id)` syntax. The term is declared in an
`inline_terms` block at the card level:

```yaml
inline_terms:
  term_id:
    kind: def | clarify | cite | xref
    tooltip: |
      <tooltip text shown on hover>
    target: <card_id, only for xref>
```

Used so far: only `def`, on `three_kinds_of_uncertainty`,
`three_kinds_of_uncertainty_stats`, and `conditioning_is_load_bearing`.
The contract is ready for `clarify`, `cite`, and `xref` but they
haven't been exercised.

**(observed)** Authoring discipline: ~3 terms per card maximum where
used. The page-0 statement is sometimes the place an inline term
lands (e.g., `three_kinds_of_uncertainty_stats` page 0 has three
`def` terms in one sentence) — this is acceptable when the terms are
the actual content of the claim, not when they're decorative.

---

## 6. The roles vocabulary

**(observed and decision)** Roles that have been exercised:

- `hook` — opening card; motivates the walk.
- `spine` — load-bearing argumentative move on the canonical walk.
- `branch` — reachable but not required for path completion.
- `support.example` — concrete instantiation, often referenced from
  multiple spine cards. The `.example` subtype is the only `support.*`
  subtype that's been used; v0 spec mentions `support.theoretical`,
  `support.mechanistic`, `support.empirical`, `support.authority` but
  none have appeared.
- `landing` — closing card. New role, not in v0 spec; introduced by
  `vaguely_right_precisely_wrong`. Distinct from `spine` in that the
  landing is the place a path *earns*, not just the last spine beat.

Not yet exercised:

- `opposition.stated` — declared in v0 spec. The statistician's
  `bounded_robustness_is_not_framing` *contains* a steel-manned
  opposition on page 1 but is itself `role: spine` with no separate
  opposition card. The opposition is *folded into the response*, not
  authored as its own card. This is a deliberate authoring choice.
  The mathematician path will likely use `opposition.stated` as a
  freestanding card type.
- `opposition.counter`, `opposition.reductio`, `concession`,
  `synthesis`, `punchline`, `foil`, `definition`, `citation` — all
  declared, none exercised yet.

**(decision)** Don't prune the unexercised roles from the schema.
They cost nothing as declarations; they're useful to have ready when
the path that needs them arrives.

---

## 7. Notes-to-self

**(observed)** Every authored card has a `notes_to_self` block. It
carries:

- The structural-function rationale ("first practice-implicating
  exposure card," "bridge-layer claim in engineer first-contact
  form")
- The specific authoring decision and what it trades against ("avoid
  the word 'subjective' deliberately," "the engineer experiences C3
  and C4 as one move; splitting them feels artificial at first
  contact")
- Open questions the card hasn't fully resolved
- Cross-references to the corpus or article when a specific phrase is
  sourced ("the 'transfer of responsibility dressed as information'
  phrasing is from the corpus")

**(decision)** Keep this field required. It's the durable record of
*why the card is the way it is*, which is what every later revisor —
including the author six months later — needs first. It is not
consumed by the renderer; it is consumed by future authoring.

---

## 8. The anchor pattern

**(observed)** Each path has one recurring concrete scenario,
authored as a card, referenced via `instantiates` edges from later
cards.

- Engineer path: `the_crossing` is `role: hook`, referenced from
  cards 2, 3, 5, 7, 9.
- Statistician path: `the_handoff` is `role: hook`, referenced from
  card 7 (likely more once authoring stabilizes).

**(decision, observed)** The anchor card has its own three-page
treatment. Page 0 is the scenario in two sentences. Page 1 is the
scenario expanded with stakes and the question the path will answer.
Page 2 is the meta-claim that the scenario will keep returning —
explicit notice that this is the path's anchor.

The anchor's `pages` are orientation-specific by nature; the same
anchor rarely works for two orientations. (The crossing works for
the engineer because their working life is concrete decisions; the
handoff works for the statistician because their working life is
methods deployed.) Anchor cards are unlikely to be reused across
paths.

---

## 9. Authoring discipline beyond the schema

**(observed)** These are conventions both paths follow that aren't
enforced by the schema but pay off:

- **One claim per card.** Both paths split cards rather than load
  them. `predictions_are_inherently_imperfect` collapses C3+C4 *as a
  deliberate engineer-first-contact authoring choice* and the
  notes-to-self flag it. The statistician path splits them back out.
- **Page 0 sentences survive the walk.** The lines that are meant to
  be quotable a week later are at page 0, in the condensation. "The
  world will not deliver 73% of a crossing." "Surveillance, not
  scrutiny." "A transfer of responsibility dressed as information."
  Authoring discipline: when a card has a sentence that should be
  the take-away, it goes in page 0, not page 1.
- **The defense gets named before it gets answered.**
  Practice-implicating cards explicitly state the defense ("safety
  factors handle this," "misuse is a deployment problem," "robustness
  analysis bounds this") at full strength on page 1 before responding
  to it. This is the friction map informing the card-level authoring
  directly.
- **Concession before response.** Where a card refuses a move, it
  concedes what the move *does* address before naming what it
  doesn't. Safety factors *do* address anticipated failure modes; the
  question is what they don't address. Robustness analysis *does*
  bound uncertainty within a class; the question is what's outside
  the class.
- **Forward-and-outward edges only.** Back-edges to already-walked
  cards are pruned. The single-instance principle does that work
  spatially.

---

## 10. What the contract deliberately omits

- **No `time_cost` field.** v2 has this; the paged-card model makes
  it less necessary (each page has roughly bounded length; total time
  on a card is roughly page count × dwell). Reintroduce if needed
  when speaker-mode scripting is authored.
- **No `prerequisites` DAG.** The current cards declare argumentative
  relations via edges; prerequisites are emergent from edge topology
  rather than declared. This is a real choice and may want revisiting
  if the composer needs to enforce prerequisites at compose-time.
- **No audience-side metadata on cards.** Per v2 §1.4 and the
  checkpoint, friction maps and belief trajectories are *path-level*
  artifacts, not per-card. Resist the temptation to add
  `assumed_priors`, `target_update`, `anticipated_resistance` fields
  to cards — that mechanization is the over-engineering the
  architecture is built to avoid.

---

## 11. Path manifest — companion schema (sketch)

A path manifest is the artifact the composer reads. It declares the
walk, the per-path metadata, and the surface filtering of the
underlying card library.

```yaml
path_id: engineer_v0
orientation: engineer
anchor: the_crossing
landing: vaguely_right_precisely_wrong

cards:
  - id: the_crossing
    role: hook
    thesis_role: enriching
    pages_key: shared    # or engineer, statistician, etc.
    surfaced_edges:      # which of the card's declared edges become tabs
      - to: predictions_are_inherently_imperfect
      - to: probability_as_judgment
  - id: predictions_are_inherently_imperfect
    role: spine
    thesis_role: load_bearing
    pages_key: shared
    surfaced_edges:
      - to: frame_is_invisible_from_inside
      - to: three_kinds_of_uncertainty
      - to: the_crossing
  - id: frame_is_invisible_from_inside
    role: spine
    thesis_role: load_bearing
    pages_key: engineer    # this card has both engineer and statistician pages
    surfaced_edges:
      - to: failure_at_interfaces       # engineer-relevant exposure card
      - to: meta_no_free_lunch
  # ... remaining cards in the canonical walk
```

The manifest is what makes path-relative metadata work. It's also
what the composer would generate from a config in v2's architecture;
for now it's hand-authored.

---

## 12. Open questions

These are the questions the next path's authoring is most likely to
resolve, because that path will exercise more of the unexercised role
and edge types and force more reuse decisions.

- Whether `honest_communication` and `responsibility_in_the_chain`
  merge into one card with orientation-keyed pages, or stay as
  separate cards.
- Whether tab preconditions on edges (§4) get added now or after the
  prototype walks.
- Whether the renderer needs `time_cost` and `prerequisites` after
  all once speaker-mode is back on the table.
- Whether the manifest's `surfaced_edges` block becomes burdensome at
  scale — if every path manifest has to list edges for every card, a
  default of "surface all declared edges except those filtered out"
  may be cheaper than "list the surfaced ones."
- Whether `opposition.stated` wants to be a freestanding card (as the
  v0 spec proposes) or whether folding the opposition into the
  responding card's page 1 (as `bounded_robustness_is_not_framing`
  does) is the better default.
- Whether `xref` inline references warrant a separate authoring
  treatment from same-card `def` terms, given that they fly the
  camera to an existing card rather than spawning a tooltip.

---

## Summary

The contract that the two authored paths have converged on:

1. **Cards declare themselves; paths declare composition.** Cards
   carry id, pages, edges, inline_terms, notes_to_self. Paths carry
   the walk, per-card role and thesis_role, page-key selection, and
   edge surfacing.

2. **Three pages per card, in fixed roles.** Page 0 is the durable
   condensation. Page 1 is the unfolding. Page 2 is the consolidation.

3. **Pages are orientation-keyed when the same claim has different
   illustrations across orientations.** Cards split into separate IDs
   when page 0 — the claim itself — differs.

4. **Edges are card-intrinsic; paths filter them.** The card's edges
   are the truth about the argumentative graph. Each path surfaces a
   subset.

5. **The friction map and belief trajectory live at the path level.**
   They are consulted during authoring and reviewed before rendering.
   Resist mechanizing them into per-card schema.

6. **Notes-to-self is the durable authoring record.** Required on
   every card.

7. **Anchor cards are path-specific.** Each path has one; it's
   referenced via `instantiates` edges and kept alive on the canvas
   by the single-instance rule.
