---
id: compute_training
role: branch
thesis_role: enriching
prerequisites: [compute_overview]
time_cost:
  short: 0
  standard: 60
faces:
  general: |
    What does it actually take to train one of these?

    Take a frontier-class model — say, 500 billion parameters,
    trained on a few trillion tokens. The math:

    - Each training step processes a batch of tokens through the
      model. The forward pass is a few trillion floating-point
      multiplications.
    - The backward pass — which computes how to nudge each
      parameter — is roughly the same cost again.
    - You do this billions of times.

    All in: 10^24-10^25 floating-point operations. A single fast
    GPU does 10^15 operations per second. That is 30+ years of
    GPU time per training run.

    Which is why frontier training is done on tens of thousands of
    GPUs running in parallel for several months. The hardware is
    half the difficulty.
  technical: |
    Training compute decomposition.

    Per step: forward pass + backward pass + optimiser step.
    Forward FLOPs $\approx 2PB$ (two FLOPs per parameter per
    token, where $B$ is batch size). Backward $\approx 2 \times$
    forward (two matrix products per layer to compute gradients).
    Total per-step $\approx 6PB$.

    Total training: $\approx 6PD$ where $D$ is total tokens. For
    $P = 5 \times 10^{11}$, $D = 5 \times 10^{12}$:
    $\approx 1.5 \times 10^{25}$ FLOPs.

    Parallelism strategies:

    - **Data parallel**: same model, batch sharded.
    - **Tensor parallel**: each weight matrix sharded across
      GPUs.
    - **Pipeline parallel**: layers split across GPUs.

    Frontier runs use all three. GPU utilisation is the limiting
    factor; achieving 50% MFU (model FLOPs utilisation) on a
    distributed training run is considered good.
notes_to_self: |
  Compute-training detail. The "30+ years on a single GPU" line
  on the general face is the kind of grounding that makes the
  scale concrete. Technical face is FLOPs accounting +
  parallelism strategies.

  Skip in 30-min layman by default; include in 60-min technical.
---

# compute_training

Compute-training branch detail. FLOPs accounting + parallelism.
Skipped in shorter renderings.
