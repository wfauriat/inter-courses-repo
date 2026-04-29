---
id: compute_overview
role: branch
thesis_role: enriching
prerequisites: [architecture_scale]
time_cost:
  short: 0
  standard: 30
faces:
  general: |
    Worth saying out loud: this only works because of the compute.

    Two regimes to keep separate:

    - **Training compute.** A one-time cost. Months of runtime on
      thousands of GPUs. Tens of millions of dollars for a frontier
      model.
    - **Inference compute.** An ongoing cost. Every time you ask a
      chatbot a question, the whole machine runs forward, once
      per token. Most of the per-query cost is here.

    Different shapes; different bottlenecks; different economics.
    The architecture is the same in both regimes; it is the
    workflow that differs.
  technical: |
    Compute regimes for an LLM:

    - **Training**: $O(P \times D)$ FLOPs (Kaplan/Chinchilla
      scaling). For a 100B-parameter model on 2T tokens,
      $\sim\!10^{24}$ FLOPs total. Modern training runs use $10^4$
      to $10^5$ GPUs in parallel (data + tensor + pipeline
      parallelism), running for weeks to months.
    - **Inference**: $O(P)$ FLOPs per generated token (with the
      KV cache, otherwise $O(P + n_{\text{seq}} \cdot d)$).
      Latency is typically memory-bandwidth-bound on modern GPUs;
      the model weights are streamed through the accelerator on
      each forward pass.

    Cost per inference token has dropped roughly $10\times$ per
    year for several years; cost per training token has not.
notes_to_self: |
  Branch off architecture_scale. Optional in 30-min layman; can
  open in 60+ min technical or in dedicated compute-focused
  rendering.

  General face is brief — the audience does not need compute
  detail to understand the talk. Technical face has the FLOPs
  scaling and the memory-bandwidth note.
---

# compute_overview

Compute branch entry. Names training vs inference and their
asymmetric economics.
