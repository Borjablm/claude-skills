# takeback-market-entry-scan

A Claude Code skill for the desk research a take-back or reuse pilot needs before it enters a new country: rules and producer responsibility for the product stream, permits to collect, store, prepare for reuse, recycle and ship it, candidate partners, competitor schemes and disposal prices. Two claim ledgers (rules tied to instruments, partners tied to dated evidence) and a checker that fails what should not reach a report.

Built from a timed test on used carpet tiles for the island of Ireland (November 2026), re-running the desk research of a 2019 take-back relaunch: 18 minutes from question to two checked ledgers, against about 50 hours by hand in 2019. Both AI runs missed the partner the 2019 team signed, and both listed a UK reuse social enterprise that had been dissolved eleven weeks earlier. The write-up is on azvai.com.

## Install
Copy the folder into `~/.claude/skills/` (or a project's `.claude/skills/`). Python 3.9+, standard library; `pip install certifi` for `--check-urls`.

## Use
Ask Claude Code for a take-back market-entry scan, naming the product, the market and any past partners. Then:

```bash
python scripts/check_ledger.py rules.csv --as-of 2026-11-21 --out rules-report.md
python scripts/check_ledger.py partners.csv --as-of 2026-11-21 --check-urls --out partners-report.md
python -m unittest discover -s evals
```

## Limits
It produces a call list, not a decision. Regulators' readings of borderline questions, partner appetite and capacity, real gate fees and the trust a partner agreement needs come from people. Legal references in the example are as checked on 21 Nov 2026 and will date.
