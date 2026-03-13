# Global Agent Memory Integration - Installation Guide

> **AI-Executable Installation Instructions**
> This document is written for execution by AI assistants (Claude Code, Cursor, Windsurf, etc.)
> Last updated: 2026-03-12

---

## 🤖 For AI Agents: Installation vs Update

**Before proceeding, check if this is an initial installation or an update:**

```bash
# Quick check: Is SpecKit already installed?
if [ -d "$HOME/.claude/spec-kit" ]; then
    echo "⚠️  SpecKit is already installed. This is likely an UPDATE request."
    echo ""
    echo "As an AI agent, you should:"
    echo "  1. Inform the user that this appears to be an update"
    echo "  2. Ask for confirmation before proceeding"
    echo "  3. If confirmed, re-run the installation steps to:"
    echo "     - Update spec-kit/ directory with latest templates"
    echo "     - Update commands/ (speckit.*.md) with latest versions"
    echo "     - Update scripts/ with latest tools"
    echo "     - Preserve existing memory, configs, and user data"
    echo "  4. All existing backups will be preserved"
    echo ""
    read -p "Proceed with updating SpecKit? (y/n): " update_confirm
    if [ "$update_confirm" != "y" ]; then
        echo "Update cancelled. Installation instructions remain available for reference."
        exit 0
    fi
    echo ""
    echo "=== Running SpecKit Update ==="
else
    echo "=== New Installation ==="
fi
```

**Key differences between installation and update:**

| Action | Installation | Update |
|--------|--------------|--------|
| spec-kit/ | Copy from repository | Re-copy from repository |
| commands/ | Create new | Overwrite with latest |
| memory/ | Create new structure | Preserve existing data |
| CLAUDE.md | Add memory section | Preserve (don't duplicate) |
| Backup | Create `.backup.*` | Create new backup timestamp |

---

---

## Supported AI Editors

| Editor | Instructions file | Commands | Notes |
|--------|------------------|----------|-------|
| **Claude Code** | `~/.claude/CLAUDE.md` | `~/.claude/commands/speckit.*.md` | Full support: slash commands, memory, vector search |
| **Cursor** | `.cursorrules` or `.cursor/rules/*.mdc` | No native commands — use rules + @-mentions | Memory via file rules, vector via terminal |

---

## Prerequisites Check

Before installation, verify:

1. **Operating System**: Windows 11, Linux, or macOS
2. **Git installed**: Run `git --version`
3. **Python 3.11+**: Run `python --version`
4. **SpecKit repository**: Cloned locally (e.g. `F:\IdeaProjects\spec-kit`)
5. **Write permissions**: Access to home config directory
6. **requests library**: Run `python -m pip install requests` (required for vector memory)

**If any prerequisite is missing, install it first before proceeding.**

---

## Installation Steps

### Step 1: Prepare Target Directory

```bash
# For Claude Code
mkdir -p "$HOME/.claude"
cd "$HOME/.claude"

# For Cursor — no global config dir needed,
# rules live in project root or ~/.cursor/rules/
```

### Step 2: Backup Existing Configurations

```bash
# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".backup.$TIMESTAMP"
mkdir -p "$BACKUP_DIR"

# Backup existing configs if they exist
if [ -f "config.json" ]; then cp config.json "$BACKUP_DIR/"; fi
if [ -d "memory" ]; then cp -r memory "$BACKUP_DIR/"; fi
if [ -d "skills" ]; then cp -r skills "$BACKUP_DIR/"; fi
if [ -d "spec-kit" ]; then cp -r spec-kit "$BACKUP_DIR/"; fi

echo "Backup created: $BACKUP_DIR"
```

### Step 3: Create Directory Structure

```bash
# Create memory directories
mkdir -p memory/projects
mkdir -p memory/backups
mkdir -p memory/vector

# Create skills directory
mkdir -p skills

echo "Directory structure created"
```

### Step 4: Copy SpecKit Repository

```bash
# Remove existing if present
if [ -d "spec-kit" ]; then rm -rf spec-kit; fi

# Copy SpecKit repository
cp -r "F:/IdeaProjects/spec-kit" spec-kit
```

> After pulling updates to spec-kit, re-run this step to sync.

### Step 5: Create Project Config Template

```bash
# Create .spec-kit directory
mkdir -p .spec-kit

# Create project config template
cat > .spec-kit/project.json << 'EOF'
{
  "project_id": "",
  "project_name": "",
  "memory_enabled": true,
  "created_at": ""
}
EOF

echo "Project config template created"
```

### Step 6: Optional - Install Ollama

**Option A: Native Installation**

```bash
# Check if Ollama is installed
if command -v ollama &> /dev/null; then
    echo "Ollama already installed: $(ollama --version)"
else
    echo "Ollama not found. Install?"
    read -p "Install Ollama now? (y/n): " install_ollama

    if [ "$install_ollama" = "y" ]; then
        # Install Ollama (Linux/macOS)
        curl -fsSL https://ollama.com/install.sh | sh

        # For Windows: download from https://ollama.com/download
        echo "Ollama installed. Please restart terminal and verify with: ollama --version"
    fi
fi
```

**Option B: Docker Compose (Recommended for Windows)**

> **Advantages**: Isolated environment, easy updates, consistent behavior across platforms

```bash
# 1. Create docker projects directory
mkdir -p "$HOME/.claude/projects/docker"
cd "$HOME/.claude/projects/docker"

# 2. Copy docker-compose file (already created in: ~/.claude/projects/docker/ollama-docker-compose.yml)
# The file includes:
# - ollama/ollama:latest image
# - Persistent volume for models
# - Health checks
# - Auto-restart on failure

# 3. Start Ollama container
docker-compose -f ollama-docker-compose.yml up -d

# 4. Wait for container to be ready (check health)
docker-compose -f ollama-docker-compose.yml ps

# 5. Pull embedding model
docker exec -it ollama ollama pull mxbai-embed-large

# 6. Verify model
docker exec ollama ollama list | grep mxbai-embed-large

# 7. Test embedding
docker exec ollama ollama embed mxbai-embed-large "test" | head -c 50
```

**Using the setup script (simpler):**

```bash
# All-in-one script for Docker Ollama management
cd "$HOME/.claude/projects/docker"
bash ollama-setup.sh start   # Start container
bash ollama-setup.sh pull    # Pull model
bash ollama-setup.sh status  # Check status
bash ollama-setup.sh stop    # Stop container
```

**Pull embedding model (after Ollama is running):**

```bash
# Native installation
if command -v ollama &> /dev/null; then
    echo "Pulling mxbai-embed-large model..."
    ollama pull mxbai-embed-large

    # Verify model
    echo "Testing embedding generation..."
    ollama embed mxbai-embed-large "test" | head -c 50

    echo "mxbai-embed-large ready"
fi

# Docker installation
if docker ps --format '{{.Names}}' | grep -q "^ollama$"; then
    echo "Pulling mxbai-embed-large model..."
    docker exec -it ollama ollama pull mxbai-embed-large

    # Verify model
    echo "Testing embedding generation..."
    docker exec ollama ollama embed mxbai-embed-large "test" | head -c 50

    echo "mxbai-embed-large ready"
fi
```

### Step 7: Optional - Setup SkillsMP API Key

> **SkillsMP provides access to 425K+ agent skills from the community.**
>
> This step is **optional**. Without an API key, the system will use GitHub fallback search.

```bash
# Navigate to .claude directory
cd "$HOME/.claude"

# Run SkillsMP API key setup
python spec-kit/scripts/memory/setup_skillsmp_key.py
```

**What the script does:**

1. **Prompts for API key** (optional - press Enter to skip)
2. **Validates format** (checks for `sk_live_*` or `sk_test_*` prefix)
3. **Tests API key** with a real search request
4. **Stores securely** using system keyring or encrypted file

**Get your API key:** https://skillsmp.com/docs/api

**If skipped:**
- GitHub fallback will be used for skill search
- You can add API key later by running the script again

**Verification:**

After setup, verify SkillsMP status:

```python
# Test from Python
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration

integration = SkillsMPIntegration()
status = integration.get_status()

print(f"SkillsMP configured: {status['skillsmp']['configured']}")
print(f"API key stored: {status['skillsmp']['api_key_stored']}")

# Test search
results = integration.search_skills("react development", limit=3)
for r in results:
    print(f"  - {r.get('title', 'N/A')}")
```

---

### Step 8: Verify Installation

```bash
echo "=== Installation Verification ==="

# Check spec-kit directory
if [ -d "spec-kit" ]; then
    echo "OK: SpecKit copied"
else
    echo "FAIL: SpecKit not found"
fi

# Check directories
if [ -d "memory/projects" ]; then
    echo "OK: Memory directory exists"
else
    echo "FAIL: Memory directory missing"
fi

if [ -d "memory/vector" ]; then
    echo "OK: Vector memory directory exists"
else
    echo "FAIL: Vector memory directory missing"
fi

if [ -d "skills" ]; then
    echo "OK: Skills directory exists"
else
    echo "FAIL: Skills directory missing"
fi

# Check config template
if [ -f ".spec-kit/project.json" ]; then
    echo "OK: Project config template exists"
else
    echo "FAIL: Project config template missing"
fi

# Check Python + requests
if python -c "import requests" 2>/dev/null; then
    echo "OK: Python requests library available"
else
    echo "WARN: requests not installed. Run: python -m pip install requests"
fi

# Check Ollama (optional)
OLLAMA_FOUND=false

# Check native installation
if command -v ollama &> /dev/null; then
    echo "OK: Ollama installed: $(ollama --version)"
    OLLAMA_FOUND=true
    if ollama list 2>/dev/null | grep -q "mxbai-embed-large"; then
        echo "OK: mxbai-embed-large model available (native)"
    else
        echo "WARN: mxbai-embed-large not found. Run: ollama pull mxbai-embed-large"
    fi
fi

# Check Docker installation
if command -v docker &> /dev/null; then
    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^ollama$"; then
        echo "OK: Ollama running in Docker container"
        OLLAMA_FOUND=true
        if docker exec ollama ollama list 2>/dev/null | grep -q "mxbai-embed-large"; then
            echo "OK: mxbai-embed-large model available (Docker)"
        else
            echo "WARN: mxbai-embed-large not found in Docker. Run: docker exec -it ollama ollama pull mxbai-embed-large"
        fi
    fi
fi

if [ "$OLLAMA_FOUND" = false ]; then
    echo "WARN: Ollama not installed (optional)"
    echo "  Install natively: https://ollama.com/download"
    echo "  Install via Docker: See Step 6B in INSTALL.md"
fi

# Check SkillsMP (optional - requires Python)
if command -v python &> /dev/null; then
    # Try to check SkillsMP status
    if python -c "from specify_cli.memory.skillsmp.integration import SkillsMPIntegration; i = SkillsMPIntegration(); print('OK' if i.has_api_key() else 'WARN')" 2>/dev/null | grep -q "OK"; then
        echo "OK: SkillsMP API key configured"
    else
        echo "WARN: SkillsMP API key not configured (optional)"
        echo "  Setup later: python ~/.claude/spec-kit/scripts/memory/setup_skillsmp_key.py"
    fi
fi

echo "=== Verification Complete ==="
```

### Step 9: Install Vector Memory Tool (Level 3)

> **Requires**: Ollama running with `mxbai-embed-large` model (Step 6)

```bash
# Create scripts directory
mkdir -p "$HOME/.claude/scripts"

# Copy vector memory CLI tool
cp spec-kit/scripts/memory/vector_memory.py "$HOME/.claude/scripts/vector_memory.py"

# Ensure requests is installed
python -m pip install requests 2>/dev/null || echo "WARN: pip not available, install requests manually"

# Verify installation
python "$HOME/.claude/scripts/vector_memory.py" status
```

**Expected output:**
```json
{
  "ollama": true,
  "model": true,
  "entries": 0,
  "store_path": "~/.claude/memory/vector/embeddings.json"
}
```

**If `ollama: false`**: Start Ollama/Docker first (see Step 6).
**If `model: false`**: Pull the model: `ollama pull mxbai-embed-large` or `docker exec ollama ollama pull mxbai-embed-large`

**Usage (Claude will call these automatically per CLAUDE.md instructions):**
```bash
# Store a memory entry
python ~/.claude/scripts/vector_memory.py store \
  --content "lesson or pattern text" \
  --type episodic \
  --project "my-project"

# Semantic search
python ~/.claude/scripts/vector_memory.py search \
  --query "search query" \
  --limit 5

# Re-index file memory (lessons.md, patterns.md) into vector store
python ~/.claude/scripts/vector_memory.py reindex --project "my-project"
```

### Step 10: Configure Agent Instructions (CRITICAL)

This step differs by editor. The memory system instructions must be injected into the AI agent's system prompt.

> **🤔 Important Decision**
>
> SpecKit proposes not just a set of commands, but a **global memory system** that enhances ALL AI assistant interactions — not just SpecKit commands.
>
> **What this means:**
> - Your AI assistant will remember lessons, patterns, and architecture decisions across ALL sessions
> - Memory is read at the start of ANY significant task (bug fixes, refactors, features)
> - Insights are saved immediately when discovered — not waiting for task completion
> - Works with your existing workflow, commands, and conversations
>
> **Your choice:**
> - ✅ **Install** — Inject memory instructions into your global config (recommended)
> - ❌ **Skip** — SpecKit commands will work, but without cross-session memory

---

#### Step 10a: Claude Code

**Option 1: Interactive Installation (Recommended)**

The AI assistant will ask for your consent before modifying your global config:

```bash
cd "$HOME/.claude"

# Check if CLAUDE.md exists
if [ -f "CLAUDE.md" ]; then
    echo "=== Global Memory Integration ==="
    echo ""
    echo "SpecKit offers to add a global memory system to your AI assistant."
    echo "This will enhance ALL commands and conversations, not just SpecKit."
    echo ""
    echo "What will be added to ~/.claude/CLAUDE.md:"
    echo "  - 3-level memory system (Session + File + Vector)"
    echo "  - Auto-creation of memory files (lessons.md, patterns.md, architecture.md)"
    echo "  - Memory read/write rules for all tasks"
    echo "  - Optional vector search via Ollama"
    echo ""
    echo "Your existing CLAUDE.md will be preserved. Memory instructions will be appended."
    echo ""
    read -p "Add global memory system to your AI assistant? (y/n): " consent

    if [ "$consent" != "y" ]; then
        echo ""
        echo "⚠️  Skipped: Global memory integration"
        echo ""
        echo "SpecKit commands will still work, but:"
        echo "  - Memory will NOT be available for non-SpecKit tasks"
        echo "  - Each session starts without past context"
        echo "  - You can add memory later by re-running Step 10a"
        echo ""
        read -p "Continue installation without memory? (y/n): " continue_install
        if [ "$continue_install" != "y" ]; then
            echo "Installation cancelled. Add memory later when ready."
            exit 0
        fi
    else
        # Backup existing CLAUDE.md
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        cp CLAUDE.md "CLAUDE.md.backup.$TIMESTAMP"
        echo "✓ Backed up existing CLAUDE.md"

        # Append memory system instructions
        cat >> CLAUDE.md << 'MEMORY_EOF'

## Global Agent Memory System

### Overview

You have a 3-level memory system. Use it to accumulate knowledge across sessions and projects.

**Memory levels:**
- **Level 1 (Session)**: Your natural conversation context — no action needed
- **Level 2 (File)**: Markdown files in `.claude/memory/` — read/write directly
- **Level 3 (Vector)**: Semantic search via embeddings — use `vector_memory.py` CLI tool

**Memory locations:**
- **Project memory**: `.claude/memory/` in each project root (lessons, patterns, architecture for THIS project)
- **Global memory**: `~/.claude/memory/projects/{project-id}/` (cross-project knowledge)

### Level 2: File Memory

| File | Purpose | When to write |
|------|---------|---------------|
| `lessons.md` | Bugs fixed, mistakes learned from | After fixing a non-trivial bug or error |
| `patterns.md` | Reusable solutions, proven approaches | When discovering a pattern used 2+ times |
| `architecture.md` | Key technical decisions, rationale | After significant architecture choices |

**Auto-Create Rule:** If a memory file does not exist when you need to write to it — create it with a proper header:
```markdown
# {Type}: {Project Name}

> Auto-created by Claude Agent Memory
> Project: {project path}

---
```

### Level 3: Vector Memory (Semantic Search)

**Tool:** `python ~/.claude/scripts/vector_memory.py`

**Commands:**
```bash
# Check status (Ollama, model, entries count)
python ~/.claude/scripts/vector_memory.py status

# Store important insight immediately when discovered
python ~/.claude/scripts/vector_memory.py store \
  --content "Description of lesson/pattern/decision" \
  --type episodic|procedural|semantic \
  --project "project-name" \
  --tags "tag1,tag2"

# Search before starting a task (semantic similarity)
python ~/.claude/scripts/vector_memory.py search \
  --query "relevant question" \
  --limit 5 \
  --project "project-name"

# Re-index file memory into vector store (after manual edits)
python ~/.claude/scripts/vector_memory.py reindex --project "project-name"
```

**Memory types:**
- `episodic` — bugs, incidents, lessons learned (what happened)
- `procedural` — patterns, how-tos, solutions (how to do)
- `semantic` — architecture decisions, domain knowledge (what is)

**When to use vector search:**
- When file memory (Level 2) has many entries and keyword search is insufficient
- When looking for similar past experiences across projects
- When the query is conceptual, not exact (e.g., "performance issues with database" vs "PostgreSQL index")

### When to READ memory (beginning of work)

At the START of any significant task (feature, bug fix, refactoring):

1. Check if `.claude/memory/` directory exists in the project
   - **If missing**: create it immediately along with stub files (`lessons.md`, `patterns.md`, `architecture.md`) using the Auto-Create header template. Then skip reading (files are empty).
   - **If exists**: read all `.md` files in it — scan headers for relevant context
2. If Ollama is available and vector store has entries — run semantic search for the task topic
3. Apply relevant knowledge to the current task silently (don't dump the full memory to user)

### When to WRITE memory (immediately, as discovered)

Do NOT wait for task completion — the session may end at any moment. Save important knowledge **as soon as you recognize it**:

- **Found a non-obvious bug or pitfall?** Immediately append to `lessons.md`
- **Discovered a reusable pattern?** Immediately append to `patterns.md`
- **Made or encountered an architecture decision?** Immediately append to `architecture.md`
- **High-importance insights** (cross-project relevance, major architecture decisions, reusable cross-project patterns) — also store in vector memory via `vector_memory.py`. If Ollama is not configured for this session — skip entirely, do not check or ask.

**Trigger:** Save right after the insight occurs (e.g., after fixing a bug, after resolving an ambiguity, after choosing a technical approach) — not at the end of the session.

**Exception:** `/speckit.implement` uses deferred writes (after all tasks complete) because implementation is a long multi-step process where interrupting to write memory mid-task can break execution flow. This is an intentional design choice.

**Format for file memory entries:**
```markdown
## {Title}

**Date:** {YYYY-MM-DD}
**Type:** {Bug Fix | Pattern | Architecture | Lesson}

**Problem/Context:**
{What happened or what situation this applies to}

**Solution/Decision:**
{What was done and why}

**Tags:** {#tag1} {#tag2} {#tag3}
```

### Deduplication Rule

Before appending to any memory file, **scan existing `##` headers** for similar entries. If a similar insight already exists — update it instead of creating a duplicate. Compare by topic, not exact wording.

### Importance Threshold

Not everything should be saved. Write to memory ONLY when:
- The bug took more than a trivial fix (non-obvious root cause)
- The pattern is reusable across tasks (not a one-off hack)
- The decision affects future development (not a cosmetic choice)

### Memory Health-Check

At the START of the first task in a session, silently run a quick diagnostic:

1. **Ollama check** (for vector memory): check if `vector_memory.py` script exists at `~/.claude/scripts/vector_memory.py`
   - If script does NOT exist: Ollama is not configured. Set `vector_memory = disabled` for this session. Do NOT attempt any vector operations, do not check Ollama, do not ask the user.
   - If script exists: run `python ~/.claude/scripts/vector_memory.py status` to check Ollama and model availability.
     - If Ollama is NOT responding: inform user once — "Ollama not running. Vector memory disabled for this session." Do not repeat.
     - If responding: note entries count; if 0 and file memory has entries, suggest once: "Run reindex to sync file memory to vector store."
2. **Memory directory check**: Verify `.claude/memory/` exists in current project
   - If missing: **create immediately** — the directory and all three stub files (`lessons.md`, `patterns.md`, `architecture.md`) with Auto-Create headers. This prevents repeated "file not found" errors during reads.

**Show health warning ONCE per session, not on every command.**
MEMORY_EOF

        echo "✓ Global memory system added to CLAUDE.md"
        echo "✓ Your AI assistant will now remember across all sessions"
    fi
else
    # Create new CLAUDE.md with memory system
    cat > CLAUDE.md << 'CLAUDE_EOF'
# Claude Code Configuration

[Add your custom rules here]

## Global Agent Memory System

[Full memory system instructions will be added here]

See: ~/.claude/spec-kit/CLAUDE.md for reference
CLAUDE_EOF

    echo "Created new CLAUDE.md (add your custom rules at the top)"
fi
```

**Option 2: Manual Installation**

If you prefer to add memory instructions manually, see the reference file:
```bash
cat ~/.claude/spec-kit/CLAUDE.md
```

Copy the **Global Agent Memory System** section to your `~/.claude/CLAUDE.md`.

**The section must include these key components:**

1. **3-level memory** (Session context, File memory, Vector memory via `vector_memory.py`)
2. **Level 2 (File)**: read/write `lessons.md`, `patterns.md`, `architecture.md` in `.claude/memory/`
3. **Level 3 (Vector)**: call `python ~/.claude/scripts/vector_memory.py` for semantic store/search
4. **Auto-Create Rule**: create memory files with headers when missing
5. **When to READ**: at task start -- check directory, create stubs if missing, read headers + vector search
6. **When to WRITE**: immediately as discovered -- dual write to file memory + vector store (do not wait for task completion)
7. **Importance Threshold**: only non-trivial, reusable insights
8. **Health-Check**: Ollama + vector status at session start, warn user once if unavailable

**Verification:**
```bash
grep -c "vector_memory.py" ~/.claude/CLAUDE.md
# Expected: 3 or more
grep -c "Memory Health-Check" ~/.claude/CLAUDE.md
# Expected: 1
```

---

#### Step 10b: Cursor

Cursor uses a different rules system. There are two levels:

**1. Global rules** (apply to all projects):
- Open Cursor Settings > General > Rules for AI
- Paste the memory system instructions there (same content as CLAUDE.md section)

**2. Project rules** (per-project, version-controlled):
- Create `.cursor/rules/memory.mdc` in your project root

```bash
mkdir -p .cursor/rules
```

Create `.cursor/rules/memory.mdc` with the following content:

````markdown
---
description: Global Agent Memory System for cross-session knowledge accumulation
globs:
alwaysApply: true
---

# Agent Memory System

You have a 3-level memory system. Use it to accumulate knowledge across sessions.

## Memory levels

- **Level 1 (Session)**: Your natural conversation context -- no action needed
- **Level 2 (File)**: Markdown files in `.claude/memory/` -- read/write directly
- **Level 3 (Vector)**: Semantic search via embeddings -- use `vector_memory.py` CLI tool

## Memory locations

- **Project memory**: `.claude/memory/` in project root
- **Global memory**: `~/.claude/memory/projects/{project-id}/`

## Level 2: File Memory

| File | Purpose | When to write |
|------|---------|---------------|
| `lessons.md` | Bugs fixed, mistakes learned from | After fixing a non-trivial bug |
| `patterns.md` | Reusable solutions, proven approaches | When discovering a reusable pattern |
| `architecture.md` | Key technical decisions, rationale | After significant architecture choices |

**Auto-Create Rule:** If a memory file does not exist when you need to write to it, create it with:

```markdown
# {Type}: {Project Name}
> Auto-created by Agent Memory
> Project: {project path}
---
```

## Level 3: Vector Memory

**Tool:** Run in terminal: `python ~/.claude/scripts/vector_memory.py`

Commands:
```bash
# Status check
python ~/.claude/scripts/vector_memory.py status

# Store insight
python ~/.claude/scripts/vector_memory.py store \
  --content "Description" --type episodic --project "project-name"

# Semantic search
python ~/.claude/scripts/vector_memory.py search \
  --query "question" --limit 5

# Re-index file memory
python ~/.claude/scripts/vector_memory.py reindex --project "project-name"
```

Memory types: `episodic` (bugs/lessons), `procedural` (patterns/how-tos), `semantic` (architecture/domain knowledge).

## When to READ memory

At the START of any significant task:
1. Check if `.claude/memory/` directory exists
   - **If missing**: create it with stub files (`lessons.md`, `patterns.md`, `architecture.md`) using Auto-Create headers, then skip reading
   - **If exists**: read all `.md` files -- scan headers for relevant context
2. If Ollama is configured and vector memory has entries -- run semantic search for the task topic. If not configured -- skip entirely, do not check or ask.
3. Apply relevant knowledge silently

## When to WRITE memory (immediately, as discovered)

Do NOT wait for task completion -- the session may end at any moment. Save important knowledge as soon as you recognize it:
- **Bug fix?** -> immediately append to `lessons.md`
- **New pattern?** -> immediately append to `patterns.md`
- **Architecture decision?** -> immediately append to `architecture.md`
- For high-importance insights (cross-project relevance, major decisions) -- also store in vector memory via `vector_memory.py`. If Ollama is not configured -- skip entirely.

## Importance Threshold

Only save when:
- Bug had non-obvious root cause
- Pattern is reusable across tasks
- Decision affects future development
````

**Cursor-specific differences from Claude Code:**

| Feature | Claude Code | Cursor |
|---------|------------|--------|
| Instructions file | `~/.claude/CLAUDE.md` | Settings > Rules + `.cursor/rules/*.mdc` |
| Slash commands | `~/.claude/commands/speckit.*.md` | Not supported natively -- use Notepad commands or @-file references |
| Terminal access | Built-in Bash tool | Built-in terminal (Composer agent mode) |
| File operations | Dedicated Read/Edit/Write tools | Built-in file tools |
| Memory read | Automatic at task start | Must reference `.claude/memory/` files via rules |
| Vector memory | Runs via Bash tool | Runs via terminal in agent mode |

**Cursor: Workaround for slash commands**

Cursor doesn't have Claude Code's `/command` system. Instead:

1. **Use @-file references**: Tell Cursor to read `@.claude/commands/speckit.specify.md` as a prompt
2. **Notepad commands**: Save SpecKit prompts as Cursor Notepad entries, then reference them with `@notepad-name`
3. **Composer custom instructions**: Add frequently used commands to Composer rules

---

### Step 11: Update SpecKit Commands (Claude Code only)

> **IMPORTANT**: Always keep SpecKit commands synchronized with the latest version!
> Cursor users: skip this step, see Step 10b for alternatives.

```bash
# Navigate to .claude directory
cd "$HOME/.claude"

# Backup existing commands before updating
BACKUP_TS=$(date +%Y%m%d_%H%M%S)
mkdir -p "commands/.backup.$BACKUP_TS"
cp commands/speckit.*.md "commands/.backup.$BACKUP_TS/" 2>/dev/null

# Update ALL commands from latest SpecKit templates
for cmd in spec-kit/templates/commands/*.md; do
  BASENAME=$(basename "$cmd" .md)
  cp "$cmd" "commands/speckit.$BASENAME.md"
  echo "OK: Updated speckit.$BASENAME.md"
done

# Preserve custom commands not in templates (e.g., tobeads.md, push.md)
echo "Custom commands preserved (not overwritten)"

echo "=== Commands updated ==="
ls -la commands/speckit.*.md
```

**Why this is necessary:**

- SpecKit commands receive regular updates and bug fixes
- Outdated commands may use deprecated APIs or incorrect workflows
- Updates are safe -- they only replace command definitions, not your data

**When to update:**

- After initial installation
- After pulling changes to the SpecKit repository
- If speckit commands behave unexpectedly
- Before starting new features (recommended weekly)

---

## Update Existing Installation

When updating an existing installation:

1. **Check current version**: Read `.spec-kit/version.json`
2. **Create backup**: Automatic backup before update
3. **Apply delta changes**: Only new/modified files
4. **Preserve user data**: memory, configs remain intact
5. **Verify**: Run verification steps

```bash
# Update command
cd "$HOME/.claude"
bash spec-kit/.specify/scripts/install/update.sh
```

---

## Troubleshooting

### Issue: spec-kit copy fails or is outdated

**Solution**: Re-copy from source repository:

```bash
cd "$HOME/.claude"
rm -rf spec-kit
cp -r "F:/IdeaProjects/spec-kit" spec-kit
```

### Issue: `pip` not found

**Solution**: Use `python -m pip` instead:

```bash
python -m pip install requests
```

### Issue: Ollama not accessible

**Native installation**:

```bash
# Linux/macOS
ollama serve

# Windows: Ollama runs as background service
# Check Task Manager for "ollama-app"
```

**Docker installation**:

```bash
# Check container status
docker ps | grep ollama

# Check logs
docker logs ollama

# Restart container
docker-compose -f ~/.claude/projects/docker/ollama-docker-compose.yml restart

# Access shell
docker exec -it ollama sh
```

### Issue: Docker Ollama fails to start

**Solution**: Check Docker Desktop is running:

```bash
# Verify Docker is available
docker info

# Check port conflicts (11434)
netstat -an | grep 11434  # Linux/macOS
netstat -an | findstr 11434  # Windows

# If port is in use, stop conflicting service or change port in docker-compose.yml
```

### Issue: Permission denied

**Solution**: Ensure write permissions to home directory:

```bash
# Fix permissions
chmod +w "$HOME/.claude"
```

### Issue: Conflicts during merge

**Solution**: Review backup and manually resolve:

```bash
# List backups
ls -la .backup.*

# Restore from backup if needed
cp -r .backup.TIMESTAMP/memory/* memory/
```

### Issue: Cursor doesn't pick up .cursor/rules/*.mdc

**Solution**:
- Ensure `alwaysApply: true` is in the YAML frontmatter
- Restart Cursor after adding new rule files
- Check that the file extension is `.mdc` (not `.md`)

---

## Rollback

If installation fails:

```bash
cd "$HOME/.claude"

# Find latest backup
LATEST_BACKUP=$(ls -td .backup.* | head -1)

# Restore from backup
cp -r $LATEST_BACKUP/* .

echo "Rolled back to $LATEST_BACKUP"
```

---

## Next Steps

After successful installation:

1. **Initialize project memory**: Run `.spec-kit/scripts/init-memory.sh` in your project
2. **Test vector memory**: `python ~/.claude/scripts/vector_memory.py status`
3. **Try /speckit.features** (Claude Code) or reference `@.claude/commands/speckit.features.md` (Cursor)
4. **Read project README**: For unique features

---

## Support

- **Original SpecKit**: https://github.com/github/spec-kit
- **Issue Tracker**: Report issues in project repository
- **Documentation**: See README.md for feature overview

---

*Installation Guide v5.0 - AI-Executable, Multi-Editor*
*Compatible with: Claude Code, Cursor | Ollama (Native & Docker) | Vector Memory CLI*
*Memory levels: Session (native) | File (markdown) | Vector (Ollama embeddings)*
