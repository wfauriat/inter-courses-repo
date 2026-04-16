# LLM Mechanics — Visual Material Plan

**Goal:** Produce hands-on Python scripts that generate visualizations explaining LLM inner mechanics. One slide = one idea = one visualization. Material serves as a deeper reference; synthetic bits extracted for the talk.

---

## Topic inventory

| # | Topic | Status | Notes |
|---|-------|--------|-------|
| 0 | **Architecture spine (glue diagram)** | **planned** | **end-to-end data flow with dimensionality, "you are here" map** |
| 1 | Tokenization | planned | subword splits, tokenizer comparison, language bias |
| 2 | Embedding | planned | tokens as vectors, semantic clustering |
| 3 | Positional encoding | planned | order injection, sinusoidal pattern |
| 4 | Attention | planned | context-dependent weighting, multi-head |
| 5 | Feedforward layers (MLP) | planned | expand-compress, factual knowledge storage |
| 6 | Transformer block / architecture | planned | full block trace with tensor shapes |
| 8 | Next-token prediction | planned | probability distribution over vocabulary |
| 9 | Softmax, temperature & sampling | planned | distribution sharpness, UQ connection |
| 10 | Training objective (loss / gradient descent) | planned | cross-entropy, loss curves, overfitting |
| 10b | Training vs. inference compute | planned | parallel training vs. sequential generation |
| 12 | Supervised fine-tuning | planned | weight update on instruction/response pairs |
| 13 | RLHF / DPO (alignment) | planned | further weight update from preference signal |
| 14 | ICL & prompt engineering vs. fine-tuning | planned | input steering (frozen weights) vs. weight steering |

**Out of scope** (too deep for the intended level):

| # | Topic | Reason |
|---|-------|--------|
| 7 | Stacking depth & residual stream | implementation detail, covered enough by the spine diagram |
| 11 | Scaling laws | empirical deep-dive, not needed for intuition |
| 15 | Context window & KV cache | inference optimization plumbing |
| 16 | Hallucination | can be mentioned verbally, doesn't need its own mechanic slide |
| 17 | Compute tradeoff: latency vs. quality | absorbed into 10b at intuition level |

### How topics map onto the architecture

The spine diagram (topic 0) is the connective tissue. Every other topic is a zoom into a specific location on it:

- **Topics 1–9** → zoom into a specific stage of the forward pass (input → output)
- **Topic 10** → the training objective (what is minimized)
- **Topic 10b** → the compute loop that wraps around the architecture (how it is minimized, and how inference differs)
- **Topics 12, 13** → **modify the boxes** (update weight matrices, partially or fully)
- **Topic 14** → **modify the input arrow** (prepend tokens; weights frozen)

This gives a clean visual dichotomy for the talk:
- Forward pass: how data flows through fixed architecture
- Training / fine-tuning / alignment: how the weights inside the architecture are shaped
- ICL / prompting: how the input is shaped to steer a frozen architecture

---

## Models

| Model | Size | Fits in 8GB | Use for |
|-------|------|-------------|---------|
| GPT-2 small | 124M | trivially | topics 1–10 (main workhorse) |
| GPT-2 medium | 355M | easily | better quality where needed |
| TinyLlama-1.1B-Chat | 1.1B | yes (fp16) | SFT comparison (topic 12) |
| Phi-2 | 2.7B | yes (4-bit) | instruction-following demos |

Tokenizer comparison: GPT-2 BPE, Llama SentencePiece, tiktoken (cl100k).

---

## Shared example data

Curated sentences reused across scripts:

**General:**
- "The cat sits on the mat"
- "The dog chased the cat" / "The cat chased the dog"
- "To be or not to be, that is the question"

**UQ / Stats domain:**
- "Uncertainty quantification requires careful propagation of input distributions through complex models"
- "The posterior distribution captures our updated beliefs after observing data"
- "Monte Carlo simulation estimates expectations by averaging over random samples"

**Ambiguity / attention:**
- "The cat sat on the mat because it was tired"
- "The trophy doesn't fit in the suitcase because it is too big"
- "The trophy doesn't fit in the suitcase because it is too small"
- "The bank was steep" / "The bank was closed"

**French:**
- "L'incertitude est inhérente à toute modélisation"
- "Les grands modèles de langage transforment la pratique scientifique"

**Numbers / math:**
- "The value of pi is 3.14159265"
- "If x = 3 and y = 7, then x + y ="

**Code:**
- "def compute_posterior(prior, likelihood):"

**Corpus:** Shakespeare from HuggingFace `datasets` (for training demos).

---

## Comparative reference: ~850-word LLM-generated explanation

*Note: this is LLM output (Claude), kept here as a comparative target for the speaker's own version. Not intended for direct use.*

### The core task: next-token prediction

An LLM does one thing: given a sequence of text, predict a probability distribution over what comes next. The entire edifice — billions of parameters, months of training, millions of dollars — serves this single objective. Everything else (answering questions, writing code, reasoning) *emerges* from doing this one thing extremely well on an enormous quantity of text.

### Tokens: how text enters the model

The model doesn't see characters or words. Text is first split into *tokens* — subword units from a learned vocabulary (typically 30,000–100,000 entries). Common words like "the" are single tokens. Rarer words get split: "uncertainty" might become ["un", "certain", "ty"]. Numbers are split digit by digit. The model literally cannot see a number as a number — it processes fragments.

This splitting is language-biased. English text is efficiently tokenized; French requires more tokens for the same content — directly affecting cost and how much text fits in a single pass.

### From tokens to vectors: embeddings

Each token is mapped to a vector in high-dimensional space (768 to 12,000+ dimensions). This mapping is learned: tokens with similar usage patterns end up geometrically close. "Probability" and "likelihood" sit nearby; "cat" and "refrigerator" do not.

### The transformer: how context flows

The model needs to understand that "it" in *"The cat sat on the mat because it was tired"* refers to the cat, not the mat. This is the job of *attention*.

Attention lets each token look at every other token and assign a learned, context-dependent weight. "Bank" in *"the river bank"* attends to "river"; in *"the bank closed"* it attends to "closed." Same word, different attention pattern, different resulting representation.

A *transformer block* pairs attention (gathering relevant context) with a feedforward network (transforming the gathered information). The model stacks many such blocks — 12 to over 100. Each layer refines the representation: early layers capture syntax, later layers capture meaning and facts.

After the final layer, scores are computed for every token in the vocabulary, then converted to probabilities via *softmax*.

### Temperature: a knob on confidence

Softmax has a parameter called *temperature*. Low temperature (0.1): the distribution is sharp, nearly deterministic — the model picks the most likely token. High temperature (2.0): the distribution flattens — the model becomes more random, more "creative." This is the most direct lever on the uncertainty of the output, and the reason the same prompt can produce different answers.

### Training: learning to predict

Take a massive corpus (books, web, code — trillions of tokens). At each position, the model predicts the next token. The error — how far the predicted distribution was from the actual token — is propagated backward through the entire architecture via automatic differentiation, and all parameters are adjusted by gradient descent.

Critical asymmetry: during training, all positions in a sequence are processed *in parallel* (the correct answers are known — teacher forcing). Training is embarrassingly parallel. Generation, by contrast, is *sequential*: token t+1 depends on token t. This is why training leverages massive GPU clusters efficiently, while generation is bottlenecked by latency.

After pre-training, the model is a powerful text completer — but not a useful assistant. Given "What is 2+2?", it continues with "What is 2+3? What is 3+3?..." rather than answering "4."

### From text completer to assistant

Two additional training stages reshape the model:

*Supervised fine-tuning (SFT)*: train on curated (instruction, response) pairs. Same architecture, same process — but the data is formatted as conversations. The model learns to *answer* rather than *continue*.

*Alignment (RLHF / DPO)*: humans rank multiple responses to the same prompt; the model is trained to prefer higher-ranked ones. This teaches preferences — helpfulness, safety, honesty — that example pairs alone cannot capture. For a decision-theory audience: alignment is optimizing a learned utility function over responses.

Both stages modify the model's weights. The architecture is unchanged.

### Using the model: prompting vs. fine-tuning

Two fundamentally different ways to steer behavior:

*Prompting (in-context learning)*: prepend instructions or examples to the input. Weights don't change — you exploit attention's ability to condition on whatever is in the input. Fast, flexible, temporary.

*Fine-tuning*: further train the weights on task-specific data. Permanent, requires compute, but produces more reliable specialization.

The tradeoff: prompting is cheap and reversible but fragile; fine-tuning is expensive but durable.

### What this means

An LLM is a next-token predictor trained on enough text to develop internal representations of language, facts, and reasoning — then shaped into usefulness through fine-tuning and alignment. It has no explicit model of truth, no database, no reasoning engine. What it has is a very powerful capacity to produce plausible continuations, which at sufficient scale looks remarkably like understanding.

---

## Per-topic example plan

### 0. Architecture spine (glue diagram)

**What to show:** The full end-to-end data flow of a decoder-only transformer (GPT-2), with dimensionality tracked at every stage. Each topic maps to a specific location on this spine.

**Data flow (GPT-2 small, d_model=768, 12 heads, 12 layers, vocab=50257):**

```
Input text                          "The cat sits"
    |
    v
Tokenizer                          [464, 3797, 13015]          <- topic 1
    |                               shape: (seq_len,)
    v
Embedding table                     look up each ID             <- topic 2
    |                               shape: (seq_len, 768)
    v
+ Positional encoding               added to embeddings         <- topic 3
    |                               shape: (seq_len, 768)
    v
+-----------------------------+
| Transformer block  (x12)   |                                 <- topic 6
|                             |
|  LayerNorm                  |     (seq_len, 768)
|       v                     |
|  Multi-Head Attention       |     (seq_len, 768)              <- topic 4
|       v                     |
|  + Residual                 |     (seq_len, 768)              <- topic 7
|       v                     |
|  LayerNorm                  |     (seq_len, 768)
|       v                     |
|  FFN: 768->3072->768        |     expand then compress        <- topic 5
|       v                     |
|  + Residual                 |     (seq_len, 768)              <- topic 7
+-----------------------------+
    |
    v
Final LayerNorm                     (seq_len, 768)
    |
    v
Linear projection to vocab          (seq_len, 50257)            <- topic 8
    |
    v
Softmax (with temperature)          probabilities               <- topic 9
    |
    v
Next token                          " on"
```

**Mapping to training / steering (visual overlay):**
- Topics 12, 13 (SFT, RLHF): highlight the boxes — weights inside are updated
- Topic 14 (ICL): highlight the input arrow — tokens prepended, weights frozen

**Visualization:** Programmatic diagram (matplotlib) with boxes, arrows, dimension annotations. Designed to be re-shown with different zones highlighted as each topic is introduced.

---

### 1. Tokenization

**What to show:** Same text split differently by different tokenizers. Subword splitting is non-obvious and has consequences (cost, context window, language bias).

**Sentences:**
- "The cat sits on the mat" — trivial baseline, tokens ~ words
- "Uncertainty quantification in computational mechanics" — domain text, splits on long words
- "L'incertitude est inhérente à toute modélisation" — French, more tokens = English-centric bias
- "3.14159265" — numbers tokenized in arbitrary chunks
- "def compute_posterior(prior, likelihood):" — code tokenization

**Compare:** GPT-2 BPE vs. Llama SentencePiece vs. tiktoken (cl100k).

**Visualization:** Colored boxes per token, token IDs below, token count comparison across tokenizers.

---

### 2. Embedding

**What to show:** Tokens become vectors in high-dimensional space. Semantic similarity = geometric proximity.

**Word groups:**
- Stats/UQ: probability, uncertainty, variance, distribution, likelihood, posterior
- Animals: cat, dog, fish, bird
- Royalty: king, queen, prince, princess
- Verbs: compute, estimate, simulate, predict

**Also:** king - man + woman ~ queen arithmetic on GPT-2 embedding table.

**Visualization:** 2D PCA/t-SNE scatter plot colored by semantic group. Vector arithmetic as arrows.

---

### 3. Positional encoding

**What to show:** Without position, "dog bites man" = "man bites dog". Position must be injected.

**Sentences:**
- "The dog chased the cat" vs. "The cat chased the dog"

**Two visuals:**
- Sinusoidal positional encoding matrix — wave pattern across positions x dimensions
- GPT-2 predictions with vs. without positional encodings — collapse to nonsense

**Visualization:** Heatmap of positional encoding matrix (position on y-axis, dimension on x-axis).

---

### 4. Attention

**What to show:** Each token attends to other tokens with learned, variable weights. This is how context flows.

**Sentences:**
- "The cat sat on the mat because it was tired" — "it" attends to "cat"
- "The trophy doesn't fit in the suitcase because it is too big" vs. "...too small" — Winograd pair, "it" attention shifts
- "The bank was steep" vs. "The bank was closed" — word sense via context

**Model:** GPT-2 small, extract attention weights from all heads.

**Visualization:** Attention heatmap (token x token). Bipartite lines from "it" to other tokens. Multiple heads side-by-side.

---

### 5. Feedforward layers (MLP)

**What to show:** Attention gathers context; FFN transforms it. The 4x expand-then-compress bottleneck. Where factual associations are stored.

**Example:**
- "The capital of France is" — hidden states before vs. after FFN
- Shape: 768 -> 3072 -> 768 in GPT-2
- Neuron activations: specific neurons fire for "Paris"/"France" across different sentences

**Visualization:** Expansion/compression schematic. Activation heatmap for selected neurons across ~10 inputs.

---

### 6. Transformer block / architecture

**What to show:** One block = LayerNorm -> Attention -> Residual Add -> LayerNorm -> FFN -> Residual Add. Full model = N stacked blocks.

**Example:** Trace "The cat" through one GPT-2 block:
- Input: (1, 2, 768)
- After attention: (1, 2, 768)
- After FFN: (1, 2, 768)
- Residual connections: input is added back, not replaced

**Visualization:** Block diagram with real tensor shapes from GPT-2. Programmatically generated, not hand-drawn.

---

### 8. Next-token prediction

**What to show:** The model's only task — predict probability distribution over the next token. Everything emerges from this.

**Prompts:**
- "The capital of France is" — peaked (Paris dominates)
- "The uncertainty in the measurement is" — broader distribution
- "To be or not to be, that is the" — very peaked (question)
- "The value of pi is 3.1" — numerical continuation

**Also:** Autoregressive generation step by step — branching tree of possibilities.

**Visualization:** Top-20 bar chart of next-token probabilities. Branching tree (3 steps, top-3 per step).

---

### 9. Softmax, temperature & sampling

**What to show:** Same logits, different temperature = different distribution sharpness. A knob on the model's "confidence". Direct UQ connection.

**Example:** Logits from "The capital of France is" at:
- T=0.1 — nearly deterministic
- T=0.5 — confident with some spread
- T=1.0 — default
- T=2.0 — flat, creative

**Also:** Same prompt generated 10x at T=0.3 vs. T=1.5 — diversity of completions.

**Visualization:** Overlaid probability distributions at different temperatures on same axes.

---

### 10. Training objective (loss / gradient descent)

**What to show:** Cross-entropy loss on a concrete example. Training = making the model assign higher probability to the correct next token.

**Example:**
- Concrete: P("Paris")=0.02 at step 0 -> loss=3.9. After training, P("Paris")=0.85 -> loss=0.16.
- Fine-tune GPT-2 small on Shakespeare (~1MB), log loss every N steps.
- Show overfitting: training loss drops, validation loss turns up.

**Visualization:** Loss curve (train + val) over steps. Side panels: predicted distribution at step 0, 500, 2000.

---

### 10b. Training vs. inference compute

**What to show:** Training wraps around the architecture as an outer loop and is parallelizable. Inference (generation) is sequential — one token at a time. This is the fundamental asymmetry.

**Training (parallel):**
```
for each batch of (input, target) pairs:
    forward pass (all positions at once — teacher forcing)
    compute loss at every position
    backward pass (autograd computes gradients)
    update weights (gradient descent)
```

- All target tokens are known upfront → all positions computed in one pass
- Multiple sequences batched together → second axis of parallelism
- Autograd: PyTorch records the forward computation, reverses it automatically for gradients

**Inference / generation (sequential):**
```
for each new token:
    run the architecture on everything so far
    get probability distribution for next token
    sample one token
    append and repeat
```

- Token t+1 depends on token t → cannot be parallelized
- This is why generating text is slow compared to processing a prompt of the same length

**Visualization:** Side-by-side schematic — training processes a full grid (positions × batch) at once; generation extends one cell at a time.

---

### 12. Supervised fine-tuning

**What to show:** Base model does pattern completion. SFT model follows instructions. Same architecture, different training data format.

**Example:**
- Prompt: "What is the capital of France?"
  - GPT-2 base -> "What is the capital of Germany? What is..." (pattern completion)
  - Instruction-tuned (TinyLlama-Chat) -> "Paris" (answers)

**Visualization:** Side-by-side generated text. Top-5 token probability comparison.

---

### 13. RLHF / DPO (alignment)

**What to show:** Alignment teaches preferences, not format. Training signal = "this response is better than that one." Reward model as utility function (decision theory connection for this audience).

**Example:**
- Preference pair: same prompt, chosen vs. rejected response
- RLHF pipeline diagram: SFT model -> generate pairs -> human ranking -> reward model -> PPO
- Reward scores for a set of responses before/after alignment

**Visualization:** Pipeline diagram. Preference pair comparison. Reward score distributions.

---

### 14. ICL & prompt engineering vs. fine-tuning

**What to show:** Two ways to steer a model — changing the input vs. changing the weights. Fundamentally different tradeoffs.

**Task:** Sentiment classification.

**Examples:**
- Zero-shot: "Classify the sentiment: 'Great movie!' ->"
- One-shot: add one labeled example
- Few-shot: 2, 4, 8 examples
- Fine-tuned: GPT-2 fine-tuned on ~100 sentiment examples

**Visualization:** Accuracy vs. number of examples (ICL vs. fine-tuning). Tradeoff table: compute, data needs, flexibility, persistence.
