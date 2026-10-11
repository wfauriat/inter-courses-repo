# Friction map

Per audience: walk-in priors, where they will resist, what protects
the resistance, and the counter-move authored into the spine.
A living artifact — update with new resistance points after each
rendering.

This build authors **two faces** rather than the spec example's four.
The reasoning: for the "what is an LLM" topic, the cs and math
audiences cluster tightly into "people who want the precise version,"
and the layman / non-technical audiences cluster into "people who
want the accessible version." A binary `general` / `technical`
distinction captures the working partition without the authoring
drain of four faces. If a future rendering reveals divergence between
cs and math priors that the technical face doesn't address, fork a
third face then.

---

## General audience

**Walk-in priors.** Has used a chatbot. Believes — implicitly,
without committing to it — that the chatbot has *some kind* of
understanding. May have heard "it's just statistics" or "it's just
predicting the next word" and accepted those phrases without a model
of what they mean. Often slightly defensive about being out of their
depth on technical material.

**Resistance points (descending order of likelihood).**

1. **"This is too technical for me"** at the first abstract
   mechanism. The mechanism dive begins at tokenisation; if the
   first slide loses them, they will mentally check out for the
   middle 15 minutes and only re-engage at alignment.
2. **Number overload** at architecture/scale. "124M parameters,"
   "trillions of tokens" can feel like raw bigness rather than
   meaningful scale.
3. **Disbelief at emergence** — "the model wasn't told what nouns
   are; it figured them out from prediction alone" can sound like a
   trick.

**Counter-moves authored into the spine.**

- The hook commits to a tone before any abstraction: a chatbot
  conversation the audience recognises, then a one-line "but here is
  what's actually happening underneath." Frames the talk as
  demystification, not lecture.
- Each mechanism card lands as a one-sentence claim followed by a
  one-sentence concrete intuition. No formalism on the general face.
- Numbers come with referents: "124 million parameters — about as
  many tunable knobs as your phone has pixels."
- The emergence claim is anchored in a concrete observable: clusters
  in the embedding space, attention head specialisation patterns.
  These are demonstrations, not assertions.

---

## Technical audience

**Walk-in priors.** Engineering or scientific background.
Familiar with neural networks, possibly with transformers
specifically. Reads formal idiom by default. Suspicious of
hand-waving. Wants the *operative* version: what is and is not
proven, where the empirical findings come from, what the precise
parameterisation looks like.

**Resistance points.**

1. **"This is review"** if the early slides repeat the standard
   transformer story without addition. Counter: the architecture
   slides include parameter-count breakdowns and the
   attention/MLP responsibility split (one mixes positions, the
   other mixes features). Even a transformer-fluent audience
   tends to find the responsibility split useful.
2. **"Emergence is hand-wavy"** at the training/emergence card.
   Counter: the technical face frames emergence as an empirical
   regularity of optimisation under scale, not a philosophical claim.
   The framing is "here is what we observe" not "here is what
   must be."
3. **"Alignment is the boring product layer"** — the technical
   audience may treat post-training as an epilogue. Counter: the
   alignment slide is the *thesis*, not the epilogue. The
   technical face emphasises that the deployed chatbot is a
   measurably different artefact from the base predictor — not a
   soft-skill veneer.
4. **"The reflexive close is too cute"** — sometimes lands, sometimes
   doesn't. Mark optional and decide live.

**Counter-moves authored into the spine.**

- Technical face uses precise notation: p(x_{n+1} | x_{<=n}),
  W_E ∈ R^{|V|×d}, softmax(QK^T/√d_h)·V. Indices, dimensions, and
  parameter counts where they sharpen the claim.
- Architecture and training cards include the scaling-laws gesture
  (Kaplan/Chinchilla shape) without dwelling on it.
- Alignment card includes the SFT + KL-regularised RLHF
  formulation as the formal sketch of "thin layer on top of the
  base predictor."

---

## Cross-audience

**The hook is identical** for both faces — chatbot interaction is
universal lived experience.

**The thesis sentence is identical** for both faces — the audience
walks away with the same one-liner regardless of register.

**The middle differs** — the technical face adds notation; the
general face stays in metaphors. The structure is the same; the
texture differs.

**Update protocol.** After a rendering: note which resistance points
fired and which didn't, which counter-moves landed, what new
resistance you didn't anticipate. Edit this file. The friction map is
the durable record of accumulated audience experience.
