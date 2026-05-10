"""Render a single preview image showing what each chart type looks like in a given brand.

Useful as a sanity check after running setup_brand.py, or before sharing a brand
profile. Outputs `brands/<slug>-preview.png` with a 2x3 grid of mini-charts.

Usage:
    python scripts/preview_brand.py --brand azvai
    python scripts/preview_brand.py --brand azvai --output my-preview.png
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

SKILL_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_SCRIPTS))
from branding import load_brand, apply_matplotlib_defaults, color, palette  # noqa: E402

BRANDS_DIR = Path(__file__).resolve().parent.parent / "brands"


def render_preview(brand_slug: str, output_path: Path) -> None:
    brand = load_brand(brand_slug)
    apply_matplotlib_defaults(brand)

    dark = color(brand, "dark")
    accent = color(brand, "accent")
    benchmark = color(brand, "benchmark", "#888")
    pal = palette(brand, n=4)

    fig = plt.figure(figsize=(14, 9))
    gs = fig.add_gridspec(2, 3, hspace=0.5, wspace=0.35)

    # --- Bar chart ---
    ax = fig.add_subplot(gs[0, 0])
    cats = ["A", "B", "C", "D", "E"]
    vals = [24, 18, 14, 10, 6]
    ax.barh(cats[::-1], vals[::-1], color=pal[0], edgecolor=dark, linewidth=0.5)
    ax.set_title("Bar chart", fontsize=11, weight="bold", color=dark, loc="left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --- Stacked bar ---
    ax = fig.add_subplot(gs[0, 1])
    rows = ["G1", "G2", "G3"]
    segs = [[40, 35, 50], [30, 30, 25], [20, 25, 15], [10, 10, 10]]
    left = [0] * len(rows)
    for i, seg_vals in enumerate(segs):
        ax.barh(rows[::-1], seg_vals[::-1], left=left,
                color=pal[i], edgecolor=dark, linewidth=0.4)
        left = [l + v for l, v in zip(left, seg_vals[::-1])]
    ax.set_title("Stacked bar", fontsize=11, weight="bold", color=dark, loc="left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --- Time series ---
    ax = fig.add_subplot(gs[0, 2])
    x = ["2022", "2023", "2024", "2025", "2026"]
    s1 = [4.0, 6.5, 9.0, 11.5, 13.0]
    s2 = [2.0, 2.5, 3.0, 3.4, 4.0]
    ax.plot(x, s1, marker="o", color=pal[0], linewidth=2.2)
    ax.plot(x, s2, marker="o", color=pal[1], linewidth=2.2)
    ax.axhline(8.0, color=benchmark, linestyle="--", linewidth=1, alpha=0.7)
    ax.set_title("Time series", fontsize=11, weight="bold", color=dark, loc="left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --- Grouped bars ---
    ax = fig.add_subplot(gs[1, 0])
    cats = ["A", "B", "C"]
    g1 = [20, 35, 30]
    g2 = [25, 32, 38]
    xpos = np.arange(len(cats))
    bw = 0.35
    ax.bar(xpos - bw/2, g1, bw, color=pal[0], edgecolor=dark, linewidth=0.4)
    ax.bar(xpos + bw/2, g2, bw, color=pal[1], edgecolor=dark, linewidth=0.4)
    ax.set_xticks(xpos)
    ax.set_xticklabels(cats)
    ax.set_title("Grouped bars", fontsize=11, weight="bold", color=dark, loc="left")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # --- Donut ---
    ax = fig.add_subplot(gs[1, 1])
    ax.pie([45, 25, 18, 12], colors=pal[:4], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.42, edgecolor="white", linewidth=2))
    ax.text(0, 0, "45%", ha="center", va="center",
            fontsize=22, weight="bold", color=dark)
    ax.set_title("Donut", fontsize=11, weight="bold", color=dark, loc="left")

    # --- Brand color swatch ---
    ax = fig.add_subplot(gs[1, 2])
    blocks = [
        ("accent", accent),
        ("dark", dark),
        ("light", color(brand, "light")),
        ("pop", color(brand, "pop")),
        ("benchmark", benchmark),
    ]
    for i, (name, c) in enumerate(blocks):
        ax.add_patch(mpatches.Rectangle((i, 0), 1, 1, facecolor=c, edgecolor="#333"))
        ax.text(i + 0.5, -0.25, name, ha="center", va="center",
                fontsize=9, color=dark)
    ax.set_xlim(0, len(blocks))
    ax.set_ylim(-0.5, 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Brand colors", fontsize=11, weight="bold", color=dark, loc="left")

    # Top header
    fig.suptitle(
        f"Brand preview: {brand.get('display_name', brand.get('name'))}",
        fontsize=16, weight="bold", color=dark, x=0.07, ha="left", y=0.97,
    )
    fig.text(
        0.07, 0.93,
        f"slug: {brand.get('name')}   |   font: {brand.get('fonts', {}).get('stack', ['?'])[0]}",
        fontsize=10, color=dark, alpha=0.6, ha="left",
    )

    plt.savefig(output_path, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close()


def main() -> int:
    p = argparse.ArgumentParser(description="Render a multi-chart preview of a brand profile")
    p.add_argument("--brand", "-b", required=True, help="Brand slug")
    p.add_argument("--output", "-o", help="Output PNG path (defaults to brands/<slug>-preview.png)")
    args = p.parse_args()

    if args.output:
        out = Path(args.output)
    else:
        out = BRANDS_DIR / f"{args.brand}-preview.png"

    out.parent.mkdir(parents=True, exist_ok=True)
    render_preview(args.brand, out)
    print(f"Saved preview: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
