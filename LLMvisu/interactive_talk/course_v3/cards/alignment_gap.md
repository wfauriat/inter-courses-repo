---
id: alignment_gap
role: spine
thesis_role: load_bearing
prerequisites: [training_emergence]
time_cost:
  short: 30
  standard: 60
faces:
  general: |
    One last thing. The model we have just described — call it
    the *base model* — is not what you talk to.

    Ask the base model: "How do I make pancakes?"

    The base model has been trained on text where that question
    appears, and it predicts the next token by the same statistical
    process as before. The most likely continuation is not
    necessarily a pancake recipe. It might be:

    > *"How do I make pancakes?" is a common question, especially
    > among first-time cooks. In this article we'll discuss the
    > basic ingredients...*

    Because in the training data, that question is often followed
    by *more text about the question,* not by an answer.

    The base model is good at continuing text. It is not yet good
    at *responding* to text. That is a different skill, and it is
    not something the next-token-prediction objective directly
    selects for.
  technical: |
    The base model after pretraining is
    $\pi_{\text{base}} = p_{\theta_{\text{base}}}$, a conditional
    next-token distribution over $V^*$. Sampling from it given a
    question-shaped prompt does not reliably produce
    answer-shaped responses, because the training distribution
    contains many continuations of question-shaped text that are
    *not* answers (forum threads, articles, lecture transcripts,
    metadiscussion).

    The misalignment is at the distribution level: the
    likelihood-maximising continuation under the training
    distribution is not the user-preferred continuation. No amount
    of cleverer prompting fixes this without changing the model;
    the base model is doing exactly what its objective rewards.
notes_to_self: |
  Beat 6 opener. Names the gap between base predictor and
  chatbot. Concrete pancakes example because it is the v1
  example I am keeping (it is also genuinely the canonical one
  for this beat).

  This card sets up the thesis card. The thesis card cannot
  land without this gap being named — otherwise alignment looks
  like an epilogue rather than a load-bearing element.
---

# alignment_gap

Beat 6 opener. Names the gap between base predictor and deployed
chatbot. Without this gap, the alignment thesis card has nothing
to bridge.
