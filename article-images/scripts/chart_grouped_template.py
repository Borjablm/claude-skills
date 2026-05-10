"""TEMPLATE — copy this into the article working directory and customize.

Grouped vertical bar chart for direct comparison of N items across M categories.
Use when you want to compare multiple groups side-by-side per category
(e.g. "with skills vs without skills" across several task types).

USAGE PATTERN:
    1. Copy this file to the article working directory
    2. Edit the DATA, LAYOUT, and OUTPUT sections
    3. Run: python chart_<topic>.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

SKILL_SCRIPTS = Path(r"<your-project-root>/.claude/skills/article-images/scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))
from branding import load_brand, apply_matplotlib_defaults, add_source_footer, add_watermark, color, palette  # noqa: E402

# ============================================================
# CONFIG — edit these
# ============================================================
BRAND = "azvai"
SOURCE = "Source name and date"
OUTPUT_BASENAME = "chart-grouped-example"
ASPECT = "landscape"

# ============================================================
# DATA
# ============================================================
CATEGORIES = ["Category A", "Category B", "Category C", "Category D"]
GROUPS = [
    ("Group 1", [20, 35, 30, 25]),
    ("Group 2", [25, 32, 38, 22]),
    ("Group 3", [18, 28, 25, 30]),
]
CHART_TITLE = "Grouped comparison — replace with your real title"
Y_LABEL = "Value (units)"
SHOW_VALUE_LABELS = True


# ============================================================
# RENDER
# ============================================================
def render():
    brand = load_brand(BRAND)
    apply_matplotlib_defaults(brand)

    figsize = (10.8, 10.8) if ASPECT == "square" else (10, 6.5)
    fig, ax = plt.subplots(figsize=figsize)

    n_groups = len(GROUPS)
    n_categories = len(CATEGORIES)
    x = np.arange(n_categories)
    bar_width = 0.8 / n_groups

    colors = palette(brand, n=n_groups)
    dark = color(brand, "dark")

    for i, (group_name, group_values) in enumerate(GROUPS):
        offset = (i - (n_groups - 1) / 2) * bar_width
        bars = ax.bar(x + offset, group_values, bar_width,
                      color=colors[i], label=group_name,
                      edgecolor=dark, linewidth=0.5)
        if SHOW_VALUE_LABELS:
            for b, v in zip(bars, group_values):
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5,
                        f"{v}", ha="center", fontsize=8, color=dark)

    ax.set_xticks(x)
    ax.set_xticklabels(CATEGORIES)
    ax.set_ylabel(Y_LABEL, fontsize=11)
    ax.set_title(CHART_TITLE, fontsize=13, color=dark,
                 pad=18, loc="left", weight="bold")
    ax.grid(axis="y", alpha=0.25, linestyle=":")
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=False, fontsize=10)

    add_source_footer(fig, SOURCE, brand)
    add_watermark(fig, brand)
    plt.tight_layout(rect=(0, 0.04, 1, 1))

    plt.savefig(f"{OUTPUT_BASENAME}.svg", format="svg", bbox_inches="tight")
    plt.savefig(f"{OUTPUT_BASENAME}.png", format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {OUTPUT_BASENAME}.svg + .png")


if __name__ == "__main__":
    render()
