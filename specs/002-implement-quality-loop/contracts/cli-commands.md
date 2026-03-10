# CLI Commands Contract

**Feature**: Quality Loop with Security Integration
**Date**: 2025-03-11
**Version**: 1.0

---

## Overview

Этот документ описывает контракты для трёх CLI команд:
1. `/speckit.implementloop` — объединённая реализация + quality loop
2. `/speckit.loop` — отдельный quality loop
3. `/speckit.implement` — обновление с рекомендацией

---

## Command 1: `/speckit.implementloop`

### Signature

```bash
/speckit.implementloop [OPTIONS]
```

### Arguments

| Аргумент | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `--criteria` | string | ❌ | auto-detect | Criteria template (api-spec, code-gen, docs, config) |
| `--max-iterations` | int | ❌ | 4 | Максимум итераций quality loop |
| `--threshold-a` | float | ❌ | 0.8 | Phase A threshold (0.0-1.0) |
| `--threshold-b` | float | ❌ | 0.9 | Phase B threshold (0.0-1.0) |

### Behaviour

**Phase 1: Implementation**
1. Читает `specs/<branch>/tasks.md`
2. Реализует все задачи (как `/speckit.implement`)
3. Показывает summary реализованных задач

**Phase 2: Quality Loop** (автоматический)
1. Детектирует artifact (изменённые файлы)
2. Запускает quality loop с указанными параметрами
3. Повторяет: EVALUATE → (CRITIQUE → REFINE) до:
   - Phase B threshold reached (score >= threshold-b)
   - OR max_iterations reached
   - OR stagnation detected
   - OR user interruption

**Output**:
```
=== Implementing Tasks from tasks.md ===

[Implementation progress...]
✅ Task 1: Create src/models/course.py
✅ Task 2: Create src/repositories/course_repository.py
✅ Task 3: Implement course service

=== Quality Loop Started ===

Iteration 1/4 | Phase A | Score: 0.72 | FAIL
Plan: Implement task from tasks.md
Hash: a3f2e1b4
Changed: src/main.py, src/utils.py
Failed: correctness.tests, quality.error_handling
Warnings: performance.caching

Iteration 2/4 | Phase A | Score: 0.84 | PASS (Phase A → B)

...

=== Quality Loop Complete ===

Iteration 4/4 | Phase B | Score: 0.91 | PASS
Stop Reason: threshold_reached
Distance to Success: 0.00 (threshold reached)
Changed Files: 3
Iterations: 4
Total Time: 4m 32s
```

### Exit Codes

| Code | Значение |
|------|----------|
| 0 | Success (implementation complete + quality loop passed/reached limit) |
| 1 | Error (implementation failed OR quality loop failed) |

### Error Handling

| Сценарий | Поведение |
|-----------|-----------|
| tasks.md не найден | Error: "No tasks.md found. Run /speckit.tasks first." |
| Criteria template не найден | Error: "Criteria template '{name}' not found. Available: api-spec, code-gen, docs, config" |
| Git не инициализирован | Warning: "Git not detected. Artifact detection will use all source files." |
| User interruption (Ctrl+C) | Graceful shutdown: save state to run.json, show "Loop interrupted. Resume with /speckit.loop resume" |

### Requirements

| FR | Статус |
|----|--------|
| FR-001 (команда существует) | ✅ |
| FR-002 (implement → automatic loop) | ✅ |
| FR-004 (аргументы --criteria, --max-iterations, --threshold-a, --threshold-b) | ✅ |
| FR-005 (defaults) | ✅ |
| FR-017 (финальный отчёт) | ✅ |

---

## Command 2: `/speckit.loop`

### Signature

```bash
/speckit.loop [OPTIONS] [TASK_ALIAS]
```

### Arguments

| Аргумент | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `TASK_ALIAS` | string | ❌ | auto-detect | Task alias для loop (если не указан, detects из git branch или current.json) |
| `--criteria` | string | ❌ | auto-detect | Criteria template (api-spec, code-gen, docs, config) |
| `--max-iterations` | int | ❌ | 4 | Максимум итераций |
| `--threshold-a` | float | ❌ | 0.8 | Phase A threshold |
| `--threshold-b` | float | ❌ | 0.9 | Phase B threshold |
| `--artifact` | path | ❌ | auto-detect | Path к artifact файлу или directory |

### Modes

**Mode 1: New Loop** (нет активного loop)
```bash
/speckit.loop --criteria code-gen
```
Создаёт новый loop на текущем коде.

**Mode 2: Resume** (активный loop существует)
```bash
/speckit.loop resume
```
Продолжает активный loop из current.json.

**Mode 3: Status** (показать статус)
```bash
/speckit.loop status
```
Показывает статус активного loop.

**Mode 4: Stop** (остановить loop)
```bash
/speckit.loop stop [reason]
```
Останавливает активный loop с опциональной причиной.

**Mode 5: List** (список loops)
```bash
/speckit.loop list
```
Показывает все loops с их статусами.

**Mode 6: History** (история loop)
```bash
/speckit.loop history [TASK_ALIAS]
```
Показывает event history для loop.

**Mode 7: Clean** (удалить loop файлы)
```bash
/speckit.loop clean [TASK_ALIAS|--all]
```
Удаляет loop файлы (требует confirmation, отказывается для running loops).

### Behaviour (New Loop)

**Step 1: Detect Artifact**
```python
artifact = detect_artifact(
    from_git=True,  # git diff против HEAD~1
    fallback_from_tasks=True  # парсить tasks.md для file paths
)
```

**Step 2: Initialize Loop State**
```python
state = LoopState(
    run_id=f"{task_alias}-{timestamp}",
    task_alias=task_alias,
    status="running",
    iteration=1,
    max_iterations=max_iterations,
    phase="A",
    current_step="PLAN"
)
save_loop_state(state)
create_current_json(state)
```

**Step 3: Run Loop Iterations**
```python
while not should_stop(state):
    # EVALUATE
    result = evaluator.evaluate(artifact, criteria)
    state.evaluation = result
    state.current_score = result.score

    # CHECK PASS
    if result.passed and state.phase == "B":
        state.stop = {"passed": True, "reason": "threshold_reached"}
        break

    # CHECK STAGNATION
    if check_stagnation(state):
        state.stop = {"passed": False, "reason": "stagnation"}
        break

    # CHECK LIMIT
    if state.iteration >= state.max_iterations:
        state.stop = {"passed": False, "reason": "iteration_limit"}
        break

    # CRITIQUE + REFINE (только если failed)
    if not result.passed:
        critique = critic.generate(result.failed_rules)
        artifact = refiner.apply(artifact, critique)
        state.critique = critique

    # NEXT ITERATION
    state.iteration += 1
    state.last_score = state.current_score
    state.phase = "B" if result.passed else "A"
    save_loop_state(state)
```

**Step 4: Final Summary**
```
=== Quality Loop Complete ===

Iteration 3/4 | Phase B | Score: 0.88 | PASS
Stop Reason: iteration_limit
Distance to Success: 0.02 (threshold: 0.9, score: 0.88)

Failed Rules Remaining: 1
- correctness.tests: "Integration tests not implemented"

Changed Files: 5
- src/models/course.py (refined)
- src/repositories/course_repository.py (refined)
- src/services/course_service.py (refined)
- tests/integration/test_courses.py (created)
- tests/unit/test_course_repository.py (created)

Iterations: 3
Total Time: 3m 15s

Next Steps:
- Run /speckit.loop with --max-iterations 6 to continue
- OR manually fix remaining issues
```

### Output Examples

**Status output**:
```
=== Active Loop Status ===

Task Alias: courses-api-ddd
Run ID: courses-api-ddd-20260311-120000
Status: running
Iteration: 2/4
Phase: A
Current Score: 0.84
Last Score: 0.72
Step: EVALUATE
Started: 2025-03-11 10:30:00
Updated: 2025-03-11 10:31:00
```

**List output**:
```
=== Quality Loops ===

courses-api-ddd          | running   | 2/4  | Phase A | 0.84
user-auth-jwt            | stopped   | 4/4  | Phase B | 0.91
payment-gateway          | completed | 3/3  | Phase B | 0.93
frontend-ui-components   | failed    | 1/4  | Phase A | error
```

**History output**:
```
=== Loop History: courses-api-ddd ===

2025-03-11 10:30:00 | plan_created | Iteration 1 | Phase A
2025-03-11 10:30:30 | artifact_created | Iteration 1 | Phase A
2025-03-11 10:31:00 | evaluation_done | Iteration 1 | Phase A | Score: 0.72
2025-03-11 10:31:30 | refinement_done | Iteration 1 | Phase A
2025-03-11 10:32:00 | evaluation_done | Iteration 2 | Phase A | Score: 0.84
2025-03-11 10:32:30 | phase_switched | Iteration 2 | Phase A → B
```

### Requirements

| FR | Статус |
|----|--------|
| FR-003 (команда существует) | ✅ |
| FR-004 (аргументы) | ✅ |
| FR-005 (defaults) | ✅ |
| FR-017 (финальный отчёт) | ✅ |

---

## Command 3: `/speckit.implement` (Update)

### Changes

**Existing behaviour**: НЕ ИЗМЕНЯЕТСЯ (все задачи реализуются как раньше)

**New behaviour**: Добавляет recommendation section в конце stdout

### Implementation

```python
# В templates/commands/implement.md
# В самом конце команды, после summary:

def show_quality_loop_recommendation():
    """Show quality loop recommendation"""
    recommendation = """
---
## 🔄 Quality Loop Available

Implementation complete! You can further improve code quality with the **Quality Loop** feature.

### What is Quality Loop?

Quality Loop automatically evaluates your code against explicit rules, generates targeted feedback, and refines the implementation through multiple iterations.

**Benefits**:
- ✅ **Score-based evaluation**: Quantifiable quality metrics (0-1.0)
- ✅ **Automatic refinements**: Targeted fixes for failed rules
- ✅ **Iterative improvement**: Cycle continues until threshold reached

### How to Use

Run quality loop on the implemented code:

```bash
/speckit.loop --criteria code-gen --max-iterations 4
```

**Arguments explained**:
- `--criteria <template>`: Rule set (api-spec, code-gen, docs, config)
- `--max-iterations <N>`: Maximum cycles (default: 4)
- `--threshold-a <0.0-1.0>`: Phase A threshold (default: 0.8)
- `--threshold-b <0.0-1.0>`: Phase B threshold (default: 0.9)

**Auto-detect criteria**:
```bash
/speckit.loop
```

**Or combine implementation + quality loop**:
```bash
/speckit.implementloop
```
"""
    print(recommendation)
```

### Output Example

```
=== Implementation Complete ===

Tasks Completed: 5
Files Modified: 8
Tests Created: 3

Time: 2m 45s

---
## 🔄 Quality Loop Available

Implementation complete! You can further improve code quality...
[rest of recommendation]
```

### Requirements

| FR | Статус |
|----|--------|
| FR-006 (рекомендация показывается) | ✅ |
| FR-007 (формат рекомендации) | ✅ |

---

## Shared Contracts

### Criteria Template Detection

**Auto-detect algorithm**:
```python
def auto_detect_criteria(task_description: str = None) -> str:
    """Auto-detect criteria template"""
    if task_description:
        words = task_description.lower().split()
        for word in words:
            if word in AUTO_DETECT_MAPPING:
                return AUTO_DETECT_MAPPING[word]
    return "code-gen"  # default
```

**Mapping**:
```python
AUTO_DETECT_MAPPING = {
    "api": "api-spec",
    "endpoint": "api-spec",
    "openapi": "api-spec",
    "rest": "api-spec",
    "graphql": "api-spec",
    "code": "code-gen",
    "implementation": "code-gen",
    "function": "code-gen",
    "class": "code-gen",
    "docs": "docs",
    "readme": "docs",
    "documentation": "docs",
    "config": "config",
    "settings": "config",
    "configuration": "config",
}
```

### Score Calculation

**Formula**:
```python
def calculate_score(
    passed_rules: List[QualityRule],
    all_rules: List[QualityRule]
) -> float:
    """Calculate score: sum(passed_weights) / sum(all_weights)"""
    passed_weight = sum(r.weight for r in passed_rules)
    all_weight = sum(r.weight for r in all_rules)

    if all_weight == 0:
        return 1.0

    return passed_weight / all_weight
```

**Passed check**:
```python
def check_passed(
    score: float,
    threshold: float,
    failed_rules: List[QualityRule]
) -> bool:
    """Check if evaluation passed"""
    has_fail = any(r.severity == "fail" for r in failed_rules)
    return score >= threshold and not has_fail
```

### Stagnation Detection

**Algorithm**:
```python
def check_stagnation(
    current_score: float,
    last_score: float,
    stagnation_count: int,
    threshold: float = 0.02
) -> bool:
    """Check if score is stagnating"""
    delta = abs(current_score - last_score)

    if delta < threshold and not any_fail_rules():
        return stagnation_count + 1 >= 2

    return False
```

---

## Error Messages Reference

| Error Code | Message | Action |
|------------|---------|--------|
| `E_NO_TASKS` | "No tasks.md found. Run /speckit.tasks first." | Создать tasks.md |
| `E_NO_CRITERIA` | "Criteria template '{name}' not found. Available: {list}" | Использовать valid template |
| `E_NO_GIT` | "Git not detected. Artifact detection will use all source files." | Warning, continuation |
| `E_INTERRUPTED` | "Loop interrupted. Resume with /speckit.loop resume" | Resume loop |
| `E_RUNNING` | "Loop '{alias}' is already running. Stop it first or use a different alias." | Stop running loop |
| `E_NOT_FOUND` | "Loop '{alias}' not found. Run /speckit.loop list to see available loops." | Check alias |
| `E_CLEAN_RUNNING` | "Cannot clean running loop '{alias}'. Stop it first." | Stop loop first |

---

## Version History

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2025-03-11 | Initial version |
