#!/usr/bin/env python3
"""WordPress REST API client for the wordpress-publish skill.

Multi-site credentials. Add per-site env vars to .env:

    WP_<SLUG>_URL=https://your-site.com
    WP_<SLUG>_USER=your-username
    WP_<SLUG>_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

    WP_<SLUG>_URL=https://your-site.com
    WP_<SLUG>_USER=your-username
    WP_<SLUG>_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

    WP_<SLUG>_URL=https://your-site.com
    WP_<SLUG>_USER=your-username
    WP_<SLUG>_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx

Then pick a site per call via --site:

    python publish.py --site azvai create --title "..." --content-file ...
    python publish.py --site ecomm list

Site name is case-insensitive; underscores allowed.

Legacy fallback: if no --site is given and WP_URL/WP_USER/WP_APP_PASSWORD are set
(no per-site prefix), those are used. Existing single-site setups keep working.
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests


def load_env() -> None:
    """Load .env from project root. Walks up from CWD until found."""
    here = Path.cwd().resolve()
    for parent in [here, *here.parents]:
        candidate = parent / ".env"
        if candidate.exists():
            _read_env_file(candidate)
            return
    script_root = Path(__file__).resolve().parents[2]
    env_file = script_root / ".env"
    if env_file.exists():
        _read_env_file(env_file)


def _read_env_file(path: Path) -> None:
    """Read a .env file. Later occurrences of the same key OVERRIDE earlier ones
    (matches dotenv standard, opposite of os.environ.setdefault).
    """
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ[key.strip()] = value.strip()


def list_configured_sites() -> list[str]:
    """Return slugs of sites with all three env vars set (e.g. ['azvai', 'ecomm'])."""
    load_env()
    sites: dict[str, dict[str, str]] = {}
    for k, v in os.environ.items():
        m = re.match(r"^WP_([A-Z0-9_]+)_(URL|USER|APP_PASSWORD)$", k)
        if m and v:
            slug = m.group(1).lower()
            sites.setdefault(slug, {})[m.group(2)] = v
    return sorted(s for s, fields in sites.items() if {"URL", "USER", "APP_PASSWORD"} <= fields.keys())


def creds(site: str | None = None) -> tuple[str, dict[str, str]]:
    """Return (base_url, auth_headers) for the given site slug.

    If site is None, falls back to legacy WP_URL/WP_USER/WP_APP_PASSWORD.
    """
    load_env()
    if site:
        slug = site.upper().replace("-", "_")
        url = os.environ.get(f"WP_{slug}_URL", "").rstrip("/")
        user = os.environ.get(f"WP_{slug}_USER", "")
        app_pw = os.environ.get(f"WP_{slug}_APP_PASSWORD", "")
        prefix = f"WP_{slug}_"
    else:
        url = os.environ.get("WP_URL", "").rstrip("/")
        user = os.environ.get("WP_USER", "")
        app_pw = os.environ.get("WP_APP_PASSWORD", "")
        prefix = "WP_"

    missing = [
        f"{prefix}{k}"
        for k, v in {"URL": url, "USER": user, "APP_PASSWORD": app_pw}.items()
        if not v
    ]
    if missing:
        configured = list_configured_sites()
        msg = f"Missing env vars: {', '.join(missing)}\n"
        if configured:
            msg += f"Configured sites: {', '.join(configured)}\n"
            msg += "Use --site <slug> to pick one, or set the legacy WP_URL/WP_USER/WP_APP_PASSWORD vars.\n"
        else:
            msg += "No per-site WP_*_URL credentials found. See publish.py docstring.\n"
        sys.stderr.write(msg)
        sys.exit(2)

    token = base64.b64encode(f"{user}:{app_pw}".encode()).decode()
    return url, {"Authorization": f"Basic {token}"}


def api(site: str | None, path: str) -> str:
    url, _ = creds(site)
    return urljoin(url + "/", f"wp-json/wp/v2/{path.lstrip('/')}")


def request(site: str | None, method: str, path: str, **kwargs):
    _, headers = creds(site)
    merged = {**headers, **kwargs.pop("headers", {})}
    r = requests.request(method, api(site, path), headers=merged, timeout=60, **kwargs)
    if not r.ok:
        sys.stderr.write(f"[{r.status_code}] {method} {path}\n{r.text}\n")
        sys.exit(1)
    return r.json()


def read_content(args) -> str:
    if args.content_file:
        return Path(args.content_file).read_text(encoding="utf-8")
    if args.content:
        return args.content
    sys.stderr.write("Provide --content or --content-file\n")
    sys.exit(2)


def split_csv(value):
    if not value:
        return None
    return [int(x) for x in value.split(",") if x.strip()]


def cmd_create(args):
    payload = {
        "title": args.title,
        "content": read_content(args),
        "status": args.status,
    }
    if args.excerpt:
        payload["excerpt"] = args.excerpt
    if args.slug:
        payload["slug"] = args.slug
    if args.featured_media:
        payload["featured_media"] = args.featured_media
    cats = split_csv(args.categories)
    if cats:
        payload["categories"] = cats
    tags = split_csv(args.tags)
    if tags:
        payload["tags"] = tags
    result = request(args.site, "POST", "posts", json=payload)
    print(json.dumps({"id": result["id"], "status": result["status"], "link": result["link"]}, indent=2))


def cmd_update(args):
    payload = {}
    if args.title is not None:
        payload["title"] = args.title
    if args.content or args.content_file:
        payload["content"] = read_content(args)
    if args.status:
        payload["status"] = args.status
    if args.excerpt is not None:
        payload["excerpt"] = args.excerpt
    if args.slug is not None:
        payload["slug"] = args.slug
    if args.featured_media is not None:
        payload["featured_media"] = args.featured_media
    cats = split_csv(args.categories)
    if cats is not None:
        payload["categories"] = cats
    tags = split_csv(args.tags)
    if tags is not None:
        payload["tags"] = tags
    if not payload:
        sys.stderr.write("Nothing to update.\n")
        sys.exit(2)
    result = request(args.site, "POST", f"posts/{args.id}", json=payload)
    print(json.dumps({"id": result["id"], "status": result["status"], "link": result["link"]}, indent=2))


def cmd_upload_media(args):
    _, headers = creds(args.site)
    path = Path(args.file)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    upload_headers = {
        **headers,
        "Content-Disposition": f'attachment; filename="{path.name}"',
        "Content-Type": mime,
    }
    with path.open("rb") as fh:
        r = requests.post(api(args.site, "media"), headers=upload_headers, data=fh.read(), timeout=120)
    if not r.ok:
        sys.stderr.write(f"[{r.status_code}] upload\n{r.text}\n")
        sys.exit(1)
    data = r.json()
    if args.alt:
        request(args.site, "POST", f"media/{data['id']}", json={"alt_text": args.alt})
    print(json.dumps({"id": data["id"], "source_url": data["source_url"]}, indent=2))


def resolve_or_create(site, endpoint, names):
    ids = []
    for name in names:
        name = name.strip()
        if not name:
            continue
        existing = request(site, "GET", f"{endpoint}?search={requests.utils.quote(name)}")
        match = next((t for t in existing if t["name"].lower() == name.lower()), None)
        if match:
            ids.append(match["id"])
        else:
            created = request(site, "POST", endpoint, json={"name": name})
            ids.append(created["id"])
    return ids


def cmd_resolve_terms(args):
    out = {}
    if args.categories:
        out["categories"] = resolve_or_create(args.site, "categories", args.categories.split(","))
    if args.tags:
        out["tags"] = resolve_or_create(args.site, "tags", args.tags.split(","))
    print(json.dumps(out, indent=2))


def cmd_list(args):
    posts = request(args.site, "GET", f"posts?per_page={args.per_page}&status=any&context=edit")
    summary = [{"id": p["id"], "status": p["status"], "title": p["title"]["rendered"], "link": p["link"]} for p in posts]
    print(json.dumps(summary, indent=2))


def cmd_get(args):
    post = request(args.site, "GET", f"posts/{args.id}?context=edit")
    print(json.dumps({
        "id": post["id"],
        "status": post["status"],
        "title": post["title"]["rendered"],
        "slug": post["slug"],
        "link": post["link"],
        "categories": post["categories"],
        "tags": post["tags"],
        "featured_media": post["featured_media"],
    }, indent=2))


def cmd_list_sites(_args):
    sites = list_configured_sites()
    if not sites:
        print("No sites configured. Set WP_<SLUG>_URL, WP_<SLUG>_USER, WP_<SLUG>_APP_PASSWORD in .env.")
        return
    load_env()
    rows = []
    for slug in sites:
        url = os.environ.get(f"WP_{slug.upper()}_URL", "")
        user = os.environ.get(f"WP_{slug.upper()}_USER", "")
        rows.append({"site": slug, "url": url, "user": user})
    print(json.dumps(rows, indent=2))


def build_parser():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--site",
        help="Site slug (e.g. azvai, quecafe, ecomm). Maps to WP_<SLUG>_URL/USER/APP_PASSWORD env vars. "
             "If omitted, falls back to legacy WP_URL/WP_USER/WP_APP_PASSWORD.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    c = sub.add_parser("create")
    c.add_argument("--title", required=True)
    c.add_argument("--content")
    c.add_argument("--content-file")
    c.add_argument("--status", default="draft", choices=["draft", "publish", "pending", "private", "future"])
    c.add_argument("--excerpt")
    c.add_argument("--slug")
    c.add_argument("--featured-media", type=int)
    c.add_argument("--categories", help="comma-separated category IDs")
    c.add_argument("--tags", help="comma-separated tag IDs")
    c.set_defaults(func=cmd_create)

    u = sub.add_parser("update")
    u.add_argument("--id", type=int, required=True)
    u.add_argument("--title")
    u.add_argument("--content")
    u.add_argument("--content-file")
    u.add_argument("--status", choices=["draft", "publish", "pending", "private", "future"])
    u.add_argument("--excerpt")
    u.add_argument("--slug")
    u.add_argument("--featured-media", type=int)
    u.add_argument("--categories")
    u.add_argument("--tags")
    u.set_defaults(func=cmd_update)

    m = sub.add_parser("upload-media")
    m.add_argument("--file", required=True)
    m.add_argument("--alt")
    m.set_defaults(func=cmd_upload_media)

    r = sub.add_parser("resolve-terms")
    r.add_argument("--categories", help="comma-separated category names")
    r.add_argument("--tags", help="comma-separated tag names")
    r.set_defaults(func=cmd_resolve_terms)

    l = sub.add_parser("list")
    l.add_argument("--per-page", type=int, default=10)
    l.set_defaults(func=cmd_list)

    g = sub.add_parser("get")
    g.add_argument("--id", type=int, required=True)
    g.set_defaults(func=cmd_get)

    s = sub.add_parser("list-sites", help="Show configured sites and their URL/user")
    s.set_defaults(func=cmd_list_sites)

    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    args.func(args)
