# What's actually happening when you ask it something

You have noticed three things: it talks, it is sometimes confidently wrong, and the same question can give you different answers. All three follow from the same small handful of facts about how the system works. The point of this piece is to walk through those facts in just enough detail that the behaviors stop being mysterious — without dragging you through architectural details you do not need.

## What happens when you ask it something

When you type a question and hit send, the system does exactly one thing: it picks the next piece of text. Then it picks the piece after that. Then the piece after that. A 200-word answer is this same step run two or three hundred times in a row. There is no internal draft it composes and then transcribes. There is no plan it works from. The answer is built up one piece at a time, and the only thing the system ever decides is what to write next.

It helps to be specific about what "a piece" means. Your text is first chopped into chunks called *tokens*. Common short words ("the", "and", "France") are one token each. Longer or rarer words get split — "tokenization" might become "token" + "ization". The vocabulary the system knows is about 50,000 such pieces, and any input is tiled out of them.

Each token is then converted into a long list of numbers — think of them as coordinates in a very high-dimensional space. After training, the geometry of this space carries meaning. Words that play similar roles end up near each other. *Cat* sits near *dog* and *kitten*; *probability* sits near *likelihood* and *uncertainty*; *Paris* sits near *Berlin* and *Tokyo*. Strikingly, relationships also become directions: the step from *man* to *woman* is the same step as from *king* to *queen*. The system was never told this; it falls out of having read enormous amounts of text and trying to predict words from their neighbors.

But fixed coordinates are not enough, because the meaning of a word depends on what is around it. *Bank* by a river is not *bank* with a savings account. The mechanism that handles this is called *attention*, and the idea is what it sounds like. For each word in your input, the system looks at every other word and asks: how relevant is that one to understanding me? The relevant ones get pulled in; the irrelevant ones are ignored. After several rounds of this, each word's representation has been reshaped to reflect not just what it is in isolation but what it means here, in this sentence, with these neighbors. This is what lets the system handle pronouns, ambiguous words, and connections across long passages — things earlier approaches could not manage.

Once all this reshaping is done, the very last word in your input has a representation that summarizes everything that came before. The system uses that summary to compute, for every one of its 50,000 possible tokens, how likely it is to come next. This produces a *probability distribution* — usually a few candidates are quite likely, most are vanishingly unlikely. The system then samples one of them (more on the sampling in a moment), appends it to your text, and runs the entire process again to pick the next one. And again. Until it produces a special "stop" token, or hits a length limit.

That is the whole generation loop.

## Where the predictions come from

The interesting question is *how* the system knows which next-word probabilities to assign. This is the work of training, and it happens once, well before you ever talk to the model.

The training process is conceptually simple. Take an enormous amount of text — most of the readable web, plus large quantities of books and code, in the trillions of words. At every position in this text, ask the model to predict the next word. Compare its prediction to the word that actually appears. If it was wrong (which, in the early days, it always is), make tiny adjustments to the billions of internal numbers — the *weights* — that govern its predictions, so that it would have done slightly better. Repeat for a long time, on a vast amount of text, with a vast number of expensive computers.

When this is finished, the weights are frozen. They contain everything the model has: its grasp of grammar, its style, its factual knowledge, its sense of what a good answer looks like. All of it, distributed across billions of numbers in a way nobody — including the people who built the model — can fully decode.

Three consequences worth holding in mind:

**Nothing changes when you talk to it.** Your conversation does not update its weights. It does not learn from you in any persistent sense. Once you close the chat, the next user gets exactly the same model. The "memory" you sometimes see across sessions in modern systems is a separate piece of scaffolding that re-feeds previous chats into the prompt — the model itself is unchanged.

**There is no separate database of facts.** The fact that Paris is the capital of France is not stored in a row that gets looked up. It is diffused across millions of weights, baked in by training, reconstructed each time it is needed by re-running the whole prediction machinery. There is no "facts" module. The same machinery that writes a poem also "knows" about Paris.

**Its knowledge has a cutoff date.** Training happened at a particular point in time. Events, papers, or facts that emerged afterwards simply do not exist for the model — unless you put them in the conversation yourself. Without external tools, the model also has no internet access, no calculator, no clock. It only ever has its frozen weights and the text in front of it.

## From a text-completer to an assistant

The training I just described produces a very capable text *continuer*, but not a useful assistant. If you took a model with only that training and typed "What is the capital of France?", it might respond with "What is the capital of Spain? What is the capital of Italy?", treating your question as a piece of text to be extended in the same style. It has no notion that you are *asking* it anything.

To bridge this, two more rounds of training are added on top.

First, human writers produce lots of high-quality (instruction, good response) examples — questions and clean answers, requests and good completions. The model is further trained on these, so it learns to *respond* to a prompt rather than to continue it. This is the step that gives the model its assistant-like form.

Second, humans are shown pairs of model responses to the same prompt and asked which one is better. These preferences are used to nudge the model toward responses humans tend to prefer — clearer, more helpful, less harmful, less likely to confidently fabricate. This is where the "personality" you experience comes from: its tone, its hedging, its refusal of certain requests.

Both rounds adjust the same weights as the original training. The architecture does not change. And it is worth knowing that this final layer is comparatively thin — under unusual prompts, the underlying text-continuer can sometimes show through.

## Now — your three observations

**Why is it sometimes confidently wrong?**

Because the system does not separately know whether it is recalling something solid or generating something plausible. Both feel the same to it. For topics that appeared often and consistently during training — common facts, well-trodden ideas — the most plausible-sounding next words are also usually correct. For topics that did not — niche details, recent events, specific citations — it still has to produce *something*, and what comes out is the most plausible-sounding text. The same fluent prose is on display in both cases. There is no separate confidence signal, no internal flag that fires when the model is on shaky ground. This is sometimes called *hallucination*, but it is not a glitch. It is the same generation process running on weaker information. The remedy is not a bug-fix; it is giving the model more reliable material in the prompt, or building external checks around its outputs.

**Why does the same prompt give different answers?**

Because of the sampling step. The system does not always pick the most likely next token — it draws one from the distribution. A knob called *temperature* controls how much randomness goes into that draw. At temperature zero, it always picks the most likely token, and you would get the same answer each time (but a stiffer, more boring one). At higher temperatures, less likely tokens get chosen more often, producing more varied and more creative outputs. Most chat interfaces sit somewhere in the middle. Once one early token goes a slightly different way, the rest of the answer can branch off into something quite different — which is why two runs of the same question can feel very different in detail, even when they agree on substance.

**Why does it talk at all?**

Because the training process turned out to be much more powerful than anyone expected. Predicting the next word, on enough text, with enough parameters, does not just produce grammatical fluency. It produces something that can summarize, translate, reason step by step, write code, and do many other things that look a lot like understanding — even though the underlying mechanism is just probability over tokens. *Why* this works as well as it does, and why some capabilities seem to appear suddenly once a model crosses a certain size, is one of the genuinely open questions in the field. The honest answer is that the people who build these systems were also surprised.

## What this gets you

Once the shape of the process is in your head, a lot of practical observations fall out naturally:

- It is better at things where the answer is in the prompt (summarize this document, translate this sentence) than at things where the answer must be pulled from memory (what was the GDP of Argentina in 1987).
- It is unexpectedly bad at arithmetic on long numbers, because it does not see digits — it sees chunks of digits, sliced however the tokenizer happens to slice them.
- It is helped enormously by being told to "think step by step", because then its later words can build on the explicit reasoning in its earlier ones, instead of trying to leap straight to a conclusion.
- Its outputs should be checked whenever they matter factually. Not because it is bad, but because its fluency carries no signal about correctness.
- Asking it the same thing twice and comparing answers is a cheap way to detect when it is on shaky ground — agreement across runs suggests stronger underlying signal; disagreement suggests guessing.
- It will be more reliable on topics that were heavily represented in training (mainstream science, popular code, common history) and less reliable on niche or very recent ones.
- It does not know the current date, has no internet access, and has no calculator — unless something external has been bolted on to give it those things.

You do not need to know what a *transformer block* or an *attention head* is to understand any of this. What you need is the shape: a system trained once on enormous amounts of text, frozen afterwards, generating text one piece at a time by sampling from a probability distribution it computes through layers of attention and weighted adjustment. Hold onto that shape and most of the surprises become predictable.
