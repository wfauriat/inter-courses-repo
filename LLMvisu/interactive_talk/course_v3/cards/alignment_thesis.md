---
id: alignment_thesis
role: spine
thesis_role: load_bearing
prerequisites: [alignment_gap]
time_cost:
  short: 60
  standard: 120
faces:
  general: |
    The gap is closed by **post-training**. Two stages:

    1. **Supervised fine-tuning (SFT).** A team of humans writes
       a few thousand example (question, answer) pairs, in the
       register users actually want — direct, helpful, formatted
       like an answer. The base model is fine-tuned on these
       pairs. It learns "when text looks like a question, the
       continuation should look like an answer."

    2. **Reinforcement learning from human feedback (RLHF).** The
       fine-tuned model generates pairs of candidate responses;
       humans pick which they prefer. Those preferences are
       turned into a reward signal, and the model is fine-tuned
       again — this time toward responses humans prefer.

    Post-training is a thin layer compared to pretraining: a few
    thousand to a few hundred thousand examples, not a few
    trillion tokens. The base model is still inside; alignment is
    a final shaping step.

    And that step is the difference between "a probability
    calculator that emits internet-flavoured text" and "a chatbot
    that answers your question."

    ---

    *That is the talk.*

    A modern LLM is a probability calculator that emits one token
    at a time. Everything that makes it feel like a thinking
    entity — fluency, context, factual recall — is the joint work
    of a stack of mechanisms (tokenisation, embedding, attention,
    transformer block) trained at internet scale, then nudged by
    a thin alignment layer at the very end.

    The calculator is the body; the mechanisms are the limbs;
    training is the upbringing; alignment is the manners.
  technical: |
    Post-training, schematically:

    - **SFT**: minimise
      $-\mathbb{E}[\log \pi(\text{response} \mid \text{prompt})]$
      on a curated $(\text{prompt}, \text{response})$ dataset of
      size $10^4$-$10^5$. Yields $\pi_{\text{SFT}}$.
    - **Reward model**: train
      $r_\phi(\text{response} \mid \text{prompt})$ from human
      preference pairs $(\text{resp}_w, \text{resp}_l)$ using a
      Bradley-Terry-style loss.
    - **RLHF (PPO or DPO variants)**: optimise

      $$\pi_{\text{RLHF}} = \arg\max_\pi\, \mathbb{E}[r_\phi(\text{resp})] - \beta\, \text{KL}(\pi \,\|\, \pi_{\text{SFT}})$$

      The KL regulariser anchors $\pi_{\text{RLHF}}$ to the SFT
      reference, preventing reward-model exploitation and
      preserving general capabilities.

    $\pi_{\text{RLHF}}$ is the deployed chatbot. The base
    predictor is structurally still inside (the architecture
    hasn't changed, most parameter values haven't moved much),
    but the distribution over responses has been re-shaped to
    match human preferences over an answer-formatted style.

    ---

    The thesis, formally: a deployed LLM-driven chatbot is
    $\pi_{\text{RLHF}}$, where $\pi_{\text{RLHF}}$ is
    $\pi_{\text{SFT}}(\pi_{\text{base}})$ shaped by $r_\phi$,
    where $\pi_{\text{base}}$ is fitted by SGD on next-token
    cross-entropy over a $\sim\!10^{13}$-token corpus, where the
    architecture is a stack of $L$ (attention + MLP) residual
    blocks.

    That whole sentence is the artefact. Everything else — the
    chatbot UI, the system prompt, the safety filtering — is the
    product layer.

    *(Reflexive close, optional: the audience has just watched a
    $\pi_{\text{RLHF}}$ explain $\pi_{\text{RLHF}}$. The talk
    performs what it argues. Land if the room has earned it; skip
    if the room is cold.)*
notes_to_self: |
  THE THESIS CARD. Lands the talk.

  General face: post-training in two stages, then the thesis
  sentence ("a modern LLM is..."). The lower paragraph
  ("calculator is the body; mechanisms are the limbs; training
  is the upbringing; alignment is the manners") is the
  metaphorical re-statement that the audience can carry home.

  Technical face: same structure, with formulas. The reflexive
  close is included as an optional inline aside. Decide live
  whether to deliver.

  Calibrate length: this card is the longest in the talk by
  design — it is the take-home. Slide-render is OK because the
  audience has bandwidth here (no new mechanism being learned).
---

# alignment_thesis

THESIS CARD. The post-training step that converts predictor into
chatbot, plus the take-home thesis sentence. Final card of the
spine.
