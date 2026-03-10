# Quality Loop Documentation

**Feature**: Quality Loop Implementation
**Version**: 0.1.0
**Date**: 2025-03-11

---

## Overview

Quality Loop — это итеративная система улучшения качества кода, автоматически оценивающая артефакты против явных правил, генерирующая целевую обратную связь и применяющая исправления через несколько циклов.

**Inspired by**: Reflex Loop from [ai-factory](https://github.com/github/ai-factory)

---

## Architecture

### Components

```
src/specify_cli/quality/
├── models.py          # Data models (LoopState, EvaluationResult, etc.)
├── state.py           # LoopStateManager (persistence)
├── rules.py           # RuleManager (criteria templates)
├── scorer.py          # Scorer (score calculation)
├── evaluator.py       # Evaluator (rule checking)
├── critique.py        # Critique (feedback generation)
├── refiner.py         # Refiner (fix application)
├── loop.py            # QualityLoop (orchestration)
└── templates/         # Built-in criteria templates
    ├── api-spec.yml
    ├── code-gen.yml
    ├── docs.yml
    └── config.yml
```

### Data Flow

```
┌─────────────┐
│   Artifact  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Evaluator  │ ← Rules (CriteriaTemplate)
└──────┬──────┘
       │
       ▼
┌─────────────┐     Score ≥ Threshold?
│   Scorer    │ ────────────────────────┐
└─────────────┘                         │ No
       │ Yes                            │
       ▼                                │
   Complete                            ▼
                            ┌─────────────┐
                            │  Critique   │ ← Failed Rules
                            └──────┬──────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │   Refiner   │ ← LLM
                            └──────┬──────┘
                                   │
                                   ▼
                            ┌─────────────┐
                            │  Refined    │
                            │  Artifact   │
                            └─────────────┘
                                   │
                                   └─────► (repeat)
```

---

## Usage

### Command: `/speckit.loop`

**New loop**:
```bash
/speckit.loop --criteria code-gen --max-iterations 4
```

**Resume**:
```bash
/speckit.loop resume
```

**Status**:
```bash
/speckit.loop status
```

**Stop**:
```bash
/speckit.loop stop
```

**List all loops**:
```bash
/speckit.loop list
```

**History**:
```bash
/speckit.loop history <task_alias>
```

**Clean**:
```bash
/speckit.loop clean <task_alias>
```

### Command: `/speckit.implementloop`

Объединяет реализацию и quality loop:

```bash
/speckit.implementloop --criteria code-gen --max-iterations 4
```

**Phases**:
1. **Implementation**: Выполняет все задачи из tasks.md
2. **Quality Loop**: Автоматический запуск quality loop на изменённых файлах

---

## Criteria Templates

### Built-in Templates

| Template | Использование | Правила |
|----------|---------------|---------|
| `api-spec` | API specifications | CRUD endpoints, status codes, auth, parameters |
| `code-gen` | Code implementation | Tests, error handling, types, structure |
| `docs` | Documentation | Title, installation, usage, structure |
| `config` | Configuration files | Syntax, types, paths, secrets |

### Custom Templates

Создайте свой template в `.speckit/criteria/`:

```yaml
# .speckit/criteria/my-custom.yml
name: "My Custom Criteria"
version: 1.0
description: "Quality rules for my project"

phases:
  a:
    threshold: 0.8
    active_levels: ["A"]
  b:
    threshold: 0.9
    active_levels: ["A", "B"]

rules:
  - id: "my.rule1"
    description: "My specific requirement"
    severity: "fail"
    weight: 2
    phase: "A"
    check: "verify pattern"
    check_type: "content"
```

Использование:
```bash
/speckit.loop --criteria my-custom
```

---

## Score Calculation

**Formula**:
```
score = sum(passed_weights) / sum(all_active_weights)
```

**Severity weights**:
- `fail`: weight = 2
- `warn`: weight = 1
- `info`: weight = 0

**Pass condition**:
```
passed = (score >= threshold) AND (no fail-severity rules failed)
```

---

## Phase Model

### Phase A (Base Quality)
- **Threshold**: 0.8 (по умолчанию)
- **Active rules**: Базовые правила correctness
- **Focus**: Основная функциональность

### Phase B (Strict Quality)
- **Threshold**: 0.9 (по умолчанию)
- **Active rules**: Все правила (quality, performance, security)
- **Focus**: Production-ready код

---

## Stop Conditions

| Condition | Description |
|-----------|-------------|
| `threshold_reached` | Phase B threshold достигнут ✅ |
| `no_major_issues` | Нет fail-severity правил ✅ |
| `iteration_limit` | Достигнут лимит итераций |
| `stagnation` | Качество не улучшается (delta < 0.02 за 2 итерации) |
| `user_stop` | Остановлено пользователем |

---

## Persistence

### State Location

```
.speckit/evolution/
├── current.json           # Активный loop pointer
└── <task-alias>/
    ├── run.json           # Loop state
    ├── history.jsonl      # Event stream
    └── artifact.md        # Artifact content
```

### Resume After Interruption

Если loop был прерван (Ctrl+C, crash):

```bash
/speckit.loop resume
```

Loop восстановится из сохранённого состояния и продолжится.

---

## API Reference

### QualityLoop

```python
from specify_cli.quality import QualityLoop, RuleManager, Scorer, Evaluator, Critique, Refiner, LoopStateManager

rule_manager = RuleManager()
scorer = Scorer()
evaluator = Evaluator(rule_manager, scorer)
critique = Critique(max_issues=5)
refiner = Refiner(llm_client=current_llm)
state_manager = LoopStateManager()

loop = QualityLoop(
    rule_manager=rule_manager,
    evaluator=evaluator,
    scorer=scorer,
    critique=critique,
    refiner=refiner,
    state_manager=state_manager
)

result = loop.run(
    artifact=artifact_content,
    task_alias="my-feature",
    criteria_name="code-gen",
    max_iterations=4,
    threshold_a=0.8,
    threshold_b=0.9,
    llm_client=current_llm
)
```

### Return Value

```python
{
    "state": {...},           # Final LoopState
    "artifact": "...",        # Refined artifact
    "score": 0.92,            # Final score
    "passed": True,           # Whether passed
    "stop_reason": "threshold_reached"
}
```

---

## Examples

### Example 1: Successful Loop

```
Iteration 1/4 | Phase A | Score: 0.72 | FAIL
Failed: correctness.tests, quality.error_handling

Iteration 2/4 | Phase A | Score: 0.84 | PASS (Phase A → B)

Iteration 3/4 | Phase B | Score: 0.88 | FAIL
Failed: performance.caching

Iteration 4/4 | Phase B | Score: 0.92 | PASS

=== Quality Loop Complete ===
Stop Reason: threshold_reached
Score: 0.92
```

### Example 2: Stagnation

```
Iteration 1/4 | Phase A | Score: 0.75
Iteration 2/4 | Phase A | Score: 0.76 (delta: 0.01)
Iteration 3/4 | Phase A | Score: 0.76 (delta: 0.00) → Stagnation detected

=== Quality Loop Complete ===
Stop Reason: stagnation
```

---

## Troubleshooting

### Loop stuck at same score

**Problem**: Score не улучшается

**Solution**: Stagnation detection автоматически остановит loop через 2 итерации с delta < 0.02. Увеличьте `--max-iterations` или проверьте правила.

### Scanner not found

**Problem**: "Criteria template not found"

**Solution**:
```bash
# List available criteria
/speckit.loop list

# Use built-in criteria
/speckit.loop --criteria code-gen
```

### False positive on rule

**Problem**: Rule fails despite code being correct

**Solution**: Проверьте `history.jsonl` для деталей. Some rules могут быть слишком строгими. Создайте custom criteria template.

---

## Performance

| Метрика | Target |
|---------|--------|
| Rule loading | < 100ms |
| Score calculation | < 10ms |
| Evaluation (10 rules) | < 1s |
| Critique generation | < 2s |
| Full iteration | < 60s |

---

## See Also

- [Quickstart Guide](../specs/002-implement-quality-loop/quickstart.md)
- [CLI Commands Contract](../specs/002-implement-quality-loop/contracts/cli-commands.md)
- [Quality Evaluation Contract](../specs/002-implement-quality-loop/contracts/quality-eval.md)
