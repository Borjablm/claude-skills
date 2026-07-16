#!/usr/bin/env python3
"""Build the synthetic test workbook the evals run against.

A skill's tests have to ship with the skill, which means the fixture cannot be a
real client's model. This generates one: a community bike-share venture carrying
the same *class* of defects the checks are for, invented rather than borrowed.

  - stock x flow: campaign days x daily riders, labelled as a population
  - subset exceeds total: the addressable market comes out larger than the city
  - an unsourced price attributed to an AI, and cells the author marked arbitrary
  - a magic number buried inside a formula

Cached values are injected afterwards because openpyxl writes formulas without
them, and the audit skill's --verify compares against exactly those cached values.
A fixture with no cached values would silently test nothing.

    python make_fixture.py --out fixtures/bikeshare.xlsx
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import zipfile
from pathlib import Path

from openpyxl import Workbook, load_workbook

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from model_graph import build_graph, Evaluator, _num  # noqa: E402


def build(path: Path):
    wb = Workbook()
    a = wb.active
    a.title = "Assumptions"
    rows = [
        ("Community bike-share — business case", None, None),
        (None, None, None),
        ("Driver", "Value", "Notes and sources"),
        ("City population", 480000, "Municipal statistics office, 2025 census"),
        ("Daily active riders", 12000, "Operator dashboard, monthly average 2025"),
        ("Campaign duration (days)", 14, "2 x 7-day sponsor campaigns per year"),
        ("% riders who buy merchandise", 0.18, "Rider survey 2025, n=900"),
        ("Repeat purchase rate", 0.04, "4% within the campaign window"),
        ("Average item price", 12, "based on ChatGPT analysis"),
        ("Number of items in range", 8, None),
        ("Converted market share", 0.06, "Arbitrary assumption"),
        ("Platform commission", 0.25, None),
        ("Sponsor fee per campaign", 45000, "Arbitrary assumption - pending negotiation"),
        ("Staff cost per year", 96000, "3 FTE, local salary benchmark"),
        ("Maintenance per bike per year", 140, "Workshop quote, 2025"),
        ("Fleet size", 900, "Arbitrary assumption"),
    ]
    for i, (c1, c2, c3) in enumerate(rows, 1):
        a.cell(row=i, column=1, value=c1)
        if c2 is not None:
            a.cell(row=i, column=2, value=c2)
        if c3 is not None:
            a.cell(row=i, column=3, value=c3)

    r = wb.create_sheet("Revenue")
    r["A1"] = "MERCHANDISE"; r["B1"] = "Y1"; r["C1"] = "Y2"; r["D1"] = "Y3"
    r["A2"] = "Campaign duration (days)"
    r["B2"], r["C2"], r["D2"] = 14, 20, 20
    r["A3"] = "Daily active riders"
    for c in "BCD":
        r[f"{c}3"] = "=Assumptions!$B$5"
    r["A4"] = "% riders who buy merchandise"
    for c in "BCD":
        r[f"{c}4"] = "=Assumptions!$B$7"
    r["A5"] = "Repeat purchase rate"
    for c in "BCD":
        r[f"{c}5"] = "=Assumptions!$B$8"
    # THE DEFECT: days x daily riders, then called a population. It also comes out
    # larger than the rider base it draws from, which is the visible symptom.
    r["A6"] = "Addressable market (#riders)"
    for c in "BCD":
        r[f"{c}6"] = f"={c}2*{c}3*{c}4"
    r["A7"] = "Average item price"
    for c in "BCD":
        r[f"{c}7"] = "=Assumptions!$B$9"
    r["A8"] = "Number of items"
    r["B8"], r["C8"], r["D8"] = 8, 8, 8
    r["A9"] = "Converted market share"
    r["B9"], r["C9"], r["D9"] = 0.06, 0.10, 0.15
    r["A10"] = "Gross revenue"
    for c in "BCD":
        r[f"{c}10"] = f"=({c}9*{c}7*{c}6*{c}8)*(1-Assumptions!$B$11)"

    r["A12"] = "SPONSORSHIP"
    r["A13"] = "Campaigns per year"
    r["B13"], r["C13"], r["D13"] = 2, 3, 4
    r["A14"] = "Sponsor fee"
    for c in "BCD":
        r[f"{c}14"] = "=Assumptions!$B$12"
    r["A15"] = "Sponsorship revenue"
    for c in "BCD":
        r[f"{c}15"] = f"={c}13*{c}14"

    p = wb.create_sheet("P&L")
    p["A1"] = "Line"; p["B1"] = "Y1"; p["C1"] = "Y2"; p["D1"] = "Y3"
    p["A2"] = "Merchandise revenue"
    for c in "BCD":
        p[f"{c}2"] = f"=Revenue!{c}10"
    p["A3"] = "Sponsorship revenue"
    for c in "BCD":
        p[f"{c}3"] = f"=Revenue!{c}15"
    p["A4"] = "Total revenue"
    # NOTE: sums B2:B3 correctly; kept clean so range-gap fires only where intended
    for c in "BCD":
        p[f"{c}4"] = f"=SUM({c}2:{c}3)"
    p["A6"] = "Staff"
    for c in "BCD":
        p[f"{c}6"] = "=Assumptions!$B$14"
    p["A7"] = "Maintenance"
    for c in "BCD":
        p[f"{c}7"] = "=Assumptions!$B$15*Assumptions!$B$16"
    p["A8"] = "Marketing"
    # magic number buried in a formula
    p["B8"], p["C8"], p["D8"] = "=2500*12", "=2500*12", "=3200*12"
    p["A9"] = "Total costs"
    for c in "BCD":
        p[f"{c}9"] = f"=SUM({c}6:{c}8)"
    p["A11"] = "Net profit"
    for c in "BCD":
        p[f"{c}11"] = f"={c}4-{c}9"

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    return path


CELL_RE = re.compile(r'(<c r="([A-Z]+\d+)"[^>]*>)(<f[^>]*>.*?</f>)(<v>.*?</v>)?')


def inject_cached_values(path: Path):
    """Write each formula's computed value into the file as Excel would cache it.

    Without this the workbook has formulas and no values, so --verify has nothing
    to compare and reports 0 checked — a test that passes by testing nothing.
    """
    g = build_graph(path)
    ev = Evaluator(g["cells"])
    vals = {}
    for key, c in g["cells"].items():
        if c.get("kind") != "formula":
            continue
        try:
            v = ev.value(key)
        except Exception:
            continue
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            vals[key] = float(v)

    tmp = path.with_suffix(".tmp.xlsx")
    shutil.copy(path, tmp)
    zin = zipfile.ZipFile(tmp, "r")
    zout = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    # sheet order in the package maps to the workbook's sheet order
    names = g["sheets"]
    try:
        for item in zin.infolist():
            data = zin.read(item.filename)
            m = re.match(r"xl/worksheets/sheet(\d+)\.xml$", item.filename)
            if m:
                idx = int(m.group(1)) - 1
                sheet = names[idx] if idx < len(names) else None
                if sheet:
                    xml = data.decode("utf-8")

                    def repl(mm):
                        open_tag, ref, ftag, vtag = mm.groups()
                        v = vals.get(f"{sheet}!{ref}")
                        if v is None:
                            return mm.group(0)
                        return f"{open_tag}{ftag}<v>{v!r}</v>"

                    xml = CELL_RE.sub(repl, xml)
                    data = xml.encode("utf-8")
            zout.writestr(item, data)
    finally:
        zin.close()
        zout.close()
        tmp.unlink(missing_ok=True)
    return len(vals)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="fixtures/bikeshare.xlsx")
    a = ap.parse_args()
    p = build(Path(a.out))
    n = inject_cached_values(p)
    print(f"fixture -> {p}  ({n} formula values cached)")

    g = build_graph(p, verify=True)
    v = g["verification"]
    print(f"  self-check: {v['matched']}/{v['checked']} formulas reproduce the cached "
          f"values ({(v['match_rate'] or 0):.0%})")
    wb = load_workbook(p, data_only=True)
    print(f"  Y3 net profit reads: {wb['P&L']['D11'].value}")


if __name__ == "__main__":
    main()
