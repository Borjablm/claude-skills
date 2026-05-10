# GSC MCP Server Setup Guide

This skill requires the **mcp-gsc** server from [AminForou/mcp-gsc](https://github.com/AminForou/mcp-gsc) - a Python-based MCP server that connects Claude Code to Google Search Console.

## Quick Start (Recommended)

**Step 1: Install the skill**
```bash
/install-skill gsc-audit-v1.0.0.zip
```

**Step 2: Run the MCP setup script**
```bash
cd ~/.claude/skills/gsc-audit
./install.sh
```

**Step 3: Set up OAuth credentials**
Ask Claude: *"Help me set up GSC OAuth credentials"*

That's it! The install script handles all the MCP server configuration correctly.

---

## What Gets Installed

| Component | Purpose | Location |
|-----------|---------|----------|
| Skill files | The audit workflow and logic | `~/.claude/skills/gsc-audit/` |
| mcp-gsc repository | The MCP server code | `~/.claude/mcp-gsc/` |
| Python virtual environment | Isolated dependencies | `~/.claude/mcp-gsc/.venv/` |
| Google Cloud CLI | Creates OAuth credentials | System-wide |
| OAuth credentials | Authenticates with Google | `~/.claude/mcp-gsc/client_secrets.json` |
| MCP configuration | Tells Claude Code how to run the server | `~/.claude.json` |

---

## Choose Your Setup Path

**Automated Setup** (Recommended)
Run the `install.sh` script after installing the skill. It uses `claude mcp add` to configure the server correctly.

**Assisted Wizard**
Ask: *"Help me set up GSC OAuth credentials"*
I'll guide you through creating OAuth credentials in Google Cloud Console.

**Manual Guide**
Jump to [Section 5: Manual Setup Guide](#5-manual-setup-guide) for complete written instructions.

---

## 1. Assisted Wizard: Overview

The wizard walks through 9 steps:

| Step | What Happens | Your Involvement |
|------|--------------|------------------|
| 1 | Check Python & Git | None (automatic) |
| 2 | Clone mcp-gsc repo | None (automatic) |
| 3 | Set up Python environment | None (automatic) |
| 4 | Install Google Cloud CLI | May need to click installer |
| 5 | Google Cloud authentication | Sign in via browser |
| 6 | Create project & enable API | None (automatic) |
| 7 | Configure OAuth consent screen | Manual in browser, type "done" when finished |
| 8 | Create OAuth credentials | Manual in browser, drag & drop JSON file |
| 9 | Configure MCP | None (automatic) |

After completion, restart Claude Code and test with "List my GSC properties".

---

## 2. Assisted Wizard: Detailed Steps

### Step 1: Check Prerequisites (Python + Git)

**Detection Logic:**
```bash
# Check Python
python3 --version   # Try this first
python --version    # Fallback

# Check Git
git --version
```

**Python Installation Matrix:**

| OS | Detection | Install Method | Fallback |
|----|-----------|----------------|----------|
| macOS + Homebrew | `which brew` succeeds | `brew install python@3.12` | Download from python.org |
| macOS (no Homebrew) | `uname -s` = Darwin | Guide to python.org download | Install Homebrew first |
| Windows | Check python/python3 | `winget install Python.Python.3.12` | Download from python.org |
| Linux | `uname -s` = Linux | `sudo apt install python3 python3-venv` | Varies by distro |

**Git Installation:**
- macOS: Usually pre-installed; if not: `brew install git` or Xcode Command Line Tools
- Windows: `winget install Git.Git` or download from git-scm.com
- Linux: `sudo apt install git`

**Troubleshooting:**
- "python: command not found" → Python not installed, guide through installation
- Python version < 3.10 → Need newer version, guide upgrade
- "git: command not found" → Install git before continuing

### Step 2: Clone mcp-gsc Repository

```bash
git clone https://github.com/AminForou/mcp-gsc.git ~/.claude/mcp-gsc
```

**Troubleshooting:**
- Directory already exists → Ask: "Update existing installation (git pull) or start fresh (delete and re-clone)?"
- Clone fails → Check internet connection; try HTTPS explicitly: `git clone https://github.com/...`
- Permission denied → May need to create `~/.claude/` directory first

### Step 3: Set Up Python Environment

```bash
cd ~/.claude/mcp-gsc

# Create virtual environment
python3 -m venv .venv

# Activate and install dependencies
# macOS/Linux:
source .venv/bin/activate

# Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
```

**Troubleshooting:**
- "No module named 'venv'" → Linux needs: `sudo apt install python3-venv`
- "pip: command not found" → Use `python -m pip` instead
- pip install fails → Try `pip install --upgrade pip` first, then retry
- SSL errors → May need to update certificates or use `--trusted-host pypi.org`

### Step 4: Check & Install Google Cloud CLI

**Detection Logic:**
```bash
gcloud --version
```

**OS Installation Matrix:**

| OS | Detection | Install Method | Fallback |
|----|-----------|----------------|----------|
| macOS + Homebrew | `which brew` succeeds | `brew install google-cloud-sdk` | Download tar.gz from cloud.google.com |
| macOS (no Homebrew) | `uname -s` = Darwin | Download tar.gz, extract, run `./install.sh` | Ask user to install manually |
| Windows + winget | `winget --version` succeeds | `winget install Google.CloudSDK` | Download installer from cloud.google.com |
| Windows (no winget) | PowerShell/CMD | Open download page, user types "installed" when done | - |
| Linux | `uname -s` = Linux | `sudo snap install google-cloud-cli --classic` | `curl https://sdk.cloud.google.com | bash` |

**macOS without Homebrew - Manual Steps:**
1. Download: https://cloud.google.com/sdk/docs/install
2. Extract: `tar -xf google-cloud-cli-*.tar.gz`
3. Install: `./google-cloud-sdk/install.sh`
4. Restart terminal or run: `source ~/.zshrc` (or `~/.bashrc`)

**Windows without winget - Manual Steps:**
1. Open: https://cloud.google.com/sdk/docs/install
2. Download the installer
3. Run the installer, follow prompts
4. Type "installed" when complete

**Troubleshooting:**
- "gcloud: command not found" after install → Restart terminal; PATH not updated
- macOS: Run `source "$(brew --prefix)/share/google-cloud-sdk/path.zsh.inc"`
- Windows: Open new PowerShell/CMD window
- Linux: Run `source ~/.bashrc` or log out/in

### Step 5: Google Cloud Authentication

```bash
gcloud auth login
```

This opens your browser. Sign in with the Google account that has Search Console access.

**Troubleshooting:**
- Browser doesn't open → Copy the URL from terminal and paste into browser manually
- Wrong account → Use `gcloud auth login` again and select correct account
- "Access blocked" → The app is in testing mode, this is normal - click "Continue"
- Auth successful but command shows error → Run `gcloud auth login` again

### Step 6: Create Project & Enable API

```bash
# Create project (use a unique suffix)
gcloud projects create gsc-audit-XXXX --name="GSC Audit"

# Set as current project
gcloud config set project gsc-audit-XXXX

# Enable Search Console API
gcloud services enable searchconsole.googleapis.com
```

**Troubleshooting:**
- "Project ID already exists" → Project IDs are global; try a different random suffix (e.g., your initials + numbers)
- "Permission denied" → May need to accept Terms of Service at console.cloud.google.com
- "Billing account required" → Shouldn't happen for Search Console API (it's free); if it does, see billing setup below
- "API not found" → Double-check spelling: `searchconsole.googleapis.com`

**If billing required (rare):**
1. Go to: https://console.cloud.google.com/billing
2. Create billing account (won't be charged for Search Console API)
3. Link it to your project
4. Re-run the enable command

### Step 7: OAuth Consent Screen (Browser - Manual)

Open this URL (replace PROJECT_ID with your actual project ID):
```
https://console.cloud.google.com/apis/credentials/consent?project=PROJECT_ID
```

**Instructions:**
1. Select **"External"** → Click **CREATE**
2. Fill in required fields:
   - App name: `GSC Audit` (or anything)
   - User support email: Select your email
   - Developer contact email: Enter your email
3. Click **SAVE AND CONTINUE**
4. Scopes page: Click **SAVE AND CONTINUE** (leave empty)
5. Test users page: Click **SAVE AND CONTINUE** (leave empty)
6. Summary page: Click **BACK TO DASHBOARD**

**Tell me "done" when finished.**

**Troubleshooting:**
- Don't see "External" option → May already have consent screen configured; try proceeding to credentials
- "You need to verify your app" → Ignore this; only needed for public apps, we're using it personally
- "Add test users" prompt → You can skip this or add your email; either works for personal use
- Page shows "In production" or "Testing" → Either status works; proceed to next step

### Step 8: Create OAuth Credentials (Browser - Manual)

Open this URL:
```
https://console.cloud.google.com/apis/credentials?project=PROJECT_ID
```

**Instructions:**
1. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
2. Application type: **"Desktop app"**
3. Name: `Claude Code` (or anything)
4. Click **CREATE**
5. In the popup, click **"DOWNLOAD JSON"**

**Drag and drop the downloaded JSON file into this chat.**

**Troubleshooting:**
- Don't see "OAuth client ID" option → Consent screen not completed; go back to Step 7
- Download didn't work → On the credentials list, click the download icon (⬇️) next to your credential
- Can't find downloaded file → Check Downloads folder for file named `client_secret_*.json`
- Accidentally closed popup → Find your credential in the list and click the download icon

### Step 9: Configure MCP

After receiving the JSON file, I will:

1. Move it to: `~/.claude/mcp-gsc/client_secrets.json`

2. Add to `.claude/settings.local.json`:

**macOS/Linux:**
```json
{
  "mcpServers": {
    "gsc": {
      "command": "~/.claude/mcp-gsc/.venv/bin/python",
      "args": ["~/.claude/mcp-gsc/gsc_server.py"],
      "env": {
        "GSC_OAUTH_CLIENT_SECRETS_FILE": "~/.claude/mcp-gsc/client_secrets.json"
      }
    }
  }
}
```

**Windows:**
```json
{
  "mcpServers": {
    "gsc": {
      "command": "C:\\Users\\USERNAME\\.claude\\mcp-gsc\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\USERNAME\\.claude\\mcp-gsc\\gsc_server.py"],
      "env": {
        "GSC_OAUTH_CLIENT_SECRETS_FILE": "C:\\Users\\USERNAME\\.claude\\mcp-gsc\\client_secrets.json"
      }
    }
  }
}
```

**Final Step: Restart Claude Code**

MCP configuration changes require a restart. After restarting, test with:
> "List my GSC properties"

The first time you use a GSC tool, a browser will open for OAuth authorization. Sign in and grant access.

---

## 3. Proactive Troubleshooting Framework

During the wizard, watch for these patterns:

| User Signal | Response |
|-------------|----------|
| "error", "failed", "not working" | Ask for exact error message; offer to diagnose |
| Long silence after browser step | Check in: "Were you able to complete that step?" |
| User seems confused | Offer to explain what we're doing and why |
| Command returns non-zero exit | Parse error, explain in plain English, suggest fix |
| User wants to stop | Save progress, explain how to resume later |

**Recovery Prompts:**
- "No worries, this stuff can be tricky. Let me try a different approach..."
- "That error usually means X. Let's fix it by doing Y..."
- "If you're stuck, you can also follow the manual guide instead. Would you prefer that?"

---

## 4. Post-Install Verification

After setup completes:

1. **Restart Claude Code** (required for MCP changes)
2. **Test:** Ask "List my GSC properties"
3. **First use:** A browser will open for OAuth - sign in and authorize
4. **Success:** You should see your Search Console properties listed

**If verification fails:**
- "MCP tools not found" → Check `.claude/settings.local.json` syntax and paths
- "No properties found" → Your Google account may not have Search Console access
- "Authentication error" → Delete `~/.claude/mcp-gsc/token.json` and try again
- Server crashes → Check Python path in config matches your actual venv location

---

## 5. Manual Setup Guide

Complete written instructions for self-service setup.

### Prerequisites

- Google account with Search Console access
- Claude Code installed
- Python 3.10+ installed
- Git installed

### Part A: Install the MCP Server

```bash
# Clone the repository
git clone https://github.com/AminForou/mcp-gsc.git ~/.claude/mcp-gsc

# Set up Python environment
cd ~/.claude/mcp-gsc
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (CMD):
.venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

### Part B: Install Google Cloud CLI

**macOS (with Homebrew):**
```bash
brew install google-cloud-sdk
```

**macOS (without Homebrew):**
1. Download from: https://cloud.google.com/sdk/docs/install
2. Extract: `tar -xf google-cloud-cli-*.tar.gz`
3. Run: `./google-cloud-sdk/install.sh`
4. Restart terminal

**Windows (with winget):**
```powershell
winget install Google.CloudSDK
```

**Windows (without winget):**
1. Download installer from: https://cloud.google.com/sdk/docs/install
2. Run installer, follow prompts
3. Open new terminal window

**Linux:**
```bash
# Snap (recommended)
sudo snap install google-cloud-cli --classic

# Or via apt
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list
sudo apt update && sudo apt install google-cloud-cli
```

### Part C: Create Google Cloud Project

```bash
# Authenticate with Google
gcloud auth login

# Create project (replace YOURNAME with something unique)
gcloud projects create gsc-audit-YOURNAME --name="GSC Audit"

# Set as active project
gcloud config set project gsc-audit-YOURNAME

# Enable Search Console API
gcloud services enable searchconsole.googleapis.com
```

### Part D: Configure OAuth Consent Screen

1. Open: https://console.cloud.google.com/apis/credentials/consent
2. Select **"External"** → Click **CREATE**
3. Fill in:
   - App name: `GSC Audit`
   - User support email: Your email
   - Developer contact email: Your email
4. Click **SAVE AND CONTINUE** through all screens
5. Click **BACK TO DASHBOARD**

### Part E: Create OAuth Credentials

1. Open: https://console.cloud.google.com/apis/credentials
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. Application type: **"Desktop app"**
4. Name: `Claude Code`
5. Click **CREATE**
6. Click **"DOWNLOAD JSON"**
7. Move the downloaded file:
   ```bash
   mv ~/Downloads/client_secret_*.json ~/.claude/mcp-gsc/client_secrets.json
   ```

### Part F: Configure Claude Code

Create or edit `.claude/settings.local.json` in your project directory:

**macOS/Linux:**
```json
{
  "mcpServers": {
    "gsc": {
      "command": "~/.claude/mcp-gsc/.venv/bin/python",
      "args": ["~/.claude/mcp-gsc/gsc_server.py"],
      "env": {
        "GSC_OAUTH_CLIENT_SECRETS_FILE": "~/.claude/mcp-gsc/client_secrets.json"
      }
    }
  }
}
```

**Windows** (replace YOURNAME with your Windows username):
```json
{
  "mcpServers": {
    "gsc": {
      "command": "C:\\Users\\YOURNAME\\.claude\\mcp-gsc\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\YOURNAME\\.claude\\mcp-gsc\\gsc_server.py"],
      "env": {
        "GSC_OAUTH_CLIENT_SECRETS_FILE": "C:\\Users\\YOURNAME\\.claude\\mcp-gsc\\client_secrets.json"
      }
    }
  }
}
```

**Note:** If you already have other MCP servers configured, add the `gsc` entry inside the existing `mcpServers` object.

### Part G: Verify Installation

1. Restart Claude Code
2. Ask: "List my GSC properties"
3. Complete browser authorization when prompted (first time only)
4. You should see your Search Console properties

---

## 6. Troubleshooting Reference

### Installation Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "python: command not found" | Python not installed | Install Python 3.10+ from python.org |
| "python3: command not found" | Python path issue | Try `python` instead, or reinstall Python |
| "git: command not found" | Git not installed | Install via brew/winget/apt |
| "No module named 'venv'" | Missing venv module | Linux: `sudo apt install python3-venv` |
| "pip: command not found" | pip not available | Use `python -m pip` instead |
| Clone fails with 404 | Wrong URL | Verify: `https://github.com/AminForou/mcp-gsc.git` |
| "Permission denied" on clone | SSH key issue | Use HTTPS URL instead of SSH |

### Google Cloud Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "gcloud: command not found" | PATH not configured | Restart terminal; run shell init script |
| "Project ID already exists" | Name taken globally | Use different name with random suffix |
| "Billing account required" | API needs billing | Create billing account (won't be charged) |
| "Permission denied" | ToS not accepted | Visit console.cloud.google.com and accept terms |
| "API not enabled" | Forgot to enable | Run `gcloud services enable searchconsole.googleapis.com` |
| Auth popup blocked | Browser settings | Check popup blocker; copy URL manually |

### OAuth Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "OAuth client ID" not in menu | Consent screen incomplete | Complete consent screen setup first |
| "Invalid client secrets" | Wrong file or path | Verify file exists at `~/.claude/mcp-gsc/client_secrets.json` |
| "Access blocked" during auth | App in testing mode | Normal - click "Continue" or "Advanced" → "Go to app" |
| "redirect_uri_mismatch" | Wrong credential type | Must be "Desktop app", not "Web application" |
| Token expired | Session timeout | Delete `~/.claude/mcp-gsc/token.json`, re-authorize |

### MCP Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "MCP tools not found" | Config not loaded | Restart Claude Code |
| "GSC tools not available" | Config syntax error | Check JSON syntax in settings.local.json |
| "Connection refused" | Server not starting | Verify Python path in config matches venv |
| "ModuleNotFoundError" | Dependencies missing | Re-run `pip install -r requirements.txt` in venv |
| "No such file or directory" | Path issue | Use absolute paths; check `~` expansion on Windows |
| Server starts but no tools | Wrong Python path | Ensure path points to venv Python, not system Python |

### Search Console Issues

| Error | Cause | Solution |
|-------|-------|----------|
| "No properties found" | No GSC access | Verify access at search.google.com/search-console |
| "Forbidden" on property | Insufficient permissions | Need at least "Restricted" access level |
| Wrong properties showing | Wrong Google account | Re-auth with `gcloud auth login` using correct account |
| "Quota exceeded" | Too many API calls | Wait and retry; reduce row_limit in queries |

---

## 7. Resuming Interrupted Setup

If you stopped partway through:

**Know where you stopped?**
- Tell me which step, and we'll continue from there

**Not sure?**
- I'll run quick checks to see what's already done:
  - Check if `~/.claude/mcp-gsc/` exists (Step 2 complete)
  - Check if `.venv/` exists (Step 3 complete)
  - Check if `gcloud` works (Step 4 complete)
  - Check if `client_secrets.json` exists (Step 8 complete)
  - Check if MCP config exists (Step 9 complete)

**Want to start fresh?**
```bash
# Remove everything and start over
rm -rf ~/.claude/mcp-gsc/
# Then delete the "gsc" entry from .claude/settings.local.json
```

---

## 8. Uninstalling

To remove the GSC MCP server:

1. Delete the repository:
   ```bash
   rm -rf ~/.claude/mcp-gsc/
   ```

2. Remove the MCP config entry from `.claude/settings.local.json`

3. Optionally delete the Google Cloud project:
   ```bash
   gcloud projects delete gsc-audit-YOURNAME
   ```

4. Restart Claude Code
