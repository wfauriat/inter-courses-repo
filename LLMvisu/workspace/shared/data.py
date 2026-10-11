"""Curated example sentences and word groups, reused across visualization scripts."""

# --- Sentences for tokenization, attention, next-token prediction ---

EXAMPLES = {
    "simple": "The cat sits on the mat",
    "reverse": "The mat sits on the cat",
    "dog_cat": "The dog chased the cat",
    "cat_dog": "The cat chased the dog",
    "shakespeare": "To be or not to be, that is the question",

    # UQ / stats domain
    "uq_propagation": "Uncertainty quantification requires careful propagation of input distributions through complex models",
    "posterior": "The posterior distribution captures our updated beliefs after observing data",
    "monte_carlo": "Monte Carlo simulation estimates expectations by averaging over random samples",

    # Ambiguity / coreference
    "it_cat": "The cat sat on the mat because it was tired",
    "trophy_big": "The trophy doesn't fit in the suitcase because it is too big",
    "trophy_small": "The trophy doesn't fit in the suitcase because it is too small",
    "bank_river": "The bank was steep",
    "bank_money": "The bank was closed",

    # French
    "fr_incertitude": "L'incertitude est inhérente à toute modélisation",
    "fr_llm": "Les grands modèles de langage transforment la pratique scientifique",

    # Numbers / math
    "pi": "The value of pi is 3.14159265",
    "addition": "If x = 3 and y = 7, then x + y =",

    # Code
    "code": "def compute_posterior(prior, likelihood):",
}

# --- Word groups for embedding visualization ---

WORD_GROUPS = {
    "stats": ["probability", "uncertainty", "variance", "distribution", "likelihood", "posterior"],
    "animals": ["cat", "dog", "fish", "bird"],
    "royalty": ["king", "queen", "prince", "princess"],
    "verbs": ["compute", "estimate", "simulate", "predict"],
}

# --- Prompts for next-token prediction / generation ---

PROMPTS = {
    "capital": "The capital of France is",
    "uncertainty": "The uncertainty in the measurement is",
    "shakespeare": "To be or not to be, that is the",
    "pi": "The value of pi is 3.1",
    "qa": "What is the capital of France?",
    "code": "def compute_posterior(prior, likelihood):\n    ",
}
