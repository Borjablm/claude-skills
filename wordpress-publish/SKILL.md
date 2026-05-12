---
name: wordpress-publish
description: Publish articles to a WordPress site via the REST API. Multi-site (azvai, quecafe, ecomm, ai-tutor, notegpt). Creates posts as drafts or published, uploads featured images, sets categories/tags. Use when the user asks to publish, push, upload, or send an article to WordPress. Natural follow-up to research-writing-assistant Stage 5.
license: MIT
requires_secrets:
  - WP_<SLUG>_URL          # one set per site
  - WP_<SLUG>_USER
  - WP_<SLUG>_APP_PASSWORD
---

# WordPress Publish

You publish articles to a configured WordPress site using the REST API. Multi-site setup — pick the target site with `--site <slug>` on every call.

## Configured sites

Run `python scripts/publish.py list-sites` to see what's set up. Each site is identified by a lowercase slug (e.g. `azvai`, `quecafe`, `ecomm`). Slug is derived from the env vars `WP_<UPPERCASE_SLUG>_URL`, `_USER`, `_APP_PASSWORD`.

The research-writing-assistant brand profile slug should match the site slug (so `azvai` brand → `--site azvai`). For ecomm.design the convention is `ecomm`.

## Inputs

The user points you at an article. Typically one of:
- A directory from `research-writing-assistant` containing `article.html` + `meta.json` + `titles.md`
- A single HTML or Markdown file
- An explicit title + body

Ask if any of these are missing: **target site** (slug), **title**, **status** (`draft` or `publish`, default `draft`), **featured image** (optional path), **categories/tags** (optional names).

If the working dir is from research-writing-assistant, infer the site from `brief.json.brand_profile` (which equals the brand slug, which equals the site slug). Confirm with the user before publishing.

## Workflow

1. **Resolve site.** Run `scripts/publish.py list-sites` if unclear. Confirm slug with user.
2. **Resolve source.** If directory: read `article.html` as content, pick title from `titles.md` (the one marked recommended — ask if ambiguous), read meta description from `meta.json`.
3. **Confirm.** Show the user: site URL, title, status, featured image (if any), categories, tags. Wait for approval.
4. **Upload featured image** (if provided): run `scripts/publish.py --site <slug> upload-media --file <path>`. Capture the returned media ID.
5. **Resolve taxonomy IDs** (if category/tag names given): run `scripts/publish.py --site <slug> resolve-terms --categories "A,B" --tags "X,Y"`. Script creates any missing terms.
6. **Create post.** Run `scripts/publish.py --site <slug> create` with the resolved inputs. Script writes the response to stdout as JSON.
7. **Report back.** Show the user the post ID, edit URL (`{site_url}/wp-admin/post.php?post=<id>&action=edit`) and preview URL.

## Updating an existing post

If the user asks to update a post they previously published, use `scripts/publish.py --site <slug> update --id <post_id>` with whichever fields changed. Do not re-upload media unless the image itself changed.

## Rules

- **Always pass `--site`.** The legacy single-site fallback (`WP_URL`/`WP_USER`/`WP_APP_PASSWORD` without prefix) still works for backwards compat, but for multi-site setups always pass an explicit slug to avoid publishing to the wrong site.
- **Default to draft.** Only `--status publish` when the user explicitly says "publish live" / "publish it" / "go live".
- **Never publish without showing the user the final title + meta description first.**
- **Strip `<html>/<head>/<body>` wrappers** if present before sending — WP expects a content fragment (see `research-writing-assistant/references/wordpress-output.md`).
- **Preserve the `<style>` block** if the article uses per-article CSS mode.

## Script reference

All commands below read credentials from the project `.env` file. The `--site` flag goes BEFORE the subcommand.

```bash
# Discover what's configured
python scripts/publish.py list-sites

# Per-site operations
python scripts/publish.py --site azvai create \
  --title "Post title" \
  --content-file path/to/article.html \
  --status draft \
  --excerpt "Meta description here" \
  --slug "post-slug" \
  --featured-media 123 \
  --categories 5,12 \
  --tags 7,8

python scripts/publish.py --site ecomm update --id 456 --status publish

python scripts/publish.py --site quecafe upload-media --file path/to/image.jpg --alt "Alt text"

python scripts/publish.py --site azvai resolve-terms --categories "SEO,Guides" --tags "beginner"

python scripts/publish.py --site ecomm list --per-page 10
python scripts/publish.py --site azvai get --id 456
```

All commands exit non-zero on API error and print the WP error body to stderr.

## Adding a new site

1. Generate a WordPress Application Password: `Users → Profile → Application Passwords` on the WP admin
2. Add three lines to `.env`:
   ```
   WP_<SLUG>_URL=https://example.com
   WP_<SLUG>_USER=username
   WP_<SLUG>_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
   ```
3. Confirm with `python scripts/publish.py list-sites`
4. (If the article-images skill needs it) create a matching brand profile in `.claude/skills/article-images/brands/<slug>.json`
