---
id: mechanisms_overview
role: spine
thesis_role: load_bearing
prerequisites: [ntp_summary]
time_cost:
  short: 30
  standard: 60
faces:
  general: |
    Predicting the next word does not, by itself, sound impressive.
    "Statistical fluency" is decades old.

    What is new is *that the prediction is good enough to feel like
    understanding.* That is the load-bearing claim of modern
    machine learning, and it took four ideas, stacked, to get there.

    1. **Tokenisation** — convert text into numerical chunks.
    2. **Embedding** — give every chunk a position in space, where
       distance and direction encode meaning.
    3. **Attention** — let chunks read each other, so a word's
       contribution depends on its neighbours.
    4. **The transformer block** — repeat the read-and-mix many
       times, so meaning compounds across layers.

    Plus a fifth: **training at scale**. We will get to that in
    beat 5.
  technical: |
    The mechanism stack of a decoder-only transformer:

    1. Tokeniser $\tau: \text{bytes} \to V^*$.
    2. Embedding $e: V \to \mathbb{R}^d$, parameterised by
       $W_E \in \mathbb{R}^{|V| \times d}$, with positional
       encoding added.
    3. Attention layer, multi-head:
       $\text{softmax}(QK^\top / \sqrt{d_h})\, V$, causally
       masked.
    4. Transformer block: attention + MLP, both residual, with
       layer norm. Stack $L$ of them ($L=12$ for GPT-2 small,
       $L \ge 80$ for frontier models).
    5. Unembedding $W_U$ followed by softmax to yield the
       next-token distribution.

    Plus the training procedure that fits the parameters; that is
    its own beat.

    Each of items 1-4 is a card.
notes_to_self: |
  The agenda for beat 3. Four mechanism cards follow, plus one
  beat closer. The technical face is more specific about the
  transformer block (attention + MLP, residual) than the general
  face — the general face introduces the block in card 4 to keep
  the pacing accessible.

  This card opens the heaviest beat. Cognitive-load-stacking risk
  starts here; mitigation is the disambig example midway through.
---

# mechanisms_overview

Beat 3 opener. Names the four mechanisms that the rest of the beat
will unpack. Functions as table-of-contents and as the setup for
the "and they are enough" claim that beat 3 closes on.
