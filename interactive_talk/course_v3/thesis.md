# Thesis

The single sentence every audience walks away with. Pinned before
authoring (per spec §4 step 1).

## Locked thesis

> **A modern LLM is a probability calculator that emits one token at
> a time. Everything that makes it feel like a thinking, conversing
> entity — fluency, context, factual recall, dialogue — is the joint
> work of a stack of mechanisms (tokenisation, embedding, attention,
> transformer block) trained at internet scale, then nudged by a
> thin alignment layer at the very end.**

The thesis card in the spine is `alignment_thesis`. Every load-bearing
card is in service of one of three movements packed in the thesis:

1. **The probability-calculator core** — `next_token_predictor`,
   `autoregression`, `architecture_pipeline`.
2. **The mechanism stack at scale** — `tokenisation`, `embedding`,
   `attention`, `transformer_block`, `training_objective`,
   `emergence`.
3. **The alignment layer** — `alignment_gap`, `alignment_thesis`.

## Why this thesis (and not the alternates)

Three theses were considered:

- **Demystification** ("once you trace the pipeline, the magic
  resolves"). Strong for audiences arriving with high mystification;
  weaker for audiences arriving with engineering optimism.
- **Relocation** ("understanding is statistical fluency, dialogue is
  alignment, the architecture makes both tractable"). Tighter
  philosophically; harder to land in 30 minutes for a mixed audience.
- **Mechanical-with-emergence-and-alignment** *(chosen)*. Names the
  three movements explicitly, ends on the alignment punchline,
  matches the existing belief trajectory of "explain how it works
  → close on the chatbot reveal."

The chosen thesis sentence is deliberately longer than a tweet —
three clauses, each load-bearing. That length is a feature: the
sentence packages the entire course into one re-readable unit.

## A note on the medium

The talk is being delivered as a slide deck. The *content* of the
slides is the talk; the slide medium is downstream of (not co-designed
with) the narrative. If the same composition were rendered as a
linear handout or a podcast script, the thesis sentence and the spine
arc would land identically — that is the point of the
authoring-composition-rendering separation in spec §3.
