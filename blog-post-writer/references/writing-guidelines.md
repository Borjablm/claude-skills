# Writing Guidelines

Shared quality rules for writer and editor sub-agents. These apply to ALL sections of every article.

## Non-Commodity Content (binding rule)

Before applying anything below, both writer and editor must read `references/non-commodity-content.md`. The article must satisfy Google's 2026 quality bar — unique, specific, authentic — or it ships with a known commodity-risk flag. Three operational rules:

1. **Specific over generic.** "Many users" → cut or replace with "68% of 412 surveyed users". "Experts say" → cut or replace with "Jane Doe, who runs Acme, says". Any unsupported generic claim in a section flagged as a non-commodity anchor (`non_commodity_anchor` non-null in the outline) is a defect — flag with `[NON_COMMODITY DRIFT]`.
2. **Information Gain per section.** Every section should add at least one element competitors don't have: a named source, a specific number, a documented incident, an original methodology detail. Sections that read like polished restatements of the SERP are commodity by definition.
3. **AI-Overview substitution test.** If the section can be summarized adequately in three sentences by an AI Overview, the section needs more specific material — a case, a number, a quote — to give the user a reason to click through and stay.

## Voice Rules

- Follow the brand profile's pronoun and person rules strictly.
- Address the reader directly — write to one person, not an audience.
- Contrarian when earned (back it up), not contrarian for shock value.
- Show, don't tell. Concrete examples > abstract claims.
- Match the brand profile's vocabulary level and humor.

## Style Rules

### Em-Dash Ban

**ZERO em-dashes (—) in any output. This is non-negotiable.**

Replace with:
- A period and a new sentence
- A comma (if the clause is short)
- Parentheses (sparingly)
- Restructure the sentence

### Paragraph Length

- Maximum 4 sentences per paragraph
- Mix short (1-2 sentence) paragraphs with longer ones for rhythm
- "Slippery slope" writing: each paragraph pulls to the next

### Sentence Rhythm

- Alternate short and long sentences
- Short sentence after a complex idea = emphasis
- Never start 3+ consecutive sentences the same way

### Lists and Tables

- Use bullet lists for 3+ inline items (don't bury lists in prose)
- Use tables for comparisons (features, pros/cons, tools)
- Don't overdo it — articles shouldn't look like documentation

## Fluff Blacklist

Remove ALL instances of these phrases. No exceptions:

- "In this section..."
- "It's important to note that..."
- "Let's dive in..."
- "Without further ado..."
- "Here's the thing:"
- "The reality is..."
- "At the end of the day..."
- "It goes without saying..."
- "Needless to say..."
- "In today's world..."
- "As we all know..."
- "It's worth mentioning..."
- "The truth is..."
- "Many people don't realize..."
- "Great question!"
- "That's a common concern"
- "Many people ask..."

## Heading Hierarchy

- `#` (H1): Article title only. Exactly ONE per article.
- `##` (H2): Major sections (list items, steps, verdict, FAQ title)
- `###` (H3): Subsections within H2s (sub-steps, FAQ questions)
- No skipped levels (no H1 → H3 without H2)
- Headings must be specific and benefit-oriented (not generic)

### Section Heading Formats by Type

- **List items:** `## [number]. [Title]` — the number = `item_number` from the outline
- **Steps:** `## Step [number]: [Title]` — the number = `item_number` from the outline
- **Sections:** `## [Title]` — no numbering
- **Verdict:** `## The Bottom Line` (or similar direct heading)
- **FAQ:** `## FAQ` or `## Frequently Asked Questions`

## SEO Rules

- Primary keyword in first 100 words of intro (bolded ONCE)
- Primary keyword 1-2 times per major section (natural placement, not forced)
- 3-5 unique LSI keywords, each used 2-3 times naturally throughout the article
- H2 titles should be search-friendly (specific, not clever)
- FAQ questions written as users actually type them into Google

## Word Count Constraints

- **Section word count = body text only**, excluding the H2/H3 heading line. This is the count that must hit ±10% of target.
- Each section must hit its `word_target` from the outline ±10%
- Total article must hit `word_count` from brief ±15%
- When over: cut low-value content, compress, consolidate
- When under: add specific examples, data points, actionable details
- NEVER pad with fluff to hit targets

## Information Density

Every sentence should earn its place. Apply this test:

1. **Does it add new information?** If not, cut it.
2. **Could it be more specific?** "Many users" → "68% of users surveyed"
3. **Is it actionable?** Vague advice → specific imperative
4. **Does it advance the reader's understanding?** Setup sentences that don't add info → cut or combine

## Engagement Hooks

Every H2 section (including step and section types) should open with an engagement hook. Types:

| Type | What It Does | Example |
|------|-------------|---------|
| `curiosity_gap` | Question or contradiction that demands resolution | "What if the most popular advice about X is wrong?" |
| `pain_point` | Name a specific frustration, pivot to solution | "You've spent hours on X only to get Y. Here's why." |
| `surprising_fact` | Counter-intuitive stat or insight | "Only 12% of teams actually use X the way it was designed." |
| `quick_win` | Promise immediate, tangible value | "This one setting change cuts your X time in half." |

## Continuity

- Reference earlier sections when relevant ("As covered in [section name] above...")
- Build a narrative arc — the article should feel like a journey, not a list of fragments
- FAQ can reference main sections: "See [Section Name] above for the full breakdown"

## Quotability

Write facts and insights in semantically friendly, NLP-friendly language that search engines can extract as featured snippets:

**Bad:** "There are various benefits to using this approach."
**Good:** "Using [approach] reduces [metric] by [X]%, according to [source]."

## WordPress-Ready Output

The final article deliverable must be WordPress-compatible HTML:

### HTML Format Rules
- **No wrapping `<html>` or `<body>` tags.** Content pastes directly into WordPress Classic Editor (Text tab) or Block Editor (Custom HTML block).
- Use semantic HTML: `<h1>` for title, `<h2>` for sections, `<h3>` for subsections, `<p>` for paragraphs, `<ul>`/`<ol>` for lists, `<strong>` for bold, `<em>` for italic.
- Links: `<a href="URL">anchor text</a>`. Add `rel="nofollow"` for commercial/product links. Internal and authority links stay dofollow. External links get `target="_blank"`.
- **No inline `<style>` blocks in articles.** Use shared theme CSS classes from `references/wordpress-theme-css.css`. These classes use the `azv-` prefix and should be added once to the WordPress theme (Appearance > Customize > Additional CSS). Articles reference the classes directly.
- Available CSS components: `azv-takeaways` (green callout), `azv-callout` (grey callout), `azv-table` (data tables), `azv-grid`/`azv-card` (feature cards), `azv-pipeline`/`azv-stage` (process flow), `azv-h2` (section spacing).

### Link Strategy
- **External authority links** (research papers, institutional reports, government sources): dofollow, `target="_blank"`
- **External commercial/product links** (company websites, SaaS tools): `rel="nofollow"`, `target="_blank"`
- **Total external links per article:** typically 5-9 for a 2,500-3,500 word piece. Don't over-link.
- **Aim for ~60-70% dofollow / 30-40% nofollow on external links.** Pure dofollow looks unnatural; pure nofollow wastes the editorial signal Google looks for. WordPress on some sites auto-applies nofollow to commercial domains, which is usually correct.

### Internal Link Volume (outbound from the new article)
Internal link count should scale with article length:

| Article length | Target internal links |
|---|---|
| < 1,500 words | 2-3 |
| 2,000-3,000 words | 4-7 |
| 3,000-5,000 words | 6-10 |
| Pillar / hub pages | 10-20+ |

Diminishing returns past ~50 internal links per page (way more than typical). The editorial test always wins: if the link genuinely helps the reader, include it; if it's forced, skip it. Quality of the target (relevance + ranking authority) matters more than count.

- **Internal links** are dofollow, `target="_blank"`.
- Always check the site's sitemap for internal link targets before finalizing.
- Spread the links across the article — don't cluster them all in one section.

### Reverse Internal Links (after publishing)
After publishing a new article, **edit 2-3 existing related pages to add forward links to it.** Don't only push outbound links from the new piece. Internal link equity flows from established pages to the new one and accelerates ranking.

- **Topical relevance over recency.** Pick pages that genuinely relate, not whichever was edited last.
- **Find natural insertion points** where the existing copy already mentions a related concept. **Avoid the second paragraph** — that placement reads as templated.
- **Vary placement** across source pages (intro, mid-section, conclusion, inside a list, FAQ).
- **Vary anchor text** across the link network. Don't repeat the same phrase.
- **One link per source page** to keep it natural.
- If no natural insertion point exists, skip the page rather than forcing a link.

### Scannable Formatting
- **Bullet points preferred over dense prose** for scannable sections (feature lists, takeaways, comparison points).
- Use callout boxes for key takeaways, methodology notes, or author context.
- Use comparison tables where appropriate (e.g., tool comparisons, feature matrices).

## Meta Data Deliverables

### Titles
- Generate **5 title options** with a **recommended pick**.
- Each title: ~60 characters max, include primary keyword once naturally.
- Vary formats: question, how-to, number, benefit-led, curiosity gap.

### Meta Descriptions
- Generate **3-5 meta description options**.
- **130 characters maximum** (strict).
- **No year references** in meta descriptions.
- Include primary keyword once. Soft CTA optional ("Learn...", "Discover...").
