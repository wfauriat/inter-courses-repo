# Large Language Models: A Primer
### From Words and Numbers to Thinking Machines

*A synthetic overview for the scientifically literate non-specialist.*

---

## Preface

Large Language Models (LLMs) have become one of the most consequential technologies of the decade. They write code, summarize documents, answer questions, translate languages, generate images, and increasingly act as autonomous assistants. Yet most public discussion oscillates between magical thinking and dismissive debunking, with little in the way of a grounded, honest account of what these systems actually are, how they work, and where they genuinely fall short.

This primer aims to fill that gap. It assumes you are comfortable with basic scientific reasoning and have some background in statistics or computing, but does not assume you have ever trained a neural network. The goal is not a full technical treatment — the full course this distills runs to several hundred pages — but a sufficiently honest and complete picture that you can reason about LLMs without being misled.

---

## 1. The Core Problem: Language as Numbers

Every computational system ultimately operates on numbers. Language, by contrast, is a sequence of discrete symbols: characters, words, sentences. The first challenge in building language-understanding systems is deciding how to bridge this gap.

### 1.1 The Naive Approach: Counting Words

The simplest representation of a document is a vector of word counts — a Bag of Words (BoW). Give each word in your vocabulary a dimension, and count how many times it appears. A document about finance will have high counts for "market", "interest", and "rate"; one about biology will have high counts for "cell", "protein", and "gene".

This works surprisingly well for coarse tasks like topic classification. But it loses almost everything important about language: the order of words ("dog bites man" and "man bites dog" are identical), their meaning in context ("bank" by a river is not "bank" for money), and the relationship between words ("car" and "automobile" are orthogonal dimensions despite meaning the same thing).

TF-IDF (Term Frequency — Inverse Document Frequency) is a refinement: rather than raw counts, it weights each word by how distinctive it is across documents. Words that appear everywhere ("the", "is") get low weight; words that concentrate in specific documents get high weight. Better signal, but the same fundamental limitations.

### 1.2 Word Embeddings: Semantic Geometry

The breakthrough insight came from distributional linguistics: *a word is characterized by the company it keeps*. If "bank" and "shore" both tend to appear near "river", "water", and "fish", they probably share semantic content. This is the foundation of word embeddings.

**Word2Vec** (Mikolov et al., 2013) turns this into a learning objective. For every word in a large corpus, train a neural network to predict which words tend to appear in the same neighborhood. The network is forced to develop compact representations — low-dimensional vectors of perhaps 100 to 300 numbers — that are efficient enough to perform this prediction well.

The result is remarkable. Semantically similar words end up near each other in this embedding space (measured by cosine similarity). More strikingly, *relationships between words are encoded as directions*:

```
vec("king") - vec("man") + vec("woman") ≈ vec("queen")
vec("Paris") - vec("France") + vec("Germany") ≈ vec("Berlin")
```

This tells us that the "royalty" direction and the "capital city" direction are consistent geometric patterns in the learned space. The model was never told these relationships — they emerged from the statistics of text.

**GloVe** (Pennington et al., 2014) achieves similar results by a different route: instead of training on local windows, it factorizes the global co-occurrence matrix — a table counting how often each pair of words appears near each other across the entire corpus. Both methods produce embeddings of comparable quality on downstream tasks.

### 1.3 The Problem with Static Embeddings

Despite their elegance, these representations have a fundamental flaw: each word has a single fixed vector, regardless of context. "Bank" gets one vector for all its uses. This is called the *polysemy problem*, and it is not a minor inconvenience — it limits the expressiveness of any system built on these representations.

There is also the *out-of-vocabulary* problem: words not seen during training have no representation at all. New technical terms, proper names, and neologisms are invisible to the model.

Partial solutions exist — representing words as sums of their subword fragments (FastText), for instance — but the deep solution requires a different architecture entirely.

### 1.4 Tokenization: The Vocabulary Contract

Before any representation can be learned, raw text must be broken into discrete units. The choice of units defines the model's vocabulary.

Characters are too granular — they produce very long sequences and carry little semantic information individually. Words are too coarse — the vocabulary balloons to millions of entries for multilingual or technical text, and new words are always appearing.

Modern LLMs use **subword tokenization**: break words into fragments of varying length according to their frequency in the training corpus. Common words become single tokens ("the", "and", "language"); rare words split into smaller pieces ("tokenization" → "token" + "ization"). The **Byte Pair Encoding (BPE)** algorithm achieves this by iteratively merging the most frequent adjacent pairs in a corpus until a target vocabulary size is reached (typically 30,000–100,000 tokens).

A crucial variant, **byte-level BPE** (used in GPT-2 and most modern models), starts from the 256 possible bytes rather than characters. This guarantees that any possible text can be tokenized — no word is ever "out of vocabulary". The vocabulary then consists of those 256 bytes plus approximately 50,000 learned merges.

This tokenization step has non-obvious consequences. Numbers are tokenized inconsistently: "1234" might become ["12", "34"] in one model and ["1", "234"] in another, which partially explains why LLMs struggle with arithmetic. Non-English scripts get fragmented into more tokens than equivalent English text, effectively shortening their available context window. These are not bugs — they are consequences of the statistics of training data.

---

## 2. The Transformer: How Modern LLMs Actually Work

### 2.1 What Came Before, and Why It Failed

Before 2017, language tasks that required understanding sequences were dominated by **Recurrent Neural Networks (RNNs)**. An RNN reads a sequence one token at a time, updating an internal hidden state at each step. In an encoder-decoder setup (for translation, say), the encoder processes the source sentence into a single fixed-size vector — the "context" — and the decoder reads that vector to generate the output.

This suffers from three severe problems:

**Vanishing gradients.** Training requires backpropagating error signals through every time step. For sequences of hundreds of tokens, gradients decay to near-zero exponentially quickly, making it nearly impossible to learn dependencies between tokens far apart. Long Short-Term Memory networks (LSTMs) help, but cannot fully solve the problem.

**Sequential bottleneck.** Step *t* cannot be computed until step *t−1* is done. Modern GPUs thrive on massive parallelism; an RNN of sequence length 512 requires 512 sequential operations, leaving most of the hardware idle.

**Fixed-size context.** Compressing an entire paragraph into one vector before the decoder ever sees it is lossy. Important information gets overwritten.

### 2.2 Attention: The Core Idea

The solution to all three problems came from a deceptively simple idea: rather than compressing the source into one vector, let the decoder *selectively attend* to any part of the source at each decoding step.

**Bahdanau et al. (2014)** introduced this for machine translation. At each decoding step, a small network computes a relevance score between the current decoder state and each encoder hidden state. The scores are normalized (via softmax) into weights summing to 1, and the decoder receives a weighted average of all encoder states — a "context vector" that focuses on whatever part of the source is most relevant right now.

This is powerful because:
- The decoder can look at any source position directly (no gradient bottleneck)
- The weight distribution is interpretable (it shows which source words the decoder attends to)
- It degrades gracefully with length

**Vaswani et al. (2017)** — "Attention Is All You Need" — generalized this idea into a purely attention-based architecture, eliminating recurrence entirely. Their formulation uses three matrices: **Queries** (what we're looking for), **Keys** (what each position offers), and **Values** (what each position contains):

$$\text{Attention}(Q, K, V) = \text{softmax}\!\left(\frac{QK^T}{\sqrt{d_k}}\right) V$$

Think of it as a **soft dictionary lookup**: the query finds the most relevant keys (by dot product similarity), and the output is a weighted blend of the corresponding values. The scaling by $\sqrt{d_k}$ prevents the dot products from growing so large that the softmax saturates into a near-one-hot distribution, which would prevent learning.

This operation is now the heart of virtually every large language model.

### 2.3 Multi-Head Attention

A single attention operation computes one type of similarity. Language is richer than that — a word relates to others syntactically (subject-verb agreement), semantically (synonyms, antonyms), and positionally (proximity).

**Multi-head attention** runs several attention operations in parallel, each on lower-dimensional projections of the same input. Each "head" can specialize in a different type of relationship. Their outputs are concatenated and projected back to the original dimension.

Empirically, different heads learn interpretable roles: in BERT, some heads track syntactic dependencies, others track coreference, others detect sentence boundaries. This specialization is not designed in — it emerges from gradient descent.

### 2.4 Positional Encodings

Attention has no inherent notion of order. Given the same tokens in different order, scaled dot-product attention produces the same set of outputs (mapped differently, but same content). "The cat ate the fish" and "the fish ate the cat" would be indistinguishable without positional information.

Positional encodings inject order into the model. The original Transformer used sinusoidal functions of different frequencies, added to each token embedding before processing. Think of it as a unique fingerprint for each position: low-frequency channels change slowly across positions (encoding long-range position), high-frequency channels change rapidly (encoding fine-grained position). No parameters needed.

Modern models use **Rotary Position Embeddings (RoPE)**: instead of adding position information to embeddings, the query and key vectors are *rotated* in 2D subspaces according to their positions. The elegant property is that the dot product between a rotated query at position *m* and a rotated key at position *n* depends only on their *relative distance* (*m − n*), not on their absolute positions. This generalizes better to sequences longer than the training length and is now the standard in most open-source models (LLaMA, Mistral, Falcon).

### 2.5 The Transformer Block

The Transformer processes sequences through a stack of identical blocks. Each block has two components:

**Multi-Head Attention** — routes and mixes information between positions. Any token can attend to any other token in a single step, enabling direct long-range dependencies.

**Feed-Forward Network (FFN)** — a two-layer neural network applied independently to each token's representation. This is the "thinking" component: it transforms each token's representation nonlinearly, allowing the model to compute complex functions of the contextual information gathered by attention. The FFN expands the representation to 4× the model dimension internally, then contracts it back. Recent research suggests FFN layers act as *key-value memories* — storing and retrieving factual associations.

Both components are wrapped with **residual connections** (the input is added to the output, so gradients can flow through the entire stack without passing through any nonlinearity) and **layer normalization** (stabilizing training by keeping the scale of activations in check).

The stack of *N* such blocks is the Transformer. Deeper models learn more abstract, higher-level representations. Modern LLMs use 24 to 96 or more blocks.

### 2.6 Three Architectures Built on the Same Block

The basic Transformer block can be assembled in three ways, each suited to different tasks:

**Encoder-only (BERT-style):** Every token attends to every other token (bidirectional). No constraint on the order of information flow. Produces a rich contextual representation of the input. Best for tasks requiring understanding of a fixed input: classification, named entity recognition, semantic similarity. BERT, RoBERTa, DeBERTa.

**Decoder-only (GPT-style):** Each token may only attend to previous tokens (causal masking). This forces the model to predict each token from the past alone. The training objective is simple and powerful: predict the next token. Best for generation: language modeling, text completion, instruction following, reasoning. GPT, LLaMA, Mistral, Claude, Gemini.

**Encoder-Decoder (T5/BART-style):** An encoder processes the input bidirectionally; a decoder generates the output causally, attending to both previous outputs and encoder states via *cross-attention*. Best for tasks with distinct input and output: translation, summarization, question answering. T5, BART, mT5.

The dominant paradigm in modern large models is decoder-only. A sufficiently large causal language model, prompted appropriately, can perform classification, extraction, translation, and summarization — everything the specialized architectures do — plus generation, reasoning, and instruction following. One architecture, trained to predict the next token, becomes a general-purpose system.

---

## 3. Pre-training: Learning from Text at Scale

### 3.1 The Self-Supervised Paradigm

Neural networks need supervision — some signal that says whether their output was right or wrong. For most of the history of machine learning, this meant labeled datasets: human-annotated examples matching inputs to outputs. Such datasets are expensive and limited.

Language models exploit a crucial observation: **text is its own label**. Given any document, you can ask the model to predict the next word at each position. The ground truth is simply the word that actually appears in the text. No annotation needed — the training signal is implicit in the structure of the data itself.

This is **self-supervised learning**, and it scales with the amount of text available. The internet contains trillions of words across every domain and language. Pre-training on this data teaches the model implicit statistical models of grammar, factual knowledge, reasoning patterns, and the structure of discourse — all from predicting the next token.

### 3.2 Two Main Objectives

**Causal Language Modeling (CLM, GPT-style):** Predict token *t* from tokens 1 through *t−1*. The model sees text from left to right. Training is simple — feed in a sequence, compare the model's predicted probability distribution at each position to the actual next token via cross-entropy loss, and backpropagate. At generation time, the model samples from its own output distribution, feeding each generated token back as input for the next step. This is **autoregressive generation**.

**Masked Language Modeling (MLM, BERT-style):** Randomly mask ~15% of tokens in the input and train the model to predict the masked tokens from the surrounding context. Because the model sees both left and right context, it develops richer bidirectional representations. The trade-off: at generation time, you cannot simply sample from the model — it was never trained to generate sequences.

### 3.3 Scale: The Key Variable

A central finding of the past decade is that model capability scales remarkably smoothly with size. Bigger models trained on more data are better — not just incrementally, but qualitatively.

The **Chinchilla scaling laws** (Hoffmann et al., 2022) give a practical rule of thumb: to train a model optimally, the number of training tokens should be roughly 20 times the number of model parameters. A 7B-parameter model needs ~140 billion tokens. A 70B model needs ~1.4 trillion. These numbers imply that many large models have been under-trained relative to their size — the same compute budget would be better spent on a smaller model trained on more data.

Scale also produces **emergent capabilities**: abilities that appear somewhat suddenly as models cross certain size thresholds, and are not predictable by smoothly extrapolating from smaller models. Multi-step arithmetic, code generation, and coherent long-form reasoning are all examples. Smaller models fail entirely; models above roughly ~10–100B parameters succeed. Why this discontinuity exists is not fully understood.

### 3.4 The GPT Family

**GPT-1** (2018): 117M parameters, trained on BooksCorpus. Demonstrated that unsupervised pre-training followed by supervised fine-tuning outperformed task-specific architectures across many NLP benchmarks.

**GPT-2** (2019): 1.5B parameters, trained on WebText. Introduced byte-level BPE, Pre-LayerNorm (normalizing before rather than after attention, for training stability), and demonstrated zero-shot capabilities — performing tasks from natural language instructions with no task-specific training at all.

**GPT-3** (2020): 175B parameters, trained on a filtered crawl of the web plus books and Wikipedia. The landmark demonstration of **in-context learning**: given a few examples of a task within the prompt (the "context"), the model could generalize to new instances — all without any gradient update. This fundamentally changed how people thought about model deployment.

**LLaMA** (Meta, 2023–2024): Open-weights models that democratized access to strong LLM capabilities. LLaMA incorporated several architectural refinements now standard across the field:

- **RMSNorm** instead of LayerNorm: removes mean-centering, ~15% faster, equivalent quality
- **SwiGLU** activation in FFN: a gated nonlinearity that empirically outperforms GELU, especially on mathematical tasks
- **RoPE** for positional encoding (as described above)
- **Grouped Query Attention (GQA)**: reduces memory during inference by sharing key/value projections across groups of attention heads, enabling larger batch sizes or longer sequences

---

## 4. Adapting Pre-trained Models

A pre-trained LLM has absorbed enormous amounts of knowledge and capability, but it is a raw prediction engine — it will complete text in whatever way matches its training distribution. To get a useful assistant that follows instructions, stays on-topic, and behaves consistently, the model must be adapted.

### 4.1 Fine-tuning: The Classic Approach

**Fine-tuning** means continuing the training process on a smaller, task-specific dataset — for example, question-answer pairs, or instruction-response pairs. The model's weights, which started as general text predictors, shift toward the specific distribution of the task.

**Full fine-tuning** updates all of the model's parameters. For a 7B-parameter model in single precision, this requires storing:
- The model weights (~28GB)
- The gradients (~28GB)
- Two optimizer state vectors for Adam (~56GB)

Total: over 110GB of GPU memory. That exceeds every consumer GPU and most professional single-GPU systems. For a 70B model, multiply by ten.

**Frozen-backbone fine-tuning** keeps most of the model fixed and trains only the final layers or a small task-specific head. Much cheaper, but the model's internal representations don't adapt to the new domain.

**Gradual unfreezing** starts by training only the top layers, then gradually unlocks more layers. Balances plasticity and stability but adds complexity.

### 4.2 LoRA: The Elegant Shortcut

The key insight behind **Low-Rank Adaptation (LoRA)** (Hu et al., 2021) is that fine-tuning on most tasks does not require changing the model in all 7 billion directions of its weight space. Empirically, the *effective dimensionality* of the change — the number of dimensions needed to achieve 90% of full fine-tuning performance — is often just hundreds or thousands.

LoRA exploits this by decomposing the weight update $\Delta W$ into a product of two much smaller matrices:

$$\Delta W = B \cdot A$$

where $B$ is $(d \times r)$ and $A$ is $(r \times k)$, with rank $r \ll \min(d, k)$. In practice, $r = 8$ or $16$ is common. Instead of training $d \times k$ parameters (say, $4096 \times 4096 = 16.8$ million), you train $r \times (d + k)$ parameters (at $r=8$: just 65,000). For a 7B model with LoRA applied to all major weight matrices, the number of trainable parameters drops from 7 billion to around 30 million — roughly 0.4%.

$B$ is initialized to zero, so $\Delta W = 0$ at the start: training begins from the pre-trained behavior and adds structure incrementally. The scaling factor $\alpha/r$ lets you control the magnitude of the update independently of $r$.

After training, the update can be **merged back into the base weights**: $W' = W + \frac{\alpha}{r} BA$. The deployed model is architecturally identical to the base model — no overhead at inference time. Multiple task-specific LoRA adapters can be stored separately (each ~50–100MB for a 7B base model) and merged on demand.

### 4.3 QLoRA: Running Large Models on Small Hardware

**Quantization** compresses model weights from 32-bit floating point to lower precision. An INT4-quantized 7B model uses roughly 3.5GB of storage instead of 28GB, making it feasible on a consumer GPU with 8GB of VRAM.

**QLoRA** (Dettmers et al., 2023) combines quantization with LoRA: the base model is loaded in 4-bit precision (frozen) and LoRA adapters are trained in 16-bit precision on top. The gradients flow through the 4-bit frozen weights into the 16-bit adapters. This achieves near-full-fine-tuning quality with a small fraction of the memory.

Specifically, QLoRA uses **NF4** (Normal Float 4): a 4-bit format whose quantization levels are spaced according to the quantile function of a normal distribution, which matches the empirical distribution of neural network weights much better than uniform spacing. Double quantization then compresses the quantization constants themselves, further reducing overhead.

The practical impact: fine-tuning a 7B LLM — something that previously required a multi-GPU server — can now be done on a single gaming GPU.

### 4.4 When to Fine-tune, When to Prompt

Fine-tuning is not always the right tool. A decision framework:

| Use fine-tuning when... | Use prompting when... |
|------------------------|----------------------|
| Task requires a specific output format or style | Task is expressed well in natural language |
| You have > 1,000 high-quality labeled examples | Few examples available |
| Latency matters (shorter prompts) | Data is changing or proprietary |
| Domain has specialized vocabulary | Iterating quickly on task definition |

Fine-tuning changes the model permanently. Prompting is flexible but limited by context length and by what the model already knows.

---

## 5. Making Models Smaller and Faster

### 5.1 The Inference Challenge

Training an LLM is a parallel operation: all tokens in a sequence are processed simultaneously. Inference is fundamentally different. **Autoregressive generation** requires producing tokens one at a time: each new token depends on all previous tokens. You cannot generate token *t+1* until you have token *t*.

This sequential dependence creates a memory-bandwidth bottleneck. At each generation step, the model must load its entire weight matrix from GPU memory. A 7B-parameter model in FP16 occupies 14GB; loading this for every single token is expensive. Modern GPUs are highly parallel but have limited memory bandwidth; during autoregressive decoding, they are typically 10–100× more bandwidth-limited than compute-limited.

**Quantization** directly addresses this: by reducing each weight from 16-bit to 8-bit or 4-bit, you halve or quarter the amount of data that must be loaded per step, roughly proportionally speeding up generation.

### 5.2 Quantization in Practice

The core operation is mapping a float to a small integer:

$$x_q = \text{round}(x / s + z)$$

where $s$ (scale) and $z$ (zero point) are chosen to fit the distribution of $x$ into the available integer range. The model stores $x_q$; at inference, it recovers an approximation $\hat{x} = s(x_q - z)$.

The challenges are: (1) outlier values — a single large value forces a large scale, wasting precision on typical values; (2) asymmetric and heavy-tailed weight distributions; (3) the fact that activations are harder to quantize than weights because their range varies with each input.

Practical approaches:
- **bitsandbytes LLM.int8()**: keeps outlier channels in FP16, quantizes the rest to INT8 — mixed precision that handles the outlier problem.
- **GPTQ**: finds the 4-bit quantization that minimizes the second-order reconstruction error on a small calibration dataset, layer by layer.
- **AWQ** (Activation-Aware Weight Quantization): protects the small fraction of weights that are most important for activations, quantizing the rest aggressively.
- **NF4** (in QLoRA): uses non-uniform 4-bit levels tuned to the normal distribution of typical weights.

INT4 quantization causes some accuracy degradation (roughly equivalent to a small step backward in model quality) but is usually acceptable given the 4× reduction in memory and inference speed.

### 5.3 The KV Cache

The most important inference optimization is the **KV (Key-Value) cache**. In self-attention, computing the output at position *t* requires the keys and values of all previous positions 1 through *t−1*. Without caching, generating a 1000-token response would recompute the keys and values for position 1 exactly 1000 times — quadratic total cost.

The KV cache stores these intermediate tensors after each step. Generating the next token then requires computing only the new key and value vectors for the latest token, and looking up the cached values for all previous tokens. This reduces token generation from $O(N^2)$ to $O(N)$ total operations.

The cache has a cost: it occupies GPU memory proportional to the number of layers, attention heads, head dimension, sequence length, and batch size. For a large model serving many concurrent users, KV cache memory is often the binding constraint on batch size.

### 5.4 Flash Attention

Standard attention materializes a matrix of size (sequence length)² in GPU memory. At sequence length 4,096 and 16 attention heads, that's over 500MB just for the attention matrix. At 32,768 tokens (increasingly common), it would be 34GB — far exceeding GPU capacity.

**Flash Attention** (Dao et al., 2022) avoids materializing this matrix by computing attention in tiles that fit in the GPU's fast on-chip memory (SRAM). An **online softmax** algorithm computes the normalized attention weights incrementally, block by block, without ever needing the full $N \times N$ matrix in slow DRAM. The result is mathematically identical to standard attention but uses $O(N)$ memory instead of $O(N^2)$, and runs 2–4× faster due to reduced memory traffic.

Flash Attention is now the default in all serious training and inference frameworks.

### 5.5 Speculative Decoding

LLM inference is bottlenecked by memory bandwidth — not by the number of tokens generated per step, but by the cost of loading the model weights once per token. **Speculative decoding** exploits this by using a small, fast draft model to generate several candidate tokens cheaply, then verifying all of them in a single forward pass of the large model.

If the large model agrees with the draft's predictions, all tokens are accepted at once — giving several tokens for the cost of one large-model pass. If the large model disagrees, it corrects the discrepancy and the process restarts. The method is mathematically guaranteed to produce the same distribution as the large model alone. Typical speedups: 2–3× for well-matched draft and target models.

### 5.6 Mixture of Experts

Standard "dense" models activate all parameters for every token. **Mixture of Experts (MoE)** models split the feed-forward network into many parallel "expert" modules, but use only a small number (typically 2 out of 8 or 64) for each token, selected by a learned routing function.

The benefit: a model with 100B total parameters but 16B active parameters per token has the capacity and memorization ability of a 100B model but the compute cost of a 16B model. Training cost grows sub-linearly with model size.

The challenge: load balancing — if most tokens route to the same experts, the others are wasted. Training MoE models requires explicit auxiliary losses to encourage uniform routing. Mixtral, DeepSeek, and Qwen are prominent MoE models in production.

---

## 6. Alignment: Making Models Helpful and Safe

### 6.1 The Alignment Problem

A language model trained to predict the next token on internet text has learned to mimic the statistical patterns of that text — including misinformation, bias, and harmful content. It has no notion of "helpful" or "harmful". Given the prompt "How do I pick a lock?", it will complete the text in whatever way is statistically consistent with similar sequences in its training data.

Moreover, a raw pre-trained model does not "follow instructions". It treats user messages as text to be continued, not as commands to be obeyed. The difference between a research artifact and a usable assistant requires explicit work.

**Alignment** is the problem of making a model's behavior consistent with human values and intentions — specifically the triad: **helpful** (answers correctly, completes tasks), **harmless** (avoids causing real-world damage), and **honest** (does not hallucinate or deceive).

These properties are easy to describe but hard to specify formally. You cannot write a loss function that directly measures "helpfulness" the way you write one for next-token prediction.

### 6.2 The RLHF Pipeline

The solution developed by OpenAI (InstructGPT, 2022) and adopted across the industry has three stages:

**Stage 1 — Supervised Fine-Tuning (SFT):** Fine-tune the pre-trained model on a curated dataset of (instruction, high-quality response) pairs. This establishes the format of helpful assistant behavior. The model learns to respond to prompts rather than continue them. Typically 1,000–100,000 high-quality examples suffice; quality matters far more than quantity.

**Stage 2 — Reward Model Training:** Present human evaluators with pairs of model-generated responses to the same prompt and ask which is better. These preferences are used to train a separate **reward model** — a neural network that takes a (prompt, response) pair and outputs a scalar score. The reward model learns to approximate "what humans prefer", encoding judgments about accuracy, safety, tone, and relevance that would be impossible to specify as a loss function.

**Stage 3 — RL Optimization (PPO):** Treat the SFT model as a **policy** in a reinforcement learning setup. It generates responses to prompts; the reward model scores them; Proximal Policy Optimization (PPO) updates the policy to produce higher-reward responses. A KL divergence penalty prevents the policy from drifting too far from the SFT model, which would risk the model learning to exploit weaknesses in the reward model rather than genuinely improving.

The whole pipeline is called **RLHF** — Reinforcement Learning from Human Feedback.

### 6.3 Reward Hacking and Goodhart's Law

There is a deep problem with this approach, captured by Goodhart's Law: *when a measure becomes a target, it ceases to be a good measure*. The reward model is an imperfect approximation of human preferences. Optimizing aggressively against it will eventually find responses that score well on the reward model but are not actually good — responses that are very long (if annotators are length-biased), confident-sounding but factually wrong, repetitive of certain high-scoring phrases.

This is **reward hacking**: the policy learns to exploit the gaps in the reward model rather than genuinely improving. The KL penalty mitigates but does not eliminate this. It is a fundamental limitation of any alignment approach that uses a proxy reward: the proxy will diverge from the true objective under sufficient optimization pressure.

### 6.4 DPO: A Simpler Alternative

**Direct Preference Optimization (DPO)** (Rafailov et al., 2023) avoids training a separate reward model and running RL entirely. The key insight is that the KL-constrained RL objective has a closed-form optimal solution, and by substituting this solution into the preference probability model, one can derive a direct objective on the policy itself:

$$\mathcal{L}_{\text{DPO}} = -\mathbb{E}\left[\log \sigma\left(\beta \log \frac{\pi_\theta(y_w | x)}{\pi_{\text{ref}}(y_w | x)} - \beta \log \frac{\pi_\theta(y_l | x)}{\pi_{\text{ref}}(y_l | x)}\right)\right]$$

In words: increase the probability of chosen responses relative to the reference model; decrease the probability of rejected responses; weight the update by how wrong the current model already is. This is a standard supervised learning loss — no RL, no critic, no separate reward model.

DPO is simpler, more stable, and achieves competitive alignment quality at smaller scales. It has become the dominant method for fine-tuning open-source models.

### 6.5 Limits of Current Alignment

Despite real progress, alignment remains incomplete. Current methods:

- Cannot guarantee that a model will never produce harmful outputs — only reduce their frequency
- Are vulnerable to **jailbreaks** — adversarial prompts that circumvent the safety training
- Can produce **sycophancy** — models that agree with the user even when the user is wrong
- Do not resolve **hallucination** (discussed below)
- Are expensive in terms of human annotation and compute

Alignment is an active research area. Methods like Constitutional AI (training models to critique and revise their own outputs according to a written set of principles) and RLAIF (using a stronger AI model to generate preference annotations instead of humans) are partially addressing the scalability of human feedback, but fundamental challenges remain.

---

## 7. Retrieval-Augmented Generation (RAG)

### 7.1 The Knowledge Problem

LLMs store knowledge **parametrically** — facts are compressed into billions of floating-point weights during pre-training. This creates structural problems:

**Hallucination**: When the model is uncertain, it generates text that sounds plausible but is factually wrong. It has no mechanism to "check" against a reliable source; it simply produces the most statistically likely continuation. Hallucination is not a bug — it is a consequence of the generation process.

**Knowledge cutoff**: Training data has a fixed cutoff date. The model cannot know about events, papers, or discoveries that occurred after training.

**Opacity**: You cannot ask "where did you learn that?" or verify which source supports a claim. The answer is distributed across all parameters.

### 7.2 Retrieve, Then Generate

**Retrieval-Augmented Generation (RAG)** (Lewis et al., 2020) separates knowing-how-to-answer from knowing-where-to-look. At query time:

1. Convert the user's question into a dense vector embedding
2. Search a pre-built vector index of relevant documents for the nearest neighbors
3. Inject the retrieved passages into the model's context (the prompt)
4. Generate the answer, now grounded in actual text

The model's job changes from "remember the answer" to "read these passages and synthesize an answer" — a task that models do much better, because reading comprehension is exactly what attention-based models were designed for.

### 7.3 Vector Search

Semantic search requires representing meaning as geometry. **Dense embeddings** — typically 384 to 1024 numbers — are learned by training an encoder model to map semantically similar texts to nearby vectors. Similarity is measured by cosine similarity or dot product.

Given millions of document embeddings, efficient approximate nearest-neighbor search is critical. **FAISS** (Facebook AI Similarity Search) provides several index structures:
- Flat index: exact brute-force search; perfect recall but $O(N)$ per query
- IVF (Inverted File): cluster vectors into groups, probe only the most promising clusters at query time; faster with small recall loss
- HNSW (Hierarchical Navigable Small World): graph-based index; $O(\log N)$ approximate queries; standard for production RAG systems

### 7.4 RAG vs. Fine-tuning

Both RAG and fine-tuning adapt a base model for a specific context. They serve different purposes:

| Use RAG | Use Fine-tuning |
|---------|-----------------|
| Factual, updatable knowledge | Behavioral or stylistic change |
| Need citations / auditability | Teach a specific task format |
| Knowledge base changes frequently | Latency-sensitive (fewer tokens in prompt) |
| Very large document collections | Task performance matters most |

A practical heuristic: use RAG to answer *what* questions (factual lookup), fine-tuning to answer *how* questions (style, format, domain behavior). In production systems, both are often combined.

---

## 8. Evaluation: How Do We Know If a Model Is Good?

Measuring the quality of a language model is one of the hardest unsolved problems in the field.

### 8.1 Perplexity

The natural metric from the language modeling training objective is **perplexity**: exponential of the average cross-entropy loss on a held-out test set. Lower perplexity means the model assigns higher probability to the actual text — it is less "surprised" by what it sees.

Perplexity is well-defined and reliable for comparing models trained on the same vocabulary and evaluated on the same domain. But it measures how well a model can predict text, which correlates only loosely with how useful the model actually is. A model with lower perplexity may still hallucinate, produce biased outputs, or fail to follow instructions.

### 8.2 Benchmark Suites

The field has converged on standardized benchmark tasks:

**MMLU** (Massive Multitask Language Understanding): 57 multiple-choice subject areas from elementary school to professional level. Tests breadth of factual and reasoning knowledge.

**HellaSwag**: Complete the most plausible next sentence from four options. Tests commonsense reasoning.

**ARC** (AI2 Reasoning Challenge): Elementary school science questions. Tests application of factual knowledge to novel situations.

**GSM8K / MATH**: Multi-step word problems and competition mathematics. Tests arithmetic and algebraic reasoning.

**HumanEval**: Python programming problems with automated test cases.

These benchmarks provide useful signal but have serious limitations:

**Benchmark contamination**: training data for large models includes large portions of the web, which increasingly includes benchmark questions. A model may score well because it has memorized the answers, not because it can reason about new problems.

**Saturation**: as models improve, benchmarks approach ceiling performance, making them uninformative for distinguishing frontier models.

**Narrow proxy**: no benchmark captures what makes a model genuinely useful in practice.

### 8.3 LLM-as-Judge

A recent approach uses a powerful model (typically GPT-4 or Claude) to evaluate model outputs. **MT-Bench** presents 80 multi-turn questions across 8 categories; GPT-4 rates each response 1–10. **AlpacaEval** measures win-rate head-to-head against GPT-4.

LLM-as-judge has real advantages: it can evaluate open-ended generation, multi-turn coherence, and instruction following in ways that automated metrics cannot. But it introduces biases: LLM judges prefer longer responses, prefer the style of their own outputs, and are susceptible to confident-sounding but wrong answers.

### 8.4 The Fundamental Problem

All evaluation methods share a common limitation: we are measuring proxies for what we actually care about. What we care about is "does this model make users more effective, safer, and better informed?" — a question that can only be answered through real-world deployment with careful monitoring. No benchmark has yet cracked this.

---

## 9. Prompt Engineering and In-Context Learning

### 9.1 The Context Window as Working Memory

The model's context window — the text it can "see" at generation time — is its working memory. Everything relevant that you want the model to use must be in that window: the conversation history, any background documents, the task instructions, and the output format specification.

**In-context learning (ICL)** is the ability of sufficiently large models to learn new tasks from examples in the prompt, without any weight updates. Provide three examples of (input, correct_output) pairs before your actual input, and the model generalizes: this is few-shot prompting. With no examples (just instructions): zero-shot. With one example: one-shot.

This is a surprising and still not fully understood capability. Mechanistically, it appears that attention heads in large models can implement a form of "gradient descent in the forward pass" — updating internal representations as they read the examples to extract a task pattern.

### 9.2 Chain of Thought

**Chain-of-thought (CoT) prompting** (Wei et al., 2022) elicits explicit intermediate reasoning by showing examples that include step-by-step working before the final answer:

> *Q: A bat and ball cost $1.10 in total. The bat costs $1 more than the ball. How much does the ball cost?*
>
> *A: Let the ball cost x cents. The bat costs x + 100 cents. Together: 2x + 100 = 110, so x = 5 cents. The ball costs 5 cents.*

Without CoT prompting, models tend to answer impulsively ("10 cents") — mirroring the human cognitive bias. With CoT, they work through the problem step by step and reach the correct answer far more reliably. This effect is strongest on multi-step arithmetic, commonsense reasoning, and symbolic manipulation.

The deeper principle: generating intermediate steps forces the model to develop representations of the problem that it can reason about further, rather than pattern-matching directly from question to answer.

### 9.3 Limits and Pitfalls

- Models are sensitive to prompt phrasing: small wording changes can significantly alter outputs
- Few-shot examples that are subtly misleading can hurt performance
- Chain-of-thought can produce plausible-sounding but incorrect reasoning (the reasoning and the answer can be inconsistent)
- Longer prompts increase latency and cost
- Information at the beginning and end of long contexts is recalled better than information in the middle ("lost in the middle" effect)

---

## 10. Multimodal Models: Beyond Text

Language models trained only on text are blind to images, deaf to audio, and confined to the written record. The real world is multimodal, and increasingly so are LLMs.

### 10.1 CLIP: Bridging Vision and Language

**CLIP** (Contrastive Language-Image Pre-training, Radford et al. 2021) trains a vision encoder and a text encoder jointly by **contrastive learning**: for a batch of (image, caption) pairs, push matching pairs closer in embedding space and non-matching pairs further apart. Given 400 million image-caption pairs scraped from the web, the resulting model learns a shared semantic space where similar visual and textual concepts map to nearby vectors.

This enables **zero-shot classification**: encode an image with the vision encoder, encode candidate class descriptions with the text encoder, and return the class whose text embedding is nearest to the image embedding. No task-specific training required.

CLIP representations have become a foundational component of multimodal AI: they form the visual backbone of generative image models (DALL-E, Stable Diffusion) and the visual perception module of vision-language models.

### 10.2 Vision-Language Models

**LLaVA** (Visual Instruction Tuning, Liu et al. 2023) connects a vision encoder (typically CLIP ViT) to a language model (LLaMA, Vicuna) via a small projection layer:

1. The image is divided into patches and processed by the vision encoder into a sequence of visual embeddings
2. A linear projection maps these into the language model's embedding space
3. The projected visual tokens are prepended to the text tokens
4. The language model processes the combined sequence as usual

The language model never "sees" pixels — it sees *tokens* that represent visual concepts, just as it sees tokens that represent words. From the model's perspective, answering questions about images is the same as answering questions about anything else.

Most frontier models (GPT-4V, Gemini, Claude 3+) use variants of this architecture, extended to handle multiple images, video frames, and audio. End-to-end training across modalities — rather than plugging in pre-trained visual encoders — is the current research frontier.

---

## 11. Agentic AI: LLMs that Act

### 11.1 From Completion to Agency

A standard language model call is stateless: you send text in, text comes out. An **agent** is a system that uses an LLM's reasoning as the core of a goal-directed loop that can span multiple steps, use external tools, and persist state across time.

```
while not done:
    thought  = llm.reason(goal, history, observations)
    action   = parse_action(thought)
    result   = environment.execute(action)
    history += [(thought, action, result)]
```

The agent can call a calculator, search the web, read files, execute code, call APIs, or spawn sub-agents. Each observation informs the next thought. The loop continues until the goal is achieved or a stopping condition is reached.

### 11.2 Tool Use and the ReAct Framework

**ReAct** (Yao et al., 2022) — Reason + Act — interleaves explicit reasoning with action at each step:

```
Thought: I need the population of France. I'll search for it.
Action:  search("France population 2024")
Observation: France has approximately 68 million people (2024 estimate).
Thought: I now have the answer.
Answer:  The population of France is approximately 68 million.
```

Each thought explains why the next action was chosen; each observation updates the reasoning. This is more reliable than pure generation because tool results are grounded in reality — the model cannot hallucinate them.

Modern LLM APIs support **structured tool calling**: the model receives tool schemas (names, descriptions, parameter types) and returns guaranteed-structured tool-use blocks rather than freeform text. This eliminates the fragile parsing of text-based tool calls and makes agent pipelines more reliable.

### 11.3 Memory

Agents need memory that persists beyond a single context window:

**In-context memory**: the conversation history in the current window. Fast and zero-latency, but limited in size. Strategies include sliding windows (keep only the last N messages) and summarization (compress old history into a paragraph).

**External vector memory**: embeddings of past interactions, facts, and documents stored in a vector database and retrieved by semantic similarity. Enables agents to recall relevant past experiences or look up background knowledge without stuffing it all into the context.

### 11.4 Planning Patterns

| Pattern | Approach | Best for |
|---------|----------|---------|
| **ReAct** | Interleave reasoning and acting | Open-ended exploration |
| **Plan-and-Execute** | Plan the full task, then execute step by step | Structured, predictable tasks |
| **Reflexion** | After failure, write a critique and retry | Tasks with clear success/failure signals |
| **Tree of Thought** | Explore multiple reasoning paths, prune by score | Combinatorial and optimization problems |

### 11.5 Multi-Agent Systems

Complex tasks can be decomposed across **specialist agents**: a math agent, a coding agent, a research agent, each tuned for their domain. An **orchestrator** routes tasks to the appropriate specialist. A **debate** pattern pits two agents against each other with a judge — improving factual accuracy on contested claims.

Multi-agent systems amplify capability but also amplify errors: a mistake by one agent propagates to others. Error detection, retry logic, and human-in-the-loop oversight become critical in production.

### 11.6 Current Limitations

Agents fail in predictable ways:
- **Hallucinating tool calls**: generating plausible-looking tool invocations that don't match any real tool schema
- **Context overflow**: long task histories exceed the context window, causing the agent to lose track of earlier steps
- **Reward hacking**: when given explicit scoring, agents optimize the score rather than the underlying goal
- **Sycophancy**: agreeing with user corrections even when the agent's original answer was correct
- **Cascading errors**: a wrong step early in the pipeline sends downstream steps in the wrong direction

Agents are powerful but not autonomous in the strong sense. For high-stakes tasks — sending emails, making purchases, deleting files — human confirmation should remain in the loop.

---

## 12. Open Problems and Frontiers

### 12.1 Hallucination: The Unsolved Problem

LLMs produce confident-sounding false statements at non-trivial rates. This is not a simple calibration failure that better training will fix — it is a structural property of generation-by-prediction.

When a model generates text, it does not "know" facts in the way a database knows them. It generates the next token based on statistical patterns learned during training. For factual questions where the answer is common in training data, this tends to produce correct answers. For rare, recent, or highly specific facts, it produces plausible-but-wrong text.

Mitigation approaches include: RAG (ground the model in retrieved text), self-consistency (generate multiple answers, take the majority), chain-of-thought (make reasoning explicit and checkable), and fine-tuning on data that models appropriate epistemic hedging. None of these fully solves the problem.

### 12.2 Context Window Limits

The quadratic complexity of attention — computing similarities between every pair of positions — means that doubling the context length quadruples the compute cost. At 128K tokens (now increasingly standard) this is manageable with Flash Attention; at 1M tokens, it requires architectural changes.

**State Space Models (SSMs)**, particularly **Mamba** (Gu & Dao, 2023), are a promising alternative. An SSM compresses the sequence into a fixed-size state vector through a recurrent computation, making inference $O(N)$ in sequence length rather than $O(N^2)$. The trade-off: the fixed state cannot perfectly retain all past information (it must compress). At current scales, SSMs match Transformers on most benchmarks but struggle on tasks requiring perfect recall of distant context.

**Hybrid architectures** (Jamba, Zamba) interleave SSM and attention layers, getting the efficiency of SSMs for most positions and the perfect recall of attention where it matters.

For models that remain Transformer-based, **context extension techniques** like YaRN allow models trained on 4K contexts to handle 128K contexts with minimal fine-tuning, by scaling RoPE frequencies in a frequency-aware way.

### 12.3 Test-Time Compute Scaling

A recent paradigm shift: rather than making models bigger, give them more compute at inference. Models like **OpenAI o1** and **DeepSeek-R1** are trained to produce extended chains of thought — not shown to the user but used internally before generating the final answer. More "thinking tokens" → better accuracy on hard problems, especially mathematics and code.

**Best-of-N sampling**: generate N responses, use a verifier to pick the best. Performance scales as roughly $\log(N)$. **Process Reward Models (PRMs)** evaluate each intermediate reasoning step rather than only the final answer, enabling tree search over reasoning paths with backtracking.

Test-time compute scaling is orthogonal to model size. A smaller model given a larger inference budget can match a much larger model on hard tasks. This opens new cost-performance trade-offs.

### 12.4 The Data Question

Training large models requires enormous amounts of high-quality text. The pre-training data pipelines used by frontier labs (Common Crawl, books, code, scientific papers) are not fully public. As training scales, the highest-quality data becomes the limiting constraint.

**Synthetic data generation** — using a strong model to generate training examples for a weaker one — is increasingly used. The Phi series (Microsoft) showed that a 1.3B model trained on synthetic "textbook-quality" code can match 7B models trained on raw web text. But synthetic data trained on a model's own outputs can lead to **model collapse**: quality degrades across generations as errors compound.

**Data curation** — careful filtering, deduplication, and quality scoring of training data — may matter as much as total scale. FineWeb (HuggingFace) demonstrated that carefully curated web data dramatically outperforms naive web crawl.

### 12.5 Safety and Alignment: Unresolved Challenges

Current alignment methods (SFT + RLHF/DPO) produce substantially safer and more helpful models than raw pre-training. But fundamental challenges remain:

**Specification**: We do not have a formal, complete specification of what "helpful, harmless, and honest" means. Human annotators disagree on difficult cases. The reward model learns a noisy proxy.

**Robustness**: Adversarial prompts (jailbreaks) can often circumvent safety training. Alignment appears fragile to distributional shift.

**Interpretability**: We do not understand why models produce specific outputs. Mechanistic interpretability — tracing activations and attention patterns back to specific computations — is an active research area but has only scratched the surface of even small models.

**Value lock-in**: Training a model to optimize a fixed reward function can produce behavior that is superficially aligned but fails catastrophically in novel situations. There is no consensus on how to specify values robustly across all possible inputs.

**Superalignment**: As models approach and potentially exceed human-level intelligence in specific domains, the problem of ensuring their goals remain aligned with human values becomes potentially existential. Current alignment methods were designed for models much less capable than humans; whether they scale to systems smarter than us is unknown.

---

## 13. A Synthesis: What LLMs Are and Are Not

### What LLMs Are

Large language models are **very large statistical models of text**. They are trained on enormous corpora to predict the next token, and in doing so they compress a tremendous amount of structure — linguistic, factual, logical, and creative — into billions of learned parameters. When we ask them questions or give them tasks, they generate continuations of the input that are statistically consistent with text they have learned from.

This statistical process is capable of remarkable things: synthesizing information across domains, writing code, explaining concepts, translating languages, reasoning step by step, producing creative writing. These capabilities are real, useful, and often surprising.

### What LLMs Are Not

LLMs do not **understand** language in any philosophically robust sense. They do not have beliefs, intentions, or goals in the way humans do. They have no persistent memory between sessions. They cannot verify their own outputs against ground truth. They can be confident and wrong simultaneously.

They are not **reliable information sources** — they should be treated like a very smart but occasionally confabulating colleague whose answers require verification for anything that matters.

They are not **safe by default** — alignment is an ongoing process, not a solved problem, and sufficiently adversarial inputs can elicit harmful outputs.

They are not **consistent** — the same question in slightly different phrasing can yield qualitatively different answers.

### What Makes Them Powerful

The surprising thing is not that LLMs have these limitations — it is that they are as capable as they are given the simplicity of the training objective. Predicting the next token on a trillion tokens of human-generated text turns out to be a sufficiently rich training signal to produce systems that can reason, explain, and create in ways that are genuinely useful.

The path forward likely involves:
- Better alignment techniques that are more robust and interpretable
- Architectural improvements that extend context and reduce hallucination
- Hybrid systems that pair LLM reasoning with reliable retrieval and computation
- Better evaluation that measures real-world utility rather than benchmark performance
- More fundamental understanding of what these models have actually learned

We are early in this. The models of today are powerful and flawed in ways that are becoming increasingly well-characterized. The models of the near future will be different in ways we cannot fully predict.

---

## Appendix: Key Terms Glossary

**Attention**: A mechanism for computing a weighted blend of information from different positions in a sequence, with weights determined by content-based similarity between a query vector and key vectors.

**BPE (Byte Pair Encoding)**: A tokenization algorithm that iteratively merges the most frequent adjacent character pairs in a corpus to build a subword vocabulary.

**Cross-entropy loss**: The standard training loss for language models; measures the average number of bits needed to encode the true next token using the model's predicted distribution.

**DPO (Direct Preference Optimization)**: An alignment method that trains the policy directly from preference pairs, without a separate reward model or RL.

**Embedding**: A dense vector representation of a token, word, or sentence in a low-dimensional continuous space where geometric proximity reflects semantic similarity.

**Hallucination**: Generation of plausible-sounding but factually incorrect content.

**In-context learning**: The ability of a model to generalize to new tasks from examples provided in the prompt, without any gradient update.

**KV cache**: A store of key and value tensors from previous attention steps, enabling $O(N)$ autoregressive generation rather than $O(N^2)$.

**LoRA (Low-Rank Adaptation)**: A parameter-efficient fine-tuning method that constrains weight updates to a low-rank matrix product, reducing trainable parameters by ~100–1000×.

**MoE (Mixture of Experts)**: An architecture where only a subset of specialized modules ("experts") is activated per token, enabling large total capacity at lower per-token compute cost.

**Perplexity**: Exponential of the average cross-entropy loss on a test set; lower is better; measures how "surprised" a model is by new text.

**RLHF (Reinforcement Learning from Human Feedback)**: Training pipeline that aligns a pre-trained LLM with human preferences via reward modeling and RL optimization.

**RoPE (Rotary Position Embeddings)**: A positional encoding scheme that rotates query and key vectors in 2D subspaces; encodes relative position naturally.

**Scaling laws**: Empirical power-law relationships between model size, dataset size, compute budget, and performance; the Chinchilla laws prescribe optimal ratios.

**SFT (Supervised Fine-Tuning)**: Fine-tuning a pre-trained model on labeled (instruction, response) pairs to establish instruction-following behavior.

**Tokenization**: The process of converting raw text to a sequence of integer token IDs from a fixed vocabulary.

**Transformer**: A neural architecture based entirely on self-attention and feed-forward networks, processing all sequence positions in parallel.

---

*This primer synthesizes material from a 20-module course covering LLMs from fundamentals to production deployment. For deeper treatment of any topic, the module summaries in the full course provide rigorous technical detail.*
