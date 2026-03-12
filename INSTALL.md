# Global Agent Memory Integration - Installation Guide

> **AI-Executable Installation Instructions**
> This document is written for execution by AI assistants (Claude Code, Cursor, Windsurf, etc.)
> Last updated: 2026-03-12

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

---

#### Step 10a: Claude Code

Copy the full **Global Agent Memory System** section into `~/.claude/CLAUDE.md` (create the file if it doesn't exist). This goes **after any existing rules**.

**The section must include these key components:**

1. **3-level memory** (Session context, File memory, Vector memory via `vector_memory.py`)
2. **Level 2 (File)**: read/write `lessons.md`, `patterns.md`, `architecture.md` in `.claude/memory/`
3. **Level 3 (Vector)**: call `python ~/.claude/scripts/vector_memory.py` for semantic store/search
4. **Auto-Create Rule**: create memory files with headers when missing
5. **When to READ**: at task start -- check file memory headers + vector search
6. **When to WRITE**: at task end -- dual write to file memory + vector store
7. **Importance Threshold**: only non-trivial, reusable insights
8. **Health-Check**: Ollama + vector status at session start, warn user once if unavailable

**Reference file**: After installation, the full prompt is in `~/.claude/CLAUDE.md`.

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
1. Check `.claude/memory/lessons.md` -- read headers
2. Check `.claude/memory/patterns.md` -- read headers
3. Check `.claude/memory/architecture.md` -- read headers
4. If vector store has entries -- run semantic search for the task topic
5. Apply relevant knowledge silently

## When to WRITE memory

After completing a task:
- **Bug fix?** -> `lessons.md` + vector store (type=episodic)
- **New pattern?** -> `patterns.md` + vector store (type=procedural)
- **Architecture decision?** -> `architecture.md` + vector store (type=semantic)

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
