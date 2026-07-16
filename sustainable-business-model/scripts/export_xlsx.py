#!/usr/bin/env python3
"""Export the spec as a spreadsheet with live formulas.

However good the HTML is, the funder will ask for the Excel. The spreadsheet is
the exchange format of trust between organisations: the grant officer, the
accountant and the board all speak it, and a model they cannot open is a model
they will not read.

So this generates one properly, rather than pasting values: assumptions in one
labelled block with their grade and source beside them, every calculated line a
real formula pointing at those cells, and the industry blue-input/black-formula
convention a finance reader parses without being told. It is the same model, in
the language of the room.

Usage:
    python export_xlsx.py spec.yaml --out model.xlsx
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from model import (load_spec, validate, compute, n_periods, period_labels,
                   parse_expr, INCOME_CATS, SpecError)
from report import DERIVED_KEYS, resolution_order

BLUE = Font(color="0000FF")
BLACK = Font(color="000000")
BOLD = Font(bold=True)
HDR = Font(bold=True, color="FFFFFF")
HDR_FILL = PatternFill("solid", start_color="1F3864")
SUB = Font(bold=True, color="1F3864")
GRADE_FILL = {"A": PatternFill("solid", start_color="C6EFCE"),
              "B": PatternFill("solid", start_color="DDEBF7"),
              "C": PatternFill("solid", start_color="FFEB9C"),
              "D": PatternFill("solid", start_color="FFC7CE"),
              "partner": PatternFill("solid", start_color="E4DFEC")}

FUNC_MAP = {"min": "MIN", "max": "MAX", "abs": "ABS", "round": "ROUND",
            "npv": "NPV", "irr": "IRR", "total": "SUM"}


def to_xl(node, cells, col, first_col):
    """Compile a spec expression into an Excel formula for one period column.

    Only period-local expressions translate cleanly. prev()/cumul() reach across
    columns and total() collapses them, so those are handled by the caller or
    left to Python — better an honest gap than a subtly wrong formula.
    """
    if isinstance(node, ast.Constant):
        return repr(float(node.value))
    if isinstance(node, ast.Name):
        if node.id not in cells:
            raise SpecError(f"no cell for {node.id!r}")
        return f"${cells[node.id][0]}{cells[node.id][1]}".replace("$", "", 0) if False \
            else f"{col}{cells[node.id]}"
    if isinstance(node, ast.BinOp):
        op = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/",
              ast.Pow: "^", ast.Mod: "MOD"}[type(node.op)]
        a = to_xl(node.left, cells, col, first_col)
        b = to_xl(node.right, cells, col, first_col)
        if op == "MOD":
            return f"MOD({a},{b})"
        return f"({a}{op}{b})"
    if isinstance(node, ast.UnaryOp):
        v = to_xl(node.operand, cells, col, first_col)
        return f"(-{v})" if isinstance(node.op, ast.USub) else v
    if isinstance(node, ast.Compare):
        op = {ast.Lt: "<", ast.Gt: ">", ast.LtE: "<=", ast.GtE: ">=",
              ast.Eq: "=", ast.NotEq: "<>"}[type(node.ops[0])]
        return (f"({to_xl(node.left, cells, col, first_col)}{op}"
                f"{to_xl(node.comparators[0], cells, col, first_col)})")
    if isinstance(node, ast.IfExp):
        return (f"IF({to_xl(node.test, cells, col, first_col)},"
                f"{to_xl(node.body, cells, col, first_col)},"
                f"{to_xl(node.orelse, cells, col, first_col)})")
    if isinstance(node, ast.Call):
        fn = node.func.id
        if fn == "prev":
            inner = node.args[0]
            if not isinstance(inner, ast.Name):
                raise SpecError("prev() needs a plain name")
            if col == first_col:
                return "0"
            prev_col = get_column_letter(ord(col) - ord("A"))
            return f"{prev_col}{cells[inner.id]}"
        if fn in FUNC_MAP:
            args = ",".join(to_xl(x, cells, col, first_col) for x in node.args)
            return f"{FUNC_MAP[fn]}({args})"
        raise SpecError(f"{fn}() has no direct Excel equivalent")
    raise SpecError(f"cannot translate {type(node).__name__}")


def build(spec):
    n = n_periods(spec)
    per = period_labels(spec)
    res = compute(spec)
    wb = Workbook()
    ws = wb.active
    ws.title = "Model"
    first_col = "C"
    cols = [get_column_letter(3 + i) for i in range(n)]

    ws["A1"] = spec["meta"].get("name", "Business model")
    ws["A1"].font = Font(bold=True, size=14)
    if spec["meta"].get("question"):
        ws["A2"] = spec["meta"]["question"]
        ws["A2"].font = Font(italic=True, color="52514E")
    ws["A3"] = ("Blue = assumption you can change. Black = calculated, do not overtype. "
                "Grade and source are beside each assumption; hover for detail.")
    ws["A3"].font = Font(size=9, color="898781")

    r = 5
    ws.cell(row=r, column=1, value="ASSUMPTIONS").font = SUB
    for i, p in enumerate(per):
        c = ws.cell(row=r, column=3 + i, value=p)
        c.font, c.fill = HDR, HDR_FILL
        c.alignment = Alignment(horizontal="right")
    for lbl, off in (("Grade", n + 3), ("Source", n + 4)):
        c = ws.cell(row=r, column=off, value=lbl)
        c.font, c.fill = HDR, HDR_FILL
    r += 1

    cells = {}
    for k, d in spec["drivers"].items():
        ws.cell(row=r, column=1, value=str(d.get("label") or k))
        ws.cell(row=r, column=2, value=k).font = Font(size=8, color="B0B0B0")
        vals = res["values"][k]
        for i, v in enumerate(vals):
            c = ws.cell(row=r, column=3 + i, value=round(v, 6))
            c.font = BLUE
            if d.get("unit") == "percent":
                c.number_format = "0.0%"
        g = d.get("grade") or ""
        gc = ws.cell(row=r, column=n + 3, value=g)
        if g in GRADE_FILL:
            gc.fill = GRADE_FILL[g]
        src = d.get("source")
        if isinstance(src, dict):
            src = " — ".join(str(x) for x in
                             (src.get("note"), src.get("url"), src.get("date")) if x)
        ws.cell(row=r, column=n + 4, value=str(src or "no source recorded"))
        note = []
        if d.get("note"):
            note.append(str(d["note"]))
        if d.get("deal_stage"):
            note.append(f"Deal stage: {d['deal_stage']} — depends on a counterparty, "
                        f"not a market fact.")
        if (rs := d.get("researched")):
            note.append(f"Researched range: {rs.get('range')}")
            if rs.get("applicability"):
                note.append(f"Applies because: {rs['applicability']}")
        if note:
            ws.cell(row=r, column=1).comment = Comment("\n".join(note)[:900],
                                                       "sustainable-business-model")
        cells[k] = r
        r += 1

    skipped = []
    # Two passes. Excel does not care whether a formula points up or down the
    # sheet, but a one-pass writer does: a line whose driver sits in a later block
    # would silently fall back to a dead value. So place every row first, then
    # write formulas once every reference is known.
    layout = []          # (kind, title|key, row)

    def place(title, keys):
        nonlocal r
        keys = [k for k in keys if k in spec["lines"] or k in spec["outputs"]]
        if not keys:
            return
        r += 1
        layout.append(("head", title, r))
        r += 1
        for k in keys:
            layout.append(("line", k, r))
            cells[k] = r
            r += 1

    def cat_keys(cat):
        return [k for k, l in spec["lines"].items() if l.get("category") == cat]

    # A subtotal per income category, both because a P&L reads better with them
    # and because ratios like grant-per-unit need a cell to point at.
    for cat, title, derived in (("earned", "EARNED INCOME", "total_earned"),
                                ("grant", "GRANTS", "total_grant"),
                                ("investment", "INVESTMENT", "total_investment"),
                                ("inkind", "IN-KIND", "total_inkind")):
        ks = cat_keys(cat)
        if not ks:
            continue
        place(title, ks)
        layout.append(("total", (f"Total {cat}", ks), r))
        cells[derived] = r
        r += 1

    income_keys = [k for k, l in spec["lines"].items() if l.get("category") in INCOME_CATS]
    cost_keys = cat_keys("cost")
    grant_keys = cat_keys("grant")

    r += 1
    layout.append(("total", ("Total income", income_keys), r)); cells["total_income"] = r
    inc_row = r; r += 1
    place("COSTS", cost_keys)
    layout.append(("total", ("Total costs", cost_keys), r)); cells["total_costs"] = r
    cost_row = r; r += 1
    r += 1
    layout.append(("net", None, r)); cells["net"] = r
    net_row = r; r += 1
    layout.append(("reserves", None, r)); r += 1
    if grant_keys:
        layout.append(("gdep", grant_keys, r)); cells["grant_dependency"] = r; r += 1
    place("IMPACT", cat_keys("impact"))
    place("RATIOS", list(spec["outputs"]))

    # ---- pass 2: now every row is known, write the content
    for kind, payload, row in layout:
        if kind == "head":
            ws.cell(row=row, column=1, value=payload).font = SUB
        elif kind == "line":
            k = payload
            ln = spec["lines"].get(k) or spec["outputs"].get(k)
            ws.cell(row=row, column=1, value=str(ln.get("label") or k))
            ws.cell(row=row, column=2, value=k).font = Font(size=8, color="B0B0B0")
            for i, col in enumerate(cols):
                if "formula" in ln:
                    try:
                        f = to_xl(parse_expr(ln["formula"]).body, cells, col, first_col)
                        c = ws.cell(row=row, column=3 + i, value=f"={f}")
                        c.font = BLACK
                    except SpecError:
                        # Honest fallback: the value is right, it just is not live.
                        c = ws.cell(row=row, column=3 + i,
                                    value=round(res["values"][k][i], 6))
                        c.font = Font(color="808080", italic=True)
                        if k not in skipped:
                            skipped.append(k)
                else:
                    c = ws.cell(row=row, column=3 + i,
                                value=round(res["values"][k][i], 6))
                    c.font = BLUE
                if ln.get("unit") == "percent":
                    c.number_format = "0.0%"
        elif kind == "total":
            title, keys = payload
            ws.cell(row=row, column=1, value=title).font = BOLD
            for i, col in enumerate(cols):
                refs = "+".join(f"{col}{cells[k]}" for k in keys if k in cells)
                ws.cell(row=row, column=3 + i,
                        value=f"={refs}" if refs else 0).font = BOLD
        elif kind == "net":
            ws.cell(row=row, column=1, value="NET").font = BOLD
            for i, col in enumerate(cols):
                ws.cell(row=row, column=3 + i,
                        value=f"={col}{inc_row}-{col}{cost_row}").font = BOLD
        elif kind == "reserves":
            ws.cell(row=row, column=1, value="Reserves (cumulative)")
            for i, col in enumerate(cols):
                ws.cell(row=row, column=3 + i,
                        value=f"=SUM({cols[0]}{net_row}:{col}{net_row})").font = BLACK
        elif kind == "gdep":
            ws.cell(row=row, column=1, value="Grant dependency")
            for i, col in enumerate(cols):
                g = "+".join(f"{col}{cells[k]}" for k in payload if k in cells)
                c = ws.cell(row=row, column=3 + i,
                            value=f"=IFERROR(({g})/{col}{inc_row},0)")
                c.number_format = "0.0%"

    for col, w in (("A", 38), ("B", 3), (get_column_letter(n + 3), 7),
                   (get_column_letter(n + 4), 60)):
        ws.column_dimensions[col].width = w
    for c in cols:
        ws.column_dimensions[c].width = 13
    ws.freeze_panes = "C6"

    # Formulas written by openpyxl carry no cached values, so tell Excel to
    # rebuild them on open rather than let the file arrive looking empty.
    try:
        wb.calculation.fullCalcOnLoad = True
    except Exception:
        pass
    return wb, skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", default="model.xlsx")
    a = ap.parse_args()

    spec = load_spec(a.spec)
    errs, _ = validate(spec)
    if errs:
        for e in errs:
            print("  ERROR ", e)
        raise SystemExit("spec has errors")

    wb, skipped = build(spec)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    wb.save(a.out)
    print(f"spreadsheet -> {a.out}")
    print("  assumptions in blue with grade + source; calculated lines are live formulas")
    print("  values rebuild on first open (fullCalcOnLoad) — open it once before sending")
    if skipped:
        print(f"  NOTE: {len(skipped)} line(s) use functions with no clean Excel "
              f"equivalent ({', '.join(skipped)}).\n        They are written as grey "
              f"static values, correct but not live. The YAML spec and the HTML report "
              f"remain the working model.")


if __name__ == "__main__":
    main()
