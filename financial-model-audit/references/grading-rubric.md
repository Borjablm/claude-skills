# Grading rubric

Grading answers one question: **if a reviewer challenges this number, what do we
say?** Not "is it right" — nobody knows, it is the future. The grade records the
quality of the answer to the challenge.

Grade the assumptions with leverage (Stage 4 tells you which). Grading everything
evenly is how an audit runs out of attention before it reaches the numbers that
matter.

## The grades

**A — primary evidence.** The organisation's own audited actuals, financial
statements, filings, signed contracts, or first-party research the team conducted
themselves (they called ten suppliers and recorded the quotes). The defining test:
the evidence is about *this* venture or *this* organisation, and it exists
independently of anyone's hope.

**B — credible secondary.** A real study, survey, industry dataset, regulator
publication, or a competitor's disclosed figures, where the population and the
period genuinely match this use. A market survey of mobile gamers, applied to a
mobile game, is B. The same survey applied to a console title is not — see
laundering below.

**C — unsourced or arbitrary.** A number someone chose. Includes anything labelled
"assumption", "estimate", "proxy", "TBC", and anything an AI produced without
citation. This is not an insult: most models are mostly C, and a C on a low-leverage
assumption is completely fine. A C on the number that decides the answer is the
finding.

**D — structurally suspect.** The number is not merely unsourced, it is wrong in
kind: a rate used as a count, a sector figure standing in for a company figure, a
statistic measuring one behaviour applied to a different behaviour, a value that
contradicts the organisation's own actuals. D means "do not fix the sourcing, fix
the reasoning".

**Partner-dependent — not a grade, a different track.** See below.

## Confidence

Grade is about evidence; confidence is about how much the evidence constrains the
answer. They come apart, and the pair is more informative than either alone.

A well-sourced number can still be low confidence (a real study, wide dispersion,
this venture could land anywhere in it). A C can be high confidence (a platform
commission of 30% is unsourced in the model but universally known). Record both:
`grade: B, confidence: low` says something specific and useful.

## The benchmark-laundering test

The failure mode this rubric exists to catch. It works like this: an agent finds a
real number, from a real source, broadly about the right sector, and then quietly
promotes it into a venture-specific assumption. Every step looks defensible in
isolation. The chain is fiction.

It is the characteristic way AI-assisted models go wrong, because the research
looks *better* than a guess — it has a citation — while being less honest, since a
guess at least announces itself.

Before any researched number enters the ledger, check three things match between
the source and the use:

- **Population** — the source measured *whom*? "69% of users on that platform have
  bought something" is about that platform's whole user base, not about the subset
  your campaign actually reaches, and not about a different platform.
- **Period** — when? A 2021 engagement figure describes a pandemic. A pre-launch
  price describes a different product.
- **Unit and behaviour** — the source measured *what action*? A study of people who
  say they would join a climate campaign is not a study of people who buy things.
  Using the first as a proxy for the second is the single most common laundering
  move, and it is invisible once the number is in a cell.

When the match is imperfect and you use it anyway — which is often legitimate,
because perfect matches rarely exist — the adaptation must be **visible**. Write it
in the source field: *"Yale study measures campaign-joining intent (26%); used here
as an upper bound on purchase propensity, which is a different behaviour; treat as
optimistic."* A visible adaptation is honest modelling. A silent one is laundering.

Grade a silently adapted figure D, not B, however good its source.

## Partner-dependent assumptions

Some numbers are not facts about the world; they are the state of a conversation. A
revenue line named after a counterparty ("national retailer, campaign development,
1.5M") cannot be researched, because the truth of it lives in a relationship, not a
dataset. Sending an agent to find a source for it produces theatre.

Track `deal_stage` instead:

| Stage | Meaning | Reasonable treatment |
|---|---|---|
| `exploration` | Conversations happening, nothing agreed | Excluded from base case, or heavily weighted down |
| `verbal` | Intent expressed, nothing written | Weighted down; present as upside |
| `LOI` | Written but non-binding | Base case with the downside modelled |
| `signed` | Contract exists | Grade A; it is an actual |

This is not pedantry, it is protection. Presenting an exploratory conversation as a
forecast, in a room that might contain the counterparty, is a specific and
avoidable embarrassment. Staging the number lets the model show ambition *and*
survive scrutiny — the partner sees an honest account of where things stand rather
than a promise they never made.

Concentration is worth flagging alongside: if a small number of named counterparties
carry most of year-one revenue, that is not an error, but it is the risk a reviewer
will find, and it is better raised by the model than by them.

## Actuals and internal grounding

Where the organisation has real data — an existing product's performance, last
year's costs, a prior grant's spend — that data outranks any research for the base
year. Anchor to it, grade it A, and check the projections against it.

A projection that contradicts the organisation's own actuals is a finding worth
raising directly: it usually means the model was built forward from ambition
rather than backward from evidence, and that is a conversation better had early.

## Recording it

```json
{
  "grade": "D",
  "confidence": "low",
  "source": "note in model reads 'based on ChatGPT analysis' — no citation",
  "researched": {
    "range": [2.80, 4.50],
    "sources": ["<url> — platform pricing page, Jul 2026",
                "<url> — 2025 industry survey, n=1,200, same genre"],
    "date": "2026-07-15",
    "applicability": "Both sources cover the same platform and item category; the
                      lower bound reflects regional pricing we do not target."
  }
}
```

The `applicability` field is where laundering gets caught, so write it even when it
is boring. Especially when it is boring — the interesting ones are the adaptations
you were tempted not to mention.
