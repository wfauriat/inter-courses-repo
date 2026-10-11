---
id: architecture_pipeline
role: spine
thesis_role: load_bearing
prerequisites: [transformer_stack_summary]
time_cost:
  short: 30
  standard: 60
faces:
  general: |
    The whole machine, in one breath:

    1. Text comes in.
    2. Tokeniser converts it to integer ids.
    3. Each id becomes a 768-dimensional vector (embedding).
    4. Vectors flow through twelve transformer blocks. Each block
       mixes information across positions (attention) and across
       features (MLP).
    5. The final vector at the last position becomes a
       probability distribution over the 50,000-token vocabulary.
    6. Sample one. Append. Go back to step 1.

    No outline of what the answer should be. No memory of
    previous conversations except what is in the prompt. No
    plan. Just six steps, billions of times.
  technical: |
    Forward pass:

    - Tokenise: $x_{1:n}$ from raw bytes.
    - Embed: $h^{(0)} = W_E[x_{1:n}] + W_P[1{:}n]$, shape
      $n \times d$.
    - Block stack ($L$ blocks): $h^{(l+1)} = \text{block}(h^{(l)})$,
      preserving the $n \times d$ shape.
    - Final layer norm: $h_{\text{final}} = \text{LN}(h^{(L)})$.
    - Unembedding: $\text{logits} = h_{\text{final}}\, W_U$,
      shape $n \times |V|$.
    - Softmax (per-position): yields
      $p(x_{i+1} \mid x_{\le i})$ for every $i$ in the sequence
      (used at training time; at inference, only the last
      position is sampled).

    The architecture is parameter-rich and computation-rich but
    structurally simple — the same block applied $L$ times. There
    is no recurrence, no convolution, no skip-skip-skip
    interconnect; just a linear chain of identical residual blocks
    on a residual stream.
notes_to_self: |
  Beat 4 spine card. Walks the whole pipeline end-to-end. The
  general face is six numbered steps; this is the only place in
  the talk where the pipeline is enumerated explicitly.

  No figure (build constraint). The numbered list does the work
  the figure would have done in v1. For a slide deck this
  actually reads cleanly.
---

# architecture_pipeline

The whole machine, walked end-to-end. Beat 4 spine card. Single
slide that lets the audience hold the entire forward pass in
mind at once.
