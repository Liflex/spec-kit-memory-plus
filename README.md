<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>Spec Kit</h1>
    <p><strong>Spec-driven development with persistent agent memory</strong></p>
    <p><a href="docs/ru/README.md">Русская версия</a></p>
</div>

---

## The Problem

AI coding agents are stateless. Every session starts from zero — no memory of past bugs, no knowledge of proven patterns, no recall of architecture decisions. Your agent makes the same mistakes, asks the same questions, and rediscovers the same solutions. Over and over.

## The Solution

Spec Kit turns your AI agent into a learning system. Every command in the spec-driven workflow — from writing specifications to implementing code — reads from and writes to a persistent memory layer. The agent accumulates project knowledge across sessions: lessons learned, reusable patterns, architecture decisions. Knowledge is saved immediately when discovered, not at the end of a session that might never finish.

**Memory is not a feature bolted onto the workflow. Memory *is* the workflow.**

---

## How It Works

```
Session 1: /speckit.specify → discovers domain rules → saves to memory
Session 2: /speckit.plan    → reads past lessons → avoids known pitfalls
Session 3: /speckit.tasks   → recalls patterns → generates better task breakdown
Session 4: /speckit.implement → applies architecture knowledge → consistent code
Session 5: bug fix          → learns from mistake → never repeats it
```

Every command follows the same cycle:

1. **Read** memory at the start (lessons, patterns, architecture decisions)
2. **Execute** the task with accumulated context
3. **Write** insights immediately when recognized — don't wait for completion

---

## Memory Architecture

Three levels, each serving a different purpose:

| Level | Storage | Purpose | Overhead |
|-------|---------|---------|----------|
| **Session** | Native context | Current conversation state | None |
| **File** | `.claude/memory/*.md` | Persistent project knowledge | ~1-2% tokens |
| **Vector** | Ollama embeddings | Semantic search across sessions | Optional |

### File Memory (always available)

Three markdown files, auto-created when missing:

| File | Contains | Written when |
|------|----------|-------------|
| `lessons.md` | Bugs fixed, pitfalls discovered, non-obvious rules | Agent encounters a non-trivial problem |
| `patterns.md` | Reusable solutions, proven approaches | A pattern is used successfully 2+ times |
| `architecture.md` | Technical decisions with rationale | Significant design choices are made |

Before writing, the agent scans existing headers to prevent duplicates. Knowledge accumulates cleanly over time.

### Vector Memory (optional, requires Ollama)

Semantic search via `vector_memory.py` CLI. Finds relevant past experience even when keywords don't match. Useful for large projects with hundreds of memory entries. Gracefully disabled when Ollama is not installed — no checks, no prompts, no errors.

---

## Commands

### Core Workflow

The full spec-driven development pipeline. Each command reads memory, executes its task, and saves new insights inline.

| Command | Purpose |
|---------|---------|
| `/speckit.specify` | Create feature specification from natural language |
| `/speckit.clarify` | Ask up to 5 targeted questions to reduce spec ambiguity |
| `/speckit.plan` | Generate architecture and implementation plan |
| `/speckit.tasks` | Break plan into dependency-ordered, actionable tasks |
| `/speckit.analyze` | Cross-artifact consistency analysis (read-only) |
| `/speckit.implement` | Execute all tasks from tasks.md |
| `/speckit.checklist` | Generate requirements quality checklist |
| `/speckit.constitution` | Define project principles and constraints |

### Quick & Combined

| Command | Purpose |
|---------|---------|
| `/speckit.features` | Quick feature for small tasks (< 4 hours) — spec + plan + implement |
| `/speckit.loop` | Quality loop on existing code — iterative evaluate/critique/refine |
| `/speckit.implementloop` | Implement tasks + quality loop in one command |

### Integration

| Command | Purpose |
|---------|---------|
| `/speckit.tobeads` | Import tasks into Beads issue tracker |
| `/speckit.taskstoissues` | Convert tasks to GitHub issues |

---

## Quickstart

### Quick Feature (< 4 hours)

```bash
/speckit.features Fix the login timeout issue on mobile
```

The agent will research the codebase, create a minimal plan, implement the fix, suggest tests, and save what it learned to memory.

### Full Workflow

```bash
# 1. Write the specification
/speckit.specify Build a user authentication system with OAuth2

# 2. Clarify ambiguities (optional but recommended)
/speckit.clarify

# 3. Create architecture plan
/speckit.plan Using Next.js with PostgreSQL

# 4. Generate tasks
/speckit.tasks

# 5. Analyze consistency before implementation (optional)
/speckit.analyze

# 6. Implement
/speckit.implement
```

### Quality Loop

```bash
# Improve existing code quality iteratively
/speckit.loop --criteria code-gen

# Security review
/speckit.loop --criteria security --max-iterations 6

# Combine criteria
/speckit.loop --criteria backend,live-test

# Implement + quality loop in one step
/speckit.implementloop --criteria code-gen --max-iterations 4
```

### Quality Loop Criteria (13 built-in)

| Criteria | Use for |
|----------|---------|
| `api-spec` | API specifications, OpenAPI |
| `code-gen` | Code generation, functions, classes |
| `docs` | Documentation, README, guides |
| `config` | Configuration files, YAML/JSON |
| `database` | Database schemas, SQL, migrations |
| `frontend` | Frontend code, React/Vue/Angular |
| `backend` | Backend services, APIs |
| `infrastructure` | DevOps, Docker, Kubernetes |
| `testing` | Test files, unit/integration tests |
| `security` | Security, auth, XSS/SQLi prevention |
| `performance` | Performance optimization |
| `ui-ux` | UI/UX design, accessibility |
| `live-test` | Real HTTP requests, browser automation, DB verification |

Combine with commas: `--criteria backend,live-test`

---

## Installation

### Via AI Assistant

Tell your AI assistant:

```
Execute the installation instructions from INSTALL.md
```

The assistant will:
- Copy Spec Kit templates and commands
- Configure your editor (Claude Code or Cursor)
- Create memory directory structure
- Optionally set up Ollama for vector search

See [INSTALL.md](INSTALL.md) for detailed editor-specific instructions.

### Supported Editors

| Editor | Support Level |
|--------|-------------|
| **Claude Code** | Full: slash commands, memory, vector search |
| **Cursor** | Rules-based: `.cursor/rules/`, memory, terminal vector search |

---

## Memory in Practice

### What gets saved

Real examples of memory entries the agent creates:

**lessons.md** — after fixing a bug:
```markdown
## PostgreSQL JSONB Index Ignored on Nested Queries

**Date:** 2026-03-10
**Problem:** GIN index on metadata column not used when querying nested keys with @> operator inside a subquery
**Solution:** Rewrite as a JOIN with lateral unnest — index is now hit, query time dropped from 4.2s to 12ms
**Tags:** #postgresql #performance #jsonb
```

**patterns.md** — after discovering a reusable approach:
```markdown
## Optimistic Locking with Version Column

**When to use:** Any entity with concurrent write access from multiple users/services
**How to implement:** Add `version INT DEFAULT 0` column, include `WHERE version = :expected` in UPDATE, handle StaleObjectError with retry
```

**architecture.md** — after a design decision:
```markdown
## Event Sourcing for Audit Trail

**Date:** 2026-03-08
**Context:** Regulatory requirement for complete change history on financial transactions
**Decision:** Event sourcing for transaction aggregate, CQRS with read projections
**Rationale:** Append-only log satisfies audit requirements; projections keep query performance acceptable
```

### How memory flows through the workflow

```
/speckit.specify
  READ:  lessons.md — "Last auth spec missed OAuth refresh token flow"
  WRITE: patterns.md — "Domain rule: all API tokens must have configurable TTL"

/speckit.plan
  READ:  architecture.md — "Project uses event sourcing for audit"
  READ:  patterns.md — "Optimistic locking pattern for concurrent writes"
  WRITE: architecture.md — "Chose Redis for session store over JWT"

/speckit.tasks
  READ:  All three files for comprehensive context
  WRITE: patterns.md — "Task decomposition: always separate migration from seed data"
  WRITE: lessons.md — "Non-obvious: auth middleware must come before rate limiter"

/speckit.implement
  READ:  All three files before each task phase
  WRITE: Deferred to completion (intentional — avoids mid-implementation noise)
```

---

## Performance

| Metric | Value |
|--------|-------|
| Memory read overhead | ~130-280 tokens (headers-first) |
| Local file search | < 200ms |
| Vector semantic search | < 1s |
| Quality loop iteration | < 60s |

---

## Project Structure

```
spec-kit/
  templates/
    commands/         # All slash command templates (12 commands)
    spec-template.md  # Feature specification template
    plan-template.md  # Implementation plan template
    tasks-template.md # Tasks breakdown template
    checklist-template.md
    constitution-template.md
  scripts/
    bash/             # Shell scripts for prerequisites and setup
    powershell/       # PowerShell equivalents for Windows
  docs/               # Documentation
  media/              # Logos and images
  INSTALL.md          # AI-executable installation guide
  CLAUDE.md           # Agent instructions (loaded into every session)
```

---

## License

This project extends [SpecKit](https://github.com/github/spec-kit), licensed under MIT.

---

## Support

- Open an issue in the repository
- See [Installation Guide](INSTALL.md) for setup help
- Check [docs/](docs/) for detailed documentation
