#!/usr/bin/env python3
"""Extract every assumption in a model into a ledger with evidence fields.

An assumption is a hardcoded number that something else depends on. In a venture
model these carry the entire argument: the arithmetic is trivial, the judgment
calls (price, retention, market share, contract value) are what a committee will
actually question. Yet they are usually scattered across tabs with no record of
where they came from.

This script finds them and builds one row per assumption. It pre-fills what can be
determined mechanically (label, value, unit, where it flows, whether a note exists,
and a *provisional* evidence signal read from that note). Grading itself is a
judgment call left to the reviewer — the heuristic only sorts the pile so attention
goes to the right rows first. See references/grading-rubric.md.

Re-running is safe: existing grades, sources and history are preserved and merged
with fresh values from the workbook.

Usage:
    python ledger.py --graph model/graph.json --out model/ledger.json [--csv model/ledger.csv]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from model_graph import load_graph

# Phrases that betray an assumption with no real evidence behind it. "Based on
# ChatGPT analysis" and "arbitrary assumption" are real examples from production
# models — they are honest admissions, and worth surfacing rather than punishing.
#
# Multilingual because models are, and incomplete by nature: an unrecognised note
# falls to "unclear", which invites a look rather than asserting anything false.
# Extend for a house style or another language with --vocab.
WEAK_MARKERS = [
    "arbitrary", "assumption", "assumed", "estimate", "estimated", "guess",
    "placeholder", "tbc", "tbd", "to be confirmed", "rough", "proxy",
    "chatgpt", "gpt", "claude", "copilot", "gemini", "ai analysis", "llm",
    "gut", "best case", "for now", "?", "made up", "indicative", "ballpark",
    "arbitrario", "supuesto", "supone", "estimacion", "estimación", "estimado",
    "aproximado", "por confirmar", "hipotesis", "hipótesis",
    "arbitraire", "hypothese", "hypothèse", "estimation", "a confirmer",
    "annahme", "schatzung", "schätzung",
]
STRONG_MARKERS = [
    "http://", "https://", "www.", "source:", "sources:", "10-k", "10-q",
    "annual report", "financial statement", "filing", "survey", "study",
    "research", "primary", "interview", "actuals", "audited", "census",
    "statistics", "dataset", "invoice", "contract", "quote", "term sheet",
    "fuente:", "fuentes:", "estudio", "encuesta", "informe anual", "auditado",
    "datos reales", "factura", "contrato", "investigacion", "investigación",
    "source :", "etude", "étude", "enquete", "enquête", "rapport annuel",
    "quelle:", "studie", "umfrage", "jahresbericht",
]
# A number attached to a named counterparty is not researchable — it is a deal.
# Its credibility is the stage of that conversation, so it gets its own track.
PARTNER_HINT = re.compile(
    r"\b(contract|partner|client|campaign development|licens\w*|sponsor|deal|"
    r"agreement|mou|loi|committed|pledge)\b", re.I)

UNIT_PATTERNS = [
    (re.compile(r"0%|0\.0%|%"), "percent"),
    (re.compile(r"[$€£]"), "currency"),
    (re.compile(r"0\.0x|x\"?$"), "multiple"),
]


def load_vocab(path):
    """Merge extra evidence markers: {"WEAK_MARKERS": [...], "STRONG_MARKERS": [...]}

    House conventions vary ("per DD's email", "SWAG", a ticket reference) and no
    built-in list can anticipate them, so make the list extensible rather than
    silently mis-signalling a note it does not recognise.
    """
    global WEAK_MARKERS, STRONG_MARKERS
    with open(path, encoding="utf-8") as f:
        extra = json.load(f)
    if isinstance(extra.get("WEAK_MARKERS"), list):
        WEAK_MARKERS = sorted(set(WEAK_MARKERS) | {w.lower() for w in extra["WEAK_MARKERS"]})
    if isinstance(extra.get("STRONG_MARKERS"), list):
        STRONG_MARKERS = sorted(set(STRONG_MARKERS) | {w.lower() for w in extra["STRONG_MARKERS"]})
    return {"WEAK_MARKERS": len(WEAK_MARKERS), "STRONG_MARKERS": len(STRONG_MARKERS)}


def infer_unit(cell):
    v, fmt = cell.get("value"), cell.get("number_format") or ""
    for rx, unit in UNIT_PATTERNS:
        if rx.search(fmt):
            return unit
    lab = (cell.get("label") or "").lower()
    if "%" in lab or "rate" in lab or "share" in lab or "margin" in lab:
        if isinstance(v, float) and 0 <= v <= 1:
            return "percent"
    if any(w in lab for w in ("price", "cost", "revenue", "fee", "value", "$")):
        return "currency"
    if any(w in lab for w in ("days", "duration", "months", "years")):
        return "duration"
    if any(w in lab for w in ("number", "count", "players", "users", "stores",
                              "properties", "brands", "items", "spaces")):
        return "count"
    return "number"


def evidence_signal(note):
    """A provisional read of the note text: strong, weak, partner, or none.

    Deliberately not a grade. It sorts the pile; a human or agent decides what the
    evidence is actually worth, because that judgment needs context the note lacks.
    """
    if not note:
        return "none"
    low = note.lower()
    if any(m in low for m in STRONG_MARKERS):
        # A source plus an admission of guesswork is still guesswork.
        return "weak" if any(m in low for m in WEAK_MARKERS[:8]) else "strong"
    if any(m in low for m in WEAK_MARKERS):
        return "weak"
    return "unclear"


def looks_structural(cell):
    """Constants that are model plumbing, not judgment calls worth researching."""
    lab = (cell.get("label") or "").lower()
    v = cell.get("value")
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return True
    # Year headers and similar sequence markers stored as numbers.
    if 1900 <= v <= 2100 and float(v).is_integer() and (
            "year" in lab or "y1" in lab or not lab):
        return True
    return False


def downstream(cells, key, limit=400):
    """Everything that changes if this assumption changes."""
    seen, stack = set(), [key]
    while stack and len(seen) < limit:
        cur = stack.pop()
        for d in cells.get(cur, {}).get("dependents", []):
            if d not in seen:
                seen.add(d)
                stack.append(d)
    return seen


def build_ledger(graph, outputs=None):
    cells = graph["cells"]
    outs = set(outputs or [o["cell"] for o in graph.get("outputs", [])])
    rows = []
    for key, c in cells.items():
        if c.get("kind") != "input":
            continue
        if not c.get("dependents"):
            continue  # nothing depends on it: not part of the argument
        if looks_structural(c):
            continue
        down = downstream(cells, key)
        note = c.get("note")
        rows.append({
            "id": slug(c, key),
            "cell": key,
            "sheet": c["sheet"],
            "label": c.get("label") or key,
            "row_label": c.get("row_label"),
            "col_label": c.get("col_label"),
            "value": c.get("value"),
            "unit": infer_unit(c),
            "note": note,
            "evidence_signal": evidence_signal(note),
            "partner_dependent": bool(PARTNER_HINT.search(c.get("label") or "")) or
                                 bool(note and PARTNER_HINT.search(note)),
            "feeds_outputs": sorted(down & outs),
            "downstream_cells": len(down),
            # Reviewer/agent fields — the judgment layer, left empty on purpose.
            "grade": None,
            "confidence": None,
            "source": None,
            "researched": None,
            "deal_stage": None,
            "impact_rank": None,
            "history": [],
        })
    rows.sort(key=lambda r: (-r["downstream_cells"], r["cell"]))
    return {"source": graph.get("source"), "assumptions": rows}


def slug(cell, key):
    base = (cell.get("row_label") or cell.get("label") or key)
    s = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")[:44]
    sheet = re.sub(r"[^a-z0-9]+", "-", cell["sheet"].lower()).strip("-")[:14]
    return f"{sheet}--{s or cell['ref'].lower()}"


def merge(old, new):
    """Keep human judgment across re-runs; refresh mechanical fields from the file."""
    keep = ("grade", "confidence", "source", "researched", "deal_stage", "history")
    by_cell = {a["cell"]: a for a in old.get("assumptions", [])}
    for a in new["assumptions"]:
        if (prev := by_cell.get(a["cell"])):
            for k in keep:
                if prev.get(k):
                    a[k] = prev[k]
            if prev.get("value") != a["value"]:
                a.setdefault("history", []).append(
                    {"value": prev.get("value"), "note": "changed in workbook since last run"})
    return new


CSV_COLS = ["id", "cell", "label", "value", "unit", "grade", "confidence",
            "evidence_signal", "partner_dependent", "deal_stage", "downstream_cells",
            "impact_rank", "note", "source"]


def write_csv(ledger, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS, extrasaction="ignore")
        w.writeheader()
        for a in ledger["assumptions"]:
            w.writerow(a)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph", default="model/graph.json")
    ap.add_argument("--out", default="model/ledger.json")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--vocab", default=None,
                    help='JSON of extra evidence markers, e.g. '
                         '{"WEAK_MARKERS": ["swag"], "STRONG_MARKERS": ["per contract"]}')
    a = ap.parse_args()

    if a.vocab:
        print("vocab extended:", load_vocab(a.vocab))
    g = load_graph(a.graph)
    led = build_ledger(g)

    out = Path(a.out)
    if out.exists():
        with open(out, encoding="utf-8") as f:
            led = merge(json.load(f), led)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(led, f, indent=1, default=str)
    if a.csv:
        write_csv(led, a.csv)

    rows = led["assumptions"]
    sig = {}
    for r in rows:
        sig[r["evidence_signal"]] = sig.get(r["evidence_signal"], 0) + 1
    print(f"{len(rows)} assumptions extracted -> {a.out}" + (f" , {a.csv}" if a.csv else ""))
    print("  evidence signal (provisional, from notes): " +
          ", ".join(f"{k}={v}" for k, v in sorted(sig.items())))
    print(f"  partner-dependent candidates: {sum(1 for r in rows if r['partner_dependent'])}")
    print("\n  widest reach (grade these first):")
    for r in rows[:10]:
        note = (r["note"] or "")[:40].replace("\n", " ")
        print(f"    {r['downstream_cells']:>3} cells  {str(r['label'])[:44]:46} "
              f"{r['value']!s:>12}  [{r['evidence_signal']}] {note}")


if __name__ == "__main__":
    main()
