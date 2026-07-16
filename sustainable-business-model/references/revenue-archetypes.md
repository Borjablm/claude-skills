# Revenue archetypes for circular and social ventures

Each archetype comes with the drivers it actually needs and the way it usually
goes wrong. The failure modes matter more than the templates: they are what a
funder's analyst finds, and they are largely predictable by archetype.

A note that applies to all of them: none of these are pure. Most real ventures
run two or three at once, plus grants, and the interesting question is usually
which one is load-bearing and whether anyone has admitted it.

---

## 1. Gate fee / waste acceptance

You are paid to accept material. Revenue = tonnes × fee per tonne.

```yaml
drivers:
  tonnes_accepted: {label: Tonnes accepted, values: [12000, 18000, 24000], unit: mass}
  gate_fee:        {label: Gate fee per tonne, value: 45, unit: currency}
lines:
  gate_income: {formula: tonnes_accepted * gate_fee, category: earned}
```

**How it fails.** The gate fee is set by what landfill and incineration cost, and
those are policy, not market — a landfill tax change moves your entire revenue
line and you do not control it. Model the fee as policy-dependent and scenario it
against tax changes, because a funder in this sector will ask.

Capacity is a hard ceiling that models routinely exceed: check `tonnes_accepted`
against permitted capacity and against actual feedstock in the catchment. Tonnes
you can process is not tonnes anyone will bring you. And contamination rates
decide costs — inbound material is dirtier than the plan assumes, every time.

---

## 2. Material recovery / secondary commodity sales

You sell what you recover. Revenue = tonnes × recovery rate × price per tonne.

```yaml
drivers:
  recovery_rate:   {label: Recovery rate, value: 0.62, unit: percent}
  material_price:  {label: Price per tonne recovered, value: 120, unit: currency}
```

**How it fails.** Commodity prices are volatile and correlated with the virgin
material you are displacing — a model with a flat price line is not a forecast, it
is a wish. Scenario the price hard, both ways.

Recovery rate is usually a lab or pilot figure applied to real mixed feedstock,
which is a classic laundering move: the number is real, the population is not
yours. And revenue per tonne is not margin per tonne — sorting, transport and
residue disposal frequently exceed the sale price for low-value fractions, so a
venture can be profitable per tonne on paper and lose money on every additional
tonne. Model the residue: what you cannot sell, you pay to dispose of.

---

## 3. Product-as-a-service / leasing

Customers pay for use, not ownership. Revenue = active units × fee per period.

```yaml
drivers:
  new_customers:   {label: New customers per year, values: [40, 90, 150]}
  churn:           {label: Annual churn, value: 0.18, unit: percent}
  monthly_fee:     {label: Fee per month, value: 25, unit: currency}
lines:
  active: {formula: prev(active) * (1 - churn) + new_customers, category: impact}
  psaas_income: {formula: active * monthly_fee * 12, category: earned}
```

**How it fails.** This is the archetype that eats cash and the models rarely show
it: you buy the asset now and are paid over years, so the faster you grow the worse
your cash position. `cumulative_net` is the line that matters, not `net`. A PaaS
model that never shows reserves is hiding its central risk.

Also: the asset comes back, and its condition decides whether the economics work.
Refurbishment cost per return cycle and how many cycles an asset survives are
drivers, not footnotes — and churn without a returns process is just theft with a
contract.

---

## 4. Repair, reuse and resale

Revenue = items processed × price or donation per item.

```yaml
drivers:
  items_processed:   {label: Items repaired per year}
  avg_price:         {label: Average price or donation per item, unit: currency}
  parts_cost:        {label: Parts per item, unit: currency}
  volunteer_hours:   {label: Volunteer hours per item, unit: duration}
```

**How it fails.** Volunteer labour is the whole economics and it is usually costed
at zero, which makes the model look viable and makes it impossible to scale — the
first paid coordinator changes everything. Value volunteer time as `inkind` income
with a matching cost, so the model shows what the venture actually consumes.
Otherwise you cannot answer "what happens when we have to pay for this?", which is
the question.

Donation-based pricing is not price: it is framing-dependent and regresses as you
scale beyond the founding community. Throughput per site regresses too — the pilot
ran on your most committed people.

---

## 5. EPR fees / producer compliance

Producers pay you to meet their obligations. Revenue = tonnes or units × fee.

**How it fails.** The revenue exists because of a regulation, so the model's real
driver is regulatory scope and enforcement, neither of which you control. Model the
scheme's phase-in explicitly, and treat "the regulation will extend to X" as a
scenario, not a base case. Fees are usually set by a scheme administrator or
negotiated collectively, so your pricing power may be zero — if so, say it, because
a model implying pricing power you do not have is the thing that unravels in
diligence.

---

## 6. Carbon and biodiversity credits

Revenue = tonnes abated × price per credit.

**How it fails.** The gap between *tonnes abated* and *credits issued* is the whole
business, and models skip it: additionality, baselines, permanence, buffer pools,
verification cost and issuance lag each remove real revenue. Model verified,
issued, sold credits with the lag, not physics.

Price ranges are enormous and quality-dependent; a single price is meaningless. And
verification and monitoring are ongoing costs, not a one-off. Be careful claiming a
tonne twice — if the credit is sold, the impact belongs to the buyer, and stating
both as your impact is a real reputational risk, not a modelling nicety.

---

## 7. Blended grant funding

Not a revenue model, but present in almost every model here, and it deserves the
same rigour.

```yaml
drivers:
  grant_core: {label: Core grant, values: [90000, 70000, 40000, 0], grade: A,
               deal_stage: signed, source: signed 3-year agreement, tapering by design}
  grant_new:  {label: New grant (in application), values: [0, 0, 30000, 30000],
               grade: partner, deal_stage: exploration}
lines:
  grants: {formula: grant_core + grant_new, category: grant, restricted: true}
```

**How it fails.** Unsecured grants sit in the base case at full value, which is the
single most common defect in this sector's models. Stage them: a grant in
application is a conversation. Put it in an upside scenario and let the base case
survive without it.

Restricted grants cannot cover the costs the model uses them for, and a model that
nets everything together hides that. And the taper is the plan: most core grants
decline by design, so the model's real question is whether earned income rises
faster than the grant falls. That is what `grant_dependency` and the grant-free
threshold are for.

Watch the timing too. Grants arrive in tranches against milestones, often late.
Annual periods hide a cash gap that is fatal in month seven — if that risk is
live, model in quarters.

---

## Choosing and combining

Ask which archetype carries the case, then check the model actually reflects it.
The recurring pattern in this sector is a venture that describes itself as one
thing (a repair network) and is financially another (a grant-funded programme with
a repair shopfront). That is not a criticism — it is a fact worth stating in the
model rather than discovering in diligence, because a funder who finds it
themselves concludes you did not know.

The test: zero out each revenue line in turn. Whatever the venture cannot survive
losing is what it actually is.
