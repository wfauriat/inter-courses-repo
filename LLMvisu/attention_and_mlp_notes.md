# Attention & MLP — personal interpretation notes

A reference for structuring my own understanding. *Not* a talk outline;
this keeps the technical mechanics (shapes, linear algebra) and the
layman / intuitive readings side by side, because each of them without
the other misleads.

---

## Division of labor — the single-line version

> **Attention decides who listens to whom. The MLP is where each token thinks.**

Each transformer block does these two things in sequence:

1. **Attention** — mixes information *across* tokens. Every token
   reaches into the rest of the sequence and pulls in whatever is
   relevant to its own current state.
2. **MLP** — processes each token *independently*. No cross-token
   interaction; purely per-token non-linear computation.

They alternate, block after block — in GPT-2 small, twelve times. The
alternation is the essential rhythm of the model: *route, compute, route,
compute.* Each cycle sharpens the representation a little further, and
the final one gets projected back onto the vocabulary to predict the
next token.

What each one **lacks** is almost as important as what each one does:

- Attention lacks a real non-linearity (softmax is a normalization, not
  a computation) and lacks per-token feature creation. On its own it
  can only *shuffle and average* existing features.
- MLP lacks cross-token awareness and positional awareness. On its own
  it can only *transform* the vector it is given.

Neither alone builds a language model. Alternated, they do.

---

## Attention

### The mechanism

For one block and one head (GPT-2 small uses 12 blocks × 12 heads, with
a 64-d subspace per head):

```
                     W_Q, W_K, W_V each (768 × 768)
                     split into 12 head slices of (768 × 64)

h ──▶ Q = h · W_Q[:, head_slice]             # (seq, 64)
 \──▶ K = h · W_K[:, head_slice]             # (seq, 64)
  \─▶ V = h · W_V[:, head_slice]             # (seq, 64)

scores  = Q · Kᵀ / √d_head                    # (seq, seq)
scores += causal_mask                          # future positions = −∞
weights = softmax(scores, axis=−1)             # each row sums to 1
out_h   = weights · V                          # (seq, 64)

out = concat(head_0, …, head_11) · W_O         # (seq, 768) added to residual
```

At its core, attention is a **weighted sum of V vectors**. Softmax
provides the only non-linearity and its job is just to turn raw scores
into a valid averaging distribution (positive, summing to one).

### Layman reading

Each token asks a question (**Q**), advertises an answer (**K**), and
carries content (**V**). The score is "how well does *this* token's
question match *that* token's offer?" Softmax converts scores to mixing
weights. Each token ends up replaced by a **weighted average of its
neighbors' V vectors** — a contextualized version of itself.

### Q·Kᵀ as direction alignment — what it captures, and what it misses

The dot product has the form `|Q||K| cos θ`, so the clean intuition is:
*tokens whose Q and K point similar ways attend to each other.* That is
the right first-order picture. Four caveats keep it honest:

- **The alignment is measured inside a subspace learned by that specific
  head**, not in the embedding space. Each head carves its own 64-d view
  of what is worth matching on. Some match on semantics, others on
  syntax, others on position, others on token identity. "Semantic
  direction" is only one flavor.
- **Q and K are different projections of the same token** (`W_Q ≠ W_K`).
  "What I ask for" and "what I advertise" can be asymmetric, which is
  what lets a head route a pronoun to its antecedent — a relationship
  that cannot exist in a symmetric cosine-similarity world.
- **The dot product gates *flow*; V carries *content*.** The attention
  weight is bandwidth — how much of token j reaches token q — and V is
  the payload. Geometry answers "who listens to whom," not "what is
  said."
- **Magnitudes matter too.** Raw dot product responds to `|Q||K|`, not
  just `cos θ`. The position-0 "attention sink" artifact in GPT-2 is
  partly a norm outlier: BOS's K has an inflated magnitude, so it
  collects softmax mass independent of direction.

### How the 64-d head space and the 768-d residual stream relate

The 64-d head space is **not a separate space**. It is a **linear
projection** of the 768-d residual stream:

```
Q_h = h · W_Q[:, head_slice]       # 768-d h → 64-d Q_h
```

No new information; the head is *choosing* which features of the 768-d
vector to care about, via its learned W_Q and W_K.

Two wrinkles worth remembering:

- At layer ℓ > 0, the 768-d residual is **not the embedding anymore**.
  It has been contextualized and transformed by earlier blocks. "Cat at
  layer 10" encodes things like "subject of the current clause, an
  animal being discussed, what came before" — not raw cat-ness.
- W_Q and W_K are *independent* matrices. The head can set them up so Q
  asks for one feature and K advertises a different one.

### Does "cat" automatically attend to keys of "dog"?

No. This is the single most important distinction between **embedding**
and **attention** geometry.

- In GloVe (the embedding workshop), `cat` and `dog` are close *by
  construction*. The training objective literally shapes that geometry,
  so cosine similarity between their vectors is high, always.
- In attention, there is no such general pressure. A head aligns cat's
  Q with dog's K *only if* it has learned to project both onto a shared
  feature they both carry (e.g. "is an animal"). That is a
  head-specific, empirical outcome.

What you actually find when you look inside:

- **Content-matching heads** — Q/K subspace keys on semantic features.
  Here, cat → dog alignment is real; induction heads and name-mover
  heads work this way.
- **Structural / positional heads** — Q/K subspace keys on position,
  syntactic role, or token identity. Semantic similarity is incidental
  or absent.
- **Layer-dependence** — early-layer heads tend to be positional and
  structural; middle-layer heads include more content matching;
  late-layer heads are task-specific.

So: semantic similarity in the embedding does *not* automatically
propagate to semantic similarity in every head's Q/K geometry. Whether
cat attends to dog depends on which head you ask.

---

## MLP

### The mechanism

For one block, applied **independently** to each token's 768-d residual
vector:

```
h ──▶ h · W_up ──▶ GELU ──▶ (·) · W_down ──▶ Δh
     (768 × 3072)            (3072 × 768)
```

Δh gets added back into the residual stream. The 768 → 3072 → 768 shape
is a conventional 4× hidden-layer expansion; GELU is the non-linearity
in GPT-2 (newer models use SwiGLU or similar). No cross-token anything
— every token is processed in parallel but in isolation.

### Layman reading

After attention gathers relevant info from neighbors, the MLP
**processes** that info at each token. Attention is the routing layer;
the MLP is the computation layer. It is where the token *thinks*.

### Three complementary readings

**1. Non-linear feature computation.** Without the MLP, the rest of the
transformer is essentially linear (attention is weighted-sum-of-V on top
of softmax). Stacking linear operations produces only linear functions.
The MLP is the main non-linearity in the model — where features actually
get *computed* rather than just shuffled.

**2. A bank of detect-and-write rules.** Read each of the 3072 hidden
neurons as a pair:
- Its **input weights** (one 768-d row of W_up) define a **pattern**.
  The neuron fires when the residual stream matches that pattern
  (through GELU).
- Its **output weights** (one 768-d column of W_down) define a
  **direction** that gets added back to the residual stream when the
  neuron fires.

So the MLP is ≈3000 rules of the form:

> *If you see pattern X in the residual stream, write direction Y
> into it.*

Some rules encode "if the context mentions Paris, add 'capital of France'
to the stream." Some encode boring syntax. Most are *not* cleanly
interpretable individually — see the polysemanticity caveat below.

**3. Associative / factual memory.** Geva et al. (2021, *"Transformer
Feed-Forward Layers Are Key-Value Memories"*) showed the MLP reads
mathematically *as* a key-value memory in exactly the detect-and-write
shape above. Meng et al. (ROME, 2022) showed that **editing specific
MLP weights in a specific layer can change a specific factual belief**
of the model — "The Eiffel Tower is in Paris" → "Rome" — without
disturbing unrelated facts. This is the empirical version of "a lot of
what the model *knows* lives in the MLP, not in attention."

### Parameter budget

Per GPT-2-small block (ignoring biases):

| Component                                 | Parameters   |
|-------------------------------------------|-------------:|
| Attention (W_Q, W_K, W_V bundled + W_O)   | ≈ 2.36 M     |
| MLP (W_up, W_down)                        | ≈ 4.72 M     |
| **Total block**                           | **≈ 7.08 M** |

The MLP is roughly **⅔ of each block's parameters**, and this ratio
holds at scale. The model spends more capacity on per-token computation
than on cross-token routing — another way of saying *attention routes,
MLP thinks*.

---

## Shared caveats

### Polysemanticity and superposition

Neurons are **not cleanly monosemantic.** A single MLP neuron typically
fires on many unrelated patterns because the model packs more features
than it has dimensions (superposition). The "each neuron is one rule"
story is an idealization; real interpretability increasingly relies on
sparse coding or dictionary learning (Sparse Autoencoders, Anthropic's
monosemantic-feature line of work) to untangle what a neuron is really
doing.

The analogous story holds on the attention side: "head X attends to
pattern Y, therefore it does Z" is a correlation. A given head's
attention pattern is often interpretable on one prompt and looks
different on another. What is robust is *structural* behavior averaged
over many prompts (previous-token heads, induction heads); what is
fragile is per-prompt interpretation.

### Post-hoc interpretation is illustration, not causation

Reading activations or attention weights tells you **what** the model
did; it does not tell you **why**, or whether that pattern *caused* the
output. Real mechanism claims need:

- **Ablation** — zero out a component, measure whether the behavior
  disappears.
- **Activation patching** — replace an activation from prompt A with
  the one from prompt B and measure which downstream tokens shift.
- **Path patching / causal scrubbing** — test a specific hypothesis
  about which paths through the network carry the behavior.

Without that, any statement of the form "this head / this neuron does X"
is a *story that fits the data*, not a *tested hypothesis*. Keep a firm
line between the two when reading attention / MLP visualizations.

---

## The integrated single-paragraph version

Attention and MLP form each transformer block. **Attention** looks
across every token in the sequence and, for each one, computes a
weighted average of the others' V vectors — where the weights come from
how well each token's query (Q) aligns with each other token's key (K)
inside a 64-d subspace specific to that head. Different heads learn to
match on different features: some on semantics, some on syntax, some on
position, some on token identity. This is how the model contextualizes
each token — it decides **who listens to whom**. Then the **MLP** takes
each token's contextualized vector and, independently of the others,
runs it through a non-linear 2-layer network that can be read as a bank
of "if you see pattern X, add direction Y" rules — including, empirically,
many of the model's factual beliefs. This is where each token **thinks**.
Alternating the two — route, compute, route, compute — twelve times
(in GPT-2 small) is what turns a raw token embedding at the bottom of
the stack into a sharp probability distribution over next tokens at the
top.
