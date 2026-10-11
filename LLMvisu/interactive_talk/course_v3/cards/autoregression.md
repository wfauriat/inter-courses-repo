---
id: autoregression
role: branch
thesis_role: enriching
prerequisites: [next_token_predictor]
time_cost:
  short: 0
  standard: 60
faces:
  general: |
    Two implications of the one-word-at-a-time rule.

    **The model cannot revise.** Once a word has been emitted, it
    is in the prefix. The model cannot look at what it just said
    and decide it was wrong. It can only condition on it.

    **The model cannot plan.** It has no sense of where the
    paragraph is heading until it has typed it. The appearance of
    structure — paragraphs, arguments, jokes with payoffs — comes
    from the fact that, given a strong prefix, the most likely
    next words are *also* the words that continue the structure.

    The structure is encoded in the prefix's continuation
    probabilities, not in any plan the model held.
  technical: |
    Auto-regressive decoding has two consequences worth naming
    explicitly.

    1. **Causal masking** in attention enforces that position $i$
       attends only to positions $j \le i$. The model is
       structurally unable to look ahead; the loss can be computed
       by a single forward pass over the full sequence.
    2. **No revision pass.** Inference cost is $O(n)$ forward
       passes for $n$ tokens (with KV caching). The model does
       not iterate; the apparent coherence is a property of the
       conditional distribution, not of a planning procedure.

    Modern systems (chain-of-thought, agentic loops) add planning
    *outside* the model — multiple forward passes that sample,
    inspect, and re-prompt. The base model still does not plan.
notes_to_self: |
  A branch off the predictor card that earns "no plan, no
  structure" by giving the audience two consequences they can
  hold onto. Useful for the technical audience (causal masking is
  a useful term to drop early); useful for the general audience as
  a concrete cap on what the model can do.

  Skip in 5-min pitch — implied in next_token_predictor.
---

# autoregression

What auto-regressive means in practice. Two consequences (no
revision, no planning) that frame the apparent magic of the rest
of the talk.
