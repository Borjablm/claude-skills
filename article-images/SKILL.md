---
name: article-images
description: Generate publish-ready visuals for sustainability reports, ESG dashboards, and research-led articles. Five modes — branded analytics charts (matplotlib), featured / title-card images, branded HTML rendered to PNG (stat cards, social images), open-license stock photo search (Unsplash + Pexels), and LinkedIn-square versions. Skip AI image generation for structured visuals: typically ~97% less compute and energy. Uses per-brand colour and font profiles. Pairs with research-writing-assistant for end-to-end content production.
license: MIT
---

# Article Images

One skill, five modes, multiple brand profiles. Built for sustainability and research-led consulting work where image production is recurring and the cost of using AI image generation for structured visuals adds up. Replaces the clone-and-adapt-Python-script pattern from past articles, and replaces AI image generation for any text-on-background or chart visual.

## Modes

| Mode | When to use | Output |
|------|-------------|--------|
| `chart` | Article references data the brand owns or analysed (sustainability metrics, ESG benchmarks, research findings, GSC analytics). | Branded SVG (inline) + PNG (featured) at requested aspect ratio. |
| `featured` | Every article needs a featured image; no other visual fits. Or an explicit title-card request. | Branded title-card PNG/JPG at OG (1200×630) and square (1080×1080). |
| `html-image` | Stat cards, social images, branded title alternatives — anything with text on background that's not a chart. Replaces AI image generation for structured visuals at ~zero compute. | Branded PNG rendered from HTML template at any size. |
| `stock` | Mid-article imagery for non-analytics pieces; LinkedIn lifestyle posts; explainers without proprietary data. | Local image file + ready-to-paste attribution markdown. Unsplash (default) with Pexels fallback. |
| `linkedin-square` | Wrapper. Take a chart or featured-image config and force 1080×1080 + bottom attribution strip. | Square PNG ready for LinkedIn upload. |

## How this fits with the other skills

- **`research-writing-assistant`** is the natural pair. When that skill writes a piece, it calls into this one in Stage 5 to generate the charts, featured image, and any stat cards the article references.
- **`gsc-audit`** outputs that warrant a chart (striking-distance keyword ladders, content decay timelines) can feed straight into `chart` mode here.
- **`wordpress-publish`** uploads the generated PNGs as featured images and inline media.

## Brand profiles

Brand colours, fonts, attribution templates, and watermark behaviour live in `brands/`. One JSON per brand.

**Recommended: use the setup wizard instead of editing JSON manually.**
Run `python scripts/setup_brand.py` (interactive) or pass `--non-interactive` with flags for CI use. The wizard validates colours, generates a default data palette, and saves a swatch preview. To verify a brand at any time, run `python scripts/preview_brand.py --brand <slug>` to render a multi-chart preview.

**Brand auto-detection:** when called from `research-writing-assistant`, infer the brand from the working directory or `brief.json` if present. Otherwise ask the user.

## How to invoke each mode

**Read the mode reference file when you reach that mode — not before.**

| Mode | Read this file |
|------|---------------|
| chart | [references/mode-chart.md](references/mode-chart.md) |
| featured | [references/mode-featured.md](references/mode-featured.md) |
| html-image | [references/mode-html-image.md](references/mode-html-image.md) |
| stock | [references/mode-stock.md](references/mode-stock.md) |
| linkedin-square | [references/mode-linkedin-square.md](references/mode-linkedin-square.md) |

For non-developer users, a unified CLI wraps everything:

```bash
python scripts/cli.py setup --slug acme --primary "#10b981"
python scripts/cli.py preview --brand acme
python scripts/cli.py featured --brand acme --title "..." --out featured
python scripts/cli.py stock --query "wind turbines" --count 3
python scripts/cli.py html --template title_card.html --brand acme --vars '{"title":"..."}' --output card.png
```

## Working directory

All output goes to the calling article's working directory. When called from `research-writing-assistant`, that's `{base}/[keyword-slug]-[date]/`. When called standalone, ask the user where to save (default: current directory).

## Environment

| Variable | Required for | Where |
|----------|--------------|-------|
| `UNSPLASH_ACCESS_KEY` | `stock` mode (preferred source) | `.env` at project root |
| `PEXELS_API_KEY` | `stock` mode (fallback when Unsplash returns no results, or as primary if Unsplash key not set) | `.env` at project root |

`pip install -r scripts/requirements.txt` once. Python 3.9+. Uses matplotlib, Pillow, requests, python-dotenv, html2image. The `html-image` mode requires Chrome / Chromium installed (which most desktops already have).

## Source attribution rule

**Every image with data or external content must cite its source.** The brand profile defines the attribution template (font, colour, position). Charts get a footer line; stock photos get a markdown attribution block alongside the image file. Featured images that show only the brand's own content don't need attribution.

## Why programmatic over AI image generation

For structured visuals — charts, stat cards, branded title cards, social images — AI image generation is the wrong tool:

- DALL-E 3 charges $0.04 to $0.12 per image. Gemini Imagen ranges from $0.02 to $0.24.
- Each image runs ~3 Wh of compute energy (per 2026 measurements).
- 3-5 iterations per image to land the right look.
- Output is generic, not brand-aware.

This skill produces equivalent or better visuals for ~$0 in cloud cost and ~0.01 Wh of local compute, with brand colours and fonts consistently applied. AI image generation stays useful for genuine photographic outputs (photorealistic compositions, custom photo edits) — keep it for that.

## Non-commodity tie-in

Charts produced by this skill are inherently non-commodity content — they show original data analysis using the brand's own framing. When the `research-writing-assistant` outline includes a non-commodity-anchored section, that section is often a chart candidate.
