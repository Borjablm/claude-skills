#!/bin/bash
# sustainable-business-model — installation

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="sustainable-business-model"

echo "🌱 sustainable-business-model — setup"
echo "====================================="
echo

if [ -d ".claude" ] && [ "$(pwd)" != "$(dirname "$SKILL_DIR")" ]; then
    TARGET=".claude/skills"
    echo "📍 Project-scoped install: $(pwd)/$TARGET"
else
    TARGET="$HOME/.claude/skills"
    echo "📍 User-scoped install: $TARGET"
fi

mkdir -p "$TARGET"
if [ -d "$TARGET/$SKILL_NAME" ]; then
    echo "⚠️  $TARGET/$SKILL_NAME exists — replacing it"
    rm -rf "$TARGET/$SKILL_NAME"
fi
cp -r "$SKILL_DIR" "$TARGET/$SKILL_NAME"
echo "✅ Skill copied"
echo

PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3

echo "📦 Installing required dependencies (pyyaml, openpyxl)…"
"$PY" -m pip install --quiet --upgrade pyyaml openpyxl
echo "✅ Required dependencies ready"

echo "📦 Installing optional intake readers (pypdf, python-docx, python-pptx)…"
if "$PY" -m pip install --quiet --upgrade pypdf python-docx python-pptx 2>/dev/null; then
    echo "✅ Intake can read PDFs, Word documents and decks"
else
    echo "⚠️  Optional readers not installed — intake will still read text, CSV and"
    echo "   spreadsheets, and will say which files it could not open."
fi
echo

if "$PY" -c "import yaml, openpyxl" 2>/dev/null; then
    echo "🎉 Done. Try the worked example:"
    echo
    echo "   $PY $TARGET/$SKILL_NAME/scripts/model.py \\"
    echo "       $TARGET/$SKILL_NAME/assets/example-repair-network.yaml"
    echo
    echo "   Or just ask:"
    echo "   \"Here's our pitch deck and costs in inputs/. Build me a financial model"
    echo "    that survives a funder asking when we stop needing grants.\""
else
    echo "❌ pyyaml/openpyxl did not import. Install manually:"
    echo "   $PY -m pip install pyyaml openpyxl"
    exit 1
fi
