# Mode: stock

Search and download free-license images from Unsplash (preferred) or Pexels (fallback), with proper attribution generated automatically.

## When to use

- Mid-article imagery for non-analytics articles (lifestyle, explainers, opinion pieces)
- LinkedIn lifestyle photo posts
- When a chart isn't appropriate but a featured image alone feels thin
- Hero/banner imagery that the brand doesn't have a custom asset for

**Do NOT use stock when:**
- The article is data-driven (use `chart` mode)
- The brand has a custom photo for this exact use (use it directly)
- The image must show a specific real entity (named person, specific product, branded location) — stock photos are generic

## Source: Unsplash + Pexels fallback

By default (`--source auto`) the script tries Unsplash first and falls back to Pexels if Unsplash returns no results or the key isn't set. Force a specific source with `--source unsplash` or `--source pexels` if you have a strong preference (some queries do better on one than the other).

## Setup (first run)

Configure at least one of these in `.env` at project root:

| Variable | Where to get a key | Free tier |
|---|---|---|
| `UNSPLASH_ACCESS_KEY` | https://unsplash.com/developers | 50 requests/hour (demo) → 5,000/hour (production) |
| `PEXELS_API_KEY` | https://www.pexels.com/api/ | 200 requests/hour |

Add to `.env`:
```
UNSPLASH_ACCESS_KEY=your-unsplash-key
PEXELS_API_KEY=your-pexels-key
```

Set both for best coverage. Either one alone is enough for normal article workflow.

## Invocation

```bash
python .claude/skills/article-images/scripts/stock.py \
  --query "coffee beans roasting" \
  --out "<article-working-dir>/images/" \
  --count 3 \
  --orientation landscape
```

## Arguments

| Flag | Required | Default | Notes |
|------|----------|---------|-------|
| `--query` | yes | — | Search terms. Be specific. "coffee" returns generic, "specialty coffee beans being roasted in a drum roaster" returns better matches. |
| `--out` | no | `.` | Output directory. Created if missing. |
| `--count` | no | `3` | Number of results to download. Pick the best one in review. |
| `--orientation` | no | `landscape` | `landscape`, `portrait`, or `squarish`. Use `squarish` for LinkedIn. |
| `--name-prefix` | no | derived from query | Filename prefix. |

## Outputs

For a query like `"coffee beans roasting"` with `--count 3`, you get:

```
coffee-beans-roasting-1.jpg
coffee-beans-roasting-2.jpg
coffee-beans-roasting-3.jpg
coffee-beans-roasting.attribution.md
```

The `.attribution.md` file contains ready-to-paste markdown blocks for each photo, formatted per Unsplash guidelines (photographer name, links with `utm_source` parameter, photo URL, license note).

## Attribution policy (important)

Unsplash photos are free for commercial and editorial use. Attribution is technically not required by the license, but **always add it** because:

1. It builds goodwill with photographers
2. It satisfies platform best practices
3. WordPress and similar CMSes treat attributed photos better in image-rights audits
4. Our brand profile rule is "every image with external content must cite its source"

The script generates the attribution markdown automatically. **Always paste it into the article** (typically as a caption under the image, or in a "Photo credits" section at the bottom).

## Workflow when called from blog-post-writer

In Stage 5, if the article needs mid-body imagery and no charts are present:

1. From the article outline / draft, pick 1-3 sections that benefit from imagery (typically intro, mid-article visual break, occasional item illustrations)
2. Compose specific search queries per section based on the actual content
3. Run `stock.py` once per query (one query per image is fine — each call is one API request)
4. Review the downloaded options, pick the best, delete the rejects
5. Insert the chosen image into the article markdown with the matching attribution block from `<prefix>.attribution.md`
6. Note the image paths in the consistency report

## Workflow when called from LinkedIn skill

LinkedIn lifestyle/opinion posts often work well with a single human or scene-led photo:

1. Read the post draft and identify the emotional hook
2. Compose a query matching the hook ("entrepreneur thinking late at night", "team meeting around laptop", "single person hiking sunrise")
3. Run with `--orientation squarish --count 4`
4. Pick best, attach to LinkedIn upload
5. Don't paste the attribution markdown into the LinkedIn post — instead, add the photographer's name as a single line at the end if voice profile allows ("Photo: Jane Doe / Unsplash"). LinkedIn doesn't do markdown.

## Search tips for better results

| Bad query | Better query |
|-----------|--------------|
| "marketing" | "marketer reviewing analytics dashboard on laptop" |
| "AI" | "developer working with multiple monitors and code" |
| "office" | "minimalist office workspace with plants and natural light" |
| "team" | "diverse small team collaborating around whiteboard" |

Specific, scene-led queries return better stock photos than abstract concept queries.

## Multi-source fallback (future)

Currently Unsplash only. If Unsplash returns no useful results, fall back to Pexels (separate API key) — not yet wired in. For now, manually search Pexels.com if Unsplash misses, and add the photo + attribution by hand.

## Cost

- Free Unsplash dev tier: 50 req/hour. Production tier free if approved.
- Bandwidth: average regular-size photo ≈ 200-500 KB.
- The script also pings Unsplash's `download_location` endpoint per their API guidelines (required for download tracking, no cost).
