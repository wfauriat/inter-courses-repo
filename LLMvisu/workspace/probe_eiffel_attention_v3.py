"""
probe_eiffel_attention_v3.py
============================

Third round. Lessons from v1:

  - Attention pattern at ' tower' is clean — pedagogically usable.
  - The "infer Eiffel from {old, steel, 400+ steps}" jump is too big
    for GPT-2 small: no Eiffel in top-10 next-token predictions, logit
    lens at tower position never names it.

This round: per user suggestion, give the model a stronger cue.
Variants:

  - SENT_PARIS  : explicit 'in Paris' locative → should steer reliably
  - SENT_FRENCH : 'French tower' → a softer cue
  - SENT_IRON   : 'iron' instead of 'steel' (Eiffel is wrought iron)
  - SENT_IRON_P : iron + Paris together
  - SENT_CITY   : 'in the french capital'

For each, check:
  (1) next-token after "... The tower I am referring to is the"
  (2) logit-lens at ' tower' position — does 'Eiffel' start surfacing?
  (3) attention at ' tower' — does it pick up on Paris / French / iron
      the same way it picked up on steel / old / famous in v1?

The question is: can we find a sentence where
  (a) attention clearly aggregates distinctive tokens into the tower
      position (the pedagogical beat we want to show),
  (b) the result is recognizably Eiffel-ish in logit-lens /
      next-token output (so the figure isn't a lie).

If yes: great, use that sentence. If not: fall back to a shorter
pointed sentence purely for the attention panel, and use mock
geometry for any embedding-space drift story.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention_workshop import ModelBackend


SENTENCES = {
    "steel":       "I climbed the 400+ steps of the famous old steel tower today.",
    "paris":       "I climbed the 400+ steps of the famous old steel tower in Paris today.",
    "french":      "I climbed the 400+ steps of the famous old steel French tower today.",
    "iron":        "I climbed the 400+ steps of the famous old iron tower today.",
    "iron_paris":  "I climbed the 400+ steps of the famous old iron tower in Paris today.",
    "french_cap":  "I climbed the 400+ steps of the famous old iron tower in the French capital today.",
    # A pointed factual probe: if GPT-2 knows Eiffel at all, this
    # minimal sentence should elicit it.
    "pointed":     "The famous iron tower in Paris is called the",
}

CONT = " The tower I am referring to is the"


def find_tower(tokens: list[str]) -> int:
    for i, t in enumerate(tokens):
        if t.strip() == "tower":
            return i
    raise ValueError("no ' tower' token")


def topk_next(backend: ModelBackend, prompt: str, k: int = 10):
    inputs = backend.tok(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = backend.model(**inputs).logits[0, -1]
    t = torch.topk(logits, k)
    return [(backend.tok.decode([int(i)]), float(v))
            for i, v in zip(t.indices, t.values)]


def logit_lens_tower(backend: ModelBackend, prompt: str, k: int = 8):
    inputs = backend.tok(prompt, return_tensors="pt")
    with torch.no_grad():
        out = backend.model(**inputs, output_hidden_states=True)
    hs = [h[0].cpu().numpy() for h in out.hidden_states]
    tokens = [backend.tok.decode([tid]) for tid in inputs.input_ids[0].tolist()]
    pos = find_tower(tokens)
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    rows = []
    for resid in hs:
        r = torch.tensor(resid[pos], dtype=torch.float32).unsqueeze(0)
        r = ln_f(r).squeeze(0).detach().cpu().numpy()
        logits = wte @ r
        top_ids = np.argsort(-logits)[:k]
        rows.append([(backend.tok.decode([int(i)]), float(logits[i]))
                     for i in top_ids])
    return rows, tokens, pos


def rank_of(backend: ModelBackend, word: str, residual: np.ndarray,
            apply_ln: bool = True) -> int:
    """Rank of `word` in the logit-lens distribution, 0 = top."""
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    r = torch.tensor(residual, dtype=torch.float32).unsqueeze(0)
    if apply_ln:
        r = ln_f(r)
    r = r.squeeze(0).detach().cpu().numpy()
    logits = wte @ r
    ids = backend.tok.encode(word, add_special_tokens=False)
    if not ids:
        return -1
    target = ids[0]
    return int((logits > logits[target]).sum())


def attention_at_tower(backend: ModelBackend, prompt: str, top_k: int = 4):
    inputs = backend.tok(prompt, return_tensors="pt")
    with torch.no_grad():
        out = backend.model(**inputs, output_attentions=True)
    attn = np.stack([a[0].cpu().numpy() for a in out.attentions])
    tokens = [backend.tok.decode([tid]) for tid in inputs.input_ids[0].tolist()]
    pos = find_tower(tokens)
    print(f"  tokens: {tokens}")
    print(f"  pos of ' tower': {pos}")
    for L in range(attn.shape[0]):
        row = attn[L, :, pos, :].mean(axis=0).copy()
        row[pos] = 0.0
        row[0] = 0.0  # attention sink
        order = np.argsort(-row)[:top_k]
        pieces = [f"{tokens[j]!r}={row[j]:.2f}" for j in order]
        print(f"    L{L:2d}: " + "  ".join(pieces))


def main() -> None:
    backend = ModelBackend("gpt2")

    # -------------------------------------------------------------------
    # Section A: next-token after the nudge. Is Eiffel ever in top-10?
    # -------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("A. Next-token after '<sentence>.<nudge>' — looking for ' Eiffel'")
    print("=" * 72)
    for tag, sent in SENTENCES.items():
        prompt = sent + CONT if tag != "pointed" else sent
        top = topk_next(backend, prompt, k=12)
        eiffel_rank = next((r for r, (s, _) in enumerate(top)
                            if "Eiffel" in s or "eiffel" in s), None)
        print(f"\n[{tag}] {prompt!r}")
        for r, (s, v) in enumerate(top):
            flag = "  <-- Eiffel" if ("Eiffel" in s or "eiffel" in s) else ""
            print(f"  {r+1:2d}. {s!r:>14}  logit={v:+.3f}{flag}")
        print(f"  [Eiffel in top-12? {'YES rank ' + str(eiffel_rank + 1) if eiffel_rank is not None else 'no'}]")

    # -------------------------------------------------------------------
    # Section B: logit-lens at ' tower' across layers. Where does
    # ' Eiffel' sit in rank?
    # -------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("B. Logit-lens at ' tower' — rank of ' Eiffel' per layer")
    print("=" * 72)
    for tag, sent in SENTENCES.items():
        if tag == "pointed":
            continue
        try:
            rows, tokens, pos = logit_lens_tower(backend, sent, k=6)
        except ValueError:
            continue
        # Show rank of ' Eiffel', ' Paris', ' tower' across layers.
        print(f"\n[{tag}]  (prompt: {sent!r})")
        print(f"  tokens: {tokens}")

        wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
        ln_f = backend.model.transformer.ln_f
        # Re-run to get residuals directly.
        inputs = backend.tok(sent, return_tensors="pt")
        with torch.no_grad():
            out = backend.model(**inputs, output_hidden_states=True)
        hs = [h[0].cpu().numpy() for h in out.hidden_states]

        targets = [" Eiffel", " Paris", " France", " iron", " steel",
                   " tower", " skyscraper"]
        header = "        " + "  ".join(f"{t.strip():>10}" for t in targets)
        print(header)
        for L, resid in enumerate(hs):
            parts = []
            for t in targets:
                parts.append(f"{rank_of(backend, t, resid[pos]):>10d}")
            print(f"  L{L:2d}  " + "  ".join(parts))
        # Also show the actual top-8 at mid and final layer
        print(f"  top-8 at L6: " + ", ".join(f"{s!r}" for s, _ in rows[6]))
        print(f"  top-8 at L12: " + ", ".join(f"{s!r}" for s, _ in rows[12]))

    # -------------------------------------------------------------------
    # Section C: attention at ' tower' for best-scoring sentence.
    # -------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("C. Attention at ' tower' — mean-over-heads per layer, for the")
    print("   iron_paris sentence (likeliest to produce clean attribution)")
    print("=" * 72)
    attention_at_tower(backend, SENTENCES["iron_paris"])
    print()
    print("-- same for 'paris' variant --")
    attention_at_tower(backend, SENTENCES["paris"])


if __name__ == "__main__":
    main()
