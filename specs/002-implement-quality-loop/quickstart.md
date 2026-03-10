# Quickstart Guide: Quality Loop with Security Integration

**Feature**: Quality Loop Implementation with Security Integration
**Date**: 2025-03-11
**Audience**: Developers using SpecKit

---

## Overview

Это руководство поможет вам начать использовать новые возможности SpecKit:
- **Quality Loop**: Итеративное улучшение качества кода с автоматической оценкой
- **Security Scanning**: Двухуровневая защита при получении скиллов и создании агентов

**Время чтения**: 10 минут

---

## Prerequisites

Убедитесь что у вас установлено:

1. **SpecKit**: Следуйте инструкциям в `INSTALL.md`
2. **Python 3.11+**: Для security scanner
3. **Git**: Для artifact detection (опционально, но рекомендуется)
4. **LLM (Claude Code или другой)**: Для Level 2 security review

---

## Part 1: Quality Loop

### What is Quality Loop?

Quality Loop автоматически оценивает ваш код против явных правил, генерирует целевую обратную связь, и улучшает реализацию через несколько итераций. Вдохновлён Reflex Loop из ai-factory.

**Benefits**:
- ✅ **Измеримое качество**: Score от 0.0 до 1.0
- ✅ **Автоматические исправления**: Targeted fixes для провалившихся правил
- ✅ **Итеративное улучшение**: Цикл продолжается пока threshold не достигнут
- ✅ **Stagnation detection**: Останавливается когда качество plateaus

### Three Ways to Use

#### 1. `/speckit.implementloop` — All-in-One

**Best for**: Новые фичи, когда вы хотите реализовать + улучшить за один раз

```bash
/speckit.implementloop --criteria code-gen --max-iterations 4
```

**Что происходит**:
1. Реализует все задачи из `tasks.md` (как `/speckit.implement`)
2. Автоматически запускает quality loop
3. Повторяет: оценка → критика → исправление до threshold или лимита

**Output**:
```
=== Implementing Tasks from tasks.md ===
✅ Task 1: Create src/models/course.py
✅ Task 2: Create src/repositories/course_repository.py

=== Quality Loop Started ===

Iteration 1/4 | Phase A | Score: 0.72 | FAIL
Failed: correctness.tests, quality.error_handling

Iteration 2/4 | Phase A | Score: 0.84 | PASS (Phase A → B)

Iteration 3/4 | Phase B | Score: 0.88 | FAIL
Failed: performance.caching

Iteration 4/4 | Phase B | Score: 0.92 | PASS

=== Quality Loop Complete ===
Stop Reason: threshold_reached
Changed Files: 5
Iterations: 4
Total Time: 4m 32s
```

#### 2. `/speckit.loop` — Separate Quality Loop

**Best for**: Код уже реализован (через `/speckit.implement` или вручную)

```bash
# Auto-detect criteria from task description
/speckit.loop

# Or specify criteria explicitly
/speckit.loop --criteria code-gen --max-iterations 6
```

**Modes**:
```bash
/speckit.loop           # New loop (auto-detect artifact)
/speckit.loop resume    # Resume active loop
/speckit.loop status    # Show active loop status
/speckit.loop stop      # Stop active loop
/speckit.loop list      # List all loops
/speckit.loop history [alias]    # Show loop history
/speckit.loop clean [alias|--all] # Delete loop files
```

#### 3. `/speckit.implement` + Recommendation

**Best for**: Обычный workflow, когда вы хотите вручную решать когда запускать quality loop

```bash
/speckit.implement
```

**В конце вы увидите**:
```
---
## 🔄 Quality Loop Available

Implementation complete! You can further improve code quality...

### How to Use
/speckit.loop --criteria code-gen --max-iterations 4
```

### Arguments Explained

| Аргумент | По умолчанию | Описание |
|----------|--------------|----------|
| `--criteria` | auto-detect | Rule set: api-spec, code-gen, docs, config |
| `--max-iterations` | 4 | Максимум циклов оценки |
| `--threshold-a` | 0.8 | Phase A threshold (base quality) |
| `--threshold-b` | 0.9 | Phase B threshold (strict quality) |

### Criteria Templates

Встроенные templates для разных типов задач:

| Template | Когда использовать |
|----------|-------------------|
| `api-spec` | API design, OpenAPI specs, endpoint definitions |
| `code-gen` | Code implementation, classes, functions |
| `docs` | Documentation, README, guides |
| `config` | Configuration files, settings, YAML/JSON |

**Auto-detection**: `/speckit.loop` автоматически детектит template из описания задачи (ключевые слова: "api", "code", "docs", "config")

### Understanding the Output

**Iteration summary**:
```
Iteration 2/4 | Phase A | Score: 0.84 | PASS (Phase A → B)
```

- `2/4`: Итерация 2 из 4
- `Phase A`: Фаза A (базовые правила)
- `Score: 0.84`: 84% правил прошли
- `PASS`: Score >= 0.8 (threshold)
- `Phase A → B`: Переход к Phase B

**Failed rules**:
```
Failed: correctness.tests, quality.error_handling
```

Эти правила не прошли и будут исправлены в следующей итерации.

**Stop reasons**:
- `threshold_reached`: Phase B threshold достигнут ✅
- `no_major_issues`: Нет fail-severity правил ✅
- `iteration_limit`: Достигнут лимит итераций
- `stagnation`: Качество не улучшается
- `user_stop`: Остановлено пользователем

### Resume After Interruption

Если loop был прерван (Ctrl+C, crash):

```bash
/speckit.loop resume
```

Loop восстановится из сохранённого состояния (`.speckit/evolution/current.json`) и продолжится с последнего места.

---

## Part 2: Security Scanning

### What is Security Scanning?

Двухуровневая защита от вредоносных скиллов и агентов:
- **Level 1**: Python статический сканер (из ai-factory)
- **Level 2**: LLM семантический обзор

**Protects against**:
- Prompt injection ("ignore previous instructions")
- Data exfiltration (curl ~/.ssh, ~/.aws)
- Stealth instructions ("do not tell user")
- Destructive commands (rm -rf)
- Config tampering (.bashrc modifications)
- Encoded payloads (base64, hex)

### Automatic Scanning

Security scanning **автоматически запускается** при:

1. **Получении скиллов из SkillsMP**:
   ```python
   from specify_cli.memory.skillsmp_integration import SkillsMPIntegration

   integration = SkillsMPIntegration()
   results = integration.search_skills("python coder")
   # Security scanning AUTOMATIC here!
   ```

2. **Создании агентов через SkillCreationWorkflow**:
   ```python
   from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

   workflow = SkillCreationWorkflow()
   created_files = workflow.create_agent_from_requirements(
       agent_name="frontend-dev",
       requirements={"role": "Frontend Developer"}
   )
   # Security scanning AUTOMATIC here!
   ```

### Understanding Scan Results

**SAFE**: ✅ Безопасно для использования
```
Scan Result: SAFE
Level 1: CLEAN (0 threats, 1.2s)
Level 2: No semantic threats found
```

**BLOCKED**: 🚫 Опасно, installation prevented
```
Scan Result: BLOCKED
Level 1: CRITICAL threats found:
- [prompt_injection] "ignore previous instructions" at SKILL.md:42
- [data_exfiltration] "curl ~/.aws/credentials" at SKILL.md:15

Action: Skill deleted, not installed
```

**WARNING**: ⚠️ Подозрительно, требуется подтверждение
```
Scan Result: WARNING
Level 1: WARNINGS found:
- [suspicious_html] "<!-- authorized by admin -->" at SKILL.md:30

Level 2: LLM review requested confirmation
Reason: "Suspicious authority pattern, may be legitimate if from admin documentation"

Install anyway? (yes/no):
```

### Manual Security Scanning

Для сканирования произвольных файлов:

```python
from specify_cli.security.scanner import SecurityScanner
from specify_cli.security.llm_review import LLMSecurityReviewer

scanner = SecurityScanner()
reviewer = LLMSecurityReviewer(llm_client)

# Scan a skill directory
report = scanner.scan_skill(Path("/path/to/skill"))

if report.final_result == "BLOCKED":
    print(f"Blocked: {report.threats}")
else:
    # Level 2 review
    result = reviewer.review(
        Path("/path/to/skill/SKILL.md"),
        stated_goal="Python coding assistant"
    )
    print(f"Safe: {result['safe']}")
```

---

## Part 3: Common Workflows

### Workflow 1: New Feature with Quality

```bash
# 1. Create specification
/speckit.specify "User authentication with JWT"

# 2. Generate plan
/speckit.plan

# 3. Generate tasks
/speckit.tasks

# 4. Implement + quality loop (all-in-one)
/speckit.implementloop --criteria code-gen
```

### Workflow 2: Implement Manually, Then Quality Loop

```bash
# 1-3. Same as above

# 4. Implement manually
/speckit.implement

# 5. See recommendation, then run quality loop
/speckit.loop --criteria code-gen --max-iterations 6
```

### Workflow 3: Quality Loop on Existing Code

```bash
# Code already exists, just run quality loop
/speckit.loop --criteria code-gen

# Or specify artifact directly
/speckit.loop --artifact ./src/main.py --criteria code-gen
```

### Workflow 4: Download Safe Skill from SkillsMP

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()

# Search (automatic security scanning)
results = workflow.search_agents("python web developer")

# Results are ALREADY SCANNED, only safe skills shown
workflow.present_options(results)
```

### Workflow 5: Create New Agent with Security

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()

# Create agent (automatic security scanning)
try:
    created_files = workflow.create_agent_from_requirements(
        agent_name="backend-dev",
        requirements={
            "role": "Backend Developer",
            "personality": "Analytical and systematic"
        }
    )
    print(f"Agent created: {created_files}")
except UnsafeAgentError as e:
    print(f"Agent blocked: {e.scan_report.threats}")
```

---

## Part 4: Configuration

### Custom Criteria Templates

Создайте свой template в `.speckit/criteria/`:

```yaml
# .speckit/criteria/my-custom.yml
name: "My Custom Criteria"
version: 1.0
description: "Quality rules for my specific use case"

phases:
  a:
    threshold: 0.8
    active_levels: ["A"]
  b:
    threshold: 0.9
    active_levels: ["A", "B"]

rules:
  - id: "custom.rule1"
    description: "My specific requirement"
    severity: "fail"
    weight: 2
    phase: "A"
    check: "verify specific pattern"
    check_type: "content"

  - id: "custom.rule2"
    description: "Another requirement"
    severity: "warn"
    phase: "B"
    check: "verify another pattern"
    check_type: "executable"
```

Использование:
```bash
/speckit.loop --criteria my-custom
```

### Loop State Location

Loop state сохраняется в `.speckit/evolution/`:

```
.speckit/
├── evolution/
│   ├── current.json           # Активный loop pointer
│   └── <task-alias>/
│       ├── run.json           # Loop state
│       ├── history.jsonl      # Event stream
│       └── artifact.md        # Artifact content
└── criteria/
    └── custom.yml             # User-defined criteria
```

**Resume after context loss**:
```bash
# Even after /clear, you can resume
/speckit.loop resume
```

---

## Part 5: Troubleshooting

### Quality Loop Issues

**Problem**: Loop stuck at same score

**Solution**: Stagnation detection automatically stops after 2 iterations with < 0.02 improvement. Increase `--max-iterations` or review rules.

**Problem**: Score not improving

**Solution**: Check failed rules with `/speckit.loop history <alias>`. Some rules may be too strict or not applicable.

**Problem**: Loop taking too long

**Solution**: Reduce `--max-iterations` or use `--criteria` with fewer rules.

### Security Scanning Issues

**Problem**: Scanner not found

**Solution**:
```bash
# Manually download scanner
curl -o ~/.claude/spec-kit/security-scan.py \
  https://raw.githubusercontent.com/github/ai-factory/main/skills/aif-skill-generator/scripts/security-scan.py
```

**Problem**: LLM review fails

**Solution**: Level 1 (Python scanner) still provides protection. Check LLM configuration.

**Problem**: False positive on legitimate code

**Solution**: Review the threat, confirm it's safe to proceed. WARNING level allows installation with confirmation.

---

## Part 6: Key Validation Scenarios

### Quality Loop Validation

**Scenario 1: Successful loop**
```bash
$ /speckit.implementloop --criteria code-gen

=== Quality Loop Complete ===
Iteration 4/4 | Phase B | Score: 0.91 | PASS
Stop Reason: threshold_reached
```

**Validation**: Score >= 0.9, stop_reason = "threshold_reached"

**Scenario 2: Loop with issues**
```bash
$ /speckit.loop status

Iteration 3/4 | Phase A | Score: 0.76 | FAIL
Failed: correctness.tests, quality.error_handling
```

**Validation**: Review failed rules, address issues, resume or start new loop.

**Scenario 3: Stagnation**
```bash
$ /speckit.loop history

Iteration 2: Score: 0.84
Iteration 3: Score: 0.85 (delta: 0.01)
Iteration 4: Score: 0.85 (delta: 0.00) → Stagnation detected
```

**Validation**: Stagnation detected after 2 iterations with < 0.02 improvement.

### Security Scanning Validation

**Scenario 1: Safe skill**
```bash
$ python -c "from specify_cli.security import scan_skill; print(scan_skill('python-coder'))"

Scan Result: SAFE
Level 1: CLEAN (0 threats)
Level 2: No semantic threats
```

**Validation**: Both Level 1 and Level 2 passed.

**Scenario 2: Malicious skill blocked**
```bash
$ python -c "from specify_cli.security import scan_skill; print(scan_skill('malicious-agent'))"

Scan Result: BLOCKED
Level 1: CRITICAL threats found:
- [prompt_injection] "ignore previous instructions" at SKILL.md:42

Action: Skill deleted
```

**Validation**: CRITICAL threat detected, installation blocked.

**Scenario 3: Suspicious but safe**
```bash
$ python -c "from specify_cli.security import scan_skill; print(scan_skill('admin-tool'))"

Scan Result: WARNING
Level 1: Suspicious authority pattern
Level 2: Legitimate if from admin documentation

Install anyway? (yes/no): yes
```

**Validation**: WARNING level requires user confirmation.

---

## Part 7: Best Practices

### Quality Loop Best Practices

1. **Start with auto-detect**: Use `/speckit.loop` without `--criteria` for first run
2. **Review before refine**: Check `history.jsonl` to understand what's being fixed
3. **Set realistic limits**: Default 4 iterations is good starting point
4. **Use Phase B for production**: Phase A (0.8) for development, Phase B (0.9) for production
5. **Clean up old loops**: Use `/speckit.loop clean --all` periodically

### Security Best Practices

1. **Always review WARNINGs**: Don't blindly confirm security warnings
2. **Check scan reports**: Review `history.jsonl` for security events
3. **Keep scanner updated**: Run with `force_download=True` periodically
4. **Validate agent roles**: Ensure role matches instructions for agents
5. **Audit downloaded skills**: Review SkillsMP downloads before use

---

## Part 8: Next Steps

After completing this quickstart:

1. **Explore criteria templates**: Check built-in templates in `src/specify_cli/quality/templates/`
2. **Create custom rules**: Add project-specific quality rules
3. **Review security patterns**: Study ai-factory security.md for threat patterns
4. **Integrate with CI/CD**: Add quality loop to CI pipeline (future feature)
5. **Contribute improvements**: Share useful criteria templates with community

---

## Part 9: Quick Reference

### Commands

| Команда | Purpose |
|---------|---------|
| `/speckit.implementloop` | Implement + quality loop (all-in-one) |
| `/speckit.loop` | Quality loop on existing code |
| `/speckit.loop status` | Show active loop status |
| `/speckit.loop resume` | Resume interrupted loop |
| `/speckit.loop stop` | Stop active loop |
| `/speckit.loop list` | List all loops |
| `/speckit.loop history` | Show loop history |
| `/speckit.loop clean` | Delete loop files |
| `/speckit.implement` | Implement (with recommendation) |

### Files

| Файл | Назначение |
|------|------------|
| `.speckit/evolution/current.json` | Активный loop pointer |
| `.speckit/evolution/<alias>/run.json` | Loop state |
| `.speckit/evolution/<alias>/history.jsonl` | Event stream |
| `.speckit/evolution/<alias>/artifact.md` | Artifact content |
| `.speckit/criteria/<name>.yml` | Custom criteria template |

### Exit Codes

| Код | Значение |
|-----|----------|
| 0 | Success |
| 1 | Error (implementation or quality loop failed) |
| 2 | Warning (security scan with warnings) |

---

## Support

Для вопросов и проблем:
- Check `docs/quality-loop.md` for detailed documentation
- Check `docs/security-scanning.md` for security details
- Open issue on GitHub with logs from `history.jsonl`

**Happy coding with quality and security!** 🚀
