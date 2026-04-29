---
id: next_token_predictor
role: spine
thesis_role: load_bearing
prerequisites: [hook]
time_cost:
  short: 30
  standard: 90
faces:
  general: |
    The one thing the machine does:

    Take a chunk of text. Compute a probability for every word that
    might come next. Pick one (usually the most likely, sometimes
    a slightly less likely one for variety). Append it. Repeat.

    The text "I am writing a" might produce a probability
    distribution where "letter" gets 8%, "book" gets 5%, "report"
    gets 4%, and a long tail of less likely options share the rest.
    Sample. Pick "letter." The new chunk is "I am writing a letter,"
    fed back into the same machine, which now computes a
    distribution over what follows *that*. And so on.

    Every paragraph you have ever read from a chatbot was built
    this way. One word at a time. No outline, no plan, no
    structure beyond what the next-word probabilities compel.
  technical: |
    A modern LLM parameterises a conditional distribution
    $p_\theta(x_{n+1} \mid x_{\le n})$ over a finite vocabulary $V$.
    Inference is auto-regressive: sample (or take argmax)
    $x_{n+1} \sim p_\theta(\cdot \mid x_{\le n})$, append,
    re-evaluate.

    The conditional distribution is computed by a single forward
    pass through the network. The network is fixed; the input is
    the prefix. Decoding strategy (greedy, top-$k$, top-$p$,
    temperature, beam search) sits *outside* the model — it is a
    sampling choice, not a model choice.

    Everything that follows specifies the network that computes
    $p_\theta$.
notes_to_self: |
  The mechanical core. After this card, the audience knows what an
  LLM is at the level of "what does it do." Subsequent cards
  unpack the *how*.

  The "I am writing a..." example is concrete and falsifiable —
  the audience could imagine running it themselves. That is
  deliberate; abstract probability claims are easier to dismiss.

  Technical face introduces the formal object and isolates
  decoding strategy as separate. This matters for the alignment
  card later (post-training changes p, not the decoding).
---

# next_token_predictor

The mechanical claim, made concrete. After this card, the audience
holds half of the thesis: LLMs are probability calculators that
emit one token at a time.
