---
name: waste-audit-analysis
description: "Desk analysis of a waste characterisation (waste composition) study: turns field tally sheets of sorted household and business waste into generation rates (kg per household and per person per day), composition by weight, income-group splits and a scale-up to tonnes per day, with a data-quality log and every adjustment written down. Use for 'analyse our waste audit data', 'waste characterization study results', 'how much waste does this town generate', 'what share is plastic', sizing a sorting facility or collection round from audit data, or checking someone else's waste composition numbers."
version: 0.1.0
---

# Waste audit analysis

For practitioners who have just run (or inherited) a waste characterisation study: households and businesses sampled for some days, waste sorted by hand into categories, weights typed into a spreadsheet. This skill does the desk part that follows. It does not design the sampling or do the sorting.

It was built from a test on a real 2019 audit in two coastal sub-districts of East Java, Indonesia (288 households, 21 businesses and institutions, 23 categories). A blind AI run matched the original workbook to the decimal in under six minutes. The same test showed where the numbers go wrong, which is what the steps below guard against: mixed units between sheets, totals mistaken for daily weights, two different per-capita averages, organics missed by the sample, and scale-ups that need data the audit never collected. Write-up: [azvai.com](https://azvai.com/en/ai-waste-composition-analysis/).

## Ground rules

- **People first.** Tally sheets usually carry names, phone numbers, addresses and incomes. Strip names, phone numbers and street addresses before any of it goes to a model. Keep village or ward. Replace shop and stall names (often the owner's name) with a type and number.
- **Never adjust silently.** If the measured rate looks too low or too high, say so and stop. An adjustment is allowed only as an entry in `adjustments` with a reason and a source, and the report shows measured and adjusted figures side by side.
- **Never invent scale-up inputs.** A municipal total needs counts of each non-household source (shops, stalls, schools, offices, health posts). If the audit didn't collect them, the total stops at households and the report lists what to get.
- **Every number in the report comes from `scripts/waste_audit.py` output**, not from the model's arithmetic.

## Step 1. Inventory (read every header cell before computing anything)

Open each sheet and record, per sheet:
- the unit (kg or g; it often differs between sheets of the same study),
- what one weight means (total over the sampling period, or a daily figure) and the number of days in it. Studies that follow the Indonesian method SNI 19-3964-1994 sample 8 consecutive days, and some drop day 1 because it holds waste stored before the study, so "7" can be normal. Check the study's own method note rather than assuming,
- household size column, income column and any income-band definitions in the study's own documents,
- which rows are sample data and which are summary rows, notes or blank formula rows,
- the category list and how it maps to material groups.

Check the study's terms of reference and any delivered report for definitions (income bands, days dropped, categories). Read them as inputs, not as results to copy. If none exist, the header cells and note rows are the only method record: say so in the assumptions register.

Map every category to one material group, including ones that turn out empty (animal manure goes with organic). Weights that aren't numbers, such as a decimal comma ("0,658"), are excluded and flagged with their effect; get them corrected at source rather than guessing.

## Step 2. Confirm four things with the user before running

Ask in one message, with what you found:
1. Units per sheet.
2. Period totals or daily weights, and how many days.
3. Income band definitions (use the study's own; invent none).
4. Population figures to scale up with, their year and source, and whether sampled villages represent the whole area.

If the user can't confirm (2), run both readings: the sensitivity table shows the factor, and the report says which was used and why.

If no user can be reached, write the four questions into `questions.md` with the answer you infer from the files, the evidence and your confidence, and carry on with those answers. What the documents say beats what looks plausible. If a header says the weights are 7-day totals and the result looks low, the low result is the finding. Never switch the unit or period reading to make a number look normal; that is the silent adjustment this skill exists to prevent.

## Step 3. Build the config and run

1. Put each area's sheet in a tidy CSV: one row per sampled household or unit, columns for id, type (household or source type), people, income, one column per category. Leading note rows starting with `#` are fine; keep them, they carry header units.
2. Copy `templates/config.example.json`, fill it in. File paths in the config are relative to the config file's folder. Leave `income_bands` empty and `benchmark_kg_cap_day` null until you have the study's definitions and a cited reference.
3. `python scripts/waste_audit.py config.json --checks-only` and read every flag with the user.
4. `python scripts/waste_audit.py config.json --out results/`

Outputs: `generation.csv`, `composition_category.csv`, `composition_group.csv`, `flows_household_t_day.csv` (what a sorting facility would receive, by material group), `income.csv`, `sensitivity.csv`, `data_issues.csv` (each problem with its measured effect on kg/cap/day where one can be computed), `adjustments.csv`, `summary.md`. If a number you need isn't in these outputs, add it to the script rather than computing it by hand.

## Step 4. Read the flags (see `references/data-quality-checklist.md`)

The checks are the value of this skill. In the Indonesian test the ones that mattered were:
- **Units** differed between the two sub-districts (kg and g).
- **Per-capita average**: the workbook's own cells used total weight over total people (0.100 and 0.144 kg/cap/day); the delivered report said 0.11 and 0.15, and the files don't show how those were derived. The mean of each household's per-person rate gives 0.113 and 0.156, so there the averaging method alone moved the result by 8 to 13% (in a synthetic test set it moved it by 2%). Report both and say which you use (ratio of totals is the one that scales up correctly to population).
- **Under-capture**: 0.10 to 0.14 kg/cap/day is far below typical figures, mostly because food scraps go to animals, compost or fires before collection. The original team later added an estimate for missed organics. That is a legitimate judgement call, and it belongs in `adjustments` with its reason, not typed into a cell.
- **Non-household scale-up** needed outside counts (business registers, school lists) and unit rates the audit didn't have.

## Step 5. Benchmark

Compare per-capita generation with a published reference for a similar place (national waste statistics, the relevant standard, peer-reviewed audits of similar towns). Put the range and its source in `benchmark_kg_cap_day` and `benchmark_source`. Cite the primary source, not a secondary paper quoting it. A rate far below the reference is a finding to explain, not a number to fix.

## Step 6. Report

Use `templates/report-outline.md`. It leads with the household generation table (measured, adjustment, adjusted), composition by group, what a sorting facility would receive in t/day, the data-quality log and the assumptions register. Density only if container volumes and matching weights exist.

## What this skill does not do

- Decide the adjustment for missed organics. It makes the gap visible; the field team decides.
- Replace the fieldwork. Sample design, the sorting itself, and the conversations that explain odd numbers (why no manure, why so little food waste) stay with people.
- Seasonality. One sampling week describes one season; repeat it before sizing anything that depends on peaks.
