# Judgment checks

The scripts compute. These are the things that need someone to look at the model
and think. Ordered by how often they change the answer.

## Does the revenue line describe how money actually arrives?

The deepest error a model can make is arithmetically perfect. Read each formula
back as a sentence and check it against reality.

- **Everyone buys everything.** `items * price * customers` says every customer
  buys every item. If you mean an attach rate, model one — it is also researchable,
  where a catalogue-size multiplier is not.
- **The funnel has no leaks.** Aware → interested → tried → paid → repeated. If the
  build skips a stage, the missing conversion is implicitly 100%.
- **Rates multiplied into people.** `days * daily_users` is person-days, not
  persons. It counts the same person once per day and looks like ordinary
  multiplication.
- **Volunteers are free.** They are not. Cost them as `inkind` income and matching
  cost, or the model cannot answer what happens when you have to pay.
- **The channel exists.** Revenue that requires a council, a platform or a retailer
  to say yes is partner-dependent, not a market size.

## Do the costs move with the venture?

- **Fixed costs that should be variable.** Delivery, coordination, support and
  logistics scale with volume. A cost base flat across a 5x ramp is a choice — ask
  whether it was one.
- **Missing entirely.** Insurance, safeguarding, DBS checks, waste disposal of what
  you cannot sell, payment fees, bad debt, the finance and admin of running a
  regulated entity, the cost of raising the next grant.
- **Full cost recovery.** Overhead allocation is a live argument in this sector and
  a model that under-recovers is not being modest, it is under-pricing its grant
  applications and quietly subsidising restricted work with unrestricted money.
  If the overhead rate is a guess, say so — it usually is.
- **Percent-of-revenue cost stacks.** Convenient, and they produce a model that
  cannot lose money at any scale. That is an artifact, not a business. Check where
  the percentages came from.
- **Who does the work?** If throughput triples and headcount does not, someone is
  working for free in the spreadsheet.

## Does growth have a mechanism?

- **Curves without causes.** 2 → 4 → 7 → 10 sites is a hope with a pattern. What
  changes in year two to produce year two, and is that change costed?
- **Pilot economics at scale.** The pilot ran on the most committed people in the
  most receptive place. Throughput per site and donation per item both regress.
  Almost no first model includes this, and almost every operator confirms it.
- **Decay is missing.** Most models have growth multipliers and no decay. If the
  founder has written down risks anywhere — a deck, an application — those are the
  most persuasive downside scenario available, because they are their own words.

## Is the shape of the model honest?

- **Single-column futures.** One set of numbers presented as the plan. The absence
  of a downside is itself a finding.
- **The terminal year does the work.** If the case only closes in year four, and
  year four is the least evidenced, the model is an argument about the least
  knowable thing.
- **Reserves, not just net.** A venture can be profitable in year four and dead in
  year two. `cumulative_net` is the survival line.
- **Precision theatre.** `28,421.875` implies a precision nobody has and invites a
  reviewer to test it.
- **Annual periods hiding a cash gap.** Grants arrive late and in tranches. If
  timing is the risk, model quarters.

## Impact claims

This sector's models carry impact numbers, and they get less scrutiny than the
money right up until they get much more.

- **Attribution vs contribution.** Would it have happened anyway? A repair that
  would have happened at a commercial shop is not a repair you caused.
- **Impact per euro is a ratio of two uncertain numbers**, so it is more uncertain
  than either. Present it as a range or not at all.
- **Double counting.** If a carbon credit is sold, the tonne belongs to the buyer.
  Claiming it too is a real reputational risk.
- **Sector-average factors are not yours.** The most common laundering site in an
  impact model. State the adaptation.
- **Impact that scales linearly forever.** The easy beneficiaries come first.

## What a funder will actually ask

Worth having answers before the meeting, because these are predictable:

- What happens if the grant does not land?
- When do you stop needing us, and what has to be true for that?
- What is the cost per unit of outcome, and how does it compare to alternatives?
- Which single assumption, if wrong, breaks this?
- What is your evidence for the biggest number in the model?
- Who else is doing this, and what did it cost them?
- What does the money we give you actually buy that earned income cannot?

A model that answers these on its own page is doing its job. `explore.py` answers
the fourth and fifth mechanically; the rest are yours.

## Reference-class checking

The strongest single check, and the least used: what did comparable ventures
actually achieve? For social enterprises this is unusually easy, because peer
accounts are filed publicly and are audited, comparable and about real ventures
doing the real thing.

A bottom-up build that lands far above every comparable is not necessarily wrong,
but it owes an explanation, and "we will execute better" is not one. Where the gap
between the build and the reference class is large, that gap is the most
interesting number in the model — and it is the one a reviewer will find.

## Building from nothing

1. **Write the revenue sentence in words with the founder** before any number
   exists. If it cannot be written, the model is premature and that is the finding.
2. **Name the drivers in that sentence.** They are the skeleton.
3. **Every input a named driver** — never a number typed inside a formula, because
   unsourceable numbers cannot be graded and invisible ones cannot be tested.
4. **Leave it all ungraded** and let it look like guesses, because it is.
5. **Run `explore.py` before researching anything.** Five numbers, not fifty.
6. **Anchor period one to actuals** if any exist.

The order front-loads the free steps. Structure costs nothing, research is
expensive, and sensitivity is what tells you which expensive thing to buy.
