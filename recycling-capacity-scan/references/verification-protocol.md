# Verification protocol

## Verdicts (one per ledger row)
| Verdict | Use when |
|---|---|
| confirmed | A primary source, fetched and quoted, supports the claim as of a known date |
| wrong | A primary source contradicts it |
| outdated | It was true once (the source is real) but no longer holds, or the latest source is too old to rely on |
| unverifiable | No source found either way, or the source will not load. Prices usually end here |
| invented | The claim has no source anywhere and looks made up (a figure, a programme name, a facility) |
| pending | Not checked yet |

## Source types, strongest first
1. `call`: the facility told you, in writing after the call.
2. `register`: company register or official gazette (closures show up here first).
3. `company` and `press_release`: the facility's own site, reports and releases. Note the document date, not the date you read it.
4. `government` and `eu`: legislation, official reports, public bodies.
5. `academic`, `trade_press`, `news`: support only; they age fast and copy each other.
6. `aggregator`: directories and data resellers. Leads, never evidence.
7. `model`: anything an AI said from memory. Discovery only. It cannot confirm a row.

A search engine's summary of a page is not the page. In the test that built this skill, a search summary said the Seychelles "ratified the Basel Convention in 2015"; the UN depositary record says it acceded in 1993 and never signed. Fetch and quote.

A fetch tool that returns a model's summary of the page (WebFetch does) is also a summary. For the three things that matter most (dates, capacity figures, closure notices) get the raw text: download the PDF and extract it, call the register's API, or ask the fetch tool for the exact sentence and check it appears verbatim.

`public_body` is for statutory or sector bodies that are not ministries (Seafish, Zero Waste Scotland, national environment agencies). For a register, `source_date` is the date of the entry or event shown (incorporation, liquidation, last filing); if the register shows only current status, use the day you read it and say so in the note.

## Liveness checks (do these before anything else)
- Company register status: active, in liquidation, struck off. A small recycler can close between two articles about it. In the test, one of the two small European nylon-net recyclers both AI runs offered had been liquidated in 2025 and struck off in October 2026, and its website had become a hosting placeholder.
- Latest dated activity on the company's own channels. Silence for two years means call before you count it.
- Renames and takeovers. One recycler had rebranded; one chemical company had renamed its recycled line; one had just come out of Chapter 11.
- The site itself: a parked domain or a hosting placeholder is a signal worth one line in the report, not proof of closure. A certificate error is usually your own machine's CA store (it happened in the test); check in a browser before reporting it.
- **Permit to accept the waste.** A company can be active and still not be permitted to take this waste. Check the environmental regulator's public register where one exists (in the UK, SEPA and the Environment Agency; elsewhere the national permit or waste-operator register).

## Capacity traps
| Trap | Seen in the test |
|---|---|
| A collection target reported as plant capacity | "35,000 to 40,000 t/yr input" was a post-consumer collection target, and the company had put it on hold |
| A figure from the year a plant opened | A 2011 output figure still circulates in 2026 |
| A plan reported as nameplate | "50 t/yr" was a 2024 ambition; the company's own site showed 6.1 t of nets recovered |
| All feedstock reported as if it were this material | Carpets and nets share one plant; the share of nets is not published |
| Collected tonnage reported as recycled | One collector gathered 10,298 t and sent 8,042 t to material recycling in the same year |

Always record: basis (input, output, nameplate, collected, planned), scope (this material only, or all feedstock), and the document's date.

## Process and polymer fit
- Mechanical or chemical? Check the facility's own wording; models mix them up (in the test, a recycled-polyamide line was called "chemical" though its maker calls it mechanical).
- Which polymers, from which sources (post-industrial or post-consumer)? A recycler of PE/PP nets is not an outlet for nylon even if 2017 articles say it once ran a nylon grade.
- A collector is not a recycler. Keep them in separate lists, and ask each collector where each fraction goes.

## Look for what the model missed
- The local operator at the origin. In the test, the no-web answer did not know that a collector already worked in the same port, with a buyer and a stripping spec. The web run found it in the first searches.
- Non-English sources in each destination country.
- Registers and EPR scheme lists, which name operators that never appear in English-language press.

## Spot-check rule
When verification is split across parallel agents, the lead re-opens the source for every `confirmed` capacity and terms row, and for every closure, before the report goes out.
