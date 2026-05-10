"""Interactive brand profile wizard for article-images.

Walks the user through creating a new brand profile JSON, validates colors,
and saves a preview swatch. Produces a brands/<slug>.json file ready for use
by chart, featured, and html-to-image modes.

Usage:
    python scripts/setup_brand.py
    python scripts/setup_brand.py --slug acme --non-interactive --primary "#FF6B35"

Non-interactive mode is useful for CI / scripted setup. It applies sensible
defaults for any flag not provided.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

BRANDS_DIR = Path(__file__).resolve().parent.parent / "brands"


# ---------- helpers ----------

HEX_RE = re.compile(r"^#?[0-9a-fA-F]{6}$")


def normalise_hex(value: str, *, fallback: str | None = None) -> str:
    """Validate and normalise a hex color. Raises ValueError on invalid input."""
    if not value:
        if fallback:
            return fallback
        raise ValueError("empty color")
    value = value.strip()
    if not HEX_RE.match(value):
        raise ValueError(f"'{value}' is not a valid 6-digit hex color")
    return "#" + value.lstrip("#").lower()


def relative_luminance(hex_color: str) -> float:
    """Return the WCAG relative luminance (0=black, 1=white)."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def slug_ok(slug: str) -> bool:
    return bool(re.match(r"^[a-z0-9][a-z0-9_-]*$", slug))


def prompt(question: str, default: str | None = None, *, validator=None) -> str:
    """Prompt with optional default and validator. Re-prompts on invalid input."""
    suffix = f" [{default}]" if default else ""
    while True:
        ans = input(f"{question}{suffix}: ").strip()
        if not ans and default is not None:
            ans = default
        if validator:
            try:
                ans = validator(ans)
            except ValueError as e:
                print(f"  Not valid: {e}")
                continue
        if ans:
            return ans


# ---------- swatch generation ----------

def render_swatch(brand: dict, output_path: Path) -> None:
    """Render a 6-square color swatch + chart preview."""
    colors = brand["colors"]
    palette = colors.get("data_palette", [])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # --- left: brand colors as named blocks ---
    blocks = [
        ("accent", colors.get("accent", "#000000")),
        ("dark", colors.get("dark", "#000000")),
        ("light", colors.get("light", "#FFFFFF")),
        ("pop", colors.get("pop", colors.get("accent", "#000000"))),
        ("benchmark", colors.get("benchmark", "#888888")),
    ]
    for i, (name, c) in enumerate(blocks):
        ax1.add_patch(mpatches.Rectangle((i, 0), 1, 1, facecolor=c, edgecolor="#333"))
        text_color = "#000" if relative_luminance(c) > 0.5 else "#FFF"
        ax1.text(i + 0.5, 0.5, name, ha="center", va="center",
                 fontsize=11, color=text_color, weight="bold")
        ax1.text(i + 0.5, -0.18, c, ha="center", va="center", fontsize=8, color="#666")
    ax1.set_xlim(0, len(blocks))
    ax1.set_ylim(-0.4, 1.2)
    ax1.set_aspect("equal")
    ax1.axis("off")
    ax1.set_title("Named brand colors", loc="left", weight="bold",
                  color=colors.get("dark", "#333"), pad=8)

    # --- right: data palette demo as a horizontal bar chart ---
    if palette:
        labels = [f"Series {i+1}" for i in range(len(palette))]
        values = list(range(len(palette), 0, -1))
        ax2.barh(labels[::-1], values[::-1], color=palette,
                 edgecolor=colors.get("dark", "#333"), linewidth=0.5)
        ax2.set_title("Data palette preview", loc="left", weight="bold",
                      color=colors.get("dark", "#333"), pad=8)
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
    else:
        ax2.text(0.5, 0.5, "No data palette configured", ha="center", va="center",
                 fontsize=11, color="#666", transform=ax2.transAxes)
        ax2.axis("off")

    fig.suptitle(f"Brand preview: {brand.get('display_name', brand.get('name'))}",
                 fontsize=14, weight="bold", color=colors.get("dark", "#333"),
                 x=0.05, ha="left", y=0.98)

    plt.tight_layout(rect=(0, 0, 1, 0.94))
    plt.savefig(output_path, dpi=120, bbox_inches="tight", facecolor="white")
    plt.close()


# ---------- builders ----------

def build_palette(accent: str, pop: str, dark: str) -> list[str]:
    """Generate a sensible default 6-color data palette from primary brand colors."""
    return [accent, pop, dark, "#A8E6A3", "#F4B184", "#888888"]


def build_brand(args, *, interactive: bool) -> dict:
    """Construct the brand dict from CLI args + (optionally) interactive prompts."""
    if interactive:
        print("\n--- Brand profile setup ---\n")

    # name + slug
    name = args.name or (
        prompt("Brand display name (e.g. 'Acme Sustainability')") if interactive else "My Brand"
    )
    default_slug = args.slug or re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    slug = (
        args.slug
        or (prompt("Slug (lowercase, hyphens)", default=default_slug, validator=lambda s: s if slug_ok(s) else (_ for _ in ()).throw(ValueError("slug must be lowercase letters/numbers/hyphens")))
            if interactive else default_slug)
    )
    if not slug_ok(slug):
        raise SystemExit(f"Invalid slug: {slug!r} (lowercase letters, digits, '-' or '_' only)")

    # site url
    site_url = args.site_url or (
        prompt("Site URL (optional, can leave blank)", default="")
        if interactive else ""
    ) or None

    # colors
    primary = normalise_hex(
        args.primary or (prompt("Primary / accent color (hex, e.g. #2563eb)",
                                validator=normalise_hex) if interactive else "#2563eb")
    )
    dark = normalise_hex(
        args.dark or (prompt("Dark / text color (hex)", default="#1F2937",
                             validator=normalise_hex) if interactive else "#1F2937")
    )
    light = normalise_hex(
        args.light or (prompt("Light / subtle background (hex)", default="#F9FAFB",
                              validator=normalise_hex) if interactive else "#F9FAFB")
    )
    pop = normalise_hex(
        args.pop or (prompt("Pop / secondary accent (hex)", default=primary,
                            validator=normalise_hex) if interactive else primary)
    )
    benchmark = normalise_hex(
        args.benchmark or (prompt("Benchmark / reference line color (hex)",
                                  default="#6B7280", validator=normalise_hex)
                           if interactive else "#6B7280")
    )

    # fonts
    font_stack_str = args.fonts or (
        prompt("Font stack (comma-separated)",
               default="DM Sans, Helvetica, Arial, sans-serif")
        if interactive else "DM Sans, Helvetica, Arial, sans-serif"
    )
    font_stack = [f.strip() for f in font_stack_str.split(",") if f.strip()]

    # attribution
    attribution_template = args.attribution or (
        prompt("Source attribution template (use {source} placeholder)",
               default=f"Source: {{source}}, analysis by {site_url or name.lower().replace(' ', '')}")
        if interactive else f"Source: {{source}}"
    )

    # watermark
    watermark_text = args.watermark or (
        prompt("Watermark text (optional, e.g. brand domain)",
               default=site_url.replace("https://", "").replace("http://", "").rstrip("/")
                       if site_url else "")
        if interactive else ""
    )

    brand = {
        "name": slug,
        "display_name": name,
        "site_url": site_url,
        "colors": {
            "accent": primary,
            "dark": dark,
            "light": light,
            "pop": pop,
            "data_palette": build_palette(primary, pop, dark),
            "benchmark": benchmark,
        },
        "fonts": {
            "family": "sans-serif",
            "stack": font_stack,
        },
        "attribution": {
            "template": attribution_template,
            "color_alpha": 0.6,
            "position": "bottom-left",
            "font_size": 10,
        },
        "watermark": {
            "enabled": bool(watermark_text),
            "text": watermark_text or None,
            "position": "bottom-right",
            "alpha": 0.6,
        },
        "title_card": {
            "background": "white",
            "accent_block": {"enabled": True, "side": "left", "width_pct": 0.06},
            "title_color": "dark",
            "subtitle_color": "dark",
            "subtitle_alpha": 0.85,
        },
    }
    return brand


# ---------- main ----------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Set up a new brand profile for article-images")
    p.add_argument("--non-interactive", action="store_true",
                   help="Skip prompts; use defaults / flags only")
    p.add_argument("--name", help="Brand display name")
    p.add_argument("--slug", help="Brand slug (lowercase, hyphens)")
    p.add_argument("--site-url", help="Brand site URL")
    p.add_argument("--primary", help="Primary / accent color (hex)")
    p.add_argument("--dark", help="Dark / text color (hex)")
    p.add_argument("--light", help="Light / subtle background (hex)")
    p.add_argument("--pop", help="Pop / secondary accent color (hex)")
    p.add_argument("--benchmark", help="Benchmark / reference color (hex)")
    p.add_argument("--fonts", help="Font stack, comma-separated")
    p.add_argument("--attribution", help="Source attribution template")
    p.add_argument("--watermark", help="Watermark text")
    p.add_argument("--overwrite", action="store_true",
                   help="Overwrite existing brand file if it already exists")
    p.add_argument("--no-swatch", action="store_true",
                   help="Skip generating the preview swatch")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    interactive = not args.non_interactive

    BRANDS_DIR.mkdir(parents=True, exist_ok=True)

    brand = build_brand(args, interactive=interactive)
    brand_path = BRANDS_DIR / f"{brand['name']}.json"

    if brand_path.exists() and not args.overwrite:
        print(f"\nBrand profile {brand_path} already exists.")
        if interactive:
            ans = input("Overwrite? [y/N]: ").strip().lower()
            if ans != "y":
                print("Aborted. Use --overwrite to skip this prompt.")
                return 1
        else:
            print("Pass --overwrite to replace it.")
            return 1

    # write JSON
    brand_path.write_text(json.dumps(brand, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved {brand_path}")

    # render swatch
    if not args.no_swatch:
        swatch_path = BRANDS_DIR / f"{brand['name']}-swatch.png"
        try:
            render_swatch(brand, swatch_path)
            print(f"Saved swatch preview: {swatch_path}")
        except Exception as e:
            print(f"Could not render swatch: {e}")

    print("\nNext steps:")
    print(f"  - Use brand='{brand['name']}' when calling chart, featured, or html-image modes")
    print(f"  - Tweak {brand_path} to adjust colors, fonts, or attribution")
    return 0


if __name__ == "__main__":
    sys.exit(main())