#!/bin/bash
# financial-model-audit — installation
# Copies the skill into your Claude skills folder and installs its one dependency.

set -e

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="financial-model-audit"

echo "📊 financial-model-audit — setup"
echo "================================"
echo

# --- where to install ---------------------------------------------------------
if [ -d ".claude" ] && [ "$(pwd)" != "$(dirname "$SKILL_DIR")" ]; then
    TARGET=".claude/skills"
    echo "📍 Project-scoped install: $(pwd)/$TARGET"
else
    TARGET="$HOME/.claude/skills"
    echo "📍 User-scoped install: $TARGET"
fi

mkdir -p "$TARGET"
if [ -d "$TARGET/$SKILL_NAME" ]; then
    echo "⚠️  $TARGET/$SKILL_NAME already exists — replacing it"
    rm -rf "$TARGET/$SKILL_NAME"
fi
cp -r "$SKILL_DIR" "$TARGET/$SKILL_NAME"
echo "✅ Skill copied"
echo

# --- dependency ---------------------------------------------------------------
PY="${PYTHON:-python}"
command -v "$PY" >/dev/null 2>&1 || PY=python3
echo "📦 Installing openpyxl (the only dependency)…"
"$PY" -m pip install --quiet --upgrade openpyxl
echo "✅ openpyxl ready"
echo

# --- verify -------------------------------------------------------------------
if "$PY" -c "import openpyxl" 2>/dev/null; then
    echo "🎉 Done. Try it:"
    echo
    echo "   \"Audit the financial model in inputs/business-plan.xlsx —"
    echo "    I'm presenting to the investment committee on Thursday.\""
    echo
    echo "   Or run the scripts directly:"
    echo "   $PY $TARGET/$SKILL_NAME/scripts/model_graph.py MODEL.xlsx --out model/graph.json --verify"
else
    echo "❌ openpyxl did not import. Install it manually:  $PY -m pip install openpyxl"
    exit 1
fi
