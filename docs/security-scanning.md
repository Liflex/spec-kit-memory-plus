# Security Scanning Documentation

**Feature**: Two-Level Security Scanning
**Version**: 0.1.0
**Date**: 2025-03-11

---

## Overview

SpecKit включает двухуровневую систему security scanning для защиты от вредоносных скиллов и агентов:

- **Level 1**: Python статический сканер (из ai-factory)
- **Level 2**: LLM семантический обзор

**Inspired by**: [ai-factory security.md](https://github.com/github/ai-factory)

---

## Architecture

### Components

```
src/specify_cli/security/
├── models.py          # SecurityReport, Threat models
├── scanner.py         # SecurityScanner (Level 1 wrapper)
├── llm_review.py      # LLMSecurityReviewer (Level 2)
├── skillsmp_hooks.py  # SkillsMP integration hooks
└── agent_hooks.py     # Agent creation hooks
```

### Scan Flow

```
┌──────────────┐
│ Skill/Agent  │
└──────┬───────┘
       │
       ▼
┌─────────────────────┐
│ Level 1: Scanner    │ ← Python static analysis
│  (security-scan.py) │
└──────┬──────────────┘
       │
       ├── CLEAN ──────► SAFE ✅
       │
       ├── BLOCKED ────► BLOCKED 🚫
       │
       └── WARNING ────► Level 2 Review
                            │
                            ▼
                      ┌─────────────┐
                      │ Level 2: LLM │
                      │   Review     │
                      └──────┬──────┘
                             │
                             ├── Safe ──► SAFE ✅
                             │
                             └── Unsafe ─► BLOCKED 🚫
```

---

## Threat Patterns

### Level 1: Static Patterns

| Category | Patterns |
|----------|----------|
| **Prompt Injection** | "ignore previous", "override instructions", "bypass security" |
| **Data Exfiltration** | "curl ~/.ssh", "cat ~/.aws", "export credentials" |
| **Stealth** | "don't tell user", "hide from logs", "silent execution" |
| **Destructive** | "rm -rf", "del /Q", "format", "drop table" |
| **Config Tampering** | Modify .bashrc, .ssh/, system files |
| **Encoded Payloads** | base64, hex encoded commands |

### Level 2: Semantic Patterns

| Category | Detection |
|----------|----------|
| **Intent Mismatch** | Role doesn't match instructions |
| **Contextual Threats** | Seemingly safe commands in malicious context |
| **Authority Abuse** | Fake "authorized by admin" claims |
| **Obfuscation** | Cleverly hidden malicious intent |

---

## Usage

### Automatic Scanning

Security scanning **автоматически запускается** при:

1. **Получении скиллов из SkillsMP**
   ```python
   from specify_cli.memory.skillsmp_integration import SkillsMPIntegration

   integration = SkillsMPIntegration()
   results = integration.search_skills("python coder")
   # Security scanning AUTOMATIC here!
   ```

2. **Создании агентов**
   ```python
   from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

   workflow = SkillCreationWorkflow()
   created_files = workflow.create_agent_from_requirements(
       agent_name="frontend-dev",
       requirements={"role": "Frontend Developer"}
   )
   # Security scanning AUTOMATIC here!
   ```

### Manual Scanning

Для произвольных файлов:

```python
from specify_cli.security import SecurityScanner, LLMSecurityReviewer

scanner = SecurityScanner()
reviewer = LLMSecurityReviewer(llm_client=current_llm)

# Scan skill directory
report = scanner.scan_skill(Path("/path/to/skill"))

if report.final_result == "BLOCKED":
    print(f"Blocked: {report.threats}")
else:
    # Level 2 review if WARNING
    result = reviewer.review(
        Path("/path/to/skill/SKILL.md"),
        stated_goal="Python coding assistant"
    )
    print(f"Safe: {result['safe']}")
```

---

## Scan Results

### SAFE ✅

```
Scan Result: SAFE
Level 1: CLEAN (0 threats, 1.2s)
Level 2: No semantic threats found
```

**Action**: Установка разрешена

### BLOCKED 🚫

```
Scan Result: BLOCKED
Level 1: CRITICAL threats found:
- [prompt_injection] "ignore previous instructions" at SKILL.md:42
- [data_exfiltration] "curl ~/.aws/credentials" at SKILL.md:15

Action: Skill deleted, not installed
```

**Action**: Установка заблокирована, файл удалён

### WARNING ⚠️

```
Scan Result: WARNING
Level 1: WARNINGS found:
- [suspicious_html] "<!-- authorized by admin -->" at SKILL.md:30

Level 2: LLM review requested confirmation
Reason: "Suspicious authority pattern, may be legitimate if from admin documentation"

Install anyway? (yes/no):
```

**Action**: Требуется подтверждение пользователя

---

## API Reference

### SecurityScanner

```python
from specify_cli.security import SecurityScanner

scanner = SecurityScanner(force_download=False)

# Scan skill
result = scanner.scan_skill(
    skill_path=Path("/path/to/skill"),
    stated_goal="Optional: stated goal for Level 2"
)

# Scan agent (same API)
result = scanner.scan_agent(
    agent_path=Path("/path/to/agent"),
    stated_goal="Optional: stated goal"
)

# Result attributes
result.final_result  # "SAFE", "BLOCKED", or "WARNING"
result.level1_threats  # List of threat dicts
result.level2_result  # Level 2 reason (if WARNING)
result.scan_time  # Scan duration in seconds
```

### LLMSecurityReviewer

```python
from specify_cli.security import LLMSecurityReviewer

reviewer = LLMSecurityReviewer(llm_client=current_llm)

result = reviewer.review(
    skill_path=Path("/path/to/skill"),
    stated_goal="Stated goal of the skill",
    level1_result="Optional: Level 1 result"
)

# Result
result["safe"]  # True if safe, False if blocked
result["reason"]  # Explanation
result["confidence"]  # "high", "medium", "low"
```

### SkillsMP Hooks

```python
from specify_cli.security.skillsmp_hooks import (
    scan_skillsmp_results,
    scan_downloaded_skill,
    UnsafeSkillError
)

# Scan all results from SkillsMP
safe_results = scan_skillsmp_results(
    results=skillsmp_results,
    scanner=scanner,
    reviewer=reviewer
)

# Scan downloaded skill before installation
try:
    scan_downloaded_skill(
        skill_path=Path("/path/to/skill"),
        skill_name="python-coder",
        scanner=scanner,
        reviewer=reviewer,
        stated_goal="Python coding assistant"
    )
    # Installation proceeds
except UnsafeSkillError as e:
    # Installation blocked
    print(f"Blocked: {e.scan_report.threats}")
```

### Agent Hooks

```python
from specify_cli.security.agent_hooks import (
    scan_created_agent,
    check_agent_specific_threats,
    UnsafeAgentError
)

# Scan newly created agent
try:
    scan_created_agent(
        agent_path=Path("/path/to/agent"),
        agent_name="backend-dev",
        agent_role="Backend Developer",
        scanner=scanner,
        reviewer=reviewer,
        stated_goal="Backend development assistant"
    )
    # Agent creation proceeds
except UnsafeAgentError as e:
    # Agent creation blocked
    print(f"Blocked: {e.scan_report.threats}")

# Check for agent-specific threats
threats = check_agent_specific_threats(
    agent_content=agents_md_content,
    agent_role="System Administrator"
)
```

---

## Integration Points

### SkillsMP Integration

```python
# In specify_cli/memory/skillsmp_integration.py

from specify_cli.security.skillsmp_hooks import scan_downloaded_skill, UnsafeSkillError

def download_skill(self, skill_id: str, target_dir: Path):
    # ... download logic ...

    # Security scan (AUTOMATIC)
    scanner = SecurityScanner()
    reviewer = LLMSecurityReviewer(llm_client=self.llm_client)

    try:
        scan_downloaded_skill(
            skill_path=target_dir,
            skill_name=skill_id,
            scanner=scanner,
            reviewer=reviewer,
            stated_goal=skill_metadata.get("description", "")
        )
    except UnsafeSkillError as e:
        # Delete and block
        shutil.rmtree(target_dir)
        raise SkillInstallationBlockedError(f"Skill blocked: {e}")
```

### Agent Creation Integration

```python
# In specify_cli/memory/agents/skill_workflow.py

from specify_cli.security.agent_hooks import scan_created_agent, UnsafeAgentError

def create_agent_from_requirements(self, agent_name: str, requirements: dict):
    # ... generate agent files ...

    # Security scan (AUTOMATIC)
    scanner = SecurityScanner()
    reviewer = LLMSecurityReviewer(llm_client=self.llm_client)

    try:
        scan_created_agent(
            agent_path=agent_dir,
            agent_name=agent_name,
            agent_role=requirements.get("role", ""),
            scanner=scanner,
            reviewer=reviewer,
            stated_goal=f"AI agent with role: {requirements.get('role', '')}"
        )
    except UnsafeAgentError as e:
        # Delete and block
        shutil.rmtree(agent_dir)
        raise AgentCreationBlockedError(f"Agent blocked: {e}")

    return created_files
```

---

## Configuration

### Scanner Location

```
~/.claude/cache/specify-cli/speckit/security-scan.py
```

**Download**: Автоматически при первом использовании

**Force update**:
```python
scanner = SecurityScanner(force_download=True)
```

### LLM Client

Level 2 review требует LLM клиента:

```python
# Use existing Claude client
from specify_cli.llm import get_llm_client

llm_client = get_llm_client()
reviewer = LLMSecurityReviewer(llm_client=llm_client)
```

---

## Troubleshooting

### Scanner not found

**Problem**: "Failed to download security scanner"

**Solution**:
```bash
# Manual download
curl -o ~/.claude/cache/specify-cli/speckit/security-scan.py \
  https://raw.githubusercontent.com/github/ai-factory/main/skills/aif-skill-generator/scripts/security-scan.py
```

### LLM review fails

**Problem**: "LLM review failed"

**Solution**: Level 1 (Python scanner) всё ещё обеспечивает защиту. WARNING level требует ручного подтверждения.

### False positive

**Problem**: Legitimate код блокируется

**Solution**: WARNING level позволяет установку с подтверждением. Для изменения правил создайте issue на GitHub.

---

## Best Practices

1. **Always review WARNINGs**: Не подтверждайте автоматически
2. **Check scan reports**: Просматривайте `history.jsonl` для security событий
3. **Keep scanner updated**: Используйте `force_download=True` периодически
4. **Validate agent roles**: Убедитесь что role совпадает с инструкциями
5. **Audit downloaded skills**: Проверяйте скиллы из SkillsMP перед использованием

---

## See Also

- [Quickstart Guide](../specs/002-implement-quality-loop/quickstart.md)
- [Security Scan Contract](../specs/002-implement-quality-loop/contracts/security-scan.md)
- [ai-factory security.md](https://github.com/github/ai-factory)
