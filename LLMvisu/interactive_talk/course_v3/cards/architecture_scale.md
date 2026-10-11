---
id: architecture_scale
role: spine
thesis_role: load_bearing
prerequisites: [architecture_pipeline]
time_cost:
  short: 30
  standard: 60
faces:
  general: |
    The pipeline is structurally simple. So why do these models
    feel so capable?

    Because the pipeline is *huge*.

    GPT-2, the model from 2019 that the slides have been talking
    about, has 124 million parameters. The frontier models in
    2026 are in the 100-billion to trillion-parameter range.

    Think of every parameter as a tiny knob — a single number,
    typically a few digits long — that the model multiplies things
    by during the forward pass. There are 124 million of those
    knobs in GPT-2. Every time you ask a question, every one of
    those knobs is consulted, billions of times, to compute the
    answer.

    The architectural choices (attention, MLP, residual stream)
    make the function class *expressive*. The scale of parameters
    makes that expressive function class *useful*.

    Both are needed. The next beat is about how the values of
    those knobs get set.
  technical: |
    Parameter accounting for GPT-2 small (~124M parameters total):

    - Embedding $W_E$: $|V| \times d = 50{,}257 \times 768
      \approx 38.6\text{M}$.
    - Positional embedding $W_P$: $n_{\text{ctx}} \times d
      = 1024 \times 768 \approx 0.8\text{M}$.
    - Per-block: 4 attention projections ($Q, K, V, O$) at
      $768 \times 768 \approx 2.4\text{M}$; MLP $W_{\text{in}}$
      ($768 \times 3072$) and $W_{\text{out}}$ ($3072 \times 768$)
      $\approx 4.7\text{M}$; small LN params. ~7M per block.
    - 12 blocks: ~85M.
    - LN final + unembedding (often tied with $W_E$): negligible
      additional with weight tying.

    Per-block split: ~1/3 attention, ~2/3 MLP. This ratio is
    consistent across most modern transformer architectures and
    motivates a separate beat on what the MLP is doing (not in
    this composition; available as a deeper branch in longer
    renderings).

    Frontier models ($10^{11}$ to $10^{12}$ parameters) keep the
    same architectural shape and grow $d$, $L$, $|V|$, and
    $n_{\text{ctx}}$.
notes_to_self: |
  Beat 4 closer + bridge to beat 5. The architectural choices
  buy expressivity; scale buys usefulness; training fits the
  parameters — that is the through-line into beat 5.

  The "tiny knob" metaphor on the general face is doing a lot of
  work — it makes 124M concrete and previews the training metaphor
  ("nudging knobs"). Calibrate against the friction-map
  number-overload concern.
---

# architecture_scale

Beat 4 closer. Names the parameter scale and bridges to beat 5
(training as the procedure that fits the parameters).
