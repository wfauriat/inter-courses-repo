---
id: training_objective
role: spine
thesis_role: load_bearing
prerequisites: [architecture_scale]
time_cost:
  short: 30
  standard: 90
faces:
  general: |
    All of this — the embeddings, the attention, the MLP layers —
    is initialised with random numbers. A freshly built LLM is
    incoherent. It would predict random tokens, with no
    structure.

    Training is the procedure that turns the random initialisation
    into a useful model. It works like this:

    Show the model a chunk of text. Ask it to predict the next
    token. Look at what it predicted versus what the actual next
    token was. Use that error to nudge every parameter slightly,
    in the direction that would have made the prediction more
    correct.

    Repeat this — *trillions of times* — across a corpus that is
    roughly the readable internet: web pages, books, papers,
    forums, code, manuals.

    No labels. No human annotations. The data labels itself: the
    next token in the text is always the answer. We just hide it,
    let the model guess, and use the gap as feedback.

    This is called **self-supervised learning**, and at this scale,
    it is what produces everything you have ever experienced from
    a chatbot.
  technical: |
    Pretraining minimises cross-entropy on next-token prediction:

    $$\mathcal{L}(\theta) = - \mathbb{E}_{i \sim \text{corpus}} \left[ \log p_\theta(x_i \mid x_{<i}) \right]$$

    The corpus is a concatenation of preprocessed text from web
    crawl (CommonCrawl filtered), Wikipedia, books, code
    repositories, scientific papers, etc. Total size: $10^{12}$
    to $10^{13}$ tokens for frontier models.

    Optimisation is SGD with momentum, in practice Adam(W). Batch
    sizes are large (millions of tokens per step), implemented via
    data + tensor + pipeline parallelism across thousands of
    GPUs. Training a frontier model is a multi-month, multi-
    million-dollar capital investment.

    The objective is *self-supervised*: no human labels, no
    auxiliary task. The supervision signal is the next token
    itself, available at every position in the training corpus.
notes_to_self: |
  Beat 5 opener. Names the training objective and lands the
  "self-supervised, internet-scale" claim.

  General face emphasises "no labels" — this is non-obvious to
  audiences who know about supervised learning and assume LLMs
  needed labelled data. Refuting this assumption preemptively
  helps the next card (emergence) land.

  Technical face gives the cross-entropy loss + the
  parallelism gesture; no need to dwell on optimisation details.
---

# training_objective

Beat 5 opener. Names training-as-procedure and the self-supervised
objective. Sets up the emergence card.
