---
name: field-inspection-prep
description: >
  Prepare technical field inspections for sustainability certifications, subsidy
  reconciliations, supplier audits, and similar regulatory site visits. Locates
  the project's source documents (approved scope, supporting evidence, certificates,
  layouts), reconciles invoices against the approved scope per period, and generates
  a physical inspection checklist plus a gaps report. Supports initial inspections
  AND re-inspections where a prior period has already been verified and construction
  has since advanced (items now buried or covered).
  Triggered by: "prepare the inspection", "inspection checklist", "re-inspection",
  "approved scope", "site visit preparation", or when the user opens a folder
  matching project ID patterns.
argument-hint: locate | extract | reinspect | checklist | print | post-visit
---

# Field Inspection Preparation Skill

This skill supports an engineer or auditor preparing on-site inspections of
projects that have been approved against a documented scope (subsidies,
certifications, capital projects, supplier audits). It is a **direct-reading**
skill: default behaviour is to open PDFs and Excel files directly rather than
running scripts, because every project has its own quirks.

The skill is provider-agnostic. Localize document type names (e.g. final
construction reports, certificates of conformity, invoices) to the language and
regulatory context of your projects. Keep item descriptions in the original
language used by the source documents.

The skill builds on optional `CLAUDE.md`, `LEARNINGS.md`, and `patterns.json`
files in your project root. When present, these capture project-specific
conventions so subsequent inspections inherit your accumulated knowledge.

---

## Commands

### `locate`
Find the key documents in the project folder.

1. Scan the project root and sub-folders (typical: `SOLICITUD`, `XUSTIFICACION`,
   `modificacion*`, `CEs/`, `Certificados/`, `DOCUMENTACION/`, or your local
   equivalents).
2. Identify the **approved final scope** document — typically a final report or
   acceptance document signed off after award. Priority order:
   1. Most recent signed final report
   2. Approved scope amendment(s) if any
   3. Original application scope (only as fallback)
3. Identify the supporting evidence per approved item:
   - Invoices / receipts (per period if multi-year)
   - Certificates of conformity (CE, ISO, B-Corp, etc.)
   - Layout drawings, photos, serial numbers
   - Material flow records or compliance attestations

### `extract`
Read the approved scope document and extract a structured list of items:
- Item ID (or generated)
- Description (in the source language)
- Approved value / quantity
- Period or annuity (for multi-year projects)
- Required evidence type

### `reinspect`
For projects already partially verified in a prior period:
1. Identify items previously confirmed as installed and accepted
2. Flag items that may now be buried, enclosed, or otherwise inaccessible
3. Build the re-inspection focus list: only newly-completed items or items
   contested in a prior visit
4. Mark previously-verified items as out-of-scope for the current visit

### `checklist`
Generate the on-site inspection checklist as a printable document:
- One row per item with: ID, description, expected location, evidence to verify
- Space for inspector notes, date, signature
- Sorted by physical location for efficient site walk
- Includes any flagged items from `reinspect`

### `print`
Render the checklist to a print-ready PDF or HTML format using the included
`md_to_print_html.py` script.

### `post-visit`
After the inspection:
1. Update the project's `LEARNINGS.md` with anything noteworthy
2. Update `patterns.json` with any new heuristics for future visits
3. Generate a gaps report listing items that could not be verified, with reasons

---

## Project structure conventions

The skill assumes (but does not require) a project layout like:

```
<your-inspection-root>/
├── PROJECT-ID-YYYY-NNNNN/
│   ├── CLAUDE.md            # project-specific context (optional)
│   ├── LEARNINGS.md         # accumulated lessons (optional)
│   ├── patterns.json        # heuristics (optional)
│   ├── SOLICITUD/           # initial application
│   ├── XUSTIFICACION/       # final justification report
│   ├── modificaciones/      # scope amendments
│   ├── CEs/                 # certificates
│   └── ...
```

Adapt the folder names to your own conventions; the skill reads what's there
rather than requiring a specific structure.

---

## Background

This skill was originally built for a Galician public-subsidy inspection workflow
(IFO/AFO reconciliations on aquaculture and food-processing facilities) and
generalised for public release. The principles transfer cleanly to any
inspection where you need to reconcile what was approved against what was
actually built or supplied.

License: MIT. Created by [azvai.com](https://azvai.com).
