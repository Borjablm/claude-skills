---
name: sustainable-business-model
description: "BUILD the financial model of a social or environmental enterprise from whatever exists — notes, a pitch deck, a grant application, a half-finished spreadsheet — for circular economy ventures, community businesses, repair and reuse projects, impact startups, co-ops, charities with trading income, and grant-funded programmes. Turns the documents into a readable model spec, links each assumption to the evidence already in the folder (and flags where the folder contradicts itself), finds the few numbers that decide the answer, and produces an interactive offline report plus a funder-ready spreadsheet. Use this skill when someone needs a business model, financial model, grant or funding budget, break-even or cost-recovery analysis, unit economics, or an impact-per-euro / cost-per-tonne figure — especially when they say they have no model yet, don't do spreadsheets, or need to answer 'when do we stop needing the grant' before a funder meeting. Blended grant + earned + in-kind income and impact metrics are first-class here. For auditing a finished spreadsheet model that already exists, use financial-model-audit instead."
license: MIT
---

# Sustainable business model

## Who this is for and what it changes

Social and environmental enterprises are modelled badly for a structural reason:
the people who understand the venture are rarely the people who can build a
spreadsheet, and the tools assume you are already an analyst. So the numbers get
made up the week before a funding deadline, and the founder ends up defending a
model they did not build and cannot inspect.

The premise here is that a founder who cannot write a formula can absolutely tell
you whether *"repair donations = repairs completed × average donation per repair"*
describes how the money actually arrives. That check is the one that catches the
errors worth catching. So the model lives in a small YAML spec they can read, and
everything else — the sums, the report, the spreadsheet — is generated from it.

They also ask a different question. A commercial model asks "how much profit?"; a
social enterprise asks **"when do we stop needing grants, and what has to be true
for that?"** The engine treats that as a first-class output rather than something
you bolt on.

## The shape of the work

```bash
python -m pip install pyyaml openpyxl        # required
python -m pip install pypdf python-docx python-pptx   # optional, for intake
```

```
project/
├── inputs/        whatever they have: deck, application, notes, old spreadsheet
├── spec.yaml      the model — the artifact that matters
└── out/           report.html, model.xlsx, explore.json
```

1. **Intake** — read what exists, list what is missing
2. **Draft the spec** — the venture in words, then in drivers
3. **Link evidence** — find what in the folder backs each driver, and what contradicts it
4. **Explore** — find the few assumptions that decide the answer
5. **Research** — source those few, properly (offer this; do not assume it)
6. **Challenge** — attack the model before a funder does
7. **Report** — interactive HTML, funder-ready xlsx
8. **Iterate** — everything is a re-render, so questions are cheap

Numbers come from the scripts; judgment comes from you. The scripts compute,
rank and render deterministically. You decide what the drivers are, what the
evidence is worth, and what it means.

## Ask, don't assume

This is somebody's venture, and the person you are working with knows things no
document contains. Left alone, it is easy to build a plausible model out of pure
inference and hand back something they cannot defend because they never agreed to
it. Stop at these five points. Keep each one to a real question with a real
default, not a menu.

| After | Ask | Why it cannot be inferred |
|---|---|---|
| Intake | "I couldn't read *X*, and I can't find anything about *Y*. Do those matter?" | The unreadable file is often the one with the numbers |
| Driver map | "Is this right: *we earn X each time a Y does Z*?" | Only they know how the money actually arrives |
| Evidence | "The deck says 75%, the model says 85% — which is current?" | Both are their documents; only they know which won |
| Explore | "Three numbers decide this. Research them — quick, deep, or not now?" | Research costs time and money that may not be yours to spend |
| Before delivery | "Should I attack this the way a funder will?" | Some people want the model hardened; some want it finished |

Confirm rather than interrogate. *"I'll rank against year-three net profit — that's
what the funder decides on, right?"* is one sentence and it can be answered with a
nod. A questionnaire is not a conversation, and a founder who feels examined stops
telling you the useful things.

## Stage 1 — Intake

```bash
python scripts/intake.py inputs/ --out out/intake.md
```

Extracts text from PDFs, decks, documents and spreadsheets, and lists every number
with the words around it. It deliberately does not guess the model: deciding that
"€4,800" is annual rent per site rather than a deposit is judgment, and a regex
that guessed wrong would be worse than no extraction, because nobody would check
it.

Read the digest. Note what could not be read and ask for it — the unreadable file
is often the one with the real numbers.

## Stage 2 — Draft the spec

Do this **with** the founder, in their language, and in this order.

**Write the revenue sentence in words first.** *"We earn X each time a Y does Z,
and Y does Z about N times a year."* If that sentence cannot be written, the model
is premature, and saying so is the honest deliverable — not a spreadsheet that
implies a business exists.

Then name the drivers in that sentence, and only then write `spec.yaml`. Full
format in `references/model-spec.md`; `assets/example-repair-network.yaml` is a
worked example. Revenue patterns specific to this sector — gate fees, material
recovery, product-as-a-service, reuse and repair, EPR fees, carbon credits, blended
grant funding — are in `references/revenue-archetypes.md`, each with its
characteristic failure mode.

Two things to get right at the start:

**Leave everything ungraded and unsourced.** A fresh model should be visibly all
guesses. That is honest, and the greyness shows exactly how far the work has got.
Do not invent sources to make it look finished.

**Categorise every line** (`earned` / `grant` / `investment` / `inkind` / `cost` /
`impact`). That is what makes grant dependency, cost recovery and impact ratios
compute themselves.

```bash
python scripts/model.py spec.yaml --check    # validate
python scripts/model.py spec.yaml            # compute and read
```

## Stage 3 — Link the evidence already in the folder

```bash
python scripts/evidence.py --spec spec.yaml --corpus inputs/ --out out/evidence.md
```

For each driver, this finds numbers sitting near the driver's own words and says
whether they agree with it. Two things come out, and the second is worth more.

**What the folder already proves.** The evidence for a model is usually in the room
already, just not next to the number it justifies. Run this on a real feasibility
folder and drivers you were about to grade "no source given" turn out to rest on
the consultant's own interviews — first-party research, grade B, and the strongest
thing in the pack. A model that undersells its own evidence is a failure too.

**What the folder contradicts.** When a deck says 75% and the model says 85%, or a
deck says 8 tonnes and the model says 35, that is not a gap — it is two of the
client's own documents disagreeing, and a funder's analyst will read both. On a
real project every one of the decisive findings was a contradiction of this kind,
and none of them came from the internet.

The report proposes; it never grades. A keyword near a number is not evidence, and
auto-grading from a match would manufacture exactly the false confidence this skill
exists to prevent. Read the quotes, then write the source into the spec yourself.

It will also miss things — proximity search cannot find a price quoted three
paragraphs from the word "price". The intake digest is still there; read it for
anything the model rests on.

## Stage 4 — Explore before researching

```bash
python scripts/explore.py spec.yaml --target net --out out/explore.json
python scripts/explore.py spec.yaml --scenarios
```

This is the step people skip, and skipping it wastes the research budget. Two
rankings come out and the second is the one to act on.

**Leverage** is how much each driver moves the target. Often several drivers tie
exactly, because driver models are chains of multiplication where every link has
the same leverage. The script says so when it happens. That is a fact about the
model, not a failure of the analysis, and it means arithmetic cannot tell you
where to look.

**Research priority** breaks the tie with evidence: leverage weighted by how weak
the backing is. A high-leverage number from a signed lease needs nothing; the same
leverage on "founder estimate" is where the risk lives. That list is the research
plan, and it is usually five items, not fifty.

The script also flags drivers that can flip a threshold — a small move that crosses
break-even matters more than a large one that changes nothing anyone decides on.

## Stage 5 — Research what matters

Only the top few. `references/evidence-and-research.md` has the method: ranges not
points, two independent sources, and an explicit check that the source's
population, period and unit actually match the use.

The failure mode to guard against is **benchmark laundering** — taking a real
statistic about a sector and quietly promoting it into a venture-specific
assumption. It is how AI-assisted models go wrong, because every step looks
defensible: the source is real, the number is real, the conclusion is fiction. A
sector average for CO₂ avoided per repair is not your CO₂ avoided per repair
unless your mix matches, and if it does not, say so in the spec where a reader
will see it.

Some numbers are not researchable. A grant "in application" is a conversation, not
a market fact; record `deal_stage: exploration` and keep it out of the base case
rather than sending an agent to find a source that does not exist.

Where the organisation has actuals — last year's costs, the pilot's real numbers —
those beat any research. Grade them A and anchor the first period to them.

## Stage 6 — Challenge it before a funder does

Offer this; do not spring it. Then do it properly, because a soft version is worse
than none — it inoculates the founder against the real thing.

```bash
python scripts/explore.py spec.yaml --scenarios --target net
```

The **evidenced downside** is built automatically (and appears in the report): every researched driver moved to
whichever end of its own range is worse, determined by testing rather than guessing
the direction. This is not pessimism, and it should be said that way — it is the
model priced at the other end of its own sources. On a real project it moved the
answer from +406k to -165k using nothing but numbers already in the client's folder.

Then attack it by hand, with `references/modelling-judgment.md` open. The stance
that finds things: **assume the author wanted this to work, and look for where that
wish is doing the arithmetic.**

- Take each of the top three drivers and argue the opposite case out loud. If the
  argument is easy to make, the number is not settled.
- Zero out each revenue line in turn. Whatever the venture cannot survive losing is
  what it actually is — which is often not what it calls itself.
- Check the unsecured money. Anything at `exploration` stage sitting in the base
  case is the defect a funder finds first.
- Reference-class it. What did comparable ventures actually achieve? A build far
  above every comparable owes an explanation, and "we will execute better" is not
  one.
- Ask what would have to be true. That converts "your model is wrong" into a
  question the founder can answer, which is the only version of this that helps.

Report what survives, not what you found. And if the honest answer is that the case
does not close, say it plainly and early — that is the cheap place to learn it, and
the founder will hear it better from you than from the person deciding.

## Stage 7 — Report and export

```bash
python scripts/report.py spec.yaml --out out/report.html --explore out/explore.json
python scripts/export_xlsx.py spec.yaml --out out/model.xlsx
```

The HTML is self-contained: the spec is compiled to JavaScript, so every number
recalculates in the browser as sliders move. No server, no key, works offline,
opens in ten years. `report.py` checks the compiled JavaScript reproduces the
Python numbers and refuses to pass silently if it does not — two engines are only
an asset if they agree.

The xlsx exists because the funder will ask for the Excel however good the HTML
is: assumptions in blue with grade and source beside them, calculated lines as
real formulas.

Both rebuild their values on first open, so open them once before forwarding.

## Stage 8 — Iterate

Everything is a re-render of the spec, so *"what if we only open three sites?"* is
a one-line change and an instant answer. Keep the spec under version control if you
can; the diff is the record of what changed and why.

## Reporting to a founder

Lead with what the model does not know. "Twelve assumptions, five are guesses, and
two of those five decide the answer" is more useful than a projection to the euro.
False precision invites a reviewer to test whether it is real.

And be careful with the honest result. Most first models of a social enterprise do
not close, and the tool will say so plainly. That is not a verdict on the venture;
it is the cheap place to find out. The useful next question is "what would have to
be true?", which the scenarios answer.

## References

| File | Read it when |
|---|---|
| `references/model-spec.md` | Writing or editing a spec (Stage 2) — full format, functions, worked patterns |
| `references/revenue-archetypes.md` | The venture is CE / social — gate fees, PaaS, repair, EPR, credits, blended grants, each with its failure mode |
| `references/evidence-and-research.md` | Grading assumptions and researching them (Stage 5), incl. laundering and deal staging |
| `references/modelling-judgment.md` | Challenging the model (Stage 6) — the checks no script can make — funnel logic, cost recovery, impact claims, what funders actually ask |

## Scripts

| Script | Does |
|---|---|
| `intake.py` | folder of anything → text digest + every number with context |
| `evidence.py` | for each driver: what in the folder supports it, and what contradicts it |
| `model.py` | load, validate, compute; blended-finance totals derived automatically |
| `explore.py` | leverage + research priority + scenarios incl. an auto-built evidenced downside; flags threshold flips |
| `report.py` | self-contained interactive HTML; verifies its own compiled JS |
| `export_xlsx.py` | funder-ready spreadsheet with live formulas, grades and sources |
