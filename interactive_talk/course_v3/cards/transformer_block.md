---
id: transformer_block
role: spine
thesis_role: load_bearing
prerequisites: [attention]
time_cost:
  short: 30
  standard: 60
faces:
  general: |
    Attention is half of the work in each layer. The other half is
    a small neural network — called an **MLP**, multi-layer
    perceptron — that operates on each token *independently*,
    after attention has done its mixing.

    The clean way to think about the two halves:

    - **Attention mixes across positions.** Tokens look at each
      other.
    - **MLP mixes across features.** Each token does some
      arithmetic on its own newly-informed vector, computing
      richer features from the components.

    Together, attention + MLP, with some bookkeeping
    (normalisation, residual connections), form one
    *transformer block*.

    A transformer block reads a sequence of token vectors,
    enriches them with attention, then refines them with the
    MLP, then hands the result to the next layer.
  technical: |
    A transformer block applied to the residual stream:

    $$h' = h + \text{Attn}(\text{LN}(h))$$

    $$h'' = h' + \text{MLP}(\text{LN}(h'))$$

    The MLP is a position-wise two-layer feed-forward network
    with a non-linearity (typically GELU):
    $\text{MLP}(x) = \text{GELU}(x W_{\text{in}} + b_{\text{in}})\, W_{\text{out}} + b_{\text{out}}$,
    with $W_{\text{in}} \in \mathbb{R}^{d \times 4d}$,
    $W_{\text{out}} \in \mathbb{R}^{4d \times d}$.

    The two halves have distinct roles:

    - Attention mixes across positions (each output depends on all
      previous inputs).
    - MLP mixes across features at a single position (each output
      depends only on the corresponding input).

    The combination is what makes transformers expressive. A pure
    attention model has no per-position non-linearity; a pure MLP
    model has no positional mixing. Both are needed.
notes_to_self: |
  Mechanism 4 of 4. Names the attention + MLP partnership and the
  responsibility split. The "attention mixes across positions, MLP
  mixes across features" line is the key articulation — even
  technical audiences who know transformers tend to find this a
  useful framing.

  No figure (per build constraint). General face stays at the
  level of "two halves, with bookkeeping"; technical face gives
  the residual + LN form.

  Beat 3 has now introduced all four mechanisms. The next card
  closes the beat.
---

# transformer_block
Mechanism 4 of 4. Attention + MLP, the two halves of a single
block. Earns the responsibility split (positions vs features) that
underlies the rest of the talk.
