---
id: compute_inference
role: branch
thesis_role: enriching
prerequisites: [compute_overview]
time_cost:
  short: 0
  standard: 60
faces:
  general: |
    Inference is what happens every time you talk to a chatbot.

    To produce one token of output: the entire model runs forward,
    once. To produce token N+1: the entire model runs forward
    again, with the prefix one token longer. To produce a
    300-token answer: 300 forward passes.

    This is why long answers visibly stream in. Each token is a
    separate computation, and each takes a non-trivial amount of
    time. Latency scales with model size (bigger = slower per
    pass) and with how much context the model has to read each
    pass.

    Each user query is, computationally, a full re-run of the
    machine. There is no shortcut. The economics of operating an
    LLM service are downstream of this fact.
  technical: |
    Per-token inference cost: $\sim 2P$ FLOPs (forward only) plus
    attention work $O(L \cdot n_{\text{seq}} \cdot d)$ where
    $n_{\text{seq}}$ grows during decoding.

    Bottleneck on modern accelerators: memory bandwidth, not
    arithmetic. The weight matrices have to be streamed through
    the accelerator on each forward pass; arithmetic is fast
    enough that the chip waits on memory. This drives the
    quantisation push (int8, int4) — fewer bytes per parameter
    means faster streaming, even though arithmetic ops are
    cheaper than they need to be.

    The KV cache is the standard optimisation: keys and values
    for prior positions are cached after first computation, so
    each new token only pays attention cost over the cache, not
    $O(n^2)$ recomputation. Memory cost:
    $2 \cdot L \cdot n \cdot d_h \cdot h$ bytes per sequence
    position.
notes_to_self: |
  Compute-inference detail. The "no shortcut, full re-run per
  token" framing is the load-bearing claim for the general face;
  technical face adds the memory-bandwidth bottleneck and KV
  cache.

  Could be its own branch off compute_overview, or could
  collapse with compute_training into a single compute card.
  Kept separate so the technical config has both.
---

# compute_inference

Compute-inference branch detail. Per-token cost shape, memory
bandwidth, KV cache.
