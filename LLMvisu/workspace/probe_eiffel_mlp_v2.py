"""
probe_eiffel_mlp_v2.py
======================

Follow-up probe. v1 found that individual MLP neurons in GPT-2 small are
polysemantic — top key/value interpretations are noisy strings
("iton", " Luffy", "netflix") that don't support a clean
"this neuron detects pattern X" figure.

This script asks two more tractable questions:

  1. Sparsity — at the ' tower' position, how many of the 3072
     neurons are strongly active per layer? This validates the
     "sparse pattern library" framing even if we can't label each
     pattern.

  2. Aggregate MLP output — the sum over all 3072 neurons at a given
     layer produces a single 768-d delta added to the residual. Does
     this delta's logit-lens look like "Eiffel"? That would let us
     honestly tell the "MLP writes Eiffel-ness back" story at the
     block level, even when individual neurons don't interpret cleanly.

  3. Top neurons by actual contribution magnitude — not |activation|
     alone, but |activation| * ||W_down_row||, which is how much each
     neuron actually pushes on the residual. Check if any have clean
     value interpretations (ignoring 'bias-like' neurons that light
     up punctuation).
"""

from __future__ import annotations

import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention_workshop import ModelBackend


SENTENCE = "In Paris today, I climbed the 400+ steps of the famous old iron tower."
TOWER_WORD = "tower"


def find_pos(tokens: list[str], word: str) -> int:
    for i, t in enumerate(tokens):
        if t.strip() == word:
            return i
    raise ValueError(f"no ' {word}' in {tokens}")


def run_with_mlp_capture(backend: ModelBackend, prompt: str):
    inputs = backend.tok(prompt, return_tensors="pt")
    captures = {"postact": {}, "mlp_out": {}}
    handles = []
    for L, block in enumerate(backend.model.transformer.h):
        def make_act_hook(L):
            def _h(_mod, _inp, out):
                captures["postact"][L] = out.detach()
            return _h

        def make_mlp_hook(L):
            def _h(_mod, _inp, out):
                captures["mlp_out"][L] = out.detach()
            return _h

        handles.append(block.mlp.act.register_forward_hook(make_act_hook(L)))
        handles.append(block.mlp.register_forward_hook(make_mlp_hook(L)))
    try:
        with torch.no_grad():
            backend.model(**inputs)
    finally:
        for h in handles:
            h.remove()
    tokens = [backend.tok.decode([tid]) for tid in inputs.input_ids[0].tolist()]
    return captures, tokens


def logit_lens_top(backend: ModelBackend, delta: np.ndarray, k: int = 10,
                     apply_ln: bool = True):
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    if apply_ln:
        r = torch.tensor(delta, dtype=torch.float32).unsqueeze(0)
        r = ln_f(r).squeeze(0).detach().cpu().numpy()
    else:
        r = delta
    logits = wte @ r
    order = np.argsort(-logits)[:k]
    return [(backend.tok.decode([int(i)]), float(logits[i])) for i in order]


def rank_of(backend: ModelBackend, delta: np.ndarray, word: str,
             apply_ln: bool = True) -> int:
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    r = torch.tensor(delta, dtype=torch.float32).unsqueeze(0)
    if apply_ln:
        r = ln_f(r)
    r = r.squeeze(0).detach().cpu().numpy()
    logits = wte @ r
    ids = backend.tok.encode(word, add_special_tokens=False)
    tid = ids[0]
    return int((logits > logits[tid]).sum())


def main() -> None:
    backend = ModelBackend("gpt2")
    captures, tokens = run_with_mlp_capture(backend, SENTENCE)
    tower_pos = find_pos(tokens, TOWER_WORD)
    n_layers = backend.n_layers

    print(f"Sentence: {SENTENCE!r}")
    print(f"Tokens: {tokens}")
    print(f"Tower pos: {tower_pos}\n")

    # --- 1. Sparsity of MLP neuron activations at tower position ---
    print("=" * 72)
    print("1. MLP neuron activation sparsity at tower position")
    print("=" * 72)
    print(f"{'Layer':>6}  {'|a|>3':>6}  {'|a|>1':>6}  {'|a|>0.5':>8}  "
          f"{'>0.1':>6}  {'max |a|':>8}  {'mean |a|':>10}")
    for L in range(n_layers):
        act = captures["postact"][L][0, tower_pos].cpu().numpy()
        abs_a = np.abs(act)
        gt3 = int((abs_a > 3.0).sum())
        gt1 = int((abs_a > 1.0).sum())
        gt05 = int((abs_a > 0.5).sum())
        gt01 = int((abs_a > 0.1).sum())
        print(f"  L{L:>2}  {gt3:>6}  {gt1:>6}  {gt05:>8}  {gt01:>6}  "
              f"{float(abs_a.max()):>8.2f}  {float(abs_a.mean()):>10.4f}")

    # --- 2. Aggregate MLP output logit-lens per layer ---
    print("\n" + "=" * 72)
    print("2. Aggregate MLP output at tower position — logit-lens top-10")
    print("    and rank of ' Eiffel' in that distribution")
    print("=" * 72)
    for L in range(n_layers):
        delta = captures["mlp_out"][L][0, tower_pos].cpu().numpy()
        top = logit_lens_top(backend, delta, k=10, apply_ln=True)
        eiffel_rank = rank_of(backend, delta, " Eiffel", apply_ln=True)
        paris_rank = rank_of(backend, delta, " Paris", apply_ln=True)
        print(f"\n  L{L}  top-10: " + ", ".join(f"{s!r}" for s, _ in top))
        print(f"       Eiffel rank: {eiffel_rank},  Paris rank: {paris_rank}")

    # --- 3. Top neurons by full contribution magnitude ---
    print("\n" + "=" * 72)
    print("3. Top neurons by |activation * ||W_down[i,:]|| at tower position")
    print("   (i.e. actual push on residual, not just activation magnitude)")
    print("=" * 72)
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    eiffel_id = backend.tok.encode(" Eiffel", add_special_tokens=False)[0]
    paris_id = backend.tok.encode(" Paris", add_special_tokens=False)[0]

    for L in range(n_layers):
        act = captures["postact"][L][0, tower_pos].cpu().numpy()
        block = backend.model.transformer.h[L]
        w_down = block.mlp.c_proj.weight.detach().cpu().numpy()  # (3072, 768)
        w_up = block.mlp.c_fc.weight.detach().cpu().numpy()      # (768, 3072)
        norms = np.linalg.norm(w_down, axis=1)                   # (3072,)
        push_magnitude = np.abs(act) * norms                     # (3072,)
        top = np.argsort(-push_magnitude)[:5]
        print(f"\n  L{L}:")
        for n_id in top:
            a_i = float(act[n_id])
            val_dir = w_down[n_id]
            # Value top tokens (by direct logit contribution, no ln_f):
            val_scores = wte @ val_dir
            val_top = np.argsort(-val_scores)[:5]
            val_toks = [backend.tok.decode([int(i)]) for i in val_top]
            # Key top tokens
            key_dir = w_up[:, n_id]
            key_scores = wte @ key_dir
            key_top = np.argsort(-key_scores)[:5]
            key_toks = [backend.tok.decode([int(i)]) for i in key_top]
            # Direct Eiffel / Paris contribution
            eiffel_push = a_i * val_dir[eiffel_id] if False else float(a_i * (wte[eiffel_id] @ val_dir))
            paris_push  = float(a_i * (wte[paris_id] @ val_dir))
            print(f"    N{n_id:>5}  a={a_i:+.2f}  push={push_magnitude[n_id]:.2f}  "
                  f"+Eiffel={eiffel_push:+.3f}  +Paris={paris_push:+.3f}")
            print(f"          key:   {key_toks}")
            print(f"          value: {val_toks}")


if __name__ == "__main__":
    main()
