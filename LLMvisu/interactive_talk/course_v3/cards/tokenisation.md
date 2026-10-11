---
id: tokenisation
role: spine
thesis_role: load_bearing
prerequisites: [mechanisms_overview]
time_cost:
  short: 20
  standard: 60
faces:
  general: |
    The model cannot read text. It can read numbers.

    So before anything else, text gets cut into pieces, and each
    piece gets a number.

    The pieces are not characters and not whole words. They are
    something in between, called *tokens.* The word "tokenisation"
    might become four tokens: "token," "is," "ation," and a
    space marker. Common words are single tokens; rare words and
    typos get split into smaller pieces.

    A token vocabulary has on the order of 50,000 entries. Every
    piece of text the model has ever seen, and every piece it
    will ever produce, is built from those 50,000 building blocks.

    From here on, when we say "the model reads," we mean: it reads
    a sequence of integers, each one indexing into the vocabulary.
  technical: |
    The tokeniser is a function $\tau: \text{bytes} \to V^*$ that
    maps a byte string to a sequence of integer ids over a fixed
    vocabulary $V$. Sub-word algorithms (BPE, WordPiece,
    SentencePiece) are the working compromise: bounded vocabulary
    size, no out-of-vocabulary failures, common words are single
    tokens, rare words split into known pieces.

    $|V|$ is a design constant chosen before training (50,257 for
    GPT-2, ~100k for modern frontier models). The model is defined
    on $V^*$, not on text. Everything downstream operates on
    sequences of integers in $[0, |V|-1]$.

    Token boundaries can affect behaviour in non-obvious ways
    (tokens split across visual word boundaries, multi-byte
    characters, capitalisation). For this talk, the relevant fact
    is just: there is a fixed alphabet of about 50,000 symbols,
    and the model's job is to predict the next symbol in that
    alphabet.
notes_to_self: |
  Tokenisation card. The general face uses "tokenisation" as the
  example token-string ("token / is / ation / space") which is
  self-referential and tends to land. Technical face introduces
  BPE/SentencePiece/WordPiece for the audience who wants the names.

  The concrete number 50,000 is repeated for grounding. It will
  reappear at architecture_scale (~40M parameters in the
  embedding table = 50k * 768).
---

# tokenisation

Mechanism 1 of 4. Pulls the rug from under the assumption that the
model "reads words" — introduces the integer-id intermediate layer
that all the geometry will live on.
