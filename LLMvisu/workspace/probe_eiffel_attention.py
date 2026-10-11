"""
probe_eiffel_attention.py
=========================

Empirical validation for the planned "Eiffel tower" attention figure.

The pedagogical story we want to tell:
    "I climbed the 400+ steps of the famous old steel tower today."
                                        ~~~~~~~~~~~~~~~ tower
    As the transformer processes this sentence, the residual at the
    `tower` position gets steered from a generic tower-cluster centroid
    toward something close to "Eiffel Tower", because attention mixes
    in features from `old`, `steel`, `400+`, `steps`.

Before we build a data-backed SVG off that story, we need to confirm
GPT-2 actually does this. Otherwise the figure is a lie.

What this script checks:

  1. Tokenization — can we locate the ` tower` token position?
  2. Next-token prediction — given "... old steel tower today. The tower
     I am referring to is the", does "Eiffel" rank high?
  3. Logit lens — at each layer, project the `tower` residual through
     the unembedding and print the top-k tokens. Does Eiffel / Paris /
     France / France-ish climb the ranks as layers process?
  4. Cosine similarity — residual at `tower` position across layers
     vs. wte of landmark words: Eiffel, Pisa, Big, Burj, Empire,
     skyscraper, monument, spire, obelisk, tower itself.
  5. Attention inspection — for each layer, which tokens does ` tower`
     attend to most heavily? Looking for clear attention to `old`,
     `steel`, `400`, `steps`.
  6. Contrastive — a sentence that describes a SMALL wooden garden
     tower should NOT steer `tower` toward Eiffel.

If (2) and (3) show clear Eiffel-ness emerging, the figure is honest.
If not, we reconsider (different attributes, different anchor, or mock
geometry).
"""

from __future__ import annotations

import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from attention_workshop import ModelBackend


# ---------------------------------------------------------------------------
# Prompts under test
# ---------------------------------------------------------------------------

SENT_FULL = "I climbed the 400+ steps of the famous old steel tower today."
SENT_FULL_Q = (SENT_FULL +
               " The tower I am referring to is the")

# Contrastive: same structure, opposite attributes.
SENT_WOOD = "I climbed the 5 steps of a short wooden garden tower today."
SENT_WOOD_Q = SENT_WOOD + " The tower I am referring to is the"

# Ablation chain — progressively strip attributes.
SENT_ABL = {
    "full":    SENT_FULL,
    "no_400":  "I climbed the steps of the famous old steel tower today.",
    "no_steel": "I climbed the 400+ steps of the famous old tower today.",
    "no_old":  "I climbed the 400+ steps of the famous steel tower today.",
    "bare":    "I looked at a tower today.",
}


# Landmarks we want to track similarity against. Using leading-space
# variants since GPT-2's BPE puts a space at the start of mid-sentence
# tokens.
LANDMARK_WORDS = [
    " Eiffel", " Paris", " France",
    " Pisa", " Burj", " Empire", " Tokyo", " Big", " London",
    " tower", " skyscraper", " monument", " spire", " obelisk",
    " building", " pyramid", " church",
    " wooden", " steel",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_tower_position(tokens: list[str]) -> int:
    """Index of the ' tower' token in the tokenization. Raises if missing."""
    for i, t in enumerate(tokens):
        if t.strip() == "tower":
            return i
    raise ValueError(f"no ' tower' token in {tokens!r}")


def get_hidden_states(backend: ModelBackend, prompt: str) -> np.ndarray:
    """Return residual-stream states at each layer boundary.

    Shape: (n_layers + 1, seq, n_embd).
    Index 0 = embeddings (after wte + wpe), index k = residual *after*
    block k-1.
    """
    inputs = backend.tok(prompt, return_tensors="pt")
    with torch.no_grad():
        out = backend.model(**inputs, output_hidden_states=True,
                            output_attentions=True)
    hs = np.stack([h[0].cpu().numpy() for h in out.hidden_states])
    attn = np.stack([a[0].cpu().numpy() for a in out.attentions])
    return hs, attn, inputs.input_ids[0].tolist()


def wte_for(backend: ModelBackend, words: list[str]) -> dict[str, np.ndarray]:
    """Return wte embedding per word. Words with multi-token encodings
    get their FIRST token's embedding (for 'Eiffel' etc., one token)."""
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    out = {}
    for w in words:
        ids = backend.tok.encode(w, add_special_tokens=False)
        if not ids:
            continue
        out[w] = wte[ids[0]]
    return out


def logit_lens_topk(backend: ModelBackend, residual: np.ndarray,
                    k: int = 8) -> list[tuple[str, float]]:
    """Project a (768,) residual through the unembedding, return top-k
    tokens as (decoded_str, logit)."""
    wte = backend.model.transformer.wte.weight.detach().cpu().numpy()
    ln_f = backend.model.transformer.ln_f
    r = torch.tensor(residual, dtype=torch.float32).unsqueeze(0)
    r = ln_f(r).squeeze(0).detach().cpu().numpy()
    logits = wte @ r
    top = np.argsort(-logits)[:k]
    return [(backend.tok.decode([int(i)]), float(logits[i])) for i in top]


def cos(a: np.ndarray, b: np.ndarray) -> float:
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

def probe_next_token(backend: ModelBackend, prompt: str, tag: str,
                     k: int = 10) -> None:
    inputs = backend.tok(prompt, return_tensors="pt")
    with torch.no_grad():
        logits = backend.model(**inputs).logits[0, -1]
    top = torch.topk(logits, k)
    print(f"\n[{tag}] Next-token after: {prompt!r}")
    for rank, (tid, sc) in enumerate(zip(top.indices.tolist(),
                                         top.values.tolist())):
        print(f"  {rank+1:2d}. {backend.tok.decode([tid])!r:>14}  "
              f"logit={sc:+.3f}")


def probe_logit_lens_at_tower(backend: ModelBackend, prompt: str, tag: str,
                              k: int = 6) -> None:
    hs, _, ids = get_hidden_states(backend, prompt)
    tokens = [backend.tok.decode([tid]) for tid in ids]
    pos = find_tower_position(tokens)
    print(f"\n[{tag}] Logit-lens at ' tower' (pos {pos}) across layers "
          f"(prompt: {prompt!r})")
    print(f"  tokens: {tokens}")
    n_layers = hs.shape[0]
    # Print every 2nd layer to keep output readable, plus final.
    layers_to_show = list(range(0, n_layers, 2))
    if n_layers - 1 not in layers_to_show:
        layers_to_show.append(n_layers - 1)
    for L in layers_to_show:
        residual = hs[L, pos]
        top = logit_lens_topk(backend, residual, k=k)
        words = "  ".join(f"{w!r}" for w, _ in top)
        print(f"  L{L:2d}: {words}")


def probe_cosine_landmarks(backend: ModelBackend, prompt: str, tag: str
                           ) -> None:
    hs, _, ids = get_hidden_states(backend, prompt)
    tokens = [backend.tok.decode([tid]) for tid in ids]
    pos = find_tower_position(tokens)
    wte = wte_for(backend, LANDMARK_WORDS)

    print(f"\n[{tag}] Cosine(' tower' residual, wte[landmark]) across layers")
    header = "        " + "  ".join(f"{w.strip():>8}" for w in LANDMARK_WORDS)
    print(header)
    n_layers = hs.shape[0]
    layers_to_show = [0, 2, 4, 6, 8, 10, n_layers - 1]
    for L in layers_to_show:
        residual = hs[L, pos]
        row = "  ".join(f"{cos(residual, wte[w]):>+8.3f}"
                        for w in LANDMARK_WORDS if w in wte)
        print(f"  L{L:2d}  {row}")


def probe_attention_at_tower(backend: ModelBackend, prompt: str, tag: str,
                             top_k: int = 4) -> None:
    _, attn, ids = get_hidden_states(backend, prompt)
    tokens = [backend.tok.decode([tid]) for tid in ids]
    pos = find_tower_position(tokens)
    n_layers, n_heads = attn.shape[0], attn.shape[1]

    print(f"\n[{tag}] Attention at ' tower' (pos {pos}) — top-{top_k} "
          f"attended tokens per (layer, head)")
    print(f"  tokens: {tokens}")
    # Aggregate across heads per layer — mean attention pattern for tower.
    print("  MEAN-over-heads per layer:")
    for L in range(n_layers):
        row = attn[L, :, pos, :].mean(axis=0)  # average heads
        # Exclude self and position 0 (attention sink).
        masked = row.copy()
        masked[pos] = 0.0
        masked[0] = 0.0
        order = np.argsort(-masked)[:top_k]
        pieces = [f"{tokens[j]!r}={row[j]:.2f}" for j in order]
        print(f"    L{L:2d}: " + "  ".join(pieces))

    # Also find the single (layer, head) where attention to the "content"
    # context words (old, steel, 400, steps) is strongest.
    content_targets: list[int] = []
    for want in ("old", "steel", "400", "steps", "famous"):
        for i, t in enumerate(tokens):
            if t.strip() == want:
                content_targets.append(i)
                break
    if content_targets:
        scores = np.zeros((n_layers, n_heads))
        for L in range(n_layers):
            for H in range(n_heads):
                scores[L, H] = attn[L, H, pos, content_targets].sum()
        L_star, H_star = np.unravel_index(np.argmax(scores), scores.shape)
        print(f"  Strongest (layer, head) for context-word attention: "
              f"L{L_star}, H{H_star}  (sum={scores[L_star, H_star]:.3f})")
        row = attn[L_star, H_star, pos]
        order = np.argsort(-row)[:6]
        print("    pattern: " + "  ".join(
            f"{tokens[j]!r}={row[j]:.2f}" for j in order))


# ---------------------------------------------------------------------------

def main() -> None:
    backend = ModelBackend("gpt2")
    print("\n" + "=" * 72)
    print("SECTION 1: next-token prediction after the 'referring to is the' nudge")
    print("=" * 72)
    probe_next_token(backend, SENT_FULL_Q, tag="full_Q", k=12)
    probe_next_token(backend, SENT_WOOD_Q, tag="wood_Q", k=12)

    print("\n" + "=" * 72)
    print("SECTION 2: logit-lens on ' tower' residual across layers")
    print("=" * 72)
    for tag, sent in SENT_ABL.items():
        try:
            probe_logit_lens_at_tower(backend, sent, tag=tag, k=6)
        except ValueError as e:
            print(f"[{tag}] skip: {e}")

    print("\n" + "=" * 72)
    print("SECTION 3: cosine(tower_residual, wte[landmark]) across layers")
    print("=" * 72)
    probe_cosine_landmarks(backend, SENT_FULL, tag="full")
    probe_cosine_landmarks(backend, SENT_ABL["bare"], tag="bare")
    probe_cosine_landmarks(backend, SENT_WOOD, tag="wood")

    print("\n" + "=" * 72)
    print("SECTION 4: attention patterns at ' tower'")
    print("=" * 72)
    probe_attention_at_tower(backend, SENT_FULL, tag="full")


if __name__ == "__main__":
    main()
