# [Study name]: waste characterisation results

## Summary (half a page)
- Household generation, measured: [x] kg per person per day ([CI]), [y] kg per household per day.
- Adjustment, if any: [+z] kg per person per day for [reason], source [source]. Adjusted: [x+z].
- Composition: organic [a]%, plastic [b]%, paper [c]%, other [d]%.
- What a sorting facility would receive: [t] t/day of recyclables, of which [..] plastic.
- The two or three data problems that most change these numbers.

## Method
Sampling (dates, days, households and units per area, how chosen), sorting categories, units, days in the totals, per-capita method (ratio of totals; mean of ratios shown for comparison), population source and year.

## Generation
Table from `generation.csv`. Measured and adjusted side by side. Non-household rates per unit type. Municipal total only if unit counts exist.

## Composition
By material group and by category (`composition_group.csv`, `composition_category.csv`), households and non-household separately.

## By income group
Bands as defined by the study (`income.csv`), number of households in each, rank correlation.

## Density
Measured value, or "not measured" and what is needed.

## Data-quality log
Every row of `data_issues.csv`, with what was done and how much it changes the result (from `sensitivity.csv`).

## Assumptions register
Each assumption, its source, and who confirmed it.
