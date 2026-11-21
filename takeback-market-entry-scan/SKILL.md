---
name: takeback-market-entry-scan
description: "Desk research before a product take-back or reuse pilot enters a new country or region: the waste and producer-responsibility rules for that product stream, the permits and registrations partners need to collect, store, prepare for reuse, recycle and ship used material, candidate reuse, logistics and recycling partners, competitor take-back schemes, and disposal-cost benchmarks for pricing. Every legal claim is tied to the instrument and every partner claim to dated evidence, then checked. Use for 'take-back scheme in Ireland / Spain / the Netherlands', 'market entry for our reuse programme', 'what permits does a carpet / furniture / textile take-back partner need', 'who could be our reuse partner in X', or before a take-back P&L."
version: 0.1.0
---

# Take-back market-entry scan

A desk scan for circular-economy practitioners who are about to launch a take-back, reuse or product-return pilot in a market they do not know yet. It answers five questions for one product stream in one market:

1. **Rules.** When is the used product waste and when is it not; which waste codes; is there an EPR scheme that covers it (now or after transposition); which levies and taxes set the cost of disposal; which procurement or building rules create demand?
2. **Permits.** What a partner needs to collect and transport, to store, sort and prepare for reuse, to recycle, and to move the material across a border. Who issues each.
3. **Partners.** Who could reuse, collect and recycle it, and is each one operating today and handling this material?
4. **Competitors.** Which take-back schemes already run in the market, and on what terms?
5. **Prices.** What disposal costs the client today, so the service can be priced below it.

It was built from a timed test on used carpet tiles for the island of Ireland (azvai.com, November 2026), re-running the desk research for a 2019 take-back relaunch. The open-web run produced in 11 minutes a better legal map than the unchecked chatbot answer, and both missed the partner the 2019 team actually signed. The method below exists for those two facts.

**It ends with a call list, not a decision.** The regulator's reading of the borderline questions, partner appetite and capacity, real gate fees and the trust that makes a partner agreement work come from people. The scan makes those calls shorter and better aimed.

## Inputs to collect first (ask if missing)

| Input | Example |
|---|---|
| Product and condition | Used commercial carpet tiles, lifted dry, palletised, mixed brands and backings |
| Hierarchy wanted | Reuse first, recycling second, no landfill or incineration |
| Market and its jurisdictions | Island of Ireland: Republic of Ireland (EU) and Northern Ireland (UK, Windsor Framework) |
| Where recycling happens | On the island, in Great Britain, or a continental plant (name it) |
| Volumes and timing | Pilot of about 15,000 m2 a year from 2027 |
| What the client already has | Past partners in the market, past agreements, a brand scheme abroad |

**Ask for past partners first.** If the client, or anyone on the team, has worked in the market before, their partner list is the first lead and the first thing to re-check. In the Ireland test neither AI run named the reuse partner signed in 2019, which still trades.

## Workflow

### Step 1. Map the jurisdictions before the rules
Write down every jurisdiction the material touches: collection, storage, preparation, recycling and every border on the way. One island can be two legal systems (Republic of Ireland under EU law; Northern Ireland under UK law with EU goods and waste-shipment rules applying through the Windsor Framework). Federal or regional systems (Spain's autonomous communities, Belgium's regions) add a layer. Each jurisdiction gets its own rows.

### Step 2. Rules ledger (`templates/rules.csv`)
One row per legal claim. Read `references/legal-sources.md` first.

| Column | Allowed values or format |
|---|---|
| topic | `waste_status`, `classification`, `epr`, `levy`, `permit`, `shipment`, `procurement`, `product_law`, `other` |
| instrument | The instrument's full name and number, e.g. `S.I. No. 398 of 2023`, `SR 1999/362`, `Regulation (EU) 2024/1157` |
| provision | Article, regulation, section, schedule or annex |
| source_type | `legislation`, `official_journal`, `court`, `regulator_guidance`, `government`, `secondary`, `model`, `call` |
| in_force_from | Date the rule or rate applies from (required for any rate, fee, levy or tax) |
| verdict | `confirmed`, `wrong`, `outdated`, `unverifiable`, `invented`, `pending` |

What the verdicts mean for a rule: `confirmed` you read the provision itself and it says this; `outdated` it was the law and has been revoked, replaced or re-rated; `wrong` it never said this; `pending` you have only a search or fetch summary, a contents page, or no reading yet; `unverifiable` you looked and the text could not settle it. `legislation` is the text of an Act or regulation; `official_journal` is EUR-Lex or a national gazette; `regulator_guidance` is a regulator's page (SEPA, EPA, NIEA); `government` is a ministry or tax page (gov.uk, gov.ie, revenue.scot).

Rules of thumb, all from errors seen in testing:
- **Read the instrument, not a summary of it.** The no-web answer gave a landfill levy three years out of date and cited the wrong regulations for carrier registration. Both looked plausible.
- **Check amendments.** The as-made text of a permit regulation gave a 7,500 t residual cap; a 2008 amending instrument had changed it to 15% of intake. A row read from an "as made" URL needs a note saying the amendments were checked, or the checker warns.
- **Guidance pages lag the law.** A regulator's live page still cited the waste-shipment regulation that had been replaced six months earlier, and a fee on another page had gone up. Cite guidance for practice and contacts; cite the instrument for the rule.
- **Check EPR scope by product code.** The new EU textile EPR (Directive (EU) 2025/1892) covers clothing, household textiles and footwear by CN code. Carpets (CN chapter 57) are out, with a review promised. Read the annex, do not infer from the word "textiles".
- **Some official sites block bots.** irishstatutebook.ie and gov.ie returned 403 to one agent's fetcher and opened fine for a plain HTTP client. If a primary source blocks you, try the print or ELI URL, or a different fetcher, before falling back to a secondary page.
- **Never guess a legislation URL or number.** A cold test guessed two Act numbers on legislation.gov.uk and got a 404 and the wrong Act, and recalled a Scottish instrument number that turned out to be an animal-health order. Find the instrument through the site's search.
- An absence ("no EPR for carpet in the UK") is a claim too. Grade it `pending` until you have searched the register or the regulator has said so.

### Step 3. Permits matrix (`templates/permits-matrix.md`)
From the rules ledger, fill the template: activity (collect and transport, broker or arrange, store and sort, prepare for reuse, recycle, export, import) by jurisdiction, with the authorisation, the issuing body, the thresholds and the fee and date. Mark every borderline question (does cleaning carpet tiles fit a textiles exemption; which waste code the regulator expects) for the call list. These questions decide the partner's cost and lead time, which is why the legal track is the slowest part of a launch.

### Step 4. Partner discovery (wide, nothing trusted yet)
Search for the product, its waste codes, "reuse", "second-hand", "used", the brand take-back schemes and the public tenders that mention take-back. Search the national reuse network, the social-enterprise directories and the regulator's permit registers. Include partners just outside the market (GB or continental plants) when the market has none. Put every candidate in `templates/partners.csv` as `pending`.

### Step 5. Partner verification (`templates/partners.csv`)
One row per claim. Read `references/verification-protocol.md` before grading.

| Field | Holds |
|---|---|
| `exists` | Registered or otherwise real, with the register number. Every organisation needs one |
| `operating` | Current status in plain words ("Dissolved on 5 September 2026", "Filed accounts March 2026") |
| `location` | Address or sites |
| `role` | What it is and its legal form (charity, CIC, company limited by guarantee, commercial firm, brand scheme). A commercial firm in the same business may be a competitor |
| `material` | Dated evidence that it takes this product now |
| `terms` | Minimums, who pays, brands accepted, area served |
| `permit` | Authorisation and waste codes, from the regulator's register |
| `contact_route` | Who to call |
| `claim_check` | A check of a specific claim another run made ("a same-name company dissolved in 2015 is a different entity"). Not age-checked |
| `other` | Anything else |

`source_type` for partners: `register` (company, charity or permit registers such as Companies House, CRO, OSCR, the Charity Commission), `company` (its own pages), `press_release`, `government`, `eu`, `public_body` (councils, agencies, public reports), `news`, `trade_press`, `directory` (business directories and network member lists), `social`, `aggregator` (sites that repackage registers or AI-written listings; leads only), `model`, `call`, `other_secondary`.

In order: company register (it exists and files), dated evidence of activity in the last 12 months, dated evidence that it handles **this** material, then permits on the regulator's register, then terms. A live website with no dates is not evidence of operating. A domain can change hands: in the Ireland test two reuse organisations' old domains now served a betting guide and a stock-trading blog.

The checker gives each organisation one status:

| Status | Means |
|---|---|
| VERIFIED | Exists and operating (primary source) and handles the material |
| OPERATING, material not confirmed | Trading, but no dated evidence it takes this material now: a call question |
| EXISTS, operation not confirmed | Registered or listed, no dated sign of activity |
| UNVERIFIED | No primary source for its existence |
| DROP (not operating) / DROP (invented) | Closed, or made up |

### Step 6. Competitors and procurement
For each brand scheme active in the market: who pays, minimum volumes, brands accepted, whether the market is actually served (a scheme page that names the UK does not mean Ireland). Search public-tender portals and green-procurement case studies for take-back criteria. In the Ireland test a national buyer had scored take-back at 250 of 1,300 points in a carpet-tile tender, the strongest demand signal found.

### Step 7. Prices
Levies and taxes from the instrument (with the date they apply from and any announced increase). Gate fees from a published survey with its date, or mark them `unverifiable` and put them on the call list. Never let a model's price range into the report as a fact.

### Step 8. Check, then write
```bash
python scripts/check_ledger.py rules.csv --as-of YYYY-MM-DD --out rules-report.md
python scripts/check_ledger.py partners.csv --as-of YYYY-MM-DD --check-urls --out partners-report.md
```
The checker fails a confirmed legal claim with no instrument or one confirmed from a model or secondary source, a rate with no in-force date, a confirmed partner claim with no source date or from a model or aggregator, and a 404. It warns about rules confirmed from guidance only, text read as made without an amendment check, operating claims older than 12 months, and dead or bot-blocked pages. Install `certifi` for `--check-urls`. Fix every ERROR before writing.

Outputs: the two ledgers and reports, the permits matrix, a short report (rules, permits, verified partners, competitors, prices, each figure dated and sourced), and `call-list.md` built from `references/call-list.md`.

## Model delegation
Discovery and first-pass verification are read-heavy: run them on a cheaper model or as parallel subagents (one for the law, one per batch of partners), all writing the same ledger format. The lead model reads the instruments for every rate and permit row itself and spot-checks the partner rows that the operating model will depend on.

## Files
- `references/legal-sources.md`: where to find primary law per jurisdiction, and the traps
- `references/verification-protocol.md`: evidence grades for partners
- `references/call-list.md`: questions for regulators, partners, competitors and disposal sites
- `templates/rules.csv`, `templates/partners.csv`: empty ledgers; `templates/permits-matrix.md`: the permits table
- `scripts/check_ledger.py`: the checker (standard library; certifi optional)
- `evals/`: fixtures with seeded faults and unit tests (`python -m unittest discover -s evals`)
- `examples/carpet-tiles-ireland-2026-11/`: ledgers and reports from the original test
