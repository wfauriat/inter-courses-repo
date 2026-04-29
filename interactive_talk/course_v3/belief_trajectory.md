# Belief trajectory

Where the audience should be at each waypoint. Calibrated to the
30-minute composition; the 5-minute pitch compresses the same arc.

Six waypoints, one per spine beat. Each waypoint names what the
audience should believe by the time the next beat opens.

---

## W0 — opening (minute 0)

Audience walks in with priors from `friction_map.md`. Claim count: 0.

---

## W1 — after the hook (minute ~3)

After: `hook`, `chatbot_interactions`.

**Both audiences accept**: chatbots produce varied, surprising,
often-correct text. There is something worth investigating about how.

**Technical adds**: this is not going to be review. The hook is
concrete enough to refuse the "intro to ML" dismissal.

---

## W2 — after the predictor claim (minute ~7)

After: `next_token_predictor`, `autoregression`, `ntp_summary`.

**General accepts**: LLMs do exactly one thing — sequentially predict
words. No structure, no plan, no understanding *yet visible*. The
"and yet they answer questions" tension is preserved.

**Technical accepts**: an LLM is p(x_{n+1} | x_{<=n}) sampled
auto-regressively over a finite vocabulary. The rest of the talk is
about this conditional distribution.

---

## W3 — after the mechanism stack (minute ~17)

After: `mechanisms_overview`, `tokenisation`, `embedding`,
`embedding_geometry`, `attention`, `attention_disambig` example,
`transformer_block`, `transformer_stack_summary`.

**General accepts**: the four mechanisms (tokens, vectors, attention,
stack) are *enough* — given enough of them, in the right shape — to
turn next-token prediction into context-aware fluent text. The
audience need not be able to explain any of them in detail; they need
to feel "I have seen the gears, and they are gears."

**Technical accepts**: standard decoder-only transformer architecture
with multi-head attention + MLP residual blocks. They have not
learned anything new at the architecture level (most know it); they
*have* learned a useful articulation of the responsibility split:
attention mixes across positions, MLP mixes across features.

This is the heaviest waypoint by node count and cognitive load.
Cognitive-load stacking risk (spec appendix item 3); mitigation is
the disambiguation example, which is concrete.

---

## W4 — after architecture-as-machine (minute ~21)

After: `architecture_pipeline`, `architecture_scale`.

**Both audiences accept**: the whole machine is now visible end-to-
end. Tokens in, vector flow through stacked blocks, distribution
out. The bulk is parameters; parameters are what training fits.

This is the bridge waypoint. If the audience does not feel that
parameters are central by minute 21, training cannot land.

---

## W5 — after the training story (minute ~26)

After: `training_objective`, `training_emergence`.

**General accepts**: the parameters were not designed; they were
fitted. The mechanisms (clusters, attention patterns) were not
designed; they emerged because they helped prediction. *No one chose
that nouns cluster; the model found it.*

**Technical accepts**: gradient descent on cross-entropy over
internet-scale data, run at scale, produces parameter
configurations that empirically encode multiple levels of linguistic
and factual structure. "Emergence" names this empirical regularity;
it is not a philosophical claim.

This is the highest-resistance waypoint for the technical audience
(engineering-optimism: "we designed the training procedure, that
counts as design"). The technical face addresses this directly.

---

## W6 — thesis (minute 30)

After: `alignment_gap`, `alignment_thesis`.

**Both audiences accept**: the deployed chatbot is not the base
predictor. A thin alignment layer (supervised fine-tuning + RLHF)
converts "continues the prompt" into "answers the prompt." The
chatbot people interact with is the base predictor *plus* this
alignment layer.

The thesis sentence — *probability calculator + mechanism stack at
scale + alignment layer = deployed chatbot* — is the single take-
home one-liner.

The reflexive close (optional, technical face only): the audience has
just watched a probability calculator explain probability
calculators. Land if engagement supports it; skip if cold.

---

## Compression rules (5-min pitch)

The pitch hits W1, W2, W4, W6 — skipping W3 (mechanism dive) and
W5 (training/emergence). The mechanism stack is named in one breath
("there are four ideas inside the predictor"); training is named in
one breath ("the parameters were trained on internet-scale data").
The thesis is accepted on authority. The pitch is a teaser, not the
talk.

## Expansion rules (60+ min technical)

W3 doubles in dwell time: every mechanism gets its technical face;
the attention card opens its QKV branch; the transformer block opens
its zoom branch. W5 expands: the autodiff branch opens, the scaling
laws gesture becomes a ten-second aside.
