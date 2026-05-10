# Mode: html-image

Render a branded HTML template to PNG. Use for stat cards, title cards, social
images, and any structured visual that's not a chart but also doesn't need AI
image generation.

## When to use

- Article featured images / OG cards (with title text + brand block)
- Stat cards: one big number + label + source attribution
- LinkedIn carousel slides
- Any structured visual that's primarily text on a background
- Anything where the same template would be reused with different variables

For free-form data charts, use `mode-chart`. For real photographs, use
`mode-stock`. For genuine photo edits (face swap, object addition), use the
separate `edit-image` skill or AI image generation.

## Why programmatic over AI image generation

Per the article ["How Claude Code Skills Cut AI Energy
Use"](https://azvai.com/claude-code-skills-cut-ai-energy-use/), AI image
generation costs roughly $0.04-$0.13 per image and ~3 Wh of energy. Rendering
HTML to PNG locally is essentially free in compute and ~0.01 Wh. For
structured visuals (text + brand + layout), HTML templates always win.

## Workflow

### 1. Pick or create a template

Two starter templates ship with the skill, in `templates/`:

| Template | Use case | Recommended size |
|---|---|---|
| `title_card.html` | Article featured image, OG card | 1200x630 |
| `stat_card.html` | One big number + source attribution | 1200x1200 (square) or 1200x630 |

Templates use:
- `{{variable_name}}` for content placeholders (filled at render time)
- `%TOKEN%` for brand colors and font stack (filled by the renderer from the brand profile)

### 2. Run the renderer

CLI:

```bash
python scripts/html_to_image.py \
    --template templates/stat_card.html \
    --brand azvai \
    --output stat-energy.png \
    --size 1200x1200 \
    --vars '{"eyebrow": "Compute saving", "value": "97%", "label": "less energy when using programmatic image production vs AI generation", "source": "Anthropic API pricing & Epoch AI 2026"}'
```

Python:

```python
from html_to_image import render_html
from branding import load_brand

render_html(
    template_path="templates/title_card.html",
    variables={
        "eyebrow": "How-to",
        "title": "How Claude Code Skills Cut AI Energy Use",
        "subtitle": "Skills, caching, and sub-agents.",
    },
    brand=load_brand("azvai"),
    output_path="featured.png",
    size=(1200, 630),
)
```

### 3. Use the output

Drop the PNG into your article, social post, or report. For SEO image alt text,
describe the visible content concretely (the value, the label, the source).

## Building your own template

A minimum HTML template:

```html
<!DOCTYPE html>
<html>
<head>
<style>
  :root {
    --accent: %ACCENT%;
    --dark: %DARK%;
    --light: %LIGHT%;
    --pop: %POP%;
    --font-family: %FONT_STACK%;
  }
  body {
    font-family: var(--font-family);
    background: var(--light);
    color: var(--dark);
  }
</style>
</head>
<body>
  <h1>{{title}}</h1>
  <p>{{description}}</p>
</body>
</html>
```

The renderer replaces:
- `%ACCENT%`, `%DARK%`, `%LIGHT%`, `%POP%`, `%BENCHMARK%` — brand colors
- `%FONT_STACK%` — quoted comma-separated font stack
- `%BRAND_NAME%`, `%SITE_URL%`, `%WATERMARK%` — brand metadata
- `{{any_var}}` — variables you pass at render time

## Dependencies

The renderer uses [`html2image`](https://pypi.org/project/html2image/), which
shells out to your local Chrome / Chromium installation. Install with:

```bash
pip install html2image
```

If you don't have Chrome installed, install a Chromium-based browser first.
For most desktops this is already present.

## Output conventions

- File format: PNG (best for text-heavy graphics with sharp edges)
- Default sizes:
  - **1200x630** — Open Graph / Twitter card aspect (most blog featured images)
  - **1200x1200** — Square, good for LinkedIn / Instagram
  - **1080x1080** — LinkedIn organic post (use mode-linkedin-square for
    additional header/footer treatment)
- Place outputs in the article working directory, not in the skill folder
- Filename pattern: `<topic>-card.png` or `stat-<value>.png`

## Source attribution

If the visual references external data, embed the source line directly in the
template (the stat_card template does this) or compose it via the
`{{source}}` variable.

## When NOT to use this mode

- The visual is primarily a chart (use `mode-chart` instead)
- The visual is a photograph (use `mode-stock` instead)
- The visual genuinely needs photographic AI generation (faces, products in
  scenes, photorealistic compositions). For those, use the `edit-image` skill
  or call Gemini/DALL-E. But check first: most "I need an AI image" requests
  turn out to be text-on-background, which this mode handles for free.