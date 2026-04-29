---
id: attention
role: spine
thesis_role: load_bearing
prerequisites: [embedding]
time_cost:
  short: 30
  standard: 90
faces:
  general: |
    Embedding gets us a static map: each token has a fixed
    position. But meaning isn't static. The word "bank" in "the
    bank of the river" is a different thing from "the bank gave
    me a loan." The token is the same; the meaning depends on
    the neighbours.

    **Attention** is the mechanism that lets a token's
    representation be modified by its neighbours, *during the
    forward pass.*

    Concretely: for every token in the sequence, the model
    computes how much each *other* token in the sequence is worth
    paying attention to. Those weights are then used to mix the
    other tokens' information into the current token's
    representation.

    A token's vector enters the attention layer as one thing and
    leaves as something subtly different — informed by which
    other tokens it decided to look at, and how strongly.

    Attention is the central architectural innovation of modern
    LLMs. It is the reason transformers replaced the previous
    generation of architectures. It is the reason the talk
    spends time on it.
  technical: |
    Attention in its scaled-dot-product form computes
    $\text{softmax}(QK^\top / \sqrt{d_h})\, V$ where $Q$, $K$,
    $V$ are linear projections of the input vectors. Each output
    position is a convex combination of the input value vectors,
    with weights given by the softmax-normalised query-key
    compatibilities.

    Multi-head attention runs $h$ attention computations in
    parallel on $h$ orthogonal sub-spaces of the embedding
    (with $d_h = d/h$), then concatenates and projects back.
    Each head learns to attend along a different axis —
    syntactic position, coreference, named-entity proximity,
    semantic similarity — though the per-head specialisation is
    empirical, not mandated.

    Causal masking sets the upper-triangular entries of
    $QK^\top$ to $-\infty$ before softmax, so each position $i$
    attends only to positions $j \le i$.
notes_to_self: |
  Mechanism 3 of 4. The single most load-bearing card in beat 3 —
  if the audience leaves attention without a working intuition,
  the rest of the talk lands as "and there's some other
  machinery." If they leave with attention as "tokens read each
  other," the rest is bookkeeping.

  General face deliberately delays the formula. The bank example
  is a separate card (attention_disambig) immediately after this
  one, as the worked refraction.

  The "central architectural innovation... reason transformers
  replaced..." is a small editorial — it gives the audience
  permission to take attention seriously without making them
  parse the formula.
---

# attention

Mechanism 3 of 4. The token-reads-other-tokens mechanism. The
load-bearing claim: a token's vector after attention is not the
same as before; it has been informed by its neighbours.
