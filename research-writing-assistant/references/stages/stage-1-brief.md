# Stage 1: Brief & Competitor Analysis

## Overview
Gather article parameters from the user, scrape competitor content, and identify content gaps for the research phase.

Brief capture is the only point in the pipeline where the brand can supply first-hand material (case studies, proprietary data, named experts). Without it, the article will default to commodity by Stage 4 — too late to fix.

## Step 1: Gather Brief

Use AskUserQuestion to collect all parameters. Ask in 1-2 rounds maximum.

### Required Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `primary_keyword` | Main SEO target keyword | "best AI tools for entrepreneurs" |
| `format` | Article format (use AskUserQuestion with options) | list, how-to, comparison, review, explainer |
| `competitor_urls` | 2-5 top-ranking URLs to analyze (minimum 2) | URLs from SERP |
| `target_audience` | Who this is for | "Solo entrepreneurs scaling with AI" |
| `word_count` | Total target word count | 3000 |
| `search_intent` | What the searcher actually wants | informational, commercial, transactional |

### Optional Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `secondary_keywords` | [] | Additional keywords to target |
| `cta_link` | null | CTA URL to include |
| `internal_links` | [] | Internal link URLs to weave in |
| `writing_samples` | null | Text samples to emulate style from (raw text pasted directly, or file path. Multiple samples separated by `---`) |
| `brand_profile` | null | Brand profile override: file path to a custom brand profile markdown. If null, reads `references/brand-profile.md` from the skill directory. |
| `editorial_notes` | null | Special instructions from the user |
| `non_commodity_assets` | null | First-hand material the brand can supply: case studies, internal data, named experts, surveys, methodologies, customer stories, A/B test results, support-ticket patterns. Free-form text or list. **Strongly recommended** — articles without at least one non-commodity asset default to commodity content. |
| `word_count_per_section` | auto-calculated | Word budget per list item/section |
| `number_of_sections` | null (auto-derived from competitors in Stage 3) | Target section count. `null` means "let the planner decide based on competitor analysis." |

### Output: `brief.json`

Write all parameters to `brief.json` in the working directory:

```json
{
  "primary_keyword": "string",
  "secondary_keywords": ["string"],
  "format": "string",
  "target_audience": "string",
  "search_intent": "string",
  "word_count": 3000,
  "word_count_per_section": 250,
  "number_of_sections": null,
  "competitor_urls": ["string"],
  "cta_link": "string or null",
  "internal_links": ["string"],
  "writing_samples": "string or null",
  "brand_profile": null,
  "editorial_notes": "string or null",
  "non_commodity_assets": "string or null"
}
```

### Asking About Non-Commodity Assets

Before finalising the brief, ask the user explicitly (one round, optional skip allowed):

> "What first-hand material can you bring to this article that competitors can't? Examples: a specific client case, internal data, an expert on your team I should quote by name, a methodology you've used and refined, customer stories or support patterns, an A/B test result, an original survey. Pick anything you have. If you have none, say so — we'll proceed but the article will be at higher risk of being commodity content under Google's 2026 quality bar."

Capture the response in `non_commodity_assets`. If the user provides nothing, note it explicitly so Stage 3 can plan around it (and warn the user before publishing).

## Step 2: Scrape Competitors

For each URL in `competitor_urls`:

1. Use **WebFetch** to scrape the page content
2. Extract the prompt: "Extract the full article content as clean markdown. Preserve all headings (H1-H6), lists, bold/italic formatting, and any data tables. Remove navigation, sidebars, ads, and footer. Return only the article body."
3. Save to `competitors/[slug].md` — derive slug from the last meaningful URL path segment, or the domain name if the path is generic (e.g., `missiveapp`, `jotform`, `nextiva`)

**If WebFetch fails** (403, paywall, JS-rendered, empty content): note the failure, skip the URL, and continue. Minimum 2 successful scrapes are required to proceed. If fewer than 2 succeed, ask the user for alternative URLs.

After all scrapes, create `competitors/summary.md` with:
- Per-competitor: URL, title, H2 count, approximate word count, section titles list
- Cross-competitor: average H2 count, average word count, common topics, unique topics

## Step 3: Competitive Gap Analysis

Run the "Competitive Gap Spotter" analysis on the combined competitor content.

### Gap Spotter Prompt

You are a **Competitive Gap Spotter**. Analyze competitor content on a topic and generate research directions for the downstream research agent.

The goal is **Information Gain** (per Google's March 2026 core update): finding angles, data, and material that competitors lack so the article can offer genuinely new knowledge — not a polished restatement of the SERP.

**Analysis process — look for:**

1. **Missing topics** — What questions would a reader still have after reading this?
2. **Thin sections** — What do they mention but barely explain?
3. **Unsupported claims** — What do they assert without data, examples, or sources?
4. **Missing perspectives** — No user stories? No expert opinions? No real-world examples? No first-hand experience?
5. **Outdated info** — Old pricing, deprecated features, stale references?
6. **Underserved angles** — Specific use cases or audience segments they ignore?
7. **Commodity tells** — Do all competitors give the same generic advice? (Same Top-10 framings, same generic steps, same surface-level pros/cons.) These are non-commodity opportunities: places where a specific instance, named expert, or original data would dominate.

### Output: `gap-analysis.json`

```json
{
  "meta": {
    "topic": "string",
    "search_intent": "string"
  },
  "competitor_gaps": [
    {
      "gap": "specific thing that's missing or weak",
      "spotted_in": "which competitor URL or 'all'"
    }
  ],
  "research_directions": [
    {
      "what_to_find": "specific information to hunt for",
      "why": "which gap this fills"
    }
  ],
  "suggested_queries": {
    "web": ["search query"],
    "video": ["search query"],
    "reddit": ["search query"],
    "x": ["search query"]
  }
}
```

### Rules

- Copy `meta.search_intent` verbatim from `brief.json` — do not reinterpret
- Be specific. "Find user complaints about X's pricing changes" beats "find user feedback"
- Only flag real gaps you actually see — don't invent problems
- Every research direction ties back to a gap
- 3-6 queries per source type, with meaningfully different angles

## Stage Complete

After writing `brief.json`, `competitors/` folder, and `gap-analysis.json`, proceed to Stage 2.

The working directory should now contain:
```
keyword-slug-date/
├── brief.json
├── competitors/
│   ├── competitor-1.md
│   ├── competitor-2.md
│   ├── competitor-3.md
│   └── summary.md
└── gap-analysis.json
```
