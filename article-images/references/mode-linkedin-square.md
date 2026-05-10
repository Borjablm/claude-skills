# Mode: linkedin-square

Wrapper for producing 1080×1080 LinkedIn-ready images from any of the other three modes.

LinkedIn images perform best at 1080×1080 (square), with the key data point or hook visible above the platform's text fold. This mode is just a convention for forcing that aspect ratio plus a bottom attribution strip — there is no separate script.

## When to use

- Sharing an article with a chart on LinkedIn (square version of the chart)
- LinkedIn-only post with a key statistic / hook
- Repurposing a featured image as a LinkedIn share

## How to invoke

Reuse one of the existing scripts with `--aspect square` (where applicable):

### From a chart

Edit your `chart_<topic>.py` (copied from `chart_template.py`) and set:

```python
ASPECT = "square"
```

Then add a header block above the chart and tighten the layout. Reference the working example: [generate_chart_linkedin.py](../../../../articles/ai-usage-sustainability-consulting-2026-04-04/generate_chart_linkedin.py). Key conventions:

- `figsize = (10.8, 10.8)` at `dpi=100` → 1080×1080
- Top 16% of the figure: lime accent block + title + subtitle (no chart axes)
- Middle 70%: the chart itself with proper padding
- Bottom 4-8%: source attribution line via `add_source_footer(fig, source, brand)`
- Make annotations LARGER than in the landscape version — square images render small in feed

### From a featured image

```bash
python .claude/skills/article-images/scripts/featured.py \
  --title "Hook or key finding" \
  --subtitle "Optional context" \
  --brand azvai \
  --aspect square \
  --bg gradient \
  --out "<article-working-dir>/post-card-square"
```

### From a stock photo

```bash
python .claude/skills/article-images/scripts/stock.py \
  --query "your search" \
  --orientation squarish \
  --count 4 \
  --out "<linkedin-dir>/"
```

Unsplash returns roughly square photos. They may not be exactly 1080×1080. If exact dimensions matter (some LinkedIn upload paths crop), use Pillow to crop after download:

```python
from PIL import Image
img = Image.open("photo.jpg")
side = min(img.size)
left = (img.width - side) // 2
top = (img.height - side) // 2
img.crop((left, top, left + side, top + side)).resize((1080, 1080)).save("photo-1080.jpg", quality=92)
```

## Conventions

- **Always include attribution.** Even on LinkedIn where it's just one line at the end of the post text, never publish a chart or stock photo without crediting the source.
- **One key insight per square.** Don't try to fit a 5-bar chart with full labels — pick the headline number. Square images are scanned in 1-2 seconds in feed.
- **Big annotations.** Font sizes 12-16pt for axis labels, 14-18pt for value labels, 24-32pt for the title. Smaller than this and it's unreadable in mobile feed.
- **Lime/accent pills for key numbers.** The matched-pair Azvai chart uses lime "pills" around the gap labels — this draws the eye to the comparison instantly.

## Output location

Save LinkedIn squares alongside the main article:

```
<article-working-dir>/
  ├── article.md
  ├── chart-headline.svg          (landscape, inline)
  ├── chart-headline.png          (landscape, social fallback)
  ├── chart-headline-linkedin.png (square 1080×1080)  ← this mode
  ├── featured-image.png          (1200×630 OG)
  └── featured-image-square.png   (1080×1080)         ← this mode
```

Filename suffix: `-linkedin.png` or `-square.png` for clarity.

## Reference output

The Azvai sustainability article produced [chart-linkedin-gap.png](../../../../articles/ai-usage-sustainability-consulting-2026-04-04/chart-linkedin-gap.png) — that's the target quality bar. It has:

- Header block with title + subtitle on lime
- Two-color comparison bars
- Lime "pills" highlighting the gap multipliers (the key insight)
- Source line at the bottom with safe padding
- Big readable typography throughout
