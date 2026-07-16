# Claude Code skills for sustainability consulting workflows

A growing hub of [Claude Code](https://claude.com/claude-code) skills built for sustainability and circular economy consultants. Created by [azvai.com](https://azvai.com).

> If you've ever found yourself pasting the same context into Claude session after session, regenerating the same chart code, or reaching for AI image generation when matplotlib would have done it for free — these skills are the architecture that fixes that. The math behind the savings is in [How Claude Code Skills Cut AI Energy Use](https://azvai.com/claude-code-skills-cut-ai-energy-use/).

## Skills

| Skill | What it does |
|---|---|
| [`article-images`](./article-images/) | Programmatic charts, stat cards, branded title images, and open-license stock photos for sustainability reports and research-led articles. Replaces AI image generation for structured visuals at ~97% less compute and energy. Pairs with research-writing-assistant. |
| [`research-writing-assistant`](./research-writing-assistant/) | End-to-end research and writing pipeline for sustainability and ESG publishers: brief, deep research, competitor analysis, outline planning, adversarial writer/editor draft, SEO meta. Pairs with article-images and gsc-audit. |
| [`gsc-audit`](./gsc-audit/) | Google Search Console audit framework for sustainability publishers and consultants. Striking-distance keywords, content decay, cannibalization, CTR optimization. Useful before writing (find targets) and after publishing (track shifts). |
| [`wordpress-publish`](./wordpress-publish/) | Multi-site WordPress REST API publisher for consultancies maintaining several brand or client sites. Featured image upload, category/tag resolution, draft or live publish. Natural endpoint for research-writing-assistant. |
| [`field-inspection-prep`](./field-inspection-prep/) | Prepare technical field inspections for sustainability certifications, subsidy reconciliations, and supplier audits. Locates approved-scope documents, reconciles invoices against approved scope per period, generates inspection checklists. |
| [`financial-model-audit`](./financial-model-audit/) | Audit and harden spreadsheet financial models — business plans, venture projections, grant budgets. Extracts every assumption into a sourced ledger with evidence grades, finds structural defects (double counting, broken totals), ranks assumptions by leverage weighted by weak evidence, builds scenarios. Writes it back into the client's own workbook. |
| [`sustainable-business-model`](./sustainable-business-model/) | Build and stress-test the financial model of a social or environmental enterprise, starting from whatever exists (deck, application, notes). Readable YAML spec instead of a spreadsheet, blended grant/earned/in-kind finance and impact ratios built in, answers "when do we stop needing grants". Interactive offline report + funder-ready Excel. Pairs with financial-model-audit. |

## Install a skill

Each skill is a self-contained directory. Drop it into your Claude Code skills folder:

```bash
# Project-scoped (recommended for skills tied to a specific project)
cp -r article-images <your-project>/.claude/skills/

# User-scoped (available across all your projects)
cp -r article-images ~/.claude/skills/
```

Each skill's own README has setup steps (env vars, dependencies, config).

## Customize for your brand

Most skills ship with a default brand profile or template. To make them yours:

1. **For `article-images`**: run the setup wizard to create a brand JSON. `python scripts/setup_brand.py` walks through colors, fonts, and attribution.
2. **For `research-writing-assistant`**: copy `references/brand-profile.template.md` to `references/brand-profile.md` and fill in your voice. Or paste a writing sample on first run; the skill builds a profile from it.
3. **For others**: see the per-skill README.

## License

MIT. Use, modify, and republish freely. Attribution to azvai.com is appreciated but not required.

## Background

These skills are extracted from [azvai.com](https://azvai.com)'s consulting workflow and sanitized for public use. The choice of which skills to publish, what to keep, and what to template was driven by the Article 2 piece [How Claude Code Skills Cut AI Energy Use](https://azvai.com/claude-code-skills-cut-ai-energy-use/) — the principle being that AI architecture choices have measurable energy and cost consequences, and reusable skills are one of the cleaner ways to keep those consequences low.

## Roadmap / requested skills

Shipped since v1: `financial-model-audit` and `sustainable-business-model` — the
business-case pair. One audits a spreadsheet model that exists; the other builds one
from whatever the founder has. Both ship with their own evals and synthetic fixtures,
so you can run the tests without a client's data.

Planned for v2:

- `csrd-prep` — CSRD reporting helper (ESRS standards, double materiality)
- `material-flow-analysis` — MFA workflow assistant
- `esg-data-review` — quality check for ESG / sustainability reports

Open an issue if there's a sustainability workflow you'd want as a skill.
