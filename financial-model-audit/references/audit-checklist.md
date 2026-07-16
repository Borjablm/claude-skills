# Judgment checks

`audit.py` finds defects that are mechanical. These are the ones that need someone
who has built models to look at the thing and think. Work through them after
reading the script's findings — they are ordered by how often they change the
answer.

## Does the driver logic describe the business?

The deepest error a model can make is arithmetically perfect. Read the revenue
build as a sentence and ask whether it is how the money actually arrives.

- **Every buyer buys everything.** `players x price x items` says each converted
  player purchases all thirty items. Almost never true, and it inflates by ~30x
  while looking like a normal multiplication. The fix is a purchases-per-buyer
  assumption, which also makes the number researchable.
- **The funnel has no leaks.** Reach → interest → trial → purchase → repeat: if the
  build skips stages, the missing conversion is implicitly 100%.
- **Reach counted repeatedly.** See stock-times-flow in the script findings. Any
  time a duration multiplies a per-period population, ask whether those are new
  people each period or the same ones returning.
- **The channel exists.** A model can assume distribution that nobody has agreed to
  provide. If a revenue line requires a platform to say yes, that is a
  partner-dependent assumption, not a market size.

## Do the costs move with the business?

- **Fixed costs that should be variable.** Support, delivery, fulfilment, moderation
  usually scale with volume. A cost base flat across a 10x revenue ramp is a
  choice; ask if it was one.
- **Costs missing entirely.** Payment processing, refunds and chargebacks, platform
  fees, tax, currency conversion, the finance and admin overhead of running the
  thing, the cost of the partnerships the revenue depends on.
- **The team that delivers this.** If revenue triples and headcount does not, who
  does the work?
- **Percent-of-revenue costs.** Convenient and often fine, but check the percentage
  came from somewhere. A cost stack expressed entirely as percentages of revenue
  produces a model that cannot lose money, which is a modelling artifact, not a
  business.

## Does growth have a mechanism?

- **Curves without causes.** 5% → 10% → 15% market share is a hope with a pattern.
  Ask what changes in year two to produce year two. If the answer is "more
  marketing", is the marketing cost in the model?
- **Year one is a pilot.** Small numbers in Y1 often reflect a deliberately small
  test. Then Y2 assumes the pilot's conversion rate at 50x the volume. Pilots are
  run on the most receptive audience available; the rate falls as it scales.
- **Decay is missing.** Most models have growth multipliers and no decay. If the
  team wrote down decay factors somewhere (retention collapse, campaign windows,
  seasonality), those belong in the downside scenario — they are the client's own
  words and they are the most persuasive scenario inputs available.

## Is the shape of the model honest?

- **Single-column futures.** One set of numbers presented as the plan. The absence
  of a downside is itself a finding.
- **Precision theatre.** `28,421.875` implies a precision nobody has. Rounding is
  not cosmetic; false precision invites a reviewer to test whether it is real, and
  it will not be.
- **Concentration.** A large share of revenue from one or two named counterparties.
  Not an error — a risk the model should raise before a reviewer does.
- **The terminal year does the work.** If the case only closes in Y3, and Y3 is the
  least evidenced year, the model is an argument about the least knowable thing.
- **Circular optimism.** Revenue funds the marketing that drives the revenue. Check
  the loop closes at plausible values.

## Cross-checks worth running

- **Reference class.** What did comparable ventures actually achieve? A bottom-up
  build that lands 10x above every comparable is not necessarily wrong, but it owes
  an explanation, and "we will execute better" is not one. Where the disagreement
  between a bottom-up build and its reference class is large, that gap is the most
  interesting number in the model.
- **Top-down sanity.** Implied market share, implied share of a platform's total
  spend, implied share of a customer's wallet. Models rarely state these, and they
  are frequently absurd once stated.
- **Per-unit realism.** Reduce the model to revenue per customer per year and ask
  whether a real person would pay that.
- **Against actuals.** If the organisation has real data, the model's base year
  should reconcile to it. Where it does not, that is where to start the
  conversation.

## Building a model from drivers

When there is no spreadsheet yet — a described venture, an application form, a
driver map — build in this order:

1. **Write the revenue sentence in words first**, with the client. "We earn X each
   time a Y does Z, and Y does Z N times a year." If that sentence cannot be
   written, the model is premature and the honest deliverable is that finding.
2. **Name the drivers in that sentence.** They are the model's skeleton, and they
   are what a reviewer will interrogate.
3. **Build the arithmetic with every input as a labelled, referenced cell** — never
   a number typed inside a formula. Unsourceable numbers cannot be graded and
   invisible numbers cannot be sensitivity-tested.
4. **Leave every assumption unsourced and say so.** A fresh model should be visibly
   all-C. Grey rows are honest; they show exactly how far the work has got.
5. **Run sensitivity before researching anything.** You will research five numbers
   instead of fifty, and you will pick the right five.
6. **Model the base year off actuals** if any exist.

The order matters because it front-loads the cheap steps. Structure is free,
research is expensive, and sensitivity is what tells you which expensive thing to
buy.

## Reading a model someone else submitted

Evaluating rather than building — a grant application, an investment proposal, a
competitor's case. The checks above apply, plus:

- **Score the evidence, not the ambition.** A modest venture with sourced numbers is
  a better bet than a spectacular one with none, and the model can only tell you
  about the second thing.
- **Unstated is not zero.** A missing cost is a question, not a deduction. Ask.
- **Absence of a digital footprint is not absence of a business.** Not everything
  verifiable is true and not everything true is verifiable. A community organisation
  with no web presence may be more real than a startup with a landing page.
- **Comparability requires a standard.** Models built differently cannot be ranked
  against each other honestly. Normalise structure first — same driver schema, same
  grading rubric — or the ranking measures modelling style rather than venture
  quality.
- **Rank and flag; do not reject.** The output is evidence for a human decision. A
  model that scores badly may describe a venture worth backing, and the person
  reading it can tell the difference in ways this process cannot.
