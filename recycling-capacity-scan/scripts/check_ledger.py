#!/usr/bin/env python3
"""Check a recycling-capacity scan ledger before anyone relies on it.

The ledger is a CSV with one row per claim (not per facility), so every
number and every "they accept X" carries its own source, date and verdict.

Usage:
    python check_ledger.py ledger.csv                 # rules only, offline
    python check_ledger.py ledger.csv --check-urls    # also fetch every source URL
    python check_ledger.py ledger.csv --as-of 2026-11-08 --max-age-months 24 --out report.md

Exit code 0 when no ERROR is found, 1 otherwise. Warnings never fail the run.
Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path

REQUIRED = ["facility_id", "facility", "field", "value", "source_url", "source_type",
            "source_date", "accessed", "verdict", "note"]
FIELDS = {"exists", "operating", "location", "process", "capacity", "polymers",
          "input_spec", "terms", "contact_route", "other"}
SOURCE_TYPES = {"company", "press_release", "register", "government", "eu", "public_body",
                "academic", "news", "trade_press", "aggregator", "model", "call"}
PRIMARY = {"company", "press_release", "register", "government", "eu", "public_body", "call"}
VERDICTS = {"confirmed", "wrong", "outdated", "unverifiable", "invented", "pending"}
CAPACITY_BASIS = ("input", "output", "nameplate", "collected", "planned")
# An "operating" row records the CURRENT status. A confirmed row that says the
# company has closed must drop it (first version of this script missed that case).
CLOSED = re.compile(r"\b(not operating|closed|liquidat|struck off|dissolved|ceased|insolven|bankrupt|"
                    r"radi[ée]e?|no longer|wound up|in administration)", re.I)


def parse_date(s: str) -> dt.date | None:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            d = dt.datetime.strptime(s, fmt).date()
            return d
        except ValueError:
            continue
    return None


def months_between(a: dt.date, b: dt.date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def _ssl_context():
    """Use certifi's CA bundle when installed. Some Python builds (seen on Windows)
    ship without a usable CA store, which makes every https URL look broken."""
    import ssl
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


SSL_CTX = None


def check_url(url: str, timeout: int = 20) -> str:
    global SSL_CTX
    if SSL_CTX is None:
        SSL_CTX = _ssl_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ledger-check)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if "CERTIFICATE" in str(reason).upper():
            return "SSL certificate problem"
        return f"network error ({type(reason).__name__})"
    except Exception as e:  # noqa: BLE001  (network errors of every kind are reported, not raised)
        return f"network error ({type(e).__name__})"


def url_finding(status: str) -> str:
    """'error' only when the page is really gone; bot blocks and network trouble are warnings."""
    if status.startswith(("2", "3")):
        return "ok"
    if status in {"404", "410"}:
        return "error"
    return "warning"


def run(path: Path, as_of: dt.date, max_age: int, urls: bool) -> tuple[list[str], list[str], dict]:
    errors: list[str] = []
    warns: list[str] = []
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
        if missing:
            return [f"ledger is missing columns: {', '.join(missing)}"], [], {}
        rows = list(reader)

    bad_shape = []
    for i, r in enumerate(rows, start=2):
        if r.get(None) or any(r.get(c) is None for c in REQUIRED):
            bad_shape.append(f"line {i}: wrong number of columns, put double quotes around any value that contains a comma")
    if bad_shape:
        return bad_shape, [], {}

    by_fac: dict[str, list[dict]] = defaultdict(list)
    url_cache: dict[str, str] = {}
    for i, r in enumerate(rows, start=2):  # line 1 is the header
        r = {k: (v or "").strip() for k, v in r.items()}
        r["_line"] = i
        loc = f"line {i} ({r['facility'] or r['facility_id']}, {r['field']})"
        by_fac[r["facility_id"]].append(r)

        if r["field"] not in FIELDS:
            errors.append(f"{loc}: unknown field '{r['field']}'")
        if r["source_type"] not in SOURCE_TYPES:
            errors.append(f"{loc}: unknown source_type '{r['source_type']}', use one of {', '.join(sorted(SOURCE_TYPES))}")
        if r["verdict"] not in VERDICTS:
            errors.append(f"{loc}: unknown verdict '{r['verdict']}'")
        if r["verdict"] == "confirmed":
            if not r["source_url"] and r["source_type"] != "call":
                errors.append(f"{loc}: confirmed without a source URL")
            if r["source_type"] == "model":
                errors.append(f"{loc}: a model answer cannot confirm a claim")
            if r["source_type"] == "aggregator":
                errors.append(f"{loc}: an aggregator alone cannot confirm a claim, find the primary source")
        sd = parse_date(r["source_date"])
        if r["verdict"] == "confirmed":
            if sd is None:
                errors.append(f"{loc}: confirmed claim has no source_date (YYYY, YYYY-MM or YYYY-MM-DD)")
            elif months_between(sd, as_of) > max_age:
                warns.append(f"{loc}: source is {months_between(sd, as_of)} months old, re-check or mark outdated")
        if not parse_date(r["accessed"]) and r["source_type"] != "model":
            errors.append(f"{loc}: no 'accessed' date")
        if r["field"] == "capacity" and r["verdict"] == "confirmed":
            text = (r["value"] + " " + r["note"]).lower()
            if not any(b in text for b in CAPACITY_BASIS):
                errors.append(f"{loc}: capacity without a basis, say input, output, nameplate, collected or planned")
            if "net" not in text and "all feedstock" not in text and "total" not in text:
                warns.append(f"{loc}: capacity does not say whether it is nets only or all feedstock")
        if r["field"] == "terms" and r["verdict"] == "confirmed" and r["source_type"] not in {"call", "company", "press_release"}:
            warns.append(f"{loc}: prices and gate fees are only reliable from the facility itself")
        if urls and r["source_url"].startswith("http"):
            if r["source_url"] not in url_cache:
                url_cache[r["source_url"]] = check_url(r["source_url"])
            status = url_cache[r["source_url"]]
            finding = url_finding(status)
            if finding == "error" and r["verdict"] == "confirmed":
                errors.append(f"{loc}: source URL returns {status}, find a live source or archive copy")
            elif finding != "ok":
                warns.append(f"{loc}: source URL returns {status} (check it in a browser)")

    summary: dict[str, dict] = {}
    for fid, claims in by_fac.items():
        name = claims[0]["facility"]
        verdict_of = {c["field"]: c["verdict"] for c in claims}
        exists = [c for c in claims if c["field"] == "exists"]
        operating = [c for c in claims if c["field"] == "operating"]
        if not exists:
            errors.append(f"{name}: no 'exists' claim, every facility needs one")
        if any(c["verdict"] == "invented" for c in exists):
            status = "DROP (invented)"
        elif any(c["verdict"] in {"wrong", "outdated"} for c in operating) or any(
                c["verdict"] == "confirmed" and CLOSED.search(c["value"]) for c in operating):
            status = "DROP (not operating)"
        elif any(c["verdict"] == "wrong" and c["field"] in {"process", "polymers"} for c in claims):
            status = "RECHECK FIT (a process or polymer claim was wrong)"
        elif not any(c["verdict"] == "confirmed" and c["source_type"] in PRIMARY for c in exists):
            status = "UNVERIFIED"
        elif not any(c["verdict"] == "confirmed" for c in operating):
            status = "EXISTS, operation not confirmed"
        else:
            confirmed = sum(1 for c in claims if c["verdict"] == "confirmed")
            status = f"VERIFIED ({confirmed}/{len(claims)} claims confirmed)"
        if "input_spec" not in verdict_of or verdict_of.get("input_spec") != "confirmed":
            if status.startswith("VERIFIED"):
                warns.append(f"{name}: verified, but its input spec is not confirmed, ask them")
        summary[fid] = {"facility": name, "status": status,
                        "counts": {v: sum(1 for c in claims if c["verdict"] == v) for v in VERDICTS}}
    return errors, warns, summary


def render(path: Path, errors: list[str], warns: list[str], summary: dict, as_of: dt.date) -> str:
    out = [f"# Ledger check: {path.name}", "", f"As of {as_of.isoformat()}.", "",
           "| Facility | Status | confirmed | wrong | outdated | unverifiable | invented | pending |",
           "|---|---|---|---|---|---|---|---|"]
    for s in sorted(summary.values(), key=lambda x: x["status"]):
        c = s["counts"]
        out.append(f"| {s['facility']} | {s['status']} | {c['confirmed']} | {c['wrong']} | {c['outdated']} | "
                   f"{c['unverifiable']} | {c['invented']} | {c['pending']} |")
    out += ["", f"## Errors ({len(errors)})"] + [f"- {e}" for e in errors]
    out += ["", f"## Warnings ({len(warns)})"] + [f"- {w}" for w in warns]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ledger", type=Path)
    ap.add_argument("--as-of", default=dt.date.today().isoformat())
    ap.add_argument("--max-age-months", type=int, default=24)
    ap.add_argument("--check-urls", action="store_true")
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    as_of = parse_date(a.as_of) or dt.date.today()
    errors, warns, summary = run(a.ledger, as_of, a.max_age_months, a.check_urls)
    report = render(a.ledger, errors, warns, summary, as_of)
    if a.out:
        a.out.write_text(report, encoding="utf-8")
    sys.stdout.write(report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
