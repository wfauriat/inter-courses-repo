"""
proto_bank_logit_lens.py
========================
Exploratory probe: does GPT-2 disambiguate "bank" via context, visibly
enough to anchor a pedagogical figure?

Two sentences with the polysemous "bank":
    river context : "He sat fishing on the bank"
    money context : "He made a deposit at the bank"

For each, we extract the hidden state at the " bank" position at every
layer (0 = embedding, 1..12 = after each transformer block in gpt2-small)
and probe it two ways:

  (A) Logit-lens top-k
      Apply ln_f + lm_head to the bank hidden state. Top tokens are the
      vocabulary neighbors of this hidden state (since lm_head = wte^T,
      high-logit tokens are those with high dot-product in embedding
      space). Interpretation: "what is this hidden state most aligned
      with, among all vocab tokens?"

  (B) Cosine to water / money centroids
      Build a centroid from a handful of water-associated wte rows and
      a centroid from money-associated wte rows. Track cos(bank_L,
      water) and cos(bank_L, money) across layers. If context-based
      disambiguation is happening, the gap between these two should
      open up somewhere in the middle layers.

Run:
    source ~/.venvDS/bin/activate
    python workspace/proto_bank_logit_lens.py

This is throwaway exploration — if the signal is legible, we graduate
to a `build_interactive_attention_*.py` generator.
"""

from __future__ import annotations

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer


MODEL_NAME = "gpt2"   # bump to "gpt2-medium" if gpt2-small is too muddy

PAIRS = [
    ("river", "He sat fishing on the bank"),
    ("money", "He made a deposit at the bank"),
]

# Cluster anchor words. Leading space matters for GPT-2 BPE — most
# "content" tokens appear post-space in training. We filter down to
# single-token items after encoding.
CLUSTER_WATER = [
    " river", " water", " shore", " stream", " beach", " lake",
    " edge", " creek", " pond", " fishing", " boat",
]
CLUSTER_MONEY = [
    " money", " cash", " account", " deposit", " loan", " credit",
    " teller", " check", " savings", " financial", " customer",
]

TOP_K = 8
# Layers to print top-k for (to keep output compact). Includes embed (0),
# early, mid, late. gpt2-small has 12 blocks, so hidden_states has 13 entries.
TOPK_LAYERS = [0, 1, 2, 4, 6, 8, 10, 11, 12]


def single_token_ids(tok, words):
    kept_words, kept_ids = [], []
    dropped = []
    for w in words:
        ids = tok.encode(w, add_special_tokens=False)
        if len(ids) == 1:
            kept_words.append(w)
            kept_ids.append(ids[0])
        else:
            dropped.append((w, ids))
    return kept_words, kept_ids, dropped


def find_bank_index(tokens):
    for i, t in enumerate(tokens):
        if t.strip().lower() == "bank":
            return i
    raise ValueError(f"'bank' not found in tokens {tokens}")


def run_probe(model, tok, sentence, water_dir, money_dir):
    ids = tok.encode(sentence, return_tensors="pt")
    tokens = [tok.decode([int(t)]) for t in ids[0]]
    bank_idx = find_bank_index(tokens)

    with torch.no_grad():
        out = model(ids, output_hidden_states=True)

    # hidden: (n_layers+1, seq, d_model)
    hidden = torch.stack(out.hidden_states, dim=0).squeeze(1)
    bank_traj = hidden[:, bank_idx, :]  # (L+1, d)

    # ----- ln_f placement probe (copy of 07_layer_by_layer.py trick) -----
    h_last = bank_traj[-1]
    true_logits = out.logits[0, bank_idx]
    with torch.no_grad():
        diff_pre = (model.lm_head(model.transformer.ln_f(h_last)) - true_logits).abs().max().item()
        diff_post = (model.lm_head(h_last) - true_logits).abs().max().item()
    last_is_post = diff_post < diff_pre

    with torch.no_grad():
        if last_is_post:
            normed = torch.cat(
                [model.transformer.ln_f(bank_traj[:-1]), bank_traj[-1:]], dim=0
            )
        else:
            normed = model.transformer.ln_f(bank_traj)
        logits = model.lm_head(normed)                # (L+1, vocab)
        probs = torch.softmax(logits, dim=-1)

    # Top-k tokens per layer
    topk_per_layer = []
    for L in range(probs.shape[0]):
        top_vals, top_ids = probs[L].topk(TOP_K)
        topk_per_layer.append([
            (tok.decode([int(tid)]), float(v))
            for tid, v in zip(top_ids, top_vals)
        ])

    # Cosine to cluster centroids (no ln_f — raw residual-stream direction).
    bank_unit = bank_traj / (bank_traj.norm(dim=-1, keepdim=True) + 1e-9)
    cos_water = (bank_unit @ water_dir).cpu().numpy()
    cos_money = (bank_unit @ money_dir).cpu().numpy()

    return {
        "tokens": tokens,
        "bank_idx": bank_idx,
        "topk": topk_per_layer,
        "cos_water": cos_water,
        "cos_money": cos_money,
        "last_is_post_lnf": last_is_post,
    }


def main():
    print(f"Loading {MODEL_NAME} ...", flush=True)
    tok = GPT2Tokenizer.from_pretrained(MODEL_NAME)
    model = GPT2LMHeadModel.from_pretrained(MODEL_NAME)
    model.eval()

    # Build cluster centroids from wte rows (non-contextual word vectors).
    water_words, water_ids, water_dropped = single_token_ids(tok, CLUSTER_WATER)
    money_words, money_ids, money_dropped = single_token_ids(tok, CLUSTER_MONEY)
    print(f"Water cluster kept ({len(water_words)}): {water_words}")
    if water_dropped:
        print(f"  dropped multi-token: {water_dropped}")
    print(f"Money cluster kept ({len(money_words)}): {money_words}")
    if money_dropped:
        print(f"  dropped multi-token: {money_dropped}")

    wte = model.transformer.wte.weight.detach()  # (vocab, d)
    water_centroid = wte[water_ids].mean(dim=0)
    money_centroid = wte[money_ids].mean(dim=0)
    water_dir = water_centroid / (water_centroid.norm() + 1e-9)
    money_dir = money_centroid / (money_centroid.norm() + 1e-9)

    results = {}
    for label, sent in PAIRS:
        print(f"\n>>> {label} context: {sent!r}")
        r = run_probe(model, tok, sent, water_dir, money_dir)
        print(f"    tokens: {r['tokens']}")
        print(f"    'bank' at position {r['bank_idx']}")
        print(f"    last-hidden-is-post-ln_f: {r['last_is_post_lnf']}")
        results[label] = r

    # ------------------------------------------------------------------
    # Report 1: cosine trajectories
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("COSINE SIMILARITY of bank hidden state to cluster centroids")
    print("=" * 72)
    print(f"{'layer':>6}  "
          f"{'river-ctx cos(H,water)':>24}  {'cos(H,money)':>14}  {'Δ_r':>8}  "
          f"| {'money-ctx cos(H,water)':>24}  {'cos(H,money)':>14}  {'Δ_m':>8}")
    r = results["river"]
    m = results["money"]
    n_layers = len(r["cos_water"])
    for L in range(n_layers):
        name = "embed" if L == 0 else f"L{L:02d}"
        rw, rm = r["cos_water"][L], r["cos_money"][L]
        mw, mm = m["cos_water"][L], m["cos_money"][L]
        dr = rw - rm
        dm = mw - mm
        # Star the layer if the sign of the gap matches expectation:
        #   river ctx → cos_water > cos_money  (dr > 0)
        #   money ctx → cos_money > cos_water  (dm < 0)
        star_r = "*" if dr > 0 else " "
        star_m = "*" if dm < 0 else " "
        print(f"{name:>6}  "
              f"{rw:>24.4f}  {rm:>14.4f}  {dr:>+8.4f}{star_r} "
              f"| {mw:>24.4f}  {mm:>14.4f}  {dm:>+8.4f}{star_m}")

    # ------------------------------------------------------------------
    # Report 2: side-by-side top-k logit-lens at selected layers
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("TOP-K logit-lens for the 'bank' position (what the hidden state 'looks like'")
    print("in vocabulary terms). Interpretation: tokens ranked by dot-product with wte.")
    print("=" * 72)
    for L in TOPK_LAYERS:
        if L >= n_layers:
            continue
        name = "embed" if L == 0 else f"L{L:02d}"
        print(f"\n--- layer {name} ---")
        for label in ("river", "money"):
            top = results[label]["topk"][L]
            items = "  ".join(f"{t!r:>14}({p:.2%})" for t, p in top[:TOP_K])
            print(f"  {label:>6}: {items}")


if __name__ == "__main__":
    main()
