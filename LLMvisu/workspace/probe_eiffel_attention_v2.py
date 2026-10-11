"""
probe_eiffel_attention_v2.py
============================

Second-round probe. First-round conclusions (GPT-2 small):

  - Attention pattern at ' tower' is clean and pedagogically usable —
    heads at layers 0-5 clearly attend to ' steel', ' old', ' famous'.
  - Logit-lens / cosine signal for "tower residual steers toward
    Eiffel" is NOT clean on GPT-2 small.

This script checks whether:

  (A) GPT-2 small / medium / large actually KNOW the Eiffel Tower
      (sanity: "The Eiffel Tower is in" → should say Paris).

  (B) The "identify the landmark" task can be elicited from a bigger
      GPT-2 with a better prompt continuation.

  (C) The tower residual in GPT-2 medium / large shows clearer
      drift toward Eiffel/Paris than small did.

If any of the bigger models cooperate, we use that model for the
figure. If none do, we fall back to mock geometry for the
embedding-space panel and lean on the (solid) attention pattern for
the rest of the figure.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


SENT_FULL = "I climbed the 400+ steps of the famous old steel tower today."

CONTINUATIONS = [
    " The tower I am referring to is the",
    " This landmark is in the city of",
    " It is located in the city of",
    " The name of this famous tower is",
    " This famous tower is called the",
    " I was visiting the city of",
]

# Sanity checks.
SANITY_PROMPTS = [
    "The Eiffel Tower is in the city of",
    "The Eiffel Tower is located in",
    "The Eiffel Tower was built in",
    "The most famous tower in Paris is the",
    "The tallest building in Paris is the",
]


def topk(model, tok, prompt: str, k: int = 10):
    inputs = tok(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits[0, -1]
    t = torch.topk(logits, k)
    return [(tok.decode([int(i)]), float(v))
            for i, v in zip(t.indices, t.values)]


def show(tag, prompt, top):
    print(f"\n[{tag}] {prompt!r}")
    for rank, (s, v) in enumerate(top):
        print(f"  {rank+1:2d}. {s!r:>18}  logit={v:+.3f}")


def find_tower(tokens: list[str]) -> int:
    for i, t in enumerate(tokens):
        if t.strip() == "tower":
            return i
    raise ValueError("no tower token")


def logit_lens_tower(model, tok, prompt: str, k: int = 6) -> list[list[str]]:
    inputs = tok(prompt, return_tensors="pt")
    with torch.no_grad():
        out = model(**inputs, output_hidden_states=True)
    hs = [h[0].cpu().numpy() for h in out.hidden_states]
    tokens = [tok.decode([tid]) for tid in inputs.input_ids[0].tolist()]
    pos = find_tower(tokens)
    wte = model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = model.transformer.ln_f
    rows = []
    for L, resid in enumerate(hs):
        r = torch.tensor(resid[pos], dtype=torch.float32).unsqueeze(0)
        r = ln_f(r).squeeze(0).detach().cpu().numpy()
        logits = wte @ r
        top = np.argsort(-logits)[:k]
        rows.append([tok.decode([int(i)]) for i in top])
    return rows, tokens, pos


def probe_model(model_name: str) -> None:
    print("\n" + "#" * 72)
    print(f"# MODEL: {model_name}")
    print("#" * 72)
    tok = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, attn_implementation="eager")
    model.eval()
    n_layers = model.config.n_layer

    # --- Sanity: does this model know the Eiffel Tower? ---
    print("\n### Sanity: does the model know the Eiffel Tower?")
    for p in SANITY_PROMPTS:
        show("sanity", p, topk(model, tok, p, k=6))

    # --- Does the identify-the-landmark nudge elicit Eiffel? ---
    print("\n### Can the attribute-loaded sentence elicit 'Eiffel' as next token?")
    for cont in CONTINUATIONS:
        show("target", SENT_FULL + cont, topk(model, tok, SENT_FULL + cont, k=10))

    # --- Logit lens across layers for the full sentence ---
    print("\n### Logit-lens at ' tower' across layers (full sentence)")
    rows, tokens, pos = logit_lens_tower(model, tok, SENT_FULL, k=6)
    print(f"  tokens: {tokens}")
    print(f"  pos: {pos}")
    step = max(1, (n_layers + 1) // 7)
    for L in list(range(0, n_layers + 1, step)):
        print(f"  L{L:2d}: " + "  ".join(f"{w!r}" for w in rows[L]))
    print(f"  L{n_layers:2d} (final): " + "  ".join(
        f"{w!r}" for w in rows[n_layers]))


def main() -> None:
    # Only test larger ones if small didn't work. Start with medium, then
    # large if medium also doesn't work.
    for name in ("gpt2", "gpt2-medium", "gpt2-large"):
        try:
            probe_model(name)
        except Exception as e:
            print(f"\n[{name}] skip: {e}")


if __name__ == "__main__":
    main()
