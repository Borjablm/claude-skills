#!/usr/bin/env python3
"""Write the analysis back into the workbook the client actually uses.

The spreadsheet stays the deliverable. People need to see the mechanics to trust
the numbers, the file has to open on anyone's machine years from now, and it must
keep working when we are gone — so the output is their workbook, hardened, not a
report about their workbook.

Adds, without disturbing existing formulas:
  - Assumptions Ledger tab: every assumption, its evidence, grade, impact rank
  - Findings tab: structural issues with the formula and the reason
  - a note on each assumption cell recording where its value came from
  - input/formula colour coding, the convention modellers already read fluently

Also writes a standalone HTML summary that opens anywhere, for people who will
never open a spreadsheet.

Usage:
    python render.py --xlsx MODEL.xlsx --ledger model/ledger.json \
        --findings model/findings.json --sensitivity model/sensitivity.json \
        --out exports/MODEL-hardened.xlsx --html exports/summary.html
"""
from __future__ import annotations

import argparse
import html
import json
from datetime import date
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# The colours are not decoration: blue-input / black-formula is the convention
# finance readers already parse without being told, so following it makes the
# hardened file legible to a committee on first open.
BLUE = Font(color="0000FF")
BLACK = Font(color="000000")
GREEN = Font(color="008000")
HDR = Font(bold=True, color="FFFFFF")
HDR_FILL = PatternFill("solid", start_color="1F3864")
GRADE_FILL = {
    "A": PatternFill("solid", start_color="C6EFCE"),
    "B": PatternFill("solid", start_color="DDEBF7"),
    "C": PatternFill("solid", start_color="FFEB9C"),
    "D": PatternFill("solid", start_color="FFC7CE"),
}
SEV_FILL = {"high": PatternFill("solid", start_color="FFC7CE"),
            "medium": PatternFill("solid", start_color="FFEB9C"),
            "low": PatternFill("solid", start_color="EDEDED")}

LEDGER_COLS = [
    ("Cell", 22), ("Assumption", 46), ("Value", 14), ("Unit", 10),
    ("Grade", 7), ("Confidence", 12), ("Impact rank", 12), ("Research first", 14),
    ("Evidence signal", 16), ("Deal stage", 14), ("Source / provenance", 60), ("Note in model", 50),
]
FINDING_COLS = [("ID", 6), ("Severity", 10), ("Check", 22), ("Cells", 26),
                ("Assumption / label", 40), ("Formula", 40), ("Why it matters", 90)]


def _sheet(wb, title):
    if title in wb.sheetnames:
        del wb[title]
    return wb.create_sheet(title)


def _cell(ws, row, col, value):
    """Write a value, forcing formula-looking text to stay text.

    The findings tab quotes the offending formula, and openpyxl turns any string
    starting with '=' into a live formula — so the evidence column would evaluate
    against the report's own grid and reach the reader as #VALUE!/#REF!. Anything
    Excel treats as a formula opener gets pinned to text instead.
    """
    c = ws.cell(row=row, column=col)
    c.value = value
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        c.data_type = "s"
    return c


def _header(ws, cols):
    for i, (name, width) in enumerate(cols, 1):
        c = ws.cell(row=1, column=i, value=name)
        c.font, c.fill = HDR, HDR_FILL
        c.alignment = Alignment(vertical="center")
        ws.column_dimensions[get_column_letter(i)].width = width
    ws.freeze_panes = "A2"


def write_ledger_tab(wb, ledger):
    ws = _sheet(wb, "Assumptions Ledger")
    _header(ws, LEDGER_COLS)
    for r, a in enumerate(sorted(ledger["assumptions"],
                                 key=lambda x: (x.get("research_priority_rank") or 9999)), 2):
        src = a.get("source")
        if isinstance(src, dict):
            src = " | ".join(f"{k}: {v}" for k, v in src.items() if v)
        res = a.get("researched") or {}
        if res.get("range") and not src:
            src = f"researched {res.get('date','')}: range {res['range']}"
        vals = [a["cell"], a["label"], a.get("value"), a.get("unit"),
                a.get("grade"), a.get("confidence"), a.get("impact_rank"),
                a.get("research_priority_rank"), a.get("evidence_signal"),
                a.get("deal_stage"),
                src, (a.get("note") or "").replace("\n", " ")[:300]]
        for i, v in enumerate(vals, 1):
            c = _cell(ws, r, i, v)
            c.alignment = Alignment(vertical="top", wrap_text=i in (2, 11, 12))
        if (g := (a.get("grade") or "").strip().upper()[:1]) in GRADE_FILL:
            ws.cell(row=r, column=5).fill = GRADE_FILL[g]
    ws.auto_filter.ref = f"A1:{get_column_letter(len(LEDGER_COLS))}{max(2, len(ledger['assumptions'])+1)}"
    return ws


def write_findings_tab(wb, findings):
    ws = _sheet(wb, "Findings")
    _header(ws, FINDING_COLS)
    for r, f in enumerate(findings.get("findings", []), 2):
        cells = f.get("cells") or [f.get("cell")]
        vals = [f.get("id"), f.get("severity"), f.get("check"),
                ", ".join(x.split("!")[-1] for x in cells if x)[:120],
                f.get("label"), (f.get("formula") or "")[:200], f.get("detail")]
        for i, v in enumerate(vals, 1):
            c = _cell(ws, r, i, v)
            c.alignment = Alignment(vertical="top", wrap_text=i in (5, 6, 7))
        ws.cell(row=r, column=2).fill = SEV_FILL.get(f.get("severity"), SEV_FILL["low"])
    return ws


def annotate_cells(wb, ledger, max_note=1000):
    """Put each assumption's provenance on the cell itself.

    Hovering a number and seeing where it came from is the single change that makes
    a model defensible in a room. It survives export, email and the passage of time.
    """
    n = 0
    for a in ledger["assumptions"]:
        sheet, ref = a["cell"].split("!", 1)
        if sheet not in wb.sheetnames:
            continue
        cell = wb[sheet][ref]
        parts = []
        if a.get("grade"):
            parts.append(f"Grade: {a['grade']}"
                         + (f" ({a['confidence']} confidence)" if a.get("confidence") else ""))
        elif a.get("evidence_signal") in ("weak", "none"):
            # Ungraded but visibly unbacked. Worth surfacing even before review:
            # it is the honest state of the cell, and it marks the work remaining.
            parts.append(f"Evidence: {a['evidence_signal']} — not yet graded")
        src = a.get("source")
        if isinstance(src, dict):
            src = " | ".join(f"{k}: {v}" for k, v in src.items() if v)
        if src:
            parts.append(f"Source: {src}")
        if (res := a.get("researched")):
            if res.get("range"):
                parts.append(f"Researched range: {res['range'][0]} to {res['range'][1]}"
                             + (f" ({res['date']})" if res.get("date") else ""))
            for s in (res.get("sources") or [])[:3]:
                parts.append(f"  - {s}")
        if a.get("deal_stage"):
            parts.append(f"Deal stage: {a['deal_stage']} (partner-dependent)")
        if a.get("impact_rank"):
            parts.append(f"Impact rank: {a['impact_rank']} of model assumptions")
        for h in (a.get("history") or [])[-3:]:
            if isinstance(h, dict):
                parts.append(f"History: {h.get('value')} — {h.get('note') or h.get('why') or ''}")
        if not parts:
            continue
        cell.comment = Comment("\n".join(parts)[:max_note], "financial-model-audit")
        n += 1
    return n


def colour_code(wb, graph):
    n = 0
    for key, c in graph["cells"].items():
        sheet, ref = key.split("!", 1)
        if sheet not in wb.sheetnames or c.get("kind") not in ("input", "formula"):
            continue
        cell = wb[sheet][ref]
        if c["kind"] == "input":
            cell.font = BLUE
        elif any("!" in d for d in c.get("deps", [])[:1]) or \
                any(d.split("!")[0] != sheet for d in c.get("deps", [])):
            cell.font = GREEN
        else:
            cell.font = BLACK
        n += 1
    return n


def write_html(path, ledger, findings, sens, source):
    a_sorted = sorted(ledger["assumptions"],
                      key=lambda x: (x.get("research_priority_rank") or 9999))[:25]
    grades = {}
    for a in ledger["assumptions"]:
        k = a.get("grade") or a.get("evidence_signal") or "ungraded"
        grades[k] = grades.get(k, 0) + 1
    e = html.escape

    def rows_led():
        out = []
        for a in a_sorted:
            src = a.get("source")
            if isinstance(src, dict):
                src = " | ".join(f"{k}: {v}" for k, v in src.items() if v)
            src = src or (a.get("note") or "")
            g = (a.get("grade") or a.get("evidence_signal") or "-")
            cls = f"g{g[:1].upper()}" if (a.get("grade") or "") else "gN"
            out.append(
                f"<tr><td>{a.get('research_priority_rank') or ''}</td>"
                f"<td>{e(str(a['label']))}<span class='ref'>{e(a['cell'])}</span></td>"
                f"<td class='num'>{e(str(a.get('value')))}</td>"
                f"<td><span class='badge {cls}'>{e(str(g))}</span></td>"
                f"<td class='src'>{e(str(src)[:180])}</td></tr>")
        return "\n".join(out)

    def rows_find():
        out = []
        for f in findings.get("findings", []):
            cells = ", ".join(x.split("!")[-1] for x in (f.get("cells") or [f.get("cell")]) if x)
            formula = f.get("formula")
            formula_html = f"<p><code>{e(str(formula)[:180])}</code></p>" if formula else ""
            out.append(
                f"<div class='f {e(f.get('severity', ''))}'>"
                f"<h4>{e(f.get('id', ''))} · {e(f.get('check', ''))} "
                f"<span class='sev'>{e(f.get('severity', ''))}</span></h4>"
                f"<p class='where'>{e(str(f.get('label') or ''))} — <code>{e(cells)}</code></p>"
                f"{formula_html}"
                f"<p>{e(f.get('detail', ''))}</p></div>")
        return "\n".join(out)

    def rows_tornado():
        if not sens:
            return "<p class='muted'>No sensitivity run.</p>"
        rs = sens["results"][:12]
        mx = max((r["swing"] for r in rs), default=1) or 1
        out = []
        for r in rs:
            w = r["swing"] / mx * 100
            out.append(
                f"<div class='trow'><div class='tl'>{e(str(r['label'])[:46])}</div>"
                f"<div class='tbar'><span style='width:{w:.1f}%'></span></div>"
                f"<div class='tv'>{r['share_of_total_swing']*100:.1f}%</div></div>")
        note = ""
        for t in sens.get("leverage_ties", [])[:1]:
            note = (f"<p class='muted'>{t['count']} assumptions share identical leverage — "
                    f"one multiplicative chain, so evidence quality decides the research order.</p>")
        return "\n".join(out) + note

    tgt = f"{sens['target_label']} = {sens['base_value']:,.0f}" if sens else "n/a"
    doc = f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Model audit — {e(Path(source).name)}</title><style>
:root{{--bg:#f9f9f7;--s:#fff;--t:#0b0b0b;--t2:#52514e;--t3:#898781;--ring:rgba(0,0,0,.1);
--blue:#2a78d6;--red:#d03b3b;--amber:#fab219;--green:#0ca30c}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0d0d0d;--s:#1a1a19;--t:#fff;--t2:#c3c2b7;
--t3:#898781;--ring:rgba(255,255,255,.12);--blue:#3987e5;--red:#e66767}}}}
*{{box-sizing:border-box;margin:0}}body{{font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;
background:var(--bg);color:var(--t);padding:24px;max-width:1080px;margin:0 auto}}
h1{{font-size:21px;margin-bottom:2px}}h2{{font-size:13px;text-transform:uppercase;letter-spacing:.05em;
color:var(--t3);margin:22px 0 8px}}.sub{{color:var(--t3);font-size:12.5px;margin-bottom:18px}}
.card{{background:var(--s);border:1px solid var(--ring);border-radius:10px;padding:14px 16px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px}}
.tile .l{{font-size:11.5px;color:var(--t3);text-transform:uppercase;letter-spacing:.04em}}
.tile .v{{font-size:24px;font-weight:650}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--t3);
padding:6px 8px 6px 0;border-bottom:1px solid var(--ring)}}
td{{padding:7px 8px 7px 0;border-bottom:1px solid var(--ring);color:var(--t2);vertical-align:top}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;color:var(--t)}}
.ref{{display:block;font-size:11px;color:var(--t3)}}.src{{font-size:12px;color:var(--t3)}}
.badge{{display:inline-block;padding:1px 8px;border-radius:99px;font-size:11.5px;font-weight:650;color:#fff}}
.gA{{background:var(--green)}}.gB{{background:var(--blue)}}.gC{{background:var(--amber);color:#4a3500}}
.gD{{background:var(--red)}}.gN{{background:none;color:var(--t3);border:1px solid var(--ring)}}
.f{{border:1px solid var(--ring);border-left:3px solid var(--t3);border-radius:8px;padding:10px 14px;
margin-bottom:10px;background:var(--s)}}.f.high{{border-left-color:var(--red)}}
.f.medium{{border-left-color:var(--amber)}}.f h4{{font-size:13.5px}}
.f .sev{{font-size:10.5px;text-transform:uppercase;color:var(--t3);letter-spacing:.05em}}
.f .where{{font-size:12px;color:var(--t3);margin:2px 0 6px}}.f p{{font-size:12.5px;color:var(--t2)}}
code{{font-size:12px;background:var(--bg);border:1px solid var(--ring);border-radius:4px;padding:0 4px}}
.trow{{display:grid;grid-template-columns:230px 1fr 56px;gap:10px;align-items:center;padding:3px 0}}
.tl{{font-size:12.5px;color:var(--t2);text-align:right}}
.tbar{{height:16px;background:var(--bg);border-radius:4px;overflow:hidden}}
.tbar span{{display:block;height:100%;background:var(--blue);border-radius:4px}}
.tv{{font-size:12px;color:var(--t3);font-variant-numeric:tabular-nums}}
.muted{{font-size:12px;color:var(--t3);margin-top:8px}}
footer{{margin-top:22px;font-size:11.5px;color:var(--t3)}}
</style></head><body>
<h1>Model audit — {e(Path(source).name)}</h1>
<div class="sub">Generated {date.today().isoformat()} · financial-model-audit</div>
<div class="tiles">
  <div class="card tile"><div class="l">Assumptions</div><div class="v">{len(ledger['assumptions'])}</div></div>
  <div class="card tile"><div class="l">Findings</div><div class="v">{len(findings.get('findings',[]))}</div>
    <div class="l">{findings.get('counts',{}).get('high',0)} high severity</div></div>
  <div class="card tile"><div class="l">Target</div><div class="v" style="font-size:16px">{e(tgt)}</div></div>
  <div class="card tile"><div class="l">Evidence mix</div>
    <div class="l" style="margin-top:6px">{e(', '.join(f'{k}: {v}' for k,v in sorted(grades.items())))}</div></div>
</div>
<h2>Structural findings</h2>{rows_find() or "<p class='muted'>No structural issues detected.</p>"}
<h2>Leverage on the target</h2><div class="card">{rows_tornado()}</div>
<h2>Research these first — highest leverage, weakest evidence</h2>
<div class="card"><table><thead><tr><th>#</th><th>Assumption</th><th class="num">Value</th>
<th>Evidence</th><th>Source / note in model</th></tr></thead><tbody>{rows_led()}</tbody></table></div>
<footer>Grades and sources reflect reviewer judgment recorded in the ledger. Findings are flags for
a modeller to confirm, not automatic corrections — some are deliberate.</footer>
</body></html>"""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(doc, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--graph", default="model/graph.json")
    ap.add_argument("--ledger", default="model/ledger.json")
    ap.add_argument("--findings", default="model/findings.json")
    ap.add_argument("--sensitivity", default=None)
    ap.add_argument("--out", default=None, help="hardened .xlsx output")
    ap.add_argument("--html", default=None, help="standalone summary .html")
    ap.add_argument("--no-colour", action="store_true")
    a = ap.parse_args()

    def load(p, default=None):
        if p and Path(p).exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        return default

    ledger = load(a.ledger, {"assumptions": []})
    findings = load(a.findings, {"findings": []})
    sens = load(a.sensitivity)

    if a.out:
        wb = load_workbook(a.xlsx)
        write_ledger_tab(wb, ledger)
        write_findings_tab(wb, findings)
        n_notes = annotate_cells(wb, ledger)
        n_col = 0
        if not a.no_colour and (g := load(a.graph)):
            n_col = colour_code(wb, g)
        # Re-saving keeps every formula but discards the values Excel had cached
        # for them, so without this the delivered file can open with blank results
        # in anything that doesn't recalculate on its own. Force the recalculation
        # rather than trust the source file's setting to carry over.
        try:
            wb.calculation.fullCalcOnLoad = True
        except Exception:
            pass
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        wb.save(a.out)
        print(f"hardened workbook -> {a.out}")
        print(f"  Assumptions Ledger tab ({len(ledger['assumptions'])} rows), "
              f"Findings tab ({len(findings.get('findings', []))} rows)")
        print(f"  {n_notes} cells annotated with provenance, {n_col} cells colour-coded")
        print("  formulas preserved; cached values are rebuilt on first open "
              "(fullCalcOnLoad set) — open it once in Excel/Sheets before sending.")
        graded = sum(1 for x in ledger["assumptions"] if x.get("grade"))
        if graded == 0:
            print("  NOTE: no assumption is graded yet, so the ledger records what the "
                  "model says, not what it is worth.\n        Grade the high-impact rows "
                  "(references/grading-rubric.md) and re-run before sending this to anyone.")
        elif graded < len(ledger["assumptions"]):
            print(f"  {graded}/{len(ledger['assumptions'])} graded — ungraded rows show "
                  f"their provisional evidence signal only.")

    if a.html:
        write_html(a.html, ledger, findings, sens, a.xlsx)
        print(f"summary page -> {a.html}")


if __name__ == "__main__":
    main()
