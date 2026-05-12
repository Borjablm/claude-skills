# Mode: chart

Branded analytics chart from data. Use when an article references a number, trend, ranking, or comparison that the brand owns or analysed.

## When to use

- Analytics articles built on public datasets (GSC, BigQuery, Cloudflare bot logs, Anthropic Economic Index, etc.)
- Original research / surveys
- Cross-account or cross-period comparisons
- Any non-commodity section in a research-writing-assistant outline that's anchored on data

## Workflow

Charts are bespoke — every article has different data and a different visual story. There's no generic CLI. Instead, **copy the template, edit the data + layout, run it**.

### 1. Copy the template

```bash
cp .claude/skills/article-images/scripts/chart_template.py "<article-working-dir>/chart_<topic-slug>.py"
```

### 2. Edit the script

Open the copied file and edit:

- `BRAND` — brand profile name (e.g. `azvai`, `lumination`, `quecafe`)
- `SOURCE` — exact source line for attribution footer (e.g. `"Anthropic Economic Index (2026)"`)
- `OUTPUT_BASENAME` — filename without extension
- `ASPECT` — `landscape` (10x6.5) or `square` (10.8x10.8) for LinkedIn
- `DATA` — your actual data points
- `CHART_TITLE`, `X_LABEL`, `BENCHMARK_VALUE`, `BENCHMARK_LABEL`

For non-trivial chart types (stacked, grouped, matched-pair, multiple subplots), don't try to extend the template — write the chart logic from scratch but **import branding helpers**:

```python
from branding import load_brand, apply_matplotlib_defaults, add_source_footer, color, palette
brand = load_brand("azvai")
apply_matplotlib_defaults(brand)
# ... your custom matplotlib code ...
add_source_footer(fig, "Source: ...", brand)
```

The Azvai article in [articles/ai-usage-sustainability-consulting-2026-04-04/](../../../../articles/ai-usage-sustainability-consulting-2026-04-04/) is the reference for what good output looks like — `chart-matched-pairs.svg` (matched-pair comparison), `chart3-task-penetration.svg` (long horizontal bar), `chart4-automation-augmentation.svg` (stacked horizontal with benchmark).

### 3. Run

```bash
python "<article-working-dir>/chart_<topic-slug>.py"
```

Outputs SVG (inline use in articles) + PNG (featured image / social share).

## Brand profile lookups

The brand JSON gives you:

```python
from branding import load_brand, color, palette
brand = load_brand("azvai")

color(brand, "accent")     # "#F1FFD2"
color(brand, "dark")       # "#3B3B3B"
color(brand, "benchmark")  # "#888888"
palette(brand, n=6)        # 6 data colors in brand order
```

## Output conventions

- **SVG** for inline article use (crisp at any zoom, smaller file size, fonts not embedded)
- **PNG** at 150 DPI for social/featured fallback
- Place outputs in the article working directory, not in the skill folder
- Filename pattern: `chart-<topic>.svg` / `chart-<topic>.png`
- For LinkedIn, also produce a square version: `chart-<topic>-linkedin.png` (1080×1080)

## Source attribution rule

**Every chart must show its source in the footer.** The `add_source_footer()` helper handles formatting per the brand profile. If the data is the brand's own original analysis, use the brand's `attribution.template` which already includes the brand attribution (e.g. "Source: X, analysis by azvai.com").

## When to also generate a LinkedIn-square version

If the chart is the article's headline finding (the "wow" data point), produce a square 1080×1080 version too. See [mode-linkedin-square.md](mode-linkedin-square.md) for layout conventions (header block at top, chart in middle, source at bottom). Use [generate_chart_linkedin.py](../../../../articles/ai-usage-sustainability-consulting-2026-04-04/generate_chart_linkedin.py) as a working reference.
