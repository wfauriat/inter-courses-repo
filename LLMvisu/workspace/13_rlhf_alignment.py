"""
13 - RLHF & Alignment: Teaching Models Human Preferences
=========================================================

Reinforcement Learning from Human Feedback (RLHF) aligns a language model's
outputs with human values and preferences.  The training signal is not
next-token likelihood but *human ranking*: which of two responses is better?

A reward model is trained on these preference pairs.  It acts as a **learned
utility function** -- a scalar mapping from (prompt, response) to a score
that encodes what humans consider helpful, harmless, and honest.

The policy (language model) is then optimized to maximize this reward, subject
to a KL-divergence penalty that keeps the aligned model close to its SFT
baseline (preventing reward hacking).

This script is entirely conceptual/diagrammatic -- no model loading needed.

Produces three figures:
  - 13_rlhf_pipeline.png          Flowchart of the 3-stage RLHF pipeline
  - 13_rlhf_preference_pairs.png  Visual cards showing preference examples
  - 13_rlhf_reward_shift.png      Reward distribution before vs after alignment

Usage:
    source ~/.venvDS/bin/activate
    python workspace/13_rlhf_alignment.py
"""

import sys
import os

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# -- shared helpers ----------------------------------------------------------
sys.path.insert(0, os.path.dirname(__file__))
from shared.viz import set_style, save_fig, COLOR_PALETTE

set_style()

# Colors from the shared palette, with semantic aliases for this script
BLUE = COLOR_PALETTE[0]       # #4C72B0
ORANGE = COLOR_PALETTE[1]     # #DD8452
GREEN = COLOR_PALETTE[2]      # #55A868
RED = COLOR_PALETTE[3]        # #C44E52
PURPLE = COLOR_PALETTE[4]     # #8172B3
GRAY = COLOR_PALETTE[7]       # #8C8C8C


# =========================================================================
# Figure 1 -- RLHF Pipeline Flowchart
# =========================================================================

def _draw_stage_box(ax, xy, width, height, title, bullets, color,
                    title_fontsize=13, bullet_fontsize=9.5):
    """Draw a rounded box with a colored header bar and bullet points."""
    x, y = xy

    # Main box (white fill, colored border)
    box = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.02",
        facecolor="white", edgecolor=color, linewidth=2.0,
        transform=ax.transData, zorder=2,
    )
    ax.add_patch(box)

    # Header bar (colored fill across the top)
    header_h = 0.065
    header = FancyBboxPatch(
        (x, y + height - header_h), width, header_h,
        boxstyle="round,pad=0.02",
        facecolor=color, edgecolor=color, linewidth=2.0,
        transform=ax.transData, zorder=3,
    )
    ax.add_patch(header)

    # Title text (white on colored header)
    ax.text(
        x + width / 2, y + height - header_h / 2,
        title, fontsize=title_fontsize, fontweight="bold",
        color="white", ha="center", va="center", zorder=4,
    )

    # Bullet points
    text_x = x + 0.035
    text_top = y + height - header_h - 0.025
    line_spacing = 0.042
    for i, bullet in enumerate(bullets):
        ax.text(
            text_x, text_top - i * line_spacing,
            bullet, fontsize=bullet_fontsize,
            color="#333333", ha="left", va="top", zorder=4,
            fontfamily="sans-serif",
        )


def _draw_arrow(ax, start_xy, end_xy, color="#555555", lw=2.0):
    """Draw a curved arrow between two points."""
    arrow = FancyArrowPatch(
        start_xy, end_xy,
        arrowstyle="->,head_width=6,head_length=5",
        connectionstyle="arc3,rad=0.0",
        color=color, linewidth=lw, zorder=5,
    )
    ax.add_patch(arrow)


def plot_rlhf_pipeline():
    """Top-to-bottom flowchart of the 3-stage RLHF pipeline."""
    fig, ax = plt.subplots(figsize=(12, 14))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Figure title
    ax.text(
        0.5, 0.98,
        "RLHF Pipeline: From Pre-trained Model to Aligned Assistant",
        fontsize=17, fontweight="bold", ha="center", va="top",
        color="#222222",
    )
    ax.text(
        0.5, 0.945,
        "Three stages turn a base language model into one that follows human preferences",
        fontsize=11, ha="center", va="top", color="#666666",
    )

    # Layout parameters
    box_w = 0.70
    center_x = (1 - box_w) / 2

    # --- Stage 1: SFT ---
    s1_y = 0.74
    s1_h = 0.17
    _draw_stage_box(
        ax, (center_x, s1_y), box_w, s1_h,
        "Stage 1:  Supervised Fine-Tuning  (SFT)",
        [
            "Start from a pre-trained base model (next-token predictor)",
            "Fine-tune on curated (prompt, high-quality response) pairs",
            "Model learns the format: follow instructions, answer questions",
            "Result: a capable but unaligned assistant",
        ],
        BLUE,
    )

    # Arrow 1 -> 2
    arrow1_start = (0.5, s1_y - 0.005)
    arrow1_end = (0.5, s1_y - 0.045)
    _draw_arrow(ax, arrow1_start, arrow1_end, color=BLUE)

    # --- Stage 2: Reward Model ---
    s2_y = 0.44
    s2_h = 0.25
    _draw_stage_box(
        ax, (center_x, s2_y), box_w, s2_h,
        "Stage 2:  Reward Model Training",
        [
            "Same prompt  -->  SFT model generates multiple responses",
            "Human annotators rank responses  (preferred vs rejected)",
            "Train a reward model R(prompt, response) --> scalar score",
            "R acts as a learned utility function encoding human values",
            "Trained via Bradley-Terry model on pairwise comparisons",
        ],
        ORANGE,
    )

    # Arrow 2 -> 3
    arrow2_start = (0.5, s2_y - 0.005)
    arrow2_end = (0.5, s2_y - 0.045)
    _draw_arrow(ax, arrow2_start, arrow2_end, color=ORANGE)

    # --- Stage 3: Policy Optimization ---
    s3_y = 0.12
    s3_h = 0.25
    _draw_stage_box(
        ax, (center_x, s3_y), box_w, s3_h,
        "Stage 3:  Policy Optimization  (PPO / DPO)",
        [
            "Generate response  -->  reward model scores it",
            "PPO: optimize SFT model to maximize expected reward",
            "DPO: directly optimize on preference pairs (no separate RM)",
            "KL penalty:  keeps aligned model close to SFT baseline",
            "Prevents reward hacking (exploiting RM without real quality gain)",
        ],
        GREEN,
    )

    # --- Side annotations ---
    # Left: data flowing in
    annot_x = center_x - 0.01
    ax.annotate(
        "Curated\ndemonstrations",
        xy=(center_x, s1_y + s1_h / 2), xytext=(annot_x - 0.10, s1_y + s1_h / 2),
        fontsize=9, color=BLUE, ha="center", va="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5),
    )
    ax.annotate(
        "Human\npreference\nrankings",
        xy=(center_x, s2_y + s2_h / 2), xytext=(annot_x - 0.10, s2_y + s2_h / 2),
        fontsize=9, color=ORANGE, ha="center", va="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=ORANGE, lw=1.5),
    )
    ax.annotate(
        "Reward\nsignal\n+ KL constraint",
        xy=(center_x, s3_y + s3_h / 2), xytext=(annot_x - 0.10, s3_y + s3_h / 2),
        fontsize=9, color=GREEN, ha="center", va="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5),
    )

    # Right: outputs
    right_x = center_x + box_w + 0.01
    ax.annotate(
        "SFT\nModel",
        xy=(right_x, s1_y + s1_h / 2),
        xytext=(right_x + 0.10, s1_y + s1_h / 2),
        fontsize=9, color=BLUE, ha="center", va="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="<-", color=BLUE, lw=1.5),
    )
    ax.annotate(
        "Reward\nModel R",
        xy=(right_x, s2_y + s2_h / 2),
        xytext=(right_x + 0.10, s2_y + s2_h / 2),
        fontsize=9, color=ORANGE, ha="center", va="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="<-", color=ORANGE, lw=1.5),
    )
    ax.annotate(
        "Aligned\nModel",
        xy=(right_x, s3_y + s3_h / 2),
        xytext=(right_x + 0.10, s3_y + s3_h / 2),
        fontsize=9, color=GREEN, ha="center", va="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="<-", color=GREEN, lw=1.5),
    )

    # Bottom note
    ax.text(
        0.5, 0.04,
        "The reward model is a learned utility function: it maps (prompt, response)\n"
        "to a scalar score encoding human preferences for helpfulness, safety, and honesty.",
        fontsize=10, ha="center", va="top", color="#555555", style="italic",
    )

    save_fig(fig, "13_rlhf_pipeline")


# =========================================================================
# Figure 2 -- Preference Pair Visualization Cards
# =========================================================================

PREFERENCE_PAIRS = [
    {
        "prompt": "What is 15% of 80?",
        "chosen": "15% of 80 = 0.15 \u00d7 80 = 12",
        "rejected": "The answer is approximately 15.",
        "tag": "Correctness",
    },
    {
        "prompt": "Is it safe to mix bleach and ammonia?",
        "chosen": (
            "No. Mixing bleach and ammonia produces toxic\n"
            "chloramine gas. Never combine these chemicals."
        ),
        "rejected": (
            "Sure, you can mix them for a stronger\n"
            "cleaning solution."
        ),
        "tag": "Safety",
    },
    {
        "prompt": "Summarize quantum computing in one sentence.",
        "chosen": (
            "Quantum computing uses qubits that can exist in\n"
            "superposition to perform certain calculations\n"
            "exponentially faster than classical computers."
        ),
        "rejected": (
            "Quantum computing is when computers use\n"
            "quantum physics to be really fast at everything."
        ),
        "tag": "Precision",
    },
]


def _draw_response_card(ax, x, y, width, height, text, border_color,
                        label, label_color):
    """Draw a single response card with a colored left border."""
    # Card background
    card = FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=0.01",
        facecolor="#FAFAFA", edgecolor=border_color, linewidth=2.5,
        transform=ax.transData, zorder=2,
    )
    ax.add_patch(card)

    # Label badge (Chosen / Rejected)
    badge_w = 0.105
    badge_h = 0.025
    badge_x = x + width / 2 - badge_w / 2
    badge_y = y + height - badge_h - 0.008
    badge = FancyBboxPatch(
        (badge_x, badge_y), badge_w, badge_h,
        boxstyle="round,pad=0.005",
        facecolor=label_color, edgecolor="none",
        transform=ax.transData, zorder=3,
    )
    ax.add_patch(badge)
    ax.text(
        badge_x + badge_w / 2, badge_y + badge_h / 2,
        label, fontsize=9, fontweight="bold", color="white",
        ha="center", va="center", zorder=4,
    )

    # Response text
    ax.text(
        x + width / 2, y + height / 2 - 0.015,
        text, fontsize=9.5, color="#333333",
        ha="center", va="center", zorder=4,
        fontfamily="sans-serif", linespacing=1.4,
    )


def plot_preference_pairs():
    """Show 3 preference-pair cards as visual examples."""
    fig, ax = plt.subplots(figsize=(14, 12))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title
    ax.text(
        0.5, 0.97,
        "Preference Pairs: The Training Signal for RLHF",
        fontsize=17, fontweight="bold", ha="center", va="top",
        color="#222222",
    )
    ax.text(
        0.5, 0.935,
        "Humans compare two responses to the same prompt and select the better one.\n"
        "The reward model learns to predict these preferences.",
        fontsize=11, ha="center", va="top", color="#666666",
        linespacing=1.5,
    )

    # Card layout
    n_pairs = len(PREFERENCE_PAIRS)
    card_h = 0.22
    gap = 0.04
    total_h = n_pairs * card_h + (n_pairs - 1) * gap
    start_y = 0.90 - (0.90 - total_h) / 2 - total_h  # center vertically

    # Adjust starting position
    start_y = 0.09

    for i, pair in enumerate(PREFERENCE_PAIRS):
        row_y = start_y + (n_pairs - 1 - i) * (card_h + gap)

        # Outer frame for the whole pair
        frame = FancyBboxPatch(
            (0.04, row_y - 0.01), 0.92, card_h + 0.02,
            boxstyle="round,pad=0.01",
            facecolor="white", edgecolor="#DDDDDD", linewidth=1.0,
            transform=ax.transData, zorder=1,
        )
        ax.add_patch(frame)

        # Tag badge in upper-right
        ax.text(
            0.93, row_y + card_h + 0.002,
            pair["tag"], fontsize=8.5, fontweight="bold",
            color=PURPLE, ha="right", va="top", zorder=4,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#F0EEF8",
                      edgecolor=PURPLE, linewidth=0.8),
        )

        # Prompt header
        prompt_y = row_y + card_h - 0.015
        ax.text(
            0.08, prompt_y,
            "Prompt:", fontsize=10, fontweight="bold",
            color="#444444", ha="left", va="top", zorder=4,
        )
        ax.text(
            0.17, prompt_y,
            f'"{pair["prompt"]}"', fontsize=11, fontweight="bold",
            color="#222222", ha="left", va="top", zorder=4,
            style="italic",
        )

        # Response cards side by side
        resp_y = row_y + 0.01
        resp_h = card_h - 0.065
        resp_w = 0.40

        # Chosen (green)
        _draw_response_card(
            ax, 0.08, resp_y, resp_w, resp_h,
            pair["chosen"], GREEN, "Chosen", GREEN,
        )

        # Rejected (red)
        _draw_response_card(
            ax, 0.52, resp_y, resp_w, resp_h,
            pair["rejected"], RED, "Rejected", RED,
        )

        # VS divider
        ax.text(
            0.50, resp_y + resp_h / 2,
            "vs", fontsize=11, fontweight="bold", color="#999999",
            ha="center", va="center", zorder=4,
        )

    # Bottom note
    ax.text(
        0.5, 0.035,
        "The chosen response is not always longer or more complex -- it is the one\n"
        "that is more accurate, safer, or more precisely stated. The reward model\n"
        "learns this nuanced preference signal from thousands of such comparisons.",
        fontsize=10, ha="center", va="top", color="#555555", style="italic",
        linespacing=1.4,
    )

    save_fig(fig, "13_rlhf_preference_pairs")


# =========================================================================
# Figure 3 -- Reward Distribution Shift (Synthetic)
# =========================================================================

def plot_reward_shift():
    """Two overlaid histograms: reward scores before and after alignment."""
    rng = np.random.default_rng(42)

    # Synthetic reward scores
    n_samples = 5000
    before = rng.normal(loc=0.0, scale=1.5, size=n_samples)    # wide, centered at 0
    after = rng.normal(loc=2.5, scale=0.8, size=n_samples)      # shifted right, tighter

    fig, ax = plt.subplots(figsize=(11, 6.5))

    bins = np.linspace(-5, 7, 60)

    ax.hist(
        before, bins=bins, alpha=0.55, color=RED, edgecolor="white",
        linewidth=0.5, label="Before alignment (SFT only)", density=True,
    )
    ax.hist(
        after, bins=bins, alpha=0.55, color=GREEN, edgecolor="white",
        linewidth=0.5, label="After alignment (RLHF)", density=True,
    )

    # Vertical lines at means
    before_mean = np.mean(before)
    after_mean = np.mean(after)
    ax.axvline(before_mean, color=RED, linestyle="--", linewidth=2, alpha=0.8)
    ax.axvline(after_mean, color=GREEN, linestyle="--", linewidth=2, alpha=0.8)

    # Annotate means
    y_top = ax.get_ylim()[1]
    ax.annotate(
        f"mean = {before_mean:.2f}",
        xy=(before_mean, y_top * 0.85),
        xytext=(before_mean - 1.5, y_top * 0.95),
        fontsize=11, fontweight="bold", color=RED,
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.5),
        ha="center",
    )
    ax.annotate(
        f"mean = {after_mean:.2f}",
        xy=(after_mean, y_top * 0.85),
        xytext=(after_mean + 1.5, y_top * 0.95),
        fontsize=11, fontweight="bold", color=GREEN,
        arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.5),
        ha="center",
    )

    # Labels and title
    ax.set_xlabel("Reward Model Score  R(prompt, response)", fontsize=13)
    ax.set_ylabel("Density", fontsize=13)
    ax.set_title(
        "Effect of RLHF on Response Quality Distribution",
        fontsize=16, fontweight="bold", pad=15,
    )

    ax.legend(fontsize=12, frameon=True, fancybox=True, shadow=True,
              loc="upper left")

    # Annotation: what this means
    ax.text(
        0.97, 0.60,
        "RLHF shifts the distribution:\n"
        "  Higher mean  (better responses)\n"
        "  Lower variance  (more consistent)",
        fontsize=10, color="#444444",
        ha="right", va="top",
        transform=ax.transAxes,
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#F5F5F5",
                  edgecolor="#CCCCCC", linewidth=0.8),
        linespacing=1.5,
    )

    # Bottom explanatory note
    fig.text(
        0.5, -0.03,
        "Synthetic illustration. Before alignment, the SFT model produces responses with widely\n"
        "varying quality. After RLHF, the reward distribution shifts right (higher quality) and\n"
        "narrows (more consistent) -- analogous to a posterior concentrating around high-utility regions.",
        ha="center", fontsize=10, color="#555555", style="italic",
        linespacing=1.3,
    )

    fig.tight_layout()
    save_fig(fig, "13_rlhf_reward_shift")


# =========================================================================
# Main
# =========================================================================

if __name__ == "__main__":
    print("=== 13: RLHF & Alignment Visualizations ===\n")

    print("Figure 1: RLHF pipeline flowchart ...")
    plot_rlhf_pipeline()

    print("Figure 2: Preference pair cards ...")
    plot_preference_pairs()

    print("Figure 3: Reward distribution shift ...")
    plot_reward_shift()

    print("\nDone -- all three figures saved to workspace/output/")
