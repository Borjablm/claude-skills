# recycling-capacity-scan

A desk scan of where a waste material can be recycled. It covers which facilities take the material, how much they can take, what condition it must arrive in, and how to ship it there legally. Every claim goes into a sourced ledger and is checked before it reaches a report.

Built and tested on a real question in November 2026, which was where end-of-life nylon fishing nets from Victoria, Seychelles, can go in Europe. The write-up of that test, with the timings and every error the AI made, is on azvai.com: [Can AI Do a Recycling Market Scan?](https://azvai.com/en/ai-recycling-market-scan-fishing-nets/)

## Why the ledger

In the test, an unchecked AI answer named real companies and attached numbers that were old, misread or invented. Both AI runs offered a recycler that had gone into liquidation. One run gave a capacity figure no source supports, and described the wrong legal route for the shipment. The ledger keeps one row per claim (not per company), each with its source, the source's date and a verdict. The checker refuses to treat a model's answer or a directory listing as evidence.

## What's inside

| Path | What it is |
|---|---|
| `SKILL.md` | The workflow Claude follows: inputs, discovery, ledger, verification passes, shipping route, outputs |
| `references/verification-protocol.md` | Verdicts, source types, liveness checks, capacity traps, process and polymer fit |
| `references/waste-shipment-eu.md` | Imports into the EU under Regulation (EU) 2024/1157 with article numbers, Basel plastic entries, waste codes, UK pointers |
| `references/call-script.md` | What to ask recyclers, collectors, forwarders and authorities |
| `templates/ledger.csv`, `templates/ledger-example.csv` | Empty ledger and a worked example |
| `scripts/check_ledger.py` | The ledger checker (Python standard library; `certifi` recommended for `--check-urls`) |
| `evals/` | Fixtures with one seeded fault each and unit tests |
| `examples/nylon-nets-seychelles-2026-11/` | The ledger (118 claims) and checker report from the original test, personal details removed |

## Install

```bash
cp -r recycling-capacity-scan ~/.claude/skills/
pip install certifi   # optional, for --check-urls
```

Then ask Claude Code something like "who in Europe can recycle our end-of-life PA6 fishing nets, and how do we ship them from Port Louis?" and the skill takes over.

## Run the checker and tests

```bash
python scripts/check_ledger.py ledger.csv --as-of 2026-11-08 --check-urls --out ledger-report.md
python -m unittest discover -s evals
```

The checker exits with 1 when it finds an ERROR. Examples include a claim "confirmed" only by a model or an aggregator, a confirmed claim with no date, a capacity with no basis (input, output, nameplate, collected or planned), a source that returns 404 or 410, or a malformed row. Warnings cover old sources, pages that block bots and unconfirmed intake specs.

## Limits

- It is a desk scan. Gate fees, current appetite, intake specs and freight quotes come from calls, so the scan ends with a call list.
- The shipping reference is checked for imports into the EU. For UK and other routes it points to the regulators and does not summarise their rules.
- Search tools and fetch tools return model summaries. For dates, capacities and closure notices, read the raw text.

## Licence

MIT, like the rest of this repository.
