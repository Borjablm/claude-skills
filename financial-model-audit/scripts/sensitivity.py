#!/usr/bin/env python3
"""Rank assumptions by how much they actually move the result.

Research is expensive and attention is finite, so the order matters: find the few
assumptions the answer hinges on, then spend the effort there. In most venture
models a handful of inputs carry the result and the rest are decoration — but
which handful is rarely the one people expect, and it is never the one with the
most confident-sounding note attached.

Each assumption is perturbed on its own, the whole model recomputed, and the
change in the target recorded. Where an assumption has a researched range, that
range is used instead of an arbitrary percentage: a number known to sit between
2.80 and 4.50 should be tested across what it could actually be, not +/-20% of
whatever was typed.

Threshold crossings are tracked separately. A small swing that flips the model
across a covenant, break-even or funding-band boundary matters more than a large
swing that changes nothing anyone decides on.

Usage:
    python sensitivity.py --graph model/graph.json --ledger model/ledger.json \
        --target "Sheet!E23" --out model/sensitivity.json [--pct 20] [--top 15]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_graph import load_graph, Evaluator, _num


def evaluate_target(cells, target, overrides=None):
    ev = Evaluator(cells, overrides=overrides or {})
    try:
        return _num(ev.value(target))
    except Exception:
        return None


def pick_target(graph, explicit=None):
    if explicit:
        return explicit
    outs = graph.get("outputs") or []
    if not outs:
        raise SystemExit("No target given and no output candidates found. Use --target 'Sheet!Ref'.")
    return outs[0]["cell"]


def perturb_values(a, pct):
    """Low/high test points for one assumption.

    A researched range beats an arbitrary percentage, because it reflects what the
    number could really be rather than how far someone chose to nudge it.
    """
    v = a.get("value")
    if not isinstance(v, (int, float)) or isinstance(v, bool):
        return None
    r = (a.get("researched") or {}).get("range")
    if r and len(r) == 2 and all(isinstance(x, (int, float)) for x in r):
        return float(min(r)), float(max(r)), "researched-range"
    if v == 0:
        # A zeroed driver (a channel switched off) has no meaningful percentage
        # move; test whether switching it on matters at all.
        return 0.0, 0.0, "zero-fixed"
    d = abs(v) * pct / 100.0
    lo, hi = v - d, v + d
    if a.get("unit") == "percent" and 0 <= v <= 1:
        lo, hi = max(0.0, lo), min(1.0, hi)
    return lo, hi, f"+/-{pct:g}%"


def run(graph, ledger, target, pct=20.0, bands=None):
    cells = graph["cells"]
    base = evaluate_target(cells, target)
    if base is None:
        raise SystemExit(f"Target {target} could not be evaluated.")
    base_band = band_of(base, bands) if bands else None

    rows = []
    for a in ledger["assumptions"]:
        pv = perturb_values(a, pct)
        if pv is None:
            continue
        lo_v, hi_v, method = pv
        lo = evaluate_target(cells, target, {a["cell"]: lo_v})
        hi = evaluate_target(cells, target, {a["cell"]: hi_v})
        if lo is None or hi is None:
            continue
        d_lo, d_hi = lo - base, hi - base
        swing = abs(d_hi - d_lo)
        entry = {
            "id": a["id"], "cell": a["cell"], "label": a["label"],
            "value": a["value"], "unit": a.get("unit"),
            "grade": a.get("grade"), "evidence_signal": a.get("evidence_signal"),
            "method": method,
            "low_input": lo_v, "high_input": hi_v,
            "low_target": lo, "high_target": hi,
            "delta_low": d_lo, "delta_high": d_hi,
            "swing": swing,
            "swing_pct_of_base": (swing / abs(base) * 100) if base else None,
        }
        if bands:
            b_lo, b_hi = band_of(lo, bands), band_of(hi, bands)
            entry["band_low"], entry["band_high"] = b_lo, b_hi
            entry["crosses_band"] = (b_lo != base_band) or (b_hi != base_band)
        rows.append(entry)

    rows.sort(key=lambda r: (-(r.get("crosses_band") or False), -r["swing"]))
    total = sum(r["swing"] for r in rows) or 1.0
    cum = 0.0
    for i, r in enumerate(rows, 1):
        r["rank"] = i
        r["share_of_total_swing"] = r["swing"] / total
        cum += r["share_of_total_swing"]
        r["cumulative_share"] = cum
        r["evidence_weight"] = evidence_weight(r)
        # What to research first is not what moves the model most, but what moves
        # the model most *while resting on the weakest evidence*. A high-leverage
        # number taken from audited actuals needs no attention; the same leverage
        # on a guess is where the risk lives.
        r["research_priority"] = r["share_of_total_swing"] * r["evidence_weight"]

    ranked = sorted(rows, key=lambda r: -r["research_priority"])
    for i, r in enumerate(ranked, 1):
        r["priority_rank"] = i

    vital_few = next((r["rank"] for r in rows if r["cumulative_share"] >= 0.8), len(rows))
    return {
        "target": target,
        "target_label": (cells.get(target) or {}).get("label"),
        "base_value": base,
        "base_band": base_band,
        "method": f"one-at-a-time, {pct:g}% unless a researched range exists",
        "assumptions_tested": len(rows),
        "vital_few": vital_few,
        "leverage_ties": detect_ties(rows),
        "results": rows,
        "research_order": [
            {k: r[k] for k in ("priority_rank", "id", "cell", "label", "value",
                               "swing", "share_of_total_swing", "grade",
                               "evidence_signal", "research_priority")}
            for r in ranked[:20]
        ],
    }


# How much attention an assumption deserves given what stands behind it.
# Graded evidence wins over the provisional note signal when a reviewer has ruled.
GRADE_WEIGHT = {"A": 0.10, "B": 0.30, "C": 0.80, "D": 1.00}
SIGNAL_WEIGHT = {"strong": 0.25, "unclear": 0.60, "none": 0.75, "weak": 0.95}


def evidence_weight(r):
    g = (r.get("grade") or "").strip().upper()[:1]
    if g in GRADE_WEIGHT:
        return GRADE_WEIGHT[g]
    return SIGNAL_WEIGHT.get(r.get("evidence_signal"), 0.7)


def detect_ties(rows):
    """Equal leverage across many inputs means a pure multiplicative chain.

    Worth saying out loud: it tells the modeller that no single driver is special,
    so the ranking cannot come from arithmetic and must come from evidence quality.
    """
    if len(rows) < 3:
        return []
    groups = {}
    for r in rows:
        k = round(r["swing"], 6)
        groups.setdefault(k, []).append(r["label"])
    ties = [{"swing": k, "count": len(v), "labels": v[:10]}
            for k, v in groups.items() if len(v) >= 3 and k > 0]
    ties.sort(key=lambda t: -t["swing"])
    return ties[:3]


def band_of(value, bands):
    """Map a result onto named decision thresholds (covenant, break-even, funding band)."""
    for b in bands:
        lo = b.get("min", float("-inf"))
        hi = b.get("max", float("inf"))
        if lo <= value < hi:
            return b.get("name")
    return None


def write_back_ranks(ledger_path, sens):
    p = Path(ledger_path)
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        led = json.load(f)
    ranks = {r["cell"]: r for r in sens["results"]}
    for a in led["assumptions"]:
        if (r := ranks.get(a["cell"])):
            a["impact_rank"] = r["rank"]
            a["impact_swing"] = r["swing"]
            a["research_priority_rank"] = r.get("priority_rank")
            a["crosses_band"] = r.get("crosses_band")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(led, f, indent=1, default=str)


def fmt(v):
    if v is None:
        return "-"
    a = abs(v)
    if a >= 1e9: return f"{v/1e9:,.2f}B"
    if a >= 1e6: return f"{v/1e6:,.2f}M"
    if a >= 1e3: return f"{v/1e3:,.0f}k"
    return f"{v:,.2f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph", default="model/graph.json")
    ap.add_argument("--ledger", default="model/ledger.json")
    ap.add_argument("--target", default=None)
    ap.add_argument("--out", default="model/sensitivity.json")
    ap.add_argument("--pct", type=float, default=20.0)
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--bands", default=None,
                    help="JSON file: [{\"name\":\"Band 1\",\"min\":-1e9,\"max\":0}, ...]")
    ap.add_argument("--no-write-back", action="store_true")
    a = ap.parse_args()

    g = load_graph(a.graph)
    with open(a.ledger, encoding="utf-8") as f:
        led = json.load(f)
    bands = None
    if a.bands:
        with open(a.bands, encoding="utf-8") as f:
            bands = json.load(f)

    target = pick_target(g, a.target)
    sens = run(g, led, target, a.pct, bands)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(sens, f, indent=1, default=str)
    if not a.no_write_back:
        write_back_ranks(a.ledger, sens)

    print(f"target  {target}  ({sens['target_label']})")
    print(f"base    {fmt(sens['base_value'])}"
          + (f"   band: {sens['base_band']}" if sens.get("base_band") else ""))
    print(f"tested  {sens['assumptions_tested']} assumptions, {sens['method']}")
    print(f"\n{sens['vital_few']} assumptions account for 80% of the total swing.\n")

    hdr = f"{'#':>3}  {'assumption':44} {'value':>11}  {'swing':>9}  {'share':>6}  band"
    print("LEVERAGE  (how much each moves the target)")
    print(hdr); print("-" * len(hdr))
    for r in sens["results"][:a.top]:
        band = ""
        if r.get("crosses_band"):
            band = f"CROSSES ({r.get('band_low')} .. {r.get('band_high')})"
        elif r.get("band_low"):
            band = "stable"
        print(f"{r['rank']:>3}  {str(r['label'])[:44]:44} {fmt(r['value']):>11}  "
              f"{fmt(r['swing']):>9}  {r['share_of_total_swing']*100:>5.1f}%  {band}")

    for t in sens.get("leverage_ties", [])[:1]:
        print(f"\n  Note: {t['count']} assumptions share identical leverage "
              f"({fmt(t['swing'])} each) — they sit in one multiplicative chain, so no "
              f"driver is arithmetically special. Evidence quality decides the order.")

    print("\nRESEARCH FIRST  (leverage weighted by how weak the evidence is)")
    hdr2 = f"{'#':>3}  {'assumption':44} {'share':>6}  {'evidence':>10}  note"
    print(hdr2); print("-" * len(hdr2))
    for r in sens["research_order"][:a.top]:
        ev = r.get("grade") or r.get("evidence_signal") or "?"
        print(f"{r['priority_rank']:>3}  {str(r['label'])[:44]:44} "
              f"{r['share_of_total_swing']*100:>5.1f}%  {ev:>10}")
    print(f"\n-> {a.out}" + ("" if a.no_write_back else f" , ranks written to {a.ledger}"))


if __name__ == "__main__":
    main()
