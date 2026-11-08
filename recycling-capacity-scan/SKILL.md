---
name: recycling-capacity-scan
description: "Desk scan of where a waste material can be recycled: which facilities take it, their capacity, the condition and preparation they need, what they pay or charge, and how to ship it there legally. Every claim goes into a sourced ledger and is checked before it reaches a report. Use for questions like 'who can recycle our end-of-life fishing nets in Europe', 'find recyclers for PA6 / HDPE / textile waste', 'recycling market scan', 'offtake options for collected material', or before a feasibility study or business model that depends on a buyer."
version: 0.1.0
---

# Recycling-capacity scan

A desk scan for circular-economy practitioners. It answers four questions about one material from one origin:

1. Who can take it (recyclers, and separately the collectors that feed them)?
2. How much can they take, and is that figure current?
3. What condition must it arrive in?
4. How does it get there legally, and what does that cost?

It was built from a test run on nylon fishing nets from Victoria, Seychelles (azvai.com, November 2026). In that test an unchecked AI answer named plausible companies with guessed capacities and prices, and got the shipping route wrong. The method below exists to catch those errors.

**It does not replace the phone calls.** Gate fees, current appetite, acceptance specs and freight quotes come from the facilities and a forwarder. The scan ends with a call list, not a decision.

## Inputs to collect first (ask if missing)

| Input | Example |
|---|---|
| Material and form | End-of-life purse-seine nets, mostly PA6, with lead lines and floats attached |
| Polymer certainty | Tested (FTIR or DSC), declared by the supplier, or assumed |
| Origin | Port Victoria, Seychelles (non-OECD, Basel Party) |
| Destination region | EU and UK, or "anywhere" |
| Quantity and rhythm | 300 t stockpile plus about 150 t a year |
| What the user can do at origin | Strip lead lines, cut, bale, wash? |

## Workflow

### Step 1. Candidate discovery (fast, wide, nothing trusted yet)
- Search in the languages of the destination countries, not only English (French, Spanish, Italian, Norwegian and Lithuanian sources were all needed in the nets test).
- Search for the material, for its waste codes and for the projects that already moved it: EU-funded projects, NGO collection schemes, brand take-back schemes, port and EPR schemes.
- Ask who already handles the material at the origin. A local collector usually already has a buyer and a spec, and that is the best lead in the scan.
- Put every candidate in the ledger as `pending`. A model's own recall is fine for discovery and worthless as evidence.

- If the material is rigid (pipe, crates, floats), search the general regrind market for that polymer as well. Most fishing-gear recyclers take nets and rope only.

### Step 2. The claim ledger
Use `templates/ledger.csv` (header only) and copy the style of `templates/ledger-example.csv`. **One row per claim, not per company**, so every number has its own source, date and verdict. Read `references/verification-protocol.md` before grading.

| Column | Allowed values or format |
|---|---|
| field | `exists`, `operating`, `location`, `process`, `capacity`, `polymers`, `input_spec`, `terms`, `contact_route`, `other` |
| source_type | `call`, `register`, `company`, `press_release`, `government`, `eu`, `public_body`, `academic`, `trade_press`, `news`, `aggregator`, `model` |
| verdict | `confirmed`, `wrong`, `outdated`, `unverifiable`, `invented`, `pending` |
| source_date | Date of the document (`YYYY-MM-DD`, `YYYY-MM` or `YYYY`); for registers see the protocol |
| accessed | The day you read it |
| value | The claim. Put double quotes around any value with a comma |

Rules of thumb:
- Every facility gets an `exists` row and an `operating` row. The `operating` row states the current status in plain words ("Not operating. Liquidation opened 2025-09-02"); the checker drops a facility whose confirmed status says it has closed.
- A capacity value names its basis and scope, for example `"15,961 t post-consumer waste collected in 2025, all feedstock, not nets only"` (basis words: input, output, nameplate, collected, planned).
- "Nothing published" is a finding: a row with verdict `unverifiable`, the page you searched as the source, and a note.

The checker gives each facility one status:

| Status | Means |
|---|---|
| VERIFIED (n/m claims confirmed) | Exists and operating, both confirmed from a primary source |
| EXISTS, operation not confirmed | Existence confirmed, no confirmed `operating` row yet |
| UNVERIFIED | No primary source confirms that it exists |
| RECHECK FIT | A claim about its process or polymers was wrong; it may not be an outlet for this material |
| DROP (not operating) | Closed, or its operating claim was wrong or outdated |
| DROP (invented) | The facility itself was made up |

### Step 3. Verification passes (in this order)
1. **Exists and operating.** The company register first (Companies House, annuaire-entreprises.data.gouv.fr and BODACC, Brønnøysund, national registers), then the company's own site and its latest dated news. Closed, in liquidation, or silent for more than two years is a stop. Where the regulator publishes permits (SEPA, Environment Agency, national registers), check that the facility may accept this waste.
2. **Process and polymers.** Mechanical or chemical, which polymers it takes and which it refuses. A recycler of PE/PP nets is not an outlet for nylon, even if old articles say it is.
3. **Capacity.** Record the basis (input, output, nameplate, collected, planned), the scope (nets only or all feedstock) and the date. A 2011 nameplate figure is history, not capacity.
4. **Input spec.** Only the facility's own documents or a call count. Note what is missing; it becomes a call question.
5. **Terms.** Prices and gate fees are almost never published. Mark them `unverifiable` and move them to the call list. Never let a model's price range into a report as a fact.

Run the checker after each pass:

```bash
python scripts/check_ledger.py ledger.csv --as-of YYYY-MM-DD --check-urls --out ledger-report.md
```

It fails when a claim is "confirmed" by a model answer or an aggregator alone, has no date, gives a capacity without a basis, or cites a page that returns 404 or 410. It warns about sources older than 24 months, pages that block bots or fail to load, and verified facilities whose input spec is still unknown. Fix every ERROR before writing anything. Install `certifi` (`pip install certifi`) so `--check-urls` uses a current certificate bundle; without it some Python builds report every https page as broken.

### Step 4. Shipping route
Read `references/waste-shipment-eu.md`. Classify the material as it will actually leave the origin (after any stripping and sorting), then work out the procedure from the origin's OECD and Basel status. Quote the article numbers. For a UK origin or a move within one country, the reference only points to the regulators; read their current guidance and quote it. Island origins add a sea leg even within one country. Freight rates come from quotes, not from the web.

### Step 5. Outputs
1. `ledger.csv` plus `ledger-report.md` (the checker's output).
2. A short report: verified outlets first, then collectors, then dropped candidates with the reason. Every figure carries its date and source.
3. `call-list.md`: per facility, the open questions from `references/call-script.md`.

## Model delegation
Discovery and first-pass verification are read-heavy, so they can run on a cheaper model or in parallel subagents, one batch of facilities each, all writing ledger rows in the same format. The lead model spot-checks every `confirmed` row on capacity and terms against the quoted source before the report.

## Files
- `references/verification-protocol.md`: evidence grades, liveness checks, capacity traps, the error types seen in testing
- `references/waste-shipment-eu.md`: EU import and export rules under Regulation (EU) 2024/1157, Basel plastic entries, waste codes
- `references/call-script.md`: what to ask a recycler, a collector and a forwarder
- `templates/ledger.csv`: empty ledger with the header
- `scripts/check_ledger.py`: the ledger checker (standard library only)
- `evals/`: fixture with one seeded fault per facility and the unit tests (`python -m unittest discover -s evals`)
- `examples/nylon-nets-seychelles-2026-11/`: the ledger and report from the original test
