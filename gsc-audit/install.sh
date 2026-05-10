#!/bin/bash
# GSC Audit Skill - MCP Server Installation Script
# This script sets up the mcp-gsc MCP server correctly using claude mcp add

set -e

echo "🔧 GSC Audit - MCP Server Setup"
echo "================================"
echo

# Save original directory - claude mcp add uses current directory context
ORIGINAL_DIR=$(pwd)

# Detect current working directory (project root)
if [ -f ".claude.json" ]; then
    PROJECT_DIR=$(pwd)
    echo "📍 Project: $PROJECT_DIR"
else
    echo "⚠️  Warning: Not in a project directory with .claude.json"
    echo "   MCP server will be configured globally"
fi
echo

# Check if mcp-gsc directory exists
if [ ! -d "$HOME/.claude/mcp-gsc" ]; then
    echo "📦 Cloning mcp-gsc repository..."
    git clone https://github.com/AminForou/mcp-gsc.git "$HOME/.claude/mcp-gsc"
    echo "✅ Repository cloned to ~/.claude/mcp-gsc"
    echo
else
    echo "✅ mcp-gsc repository already exists"
    echo
fi

# Set up Python virtual environment
cd "$HOME/.claude/mcp-gsc"

if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
    echo
else
    echo "✅ Python virtual environment already exists"
    echo
fi

# Install dependencies
echo "📚 Installing Python dependencies..."
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
deactivate
echo "✅ Dependencies installed"
echo

# Return to original directory for MCP configuration
cd "$ORIGINAL_DIR" || exit 1

# Add MCP server using claude mcp add command
echo "🔗 Configuring MCP server..."

# Remove existing gsc server if it exists (clean slate)
claude mcp remove gsc 2>/dev/null || true

# Add the server with correct configuration
# Note: Don't include "stdio" - it's the default transport type
if claude mcp add gsc -- \
    "$HOME/.claude/mcp-gsc/.venv/bin/python" \
    "$HOME/.claude/mcp-gsc/gsc_server.py"; then
    echo "✅ MCP server configured correctly"
else
    echo "❌ Failed to add MCP server"
    exit 1
fi
echo

# Add OAuth credentials environment variable if client_secrets.json exists
if [ -f "$HOME/.claude/mcp-gsc/client_secrets.json" ]; then
    echo "✅ OAuth credentials found"
    echo "🔧 Adding OAuth environment variable to MCP config..."

    # Use Python to safely edit .claude.json
    python3 <<EOF
import json
import os
from pathlib import Path

# Find .claude.json in current directory or home
config_paths = [
    Path.cwd() / ".claude.json",
    Path.home() / ".claude.json"
]

for config_path in config_paths:
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Navigate to the gsc MCP server config
        # Check both project-level and global locations
        gsc_config = None
        if 'projects' in config:
            for project_path, project_data in config['projects'].items():
                if 'mcpServers' in project_data and 'gsc' in project_data['mcpServers']:
                    gsc_config = project_data['mcpServers']['gsc']
                    break

        if gsc_config and 'env' in gsc_config:
            gsc_config['env']['GSC_OAUTH_CLIENT_SECRETS_FILE'] = str(Path.home() / ".claude/mcp-gsc/client_secrets.json")

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"✅ Updated {config_path}")
            break
EOF

    echo "✅ OAuth credentials configured"
    echo
    echo "🎉 Setup complete! The GSC MCP server is ready to use."
    echo
    echo "📋 To test:"
    echo "   Restart Claude Code and ask: 'List my GSC properties'"
    echo
else
    echo "⚠️  OAuth credentials not found"
    echo
    echo "📋 Next steps:"
    echo "   1. Ask Claude: 'Help me set up GSC OAuth credentials'"
    echo "   2. OR follow the manual guide in references/setup-guide.md"
    echo "   3. After getting credentials, run this script again"
    echo
fi

echo "✨ Installation complete!"
echo
