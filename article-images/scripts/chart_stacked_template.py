"""TEMPLATE — copy this into the article working directory and customize.

Stacked horizontal bar chart. Each row sums across multiple categories.
Use when you want to show composition / breakdown across multiple groups.

USAGE PATTERN:
    1. Copy this file to the article working directory as e.g. `chart_<topic>.py`
    2. Edit the DATA, LAYOUT, and OUTPUT sections
    3. Run: python chart_<topic>.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt

SKILL_SCRIPTS = Path(r"<your-project-root>/.claude/skills/article-images/scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))
from branding import load_brand, apply_matplotlib_defaults, add_source_footer, add_watermark, color, palette  # noqa: E402

# ============================================================
# CONFIG — edit these
# ============================================================
BRAND = "azvai"
SOURCE = "Source name and date"
OUTPUT_BASENAME = "chart-stacked-example"
ASPECT = "landscape"     # 'landscape' (10x6.5) or 'square' (10.8x10.8)

# ============================================================
# DATA — each row's segments must sum sensibly (typically to 100%)
# ============================================================
SEGMENT_LABELS = ["Segment A", "Segment B", "Segment C", "Other"]
ROWS = [
    ("Group 1", [40, 30, 20, 10]),
    ("Group 2", [25, 35, 30, 10]),
    ("Group 3", [50, 20, 15, 15]),
    ("Group 4", [10, 10, 50, 30]),
]
CHART_TITLE = "Stacked breakdown — replace with your real title"
X_LABEL = "Share (%)"


# ============================================================
# RENDER
# ============================================================
def render():
    brand = load_brand(BRAND)
    apply_matplotlib_defaults(brand)

    figsize = (10.8, 10.8) if ASPECT == "square" else (10, 6.5)
    fig, ax = plt.subplots(figsize=figsize)

    labels = [r[0] for r in ROWS][::-1]
    values_by_segment = list(zip(*[r[1] for r in ROWS][::-1]))
    colors = palette(brand, n=len(SEGMENT_LABELS))

    left = [0] * len(labels)
    for i, (segment_label, segment_values) in enumerate(zip(SEGMENT_LABELS, values_by_segment)):
        ax.barh(labels, segment_values, left=left, color=colors[i],
                label=segment_label, edgecolor=color(brand, "dark"), linewidth=0.4)
        left = [l + v for l, v in zip(left, segment_values)]

    ax.set_xlabel(X_LABEL, fontsize=11)
    ax.set_title(CHART_TITLE, fontsize=13, color=color(brand, "dark"),
                 pad=18, loc="left", weight="bold")
    ax.set_xlim(0, max(105, max(left) * 1.05))
    ax.grid(axis="x", alpha=0.25, linestyle=":")
    ax.set_axisbelow(True)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.18),
              ncol=len(SEGMENT_LABELS), frameon=False, fontsize=9)

    add_source_footer(fig, SOURCE, brand, y=0.01)
    add_watermark(fig, brand, y=0.01)
    plt.tight_layout(rect=(0, 0.10, 1, 1))

    plt.savefig(f"{OUTPUT_BASENAME}.svg", format="svg", bbox_inches="tight")
    plt.savefig(f"{OUTPUT_BASENAME}.png", format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {OUTPUT_BASENAME}.svg + .png")


if __name__ == "__main__":
    render()
