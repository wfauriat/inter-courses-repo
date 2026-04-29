---
id: compute_kv_cache
role: branch
thesis_role: enriching
prerequisites: [compute_inference, attention_qkv]
technical: true
time_cost:
  short: 0
  standard: 0
  deep: 60
faces:
  technical: |
    The KV cache, in detail.

    During auto-regressive decoding, for each new token at
    position $n+1$:

    - The new token's $Q_{n+1}$, $K_{n+1}$, $V_{n+1}$ are
      computed from its embedding.
    - The new token attends to all positions $j \le n+1$.
    - Crucially, $K_j$ and $V_j$ for $j \le n$ were already
      computed during prior decoding steps and *do not change.*

    The KV cache stores $(K_j, V_j)$ for all prior positions,
    per layer, per head. On each new token: append the new $K$
    and $V$, then run attention with $Q_{n+1}$ against the full
    cache.

    Per-step cost: $O(n)$ instead of $O(n^2)$. Memory cost:
    $2 \cdot L \cdot n \cdot h \cdot d_h \cdot \text{sizeof(float)}$
    per sequence. For long contexts ($32\text{k}{+}$ tokens) on
    large models, KV cache memory can dominate the parameter
    memory.

    Recent research (group-query attention, multi-query
    attention) shrinks the cache by sharing K/V across heads.
    Frontier models use these techniques heavily.
notes_to_self: |
  Technical sub-branch off compute_inference. Requires
  attention_qkv as prereq. Skipped in non-technical configs.

  No general face — the KV cache is a technical-audience
  concept. (If a general audience needs to know about it, the
  framing is "there's an engineering trick that makes long
  conversations possible," which fits in compute_inference's
  general face.)
---

# compute_kv_cache

Technical branch. The KV cache mechanic. Skipped in non-technical
configs.
