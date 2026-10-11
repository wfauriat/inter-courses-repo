# Statistician Path — Card Set v0

Second path through the territory, authored for the statistician
orientation. Ten cards total: six new for this path, four reused from
the engineer set (two unchanged, two with statistician-keyed pages).

The path is designed to be walkable end-to-end and is the first path
that exercises `opposes` / `synthesizes` edge types — the engineer path
was developmental, the statistician path stages a steel-manned objection
at the central practice-implicating card.

**A note on what's new.** This path forces three schema-level decisions
the engineer path didn't: that `pages` is orientation-keyed, that
`thesis_role` and `role` are path-relative rather than card-intrinsic,
and that two cards (the anchor and the central exposure card) genuinely
have to be distinct from their engineer cousins because the move they
make is different. The `_reused_cards.md` file documents the reuse
decisions.

---

## Canonical walk

```
1. the_handoff                          (hook, new)
2. probability_as_judgment              (spine, reused, stats pages)
3. conditioning_is_load_bearing         (spine, new)
4. three_kinds_of_uncertainty_stats     (branch, new)
5. bounded_robustness_is_not_framing    (spine, new, opposition shape)
6. frame_is_invisible_from_inside       (spine, reused, stats pages)
7. the_deployment_gap                   (spine, new)
8. responsibility_in_the_chain          (spine, new)
9. vaguely_right_precisely_wrong        (landing, reused unchanged)
10. meta_no_free_lunch                  (spine, reused unchanged, LOAD-BEARING here)
```

Alternate walks are available — the self-paced statistician can enter
at `conditioning_is_load_bearing` (skipping the anchor's narrative
setup), or pull `meta_no_free_lunch` early from card 5, or visit the
deployment-gap thread before the framing thread. All complete walks
visit the structural floor cards (in this orientation: 3, 6, 10) and
the practice-implicating exposure cards (5, 7, 8).

---

## What's load-bearing

**Structural floor in statistician form:** `conditioning_is_load_bearing`
(C3, finite specification, statistician form), `frame_is_invisible_from_inside`
(C2, statistician page-keys), `meta_no_free_lunch` (C5, promoted to
load-bearing here), `bounded_robustness_is_not_framing` (C4 in
opposition-and-synthesis form, statistician's specific way of
encountering rigor-within-frame vs adequacy-of-frame).

**Practice-implicating exposure cards:** `bounded_robustness_is_not_framing`
(handles the technical-reframing defense), `the_deployment_gap` (handles
the locational defense), `responsibility_in_the_chain` (names what the
practice owes in light of both).

**Hook:** `the_handoff` (not the crossing). The statistician's working
life is methods deployed in chains, not single decisions made. The
hook needs to land at that level of abstraction.

**Landing:** `vaguely_right_precisely_wrong`, same as the engineer.
This is the convergence point — different orientations reach it through
different territory, but the disposition is the place they all earn.

---

## Edge types exercised

`supports`, `qualifies`, `instantiates`, `responds-to`, `synthesizes`,
**`opposes`**.

The opposition appears at `bounded_robustness_is_not_framing` — page 1
stages the steel-manned objection ("sensitivity analysis bounds the
residue") in italics and quoted form, then responds to it structurally.
This is the v0 canvas's first chance to render an `opposition.stated` /
`responds-to` shape. The synthesis is in the page-2 close ("two
tools, two objects").

`depends-on` and `defers-to` still aren't used. They may not be
necessary for any of the five paths — worth tracking but not chasing.

---

## What's not here

- No examples beyond `the_handoff`. The statistician path doesn't need
  a second recurring example; the handoff carries enough by itself.
- No `xref` references between cards. The `def` inline terms on
  `three_kinds_of_uncertainty_stats` and `conditioning_is_load_bearing`
  are the only inline references.
- No speaker-mode path scripted. Same as the engineer path — speaker
  mode is deferred until self-paced walks well on the canvas.

---

## What this card set tests

1. **`pages` is orientation-keyed.** `probability_as_judgment` and
   `frame_is_invisible_from_inside` now have engineer pages and
   statistician pages. The canvas has to know which to render based on
   which path the receiver is walking. (Or, eventually, based on a
   user choice.)

2. **`thesis_role` and `role` are path-relative.** `meta_no_free_lunch`
   is `branch / enriching` for the engineer and `spine / load_bearing`
   for the statistician. The renderer can't get this from the card
   alone; it needs a path manifest.

3. **The same engine renders an adversarial path and a developmental
   path.** The engineer path had no `opposes` cards.
   `bounded_robustness_is_not_framing` is the test of whether the
   spatial-semantics-free design (per the checkpoint) still
   communicates argumentative shape clearly when the shape is
   opposition-and-response.

4. **The structural floor reads as a floor across orientations.** The
   engineer and statistician both visit C2 (frame invisibility), C3
   (finite specification / conditioning), and C5 (meta no free lunch).
   The cards are the same; the entry route, the relative weight, and
   in some cases the pages differ. Whether the receiver, having walked
   either path, has actually been "exposed to the floor" is the
   deepest test the prototype can run.

---

## Suggested prototype scope for adding this path

The engineer path's seven-card scope (`the_crossing`,
`predictions_are_inherently_imperfect`, `frame_is_invisible_from_inside`,
`failure_at_interfaces`, `automation_erodes_reflexivity`,
`honest_communication`, `vaguely_right_precisely_wrong`) was the
sensible minimum for the canvas's first walk.

For the statistician, the analogous minimum is seven cards:
`the_handoff`, `conditioning_is_load_bearing`,
`frame_is_invisible_from_inside` (statistician pages),
`bounded_robustness_is_not_framing`, `the_deployment_gap`,
`responsibility_in_the_chain`, `vaguely_right_precisely_wrong`. The
two reused cards (`frame_is_invisible_from_inside`,
`vaguely_right_precisely_wrong`) are already authored; only five new
cards. `bounded_robustness_is_not_framing` is the high-priority card
to validate, since it's the first opposition shape.

Skip `three_kinds_of_uncertainty_stats`, `probability_as_judgment`
(statistician pages), and `meta_no_free_lunch` in the very first
statistician walk. They're each defensible to defer for the same
reason: the seven-card path is internally complete without them, and
the additions extend rather than complete the walk.

---

## Topology summary

- Spine: 1, 2 (reused), 3, 5, 6 (reused), 7, 8, 9 (reused), 10 (reused).
- Branch: 4.
- Load-bearing in this path: 3, 5, 6, 7, 8, 9, 10.
- Practice-implicating exposure: 5, 7, 8.
- Reused cards: 2, 6, 9, 10. Two need stats pages (2, 6); two reuse
  unchanged (9, 10).
- New cards: 1, 3, 4, 5, 7, 8.
- The `opposes`-shape card: 5. The `synthesizes`-edge close: 5 to 10.

---

## Tab-precondition candidates

- `meta_no_free_lunch` from any card other than the landing should
  probably be precondition-gated: available only after one of the
  practice-implicating cards (5, 7, or 8) has been visited. The
  meta-claim lands wrong without the practical motivation in place,
  for the statistician same as the engineer.

- The `synthesizes`-edge from `bounded_robustness_is_not_framing` to
  `meta_no_free_lunch` is a strong candidate for a precondition
  (`visited_all: [conditioning_is_load_bearing, three_kinds_of_uncertainty_stats]`)
  — the synthesis is meaningful only after both threads it synthesizes
  have been walked.

---

## What this isn't

A claim that the statistician path is *correct* in all its
details. The opposition framing in card 5 is the highest-stakes
authoring choice — too sharp and the statistician feels strawmanned;
too soft and the response doesn't have anything to push against.
That card especially wants prototype-testing with real statistician
readers. `the_handoff` is similarly tunable; the "promotion" framing
may be too elaborate for the page-0 condensation and want
simplifying.

These are exactly the questions that putting the cards on a canvas
should help answer.
