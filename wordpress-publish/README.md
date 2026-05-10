# wordpress-publish

Claude Code skill that publishes articles to WordPress via the REST API.

## Install

1. Copy the skill into your Claude Code skills directory:
   ```bash
   cp -r wordpress-publish .claude/skills/
   ```
2. Install the Python dependency (once):
   ```bash
   pip install requests
   ```
3. Add credentials to `.env` at the project root:
   ```
   WP_URL=https://your-site.com
   WP_USER=your-wp-username
   WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
   ```

## Generating an Application Password

In WordPress admin: **Users → Profile → Application Passwords**. Give it a name like "Claude Code" and copy the generated password (spaces are fine, keep them). This is NOT your login password — it's a revocable credential scoped to REST API access.

The user calling the API must have the `edit_posts` capability (Author role or above).

## Smoke test

From the project root, after setting `.env`:

```bash
python wordpress-publish/scripts/publish.py list --per-page 3
```

You should get back JSON with your three most recent posts.
