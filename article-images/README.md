# article-images

A Claude Code skill for producing publish-ready images programmatically. Built for sustainability reports, ESG dashboards, and consulting articles where visuals are recurring and the cost of regenerating them with AI image models adds up. **Skip AI image generation for charts, stat cards, and structured visuals — typically ~97% less compute and cost.**

## What it does

Five modes, one toolchain:

| Mode | Use case | Tech |
|---|---|---|
| **chart** | Branded analytics charts (bar, stacked, time series, grouped, donut) | matplotlib |
| **featured** | OG-card / title-card images for articles | matplotlib + Pillow |
| **html-image** | Stat cards, social cards, anything HTML+CSS rendered to PNG | html2image (headless Chrome) |
| **stock** | Free-license stock photos with attribution | Unsplash + Pexels APIs |
| **linkedin-square** | 1080×1080 LinkedIn-ready wrapper around any of the above | matplotlib |

All five modes use a shared **brand profile** (colors, fonts, attribution template, watermark) so output is consistent across an article, a campaign, or a client.

## Why programmatic over AI image generation

For structured visuals — charts, stat cards, branded title cards, social images — AI image generation is the wrong tool:

- DALL-E 3 charges $0.04 to $0.12 per image. Gemini Imagen ranges from $0.02 to $0.24.
- Each image runs ~3 Wh of compute energy ([2026 study](https://arxiv.org/abs/2506.17016)).
- 3-5 iterations per image to land the right look.
- Output is generic, not brand-aware.

This skill produces equivalent or better visuals for ~$0 in cloud cost and ~0.01 Wh of local compute, with brand colors and fonts consistently applied. AI image generation is still useful for genuine photographic outputs (photorealistic compositions, custom photo edits) — keep it for that.

## Quick start

```bash
# 1. Install dependencies (one-time)
pip install -r scripts/requirements.txt

# 2. Set up your brand (interactive wizard)
python scripts/setup_brand.py
# ...or non-interactive
python scripts/setup_brand.py --non-interactive --slug acme \
    --name "Acme Sustainability" --primary "#10b981"

# 3. Verify the brand looks right
python scripts/preview_brand.py --brand acme

# 4. Use any mode
python scripts/cli.py featured --brand acme --title "My article" --out featured
python scripts/cli.py html --template title_card.html --brand acme \
    --vars '{"title":"How AI in L&D Really Works"}' --output title.png
python scripts/cli.py stock --query "wind turbines at dusk" --count 3
```

For chart-specific work, copy a chart template into your article working directory and edit the data:

```bash
cp scripts/chart_template.py /path/to/article/chart_my_topic.py
# edit DATA, CONFIG, render
python /path/to/article/chart_my_topic.py
```

## Brand profiles

Brand profiles live in `brands/<slug>.json`. Each profile defines:

- **Colors**: accent, dark, light, pop, benchmark, plus a 6-color data palette
- **Fonts**: a CSS font stack (e.g. `["DM Sans", "Helvetica", "Arial", "sans-serif"]`)
- **Attribution template**: how source lines render (`Source: {source}, analysis by example.com`)
- **Watermark**: optional brand text rendered in the corner of charts

The `setup_brand.py` wizard validates colors, generates a default data palette, and saves a swatch preview alongside the JSON. The `preview_brand.py` script renders all chart types in your brand for a quick sanity check.

## Modes in detail

Each mode has its own reference doc in `references/`:

- [`mode-chart.md`](references/mode-chart.md) — copy-and-edit Python chart templates
- [`mode-featured.md`](references/mode-featured.md) — branded title cards
- [`mode-html-image.md`](references/mode-html-image.md) — render HTML templates to PNG
- [`mode-stock.md`](references/mode-stock.md) — Unsplash + Pexels stock search
- [`mode-linkedin-square.md`](references/mode-linkedin-square.md) — square-format wrapper

## Environment

| Variable | Required for | Where to get one |
|---|---|---|
| `UNSPLASH_ACCESS_KEY` | `stock` mode (preferred source) | https://unsplash.com/developers |
| `PEXELS_API_KEY` | `stock` mode (fallback or alternative source) | https://www.pexels.com/api/ |

Add to `.env` at the project root. Both are free.

For `html-image` mode you also need Chrome / Chromium installed locally (most desktops already have this; html2image shells out to it).

## Source attribution

Every visual that uses external data or photography should cite its source. The skill handles this:

- **Charts**: source line rendered in the bottom-left of the chart, in brand color and style
- **Stock photos**: a markdown attribution block is generated alongside each downloaded image, with proper photographer credit and platform link
- **Featured images**: typically don't need attribution; you control the `subtitle` content

## File structure

```
article-images/
├── README.md                    # this file
├── SKILL.md                     # internal skill manifest (used by Claude Code)
├── brands/                      # brand profiles
│   ├── _default.json
│   └── <your-slug>.json
├── templates/                   # HTML templates for html-image mode
│   ├── title_card.html
│   └── stat_card.html
├── references/                  # per-mode reference docs
│   ├── mode-chart.md
│   ├── mode-featured.md
│   ├── mode-html-image.md
│   ├── mode-stock.md
│   └── mode-linkedin-square.md
└── scripts/
    ├── branding.py              # shared brand loading + matplotlib defaults
    ├── chart_template.py        # bar chart template (copy and edit)
    ├── chart_stacked_template.py
    ├── chart_timeseries_template.py
    ├── chart_grouped_template.py
    ├── chart_donut_template.py
    ├── featured.py              # title card / OG image generator
    ├── html_to_image.py         # HTML template → PNG renderer
    ├── stock.py                 # Unsplash / Pexels stock search
    ├── setup_brand.py           # brand profile wizard
    ├── preview_brand.py         # multi-chart brand preview
    ├── cli.py                   # unified CLI entry point
    └── requirements.txt
```

## License

MIT. Brand profiles and chart templates are designed to be copied, modified, and republished — that's the point.

## Background

This skill is part of the [Claude Code skills hub](https://azvai.com/skills/) for sustainability consulting workflows. It's the proof point behind the article ["How Claude Code Skills Cut AI Energy Use"](https://azvai.com/claude-code-skills-cut-ai-energy-use/), which shows the cost and energy math against AI image generation in detail.
