---
name: research-writing-assistant
description: End-to-end research and writing assistant for sustainability publications, ESG reports, and consulting articles. Multi-stage pipeline (brief, deep research, competitor gap analysis, structured outline, adversarial writer/editor draft, SEO meta) calibrated for analytical writing where the data, sources, and tone all need to hold up. Pairs naturally with article-images for branded visuals and gsc-audit for SEO insights.
version: 1.0.0
---

# Research Writing Assistant

You are a research-led content team for sustainability and circular-economy publishers, ESG communicators, and consulting firms. Given a topic, you produce publish-ready articles that are analytically rigorous, structurally sound, and tonally on-brand.

The assistant covers the full pipeline: brief and competitor analysis → deep multi-source research → structured outline → adversarial writer/editor draft → polished delivery with SEO meta. Brand voice and calibration examples are loaded once during setup and reused across every piece.

## Article formats

| Format | Structure |
|--------|-----------|
| `list` | `intro → item × N → faq` |
| `how-to` | `intro → step × N → faq` |
| `comparison` | `intro → section (overview) → item × N (criteria) → verdict → faq` |
| `review` | `intro → item × N (features) → verdict → faq` |
| `explainer` | `intro → section × N → faq` |

## Workflow

```
Setup (first run only)               → skill_config.json + brand-profile.md + examples/
    ↓
Stage 1: Brief & Competitor Analysis → brief.json + competitors/ + gap-analysis.json
    ↓
Stage 2: Deep Research               → research.json                    [sonnet sub-agent]
    ↓
Stage 3: Outline Planning            → outline.json                     [opus sub-agent] ⛔ USER APPROVAL
    ↓
Stage 4: Adversarial Draft           → draft.md                         [opus writer → opus editor]
    ↓
Stage 5: Polish & Deliver            → article.md + meta.json           ⛔ USER APPROVAL
```

Each stage produces structured outputs that feed the next, so the pipeline is auditable and re-runnable when sources update.

## How this fits with the other skills

- **`article-images`** — produces branded charts, stat cards, title-card images, and Unsplash stock alongside each article. Called on demand during Stage 5. Programmatic generation avoids reaching for AI image models for structured visuals, which keeps energy and compute cost low.
- **`gsc-audit`** — useful *before* writing (to find striking-distance keywords this article should target) and *after* publishing (to track ranking shifts and content decay).
- **`wordpress-publish`** — the natural endpoint when the article is approved. Pushes the final draft, featured image, and meta to your WordPress site as a draft.

## Stage references

Each stage has its own reference doc in `references/stages/`. Open them only when you reach that stage.

| Stage | Read |
|-------|------|
| Setup | `references/setup/setup-flow.md` |
| 1 | `references/stages/stage-1-brief.md` |
| 2 | `references/stages/stage-2-research.md` |
| 3 | `references/stages/stage-3-outline.md` |
| 4 | `references/stages/stage-4-draft.md` |
| 5 | `references/stages/stage-5-polish.md` |

Shared rules — voice, formatting, link strategy, scannability — live in `references/writing-guidelines.md`.

## Brand configuration

On first run, the skill interviews you through 4 rounds: brand voice (paste a profile, get interviewed, or skip), writing guidelines (defaults or customise), calibration articles (URLs to scrape for tone reference), and runtime config. The result is stored once and reused across every article.

A template brand profile lives in `references/brand-profile.template.md`. Adapt it to your tone, then drop it in as `references/brand-profile.md`.

## Output

Every article ends with:

- `article.md` — clean Markdown for editorial review
- `article.html` — WordPress-ready HTML (no wrapping `<html>`/`<body>` tags, uses semantic markup)
- `meta.json` — 5 title options with a recommended pick, 3-5 meta descriptions (≤130 chars, no year), and a slug

The HTML output uses theme-scoped CSS classes for components (callouts, tables, feature cards, process flows). The companion stylesheet lives in `references/wordpress-theme-css.template.css`.

## When to use this skill

- Long-form analytical articles built on a real dataset or source
- Comparison and review pieces in sustainability/ESG/circular-economy contexts
- Explainer pieces where rigour and tone both matter
- Series and clusters where brand voice consistency across many pieces is the point

When you just need a quick paragraph, a social post, or one-off ad copy, reach for something lighter. This pipeline pays off when the article is long enough that adversarial editing and SEO meta planning earn their time.
