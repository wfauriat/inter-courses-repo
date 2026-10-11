# Embedding Workshop — Plan

A standalone PySide app, separate from `GPT_arch_workshop.py` and
`attention_workshop.py`. Its job is to make **semantic geometry** visible in
a clean setting — using a dedicated word-level embedding (GloVe), not
GPT-2's wte. The other apps cover GPT-2 mechanics; this one is about the
*idea* of "meaning as direction" in vector space.

Explicit non-goal: do *not* show GPT-2 wte alongside GloVe in this app. The
side-by-side comparison was tempting but the user wants a clean,
disconnected story here. GPT-2's anisotropic embedding can stay a topic
for the architecture workshop.

---

## What it teaches

The user should walk away able to answer, unprompted:

1. **Words are vectors, and similar meanings sit close together.** Type
   `cat` and the nearest neighbors are `dog`, `kitten`, `pet` — not
   alphabetical, not random.
2. **Categories form clusters in 2D.** Project a handful of animals and
   buildings into 2D and they separate visually; the geometry isn't
   accidental.
3. **Pairwise cosine similarities encode taxonomy.** A heatmap of cat /
   dog / sheep / tower / building / bridge shows two clear blocks.
4. **(Optional) Vector arithmetic recovers analogies.** `king − man + 
   woman ≈ queen`. The classic word2vec demo, included only if it's worth
   the panel.
5. **(Optional, contrast) Distance metric matters.** Cosine vs Euclidean
   give different rankings — cosine ignores frequency-driven norm
   differences, Euclidean doesn't. This is the bridge to why transformer
   research mostly uses cosine.

Out of scope (explicit): GPT-2 anything, training/learning the
embeddings, multilingual embeddings, contextual embeddings (BERT/ELMo),
sentence embeddings.

---

## Data source

**GloVe** is the right choice — pre-trained, well-known, freely available,
canonical for this exact teaching demo.

Variant choice (default = **glove.6B.100d**):
- `glove.6B.50d` (171 MB) — too low-resolution; semantic clusters get
  fuzzy.
- `glove.6B.100d` (347 MB) — sweet spot. Fast to load, structure clear.
- `glove.6B.200d` (685 MB) — diminishing returns for visualization.
- `glove.6B.300d` (1.04 GB) — overkill, slow first-load.

Source: Stanford NLP page (`https://nlp.stanford.edu/data/glove.6B.zip`),
or via `gensim.downloader` if we want to skip the manual download dance.
File format is plain text — one word per line, space-separated:
`word v1 v2 ... vN`.

Loading strategy:
- One-time download to `workspace/data/glove.6B.100d.txt` (gitignored).
- On first app start, parse and cache as a `.npz` (vectors + word list)
  for fast subsequent loads. Warn if not present and exit cleanly.
- In-memory: `np.ndarray (vocab, dim)` + `dict[word -> idx]` + `list[word]`.

Optional optimization: ship a precomputed subset of the **20k most
frequent words** (~16 MB at 100d). Cuts load time from seconds to
instant, covers everything anyone would type in a teaching demo. Defer to
v2 unless first-load speed becomes annoying.

---

## Panel layout (sketch)

Two-column layout. Left column = inputs (compact, fits in ~350px). Right
column = visualizations (the bulk of the window).

**Left column (top → bottom):**

1. **Word groups input.** A small table widget where each row is one
   category: `name | comma-separated words | color`. Default rows
   pre-filled with the user's example:
   ```
   animals       | cat, dog, sheep, horse, cow      | blue
   constructions | tower, building, bridge, house   | orange
   ```
   Buttons: *add row*, *remove row*, *update*. "Update" recomputes the
   right-column visualizations.

2. **Word inspector.** Single text field + "lookup" button. Shows the
   top-k nearest neighbors of the typed word with cosine similarity
   scores. Useful as a quick "explore the vocabulary" tool, separate
   from the configured groups.

3. **(Optional) Analogy box.** Three text fields: `A − B + C = ?`.
   Returns top-k candidate words. Pre-filled default:
   `king − man + woman = ?`. Cheap to add, good talk demo.

**Right column (top → bottom):**

1. **2D scatter.** All configured words projected into 2D, colored by
   category, labeled. PCA by default (deterministic, fast); toggle for
   t-SNE (prettier separation but stochastic, takes a couple seconds).
2. **Pairwise similarity matrix.** Cosine-similarity heatmap of all
   configured words against each other. Words grouped on each axis by
   category; a thin separator line between blocks. Cell values
   annotated when ≤ ~16 words.
3. **(Optional, behind toggle) Cosine vs Euclidean comparison.** For a
   single chosen anchor word from the configured set, two side-by-side
   nearest-neighbor lists — one ranked by cosine, one by Euclidean.
   Lets the talk discuss why the field settled on cosine.

Layout host: PySide `QSplitter(Qt.Horizontal)` between left and right
columns; right column is its own `QVBoxLayout` of `FigureCanvas`es. No
scroll area needed — the panels are designed to fit a 1500×1000 window.

---

## Controls

- Word groups table (left column) — primary input.
- "Update" button — recomputes right column from current groups.
- Reduction method dropdown — `PCA` (default) / `t-SNE` / `UMAP` (UMAP
  only if the dependency is acceptable; otherwise drop).
- Top-k slider for word inspector (default 8).
- Analogy text fields (if included) + "compute" button.
- Toggle: "Show cosine vs Euclidean comparison" (default off).

No per-cell hover / zoom interactions in v1 — keep matplotlib stock
behaviour (built-in pan/zoom toolbar is enough). Defer fancy
interactivity to v2 if needed.

---

## Backend

Single class `EmbeddingBackend` exposing:

- `__init__(path)` — loads vectors and word list into numpy.
- `vector(word) -> np.ndarray | None` — case-insensitive lookup,
  returns None on OOV.
- `nearest(word, k, metric="cosine") -> list[tuple[word, score]]` —
  cosine or Euclidean ranking, OOV-safe.
- `analogy(a, b, c, k) -> list[tuple[word, score]]` — `a − b + c`,
  excluding the three input words from the result.
- `pca_2d(words) -> np.ndarray (len, 2)` — fit fresh PCA on just the
  selected words (not the whole vocab) so the axes are tuned to what
  the user is showing.
- `tsne_2d(words, seed=0) -> np.ndarray (len, 2)` — same, but t-SNE.
  Fixed seed for reproducibility.
- `pairwise_cosine(words) -> np.ndarray (len, len)` — symmetric matrix.

Vocabulary lookup is case-insensitive (lowercase the input), with a
visible warning in the UI if a typed word is OOV.

---

## Confirmed design decisions

1. **GloVe only**, no GPT-2 wte side-by-side in this app. The user
   wants the two stories disconnected.
2. **glove.6B.100d as default** — fast load, clean clusters, enough
   resolution for teaching.
3. **Categories are user-editable**, with sensible defaults pre-filled
   (animals + constructions per the user's example). Hardcoded
   categories would defeat the workshop concept.
4. **Analogy panel included** (`A − B + C = ?`). Classic word2vec demo,
   pre-filled with `king − man + woman`.
5. **Cosine-vs-Euclidean comparison included, behind a default-off
   toggle.** Keeps v1's main view clean while making the metric story
   available when teaching it.
6. **PCA + t-SNE, PCA as default.** PCA is deterministic and honest
   about distances; t-SNE separates clusters more dramatically but
   distorts geometry — flag that in a tooltip. **No UMAP** in v1
   (extra dependency, marginal gain over t-SNE).
7. **Manual GloVe download.** On first launch, print clear instructions
   and the URL; do not auto-download 350 MB silently.
8. **No 20k-word precomputed subset in v1.** Ship the full 100d file;
   only optimize load time if it actually proves annoying.

---

## File structure

- `workspace/embedding_workshop.py` — the single-script app.
- `workspace/data/glove.6B.100d.txt` — GloVe weights (gitignored).
- `workspace/data/glove.6B.100d.npz` — cached numpy version (built on
  first run, gitignored).

---

## Build order, if greenlit

1. **Backend.** Load glove.6B.100d, expose the methods above. Sanity
   probe: `nearest("cat", 5)` should include `dog` and `kitten`;
   `analogy("king", "man", "woman", 3)` should include `queen`. If
   either fails, the loader is wrong.
2. **Skeleton app.** Word groups table + Update button + an empty
   right-column placeholder. Confirm the table edits propagate.
3. **2D scatter panel** with PCA. Hardest visualization to get
   readable — solve it before adding more panels.
4. **Pairwise similarity matrix.** Mostly a heatmap, easy after the
   scatter is working.
5. **Word inspector** + (optional) analogy panel.
6. **(Optional) cosine-vs-Euclidean comparison toggle.**
7. **Polish:** OOV warnings, axis labels, category color consistency
   between scatter and similarity matrix.
