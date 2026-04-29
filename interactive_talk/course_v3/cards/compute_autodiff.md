---
id: compute_autodiff
role: branch
thesis_role: enriching
prerequisites: [compute_training]
technical: true
time_cost:
  short: 0
  standard: 0
  deep: 60
faces:
  technical: |
    How does training "nudge each parameter in the right
    direction"? Auto-differentiation.

    Given a forward pass that computes
    $\mathcal{L}(\theta) = f_n \circ f_{n-1} \circ \cdots \circ f_1\,(\text{input}, \theta)$,
    reverse-mode auto-diff computes the gradient
    $\partial \mathcal{L} / \partial \theta$ in time and memory
    comparable to the forward pass. The chain rule is applied
    node-by-node, backwards through the computation graph.

    Frameworks (PyTorch, JAX) build the computation graph during
    the forward pass (or trace it ahead-of-time) and traverse it
    in reverse. Each operation has a registered backward pass;
    the gradient propagates layer-by-layer, accumulating
    contributions from each parameter use.

    Cost: $O(\text{forward pass})$, regardless of parameter
    dimension. Memory: $O(\text{activations})$, which can be
    reduced via gradient checkpointing (recompute selected
    forward activations during backward).

    Without auto-diff, training a billion-parameter model would
    require billions of forward passes per gradient step. With
    auto-diff, a single forward + backward suffices.
notes_to_self: |
  Technical sub-branch off compute_training. The chain rule +
  reverse-mode AD framing is canonical for ML audiences;
  general audiences do not need this card.

  No general face. If a 60-min mixed audience wants
  backpropagation, write a general face later.
---

# compute_autodiff

Technical branch. Reverse-mode auto-diff and why gradient
computation is tractable. Skipped in non-technical configs.
