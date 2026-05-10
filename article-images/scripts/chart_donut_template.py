"""TEMPLATE — copy this into the article working directory and customize.

Donut chart with center text. Use sparingly: donuts are weaker than bar charts
for comparison, but they work well for showing one or two big slices in a
total (e.g. "what percentage of usage is X").

USAGE PATTERN:
    1. Copy this file to the article working directory
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
OUTPUT_BASENAME = "chart-donut-example"
ASPECT = "square"     # 'square' (8x8) is usual for donuts; 'landscape' adds room for legend right

# ============================================================
# DATA — keep to 4-6 segments max for readability
# ============================================================
SEGMENTS = [
    ("Largest segment", 45),
    ("Second", 25),
    ("Third", 18),
    ("Other", 12),
]
CHART_TITLE = "Composition — replace with your real title"

# Big text that goes in the donut hole (e.g. the headline percentage)
CENTER_BIG = "45%"
CENTER_SMALL = "in largest segment"


# ============================================================
# RENDER
# ============================================================
def render():
    brand = load_brand(BRAND)
    apply_matplotlib_defaults(brand)

    figsize = (8, 8) if ASPECT == "square" else (10, 6.5)
    fig, ax = plt.subplots(figsize=figsize)

    labels = [s[0] for s in SEGMENTS]
    values = [s[1] for s in SEGMENTS]
    colors = palette(brand, n=len(SEGMENTS))
    dark = color(brand, "dark")

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        startangle=90,
        counterclock=False,
        autopct="%1.0f%%",
        pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2),
        textprops=dict(fontsize=11, color=dark),
    )
    for at in autotexts:
        at.set_color("white")
        at.set_weight("bold")
        at.set_fontsize(10)

    # Center text
    if CENTER_BIG:
        ax.text(0, 0.07, CENTER_BIG, ha="center", va="center",
                fontsize=36, color=dark, weight="bold")
    if CENTER_SMALL:
        ax.text(0, -0.12, CENTER_SMALL, ha="center", va="center",
                fontsize=11, color=dark, alpha=0.7)

    ax.set_title(CHART_TITLE, fontsize=13, color=dark,
                 pad=18, loc="left", weight="bold")

    add_source_footer(fig, SOURCE, brand, y=0.02)
    add_watermark(fig, brand, y=0.02)
    plt.tight_layout(rect=(0, 0.04, 1, 1))

    plt.savefig(f"{OUTPUT_BASENAME}.svg", format="svg", bbox_inches="tight")
    plt.savefig(f"{OUTPUT_BASENAME}.png", format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"Saved {OUTPUT_BASENAME}.svg + .png")


if __name__ == "__main__":
    render()
