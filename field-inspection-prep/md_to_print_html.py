#!/usr/bin/env python3
"""Convert an inspection markdown file to a print-ready, B&W HTML.

Usage:
    python md_to_print_html.py <input.md> [output.html]

If output.html is omitted, writes alongside the input with .html extension.
Open the HTML in any browser and use Ctrl+P → "Save as PDF" (set "Color"
to "Black and white" and disable backgrounds for the cleanest output).
"""
import re
import sys
from pathlib import Path

try:
    import markdown as md_lib
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


CSS = """
@page {
    size: A4;
    margin: 1.6cm 1.5cm 1.8cm 1.5cm;
}

* { box-sizing: border-box; }

html, body {
    color: #000;
    background: #fff;
}

body {
    font-family: Georgia, "Times New Roman", serif;
    font-size: 10.5pt;
    line-height: 1.42;
    max-width: 920px;
    margin: 2em auto;
    padding: 0 2em;
}

@media print {
    body { margin: 0; max-width: none; padding: 0; }
    a { color: #000; text-decoration: none; }
    .no-print { display: none !important; }
}

h1 {
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 20pt;
    border-bottom: 2.5px solid #000;
    padding-bottom: 0.25em;
    margin: 0 0 0.6em 0;
    page-break-after: avoid;
}

h2 {
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 14pt;
    border-bottom: 1px solid #000;
    padding-bottom: 0.2em;
    margin: 1.6em 0 0.5em 0;
    page-break-after: avoid;
}

h3 {
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 11.5pt;
    margin: 1.2em 0 0.3em 0;
    page-break-after: avoid;
}

p, li { orphans: 3; widows: 3; }

table {
    border-collapse: collapse;
    width: 100%;
    margin: 0.7em 0;
    page-break-inside: avoid;
    font-size: 10pt;
}

th, td {
    border: 1px solid #000;
    padding: 5px 8px;
    text-align: left;
    vertical-align: top;
}

th {
    background: #e8e8e8;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    font-weight: bold;
    font-family: "Helvetica Neue", Arial, sans-serif;
}

ul, ol { margin: 0.4em 0; padding-left: 1.5em; }
li { margin: 0.1em 0; }

ul.task-list { list-style: none; padding-left: 0.4em; }
ul.task-list li { padding-left: 1.6em; position: relative; }
ul.task-list li::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0.25em;
    width: 11px;
    height: 11px;
    border: 1.5px solid #000;
    background: #fff;
}
ul.task-list li.checked::before {
    content: "✓";
    text-align: center;
    line-height: 9px;
    font-weight: bold;
    font-size: 11pt;
}

code {
    font-family: "Consolas", "Courier New", monospace;
    background: #f1f1f1;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    border: 1px solid #ccc;
    padding: 0 4px;
    font-size: 9.5pt;
    border-radius: 2px;
}

pre {
    background: #f5f5f5;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
    border: 1px solid #bbb;
    padding: 0.6em 0.9em;
    overflow-x: auto;
    page-break-inside: avoid;
}
pre code { background: transparent; border: none; padding: 0; }

blockquote {
    border-left: 3px solid #000;
    margin: 0.6em 0;
    padding: 0.1em 1em;
    font-style: italic;
}

hr { border: none; border-top: 1px solid #000; margin: 1.2em 0; }

strong { font-weight: bold; }
em { font-style: italic; }

.print-btn {
    position: fixed;
    top: 1em;
    right: 1em;
    padding: 0.55em 1.1em;
    background: #000;
    color: #fff;
    border: none;
    cursor: pointer;
    font-family: "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    border-radius: 3px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.25);
}
.print-btn:hover { background: #333; }

.meta {
    color: #555;
    font-size: 9.5pt;
    font-style: italic;
    margin-bottom: 1.2em;
}
"""


def simple_md_to_html(text: str) -> str:
    """Bare-bones markdown converter for when the markdown lib isn't installed."""
    lines = text.split("\n")
    out, in_table, in_list, in_pre = [], False, False, False
    table_buf = []

    def flush_table():
        if not table_buf:
            return
        rows = table_buf[:]
        table_buf.clear()
        rows = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
        if len(rows) >= 2 and all(re.match(r"^:?-+:?$", c) for c in rows[1]):
            header, body_rows = rows[0], rows[2:]
        else:
            header, body_rows = None, rows
        out.append("<table>")
        if header:
            out.append("<thead><tr>")
            for c in header:
                out.append(f"<th>{inline(c)}</th>")
            out.append("</tr></thead>")
        out.append("<tbody>")
        for r in body_rows:
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
        out.append("</tbody></table>")

    def inline(s: str) -> str:
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^\)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    for line in lines:
        if line.strip().startswith("```"):
            in_pre = not in_pre
            out.append("<pre><code>" if in_pre else "</code></pre>")
            continue
        if in_pre:
            out.append(line)
            continue
        if "|" in line and line.strip().startswith("|"):
            in_table = True
            table_buf.append(line)
            continue
        if in_table:
            flush_table()
            in_table = False
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            continue
        if re.match(r"^\s*[-*]\s+", line):
            if not in_list:
                # detect task list
                is_task = bool(re.match(r"^\s*[-*]\s+\[[ xX]\]\s+", line))
                out.append(
                    '<ul class="task-list">' if is_task else "<ul>"
                )
                in_list = True
            cb = re.match(r"^\s*[-*]\s+\[([ xX])\]\s+(.*)$", line)
            if cb:
                cls = ' class="checked"' if cb.group(1).lower() == "x" else ""
                out.append(f"<li{cls}>{inline(cb.group(2))}</li>")
            else:
                content = re.sub(r"^\s*[-*]\s+", "", line)
                out.append(f"<li>{inline(content)}</li>")
            continue
        if in_list and not line.strip():
            out.append("</ul>")
            in_list = False
            continue
        if line.strip() == "---":
            out.append("<hr>")
            continue
        if line.strip():
            out.append(f"<p>{inline(line)}</p>")
        else:
            out.append("")
    if in_list:
        out.append("</ul>")
    if in_table:
        flush_table()
    return "\n".join(out)


def post_process_task_lists(html: str) -> str:
    """Turn GitHub-style task list <li>[ ] foo</li> into styled checkboxes."""
    def repl(m):
        marker = m.group(1)
        rest = m.group(2)
        cls = " checked" if marker.lower() == "x" else ""
        return f'<li class="task-item{cls}">{rest}</li>'

    html = re.sub(r"<li>\s*\[([ xX])\]\s+(.*?)</li>", repl, html, flags=re.DOTALL)
    html = re.sub(
        r"<ul>(\s*<li class=\"task-item)",
        r'<ul class="task-list">\1',
        html,
    )
    html = html.replace('class="task-item checked"', 'class="checked"')
    html = html.replace('class="task-item"', "")
    return html


def extract_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        m = re.match(r"^#\s+(.*)$", line)
        if m:
            return m.group(1).strip()
    return fallback


def convert(md_path: Path, out_path: Path) -> None:
    text = md_path.read_text(encoding="utf-8")
    title = extract_title(text, md_path.stem)

    if HAS_MARKDOWN:
        body = md_lib.markdown(
            text,
            extensions=["tables", "fenced_code", "sane_lists"],
        )
        body = post_process_task_lists(body)
    else:
        body = simple_md_to_html(text)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{CSS}</style>
</head>
<body>
<button class="print-btn no-print" onclick="window.print()">Imprimir / Save as PDF</button>
{body}
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    # Use ASCII-only stdout so Windows cp1252 console doesn't blow up.
    print(f"OK  {md_path.name} -> {out_path}")
    if not HAS_MARKDOWN:
        print(
            "    (using built-in fallback converter; "
            "for richer output: pip install markdown)"
        )


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    md_path = Path(argv[1])
    if not md_path.exists():
        print(f"Error: {md_path} not found", file=sys.stderr)
        sys.exit(1)
    out_path = Path(argv[2]) if len(argv) >= 3 else md_path.with_suffix(".html")
    convert(md_path, out_path)


if __name__ == "__main__":
    main(sys.argv)
