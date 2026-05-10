"""TEMPLATE — copy this into the article working directory and customize.

Line / time series chart with optional benchmark and trend annotation.
Use when you want to show change over time across one or more series.

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
OUTPUT_BASENAME = "chart-timeseries-example"
ASPECT = "landscape"

# ============================================================
# DATA — list of (series_name, [(x_label, y_value), ...])
# ============================================================
X_AXIS_LABELS = ["2022", "2023", "2024", "2025", "2026"]
SERIES = [
    ("Series A", [4.0, 6.5, 9.0, 11.5, 13.0]),
    ("Series B", [2.0, 2.5, 3.0, 3.4, 4.0]),
]
CHART_TITLE = "Trend over time — replace with your real title"
Y_LABEL = "Value"

# Optional: horizontal benchmark line (set None to disable)
BENCHMARK_VALUE = 8.0
BENCHMARK_LABEL = "Reference: 8.0"

# Optional: annotate the last point of each series
ANNOTATE_END_POINTS = True


# ============================================================
# RENDER
# ============================================================
def render():
    brand = load_brand(BRAND)
    apply_matplotlib_defaults(brand)

    figsize = (10.8, 10.8) if ASPECT == "square" else (10, 6.5)
    fig, ax = plt.subplots(figsize=figsize)

    colors = palette(brand, n=len(SERIES))

    for (name, values), c in zip(SERIES, colors):
        ax.plot(X_AXIS_LABELS, values, marker="o", linewidth=2.5,
                color=c, label=name, markersize=7,
                markeredgecolor=color(brand, "dark"), markeredgewidth=0.5)

        if ANNOTATE_END_POINTS:
            last_x = X_AXIS_LABELS[-1]
            last_y = values[-1]
            ax.annotate(f"{last_y:.1f}", xy=(last_x, last_y),
                        xytext=(8, 0), textcoords="offset points",
                        fontsize=10, color=color(brand, "dark"), weight="bold",
                        va="center")

    if BENCHMARK_VALUE is not None:
        ax.axhline(BENCHMARK_VALUE, color=color(brand, "benchmark", "#888"),
                   linestyle="--", linewidth=1.2, alpha=0.8)
        ax.text(0.99, BENCHMARK_VALUE, f"  {BENCHMARK_LABEL}",
                transform=ax.get_yaxis_transform(),
                color=color(brand, "benchmark", "#888"),
                fontsize=9, style="italic", va="center")

    ax.set_ylabel(Y_LABEL, fontsize=11)
    ax.set_title(CHART_TITLE, fontsize=13, color=color(brand, "dark"),
                 pad=18, loc="left", weight="bold")
    ax.grid(axis="y", alpha=0.25, linestyle=":")
    ax.set_axisbelow(True)
    if len(SERIES) > 1:
        ax.legend(loc="upper left", frameon=False, fontsize=10)

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