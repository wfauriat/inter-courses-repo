"""
10 - Training Objective: Learning by Predicting the Next Token
==============================================================

An LLM learns by minimising *cross-entropy loss* -- the gap between its
predicted probability distribution over the vocabulary and the one-hot
distribution that places all mass on the true next token.  The loss for
a single example is simply  loss = -log P(correct token).

Gradient descent iteratively adjusts billions of parameters to push that
loss down.  This script produces three figures using only **synthetic
data** (no model is loaded -- everything runs in milliseconds):

1. Concrete loss example -- side-by-side bar charts showing the model's
   predicted distribution before and after training, with the loss value
   annotated.
2. Training loss curve -- simulated training and validation loss over
   5 000 steps, illustrating typical learning dynamics and overfitting.
3. Gradient descent intuition -- a 2D contour plot of a synthetic loss
   landscape with an optimisation trajectory overlaid.
"""

import sys
import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LogNorm

# ── shared helpers ──────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE

set_style()


# ========================================================================
# Figure 1 -- Concrete cross-entropy loss example
# ========================================================================

def plot_loss_concrete():
    """Side-by-side bar charts: predicted distribution before vs. after
    training for the prompt 'The capital of France is ___'."""

    tokens = ["Paris", "London", "the", "Berlin", "a", "Lyon", "not", "in"]

    # --- Before training: near-uniform with slight randomness -----------
    rng = np.random.RandomState(42)
    before = rng.dirichlet(np.ones(len(tokens)) * 3.0)
    # Nudge "Paris" to ~0.02 for a clean annotation
    paris_idx = 0
    before[paris_idx] = 0.02
    before[1:] = before[1:] / before[1:].sum() * (1.0 - 0.02)

    # --- After training: peaked on Paris --------------------------------
    after = np.array([0.85, 0.04, 0.03, 0.025, 0.02, 0.015, 0.01, 0.01])
    after = after / after.sum()  # normalise to exactly 1

    loss_before = -np.log(before[paris_idx])
    loss_after = -np.log(after[paris_idx])

    # --- Plotting -------------------------------------------------------
    fig, (ax_bef, ax_aft) = plt.subplots(1, 2, figsize=(14, 5.5), sharey=True)

    x = np.arange(len(tokens))
    bar_w = 0.6

    for ax, probs, loss_val, title, title_col in [
        (ax_bef, before, loss_before, "Before training", COLOR_PALETTE[3]),
        (ax_aft, after,  loss_after,  "After training",  COLOR_PALETTE[2]),
    ]:
        colours = [COLOR_PALETTE[3] if title == "Before training"
                   else COLOR_PALETTE[2]] * len(tokens)
        # Highlight Paris bar
        colours[paris_idx] = COLOR_PALETTE[0]

        bars = ax.bar(x, probs, width=bar_w, color=colours, edgecolor="white",
                      linewidth=0.8)

        ax.set_xticks(x)
        ax.set_xticklabels(tokens, rotation=35, ha="right", fontsize=10)
        ax.set_ylabel("Predicted probability" if ax is ax_bef else "")
        ax.set_title(title, fontsize=14, fontweight="bold", color=title_col)
        ax.set_ylim(0, 1.05)

        # Probability label above Paris bar
        paris_bar = bars[paris_idx]
        ax.text(paris_bar.get_x() + paris_bar.get_width() / 2,
                paris_bar.get_height() + 0.02,
                f"P = {probs[paris_idx]:.2f}",
                ha="center", va="bottom", fontsize=11, fontweight="bold",
                color=COLOR_PALETTE[0])

        # Loss annotation
        ax.text(0.97, 0.92,
                f"loss = $-\\log({probs[paris_idx]:.2f})$\n"
                f"        $= {loss_val:.2f}$",
                transform=ax.transAxes, ha="right", va="top",
                fontsize=12, fontfamily="monospace",
                bbox=dict(boxstyle="round,pad=0.4", fc="#f0f0f0",
                          ec="#cccccc", lw=0.8))

    fig.suptitle(
        'Prompt: "The capital of France is ___"',
        fontsize=15, fontweight="bold", y=1.02,
    )

    # Legend
    highlight_patch = mpatches.Patch(color=COLOR_PALETTE[0],
                                      label='Correct token ("Paris")')
    fig.legend(handles=[highlight_patch], loc="upper center",
               bbox_to_anchor=(0.5, 0.98), fontsize=11, frameon=False)

    fig.text(
        0.5, -0.05,
        "Cross-entropy loss = $-\\log\\,P$(correct token).  Lower predicted "
        "probability $\\Rightarrow$ higher loss.\n"
        "Training pushes the model to place more mass on the correct next "
        "token, shrinking the loss from 3.91 to 0.16.",
        ha="center", fontsize=10, color="#555555",
    )

    fig.tight_layout()
    save_fig(fig, "10_loss_concrete")


# ========================================================================
# Figure 2 -- Simulated training loss curve
# ========================================================================

def plot_loss_curve():
    """Training and validation loss over 5 000 steps (synthetic)."""

    rng = np.random.RandomState(7)
    steps = np.arange(0, 5001)

    # --- Training loss: steep drop then slow decay + noise ---------------
    train_smooth = 10.0 * np.exp(-steps / 400.0) + 2.8 * np.exp(-steps / 3000.0) + 0.3
    train_noise = rng.normal(0, 0.12, size=len(steps))
    # Larger noise early, smaller noise late
    noise_scale = 0.6 * np.exp(-steps / 800.0) + 0.15
    train_loss = train_smooth + train_noise * noise_scale

    # --- Validation loss: follows training then diverges (overfitting) ---
    val_smooth = train_smooth + 0.15  # slightly above training
    # After step ~3200, validation starts climbing
    overfit_start = 3200
    overfit_mask = steps > overfit_start
    overfit_rise = np.zeros_like(steps, dtype=float)
    overfit_rise[overfit_mask] = 0.4e-6 * (steps[overfit_mask] - overfit_start) ** 2
    val_smooth = val_smooth + overfit_rise
    val_noise = rng.normal(0, 0.08, size=len(steps))
    val_noise_scale = 0.3 * np.exp(-steps / 800.0) + 0.10
    val_loss = val_smooth + val_noise * val_noise_scale

    # --- Plotting --------------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 5.5))

    ax.plot(steps, train_loss, color=COLOR_PALETTE[0], linewidth=1.0,
            alpha=0.85, label="Training loss")
    ax.plot(steps, val_loss, color=COLOR_PALETTE[3], linewidth=1.0,
            alpha=0.85, label="Validation loss")

    # Shade the overfitting region
    ax.axvspan(overfit_start, 5000, alpha=0.08, color=COLOR_PALETTE[3])
    ax.annotate(
        "Overfitting region\n(val loss rising)",
        xy=(4100, val_loss[4100] + 0.15),
        xytext=(3700, 5.8),
        fontsize=11, fontweight="bold", color=COLOR_PALETTE[3],
        arrowprops=dict(arrowstyle="->", color=COLOR_PALETTE[3], lw=1.5),
        ha="center",
    )

    # Early-stopping annotation
    best_val_step = overfit_start + np.argmin(val_loss[overfit_start:overfit_start+200])
    ax.axvline(best_val_step, ls="--", color="#888888", lw=1.0, alpha=0.7)
    ax.text(best_val_step - 80, 8.5, "Best checkpoint\n(early stopping)",
            fontsize=9, color="#666666", ha="right",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#cccccc",
                      lw=0.6))

    ax.set_xlabel("Training step")
    ax.set_ylabel("Cross-entropy loss")
    ax.set_title("Simulated Training Run", fontsize=15, fontweight="bold")
    ax.legend(fontsize=12, loc="upper right", framealpha=0.9)
    ax.set_xlim(0, 5000)
    ax.set_ylim(0, 11)

    fig.text(
        0.5, -0.04,
        "Loss starts high (~10) and drops steeply as the model learns "
        "basic patterns, then plateaus.\n"
        "Validation loss eventually diverges -- the model memorises "
        "training data instead of generalising (overfitting).",
        ha="center", fontsize=10, color="#555555",
    )

    fig.tight_layout()
    save_fig(fig, "10_loss_curve")


# ========================================================================
# Figure 3 -- Gradient descent on a 2D loss landscape
# ========================================================================

def plot_gradient_descent():
    """Contour plot of a synthetic loss surface with a gradient-descent
    trajectory from a random start to the minimum."""

    # --- Loss surface: Rosenbrock-inspired with a single minimum ---------
    # f(w1, w2) = (1 - w1)^2 + 5*(w2 - w1^2)^2   (minimum at (1, 1))
    w1 = np.linspace(-2.0, 2.5, 400)
    w2 = np.linspace(-1.5, 4.0, 400)
    W1, W2 = np.meshgrid(w1, w2)
    Z = (1.0 - W1) ** 2 + 5.0 * (W2 - W1 ** 2) ** 2

    # --- Gradient descent trajectory (manual simple GD) ------------------
    def grad_f(w):
        """Gradient of the loss surface."""
        g1 = -2.0 * (1.0 - w[0]) - 20.0 * w[0] * (w[1] - w[0] ** 2)
        g2 = 10.0 * (w[1] - w[0] ** 2)
        return np.array([g1, g2])

    lr = 0.02
    n_steps = 250
    path = np.zeros((n_steps + 1, 2))
    path[0] = np.array([-1.5, 3.5])  # starting point

    for i in range(n_steps):
        g = grad_f(path[i])
        path[i + 1] = path[i] - lr * g

    # Subsample for cleaner arrows
    show_idx = np.concatenate([
        np.arange(0, 30, 2),          # dense early (large steps)
        np.arange(30, 100, 5),        # medium
        np.arange(100, n_steps, 15),  # sparse near minimum
    ])
    show_idx = show_idx[show_idx <= n_steps]

    # --- Plotting --------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 7))

    # Filled contours (log scale for better dynamic range)
    levels = np.logspace(-1, 3, 30)
    cf = ax.contourf(W1, W2, Z, levels=levels, cmap="YlOrRd", norm=LogNorm(),
                     alpha=0.75)
    ax.contour(W1, W2, Z, levels=levels, colors="k", linewidths=0.3,
               norm=LogNorm(), alpha=0.35)

    cbar = fig.colorbar(cf, ax=ax, fraction=0.04, pad=0.03)
    cbar.set_label("Loss value", fontsize=11)

    # Trajectory: line + dots
    ax.plot(path[:, 0], path[:, 1], color=COLOR_PALETTE[0], lw=1.2,
            alpha=0.7, zorder=3)
    ax.scatter(path[show_idx, 0], path[show_idx, 1],
               c=COLOR_PALETTE[0], s=18, edgecolors="white", linewidths=0.5,
               zorder=4)

    # Arrows on a few early steps for directionality
    for i in range(0, min(20, len(show_idx) - 1), 2):
        si = show_idx[i]
        si_next = show_idx[min(i + 1, len(show_idx) - 1)]
        dx = path[si_next, 0] - path[si, 0]
        dy = path[si_next, 1] - path[si, 1]
        ax.annotate("", xy=(path[si, 0] + dx, path[si, 1] + dy),
                     xytext=(path[si, 0], path[si, 1]),
                     arrowprops=dict(arrowstyle="-|>", color=COLOR_PALETTE[0],
                                     lw=1.5))

    # Mark start and minimum
    ax.plot(*path[0], marker="o", ms=12, color=COLOR_PALETTE[3],
            markeredgecolor="white", markeredgewidth=1.5, zorder=5)
    ax.annotate("Random\nstart", xy=path[0], xytext=(-1.9, 2.5),
                fontsize=11, fontweight="bold", color=COLOR_PALETTE[3],
                arrowprops=dict(arrowstyle="->", color=COLOR_PALETTE[3],
                                lw=1.5),
                ha="center")

    ax.plot(1.0, 1.0, marker="*", ms=18, color=COLOR_PALETTE[2],
            markeredgecolor="white", markeredgewidth=1.0, zorder=5)
    ax.annotate("Loss\nminimum", xy=(1.0, 1.0), xytext=(1.8, 0.0),
                fontsize=11, fontweight="bold", color=COLOR_PALETTE[2],
                arrowprops=dict(arrowstyle="->", color=COLOR_PALETTE[2],
                                lw=1.5),
                ha="center")

    ax.set_xlabel("Parameter $\\theta_1$")
    ax.set_ylabel("Parameter $\\theta_2$")
    ax.set_title("Gradient Descent on a Loss Landscape",
                 fontsize=15, fontweight="bold")

    fig.text(
        0.5, -0.04,
        "Each dot is one optimisation step.  The gradient (direction of "
        "steepest ascent) is negated\n"
        "to step downhill.  Steps are large early (steep slope) and shrink "
        "near the minimum (flat region).",
        ha="center", fontsize=10, color="#555555",
    )

    fig.tight_layout()
    save_fig(fig, "10_gradient_descent")


# ========================================================================
# Main
# ========================================================================

if __name__ == "__main__":
    plot_loss_concrete()
    plot_loss_curve()
    plot_gradient_descent()
    print("Done -- all three figures saved to workspace/output/")
