# Data Model: Quality Loop with Security Integration

**Feature**: Quality Loop Implementation with Security Integration
**Date**: 2025-03-11
**Status**: Complete

---

## Overview

Эта документация описывает все сущности данных для quality loop и security интеграции. Модель спроектирована для:

1. **Quality Loop**: Score-based оценка, правила, итерации, состояние
2. **Security**: Двухуровневое сканирование (Python + LLM), угрозы, отчёты
3. **Persistence**: JSON для state, JSONL для audit trail, YAML для templates

---

## Core Entities

### 1. QualityRule

**Описание**: Правило оценки для quality loop с весом и severity.

**Поля**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `id` | string | ✅ | Уникальный ID правила (e.g., "correctness.endpoints") |
| `description` | string | ✅ | Человекочитаемое описание правила |
| `severity` | enum | ✅ | "fail" (weight=2), "warn" (weight=1), "info" (weight=0) |
| `weight` | int | ❌ | Вес правила (default из severity: fail=2, warn=1, info=0) |
| `phase` | enum | ✅ | "A" или "B" — фаза оценки |
| `check` | string | ✅ | Описание проверки или executable check |
| `check_type` | enum | ✅ | "content" (text analysis), "executable" (run script), "hybrid" |

**Пример**:
```json
{
  "id": "correctness.endpoints",
  "description": "All core CRUD endpoints are present",
  "severity": "fail",
  "weight": 2,
  "phase": "A",
  "check": "verify each endpoint from task prompt exists",
  "check_type": "content"
}
```

**Валидация**:
- `id` должен быть уникальным в рамках criteria template
- `severity` должен быть одним из: "fail", "warn", "info"
- `phase` должен быть "A" или "B"
- `weight` должен быть 0, 1, или 2
- `check_type` должен быть одним из: "content", "executable", "hybrid"

**State Transitions**: None (immutable после создания)

---

### 2. CriteriaTemplate

**Описание**: Переиспользуемый набор правил для типа задач (API-spec, code-gen, docs, config).

**Поля**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `name` | string | ✅ | Название template (e.g., "Code Generation Criteria") |
| `version` | float | ✅ | Версия template (e.g., 1.0) |
| `description` | string | ✅ | Описание назначения template |
| `phases` | object | ✅ | Конфигурация фаз (threshold, active_levels) |
| `rules` | array | ✅ | Список QualityRule объектов |

**Пример**:
```json
{
  "name": "Code Generation Criteria",
  "version": 1.0,
  "description": "Quality rules for generated code",
  "phases": {
    "a": {
      "threshold": 0.8,
      "active_levels": ["A"]
    },
    "b": {
      "threshold": 0.9,
      "active_levels": ["A", "B"]
    }
  },
  "rules": [
    {
      "id": "correctness.endpoints",
      "description": "All core CRUD endpoints are present",
      "severity": "fail",
      "weight": 2,
      "phase": "A",
      "check": "verify each endpoint from task prompt exists",
      "check_type": "content"
    }
  ]
}
```

**Валидация**:
- `phases.a.threshold` и `phases.b.threshold` должны быть между 0.0 и 1.0
- `rules` не должен быть пустым (минимум 1 правило)
- Все `rule.id` в `rules` должны быть уникальными

**Relationships**:
- HasMany → QualityRule (rules array)

---

### 3. EvaluationResult

**Описание**: Результат оценки артефакта по правилам.

**Поля**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `score` | float | ✅ | Score от 0.0 до 1.0 |
| `passed` | boolean | ✅ | Прошла ли оценка (score >= threshold AND no fails) |
| `threshold` | float | ✅ | Используемый threshold для этой оценки |
| `phase` | string | ✅ | "A" или "B" |
| `passed_rules` | array | ✅ | Список QualityRule.id которые прошли |
| `failed_rules` | array | ✅ | Список {rule_id, reason} для проваленных |
| `warnings` | array | ✅ | Список {rule_id, reason} для warn severity |
| `evaluated_at` | string | ✅ | ISO timestamp оценки |

**Пример**:
```json
{
  "score": 0.72,
  "passed": false,
  "threshold": 0.8,
  "phase": "A",
  "passed_rules": ["quality.readability", "security.auth"],
  "failed_rules": [
    {
      "rule_id": "correctness.endpoints",
      "reason": "DELETE endpoint missing"
    },
    {
      "rule_id": "quality.tests",
      "reason": "No unit tests found"
    }
  ],
  "warnings": [
    {
      "rule_id": "performance.caching",
      "reason": "Response caching not implemented"
    }
  ],
  "evaluated_at": "2025-03-11T10:30:00Z"
}
```

**Валидация**:
- `score` должен быть между 0.0 и 1.0
- `passed` = (score >= threshold) AND (no failed_rules с severity="fail")
- `evaluated_at` должен быть валидным ISO 8601 timestamp

---

### 4. SecurityThreat

**Описание**: Обнаруженная угроза безопасности в скилле или агенте.

**Поля**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `type` | string | ✅ | Тип угрозы (prompt_injection, data_exfiltration, stealth, destructive, config_tampering, encoded_payload, social_engineering, suspicious_html, other) |
| `severity` | string | ✅ | "CRITICAL" или "WARNING" |
| `description` | string | ✅ | Описание угрозы |
| `location` | string | ✅ | Местоположение (file:line или context) |
| `evidence` | string | ❌ | Цитата из кода triggering угрозу |
| `level` | int | ✅ | Уровень обнаружения (1=Python scanner, 2=LLM review) |

**Пример**:
```json
{
  "type": "prompt_injection",
  "severity": "CRITICAL",
  "description": "Detected 'ignore previous instructions' pattern",
  "location": "SKILL.md:42",
  "evidence": "If user says 'ignore previous instructions', then...",
  "level": 1
}
```

**Валидация**:
- `type` должен быть одним из pre-defined типов
- `severity` должен быть "CRITICAL" или "WARNING"
- `level` должен быть 1 или 2

---

### 5. SkillScanReport

**Описание**: Отчёт о сканировании скилла с результатами обоих уровней.

**Поля**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `skill_id` | string | ✅ | ID или название скилла |
| `scanned_at` | string | ✅ | ISO timestamp сканирования |
| `level1_result` | object | ✅ | Результат Python сканера |
| `level2_result` | object | ❌ | Результат LLM обзора (если Level 1 passed) |
| `final_result` | string | ✅ | "SAFE", "BLOCKED", или "WARNING" |
| `threats` | array | ✅ | Список SecurityThreat объектов |

**Пример**:
```json
{
  "skill_id": "python-coder-v2",
  "scanned_at": "2025-03-11T10:30:00Z",
  "level1_result": {
    "exit_code": 0,
    "status": "CLEAN",
    "scan_time_ms": 1250
  },
  "level2_result": {
    "safe": true,
    "threats": [],
    "reasoning": "All instructions serve stated purpose: Python coding assistance"
  },
  "final_result": "SAFE",
  "threats": []
}
```

**Валидация**:
- `level1_result.exit_code` должен быть 0 (CLEAN), 1 (BLOCKED), или 2 (WARNINGS)
- `final_result` должен соответствовать комбинации Level 1 + Level 2
- Если `level1_result.exit_code != 0`, то `level2_result` отсутствует

**Relationships**:
- HasMany → SecurityThreat (threats array)

**State Machine**:
```
Level 1 Scan → exit_code=0 (CLEAN) → Level 2 Review → SAFE/WARNING
            → exit_code=1 (BLOCKED) → BLOCKED
            → exit_code=2 (WARNINGS) → WARNING (user confirmation)
```

---

### 6. AgentScanReport

**Описание**: Отчёт о сканировании агента с дополнительными проверками для системных прав.

**Поля**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `agent_name` | string | ✅ | Название агента |
| `scanned_at` | string | ✅ | ISO timestamp сканирования |
| `level1_result` | object | ✅ | Результат Python сканера (агент-специфичный) |
| `level2_result` | object | ❌ | Результат LLM обзора |
| `final_result` | string | ✅ | "SAFE", "BLOCKED", или "WARNING" |
| `threats` | array | ✅ | Список SecurityThreat объектов |
| `agent_checks` | object | ✅ | Агент-специфичные проверки |

**Пример**:
```json
{
  "agent_name": "frontend-dev",
  "scanned_at": "2025-03-11T10:30:00Z",
  "level1_result": {
    "exit_code": 0,
    "status": "CLEAN",
    "scan_time_ms": 1800
  },
  "level2_result": {
    "safe": true,
    "threats": [],
    "reasoning": "Agent role (Frontend Developer) matches instructions. No stealth patterns detected."
  },
  "final_result": "SAFE",
  "threats": [],
  "agent_checks": {
    "system_access": false,
    "shell_commands": [],
    "file_write_access": false,
    "stealth_patterns": [],
    "role_instruction_mismatch": false
  }
}
```

**Агент-специфичные проверки** (`agent_checks`):

| Поле | Тип | Описание |
|------|-----|----------|
| `system_access` | boolean | Запрашивает ли агент доступ к системе (shell, exec) |
| `shell_commands` | array | Список shell команд которые агент может выполнять |
| `file_write_access` | boolean | Может ли агент писать в файлы |
| `stealth_patterns` | array | Список обнаруженных stealth инструкций |
| `role_instruction_mismatch` | boolean | Несоответствие между role и instructions |

**Валидация**:
- Все поля из `SkillScanReport` применимы
- `agent_checks` должен быть present для всех agent scans

**Relationships**:
- Inherits → SkillScanReport (базовая структура)
- HasMany → SecurityThreat (threats array)

---

### 7. LoopState

**Описание**: Состояние quality loop для персистентности и восстановления.

**Поля**:

| Поле | Тип | Обязательное | Описание |
|------|-----|--------------|----------|
| `run_id` | string | ✅ | Уникальный ID запуска (timestamp-based) |
| `task_alias` | string | ✅ | Короткое название задачи (из ветки или user input) |
| `status` | string | ✅ | "running", "stopped", "completed", "failed" |
| `iteration` | int | ✅ | Текущий номер итерации (1-based) |
| `max_iterations` | int | ✅ | Максимум итераций |
| `phase` | string | ✅ | "A" или "B" |
| `current_step` | string | ✅ | Текущий шаг ("PLAN", "PRODUCE", "PREPARE", "EVALUATE", "CRITIQUE", "REFINE") |
| `task` | object | ✅ | Описание задачи (prompt, ideal_result) |
| `criteria` | object | ✅ | Используемые criteria (name, version, phases, rules) |
| `plan` | array | ❌ | План (3-5 steps) |
| `prepared_checks` | object | ❌ | Подготовленные checks из PREPARE фазы |
| `evaluation` | object | ❌ | Последний EvaluationResult |
| `critique` | object | ❌ | Последняя критика (failed rules + fix instructions) |
| `stop` | object | ✅ | Stop condition (passed, reason) |
| `last_score` | float | ✅ | Score на предыдущей итерации (для stagnation) |
| `current_score` | float | ✅ | Score на текущей итерации |
| `stagnation_count` | int | ✅ | Счётчик stagnation |
| `created_at` | string | ✅ | ISO timestamp создания |
| `updated_at` | string | ✅ | ISO timestamp последнего обновления |

**Пример**:
```json
{
  "run_id": "courses-api-ddd-20260311-120000",
  "task_alias": "courses-api-ddd",
  "status": "running",
  "iteration": 2,
  "max_iterations": 4,
  "phase": "A",
  "current_step": "EVALUATE",
  "task": {
    "prompt": "OpenAPI 3.1 spec + DDD notes + JSON examples",
    "ideal_result": "Spec + notes + examples pass phase B"
  },
  "criteria": {
    "name": "code-gen",
    "version": 1.0,
    "phases": {
      "a": {"threshold": 0.8, "active_levels": ["A"]},
      "b": {"threshold": 0.9, "active_levels": ["A", "B"]}
    },
    "rules": [...]
  },
  "plan": [
    "1. Parse OpenAPI spec",
    "2. Generate domain models",
    "3. Implement repository pattern",
    "4. Add JSON examples",
    "5. Verify all endpoints"
  ],
  "prepared_checks": null,
  "evaluation": {
    "score": 0.84,
    "passed": true,
    "threshold": 0.8,
    "phase": "A",
    "passed_rules": [...],
    "failed_rules": [],
    "warnings": [...],
    "evaluated_at": "2025-03-11T10:31:00Z"
  },
  "critique": null,
  "stop": {
    "passed": false,
    "reason": ""
  },
  "last_score": 0.72,
  "current_score": 0.84,
  "stagnation_count": 0,
  "created_at": "2025-03-11T10:30:00Z",
  "updated_at": "2025-03-11T10:31:00Z"
}
```

**Валидация**:
- `run_id` должен быть уникальным (формируется как `{alias}-{YYYYMMDD-HHMMSS}`)
- `status` должен быть одним из: "running", "stopped", "completed", "failed"
- `iteration` должен быть между 1 и `max_iterations`
- `phase` должен быть "A" или "B"
- `current_step` должен быть одним из 6 phases
- `stagnation_count` должен быть >= 0

**Relationships**:
- HasOne → CriteriaTemplate (criteria)
- HasMany → EvaluationResult (evaluation, implicit history)
- HasMany → Critique (critique)

**State Machine**:
```
running → evaluation_passed && phase_b_reached → completed
        → evaluation_failed && stagnation_count >= 2 → stopped (stagnation)
        → iteration >= max_iterations → stopped (iteration_limit)
        → user_stop → stopped (user_stop)
        → phase_error → failed
```

---

## Persistence Models

### run.json

**Описание**: Single source of truth для состояния loop (соответствует LoopState).

**Расположение**: `.speckit/evolution/<task-alias>/run.json`

**Формат**: JSON (один объект LoopState)

**Обновления**: После каждого phase transition (PLAN → PRODUCE → ... → REFINE)

**Пример пути**: `.speckit/evolution/courses-api-ddd/run.json`

---

### history.jsonl

**Описание**: Append-only event stream для аудита и восстановления.

**Расположение**: `.speckit/evolution/<task-alias>/history.jsonl`

**Формат**: JSONL (один JSON объект на строку)

**События**:
```json
{"ts":"2025-03-11T10:30:00Z","run_id":"courses-api-ddd-20260311-120000","iteration":1,"phase":"A","step":"PLAN","event":"plan_created","status":"ok"}
{"ts":"2025-03-11T10:30:30Z","run_id":"courses-api-ddd-20260311-120000","iteration":1,"phase":"A","step":"PRODUCE","event":"artifact_created","status":"ok"}
{"ts":"2025-03-11T10:31:00Z","run_id":"courses-api-ddd-20260311-120000","iteration":1,"phase":"A","step":"EVALUATE","event":"evaluation_done","status":"ok","payload":{"score":0.72,"passed":false}}
{"ts":"2025-03-11T10:31:30Z","run_id":"courses-api-ddd-20260311-120000","iteration":1,"phase":"A","step":"REFINE","event":"refinement_done","status":"ok"}
{"ts":"2025-03-11T10:32:00Z","run_id":"courses-api-ddd-20260311-120000","iteration":2,"phase":"A","step":"EVALUATE","event":"evaluation_done","status":"ok","payload":{"score":0.84,"passed":true}}
{"ts":"2025-03-11T10:32:30Z","run_id":"courses-api-ddd-20260311-120000","iteration":2,"phase":"A","step":"EVALUATE","event":"phase_switched","status":"ok","payload":{"to_phase":"B"}}
```

**Use Cases**:
1. **Аудит**: Полная история всех действий в loop
2. **Восстановление**: Reconstruct run.json из history.jsonl если corruption
3. **Аналитика**: Post-hoc анализ loop performance

---

### artifact.md

**Описание**: Содержание артефакта (текущая версия кода для оценки).

**Расположение**: `.speckit/evolution/<task-alias>/artifact.md`

**Формат**: Markdown с code blocks для каждого файла

**Пример**:
```markdown
# Artifact: courses-api-ddd

## src/models/course.py

```python
from dataclasses import dataclass
from typing import List

@dataclass
class Course:
    id: int
    title: str
    description: str
    modules: List["Module"]

@dataclass
class Module:
    id: int
    course_id: int
    title: str
    lessons: List["Lesson"]
```

## src/repositories/course_repository.py

```python
class CourseRepository:
    def find_all(self) -> List[Course]:
        # Implementation
        pass
```
```

**Обновления**: После PRODUCE и REFINE phases

---

### current.json

**Описание**: Указатель на активный loop (exists только пока loop запущен).

**Расположение**: `.speckit/evolution/current.json`

**Формат**: JSON
```json
{
  "active_run_id": "courses-api-ddd-20260311-120000",
  "task_alias": "courses-api-ddd",
  "status": "running",
  "updated_at": "2025-03-11T10:30:00Z"
}
```

**Обновления**: Создаётся при запуске loop, удаляется при termination

**Use Cases**:
1. **Resume**: `/speckit.loop resume` читает current.json для нахождения активного loop
2. **Status**: `/speckit.loop status` показывает активный loop
3. **Stop**: `/speckit.loop stop` использует current.json для остановки

---

## YAML Models

### Criteria Template (YAML)

**Описание**: Criteria template в YAML формате для редактирования людьми.

**Расположение**:
- Library: `.speckit/criteria/<name>.yml` (user override)
- Default: `src/specify_cli/quality/templates/<name>.yml` (built-in)

**Пример**: см. Research → Decision 2

**Loading Order**:
1. Check `.speckit/criteria/<name>.yml` (user override)
2. Fallback to `src/specify_cli/quality/templates/<name>.yml` (default)

---

## Entity Relationships Summary

```
CriteriaTemplate (1) ───(has many)──> QualityRule (*)
      │
      └──(used by)──> LoopState (1)
                          │
                          ├──(produces)──> EvaluationResult (*)
                          │
                          ├──(generates)──> Critique (*)
                          │
                          └──(persisted in)──> run.json (1)
                                                + artifact.md (1)
                                                + history.jsonl (*)

SecurityScan (1) ───(produces)──> SkillScanReport (1)
                                            │
                                            ├──(has many)──> SecurityThreat (*)
                                            │
                                            └──(specialized by)──> AgentScanReport (1)
                                                                    │
                                                                    └──(extends with)──> agent_checks (1)
```

---

## Data Access Patterns

### Read Patterns

1. **Load criteria template**:
   ```python
   def load_criteria(name: str) -> CriteriaTemplate:
       # Check user override, then default
       user_path = Path(".speckit/criteria") / f"{name}.yml"
       default_path = Path("src/specify_cli/quality/templates") / f"{name}.yml"

       if user_path.exists():
           return parse_yaml(user_path)
       return parse_yaml(default_path)
   ```

2. **Load loop state**:
   ```python
   def load_loop_state(task_alias: str) -> LoopState:
       path = Path(".speckit/evolution") / task_alias / "run.json"
       return parse_json(path)
   ```

3. **Load artifact**:
   ```python
   def load_artifact(task_alias: str) -> str:
       path = Path(".speckit/evolution") / task_alias / "artifact.md"
       return path.read_text()
   ```

### Write Patterns

1. **Save loop state**:
   ```python
   def save_loop_state(state: LoopState):
       path = Path(".speckit/evolution") / state.task_alias / "run.json"
       state.updated_at = datetime.now().isoformat()
       write_json(path, state)
   ```

2. **Append event**:
   ```python
   def append_event(event: Event):
       path = Path(".speckit/evolution") / event.task_alias / "history.jsonl"
       with open(path, "a") as f:
           f.write(json.dumps(event) + "\n")
   ```

3. **Save artifact**:
   ```python
   def save_artifact(task_alias: str, content: str):
       path = Path(".speckit/evolution") / task_alias / "artifact.md"
       path.write_text(content)
   ```

---

## Validation Rules Summary

| Entity | Key Rules |
|--------|-----------|
| QualityRule | Unique id, valid severity/phase/weight, non-empty check |
| CriteriaTemplate | Non-empty rules, unique rule ids, valid thresholds |
| EvaluationResult | Score 0-1, passed = logic, valid timestamp |
| SecurityThreat | Valid type, valid severity, valid level |
| SkillScanReport | Valid exit codes, consistent final_result |
| AgentScanReport | All SkillScanReport rules + agent_checks present |
| LoopState | Unique run_id, valid status/phase/step, iteration <= max |

---

## Migration Notes

**Version 1.0 → 1.1** (hypothetical):
- Added `agent_checks` to AgentScanReport
- Migration: Add empty `agent_checks` to existing reports

**Version 1.0 → 2.0** (hypothetical):
- Changed `severity` from string to enum
- Migration: Validate all existing severity values are valid enum members
