#!/usr/bin/env python3
"""Sensitivity, research priority, and scenarios over a model spec.

Two questions, and only the second one is usually asked well.

"Which assumptions move the answer?" is arithmetic, and often unhelpful: driver
models are chains of multiplication, so many drivers have identical leverage and
a tornado chart just shows a row of equal bars. When that happens, arithmetic
cannot tell you where to look.

"Which assumptions move the answer *and* rest on nothing?" is the useful question.
A high-leverage number taken from a signed lease needs no attention; the same
leverage resting on "founder estimate" is where the risk actually lives. That
product — leverage x evidence weakness — is the research plan.

Usage:
    python explore.py spec.yaml --target net --out model/explore.json
    python explore.py spec.yaml --scenarios
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from model import (load_spec, validate, compute, n_periods, period_labels,
                   fmt, SpecError)

# What attention an assumption deserves, given what stands behind it.
GRADE_WEIGHT = {"A": 0.10, "B": 0.30, "C": 0.85, "D": 1.00, "partner": 0.95}
UNGRADED_WITH_SOURCE = 0.55
UNGRADED_NO_SOURCE = 0.90


def evidence_weight(d):
    g = (d.get("grade") or "").strip()
    if g in GRADE_WEIGHT:
        return GRADE_WEIGHT[g]
    return UNGRADED_WITH_SOURCE if d.get("source") else UNGRADED_NO_SOURCE


def scalarise(v, how="last"):
    """Reduce a target vector to one number to rank against.

    Default is the final period: it is the number that carries the case, and it
    is also the least evidenced, which is worth remembering.
    """
    if how == "last":   return v[-1]
    if how == "first":  return v[0]
    if how == "total":  return sum(v)
    if how == "mean":   return sum(v) / len(v)
    if how == "min":    return min(v)
    return v[-1]


def perturb(spec, key, pct):
    """Test points for one driver: its researched range if it has one, otherwise
    +/- a percentage. A range beats a percentage — it reflects what the number
    could actually be, rather than how far someone chose to nudge it."""
    d = spec["drivers"][key]
    base = d.get("values", d.get("value"))
    n = n_periods(spec)
    r = (d.get("researched") or {}).get("range")
    if r and len(r) == 2:
        return float(min(r)), float(max(r)), "researched range"
    if isinstance(base, list):
        lo = [x * (1 - pct / 100) for x in base]
        hi = [x * (1 + pct / 100) for x in base]
    else:
        b = float(base or 0)
        lo, hi = b * (1 - pct / 100), b * (1 + pct / 100)
    if d.get("unit") == "percent":
        clip = lambda v: (min(1.0, max(0.0, v)) if not isinstance(v, list)
                          else [min(1.0, max(0.0, x)) for x in v])
        lo, hi = clip(lo), clip(hi)
    return lo, hi, f"+/-{pct:g}%"


def run(spec, target, pct=20.0, how="last"):
    base_res = compute(spec)
    if target not in base_res["values"]:
        raise SpecError(f"unknown target {target!r}. Available: "
                        + ", ".join(sorted(base_res["values"])[:25]))
    base = scalarise(base_res["values"][target], how)

    def threshold_state(res):
        return tuple(t.get("met_all") for t in res["thresholds"])

    base_thr = threshold_state(base_res)
    rows = []
    for k, d in spec["drivers"].items():
        lo, hi, method = perturb(spec, k, pct)
        r_lo = compute(spec, {k: lo})
        r_hi = compute(spec, {k: hi})
        v_lo = scalarise(r_lo["values"][target], how)
        v_hi = scalarise(r_hi["values"][target], how)
        swing = abs(v_hi - v_lo)
        flips = (threshold_state(r_lo) != base_thr) or (threshold_state(r_hi) != base_thr)
        rows.append({
            "key": k, "label": d.get("label") or k,
            "value": d.get("values", d.get("value")),
            "unit": d.get("unit"), "grade": d.get("grade"),
            "source": d.get("source"), "deal_stage": d.get("deal_stage"),
            "method": method, "low": v_lo, "high": v_hi, "swing": swing,
            "flips_threshold": flips,
            "evidence_weight": evidence_weight(d),
        })

    total = sum(r["swing"] for r in rows) or 1.0
    rows.sort(key=lambda r: -r["swing"])
    for i, r in enumerate(rows, 1):
        r["leverage_rank"] = i
        r["share"] = r["swing"] / total
        r["research_priority"] = r["share"] * r["evidence_weight"]

    ranked = sorted(rows, key=lambda r: (-r["research_priority"]))
    for i, r in enumerate(ranked, 1):
        r["priority_rank"] = i

    # Equal leverage across several drivers means a multiplicative chain. Worth
    # naming: it tells the founder no driver is arithmetically special, so the
    # ranking has to come from evidence.
    groups = {}
    for r in rows:
        groups.setdefault(round(r["swing"], 6), []).append(r["label"])
    ties = [{"swing": k, "count": len(v), "labels": v}
            for k, v in groups.items() if len(v) >= 3 and k > 0]

    return {
        "target": target, "target_scalar": how, "base": base,
        "method": f"one-at-a-time, {pct:g}% unless a researched range exists",
        "results": rows,
        "ties": sorted(ties, key=lambda t: -t["swing"])[:3],
        "research_order": [
            {k: r[k] for k in ("priority_rank", "key", "label", "value", "grade",
                               "share", "research_priority", "deal_stage",
                               "flips_threshold")}
            for r in ranked],
    }


def evidenced_case(spec, target="net", how="last", favourable=False):
    """Build a case from what the evidence allows, not from a mood.

    Every driver with a researched range is moved to whichever end of that range is
    worse (or better) for the target — determined by testing, not by guessing the
    direction. The result is not pessimism: it is the model priced at the other end
    of its own sources, which is the question a funder is really asking. On a real
    project this single scenario moved the answer from +406k to -165k using nothing
    but numbers already in the client's own folder.
    """
    base_res = compute(spec)
    if target not in base_res["values"]:
        raise SpecError(f"unknown target {target!r}")
    base = scalarise(base_res["values"][target], how)
    ov, why = {}, []
    for k, d in spec["drivers"].items():
        r = (d.get("researched") or {}).get("range")
        if not (r and len(r) == 2):
            continue
        lo, hi = float(min(r)), float(max(r))
        v_lo = scalarise(compute(spec, {k: lo})["values"][target], how)
        v_hi = scalarise(compute(spec, {k: hi})["values"][target], how)
        pick = (hi if v_hi > v_lo else lo) if favourable else (lo if v_lo < v_hi else hi)
        if pick != (d.get("values", d.get("value"))):
            ov[k] = pick
            why.append(f"{d.get('label') or k} at {pick:g}")
    return {
        "name": ("Evidenced upside" if favourable else "Evidenced downside"),
        "why": ("Every researched driver at the "
                + ("favourable" if favourable else "unfavourable")
                + " end of the range its own sources support. No added pessimism — "
                  "this is the model priced at the other end of its own evidence. "
                + ("Moves: " + "; ".join(why) if why else "")),
        "overrides": ov, "base": base,
    }


def run_scenarios(spec, target="net", how="last", include_evidenced=True):
    base = compute(spec)
    out = [{"name": "Base (as written)", "why": None, "res": base, "overrides": {}}]
    if include_evidenced:
        for fav in (False, True):
            try:
                ec = evidenced_case(spec, target, how, favourable=fav)
            except SpecError:
                continue
            if ec["overrides"]:
                out.append({"name": ec["name"], "why": ec["why"],
                            "res": compute(spec, ec["overrides"]),
                            "overrides": ec["overrides"]})
    for name, sc in (spec.get("scenarios") or {}).items():
        ov = sc.get("overrides") or {}
        out.append({"name": name, "why": sc.get("why"),
                    "res": compute(spec, ov), "overrides": ov})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--target", default="net")
    ap.add_argument("--pct", type=float, default=20.0)
    ap.add_argument("--scalar", default="last",
                    choices=["last", "first", "total", "mean", "min"])
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--scenarios", action="store_true")
    ap.add_argument("--no-evidenced", action="store_true",
                    help="omit the auto-built evidenced downside/upside cases")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    spec = load_spec(a.spec)
    errs, _ = validate(spec)
    if errs:
        for e in errs:
            print("  ERROR ", e)
        raise SystemExit("spec has errors")

    if a.scenarios:
        rows = run_scenarios(spec, a.target, a.scalar,
                             include_evidenced=not a.no_evidenced)
        per = period_labels(spec)
        w = max(len(r["name"]) for r in rows) + 2
        print(f"{'scenario':{w}}{'net (final)':>14}{'grant dep.':>12}"
              f"{'reserves':>12}   thresholds met")
        print("-" * (w + 52))
        for r in rows:
            v = r["res"]["values"]
            met = sum(1 for t in r["res"]["thresholds"] if t.get("met_all"))
            tot = len(r["res"]["thresholds"])
            print(f"{r['name']:{w}}{fmt(v['net'][-1]):>14}"
                  f"{fmt(v['grant_dependency'][-1],'percent'):>12}"
                  f"{fmt(v['cumulative_net'][-1]):>12}   {met}/{tot}")
        for r in rows:
            if r["why"]:
                print(f"\n  {r['name']}: {r['why']}")
        if a.out:
            Path(a.out).parent.mkdir(parents=True, exist_ok=True)
            json.dump([{k: v for k, v in r.items() if k != "res"} | {"result": r["res"]}
                       for r in rows], open(a.out, "w", encoding="utf-8"), indent=1)
            print(f"\n-> {a.out}")
        return

    res = run(spec, a.target, a.pct, a.scalar)
    print(f"target  {a.target} ({a.scalar} period) = {fmt(res['base'])}")
    print(f"method  {res['method']}\n")

    print("LEVERAGE — how much each driver moves the target")
    print(f"{'#':>3}  {'driver':38}{'swing':>12}{'share':>8}  flips?")
    print("-" * 72)
    for r in res["results"][:a.top]:
        print(f"{r['leverage_rank']:>3}  {str(r['label'])[:38]:38}{fmt(r['swing']):>12}"
              f"{r['share']*100:>7.1f}%  {'YES' if r['flips_threshold'] else ''}")

    for t in res["ties"][:1]:
        print(f"\n  {t['count']} drivers share identical leverage ({fmt(t['swing'])} each) — "
              f"they sit in one\n  multiplicative chain, so no driver is arithmetically "
              f"special. Evidence decides.")

    print("\nRESEARCH FIRST — leverage weighted by how weak the evidence is")
    print(f"{'#':>3}  {'driver':38}{'share':>8}  {'evidence':<12} flips?")
    print("-" * 72)
    for r in res["research_order"][:a.top]:
        ev = r.get("grade") or "ungraded"
        if r.get("deal_stage"):
            ev = f"{ev}/{r['deal_stage']}"
        print(f"{r['priority_rank']:>3}  {str(r['label'])[:38]:38}{r['share']*100:>7.1f}%  "
              f"{ev:<12} {'YES' if r['flips_threshold'] else ''}")

    # A signed agreement is settled — it is an actual, not an open question.
    # Only unsettled counterparty numbers need this warning.
    partner = [r for r in res["research_order"]
               if r.get("deal_stage") and r["deal_stage"] != "signed"]
    if partner:
        print("\n  Not researchable: "
              + ", ".join(f"{r['label']} ({r['deal_stage']})" for r in partner)
              + "\n  These depend on a named counterparty. Their credibility is the stage "
                "of that\n  conversation, not a number in a dataset. Stage them; do not "
                "search for them.")

    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
        print(f"\n-> {a.out}")


if __name__ == "__main__":
    main()
