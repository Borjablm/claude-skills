# Research protocol

For assumptions on the research-priority list from Stage 4. Two depths: **quick**
when you need a defensible range in minutes, **deep** when the number decides the
answer and will be challenged.

The output is always the same shape: a range, its sources, and an explicit note on
whether the sources actually apply.

## Quick mode

Minutes per assumption. Enough for a first pass, and enough to replace a guess with
something a reviewer can check.

1. **Frame the question so it has an answer.** Not "what do skins cost?" but "what
   is the typical price of a cosmetic item in this platform's marketplace, in the
   last 18 months, in the regions we target?" A vague question retrieves a vague
   number and you will not notice the mismatch later.
2. **Find two independent sources.** Two, because one is an anecdote. Independent,
   because two blogs citing the same report is one source wearing a hat.
3. **Produce low / base / high.** The spread between your sources *is* the range.
   If they agree suspiciously, suspect shared provenance.
4. **Write the applicability note.** One sentence on how well the source matches
   this use, including where it does not.
5. **Record** grade, confidence, range, sources, date.

## Deep mode

For the handful of numbers that carry the model. Slower, adversarial, and worth it
precisely where being wrong is expensive.

### 1. Source fan-out
Search several ways rather than several times. Different search angles surface
different source types, and one angle finds only what that angle can see:

- the primary actors (platform disclosures, company filings, annual reports)
- the measurers (industry surveys, academic studies, regulators, statistics offices)
- the practitioners (trade press, operator interviews, conference talks)
- the adjacent (a comparable market where the number is better documented)

### 2. Source qualification
Tier every candidate before extracting anything. Ask of each: who measured this,
when, on whom, with what incentive, and does the underlying data exist or is this
a citation of a citation? Aggregator sites that restate other people's numbers
without method are not sources; find what they cite, and if that cannot be found,
that itself is information about the number's reliability.

Vendor-published market sizes deserve particular suspicion: the incentive runs one
way, and the method is usually absent.

### 3. Extraction plan
Decide *which number comes from which source* before pulling any of them.
Otherwise the selection happens implicitly, and it selects for what confirms the
model. Write it down: "price from the platform's own pricing page; conversion rate
from the 2025 survey; nothing from the vendor report except context."

### 4. Adversarial cross-check
Now try to break your own result. The most useful framing is: *the model's author
wants this number to be high; assume that bias and attack it.*

- Does the population match? (the laundering test, `grading-rubric.md`)
- Does the period match, or has the market changed since?
- Does the unit match — is a rate being read as a count, a monthly figure as annual,
  a gross figure as net?
- Is this a survivor statistic? Public figures skew to successes; the ventures that
  failed did not publish their conversion rates.
- Is the source measuring stated intent rather than behaviour? Intent overstates.
- Would a hostile reviewer with a browser find a source that contradicts this in
  ten minutes? If so, find it now.

A value that fails cross-check goes back to fan-out or enters the ledger flagged,
with the failure recorded. Do not quietly widen the range to make an objection go
away — the objection is information.

### 5. Record with provenance
Sources with URLs and dates, the applicability note, and where the cross-check
pushed back. A range whose reasoning is legible can be argued with, which is the
point; a range that just appears cannot be defended by anyone but its author.

## What not to research

**Partner-dependent numbers.** A revenue line named after a counterparty is a deal.
Stage it (`grading-rubric.md`), do not search for it.

**Numbers the organisation already knows.** Internal actuals beat external research
for anything about the organisation itself. Ask before searching.

**Low-leverage assumptions.** If Stage 4 says it does not move the target, a
sourced range for it is effort spent where nobody was ever going to look.

**Numbers that are really decisions.** "What price should we charge?" is not a
research question, it is a strategy question that the model exists to inform. Model
it as a scenario variable, not as a fact to be discovered.

## When research comes back inconvenient

It usually will, at least once: the sourced range sits below the model's number and
the result stops working. That is the audit doing its job, and it is worth saying so
plainly rather than softening it.

Report it as what it is — the model's viability now depends on an assumption the
evidence does not support, and here are the three ways that could resolve (the
number is beatable for a reason the sources cannot see; the strategy changes; the
case does not close). The modeller decides. A researcher who quietly picks the top
of the range to keep the model alive has produced a worse artifact than the guess
they replaced.
