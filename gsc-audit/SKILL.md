---
name: gsc-audit
description: Comprehensive Google Search Console SEO audit for agencies. Use when asked for "GSC audit", "Search Console analysis", "CTR optimization", "content decay", "keyword cannibalization", "striking distance keywords", or SEO opportunities from GSC data. Requires GSC MCP connection.
version: 1.0.0
---

# GSC SEO Audit

Generate a comprehensive SEO audit report from Google Search Console data. Analyzes 8 key areas and produces actionable recommendations.

**Non-commodity content lens.** Per Google's Search Central Live Toronto (April 2026) and the March 2026 core update's Information Gain weighting, content that reads like a polished restatement of the SERP is increasingly filtered, deindexed, or replaced by AI Overviews. This audit treats commodity-content risk as a primary diagnosis, not a side note. Read `references/non-commodity-content.md` (in the research-writing-assistant skill) for the full principles, recipes, and content-type tiering.

## What This Audit Covers

| Analysis | What It Finds | Why It Matters |
|----------|---------------|----------------|
| CTR Optimization | Pages ranking well but getting fewer clicks than expected | Quick wins - update title/meta for more traffic |
| Content Decay | Pages losing traffic vs previous period | Prioritize content refreshes |
| **Commodity Risk** | **Pages most likely to be filtered as commodity content under Google's 2026 quality bar** | **Triage rewrite candidates by commodity risk before generic refresh** |
| Quick Wins | Keywords at positions 11-20 with decent volume | Small improvements → page 1 rankings |
| Cannibalization | Multiple pages competing for same keyword | Consolidate or differentiate content |
| Mobile/Desktop Gap | Pages performing differently across devices | Fix device-specific UX issues |
| Dead Pages | Pages that dropped to zero traffic | Catch accidental deletions/deindexing |
| Brand vs Non-Brand | Traffic dependency on branded searches | Measure organic visibility health |

## Prerequisites

This skill requires the **GSC MCP server** to be configured.

**First time setup?** Read `references/setup-guide.md` and ask me: "Help me set up GSC access" — I'll guide you through it step by step, or you can follow the manual instructions.

**Already set up?** If you see "GSC tools not found" errors, check the troubleshooting section in `references/setup-guide.md`.

## Workflow

### Phase 0: Property Selection

1. List available properties:
```
Call: mcp__gsc__list_properties
```

2. Present the list and ask which property to audit.

### Phase 1: Configuration

Ask the user (with sensible defaults):

- **Brand terms**: Words to exclude from cannibalization analysis (default: extract from domain name)
- **Analysis period**: Days to analyze (default: 28)
- **Analyses to run**: All 7 or specific ones (default: all)
- **High-value pages** (optional): URL patterns where clicks matter more (sales, pricing, demo pages)
  - Default patterns: `/pricing`, `/demo`, `/contact`, `/buy`, `/checkout`, `/signup`, `/trial`, `/quote`
  - Used to prioritize CTR opportunities by business impact

### Phase 2: Data Collection

Run these MCP calls. Show progress to user ("Collecting page data... Analyzing CTR patterns...").

**For CTR Optimization + Quick Wins:**
```
Call: mcp__gsc__get_advanced_search_analytics
Params:
  site_url: [selected property]
  dimensions: "page"
  row_limit: 2000
  sort_by: "impressions"
  sort_direction: "descending"
```

**For Content Decay + Dead Pages:**
```
Call: mcp__gsc__compare_search_periods
Params:
  site_url: [selected property]
  period1_start: [28 days ago]
  period1_end: [yesterday]
  period2_start: [56 days ago]
  period2_end: [29 days ago]
  dimensions: "page"
  limit: 500
```

**For Cannibalization:**
```
Call: mcp__gsc__get_advanced_search_analytics
Params:
  site_url: [selected property]
  dimensions: "query,page"
  row_limit: 5000
  sort_by: "impressions"
  sort_direction: "descending"
```

**For Mobile/Desktop Gap:**
```
Call: mcp__gsc__get_advanced_search_analytics
Params:
  site_url: [selected property]
  dimensions: "page,device"
  row_limit: 1000
  sort_by: "impressions"
  sort_direction: "descending"
```

**For Brand vs Non-Brand:**
```
Call: mcp__gsc__get_advanced_search_analytics
Params:
  site_url: [selected property]
  dimensions: "query"
  row_limit: 2000
  sort_by: "clicks"
  sort_direction: "descending"
```

### Phase 3: Analysis

Process the collected data according to the rules in each analysis section below.

### Phase 4: Report Delivery

1. Present a **summary** with counts and top-line metrics
2. Ask if user wants the **full report**
3. Offer **CSV export** for any section

---

## Analysis Logic

### 1. CTR Optimization Opportunities

**Goal:** Find pages with good rankings but poor CTR compared to benchmarks.

**Processing:**
1. Filter to pages with position < 20 and impressions > 50
2. Look up expected CTR from `references/ctr-benchmarks.md`
3. Calculate: `ctr_gap = expected_ctr - actual_ctr`
4. Flag pages where `actual_ctr < expected_ctr * 0.7` (30%+ underperformance)
5. Calculate: `potential_clicks = impressions * ctr_gap`
6. Sort by potential_clicks descending

**Output Table:**
```
| Page | Position | Impressions | Actual CTR | Expected CTR | Gap | Potential Clicks |
```

### 2. Content Decay Detection

**Goal:** Find pages losing significant traffic that need refreshing.

**Processing:**
1. From period comparison, calculate `pct_change = (new_clicks - old_clicks) / old_clicks`
2. Flag pages with `pct_change < -0.25` (25%+ loss)
3. Determine diagnosis:
   - If position dropped >2: "Position decay - content needs refresh"
   - If position stable but CTR dropped: "CTR decay - title/snippet needs update OR AI Overview substitution"
   - If both dropped: "Full decay - major refresh needed"
   - If impressions stable but clicks dropped sharply: "AI-Overview cannibalization risk - content is summarizable, needs non-commodity material"
4. Sort by absolute click loss

**Output Table:**
```
| Page | Old Clicks | New Clicks | % Change | Old Pos | New Pos | Diagnosis |
```

### 2b. Commodity Risk Detection

**Goal:** Identify pages most likely to be filtered as commodity content under Google's 2026 quality bar (Sullivan/Levering, Search Central Live Toronto, April 2026; March 2026 Information Gain core update). These pages are rewrite candidates, not refresh candidates — generic edits won't save them.

**Inputs:** combine the data already pulled for Content Decay, CTR Optimization, and Dead Pages. Optionally fetch a small sample of the page content (via WebFetch) for the top candidates to verify.

**Risk signals (each adds to a commodity-risk score):**
1. **Index status: "Crawled - currently not indexed"** (from URL inspection on Dead Pages or top decay candidates) — strongest signal: Google has decided the content isn't valuable enough to index.
2. **Stable impressions, declining clicks** (from Content Decay): suggests AI Overview is now answering the query.
3. **High position (1-5), CTR significantly below benchmark** (from CTR Optimization): the title earned the rank but users don't click — often because the AI Overview / featured snippet has answered them already, or because the title screams generic.
4. **URL pattern signals commodity framing**: contains `/top-`, `/best-`, `/-tips`, `/-things-to-know`, `/what-is-`, `/how-to-`, `/ultimate-guide-`, plus no original-data subpath like `/research/`, `/case-study/`, `/data/`, `/report/`. Use as a soft signal, not definitive.
5. **Title pattern signals commodity framing**: starts with "Top N", "X Best", "Ultimate Guide to", "Everything you need to know", "What is", "How to" — without a specific qualifier or proprietary angle. Soft signal.
6. **Stable position but no click trend in either direction over 90 days**: the page is treading water. Often a sign that it's commodity-OK-but-replaceable.

**Scoring (sum of triggered signals):**
- 3+ signals → **High commodity risk** — recommend rewrite with non-commodity material before any other intervention
- 2 signals → **Medium commodity risk** — recommend non-commodity injection (case study, original number, named expert) into the existing article
- 1 signal → **Low commodity risk** — note but no priority action

**Output Table:**
```
| Page | Risk | Signals (count) | Triggered Signals | Recommended Recipe |
```

`Recommended Recipe` references the recipes in `references/non-commodity-content.md` of the research-writing-assistant skill (or equivalent text). Recommend by name and with a concrete first step. Examples:

- "Recipe 1 — pull last 90 days of GSC search-terms for this URL, identify the 5 highest-impression queries, run a hands-on test or analysis answering each query specifically. Title becomes '[topic]: what we found in our [analysis type]'."
- "Recipe 4 — interview one named practitioner from [adjacent network/community]. 20-minute call, 3-4 quotes, drop into existing sections."
- "Recipe 2 — crawl the top 50 [thing] from [public source], classify by [criteria], publish the breakdown table. Title becomes 'We analyzed N [things]. Here's [counterintuitive finding].'"

**For each High-risk page, also propose a content-type tier upgrade:**

> "Currently a Tier 3 generic explainer ('What is X'). Upgrade to Tier 1 by [specific recipe], or accept that organic traffic will continue to decline as AI Overviews absorb the query."

### 3. Quick Wins (Striking Distance)

**Goal:** Find keywords close to page 1 that could rank with small improvements.

**Processing:**
1. From query+page data, filter to position >= 11 AND position <= 20
2. Filter to impressions >= 100
3. Sort by impressions descending
4. Group by page to show which pages have the most opportunities

**Output Table:**
```
| Query | Page | Position | Impressions | Clicks | CTR |
```

### 4. Cannibalization Detection

**Goal:** Find queries where multiple pages compete against each other.

**Processing:**
1. From query+page data, group by query
2. Filter to queries with 2+ unique pages ranking
3. Exclude queries containing brand terms (user-provided)
4. Sort groups by total impressions
5. Within each group, sort pages by position

**Output Format:**
```
**Query: "keyword phrase"** (3 pages competing, 1,500 total impressions)
| Page | Position | Impressions | Clicks |
| /page-1/ | 8 | 800 | 45 |
| /page-2/ | 15 | 500 | 12 |
| /page-3/ | 23 | 200 | 2 |
*Recommendation: Consider consolidating into single authoritative page*
```

### 5. Mobile vs Desktop Gap

**Goal:** Find pages with significant device performance differences.

**Processing:**
1. From page+device data, pivot to get desktop and mobile metrics per page
2. Calculate gaps:
   - `ctr_ratio = max(desktop_ctr, mobile_ctr) / min(desktop_ctr, mobile_ctr)`
   - `pos_gap = abs(desktop_pos - mobile_pos)`
3. Flag pages with `ctr_ratio > 2` OR `pos_gap > 5`
4. Determine likely issue:
   - Mobile CTR much lower: "Mobile UX issue - check page speed, layout"
   - Mobile position much worse: "Mobile content issue - check mobile rendering"

**Output Table:**
```
| Page | Desktop CTR | Mobile CTR | Ratio | Desktop Pos | Mobile Pos | Gap | Issue |
```

### 6. Dead Page Finder

**Goal:** Catch pages that may have been accidentally removed or deindexed.

**Processing:**
1. From period comparison, find pages where:
   - Previous period clicks > 0
   - Current period clicks = 0
2. Exclude pages with <10 previous clicks (noise)
3. Sort by previous period clicks
4. **Auto-inspect top 5 dead pages** using URL inspection:
```
Call: mcp__gsc__inspect_url_enhanced
Params:
  site_url: [selected property]
  url: [dead page URL]
```

**Output Table:**
```
| Page | Previous Clicks | Previous Impressions | Index Status | Last Crawl | Issue |
```

Index Status values: "Indexed", "Not indexed", "Redirect", "Error"
Issue diagnosis based on inspection:
- "Submitted and indexed" → Page is fine, traffic may have shifted to another page
- "Crawled - currently not indexed" → Quality issue, content needs improvement
- "Discovered - currently not indexed" → Crawl budget issue
- "URL is not on Google" → Blocked, noindex, or removed
- "Page with redirect" → Check redirect chain

### 7. Brand vs Non-Brand Health

**Goal:** Measure organic visibility independent of brand searches.

**Processing:**
1. Classify each query as brand (contains brand term) or non-brand
2. Calculate totals for each category:
   - Total clicks, impressions
   - Average CTR, position
3. Calculate `non_brand_ratio = non_brand_clicks / total_clicks`
4. Health assessment:
   - >60%: Healthy - strong organic visibility
   - 40-60%: Moderate - room for content growth
   - <40%: Needs work - over-dependent on brand

**Output:**
```
## Brand vs Non-Brand Summary

| Metric | Brand | Non-Brand |
|--------|-------|-----------|
| Clicks | X | Y |
| Impressions | X | Y |
| Avg CTR | X% | Y% |
| Avg Position | X | Y |

**Non-brand ratio: X% - [HEALTHY/MODERATE/NEEDS WORK]**

### Top 10 Non-Brand Queries
| Query | Clicks | Impressions | CTR | Position |
```

---

## Report Format

Structure the final report as:

```markdown
# GSC Audit Report: [domain]
**Generated:** [date]
**Period:** [start] to [end]

## Executive Summary
- X CTR optimization opportunities (potential +Y clicks/month)
- X pages with content decay (lost Y clicks)
- X high commodity-risk pages, Y medium (rewrite candidates)
- X striking distance keywords
- X cannibalized queries
- X pages with mobile issues
- X dead pages detected
- Non-brand health: [status]

## 1. CTR Optimization Opportunities
[table]

## 2. Content Decay
[table]

## 3. Commodity Risk (rewrite candidates)
[table — page, risk, signals, recommended recipe, suggested tier upgrade]

## 4. Quick Wins
[table]

## 5. Cannibalization Issues
[grouped output]

## 6. Mobile/Desktop Gaps
[table]

## 7. Dead Pages
[table]

## 8. Brand vs Non-Brand
[summary + table]
```

---

## CSV Export

If user requests CSV export, format each section as comma-separated values with headers. Example for CTR Optimization:

```csv
page,position,impressions,actual_ctr,expected_ctr,gap,potential_clicks
/page-1/,5,2500,2.1%,6%,3.9%,97
/page-2/,8,1800,1.5%,3.5%,2%,36
```

---

## Error Handling

**GSC MCP not found:**
> "The GSC MCP server isn't configured. Would you like me to guide you through setup?
> I can walk you through it step-by-step, or give you a written guide to follow yourself."
>
> Follow the wizard or manual guide in `references/setup-guide.md`.

**No properties found:**
> "No Search Console properties found. Make sure your Google account has access to at least one verified property."

**Insufficient data:**
> "This property has limited data (fewer than 100 impressions in the period). The audit may not be meaningful. Continue anyway?"

**Rate limiting:**
> If GSC API returns errors, wait 30 seconds and retry. Most audits complete within rate limits.
