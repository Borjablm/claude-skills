# Data-quality checklist for waste audit tally sheets

Each item says what to look for, why it matters and what to do. The script flags the ones marked (auto); the rest need a person to read the sheet.

| # | Check | Why it matters | What to do |
|---|---|---|---|
| 1 | Unit per sheet (auto, via magnitude) | Sheets of one study can mix kg and g; a 1000x error looks plausible in a percentage table | Read header cells; set `unit` per area; the script flags a median household outside 0.05-30 kg/day |
| 2 | Period totals or daily weights | A 7-day total read as daily inflates everything 7x | Read headers ("SUM", "per day", "days surveyed"); sensitivity table shows both |
| 3 | Days in the totals (auto) | Day 1 often holds waste stored before the study and is dropped | Confirm which days; record it |
| 4 | Two per-capita averages (auto) | Mean of household ratios and ratio of totals differ when household sizes vary (by 8 and 13% in the Indonesian test, 2% in the synthetic one) | Report both; scale up with the ratio of totals |
| 5 | Household size typed as a decimal (auto) | A mean typed in for a missing value | Ask; exclude or keep, but log it |
| 6 | Non-numeric weights (auto) | Decimal commas, text like "n/a", shifted columns | Fix at source with the field team; never guess |
| 7 | Duplicate rows (auto) | Copy-paste in data entry inflates totals | Check against the paper tally sheets |
| 8 | Outliers per person (auto) | One mistyped weight can move a category share | Keep, report the sensitivity without them, check the paper sheet |
| 9 | Categories that are zero everywhere (auto) | Not present, or not sorted into that category | Ask the sorting team |
| 10 | Generation outside a broad 0.2-3 kg/cap/day plausibility range (auto, always) or below a cited reference (auto, if a benchmark is set) | Food fed to animals, composted or burned; material sold before collection; samples taken after waste pickers passed | Make it a finding; any adjustment goes in `adjustments` with reason and source |
| 11 | Waste sold to scrap dealers | Valuable fractions may never reach the sample | Ask whether sold material was weighed; report separately |
| 12 | Coverage against the plan | Source types in the terms of reference that were never sampled (dairy, fish processing, markets) | List them; they limit the municipal total |
| 13 | Non-household counts (auto) | A municipal total needs the number of each source type | Business register, school and health lists, market stall counts; else stop at households |
| 14 | Population figures | Year and source; whether sampled villages represent the whole area | Write both into the assumptions register |
| 15 | Income bands (auto, if bands missing) | Results by income depend on where the lines are drawn | Use the study's own definitions; test another cut as a sensitivity |
| 16 | Density | Needs container volume and paired weights | Otherwise say "not measured" and what would be needed |
| 17 | Category list against the plan | The tally may use fewer categories than the terms of reference listed | Map them; note what can't be reported |
| 18 | Season | One sampling week is one season | State it; plan a second round if facility sizing depends on it |

## Personal data

Before a model sees the sheet: drop names, phone numbers and street addresses; replace shop and stall names with type and number; keep village or ward. Keep the original files out of any synced or public repository.
