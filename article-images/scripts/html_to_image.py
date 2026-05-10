"""Render an HTML template to a PNG image, brand-aware.

Useful for stat cards, title cards, branded social images, and any structured
visual that's not a chart but also doesn't need AI image generation. Roughly
zero compute cost compared to DALL-E / Gemini image generation.

Usage:
    # CLI:
    python scripts/html_to_image.py \
        --template templates/title_card.html \
        --brand azvai \
        --output title.png \
        --size 1200x630 \
        --vars '{"title": "My article", "subtitle": "A subtitle"}'

    # Python:
    from html_to_image import render_html
    render_html(
        template_path="templates/stat_card.html",
        variables={"value": "97%", "label": "Energy reduction"},
        brand=load_brand("azvai"),
        output_path="card.png",
        size=(1200, 1200),
    )

Templates use {{var_name}} placeholders for variables, and CSS custom properties
that the renderer fills from the brand profile:

    :root {
        --accent: %ACCENT%;
        --dark: %DARK%;
        --light: %LIGHT%;
        --pop: %POP%;
        --font-family: %FONT_STACK%;
    }

The renderer replaces these tokens before passing the HTML to html2image.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Make `branding` importable when this file is copied elsewhere
SKILL_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_SCRIPTS))
from branding import load_brand  # noqa: E402

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"


# ---------- token replacement ----------

def _apply_brand_tokens(html: str, brand: dict) -> str:
    """Replace %ACCENT%, %DARK%, etc. with brand colors and font stack."""
    colors = brand.get("colors", {})
    fonts = brand.get("fonts", {})
    font_stack = fonts.get("stack", ["sans-serif"])
    font_family_css = ", ".join(f'"{f}"' if " " in f else f for f in font_stack)

    replacements = {
        "%ACCENT%": colors.get("accent", "#2563eb"),
        "%DARK%": colors.get("dark", "#1F2937"),
        "%LIGHT%": colors.get("light", "#F9FAFB"),
        "%POP%": colors.get("pop", colors.get("accent", "#2563eb")),
        "%BENCHMARK%": colors.get("benchmark", "#6B7280"),
        "%FONT_STACK%": font_family_css,
        "%BRAND_NAME%": brand.get("display_name", brand.get("name", "")),
        "%SITE_URL%": brand.get("site_url") or "",
        "%WATERMARK%": (brand.get("watermark") or {}).get("text") or "",
    }
    for token, value in replacements.items():
        html = html.replace(token, str(value))
    return html


def _apply_variables(html: str, variables: dict) -> str:
    """Replace {{var_name}} placeholders. Missing variables become empty strings."""
    def repl(match: re.Match) -> str:
        key = match.group(1).strip()
        return str(variables.get(key, ""))
    return re.sub(r"\{\{\s*([^}]+?)\s*\}\}", repl, html)


# ---------- rendering ----------

def render_html(
    template_path: str | Path,
    variables: dict,
    brand: dict,
    output_path: str | Path,
    size: tuple[int, int] = (1200, 630),
) -> Path:
    """Render an HTML template to PNG. Returns the output Path."""
    try:
        from html2image import Html2Image
    except ImportError:
        raise SystemExit(
            "html2image is required. Install it with:\n"
            "    pip install html2image\n"
            "It uses your system's Chrome / Chromium installation."
        )

    template_path = Path(template_path)
    if not template_path.exists():
        # Try relative to templates dir
        candidate = TEMPLATES_DIR / template_path
        if candidate.exists():
            template_path = candidate
        else:
            raise FileNotFoundError(f"Template not found: {template_path}")

    raw_html = template_path.read_text(encoding="utf-8")
    html = _apply_brand_tokens(raw_html, brand)
    html = _apply_variables(html, variables)

    # Inject explicit viewport sizing so 100vh / flex layouts work reliably
    # (html2image's headless Chrome sometimes does not apply viewport height to body
    # when rendering at custom sizes).
    width, height = size
    sizing_css = (
        f"<style>html, body {{ width: {width}px !important; "
        f"height: {height}px !important; margin: 0 !important; }}</style>"
    )
    if "</head>" in html:
        html = html.replace("</head>", sizing_css + "</head>", 1)
    else:
        html = sizing_css + html

    output_path = Path(output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    hti = Html2Image(output_path=str(output_path.parent))
    hti.screenshot(
        html_str=html,
        save_as=output_path.name,
        size=size,
    )
    return output_path


# ---------- CLI ----------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render HTML template to PNG (brand-aware)")
    p.add_argument("--template", "-t", required=True,
                   help="Path to HTML template (relative to templates/ or absolute)")
    p.add_argument("--brand", "-b", default="_default",
                   help="Brand profile slug")
    p.add_argument("--output", "-o", required=True,
                   help="Output PNG path")
    p.add_argument("--size", "-s", default="1200x630",
                   help="Output size as WIDTHxHEIGHT (default: 1200x630)")
    p.add_argument("--vars", "-v", default="{}",
                   help="JSON object of template variables")
    p.add_argument("--vars-file",
                   help="Path to JSON file with template variables")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    # Parse size
    if "x" not in args.size:
        print(f"Invalid size: {args.size}. Use WIDTHxHEIGHT format.", file=sys.stderr)
        return 2
    w, h = args.size.split("x", 1)
    size = (int(w), int(h))

    # Load variables
    if args.vars_file:
        variables = json.loads(Path(args.vars_file).read_text(encoding="utf-8"))
    else:
        variables = json.loads(args.vars)

    # Load brand
    brand = load_brand(args.brand)

    # Render
    out = render_html(
        template_path=args.template,
        variables=variables,
        brand=brand,
        output_path=args.output,
        size=size,
    )
    print(f"Saved: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
