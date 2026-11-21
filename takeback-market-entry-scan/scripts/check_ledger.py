#!/usr/bin/env python3
"""Check a take-back market-entry scan ledger (rules or partners) before anyone relies on it.

Two ledgers, one row per claim:
  rules.csv     every legal or regulatory claim, tied to the instrument that makes it
  partners.csv  every claim about an organisation (exists, operating, handles the material, terms)

The kind is detected from the header.

Usage:
    python check_ledger.py rules.csv --as-of 2026-11-21 --out rules-report.md
    python check_ledger.py partners.csv --check-urls --out partners-report.md

Exit code 0 when no ERROR is found, 1 otherwise. Warnings never fail the run.
Standard library only (certifi is used for --check-urls when installed).
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

RULE_COLS = ["rule_id", "jurisdiction", "topic", "claim", "instrument", "provision", "source_url",
             "source_type", "in_force_from", "accessed", "verdict", "note"]
PARTNER_COLS = ["org_id", "org", "field", "value", "source_url", "source_type", "source_date",
                "accessed", "verdict", "note"]

TOPICS = {"waste_status", "classification", "epr", "levy", "permit", "shipment", "procurement",
          "product_law", "other"}
RULE_SOURCES = {"legislation", "official_journal", "regulator_guidance", "government", "court",
                "secondary", "model", "call"}
LAW_SOURCES = {"legislation", "official_journal", "court"}

FIELDS = {"exists", "operating", "location", "role", "material", "terms", "permit", "contact_route",
          "claim_check", "other"}
PARTNER_SOURCES = {"company", "press_release", "register", "government", "eu", "public_body",
                   "news", "trade_press", "directory", "social", "aggregator", "model", "call",
                   "other_secondary"}
PRIMARY = {"company", "press_release", "register", "government", "eu", "public_body", "call"}

VERDICTS = {"confirmed", "wrong", "outdated", "unverifiable", "invented", "pending"}
MONEY = re.compile(r"(€|£|\$|\bEUR\b|\bGBP\b|per tonne|/t\b|\bfee\b|\blevy\b|\btax\b)", re.I)
CLOSED = re.compile(r"\b(not operating|closed|liquidat|struck off|dissolved|ceased|insolven|bankrupt|"
                    r"no longer|wound up|in administration)", re.I)
AS_MADE = re.compile(r"/(made|enacted)(/|$)|as made|as enacted", re.I)
# The note must say the amendments were looked at, not merely that they exist.
AMEND_CHECKED = re.compile(r"amended by|amendments? (checked|read)|revised version|consolidated|"
                           r"no later amendment found", re.I)
CONTENTS = re.compile(r"/contents/?$", re.I)


def parse_date(s: str) -> dt.date | None:
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def months_between(a: dt.date, b: dt.date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


_SSL = None


def check_url(url: str, timeout: int = 20) -> str:
    global _SSL
    if _SSL is None:
        import ssl
        try:
            import certifi  # type: ignore
            _SSL = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            _SSL = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (ledger-check)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_SSL) as r:
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except Exception as e:  # noqa: BLE001  network trouble is reported, not raised
        return f"network error ({type(e).__name__})"


def read(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        rows = list(reader)
    if all(c in cols for c in RULE_COLS):
        kind, req = "rules", RULE_COLS
    elif all(c in cols for c in PARTNER_COLS):
        kind, req = "partners", PARTNER_COLS
    else:
        return None, [], [f"header matches neither ledger. Rules need: {', '.join(RULE_COLS)}. "
                          f"Partners need: {', '.join(PARTNER_COLS)}"]
    bad = [f"line {i}: wrong number of columns, put double quotes around any value that contains a comma"
           for i, r in enumerate(rows, start=2) if r.get(None) or any(r.get(c) is None for c in req)]
    if bad:
        return kind, [], bad
    return kind, [{k: (v or "").strip() for k, v in r.items() if k} for r in rows], []


def url_checks(rows, loc_of, errors, warns):
    cache: dict[str, str] = {}
    for r in rows:
        u = r["source_url"]
        if not u.startswith("http"):
            continue
        status = cache.setdefault(u, check_url(u))
        if status in {"404", "410"} and r["verdict"] == "confirmed":
            errors.append(f"{loc_of(r)}: source URL returns {status}, find a live source")
        elif not status.startswith(("2", "3")):
            warns.append(f"{loc_of(r)}: source URL returns {status} (check it in a browser)")


def check_rules(rows, as_of, urls):
    errors, warns = [], []

    def loc(r):
        return f"line {r['_line']} ({r['rule_id']}, {r['jurisdiction']})"

    for i, r in enumerate(rows, start=2):
        r["_line"] = i
        if r["topic"] not in TOPICS:
            errors.append(f"{loc(r)}: unknown topic '{r['topic']}', use one of {', '.join(sorted(TOPICS))}")
        if r["source_type"] not in RULE_SOURCES:
            errors.append(f"{loc(r)}: unknown source_type '{r['source_type']}', use one of {', '.join(sorted(RULE_SOURCES))}")
        if r["verdict"] not in VERDICTS:
            errors.append(f"{loc(r)}: unknown verdict '{r['verdict']}'")
        if not parse_date(r["accessed"]):
            errors.append(f"{loc(r)}: no 'accessed' date")
        if r["verdict"] != "confirmed":
            continue
        st = r["source_type"]
        if st in {"model", "secondary"}:
            errors.append(f"{loc(r)}: a {st} source cannot confirm a legal claim, read the instrument")
        if not r["instrument"]:
            errors.append(f"{loc(r)}: confirmed rule names no instrument")
        if st in LAW_SOURCES and not r["provision"]:
            warns.append(f"{loc(r)}: no article, regulation, section or schedule given")
        if st in {"regulator_guidance", "government"}:
            warns.append(f"{loc(r)}: confirmed from guidance only; guidance pages can lag the law, "
                         f"check the instrument itself")
        if st in LAW_SOURCES and AS_MADE.search(r["source_url"] + " " + r["note"]) and \
                not AMEND_CHECKED.search(r["note"]):
            warns.append(f"{loc(r)}: read from the text as made; check later amending instruments "
                         f"or a revised version, and say so in the note")
        if st in LAW_SOURCES and CONTENTS.search(r["source_url"]):
            warns.append(f"{loc(r)}: cites a contents page; link the provision you read, or grade it pending")
        if MONEY.search(r["claim"]):
            if not parse_date(r["in_force_from"]):
                errors.append(f"{loc(r)}: a rate, fee or levy needs the date it applies from (in_force_from)")
        d = parse_date(r["in_force_from"])
        if d and d > as_of:
            warns.append(f"{loc(r)}: applies from {d.isoformat()}, after the scan date; report it as future")
    if urls:
        url_checks(rows, loc, errors, warns)

    summary = defaultdict(lambda: {v: 0 for v in VERDICTS})
    for r in rows:
        if r["verdict"] in VERDICTS:
            summary[(r["jurisdiction"], r["topic"])][r["verdict"]] += 1
    return errors, warns, summary


def check_partners(rows, as_of, urls, max_age):
    errors, warns = [], []
    by_org = defaultdict(list)

    def loc(r):
        return f"line {r['_line']} ({r['org'] or r['org_id']}, {r['field']})"

    for i, r in enumerate(rows, start=2):
        r["_line"] = i
        by_org[r["org_id"]].append(r)
        if r["field"] not in FIELDS:
            errors.append(f"{loc(r)}: unknown field '{r['field']}', use one of {', '.join(sorted(FIELDS))}")
        if r["source_type"] not in PARTNER_SOURCES:
            errors.append(f"{loc(r)}: unknown source_type '{r['source_type']}', use one of {', '.join(sorted(PARTNER_SOURCES))}")
        if r["verdict"] not in VERDICTS:
            errors.append(f"{loc(r)}: unknown verdict '{r['verdict']}'")
        if not parse_date(r["accessed"]):
            errors.append(f"{loc(r)}: no 'accessed' date")
        if r["verdict"] == "confirmed":
            if not r["source_url"] and r["source_type"] != "call":
                errors.append(f"{loc(r)}: confirmed without a source URL")
            if r["source_type"] in {"model", "aggregator"}:
                errors.append(f"{loc(r)}: a {r['source_type']} cannot confirm a claim, find the primary source")
            sd = parse_date(r["source_date"])
            if sd is None:
                errors.append(f"{loc(r)}: confirmed claim has no source_date")
            elif r["field"] == "operating" and months_between(sd, as_of) > 12:
                warns.append(f"{loc(r)}: 'operating' rests on evidence {months_between(sd, as_of)} months old")
            elif r["field"] != "claim_check" and months_between(sd, as_of) > max_age:
                warns.append(f"{loc(r)}: source is {months_between(sd, as_of)} months old")
            if r["field"] == "terms" and r["source_type"] not in {"call", "company", "press_release"}:
                warns.append(f"{loc(r)}: terms and prices are only reliable from the organisation itself")
    if urls:
        url_checks(rows, loc, errors, warns)

    summary = {}
    for oid, claims in by_org.items():
        name = claims[0]["org"]
        ex = [c for c in claims if c["field"] == "exists"]
        op = [c for c in claims if c["field"] == "operating"]
        mat = [c for c in claims if c["field"] == "material"]
        if not ex:
            errors.append(f"{name}: no 'exists' claim, every organisation needs one")
        if any(c["verdict"] == "invented" for c in ex):
            status = "DROP (invented)"
        elif any(c["verdict"] in {"wrong", "outdated"} for c in op) or any(
                c["verdict"] == "confirmed" and CLOSED.search(c["value"]) for c in op):
            status = "DROP (not operating)"
        elif not any(c["verdict"] == "confirmed" and c["source_type"] in PRIMARY for c in ex):
            status = "UNVERIFIED"
        elif not any(c["verdict"] == "confirmed" for c in op):
            status = "EXISTS, operation not confirmed"
        elif not any(c["verdict"] == "confirmed" for c in mat):
            status = "OPERATING, material not confirmed (ask them)"
        else:
            status = f"VERIFIED ({sum(c['verdict'] == 'confirmed' for c in claims)}/{len(claims)} claims confirmed)"
        summary[oid] = {"org": name, "status": status,
                        "counts": {v: sum(c["verdict"] == v for c in claims) for v in VERDICTS}}
    return errors, warns, summary


def render(path, kind, errors, warns, summary, as_of):
    out = [f"# Ledger check ({kind}): {path.name}", "", f"As of {as_of.isoformat()}.", ""]
    if kind == "rules":
        out += ["| Jurisdiction | Topic | confirmed | wrong | outdated | unverifiable | invented | pending |",
                "|---|---|---|---|---|---|---|---|"]
        for (j, t), c in sorted(summary.items()):
            out.append(f"| {j} | {t} | {c['confirmed']} | {c['wrong']} | {c['outdated']} | "
                       f"{c['unverifiable']} | {c['invented']} | {c['pending']} |")
    else:
        out += ["| Organisation | Status | confirmed | wrong | outdated | unverifiable | invented | pending |",
                "|---|---|---|---|---|---|---|---|"]
        for s in sorted(summary.values(), key=lambda x: (x["status"], x["org"])):
            c = s["counts"]
            out.append(f"| {s['org']} | {s['status']} | {c['confirmed']} | {c['wrong']} | {c['outdated']} | "
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
    kind, rows, problems = read(a.ledger)
    if problems:
        sys.stdout.write("\n".join(problems) + "\n")
        return 1
    if kind == "rules":
        errors, warns, summary = check_rules(rows, as_of, a.check_urls)
    else:
        errors, warns, summary = check_partners(rows, as_of, a.check_urls, a.max_age_months)
    report = render(a.ledger, kind, errors, warns, summary, as_of)
    if a.out:
        a.out.write_text(report, encoding="utf-8")
    sys.stdout.write(report)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
