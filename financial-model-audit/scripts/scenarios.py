#!/usr/bin/env python3
"""Build and compare scenarios by overriding assumptions and recomputing.

A single-column model states one future as if it were the plan. Scenarios make the
uncertainty explicit and, more usefully, turn the conversation from "is this number
right?" (unanswerable) into "what has to be true for this to work?" (answerable).

A scenario is a named set of assumption overrides, defined in a small JSON file so
it can be reviewed, versioned and argued with. Where the ledger has researched
ranges, downside/upside can be generated from them automatically: the case is then
built from what the evidence allows rather than from a round number someone liked.

Scenario file format (scenarios.json):
    [
      {"name": "Downside",
       "why": "Their own stated decay factors: shorter campaigns, weaker retention",
       "overrides": {"Sheet!B3": 10, "Sheet!B5": 0.02}},
      {"name": "No anchor partner",
       "why": "Tests concentration risk if the largest counterparty does not sign",
       "overrides": {"Sheet!C5": 0}}
    ]

Usage:
    python scenarios.py --graph model/graph.json --scenarios model/scenarios.json \
        --targets "Sheet!E23,Sheet!E9" --out model/scenario_results.json
    python scenarios.py --graph ... --ledger ... --auto --out ...   # from researched ranges
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from model_graph import load_graph, Evaluator, _num
from sensitivity import band_of, fmt


def evaluate_all(cells, targets, overrides):
    ev = Evaluator(cells, overrides=overrides)
    out = {}
    for t in targets:
        try:
            out[t] = _num(ev.value(t))
        except Exception as e:
            out[t] = None
    return out


def auto_scenarios(ledger, direction_hint=None):
    """Derive downside/upside from researched ranges.

    Only assumptions with a researched range participate: a case built from
    unsourced guesses moved by an arbitrary percentage is theatre, not analysis.
    """
    lo, hi = {}, {}
    for a in ledger["assumptions"]:
        r = (a.get("researched") or {}).get("range")
        if not (r and len(r) == 2):
            continue
        good_high = (a.get("direction") or direction_hint or "higher-is-better") == "higher-is-better"
        lo[a["cell"]] = float(min(r)) if good_high else float(max(r))
        hi[a["cell"]] = float(max(r)) if good_high else float(min(r))
    scen = []
    if lo:
        scen.append({"name": "Downside (researched low)",
                     "why": f"Every researched assumption at the unfavourable end of its "
                            f"evidenced range ({len(lo)} assumptions).",
                     "overrides": lo})
        scen.append({"name": "Upside (researched high)",
                     "why": f"Every researched assumption at the favourable end of its "
                            f"evidenced range ({len(hi)} assumptions).",
                     "overrides": hi})
    return scen


def run(graph, scenarios, targets, bands=None):
    cells = graph["cells"]
    base = evaluate_all(cells, targets, {})
    rows = [{"name": "Base (model as filed)", "why": "The model's own values, unchanged.",
             "overrides": {}, "values": base,
             "bands": {t: band_of(v, bands) if (bands and v is not None) else None
                       for t, v in base.items()},
             "deltas": {t: 0.0 for t in targets}}]
    for s in scenarios:
        ov = {k: v for k, v in s["overrides"].items()}
        vals = evaluate_all(cells, targets, ov)
        rows.append({
            "name": s["name"],
            "why": s.get("why"),
            "overrides": ov,
            "override_count": len(ov),
            "values": vals,
            "bands": {t: band_of(v, bands) if (bands and v is not None) else None
                      for t, v in vals.items()},
            "deltas": {t: (vals[t] - base[t]) if (vals[t] is not None and base[t] is not None)
                       else None for t in targets},
        })
    labels = {t: (cells.get(t) or {}).get("label") for t in targets}
    spread = {}
    for t in targets:
        vs = [r["values"][t] for r in rows if r["values"][t] is not None]
        if vs:
            spread[t] = {"min": min(vs), "max": max(vs), "range": max(vs) - min(vs)}
    return {"targets": targets, "target_labels": labels, "scenarios": rows, "spread": spread}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph", default="model/graph.json")
    ap.add_argument("--scenarios", default=None, help="scenario definitions JSON")
    ap.add_argument("--ledger", default="model/ledger.json")
    ap.add_argument("--auto", action="store_true",
                    help="generate downside/upside from researched ranges in the ledger")
    ap.add_argument("--targets", default=None, help="comma-separated cell keys")
    ap.add_argument("--bands", default=None)
    ap.add_argument("--out", default="model/scenario_results.json")
    a = ap.parse_args()

    g = load_graph(a.graph)
    targets = ([t.strip() for t in a.targets.split(",")] if a.targets
               else [o["cell"] for o in (g.get("outputs") or [])[:3]])
    if not targets:
        raise SystemExit("No targets. Pass --targets 'Sheet!E23'.")

    scen = []
    if a.scenarios and Path(a.scenarios).exists():
        with open(a.scenarios, encoding="utf-8") as f:
            scen = json.load(f)
    if a.auto:
        with open(a.ledger, encoding="utf-8") as f:
            scen = auto_scenarios(json.load(f)) + scen
    if not scen:
        raise SystemExit("No scenarios. Provide --scenarios FILE or --auto "
                         "(which needs researched ranges in the ledger).")

    bands = None
    if a.bands:
        with open(a.bands, encoding="utf-8") as f:
            bands = json.load(f)

    res = run(g, scen, targets, bands)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, default=str)

    w = max(len(r["name"]) for r in res["scenarios"]) + 2
    print(f"{'scenario':{w}}" + "".join(f"{str(res['target_labels'][t])[:22]:>24}" for t in targets))
    print("-" * (w + 24 * len(targets)))
    for r in res["scenarios"]:
        line = f"{r['name']:{w}}"
        for t in targets:
            v, d = r["values"][t], r["deltas"][t]
            cell = fmt(v)
            if d and abs(d) > 0.005:
                cell += f" ({'+' if d > 0 else ''}{fmt(d)})"
            line += f"{cell:>24}"
        print(line)
        if r.get("bands") and any(r["bands"].values()):
            print(f"{'':{w}}" + "".join(f"{str(r['bands'][t] or ''):>24}" for t in targets))
    for t, s in res["spread"].items():
        print(f"\n{str(res['target_labels'][t])[:40]}: spans {fmt(s['min'])} to {fmt(s['max'])} "
              f"across scenarios (range {fmt(s['range'])}).")
    print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
