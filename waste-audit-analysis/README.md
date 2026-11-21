# waste-audit-analysis

Desk analysis of a waste characterisation study. It turns hand-sorted tally sheets into generation rates (kg per household and per person per day), composition by weight, income-group splits and a scale-up to tonnes per day. Every adjustment and every data problem is written down.

Built and tested in November 2026 on a real 2019 household waste audit from two coastal sub-districts in East Java, Indonesia. A blind AI run matched the original workbook to the decimal in under six minutes. The test also showed where such numbers go wrong. The write-up, with timings and errors, is on azvai.com: [Can AI Analyse a Waste Characterisation Study?](https://azvai.com/en/ai-waste-composition-analysis/)

## What's inside

| Path | What it is |
|---|---|
| `SKILL.md` | The workflow Claude follows: inventory, four questions to confirm, run, read the flags, benchmark, report |
| `scripts/waste_audit.py` | The analysis (Python 3, pandas). Pre-flight checks, both per-capita averages with a bootstrap interval, composition, income bands, sensitivity, adjustments that must carry a reason and a source |
| `references/data-quality-checklist.md` | 18 checks: what to look for, why, what to do |
| `templates/config.example.json`, `templates/report-outline.md` | Config to copy, report structure |
| `examples/make_synthetic.py`, `examples/synthetic-config.json` | A synthetic two-ward audit with planted problems and a known answer (invented data) |
| `tests/` | Unit tests (`python -m unittest discover -s tests`) |

## Install

```bash
cp -r waste-audit-analysis ~/.claude/skills/
pip install pandas
```

Then ask Claude something like "analyse the waste audit in this folder". It will ask you four questions before it computes anything.

## Limits

It doesn't design the sampling, sort the waste or decide how much missed food waste to add back. One sampling week is one season.
