"""Generate a branded featured/title-card image.

Usage:
    python featured.py --title "AI Usage in Sustainability Consulting" \
                       --subtitle "Anthropic Economic Index Analysis" \
                       --brand azvai \
                       --aspect og \
                       --out ./featured-image
                       [--bg gradient|solid]

Aspect ratios:
    og        1200x630  (default — Open Graph / blog featured)
    square    1080x1080 (LinkedIn, Instagram)
    landscape 1200x675  (Twitter/X)

Outputs PNG and JPG side-by-side.
"""
import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from branding import load_brand, apply_matplotlib_defaults  # noqa: E402

ASPECTS = {
    "og": (12, 6.3, 100),       # 1200x630
    "square": (10.8, 10.8, 100),  # 1080x1080
    "landscape": (12, 6.75, 100),  # 1200x675
}


def _resolve_color(brand: dict, key: str) -> str:
    """Map 'dark'/'light'/'accent' or hex strings to actual hex."""
    if key.startswith("#"):
        return key
    return brand["colors"].get(key, "#FFFFFF")


def _draw_gradient_bg(ax, brand: dict) -> None:
    """Soft gradient from light → accent diagonal."""
    light = _resolve_color(brand, "light")
    accent = _resolve_color(brand, "accent")
    cmap = LinearSegmentedColormap.from_list("bg", [light, accent], N=256)
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    gradient = np.vstack((gradient, gradient))
    ax.imshow(gradient, aspect="auto", cmap=cmap, extent=[0, 1, 0, 1], alpha=0.5, zorder=0)


def render(title: str, subtitle: str | None, brand: dict, aspect: str, out_path: Path,
           bg: str = "solid") -> None:
    apply_matplotlib_defaults(brand)
    w, h, dpi = ASPECTS[aspect]

    tc = brand.get("title_card", {})
    bg_key = tc.get("background", "white")
    bg_color = "#FFFFFF" if bg_key == "white" else _resolve_color(brand, bg_key)
    title_color = _resolve_color(brand, tc.get("title_color", "dark"))
    subtitle_color = _resolve_color(brand, tc.get("subtitle_color", "dark"))
    subtitle_alpha = tc.get("subtitle_alpha", 0.85)

    fig = plt.figure(figsize=(w, h), dpi=dpi)
    fig.patch.set_facecolor(bg_color)

    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)

    if bg == "gradient":
        _draw_gradient_bg(ax, brand)

    # Accent block on the side
    accent_block = tc.get("accent_block", {})
    if accent_block.get("enabled"):
        side = accent_block.get("side", "left")
        width = accent_block.get("width_pct", 0.06)
        accent_color = _resolve_color(brand, "accent")
        if side == "left":
            ax.add_patch(mpatches.Rectangle((0, 0), width, 1, color=accent_color, linewidth=0, zorder=1))
            text_x = width + 0.06
        else:
            ax.add_patch(mpatches.Rectangle((1 - width, 0), width, 1, color=accent_color, linewidth=0, zorder=1))
            text_x = 0.06
    else:
        text_x = 0.08

    # Layout differs by aspect ratio: square needs tighter / centered, og is left-aligned
    if aspect == "square":
        title_size = 44
        subtitle_size = 22
        site_size = 14
        title_y_top = 0.65
        subtitle_y = 0.32
        site_y = 0.12
    else:
        title_size = 50
        subtitle_size = 22
        site_size = 14
        title_y_top = 0.62
        subtitle_y = 0.32
        site_y = 0.13

    # Title — split intelligently if long
    title_lines = _wrap_title(title, max_chars=28 if aspect != "og" else 32)
    line_height = 0.14 if aspect == "square" else 0.13
    for i, line in enumerate(title_lines):
        ax.text(text_x, title_y_top - i * line_height, line,
                fontsize=title_size, color=title_color, weight="bold", va="center", zorder=2)

    if subtitle:
        ax.text(text_x, subtitle_y, subtitle,
                fontsize=subtitle_size, color=subtitle_color,
                va="center", style="italic", alpha=subtitle_alpha, zorder=2)

    # Site URL bottom-left
    site_url = brand.get("site_url")
    if site_url:
        site_label = site_url.replace("https://", "").replace("http://", "").rstrip("/")
        ax.text(text_x, site_y, site_label,
                fontsize=site_size, color=title_color, va="center", weight="bold",
                alpha=0.6, zorder=2)

    # Save
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    png_path = out_path.with_suffix(".png")
    jpg_path = out_path.with_suffix(".jpg")
    plt.savefig(png_path, format="png", dpi=dpi, bbox_inches=None, facecolor=bg_color)
    plt.savefig(jpg_path, format="jpg", dpi=dpi, bbox_inches=None, facecolor=bg_color,
                pil_kwargs={"quality": 90})
    plt.close()
    print(f"Saved {png_path}")
    print(f"Saved {jpg_path}")


def _wrap_title(title: str, max_chars: int = 32) -> list[str]:
    """Naive title wrapper: split on word boundaries, target ≤ max_chars per line."""
    words = title.split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        candidate = " ".join(current + [w])
        if len(candidate) <= max_chars:
            current.append(w)
        else:
            if current:
                lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    # Cap at 3 lines — anything longer means the title is too long for this card
    return lines[:3]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--subtitle", default=None)
    ap.add_argument("--brand", default="_default")
    ap.add_argument("--aspect", default="og", choices=ASPECTS.keys())
    ap.add_argument("--bg", default="solid", choices=["solid", "gradient"])
    ap.add_argument("--out", default="featured-image",
                    help="Output path without extension; .png and .jpg will be created")
    args = ap.parse_args()

    brand = load_brand(args.brand)
    render(args.title, args.subtitle, brand, args.aspect, Path(args.out), bg=args.bg)


if __name__ == "__main__":
    main()
