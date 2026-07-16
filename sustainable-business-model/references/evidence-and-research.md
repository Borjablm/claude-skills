# Evidence and research

Grading answers one question: **if a funder challenges this number, what do we
say?** Not "is it right" — nobody knows, it is the future. The grade records the
quality of the answer to the challenge.

Grade the drivers `explore.py` says carry the result. Grading everything evenly is
how the work runs out of attention before it reaches the numbers that matter.

## The grades

**A — primary.** Your own actuals, a signed agreement, an invoice, first-party
research you did yourself. The test: the evidence is about *this* venture, and it
exists independently of anyone's hope.

**B — credible secondary.** A real study, a sector benchmark, a regulator's
publication — where the population and period genuinely match this use.

**C — unsourced.** A number someone chose. This is not an insult: most first models
are mostly C, and a C on a driver that barely moves the result is completely fine.
A C on the number that decides the answer is the finding.

**D — wrong in kind.** Not merely unsourced: a rate used as a count, a sector
figure standing in for yours, a statistic measuring one behaviour applied to
another. D means fix the reasoning, not the sourcing.

**partner — not a grade, a different track.** A number that depends on a named
counterparty. See below.

Grade and confidence come apart, and the pair says more than either. A real study
with wide dispersion is `grade: B, confidence: low`. A universally-known platform
fee with no citation is `grade: C, confidence: high`. Record both.

## Benchmark laundering — the thing to guard against

Take a real statistic about a sector, quietly promote it into a venture-specific
assumption. Every step looks defensible: the source is real, the number is real,
the conclusion is fiction.

It is the characteristic way AI-assisted models go wrong, because the research
looks *better* than a guess — it has a citation — while being less honest, since a
guess at least announces itself.

Before a number enters the spec, check three things match between source and use:

- **Population.** Measured on whom? A study of urban repair cafés in the
  Netherlands is not a rural Spanish network. A sector-average CO₂ saving across
  all appliance types is not yours if you only take small electricals.
- **Period.** When? A 2021 engagement figure describes a pandemic. Energy prices
  from 2022 describe a shock.
- **Unit and behaviour.** What action was measured? People who say they would
  repair rather than replace are not people who did. Stated intent overstates
  behaviour, reliably.

When the match is imperfect and you use it anyway — which is often legitimate,
because perfect matches rarely exist — the adaptation must be **visible**:

```yaml
researched:
  range: [18, 31]
  applicability: >
    Sector average across appliance types; our mix skews to small electricals which
    sit at the lower end. 24 is optimistic for us. Kept pending our own sample.
```

A visible adaptation is honest modelling. A silent one is laundering. Grade a
silently adapted figure D, however good its source.

## Numbers that are not researchable

**Partner-dependent.** A grant in application, a contract under discussion, an
offtake agreement being negotiated. The truth lives in a relationship, not a
dataset, and sending an agent to find a source produces theatre.

| stage | treatment |
|---|---|
| `exploration` | out of the base case, or heavily weighted down |
| `verbal` | upside scenario; base case survives without it |
| `LOI` | base case, with the downside modelled |
| `signed` | grade A — it is an actual |

This protects the founder. A model that shows an unsecured grant as revenue, to a
funder who knows that fund, is a specific and avoidable embarrassment.

**Decisions dressed as facts.** "How many sites do we open?" is a plan, not a
discovery. Model it as a scenario variable and label it as a decision in the
`note`, so nobody researches it and nobody mistakes it for evidence.

**Things the organisation already knows.** Ask before searching. Internal actuals
beat external research for anything about the organisation itself, every time.

**Low-leverage drivers.** If `explore.py` says it does not move the target, a
sourced range for it is effort spent where nobody will ever look.

## How to research one assumption

**Quick** — minutes. Enough to replace a guess with something checkable.

1. **Frame it so it has an answer.** Not "what do repairs cost?" but "what is the
   average parts cost for a small-appliance repair in a community setting in
   Western Europe, last three years?" A vague question retrieves a vague number and
   the mismatch goes unnoticed.
2. **Two independent sources.** One is an anecdote. Two blogs citing the same
   report is one source wearing a hat.
3. **Produce low / base / high.** The spread between sources *is* the range. If
   they agree suspiciously, suspect shared provenance.
4. **Write the applicability note**, including where it does not fit.
5. **Record** grade, confidence, `researched.range`, sources, date.

**Deep** — for the few numbers that carry the model.

- **Fan out by source type**, not by rephrasing: the actors (operators,
  companies), the measurers (studies, regulators, statistics offices), the
  practitioners (trade press, interviews), and the adjacent (a comparable sector
  where the number is documented better).
- **Qualify before extracting.** Who measured, when, on whom, with what incentive,
  and does the underlying data exist or is this a citation of a citation?
  Aggregator sites restating other people's numbers are not sources; find what they
  cite. Vendor-published market sizes deserve particular suspicion — the incentive
  runs one way and the method is usually absent.
- **Decide which number comes from which source before pulling any**, or the
  selection happens implicitly and selects for what flatters the model.
- **Then attack your own result.** Assume the author wants this number to be
  favourable. Does the population match? Has the market moved? Is this a survivor
  statistic — the failed ventures did not publish their conversion rates? Would a
  hostile reviewer with a browser contradict this in ten minutes? If so, find it
  now.

A value that fails the attack goes back to fan-out, or enters flagged, with the
failure recorded. Do not widen a range to make an objection disappear; the
objection is information.

## Sources worth knowing in this sector

Not a substitute for searching, but a reasonable starting order: national
statistics offices and Eurostat for material flows and waste; the EU JRC and EEA
for lifecycle and environmental factors; sector bodies (RREUSE, Zero Waste Europe,
Ellen MacArthur Foundation) for operating benchmarks; charity and CIC regulators
for peer financials, which are public and comparable and underused; municipal
tender documents for real gate fees and contract values; and your own peers, who
will usually tell you if asked.

Peer accounts deserve a special mention: for a social enterprise, another
organisation's filed accounts are often a better benchmark than any study, because
they are audited, comparable, and about a real venture doing the real thing.

## When research comes back inconvenient

It usually will. The sourced range lands below the model's number and the case
stops closing.

That is the work succeeding, and it should be said plainly. Report it as what it
is — the venture's viability rests on an assumption the evidence does not support,
and here are the ways that resolves: the number is beatable for a reason the
sources cannot see (say why), the plan changes, or the case does not close on this
design. The founder decides.

A researcher who quietly picks the top of the range to keep the model alive has
produced something worse than the guess they replaced, because now it has a
citation.
