"""
probe_eiffel_attention_v4.py
============================

v3 finding: the 'Paris' cue was wasted because it appeared AFTER
' tower' in the sentence — causal masking means ' tower' can't see
it. Fix: put all the attribution cues BEFORE ' tower'.

This round: try reordered sentences and measure the Eiffel logit-lens
rank drop at the ' tower' position. If the drop is deeper (e.g. into
top-100 or better) when Paris is accessible, we have a great
data-backed figure. Also re-measure attention patterns now that Paris
is reachable.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention_workshop import ModelBackend


SENTENCES = {
    "v3_iron_paris":  "I climbed the 400+ steps of the famous old iron tower in Paris today.",
    # Reordered so every cue is BEFORE 'tower':
    "v4_paris_first": "In Paris today, I climbed the 400+ steps of the famous old iron tower.",
    "v4_paris_comma": "Yesterday in Paris, I climbed 400+ steps of a famous old iron tower.",
    "v4_inline":      "I visited Paris and climbed the 400+ steps of the famous old iron tower.",
    # Short punchy version:
    "v4_short":       "In Paris, the famous old iron tower",
    "v4_shorter":     "The famous old Parisian iron tower",
}

# Second-sentence probes — given that the first sentence has steered the
# representation toward "Eiffel-ish", ask the model to commit. The target
# prediction is either 'Gustave' (architect's first name) or 'Eiffel'.
#
# Per the user's suggestion: this is pedagogically a bit 'cheating' —
# we're giving the model a direct question that exposes the latent
# Eiffel-identification — but the whole point of the figure is to make
# the mechanism *visible*, and this is the cleanest way.
CONTINUATIONS = [
    " I think it was built in 1889 by",
    " It was built in 1889 by",
    " It was constructed in 1889 by a man named",
    " I think it was built in the year",
    " The engineer who built it was named",
    " The name of this famous tower is",
    " This tower is called the",
]


def find_tower(tokens: list[str]) -> int:
    for i, t in enumerate(tokens):
        if t.strip() == "tower":
            return i
    raise ValueError("no ' tower' token")


def rank_of_token(model, tok, residual: np.ndarray, target_word: str) -> int:
    wte = model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = model.transformer.ln_f
    r = torch.tensor(residual, dtype=torch.float32).unsqueeze(0)
    r = ln_f(r).squeeze(0).detach().cpu().numpy()
    logits = wte @ r
    ids = tok.encode(target_word, add_special_tokens=False)
    if not ids:
        return -1
    target = ids[0]
    return int((logits > logits[target]).sum())


def probe_sentence(backend: ModelBackend, tag: str, sent: str):
    inputs = backend.tok(sent, return_tensors="pt")
    with torch.no_grad():
        out = backend.model(**inputs,
                            output_hidden_states=True,
                            output_attentions=True)
    hs = [h[0].cpu().numpy() for h in out.hidden_states]
    attn = np.stack([a[0].cpu().numpy() for a in out.attentions])
    tokens = [backend.tok.decode([tid])
              for tid in inputs.input_ids[0].tolist()]
    try:
        pos = find_tower(tokens)
    except ValueError:
        print(f"[{tag}] skip: no ' tower' in {tokens}")
        return

    print(f"\n\n=== [{tag}] {sent!r}")
    print(f"  tokens: {tokens}")
    print(f"  ' tower' at pos {pos}")

    # --- (A) Rank of ' Eiffel' across layers at tower position ---
    print("\n  Logit-lens rank per layer (lower = more present):")
    targets = [" Eiffel", " Paris", " France", " iron", " tower", " skyscraper"]
    header = "        " + "  ".join(f"{t.strip():>10}" for t in targets)
    print(header)
    for L, resid in enumerate(hs):
        ranks = [rank_of_token(backend.model, backend.tok, resid[pos], t)
                 for t in targets]
        print(f"  L{L:2d}  " + "  ".join(f"{r:>10d}" for r in ranks))

    # --- (B) Mean attention at ' tower' per layer ---
    print("\n  Mean attention at ' tower' — top-4 attended tokens per layer:")
    for L in range(attn.shape[0]):
        row = attn[L, :, pos, :].mean(axis=0).copy()
        row[pos] = 0.0
        row[0] = 0.0  # attention sink at position 0
        order = np.argsort(-row)[:5]
        pieces = [f"{tokens[j]!r}={row[j]:.2f}" for j in order]
        print(f"    L{L:2d}: " + "  ".join(pieces))

    # --- (C) Strongest single head attending to content words ---
    content = []
    for want in ("Paris", "iron", "old", "famous", "400", "steps"):
        for i, t in enumerate(tokens):
            if t.strip() == want:
                content.append((want, i))
                break
    if content:
        n_layers, n_heads = attn.shape[0], attn.shape[1]
        best = []  # (score, L, H, word)
        for L in range(n_layers):
            for H in range(n_heads):
                for word, i in content:
                    best.append((attn[L, H, pos, i], L, H, word, i))
        best.sort(reverse=True)
        print("\n  Top single-(layer, head) attentions to content words:")
        for s, L, H, word, i in best[:8]:
            print(f"    {word!r} (pos {i})  L{L:2d}H{H:2d}  α={s:.3f}")


def probe_continuations(backend: ModelBackend, base: str, tag: str) -> None:
    print(f"\n\n### [{tag}] Next-token probes with various continuations")
    print(f"### base sentence: {base!r}")
    for cont in CONTINUATIONS:
        prompt = base + cont
        inputs = backend.tok(prompt, return_tensors="pt")
        with torch.no_grad():
            logits = backend.model(**inputs).logits[0, -1]
        t = torch.topk(logits, 15)
        hits = []
        for r, (tid, sc) in enumerate(zip(t.indices.tolist(), t.values.tolist())):
            s = backend.tok.decode([tid])
            mark = ""
            for needle in ("Eiffel", "Gustave", "Gust", "Eif", "1889", "1887", "89", "88"):
                if needle in s:
                    mark = f"  <-- {needle}"
                    hits.append((needle, r+1, s, sc))
                    break
        print(f"\n  {prompt!r}")
        for r, (tid, sc) in enumerate(zip(t.indices.tolist(), t.values.tolist())):
            s = backend.tok.decode([tid])
            mark = ""
            for needle in ("Eiffel", "Gustave", "Gust", "Eif", "1889", "1887", "89", "88"):
                if needle in s:
                    mark = f"  <-- {needle}"
                    break
            print(f"    {r+1:2d}. {s!r:>14}  logit={sc:+.3f}{mark}")
        if hits:
            summary = "; ".join(f"{n}@{r}" for n, r, _, _ in hits)
            print(f"    [HIT: {summary}]")
        else:
            print(f"    [no Eiffel/Gustave/1889 in top-15]")


def main() -> None:
    backend = ModelBackend("gpt2")
    for tag, sent in SENTENCES.items():
        probe_sentence(backend, tag, sent)

    # Also probe continuations on the strongest sentence(s) — see if
    # "I think it was built in 1889 by" surfaces 'Eiffel' or 'Gustave'.
    print("\n\n" + "=" * 72)
    print("CONTINUATION PROBES")
    print("=" * 72)
    probe_continuations(backend, SENTENCES["v4_paris_first"], "paris_first")
    probe_continuations(backend, SENTENCES["v3_iron_paris"], "iron_paris")


if __name__ == "__main__":
    main()
