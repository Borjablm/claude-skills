---
name: financial-model-audit
description: "Audit, stress-test and harden a financial model that ALREADY EXISTS as a spreadsheet — business plans, venture projections, business cases, grant and investment budgets. Extracts every assumption into a sourced ledger with evidence grades, finds structural errors (double counting, totals that skip rows, inconsistent formulas, a subset larger than its source), ranks assumptions by how much they move the result weighted by how weak their evidence is, and writes it all back into the user's own workbook with provenance on every cell. Use this skill whenever someone has a spreadsheet of forecasts and wants it reviewed, sanity-checked, stress-tested, challenged, sourced, or made defensible before a board, funder, bank or investment committee — including 'can you look at these numbers' with an .xlsx attached, 'which assumptions actually matter', 'run a sensitivity analysis on this model', 'what will they pick apart', or 'I inherited this model and have to present it'. Also use for evaluating and comparing models submitted by other people. NOT for building a model when no spreadsheet exists yet — for that, and for social or environmental enterprises specifically, use sustainable-business-model."
license: MIT
---

# Financial model audit

## What this is for

A financial model is an argument about the future wearing the costume of arithmetic.
The formulas are almost never the hard part: they are multiplication. The argument
lives in the assumptions, and for a venture that does not exist yet, those
assumptions are mostly guesses about the outside world. Which is fine. What is not
fine is when nobody can tell which numbers are evidenced and which were typed in
on a Tuesday, because then the whole model inherits the credibility of its weakest
cell, and the person presenting it finds that out in the room.

So the job here is not "check the maths". It is to make every number in the model
say where it came from, find the few that actually decide the answer, and put
honest ranges around them.

## The shape of the work

Six stages. They are not a ritual — skip freely. An audit for a first read is
stages 1-4 and takes minutes. A full hardening runs everything and is measured in
days, most of it research.

1. **Map** — parse the workbook into a dependency graph, verify it reproduces
2. **Extract** — pull every assumption into a ledger
3. **Audit** — structural checks the eye cannot do
4. **Rank** — find the assumptions that actually move the result
5. **Research** — source the weak ones that matter (this is the expensive part)
6. **Scenario & render** — build cases, write it back into their workbook

Numbers come from the scripts; judgment comes from you. That division is the whole
design. The scripts parse, recompute, rank and render deterministically — no model
guesses at arithmetic. You grade evidence, interpret findings, decide what to
research, and say what it means. When you report a number, it came from a script;
when you report a judgment, it is yours and you own it.

## Setup

```bash
python -m pip install openpyxl        # the only dependency
```

Work in a project folder per model. Keep the client's file untouched in `inputs/`;
state lives in `model/`; deliverables land in `exports/`.

```
project/
├── inputs/    model.xlsx  (never edited)
├── model/     graph.json, ledger.json, findings.json, sensitivity.json
└── exports/   model-hardened.xlsx, summary.html
```

## Stage 1 — Map

```bash
python scripts/model_graph.py inputs/model.xlsx --out model/graph.json --verify
```

`--verify` recomputes every formula and compares against the values Excel cached.
Read that number before anything else. If it says 160/160, the graph is the model
and everything downstream is trustworthy. If formulas are unsupported or mismatched,
say so plainly and work around those cells — analysis of a model you cannot
reproduce is analysis of a different model, and quietly reporting confident numbers
from a broken parse is the worst thing this skill could do.

Every model is shaped differently, so expect surprises rather than the layout you
last saw. Periods may run down the rows instead of across the columns; labels may
sit above their values rather than beside them; a workbook may be monthly with 60
columns, or in Spanish, or built on named ranges and lookup tables. The parser
handles these, but two caveats are worth holding:

- **Files written by a script have no cached values**, so `--verify` reports
  nothing to check. That is not a pass. Say so.
- **`checked` counts only numeric formulas.** A high match rate on 8 of 200
  formulas is not a verified model.

If `--verify` reports unsupported functions, name them for the user and say which
cells are affected rather than silently treating them as zero.

The command prints candidate output cells, matched either by label (in several
languages) or, failing that, structurally — terminal formulas with the deepest
dependency trees, which is what a result cell looks like in any language. Confirm
the target rather than interrogating: *"I'll rank assumptions against Y3 net profit
— that's the number the committee decides on, right?"* When the label pass finds
nothing and the structural fallback is guessing, say so and ask.

## Stage 2 — Extract

```bash
python scripts/ledger.py --graph model/graph.json --out model/ledger.json --csv exports/ledger.csv
```

An assumption is a hardcoded number something else depends on. The script finds
them, infers what each means from the surrounding labels, and reads any note the
modeller left into a provisional **evidence signal** (`strong` / `weak` /
`unclear` / `none`).

That signal is a sorting device, not a verdict. Grading is yours. Read
`references/grading-rubric.md` and grade the ones that matter — which, after Stage
4, you will know. Do not grade all 149 rows in a big model; grade the ones with
leverage and leave the rest, because an audit that spends its attention evenly
spends it badly.

Write grades, sources and confidence back into `model/ledger.json`. Re-running the
script preserves them.

## Stage 3 — Audit

```bash
python scripts/audit.py --graph model/graph.json --out model/findings.json
```

Seven deterministic checks, grouped by root cause so three year-columns of one
mistake read as one finding.

Three of the checks read labels (`stock-times-flow`, `subset-exceeds-total`, and
the flow/duration vocabulary behind them), which means they can only fire on words
they recognise. The lists cover several languages and are domain-neutral, but a
sector says things they cannot anticipate — "per tonne", "per MWh", "per bed-night".
So **a clean audit is not proof of a clean model**, only that nothing recognisable
tripped. Extend with `--vocab extra.json` when a model's language is unusual, and
lean on the judgment checklist regardless.

The two checks that most often change the answer:

- **stock-times-flow** — a per-day rate multiplied by a duration, then labelled as
  a population. Twenty days of a 1.3M-player game is not 26M players; it is the
  same players, twenty times. Everything downstream inflates.
- **subset-exceeds-total** — an "addressable market" larger than the market. Always
  a symptom, usually of the above.

Then read `references/audit-checklist.md` for the judgment checks no script can
make: whether the driver logic actually describes the business, whether the cost
base moves with revenue, whether the growth curve has a mechanism behind it.

Findings are flags, not corrections. Some are deliberate. Present each with its
formula and its consequence, and let the modeller rule — you are reviewing their
work, and the fastest way to lose the room is to announce their model is wrong
when they had a reason.

## Stage 4 — Rank

```bash
python scripts/sensitivity.py --graph model/graph.json --ledger model/ledger.json \
    --target "Sheet!E23" --out model/sensitivity.json
```

Two rankings come out and the second is the useful one.

**Leverage** is how much each assumption moves the target. Often a dozen
assumptions tie exactly, because driver models are multiplicative chains where
every link has identical leverage. The script says so when it happens. That is not
a failure of the analysis; it is a fact about the model, and it means arithmetic
cannot tell you what to research.

**Research priority** breaks the tie with evidence: leverage weighted by how weak
the backing is. A high-leverage number taken from audited actuals needs nothing. The
same leverage resting on "arbitrary assumption" is where the risk lives. That list
is your research plan, and it is usually five to ten rows out of a hundred and
fifty.

If the model feeds a decision with thresholds — a covenant, a break-even, a funding
band, a go/no-go — pass `--bands bands.json` and the script reports which
assumptions can flip the decision. A small swing that crosses a boundary matters
more than a large one that changes nothing anybody acts on.

```json
[{"name": "Band 1 — survival", "min": -100000000, "max": 0},
 {"name": "Band 2 — partial",  "min": 0, "max": 250000}]
```

## Stage 5 — Research

The expensive stage, so it runs on the priority list, not the whole ledger.
`references/research-protocol.md` has the method. The essentials:

Produce **ranges, not points**. A single number implies a precision nobody has, and
a range is what makes the scenario stage honest later.

Guard against **benchmark laundering** — taking a real statistic about a sector and
quietly promoting it into a venture-specific assumption. It is the most common way
an AI-researched model goes wrong, because every individual step looks defensible:
the source is real, the number is real, and the conclusion is fiction. Before a
value enters the ledger, check that the population, date and unit of the source
actually match the use. When you adapt a figure, write the adaptation down where a
reader will see it.

Some numbers are not researchable at all. A revenue line that depends on a named
counterparty is a **deal**, not a market fact, and its credibility is the stage of
that conversation. Record `deal_stage` (exploration / verbal / LOI / signed) rather
than sending an agent to find a source that does not exist. This matters more than
it sounds: presenting an exploratory conversation as a forecast, to a room that may
contain that counterparty, is a specific and avoidable embarrassment.

Where the organisation has actuals — an existing product, previous costs, a prior
year — anchor to them and grade them A. Internal data beats research for the base
year, every time. When projections contradict actuals, that is a finding.

Record in the ledger: `grade`, `confidence`, `source`, and
`researched: {range: [lo, hi], sources: [...], date: "..."}`.

## Stage 6 — Scenario and render

```bash
python scripts/scenarios.py --graph model/graph.json --ledger model/ledger.json \
    --auto --targets "Sheet!E23" --out model/scenario_results.json
```

`--auto` builds downside/upside from researched ranges, so the cases are what the
evidence allows rather than round numbers. Add hand-written scenarios for the
questions a reviewer will actually ask — the anchor client not signing, the channel
launching late — in a JSON file. The point of a scenario is not to predict; it is to
convert "is this number right?" into "what has to be true for this to work?", which
is a question a room can answer.

```bash
python scripts/render.py --xlsx inputs/model.xlsx --graph model/graph.json \
    --ledger model/ledger.json --findings model/findings.json \
    --sensitivity model/sensitivity.json \
    --out exports/model-hardened.xlsx --html exports/summary.html
```

The deliverable is their workbook, hardened: an Assumptions Ledger tab, a Findings
tab, provenance in a note on every assumption cell, and blue/black input/formula
colouring. Not a report *about* their model — the model itself, improved, which
they own and can still open in ten years without us.

One property of the write step worth knowing, because it looks like data loss:
re-saving preserves every formula but discards the values Excel had cached for
them, so the file rebuilds its numbers on first open (`fullCalcOnLoad` is set for
this reason). Open it once before forwarding it, and don't be alarmed if a
programmatic reader shows blanks in the meantime — the formulas are intact.

## Reporting

Lead with what changed the answer, not with volume. "149 assumptions, 5 findings"
is a statistic; "your Y3 revenue rests on six numbers, four of which have no
source, and one formula counts players twenty times" is a finding.

Be careful with tone when the model is someone's work. Structural findings are
easier to hear when they arrive with the formula, the corrected number, and no
adjectives. And the honest framing is usually true anyway: these defects are
normal, they are invisible by design, and finding them here is the cheap place to
find them.

## References

| File | Read it when |
|---|---|
| `references/grading-rubric.md` | Grading assumptions (Stage 2), incl. the benchmark-laundering test and partner-dependent staging |
| `references/research-protocol.md` | Researching assumptions (Stage 5), incl. deep mode with adversarial cross-check |
| `references/audit-checklist.md` | The judgment checks scripts cannot make (Stage 3), incl. building a model from drivers |

## Scripts

| Script | Does |
|---|---|
| `model_graph.py` | xlsx → dependency graph + formula evaluator; `--verify` proves the parse |
| `ledger.py` | assumptions → ledger (json/csv); merges, preserving your grades |
| `audit.py` | 7 structural checks, grouped by root cause |
| `sensitivity.py` | leverage + research-priority ranking; optional decision bands |
| `scenarios.py` | named override sets; `--auto` from researched ranges |
| `render.py` | hardened workbook (ledger tab, findings tab, cell notes, colour) + html summary |

All are plain Python with one dependency. They can be run by hand, in any order,
and their JSON is stable — so a user who wants to script their own pipeline around
them can.
