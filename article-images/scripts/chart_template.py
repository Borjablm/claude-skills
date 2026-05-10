"""TEMPLATE — copy this into the article working directory and customize.

Charts are bespoke per article. Don't try to make this generic. Copy this
template, edit the data + layout for your chart, run it.

The shared `branding` module gives you brand colors, fonts, source attribution,
and watermark — so you only have to write the chart logic.

USAGE PATTERN:
    1. Copy this file to the article working directory as e.g. `chart_<topic>.py`
    2. Edit the DATA, LAYOUT, and OUTPUT sections
    3. Run: python chart_<topic>.py

To find brand colors / palette / etc., read brands/<brand>.json or use:
    color(brand, 'accent'), color(brand, 'dark'), palette(brand, n=4)

For LinkedIn-square versions, set ASPECT = 'square' (10.8 x 10.8) and add a
header block (see references/mode-linkedin-square.md).
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Make `branding` importable when this file is copied elsewhere
SKILL_SCRIPTS = Path(r"<your-project-root>/.claude/skills/article-images/scripts")
sys.path.insert(0, str(SKILL_SCRIPTS))
from branding import load_brand, apply_matplotlib_defaults, add_source_footer, color, palette  # noqa: E402

# ============================================================
# CONFIG — edit these
# ============================================================
BRAND = "azvai"          # which brand profile to use
SOURCE = "Anthropic Economic Index (2026)"
OUTPUT_BASENAME = "chart-example"
ASPECT = "landscape"     # 'landscape' (10x6.5) or 'square' (10.8x10.8)

# ============================================================
# DATA — edit these
# ============================================================
DATA = [
    ("Category A", 24.4),
    ("Category B", 18.5),
    ("Category C", 14.4),
    ("Category D", 9.6),
    ("Category E", 5.5),
]
CHART_TITLE = "Example chart title — replace with your real title"
X_LABEL = "Your value label (%)"
BENCHMARK_VALUE = 12.0    # set None to disable
BENCHMARK_LABEL = "Reference: 12.0"

# ============================================================
# RENDER
# ============================================================
def render():
    brand = load_brand(BRAND)
    apply_matplotlib_defaults(brand)

    if ASPECT == "square":
        figsize = (10.8, 10.8)
    else:
        figsize = (10, 6.5)

    fig, ax = plt.subplots(figsize=figsize)

    labels = [d[0] for d in DATA][::-1]
    values = [d[1] for d in DATA][::-1]
    colors = palette(brand, n=len(values))

    bars = ax.barh(labels, values, color=colors,
                   edgecolor=color(brand, "dark"), linewidth=0.5)

    # Value labels on bars
    for bar, val in zip(bars, values):
        ax.text(val + max(values) * 0.015,
                bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=10,
                color=color(brand, "dark"))

    # Benchmark line
    if BENCHMARK_VALUE is not None:
        ax.axvline(BENCHMARK_VALUE, color=color(brand, "benchmark", "#888"),
                   linestyle="--", linewidth=1.2, alpha=0.8)
        ax.text(BENCHMARK_VALUE * 1.02, -0.8, BENCHMARK_LABEL,
                color=color(brand, "benchmark", "#888"), fontsize=9, style="italic")

    ax.set_xlabel(X_LABEL, fontsize=11)
    ax.set_title(CHART_TITLE, fontsize=13, color=color(brand, "dark"),
                 pad=18, loc="left", weight="bold")
    ax.set_xlim(0, max(values) * 1.15)
    ax.grid(axis="x", alpha=0.25, linestyle=":")
    ax.set_axisbelow(True)

    # Source footer + watermark
    add_source_footer(fig, SOURCE, brand)

    plt.tight_layout(rect=(0, 0.04, 1, 1))   # leave room for footer

    # Output: SVG (inline) + PNG (featured/social)
    plt.savefig(f"{OUTPUT_BASENAME}.svg", format="svg", bbox_inches="tight")
    plt.savefig(f"{OUTPUT_BASENAME}.png", format="png", dpi=150, bbox_inches="tight",
                facecolor="white")
    plt.close()
    print(f"Saved {OUTPUT_BASENAME}.svg")
    print(f"Saved {OUTPUT_BASENAME}.png")


if __name__ == "__main__":
    render()
