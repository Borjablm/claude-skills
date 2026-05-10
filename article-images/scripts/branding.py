"""Shared brand profile loader and matplotlib defaults for article-images.

Usage:
    from branding import load_brand, apply_matplotlib_defaults, add_source_footer

    brand = load_brand("azvai")
    apply_matplotlib_defaults(brand)
    fig, ax = plt.subplots(...)
    add_source_footer(fig, "Anthropic Economic Index (2026)", brand)
"""
import json
from pathlib import Path

import matplotlib.pyplot as plt

BRANDS_DIR = Path(__file__).resolve().parent.parent / "brands"


def load_brand(name: str | None = None) -> dict:
    """Load a brand profile by name. Falls back to _default if missing."""
    if not name:
        name = "_default"
    path = BRANDS_DIR / f"{name}.json"
    if not path.exists():
        print(f"[branding] '{name}' not found, falling back to _default")
        path = BRANDS_DIR / "_default.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_matplotlib_defaults(brand: dict) -> None:
    """Set matplotlib rcParams from a brand profile."""
    fonts = brand.get("fonts", {})
    colors = brand.get("colors", {})
    dark = colors.get("dark", "#1F2937")

    plt.rcParams.update({
        "font.family": fonts.get("family", "sans-serif"),
        "font.sans-serif": fonts.get("stack", ["Helvetica", "Arial", "sans-serif"]),
        "font.size": 11,
        "axes.edgecolor": dark,
        "axes.labelcolor": dark,
        "xtick.color": dark,
        "ytick.color": dark,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "svg.fonttype": "none",
    })


def add_source_footer(fig, source: str, brand: dict, x: float = 0.02, y: float = 0.02) -> None:
    """Add a source attribution line in brand style."""
    attribution = brand.get("attribution", {})
    template = attribution.get("template", "Source: {source}")
    text = template.format(source=source)
    fig.text(
        x, y, text,
        fontsize=attribution.get("font_size", 10),
        color=brand["colors"].get("dark", "#1F2937"),
        alpha=attribution.get("color_alpha", 0.6),
    )


def add_watermark(fig, brand: dict, x: float = 0.98, y: float = 0.02) -> None:
    """Add a brand watermark (e.g. 'azvai.com') in the bottom-right by default."""
    wm = brand.get("watermark", {})
    if not wm.get("enabled"):
        return
    text = wm.get("text")
    if not text:
        return
    fig.text(
        x, y, text,
        fontsize=10,
        color=brand["colors"].get("dark", "#1F2937"),
        alpha=wm.get("alpha", 0.6),
        ha="right",
        weight="bold",
    )


def color(brand: dict, key: str, default: str = "#000000") -> str:
    """Convenience: brand color lookup with fallback."""
    return brand.get("colors", {}).get(key, default)


def palette(brand: dict, n: int | None = None) -> list:
    """Get the data palette, optionally first n colors."""
    p = brand.get("colors", {}).get("data_palette", [])
    if n is None:
        return p
    if n <= len(p):
        return p[:n]
    # Repeat if asked for more than available
    out = list(p)
    while len(out) < n:
        out.extend(p)
    return out[:n]
