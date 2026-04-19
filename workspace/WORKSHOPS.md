# LLM Mechanics — Interactive Workshops

Companion document to the three PySide6 + matplotlib apps in this workspace.
They form a coherent set for a vulgarization talk on LLM inner mechanics and
are designed to be run live, one concept at a time. The numbered
`00_..14_...py` scripts in the same folder generate *static* slide figures;
the workshops are the *interactive* counterpart — a place to click around
and build intuition the figures can't convey alone.

**Common stack.** Python, PySide6 (Qt) for the window and controls,
matplotlib (QtAgg backend) for the plots, NumPy / scikit-learn for the
math. GPT-2 small (124 M) via HuggingFace `transformers` is the model
backbone for the two GPT-2 apps; GloVe 100 d is the data backbone for the
third.

**Run** (after `source ~/.venvDS/bin/activate`):

```bash
python workspace/GPT_arch_workshop.py
python workspace/attention_workshop.py
python workspace/embedding_workshop.py --fetch-glove   # one-time, ~862 MB zip
python workspace/embedding_workshop.py
```

---

## The three-workshop split

The three apps deliberately do *not* overlap. Each one carries a single
teaching beat; trying to cram them together dilutes all three.

| Workshop            | Scope                                            | Backbone       |
|---------------------|--------------------------------------------------|----------------|
| Embedding           | Meaning as direction in a clean word-level space | GloVe 100 d    |
| Attention / Q-K-V   | The *construction* of attention — one head       | GPT-2 small    |
| GPT architecture    | The *whole* forward pass, layer by layer         | GPT-2 small    |

A natural talk order is: **embedding → attention → architecture**. The
embedding workshop sets up "vectors encode meaning"; the attention
workshop zooms into how a single head mixes those vectors; the
architecture workshop zooms out to the stack of 12 blocks and shows the
residual stream evolving all the way to a next-token prediction.

Locked design decision: the embedding workshop uses GloVe **only**. No
GPT-2 `wte` side-by-side. GPT-2's anisotropic BPE embedding belongs to the
architecture workshop story, not the "meaning as direction" story.

---

## 1. Embedding Workshop — `embedding_workshop.py`

**Objective.** Make "a word is a direction in vector space" visible and
manipulable. Without this, the rest of the architecture is just matrix
multiplication.

### What the audience should walk away able to answer

1. Words are vectors — similar meanings sit close together (`cat` →
   `dog`, `kitten`, `pet`).
2. Categories form *clusters* in 2D; the geometry isn't accidental.
3. A pairwise cosine similarity matrix encodes *taxonomy* — you can
   literally see animal/building blocks.
4. Vector arithmetic recovers analogies: `king − man + woman ≈ queen`.
5. The choice of distance metric matters — cosine and Euclidean can rank
   neighbors differently.

### How it works

- **Backend (`EmbeddingBackend`).** Loads `glove.6B.100d` once — either
  from the plain-text file downloaded via `--fetch-glove` (HuggingFace
  mirror of the Stanford zip) or from the `.npz` cache built on first
  parse. Offers `vector`, `nearest`, `analogy`, `pca_2d`, `tsne_2d`,
  `pairwise_cosine`. PCA is refit on the *selected* words (not the whole
  400 k vocab) so the axes are tuned to what's on screen.
- **Left column (inputs).**
  - *Word groups* table — one row per category, `name | comma-separated
    words | color`. Defaults pre-fill two rows (e.g. animals vs
    constructions). "Update" recomputes the right column.
  - *Word inspector* — type a word, get the top-k nearest neighbors
    with cosine scores. Useful for "explore the vocabulary" moments.
  - *Analogy* — three fields for `A − B + C = ?`, pre-filled with
    `king − man + woman`. Shows top-k candidates.
  - *2D projection* dropdown: PCA (default, deterministic) or t-SNE
    (prettier separation, non-linear, stochastic with fixed seed).
  - *Cosine vs Euclidean* toggle — reveals the third right-column panel.
- **Right column (visuals).**
  - 2D scatter of all configured words, colored by category, labeled.
  - Pairwise cosine similarity heatmap, blocked by category.
  - (Toggleable) side-by-side cosine- vs Euclidean-ranked neighbors for
    a chosen anchor word.
- **Theory button.** An "ℹ Theory" dialog explains what GloVe is, how it
  was trained, and what "6B / 100d" means — so the demo isn't a magic
  trick.

### Why it's disconnected from GPT-2

GloVe is a clean, well-known, word-level embedding. GPT-2's `wte` is
BPE-tokenized and anisotropic (all vectors bunch along one axis), which
makes the classic word2vec demos come out wrong (`king − man + woman`
famously returns `king`, not `queen`). Telling both stories in one view
confuses both messages. The architecture workshop deals with GPT-2 wte
on its own terms.

---

## 2. Attention / Q-K-V Workshop — `attention_workshop.py`

**Objective.** Show the *mechanics upstream* of the attention heatmap —
how a single hidden state and a single bundled weight matrix produce the
Q, K, V vectors, the score row, the softmax, and the per-head output.
The architecture workshop already shows the *output* of attention;
this one shows the machinery that built it.

### What the audience should walk away able to answer

1. **Where do Q, K, V come from?** One bundled `c_attn` weight of shape
   `(768, 2304)` sliced into three `(768, 768)` blocks. Every token's
   hidden state is multiplied against them independently.
2. **What does "12 heads of dim 64" mean?** The 768-d output of W_Q / W_K
   / W_V is reshaped into 12 contiguous 64-d slices; one head sees only
   its own slice.
3. **Why does Q come from the query token but K/V come from all
   tokens?** Q asks "what am I looking for"; K and V answer for every
   token in context. Same hidden state, different roles, different
   matrices.
4. **What is the score row?** `Q · K_jᵀ / √64` for each key j, with
   causal masking on future tokens.
5. **What does softmax produce?** A weighted average over V vectors —
   that's the per-head output. After concatenation and `c_proj` over all
   12 heads, it becomes the residual delta added back to the stream.

### How it works

- **Backend (`ModelBackend`).** Loads GPT-2 small with
  `attn_implementation="eager"` and sets `output_attentions=True` on the
  config (sdpa refuses to expose weights; the kwarg-on-forward path is
  silently dropped as a "generation flag"). Captures two things by
  forward hook:
  - Input to each `block.attn.c_attn` — i.e. `ln_1(h_prev)`, the right
    hidden state to multiply against the split weights.
  - Output of each `block.attn` — i.e. the post-`c_proj` 768-d residual
    contribution for stage 7.
  `compute(prompt, layer, head, query_idx)` slices the chosen head's
  columns out of each W_{Q,K,V}, computes Q (1×64), K and V
  (seq×64), the score row, the causal mask, the softmax, and the
  per-head output. Also manually cross-checks the softmax against HF's
  reported attention — the worst absolute difference is shown in the
  status line as a sanity signal.
- **UI.** A scrollable vertical pipeline of seven fixed-height panels,
  one per stage:

  1. **Hidden state h_q** — 768-d input to attention for the query token.
  2. **Bundled c_attn weight** — schematic of `[W_Q | W_K | W_V]` with
     the chosen head's 64-column slice highlighted in each block.
  3. **Q, K, V** — Q (1×64), K and V (seq×64) as heatmaps.
  4. **Score row** — bar chart of `Q · K_jᵀ / √64`; causally masked
     positions are *greyed, not removed*, so the viewer sees what is
     being suppressed.
  5. **Softmax weights** — same x-axis as the score row, masked
     positions at 0, top-k annotated.
  6. **Per-head output** — `Σ_j α_j V_j`, shown as a 64-d vector.
  7. **Residual contribution** (toggleable, default off) — the
     post-`c_proj` 768-d vector that all 12 heads together add back to
     the residual stream.

- **Controls.** Prompt, layer (0-11), head (0-11), query token
  (combo of decoded BPE tokens), and a "Show c_proj output" toggle for
  the last panel.

### Design choices to keep in mind

- **Single-head focus in v1.** No compare-two-heads mode yet; picking
  different heads at the same layer is already a good teaching moment.
- **Biases omitted** from the visualization (a token-independent DC
  offset that would visually dominate without adding insight). A
  tooltip flags them.
- **Pipeline ends at the c_proj 768-d residual contribution**, behind a
  default-off toggle, so the v1 walkthrough stays focused on Q/K/V while
  still offering a bridge into the architecture workshop.

---

## 3. GPT Architecture Workshop — `GPT_arch_workshop.py`

**Objective.** "Putting it all together" — take an arbitrary prompt
through the entire GPT-2 forward pass and see the internals at any
layer, any head, in any of six views, with a top-k next-token bar
continuously reflecting the actual prediction.

### What the audience should walk away with

- A concrete feel for the *residual stream* as the thing that evolves
  across layers, not a static vector.
- An understanding of how each layer's attention + MLP deltas nudge
  that stream toward the next-token prediction.
- A sense of *where* the model "decides" — the logit-lens view makes
  this startlingly literal.
- Awareness of the attention-sink / position-0 artifact (a known GPT-2
  quirk that dominates naive plots — see the "Soften" toggle).

### How it works

- **Backend (`ModelBackend`, `ForwardResult`).** One forward pass per
  prompt change, caching hidden states (13 × seq × 768), attention
  weights (12 × 12 × seq × seq), MLP activations, per-layer
  attention and MLP residual deltas, logits, `ln_f`-normalized final
  states, and a pre-computed *logit lens* (top-1 token per layer,
  emergence curve for the final prediction).
- **Top bar.** Prompt field, "Live" checkbox (debounced 300 ms
  re-run on typing), "Run" button, "Arch" toggle for the companion
  architecture mini-map.
- **Left controls column.** Layer combo, head combo, **View** radio
  group (6 options below), PCA axis pickers (when the PCA view is
  active), "Soften pos-0 sink" checkbox, token list.
- **Six views** (main canvas, with the top-k bar chart sitting
  underneath):

  | View          | What it shows                                                            |
  |---------------|--------------------------------------------------------------------------|
  | Heatmap       | Selected layer's hidden state as (seq × dim) image, with vmax clipping   |
  | PCA           | Selected hidden state projected onto a vocab reference cloud, PC1..PC6   |
  | Cosine        | Pairwise cosine similarity (or raw attention) between token positions   |
  | Attention     | (head, seq, seq) attention matrix for the chosen layer and head          |
  | Logit lens    | Top-1 token per layer + emergence curve for the final prediction        |
  | Trajectory    | Cross-layer residual-stream path for one token, with attn/MLP deltas    |

- **Architecture mini-map** (`ArchitectureWindow`). A separate Qt window
  showing the 12-block transformer stack as clickable cells. Clicking a
  cell selects that layer in the main window; cross-layer views
  (logit lens, trajectory) ring *all* cells instead of highlighting one.

### Artifacts and mitigations worth knowing about

- **Position-0 attention sink.** GPT-2 uses position 0 as a dumping
  ground for attention mass that has no better target. This
  blows up defaults: naive `vmin/vmax` from `abs(data).max()` gets
  pinned to the outlier; PCA on raw hidden states finds "pos-0 or not"
  as PC1; norm plots need log-y. Mitigations baked into the app:
  per-token L2 normalization before PCA, `PowerNorm(γ=0.4)` on
  attention heatmaps, head variance computed on columns ≥ 1, and the
  "Soften pos-0 sink" checkbox that drops the pos-0 row/column and
  renormalizes.
- **HF `output_attentions` gotchas.** Passed as a forward kwarg it is
  silently dropped ("generation flag"); on the default `sdpa` backend
  it is refused outright. Fixed once, at model load:
  `attn_implementation="eager"` + `config.output_attentions = True`.
- **Post-hoc attention interpretation is weaker than it looks.**
  "Head X attends to Y, therefore it does Z" is *illustration*, not a
  causal claim. The app is a scanning tool; real mechanism claims need
  ablation or activation patching.

---

## How the three workshops relate

- The **embedding workshop** answers "why do vectors encode meaning at
  all". It's the foundation.
- The **attention workshop** answers "how does one head mix those
  vectors for one token at one layer". It zooms all the way in.
- The **architecture workshop** answers "and how does that repeat
  twelve times to produce a next-token prediction". It zooms all the
  way out.

Moving between them in a talk gives the audience a complete round trip
from concept (meaning as direction) through mechanism (Q, K, V, score,
softmax, output) to system (12-layer residual stream ending in a
prediction), without ever asking them to hold all three stories in their
head at once.

---

## Adding to the set

Each workshop has a locked plan next to it (`*_plan.md`) that documents
the design decisions and explicit non-goals. Before extending any
workshop, check its plan — many "obvious" features were considered and
declined on purpose (e.g. GPT-2 wte next to GloVe, compare-two-heads
mode in v1, logit-lens in the attention workshop). If a proposed
feature crosses scopes between workshops, surface the scope question
before building.
