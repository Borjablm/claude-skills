# Mode: featured

Branded title-card / featured image. Use when an article needs a featured image and no other visual fits, or when explicitly requested.

## When to use

- Every blog-post-writer article needs a featured image — call this mode in Stage 5 unless the article already has a chart or stock image suitable for featured use
- Title cards for LinkedIn (use `--aspect square`)
- Quick OG image for any article without bespoke imagery

## Invocation

```bash
python .claude/skills/article-images/scripts/featured.py \
  --title "Your article title" \
  --subtitle "Optional subtitle or kicker" \
  --brand azvai \
  --aspect og \
  --bg solid \
  --out "<article-working-dir>/featured-image"
```

Both `<basename>.png` and `<basename>.jpg` are produced (WordPress prefers JPG for featured images, but PNG keeps text crisp).

## Arguments

| Flag | Required | Default | Notes |
|------|----------|---------|-------|
| `--title` | yes | — | Article title. Wrapped automatically at ~28-32 chars per line, max 3 lines. Keep titles short. |
| `--subtitle` | no | none | Italic kicker line below the title. |
| `--brand` | no | `_default` | Brand profile slug from [brands/](../brands/). |
| `--aspect` | no | `og` | `og` (1200×630), `square` (1080×1080), or `landscape` (1200×675). |
| `--bg` | no | `solid` | `solid` (brand `title_card.background` color) or `gradient` (light → accent diagonal). |
| `--out` | no | `featured-image` | Output basename (no extension). |

## Visual anatomy

The featured image always has:

- Background (solid or gradient based on `--bg`)
- Optional accent block on the side (controlled by brand profile `title_card.accent_block`)
- Title in bold, large, brand `title_color`
- Subtitle in italic, smaller, alpha-reduced
- Site URL in bottom-left, alpha-reduced

This is intentionally simple. The visual interest comes from the brand colors and accent block, not from generative imagery. For richer visuals, use `stock` mode or generate a chart with `chart` mode.

## Aspect-ratio guidance

| Aspect | When | Notes |
|--------|------|-------|
| `og` (1200×630) | Default for blog featured / Open Graph / Twitter card | Most platforms accept this |
| `square` (1080×1080) | LinkedIn post image, Instagram | Layout adjusts: tighter typography, centered |
| `landscape` (1200×675) | Twitter/X large card | Subtle aspect change from OG |

Generate `og` and `square` together for any article that will also be posted to LinkedIn — easier than re-running later.

## Calling from blog-post-writer

In Stage 5 (Polish & Deliver), after the article is finalized:

1. Read `meta.json` for the recommended title and `brief.json` for the brand
2. If no featured image exists yet (no chart suitable, no stock fetched), call:

```bash
python .claude/skills/article-images/scripts/featured.py \
  --title "<recommended_title>" \
  --subtitle "<brand display_name or topic kicker>" \
  --brand <brand_slug> \
  --aspect og \
  --out "<working_dir>/featured-image"
```

3. Note the path in the consistency report as the `featured_image` deliverable.

## Calling from LinkedIn skill

For a text-only LinkedIn post that needs a quick visual, call with `--aspect square`:

```bash
python .claude/skills/article-images/scripts/featured.py \
  --title "<post hook or one-liner>" \
  --brand <brand_slug> \
  --aspect square \
  --out "<linkedin-output-dir>/post-card"
```

Use a short, punchy title (≤60 chars). The square layout breathes badly with long titles.

## Limitations

- No imagery beyond solid background + accent block + gradient. For richer featured images, layer over a stock photo (use `stock` mode to fetch the photo, then use `edit-image` skill or PIL composition — out of scope for this script).
- Title wrapping is naive (word boundaries, max 3 lines). For perfect typography, generate the image, eyeball it, and adjust the title length if it wraps badly.
- Default fonts assume DM Sans/Helvetica/Arial are available on the system. If not, matplotlib falls back to the next available sans-serif.
