---
id: transformer_stack_summary
role: spine
thesis_role: load_bearing
prerequisites: [transformer_block]
time_cost:
  short: 15
  standard: 45
faces:
  general: |
    Beat 3 closes.

    Tokens become integers (tokenisation). Integers become vectors
    (embedding). Vectors read each other (attention). Each layer
    refines the result (transformer block).

    Stack twelve of these blocks (more, for bigger models). Each
    layer's output is the next layer's input. By the top of the
    stack, the vector at each position has been mixed, refined,
    re-mixed, re-refined — twelve times.

    The vector at the top represents not just the token, but the
    token *as it appears in this specific context.*

    From there, one final step (the "unembedding"): map the top
    vector back to a probability distribution over the
    vocabulary. That is the next-token distribution we have been
    chasing since beat 2.
  technical: |
    Beat 3 closes. The function class is now specified:

    $$p_\theta(x_{n+1} \mid x_{\le n}) = \text{softmax}\bigl(W_U\, \text{LN}(h_n^{(L)})\bigr)$$

    where $h^{(0)} = W_E[x] + W_P[\text{positions}]$, and

    $$h^{(l+1)} = h^{(l)} + \text{Attn}(\text{LN}(h^{(l)})) + \text{MLP}(\text{LN}(h^{(l)} + \text{Attn}(\text{LN}(h^{(l)}))))$$

    for $l = 0, \ldots, L-1$.

    For GPT-2 small: $L = 12$, $d = 768$, $h = 12$, $d_h = 64$,
    $|V| = 50{,}257$. For frontier models the constants are
    larger but the form is the same.

    The $\theta$ parameters consist of: $W_E$, $W_P$, the
    per-block $(W_Q^k, W_K^k, W_V^k, W_O, W_{\text{in}}, W_{\text{out}})$,
    the LN parameters, and $W_U$. About 124M of them for GPT-2
    small; 100B+ for the deployed frontier.
notes_to_self: |
  Beat-3 closer. One slide. Names the full mechanism stack as a
  single object and previews the architecture beat ("from there,
  one final step").

  The technical face introduces the parameter count
  (124M for GPT-2 small) which is the bridge to architecture_scale.
---

# transformer_stack_summary

Beat 3 closer. The four mechanisms stacked into one object. The
audience now has the entire function class in mind; the next beat
zooms out to look at the whole thing.
