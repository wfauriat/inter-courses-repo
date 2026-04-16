"""
10b_training_vs_inference.py
============================
Educational visualization: the fundamental compute asymmetry between
training (all positions processed in parallel via teacher forcing) and
generation (tokens emitted sequentially, each depending on the last).

Produces two figures:
  - 10b_parallel_vs_sequential.png   Side-by-side schematic
  - 10b_training_loop.png            Circular training-loop flowchart

Pure matplotlib diagrams -- no model loading required.
Usage:
    source ~/.venvDS/bin/activate
    python workspace/10b_training_vs_inference.py
"""

import sys
import os
import math

sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

# ---------------------------------------------------------------------------
# Colour scheme
# ---------------------------------------------------------------------------
COL_BG = "#FAFAFA"
COL_TEXT = "#2B2B2B"
COL_DIM = "#6B6B6B"
COL_ARROW = "#555555"

COL_TRAIN = "#4C72B0"          # training accent
COL_TRAIN_FILL = "#D6E0F0"    # training cell fill
COL_TRAIN_DARK = "#2E5090"    # header / emphasis

COL_GEN = "#DD8452"            # generation accent
COL_GEN_FILL = "#FAE3D2"      # generation cell fill
COL_GEN_DARK = "#B86830"      # emphasis

COL_PROMPT = "#55A868"         # prompt / prefill
COL_PROMPT_FILL = "#D5EDDB"

COL_LOOP_BG = "#E8EDF5"       # light background for the loop diagram
COL_STEP_FILL = "#FFFFFF"     # step box fill

# Training loop step colours
COL_DATA = "#55A868"
COL_FORWARD = "#4C72B0"
COL_LOSS = "#DD8452"
COL_BACKWARD = "#C44E52"
COL_OPTIM = "#8172B3"


# ---------------------------------------------------------------------------
# Helper: rounded box
# ---------------------------------------------------------------------------
def draw_box(ax, cx, cy, w, h, label, edge_col=COL_TEXT,
             fill_col="#FFFFFF", fontsize=10, fontweight="bold",
             text_col=COL_TEXT, radius=0.02, alpha=1.0, zorder=2,
             ha="center", va="center", linestyle="-", linewidth=1.5):
    box = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        linewidth=linewidth, edgecolor=edge_col, facecolor=fill_col,
        zorder=zorder, alpha=alpha, linestyle=linestyle,
    )
    ax.add_patch(box)
    ax.text(cx, cy, label, ha=ha, va=va,
            fontsize=fontsize, fontweight=fontweight, color=text_col,
            zorder=zorder + 1, alpha=alpha)


# ---------------------------------------------------------------------------
# Figure 1 -- Parallel vs Sequential schematic
# ---------------------------------------------------------------------------
def make_parallel_vs_sequential():
    set_style()

    fig, (ax_train, ax_gen) = plt.subplots(1, 2, figsize=(16, 9))
    for ax in (ax_train, ax_gen):
        ax.set_xlim(-0.5, 10.5)
        ax.set_ylim(-2.5, 8.5)
        ax.axis("off")
    fig.patch.set_facecolor(COL_BG)

    # --- Overall title ---
    fig.suptitle(
        "Training vs Generation: The Fundamental Compute Asymmetry",
        fontsize=17, fontweight="bold", color=COL_TEXT, y=0.97,
    )

    # =====================================================================
    # LEFT PANEL -- Training (parallel)
    # =====================================================================
    ax = ax_train
    ax.set_title("Training  (teacher forcing)", fontsize=14,
                 fontweight="bold", color=COL_TRAIN_DARK, pad=14)

    n_batch = 4
    n_pos = 8
    cell_w = 1.05
    cell_h = 0.85
    grid_x0 = 0.6
    grid_y0 = 6.8

    # Row labels
    for r in range(n_batch):
        y = grid_y0 - r * cell_h
        ax.text(grid_x0 - 0.35, y - cell_h / 2, f"seq {r+1}",
                ha="right", va="center", fontsize=9, color=COL_DIM,
                fontfamily="monospace")

    # Column headers
    for c in range(n_pos):
        x = grid_x0 + c * cell_w
        ax.text(x + cell_w / 2, grid_y0 + 0.25, f"pos {c}",
                ha="center", va="center", fontsize=8, color=COL_DIM,
                fontfamily="monospace")

    # Draw grid cells -- all filled simultaneously
    for r in range(n_batch):
        for c in range(n_pos):
            x = grid_x0 + c * cell_w
            y = grid_y0 - r * cell_h
            # Slight colour variation for visual interest
            saturation = 0.55 + 0.45 * ((r + c) % 3) / 2
            rect = mpatches.FancyBboxPatch(
                (x + 0.04, y - cell_h + 0.04),
                cell_w - 0.08, cell_h - 0.08,
                boxstyle="round,pad=0,rounding_size=0.04",
                facecolor=COL_TRAIN_FILL,
                edgecolor=COL_TRAIN,
                linewidth=1.2, alpha=saturation,
                zorder=2,
            )
            ax.add_patch(rect)
            # Token placeholder
            ax.text(x + cell_w / 2, y - cell_h / 2, f"t{c}",
                    ha="center", va="center", fontsize=8,
                    color=COL_TRAIN_DARK, fontweight="bold",
                    alpha=saturation, zorder=3)

    # Big bracket/flash annotation: "all at once"
    brace_x = grid_x0 + n_pos * cell_w + 0.3
    brace_y_top = grid_y0
    brace_y_bot = grid_y0 - n_batch * cell_h
    mid_y = (brace_y_top + brace_y_bot) / 2

    ax.annotate("", xy=(brace_x, brace_y_top),
                xytext=(brace_x, brace_y_bot),
                arrowprops=dict(arrowstyle="-", color=COL_TRAIN_DARK,
                                lw=2.0))
    # top and bottom ticks of bracket
    for yy in (brace_y_top, brace_y_bot):
        ax.plot([brace_x - 0.1, brace_x], [yy, yy],
                color=COL_TRAIN_DARK, lw=2.0, zorder=3)

    ax.text(brace_x + 0.15, mid_y,
            "One\nforward\npass",
            ha="left", va="center", fontsize=10,
            fontweight="bold", color=COL_TRAIN_DARK)

    # Label below grid
    label_y = grid_y0 - n_batch * cell_h - 0.65
    ax.text(grid_x0 + n_pos * cell_w / 2, label_y,
            "All positions computed at once\n(teacher forcing: targets are known)",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color=COL_TRAIN_DARK)

    # Training outer-loop annotation at the bottom
    loop_y = label_y - 1.25
    loop_steps = [
        "forward",
        "loss",
        "backward\n(autograd)",
        "update\nweights",
    ]
    step_w = 1.8
    total_w = len(loop_steps) * step_w + (len(loop_steps) - 1) * 0.6
    start_x = grid_x0 + (n_pos * cell_w - total_w) / 2

    for i, step_label in enumerate(loop_steps):
        sx = start_x + i * (step_w + 0.6)
        draw_box(ax, sx + step_w / 2, loop_y, step_w, 0.7, step_label,
                 edge_col=COL_TRAIN, fill_col=COL_TRAIN_FILL,
                 fontsize=8.5, fontweight="bold", text_col=COL_TRAIN_DARK,
                 radius=0.04, linewidth=1.2)

        # Arrow between steps
        if i < len(loop_steps) - 1:
            ax.annotate(
                "", xy=(sx + step_w + 0.15, loop_y),
                xytext=(sx + step_w + 0.45, loop_y),
                arrowprops=dict(arrowstyle="<-", color=COL_TRAIN_DARK,
                                lw=1.5),
            )

    # "repeat" loop-back arrow under the steps
    ax.annotate(
        "",
        xy=(start_x + 0.1, loop_y - 0.55),
        xytext=(start_x + total_w - 0.1, loop_y - 0.55),
        arrowprops=dict(
            arrowstyle="<-",
            color=COL_TRAIN, lw=1.4,
            connectionstyle="arc3,rad=0.35",
        ),
    )
    ax.text(start_x + total_w / 2, loop_y - 1.15, "repeat for each batch",
            ha="center", va="center", fontsize=9, color=COL_TRAIN,
            fontweight="bold", style="italic")

    # =====================================================================
    # RIGHT PANEL -- Generation (sequential)
    # =====================================================================
    ax = ax_gen
    ax.set_title("Generation  (autoregressive)", fontsize=14,
                 fontweight="bold", color=COL_GEN_DARK, pad=14)

    n_prompt = 5
    n_gen = 3
    n_total = n_prompt + n_gen
    row_y = 5.8
    cell_w_gen = 1.05
    cell_h_gen = 1.0
    x0 = 0.4

    # --- Prompt tokens (prefill -- parallel) ---
    for c in range(n_prompt):
        x = x0 + c * cell_w_gen
        rect = mpatches.FancyBboxPatch(
            (x + 0.04, row_y - cell_h_gen + 0.04),
            cell_w_gen - 0.08, cell_h_gen - 0.08,
            boxstyle="round,pad=0,rounding_size=0.04",
            facecolor=COL_PROMPT_FILL,
            edgecolor=COL_PROMPT,
            linewidth=1.5, zorder=2,
        )
        ax.add_patch(rect)
        ax.text(x + cell_w_gen / 2, row_y - cell_h_gen / 2,
                f"p{c}", ha="center", va="center",
                fontsize=10, fontweight="bold", color="#2D7A3F", zorder=3)

    # Bracket under prompt
    prompt_left = x0 + 0.04
    prompt_right = x0 + n_prompt * cell_w_gen - 0.04
    bracket_y = row_y - cell_h_gen - 0.15
    ax.plot([prompt_left, prompt_left], [bracket_y, bracket_y - 0.12],
            color=COL_PROMPT, lw=1.5)
    ax.plot([prompt_right, prompt_right], [bracket_y, bracket_y - 0.12],
            color=COL_PROMPT, lw=1.5)
    ax.plot([prompt_left, prompt_right], [bracket_y - 0.12, bracket_y - 0.12],
            color=COL_PROMPT, lw=1.5)
    ax.text((prompt_left + prompt_right) / 2, bracket_y - 0.42,
            "prefill  (parallel)",
            ha="center", va="center", fontsize=10, fontweight="bold",
            color=COL_PROMPT)

    # --- Generated tokens (sequential, one at a time) ---
    opacity_steps = [1.0, 0.7, 0.4]

    for i, c in enumerate(range(n_prompt, n_total)):
        x = x0 + c * cell_w_gen
        alpha = opacity_steps[i]
        rect = mpatches.FancyBboxPatch(
            (x + 0.04, row_y - cell_h_gen + 0.04),
            cell_w_gen - 0.08, cell_h_gen - 0.08,
            boxstyle="round,pad=0,rounding_size=0.04",
            facecolor=COL_GEN_FILL,
            edgecolor=COL_GEN,
            linewidth=1.5, alpha=alpha, zorder=2,
        )
        ax.add_patch(rect)
        ax.text(x + cell_w_gen / 2, row_y - cell_h_gen / 2,
                f"g{i+1}", ha="center", va="center",
                fontsize=10, fontweight="bold", color=COL_GEN_DARK,
                alpha=alpha, zorder=3)

        # Step number above the cell
        ax.text(x + cell_w_gen / 2, row_y + 0.22,
                f"step {i+1}", ha="center", va="center",
                fontsize=8.5, fontweight="bold", color=COL_GEN_DARK,
                alpha=alpha,
                bbox=dict(boxstyle="round,pad=0.15", facecolor=COL_GEN_FILL,
                          edgecolor=COL_GEN, alpha=alpha * 0.6, linewidth=0.8))

        # Sequential arrow from previous cell to this one
        if i == 0:
            # Arrow from last prompt token
            ax.annotate(
                "", xy=(x + 0.06, row_y - cell_h_gen / 2),
                xytext=(x - 0.12, row_y - cell_h_gen / 2),
                arrowprops=dict(arrowstyle="->,head_width=0.12,head_length=0.06",
                                color=COL_GEN_DARK, lw=1.8),
            )
        else:
            ax.annotate(
                "", xy=(x + 0.06, row_y - cell_h_gen / 2),
                xytext=(x - 0.12, row_y - cell_h_gen / 2),
                arrowprops=dict(arrowstyle="->,head_width=0.12,head_length=0.06",
                                color=COL_GEN_DARK, lw=1.8,
                                alpha=alpha),
            )

    # Bracket under generated tokens
    gen_left = x0 + n_prompt * cell_w_gen + 0.04
    gen_right = x0 + n_total * cell_w_gen - 0.04
    ax.plot([gen_left, gen_left], [bracket_y, bracket_y - 0.12],
            color=COL_GEN, lw=1.5)
    ax.plot([gen_right, gen_right], [bracket_y, bracket_y - 0.12],
            color=COL_GEN, lw=1.5)
    ax.plot([gen_left, gen_right], [bracket_y - 0.12, bracket_y - 0.12],
            color=COL_GEN, lw=1.5)
    ax.text((gen_left + gen_right) / 2, bracket_y - 0.42,
            "generate  (sequential)",
            ha="center", va="center", fontsize=10, fontweight="bold",
            color=COL_GEN_DARK)

    # Dependency annotation
    dep_y = bracket_y - 1.05
    ax.text(x0 + n_total * cell_w_gen / 2, dep_y,
            "token t+1 depends on token t",
            ha="center", va="center", fontsize=11, fontweight="bold",
            color=COL_GEN_DARK, style="italic")

    # --- Key insight box at the bottom of the generation panel ---
    insight_y = dep_y - 1.4
    insight_text = (
        "Generating N tokens requires N sequential\n"
        "forward passes (one per new token).\n"
        "This is the main inference bottleneck."
    )
    draw_box(ax, x0 + n_total * cell_w_gen / 2, insight_y,
             6.5, 1.3, insight_text,
             edge_col=COL_GEN, fill_col="#FFF8F2",
             fontsize=10, fontweight="normal", text_col=COL_GEN_DARK,
             radius=0.06, linewidth=1.5)

    # --- Corresponding insight box on the training side ---
    ax_train_insight_y = insight_y
    train_insight = (
        "One forward pass processes all positions\n"
        "and all sequences in the batch at once.\n"
        "GPU parallelism is fully utilized."
    )
    draw_box(ax_train, grid_x0 + n_pos * cell_w / 2, ax_train_insight_y,
             6.5, 1.3, train_insight,
             edge_col=COL_TRAIN, fill_col="#F2F5FB",
             fontsize=10, fontweight="normal", text_col=COL_TRAIN_DARK,
             radius=0.06, linewidth=1.5)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    return fig


# ---------------------------------------------------------------------------
# Figure 2 -- Training loop circular diagram
# ---------------------------------------------------------------------------
def make_training_loop():
    set_style()

    fig, ax = plt.subplots(figsize=(11, 11))
    ax.set_xlim(-6.5, 6.5)
    ax.set_ylim(-6.5, 6.5)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(COL_BG)

    # Title
    ax.text(0, 6.1, "The Training Loop",
            ha="center", va="center", fontsize=18, fontweight="bold",
            color=COL_TEXT)
    ax.text(0, 5.6, "One iteration: batch in, weights updated, repeat",
            ha="center", va="center", fontsize=12, color=COL_DIM)

    # --- Central model box ---
    model_w, model_h = 3.2, 1.6
    model_box = FancyBboxPatch(
        (-model_w / 2, -model_h / 2), model_w, model_h,
        boxstyle="round,pad=0,rounding_size=0.12",
        facecolor="#E8EDF5", edgecolor=COL_TRAIN_DARK,
        linewidth=2.5, zorder=5,
    )
    ax.add_patch(model_box)
    ax.text(0, 0.2, "Transformer\nModel", ha="center", va="center",
            fontsize=14, fontweight="bold", color=COL_TRAIN_DARK, zorder=6)
    ax.text(0, -0.5, "(weights: W)", ha="center", va="center",
            fontsize=10, color=COL_DIM, fontfamily="monospace", zorder=6)

    # --- Loop steps arranged in a circle around the model ---
    # Steps:
    # 0: Training data (batches)    -- top
    # 1: Forward pass               -- top-right
    # 2: Compute loss               -- bottom-right
    # 3: Backward pass              -- bottom
    # 4: Optimizer step             -- top-left
    steps = [
        ("Training Data\n(batches)",               COL_DATA,     "#D5EDDB"),
        ("Forward Pass\n(all positions,\nparallel)", COL_FORWARD,  "#D6E0F0"),
        ("Compute Loss\n(cross-entropy at\neach position)", COL_LOSS, "#FAE3D2"),
        ("Backward Pass\n(autograd: compute\ngradients)", COL_BACKWARD, "#F2D5D5"),
        ("Optimizer Step\n(update weights)",        COL_OPTIM,    "#E0DAEF"),
    ]

    n_steps = len(steps)
    radius = 4.0
    # Arrange starting from the top and going clockwise
    # Angle 0 = top, increasing clockwise
    angles_deg = [90, 18, -54, -126, -198]
    angles_rad = [math.radians(a) for a in angles_deg]

    box_w = 2.8
    box_h = 1.5
    step_positions = []

    for i, (label, edge_c, fill_c) in enumerate(steps):
        angle = angles_rad[i]
        cx = radius * math.cos(angle)
        cy = radius * math.sin(angle)
        step_positions.append((cx, cy))

        step_box = FancyBboxPatch(
            (cx - box_w / 2, cy - box_h / 2), box_w, box_h,
            boxstyle="round,pad=0,rounding_size=0.08",
            facecolor=fill_c, edgecolor=edge_c,
            linewidth=2.0, zorder=4,
        )
        ax.add_patch(step_box)

        # Step number badge
        badge_r = 0.25
        badge_x = cx - box_w / 2 + 0.25
        badge_y = cy + box_h / 2 - 0.25
        badge = mpatches.Circle((badge_x, badge_y), badge_r,
                                facecolor=edge_c, edgecolor="white",
                                linewidth=1.5, zorder=6)
        ax.add_patch(badge)
        ax.text(badge_x, badge_y, str(i + 1),
                ha="center", va="center", fontsize=10,
                fontweight="bold", color="white", zorder=7)

        ax.text(cx, cy - 0.05, label,
                ha="center", va="center", fontsize=10.5,
                fontweight="bold", color=COL_TEXT, zorder=5)

    # --- Draw curved arrows between consecutive steps ---
    for i in range(n_steps):
        j = (i + 1) % n_steps
        x1, y1 = step_positions[i]
        x2, y2 = step_positions[j]

        # Compute points on the edge of the boxes (towards each other)
        dx = x2 - x1
        dy = y2 - y1
        dist = math.sqrt(dx ** 2 + dy ** 2)
        ux, uy = dx / dist, dy / dist

        # Start and end points offset from box centres
        # Determine which edge of the box to start/end from
        pad_start = _box_edge_offset(ux, uy, box_w / 2, box_h / 2) + 0.08
        pad_end = _box_edge_offset(-ux, -uy, box_w / 2, box_h / 2) + 0.08

        sx = x1 + ux * pad_start
        sy = y1 + uy * pad_start
        ex = x2 - ux * pad_end
        ey = y2 - uy * pad_end

        edge_c = steps[i][1]

        ax.annotate(
            "", xy=(ex, ey), xytext=(sx, sy),
            arrowprops=dict(
                arrowstyle="->,head_width=0.2,head_length=0.12",
                color=edge_c, lw=2.2,
                connectionstyle="arc3,rad=0.15",
            ),
            zorder=3,
        )

    # --- Radial dashed lines from centre to forward and backward steps ---
    for idx in [1, 3]:  # forward, backward
        sx, sy = step_positions[idx]
        # Line from model box edge to step box edge
        dx = sx
        dy = sy
        dist = math.sqrt(dx ** 2 + dy ** 2)
        ux, uy = dx / dist, dy / dist

        # Inner edge (model box)
        inner_pad = _box_edge_offset(ux, uy, model_w / 2, model_h / 2) + 0.05
        # Outer edge (step box)
        outer_pad = _box_edge_offset(-ux, -uy, box_w / 2, box_h / 2) + 0.05

        lx1 = ux * inner_pad
        ly1 = uy * inner_pad
        lx2 = sx - ux * outer_pad
        ly2 = sy - uy * outer_pad

        ax.plot([lx1, lx2], [ly1, ly2],
                color="#BBBBBB", lw=1.2, linestyle="--", zorder=1)

    # --- Bottom annotation ---
    ax.text(0, -6.05,
            "Each iteration processes one batch.  "
            "Gradients from the backward pass tell the optimizer\n"
            "how to adjust every weight so the model's predictions improve.",
            ha="center", va="center", fontsize=10, color=COL_DIM,
            linespacing=1.5,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#F0F0F0",
                      edgecolor="#CCCCCC", linewidth=0.8))

    fig.tight_layout()
    return fig


def _box_edge_offset(ux, uy, half_w, half_h):
    """Distance from box centre to its edge along direction (ux, uy)."""
    # Find the intersection of the ray from the centre with the box boundary
    if abs(ux) < 1e-9:
        return half_h
    if abs(uy) < 1e-9:
        return half_w
    tx = half_w / abs(ux)
    ty = half_h / abs(uy)
    t = min(tx, ty)
    return t


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=== Figure 1: Parallel vs Sequential schematic ===")
    fig1 = make_parallel_vs_sequential()
    save_fig(fig1, "10b_parallel_vs_sequential")

    print("\n=== Figure 2: Training loop diagram ===")
    fig2 = make_training_loop()
    save_fig(fig2, "10b_training_loop")

    print("\nDone.")
