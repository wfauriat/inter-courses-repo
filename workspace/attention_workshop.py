"""
attention_workshop.py
=====================
Qt app dedicated to the *construction* of attention in GPT-2 small.

Where GPT_arch_workshop.py shows the *output* of attention (the post-softmax
matrix), this app shows the *machinery upstream* of that matrix — how a single
hidden state and a single bundled c_attn weight produce the per-head Q, K, V
vectors, the score row, the softmax, and the residual contribution.

Pipeline (top → bottom panels):
  1. Hidden state h_q                — input to attention for the query token
  2. Bundled c_attn weight (768x2304) — the "one matrix doing three jobs" picture
  3. Q, K, V vectors                  — per-head 64-d projections
  4. Score row Q·Kᵀ/√64               — pre-softmax scores, causal mask greyed
  5. Softmax weights                  — same x-axis as the score row
  6. Per-head output Σ α·V            — what one head produces (64-d)
  7. Residual contribution (toggle)   — full c_proj output (all 12 heads, 768-d)

Selectable: layer, head, query token, prompt.

Usage:
    source ~/.venvDS/bin/activate
    python workspace/attention_workshop.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, FancyBboxPatch

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import COLOR_PALETTE


# ---------------------------------------------------------------------------
# Backend: forward pass + per-(layer, head, query) attention computation
# ---------------------------------------------------------------------------

@dataclass
class ForwardResult:
    tokens: list[str]
    token_ids: list[int]
    # Per-layer input to the attention sublayer (post-ln_1, pre-c_attn).
    # Captured via a forward hook on block.attn.c_attn — its first input
    # tensor IS the (seq, 768) post-LN hidden state we want to multiply
    # against W_Q/W_K/W_V.
    attn_inputs: np.ndarray   # (n_layers, seq, 768)
    # Per-layer attention sublayer output (post-c_proj). Captured via
    # forward hook on block.attn — this is the 768-d residual delta added
    # to the residual stream for each token.
    attn_outputs: np.ndarray  # (n_layers, seq, 768)
    # HF's reported attention weights — sanity-check target for the
    # manually computed softmax.
    attentions: np.ndarray    # (n_layers, n_heads, seq, seq)


@dataclass
class AttentionData:
    # Identity / context
    layer: int
    head: int
    query_idx: int
    tokens: list[str]
    seq_len: int

    # Stage 1: hidden state at the query position
    h_q: np.ndarray           # (768,)

    # Stage 2: weights, with the chosen head's slice
    W_Q_head: np.ndarray      # (768, 64)
    W_K_head: np.ndarray      # (768, 64)
    W_V_head: np.ndarray      # (768, 64)
    n_heads: int
    d_head: int
    n_embd: int

    # Stage 3: Q for query, K and V for all tokens
    Q: np.ndarray             # (64,)
    K: np.ndarray             # (seq, 64)
    V: np.ndarray             # (seq, 64)

    # Stage 4–5: scores, mask, softmax weights
    scores: np.ndarray        # (seq,) — pre-mask
    mask: np.ndarray          # (seq,) bool — True = masked (future)
    weights: np.ndarray       # (seq,) — post-softmax, masked positions = 0

    # Stage 6: per-head output
    out_head: np.ndarray      # (64,)

    # Stage 7: full residual contribution (post-c_proj, all 12 heads merged)
    residual_contribution: np.ndarray  # (768,)

    # Sanity check: how close is our manual softmax to HF's reported attn?
    sanity_max_abs_diff: float


class ModelBackend:
    def __init__(self, name: str = "gpt2"):
        print(f"Loading {name} ...", flush=True)
        self.tok = AutoTokenizer.from_pretrained(name)
        # Need eager attention to get output_attentions; the default sdpa
        # path silently drops them.
        self.model = AutoModelForCausalLM.from_pretrained(
            name, attn_implementation="eager")
        self.model.eval()
        self.model.config.output_attentions = True
        cfg = self.model.config
        self.n_layers = cfg.n_layer
        self.n_heads = cfg.n_head
        self.n_embd = cfg.n_embd
        self.d_head = self.n_embd // self.n_heads
        self._cache: dict[str, ForwardResult] = {}
        print(f"Model ready: n_layers={self.n_layers} "
              f"n_heads={self.n_heads} n_embd={self.n_embd} "
              f"d_head={self.d_head}", flush=True)

    def run(self, prompt: str) -> ForwardResult:
        if prompt in self._cache:
            return self._cache[prompt]

        inputs = self.tok(prompt, return_tensors="pt")

        cap_attn_in: dict[int, torch.Tensor] = {}
        cap_attn_out: dict[int, torch.Tensor] = {}
        handles = []
        for i, block in enumerate(self.model.transformer.h):
            def make_in_hook(idx: int):
                def _hook(_mod, inp, _out):
                    # inp is a tuple of input tensors; first is (batch, seq, 768)
                    cap_attn_in[idx] = inp[0].detach()
                return _hook

            def make_out_hook(idx: int):
                def _hook(_mod, _inp, out):
                    tensor = out[0] if isinstance(out, tuple) else out
                    cap_attn_out[idx] = tensor.detach()
                return _hook

            handles.append(block.attn.c_attn.register_forward_hook(make_in_hook(i)))
            handles.append(block.attn.register_forward_hook(make_out_hook(i)))

        try:
            with torch.no_grad():
                out = self.model(**inputs)
        finally:
            for h in handles:
                h.remove()

        ids = inputs.input_ids[0].tolist()
        tokens = [self.tok.decode([tid]) for tid in ids]

        attn_inputs = np.stack([cap_attn_in[i][0].cpu().numpy()
                                for i in range(self.n_layers)])
        attn_outputs = np.stack([cap_attn_out[i][0].cpu().numpy()
                                 for i in range(self.n_layers)])
        attentions = np.stack([a[0].cpu().numpy() for a in out.attentions])

        result = ForwardResult(
            tokens=tokens,
            token_ids=ids,
            attn_inputs=attn_inputs,
            attn_outputs=attn_outputs,
            attentions=attentions,
        )
        self._cache[prompt] = result
        return result

    def compute(self, prompt: str, layer: int, head: int,
                query_idx: int) -> AttentionData:
        result = self.run(prompt)
        seq_len = len(result.tokens)
        if not (0 <= layer < self.n_layers):
            raise ValueError(f"layer out of range: {layer}")
        if not (0 <= head < self.n_heads):
            raise ValueError(f"head out of range: {head}")
        if not (0 <= query_idx < seq_len):
            raise ValueError(f"query_idx out of range: {query_idx}")

        H = result.attn_inputs[layer]                # (seq, 768) — post-ln_1
        h_q = H[query_idx]                           # (768,)

        block = self.model.transformer.h[layer]
        # HF's Conv1D weight is (in, out) = (768, 2304). Concatenated as
        # [Q | K | V] each of width n_embd; per-head slice on the head dim.
        W_c = block.attn.c_attn.weight.detach().cpu().numpy()  # (768, 2304)
        b_c = block.attn.c_attn.bias.detach().cpu().numpy()    # (2304,)

        n = self.n_embd
        d = self.d_head
        s = head * d
        e = s + d

        W_Q_head = W_c[:, s:e]
        W_K_head = W_c[:, n + s:n + e]
        W_V_head = W_c[:, 2 * n + s:2 * n + e]
        b_Q_head = b_c[s:e]
        b_K_head = b_c[n + s:n + e]
        b_V_head = b_c[2 * n + s:2 * n + e]

        # Note: biases are included in the math (so the sanity check matches
        # HF exactly), but they're omitted from the visualization on purpose
        # — they're a token-independent DC offset and would visually
        # dominate the small Q/K/V panels.
        Q = h_q @ W_Q_head + b_Q_head                 # (64,)
        K = H @ W_K_head + b_K_head                   # (seq, 64)
        V = H @ W_V_head + b_V_head                   # (seq, 64)

        scores = (K @ Q) / np.sqrt(d)                 # (seq,)
        mask = np.zeros(seq_len, dtype=bool)
        mask[query_idx + 1:] = True                   # causal: mask future
        scores_masked = np.where(mask, -np.inf, scores)
        sm = np.exp(scores_masked - np.nanmax(scores_masked[~mask]))
        sm = np.where(mask, 0.0, sm)
        weights = sm / sm.sum()

        out_head = weights @ V                        # (64,)

        residual_contribution = result.attn_outputs[layer, query_idx]  # (768,)

        # Sanity: manual softmax weights should match HF's attention
        # weights for this (layer, head, query_idx).
        hf_w = result.attentions[layer, head, query_idx]
        diff = float(np.abs(weights - hf_w).max())

        return AttentionData(
            layer=layer, head=head, query_idx=query_idx,
            tokens=result.tokens, seq_len=seq_len,
            h_q=h_q,
            W_Q_head=W_Q_head, W_K_head=W_K_head, W_V_head=W_V_head,
            n_heads=self.n_heads, d_head=self.d_head, n_embd=self.n_embd,
            Q=Q, K=K, V=V,
            scores=scores, mask=mask, weights=weights,
            out_head=out_head,
            residual_contribution=residual_contribution,
            sanity_max_abs_diff=diff,
        )


# ---------------------------------------------------------------------------
# Panel renderers — each takes an AttentionData and a Figure
# ---------------------------------------------------------------------------

def _robust_vmax(arr: np.ndarray, p: float = 99.0) -> float:
    """Clip threshold = p-th percentile of |arr|. For small arrays p99
    sits near the max so this barely does anything; for larger arrays
    (e.g. the 768-d residual contribution with its rogue dimensions) it
    keeps a few outlier coordinates from saturating the colormap."""
    return max(float(np.percentile(np.abs(arr), p)), 1e-6)


def _seq_vmax(arr: np.ndarray, p: float = 99.0) -> float:
    """Like _robust_vmax but excludes row 0 from the statistics for
    (seq, D) tensors — position 0 in GPT-2 is a known attention/residual
    sink and would otherwise drive the color scale alone, washing out
    the rest of the rows. Row 0 is still drawn at full magnitude."""
    body = arr if arr.shape[0] <= 1 else arr[1:]
    return max(float(np.percentile(np.abs(body), p)), 1e-6)


def render_hidden_state(data: AttentionData, fig: Figure) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    h = data.h_q[None, :]   # (1, 768)
    vmax = _robust_vmax(h)
    im = ax.imshow(h, cmap="RdBu_r", aspect="auto", vmin=-vmax, vmax=vmax,
                   interpolation="nearest")
    ax.set_yticks([0])
    ax.set_yticklabels([repr(data.tokens[data.query_idx])],
                       fontsize=9, fontfamily="monospace")
    ax.set_xlabel(f"Dimension (0 .. {data.n_embd - 1})")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    ax.set_title(
        f"1. Hidden state h_q  —  input to attention at layer {data.layer}, "
        f"query token {data.tokens[data.query_idx]!r} "
        f"(pos {data.query_idx})\n"
        f"$h_q \\in \\mathbb{{R}}^{{{data.n_embd}}}$  ·  post-ln_1, pre-c_attn",
        fontsize=10, fontweight="bold", loc="left")
    fig.tight_layout()


def render_c_attn_schematic(data: AttentionData, fig: Figure) -> None:
    """Block diagram of the bundled c_attn weight (768x2304), showing the
    three n_embd-wide chunks Q/K/V and highlighting the chosen head's
    64-column band inside each chunk."""
    fig.clear()
    ax = fig.add_subplot(111)
    n = data.n_embd
    d = data.d_head
    h = data.head

    chunk_colors = {"Q": "#dbe7f5", "K": "#f5e3db", "V": "#dbf5e1"}
    edge_colors  = {"Q": "#4C72B0", "K": "#DD8452", "V": "#55A868"}

    # Lay out three rectangles side by side: x in [0, 3*n], y in [0, n]
    for i, name in enumerate(["Q", "K", "V"]):
        rect = Rectangle((i * n, 0), n, n,
                         facecolor=chunk_colors[name],
                         edgecolor=edge_colors[name], lw=1.6)
        ax.add_patch(rect)
        ax.text(i * n + n / 2, n + n * 0.06,
                f"$W_{{{name}}}$  (768 × {n})",
                ha="center", va="bottom", fontsize=10, fontweight="bold",
                color=edge_colors[name])
        # Highlighted per-head band: columns h*d .. (h+1)*d inside this chunk
        band = Rectangle((i * n + h * d, 0), d, n,
                         facecolor="none", edgecolor="#222",
                         lw=2.4, hatch="//", alpha=0.85)
        ax.add_patch(band)
        ax.text(i * n + h * d + d / 2, -n * 0.06,
                f"head {h}\ncols {h*d}:{(h+1)*d}",
                ha="center", va="top", fontsize=8, color="#222")

    ax.set_xlim(-n * 0.04, 3 * n + n * 0.04)
    ax.set_ylim(-n * 0.28, n * 1.22)
    # No aspect lock — let the schematic fill the panel width. Visually
    # this also stretches the chunks horizontally, which actually helps
    # convey "c_attn is wider than tall" (3·n_embd output cols vs n_embd
    # input rows).
    ax.set_aspect("auto")
    ax.set_xticks([n / 2, n + n / 2, 2 * n + n / 2])
    ax.set_xticklabels(["Q chunk\n(cols 0–767)",
                        "K chunk\n(cols 768–1535)",
                        "V chunk\n(cols 1536–2303)"], fontsize=9)
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(
        f"2. Bundled c_attn weight  —  one matrix doing three jobs\n"
        f"$\\mathrm{{c\\_attn}} \\in \\mathbb{{R}}^{{768 \\times 2304}} = "
        f"[\\,W_Q\\,|\\,W_K\\,|\\,W_V\\,]$"
        f"   ·   per-head slice = 64 contiguous columns inside each chunk",
        fontsize=10, fontweight="bold", loc="left")
    # tooltip-equivalent footnote
    ax.text(1.5 * n, -n * 0.18,
            "(biases also added but omitted from this visualization "
            "— token-independent DC offset)",
            ha="center", va="top", fontsize=8, color="#666", style="italic")
    fig.tight_layout()


def render_qkv(data: AttentionData, fig: Figure) -> None:
    fig.clear()
    # Slightly wider Q so its single-line title with the formula fits.
    gs = fig.add_gridspec(1, 3, width_ratios=[1.2, 1.6, 1.6], wspace=0.35)
    axQ = fig.add_subplot(gs[0])
    axK = fig.add_subplot(gs[1])
    axV = fig.add_subplot(gs[2])

    # Q: 1x64 row
    Q = data.Q[None, :]
    vmaxQ = _robust_vmax(Q)
    axQ.imshow(Q, cmap="RdBu_r", aspect="auto", vmin=-vmaxQ, vmax=vmaxQ,
               interpolation="nearest")
    axQ.set_yticks([0])
    axQ.set_yticklabels([repr(data.tokens[data.query_idx])],
                        fontsize=8, fontfamily="monospace")
    axQ.set_xlabel(f"head dim (0..{data.d_head - 1})")
    axQ.set_title(r"Q  (1×64)    $Q = h_q\, W_Q^{(h)}$",
                  fontsize=9, fontweight="bold", loc="left", pad=8)

    # K: (seq, 64) heatmap
    vmaxK = _seq_vmax(data.K)
    axK.imshow(data.K, cmap="RdBu_r", aspect="auto", vmin=-vmaxK, vmax=vmaxK,
               interpolation="nearest")
    axK.set_yticks(range(data.seq_len))
    axK.set_yticklabels([repr(t) for t in data.tokens],
                        fontsize=8, fontfamily="monospace")
    axK.set_xlabel(f"head dim (0..{data.d_head - 1})")
    axK.set_title(rf"K  ({data.seq_len}×64)    $K = H\, W_K^{{(h)}}$",
                  fontsize=9, fontweight="bold", loc="left", pad=8)

    # V: (seq, 64) heatmap
    vmaxV = _seq_vmax(data.V)
    axV.imshow(data.V, cmap="RdBu_r", aspect="auto", vmin=-vmaxV, vmax=vmaxV,
               interpolation="nearest")
    axV.set_yticks(range(data.seq_len))
    axV.set_yticklabels([repr(t) for t in data.tokens],
                        fontsize=8, fontfamily="monospace")
    axV.set_xlabel(f"head dim (0..{data.d_head - 1})")
    axV.set_title(rf"V  ({data.seq_len}×64)    $V = H\, W_V^{{(h)}}$",
                  fontsize=9, fontweight="bold", loc="left", pad=8)

    # Section header above all three subplots. Plain text, no math —
    # avoids the line-height jump that mathtext causes in mixed-content
    # multi-line titles, which was making the suptitle and subplot
    # titles overlap.
    fig.suptitle(
        f"3. Q, K, V — per-head 64-d projections of the hidden states  "
        f"(layer {data.layer}, head {data.head})",
        fontsize=10, fontweight="bold", x=0.01, ha="left", y=0.985)
    fig.tight_layout(rect=(0, 0, 1, 0.92))


def render_score_row(data: AttentionData, fig: Figure) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    xs = np.arange(data.seq_len)
    colors = ["#bbbbbb" if data.mask[i] else COLOR_PALETTE[0]
              for i in range(data.seq_len)]
    bars = ax.bar(xs, data.scores, color=colors, edgecolor="#333", lw=0.6)

    # Mark the query position with a vertical line.
    ax.axvline(data.query_idx, color="#C44E52", lw=1.0, ls="--", alpha=0.6)
    ax.text(data.query_idx, ax.get_ylim()[1], "  query",
            color="#C44E52", fontsize=8, va="top")

    ax.set_xticks(xs)
    ax.set_xticklabels([repr(t) for t in data.tokens],
                       fontsize=8, fontfamily="monospace",
                       rotation=30, ha="right")
    ax.axhline(0, color="#333", lw=0.5)
    ax.set_ylabel("score")
    ax.set_title(
        f"4. Score row  —  $s_j = Q \\cdot K_j^\\top / \\sqrt{{{data.d_head}}}$"
        f"   ·   greyed bars are causally masked (future tokens, set to "
        f"$-\\infty$ before softmax)",
        fontsize=10, fontweight="bold", loc="left")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()


def render_softmax(data: AttentionData, fig: Figure, top_k: int = 3) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    xs = np.arange(data.seq_len)
    colors = ["#bbbbbb" if data.mask[i] else COLOR_PALETTE[2]
              for i in range(data.seq_len)]
    ax.bar(xs, data.weights, color=colors, edgecolor="#333", lw=0.6)

    # Annotate top-k weighted (unmasked) tokens.
    unmasked_idx = np.where(~data.mask)[0]
    order = unmasked_idx[np.argsort(-data.weights[unmasked_idx])][:top_k]
    for rank, j in enumerate(order):
        ax.text(j, data.weights[j],
                f"  α={data.weights[j]:.2f}\n  ({data.tokens[j]!r})",
                fontsize=8, ha="left", va="bottom",
                color="#222" if rank == 0 else "#555")

    ax.set_xticks(xs)
    ax.set_xticklabels([repr(t) for t in data.tokens],
                       fontsize=8, fontfamily="monospace",
                       rotation=30, ha="right")
    ax.set_ylabel("weight")
    ax.set_ylim(0, max(0.05, float(data.weights.max()) * 1.25))
    ax.set_title(
        f"5. Softmax weights  —  $\\alpha_j = \\mathrm{{softmax}}(s)_j$"
        f"   ·   sums to 1 over unmasked positions",
        fontsize=10, fontweight="bold", loc="left")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()


def render_per_head_output(data: AttentionData, fig: Figure) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    out = data.out_head[None, :]
    vmax = _robust_vmax(out)
    im = ax.imshow(out, cmap="RdBu_r", aspect="auto", vmin=-vmax, vmax=vmax,
                   interpolation="nearest")
    ax.set_yticks([0])
    ax.set_yticklabels([f"head {data.head}"], fontsize=9)
    ax.set_xlabel(f"head dim (0..{data.d_head - 1})")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    ax.set_title(
        f"6. Per-head output  —  $\\mathrm{{out}}_h = "
        f"\\sum_j \\alpha_j \\cdot V_j \\in \\mathbb{{R}}^{{{data.d_head}}}$"
        f"   ·   what one head produces, before merging with the other "
        f"{data.n_heads - 1} heads",
        fontsize=10, fontweight="bold", loc="left")
    fig.tight_layout()


def render_residual_contribution(data: AttentionData, fig: Figure) -> None:
    fig.clear()
    ax = fig.add_subplot(111)
    r = data.residual_contribution[None, :]
    vmax = _robust_vmax(r)
    im = ax.imshow(r, cmap="RdBu_r", aspect="auto", vmin=-vmax, vmax=vmax,
                   interpolation="nearest")
    ax.set_yticks([0])
    ax.set_yticklabels([repr(data.tokens[data.query_idx])],
                       fontsize=9, fontfamily="monospace")
    ax.set_xlabel(f"Dimension (0 .. {data.n_embd - 1})")
    fig.colorbar(im, ax=ax, fraction=0.02, pad=0.01)
    ax.set_title(
        f"7. Residual contribution  —  $\\Delta_{{\\mathrm{{attn}}}} = "
        f"\\mathrm{{c\\_proj}}([\\,\\mathrm{{out}}_0 \\oplus \\dots \\oplus "
        f"\\mathrm{{out}}_{{{data.n_heads - 1}}}\\,]) "
        f"\\in \\mathbb{{R}}^{{{data.n_embd}}}$"
        f"   ·   includes ALL {data.n_heads} heads (not just head "
        f"{data.head}); this is what gets added to the residual stream",
        fontsize=10, fontweight="bold", loc="left")
    fig.tight_layout()


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

DEFAULT_PROMPT = "The Eiffel Tower is in the city of"


class AttentionWorkshop(QMainWindow):
    def __init__(self, backend: ModelBackend):
        super().__init__()
        self.backend = backend
        self.current_result: AttentionData | None = None
        self.setWindowTitle("Attention / Q-K-V Workshop — GPT-2 small")
        self.resize(1500, 1000)
        self._build_ui()
        self._on_run_clicked()  # initial run with default prompt

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)

        # --- Top control bar ---------------------------------------------
        ctrl = QHBoxLayout()

        ctrl.addWidget(QLabel("Prompt:"))
        self.prompt_edit = QLineEdit(DEFAULT_PROMPT)
        self.prompt_edit.setMinimumWidth(420)
        self.prompt_edit.returnPressed.connect(self._on_run_clicked)
        ctrl.addWidget(self.prompt_edit)

        run_btn = QPushButton("Run")
        run_btn.clicked.connect(self._on_run_clicked)
        ctrl.addWidget(run_btn)

        ctrl.addSpacing(20)
        ctrl.addWidget(QLabel("Layer:"))
        self.layer_combo = QComboBox()
        for i in range(self.backend.n_layers):
            self.layer_combo.addItem(f"{i}", i)
        self.layer_combo.currentIndexChanged.connect(self._on_selection_changed)
        ctrl.addWidget(self.layer_combo)

        ctrl.addWidget(QLabel("Head:"))
        self.head_combo = QComboBox()
        for i in range(self.backend.n_heads):
            self.head_combo.addItem(f"{i}", i)
        self.head_combo.currentIndexChanged.connect(self._on_selection_changed)
        ctrl.addWidget(self.head_combo)

        ctrl.addWidget(QLabel("Query token:"))
        self.token_combo = QComboBox()
        # Filled after first run — depends on the prompt.
        self.token_combo.currentIndexChanged.connect(self._on_selection_changed)
        ctrl.addWidget(self.token_combo)

        ctrl.addSpacing(20)
        self.cproj_check = QCheckBox("Show c_proj output")
        self.cproj_check.setChecked(False)
        self.cproj_check.stateChanged.connect(self._update_cproj_visibility)
        ctrl.addWidget(self.cproj_check)

        ctrl.addStretch(1)
        outer.addLayout(ctrl)

        # --- Sanity status line ------------------------------------------
        self.sanity_label = QLabel("")
        self.sanity_label.setStyleSheet("color: #666; font-size: 11px;")
        outer.addWidget(self.sanity_label)

        # --- Scroll area with the panel stack ----------------------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, stretch=1)

        host = QWidget()
        scroll.setWidget(host)
        self.panels_layout = QVBoxLayout(host)
        self.panels_layout.setSpacing(8)

        # Build canvases up front; we'll re-render them on update.
        # Heights chosen to make each panel readable without crowding.
        self.canvases: dict[str, FigureCanvas] = {}
        self._add_canvas("h",      height_in=1.6)
        self._add_canvas("cattn",  height_in=3.2)
        self._add_canvas("qkv",    height_in=3.4)
        self._add_canvas("scores", height_in=2.4)
        self._add_canvas("soft",   height_in=2.4)
        self._add_canvas("out",    height_in=1.6)
        self._add_canvas("resid",  height_in=1.8)

        self._update_cproj_visibility()

    def _add_canvas(self, key: str, height_in: float) -> None:
        fig = Figure(figsize=(14, height_in), dpi=100)
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(int(height_in * 100))
        self.panels_layout.addWidget(canvas)
        self.canvases[key] = canvas

    # -- event handlers ---------------------------------------------------

    def _on_run_clicked(self) -> None:
        prompt = self.prompt_edit.text().strip()
        if not prompt:
            return
        # Re-run forward (cached internally), then refresh the token combo
        # to match the new tokenization.
        result = self.backend.run(prompt)
        self.token_combo.blockSignals(True)
        self.token_combo.clear()
        for i, t in enumerate(result.tokens):
            self.token_combo.addItem(f"{i}: {t!r}", i)
        # Default to last token — that's what the trajectory view defaults
        # to elsewhere, and it's the most interesting one for a partial
        # prompt.
        self.token_combo.setCurrentIndex(len(result.tokens) - 1)
        self.token_combo.blockSignals(False)
        self._on_selection_changed()

    def _on_selection_changed(self) -> None:
        prompt = self.prompt_edit.text().strip()
        if not prompt or self.token_combo.count() == 0:
            return
        layer = int(self.layer_combo.currentData())
        head = int(self.head_combo.currentData())
        query_idx = int(self.token_combo.currentData())
        try:
            data = self.backend.compute(prompt, layer, head, query_idx)
        except Exception as exc:
            self.sanity_label.setText(f"compute error: {exc}")
            return
        self.current_result = data
        self.sanity_label.setText(
            f"Sanity: |manual α − HF α|_max = {data.sanity_max_abs_diff:.2e}  "
            f"({'OK' if data.sanity_max_abs_diff < 1e-5 else 'mismatch'})"
        )
        self._redraw_all()

    def _update_cproj_visibility(self) -> None:
        on = self.cproj_check.isChecked()
        self.canvases["resid"].setVisible(on)
        if on and self.current_result is not None:
            render_residual_contribution(self.current_result,
                                         self.canvases["resid"].figure)
            self.canvases["resid"].draw_idle()

    def _redraw_all(self) -> None:
        d = self.current_result
        if d is None:
            return
        render_hidden_state(d,         self.canvases["h"].figure)
        render_c_attn_schematic(d,     self.canvases["cattn"].figure)
        render_qkv(d,                  self.canvases["qkv"].figure)
        render_score_row(d,            self.canvases["scores"].figure)
        render_softmax(d,              self.canvases["soft"].figure)
        render_per_head_output(d,      self.canvases["out"].figure)
        for key in ("h", "cattn", "qkv", "scores", "soft", "out"):
            self.canvases[key].draw_idle()
        if self.cproj_check.isChecked():
            render_residual_contribution(d, self.canvases["resid"].figure)
            self.canvases["resid"].draw_idle()


def main() -> None:
    backend = ModelBackend("gpt2")
    app = QApplication(sys.argv)
    win = AttentionWorkshop(backend)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
