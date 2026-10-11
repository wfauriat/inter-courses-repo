# LLM Mechanics — Visualization Workspace

**Created:** 2026-04-16
**Purpose:** Hands-on Python scripts generating matplotlib visuals explaining LLM inner mechanics. One script = one topic = one or more slide-ready figures. Material supports a vulgarization talk for UQ/StatsML peers.

**Model:** GPT-2 small (124M) — main workhorse for all model-based scripts.
**Venv:** `~/.venvDS/bin/activate` (torch, transformers, scikit-learn, matplotlib, tiktoken, etc.)
**Run:** `source ~/.venvDS/bin/activate && python <script>.py` — PNGs go to `output/`.

---

## Project structure

```
workspace/
├── shared/
│   ├── __init__.py          # re-exports data + viz helpers
│   ├── data.py              # curated example sentences, word groups, prompts
│   └── viz.py               # matplotlib style, save_fig(), COLOR_PALETTE
├── output/                  # generated PNGs (33 files)
├── 00_architecture_spine.py
├── 01_tokenization.py
├── 02_embedding.py
├── 03_positional_encoding.py
├── 04_attention.py
├── 05_feedforward.py
├── 06_transformer_block.py
├── 08_next_token_prediction.py
├── 09_softmax_temperature.py
├── 10_training_objective.py
├── 10b_training_vs_inference.py
├── 12_supervised_finetuning.py
├── 13_rlhf_alignment.py
└── 14_icl_vs_finetuning.py
```

---

## Script inventory

### 00_architecture_spine.py (no GPU)
End-to-end data flow diagram of GPT-2 small (decoder-only transformer). Boxes with dimension annotations at every stage: input text → tokenizer → embedding (seq, 768) → +positional → 12× transformer blocks → layernorm → linear projection (seq, 50257) → softmax → next token.
- **Output:** `00_architecture_spine.png`

### 01_tokenization.py (tokenizer only)
Shows how text is split into subword tokens. 5 sentences (English, French, numbers, code) shown as colored boxes with token IDs. Compares GPT-2 BPE vs tiktoken cl100k_base on the same sentence.
- **Outputs:** `01_tokenization_splits.png`, `01_tokenization_comparison.png`

### 02_embedding.py (model weights, needs scikit-learn)
Extracts GPT-2 token embeddings, projects to 2D via PCA. Scatter plot of 4 semantic word groups (stats, animals, royalty, verbs). Vector arithmetic: king - man + woman (note: result is "king" not "queen" with raw GPT-2 embeddings — known limitation vs dedicated word2vec).
- **Outputs:** `02_embedding_clusters.png`, `02_embedding_arithmetic.png`

### 03_positional_encoding.py (inference)
Heatmap of GPT-2's learned positional embeddings (128 positions × 64 dims, RdBu colormap). Effect demo: different next-token predictions for "The dog chased the cat..." vs "The cat chased the dog..." — same tokens, different order.
- **Outputs:** `03_positional_heatmap.png`, `03_positional_effect.png`

### 04_attention.py (inference)
2×2 grid of attention heatmaps (4 highest-variance heads from layer 5). Coreference: what "it" attends to in "The cat sat on the mat because it was tired" — auto-selects best layer. Winograd pair comparison: "too big" vs "too small" shifts attention target.
- **Outputs:** `04_attention_heatmap.png`, `04_attention_coreference.png`, `04_attention_winograd.png`

### 05_feedforward.py (inference)
FFN expand/compress shape schematic (768→3072→768). Neuron activation heatmap: 50 highest-variance neurons across 8 sentences, captured via forward hook on layer 8's MLP.
- **Outputs:** `05_ffn_shape.png`, `05_ffn_activations.png`

### 06_transformer_block.py (inference)
Detailed block diagram of one transformer block with tensor shapes, residual skip connections, Q/K/V projections. Residual evolution: cosine similarity to final layer at each of the 12 layers (line chart + heatmap across all tokens).
- **Outputs:** `06_transformer_block.png`, `06_residual_evolution.png`

### 08_next_token_prediction.py (inference)
Top-20 next-token probability bar charts for 4 prompts (peaked vs broad distributions). Autoregressive generation tree from "The cat" — 3-step branching with top-3 tokens at each step.
- **Outputs:** `08_next_token_topk.png`, `08_next_token_tree.png`

### 09_softmax_temperature.py (inference + generation)
Same logits at T=0.1/0.5/1.0/2.0 as 2×2 bar chart grid and overlay plot. 8 generations at T=0.3 vs T=1.5 shown side-by-side — diversity effect.
- **Outputs:** `09_temperature_bars.png`, `09_temperature_overlay.png`, `09_temperature_generations.png`

### 10_training_objective.py (no GPU, synthetic data)
Concrete cross-entropy loss: simulated before/after distributions for "capital of France". Synthetic training + validation loss curves with overfitting annotation. 2D gradient descent trajectory on a Rosenbrock-variant loss surface.
- **Outputs:** `10_loss_concrete.png`, `10_loss_curve.png`, `10_gradient_descent.png`

### 10b_training_vs_inference.py (no GPU, diagrams)
Side-by-side schematic: training grid (batch × positions, all at once) vs generation (sequential, one token at a time). Circular training loop flowchart: data → forward → loss → backward (autograd) → optimizer → repeat.
- **Outputs:** `10b_parallel_vs_sequential.png`, `10b_training_loop.png`

### 12_supervised_finetuning.py (inference + generation)
3 prompts: GPT-2 base completions vs hardcoded instruction-tuned responses side-by-side. SFT training data format: 3 instruction/response card pairs. Top-10 next-token probabilities showing base model predicts continuation, not answers.
- **Outputs:** `12_sft_comparison.png`, `12_sft_training_format.png`, `12_sft_probability_shift.png`

### 13_rlhf_alignment.py (no GPU, diagrams + synthetic)
3-stage RLHF pipeline flowchart (SFT → Reward Model → Policy Optimization). 3 preference pair cards (chosen vs rejected). Synthetic reward score distributions before/after alignment.
- **Outputs:** `13_rlhf_pipeline.png`, `13_rlhf_preference_pairs.png`, `13_rlhf_reward_shift.png`

### 14_icl_vs_finetuning.py (inference)
Zero/one/few-shot sentiment classification with GPT-2 — bar charts of next-token predictions showing ICL effect. Tradeoff comparison table (6 axes). Side-by-side architecture spines: ICL highlights input arrow (frozen weights) vs fine-tuning highlights model boxes (updated weights).
- **Outputs:** `14_icl_fewshot.png`, `14_icl_vs_ft_tradeoffs.png`, `14_icl_vs_ft_architecture.png`

---

## Known issues

1. **02_embedding arithmetic:** king - man + woman → "king" (not "queen"). Raw GPT-2 token embeddings don't reproduce the classic word2vec demo cleanly. Visualization still illustrates the concept.
2. **09_softmax_temperature:** harmless `tight_layout` warning.
3. **All model scripts:** HF Hub warning about unauthenticated requests — cosmetic, models still download/load fine.

---

## What's NOT here (out of scope)

- Topic 7 (stacking/residual stream) — absorbed into topic 6
- Topic 11 (scaling laws) — too deep
- Topic 15 (context window / KV cache) — inference plumbing
- Topic 16 (hallucination) — verbal, not a mechanics slide
- Topic 17 (latency vs quality tradeoff) — absorbed into topic 10b
