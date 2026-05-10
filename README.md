# Claude Code skills for sustainability consulting workflows

A growing hub of [Claude Code](https://claude.com/claude-code) skills built for sustainability and circular economy consultants. Created by [azvai.com](https://azvai.com).

> If you've ever found yourself pasting the same context into Claude session after session, regenerating the same chart code, or reaching for AI image generation when matplotlib would have done it for free — these skills are the architecture that fixes that. The math behind the savings is in [How Claude Code Skills Cut AI Energy Use](https://azvai.com/claude-code-skills-cut-ai-energy-use/).

## Skills

| Skill | What it does |
|---|---|
| [`article-images`](./article-images/) | Programmatic charts, stat cards, branded title images, and stock photo search. Replaces AI image generation for structured visuals at ~97% less compute and cost. |
| [`blog-post-writer`](./blog-post-writer/) | End-to-end SEO content pipeline: research, competitor analysis, outline planning, adversarial writer/editor draft, meta generation. Built for sustainability content but works for any domain. |
| [`gsc-audit`](./gsc-audit/) | Comprehensive Google Search Console audit framework. Striking-distance keywords, content decay, cannibalization, CTR optimization, brand vs non-brand health. |
| [`wordpress-publish`](./wordpress-publish/) | Publish articles to WordPress via REST API. Multi-site support. Natural follow-up to blog-post-writer. |
| [`field-inspection-prep`](./field-inspection-prep/) | Prepare technical field inspections for sustainability certifications, subsidy reconciliations, supplier audits. Locates documents, reconciles invoices against approved scopes, generates inspection checklists. |

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
2. **For `blog-post-writer`**: copy `references/brand-profile.template.md` to `references/brand-profile.md` and fill in your voice. Or paste a writing sample on first run; the skill builds a profile from it.
3. **For others**: see the per-skill README.

## License

MIT. Use, modify, and republish freely. Attribution to azvai.com is appreciated but not required.

## Background

These skills are extracted from [azvai.com](https://azvai.com)'s consulting workflow and sanitized for public use. The choice of which skills to publish, what to keep, and what to template was driven by the Article 2 piece [How Claude Code Skills Cut AI Energy Use](https://azvai.com/claude-code-skills-cut-ai-energy-use/) — the principle being that AI architecture choices have measurable energy and cost consequences, and reusable skills are one of the cleaner ways to keep those consequences low.

## Roadmap / requested skills

Planned for v2:

- `csrd-prep` — CSRD reporting helper (ESRS standards, double materiality)
- `material-flow-analysis` — MFA workflow assistant
- `esg-data-review` — quality check for ESG / sustainability reports

Open an issue if there's a sustainability workflow you'd want as a skill.
