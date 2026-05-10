# GSC Audit Skill

Comprehensive SEO audit powered by Google Search Console data. Analyzes CTR opportunities, content decay, keyword cannibalization, quick wins, and more.

## Installation

### Step 1: Install the Skill

```bash
/install-skill gsc-audit-v1.0.0.zip
```

### Step 2: Run the MCP Server Setup

After installing the skill, run the installation script:

```bash
cd ~/.claude/skills/gsc-audit
./install.sh
```

This will:
- Clone the mcp-gsc repository to `~/.claude/mcp-gsc/`
- Set up the Python virtual environment
- Install dependencies
- Configure the MCP server correctly using `claude mcp add`

### Step 3: Set Up OAuth Credentials

You have two options:

**Option A: Assisted Wizard (Recommended)**
Ask Claude:
> "Help me set up GSC OAuth credentials"

Claude will guide you through creating OAuth credentials in Google Cloud Console.

**Option B: Manual Setup**
Follow the complete written guide in `references/setup-guide.md` Section 5.

### What Gets Installed

| Component | Purpose | Location |
|-----------|---------|----------|
| mcp-gsc repository | The MCP server code | `~/.claude/mcp-gsc/` |
| Python virtual environment | Isolated dependencies | `~/.claude/mcp-gsc/.venv/` |
| Google Cloud CLI | Creates OAuth credentials | System-wide |
| OAuth credentials | Authenticates with Google | `~/.claude/mcp-gsc/client_secrets.json` |

### Prerequisites

- **Python 3.10+** - Will be installed if missing
- **Git** - Usually pre-installed on macOS/Linux
- **Google Account** with Search Console access
- **Claude Code** installed and working

### Time Required

- Assisted wizard: ~10-15 minutes
- Manual setup: ~15-20 minutes

Most of the time is spent in the browser configuring Google Cloud OAuth.

## Dependencies

### Python Packages (in mcp-gsc)
The MCP server installs its own dependencies in an isolated virtual environment:
- google-api-python-client
- google-auth-oauthlib
- Other dependencies from mcp-gsc requirements.txt

### System Tools
- **Google Cloud CLI** - Installed during setup
  - macOS: `brew install google-cloud-sdk`
  - Windows: `winget install Google.CloudSDK`
  - Linux: `sudo snap install google-cloud-cli --classic`

### MCP Server
- **mcp-gsc** from [github.com/AminForou/mcp-gsc](https://github.com/AminForou/mcp-gsc)

## Costs

**Google Search Console API: FREE**

The Search Console API is free to use. No billing account required (though Google Cloud may ask you to create one, you won't be charged).

Rate limits:
- 1,200 queries per minute
- Most audits complete well within these limits

## Usage

After setup, trigger the skill by asking:

```
Run a GSC audit
```

Or be more specific:
```
Find my striking distance keywords
Which pages are losing traffic?
Check for keyword cannibalization
```

See `WORKFLOW.md` for detailed usage examples.

## What the Audit Covers

| Analysis | What It Finds |
|----------|---------------|
| CTR Optimization | Pages ranking well but getting fewer clicks than expected |
| Content Decay | Pages that lost significant traffic vs previous period |
| Quick Wins | Keywords at positions 11-20 with good volume |
| Cannibalization | Multiple pages competing for same keyword |
| Mobile/Desktop Gap | Pages performing differently by device |
| Dead Pages | Pages that dropped to zero traffic |
| Brand vs Non-Brand | Traffic dependency on branded searches |

## Troubleshooting

| Error | Solution |
|-------|----------|
| "GSC tools not found" | MCP server not configured - follow setup guide |
| "No properties found" | Google account lacks Search Console access |
| "gcloud: command not found" | Google Cloud CLI not installed or PATH not set |
| "Authentication error" | Re-run `gcloud auth login` |

For complete troubleshooting, see `references/setup-guide.md` Section 6.

## Uninstalling

To remove the skill:
```bash
# Remove skill folder
rm -rf ~/.claude/skills/gsc-audit/

# Remove MCP server (optional)
rm -rf ~/.claude/mcp-gsc/

# Remove MCP config from .claude/settings.local.json
```

---
Packaged with Claude Code /export-skill

Skill provided by Authority Hacker's AI Accelerator
Learn more: https://www.authorityhacker.com/ai-accelerator/
