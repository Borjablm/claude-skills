# The model spec

One YAML file. It is the model, the ledger and the deliverable at once — the
founder can read it, git can diff it, and the scripts can run it.

```yaml
meta:
  name: Repair café network
  currency: EUR
  periods: {count: 4, unit: year, start: 2027}
  question: When do we stop needing grants, and what does that require?
  language: en
```

`question` is worth writing. A model built to answer a stated question stays
honest; one built to produce a number drifts toward the number someone wanted.

## Drivers — the assumptions

Everything the model rests on. One entry each, with what stands behind it.

```yaml
drivers:
  sites:
    label: Repair cafés open          # what a human calls it
    values: [2, 4, 7, 10]             # one per period, or `value:` for a constant
    unit: count                       # count | currency | percent | duration | mass | energy
    grade: C                          # A | B | C | D | partner
    confidence: low                   # high | medium | low
    source: founder plan — one site per quarter from Y2
    note: Not a market fact. This is the plan, so it is a decision, not a discovery.

  co2_per_repair_kg:
    label: CO2e avoided per repair
    value: 24
    unit: mass
    grade: B
    source: {note: "EU JRC, small appliance lifetime extension", url: "https://...", date: "2024"}
    researched:
      range: [18, 31]                 # explore.py tests across this, not +/-20%
      sources: ["...", "..."]
      date: "2026-07"
      applicability: >
        Sector average across appliance types; our mix skews to small electricals,
        which sit at the lower end. Treat 24 as optimistic.

  grant_new:
    label: New grant (in application)
    values: [0, 0, 30000, 30000]
    grade: partner
    deal_stage: exploration           # exploration | verbal | LOI | signed
    source: municipal fund, conversation only
```

Fields: `label`, `values`/`value`, `unit`, `grade`, `confidence`, `source`,
`researched`, `deal_stage`, `note`. Only `values`/`value` is required — but a
driver with no grade and no source will be reported as a guess, which is usually
the truth and always worth seeing.

`researched.range` matters more than it looks: `explore.py` tests a driver across
its evidenced range rather than an arbitrary percentage, so the sensitivity
reflects what the number could actually be.

`applicability` is where laundering gets caught. Write it even when it is boring —
especially then, because the interesting ones are the adaptations you were tempted
not to mention.

## Lines — what happens each period

```yaml
lines:
  repairs:
    label: Repairs completed
    formula: sites * repairs_per_site_week * weeks_open
    category: impact
    unit: count

  donation_income:
    label: Repair donations
    formula: repairs * avg_donation
    category: earned

  grants:
    label: Grants
    formula: grant_core + grant_new
    category: grant
    restricted: true

  workshop_income:
    label: Paid workshops
    values: [4000, 9000, 16000, 22000]   # entered directly — a plan, not a calculation
    category: earned
```

**Category is not decoration.** It is what lets the model answer this sector's
actual question without anyone wiring it up:

| category | meaning |
|---|---|
| `earned` | trading income — what you sell |
| `grant` | grants and donations (add `restricted: true` if it cannot be spent freely) |
| `investment` | loans or equity in |
| `inkind` | donated goods, space, volunteer time given a value |
| `cost` | anything you spend |
| `impact` | outcomes — repairs, tonnes, beneficiaries. Not money |

## Derived automatically

Available in any formula or threshold without defining them. Define one yourself
and yours wins.

`total_earned` · `total_grant` · `total_investment` · `total_inkind` ·
`total_income` · `total_costs` · `net` · `net_excl_grants` · `grant_dependency` ·
`earned_ratio` · `cumulative_net`

`cumulative_net` is reserves — the line that tells you whether the plan survives
the journey, not just the destination.

## Outputs — the ratios someone will ask for

```yaml
outputs:
  cost_per_repair:
    label: Full cost per repair
    formula: total_costs / repairs
    unit: currency
  cost_per_tonne_co2:
    label: Net cost per tonne CO2e avoided
    formula: (total_costs - total_earned) / co2_avoided
    unit: currency
    note: The number a climate funder asks for. Negative means it pays for itself.
```

## Thresholds — does it work?

```yaml
thresholds:
  - name: Grant-free operation
    test: total_earned >= total_costs
    meaning: Earned income covers full costs. The point of the whole exercise.
  - name: Reserves not negative
    test: cumulative_net >= 0
    meaning: The network never runs out of money on the way.
```

Reported per period, and the report distinguishes *reached* from *held*. A
threshold that holds in year one and breaks in year four reads as `BREACH`, not as
met — that pattern is the one founders discover too late.

## Scenarios

```yaml
scenarios:
  no_new_grant:
    why: The municipal fund is a conversation, not a commitment.
    overrides: {grant_new: 0}
  pilot_regression:
    why: Throughput and donations regress as the network scales past the founding site.
    overrides:
      repairs_per_site_week: [10, 10, 10, 10]
      avg_donation: [7.5, 7, 6.5, 6.5]
```

`why` is not optional in spirit. A scenario without a reason is a number; with one
it is an argument, and arguments are what get discussed in the room.

## Expressions

Arithmetic (`+ - * / ** %`), comparisons, `and/or/not`, and
`a if cond else b`. Names refer to drivers, lines, outputs, or derived values.
Everything is a vector over periods; constants broadcast.

| function | does |
|---|---|
| `prev(x)` | previous period, 0 at the start — carry-overs, balances |
| `cumul(x)` | running total — reserves, cumulative impact |
| `total(x)` | sum across all periods (broadcast) |
| `first(x)` `last(x)` `peak(x)` | one period, broadcast |
| `npv(rate, x)` `irr(x)` | discounting; `irr` returns 0 when undefined |
| `min` `max` `abs` `round` `clamp(x, lo, hi)` | as expected |
| `where(cond, a, b)` | elementwise choice |

A spec is data, not a program: only these are allowed, so a spec can never execute
arbitrary code. If a model needs loops, it has outgrown this format — and probably
its audience.

## Conventions worth keeping

**One driver, one meaning.** If a number is used for two things, split it. Fused
drivers cannot be sourced or sensitivity-tested.

**Catalogue size is not quantity sold.** `items * price * customers` says every
customer buys every item. If you mean an attach rate, model an attach rate.

**Rates and durations do not multiply into people.** `days * daily_users` counts
person-days, not persons. It inflates everything downstream and looks like ordinary
multiplication.

**Put the plan in the spec, not in your head.** A `note` explaining that a driver
is a decision rather than a discovery is worth more later than the number itself.
