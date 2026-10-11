"""Shared matplotlib styling and helpers for all visualization scripts."""

import matplotlib.pyplot as plt
import matplotlib
import os

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

COLOR_PALETTE = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]

def set_style():
    """Apply consistent style across all figures."""
    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 12,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.2,
    })

def save_fig(fig, name):
    """Save figure to output directory as PNG."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"{name}.png")
    fig.savefig(path)
    plt.close(fig)
    print(f"Saved: {path}")
    return path
