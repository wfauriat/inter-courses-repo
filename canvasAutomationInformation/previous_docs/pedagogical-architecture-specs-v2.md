# Pedagogical Architecture Specs (v2)

A methodology and architecture for building pedagogical artifacts (talks, presentations, courses, explainers) that carry structuring ideas across audiences, durations, and media — without rewriting content per format.

**How to use this document.** As context for an LLM helping you architect a new artifact; as reference for your own authoring and composition process; as a checklist when reviewing existing work. The document is meta-instructional in §§0–4 and §6, and concretely instantiating in §5.

**Version note.** v2 adds two *audience-side* layers — persuasive and affective — to the three content-side layers of v1, plus two lightweight authoring artifacts (a friction map and a belief trajectory) and a review pass that surface these dimensions without mechanizing them into the card schema. The decision to keep them lightweight is itself a deliberate architectural choice and is explained in §1.4. v1 remains valid as a minimal version; v2 adds depth without modifying v1's pipeline mechanics.

---

## 0. Purpose and scope

This document specifies an approach to designing pedagogical artifacts under three simultaneous pressures:

1. *Topology* — the ideas form a structured web, and the audience should sense that structure.
2. *Narrative* — the audience should experience an arc with momentum and resolution, not a tour of a map.
3. *Adaptability* — the same content should serve audiences of varying background and durations without combinatorial rewriting.

The architecture's central claim is that these pressures can be jointly satisfied if and only if authoring, composition, and rendering are separated cleanly into three pipeline stages.

v2 adds a fourth pressure, acknowledged but not mechanized:

4. *Reception* — the audience arrives with priors, identity stakes, and defense mechanisms; the artifact transforms their belief state and produces an emotional and attentional experience along the way. The artifact you author and the experience the audience has are different things, and the gap is what teaching is.

---

## 1. Conceptual foundation

### 1.1 Five layers, two sides

Every pedagogical artifact lives at five layers, organized into two sides.

**Content-side layers (what the artifact is)**

The *content topology* is the timeless web of relations among the ideas. It is atemporal, audience-blind, and indifferent to format. Its nodes are claims, examples, formalisms; its edges are dependencies, contrasts, dualities, instances. Drawing the topology is a clarifying exercise unto itself, but the topology is not the artifact.

The *narrative shape* is the temporal arc you choose through that web. It selects which nodes to visit, in what order, with which emphasis, ending at a thesis. It controls what earns what, what surprises, what the closing sentence is. The same topology can support many narratives; choosing one is a thesis-laden act.

The *medium* is the body that hosts the experience: slides, canvas, interactive web app, keyboard-driven talk, handout, document. A given narrative can be carried by many media; the choice of medium is downstream of (not co-designed with) the choice of narrative.

**Audience-side layers (what the artifact does)**

The *persuasive trajectory* is the path of belief change the artifact produces in the audience. It is independent of content selection: two artifacts visiting identical conceptual nodes can produce very different belief trajectories through framing, sequencing, and which claims are foregrounded. Modeled mechanistically as Bayesian update (priors plus likelihood plus sequential evidence), with psychological deviations from the idealization (identity stakes, defense mechanisms, motivated cognition, peer-coalition position).

The *affective rhythm* is the emotional and attentional experience the artifact produces — tension and release, surprise, breath, drama, the moments where the audience leans in and the moments where they rest. Independent of both content and persuasion: the same persuasive trajectory can be performed warmly or tensely, and the same content can land in entirely different affective registers.

The two sides are not co-equal in authoring. Content-side layers determine *what exists* in the artifact and admit fully formalized representation (cards, prerequisites, audience faces). Audience-side layers determine *what happens to the audience* and resist formalization without diminishing returns. They are real and matter, but they want to be authored as global notes rather than per-card metadata. §1.4 explains why.

### 1.2 Tensions

The layers trade off in practice even though they are independent in principle.

*Topology versus narrative.* Topology-faithful artifacts (canvases, concept maps) make structure visible but kill momentum and leave the order of revelation arbitrary. Narrative-controlled artifacts (linear talks, slide decks) build momentum but hide that the ideas form a structure at all. Most pedagogical artifacts that fail do so by collapsing into one extreme.

*Coherence versus adaptability.* Adapting a single artifact to multiple audiences and durations creates pressure for modularity. Pure modularity, unmediated, becomes the *shopping-list failure mode*: an artifact composed of independent units that do not converge on a single thesis. The cure is to commit, before authoring, to a single load-bearing thesis sentence that every entry-point and every branch must converge on.

*Designed versus received.* The artifact you author and the experience the audience has are different things. Content-side layers describe the artifact; audience-side layers describe the experience. Designing the experience without designing the artifact produces vibes; designing the artifact without anticipating the experience produces lectures that are technically correct and humanly inert.

### 1.3 Load-bearing principles

Three principles are non-negotiable in this approach.

*One thesis sentence.* The artifact has exactly one thesis sentence — what every audience walks away with. It is written before authoring begins. If the sentence cannot be written, the artifact is not yet ready to be built.

*Atomic authoring.* Content is authored in atomic units (cards), one claim per unit, written once and re-rendered many times.

*Authoring–composition–rendering separation.* The pipeline has three stages, each downstream of the previous. Adaptation lives at the composition and rendering layers, never at the authoring layer.

### 1.4 The audience-side layers, treated lightly

The persuasive and affective layers are real dimensions that any working pedagogical artifact navigates whether or not the author thinks about them deliberately. The question is not whether to include them but *how heavily to mechanize them*.

A maximalist persuasive layer would attach to every card a set of fields: assumed priors per audience, target updates, evidence type, anticipated resistance, transparency, commitment level. The composer would then optimize compositions over a belief-trajectory constraint as well as time and prerequisites.

This version is rejected. Two reasons. First, the authoring cost is prohibitive — most fields would be stubbed or skipped in practice, and partial metadata is worse than none because it makes the architecture look more rigorous than it actually is. Second, and more importantly, the v1 architecture earned its complexity by *removing* authoring work (write once, render many); a maximalist audience-side layer does the opposite, adding work without reducing work elsewhere. That asymmetry is the signal that the addition is over-engineered.

The lightweight version retains the insight without the tax. Two artifacts, both global, both authored once for the whole effort, neither encoded into the card schema:

*A friction map per audience profile.* For each audience you actually plan to address, one short paragraph: what they walk in believing, where they will resist, what protects their resistance, what defense mechanism is likely. This is not a fifteen-field schema; it is a paragraph. Drafted after the spine is sketched and before card authoring proceeds in earnest.

*A belief trajectory for the load-bearing claims.* One short paragraph: by what point in the artifact each load-bearing claim should be accepted, made uneasy, or committed to. This is a sketch, not a constraint the composer enforces — it informs sequencing decisions rather than dictating them.

Together these two artifacts cost roughly thirty minutes of writing. They are consulted at two moments: while authoring spine cards (to choose framings that respect resistance points) and during a review pass before rendering (to check that the composition produces the intended trajectory).

The affective layer gets even lighter treatment: no authored artifact at all, only a review pass after composition. Read through once asking where the artifact breathes, surprises, slows, lands. Annotate with rhythm cues if helpful. The point is to have asked the question.

*A note on the temptation.* The architecture is finished when these two layers feel underspecified. After a rendering goes badly and you can identify exactly which resistance point you missed, the temptation to add per-card schema fields is strong. Resist. The remedy for missed resistance is a better friction map and a more careful review pass, not more schema. The audience-side layers are kept underspecified on purpose; the underspecification is what protects authoring discipline.

---

## 2. Architectural patterns

Several patterns sit between the topology-extreme and narrative-extreme.

A *spine with calibrated branches* maintains a canonical linear path (the spine) that always carries the thesis. Each spine node has optional branches you open or skip depending on time and audience. Branches always return to the spine.

A *refracted concrete example* uses a single scenario as the de facto spine. Concepts become episodes that re-tell the scenario through different lenses. Robust across audiences because ground truth is shared.

A *spine plus ambient canvas* runs the talk on a spine while a small map of the topology stays visible throughout, with a "you are here" marker. Spine creates flow; map preserves topological reassurance.

A *modular card deck composed at render time* has atomic cards declared with full metadata; a composer picks a sequence per format. Most reusable, highest authoring overhead.

The recommended hybrid is *spine + ambient canvas + atomic cards*: spine prevents shopping-list collapse, canvas preserves topological visibility, and atomic-card authoring enables cross-audience and cross-duration composition without rewrite.

---

## 3. Pipeline architecture

The architecture cleanly separates three stages:

```
[Card library]  →  [Composer]  →  [Renderer]  →  [Medium]
                       ↑
                   [Config]
```

The card library is authored once. The composer takes a config (format, audience, thesis) and produces a composition. The renderer maps a composition to a medium. Adaptation happens by changing the config or the renderer, never by rewriting cards.

### 3.1 Card schema

Each card encodes one claim or one move. Cards are stored as structured records (YAML, JSON, or a database). A reasonable schema:

```yaml
id: frame_problem
role: spine                      # spine | branch | example | hook | foil
thesis_role: load_bearing        # load_bearing | enriching
prerequisites: [bounded_rationality]
time_cost:
  minimal: 60                    # seconds (compressed renderings)
  standard: 180                  # seconds (default renderings)
  deep: 600                      # seconds (expanded renderings)
faces:
  layman: |
    Before you can decide what is worth thinking about, you have already
    done some thinking...
  cs: |
    The frame problem in McCarthy's sense concerns the cost of explicitly
    representing what does not change...
  statistician: |
    The relevance of a feature is conditional on a model class that is
    itself a choice...
  mathematician: |
    Given a knowledge base K and an action a, the frame axioms specify
    which fluents persist...
illustrations:
  - id: triage_frame_breakdown
    type: scenario
formal_appendix: |
  Optional proofs, derivations, or technical detail.
visual_assets:
  - diagram_id: relevance_explosion
notes_to_self: |
  Load-bearing card for the indeterminacy thread.
```

*Required fields:* `id`, `role`, `thesis_role`, `prerequisites`, `time_cost`, `faces` (at least one).

*Faces.* A face is a complete rendering of the same claim for a given audience. Faces are not summaries of one another — they are independent renderings written from inside the relevant idiom. Authoring guideline: write the hardest face first, then back-translate.

*Roles.* `spine` cards carry the thesis arc and must appear in any rendering. `branch` cards are excursions that open from a spine node and return. `example` cards are concrete instantiations referenced from many spine and branch cards. `hook` cards open the artifact and motivate. `foil` cards exist to be argued against.

*Thesis role.* `load_bearing` means the thesis collapses without this card. `enriching` means the card adds depth, color, or audience-specific traction but is not necessary.

*What the schema deliberately omits.* The schema does not include persuasive metadata (assumed priors, target updates, anticipated resistance) or affective metadata (rhythm cues, intensity markers). The reasoning is given in §1.4: per-card encoding of audience belief state and emotional arc produces partial metadata that degrades authoring discipline more than it informs composition. Audience-side concerns are handled at the global artifact level (§1.4) and via review pass (§4).

### 3.2 Composer

*Inputs:* the card library and a config specifying format (time budget), audience (which faces to use), and thesis (the destination card).

*Outputs:* an ordered sequence of cards, each tagged with a chosen face, plus the set of branches available off the trunk but not on it.

*Rules the composer enforces:*

- Every load-bearing card appears.
- Prerequisites are respected (topological order on the prerequisites DAG).
- Total time cost (with chosen depth) stays within budget.
- The sequence ends at the thesis card.
- Faces are consistent across the composition unless mixing is intentional and signposted.

The composer does *not* enforce belief-trajectory or rhythm constraints. These are checked manually in the review pass (§4 step 9).

Composition can be hand-curated or rule-based. Start hand-curated; mechanize only when the same compositions are being re-derived repeatedly.

### 3.3 Renderer

*Inputs:* a composition. *Outputs:* an artifact in a specific medium. Reasonable rendering targets include spine + ambient canvas web app, keyboard-driven DFS talk, linear slide deck, document/handout, interactive explainer.

Swapping the renderer never costs content rewriting. The same composition feeds any renderer; the same card library feeds any composition.

---

## 4. Instantiation workflow

The recommended sequence for a new artifact:

**1. Lock the thesis sentence.** Write the single sentence every audience walks away with. Pin it where you have to look at it. If you cannot write it, do not start authoring.

**2. Sketch the spine in the abstract.** Five to seven conceptual beats from setup to thesis. Each beat will become one spine card. Write the beats as one-line claims, not as content. Verify that the last beat is the thesis sentence.

**3. Draft friction map and belief trajectory.** *(New in v2.)* For each audience profile you will address, write one short paragraph: walk-in beliefs, resistance points, defense mechanisms, counter-moves. Then write one short paragraph specifying where the audience should be on each load-bearing claim at key points (opening, midpoints, close). These two notes are consulted during card authoring and during the review pass before rendering. Do not formalize them into per-card metadata — keeping them as free prose is part of the design.

**4. Author spine cards, hardest face first.** For each beat, write the mathematician (or otherwise most precise) face first, because precision disambiguates the layman version. Add audience faces in increasing accessibility order. Mark each card's role and prerequisites. While drafting, consult the friction map: at resistance points, choose framings that address the anticipated defense rather than ignoring it.

**5. Author examples and hooks as their own cards.** Examples are first-class branches, not decorations. The recurring concrete example (if you choose to refract one) gets its own dedicated card with multiple faces.

**6. Author branch cards selectively.** Only branches you actually plan to open. Authoring branches you'll never use is the single biggest authoring drain.

**7. Build the minimum renderer.** A YAML/JSON card index plus a Markdown-driven static-site template is sufficient for the first two renderings.

**8. Compose and render once.** Generate the first composition for the first target format and audience; emit the artifact.

**9. Review pass for resistance and rhythm.** *(New in v2.)* Before showing the artifact to anyone, read the composition once with two questions, in this order. First: where will each audience profile resist, and is there something at that point that addresses the resistance? Cross-check against the belief trajectory — is the audience where it should be at each waypoint? Second: where does the artifact breathe, surprise, slow, land? Annotate the composition with rhythm cues if helpful — a marker for "pause here," "do not rush this," "the surprise lands at this card." This pass costs five to ten minutes and prevents most of the failures the audience-side layers are meant to prevent. If the review pass surfaces problems, the fix is usually a card reordering or a face change, occasionally a new card; almost never a schema change.

**10. Render again and revise.** Most of what is worth knowing about your engine is invisible until two real compositions have flowed through it. Things that seem general after one rendering are often incidental scaffolding. After the second rendering, also revise the friction map and belief trajectory if the second audience surfaced surprises the first did not.

---

## 5. Worked example: automation, bounded rationality, Bayesian decision theory

This section instantiates the architecture for a specific topic: the automation of information processing, the indeterminacy of relevance and the frame problem, the limits of bounded rationality, Bayesian decision theory and maximum subjective utility, and risks in decision automation and agency.

### 5.1 Candidate thesis sentences

Different theses suggest different spines. Three candidates:

> *Automated decision systems inherit foundational indeterminacies — about what is relevant, what counts as success, what is worth optimizing — that no formalism dissolves; Bayesian decision theory crystallizes the dream of dissolving them and reveals exactly why it fails.*

> *Decision automation is not a substitute for normative judgment but a relocation of it: every layer of the pipeline imports value choices that the formalism makes invisible.*

> *The frame problem and bounded rationality together imply that maximum-subjective-utility is not a recipe but a regulative ideal; the design question is what to do given that the ideal is unreachable.*

The first emphasizes Bayesian theory as a foil; the second emphasizes the politics of automation; the third emphasizes pragmatic design under irreducible limits. Pick one and pin it before authoring.

### 5.2 Candidate spine (assuming the first thesis)

1. **Hook.** A concrete automation scenario where things go subtly wrong (e.g., medical triage with shifting case mix; the recurring example for refraction).
2. **Information processing as automation.** The project of mechanizing inference and decision; the scope of the dream.
3. **The frame problem.** Relevance is not given by the world; it is fixed by a frame, which is itself an underdetermined choice.
4. **Bounded rationality.** Even setting frame aside, optimization is bounded by computation, time, and information; "rational" is a contextual standard.
5. **Bayesian decision theory and maximum subjective utility.** The elegant unification — coherent priors, expected utility, dominance — and why it appears to dissolve the previous problems.
6. **Why the unification fails.** Prior selection is a frame choice; utility specification is a value choice; coherence under bounded computation is unattainable; the residue is irreducible.
7. **Implications.** Agency under irreducibility; automation as relocation rather than dissolution; the design question. Lands on the thesis.

### 5.3 Card sketches

Roles for the seven spine beats: card 1 is `spine` and also serves as `hook`; cards 3, 5, 6 are `load_bearing`; cards 2 and 4 are `enriching` for short formats but `load_bearing` for technical audiences; card 7 is the thesis card.

Non-exhaustive list of branch and example cards: triage example (`example`, referenced from cards 1, 3, 4, 6); McCarthy's frame problem (`branch` off card 3); Simon's bounded rationality (`branch` off card 4); Dutch book argument (`branch` off card 5); Goodhart's law (`branch` off card 6); Cromwell's rule (`branch` off card 6); Knightian uncertainty (`branch` off card 6); mechanism design as automation foil (`foil`, referenced from card 7).

### 5.4 What to render first

The same card library serves all four formats below. No content is rewritten between formats; only the composer's config changes.

*30-minute mixed-audience talk.* Spine (cards 1–7) at standard depth with layman faces, plus the triage example refracted at each spine beat. No branches opened by default.

*5-minute pitch.* Cards 1, 3, 6, 7 at minimal depth. Drop the example refraction; keep the example only as the hook.

*90-minute technical talk.* Full spine at deep depth with mathematician faces, plus the McCarthy, Simon, Dutch book, and Goodhart branches.

*Course.* Full spine at deep depth, all branches open, all audience faces available as supplementary reading, with formal appendices.

### 5.5 Friction map (worked example)

Sketches for each audience profile, assuming the first thesis.

*Mathematician.* Walks in believing Bayesian decision theory is a clean formalism that, in principle, solves decision problems; remaining issues are practical (computation, elicitation), not foundational. Identity stake in formal rigor. Resistance peaks at card 6, specifically at the move from "priors are a choice" to "rationality is therefore contextual." Defense mechanism: re-frame foundational critique as practical engineering issue ("better algorithms will close the gap"). Counter-move: card 6 should not appeal to practical limits but to the structural point that prior selection imports values; the triage refraction at card 6 carries this load.

*Statistician.* Walks in with priors closer to the destination — comfortable with the idea that modeling involves choices, accustomed to robustness and elicitation methods. Lower overall resistance, but specific resistance to "the residue is irreducible" — they may argue that elicitation, sensitivity analysis, and robustness can bound the residue arbitrarily tightly. Defense mechanism: technical reframing of normative critique. Counter-move: distinguish bounded uncertainty (their move) from indeterminate framing (the actual claim) — these are different objects.

*Computer scientist.* Walks in with engineering optimism — frame problem feels like "old AI," bounded rationality feels like a curiosity, current ML feels like a different paradigm. Identity stake in current ML investment. Resistance peaks at card 3 (treated as obsolete) and card 7 (treated as not applicable to ML practice). Defense mechanism: dismissal as philosophical, not technical. Counter-move: lead with the triage hook at card 1, then return to it explicitly at card 3 in modern ML idiom (training distribution as frame, distribution shift as frame breakdown, reward specification as utility specification).

*Layperson.* Walks in with mixed priors — AI is mysteriously powerful, mysteriously dangerous, or both. Identity stake is feeling competent rather than lost. Resistance is mostly attentional rather than ideological — the concern is checkout, not pushback. Defense mechanism: "this is too technical for me." Counter-move: keep the triage example concrete throughout, defer formalisms to optional branches, ensure each spine beat lands as one sentence the layperson can paraphrase.

### 5.6 Belief trajectory (worked example)

Targets for the load-bearing claims, calibrated to a 30-minute talk.

By the close of the hook (minute 2): audience accepts that the triage example is interesting and that something is going wrong in it that they cannot immediately diagnose.

By the end of card 4 (minute 12): audience accepts that even with unbounded reasoning, relevance is not given by the world — it is fixed by a frame, and the frame is a choice. Mathematicians and CS may still treat this as a practical problem; that is fine for now.

By the end of card 5 (minute 17): audience has seen the elegance of Bayesian decision theory and feels the temptation to treat it as the answer. The talk has not yet contested it. This is deliberate — the foil must be presented at full strength.

By the end of card 6 (minute 25): audience has accepted that prior selection is a frame choice, that utility specification is a value choice, and that the unification does not eliminate the indeterminacies — it relocates them. Resistance is highest here. The triage refraction at card 6 is the heaviest evidence load.

By the close (minute 30): audience commits to the thesis — automation as relocation, not dissolution, of normative judgment — and accepts the implication for design.

### 5.7 The reflexive case

The topic creates a particular trap. The talk argues that bounded-Bayesian reasoning is a regulative ideal under irreducible limits; the talk's design uses bounded-Bayesian reasoning (priors plus likelihood plus sequential evidence) to plan how to convince the audience. This can be played as a feature (the talk performs what it argues; the design instantiates the thesis) or as a trap (the audience watches the cleverness of the reflexivity instead of receiving the argument).

Choose deliberately. A small explicit acknowledgment near the close — *"what we just did was Bayesian persuasion under bounded conditions, which is the thesis"* — can land powerfully with self-aware audiences and condescend to others. Decide per audience; the friction map should record which audiences want the reflexive close and which do not. The mathematician audience tends to enjoy it; the layperson audience tends not to need it.

---

## 6. Authoring conventions

A short list of conventions that pay off in practice.

*One claim per card.* If a card has two claims, split it. The composer cannot move the half you want without dragging the half you don't.

*Prerequisites are real, not aspirational.* If a card uses a concept, the card defining that concept is a prerequisite.

*Faces are independent renderings, not translations.* The mathematician face uses formal idiom; the layman face uses concrete imagery. Translating one into the other usually produces both poorly. Write each from inside its idiom.

*Examples are first-class.* An example referenced from three spine cards is one card with three references, not three half-examples scattered across the spine cards.

*Mark the load-bearing cards explicitly.* The composer's first job is to ensure these appear; without explicit marking, this enforcement cannot happen.

*Resist over-authoring on the content side.* Branches you will never open, faces for audiences you will never address, formal appendices nobody will read — these drain authoring time without serving any rendering.

*Refactor toward atomicity, not coverage.* When a card grows long, the impulse is to add detail. Resist; split. Atomicity is what makes the engine work.

*Resist over-formalizing the audience-side layers.* (New in v2.) The temptation to encode resistance and rhythm into per-card metadata is strong, especially after a rendering goes wrong in a way you can pinpoint. The remedy for missed resistance is a better friction map and a more careful review pass, not more schema fields. The same goes for affect: review-pass annotations, not authored encoding. The audience-side layers are deliberately left underspecified; the underspecification is what protects authoring discipline.

*Update the friction map after each rendering.* (New in v2.) When a rendering goes well or badly, the lesson lives in the friction map, not in the cards. New resistance points discovered in the room go into the relevant audience paragraph; counter-moves that worked go alongside them. The friction map is the durable artifact of accumulated audience experience.

---

## Appendix: Minimum implementation

A workable minimum implementation requires only:

- A directory of card files, one YAML or Markdown-with-frontmatter file per card.
- A small composer script that reads the card directory plus a config file and emits an ordered list of card IDs with chosen faces.
- A renderer per target medium (a static-site generator template, a slides script, etc.) that reads the composition and emits the artifact.
- *Two short prose documents* (new in v2): a friction map and a belief trajectory, each one to two pages, kept alongside the card library and updated as renderings accumulate experience.

Total code footprint: a few hundred lines per renderer. Total prose footprint for the audience-side layers: roughly two pages. The architectural payoff is not in the engine; it is in the discipline the engine imposes on authoring, plus the audience-side awareness the friction map and belief trajectory impose on framing.

---

## Appendix: Intellectual lineage and positioning

A high-level orientation: which traditions this spec leans on, which it overlaps with without citing, and which it deliberately departs from. This is not a literature review — the goal is to surface the spec's commitments by showing where they came from and where they sit relative to other approaches. Knowing where the architecture sits is part of using it well.

### Lineages it leans on, mostly tacitly

The atomic-card-plus-recomposition idea descends from the *Zettelkasten* tradition (Niklas Luhmann), which already worked out that knowledge artifacts are best built from atomic units with explicit links, composed at use-time rather than authored as monoliths. The literate-programming tradition (Knuth) and the modular-document movement (DITA in technical writing) have the same shape: small reusable units, metadata-driven composition, multiple outputs. The audience-faces idea sits inside the broader *audience analysis* tradition in rhetoric and technical communication. The thesis-first principle echoes the *Minto Pyramid Principle* favored in management consulting and, at a more rarefied level, mathematical exposition's "state the theorem first" convention. The single-load-bearing-thesis discipline is also what some commentators have called the "argument-driven" model of academic writing, against the "report-driven" model.

### Overlaps on narrative

The thesis-as-destination, the load-bearing-spine, the friction-and-resistance framing — these are all classical *rhetoric* in modern dress. The five canons (invention, arrangement, style, memory, delivery) map roughly onto topology, narrative, faces, medium, and performance. The friction map is a folk version of *stasis theory* (where the disagreement actually lives). The reflexive case section is, broadly, what Aristotle called *ethos* and what contemporary work calls *epistemic positioning* — the speaker's relation to their own argument is itself part of the argument. The dramaturgy concern (affective rhythm, breath, surprise) sits inside the storytelling tradition that runs from Aristotle's *Poetics* through screenwriting craft (McKee, Field) through the talk-design literature popularized by TED-style coaches (Duarte, Anderson) — all of whom would recognize the spine-and-tension structure.

### Overlaps on persuasion

The persuasive-trajectory framing is essentially Bayesian rhetoric — a strain that runs from signaling theory and Bayesian epistemology into recent formal work on Bayesian persuasion (Kamenica and Gentzkow). The psychological deviations from the idealization are familiar territory: dual-process theory, motivated reasoning (Kunda), identity-protective cognition (Kahan), the elaboration likelihood model (Petty and Cacioppo). The friction-map move is a lightweight version of what political communication and behavioral-change practitioners call *audience segmentation* plus *anticipated counter-argumentation*.

### Overlaps on pedagogy

The multi-audience-faces design has cousins in *Universal Design for Learning* (multiple representations of the same content) and in the differentiated-instruction tradition. The prerequisites DAG and the careful sequencing of cognitive load echo *cognitive load theory* (Sweller) and the broader instructional-design tradition (Merrill, Gagné). The example-refraction pattern — one scenario re-told through multiple lenses — is essentially Bruner's *spiral curriculum* compressed into a single artifact. The "explain at multiple depths" intuition has been popularized recently as the "five levels of explanation" format, which is folk-pedagogy but not nothing.

### Lineages it sidles up to but does not commit to

Constructivist pedagogy (Papert, Vygotsky's zone of proximal development) would push harder than the spec does on the audience constructing rather than receiving — the spec is structurally closer to a transmission model dressed in adaptive clothing. Discovery learning and inquiry-based approaches would replace the spine with a problem and let the structure emerge; the spec instead front-loads the spine and lets only branches and faces vary. The dialogic tradition (Bakhtin, recent work on classroom discourse) would be skeptical of a single-thesis-sentence discipline as too monologic. The spec is upfront-architectural in a way these traditions are not, and a reader from those lineages would correctly identify that as a commitment rather than a neutral choice.

### Where it deliberately departs

Three places. First, most talk-design advice in the popular register (TED-coach literature, "how to give a great talk" books) emphasizes performance and storytelling over architecture; the spec inverts that by making architecture primary and treating performance as a review-pass concern. This is a deliberate choice for content where the conceptual structure is the harder problem; it would be the wrong inversion for a memoir talk or a fundraising pitch. Second, most academic exposition guidance assumes a single-format, single-audience artifact; the spec's whole point is multi-audience and multi-duration reuse. Third, most rhetoric and persuasion literature treats the audience-side concerns as central to design from the start; the spec deliberately sidelines them into a lightweight global-prose layer, on the grounds that elevating them to the schema level produces over-engineering. That is a defensible but contestable stance.

### Where it is probably under-equipped

The spec is thin on what classical pedagogy calls *assessment* — how you find out whether the audience actually moved along the belief trajectory you designed. A friction map updated post-rendering is a folk version of formative assessment, but a more developed treatment would specify probes, signals, and revision protocols. It is also thin on what learning sciences call *retrieval* and *spacing* — the spec is artifact-centric, not learning-centric, and would need extension to handle multi-session courses where the audience-side concern is consolidation rather than first-pass conviction. A v3 that took those seriously would borrow more from instructional design and less from rhetoric.

### Honest summary

The spec is closer in spirit to *modular technical communication* (DITA, single-source publishing) and *Bayesian rhetoric* than to either classical instructional design or popular talk-design literature. It treats pedagogy as a structured-content problem with audience-aware composition, rather than as a performance problem with content support. That framing has real strengths — multi-format reuse, explicit thesis discipline, audience-side awareness without over-engineering — and real blind spots in the directions classical pedagogy and dialogic traditions would point out. A user fluent in any of the lineages above will find specific points to argue with; that is healthy and the spec is better for being argued with.

### Standing warnings

Bookkeeping of caveats raised against this appendix and worth revisiting: (1) the spec assumes a transmission model and is under-equipped for dialogic settings where audience contribution rather than reception is the unit of pedagogy; (2) the single-thesis discipline can flatten genuinely plural content where the honest treatment is irresolution among voices in tension; (3) `time_cost` does not capture cognitive-load stacking — the review pass should add a check for stretches of three or more consecutive heavy-abstraction cards; (4) this appendix is itself an LLM-generated literature tour and is best treated as a starting map rather than a finished orientation, with at least one named tradition (constructivist pedagogy, threshold concepts, or French *didactique*) read into directly rather than via summary.

---

## Quick-reference checklist

Before authoring:

- [ ] Single thesis sentence written and pinned.
- [ ] Spine sketched (5–7 beats), last beat = thesis.
- [ ] Load-bearing beats marked.
- [ ] Recurring example chosen (or explicit decision not to refract).
- [ ] Friction map drafted for each audience profile. *(v2.)*
- [ ] Belief trajectory sketched for load-bearing claims. *(v2.)*

During authoring:

- [ ] One claim per card.
- [ ] Prerequisites declared accurately.
- [ ] Hardest face written first.
- [ ] Examples authored as their own cards.
- [ ] Friction map consulted at resistance-prone cards. *(v2.)*

Before rendering:

- [ ] Config specifies format, audience, thesis.
- [ ] Composition includes every load-bearing card.
- [ ] Total time cost within budget.
- [ ] Sequence ends at thesis.

After composition, before delivery:

- [ ] Review pass: resistance points addressed, belief trajectory met. *(v2.)*
- [ ] Review pass: rhythm annotated, breath and surprise placed. *(v2.)*

After delivery:

- [ ] Notes taken on what felt structural vs incidental.
- [ ] Friction map updated with new resistance points or successful counter-moves. *(v2.)*
- [ ] Second rendering attempted before generalizing the engine.
