"""
probe_eiffel_mlp.py
===================

Empirical validation for the planned MLP figure — the "bank of
learned patterns" / Geva-et-al key-value memory framing.

We want to answer:

  1. When the ' tower' residual (contextualized by attention) enters
     the MLP, which neurons fire?
  2. What does each firing neuron "know"? Two ways to interpret:
       - KEY direction (W_up[:, i]): tokens whose wte is most aligned
         with this neuron's input direction — "what makes this neuron
         fire"
       - VALUE direction (W_down[i, :]): tokens most promoted by the
         residual contribution this neuron writes — "what this neuron
         adds to the prediction"
  3. Do any firing neurons have VALUE directions that promote
     Eiffel-related tokens? That would be the clean pedagogical story:
     "a neuron that matches 'iron + old + Parisian attribute pattern'
     fires, and writes Eiffel-ness back."

Outputs a compact report: per layer, top-5 firing neurons at tower
position, each annotated with its top-5 key tokens and top-5 value
tokens, plus the neuron's direct contribution to ' Eiffel' logit.

If the picture is clean, we use those neuron ids in the figure. If
noisy (MLP neurons in GPT-2 small are often polysemantic), we fall
back to a more schematic figure with hand-picked illustrative labels.
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
    """Forward pass capturing:
       - residual stream entering each MLP (post-ln_2)
       - MLP pre-activation (post-c_fc, pre-gelu)
       - MLP post-activation (post-gelu, pre-c_proj)
    """
    inputs = backend.tok(prompt, return_tensors="pt")

    captures = {"ln2_in": {}, "preact": {}, "postact": {}, "mlp_out": {}}
    handles = []
    for L, block in enumerate(backend.model.transformer.h):
        # Hook 1: capture input to ln_2 (the residual entering MLP sublayer)
        def make_ln2_hook(L):
            def _h(_mod, inp, out):
                captures["ln2_in"][L] = out.detach()
            return _h
        # Actually ln_2 output IS what goes into c_fc. Output captures the
        # post-ln input to the MLP.

        # Hook 2: c_fc output = pre-activation
        def make_cfc_hook(L):
            def _h(_mod, _inp, out):
                captures["preact"][L] = out.detach()
            return _h

        # Hook 3: mlp.act output = post-GELU activation
        def make_act_hook(L):
            def _h(_mod, _inp, out):
                captures["postact"][L] = out.detach()
            return _h

        # Hook 4: mlp output = post-c_proj (what gets added to residual)
        def make_mlp_hook(L):
            def _h(_mod, _inp, out):
                captures["mlp_out"][L] = out.detach()
            return _h

        handles.append(block.ln_2.register_forward_hook(make_ln2_hook(L)))
        handles.append(block.mlp.c_fc.register_forward_hook(make_cfc_hook(L)))
        handles.append(block.mlp.act.register_forward_hook(make_act_hook(L)))
        handles.append(block.mlp.register_forward_hook(make_mlp_hook(L)))

    try:
        with torch.no_grad():
            backend.model(**inputs)
    finally:
        for h in handles:
            h.remove()

    tokens = [backend.tok.decode([tid])
              for tid in inputs.input_ids[0].tolist()]
    return captures, tokens


def interpret_key(backend: ModelBackend, w_up_col: np.ndarray,
                   k: int = 5) -> list[tuple[str, float]]:
    """Top-k tokens whose wte is most aligned with a neuron's key
    direction (column of W_up). Positive = more aligned → more firing."""
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    scores = wte @ w_up_col                # (vocab,)
    top = np.argsort(-scores)[:k]
    return [(backend.tok.decode([int(i)]), float(scores[i])) for i in top]


def interpret_value(backend: ModelBackend, w_down_row: np.ndarray,
                     k: int = 5) -> list[tuple[str, float]]:
    """Top-k tokens most promoted (logit-wise) by a neuron's value
    direction (row of W_down). We apply ln_f first so the logit
    projection matches what the model actually sees."""
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    v = torch.tensor(w_down_row, dtype=torch.float32).unsqueeze(0)
    v_ln = ln_f(v).squeeze(0).detach().cpu().numpy()
    scores = wte @ v_ln
    top = np.argsort(-scores)[:k]
    return [(backend.tok.decode([int(i)]), float(scores[i])) for i in top]


def direct_logit_contribution(backend: ModelBackend,
                                neuron_contrib_to_residual: np.ndarray,
                                target_token: str) -> float:
    """Contribution of a neuron (at one position) to the logit of
    target_token. Apply ln_f (approximate — as if this neuron's
    contribution were added on top of the current residual)."""
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    tid = backend.tok.encode(target_token, add_special_tokens=False)[0]
    # Not applying ln_f here because ln_f is non-linear; the direct
    # contribution to the logit is the linear part only. This is a
    # rough diagnostic.
    return float(neuron_contrib_to_residual @ wte[tid])


def main() -> None:
    backend = ModelBackend("gpt2")
    captures, tokens = run_with_mlp_capture(backend, SENTENCE)
    tower_pos = find_pos(tokens, TOWER_WORD)

    n_layers = backend.n_layers
    n_neurons = 3072  # GPT-2 small MLP intermediate size

    # W_up / W_down for each layer — cached as numpy arrays.
    w_up_all = []
    w_down_all = []
    for L in range(n_layers):
        block = backend.model.transformer.h[L]
        # Conv1D weight shape is (in, out), so:
        #   c_fc.weight   : (768, 3072) = W_up
        #   c_proj.weight : (3072, 768) = W_down
        w_up_all.append(block.mlp.c_fc.weight.detach().cpu().numpy())
        w_down_all.append(block.mlp.c_proj.weight.detach().cpu().numpy())

    print(f"\nSentence: {SENTENCE!r}")
    print(f"Tokens: {tokens}")
    print(f"Tower position: {tower_pos}")

    # Candidate "target tokens" for the value-interpretation pedagogical lens.
    TARGET_TOKENS = [" Eiffel", " Paris", " France", " iron", " famous",
                     " old", " steel", " tall", " tower", " landmark"]

    # --- Per-layer report ---
    summary_rows = []  # list of (rank_eiffel_among_neurons, L, neuron_id, ...)
    for L in range(n_layers):
        # Post-activation at tower position: shape (3072,)
        act = captures["postact"][L][0, tower_pos].cpu().numpy()
        top_neurons = np.argsort(-np.abs(act))[:8]  # top-8 by |activation|

        print(f"\n\n=== Layer {L} MLP at tower position ===")
        for neuron_id in top_neurons:
            a_i = float(act[neuron_id])
            w_up_col = w_up_all[L][:, neuron_id]    # (768,)
            w_down_row = w_down_all[L][neuron_id]   # (768,)
            # Neuron's direct contribution to residual stream
            # = activation * value_direction
            contrib = a_i * w_down_row
            key_top = interpret_key(backend, w_up_col, k=5)
            val_top = interpret_value(backend, w_down_row, k=5)
            eiffel_logit_delta = direct_logit_contribution(
                backend, contrib, " Eiffel")
            paris_logit_delta = direct_logit_contribution(
                backend, contrib, " Paris")

            print(f"\n  Neuron L{L}/N{neuron_id}  activation={a_i:+.2f}")
            print(f"    key (W_up[:,{neuron_id}]) top tokens: "
                  + ", ".join(f"{s!r}({sc:.2f})" for s, sc in key_top))
            print(f"    value (W_down[{neuron_id},:]) top tokens: "
                  + ", ".join(f"{s!r}({sc:.2f})" for s, sc in val_top))
            print(f"    direct logit contrib:  Eiffel={eiffel_logit_delta:+.4f}  "
                  f"Paris={paris_logit_delta:+.4f}")
            summary_rows.append({
                "L": L, "N": int(neuron_id), "act": a_i,
                "eiffel_delta": eiffel_logit_delta,
                "paris_delta": paris_logit_delta,
                "key_top": [s for s, _ in key_top],
                "val_top": [s for s, _ in val_top],
            })

    # --- Summary: neurons that push most toward ' Eiffel' ---
    print("\n\n" + "=" * 72)
    print("Top neurons by direct logit contribution to ' Eiffel'")
    print("=" * 72)
    summary_rows.sort(key=lambda r: -r["eiffel_delta"])
    for r in summary_rows[:10]:
        print(f"\n  L{r['L']}/N{r['N']}  act={r['act']:+.2f}  "
              f"+Eiffel={r['eiffel_delta']:+.4f}  +Paris={r['paris_delta']:+.4f}")
        print(f"    key:   {r['key_top']}")
        print(f"    value: {r['val_top']}")

    # --- Summary: neurons with HIGHEST |activation| AND significant Eiffel push ---
    print("\n\n" + "=" * 72)
    print("Most active neurons (|act|>1) sorted by Eiffel contribution")
    print("=" * 72)
    significant = [r for r in summary_rows if abs(r["act"]) > 1.0]
    significant.sort(key=lambda r: -r["eiffel_delta"])
    for r in significant[:10]:
        print(f"\n  L{r['L']}/N{r['N']}  act={r['act']:+.2f}  "
              f"+Eiffel={r['eiffel_delta']:+.4f}")
        print(f"    key:   {r['key_top']}")
        print(f"    value: {r['val_top']}")


if __name__ == "__main__":
    main()
