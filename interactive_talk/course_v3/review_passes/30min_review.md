# Review pass — talk_30min_general

Composition: 19 slides, general audience, ~23 min budgeted, ~30 min
delivered with speaker dwell.

Conducted per spec §4 step 9: read once for resistance + belief
trajectory, then once for rhythm.

---

## Resistance check

### General audience

**W1 hook**: `hook` + `chatbot_interactions`. Two slides; the
chatbot examples (shell command, Bayes explainer, Korean
translation) demonstrate range without forcing technical register.
**Mitigation present.**

**Checkout risk at first abstraction**: `mechanisms_overview` is the
fourth slide (after hook + interactions + predictor + autoregression
+ ntp_summary). By this point the audience has bought into "it's a
predictor"; the four-mechanism announcement gives them the agenda.
**Mitigation present.**

**Checkout risk at tokenisation**: `tokenisation` introduces sub-
word tokens; the example "tokenisation -> token / is / ation" is
self-referential and tends to land. **Mitigation present.**

**Checkout risk at embedding/geometry**: `embedding` (lifts to high-
dim space) followed by `embedding_geometry` (clusters + king-queen
direction). The king-queen example is the strongest single anchor
for "geometry encodes meaning." **Mitigation present.**

**Bank disambig**: `attention` + `attention_disambig` is the
strongest single moment in the talk. The audience holds W3 here.
**Mitigation present and strong.**

**Numbers overload at architecture**: `architecture_scale` says
"124M parameters... think of every parameter as a tiny knob." The
metaphor grounds the number. **Mitigation present, observe live.**

**Emergence resistance**: `training_emergence`'s general face leads
with three concrete examples ("nobody designed the clusters /
attention head / MLP neurons"). Earns the claim before stating it.
**Mitigation present.**

**Alignment-as-epilogue risk**: `alignment_gap` names the gap
explicitly with the pancakes example; `alignment_thesis` is framed
as THE thesis card, not an epilogue. **Mitigation present.**

### Technical audience reading the general composition

The technical audience is not the target of this composition. They
will likely:

- Find the cs-friendly autoregression card useful (causal masking,
  no-revision-pass).
- Find the embedding_geometry technical face's caveat about
  approximate directional structure honest.
- Find the alignment_thesis general face's metaphor ("body, limbs,
  upbringing, manners") charming but want the formula. Switch to
  `talk_60min_technical` for that.

## Belief trajectory waypoints

- **W1 hook (~min 2-3)**: hook + chatbot_interactions. ~2 slides.
  **Hits.**
- **W2 NTP (~min 6-7)**: next_token_predictor + autoregression +
  ntp_summary. **Hits.** The autoregression card adds "no plan,
  no revision" which strengthens the claim.
- **W3 mechanism stack (~min 13-17)**: mechanisms_overview +
  tokenisation + embedding + embedding_geometry + attention +
  attention_disambig + transformer_block + transformer_stack_summary.
  8 slides. Heaviest section. **Hits, but watch cognitive load.**
- **W4 architecture (~min 19-21)**: architecture_pipeline +
  architecture_scale. **Hits.**
- **W5 emergence (~min 24-26)**: training_objective +
  training_emergence. Two slides; the emergence story is the
  load-bearer. **Hits.**
- **W6 thesis (~min 29-30)**: alignment_gap + alignment_thesis.
  **Hits.** The thesis sentence on alignment_thesis general face is
  the take-home one-liner.

## Rhythm pass

Annotations for delivery (not authored into cards):

- **Pause after `hook`** — let "this talk takes the calculator
  apart" land.
- **Pause after `chatbot_interactions`** — the closing line "it is
  doing exactly one thing" pivots into the next slide.
- **Pause on the king-queen example** in `embedding_geometry` —
  this is one of the talk's two "wait, really?" moments.
- **Pause after the bank disambig reveal** in `attention_disambig`
  — the second "wait, really?" moment. Watch the room.
- **Slow through `transformer_block`** — abstract; audience is
  several mechanisms deep, may need to recover.
- **Pause after `transformer_stack_summary`** — beat closer, breath
  before architecture beat.
- **Pause after `architecture_scale`** — "tiny knob" metaphor + the
  bridge to training. Don't rush the bridge.
- **Slow through `training_emergence`** — the surprise of the talk.
  Audience may want a beat to process "trained, not programmed."
- **Land at `alignment_thesis`** — final slide. Read the thesis
  sentence aloud. Don't rush. Optionally pause before the
  body-limbs-upbringing-manners metaphor as a coda.

## Action items

- [ ] Live observe whether the W3 section (8 slides, heaviest
      cognitive load) sustains attention. If not, consider trimming
      `embedding_geometry` to a one-paragraph version.
- [ ] Live observe whether `architecture_scale`'s "tiny knob"
      metaphor lands as scale or as condescension.
- [ ] Live observe whether the gap between `alignment_gap` and
      `alignment_thesis` is too compressed (one slide for the gap,
      one for the resolution). May want to expand the gap with a
      second example beyond pancakes if the audience is technical.
- [ ] Update `friction_map.md` after first live rendering.
