---
id: training_emergence
role: spine
thesis_role: load_bearing
prerequisites: [training_objective]
time_cost:
  short: 30
  standard: 90
faces:
  general: |
    Here is the part that surprises people.

    Nobody designed the embedding clusters where animals end up
    near each other.
    Nobody designed the attention head that disambiguates "bank."
    Nobody designed the MLP neurons that fire on Eiffel-Tower-
    shaped contexts.

    Those structures *emerged*. They were not built; they were
    found. The only thing that was specified was: "predict the
    next token, well, on a lot of text."

    The architecture is expressive enough that *if* there are
    statistical regularities in the data that help predict the
    next token, gradient descent will tend to find them. And in
    natural-language text, there are: grammar, word meaning,
    syntactic structure, factual associations, coherence, idiom,
    register, even a notion of arithmetic.

    All of those end up encoded — somewhere, in some
    distributed-and-not-quite-readable way — in the parameters
    of the trained model.

    This is what people mean when they say LLMs are "trained,
    not programmed." Nothing about the model's behaviour was
    programmed. All of it was learned, from one objective.
  technical: |
    "Emergence" is the empirical observation that, given enough
    parameters, enough data, and enough compute, gradient descent
    on next-token cross-entropy reliably produces parameter
    configurations that encode multiple levels of linguistic and
    factual structure — *without those structures being part of
    the optimisation objective.*

    Concrete observables:

    - Linear probes on intermediate activations recover
      grammatical features (part of speech, tense, number).
    - Attention head specialisation: heads can be identified that
      consistently track coreference, syntactic dependency, or
      named-entity proximity.
    - MLP neuron sparsity: per token, only ~3-5% of MLP
      intermediate units fire strongly; identified neurons can
      sometimes be associated with specific concepts (e.g.
      "code-comment-style," "named-landmark").
    - Probing for factual knowledge ("the capital of France is")
      shows reliable retrieval up to model-size limits.

    None of these properties was directly optimised for. They
    are downstream consequences of next-token prediction at
    scale.

    Caveat: "emergence" sometimes refers to the more specific
    claim that capabilities appear *suddenly* with scale (as
    opposed to gradually). That stronger claim is contested
    methodologically (Schaeffer et al. 2023). The weaker claim
    used here — that next-token-relevant structure ends up
    encoded — is robust.
notes_to_self: |
  The high-resistance card for the technical audience. The
  general face emphasises "found, not built" with three
  concrete examples; the technical face addresses the
  emergence-is-hand-wavy concern by re-framing emergence as
  empirical regularity backed by interpretability findings, with
  a citation gesture (Schaeffer et al.) on the stronger claim.

  This is also the W5 belief-trajectory waypoint. If the
  audience accepts that the structures were found and not built,
  they accept the second movement of the thesis.
---

# training_emergence

Beat 5 closer. The emergence claim — what training produces, why
the produced structure was not designed, why this matters for the
thesis. The highest-resistance card for technical audiences.
