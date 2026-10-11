# Notes on `corpus_topology_v0.json`

Remarks made during and after producing the first full-corpus topological
digest. The digest itself (36 nodes, 54 edges) is in
`corpus_topology_v0.json`. It is deliberately rough — node bodies are 1–3
sentences, not card-quality prose — and is meant to surface the *shape* of
the territory rather than to be walked as-is.

These notes record what fell out of the exercise that seems worth
keeping. They are not conclusions; they are flags for the next pass.

---

## What naturally clusters

Five groupings emerged without forcing:

1. **Disposition entry** — `humility_as_disposition`,
   `what_could_be_over_what_is`, `intent_purpose`.
2. **Inference foundations** — `deduction_vs_induction`,
   `statistics_as_practice`, `probability_as_judgment` and its
   neighbors (`exact_probability_is_error`, `conditional_probability_framing`,
   `law_of_total_probability`, `subjectivity_of_conclusions`).
3. **Frame-problem core** — `frame_problem`, `indeterminacy_of_relevance`,
   `finite_specification`, `frame_applies_to_both_modes`,
   `frame_invisible_from_inside`, with `three_kinds_of_uncertainty` and
   `russells_turkey` immediately adjacent.
4. **Decision-making lower row** — `world_responds_to_action`,
   `decisions_on_expectations`, `expected_utility_distribution`,
   `calibration_often_unavailable`, `no_right_balance`, anchored by
   `crossing_example`.
5. **Modern context** — `automation_opacity`,
   `throughput_outpaces_evaluation`, `model_free_drift`,
   `data_driven_extrapolation_limit`, `data_we_dont_have`.

`meta_no_free_lunch` and `vaguely_right_precisely_wrong` sit on the far
right as common destinations across the clusters.

The exploration / agency cluster (`agents_are_formal_systems`,
`two_ways_to_discover_relevance`, `exploration_expands_ontology`,
`exploration_doesnt_escape_finite_spec`, `exploration_practical_limits`)
is a sixth grouping, but a thinner one — it hangs off the frame-problem
core and loops back to `finite_specification`.

---

## `finite_specification` is the hub

The highest-degree node in the digest. It is reached from inference (via
`conditional_probability_framing` and `law_of_total_probability` through
`frame_problem`), from the frame problem itself, from exploration (as
the same limit one level up), and from the automation context (where
the finite spec is what produces the modal failures). It sends to
`frame_invisible_from_inside`, `three_kinds_of_uncertainty`,
`automation_opacity`, and `meta_no_free_lunch`.

If the existing orientation paths each route through this node, the
corpus is telling us it is the actual hub of the territory rather than
a stop along the way. Worth checking whether the path manifests treat
it as load-bearing accordingly.

---

## What the digest treats as one anchor among several

`crossing_example` and `russells_turkey` are both in the digest as
worked illustrations attached via `instantiates` to the abstract claims
they make vivid. Neither is privileged as the canonical anchor at the
corpus level — they are *available* anchors. The same is true of the
anchors the orientation paths chose that are not in this digest
(the handoff, the diagnosis, the formalization, the deployment): they
are equally legitimate instantiations, and the corpus does not pick
between them. Anchor selection is a path-level decision.

This matches what synthesis §3.9 already says about anchors being
path-specific. The digest is consistent with that and gives no reason
to revise it.

---

## A single long-range edge worth flagging

`humility_as_disposition → meta_no_free_lunch` (e_54, `synthesizes`).
This says the structural reason humility is load-bearing rather than
just stylistic is the meta no-free-lunch — there is no procedure that
makes humility optional. The edge is plausible at the corpus level.
Whether you want it surfaced in any particular path or whether humility
should arrive only through `vaguely_right_precisely_wrong` is a
judgment call. It is in the digest provisionally.

---

## Items folded into other nodes (not lost, but not their own nodes here)

These claims from the corpus are in the digest but absorbed into other
nodes' bodies rather than getting their own card:

- "Stripping uncertainty in long chains is risky" — folded into
  `displaying_uncertainty`.
- "A rational agent does not pick a lower-EU alternative" — folded into
  `decisions_on_expectations`.
- "Bounded rationality" as terminology — implicit in `meta_no_free_lunch`.
- "Pure mathematics has no direct reach into the real world" — folded
  into `statistics_as_practice`.
- "Exploration has no built-in guarantee of discovery" — folded into
  `exploration_expands_ontology`.

Easy to promote any of these to their own node if a path wants them
as a separate beat.

---

## Cluster boundaries I am least confident about

- **Exploration cluster.** Four nodes
  (`two_ways_to_discover_relevance`, `exploration_expands_ontology`,
  `exploration_doesnt_escape_finite_spec`,
  `exploration_practical_limits`) might collapse into two at this
  resolution. They are individually thin and densely connected to each
  other.
- **`agents_are_formal_systems` vs `frame_invisible_from_inside`.**
  These are close. Their distinction is "what kind of system has this
  property" (agents) vs "the property itself" (invisible from inside).
  Plausible to merge; plausible to keep separate.
- **`exact_probability_is_error` as its own node.** It is the only
  `opposes` edge in the graph. May want to be a `clarify` inline term
  on `probability_as_judgment` rather than a freestanding node — at
  card-quality resolution, the move is "what this reading rules out"
  inside the same beat.

---

## What the digest tells us about edge-type usage

In 54 edges across the corpus-level web:

- `supports` — dominant, used for the core argumentative chain.
- `qualifies` — used where one claim adds a condition or scope to
  another.
- `instantiates` — used for worked illustrations (`crossing_example`,
  `russells_turkey`) and for the "this is how the abstract claim shows
  up here" move.
- `synthesizes` — used sparingly, for the moves that bring multiple
  threads together (`frame_problem → finite_specification`,
  `frame_invisible_from_inside → meta_no_free_lunch`,
  `meta_no_free_lunch → vaguely_right_precisely_wrong`,
  `humility → meta_no_free_lunch`).
- `responds-to` — used for back-edges that name what an earlier card
  was implicitly raising (`meta_no_free_lunch → finite_specification`,
  `frame_applies_to_both_modes → deduction_vs_induction`,
  `data_we_dont_have → three_kinds_of_uncertainty`).
- `opposes` — used **once** (`probability_as_judgment →
  exact_probability_is_error`).
- `depends-on`, `defers-to` — not used.

The thinness of `opposes` is consistent with what the orientation paths
show: the corpus is mostly built out of mutually-reinforcing claims,
not adversarial moves. The cases where opposition matters (sensitivity
analysis vs framing; scale vs frame; safety factors vs frame failures;
methodology vs meta-no-free-lunch) are *path-level* moves — they
position a defense to be addressed within a card, rather than appearing
as `opposes` edges in the corpus graph.

That is information about the structure: at the corpus level, oppositions
are *contained inside cards* in the orientation paths, not declared as
graph edges. The contract's `opposes` edge type may be doing less work
than it looks.

---

## What this digest does *not* do

- It does not encode page 0 / 1 / 2 structure. Nodes have one `body`
  field for now.
- It does not declare `notes_to_self`, `inline_terms`, `role`,
  `thesis_role`, or any path-manifest metadata.
- It does not match the existing orientation paths node-for-node.
  Some corpus nodes here (e.g., `subjectivity_of_conclusions`,
  `law_of_total_probability` as its own node,
  `data_driven_extrapolation_limit`) do not appear in any of the
  authored v0 paths. Some path nodes (e.g., `failure_at_interfaces`,
  `automation_erodes_reflexivity` in the engineer path) are
  *orientation-specific instantiations* of corpus moves and would not
  appear at the corpus-graph level.

The digest is meant to be the layer *above* the orientation paths —
the library the paths select and instantiate from.

---

## Next-pass questions this surfaces

1. Does the relationship between the corpus topology and the
   orientation paths want to be made explicit — i.e., does each path
   declare which corpus nodes it instantiates, the way card edges
   declare relations?
2. Is the corpus-level graph meant to be walkable on its own (as a
   "structure of the territory" view), or only as the source the path
   manifests draw from?
3. If `finite_specification` is the corpus hub, should every legitimate
   path be required to visit it? (Synthesis §2.2 already names the C1–C5
   structural floor — this is roughly C2/C3 in that scheme.)
4. Do the corpus-level nodes that don't appear in any current path
   (e.g., `subjectivity_of_conclusions`,
   `data_driven_extrapolation_limit`) want to be authored as
   library-level cards in case a future path needs them, or left as
   topology entries until a path actually pulls on them?
