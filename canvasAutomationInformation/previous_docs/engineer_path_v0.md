# Engineer Path — Card Set v0

First path through the territory, authored for the engineer orientation. Nine cards: one hook, three structural-floor cards in engineer-side first-contact form, one inference-bridge card, two practice-implicating exposure cards, one disposition card, one landing card.

The path is designed to be walkable end-to-end but also wanderable. Each card has multiple outgoing edges; the "canonical" walk visits them in roughly the order presented below, but the engineer in self-paced mode can pull threads in other orders.

**A note on what's not here yet.** No examples beyond the one in the hook (the corpus's lifeboat). No `xref` cards for definitions (`probability`, `expected utility`, etc.) — these get authored when the engineer reaches a card that needs them, and we'll see how many we actually need. No tab preconditions yet beyond the obvious (a synthesis tab requires both parents visited). These come in iteration.

---

## Card 1: `the_crossing`

```yaml
id: the_crossing
role: hook
thesis_role: enriching
summary: |
  A concrete decision under uncertainty with stakes — the framing
  scenario the rest of the path keeps returning to.
faces:
  engineer: |
    You're crossing the Atlantic in a small boat. Before you leave,
    you decide whether to take a satellite phone. Conditions look
    favorable. The forecast is good. The boat is well-maintained.
    A satellite phone costs money, weight, and one more thing to
    maintain. You can compute the probability of needing it: take
    historical incident rates for the route, adjust for season and
    boat class, propagate forecast uncertainty. You get a number.

    The number is real, and it is also conditional on what you decided
    to include in the calculation.

    Whatever the number is, the crossing will either go fine or it
    won't. The probability is how you judge likelihood before you
    sail. The world will not deliver "73% of a crossing." It will
    deliver a crossing.

    The question this path is about: what is the methodological
    care that the gap between the number and the crossing actually
    warrants?
edges:
  - to: predictions_are_inherently_imperfect
    type: supports
    label: Why is the number conditional?
  - to: probability_as_judgment
    type: instantiates
    label: What is "the number," really?
  - to: vaguely_right_precisely_wrong
    type: qualifies
    label: Vague rightness vs precise wrongness
```

**Notes.** The crossing is the corpus's lifeboat scenario. It's the recurring concrete example for the engineer path — referenced from at least cards 2, 3, 5, and 7 below. Should be authored once with care; everything else points back to it.

---

## Card 2: `predictions_are_inherently_imperfect`

```yaml
id: predictions_are_inherently_imperfect
role: spine
thesis_role: load_bearing
summary: |
  Predictions are not approximations to a true number; they are
  conditional outputs of a finite specification. The conditioning is
  structural, not a flaw to be reduced.
faces:
  engineer: |
    When you computed the crossing's incident probability, you
    decided what to include. Historical rates over what window?
    Adjusted for which conditions? Which boat class is yours
    grouped with? Which kinds of incidents counted as "needing"
    the phone?

    Every prediction works this way. You specify a finite set of
    conditions; the prediction is conditional on that specification.
    The number is precise within the specification and silent about
    what the specification omits.

    This is not a problem you fix by adding more variables. Each
    addition is another specification choice. The set is always
    finite. What's outside it doesn't show up in the prediction —
    not as uncertainty, not as a wider interval. It is silent.

    "Inherently imperfect" doesn't mean "imprecise within the
    model." It means "precise within a frame the model cannot see
    past." The two are different failure modes and they call for
    different responses.
edges:
  - to: frame_is_invisible_from_inside
    type: supports
    label: Why can't the model see past the frame?
  - to: three_kinds_of_uncertainty
    type: qualifies
    label: What kinds of uncertainty are there?
  - to: the_crossing
    type: instantiates
    label: Back to the boat
```

**Notes.** This is the engineer-side first-contact form of C3 (finite specification) and C4 (rigor-within-frame vs adequacy-of-frame). I'm rolling them together because the engineer experiences them as one move: "your prediction is conditional and the conditioning is structural, not a fixable imprecision." Splitting them feels artificial at first contact.

---

## Card 3: `frame_is_invisible_from_inside`

```yaml
id: frame_is_invisible_from_inside
role: spine
thesis_role: load_bearing
summary: |
  The structural reason: any reasoning system filters relevance
  using prior assumptions about what could be relevant. It cannot
  audit those assumptions using its own machinery, because the
  machinery is what the assumptions produced.
faces:
  engineer: |
    Why can't the model see what it omitted? Because the model
    was built by deciding what mattered, and the deciding happened
    before the modeling. The model's machinery — its variables,
    its likelihoods, its loss function — is the result of those
    decisions, not a tool for auditing them.

    A safety factor doesn't help here. Safety factors are calibrated
    against failure modes you anticipated. The frame failures that
    matter are the ones you didn't anticipate — the variable that
    wasn't in the analysis because it wasn't on the list, the
    interaction between subsystems that no single model covered,
    the assumption too obvious to write down.

    The model can be internally consistent, mathematically sound,
    empirically validated against everything you measured. None of
    that tells you whether the frame was adequate. "Adequate"
    is a relation between the frame and what's outside it, and
    "what's outside it" is exactly what the frame doesn't carry.

    This is not a quirk of bad models. It is a property of any
    reasoning system that filters a finite specification from an
    open world.
edges:
  - to: predictions_are_inherently_imperfect
    type: supports
    label: This is why predictions are conditional
  - to: failure_at_interfaces
    type: instantiates
    label: Where does this bite in practice?
  - to: meta_no_free_lunch
    type: qualifies
    label: Can't we solve this with better methodology?
  - to: the_crossing
    type: instantiates
    label: What did the crossing forecast not see?
```

**Notes.** This is C2 in engineer first-contact form. The hardest card to land for this audience, because the structural claim has to feel like *the reason for what they just accepted* rather than a philosophical add-on. The "safety factor doesn't help" move is the specific counter to the engineer's defense mechanism — it concedes what safety factors *do* address while naming what they don't.

This card has four outgoing edges, more than I'd want on most cards. The fourth (`meta_no_free_lunch`) is a `qualifies` edge that anticipates the engineer's likely move ("better methodology"). It's not on the main spine but should be available — and probably has a precondition that delays it until at least the next card has been visited, so the structural argument lands before the methodological one is raised.

---

## Card 4: `three_kinds_of_uncertainty`

```yaml
id: three_kinds_of_uncertainty
role: branch
thesis_role: enriching
summary: |
  Uncertainty quantification distinguishes aleatory (chosen not to
  specify) from epistemic (could-be-reduced). The category that
  matters most — what wasn't considered — is the one practice
  underweights.
faces:
  engineer: |
    Standard uncertainty quantification gives you two categories.
    Aleatory uncertainty is what you've chosen to model as randomness
    — wave heights, component lifetimes, arrival times. Epistemic
    uncertainty is what you could in principle reduce with more
    information — better measurements, more data, finer modeling.

    These are real categories and they're useful. They are also
    not the whole picture.

    There is a third category that gets less attention: ontological
    uncertainty. What didn't make it into the model because no one
    thought to put it there. It is not a wider interval on an
    existing variable. It is the variable that isn't on the list.

    When a system fails in ways that surprise its designers, the
    failure mode is rarely "aleatory variation was higher than
    expected" and not always "epistemic uncertainty was higher
    than expected." Often it's "this wasn't in the model at all."

    The standard UQ machinery doesn't speak to this category, and
    cannot, because the machinery operates inside a specified set
    of variables. The category names what the specification
    omitted, and the specification is what the machinery runs on.
edges:
  - to: failure_at_interfaces
    type: instantiates
    label: A concrete failure mode
  - to: frame_is_invisible_from_inside
    type: supports
    label: This is the structural reason
  - to: honest_communication
    type: supports
    label: What this means for what you report
```

**Notes.** This card is a branch off the spine but probably load-bearing for the engineer specifically. Their UQ training likely covers aleatory and epistemic; introducing ontological is the move that brings the structural claim into their working vocabulary.

---

## Card 5: `probability_as_judgment`

```yaml
id: probability_as_judgment
role: spine
thesis_role: load_bearing
summary: |
  Probability is not a quantity discovered in the world; it is a
  distribution over alternative possibilities given background
  knowledge. The mathematics is sound; the metaphysics that often
  accompanies it is not load-bearing.
faces:
  engineer: |
    Go back to the crossing. You computed a probability of needing
    the phone. What is that number?

    One reading: it's a frequency. Out of many similar crossings,
    that fraction would have incidents. This is meaningful when
    "similar crossings" is a well-defined reference class with
    stable conditions. For most actual decisions — your boat, your
    route, your season, your forecast — the reference class is
    something you constructed, not something you found.

    A more honest reading: the probability is how you distribute
    over alternative possibilities given what you know. Your
    background knowledge — historical rates, forecast, boat
    condition — informs the distribution. The number summarizes
    your judgment, made explicit and computable, conditional on
    that knowledge.

    This matters because the second reading is what you're actually
    doing, even when the first reading is what you say you're doing.
    The mathematics is identical. The interpretation determines
    what you'd do when the reference class is contested, when the
    background knowledge is incomplete, when someone asks "what is
    the probability of X" for an X that has never happened before.

    Treating probability as judgment-given-knowledge keeps the
    conditioning visible. Treating it as frequency-in-nature hides
    the conditioning behind a claim about the world.
edges:
  - to: the_crossing
    type: instantiates
    label: The probability of needing the phone
  - to: predictions_are_inherently_imperfect
    type: supports
    label: This is why the number is conditional
  - to: honest_communication
    type: supports
    label: What this means for how you report a number
```

**Notes.** This is the bridge-layer claim from the corpus, in engineer-first-contact form. I wrote it to make the foundational distinction *do work* on the crossing example rather than presenting it as a definitional preliminary. The statistician path would author this card differently (faces, not edges) — the same claim is foundational for them but the engineer needs it in this register.

The card avoids the word "subjective" deliberately. "Judgment given background knowledge" is the same object and doesn't trip the tripwire.

---

## Card 6: `failure_at_interfaces`

```yaml
id: failure_at_interfaces
role: support.example
thesis_role: enriching
summary: |
  The places frame failures actually live: between models, in
  excluded variables, in unstated assumptions. The exposure
  claim's concrete instantiation for the engineer.
faces:
  engineer: |
    Where do frame failures actually live? Three places, in
    practice.

    Between models. You have a structural model, a load model, a
    fatigue model. Each is validated within its scope. The failure
    mode that gets you is the coupling — load patterns the
    structural model doesn't represent, fatigue regimes the load
    model doesn't anticipate. No single model is wrong. The
    interface is wrong.

    In the variable that was excluded. The analysis runs on a
    selected set of variables. The selection happened before the
    analysis you can audit. The variable that wasn't selected
    doesn't appear as zero — it doesn't appear. Years later, when
    failure data accumulates, that variable turns out to have been
    the one.

    In the assumption too obvious to state. Steady-state operation.
    Standard conditions. Components from qualified vendors. These
    are not modeled because they are the ground on which the
    modeling stands. They are also exactly what shifts in deployment
    contexts the analysis didn't anticipate.

    These three are not exotic. They are the modal failure modes
    of complex engineered systems. They are also the failure modes
    that more analysis, within the same frame, does not catch.
edges:
  - to: frame_is_invisible_from_inside
    type: supports
    label: The structural reason
  - to: automation_erodes_reflexivity
    type: supports
    label: Why automation makes this worse
  - to: honest_communication
    type: responds-to
    label: What you owe whoever bears the consequences
```

**Notes.** This is the first practice-implicating exposure card. It names the specific failure modes the engineer's practice tends to be insulated from. The "between models / excluded variable / unstated assumption" trio is from the article (section 3) and the corpus. Concrete enough to land; structural enough to do the work.

---

## Card 7: `automation_erodes_reflexivity`

```yaml
id: automation_erodes_reflexivity
role: spine
thesis_role: load_bearing
summary: |
  Automation increases the throughput of confident outputs while
  reducing the resource available for evaluating each. The
  capacity to interrogate frames is what gets cut, because
  interrogation does not scale.
faces:
  engineer: |
    Most of what you do is now in part automated. Calculations
    that took weeks take hours. Analyses that needed a team can
    be run by one engineer. The throughput of confident outputs
    has gone up, dramatically.

    The throughput of frame-interrogation has not gone up. It
    can't, structurally. Interrogating a frame means stepping
    back, asking what was assumed, considering what's outside the
    analysis. That work is slow. It resists automation, because
    automating it would require knowing in advance what to ask —
    which is the thing being looked for.

    The ratio matters. When ten outputs need evaluation and you
    have time for five, you triage. When a thousand outputs need
    evaluation and you have time for five, the evaluation stops
    being meaningful. It becomes spot-checking, which is
    surveillance, not scrutiny.

    Your practice now operates under conditions where producing
    confident outputs is cheap and catching frame failures is
    expensive. That is a real shift in the working conditions of
    the discipline, and it is not neutral.

    The capacity to do the work that catches frame failure has to
    be actively protected, because the working conditions will
    not protect it for you.
edges:
  - to: failure_at_interfaces
    type: supports
    label: Why this is the practice-implicating claim
  - to: honest_communication
    type: supports
    label: What you owe downstream
  - to: vaguely_right_precisely_wrong
    type: synthesizes
    label: The disposition this calls for
```

**Notes.** This is the central practice-implicating exposure card for the engineer. It's where the path turns from "here's why predictions are structurally imperfect" to "here's why your current working conditions make catching frame failure harder than it used to be." Should land with sharpness — this is the card whose job is to make the engineer's practice questionable to themselves.

The framing avoids moralizing. The claim is structural ("automation increases throughput, interrogation doesn't scale") rather than evaluative ("the field has lost its way").

---

## Card 8: `honest_communication`

```yaml
id: honest_communication
role: spine
thesis_role: load_bearing
summary: |
  A number reported without its conditions is a transfer of
  responsibility, not a transfer of information. Honest
  communication of what a number depends on is part of the
  number's content, not commentary on it.
faces:
  engineer: |
    When you hand a number to a decision-maker — the probability
    of failure, the projected cost, the expected performance —
    you are also handing them everything the number is conditional
    on. Whether you communicate that conditioning or not, they are
    receiving it.

    A number without its conditions is not a more efficient
    communication. It is a transfer. The receiver acts on the
    number as if it stood alone, the consequences land on them,
    and the conditions that should have shaped their action are
    invisible. You have not given them information. You have
    given them an output and kept the information.

    This is the load the disposition actually bears. Frames are
    invisible from inside; you cannot eliminate the conditioning.
    What you can do — what is in your control — is make the
    conditioning legible to whoever bears the consequences. The
    conditions of the number, the assumptions of the analysis,
    the regime of validity, the failure modes you anticipate and
    the ones you cannot rule out.

    "Decision-makers want a number, not a philosophy lecture" is
    fair up to a point. The point at which it stops being fair is
    when the number drives a consequential outcome badly wrong and
    the receiver had no way to see it coming. At that point, the
    missing conditions are not a kindness withheld.
edges:
  - to: automation_erodes_reflexivity
    type: responds-to
    label: This is why protection has to be active
  - to: vaguely_right_precisely_wrong
    type: supports
    label: The disposition this realizes
  - to: three_kinds_of_uncertainty
    type: responds-to
    label: Including the category that isn't in the number
```

**Notes.** Second practice-implicating exposure card, paired with `automation_erodes_reflexivity`. Where the previous card named the structural pressure on the practice, this one names what the practice owes downstream in spite of that pressure. The phrasing "transfer of responsibility dressed as information" is from the article and is sharper than anything in the corpus — it's the kind of sentence the engineer should be able to remember after the path is over.

---

## Card 9: `vaguely_right_precisely_wrong`

```yaml
id: vaguely_right_precisely_wrong
role: spine
thesis_role: load_bearing
summary: |
  The disposition Keynes named: a different kind of rigor, one
  that knows where its precision was earned and where it was
  assumed, and propagates that awareness rather than laundering
  it.
faces:
  engineer: |
    Keynes is supposed to have preferred being vaguely right to
    precisely wrong. The line is often misread as a defense of
    imprecision. It is not. It is a defense of a different kind
    of rigor.

    Precise wrongness is what happens when an analysis produces
    a sharp number whose frame was inadequate. The number is
    internally consistent. The arithmetic is right. The frame
    omitted something that mattered. The result: high confidence
    in a wrong conclusion, with all the appearances of having
    been done correctly.

    Vague rightness is what happens when an analysis produces a
    less sharp answer that's honest about its conditions, its
    omissions, and its regime of validity. The answer carries
    less false precision. It carries more usable information.

    The discipline this calls for is not vagueness. It is the
    rigor of knowing where your precision was earned and where
    it was assumed. Of propagating that awareness through the
    chain rather than laundering it at every interface where it
    becomes inconvenient. Of designing for robustness to surprise,
    not just optimization for the anticipated case.

    For some problems — well-understood, low-stakes, stable
    conditions — the cost of this is not warranted. For
    consequential decisions in complex or poorly-understood
    systems, it is the minimum the difficulty actually requires.
    The judgment of which is which is itself irreducible. No
    procedure decides it for you.
edges:
  - to: honest_communication
    type: instantiates
    label: One concrete realization
  - to: automation_erodes_reflexivity
    type: responds-to
    label: The disposition under modern conditions
  - to: the_crossing
    type: instantiates
    label: What this would look like for the crossing
  - to: meta_no_free_lunch
    type: supports
    label: Why no procedure decides this
```

**Notes.** Landing card for the engineer path. Not a "destination" in the sense that every audience reaches it — but the place the engineer's walk earns. The closing return to the crossing (via `instantiates`) is deliberate: the path ends where it began, with the receiver in a position to see the original scenario differently. The edge to `meta_no_free_lunch` opens the door to the deeper structural claim for receivers who want to pull further.

---

## Card 10: `meta_no_free_lunch` (provisional, deferred)

**Status: declared but not authored.** This is the meta-level commitment (C5). It should exist as a card the engineer *can* reach but isn't required to visit for path completion. The engineer's path completes at `vaguely_right_precisely_wrong`; the meta-level claim is available as a final pull for the receiver who wants the structural reason behind why no methodology dissolves the problem.

Authoring it for the engineer entry deferred until we know whether it's needed in the prototype. If it appears reachable but unauthored in the canvas, the receiver will see the tab but not be able to click it; we'll see how that feels in practice.

---

## What this card set is, and what it isn't

**It is:** A walkable end-to-end path for the engineer orientation, with multiple legitimate sub-routes between cards. The canonical walk is `1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9`. The engineer can also walk `1 → 5 → 2 → 3 → ...` (entering at the probability question) or `1 → 2 → 3 → 6 → 7 → 8 → 9` (skipping the UQ branch). All of these visit the structural floor and the practice-implicating exposure set; all are complete.

**It isn't:** A claim that the engineer path is *correct* in all its details. The exposure set as currently authored may be too sharp or not sharp enough. The bridge card (`probability_as_judgment`) may want to be split into two cards. The deferred `meta_no_free_lunch` may want to be promoted to load-bearing for the engineer rather than optional. These are exactly the questions that putting the cards on a canvas should help answer.

**Topology summary.**

Spine cards (canonical walk): 1, 2, 3, 5, 7, 8, 9.
Branch cards (reachable but not required): 4, 6, 10.
Load-bearing cards (must appear for path completion): 2, 3, 5, 7, 8, 9.
Practice-implicating exposure cards: 6, 7, 8.
Structural floor cards in engineer first-contact form: 2 (C3+C4), 3 (C2), 5 (gestures at the same point), 10 deferred (C5). C1 is implicit in card 1; it doesn't get its own card for the engineer because the crossing scenario makes it concrete from the start.

**Edge types used.** `supports`, `qualifies`, `instantiates`, `responds-to`, `synthesizes`. Five of the eight v0 §3.2 types. `opposes`, `depends-on`, and `defers-to` are not used in this path — which is itself interesting and worth noting. The engineer path doesn't visibly stage an opposition. That's a real authorial choice (the article doesn't either, in its argumentative spine) but it means the canvas's `opposes`-docking visual won't get exercised by this path alone. The mathematician path probably will exercise it.

**Tab-precondition candidate.** The `meta_no_free_lunch` edge from card 3 (and elsewhere) probably wants a precondition: only available after at least card 6 or card 7 has been visited. The structural meta-claim lands wrong if it appears before the practice-implicating cards have built the motivation for it.

---

## What I'd suggest for the prototype

Author cards 1, 2, 3, 6, 7, 8, 9 first — these are the practice-load-bearing seven. Skip 4 and 5 in the very first prototype build; they're branches/bridges and the canvas will work without them. Skip 10 for now.

This is seven cards. Edges between them. One audience face per card (`engineer`). One inline reference type, on whichever card most wants a `def` (probably `probability_as_judgment` if it's included, otherwise none in the seven-card version). Self-paced mode only. Click a border tab → spawn or fly-to child → dock at edge-type angle → camera animates.

This matches v0 §10's minimum scope almost exactly, with concrete content slotted in.

When this walks end-to-end, we'll know more about whether the architecture holds than any further document iteration would tell us.