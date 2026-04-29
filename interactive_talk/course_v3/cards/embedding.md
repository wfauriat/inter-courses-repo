---
id: embedding
role: spine
thesis_role: load_bearing
prerequisites: [tokenisation]
time_cost:
  short: 30
  standard: 90
faces:
  general: |
    Tokens are integers. Integers are not useful — you cannot do
    "this integer is somewhat similar to that integer" with raw
    indices.

    So the next step gives every token a position in a high-
    dimensional space. Imagine a 768-dimensional graph, with one
    point per token in the vocabulary. Token "cat" is one point.
    Token "dog" is another. Token "thermodynamics" is another.

    The position is a list of 768 numbers — the *embedding* of
    that token.

    Two tokens are *similar* if their points are close together.
    Two tokens are *related by some pattern* if the line between
    them points in a particular direction.

    This is the trick that makes everything else work. The model
    cannot operate on integers, but it can do arithmetic on
    high-dimensional points. So we lift integers into points, and
    the integers' relationships become geometry.
  technical: |
    The embedding layer is a learned lookup table
    $W_E \in \mathbb{R}^{|V| \times d}$, with $d = 768$ for
    GPT-2 small (and larger for bigger models). Token id $i$
    indexes row $i$, yielding a $d$-dimensional vector.

    Embedding lifts the model from a function over $V^*$
    (discrete) to a function over $(\mathbb{R}^d)^*$
    (continuous). All downstream operations — attention, MLP,
    unembedding — are continuous functions on
    $\mathbb{R}^d$-valued sequences.

    Positional information is added separately (positional
    embedding, rotary, etc.) so the model can distinguish "cat
    chases dog" from "dog chases cat."

    The geometry of $W_E$ is not designed; it is what gradient
    descent on the next-token prediction loss picks out. The
    next card discusses what that geometry looks like.
notes_to_self: |
  The discrete-to-continuous hinge. From here on, everything
  operates on vectors. This is the conceptual pivot of the
  mechanism beat — without it, the model is just bookkeeping;
  with it, the model can do real arithmetic on meaning.

  General face uses the "graph with one point per token" framing.
  Technical face introduces W_E and notes that geometry is
  trained, not designed (a foreshadowing of training_emergence).

  Note: I am not introducing positional embedding as a separate
  card. Position info is mentioned in passing in the technical
  face. The general face glosses over it; this is acceptable
  because the audience does not need positional embedding to
  understand the rest. If a future audience asks, the technical
  face has the gesture.
---

# embedding

Mechanism 2 of 4. The discrete-to-continuous lift. Tokens become
vectors; geometry becomes available; downstream cards can do
arithmetic on meaning.
