#!/usr/bin/env python3
"""Render the model as one self-contained HTML page the founder can actually use.

The spec is compiled to JavaScript and embedded, so every number recalculates in
the browser as sliders move. No server, no API key, no dependency on us — the file
works offline, opens in ten years, and can be emailed to a funder who will never
install anything. That property is the point: a model somebody else has to run for
you is a model you cannot defend.

The page leads with what the model does not know. Coverage and evidence grades come
before results, because a projection presented without its provenance invites a
confidence nobody has earned.

Usage:
    python report.py spec.yaml --out report.html [--explore model/explore.json]
"""
from __future__ import annotations

import argparse
import ast
import html
import json
from datetime import date
from pathlib import Path

from model import (load_spec, validate, compute, n_periods, period_labels,
                   Engine, parse_expr, SpecError, INCOME_CATS)


def scenario_rows(spec, target="net"):
    """Base + auto-built evidenced cases + the spec's own scenarios.

    Imported lazily: explore.py imports from model.py too, and keeping the import
    inside the function avoids a cycle if report is ever imported the other way.
    """
    from explore import run_scenarios, evidenced_case
    try:
        auto = {evidenced_case(spec, target, "last", favourable=f)["name"]
                for f in (False, True)}
    except Exception:
        auto = set()
    rows = run_scenarios(spec, target=target, how="last", include_evidenced=True)
    for r in rows:
        r["evidenced"] = r["name"] in auto
    return rows

# --------------------------------------------------------------- python -> js

JS_BIN = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul", ast.Div: "div",
          ast.Pow: "pow", ast.Mod: "mod"}
JS_CMP = {ast.Lt: "<", ast.Gt: ">", ast.LtE: "<=", ast.GtE: ">=",
          ast.Eq: "==", ast.NotEq: "!="}


def to_js(src: str) -> str:
    """Transpile a spec expression to a JS expression over vector helpers.

    Safe by construction: the same whitelist the Python engine uses, so anything
    that reaches here has already been proven to be arithmetic over named values.
    """
    return _js(parse_expr(src).body)


def _js(nd) -> str:
    if isinstance(nd, ast.Constant):
        return f"V.k({float(nd.value)})"
    if isinstance(nd, ast.Name):
        return f"v[{nd.id!r}]"
    if isinstance(nd, ast.UnaryOp):
        if isinstance(nd.op, ast.USub):
            return f"V.neg({_js(nd.operand)})"
        if isinstance(nd.op, ast.Not):
            return f"V.not_({_js(nd.operand)})"
        return _js(nd.operand)
    if isinstance(nd, ast.BinOp):
        return f"V.{JS_BIN[type(nd.op)]}({_js(nd.left)}, {_js(nd.right)})"
    if isinstance(nd, ast.Compare):
        return f"V.cmp({JS_CMP[type(nd.ops[0])]!r}, {_js(nd.left)}, {_js(nd.comparators[0])})"
    if isinstance(nd, ast.BoolOp):
        fn = "and_" if isinstance(nd.op, ast.And) else "or_"
        return f"V.{fn}([{', '.join(_js(v) for v in nd.values)}])"
    if isinstance(nd, ast.IfExp):
        return f"V.where({_js(nd.test)}, {_js(nd.body)}, {_js(nd.orelse)})"
    if isinstance(nd, ast.Call):
        args = ", ".join(_js(a) for a in nd.args)
        return f"V.{nd.func.id}({args})"
    raise SpecError(f"cannot compile {type(nd).__name__} to JS")


def resolution_order(spec):
    """The order lines/outputs can be evaluated in. Emitting JS in this order lets
    the browser recompute in one pass."""
    n = n_periods(spec)
    known = set(spec["drivers"]) | {
        k for g in ("lines", "outputs") for k, v in spec[g].items() if "formula" not in v}
    known |= set(DERIVED_KEYS)
    pending = {k: v["formula"] for g in ("lines", "outputs")
               for k, v in spec[g].items() if "formula" in v}
    order = []
    for _ in range(len(pending) + 2):
        if not pending:
            break
        for k in list(pending):
            names = {x.id for x in ast.walk(parse_expr(pending[k]))
                     if isinstance(x, ast.Name)}
            if names <= known:
                order.append(k)
                known.add(k)
                del pending[k]
    order.extend(pending)  # anything left is circular; Python already flagged it
    return order


DERIVED_KEYS = ["total_earned", "total_grant", "total_investment", "total_inkind",
                "total_income", "total_costs", "net", "net_excl_grants",
                "grant_dependency", "earned_ratio", "cumulative_net"]


def build_js(spec):
    n = n_periods(spec)
    order = resolution_order(spec)
    lines = []
    for k in order:
        src = (spec["lines"].get(k) or spec["outputs"].get(k))["formula"]
        lines.append(f"  v[{k!r}] = {to_js(src)};\n  derive(v);")
    cat = {c: [k for k, l in spec["lines"].items() if l.get("category") == c]
           for c in list(INCOME_CATS) + ["cost", "impact"]}
    # A derived name the author defined themselves must not be overwritten.
    owned = [k for k in DERIVED_KEYS
             if k in spec["drivers"] or k in spec["lines"] or k in spec["outputs"]]
    # Lines entered as plain values rather than formulas still have to reach the
    # browser. Miss them and the compiled model silently drops whole revenue lines
    # while every number on the page still looks plausible.
    consts = {}
    for grp in ("lines", "outputs"):
        for k, ln in spec[grp].items():
            if "formula" not in ln:
                raw = ln.get("values", ln.get("value"))
                consts[k] = (raw if isinstance(raw, list) else [raw] * n)
                consts[k] = [float(x or 0) for x in
                             (consts[k] + [consts[k][-1]] * n)[:n]]
    thr = [{"name": t.get("name"), "meaning": t.get("meaning"),
            "js": to_js(t["test"])} for t in spec["thresholds"] if "test" in t]
    return {"n": n, "assign": "\n".join(lines), "cat": cat, "owned": owned,
            "consts": consts, "thresholds": thr}


# ------------------------------------------------------------------- rendering

def sentence(spec, k, ln):
    """Render a formula as something a non-modeller can check.

    A founder cannot audit `repairs * avg_donation`, but they can absolutely tell
    you whether "Repair donations = Repairs completed x Average donation per
    repair" describes how the money actually arrives. That check is the one that
    catches the errors worth catching.
    """
    f = ln.get("formula")
    if not f:
        return None
    labels = {}
    for grp in ("drivers", "lines", "outputs"):
        for kk, vv in spec[grp].items():
            labels[kk] = (vv.get("label") or kk) if isinstance(vv, dict) else kk
    for kk in DERIVED_KEYS:
        labels.setdefault(kk, kk.replace("_", " "))
    out = f
    for kk in sorted(labels, key=len, reverse=True):
        out = out.replace(kk, labels[kk])
    return (out.replace("*", " × ").replace("/", " ÷ ")
               .replace("+", " + ").replace("  ", " "))


GRADE_TEXT = {
    "A": ("A", "Primary evidence — own actuals, a signed agreement, first-party research"),
    "B": ("B", "Credible secondary — a real study or benchmark that matches this use"),
    "C": ("C", "Unsourced — a considered guess. Fine unless it decides the answer"),
    "D": ("D", "Wrong in kind — the number does not measure what it is being used for"),
    "partner": ("P", "Depends on a named counterparty — a deal, not a market fact"),
}


def render(spec, res, explore=None):
    e = html.escape
    per = period_labels(spec)
    n = len(per)
    cur = spec["meta"].get("currency", "")
    js = build_js(spec)

    drivers = spec["drivers"]
    graded = sum(1 for d in drivers.values() if d.get("grade"))
    sourced = sum(1 for d in drivers.values() if d.get("source"))
    weak = [k for k, d in drivers.items()
            if (d.get("grade") in ("C", "D") or not d.get("grade"))]

    prio = {}
    if explore:
        prio = {r["key"]: r for r in explore.get("research_order", [])}

    def vrow(label, key, unit=None, cls=""):
        if key not in res["values"]:
            return ""
        v = res["values"][key]
        tds = "".join(f"<td class='num'>{e(fmtv(x, unit, cur))}</td>" for x in v)
        # data-k is what lets the sliders rewrite this row live.
        return (f"<tr class='{cls}' data-k='{e(key)}'><td>{e(label)}</td>{tds}</tr>")

    # ---- drivers with sliders
    drows = []
    for k, d in drivers.items():
        base = d.get("values", d.get("value"))
        vals = base if isinstance(base, list) else [base] * n
        vals = [float(x) for x in (vals + [vals[-1]] * n)[:n]]
        g = d.get("grade")
        gk, gt = GRADE_TEXT.get(g, ("?", "Not graded — nobody has said what stands behind it"))
        src = d.get("source")
        if isinstance(src, dict):
            src = " — ".join(str(x) for x in
                             (src.get("note"), src.get("url"), src.get("date")) if x)
        p = prio.get(k)
        rank = f"<span class='rank'>#{p['priority_rank']}</span>" if p else ""
        lo = min(vals) * 0.4 or 0.0
        hi = (max(vals) * 1.8) or 1.0
        step = (hi - lo) / 200 or 0.01
        drows.append(f"""
        <div class="drv" data-key="{e(k)}">
          <div class="dhead">
            <span class="dlabel">{rank}{e(str(d.get('label') or k))}</span>
            <span class="badge g{e(gk)}" title="{e(gt)}">{e(gk)}</span>
            <output id="o_{e(k)}"></output>
          </div>
          <input type="range" id="s_{e(k)}" min="{lo}" max="{hi}" step="{step}"
                 value="{vals[-1]}" data-key="{e(k)}">
          <div class="dsrc">{e(str(src) or 'no source recorded')}
            {f"<em>{e(str(d.get('deal_stage')))}</em>" if d.get('deal_stage') else ''}</div>
        </div>""")

    # ---- plain-language model
    sents = []
    for grp in ("lines", "outputs"):
        for k, ln in spec[grp].items():
            s = sentence(spec, k, ln)
            if s:
                sents.append(f"<li><b>{e(str(ln.get('label') or k))}</b> = {e(s)}</li>")
            elif grp == "lines":
                sents.append(f"<li><b>{e(str(ln.get('label') or k))}</b> — "
                             f"<span class='muted'>entered directly, not calculated</span></li>")

    inc_rows = "".join(
        vrow("  " + str(l.get("label") or k), k)
        for c in INCOME_CATS for k, l in spec["lines"].items() if l.get("category") == c)
    cost_rows = "".join(
        vrow("  " + str(l.get("label") or k), k)
        for k, l in spec["lines"].items() if l.get("category") == "cost")
    imp_rows = "".join(
        vrow(str(l.get("label") or k), k, l.get("unit"))
        for k, l in spec["lines"].items() if l.get("category") == "impact")
    out_rows = "".join(
        vrow(str(o.get("label") or k), k, o.get("unit"))
        for k, o in spec["outputs"].items())

    thead = "".join(f"<th class='num'>{e(p)}</th>" for p in per)

    prio_rows = ""
    if explore:
        for r in explore["research_order"][:8]:
            ev = r.get("grade") or "ungraded"
            stage = f" / {r['deal_stage']}" if r.get("deal_stage") else ""
            prio_rows += (f"<tr><td>{r['priority_rank']}</td><td>{e(str(r['label']))}</td>"
                          f"<td class='num'>{r['share']*100:.1f}%</td>"
                          f"<td>{e(ev)}{e(stage)}</td></tr>")
        ties = explore.get("ties") or []
        if ties:
            prio_rows += (f"<tr><td colspan=4 class='muted'>{ties[0]['count']} drivers share "
                          f"identical leverage — one multiplicative chain, so evidence "
                          f"decides the order, not arithmetic.</td></tr>")

    # The evidenced cases are the point of the scenarios section: the model priced
    # at the other end of its own sources, rather than at a mood someone chose. They
    # belong on the page a funder reads, not only in the terminal.
    scen, seen_ov = "", []
    for row in scenario_rows(spec):
        ov = row["overrides"]
        if ov and any(ov == prev for prev in seen_ov):
            continue  # a hand-written scenario already says this
        seen_ov.append(ov)
        v = row["res"]["values"]
        tag = ("<span class='eb'>from your evidence</span>" if row.get("evidenced")
               else "")
        scen += (f"<tr><td>{e(row['name'])} {tag}"
                 f"<div class='muted'>{e(str(row.get('why') or ''))}</div></td>"
                 f"<td class='num'>{e(fmtv(v['net'][-1], None, cur))}</td>"
                 f"<td class='num'>{e(fmtv(v['grant_dependency'][-1],'percent',cur))}</td>"
                 f"<td class='num'>{e(fmtv(v['cumulative_net'][-1], None, cur))}</td></tr>")

    q = spec["meta"].get("question")
    doc = f"""<!DOCTYPE html><html lang="{e(spec['meta'].get('language','en'))}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(str(spec['meta'].get('name','Business model')))}</title>
<style>
:root{{--bg:#f9f9f7;--s:#fff;--t:#0b0b0b;--t2:#52514e;--t3:#898781;--ring:rgba(0,0,0,.1);
--acc:#2a78d6;--good:#0ca30c;--warn:#fab219;--bad:#d03b3b;--grid:#e1e0d9}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0d0d0d;--s:#1a1a19;--t:#fff;--t2:#c3c2b7;
--t3:#898781;--ring:rgba(255,255,255,.12);--acc:#3987e5;--bad:#e66767;--grid:#2c2c2a}}}}
*{{box-sizing:border-box;margin:0}}
body{{font:14px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);
color:var(--t);padding:22px;max-width:1180px;margin:0 auto}}
h1{{font-size:22px}}h2{{font-size:12.5px;text-transform:uppercase;letter-spacing:.05em;
color:var(--t3);margin:24px 0 8px}}
.q{{font-size:15px;color:var(--t2);margin:4px 0 16px;max-width:70ch}}
.card{{background:var(--s);border:1px solid var(--ring);border-radius:10px;padding:14px 16px}}
.grid{{display:grid;grid-template-columns:340px 1fr;gap:16px;align-items:start}}
@media(max-width:940px){{.grid{{grid-template-columns:1fr}}}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:14px}}
.tile .l{{font-size:11px;color:var(--t3);text-transform:uppercase;letter-spacing:.04em}}
.tile .v{{font-size:22px;font-weight:650}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:.04em;
color:var(--t3);padding:6px 8px 6px 0;border-bottom:1px solid var(--grid)}}
td{{padding:6px 8px 6px 0;border-bottom:1px solid var(--grid);color:var(--t2)}}
td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums}}
tr.tot td{{font-weight:650;color:var(--t);border-top:1px solid var(--t3)}}
.drv{{padding:8px 0;border-bottom:1px solid var(--grid)}}
.dhead{{display:flex;align-items:baseline;gap:6px;font-size:12.5px}}
.dlabel{{flex:1;color:var(--t2)}}
.rank{{display:inline-block;background:var(--acc);color:#fff;font-size:10px;border-radius:99px;
padding:0 5px;margin-right:5px}}
.dsrc{{font-size:11px;color:var(--t3);margin-top:2px}}
.dsrc em{{background:var(--warn);color:#3a2a00;border-radius:3px;padding:0 4px;font-style:normal}}
output{{font-variant-numeric:tabular-nums;font-weight:650;font-size:12.5px}}
input[type=range]{{width:100%;accent-color:var(--acc);margin-top:3px}}
.badge{{display:inline-block;min-width:17px;text-align:center;border-radius:99px;
font-size:10.5px;font-weight:700;color:#fff;padding:0 5px;cursor:help}}
.gA{{background:var(--good)}}.gB{{background:var(--acc)}}.gC{{background:var(--warn);color:#3a2a00}}
.gD{{background:var(--bad)}}.gP{{background:none;color:var(--t3);border:1px solid var(--ring)}}
.g\\?{{background:none;color:var(--t3);border:1px dashed var(--ring)}}
.thr{{display:flex;gap:8px;align-items:flex-start;padding:7px 0;border-bottom:1px solid var(--grid)}}
.pill{{font-size:10.5px;font-weight:700;border-radius:99px;padding:1px 7px;color:#fff;flex:none}}
.pOK{{background:var(--good)}}.pNO{{background:var(--bad)}}.pBR{{background:var(--warn);color:#3a2a00}}
.muted{{color:var(--t3);font-size:12px}}
.eb{{display:inline-block;font-size:10px;text-transform:uppercase;letter-spacing:.04em;
background:var(--acc);color:#fff;border-radius:99px;padding:1px 7px;vertical-align:1px}}
ul{{margin:0;padding-left:18px}}li{{font-size:12.5px;color:var(--t2);padding:2px 0}}
.warn{{background:#fff4d6;border:1px solid var(--warn);color:#4a3500;border-radius:8px;
padding:10px 12px;font-size:12.5px;margin-bottom:14px}}
@media(prefers-color-scheme:dark){{.warn{{background:#2a2410;color:#e9d9a8}}}}
footer{{margin-top:20px;font-size:11.5px;color:var(--t3)}}
button.rst{{font-size:11.5px;background:none;border:1px solid var(--ring);border-radius:6px;
padding:2px 9px;color:var(--t2);cursor:pointer}}
</style></head><body>
<h1>{e(str(spec['meta'].get('name','Business model')))}</h1>
{f'<div class="q">{e(str(q))}</div>' if q else ''}

<div class="warn">
  <b>{len(drivers)} assumptions. {graded} graded, {sourced} with a source, {len(weak)} still a
  guess.</b> Every number below is computed from those assumptions — move a slider and watch
  what it does. This is a projection, not a forecast: it is only worth what the evidence
  behind its inputs is worth, which is what the grades record.
</div>

<div class="tiles">
  <div class="card tile"><div class="l">Net, {e(per[-1])}</div><div class="v" id="t_net"></div></div>
  <div class="card tile"><div class="l">Grant dependency</div><div class="v" id="t_gd"></div></div>
  <div class="card tile"><div class="l">Reserves, {e(per[-1])}</div><div class="v" id="t_res"></div></div>
  <div class="card tile"><div class="l">Earned covers</div><div class="v" id="t_cov"></div></div>
</div>

<div class="grid">
  <div>
    <div class="card">
      <h2 style="margin-top:0">Assumptions <button class="rst" id="rst">reset</button></h2>
      {''.join(drows)}
    </div>
  </div>
  <div>
    <div class="card">
      <h2 style="margin-top:0">The model</h2>
      <table><thead><tr><th>Line</th>{thead}</tr></thead><tbody id="tb">
        {inc_rows}
        {vrow('Total income','total_income',None,'tot')}
        {cost_rows}
        {vrow('Total costs','total_costs',None,'tot')}
        {vrow('Net','net',None,'tot')}
        {vrow('Reserves (cumulative)','cumulative_net')}
        {vrow('Grant dependency','grant_dependency','percent')}
      </tbody></table>
    </div>

    {f'<h2>Impact</h2><div class="card"><table><thead><tr><th>Measure</th>{thead}</tr></thead><tbody>{imp_rows}</tbody></table></div>' if imp_rows else ''}
    {f'<h2>Key ratios</h2><div class="card"><table><thead><tr><th>Measure</th>{thead}</tr></thead><tbody>{out_rows}</tbody></table></div>' if out_rows else ''}

    <h2>Does it work?</h2>
    <div class="card" id="thr"></div>

    <h2>How the model works, in words</h2>
    <div class="card"><ul>{''.join(sents)}</ul>
      <div class="muted" style="margin-top:8px">If a line here does not describe how the money
      actually arrives, the model is wrong in a way no amount of better numbers will fix.</div>
    </div>

    {f'<h2>Research these first</h2><div class="card"><table><thead><tr><th>#</th><th>Assumption</th><th class="num">Leverage</th><th>Evidence</th></tr></thead><tbody>{prio_rows}</tbody></table><div class="muted" style="margin-top:8px">Ranked by leverage weighted by how weak the evidence is. A high-leverage number from a signed contract needs nothing; the same leverage on a guess is where the risk lives.</div></div>' if prio_rows else ''}

    {f'<h2>Scenarios</h2><div class="card"><table><thead><tr><th>Scenario</th><th class="num">Net ({e(per[-1])})</th><th class="num">Grant dep.</th><th class="num">Reserves</th></tr></thead><tbody>{scen}</tbody></table><div class="muted" style="margin-top:8px">Rows marked <span class="eb">from your evidence</span> are not opinions about the future. They move every researched assumption to the end of the range its own sources support, which is the question a funder is really asking. Sliders above show the live model; this table is fixed.</div></div>' if scen else ''}
  </div>
</div>

<footer>Generated {date.today().isoformat()} from the model spec · recalculates in your browser,
no internet needed · grades and sources reflect what has been recorded, not an audit.</footer>

<script>
const N = {js['n']};
const CUR = {json.dumps(cur)};
const PER = {json.dumps(per)};
const BASE = {json.dumps({k: (d.get('values') if isinstance(d.get('values'), list)
                             else [d.get('values', d.get('value'))] * n)
                          for k, d in drivers.items()}, default=float)};
const CAT = {json.dumps(js['cat'])};
const OWNED = {json.dumps(js['owned'])};
const CONSTS = {json.dumps(js['consts'])};
const UNITS = {json.dumps(
    {k: (spec['lines'].get(k) or spec['outputs'].get(k) or {}).get('unit')
     for k in list(spec['lines']) + list(spec['outputs'])}
    | {"grant_dependency": "percent", "earned_ratio": "percent"})};
const THR = {json.dumps([{k: v for k, v in t.items() if k != 'js'} for t in js['thresholds']])};

const V = {{
  k: x => Array(N).fill(x),
  z: () => Array(N).fill(0),
  add:(a,b)=>a.map((x,i)=>x+b[i]), sub:(a,b)=>a.map((x,i)=>x-b[i]),
  mul:(a,b)=>a.map((x,i)=>x*b[i]), div:(a,b)=>a.map((x,i)=>b[i]?x/b[i]:0),
  pow:(a,b)=>a.map((x,i)=>Math.pow(x,b[i])), mod:(a,b)=>a.map((x,i)=>b[i]?x%b[i]:0),
  neg:a=>a.map(x=>-x), not_:a=>a.map(x=>x?0:1),
  cmp:(o,a,b)=>a.map((x,i)=>{{const y=b[i];return (o=='<'?x<y:o=='>'?x>y:o=='<='?x<=y:
    o=='>='?x>=y:o=='=='?x==y:x!=y)?1:0;}}),
  and_:vs=>Array.from({{length:N}},(_,i)=>vs.every(v=>v[i])?1:0),
  or_:vs=>Array.from({{length:N}},(_,i)=>vs.some(v=>v[i])?1:0),
  where:(c,a,b)=>c.map((x,i)=>x?a[i]:b[i]),
  prev:a=>[0].concat(a.slice(0,-1)),
  cumul:a=>{{let s=0;return a.map(x=>s+=x);}},
  total:a=>Array(N).fill(a.reduce((p,c)=>p+c,0)),
  peak:a=>Array(N).fill(Math.max(...a)), first:a=>Array(N).fill(a[0]),
  last:a=>Array(N).fill(a[a.length-1]),
  abs:a=>a.map(Math.abs), round:(a,d)=>a.map(x=>+x.toFixed(d?d[0]:0)),
  min:(...g)=>Array.from({{length:N}},(_,i)=>Math.min(...g.map(v=>v[i]))),
  max:(...g)=>Array.from({{length:N}},(_,i)=>Math.max(...g.map(v=>v[i]))),
  clamp:(a,lo,hi)=>a.map((x,i)=>Math.max(lo[i],Math.min(hi[i],x))),
  npv:(r,f)=>Array(N).fill(f.reduce((s,x,i)=>s+x/Math.pow(1+r[0],i+1),0)),
  irr:a=>{{const f=r=>a.reduce((s,x,i)=>s+x/Math.pow(1+r,i),0);
    let lo=-0.9999,hi=10,fl=f(lo);if(fl*f(hi)>0)return Array(N).fill(0);
    for(let i=0;i<200;i++){{const m=(lo+hi)/2,vv=f(m);if(Math.abs(vv)<1e-9)return Array(N).fill(m);
    if(fl*vv<0)hi=m;else{{lo=m;fl=vv;}}}}return Array(N).fill((lo+hi)/2);}}
}};

function catSum(v, cats) {{
  let o = V.z();
  cats.forEach(c => (CAT[c]||[]).forEach(k => {{ if (v[k]) o = V.add(o, v[k]); }}));
  return o;
}}
function derive(v) {{
  const put = (k, val) => {{ if (!OWNED.includes(k)) v[k] = val; }};
  const earned = catSum(v, ['earned']), grant = catSum(v, ['grant']);
  const inv = catSum(v, ['investment']), ink = catSum(v, ['inkind']);
  const income = V.add(V.add(earned, grant), V.add(inv, ink));
  const costs = catSum(v, ['cost']);
  put('total_earned', earned); put('total_grant', grant);
  put('total_investment', inv); put('total_inkind', ink);
  put('total_income', income); put('total_costs', costs);
  put('net', V.sub(income, costs));
  put('net_excl_grants', V.sub(V.sub(income, grant), costs));
  put('grant_dependency', V.div(grant, income));
  put('earned_ratio', V.div(earned, income));
  put('cumulative_net', V.cumul(v['net'] || V.sub(income, costs)));
}}
function compute(dv) {{
  const v = Object.assign({{}}, JSON.parse(JSON.stringify(CONSTS)), dv);
  derive(v);
{js['assign']}
  derive(v);
  return v;
}}

const fmt = (x, u) => {{
  if (u === 'percent') return (x*100).toFixed(1) + '%';
  const a = Math.abs(x);
  if (a >= 1e9) return (x/1e9).toFixed(2)+'B';
  if (a >= 1e6) return (x/1e6).toFixed(2)+'M';
  if (a >= 1e4) return (x/1e3).toFixed(0)+'k';
  if (a >= 100) return x.toLocaleString(undefined,{{maximumFractionDigits:0}});
  // Below 100, drop the decimals only if there are none: a 2.5-year lifespan
  // rendered as "3" misreads the assumption a reader is checking.
  if (a >= 1)   return x.toLocaleString(undefined,{{maximumFractionDigits:2}});
  if (a === 0)  return '0';
  return x.toPrecision(3);
}};

let DV = JSON.parse(JSON.stringify(BASE));

function refresh() {{
  const v = compute(DV);
  document.getElementById('t_net').textContent  = fmt(v.net[N-1]);
  document.getElementById('t_gd').textContent   = fmt(v.grant_dependency[N-1],'percent');
  document.getElementById('t_res').textContent  = fmt(v.cumulative_net[N-1]);
  document.getElementById('t_cov').textContent  = fmt(V.div(v.total_earned,v.total_costs)[N-1],'percent');
  ['t_net','t_res'].forEach(id=>{{
    const el=document.getElementById(id);
    el.style.color = parseFloat(el.textContent.replace(/[^0-9.-]/g,'')) < 0 ? 'var(--bad)' : '';
  }});
  document.querySelectorAll('#tb tr').forEach(tr => {{
    const key = tr.dataset.k; if (!key || !v[key]) return;
    tr.querySelectorAll('td.num').forEach((td,i) => td.textContent = fmt(v[key][i], UNITS[key]));
  }});
  document.querySelectorAll('tr[data-k]').forEach(tr => {{
    const key = tr.dataset.k; if (!v[key]) return;
    tr.querySelectorAll('td.num').forEach((td,i) => td.textContent = fmt(v[key][i], UNITS[key]));
  }});
  const T = [{','.join(f'(v)=>({t["js"]})' for t in js['thresholds'])}];
  document.getElementById('thr').innerHTML = THR.map((t,i) => {{
    const r = T[i](v).map(Boolean);
    const all = r.every(Boolean), any = r.some(Boolean);
    const firstMet = r.indexOf(true), firstBreach = r.indexOf(false);
    let cls, txt;
    if (all) {{ cls='pOK'; txt='every period'; }}
    else if (!any) {{ cls='pNO'; txt='never'; }}
    else if (firstBreach > firstMet) {{ cls='pBR';
      txt='holds '+PER[firstMet]+', then fails from '+PER[firstBreach]; }}
    else {{ cls='pOK'; txt='from '+PER[firstMet]; }}
    return `<div class="thr"><span class="pill ${{cls}}">${{cls=='pOK'?'OK':cls=='pNO'?'NO':'BREACH'}}</span>
      <div><b>${{t.name}}</b> — ${{txt}}<div class="muted">${{t.meaning||''}}</div></div></div>`;
  }}).join('');
  Object.keys(BASE).forEach(k => {{
    const o = document.getElementById('o_'+k); if (o) o.textContent = fmt(DV[k][N-1]);
  }});
}}

document.querySelectorAll('input[type=range]').forEach(s => s.addEventListener('input', ev => {{
  const k = ev.target.dataset.key, x = parseFloat(ev.target.value);
  const ratio = BASE[k][N-1] ? x / BASE[k][N-1] : 1;
  // Move the whole trajectory, not just the last period: a driver that grows over
  // time should keep its shape when you test it.
  DV[k] = BASE[k].map(b => BASE[k][N-1] === b && BASE[k].every(y=>y===b) ? x : b * ratio);
  refresh();
}}));
document.getElementById('rst').addEventListener('click', () => {{
  DV = JSON.parse(JSON.stringify(BASE));
  document.querySelectorAll('input[type=range]').forEach(s =>
    s.value = BASE[s.dataset.key][N-1]);
  refresh();
}});
refresh();
</script></body></html>"""
    return doc


def fmtv(v, unit=None, cur=""):
    if unit == "percent":
        return f"{v*100:.1f}%"
    a = abs(v)
    if a >= 1e9: return f"{v/1e9:,.2f}B"
    if a >= 1e6: return f"{v/1e6:,.2f}M"
    if a >= 1e4: return f"{v/1e3:,.0f}k"
    if a >= 100: return f"{v:,.0f}"
    if a == 0:   return "0"
    if a >= 1:   return f"{v:,.2f}".rstrip("0").rstrip(".")
    return f"{v:,.3g}"


def verify_js(html_path, spec, res, tol=1e-6):
    """Check the compiled JS reproduces the Python numbers.

    The page recalculates in the browser, so a transpiler bug would show the
    founder confident numbers that are simply wrong, with nothing to notice. Two
    engines are only an asset if they agree; otherwise they are a liability.
    Requires node, and says so plainly when node is absent rather than implying
    a check happened.
    """
    import re
    import shutil
    import subprocess
    import tempfile

    if not shutil.which("node"):
        return {"ran": False, "reason": "node not found — compiled JS not verified"}
    src = Path(html_path).read_text(encoding="utf-8")
    m = re.search(r"<script>(.*?)</script>", src, re.S)
    if not m:
        return {"ran": False, "reason": "no script block found"}
    body = m.group(1)
    # Keep only up to compute(); the DOM code below it cannot run under node.
    cut = body.find("const fmt =")
    harness = body[:cut] + """
const out = compute(JSON.parse(JSON.stringify(BASE)));
console.log(JSON.stringify(out));
"""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "check.js"
        f.write_text(harness, encoding="utf-8")
        p = subprocess.run(["node", str(f)], capture_output=True, text=True, timeout=60)
        if p.returncode != 0:
            return {"ran": True, "ok": False,
                    "reason": f"node error: {p.stderr.strip()[:300]}"}
        try:
            js_vals = json.loads(p.stdout)
        except json.JSONDecodeError:
            return {"ran": True, "ok": False, "reason": "JS produced no JSON"}

    diffs = []
    checked = 0
    for k, pv in res["values"].items():
        jv = js_vals.get(k)
        if jv is None:
            diffs.append({"key": k, "why": "missing in compiled JS"})
            continue
        for i, (a, b) in enumerate(zip(pv, jv)):
            checked += 1
            scale = max(1.0, abs(a))
            if abs(a - (b or 0)) / scale > tol:
                diffs.append({"key": k, "period": i, "python": a, "js": b})
                break
    return {"ran": True, "ok": not diffs, "checked": checked,
            "keys": len(res["values"]), "diffs": diffs[:8]}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out", default="report.html")
    ap.add_argument("--explore", default=None, help="explore.json for research ranking")
    ap.add_argument("--no-verify", action="store_true",
                    help="skip checking that the compiled JS matches Python")
    a = ap.parse_args()

    spec = load_spec(a.spec)
    errs, _ = validate(spec)
    if errs:
        for e_ in errs:
            print("  ERROR ", e_)
        raise SystemExit("spec has errors")
    res = compute(spec)
    ex = None
    if a.explore and Path(a.explore).exists():
        ex = json.load(open(a.explore, encoding="utf-8"))

    doc = render(spec, res, ex)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(doc, encoding="utf-8")
    print(f"report -> {a.out}  ({len(doc)//1024} KB, self-contained, works offline)")

    if not a.no_verify:
        v = verify_js(a.out, spec, res)
        if not v.get("ran"):
            print(f"  NOT VERIFIED: {v['reason']}. The page's own arithmetic has not been "
                  f"checked against this run.")
        elif v.get("ok"):
            print(f"  verified: the page reproduces all {v['keys']} computed series "
                  f"({v['checked']} values) exactly.")
        else:
            print(f"  MISMATCH between Python and the page's JS — do not send this file:")
            for d in v.get("diffs", []):
                print(f"    {d}")
            if v.get("reason"):
                print(f"    {v['reason']}")
            raise SystemExit(1)


if __name__ == "__main__":
    main()
