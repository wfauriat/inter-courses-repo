"""
interactive_explorer.py
=======================
Qt app for reactive inspection of GPT-2 small internals.

Type a prompt, pick a layer / head / view, watch the top-k next-token bar
update. Three views for the selected tensor: heatmap, PCA projection onto
a vocabulary reference cloud, cosine similarity matrix.

Usage:
    source ~/.venvDS/bin/activate
    python workspace/interactive_explorer.py

Dependencies: torch, transformers, scikit-learn, matplotlib, PySide6, numpy.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional

import numpy as np
import torch
from sklearn.decomposition import PCA
from transformers import AutoModelForCausalLM, AutoTokenizer

import matplotlib
matplotlib.use("QtAgg")  # ensure Qt backend before pyplot import
import matplotlib.pyplot as plt  # noqa: E402 — after backend selection
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.colors import PowerNorm
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QComboBox, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QMainWindow, QPushButton, QRadioButton,
    QSplitter, QVBoxLayout, QWidget,
)

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import COLOR_PALETTE


# ---------------------------------------------------------------------------
# Backend: model wrapper + forward-pass cache
# ---------------------------------------------------------------------------

@dataclass
class ForwardResult:
    tokens: list[str]           # decoded BPE labels, one per input position
    hidden_states: np.ndarray   # (n_layers+1, seq, d_model) — [0] = embedding
    attentions: np.ndarray      # (n_layers, n_heads, seq, seq)
    mlp_acts: np.ndarray        # (n_layers, seq, d_mlp) — post-activation MLP
    attn_deltas: np.ndarray     # (n_layers, seq, d_model) — per-block attn residual contribution
    mlp_deltas: np.ndarray      # (n_layers, seq, d_model) — per-block mlp residual contribution
    logits: np.ndarray          # (seq, vocab)
    ln_f_out: np.ndarray        # (seq, d_model) — ln_f applied to last hidden
    topk_next: list[tuple[str, float]]
    # Logit lens: what the model would predict if it stopped at each layer.
    lens_top1_tokens: list[str]      # len n_layers+1 — top-1 token per layer
    lens_top1_probs: np.ndarray      # (n_layers+1,) — prob of that top-1
    lens_final_token: str            # decoded top-1 at the last layer
    lens_final_curve: np.ndarray     # (n_layers+1,) — P(final top-1) per layer


N_PCA_COMPONENTS = 6


class ModelBackend:
    def __init__(self, name: str = "gpt2"):
        print(f"Loading {name} ...", flush=True)
        self.tok = AutoTokenizer.from_pretrained(name)
        # attn_implementation="eager" is required for output_attentions=True
        # (the default "sdpa" path does not expose attention weights).
        self.model = AutoModelForCausalLM.from_pretrained(
            name, attn_implementation="eager")
        self.model.eval()
        self.model.config.output_attentions = True
        self.model.config.output_hidden_states = True
        cfg = self.model.config
        self.n_layers = cfg.n_layer
        self.n_heads = cfg.n_head
        self.d_model = cfg.n_embd
        # Intermediate MLP width — 4x d_model for GPT-2.
        self.d_mlp = getattr(cfg, "n_inner", None) or 4 * cfg.n_embd
        self._cache: dict[str, ForwardResult] = {}
        self._vocab_pca: Optional[PCA] = None
        self._ref_xy: Optional[np.ndarray] = None
        print(f"Model ready: n_layers={self.n_layers} "
              f"n_heads={self.n_heads} d_model={self.d_model}", flush=True)

    # -- forward pass -------------------------------------------------------

    def run(self, prompt: str) -> ForwardResult:
        if prompt in self._cache:
            return self._cache[prompt]

        inputs = self.tok(prompt, return_tensors="pt")

        # Hook every block's MLP activation (post-GELU) so we can expose the
        # intermediate 3072-d neuron firings as a selectable view.
        # Also hook block.attn and block.mlp themselves — their outputs are
        # the deltas added to the residual stream, needed by the trajectory
        # view to separate attention-write vs MLP-write arrows per block.
        captured: dict[int, torch.Tensor] = {}
        cap_attn: dict[int, torch.Tensor] = {}
        cap_mlp: dict[int, torch.Tensor] = {}
        handles = []
        for i, block in enumerate(self.model.transformer.h):
            def make_act_hook(idx: int):
                def _hook(_mod, _inp, out):
                    captured[idx] = out.detach()
                return _hook

            def make_attn_hook(idx: int):
                def _hook(_mod, _inp, out):
                    tensor = out[0] if isinstance(out, tuple) else out
                    cap_attn[idx] = tensor.detach()
                return _hook

            def make_mlp_hook(idx: int):
                def _hook(_mod, _inp, out):
                    tensor = out[0] if isinstance(out, tuple) else out
                    cap_mlp[idx] = tensor.detach()
                return _hook

            handles.append(block.mlp.act.register_forward_hook(make_act_hook(i)))
            handles.append(block.attn.register_forward_hook(make_attn_hook(i)))
            handles.append(block.mlp.register_forward_hook(make_mlp_hook(i)))

        try:
            with torch.no_grad():
                out = self.model(**inputs)
                ln_f = self.model.transformer.ln_f(out.hidden_states[-1])[0]
        finally:
            for h in handles:
                h.remove()

        ids = inputs.input_ids[0].tolist()
        tokens = [self.tok.decode([tid]) for tid in ids]

        hidden_states = np.stack([h[0].cpu().numpy() for h in out.hidden_states])
        attentions = np.stack([a[0].cpu().numpy() for a in out.attentions])
        mlp_acts = np.stack([captured[i][0].cpu().numpy()
                             for i in range(self.n_layers)])
        attn_deltas = np.stack([cap_attn[i][0].cpu().numpy()
                                for i in range(self.n_layers)])
        mlp_deltas = np.stack([cap_mlp[i][0].cpu().numpy()
                               for i in range(self.n_layers)])
        logits = out.logits[0].cpu().numpy()
        ln_f_out = ln_f.cpu().numpy()

        probs = torch.softmax(out.logits[0, -1, :], dim=-1)
        top_p, top_i = probs.topk(10)
        topk_next = [(self.tok.decode([int(ti)]), float(tp))
                     for tp, ti in zip(top_p, top_i)]

        lens = self._compute_logit_lens(out.hidden_states, out.logits)

        result = ForwardResult(
            tokens=tokens,
            hidden_states=hidden_states,
            attentions=attentions,
            mlp_acts=mlp_acts,
            attn_deltas=attn_deltas,
            mlp_deltas=mlp_deltas,
            logits=logits,
            ln_f_out=ln_f_out,
            topk_next=topk_next,
            lens_top1_tokens=lens["top1_tokens"],
            lens_top1_probs=lens["top1_probs"],
            lens_final_token=lens["final_token"],
            lens_final_curve=lens["final_curve"],
        )
        self._cache[prompt] = result
        return result

    # -- logit lens --------------------------------------------------------

    def _compute_logit_lens(self, hidden_states, final_logits) -> dict:
        """Project each layer's last-position hidden state through ln_f and
        the unembedding to see what the model would predict if it stopped
        there. HuggingFace's last hidden state is sometimes already post-
        ln_f, so we probe once and avoid double-normalizing.
        """
        with torch.no_grad():
            h_last = torch.stack(
                [h[0, -1, :] for h in hidden_states], dim=0
            )  # (n_layers+1, d_model)
            true = final_logits[0, -1]
            lm_head = self.model.lm_head
            ln_f = self.model.transformer.ln_f
            diff_pre = (lm_head(ln_f(h_last[-1])) - true).abs().max().item()
            diff_post = (lm_head(h_last[-1]) - true).abs().max().item()
            last_is_post_lnf = diff_post < diff_pre

            if last_is_post_lnf:
                normed = torch.cat([ln_f(h_last[:-1]), h_last[-1:]], dim=0)
            else:
                normed = ln_f(h_last)

            layer_logits = lm_head(normed)
            layer_probs = torch.softmax(layer_logits, dim=-1).cpu().numpy()

        n = layer_probs.shape[0]
        top1_ids = layer_probs.argmax(axis=-1)
        top1_probs = layer_probs[np.arange(n), top1_ids]
        top1_tokens = [self.tok.decode([int(tid)]) for tid in top1_ids]
        final_id = int(top1_ids[-1])
        return {
            "top1_tokens": top1_tokens,
            "top1_probs": top1_probs,
            "final_token": self.tok.decode([final_id]),
            "final_curve": layer_probs[:, final_id],
        }

    # -- vocab-reference PCA (fit once) ------------------------------------

    def vocab_pca(self) -> tuple[PCA, np.ndarray]:
        if self._vocab_pca is None:
            wte = self.model.transformer.wte.weight.detach().cpu().numpy()
            rng = np.random.default_rng(42)
            idx = rng.choice(wte.shape[0], 2000, replace=False)
            ref = wte[idx]
            # Fit 6 components once — the extra axes are nearly free and let
            # the UI offer PC pairs beyond the default PC1/PC2.
            pca = PCA(n_components=6)
            self._ref_xy = pca.fit_transform(ref)
            self._vocab_pca = pca
        return self._vocab_pca, self._ref_xy


# ---------------------------------------------------------------------------
# Tensor selector: layer tag + head idx -> 2D array
# ---------------------------------------------------------------------------

def parse_tag(tag: str) -> tuple:
    """Parse a combo-box tag string into its structured components.

    Formats:
      'embedding'           -> ('embedding',)
      'block:<i>:attn'      -> ('block', i, 'attn')
      'block:<i>:mlp'       -> ('block', i, 'mlp')
      'block:<i>:residual'  -> ('block', i, 'residual')
      'ln_f'                -> ('ln_f',)
    """
    parts = tag.split(":")
    if parts[0] == "block":
        return ("block", int(parts[1]), parts[2])
    return (parts[0],)


def get_tensor(result: ForwardResult, tag: str,
               head_idx: int) -> np.ndarray:
    """Return the 2D array identified by (tag, head_idx)."""
    parsed = parse_tag(tag)
    if parsed[0] == "embedding":
        return result.hidden_states[0]
    if parsed[0] == "block":
        _, i, kind = parsed
        if kind == "attn":
            attn = result.attentions[i]             # (n_heads, seq, seq)
            if head_idx == -1:
                return attn.mean(axis=0)
            return attn[head_idx]
        if kind == "residual":
            return result.hidden_states[i + 1]
        if kind == "mlp":
            return result.mlp_acts[i]
    if parsed[0] == "ln_f":
        return result.ln_f_out
    raise ValueError(f"unknown layer tag: {tag}")


def describe(tag: str, head_idx: int) -> str:
    """Human-readable label for a (tag, head) selection."""
    parsed = parse_tag(tag)
    if parsed[0] == "embedding":
        return "embedding (wte + wpe)"
    if parsed[0] == "block":
        _, i, kind = parsed
        if kind == "attn":
            head_str = "all heads avg" if head_idx == -1 else f"head {head_idx}"
            return f"block {i} attention — {head_str}"
        if kind == "mlp":
            return f"block {i} FFN (post-GELU)"
        return f"block {i} residual out"
    if parsed[0] == "ln_f":
        return "final ln_f output"
    return tag


def is_attention_tag(tag: str) -> bool:
    parsed = parse_tag(tag)
    return parsed[0] == "block" and parsed[2] == "attn"


# ---------------------------------------------------------------------------
# View renderers — draw into an Axes, no side effects
# ---------------------------------------------------------------------------

def _soften_attn(attn_2d: np.ndarray) -> np.ndarray:
    """Drop the pos-0 row and column from an attention matrix, then
    renormalize each remaining row so it sums to 1. This removes the
    dominant "attention sink" column so the real inter-token structure
    becomes visible.
    """
    if attn_2d.shape[0] <= 1 or attn_2d.shape[1] <= 1:
        return attn_2d
    data = attn_2d[1:, 1:].copy()
    row_sums = data.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums < 1e-12, 1.0, row_sums)
    return data / row_sums


def _soften_suffix() -> str:
    return "  (pos-0 softened)"


def render_heatmap(result: ForwardResult, tag: tuple, head_idx: int,
                   ax, *, soften: bool = False) -> None:
    tensor = get_tensor(result, tag, head_idx)
    tokens = result.tokens

    if is_attention_tag(tag):
        # (seq, seq) attention — Blues + PowerNorm to compress the sink's
        # dynamic range. When softened, drop pos-0 row/col and renormalize
        # so each row's remaining mass sums to 1.
        if soften:
            data = _soften_attn(tensor)
            row_tokens = tokens[1:] if tensor.shape[0] > 1 else tokens
            col_tokens = tokens[1:] if tensor.shape[1] > 1 else tokens
        else:
            data = tensor
            row_tokens = tokens
            col_tokens = tokens
        vmax = max(float(data.max()), 1e-6)
        im = ax.imshow(data, cmap="Blues", aspect="auto",
                       norm=PowerNorm(gamma=0.4, vmin=0, vmax=vmax))
        ax.set_xticks(range(len(col_tokens)))
        ax.set_yticks(range(len(row_tokens)))
        ax.set_xticklabels([repr(t) for t in col_tokens],
                           rotation=45, ha="right",
                           fontsize=8, fontfamily="monospace")
        ax.set_yticklabels([repr(t) for t in row_tokens],
                           fontsize=8, fontfamily="monospace")
        ax.set_xlabel("Attends to (key)")
        ax.set_ylabel("Token (query)")
    else:
        # (seq, D) — RdBu_r with a robust vmax:
        #   • skip row 0 to avoid the position-0 residual outlier.
        #   • p99 of the remaining magnitudes, so a handful of outlier MLP
        #     neurons can't stretch the scale and wash the rest out.
        if soften and tensor.shape[0] > 1:
            data = tensor[1:]
            y_labels = tokens[1:]
        else:
            data = tensor
            y_labels = tokens
        # When not softened we still exclude row 0 from the *statistics*.
        stat_body = data if (soften or data.shape[0] <= 1) else data[1:]
        abs_body = np.abs(stat_body)
        vmax = float(np.percentile(abs_body, 99))
        vmax = max(vmax, float(abs_body.max()) * 0.15, 1e-6)
        im = ax.imshow(data, cmap="RdBu_r", aspect="auto",
                       vmin=-vmax, vmax=vmax, interpolation="nearest")
        ax.set_yticks(range(len(y_labels)))
        ax.set_yticklabels([repr(t) for t in y_labels],
                           fontsize=9, fontfamily="monospace")
        ax.set_xlabel(f"Dimension (0 .. {data.shape[1] - 1})")

    ax.figure.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
    suffix = _soften_suffix() if soften else ""
    ax.set_title(f"Heatmap — {describe(tag, head_idx)}{suffix}",
                 fontsize=11, fontweight="bold")


def render_pca(result: ForwardResult, tag: tuple, head_idx: int,
               backend: ModelBackend, ax, *,
               soften: bool = False,
               pc_x: int = 0, pc_y: int = 1) -> None:
    tensor = get_tensor(result, tag, head_idx)
    if tensor.ndim != 2 or tensor.shape[-1] != backend.d_model:
        _draw_na(ax,
                 f"PCA view is only defined for\n"
                 f"(seq, {backend.d_model}) hidden-state tensors.\n\n"
                 f"Current tensor shape: {tensor.shape}")
        return

    pca, ref_xy = backend.vocab_pca()
    xy = pca.transform(tensor)

    ax.scatter(ref_xy[:, pc_x], ref_xy[:, pc_y], s=6, alpha=0.22,
               color="gray", label="2000 random vocab tokens")

    start = 1 if (soften and xy.shape[0] > 1) else 0
    for i in range(start, xy.shape[0]):
        x, y = xy[i, pc_x], xy[i, pc_y]
        color = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        ax.scatter(x, y, s=220, color=color, edgecolors="black",
                   lw=1.2, zorder=3)
        ax.annotate(f"  {result.tokens[i]!r}", (x, y),
                    fontsize=10, fontweight="bold",
                    family="monospace", zorder=4)

    var = pca.explained_variance_ratio_
    ax.set_xlabel(f"PC{pc_x + 1} ({var[pc_x]:.1%} of vocab var)")
    ax.set_ylabel(f"PC{pc_y + 1} ({var[pc_y]:.1%} of vocab var)")
    suffix = _soften_suffix() if soften else ""
    ax.set_title(f"PCA (vocab reference) — {describe(tag, head_idx)}{suffix}",
                 fontsize=11, fontweight="bold")
    ax.legend(loc="best", fontsize=8)
    ax.grid(True, alpha=0.3)


def render_trajectory(result: ForwardResult, backend: ModelBackend, ax, *,
                      token_idx: int = -1,
                      pc_x: int = 0, pc_y: int = 1) -> None:
    """Residual-stream trajectory for a single token position.

    Plots 1 + 2·n_layers points: the embedding, then after each block's
    attention-write and after each block's MLP-write. Arrows between
    successive points are colored by whether the delta came from attention
    (blue) or from the MLP (orange), making the "every block adds to the
    running sum" idea visible at a glance.
    """
    seq_len = result.hidden_states.shape[1]
    idx = seq_len - 1 if token_idx < 0 else min(token_idx, seq_len - 1)

    h = result.hidden_states[:, idx, :]   # (n_layers+1, d_model)
    a = result.attn_deltas[:, idx, :]     # (n_layers, d_model)
    m = result.mlp_deltas[:, idx, :]      # (n_layers, d_model)
    n_layers = a.shape[0]

    points = [h[0]]
    kinds = ["start"]
    for i in range(n_layers):
        points.append(h[i] + a[i])
        kinds.append("attn")
        points.append(h[i] + a[i] + m[i])  # == h[i+1]
        kinds.append("mlp")
    points = np.stack(points)

    pca, ref_xy = backend.vocab_pca()
    xy = pca.transform(points)

    ax.scatter(ref_xy[:, pc_x], ref_xy[:, pc_y], s=6, alpha=0.18,
               color="gray", zorder=1)

    attn_color = COLOR_PALETTE[0]   # blue
    mlp_color = COLOR_PALETTE[1]    # orange
    for k in range(1, len(points)):
        color = attn_color if kinds[k] == "attn" else mlp_color
        ax.annotate("", xy=(xy[k, pc_x], xy[k, pc_y]),
                    xytext=(xy[k - 1, pc_x], xy[k - 1, pc_y]),
                    arrowprops=dict(arrowstyle="->", color=color,
                                    lw=1.4, alpha=0.85),
                    zorder=2)

    # Mark layer boundaries (post-MLP points) with small white dots; label
    # a handful so the path is readable without overcrowding it.
    label_stride = max(1, n_layers // 4)
    for i in range(n_layers):
        pt = 2 + 2 * i
        ax.scatter(xy[pt, pc_x], xy[pt, pc_y], s=34,
                   color="white", edgecolor="#333", lw=0.7, zorder=4)
        if i % label_stride == (label_stride - 1) and pt != len(points) - 1:
            ax.annotate(f" L{i}", (xy[pt, pc_x], xy[pt, pc_y]),
                        fontsize=8, color="#333", zorder=5)

    # Emphasize endpoints.
    ax.scatter(xy[0, pc_x], xy[0, pc_y], s=190, color="black",
               marker="o", edgecolor="white", lw=1.4, zorder=6)
    ax.annotate(" embed", (xy[0, pc_x], xy[0, pc_y]),
                fontsize=9, fontweight="bold", color="#111", zorder=7)
    ax.scatter(xy[-1, pc_x], xy[-1, pc_y], s=260, color=COLOR_PALETTE[3],
               marker="*", edgecolor="black", lw=1.2, zorder=6)
    ax.annotate(f" L{n_layers - 1} out", (xy[-1, pc_x], xy[-1, pc_y]),
                fontsize=9, fontweight="bold", color="#111", zorder=7)

    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0], [0], color=attn_color, lw=2.2, label="Δ attention"),
        Line2D([0], [0], color=mlp_color, lw=2.2, label="Δ MLP"),
        Line2D([0], [0], marker="o", color="black", linestyle="",
               markersize=8, label="embedding"),
        Line2D([0], [0], marker="*", color=COLOR_PALETTE[3], linestyle="",
               markersize=11, label="final residual"),
    ]
    ax.legend(handles=legend_items, loc="best", fontsize=8)

    var = pca.explained_variance_ratio_
    ax.set_xlabel(f"PC{pc_x + 1} ({var[pc_x]:.1%} of vocab var)")
    ax.set_ylabel(f"PC{pc_y + 1} ({var[pc_y]:.1%} of vocab var)")
    ax.set_title(
        f"Residual-stream trajectory — token {result.tokens[idx]!r} "
        f"(position {idx})",
        fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)


def render_cosine(result: ForwardResult, tag: tuple, head_idx: int,
                  ax, *, soften: bool = False) -> None:
    tensor = get_tensor(result, tag, head_idx)
    tokens = result.tokens

    if is_attention_tag(tag):
        # Attention is already a (seq, seq) pairwise score — just display it
        if soften:
            mat = _soften_attn(tensor)
            display_tokens = tokens[1:] if tensor.shape[0] > 1 else tokens
        else:
            mat = tensor
            display_tokens = tokens
        vmin, vmax = 0.0, float(max(mat.max(), 1e-6))
        cmap, label = "Blues", "attention weight"
    elif tensor.ndim == 2 and tensor.shape[-1] > 1:
        norms = np.linalg.norm(tensor, axis=-1, keepdims=True)
        mat = (tensor @ tensor.T) / (norms @ norms.T + 1e-9)
        if soften and mat.shape[0] > 1:
            mat = mat[1:, 1:]
            display_tokens = tokens[1:]
        else:
            display_tokens = tokens
        vmin, vmax = -1.0, 1.0
        cmap, label = "RdBu_r", "cosine similarity"
    else:
        _draw_na(ax, "Cosine view expects a (seq, d) tensor.")
        return

    im = ax.imshow(mat, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_xticks(range(len(display_tokens)))
    ax.set_yticks(range(len(display_tokens)))
    ax.set_xticklabels([repr(t) for t in display_tokens],
                       rotation=45, ha="right",
                       fontsize=8, fontfamily="monospace")
    ax.set_yticklabels([repr(t) for t in display_tokens],
                       fontsize=8, fontfamily="monospace")
    # Annotate cells if small enough
    if len(display_tokens) <= 14:
        for i in range(len(display_tokens)):
            for j in range(len(display_tokens)):
                v = mat[i, j]
                threshold = 0.55 if vmin < 0 else (vmax * 0.55)
                color = "white" if abs(v) > threshold else "#111"
                ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                        color=color, fontsize=8)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04,
                       label=label)
    suffix = _soften_suffix() if soften else ""
    ax.set_title(f"Relational view — {describe(tag, head_idx)}{suffix}",
                 fontsize=11, fontweight="bold")


def render_topk(result: ForwardResult, ax) -> None:
    tokens, probs = zip(*result.topk_next)
    y_pos = np.arange(len(tokens))
    ax.barh(y_pos, probs, color=COLOR_PALETTE[0], edgecolor="white")
    ax.set_yticks(y_pos)
    ax.set_yticklabels([repr(t) for t in tokens],
                       fontsize=9, fontfamily="monospace")
    ax.invert_yaxis()
    for i, p in enumerate(probs):
        ax.text(p + max(probs) * 0.01, i, f"{p:.1%}",
                va="center", fontsize=9, color="#333")
    ax.set_xlabel("Probability")
    ax.set_title("Top-10 next-token predictions",
                 fontsize=11, fontweight="bold")
    ax.set_xlim(0, max(probs) * 1.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def render_logit_lens(result: ForwardResult, ax_top1, ax_curve) -> None:
    """Two-panel view of the layer-by-layer next-token prediction.

    Left panel: the top-1 token the model would emit if generation stopped
    at each layer, shaded by its probability.
    Right panel: the probability of the *final* top-1 token, tracked across
    layers — shows at which depth the eventual answer emerges.
    """
    tokens = result.lens_top1_tokens
    probs = result.lens_top1_probs
    n = len(tokens)

    # -- left: top-1 column ----------------------------------------------
    ax = ax_top1
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, n - 0.5)
    ax.invert_yaxis()
    ax.set_yticks(range(n))
    ax.set_yticklabels(
        ["embed" if i == 0 else f"L{i - 1:02d}" for i in range(n)],
        fontsize=9, fontfamily="monospace",
    )
    ax.set_xticks([])
    ax.set_title("Top-1 prediction at each layer",
                 fontsize=11, fontweight="bold")
    ax.set_frame_on(False)
    ax.grid(False)

    cmap = plt.get_cmap("Blues")
    for i in range(n):
        p = float(probs[i])
        shade = cmap(min(0.12 + p * 1.4, 0.92))
        ax.add_patch(Rectangle((0.05, i - 0.4), 0.9, 0.8,
                               facecolor=shade, edgecolor="#555", lw=0.6))
        text_color = "white" if p > 0.35 else "#111"
        ax.text(0.5, i, f"{tokens[i]!r}   {p:5.1%}",
                ha="center", va="center", fontsize=9,
                family="monospace", color=text_color)

    # -- right: emergence curve -----------------------------------------
    curve = result.lens_final_curve
    xs = np.arange(n)
    ax = ax_curve
    ax.plot(xs, curve, "-o", color=COLOR_PALETTE[0], lw=2.0, ms=5)
    ax.fill_between(xs, 0, curve, color=COLOR_PALETTE[0], alpha=0.12)
    ax.set_xticks(xs)
    ax.set_xticklabels(
        ["embed"] + [f"L{i:02d}" for i in range(n - 1)],
        rotation=45, ha="right", fontsize=8,
    )
    ax.set_xlabel("Layer")
    ax.set_ylabel(f"P({result.lens_final_token!r})")
    ax.set_ylim(0, max(float(curve.max()) * 1.15, 0.05))
    ax.set_title(f"Emergence of {result.lens_final_token!r}",
                 fontsize=11, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _draw_na(ax, message: str) -> None:
    ax.text(0.5, 0.5, message, ha="center", va="center",
            transform=ax.transAxes, fontsize=12, color="#555",
            style="italic")
    ax.set_axis_off()


# ---------------------------------------------------------------------------
# Architecture mini-map
# ---------------------------------------------------------------------------

class ArchitectureWindow(QMainWindow):
    """A second window showing the transformer stack as selectable cells.

    Each cell corresponds to one of the tags understood by the main window
    (embedding, block:i:attn, block:i:mlp, block:i:residual, ln_f). The
    main window drives this view via :meth:`highlight`. Clicking a cell
    emits :attr:`cell_clicked` so the main window can update its combo.
    """

    # Emitted when the user picks a cell (tag string).
    cell_clicked = Signal(str)
    # Emitted when the user closes the window (we hide instead of destroy).
    hidden_by_user = Signal()

    COL_EMBEDDING = "#E6DEF0"   # light purple
    COL_ATTN      = "#D6E0F0"   # light blue
    COL_MLP       = "#FAE3D2"   # light orange
    COL_RESIDUAL  = "#D5EDDB"   # light green
    COL_LNF       = "#E6E6E6"   # light grey
    EDGE_DEFAULT  = "#666666"
    EDGE_HIGHLIGHT = "#C44E52"  # palette red
    SENTINEL_LOGIT_LENS = "__logit_lens__"
    SENTINEL_TRAJECTORY = "__trajectory__"

    def __init__(self, n_layers: int, *,
                 d_model: int = 768, d_mlp: int = 3072, n_heads: int = 12,
                 vocab_size: int = 50257, n_positions: int = 1024,
                 parent=None):
        super().__init__(parent)
        self.n_layers = n_layers
        self.d_model = d_model
        self.d_mlp = d_mlp
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        self.vocab_size = vocab_size
        self.n_positions = n_positions
        # Per-cell parameter counts. GPT-2 ties lm_head to wte so the
        # unembedding itself adds no new params beyond the embedding table.
        self.p_attn = 4 * d_model * d_model + 4 * d_model        # QKV + out proj
        self.p_mlp = 2 * d_model * d_mlp + d_model + d_mlp       # c_fc + c_proj
        self.p_embed = vocab_size * d_model + n_positions * d_model
        self.setWindowTitle("Transformer architecture — GPT-2 small")
        self.canvas = FigureCanvas(Figure(figsize=(4.6, 9.4)))
        self.setCentralWidget(self.canvas)
        self.patches: dict[str, Rectangle] = {}
        self._tearing_down = False
        self._build_figure()
        self.canvas.mpl_connect("pick_event", self._on_pick)
        self.resize(460, 920)

    @staticmethod
    def _fmt_m(n: int) -> str:
        """Format a parameter count in megas, e.g. 2362368 -> '≈ 2.4M'."""
        return f"≈ {n / 1e6:.1f}M"

    # -- figure construction ------------------------------------------------

    def _build_figure(self) -> None:
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        # Rows: top = ln_f, then block 11..0, bottom = embedding.
        n_rows = self.n_layers + 2
        ax.set_xlim(0, 10)
        ax.set_ylim(0, n_rows)
        ax.invert_yaxis()
        ax.set_aspect("auto")
        ax.axis("off")
        ax.set_title(self.DEFAULT_TITLE,
                     fontsize=11, fontweight="bold", pad=8, color="#222")

        # --- Top: ln_f + lm_head ---
        row = 0
        self._add_cell(ax, "ln_f", x=0.4, y=row + 0.15, w=9.2, h=0.7,
                       label="ln_f + lm_head", facecolor=self.COL_LNF,
                       label_size=10, label_weight="bold",
                       sublabel=f"{self.d_model} → {self.vocab_size} logits  "
                                f"(lm_head tied with wte)")

        attn_sub = (f"QKV+O  ·  {self.n_heads}×{self.d_head}  "
                    f"·  {self._fmt_m(self.p_attn)}")
        mlp_sub = (f"{self.d_model}→{self.d_mlp}→{self.d_model}  "
                   f"·  {self._fmt_m(self.p_mlp)}")
        # --- Blocks, top-down: block 11 just below ln_f ---
        for i in range(self.n_layers - 1, -1, -1):
            row += 1
            # Outer block background for visual grouping
            ax.add_patch(Rectangle((0.3, row + 0.05), 9.4, 0.9,
                                   facecolor="#FAFAFA", edgecolor="#DDDDDD",
                                   lw=0.6, zorder=0))
            # Block number on the far left
            ax.text(0.05, row + 0.5, f"B{i:>2}",
                    ha="left", va="center", fontsize=8,
                    family="monospace", color="#666")
            # Three interactive sub-cells: Attn | MLP | Residual out
            self._add_cell(ax, f"block:{i}:attn",
                           x=0.8, y=row + 0.15, w=2.7, h=0.7,
                           label="Attn", facecolor=self.COL_ATTN,
                           sublabel=attn_sub, sublabel_size=5.8)
            self._add_cell(ax, f"block:{i}:mlp",
                           x=3.7, y=row + 0.15, w=2.7, h=0.7,
                           label="MLP", facecolor=self.COL_MLP,
                           sublabel=mlp_sub, sublabel_size=5.8)
            self._add_cell(ax, f"block:{i}:residual",
                           x=6.6, y=row + 0.15, w=2.8, h=0.7,
                           label="Res. out", facecolor=self.COL_RESIDUAL,
                           sublabel="sum (no params)", sublabel_size=5.8)

        # --- Bottom: embedding ---
        row += 1
        self._add_cell(ax, "embedding", x=0.4, y=row + 0.15, w=9.2, h=0.7,
                       label="Embedding  (wte + wpe)",
                       facecolor=self.COL_EMBEDDING,
                       label_size=10, label_weight="bold",
                       sublabel=f"wte {self.vocab_size}×{self.d_model}  +  "
                                f"wpe {self.n_positions}×{self.d_model}  ·  "
                                f"{self._fmt_m(self.p_embed)}")

        # Footer: flow shapes — reinforces that the residual stream keeps
        # a constant (T, d_model) shape all the way through; only the MLP
        # and attention heads expand into wider spaces locally.
        fig.text(
            0.5, 0.028,
            f"Residual stream: (T, {self.d_model}) "
            f"— constant at every layer",
            ha="center", va="bottom", fontsize=7.0, color="#333",
            fontweight="bold",
        )
        fig.text(
            0.5, 0.008,
            f"Local widening  —  MLP: (T, {self.d_mlp})   ·   "
            f"Attn: {self.n_heads} heads × {self.d_head}",
            ha="center", va="bottom", fontsize=6.5, color="#555",
            style="italic",
        )

        fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.06)
        self.canvas.draw_idle()

    def _add_cell(self, ax, tag: str, *, x: float, y: float, w: float, h: float,
                  label: str, facecolor: str,
                  label_size: int = 9, label_weight: str = "normal",
                  sublabel: Optional[str] = None,
                  sublabel_size: float = 6.5) -> None:
        rect = Rectangle((x, y), w, h,
                         facecolor=facecolor, edgecolor=self.EDGE_DEFAULT,
                         lw=0.8, zorder=2, picker=True)
        ax.add_patch(rect)
        if sublabel is None:
            ax.text(x + w / 2, y + h / 2, label,
                    ha="center", va="center",
                    fontsize=label_size, fontweight=label_weight,
                    color="#222", zorder=3)
        else:
            ax.text(x + w / 2, y + h / 2 - 0.13, label,
                    ha="center", va="center",
                    fontsize=label_size, fontweight=label_weight,
                    color="#222", zorder=3)
            ax.text(x + w / 2, y + h / 2 + 0.18, sublabel,
                    ha="center", va="center",
                    fontsize=sublabel_size, style="italic",
                    color="#555", zorder=3)
        self.patches[tag] = rect

    # -- interaction --------------------------------------------------------

    def _on_pick(self, event) -> None:
        for tag, patch in self.patches.items():
            if patch is event.artist:
                self.cell_clicked.emit(tag)
                return

    DEFAULT_TITLE = "Where is the current view?"
    LOGIT_LENS_TITLE = "Logit lens — cross-layer probe"
    TRAJECTORY_TITLE = "Residual stream — cross-layer trajectory"

    def highlight(self, tag: Optional[str]) -> None:
        """Ring the cell matching *tag*. Clear otherwise.

        Sentinel ``__logit_lens__`` is a cross-layer mode: rings ln_f and
        all residual cells and updates the title to indicate the probe
        is not bound to a single layer.
        """
        for p in self.patches.values():
            p.set_edgecolor(self.EDGE_DEFAULT)
            p.set_linewidth(0.8)

        ax = self.canvas.figure.axes[0]
        if tag is None:
            ax.set_title(self.DEFAULT_TITLE,
                         fontsize=11, fontweight="bold", pad=8, color="#222")
            self.canvas.draw_idle()
            return

        if tag == self.SENTINEL_LOGIT_LENS:
            for i in range(self.n_layers):
                p = self.patches.get(f"block:{i}:residual")
                if p is not None:
                    p.set_edgecolor(self.EDGE_HIGHLIGHT)
                    p.set_linewidth(1.6)
            p = self.patches.get("ln_f")
            if p is not None:
                p.set_edgecolor(self.EDGE_HIGHLIGHT)
                p.set_linewidth(2.8)
            ax.set_title(self.LOGIT_LENS_TITLE,
                         fontsize=11, fontweight="bold", pad=8,
                         color=self.EDGE_HIGHLIGHT)
        elif tag == self.SENTINEL_TRAJECTORY:
            p = self.patches.get("embedding")
            if p is not None:
                p.set_edgecolor(self.EDGE_HIGHLIGHT)
                p.set_linewidth(2.4)
            for i in range(self.n_layers):
                p = self.patches.get(f"block:{i}:residual")
                if p is not None:
                    p.set_edgecolor(self.EDGE_HIGHLIGHT)
                    p.set_linewidth(1.6)
            ax.set_title(self.TRAJECTORY_TITLE,
                         fontsize=11, fontweight="bold", pad=8,
                         color=self.EDGE_HIGHLIGHT)
        elif tag in self.patches:
            p = self.patches[tag]
            p.set_edgecolor(self.EDGE_HIGHLIGHT)
            p.set_linewidth(2.8)
            ax.set_title(self.DEFAULT_TITLE,
                         fontsize=11, fontweight="bold", pad=8, color="#222")

        self.canvas.draw_idle()

    # -- lifecycle ----------------------------------------------------------

    def closeEvent(self, event) -> None:
        # Hide rather than destroy so the main window can re-show us — unless
        # the main window is explicitly tearing us down on shutdown.
        if self._tearing_down:
            super().closeEvent(event)
            return
        event.ignore()
        self.hide()
        self.hidden_by_user.emit()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class MainWindow(QMainWindow):
    VIEW_HEATMAP = 0
    VIEW_PCA = 1
    VIEW_COSINE = 2
    VIEW_LOGIT_LENS = 3
    VIEW_TRAJECTORY = 4

    DEBOUNCE_MS = 300

    def __init__(self, backend: ModelBackend,
                 arch: Optional["ArchitectureWindow"] = None):
        super().__init__()
        self.backend = backend
        self.arch = arch
        self.current: Optional[ForwardResult] = None

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._run_forward)

        self.setWindowTitle("LLM Explorer — GPT-2 small")
        self._build_ui()
        self.resize(1280, 820)

        if self.arch is not None:
            self.arch.cell_clicked.connect(self._on_arch_cell_clicked)
            self.arch.hidden_by_user.connect(
                lambda: self.arch_btn.setChecked(False))

        # Kick off with a sensible initial prompt
        self.prompt_edit.setText("The Eiffel Tower is in the city of")
        self._update_pca_axes_visibility()
        self._run_forward()
        self._update_arch()

    # -- UI construction ---------------------------------------------------

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # --- top bar: prompt | live | run -------------------------------
        top = QHBoxLayout()
        top.addWidget(QLabel("Prompt:"))
        self.prompt_edit = QLineEdit()
        self.prompt_edit.textChanged.connect(self._on_prompt_changed)
        self.prompt_edit.returnPressed.connect(self._run_forward)
        top.addWidget(self.prompt_edit, stretch=1)

        self.live_cb = QCheckBox("Live")
        self.live_cb.setChecked(True)
        self.live_cb.setToolTip(
            "When on, re-run 300 ms after typing stops. "
            "Uncheck to only recompute on Run.")
        top.addWidget(self.live_cb)

        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run_forward)
        top.addWidget(self.run_btn)

        self.arch_btn = QPushButton("Arch")
        self.arch_btn.setCheckable(True)
        self.arch_btn.setChecked(self.arch is not None)
        self.arch_btn.setEnabled(self.arch is not None)
        self.arch_btn.setToolTip(
            "Show / hide the transformer architecture mini-map.")
        self.arch_btn.toggled.connect(self._toggle_arch)
        top.addWidget(self.arch_btn)

        root.addLayout(top)

        # --- splitter: controls | plots ---------------------------------
        splitter = QSplitter(Qt.Horizontal)
        root.addWidget(splitter, stretch=1)

        splitter.addWidget(self._build_controls())
        splitter.addWidget(self._build_plots())
        splitter.setSizes([260, 1020])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # --- status bar -------------------------------------------------
        self.status = self.statusBar()
        self.status.showMessage("Ready.")

    def _build_controls(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(8, 4, 8, 4)

        lay.addWidget(QLabel("Layer:"))
        self.layer_combo = QComboBox()
        self._populate_layers()
        self.layer_combo.currentIndexChanged.connect(self._on_selection_changed)
        lay.addWidget(self.layer_combo)

        lay.addWidget(QLabel("Head:"))
        self.head_combo = QComboBox()
        self._populate_heads()
        self.head_combo.currentIndexChanged.connect(self._on_selection_changed)
        lay.addWidget(self.head_combo)

        lay.addSpacing(8)
        lay.addWidget(QLabel("View:"))
        self.view_group = QButtonGroup(self)
        for i, name in enumerate(
            ["Heatmap", "PCA (vocab ref)", "Cosine", "Logit lens",
             "Trajectory"]
        ):
            rb = QRadioButton(name)
            if i == 0:
                rb.setChecked(True)
            self.view_group.addButton(rb, i)
            lay.addWidget(rb)
        self.view_group.idClicked.connect(self._on_view_changed)

        # --- PCA axis pickers (visible only for the PCA view) -----------
        self.pca_axes_label = QLabel("PCA axes:")
        lay.addWidget(self.pca_axes_label)
        pca_row = QHBoxLayout()
        pca_row.setContentsMargins(0, 0, 0, 0)
        self.pca_x_combo = QComboBox()
        self.pca_y_combo = QComboBox()
        for k in range(N_PCA_COMPONENTS):
            self.pca_x_combo.addItem(f"PC{k + 1}", k)
            self.pca_y_combo.addItem(f"PC{k + 1}", k)
        self.pca_x_combo.setCurrentIndex(0)
        self.pca_y_combo.setCurrentIndex(1)
        self.pca_x_combo.setToolTip("Which principal component on the X axis.")
        self.pca_y_combo.setToolTip("Which principal component on the Y axis.")
        self.pca_x_combo.currentIndexChanged.connect(self._redraw_main)
        self.pca_y_combo.currentIndexChanged.connect(self._redraw_main)
        pca_row.addWidget(QLabel("X"))
        pca_row.addWidget(self.pca_x_combo, stretch=1)
        pca_row.addSpacing(6)
        pca_row.addWidget(QLabel("Y"))
        pca_row.addWidget(self.pca_y_combo, stretch=1)
        self._pca_axes_widget = QWidget()
        self._pca_axes_widget.setLayout(pca_row)
        lay.addWidget(self._pca_axes_widget)

        lay.addSpacing(8)
        self.soften_cb = QCheckBox("Soften pos-0 sink")
        self.soften_cb.setChecked(False)
        self.soften_cb.setToolTip(
            "Drop position 0 from the view and renormalize. Attention rows "
            "are re-scaled to sum to 1 without the sink column; hidden-state "
            "views simply omit the pos-0 row (and its column, for cosine). "
            "Default OFF so the audience sees the sink artifact first.")
        self.soften_cb.stateChanged.connect(self._redraw_main)
        lay.addWidget(self.soften_cb)

        lay.addSpacing(12)
        lay.addWidget(QLabel("Tokens (input):"))
        self.tokens_list = QListWidget()
        self.tokens_list.setMaximumHeight(260)
        lay.addWidget(self.tokens_list)

        lay.addStretch(1)
        return w

    def _build_plots(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        self.main_canvas = FigureCanvas(Figure(figsize=(8, 5)))
        self.topk_canvas = FigureCanvas(Figure(figsize=(8, 3)))
        lay.addWidget(self.main_canvas, stretch=3)
        lay.addWidget(self.topk_canvas, stretch=2)
        return w

    def _populate_layers(self):
        self.layer_combo.addItem("Embedding (wte + wpe)", "embedding")
        for i in range(self.backend.n_layers):
            self.layer_combo.addItem(f"Block {i:>2} — attention",
                                     f"block:{i}:attn")
            self.layer_combo.addItem(f"Block {i:>2} — MLP (post-GELU)",
                                     f"block:{i}:mlp")
            self.layer_combo.addItem(f"Block {i:>2} — residual out",
                                     f"block:{i}:residual")
        self.layer_combo.addItem("Final ln_f output", "ln_f")

    def _populate_heads(self):
        self.head_combo.addItem("All heads (avg)", -1)
        for i in range(self.backend.n_heads):
            self.head_combo.addItem(f"Head {i}", i)

    # -- slots -------------------------------------------------------------

    def _on_prompt_changed(self):
        if self.live_cb.isChecked():
            self._debounce.start(self.DEBOUNCE_MS)

    def _on_selection_changed(self):
        tag = self.layer_combo.currentData()
        self.head_combo.setEnabled(bool(tag) and is_attention_tag(tag))
        # A new layer/head is a fresh subject of inspection — fall back to
        # the canonical PC1/PC2 so the user always starts from a consistent
        # view before exploring higher components.
        self._reset_pca_axes()
        self._redraw_main()
        self._update_arch()

    def _on_view_changed(self, _view_id: int) -> None:
        self._update_pca_axes_visibility()
        self._redraw_main()
        self._update_arch()

    def _reset_pca_axes(self) -> None:
        for combo, default in ((self.pca_x_combo, 0), (self.pca_y_combo, 1)):
            combo.blockSignals(True)
            combo.setCurrentIndex(default)
            combo.blockSignals(False)

    def _update_pca_axes_visibility(self) -> None:
        shown = self.view_group.checkedId() in (
            self.VIEW_PCA, self.VIEW_TRAJECTORY)
        self.pca_axes_label.setVisible(shown)
        self._pca_axes_widget.setVisible(shown)

    # -- architecture window coupling --------------------------------------

    def _update_arch(self) -> None:
        if self.arch is None:
            return
        view_id = self.view_group.checkedId()
        if view_id == self.VIEW_LOGIT_LENS:
            self.arch.highlight(ArchitectureWindow.SENTINEL_LOGIT_LENS)
        elif view_id == self.VIEW_TRAJECTORY:
            self.arch.highlight(ArchitectureWindow.SENTINEL_TRAJECTORY)
        else:
            self.arch.highlight(self.layer_combo.currentData())

    def _toggle_arch(self, on: bool) -> None:
        if self.arch is None:
            return
        if on:
            self.arch.show()
            self._update_arch()
        else:
            self.arch.hide()

    def _on_arch_cell_clicked(self, tag: str) -> None:
        idx = self.layer_combo.findData(tag)
        if idx != -1:
            # Setting the combo triggers _on_selection_changed, which
            # re-highlights the arch — so the click feels symmetric.
            self.layer_combo.setCurrentIndex(idx)

    def _run_forward(self):
        prompt = self.prompt_edit.text().strip()
        if not prompt:
            self.status.showMessage("Empty prompt — nothing to run.")
            return
        cached = prompt in self.backend._cache
        self.status.showMessage(
            f"Running forward pass... ({'cached' if cached else 'computing'})")
        QApplication.processEvents()

        self.current = self.backend.run(prompt)

        self.tokens_list.clear()
        for i, t in enumerate(self.current.tokens):
            self.tokens_list.addItem(f"{i:>2}  {t!r}")

        self._redraw_main()
        self._redraw_topk()

        argmax_tok, argmax_p = self.current.topk_next[0]
        self.status.showMessage(
            f"{len(self.current.tokens)} tokens  |  "
            f"next: {argmax_tok!r} ({argmax_p:.1%})  |  "
            f"cache size: {len(self.backend._cache)}")

    def _redraw_main(self):
        if self.current is None:
            return
        tag = self.layer_combo.currentData()
        head = self.head_combo.currentData()
        view_id = self.view_group.checkedId()

        fig = self.main_canvas.figure
        fig.clear()

        if view_id == self.VIEW_LOGIT_LENS:
            # Logit lens ignores the Layer / Head selection — it is a
            # cross-layer view by construction.
            axes = fig.subplots(1, 2, gridspec_kw={"width_ratios": [0.9, 1.1]})
            render_logit_lens(self.current, axes[0], axes[1])
        elif view_id == self.VIEW_TRAJECTORY:
            # Also a cross-layer view; layer/head/soften are irrelevant.
            ax = fig.add_subplot(111)
            render_trajectory(self.current, self.backend, ax,
                              pc_x=self.pca_x_combo.currentData(),
                              pc_y=self.pca_y_combo.currentData())
        else:
            soften = self.soften_cb.isChecked()
            ax = fig.add_subplot(111)
            if view_id == self.VIEW_HEATMAP:
                render_heatmap(self.current, tag, head, ax, soften=soften)
            elif view_id == self.VIEW_PCA:
                render_pca(self.current, tag, head, self.backend, ax,
                           soften=soften,
                           pc_x=self.pca_x_combo.currentData(),
                           pc_y=self.pca_y_combo.currentData())
            else:
                render_cosine(self.current, tag, head, ax, soften=soften)

        fig.tight_layout()
        self.main_canvas.draw_idle()

    def _redraw_topk(self):
        if self.current is None:
            return
        fig = self.topk_canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        render_topk(self.current, ax)
        fig.tight_layout()
        self.topk_canvas.draw_idle()

    # -- lifecycle ---------------------------------------------------------

    def closeEvent(self, event):
        # Tear down the arch window for real when the main window closes,
        # since it normally intercepts close to merely hide itself.
        if self.arch is not None:
            self.arch._tearing_down = True
            self.arch.close()
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

def main():
    backend = ModelBackend("gpt2")
    app = QApplication(sys.argv)
    cfg = backend.model.config
    arch = ArchitectureWindow(
        backend.n_layers,
        d_model=backend.d_model,
        d_mlp=backend.d_mlp,
        n_heads=backend.n_heads,
        vocab_size=cfg.vocab_size,
        n_positions=cfg.n_positions,
    )
    win = MainWindow(backend, arch=arch)
    win.show()
    # Position the architecture window just to the right of the main one.
    main_geom = win.frameGeometry()
    arch.move(main_geom.right() + 12, main_geom.top())
    arch.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
