"""Search free-license stock photos and download with proper attribution.

Supports Unsplash (preferred) and Pexels (fallback). Both have generous free APIs.

Usage:
    python stock.py --query "wind turbines at dusk" --out ./images/ --count 3 [--orientation landscape]
    python stock.py --query "..." --source pexels   # force a specific source
    python stock.py --query "..." --source auto     # default: try Unsplash, fall back to Pexels

Outputs:
    - <slug>-1.jpg, <slug>-2.jpg, ... in --out
    - <slug>.attribution.md  with markdown attribution blocks per image

Environment:
    UNSPLASH_ACCESS_KEY  — Unsplash API key (https://unsplash.com/developers)
    PEXELS_API_KEY        — Pexels API key (https://www.pexels.com/api/)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv
    here = Path(__file__).resolve()
    for parent in here.parents:
        env_path = parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass

UNSPLASH_API = "https://api.unsplash.com"
PEXELS_API = "https://api.pexels.com/v1"
APP_NAME = "article-images"


def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:60]


# ---------- normalized photo dict ----------
# Each search function returns dicts of the form:
#   {
#       "img_url": str,             # direct image URL to download
#       "page_url": str,            # photo's page on the host
#       "author_name": str,
#       "author_url": str,
#       "description": str | None,
#       "source": "unsplash" | "pexels",
#       "license_note": str,
#       "raw": dict,                # original API response object
#   }


def search_unsplash(query: str, count: int, orientation: str) -> list[dict]:
    key = os.environ.get("UNSPLASH_ACCESS_KEY")
    if not key:
        return []
    params = {
        "query": query,
        "per_page": min(count, 30),
        "orientation": orientation,
        "content_filter": "high",
    }
    headers = {"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}
    r = requests.get(f"{UNSPLASH_API}/search/photos", params=params, headers=headers, timeout=30)
    r.raise_for_status()
    photos = r.json().get("results", [])[:count]
    return [
        {
            "img_url": p["urls"]["regular"],
            "page_url": p["links"]["html"],
            "author_name": p["user"]["name"],
            "author_url": p["user"]["links"]["html"],
            "description": p.get("description") or p.get("alt_description"),
            "source": "unsplash",
            "license_note": "Unsplash License (free for commercial and editorial use)",
            "raw": p,
            "_download_trigger": p["links"].get("download_location"),
        }
        for p in photos
    ]


def search_pexels(query: str, count: int, orientation: str) -> list[dict]:
    key = os.environ.get("PEXELS_API_KEY")
    if not key:
        return []
    pexels_orientation = {
        "landscape": "landscape",
        "portrait": "portrait",
        "squarish": "square",
    }.get(orientation, "landscape")
    params = {
        "query": query,
        "per_page": min(count, 80),
        "orientation": pexels_orientation,
    }
    headers = {"Authorization": key}
    r = requests.get(f"{PEXELS_API}/search", params=params, headers=headers, timeout=30)
    r.raise_for_status()
    photos = r.json().get("photos", [])[:count]
    return [
        {
            "img_url": p["src"]["large2x"] if "large2x" in p["src"] else p["src"]["large"],
            "page_url": p["url"],
            "author_name": p["photographer"],
            "author_url": p.get("photographer_url") or "https://www.pexels.com",
            "description": p.get("alt"),
            "source": "pexels",
            "license_note": "Pexels License (free for commercial and editorial use)",
            "raw": p,
            "_download_trigger": None,
        }
        for p in photos
    ]


def search(query: str, count: int, orientation: str, source: str = "auto") -> list[dict]:
    """Search the configured stock source. With 'auto', tries Unsplash then Pexels."""
    if source == "unsplash":
        results = search_unsplash(query, count, orientation)
        if not results and not os.environ.get("UNSPLASH_ACCESS_KEY"):
            sys.exit("UNSPLASH_ACCESS_KEY not set. Set it in .env or use --source pexels.")
        return results

    if source == "pexels":
        results = search_pexels(query, count, orientation)
        if not results and not os.environ.get("PEXELS_API_KEY"):
            sys.exit("PEXELS_API_KEY not set. Set it in .env or use --source unsplash.")
        return results

    # auto: try Unsplash first, fall back to Pexels if no results or no key
    has_unsplash = bool(os.environ.get("UNSPLASH_ACCESS_KEY"))
    has_pexels = bool(os.environ.get("PEXELS_API_KEY"))
    if not has_unsplash and not has_pexels:
        sys.exit("Neither UNSPLASH_ACCESS_KEY nor PEXELS_API_KEY is set. Configure at least one in .env.")

    if has_unsplash:
        results = search_unsplash(query, count, orientation)
        if results:
            return results
        if has_pexels:
            print("[stock] Unsplash returned no results, falling back to Pexels...", file=sys.stderr)
    if has_pexels:
        return search_pexels(query, count, orientation)
    return []


def download(photo: dict, out_path: Path) -> None:
    r = requests.get(photo["img_url"], timeout=60)
    r.raise_for_status()
    out_path.write_bytes(r.content)

    # Trigger the Unsplash download endpoint per their API policy (Pexels has no equivalent requirement)
    if photo["source"] == "unsplash" and photo.get("_download_trigger"):
        key = os.environ.get("UNSPLASH_ACCESS_KEY")
        if key:
            headers = {"Authorization": f"Client-ID {key}", "Accept-Version": "v1"}
            try:
                requests.get(photo["_download_trigger"], headers=headers, timeout=30)
            except Exception as e:
                print(f"[stock] warn: could not trigger Unsplash download endpoint: {e}", file=sys.stderr)


def attribution_md(photo: dict, local_filename: str) -> str:
    name = photo["author_name"]
    user_url = photo["author_url"]
    photo_url = photo["page_url"]
    desc = photo["description"] or ""

    if photo["source"] == "unsplash":
        utm = f"?utm_source={APP_NAME}&utm_medium=referral"
        attribution = f"[{name}]({user_url}{utm}) on [Unsplash]({photo_url}{utm})"
    else:
        attribution = f"[{name}]({user_url}) on [Pexels]({photo_url})"

    lines = [
        f"### {local_filename}",
        f"- **Photo by**: {attribution}",
    ]
    if desc:
        lines.append(f"- **Description**: {desc}")
    lines.append(f"- **Photo URL**: {photo_url}")
    lines.append(f"- **Author URL**: {user_url}")
    lines.append(f"- **License**: {photo['license_note']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--out", default=".", help="Output directory")
    ap.add_argument("--count", type=int, default=3)
    ap.add_argument("--orientation", default="landscape",
                    choices=["landscape", "portrait", "squarish"])
    ap.add_argument("--source", default="auto",
                    choices=["auto", "unsplash", "pexels"],
                    help="Which stock provider to query (default: auto = try Unsplash, fall back to Pexels)")
    ap.add_argument("--name-prefix", default=None,
                    help="Filename prefix (default: derived from query)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = args.name_prefix or slugify(args.query)

    photos = search(args.query, args.count, args.orientation, source=args.source)
    if not photos:
        sys.exit(f"No results for: {args.query}")

    attribution_blocks = []
    saved = []
    for i, photo in enumerate(photos, 1):
        filename = f"{prefix}-{i}.jpg" if len(photos) > 1 else f"{prefix}.jpg"
        path = out_dir / filename
        download(photo, path)
        saved.append(str(path))
        attribution_blocks.append(attribution_md(photo, filename))
        print(f"Saved {path} (source: {photo['source']})")

    sources_used = sorted({p["source"] for p in photos})
    attribution_path = out_dir / f"{prefix}.attribution.md"
    attribution_path.write_text(
        f"# Image Attribution\n\nQuery: `{args.query}`\n"
        f"Source(s): {', '.join(sources_used)}\n\n" +
        "\n".join(attribution_blocks),
        encoding="utf-8",
    )
    print(f"Saved {attribution_path}")

    print("---SUMMARY---")
    print(json.dumps({
        "files": saved,
        "attribution": str(attribution_path),
        "count": len(saved),
        "sources_used": sources_used,
    }))


if __name__ == "__main__":
    main()
