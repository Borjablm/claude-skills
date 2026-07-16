#!/usr/bin/env python3
"""The model engine: load a spec, check it, compute it.

The spec is a small YAML file that a founder can read. That is the whole design.
A social enterprise usually has no analyst, so a model they cannot inspect is a
model they cannot defend, and one they cannot defend is worthless in the room
where it matters. Keeping the model declarative means the artifact stays theirs:
readable, diffable, versionable, and executable by anything — not locked inside a
spreadsheet's cell references or this tool's code.

Every value is a vector over periods; scalars broadcast. Expressions are parsed
with Python's own parser and walked against a whitelist, so a spec can never
execute arbitrary code — it is data, not a program, and it should stay that way.

Usage:
    python model.py spec.yaml                 # compute and print
    python model.py spec.yaml --check         # validate only
    python model.py spec.yaml --json out.json # full results for other scripts
"""
from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required:  python -m pip install pyyaml")

# Categories that make blended finance legible. Most tools model sales; social
# enterprises live on a mix, and the mix is usually the actual question.
INCOME_CATS = ("earned", "grant", "investment", "inkind")
COST_CATS = ("cost",)
IMPACT_CATS = ("impact",)
ALL_CATS = INCOME_CATS + COST_CATS + IMPACT_CATS

GRADES = ("A", "B", "C", "D", "partner")
DEAL_STAGES = ("exploration", "verbal", "LOI", "signed")


class SpecError(Exception):
    pass


# ----------------------------------------------------------------- expressions

ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Call,
    ast.Compare, ast.BoolOp, ast.IfExp, ast.Load,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Mod,
    ast.Lt, ast.Gt, ast.LtE, ast.GtE, ast.Eq, ast.NotEq, ast.And, ast.Or, ast.Not,
)

FUNCS = ("prev", "cumul", "total", "npv", "irr", "min", "max", "abs",
         "round", "clamp", "where", "peak", "first", "last")


def parse_expr(src: str):
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError as e:
        raise SpecError(f"cannot parse expression {src!r}: {e}")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED_NODES):
            raise SpecError(
                f"expression {src!r} uses {type(node).__name__}, which is not allowed. "
                f"A spec is data, not code — use arithmetic and {', '.join(FUNCS)}.")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in FUNCS:
                fn = getattr(node.func, "id", "?")
                raise SpecError(f"unknown function {fn}() in {src!r}. "
                                f"Available: {', '.join(FUNCS)}")
    return tree


def expr_names(src: str) -> set:
    return {n.id for n in ast.walk(parse_expr(src))
            if isinstance(n, ast.Name) and n.id not in FUNCS}


# ------------------------------------------------------------------ vector ops

def vec(v, n):
    """Anything → a vector of length n. Scalars broadcast; short lists repeat last."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return [float(v)] * n
    if isinstance(v, bool):
        return [1.0 if v else 0.0] * n
    if isinstance(v, (list, tuple)):
        out = [float(x) if x is not None else 0.0 for x in v]
        if not out:
            return [0.0] * n
        return (out + [out[-1]] * n)[:n]
    if v is None:
        return [0.0] * n
    raise SpecError(f"cannot use {v!r} as a number")


def _bin(op, a, b):
    return [op(x, y) for x, y in zip(a, b)]


def _div(x, y):
    return x / y if y else 0.0


class Engine:
    """Evaluates spec expressions over the period vectors."""

    def __init__(self, n, values):
        self.n, self.values = n, values

    def eval(self, src):
        return self._node(parse_expr(src).body)

    def _node(self, nd):
        n = self.n
        if isinstance(nd, ast.Constant):
            return vec(nd.value, n)
        if isinstance(nd, ast.Name):
            if nd.id not in self.values:
                raise SpecError(f"unknown name {nd.id!r}")
            return self.values[nd.id]
        if isinstance(nd, ast.UnaryOp):
            v = self._node(nd.operand)
            if isinstance(nd.op, ast.USub):
                return [-x for x in v]
            if isinstance(nd.op, ast.Not):
                return [0.0 if x else 1.0 for x in v]
            return v
        if isinstance(nd, ast.BinOp):
            a, b = self._node(nd.left), self._node(nd.right)
            o = nd.op
            if isinstance(o, ast.Add):  return _bin(lambda x, y: x + y, a, b)
            if isinstance(o, ast.Sub):  return _bin(lambda x, y: x - y, a, b)
            if isinstance(o, ast.Mult): return _bin(lambda x, y: x * y, a, b)
            if isinstance(o, ast.Div):  return _bin(_div, a, b)
            if isinstance(o, ast.Pow):  return _bin(lambda x, y: x ** y, a, b)
            if isinstance(o, ast.Mod):  return _bin(lambda x, y: x % y if y else 0.0, a, b)
        if isinstance(nd, ast.Compare):
            a = self._node(nd.left)
            b = self._node(nd.comparators[0])
            o = nd.ops[0]
            fn = {ast.Lt: lambda x, y: x < y, ast.Gt: lambda x, y: x > y,
                  ast.LtE: lambda x, y: x <= y, ast.GtE: lambda x, y: x >= y,
                  ast.Eq: lambda x, y: x == y, ast.NotEq: lambda x, y: x != y}[type(o)]
            return [1.0 if fn(x, y) else 0.0 for x, y in zip(a, b)]
        if isinstance(nd, ast.BoolOp):
            vs = [self._node(v) for v in nd.values]
            if isinstance(nd.op, ast.And):
                return [1.0 if all(v[i] for v in vs) else 0.0 for i in range(n)]
            return [1.0 if any(v[i] for v in vs) else 0.0 for i in range(n)]
        if isinstance(nd, ast.IfExp):
            c, a, b = self._node(nd.test), self._node(nd.body), self._node(nd.orelse)
            return [a[i] if c[i] else b[i] for i in range(n)]
        if isinstance(nd, ast.Call):
            return self._call(nd.func.id, [self._node(a) for a in nd.args])
        raise SpecError(f"unsupported expression element {type(nd).__name__}")

    def _call(self, fn, args):
        n = self.n
        a = args[0] if args else [0.0] * n
        if fn == "prev":                        # last period's value, 0 at the start
            return [0.0] + a[:-1]
        if fn == "cumul":                       # running total — reserves, cash
            out, s = [], 0.0
            for x in a:
                s += x
                out.append(s)
            return out
        if fn == "total":                       # sum across periods, broadcast
            return [sum(a)] * n
        if fn == "peak":
            return [max(a)] * n
        if fn == "first":
            return [a[0]] * n
        if fn == "last":
            return [a[-1]] * n
        if fn == "npv":
            r = args[0][0]
            f = args[1]
            return [sum(x / (1 + r) ** (i + 1) for i, x in enumerate(f))] * n
        if fn == "irr":
            return [_irr(a) or 0.0] * n
        if fn == "abs":
            return [abs(x) for x in a]
        if fn == "round":
            d = int(args[1][0]) if len(args) > 1 else 0
            return [round(x, d) for x in a]
        if fn in ("min", "max"):
            f = min if fn == "min" else max
            return [f(*[g[i] for g in args]) for i in range(n)]
        if fn == "clamp":
            lo, hi = args[1], args[2]
            return [max(lo[i], min(hi[i], a[i])) for i in range(n)]
        if fn == "where":
            c, x, y = args[0], args[1], args[2]
            return [x[i] if c[i] else y[i] for i in range(n)]
        raise SpecError(f"unknown function {fn}()")


def _irr(flows, lo=-0.9999, hi=10.0):
    f = lambda r: sum(x / (1 + r) ** i for i, x in enumerate(flows))
    try:
        a, b = f(lo), f(hi)
    except ZeroDivisionError:
        return None
    if a * b > 0:
        return None
    for _ in range(200):
        m = (lo + hi) / 2
        v = f(m)
        if abs(v) < 1e-9:
            return m
        if a * v < 0:
            hi = m
        else:
            lo, a = m, v
    return (lo + hi) / 2


# ---------------------------------------------------------------------- spec io

def load_spec(path):
    """Load the spec, and fail like a human when the YAML is malformed.

    The person editing this file is a founder, not a YAML programmer. A raw parser
    traceback tells them nothing and makes the tool feel like it broke rather than
    like they typed a colon. Point at the line and name the usual cause.
    """
    try:
        with open(path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)
    except yaml.YAMLError as e:
        mark = getattr(e, "problem_mark", None)
        where = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        problem = getattr(e, "problem", str(e))
        hint = ""
        if mark:
            try:
                line = open(path, encoding="utf-8").read().splitlines()[mark.line]
                hint = f"\n\n  {mark.line + 1} | {line.strip()[:100]}"
                if ":" in line.split("#")[0].strip()[1:]:
                    hint += ("\n\n  Most likely: a colon inside unquoted text. YAML reads "
                             "`note: it is a grant: not income` as a mapping.\n  Wrap the "
                             "text in quotes, or start it with `>` on its own line.")
            except Exception:
                pass
        raise SpecError(f"{path} is not valid YAML{where}: {problem}{hint}")
    if not isinstance(spec, dict):
        raise SpecError("spec must be a YAML mapping (key: value pairs at the top level)")
    spec.setdefault("meta", {})
    spec.setdefault("drivers", {})
    spec.setdefault("lines", {})
    spec.setdefault("outputs", {})
    spec.setdefault("thresholds", [])
    spec.setdefault("scenarios", {})
    return spec


def n_periods(spec):
    p = spec["meta"].get("periods", {})
    if isinstance(p, dict) and p.get("count"):
        return int(p["count"])
    for d in spec["drivers"].values():
        if isinstance(d.get("values"), list):
            return len(d["values"])
    return 3


def period_labels(spec):
    n = n_periods(spec)
    p = spec["meta"].get("periods", {}) or {}
    start, unit = p.get("start"), (p.get("unit") or "year")
    if isinstance(start, int):
        return [str(start + i) for i in range(n)]
    return [f"{unit.title()[:1]}{i+1}" for i in range(n)]


def validate(spec):
    """Report every problem at once. A founder editing YAML deserves the whole
    list, not a fix-one-rerun loop."""
    errs, warns = [], []
    n = n_periods(spec)
    keys = set(spec["drivers"]) | set(spec["lines"]) | set(spec["outputs"])
    derived = set(DERIVED)

    for k, d in spec["drivers"].items():
        if not isinstance(d, dict):
            errs.append(f"driver {k}: must be a mapping"); continue
        if "values" not in d and "value" not in d:
            errs.append(f"driver {k}: needs `value:` or `values:`")
        if (g := d.get("grade")) and g not in GRADES:
            errs.append(f"driver {k}: grade {g!r} not in {GRADES}")
        if (s := d.get("deal_stage")) and s not in DEAL_STAGES:
            errs.append(f"driver {k}: deal_stage {s!r} not in {DEAL_STAGES}")
        if isinstance(d.get("values"), list) and len(d["values"]) not in (1, n):
            warns.append(f"driver {k}: {len(d['values'])} values for {n} periods "
                         f"(last value will repeat)")
        if not d.get("grade") and not d.get("source"):
            warns.append(f"driver {k}: no grade and no source — it will read as a guess")

    for group in ("lines", "outputs"):
        for k, ln in spec[group].items():
            if not isinstance(ln, dict):
                errs.append(f"{group[:-1]} {k}: must be a mapping"); continue
            if "formula" not in ln and "values" not in ln and "value" not in ln:
                errs.append(f"{group[:-1]} {k}: needs `formula:` or `values:`")
            if (f := ln.get("formula")):
                try:
                    for nm in expr_names(f):
                        if nm not in keys and nm not in derived:
                            errs.append(f"{group[:-1]} {k}: formula references unknown "
                                        f"{nm!r}")
                except SpecError as e:
                    errs.append(f"{group[:-1]} {k}: {e}")
            if group == "lines":
                c = ln.get("category")
                if c and c not in ALL_CATS:
                    errs.append(f"line {k}: category {c!r} not in {ALL_CATS}")
                if not c:
                    warns.append(f"line {k}: no category — excluded from income/cost totals")

    for t in spec["thresholds"]:
        if not isinstance(t, dict) or "test" not in t:
            errs.append(f"threshold {t!r}: needs `name:` and `test:`")
            continue
        try:
            for nm in expr_names(t["test"]):
                if nm not in keys and nm not in derived:
                    errs.append(f"threshold {t.get('name')}: unknown {nm!r} in test")
        except SpecError as e:
            errs.append(f"threshold {t.get('name')}: {e}")

    for sname, sc in spec["scenarios"].items():
        for k in (sc.get("overrides") or {}):
            if k not in spec["drivers"]:
                errs.append(f"scenario {sname}: overrides unknown driver {k!r}")
    return errs, warns


# Derived automatically when lines carry categories. The point: "when do we stop
# needing grants?" is the question this sector actually asks, so the model should
# answer it without anyone having to wire it up.
DERIVED = {
    "total_earned": "sum of lines with category: earned",
    "total_grant": "sum of lines with category: grant",
    "total_investment": "sum of lines with category: investment",
    "total_inkind": "sum of lines with category: inkind",
    "total_income": "all income categories",
    "total_costs": "sum of lines with category: cost",
    "net": "total_income - total_costs",
    "net_excl_grants": "total_income - total_grant - total_costs",
    "grant_dependency": "total_grant / total_income",
    "earned_ratio": "total_earned / total_income",
    "cumulative_net": "running total of net",
}


def compute(spec, overrides=None):
    """Evaluate the whole model. Overrides swap driver values without touching the
    spec, which is what makes sensitivity and scenarios cheap."""
    n = n_periods(spec)
    overrides = overrides or {}
    values = {}

    for k, d in spec["drivers"].items():
        raw = overrides.get(k, d.get("values", d.get("value")))
        values[k] = vec(raw, n)

    # Lines and outputs may reference each other, so resolve iteratively rather
    # than demand the author order them correctly.
    pending = {}
    for group in ("lines", "outputs"):
        for k, ln in spec[group].items():
            if "formula" in ln:
                pending[k] = ln["formula"]
            else:
                values[k] = vec(ln.get("values", ln.get("value")), n)

    _add_derived(spec, values, n)
    for _ in range(len(pending) + 2):
        if not pending:
            break
        progressed = False
        for k in list(pending):
            try:
                values[k] = Engine(n, values).eval(pending[k])
                del pending[k]
                progressed = True
                _add_derived(spec, values, n)
            except SpecError:
                continue
        if not progressed:
            break
    if pending:
        raise SpecError(
            "could not resolve: " + ", ".join(f"{k} ({v})" for k, v in pending.items())
            + " — check for a circular reference or an unknown name")
    _add_derived(spec, values, n, final=True)

    res = {
        "meta": spec.get("meta", {}),
        "periods": period_labels(spec),
        "n": n,
        "values": {k: [round(x, 6) for x in v] for k, v in values.items()},
        "thresholds": [],
    }
    for t in spec["thresholds"]:
        try:
            v = Engine(n, values).eval(t["test"])
            pp = [bool(x) for x in v]
            # "Reaches break-even" and "never runs out of cash" are different
            # questions, and reporting both as "met" would hide the breach that
            # matters. Record the pattern, not a verdict.
            res["thresholds"].append({
                "name": t.get("name"), "test": t["test"],
                "meaning": t.get("meaning"),
                "per_period": pp,
                "met_any": any(pp), "met_all": all(pp),
                "first_met": next((i for i, x in enumerate(pp) if x), None),
                "first_breach": next((i for i, x in enumerate(pp) if not x), None),
                "breaches_after_met": bool(
                    any(pp) and not all(pp)
                    and (bi := next((i for i, x in enumerate(pp) if not x), None)) is not None
                    and (fm := next((i for i, x in enumerate(pp) if x), None)) is not None
                    and bi > fm),
            })
        except SpecError as e:
            res["thresholds"].append({"name": t.get("name"), "error": str(e)})
    return res


def _cat_sum(spec, values, cats, n):
    out = [0.0] * n
    for k, ln in spec["lines"].items():
        if ln.get("category") in cats and k in values:
            out = _bin(lambda x, y: x + y, out, values[k])
    return out


def _add_derived(spec, values, n, final=False):
    """Only fill a derived name if the author has not defined it themselves."""
    def put(k, v):
        if k not in spec["drivers"] and k not in spec["lines"] and k not in spec["outputs"]:
            values[k] = v

    earned = _cat_sum(spec, values, ("earned",), n)
    grant = _cat_sum(spec, values, ("grant",), n)
    inv = _cat_sum(spec, values, ("investment",), n)
    inkind = _cat_sum(spec, values, ("inkind",), n)
    income = [earned[i] + grant[i] + inv[i] + inkind[i] for i in range(n)]
    costs = _cat_sum(spec, values, COST_CATS, n)
    net = [income[i] - costs[i] for i in range(n)]
    put("total_earned", earned); put("total_grant", grant)
    put("total_investment", inv); put("total_inkind", inkind)
    put("total_income", income); put("total_costs", costs)
    put("net", net)
    put("net_excl_grants", [income[i] - grant[i] - costs[i] for i in range(n)])
    put("grant_dependency", [_div(grant[i], income[i]) for i in range(n)])
    put("earned_ratio", [_div(earned[i], income[i]) for i in range(n)])
    c, s = [], 0.0
    for x in net:
        s += x
        c.append(s)
    put("cumulative_net", c)


# ------------------------------------------------------------------------- cli

def fmt(v, unit=None):
    a = abs(v)
    if unit == "percent":
        return f"{v*100:.1f}%"
    if a >= 1e9: return f"{v/1e9:,.2f}B"
    if a >= 1e6: return f"{v/1e6:,.2f}M"
    if a >= 1e4: return f"{v/1e3:,.0f}k"
    if a >= 1:   return f"{v:,.0f}"
    return f"{v:,.3g}"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--json", default=None, help="write full results")
    a = ap.parse_args()

    try:
        spec = load_spec(a.spec)
    except SpecError as e:
        sys.exit(f"\n{e}\n")
    errs, warns = validate(spec)
    for w in warns:
        print(f"  warn   {w}")
    for e in errs:
        print(f"  ERROR  {e}")
    if errs:
        sys.exit(f"\n{len(errs)} error(s) — model not computed.")
    if a.check:
        print(f"\nspec OK: {len(spec['drivers'])} drivers, {len(spec['lines'])} lines, "
              f"{len(spec['outputs'])} outputs, {n_periods(spec)} periods")
        return

    res = compute(spec)
    per = res["periods"]
    print(f"\n{spec['meta'].get('name', a.spec)}   ({spec['meta'].get('currency','')})")
    print(f"{'':34}" + "".join(f"{p:>13}" for p in per))
    print("-" * (34 + 13 * len(per)))

    def row(label, key, unit=None):
        if key not in res["values"]:
            return
        v = res["values"][key]
        print(f"{label[:33]:34}" + "".join(f"{fmt(x, unit):>13}" for x in v))

    for cat, title in (("earned", "Earned income"), ("grant", "Grants"),
                       ("investment", "Investment"), ("inkind", "In-kind")):
        ks = [k for k, l in spec["lines"].items() if l.get("category") == cat]
        for k in ks:
            row("  " + (spec["lines"][k].get("label") or k), k)
    row("TOTAL INCOME", "total_income")
    for k, l in spec["lines"].items():
        if l.get("category") == "cost":
            row("  " + (l.get("label") or k), k)
    row("TOTAL COSTS", "total_costs")
    row("NET", "net")
    row("Cumulative net", "cumulative_net")
    row("Grant dependency", "grant_dependency", "percent")

    impact = [k for k, l in spec["lines"].items() if l.get("category") == "impact"]
    if impact:
        print()
        for k in impact:
            row((spec["lines"][k].get("label") or k), k, spec["lines"][k].get("unit"))

    if spec["outputs"]:
        print()
        for k, o in spec["outputs"].items():
            row((o.get("label") or k), k, o.get("unit"))

    if res["thresholds"]:
        print("\nThresholds")
        for t in res["thresholds"]:
            if t.get("error"):
                print(f"  {t['name']}: ERROR {t['error']}"); continue
            if t["met_all"]:
                mark, when = "OK    ", "every period"
            elif not t["met_any"]:
                mark, when = "NO    ", "never"
            elif t["breaches_after_met"]:
                # The dangerous case: it looks achieved, then fails later.
                mark = "BREACH"
                when = (f"holds {per[t['first_met']]}, then fails from "
                        f"{per[t['first_breach']]}")
            else:
                mark, when = "OK    ", f"from {per[t['first_met']]}"
            print(f"  {mark}  {t['name']:<34} {when}")
            if t.get("meaning"):
                print(f"          {t['meaning']}")

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, indent=1)
        print(f"\n-> {a.json}")


if __name__ == "__main__":
    main()
