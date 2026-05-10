---
name: article-images
description: Generate publish-ready images for sustainability reports, ESG dashboards, and consulting articles. Five modes — branded analytics charts (matplotlib), featured/title-card images, branded HTML rendered to PNG (stat cards, social images), open-source stock photo search (Unsplash + Pexels fallback), and LinkedIn-square versions. Skip AI image generation for structured visuals — typically ~97% less compute and cost. Uses per-brand color and font profiles. Called on demand by blog-post-writer (Stage 5) and linkedin skill.
license: MIT
---

# Article Images

One skill, five modes, multiple brand profiles. Replaces the clone-and-adapt-Python-script pattern from past articles, and replaces AI image generation for any structured (text-on-background, chart, or branded-card) visual. Built for sustainability and consulting workflows where image production is recurring.

## Modes

| Mode | When to use | Output |
|------|-------------|--------|
| `chart` | Article references data the brand owns or analysed (analytics articles, original research, GSC findings, BigQuery-derived insights). | Branded SVG (inline) + PNG (featured) at requested aspect ratio. |
| `featured` | Every article needs a featured image; no other visual fits. Or an explicit title-card request. | Branded title-card PNG/JPG at OG (1200×630) and square (1080×1080). |
| `html-image` | Stat cards, social images, branded title alternatives — anything with text on background that's not a chart. Replaces AI image generation for structured visuals at ~zero compute. | Branded PNG rendered from HTML template at any size. |
| `stock` | Mid-article imagery for non-analytics pieces; LinkedIn lifestyle posts; explainers without proprietary data. | Local image file + ready-to-paste attribution markdown. Unsplash (default) with Pexels fallback. |
| `linkedin-square` | Wrapper. Take a chart or featured-image config and force 1080×1080 + bottom attribution strip. | Square PNG ready for LinkedIn upload. |

## Brand profiles

Brand colors, fonts, attribution templates, and watermark behaviour live in [brands/](brands/). One JSON per brand.

| Brand | Status | Used for |
|-------|--------|----------|
| `azvai` | Configured | Azvai blog (azvai.com), analytics articles |
| `quecafe` | Placeholder | QueCafe blog (quecafe.info) |
| `lumination` | Placeholder | Lumination consulting site |
| `_default` | Configured | Fallback when no brand specified |

**Recommended: use the setup wizard instead of editing JSON manually.**
Run `python scripts/setup_brand.py` (interactive) or pass `--non-interactive` with flags for CI use. The wizard validates colors, generates a default data palette, and saves a swatch preview. To verify a brand at any time, run `python scripts/preview_brand.py --brand <slug>` to render a multi-chart preview.

**Brand auto-detection**: when called from blog-post-writer or linkedin, infer the brand from the working directory or `brief.json` if present. Otherwise ask the user.

## How to invoke each mode

**Read the mode reference file when you reach that mode — not before.**

| Mode | Read This File |
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

All output goes to the calling article's working directory. When called from blog-post-writer, that's `{base}/[keyword-slug]-[date]/`. When called standalone, ask the user where to save (default: current directory).

## Environment

| Variable | Required for | Where |
|----------|--------------|-------|
| `UNSPLASH_ACCESS_KEY` | `stock` mode (preferred source) | `.env` at project root |
| `PEXELS_API_KEY` | `stock` mode (fallback when Unsplash returns no results, or as primary if Unsplash key not set) | `.env` at project root |

`pip install -r .claude/skills/article-images/scripts/requirements.txt` once. Python 3.9+. Uses matplotlib, Pillow, requests, python-dotenv, html2image. The `html-image` mode requires Chrome / Chromium installed (which most desktops already have).

## Source attribution rule

**Every image with data or external content must cite its source.** The brand profile defines the attribution template (font, colour, position). Charts get a footer line; stock photos get a markdown attribution block alongside the image file. Featured images that show only the brand's own content don't need attribution.

## Non-commodity tie-in

Charts produced by this skill are inherently non-commodity content — they show original data analysis using the brand's own framing. When the blog-post-writer Stage 3 outline includes a non-commodity-anchored section, that section is often a chart candidate. See `references/non-commodity-content.md` in the blog-post-writer skill for the wider rule.
