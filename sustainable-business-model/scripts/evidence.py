#!/usr/bin/env python3
"""Search the source folder for what stands behind each driver — and what contradicts it.

The evidence for a model is usually already in the room: in an interview transcript,
a slide, a report annex. It is just not next to the number it justifies, so it never
gets connected and the model looks like a pile of guesses when half of it is field
research. Running this by hand on a real project, the best evidence in the folder
was a consultant's own interviews with net experts — and the first pass had graded
those drivers "no source given".

The other half matters more. When a deck says 75% and the model says 85%, or a deck
says 8 tonnes and the model says 35, that is not a gap — it is a contradiction
between the project's own documents, and it is the most valuable thing an evidence
search can surface. A funder's analyst reads both documents.

This proposes; it does not decide. Every hit is a quote with its file and its
context, for a human to accept, reject or investigate. Auto-grading from a keyword
match would manufacture exactly the false confidence the whole skill exists to
prevent.

Usage:
    python evidence.py --spec spec.yaml --corpus inputs/ --out out/evidence.md
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

from model import load_spec, n_periods, SpecError
from intake import READERS, TEXT_EXT

STOP = {
    "the", "a", "an", "of", "per", "and", "or", "to", "in", "for", "on", "at", "by",
    "from", "with", "as", "is", "are", "be", "year", "years", "total", "average",
    "avg", "cost", "costs", "price", "number", "share", "rate", "de", "la", "el",
    "los", "las", "y", "o", "en", "por", "del", "un", "una", "coste", "precio",
}
# Number formats that appear in real documents: 1,000 / 1.000 / 1 000 / 1000.5
NUM_RE = re.compile(r"\d{1,3}(?:[.,  ]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?")


def norm(s):
    """Lowercase and strip accents, one output char per input char.

    Length has to be preserved: matches are found in the normalised text and then
    sliced out of the original, so any change in length silently shifts every
    quote. NFKD-then-drop-combining does change length ("é" becomes two chars, one
    is dropped, but "ﬁ" becomes two and neither is), which quietly returned
    snippets from the wrong part of the document.
    """
    out = []
    for ch in str(s):
        d = unicodedata.normalize("NFKD", ch)
        base = "".join(c for c in d if not unicodedata.combining(c))
        out.append(base[0] if base else ch)
    return "".join(out).lower()


def parse_number(tok):
    """Read 1,000 / 1.000 / 1 000 / 1000.5 as a float, tolerating both conventions."""
    t = tok.strip().replace(" ", " ")
    t = re.sub(r"(?<=\d)[ ](?=\d{3}\b)", "", t)
    if "," in t and "." in t:
        # whichever separator is last is the decimal one
        t = t.replace(".", "").replace(",", ".") if t.rfind(",") > t.rfind(".") \
            else t.replace(",", "")
    elif "," in t:
        t = t.replace(",", "") if re.search(r",\d{3}\b", t) else t.replace(",", ".")
    elif "." in t:
        if re.search(r"\.\d{3}\b", t) and not re.search(r"\.\d{1,2}$", t):
            t = t.replace(".", "")
    try:
        return float(t)
    except ValueError:
        return None


def read_corpus(root: Path):
    out = {}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.name.startswith("~$"):
            continue
        ext = p.suffix.lower()
        try:
            if ext in TEXT_EXT:
                txt = p.read_text(encoding="utf-8", errors="replace")
            elif ext in READERS:
                txt, _ = READERS[ext](p)
            else:
                continue
        except Exception:
            continue
        if txt:
            out[str(p.relative_to(root))] = txt
    return out


def keywords(driver, key):
    """Search terms from the driver's label.

    Tokens may contain digits after the first letter — "co2e", "pa6", "40ft" are
    exactly the words worth searching for, and a letters-only pattern drops them.
    """
    words = re.findall(r"[a-zà-ÿ][a-z0-9à-ÿ]{2,}", norm(driver.get("label") or key))
    words = [w for w in words if w not in STOP]
    # Longer words first: "processed" locates a passage better than "nets".
    words.sort(key=len, reverse=True)
    return words[:4]


# The digest's own scaffolding ("### slide 14", "### sheet: P&L") carries numbers
# that belong to the extractor, not the document. Left in, they crowd out real
# contradictions with slide indices.
SCAFFOLD_RE = re.compile(r"###\s*(slide|sheet|page)\s*:?\s*\d*", re.I)


def magnitude_gap(v, targets):
    """How far apart two numbers are in orders of magnitude.

    This is what separates a contradiction from a coincidence. A document saying 8
    where the model says 6.5 is a competing claim about the same quantity. A
    document saying 1,000,000 is talking about something else entirely, however
    close to the keyword it sits.
    """
    import math
    best = None
    for t in targets:
        if t == 0 or v == 0:
            continue
        for scale in (1, 1000, 0.001, 100, 0.01):
            g = abs(math.log10(abs(v) / abs(t * scale)))
            best = g if best is None else min(best, g)
    return best if best is not None else 99


def scan_driver(corpus, driver, key, n, window=200):
    """Find every number sitting near this driver's words, and say whether it agrees."""
    base = driver.get("values", driver.get("value"))
    targets = [float(x) for x in (base if isinstance(base, list) else [base])
               if isinstance(x, (int, float))]
    if not targets:
        return []
    kws = keywords(driver, key)
    if not kws:
        return []
    hits = []
    for fname, text in corpus.items():
        ntext = norm(text)
        for kw in kws:
            for m in re.finditer(re.escape(kw), ntext):
                s, e = max(0, m.start() - window), min(len(text), m.end() + window)
                snippet = " ".join(text[s:e].split())
                # Skip raw spreadsheet cell dumps — the model quoting itself.
                if snippet.count("=") > 3 and snippet.count("|") > 3:
                    continue
                clean = SCAFFOLD_RE.sub(" ", snippet)
                for nm in NUM_RE.finditer(clean):
                    v = parse_number(nm.group())
                    if v is None or v == 0:
                        continue
                    agrees = any(
                        abs(v - t) <= max(0.01, abs(t) * 0.02) or
                        # tolerate unit shifts: 60 t vs 60,000 kg, 0.85 vs 85%
                        abs(v - t * 1000) <= abs(t * 1000) * 0.02 or
                        abs(v - t / 1000) <= abs(t / 1000) * 0.02 or
                        abs(v - t * 100) <= abs(t * 100) * 0.02
                        for t in targets)
                    gap = magnitude_gap(v, targets)
                    # Two orders of magnitude out is a different quantity, not a
                    # competing claim. Keeping those buries the real ones.
                    if not agrees and gap > 1.4:
                        continue
                    hits.append({"file": fname, "keyword": kw, "value": v, "gap": gap,
                                 "agrees": agrees, "snippet": snippet})
    seen, out = set(), []
    # Agreement first; then closest in magnitude, which is the likeliest to be a
    # claim about the same thing.
    for h in sorted(hits, key=lambda h: (not h["agrees"], h["gap"], h["file"])):
        sig = (h["file"], round(h["value"], 4), h["snippet"][:60])
        if sig in seen:
            continue
        seen.add(sig)
        out.append(h)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", default="spec.yaml")
    ap.add_argument("--corpus", default="inputs")
    ap.add_argument("--out", default="out/evidence.md")
    ap.add_argument("--max-per-driver", type=int, default=6)
    a = ap.parse_args()

    try:
        spec = load_spec(a.spec)
    except SpecError as e:
        raise SystemExit(f"\n{e}\n")
    corpus = read_corpus(Path(a.corpus))
    if not corpus:
        raise SystemExit(f"nothing readable in {a.corpus}")
    n = n_periods(spec)

    parts = ["# Evidence found in the source folder", "",
             f"Searched {len(corpus)} document(s) for what stands behind each driver.",
             "",
             "**These are proposals, not gradings.** Each hit is a number sitting near "
             "the driver's own words. Read the quote and decide: does it support this "
             "driver, contradict it, or is it about something else entirely? A keyword "
             "match is not evidence.", ""]

    supported, contradicted, orphan = [], [], []
    for key, d in spec["drivers"].items():
        hits = scan_driver(corpus, d, key, n)
        agree = [h for h in hits if h["agrees"]][:a.max_per_driver]
        differ = [h for h in hits if not h["agrees"]][:a.max_per_driver]
        label = d.get("label") or key
        base = d.get("values", d.get("value"))
        parts.append(f"## {label}\n")
        parts.append(f"`{key}` = **{base}**"
                     + (f" · graded **{d['grade']}**" if d.get("grade") else " · ungraded")
                     + (f" · source recorded: {str(d.get('source'))[:90]}"
                        if d.get("source") else " · **no source recorded**") + "\n")
        if agree:
            supported.append(key)
            parts.append("**Documents containing this value**\n")
            for h in agree:
                parts.append(f"- `{h['file']}` — …{h['snippet'][:260]}…")
            parts.append("")
        if differ:
            parts.append("**Different numbers near the same words — check for a "
                         "contradiction**\n")
            for h in differ:
                parts.append(f"- **{h['value']:g}** in `{h['file']}` — …{h['snippet'][:260]}…")
            parts.append("")
            contradicted.append(key)
        if not hits:
            orphan.append(key)
            parts.append("_Nothing in the folder mentions this. Either it comes from "
                         "outside, or it was never written down. If it has leverage, "
                         "that is a question for whoever built the model._\n")

    head = [
        "## Summary\n",
        f"- **{len(supported)}** driver(s) have their value written somewhere in the "
        f"folder — those documents are the source, and the driver should say so.",
        f"- **{len(contradicted)}** driver(s) have *other* numbers sitting next to the "
        f"same words. Some will be noise. Some will be a document contradicting the "
        f"model, which is the most useful thing in this report.",
        f"- **{len(orphan)}** driver(s) appear nowhere in the folder.\n",
        "Where a document and the model disagree, the document usually wins — and "
        "either way somebody should reconcile them before a funder reads both.\n",
    ]
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts[:5] + head + parts[5:]), encoding="utf-8")

    print(f"evidence -> {a.out}")
    print(f"  searched {len(corpus)} document(s) for {len(spec['drivers'])} drivers")
    print(f"  {len(supported)} value(s) found in the folder, "
          f"{len(contradicted)} with competing numbers nearby, {len(orphan)} unmentioned")
    if orphan:
        print("  not mentioned anywhere: " + ", ".join(orphan[:6]))


if __name__ == "__main__":
    main()
