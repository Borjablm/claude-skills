#!/usr/bin/env python3
"""Parse a spreadsheet financial model into a typed dependency graph.

Why this exists: everything downstream (assumption extraction, audit checks,
sensitivity, scenarios) needs to know which cells are inputs, which are computed,
what each one *means*, and what depends on what. Reading the .xlsx once into an
explicit graph makes those questions cheap and keeps the rest of the toolkit from
re-parsing spreadsheets.

The evaluator handles the formula subset that driver-based venture models actually
use (arithmetic, percentages, cross-sheet references, SUM/ROUND/IF/MIN/MAX/...).
It is deliberately NOT a full Excel engine. Run with --verify to recompute every
formula and compare against the values Excel cached: if the graph reproduces the
workbook, downstream analysis can be trusted; if it doesn't, you'll see exactly
which cells are unsupported before you rely on any numbers.

Usage:
    python model_graph.py MODEL.xlsx --out model/graph.json [--verify]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter, column_index_from_string
except ImportError:
    sys.exit("openpyxl is required:  python -m pip install openpyxl")

# ---------------------------------------------------------------- tokenizer

TOKEN_RE = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<string>"(?:[^"]|"")*")
  | (?P<ref>(?:'[^']+'|[A-Za-z_][A-Za-z0-9_.]*)!\$?[A-Z]{1,3}\$?[0-9]+
            (?::\$?[A-Z]{1,3}\$?[0-9]+)?
     |\$?[A-Z]{1,3}\$?[0-9]+(?::\$?[A-Z]{1,3}\$?[0-9]+)?)
  | (?P<func>[A-Za-z_][A-Za-z0-9_.]*(?=\s*\())
  | (?P<bool>\b(?:TRUE|FALSE)\b)
  | (?P<name>[A-Za-z_\\][A-Za-z0-9_.\\]*)
  | (?P<number>[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?%?)
  | (?P<op><=|>=|<>|[-+*/^&=<>])
  | (?P<lparen>\()
  | (?P<rparen>\))
  | (?P<comma>[,;])
    """,
    re.VERBOSE | re.IGNORECASE,
)


class Tok:
    __slots__ = ("kind", "text")

    def __init__(self, kind, text):
        self.kind, self.text = kind, text

    def __repr__(self):
        return f"{self.kind}:{self.text}"


def tokenize(formula: str):
    pos, out = 0, []
    while pos < len(formula):
        m = TOKEN_RE.match(formula, pos)
        if not m:
            raise ValueError(f"cannot tokenize at {pos}: {formula[pos:pos+18]!r}")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        out.append(Tok(kind, m.group()))
    return out


# ---------------------------------------------------------------- AST nodes
# Kept as plain dicts so the graph serializes to JSON and a future transpiler can
# walk the same structure without importing this module.

def n_num(v):        return {"t": "num", "v": v}
def n_str(v):        return {"t": "str", "v": v}
def n_bool(v):       return {"t": "bool", "v": v}
def n_ref(key):      return {"t": "ref", "key": key}
def n_range(keys, rows=None, cols=None):
    # Shape is kept because lookups (VLOOKUP/INDEX/MATCH) need the rectangle, not
    # just the members.
    return {"t": "range", "keys": keys, "rows": rows, "cols": cols}
def n_bin(op, a, b): return {"t": "bin", "op": op, "a": a, "b": b}
def n_un(op, a):     return {"t": "un", "op": op, "a": a}
def n_func(name, a): return {"t": "func", "name": name.upper(), "args": a}


# ---------------------------------------------------------------- parser

CELL_RE = re.compile(r"^(?:(?:'([^']+)'|([A-Za-z_][A-Za-z0-9_.]*))!)?\$?([A-Z]{1,3})\$?([0-9]+)$")
RANGE_RE = re.compile(
    r"^(?:(?:'([^']+)'|([A-Za-z_][A-Za-z0-9_.]*))!)?"
    r"\$?([A-Z]{1,3})\$?([0-9]+):\$?([A-Z]{1,3})\$?([0-9]+)$"
)


def cell_key(sheet: str, col: str, row) -> str:
    return f"{sheet}!{col.upper()}{row}"


class Parser:
    """Recursive-descent parser for the Excel formula subset.

    `names` maps defined names to their reference text. Named ranges are a mark of
    a carefully built model (=Revenue*Growth reads better than =B2*$B$4), so a
    parser that cannot resolve them fails hardest on the best-maintained files.
    """

    def __init__(self, tokens, default_sheet, names=None):
        self.toks, self.i, self.sheet = tokens, 0, default_sheet
        self.names = names or {}

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def eat(self, kind=None, text=None):
        t = self.peek()
        if t is None or (kind and t.kind != kind) or (text and t.text.upper() != text):
            raise ValueError(f"expected {kind or text}, got {t}")
        self.i += 1
        return t

    def parse(self):
        node = self.comparison()
        if self.peek():
            raise ValueError(f"trailing tokens: {self.toks[self.i:]}")
        return node

    def comparison(self):
        node = self.concat()
        while (t := self.peek()) and t.kind == "op" and t.text in ("=", "<>", "<", ">", "<=", ">="):
            self.i += 1
            node = n_bin(t.text, node, self.concat())
        return node

    def concat(self):
        node = self.additive()
        while (t := self.peek()) and t.kind == "op" and t.text == "&":
            self.i += 1
            node = n_bin("&", node, self.additive())
        return node

    def additive(self):
        node = self.multiplicative()
        while (t := self.peek()) and t.kind == "op" and t.text in ("+", "-"):
            self.i += 1
            node = n_bin(t.text, node, self.multiplicative())
        return node

    def multiplicative(self):
        node = self.unary()
        while (t := self.peek()) and t.kind == "op" and t.text in ("*", "/"):
            self.i += 1
            node = n_bin(t.text, node, self.unary())
        return node

    def unary(self):
        t = self.peek()
        if t and t.kind == "op" and t.text in ("-", "+"):
            self.i += 1
            return n_un(t.text, self.unary())
        return self.power()

    def power(self):
        node = self.primary()
        if (t := self.peek()) and t.kind == "op" and t.text == "^":
            self.i += 1
            return n_bin("^", node, self.unary())
        return node

    def primary(self):
        t = self.peek()
        if t is None:
            raise ValueError("unexpected end of formula")
        if t.kind == "number":
            self.i += 1
            txt = t.text
            return n_num(float(txt[:-1]) / 100.0 if txt.endswith("%") else float(txt))
        if t.kind == "string":
            self.i += 1
            return n_str(t.text[1:-1].replace('""', '"'))
        if t.kind == "bool":
            self.i += 1
            return n_bool(t.text.upper() == "TRUE")
        if t.kind == "func":
            self.i += 1
            name = t.text
            self.eat("lparen")
            args = []
            if not ((p := self.peek()) and p.kind == "rparen"):
                args.append(self.comparison())
                while (p := self.peek()) and p.kind == "comma":
                    self.i += 1
                    args.append(self.comparison())
            self.eat("rparen")
            return n_func(name, args)
        if t.kind == "lparen":
            self.i += 1
            node = self.comparison()
            self.eat("rparen")
            return node
        if t.kind == "ref":
            self.i += 1
            return self.make_ref(t.text)
        if t.kind == "name":
            self.i += 1
            key = t.text.lstrip("\\")
            target = self.names.get(key) or self.names.get(key.upper())
            if target is None:
                raise ValueError(f"unknown name {t.text!r} (not a defined name)")
            return self.make_ref(target)
        raise ValueError(f"unexpected token {t}")

    def make_ref(self, text):
        text = text.replace("$", "") if False else text
        if (m := RANGE_RE.match(text)):
            sheet = m.group(1) or m.group(2) or self.sheet
            c1, r1, c2, r2 = m.group(3), int(m.group(4)), m.group(5), int(m.group(6))
            ci1, ci2 = column_index_from_string(c1), column_index_from_string(c2)
            r_lo, r_hi = min(r1, r2), max(r1, r2)
            c_lo, c_hi = min(ci1, ci2), max(ci1, ci2)
            keys = [
                cell_key(sheet, get_column_letter(c), r)
                for r in range(r_lo, r_hi + 1)
                for c in range(c_lo, c_hi + 1)
            ]
            return n_range(keys, rows=r_hi - r_lo + 1, cols=c_hi - c_lo + 1)
        if (m := CELL_RE.match(text)):
            sheet = m.group(1) or m.group(2) or self.sheet
            return n_ref(cell_key(sheet, m.group(3), int(m.group(4))))
        raise ValueError(f"bad reference {text!r}")


def parse_formula(formula: str, default_sheet: str, names=None):
    body = formula[1:] if formula.startswith("=") else formula
    return Parser(tokenize(body), default_sheet, names).parse()


def extract_names(wb):
    """Defined names → their reference text, so the parser can resolve them."""
    out = {}
    try:
        items = list(wb.defined_names.items())
    except Exception:
        return out
    for name, dn in items:
        try:
            txt = getattr(dn, "attr_text", None) or getattr(dn, "value", None)
            if txt and "!" in str(txt) and "#REF" not in str(txt):
                out[name] = str(txt).replace("$", "")
        except Exception:
            continue
    # Sheet-scoped names live on the worksheet, not the workbook.
    for ws in getattr(wb, "worksheets", []):
        try:
            for name, dn in getattr(ws, "defined_names", {}).items():
                txt = getattr(dn, "attr_text", None) or getattr(dn, "value", None)
                if txt and "#REF" not in str(txt):
                    t = str(txt).replace("$", "")
                    out.setdefault(name, t if "!" in t else f"{ws.title}!{t}")
        except Exception:
            continue
    return out


def ast_refs(node, out=None, direct_only=False):
    """Every cell key an AST touches — this is what makes the dependency graph.

    direct_only skips range members. A formula naming an empty cell is a defect;
    a SUM range spanning empty rows is ordinary, so the two need separating.
    """
    out = set() if out is None else out
    t = node["t"]
    if t == "ref":
        out.add(node["key"])
    elif t == "range":
        if not direct_only:
            out.update(node["keys"])
    elif t == "bin":
        ast_refs(node["a"], out, direct_only); ast_refs(node["b"], out, direct_only)
    elif t == "un":
        ast_refs(node["a"], out, direct_only)
    elif t == "func":
        for a in node["args"]:
            ast_refs(a, out, direct_only)
    return out


# ---------------------------------------------------------------- evaluator

class CircularReference(Exception):
    pass


def _num(v):
    if v is None or v == "":
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _flatten(vals):
    out = []
    for v in vals:
        out.extend(v) if isinstance(v, list) else out.append(v)
    return out


class Evaluator:
    """Lazy, memoized evaluation over the cell graph.

    Overrides let sensitivity and scenario runs reuse one graph: pass
    {cell_key: new_value} and everything downstream recomputes without touching
    the source file.
    """

    def __init__(self, cells, overrides=None):
        self.cells = cells
        self.overrides = overrides or {}
        self.cache = {}
        self.stack = set()
        self.errors = {}

    def value(self, key):
        if key in self.overrides:
            return self.overrides[key]
        if key in self.cache:
            return self.cache[key]
        if key in self.stack:
            raise CircularReference(key)
        cell = self.cells.get(key)
        if cell is None:
            return 0.0
        if cell.get("ast") is None:
            v = cell.get("value")
            self.cache[key] = v
            return v
        self.stack.add(key)
        try:
            v = self.eval(cell["ast"], key)
        except CircularReference:
            raise
        except Exception as e:  # a single unsupported cell must not kill the run
            self.errors[key] = f"{type(e).__name__}: {e}"
            v = None
        finally:
            self.stack.discard(key)
        self.cache[key] = v
        return v

    def eval(self, node, ctx):
        t = node["t"]
        if t in ("num", "str", "bool"):
            return node["v"]
        if t == "ref":
            return self.value(node["key"])
        if t == "range":
            return [self.value(k) for k in node["keys"]]
        if t == "un":
            v = _num(self.eval(node["a"], ctx))
            return -v if node["op"] == "-" else v
        if t == "bin":
            return self._binary(node, ctx)
        if t == "func":
            return self._call(node, ctx)
        raise ValueError(f"unknown node {t}")

    def _binary(self, node, ctx):
        op = node["op"]
        a, b = self.eval(node["a"], ctx), self.eval(node["b"], ctx)
        if op == "&":
            fmt = lambda x: "" if x is None else (f"{x:g}" if isinstance(x, float) else str(x))
            return fmt(a) + fmt(b)
        if op in ("=", "<>", "<", ">", "<=", ">="):
            if isinstance(a, str) or isinstance(b, str):
                a, b = str(a or "").upper(), str(b or "").upper()
            else:
                a, b = _num(a), _num(b)
            return {"=": a == b, "<>": a != b, "<": a < b,
                    ">": a > b, "<=": a <= b, ">=": a >= b}[op]
        x, y = _num(a), _num(b)
        if op == "+": return x + y
        if op == "-": return x - y
        if op == "*": return x * y
        if op == "/":
            if y == 0:
                self.errors[ctx] = "#DIV/0!"
                return None
            return x / y
        if op == "^": return x ** y
        raise ValueError(f"unknown operator {op}")

    def _raw_range(self, node, ctx):
        """Values plus shape — lookups need the rectangle, not a flat list."""
        if node["t"] != "range":
            return [[self.eval(node, ctx)]], 1, 1
        vals = [self.value(k) for k in node["keys"]]
        rows = node.get("rows") or len(vals)
        cols = node.get("cols") or 1
        grid = [vals[i * cols:(i + 1) * cols] for i in range(rows)]
        return grid, rows, cols

    def _call(self, node, ctx):
        name, args = node["name"], node["args"]
        # Lazy forms first: these must not evaluate every argument up front.
        if name == "IF":
            cond = self.eval(args[0], ctx)
            truthy = bool(cond) if isinstance(cond, bool) else _num(cond) != 0
            if truthy:
                return self.eval(args[1], ctx)
            return self.eval(args[2], ctx) if len(args) > 2 else False
        if name in ("AND", "OR"):
            flat = _flatten([self.eval(a, ctx) for a in args])
            tests = [bool(v) if isinstance(v, bool) else _num(v) != 0
                     for v in flat if v is not None]
            return all(tests) if name == "AND" else any(tests)
        if name == "NOT":
            v = self.eval(args[0], ctx)
            return not (bool(v) if isinstance(v, bool) else _num(v) != 0)
        if name in ("VLOOKUP", "HLOOKUP"):
            return self._lookup(name, args, ctx)
        if name in ("SUMIF", "SUMIFS", "COUNTIF", "COUNTIFS", "AVERAGEIF"):
            return self._conditional(name, args, ctx)
        if name == "INDEX":
            grid, rows, cols = self._raw_range(args[0], ctx)
            r = int(_num(self.eval(args[1], ctx)))
            c = int(_num(self.eval(args[2], ctx))) if len(args) > 2 else 1
            if rows == 1 and len(args) < 3:      # single row: arg is the column
                r, c = 1, r
            elif cols == 1 and len(args) < 3:
                c = 1
            try:
                return grid[r - 1][c - 1]
            except IndexError:
                raise ValueError("INDEX out of range")
        if name == "MATCH":
            target = self.eval(args[0], ctx)
            grid, rows, cols = self._raw_range(args[1], ctx)
            flat = [v for row in grid for v in row]
            typ = int(_num(self.eval(args[2], ctx))) if len(args) > 2 else 1
            return self._match(target, flat, typ)
        if name in ("NPV", "XNPV"):
            rate = _num(self.eval(args[0], ctx))
            flows = [_num(v) for v in _flatten([self.eval(a, ctx) for a in args[1:]])
                     if v is not None and not isinstance(v, str)]
            return sum(f / (1 + rate) ** (i + 1) for i, f in enumerate(flows))
        if name in ("IRR", "XIRR"):
            flows = [_num(v) for v in _flatten([self.eval(args[0], ctx)])
                     if v is not None and not isinstance(v, str)]
            return self._irr(flows)
        vals = [self.eval(a, ctx) for a in args]
        flat = [v for v in _flatten(vals) if v is not None and v != ""]
        nums = [_num(v) for v in flat if not isinstance(v, str)]
        if name == "SUM":     return sum(nums)
        if name == "PRODUCT":
            p = 1.0
            for v in nums: p *= v
            return p
        if name == "AVERAGE": return sum(nums) / len(nums) if nums else None
        if name in ("MIN", "MINA"): return min(nums) if nums else 0.0
        if name in ("MAX", "MAXA"): return max(nums) if nums else 0.0
        if name == "COUNT":   return float(len(nums))
        if name == "COUNTA":  return float(len(flat))
        if name == "ABS":     return abs(_num(vals[0]))
        if name == "SQRT":    return _num(vals[0]) ** 0.5
        if name == "POWER":   return _num(vals[0]) ** _num(vals[1])
        if name == "ROUND":
            v, d = _num(vals[0]), int(_num(vals[1])) if len(vals) > 1 else 0
            # Excel rounds half away from zero; Python's round() is banker's rounding.
            f = 10 ** d
            x = v * f
            r = float(int(x + (0.5 if x >= 0 else -0.5)))
            return r / f
        if name in ("ROUNDUP", "ROUNDDOWN"):
            import math
            v, d = _num(vals[0]), int(_num(vals[1])) if len(vals) > 1 else 0
            f = 10 ** d
            fn = math.ceil if name == "ROUNDUP" else math.floor
            return (fn(abs(v) * f) / f) * (1 if v >= 0 else -1)
        if name == "SUMPRODUCT":
            arrs = [v if isinstance(v, list) else [v] for v in vals]
            return sum(
                _num(x := 1) or 0 for _ in [0]
            ) if not arrs else sum(
                __import__("math").prod(_num(a[i]) for a in arrs) for i in range(len(arrs[0]))
            )
        if name == "IFERROR":
            return vals[0] if vals[0] is not None else (vals[1] if len(vals) > 1 else None)
        if name == "MEDIAN":
            s = sorted(nums)
            n = len(s)
            if not n:
                return None
            return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2
        raise ValueError(f"unsupported function {name}()")

    # -- lookup / conditional helpers ------------------------------------------

    def _match(self, target, flat, typ):
        if typ == 0:
            for i, v in enumerate(flat):
                if (isinstance(v, str) and isinstance(target, str)
                        and v.upper() == target.upper()) or v == target:
                    return float(i + 1)
            raise ValueError("MATCH: no exact match")
        t = _num(target)
        best = None
        for i, v in enumerate(flat):
            if isinstance(v, str) or v is None:
                continue
            n = _num(v)
            if typ == 1 and n <= t:
                best = i + 1
            elif typ == -1 and n >= t:
                best = i + 1
        if best is None:
            raise ValueError("MATCH: no match")
        return float(best)

    def _lookup(self, name, args, ctx):
        target = self.eval(args[0], ctx)
        grid, rows, cols = self._raw_range(args[1], ctx)
        idx = int(_num(self.eval(args[2], ctx)))
        approx = True
        if len(args) > 3:
            a = self.eval(args[3], ctx)
            approx = bool(a) if isinstance(a, bool) else _num(a) != 0
        if name == "HLOOKUP":
            grid = [list(r) for r in zip(*grid)]  # transpose: search the first row
            rows, cols = cols, rows
        keys = [r[0] for r in grid]
        try:
            pos = int(self._match(target, keys, 1 if approx else 0))
        except ValueError:
            return None  # #N/A
        try:
            return grid[pos - 1][idx - 1]
        except IndexError:
            raise ValueError(f"{name}: column {idx} outside range")

    def _criteria(self, crit):
        """Excel criteria: ">0", "<=5", "income", "*text*"."""
        if isinstance(crit, str):
            s = crit.strip()
            m = re.match(r"^(<=|>=|<>|=|<|>)\s*(.*)$", s)
            if m:
                op, rhs = m.group(1), m.group(2)
                try:
                    rv = float(rhs)
                    return lambda v: (not isinstance(v, str)) and _compare(_num(v), op, rv)
                except ValueError:
                    return lambda v: _compare_str(str(v or "").upper(), op, rhs.upper())
            return lambda v: str(v or "").upper() == s.upper()
        cv = _num(crit)
        return lambda v: (not isinstance(v, str)) and _num(v) == cv

    def _conditional(self, name, args, ctx):
        def flat(node):
            g, _, _ = self._raw_range(node, ctx)
            return [v for row in g for v in row]
        if name in ("SUMIF", "AVERAGEIF", "COUNTIF"):
            rng = flat(args[0])
            test = self._criteria(self.eval(args[1], ctx))
            if name == "COUNTIF":
                return float(sum(1 for v in rng if test(v)))
            target = flat(args[2]) if len(args) > 2 else rng
            picked = [_num(target[i]) for i, v in enumerate(rng)
                      if test(v) and i < len(target)]
            if name == "SUMIF":
                return sum(picked)
            return sum(picked) / len(picked) if picked else None
        # SUMIFS(sum_range, crit_range1, crit1, ...) / COUNTIFS(crit_range1, crit1, ...)
        if name == "SUMIFS":
            target, pairs = flat(args[0]), args[1:]
        else:
            target, pairs = None, args
        conds = []
        for i in range(0, len(pairs) - 1, 2):
            conds.append((flat(pairs[i]), self._criteria(self.eval(pairs[i + 1], ctx))))
        n = len(conds[0][0]) if conds else 0
        hits = [i for i in range(n) if all(t(r[i]) for r, t in conds if i < len(r))]
        if name == "COUNTIFS":
            return float(len(hits))
        return sum(_num(target[i]) for i in hits if i < len(target))

    def _irr(self, flows, lo=-0.9999, hi=10.0):
        """Bisection: no dependency, and converges for ordinary cash-flow shapes."""
        def npv(r):
            return sum(f / (1 + r) ** i for i, f in enumerate(flows))
        try:
            f_lo, f_hi = npv(lo), npv(hi)
        except ZeroDivisionError:
            return None
        if f_lo * f_hi > 0:
            return None  # no sign change: IRR undefined, like Excel's #NUM!
        for _ in range(200):
            mid = (lo + hi) / 2
            v = npv(mid)
            if abs(v) < 1e-9:
                return mid
            if f_lo * v < 0:
                hi, f_hi = mid, v
            else:
                lo, f_lo = mid, v
        return (lo + hi) / 2


def _compare(a, op, b):
    return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b,
            "=": a == b, "<>": a != b}[op]


def _compare_str(a, op, b):
    return {"=": a == b, "<>": a != b, "<": a < b, ">": a > b,
            "<=": a <= b, ">=": a >= b}[op]


# ---------------------------------------------------------------- graph build

LABEL_MIN_LEN = 2


def _is_text(v):
    return isinstance(v, str) and len(v.strip()) >= LABEL_MIN_LEN


def build_graph(path: Path, verify=False):
    wb_f = load_workbook(path, data_only=False)
    wb_v = load_workbook(path, data_only=True)

    cells = {}
    sheets = wb_f.sheetnames
    names = extract_names(wb_f)

    for name in sheets:
        ws_f, ws_v = wb_f[name], wb_v[name]
        for row_f, row_v in zip(ws_f.iter_rows(), ws_v.iter_rows()):
            for cf, cv in zip(row_f, row_v):
                if cf.value is None and cv.value is None:
                    continue
                key = f"{name}!{cf.coordinate}"
                raw = cf.value
                is_formula = isinstance(raw, str) and raw.startswith("=")
                entry = {
                    "sheet": name,
                    "ref": cf.coordinate,
                    "row": cf.row,
                    "col": cf.column,
                    "value": cv.value,
                    "cached": cv.value,
                    "formula": raw if is_formula else None,
                    "ast": None,
                    "deps": [],
                    "dependents": [],
                    "number_format": cf.number_format,
                    "note": cf.comment.text.strip() if cf.comment else None,
                }
                if is_formula:
                    try:
                        ast = parse_formula(raw, name, names)
                        entry["ast"] = ast
                        entry["deps"] = sorted(ast_refs(ast))
                        entry["direct_deps"] = sorted(ast_refs(ast, direct_only=True))
                        entry["kind"] = "formula"
                    except Exception as e:
                        entry["kind"] = "formula"
                        entry["parse_error"] = str(e)
                elif _is_text(raw):
                    entry["kind"] = "label"
                    entry["value"] = raw
                elif isinstance(raw, (int, float, bool)):
                    entry["kind"] = "input"
                    entry["value"] = float(raw) if isinstance(raw, (int, float)) else raw
                else:
                    entry["kind"] = "other"
                cells[key] = entry

    # reverse edges
    for key, c in cells.items():
        for d in c["deps"]:
            if d in cells:
                cells[d]["dependents"].append(key)
    for c in cells.values():
        c["dependents"] = sorted(set(c["dependents"]))

    _attach_labels(cells)

    graph = {
        "source": str(path),
        "sheets": sheets,
        "defined_names": names,
        "cells": cells,
        "stats": {
            "cells": len(cells),
            "formulas": sum(1 for c in cells.values() if c["kind"] == "formula"),
            "inputs": sum(1 for c in cells.values() if c["kind"] == "input"),
            "labels": sum(1 for c in cells.values() if c["kind"] == "label"),
            "parse_errors": sum(1 for c in cells.values() if "parse_error" in c),
        },
    }
    graph["outputs"] = _find_outputs(cells)
    if verify:
        graph["verification"] = verify_graph(cells)
    return graph


def _attach_labels(cells):
    """Infer what each cell means from its row and column headers.

    Spreadsheets encode meaning in layout: the text to the left of a number names
    it, the text above names its period. Recovering that is what lets the ledger
    say "Average item price / Y2" instead of "Rev!C8".
    """
    by_sheet = {}
    for key, c in cells.items():
        by_sheet.setdefault(c["sheet"], []).append(c)

    for sheet, items in by_sheet.items():
        labels = {(c["row"], c["col"]): c["value"] for c in items if c["kind"] == "label"}
        max_col = max((c["col"] for c in items), default=1)
        for c in items:
            if c["kind"] not in ("input", "formula"):
                continue
            row_label = next(
                (labels[(c["row"], col)] for col in range(c["col"] - 1, 0, -1)
                 if (c["row"], col) in labels), None)
            col_label = next(
                (labels[(row, c["col"])] for row in range(c["row"] - 1, 0, -1)
                 if (row, c["col"]) in labels), None)
            # A note is text sitting to the right of the numeric block — the
            # "Notes and sources" column convention most modellers already use.
            note = next(
                (labels[(c["row"], col)] for col in range(c["col"] + 1, max_col + 1)
                 if (c["row"], col) in labels), None)
            c["row_label"] = row_label.strip() if isinstance(row_label, str) else None
            c["col_label"] = col_label.strip() if isinstance(col_label, str) else None
            c["label"] = " / ".join(x for x in (c["row_label"], c["col_label"]) if x) or None
            if note and not c.get("note"):
                c["note"] = note.strip()


# Result-cell vocabulary. Models are not written only in English, and a skill that
# silently finds no target on a Spanish or French model is worse than one that
# admits it cannot tell — hence the structural fallback below.
OUTPUT_HINTS = (
    # English
    "net profit", "net income", "profit", "ebitda", "ebit", "net margin",
    "total revenue", "npv", "irr", "cash flow", "free cash", "balance",
    "surplus", "deficit", "bottom line", "contribution", "gross margin",
    "payback", "roi", "total income", "operating income", "net result",
    # Spanish / Galician / Portuguese
    "beneficio", "resultado", "margen", "van", "tir", "ingresos totales",
    "excedente", "flujo de caja", "tesoreria", "rentabilidad", "lucro",
    # French
    "benefice", "bénéfice", "resultat net", "résultat net", "marge", "van",
    "tri", "tresorerie", "trésorerie", "flux de tresorerie",
    # German / Italian / Dutch
    "gewinn", "ergebnis", "uberschuss", "überschuss", "kapitalwert",
    "utile", "risultato", "margine", "winst", "resultaat",
)


def _find_outputs(cells):
    """Candidate result cells.

    Two passes. Labels first, because a cell called "Net profit" is almost
    certainly the answer. Then structure: in any model the result is a formula
    everything flows into and nothing flows out of. The structural pass is what
    keeps this working on a model in a language the hint list has never seen, or
    one whose author named the row something idiosyncratic.
    """
    out, seen = [], set()

    def add(key, c, why):
        if key in seen:
            return
        seen.add(key)
        out.append({
            "cell": key,
            "label": c.get("label"),
            "value": c.get("cached"),
            "depth": len(c["deps"]),
            "terminal": not c["dependents"],
            "matched": why,
        })

    for key, c in cells.items():
        if c["kind"] != "formula":
            continue
        lab = (c.get("row_label") or "").lower()
        if any(h in lab for h in OUTPUT_HINTS):
            add(key, c, "label")

    # Structural fallback: terminal formulas with the deepest dependency trees.
    if len(out) < 3:
        cands = [(key, c) for key, c in cells.items()
                 if c["kind"] == "formula" and not c["dependents"]
                 and isinstance(c.get("cached"), (int, float))
                 and not isinstance(c.get("cached"), bool)]
        cands.sort(key=lambda kc: -len(kc[1]["deps"]))
        for key, c in cands[:8]:
            add(key, c, "structure (terminal formula, deep dependency tree)")

    out.sort(key=lambda o: (o["matched"] != "label", not o["terminal"], -o["depth"]))
    return out[:20]


def verify_graph(cells, tol=0.01):
    """Recompute every formula and compare against Excel's cached values.

    This is the trust gate. Analysis built on a graph that cannot reproduce the
    workbook is analysis of a different model, so surface the mismatches loudly
    rather than quietly reporting confident numbers.
    """
    ev = Evaluator(cells)
    checked = matched = 0
    mismatches, unsupported = [], []
    for key, c in cells.items():
        if c["kind"] != "formula":
            continue
        if "parse_error" in c:
            unsupported.append({"cell": key, "reason": c["parse_error"],
                                "formula": c["formula"]})
            continue
        cached = c.get("cached")
        if not isinstance(cached, (int, float)) or isinstance(cached, bool):
            continue
        checked += 1
        try:
            got = ev.value(key)
        except CircularReference as e:
            unsupported.append({"cell": key, "reason": f"circular: {e}"})
            continue
        if got is None:
            unsupported.append({"cell": key, "reason": ev.errors.get(key, "no value"),
                                "formula": c["formula"]})
            continue
        got, exp = _num(got), float(cached)
        scale = max(1.0, abs(exp))
        if abs(got - exp) / scale <= tol:
            matched += 1
        else:
            mismatches.append({"cell": key, "formula": c["formula"],
                               "expected": exp, "computed": got})
    return {
        "checked": checked,
        "matched": matched,
        "match_rate": round(matched / checked, 4) if checked else None,
        "mismatches": mismatches[:25],
        "mismatch_count": len(mismatches),
        "unsupported": unsupported[:25],
        "unsupported_count": len(unsupported),
    }


def load_graph(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save_graph(graph, p):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=1, default=str)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx")
    ap.add_argument("--out", default="model/graph.json")
    ap.add_argument("--verify", action="store_true",
                    help="recompute formulas and compare to Excel's cached values")
    a = ap.parse_args()

    g = build_graph(Path(a.xlsx), verify=a.verify)
    save_graph(g, a.out)

    s = g["stats"]
    print(f"{g['source']}")
    print(f"  sheets     {len(g['sheets'])}: {', '.join(g['sheets'])}")
    print(f"  cells      {s['cells']}  ({s['formulas']} formulas, {s['inputs']} inputs, {s['labels']} labels)")
    if s["parse_errors"]:
        print(f"  !! {s['parse_errors']} formulas failed to parse")
    if (v := g.get("verification")):
        rate = v["match_rate"]
        print(f"  verify     {v['matched']}/{v['checked']} formulas reproduce Excel"
              f"{f' ({rate:.1%})' if rate is not None else ''}")
        for m in v["mismatches"][:5]:
            print(f"    MISMATCH {m['cell']}: expected {m['expected']:,.2f} got {m['computed']:,.2f}")
        for u in v["unsupported"][:5]:
            print(f"    UNSUPPORTED {u['cell']}: {u['reason']}")
    if g["outputs"]:
        print("  outputs (candidates):")
        for o in g["outputs"][:6]:
            print(f"    {o['cell']:36} {str(o['label'])[:44]:46} {o['value']}")
    print(f"  -> {a.out}")


if __name__ == "__main__":
    main()
