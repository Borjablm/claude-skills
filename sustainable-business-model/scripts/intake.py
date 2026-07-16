#!/usr/bin/env python3
"""Read a folder of whatever the founder has and produce a digest to model from.

Nobody arrives with a clean model. They arrive with a pitch deck, a grant
application, an email about rent, a spreadsheet someone started, and a lot in
their head. This reads what is there and lays it out — text, tables, and the
numbers it can find with their surrounding context.

It deliberately does not guess the model. Extraction is mechanical and belongs in
code; deciding that "€4,800" is annual rent per site rather than a one-off deposit
is judgment and belongs to whoever reads the digest. A regex that quietly guessed
wrong would be worse than no extraction at all, because nobody would check it.

Usage:
    python intake.py inputs/ --out model/intake.md
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

TEXT_EXT = {".txt", ".md", ".csv", ".json", ".yaml", ".yml"}
NUM_RE = re.compile(
    r"(?<![\w.])"
    r"(?:[€$£]\s?)?"
    r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+[.,]\d+|\b\d{2,}\b"
    r"(?:\s?%)?")


def read_pdf(p):
    try:
        from pypdf import PdfReader
    except ImportError:
        return None, "pypdf not installed"
    try:
        r = PdfReader(str(p))
        return "\n".join((pg.extract_text() or "") for pg in r.pages), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def read_docx(p):
    try:
        import docx
    except ImportError:
        return None, "python-docx not installed"
    try:
        d = docx.Document(str(p))
        parts = [x.text for x in d.paragraphs if x.text.strip()]
        for t in d.tables:
            for row in t.rows:
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    parts.append(" | ".join(cells))
        return "\n".join(parts), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def read_xlsx(p):
    try:
        from openpyxl import load_workbook
    except ImportError:
        return None, "openpyxl not installed"
    try:
        wb = load_workbook(str(p), data_only=True)
        out = []
        for ws in wb.worksheets:
            out.append(f"### sheet: {ws.title}")
            for row in ws.iter_rows():
                cells = [f"{c.coordinate}={c.value!r}" for c in row if c.value is not None]
                if cells:
                    out.append("  " + " | ".join(cells))
        return "\n".join(out), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def read_pptx(p):
    try:
        from pptx import Presentation
    except ImportError:
        return None, "python-pptx not installed (pitch decks are often .pptx)"
    try:
        pres = Presentation(str(p))
        out = []
        for i, slide in enumerate(pres.slides, 1):
            out.append(f"### slide {i}")
            for sh in slide.shapes:
                if sh.has_text_frame and sh.text_frame.text.strip():
                    out.append("  " + sh.text_frame.text.strip().replace("\n", " / "))
        return "\n".join(out), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


READERS = {".pdf": read_pdf, ".docx": read_docx, ".xlsx": read_xlsx,
           ".xlsm": read_xlsx, ".pptx": read_pptx}


def numbers_with_context(text, width=60):
    """Every number with the words around it. The context is the whole point —
    a number without it cannot be turned into an assumption."""
    out = []
    for m in NUM_RE.finditer(text):
        s = max(0, m.start() - width)
        e = min(len(text), m.end() + width)
        ctx = " ".join(text[s:e].split())
        out.append({"value": m.group().strip(), "context": ctx})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--out", default="model/intake.md")
    ap.add_argument("--max-numbers", type=int, default=120)
    a = ap.parse_args()

    root = Path(a.folder)
    if not root.exists():
        raise SystemExit(f"{root} does not exist")
    files = sorted(p for p in root.rglob("*") if p.is_file()
                   and not p.name.startswith("~$"))

    parts = ["# Intake digest", "",
             f"Source folder: `{root}`  ", f"{len(files)} file(s) found.", ""]
    inventory, unread = [], []
    all_text = []

    for p in files:
        ext = p.suffix.lower()
        if ext in TEXT_EXT:
            try:
                txt = p.read_text(encoding="utf-8", errors="replace")
                err = None
            except Exception as e:
                txt, err = None, str(e)
        elif ext in READERS:
            txt, err = READERS[ext](p)
        else:
            txt, err = None, f"no reader for {ext}"
        rel = p.relative_to(root)
        if txt:
            inventory.append((str(rel), len(txt)))
            all_text.append((str(rel), txt))
        else:
            unread.append((str(rel), err))

    parts.append("## What was read\n")
    if inventory:
        parts.append("| file | characters |\n|---|---|")
        for n, ln in inventory:
            parts.append(f"| `{n}` | {ln:,} |")
    else:
        parts.append("_Nothing readable._")
    if unread:
        parts.append("\n## Not read\n")
        parts.append("| file | why |\n|---|---|")
        for n, e in unread:
            parts.append(f"| `{n}` | {e} |")
        parts.append("\nThese may hold the numbers that matter. Convert them, or ask "
                     "for the content directly, rather than modelling around the gap.")

    parts.append("\n## Numbers found, with their context\n")
    parts.append("Every number the digest could see, with surrounding words. A number "
                 "without context cannot become an assumption — read these, do not trust "
                 "them.\n")
    total = 0
    for name, txt in all_text:
        nums = numbers_with_context(txt)
        if not nums:
            continue
        parts.append(f"### {name}\n")
        for nn in nums[:max(1, a.max_numbers // max(1, len(all_text)))]:
            parts.append(f"- **{nn['value']}** — …{nn['context']}…")
            total += 1
        parts.append("")

    parts.append("## Full text\n")
    for name, txt in all_text:
        parts.append(f"### {name}\n\n```\n{txt[:20000]}\n```\n")

    parts.append("## What to do next\n")
    parts.append(
        "1. Read the text above and write the revenue sentence in plain words with the "
        "founder: *\"we earn X each time a Y does Z, and Y does Z N times a year\"*. If "
        "that sentence cannot be written, the model is premature and saying so is the "
        "honest deliverable.\n"
        "2. Name the drivers in that sentence. They are the model's skeleton.\n"
        "3. Draft `spec.yaml` with every driver ungraded and no source. A fresh model "
        "should be visibly all-C — that is honest, and it shows how far the work has got.\n"
        "4. Run `explore.py` **before** researching anything, so effort goes to the "
        "five numbers that matter rather than all fifty.\n"
        "5. Ask the founder for anything in the 'Not read' list that looks load-bearing.")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"intake digest -> {a.out}")
    print(f"  read {len(inventory)} file(s), {total} numbers with context")
    if unread:
        print(f"  could not read {len(unread)}: " +
              ", ".join(n for n, _ in unread[:4]))


if __name__ == "__main__":
    main()
