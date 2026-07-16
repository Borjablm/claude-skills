#!/usr/bin/env python3
"""Structural checks on a financial model — the errors that survive eyeballing.

These checks look for defects that are invisible when you read a spreadsheet but
change the answer: a formula that differs from its neighbours, a total that skips a
row, a rate multiplied by a duration and then treated as a population, a subset
that came out bigger than the set it belongs to.

Every finding carries the formula, the trace, and why it matters, because a finding
a modeller cannot verify is just an accusation. Findings are ranked by severity but
none are auto-corrected: some are deliberate. The reviewer decides.

Checks:
  inconsistent-formula   sibling periods computed differently (usually copy-paste)
  range-gap              SUM/AVERAGE skips or swallows rows next to its block
  embedded-hardcode      magic number inside a formula instead of a labelled input
  stock-times-flow       per-day rate x duration presented as a population
  subset-exceeds-total   "addressable/converted" larger than the total it draws from
  divide-no-guard        division by a cell that can legitimately be zero
  dangling-reference     formula points at an empty or missing cell

Usage:
    python audit.py --graph model/graph.json --out model/findings.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from model_graph import load_graph, Evaluator, _num
from openpyxl.utils import column_index_from_string, get_column_letter

SEVERITY = {"high": 0, "medium": 1, "low": 2}

REF_RX = re.compile(r"(?:(?:'[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!)?(\$?)([A-Z]{1,3})(\$?)([0-9]+)")

# Vocabulary for the label-based judgment checks.
#
# These are heuristics over what people name things, so they are necessarily
# incomplete — a model using unfamiliar words simply won't trigger the check,
# which is the safe direction to fail. Kept domain-neutral on purpose: an early
# version carried terms from the model it was written against ("players",
# "gamers", "DAU") and would have quietly stopped working outside that sector.
# Extend via --vocab rather than by editing this list.

FLOW_WORDS = ("daily", "per day", "per-day", "/day", "per week", "weekly",
              "per month", "monthly", "per hour", "hourly", "run rate", "rate",
              "active", "throughput", "per store", "per site", "per property",
              "per unit time", "diario", "diaria", "mensual", "semanal",
              "par jour", "taglich", "täglich")
DURATION_WORDS = ("days", "duration", "months", "weeks", "period", "length",
                  "window", "term", "campaign", "dias", "días", "duracion",
                  "duración", "meses", "semanas", "periodo", "jours", "duree",
                  "durée", "tage", "dauer")
POPULATION_WORDS = ("market", "users", "customers", "audience", "people",
                    "reach", "subscribers", "visitors", "members", "clients",
                    "accounts", "households", "population", "buyers", "leads",
                    "mercado", "usuarios", "clientes", "personas", "publico",
                    "público", "alcance", "utilisateurs", "marche", "marché",
                    "nutzer", "markt")
SUBSET_WORDS = ("addressable", "converted", "reachable", "target", "captured",
                "penetrat", "serviceable", "obtainable", "reached", "acquired",
                "sam", "som", "direccionable", "objetivo", "alcanzable",
                "captado", "cible", "erreichbar")
TOTAL_WORDS = ("total", "active users", "daily active", "monthly active",
               "population", "universe", "tam", "all ", "entire", "base",
               "whole", "overall", "totales", "totale", "poblacion",
               "población", "gesamt", "insgesamt")

VOCAB = {"FLOW_WORDS": FLOW_WORDS, "DURATION_WORDS": DURATION_WORDS,
         "POPULATION_WORDS": POPULATION_WORDS, "SUBSET_WORDS": SUBSET_WORDS,
         "TOTAL_WORDS": TOTAL_WORDS}


def load_vocab(path):
    """Merge extra terms from a JSON file: {"FLOW_WORDS": ["per tonne", ...], ...}

    Sector vocabulary is unguessable from here — a waste model says "per tonne",
    an energy model says "per MWh" — so let the person who knows the domain add
    their words instead of pretending the built-in list is complete.
    """
    global FLOW_WORDS, DURATION_WORDS, POPULATION_WORDS, SUBSET_WORDS, TOTAL_WORDS
    with open(path, encoding="utf-8") as f:
        extra = json.load(f)
    g = globals()
    for k, words in extra.items():
        if k in VOCAB and isinstance(words, list):
            g[k] = tuple(set(g[k]) | {w.lower() for w in words})
    return {k: len(g[k]) for k in VOCAB}


def to_r1c1(formula, row, col):
    """Normalise a formula to position-independent form so siblings can be compared."""
    def sub(m):
        abs_c, c, abs_r, r = m.group(1), m.group(2), m.group(3), int(m.group(4))
        ci = column_index_from_string(c)
        rpart = f"R{r}" if abs_r else f"R[{r - row}]"
        cpart = f"C{ci}" if abs_c else f"C[{ci - col}]"
        return rpart + cpart
    return REF_RX.sub(sub, formula or "")


def _lab(cells, key):
    c = cells.get(key) or {}
    return (c.get("label") or c.get("row_label") or "").lower()


def _row_lab(cells, key):
    return ((cells.get(key) or {}).get("row_label") or "").lower()


def check_inconsistent_formulas(cells):
    """Sibling periods should compute the same way. When one differs, it is either
    a deliberate exception or a copy-paste error, and both are worth knowing."""
    out = []
    rows = {}
    for key, c in cells.items():
        if c.get("kind") == "formula" and c.get("formula"):
            rows.setdefault((c["sheet"], c["row"]), []).append(c)
    for (sheet, row), group in rows.items():
        if len(group) < 3:
            continue
        group.sort(key=lambda c: c["col"])
        shapes = [(c, to_r1c1(c["formula"], c["row"], c["col"])) for c in group]
        counts = {}
        for _, s in shapes:
            counts[s] = counts.get(s, 0) + 1
        if len(counts) < 2:
            continue
        common, n = max(counts.items(), key=lambda kv: kv[1])
        if n < 2:
            continue
        for c, s in shapes:
            if s != common:
                out.append({
                    "check": "inconsistent-formula",
                    "severity": "high",
                    "cell": f"{sheet}!{c['ref']}",
                    "label": c.get("label"),
                    "formula": c["formula"],
                    "detail": f"Differs from {n} sibling period(s) in the same row, which share "
                              f"one shape. Either an intentional exception or a copy-paste slip.",
                    "peers": [f"{sheet}!{o['ref']}" for o, s2 in shapes if s2 == common][:4],
                })
    return out


def check_range_gaps(cells):
    """A total that skips the row above it, or reaches into a header, is a silent
    understatement or overstatement — the classic spreadsheet defect."""
    out = []
    for key, c in cells.items():
        if c.get("kind") != "formula" or not (f := c.get("formula")):
            continue
        for m in re.finditer(r"\b(SUM|AVERAGE)\s*\(\s*"
                             r"(?:(?:'[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!)?"
                             r"\$?([A-Z]{1,3})\$?([0-9]+):\$?([A-Z]{1,3})\$?([0-9]+)\s*\)",
                             f, re.I):
            fn, c1, r1, c2, r2 = m.group(1), m.group(2), int(m.group(3)), m.group(4), int(m.group(5))
            if c1 != c2:
                continue  # column-wise sums only; row sums rarely show this defect
            sheet, col = c["sheet"], c1
            lo, hi = min(r1, r2), max(r1, r2)
            # Numeric cell immediately above the range, not included in it?
            above = cells.get(f"{sheet}!{col}{lo - 1}")
            if above and above.get("kind") in ("input", "formula") and \
                    isinstance(above.get("value"), (int, float)) and \
                    not isinstance(above.get("value"), bool) and above.get("value") not in (None, 0):
                out.append({
                    "check": "range-gap",
                    "severity": "high",
                    "cell": key,
                    "label": c.get("label"),
                    "formula": f,
                    "detail": f"{fn}({col}{lo}:{col}{hi}) starts at row {lo}, but {col}{lo-1} "
                              f"({above.get('label') or 'unlabelled'} = {above.get('value')}) "
                              f"sits directly above and is excluded. Verify the range.",
                })
            # A label caught inside the range means the block boundary moved.
            for r in range(lo, hi + 1):
                cc = cells.get(f"{sheet}!{col}{r}")
                if cc and cc.get("kind") == "label":
                    out.append({
                        "check": "range-gap", "severity": "medium", "cell": key,
                        "label": c.get("label"), "formula": f,
                        "detail": f"{fn} range covers {col}{r} which holds text "
                                  f"({str(cc.get('value'))[:30]!r}). Range likely drifted.",
                    })
                    break
    return out


def check_embedded_hardcodes(cells):
    """A number typed inside a formula cannot be found, sourced or sensitivity-tested.
    Small integers (2, 12, 100, 0.5) are usually arithmetic, not judgment — skip those."""
    out = []
    NUM = re.compile(r"(?<![A-Za-z0-9_$:!.])(\d+\.?\d*)(?![%\dA-Za-z_(])")
    BENIGN = {0, 1, 2, 3, 4, 6, 10, 12, 24, 30, 52, 100, 360, 365, 1000, 0.5}
    for key, c in cells.items():
        if c.get("kind") != "formula" or not (f := c.get("formula")):
            continue
        body = re.sub(r"'[^']*'", "", f)
        hits = []
        for m in NUM.finditer(body):
            v = float(m.group(1))
            span = body[max(0, m.start() - 2):m.start()]
            if span.endswith(("R", "C")) or v in BENIGN:
                continue
            hits.append(m.group(1))
        if hits:
            out.append({
                "check": "embedded-hardcode",
                "severity": "medium",
                "cell": key,
                "label": c.get("label"),
                "formula": f,
                "detail": f"Contains literal value(s) {', '.join(hits[:4])} inside the formula. "
                          f"Move to a labelled input cell so the number can be sourced, "
                          f"reviewed and sensitivity-tested.",
            })
    return out


def check_stock_times_flow(cells):
    """Multiplying a per-day rate by a campaign duration counts each returning
    person once per day. Sold as a population, that inflates everything downstream.

    A real example: days x daily-active-users x purchase-rate labelled "addressable
    market (#players)". Twenty days of a 1.3M-player game is not 26M players.
    """
    out = []
    for key, c in cells.items():
        if c.get("kind") != "formula" or not c.get("deps"):
            continue
        own = _lab(cells, key)
        if not any(w in own for w in POPULATION_WORDS):
            continue
        if not any(o in c["formula"] for o in ("*", "PRODUCT")):
            continue
        flow = [d for d in c["deps"] if any(w in _row_lab(cells, d) for w in FLOW_WORDS)]
        dur = [d for d in c["deps"] if any(w in _row_lab(cells, d) for w in DURATION_WORDS)]
        if flow and dur:
            out.append({
                "check": "stock-times-flow",
                "severity": "high",
                "cell": key,
                "label": c.get("label"),
                "formula": c["formula"],
                "detail": "Multiplies a per-period rate by a duration and labels the result as "
                          "a population. This counts the same person once per period "
                          "(person-days, not people). If repeat exposure is intended, "
                          "model reach and frequency separately so both can be sourced.",
                "flow_inputs": [{"cell": d, "label": cells[d].get("label")} for d in flow[:3]],
                "duration_inputs": [{"cell": d, "label": cells[d].get("label")} for d in dur[:3]],
            })
    return out


def check_subset_exceeds_total(cells):
    """A slice of a market that is larger than the market. Arithmetically possible,
    logically not — and it is the visible symptom a reviewer will catch first."""
    out = []
    ev = Evaluator(cells)
    for key, c in cells.items():
        if c.get("kind") != "formula" or not c.get("deps"):
            continue
        own = _lab(cells, key)
        if not any(w in own for w in SUBSET_WORDS):
            continue
        try:
            val = _num(ev.value(key))
        except Exception:
            continue
        if val <= 0:
            continue
        for d in c["deps"]:
            dl = _row_lab(cells, d)
            if not any(w in dl for w in TOTAL_WORDS):
                continue
            try:
                dv = _num(ev.value(d))
            except Exception:
                continue
            if dv > 0 and val > dv:
                out.append({
                    "check": "subset-exceeds-total",
                    "severity": "high",
                    "cell": key,
                    "label": c.get("label"),
                    "formula": c["formula"],
                    "detail": f"Computes {val:,.0f} but draws from "
                              f"{cells[d].get('label') or d} = {dv:,.0f} "
                              f"({val/dv:.1f}x larger). A subset cannot exceed its source; "
                              f"usually a symptom of double counting upstream.",
                    "compared_with": d,
                })
                break
    return out


def check_divide_no_guard(cells):
    out = []
    for key, c in cells.items():
        if c.get("kind") != "formula" or not (f := c.get("formula")):
            continue
        for m in re.finditer(r"/\s*((?:'[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!)?"
                             r"(\$?[A-Z]{1,3}\$?[0-9]+)", f):
            ref = (m.group(1) or "") + m.group(2)
            sheet = (m.group(1) or "").rstrip("!").strip("'") or c["sheet"]
            cellref = m.group(2).replace("$", "")
            dk = f"{sheet}!{cellref}"
            d = cells.get(dk)
            if d and d.get("kind") == "input" and _num(d.get("value")) == 0:
                out.append({
                    "check": "divide-no-guard", "severity": "medium", "cell": key,
                    "label": c.get("label"), "formula": f,
                    "detail": f"Divides by {dk} which is currently 0 "
                              f"({d.get('label') or 'unlabelled'}). Produces #DIV/0! as written; "
                              f"wrap in IFERROR or guard the input.",
                })
                break
    return out


def check_dangling(cells):
    """Only direct references count. An empty row inside a SUM range is normal
    modelling; a formula that names an empty cell by hand is not."""
    out = []
    for key, c in cells.items():
        if c.get("kind") != "formula":
            continue
        missing = [d for d in c.get("direct_deps", []) if d not in cells]
        if missing:
            out.append({
                "check": "dangling-reference", "severity": "medium", "cell": key,
                "label": c.get("label"), "formula": c.get("formula"),
                "detail": f"Names empty or non-existent cell(s): {', '.join(missing[:4])}. "
                          f"Treated as zero, which silently understates the result.",
            })
    return out


CHECKS = [
    check_inconsistent_formulas,
    check_range_gaps,
    check_embedded_hardcodes,
    check_stock_times_flow,
    check_subset_exceeds_total,
    check_divide_no_guard,
    check_dangling,
]


def group_by_root_cause(findings, cells):
    """Collapse the same defect repeated across periods into one finding.

    A driver row copied across Y1-Y3 produces three identical hits. They are one
    problem with one fix, and listing them separately makes an audit look like
    noise and buries the distinct issues.
    """
    groups, order = {}, []
    for f in findings:
        cell = f.get("cell")
        c = cells.get(cell) if cell else None
        row_lab = (c or {}).get("row_label") or f.get("label") or ""
        gkey = (f["check"], (c or {}).get("sheet"), row_lab, f.get("formula") is not None)
        if gkey not in groups:
            groups[gkey] = dict(f)
            groups[gkey]["cells"] = []
            order.append(gkey)
        g = groups[gkey]
        g["cells"].append(cell)
        # Keep the widest evidence: the instance with the most telling numbers.
        if len(f.get("detail", "")) > len(g.get("detail", "")):
            g["detail"] = f["detail"]
    out = []
    for gkey in order:
        g = groups[gkey]
        g["cells"] = [c for c in g["cells"] if c]
        g["occurrences"] = len(g["cells"])
        g["cell"] = g["cells"][0] if g["cells"] else g.get("cell")
        if g["occurrences"] > 1:
            g["detail"] += (f" Same pattern in {g['occurrences']} cells "
                            f"({', '.join(x.split('!')[-1] for x in g['cells'][:6])}"
                            f"{'...' if g['occurrences'] > 6 else ''}) — one root cause, one fix.")
        out.append(g)
    return out


def run_audit(graph, group=True):
    cells = graph["cells"]
    findings = []
    for fn in CHECKS:
        try:
            findings.extend(fn(cells))
        except Exception as e:
            findings.append({"check": fn.__name__, "severity": "low", "cell": None,
                             "detail": f"check failed to run: {type(e).__name__}: {e}"})
    if group:
        findings = group_by_root_cause(findings, cells)
    findings.sort(key=lambda f: (SEVERITY.get(f["severity"], 3),
                                 -f.get("occurrences", 1), f["check"], f.get("cell") or ""))
    for i, f in enumerate(findings, 1):
        f["id"] = f"F{i}"
    summary = {}
    for f in findings:
        summary[f["check"]] = summary.get(f["check"], 0) + 1
    return {"source": graph.get("source"), "findings": findings, "summary": summary,
            "counts": {s: sum(1 for f in findings if f["severity"] == s)
                       for s in ("high", "medium", "low")},
            "cells_affected": sum(f.get("occurrences", 1) for f in findings)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph", default="model/graph.json")
    ap.add_argument("--out", default="model/findings.json")
    ap.add_argument("--vocab", default=None,
                    help='JSON of extra label terms for the judgment checks, e.g. '
                         '{"FLOW_WORDS": ["per tonne"], "POPULATION_WORDS": ["sites"]}')
    a = ap.parse_args()

    if a.vocab:
        print("vocab extended:", load_vocab(a.vocab))
    g = load_graph(a.graph)
    res = run_audit(g)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=str)

    c = res["counts"]
    print(f"{len(res['findings'])} findings across {res['cells_affected']} cells  "
          f"(high {c['high']}, medium {c['medium']}, low {c['low']})  -> {a.out}")
    for check, n in sorted(res["summary"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:>3}  {check}")
    print()
    for f in [x for x in res["findings"] if x["severity"] == "high"][:8]:
        n = f.get("occurrences", 1)
        print(f"  [{f['id']}] {f['check']}  {f['cell']}" + (f"  (+{n-1} more)" if n > 1 else ""))
        print(f"        {str(f.get('label'))[:70]}")
        print(f"        {f['detail'][:190]}")
        print()


if __name__ == "__main__":
    main()
