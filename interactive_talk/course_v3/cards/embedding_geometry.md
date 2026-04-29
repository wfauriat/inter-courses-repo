---
id: embedding_geometry
role: branch
thesis_role: load_bearing
prerequisites: [embedding]
time_cost:
  short: 0
  standard: 90
faces:
  general: |
    What does the geometry actually look like?

    **Clusters.** Animal words end up near each other. Verbs end
    up near each other. Country names end up near each other. The
    model was never told that "cat" and "dog" are similar; it
    figured out a representation in which they end up close,
    because their similarity helps prediction.

    **Directions.** The vector from "Paris" to "France" points in
    roughly the same direction as the vector from "Berlin" to
    "Germany." There is a "capital-of-country" direction, and
    you can travel along it. (`king - man + woman` lands near
    `queen` — the famous demonstration of this property.)

    No one wrote down "make capitals offset from countries by a
    consistent vector." The model found that arrangement because
    it makes the next-word probabilities sharper.

    The geometry is not metaphorical. The model is literally
    doing arithmetic on these vectors when it makes predictions.
  technical: |
    Two empirical properties of trained embedding spaces:

    **Local clustering.** Cosine similarity between embeddings is
    a usable proxy for token-level semantic similarity. This is
    the basis for vector-search applications (retrieval, RAG)
    that use LLM embeddings as features.

    **Linear directional structure.** Some semantic relations
    correspond approximately to fixed offsets:
    $e(\text{king}) - e(\text{man}) + e(\text{woman}) \approx
    e(\text{queen})$. The relation is approximate (it depends
    heavily on the embedding model; GPT-2 raw token embeddings
    are noisier than older word2vec/GloVe embeddings) but the
    pattern is robust enough to use pedagogically and
    load-bearing for the talk.

    Caveat: the directional structure exists in $W_E$ *and* in
    the residual stream at deeper layers; the deeper-layer
    directional structure is closer to "concept-of-X" than to
    "token-of-X."
notes_to_self: |
  This is the embedding mechanism's "earned" card — without it,
  the embedding card is "tokens become vectors and trust me it's
  useful." With it, the audience has a concrete reason to believe
  the lift accomplishes something.

  No figure (per spec for this build). The king-queen example
  carries the load on the general face; the cosine-similarity
  + caveat note grounds the technical face.

  Marked load_bearing because it earns the embedding mechanism's
  load-bearing role. Without geometry-encodes-meaning, the
  embedding step is opaque.
---

# embedding_geometry

What the embedding space actually looks like, and why we trust
that the geometry encodes meaning. Earns the embedding mechanism
its load-bearing role.
