"""Unified CLI entry point for article-images.

Dispatches to the underlying scripts for each mode. Useful for non-developers
who don't want to hunt through scripts/ to find the right file.

Usage:
    python -m scripts.cli setup --slug acme --primary "#10b981"
    python -m scripts.cli preview --brand acme
    python -m scripts.cli featured --brand acme --title "My article" --out featured
    python -m scripts.cli stock --query "wind turbines" --count 3
    python -m scripts.cli html --template title_card.html --brand acme \
        --vars '{"title":"Hello"}' --output hello.png

Run any subcommand with --help for full options.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SKILL_SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SKILL_SCRIPTS))


# ---------- subcommand dispatchers ----------

def _cmd_setup(rest_argv: list[str]) -> int:
    import setup_brand
    sys.argv = ["setup_brand.py"] + rest_argv
    return setup_brand.main()


def _cmd_preview(rest_argv: list[str]) -> int:
    import preview_brand
    sys.argv = ["preview_brand.py"] + rest_argv
    return preview_brand.main()


def _cmd_featured(rest_argv: list[str]) -> int:
    import featured
    sys.argv = ["featured.py"] + rest_argv
    featured.main()
    return 0


def _cmd_stock(rest_argv: list[str]) -> int:
    import stock
    sys.argv = ["stock.py"] + rest_argv
    stock.main()
    return 0


def _cmd_html(rest_argv: list[str]) -> int:
    import html_to_image
    sys.argv = ["html_to_image.py"] + rest_argv
    return html_to_image.main()


COMMANDS = {
    "setup": ("Create a new brand profile (interactive wizard or flags)", _cmd_setup),
    "preview": ("Render a multi-chart preview of a brand profile", _cmd_preview),
    "featured": ("Render a featured / title card image (matplotlib)", _cmd_featured),
    "stock": ("Search and download stock photos (Unsplash / Pexels)", _cmd_stock),
    "html": ("Render an HTML template to PNG (brand-aware)", _cmd_html),
}


def print_help() -> None:
    print("article-images CLI\n")
    print("Usage: python -m scripts.cli <command> [options]\n")
    print("Commands:")
    width = max(len(c) for c in COMMANDS)
    for cmd, (desc, _) in COMMANDS.items():
        print(f"  {cmd.ljust(width)}  {desc}")
    print("\nRun 'python -m scripts.cli <command> --help' for command options.")


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help"}:
        print_help()
        return 0

    command = sys.argv[1]
    if command not in COMMANDS:
        print(f"Unknown command: {command}\n", file=sys.stderr)
        print_help()
        return 2

    rest_argv = sys.argv[2:]
    _, handler = COMMANDS[command]
    return handler(rest_argv) or 0


if __name__ == "__main__":
    sys.exit(main())
