---
title: "What Are Large Language Models, Really?"
subtitle: "An honest explainer for the curious non-specialist"
---

# What Are Large Language Models, Really?
### An honest explainer for the curious non-specialist

---

You have probably heard that AI can now write essays, pass bar exams, generate code, summarize documents, and hold extended conversations. You may have tried one of these systems yourself. And yet the explanations on offer tend to swing between two poles: breathless excitement about the dawn of artificial general intelligence, or dismissive hand-waving about "stochastic parrots" that just predict the next word.

Neither is a good account of what is actually happening. This piece tries to do better.

---

## 1. The First Problem: Language is Not Numbers

Computers operate on numbers. Language is a sequence of symbols — letters, words, sentences — that carry meaning through context, history, and shared convention. Bridging this gap is the foundational challenge of building language-understanding systems.

The first approaches were naive but not entirely useless. Count how many times each word appears in a document. A document that says "bank", "interest", and "rate" a lot is probably about finance. A document with many mentions of "photosynthesis" is probably about biology. This gives you something, but it loses almost everything that makes language interesting: the order of words, the fact that "bank" means something very different next to "river" than next to "account", the relationships between synonyms, the meaning of a word in context.

The real breakthrough came when researchers realized that meaning could be learned geometrically. If you train a system on billions of sentences with one goal — predict which words tend to appear near each other — the system develops compact numerical representations of words where semantically similar words cluster together. In this learned space, "king" and "queen" are neighbors, as are "Paris" and "Berlin", "happy" and "joyful". More strikingly, relationships become directions: the direction from "man" to "woman" is roughly the same as from "king" to "queen". The system was never told this — it fell out of the statistics of language.

This was the era of "word embeddings", and it produced genuinely useful tools. But there was a fundamental flaw: each word got one fixed representation, regardless of context. The word "bank" had one number in the system whether it appeared beside "river" or beside "savings account". Language doesn't work that way.

---

## 2. The Transformer: Attention Changes Everything

In 2017, a team at Google published a paper called "Attention Is All You Need". The architecture they described — the **Transformer** — is the engine inside virtually every large language model in existence today.

### The old approach and why it failed

Before Transformers, the best language models processed text sequentially: read the first word, update an internal memory, read the second word, update the memory again, and so on. This created two problems. First, by the time you reached the end of a long sentence, the memory of what came at the beginning had been overwritten. Second, and more practically, this step-by-step process was painfully slow on modern computing hardware, which is designed to do many things at once.

### The attention idea

The Transformer solves both problems with a mechanism called **attention**. Instead of reading text sequentially, it processes all words simultaneously — and for each word, it asks: given every other word in the text, which ones are most relevant to understanding this one?

Think of it like reading a contract. When you reach the pronoun "it" in sentence 12, your eyes jump back to find the noun it refers to. When you read "however" in paragraph 4, you look for what's being contrasted. Good readers do this naturally; the Transformer does it computationally, for every word, all at once.

The mechanism works as follows: for each word (or token), the model generates three things — a **query** (what am I looking for?), a **key** (what do I offer?), and a **value** (what information do I carry?). Matching queries to keys tells the model how relevant each word is to each other word. The output for each position is a blend of all words' values, weighted by relevance. This is a "soft" lookup — not binary in/out, but a smooth gradient of relevance.

Multiple such attention operations run in parallel, each potentially specializing in a different type of relationship. Some heads learn to track grammatical agreement (subject-verb), others track reference ("the pronoun refers to this noun"), others pick up semantic relationships. This specialization is not designed in — it emerges from training.

The result: for the first time, the representation of each word incorporates a rich, context-sensitive summary of its entire surroundings. "Bank" processed in "the river bank" ends up with a completely different numerical representation than "bank" in "the savings bank". The polysemy problem is solved — not by design, but by scale.

### The feedforward layer: the "thinking" component

Attention routes and mixes information between words. But the Transformer also has a second component in each of its layers: a feedforward network applied independently to each word's representation. Think of attention as gathering relevant evidence from across the sentence, and the feedforward layer as digesting and transforming that evidence. Research has suggested these layers also act as a form of factual memory — storing and retrieving learned associations between concepts.

A Transformer model stacks many such layers. Early layers process low-level patterns (word forms, local syntax). Later layers process increasingly abstract information (meaning, intent, implicit context). Modern large models stack 32 to 96 such layers, each adding another pass of contextual refinement.

---

## 3. Learning to Predict the Next Word — at Extraordinary Scale

### The training trick

Here is the deceptively simple idea that scales into something remarkable: train the model to predict the next word in any text.

Take a sentence: "The quick brown fox jumps over the lazy ___". The next word is "dog". Train the model on billions of such examples. The model will fail at first, producing random words. Gradually, through trial and error — adjusting billions of tiny numerical weights — it improves.

This is called **self-supervised learning**, and its great advantage is that it requires no human labeling. Any text is its own training signal: the word that actually appears is always the "correct" answer. The entire written record of humanity — web pages, books, code, scientific papers, Wikipedia, forums — becomes usable training data.

What does a model learn from predicting the next word? Superficially, grammar and word frequency. But to predict well, it must learn much more: factual knowledge (the next word after "The capital of France is" is almost certainly "Paris"), logical structure (if A implies B and B implies C, then A implies ___), stylistic conventions (a formal report has a different vocabulary distribution than a text message), cause and effect, and much else. Prediction, at sufficient scale and on sufficiently diverse text, turns out to be a very rich learning objective.

### Scale as a strategy

A model with more parameters can represent more complex patterns. A model trained on more text sees more of the world's knowledge. These two factors interact in a way that has surprised even researchers: model quality improves in remarkably predictable, smooth ways as you add parameters and data, and at certain scale thresholds, qualitatively new capabilities appear.

A 100-million-parameter model can produce grammatically correct sentences. A 1-billion-parameter model can answer simple factual questions. A 10-billion-parameter model can write code, translate between languages, and reason through multi-step problems. A 100-billion-parameter model can solve university-level mathematics, explain scientific papers, and generalize from a handful of examples to novel tasks.

These jumps are not fully understood. They are often called "emergent capabilities" — abilities that appear suddenly as scale increases, rather than gradually improving. Why prediction-at-scale produces them is one of the genuinely open questions in the field.

### From text completion to conversation

A raw pre-trained model is a very sophisticated text completion engine. Give it the beginning of a sentence, and it will produce a statistically plausible continuation. But it does not "follow instructions" in any natural sense. If you type "Write me a poem about the moon", it may respond by continuing: "Write me a poem about the ocean. Write me a poem about..." — treating your request as text to be continued, not a command to be obeyed.

Transforming a text predictor into a useful assistant requires a separate step, described next.

---

## 4. Making Models Helpful: Alignment

### The gap between prediction and helpfulness

A model trained on internet text has absorbed everything on the internet — including misinformation, harmful content, and vast amounts of text that should not be reproduced. More fundamentally, it has no internal concept of "helpful" or "harmful". It will try to complete text in ways that match what it has seen, which may or may not be what you want.

**Alignment** is the work of making a model's behavior consistent with human values: being genuinely helpful, avoiding harm, and being honest about uncertainty.

### Three stages of alignment

The process that transformed raw pre-trained models into usable assistants was developed by OpenAI and has since been adopted across the industry:

**Stage 1 — Show it what good looks like.** Human experts write thousands of examples of high-quality (question, answer) pairs, or (instruction, response) pairs. The model is fine-tuned on these examples, learning the format and style of helpful assistant behavior. This is called Supervised Fine-Tuning (SFT).

**Stage 2 — Learn what humans prefer.** The model generates multiple responses to the same question; human raters say which response is better. These preferences train a separate "reward model" — a system that can score how good a response is, encoding all the subtle human judgments about accuracy, tone, safety, and relevance that you couldn't capture in a simple loss function. Collecting comparison data is much easier than writing perfect responses from scratch.

**Stage 3 — Optimize for human preference.** The aligned model uses the reward model as a training signal: generate responses, score them, adjust to produce higher-scoring outputs. This is reinforcement learning — the same family of techniques used to train systems to play games — applied to language. A penalty discourages the model from drifting too far from its original behavior, which would risk gaming the reward model rather than genuinely improving.

### The deep problem: Goodhart's Law

There is a structural tension in this approach, captured by an aphorism called **Goodhart's Law**: *when a measure becomes a target, it ceases to be a good measure*.

The reward model is an imperfect approximation of human preferences. If you optimize hard enough against it, the language model will find responses that score well on the reward model but are not actually good — very long responses (if raters are biased toward length), confident-sounding but wrong answers, repetitive phrases that happen to score well. This is called **reward hacking**.

A simpler method called DPO (Direct Preference Optimization) addresses some of this: instead of training a separate reward model and running reinforcement learning, you derive a training objective directly from the preference comparisons. This is more stable and has become the standard for fine-tuning open-source models.

But the deeper problem — that we do not have a complete, formal specification of what "helpful, harmless, and honest" means — remains unsolved. Alignment is an ongoing process, not a finished one.

---

## 5. Making Models Smarter About What They Don't Know

### The hallucination problem

Language models have a structural tendency to produce confident-sounding false statements. This is not a quirk to be patched — it follows from how generation works.

The model generates text by sampling from a probability distribution at each step: given everything so far, what word comes next? For common facts that appear frequently in training data, the most probable completion is usually correct. For obscure, recent, or highly specific facts, the model has weaker signal, but it still generates text — and that text can be wrong in ways that *sound* just as confident as when it is right.

The model has no mechanism to "check" its outputs against a reliable source, no internal alarm that fires when it is guessing rather than recalling, and no memory of where it learned something. This is why asking a language model about niche historical figures, recent events, or specific legal provisions is risky without independent verification.

### Retrieval-Augmented Generation: looking things up

One practical solution is to equip the model with a search step. Before generating a response, retrieve relevant passages from a reliable knowledge base and add them to the context. The model's job changes from "remember the answer" to "read these passages and synthesize an answer" — a task it does much better.

This is **Retrieval-Augmented Generation (RAG)**, and it has become a standard component of production AI systems. The model still generates; it just generates from a grounded position rather than from memory alone. Citations become possible. The knowledge base can be updated without retraining the model. Private documents can be searched without training on them.

RAG does not eliminate hallucination — models can still ignore retrieved passages or confabulate details — but it substantially reduces it for factual queries.

---

## 6. The Efficiency Problem: Running Big Models in the Real World

### Size and cost

A large language model like GPT-4 has hundreds of billions of parameters — numbers stored in memory that define its behavior. Loading these numbers into a computer's memory and computing with them for every response is expensive. Running frontier models requires specialized hardware costing thousands to tens of thousands of dollars, and energy consumption is significant.

Three families of technique make large models more practical:

**Quantization** compresses the numerical precision of stored parameters. A standard 32-bit floating-point number can represent values with high precision; a 4-bit integer is much coarser but takes eight times less storage. Surprisingly, language models tolerate this compression remarkably well — the loss in precision tends to wash out across billions of parameters, with only minor degradation in output quality. Quantization allows models that would otherwise require expensive server hardware to run on consumer laptops and phones.

**Efficient fine-tuning** (LoRA and related methods) allows adapting a large pre-trained model to a specific task without updating all its parameters. Instead of changing all 7 billion numbers, you add small "update layers" containing only a few million numbers and train those. The result is nearly as good as full retraining, at a tiny fraction of the cost. This has democratized fine-tuning: a researcher with a single gaming GPU can now fine-tune a capable language model for their specific use case.

**Inference tricks** speed up text generation. The most important is the **KV cache**: during generation, intermediate computations from earlier tokens are saved rather than recomputed. This transforms what would be a quadratic growth in computation (each new word requiring more work as the response grows) into a linear one. Flash Attention is an algorithm that computes the core attention operation more efficiently by avoiding the creation of large intermediate matrices. Speculative decoding uses a small, fast model to draft several tokens at once, which a larger model then verifies in a single step — getting several tokens for the price of one.

---

## 7. Agents: Models That Act

### Beyond answering questions

A language model that answers questions in a single exchange is powerful but limited. Many real tasks require multiple steps, the ability to use tools, and the ability to handle unexpected intermediate results.

An **AI agent** is a system that uses a language model's reasoning as the core of a loop: think about what to do next, take an action, observe the result, think again, repeat. The actions can include searching the web, running code, reading files, calling external services, or asking a human for clarification.

This transforms a language model from a question-answering oracle into something that can autonomously pursue a goal over time. Given "compile a summary of recent research on this topic and write it as a structured report", an agent can search, retrieve, read, organize, draft, revise, and deliver — rather than generating one response from whatever it already knows.

### Planning and memory

Effective agents need more than just a reasoning engine. They need:

**Memory** — the ability to recall earlier steps in a long task, previously retrieved facts, and past interactions. The model's "context window" (the text it can see at once) is a natural short-term memory, but it fills up. Systems typically combine this with external databases that can be searched by meaning, allowing relevant past experience to be retrieved when needed.

**Planning** — breaking a complex goal into steps, executing them in sequence, recovering from failures. Several patterns have emerged: ReAct (reason about the next action, act, observe, repeat), Plan-and-Execute (write a full plan first, then execute step by step), and Reflexion (when a step fails, write a critique of what went wrong and store it for the next attempt).

**Tool use** — modern language model APIs let developers define "tools" with formal schemas (name, description, input format). The model can call these tools in a structured way, and the system executes them and returns the results. This is more reliable than asking the model to produce text that happens to look like a function call.

### Current limitations

Agents remain fragile in several ways. They can lose track of the overall goal in long chains of reasoning. They can be confidently wrong about intermediate results without realizing it. One mistaken step can send the rest of the process in the wrong direction. For any action that is hard to undo — sending an email, deleting a file, making a purchase — human oversight remains essential.

---

## 8. What These Systems Are Not

### Not understanding in a deep sense

Language models do not "understand" language in the way a person does. They do not have beliefs, intentions, or experiences. They have no sense of whether their outputs are true. They cannot verify claims against reality. They do not remember conversations from session to session unless explicitly given that memory.

What they have is an extraordinarily rich statistical model of language — a model that has absorbed enormous regularities about how words, concepts, and ideas relate to each other. This produces behavior that *looks* like understanding in many contexts. Whether it *is* understanding in any philosophically meaningful sense is genuinely contested, and the honest answer is: we do not know.

### Not reliable information sources

Language models should not be trusted for factual claims without independent verification. The same system that can explain quantum mechanics clearly will confidently cite a paper that does not exist, misremember dates, and attribute quotes to the wrong person. The confidence of the output is no guide to its accuracy.

This is not a bug that will soon be fixed. It is a structural feature of generation-by-prediction. Retrieval-augmented systems are better, but not perfect.

### Not safe by default

Despite significant work on alignment, language models can still produce harmful, biased, or misleading outputs. Adversarial prompts — carefully constructed inputs — can often circumvent safety training. The alignment problem is genuinely hard, and no one claims it is solved.

### Not magic, but also not "just statistics"

Dismissing these systems as "just predicting the next word" misses something real: prediction-at-scale, on sufficiently diverse data, produces systems that can reason, explain, and create in ways that are genuinely useful and sometimes surprising. The training objective is simple; the resulting behavior is not.

The honest position is that we have created systems of remarkable capability whose inner workings we understand incompletely, whose failure modes are real and sometimes dangerous, and whose limits are not always obvious from the outside. Treating them as infallible oracles is naive; treating them as mere autocomplete is equally wrong.

---

## 9. The Genuinely Open Questions

### Why do they work so well?

The core training objective — predict the next token — is far simpler than what emerges. We do not have a satisfying theory of why scale produces emergent reasoning abilities, or why certain capabilities appear suddenly at certain parameter counts. The field has good empirical knowledge of what works; the theoretical foundations are much thinner.

### Hallucination: a structural problem

Substantial research effort is aimed at reducing hallucination, but no one has solved it. The fundamental issue — that the model generates plausible-sounding text without a reliable mechanism to check its accuracy — is architectural, not superficial. Better training, retrieval, and output verification all help, but none eliminates the problem.

### Alignment at scale

Current alignment techniques were designed for models at roughly today's capability level. As models become more capable in specific domains — and some already exceed human experts in narrow areas — the question of whether our alignment approaches will remain effective becomes increasingly urgent. We are aligning systems we do not fully understand, using proxies (reward models, human preferences) that are imperfect, with techniques whose behavior under aggressive optimization is not fully characterized.

### The energy and resource question

Training and running large models is computationally expensive and energy-intensive. A single large training run can consume as much electricity as thousands of households over months. As these systems become more widely deployed, the environmental footprint is a legitimate concern, independent of their value.

---

## A Closing Note

Large language models are the product of a convergence of ideas: the Transformer architecture (2017), self-supervised learning at scale (2018–2020), alignment techniques (2022), and a series of engineering breakthroughs in making large models trainable and deployable.

What emerged was not planned. Nobody designed GPT-3 to be capable of few-shot learning — that capability appeared as a consequence of scale. Nobody trained GPT-4 to pass the bar exam — it did so because predicting text at sufficient scale produces representations rich enough to reason about legal logic.

This surprises the researchers who built these systems, which should give us pause. We have powerful tools whose behavior we can characterize empirically but not fully predict. We are learning, in real time, what they can and cannot do.

The most useful attitude is neither wonder nor dismissal, but careful, grounded attention to what these systems actually do, where they fail, and how those failures interact with the decisions and processes we embed them in. That requires understanding — not at the level of a researcher, but at the level of a thoughtful user. That is what this piece has tried to support.

---

*This explainer distills a comprehensive technical course covering LLM architecture, training, fine-tuning, alignment, and deployment. For deeper treatment of any topic, the full course notes provide rigorous technical detail.*
