---
id: attention_qkv
role: branch
thesis_role: enriching
prerequisites: [attention]
technical: true
time_cost:
  short: 0
  standard: 0
  deep: 120
faces:
  technical: |
    The mechanic, more precisely.

    For each token in the sequence, three vectors are derived
    from its embedding by linear projection:

    - **Query** $Q = x W_Q$ — *what am I looking for?*
    - **Key** $K = x W_K$ — *what do I offer?*
    - **Value** $V = x W_V$ — *what do I contribute if picked?*

    For a target position $i$, attention computes a weight
    distribution over all positions $j \le i$:

    $$\alpha_{ij} = \text{softmax}_j \left( \frac{Q_i \cdot K_j^\top}{\sqrt{d_h}} \right)$$

    The output at position $i$ is the weighted sum:

    $$o_i = \sum_j \alpha_{ij} V_j$$

    Multi-head attention runs $h$ such computations in parallel
    on $h$ non-overlapping $d_h$-dimensional subspaces of the
    $d$-dimensional embedding. Heads learn to specialise — some
    attend along positional axes, some along semantic axes, some
    along syntactic ones.

    $W_Q$, $W_K$, $W_V$, $W_O$ are the learned parameters. They
    constitute roughly one third of the parameters per
    transformer block; the other two thirds are the MLP.
  general: |
    *(Skipped on the general face — see the attention card and
    the disambig example for the working intuition.)*
notes_to_self: |
  Technical branch — opens in 60+ minute renderings, hidden
  otherwise. Carries the QKV formula. The "what am I looking for
  / what do I offer / what do I contribute" framing is from
  recent interpretability literature and lands cleanly even for
  technical audiences who already know the formula.

  Marked technical: true so the renderer can hide it in
  shorter compositions.
---

# attention_qkv

Technical branch. The QKV mechanic, with the formula. Skipped in
shorter renderings; opens in the 60+ minute config.
