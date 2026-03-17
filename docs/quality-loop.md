# Quality Loop Documentation

**Feature**: Quality Loop Implementation
**Version**: 0.3.0
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
    ├── api-spec.yml   # API specifications
    ├── code-gen.yml   # Code implementation
    ├── docs.yml       # Documentation
    ├── config.yml     # Configuration files
    ├── database.yml   # Database schemas
    ├── frontend.yml   # Frontend code
    ├── backend.yml    # Backend services
    ├── infrastructure.yml # DevOps & IaC
    ├── testing.yml    # Test files
    ├── security.yml   # Security review
    ├── performance.yml # Performance optimization
    └── ui-ux.yml      # UI/UX design
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

### Built-in Templates (11 шт.)

| Template | Описание | Правил | Ключевые проверки |
|----------|----------|--------|-------------------|
| `api-spec` | API спецификации | 10 | Endpoints, status codes, auth, параметры |
| `code-gen` | Генерация кода | 11 | Тесты, обработка ошибок, типы, структура |
| `docs` | Документация | 10 | Заголовок, установка, использование, структура |
| `config` | Конфигурационные файлы | 9 | Синтаксис, типы, пути, секреты |
| `database` | Базы данных | 10 | Primary/foreign keys, индексы, SQL injection |
| `frontend` | Frontend код | 10 | Компоненты, state management, routing |
| `backend` | Backend сервисы | 10 | API структура, service layer, DI |
| `infrastructure` | DevOps & IaC | 10 | Dockerfile, health checks, ресурсы |
| `testing` | Тестовые файлы | 10 | AAA паттерн, assertions, edge cases |
| `security` | Безопасность | 10 | Секреты, валидация, auth, XSS/SQLi |
| `performance` | Производительность | 10 | Кэширование, async, запросы, мониторинг |
| `ui-ux` | UI/UX дизайн | 10 | Accessibility, responsive, состояния |

### Детальное описание шаблонов

#### 1. `api-spec` — API спецификации

**Правила (Phase A/B)**:
- `correctness.crud_operations` — CRUD операции определены (fail, weight 2)
- `correctness.status_codes` — Правильные HTTP status codes (fail, weight 2)
- `security.authentication` — Аутентификация описана (fail, weight 2)
- `correctness.parameters` — Параметры запросов описаны (warn, weight 1)
- `quality.examples` — Примеры запросов/ответов (warn, weight 1)
- `correctness.error_responses` — Ошибки описаны (fail, weight 2)
- `quality.rate_limiting` — Rate limiting указан (info, weight 0)
- `security.authorization` — Авторизация описана (fail, weight 2)
- `quality.versioning` — Версионирование API (info, weight 0)
- `correctness.content_type` — Content-type указан (warn, weight 1)

**Влияние на loop**: Проверяет полноту API спецификации. Fail-правила (auth, status codes) блокируют прохождение. В Phase A проверяются базовые операции, Phase B добавляет versioning.

---

#### 2. `code-gen` — Генерация кода

**Правила (Phase A/B)**:
- `correctness.tests` — Тесты покрывают основной код (fail, weight 2)
- `correctness.error_handling` — Обработка ошибок (fail, weight 2)
- `correctness.types` — Типы данных определены (warn, weight 1)
- `quality.naming` — Консистентное именование (warn, weight 1)
- `correctness.structure` — Модульная структура (warn, weight 1)
- `performance.complexity` — Не слишком сложная логика (warn, weight 1)
- `quality.comments` — Комментарии для сложного кода (info, weight 0)
- `security.input_validation` — Валидация входных данных (fail, weight 2)
- `correctness.async` — Async для I/O операций (warn, weight 1)
- `quality.dependencies` — Зависимости чистые (info, weight 0)
- `correctness.entry_point` — Точка входа определена (fail, weight 2)

**Влияние на loop**: Самый строгий шаблон для генерации кода. Fail-правила (тесты, ошибки, валидация) требуют исправления. В Phase A базовое качество, Phase B добавляет сложность и комментарии.

---

#### 3. `docs` — Документация

**Правила (Phase A/B)**:
- `correctness.title` — Заголовок описывает суть (fail, weight 2)
- `correctness.installation` — Инструкция по установке (fail, weight 2)
- `correctness.usage` — Примеры использования (fail, weight 2)
- `quality.structure` — Логичная структура (warn, weight 1)
- `correctness.code_examples` — Код примеры работают (warn, weight 1)
- `quality.prerequisites` — Предварительные требования (warn, weight 1)
- `correctness.api_reference` — API документация (warn, weight 1)
- `quality.troubleshooting` — Раздел troubleshooting (info, weight 0)
- `quality.links` — Ссылки рабочие (warn, weight 1)
- `correctness.summary` — Краткое описание (fail, weight 2)

**Влияние на loop**: Проверяет полноту документации. Fail-правила (заголовок, установка, использование) критичны. Phase A — базовая документация, Phase B — troubleshooting и ссылки.

---

#### 4. `config` — Конфигурационные файлы

**Правила (Phase A/B)**:
- `correctness.syntax` — Валидный синтаксис (fail, weight 2)
- `correctness.types` — Типы данных правильные (warn, weight 1)
- `security.secrets` — Секреты не захардкодены (fail, weight 2)
- `correctness.paths` — Пути корректные (warn, weight 1)
- `quality.defaults` — Значения по умолчанию (warn, weight 1)
- `correctness.required_fields` — Обязательные поля (fail, weight 2)
- `quality.comments` — Комментарии для сложных значений (info, weight 0)
- `security.permissions` — Права доступа (warn, weight 1)
- `correctness.environment_vars` — Переменные окружения (warn, weight 1)

**Влияние на loop**: Проверяет конфигурационные файлы. Критичны: синтаксис, секреты, обязательные поля. Phase A — базовая валидность, Phase B — права доступа.

---

#### 5. `database` — Базы данных

**Правила (Phase A/B)**:
- `correctness.primary_key` — Primary key определён (fail, weight 2)
- `correctness.foreign_keys` — Foreign keys с ограничениями (fail, weight 2)
- `correctness.indexes` — Индексы на частых запросах (warn, weight 1)
- `correctness.data_types` — Адекватные типы данных (warn, weight 1)
- `correctness.not_null` — NOT NULL на важных полях (warn, weight 1)
- `security.sql_injection` — Защита от SQL injection (fail, weight 2)
- `performance.denormalization` — Денормализация для read-heavy (info, weight 0)
- `correctness.timestamps` — created_at/updated_at (warn, weight 1)
- `quality.migrations` — Миграции упорядочены (warn, weight 1)
- `quality.constraints` — Constraints именованы (info, weight 0)

**Влияние на loop**: Проверяет схему базы данных. Критичны: ключи, SQL injection. Phase A — базовая схема, Phase B — оптимизация и миграции.

---

#### 6. `frontend` — Frontend код

**Правила (Phase A/B)**:
- `correctness.components` — Компонентная архитектура (fail, weight 2)
- `correctness.state_management` — State management (fail, weight 2)
- `quality.props_validation` — PropTypes/TS interfaces (warn, weight 1)
- `correctness.routing` — Routing определён (fail, weight 2)
- `quality.responsive` — Responsive дизайн (warn, weight 1)
- `accessibility.alt_text` — Alt текст для изображений (warn, weight 1)
- `performance.lazy_loading` — Code splitting (info, weight 0)
- `quality.semantic_html` — Семантический HTML (warn, weight 1)
- `security.xss_prevention` — Защита от XSS (fail, weight 2)
- `quality.css_organization` — CSS организован (warn, weight 1)

**Влияние на loop**: Проверяет frontend код. Критичны: компоненты, state, routing, XSS. Phase A — базовая структура, Phase B — оптимизация.

---

#### 7. `backend` — Backend сервисы

**Правила (Phase A/B)**:
- `correctness.api_structure` — RESTful API структура (fail, weight 2)
- `correctness.service_layer` — Business logic в service layer (fail, weight 2)
- `correctness.dependency_injection` — DI используется (warn, weight 1)
- `quality.error_responses` — Правильные error responses (fail, weight 2)
- `correctness.validation` — Валидация входных данных (fail, weight 2)
- `quality.logging` — Структурированный logging (warn, weight 1)
- `security.authentication` — Аутентификация на endpoints (fail, weight 2)
- `security.authorization` — Authorization checks (fail, weight 2)
- `performance.caching` — Кэширование (info, weight 0)
- `performance.async_operations` — Async для I/O (warn, weight 1)

**Влияние на loop**: Проверяет backend сервисы. Критичны: API структура, validation, auth. Phase A — базовая логика, Phase B — производительность.

---

#### 8. `infrastructure` — DevOps & IaC

**Правила (Phase A/B)**:
- `correctness.dockerfile` — Dockerfile best practices (fail, weight 2)
- `correctness.environment_variables` — ENV документированы (warn, weight 1)
- `security.secrets_management` — Секреты не в коде (fail, weight 2)
- `correctness.health_checks` — Health check endpoints (fail, weight 2)
- `quality.resource_limits` — Лимиты ресурсов (warn, weight 1)
- `correctness.persistent_storage` — Persistent volumes (warn, weight 1)
- `performance.scaling` — Horizontal scaling (info, weight 0)
- `quality.monitoring` — Мониторинг настроен (warn, weight 1)
- `security.network_policies` — Network policies (info, weight 0)
- `quality.restart_policy` — Restart policies (warn, weight 1)

**Влияние на loop**: Проверяет инфраструктуру. Критичны: Dockerfile, секреты, health checks. Phase A — базовая инфраструктура, Phase B — масштабирование.

---

#### 9. `testing` — Тестовые файлы

**Правила (Phase A/B)**:
- `correctness.test_structure` — AAA паттерн (warn, weight 1)
- `correctness.assertions` — Asserts с сообщениями (fail, weight 2)
- `quality.test_isolation` — Тесты изолированы (fail, weight 2)
- `correctness.edge_cases` — Граничные случаи (warn, weight 1)
- `quality.mocks_usage` — Mocks правильно (warn, weight 1)
- `correctness.error_tests` — Тесты ошибок (fail, weight 2)
- `quality.coverage` — Coverage ≥ 80% (warn, weight 1)
- `performance.test_speed` — Тесты быстрые (info, weight 0)
- `quality.integration_tests` — Интеграционные тесты (warn, weight 1)
- `quality.test_naming` — Названия описательные (warn, weight 1)

**Влияние на loop**: Проверяет качество тестов. Критичны: assertions, изоляция, error tests. Phase A — базовые тесты, Phase B — интеграционные.

---

#### 10. `security` — Безопасность

**Правила (Phase A/B)**:
- `security.no_hardcoded_secrets` — Секреты не захардкодены (fail, weight 2)
- `security.input_validation` — Валидация входных данных (fail, weight 2)
- `security.sql_injection_prevention` — Защита от SQLi (fail, weight 2)
- `security.xss_prevention` — Защита от XSS (fail, weight 2)
- `security.authentication` — Аутентификация (fail, weight 2)
- `security.authorization` — Авторизация (fail, weight 2)
- `security.https_only` — HTTPS only (warn, weight 1)
- `security.csrf_protection` — CSRF защита (warn, weight 1)
- `security.error_handling` — Безопасная обработка ошибок (warn, weight 1)
- `security.dependencies` — Зависимости без уязвимостей (warn, weight 1)

**Влияние на loop**: Проверяет безопасность. Все fail-правила (6 шт.) критичны и блокируют прохождение. Phase A — базовая безопасность, Phase B — advanced (HTTPS, CSRF).

---

#### 11. `performance` — Производительность

**Правила (Phase A/B)**:
- `performance.caching` — Кэширование (warn, weight 1)
- `performance.async_operations` — Async для I/O (warn, weight 1)
- `performance.query_optimization` — Оптимизированные запросы (warn, weight 1)
- `performance.lazy_loading` — Lazy loading (info, weight 0)
- `performance.pagination` — Пагинация (warn, weight 1)
- `performance.compression` — Сжатие данных (info, weight 0)
- `performance.connection_pooling` — Connection pool (warn, weight 1)
- `performance.batch_operations` — Batch операции (warn, weight 1)
- `performance.memory_leaks` — Нет утечек памяти (fail, weight 2)
- `performance.monitoring` — Мониторинг (warn, weight 1)

**Влияние на loop**: Проверяет производительность. Критично только memory leaks. Остальное — рекомендации. Phase A — базовая оптимизация, Phase B — advanced (pooling, batching).

---

#### 12. `ui-ux` — UI/UX дизайн

**Правила (Phase A/B)**:
- `accessibility.alt_text` — Alt текст (warn, weight 1)
- `accessibility.keyboard_navigation` — Клавиатурная навигация (warn, weight 1)
- `accessibility.contrast` — Контраст WCAG AA (warn, weight 1)
- `accessibility.aria_labels` — ARIA метки (warn, weight 1)
- `quality.responsive_design` — Responsive дизайн (warn, weight 1)
- `quality.loading_states` — Состояния загрузки (warn, weight 1)
- `quality.empty_states` — Empty states (warn, weight 1)
- `quality.error_states` — Error states (fail, weight 2)
- `quality.consistent_spacing` — Консистентные отступы (info, weight 0)
- `quality.feedback_timing` — Быстрый feedback (warn, weight 1)

**Влияние на loop**: Проверяет UI/UX. Критично только error states. Остальное — рекомендации. Phase A — базовая UX, Phase B — детали.

---

### Как критерии влияют на Quality Loop

#### Severity Levels (Важность)

| Severity | Weight | Описание | Влияние на loop |
|----------|--------|----------|-----------------|
| `fail` | 2 | Критическое правило | **Блокирует прохождение** даже при хорошем score |
| `warn` | 1 | Предупреждение | Снижает score, но не блокирует |
| `info` | 0 | Информация | Не влияет на score, только для отслеживания |

#### Score Calculation

```
score = sum(passed_weights) / sum(all_active_weights)

Пример:
- 10 правил active в Phase A
- 5 passed: 3 fail (weight 2) + 2 warn (weight 1) = 8
- 2 failed: 1 fail + 1 warn = 3
- score = 8 / (8 + 3) = 0.73 → FAIL

Даже если score ≥ threshold:
- ЛЮБОЕ fail-severity правило = FAIL
```

#### Phase Transitions

```
Phase A (threshold 0.8):
  - Активны только Phase A правила
  - Базовые проверки correctness

Phase B (threshold 0.9):
  - Активны Phase A + Phase B правила
  - Строгие проверки quality/performance/security
```

#### Auto-detection

Keywords → Criteria:
- "api", "endpoint", "rest" → `api-spec`
- "code", "implementation", "function" → `code-gen`
- "docs", "readme" → `docs`
- "config", "settings" → `config`
- "database", "sql", "schema" → `database`
- "frontend", "react", "component" → `frontend`
- "backend", "service", "api" → `backend`
- "docker", "deploy", "infrastructure" → `infrastructure`
- "test", "testing", "unit" → `testing`
- "security", "auth", "authorization" → `security`
- "performance", "cache", "optimization" → `performance`
- "ux", "accessibility", "responsive" → `ui-ux`

---

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

**Пример**:
```
Phase A (threshold 0.8), 10 правил active:
- Passed: correctness.tests (fail), types (warn), structure (warn)
  → weights: 2 + 1 + 1 = 4
- Failed: error_handling (fail), async (warn)
  → weights: 2 + 1 = 3
- Score: 4 / (4 + 3) = 0.57 → FAIL
- Также FAIL из-за fail-severity правила error_handling
```

---

## Phase Model

### Phase A (Base Quality)
- **Threshold**: 0.8 (по умолчанию)
- **Active rules**: Только Phase A правила
- **Focus**: Основная функциональность и correctness
- **Severity**: Все fail-правила критичны

### Phase B (Strict Quality)
- **Threshold**: 0.9 (по умолчанию)
- **Active rules**: Phase A + Phase B правила
- **Focus**: Production-ready качество
- **Severity**: Дополнительные проверки quality/performance/security

**Переход**: Phase A → Phase B происходит автоматически когда все Phase A правила pass.

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

### Example 3: Security Review

```
/speckit.loop --criteria security --max-iterations 6

Iteration 1/6 | Phase A | Score: 0.60 | FAIL
Failed: security.input_validation, security.sql_injection_prevention

Iteration 2/6 | Phase A | Score: 0.80 | PASS (Phase A → B)

Iteration 3/6 | Phase B | Score: 0.85 | FAIL
Failed: security.csrf_protection

Iteration 4/6 | Phase B | Score: 0.90 | PASS

=== Quality Loop Complete ===
Stop Reason: threshold_reached
Score: 0.90
All security checks passed ✅
```

---

## Troubleshooting

### Loop stuck at same score

**Problem**: Score не улучшается

**Solution**: Stagnation detection автоматически остановит loop через 2 итерации с delta < 0.02. Увеличьте `--max-iterations` или проверьте правила.

### Criteria template not found

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

**Solution**: Проверьте `history.jsonl` для деталей. Некоторые правила могут быть слишком строгими. Создайте custom criteria template.

### Too many failures

**Problem**: Loop не проходит даже после нескольких итераций

**Solution**:
1. Проверьте failed rules — это fail или warn severity?
2. Fail-правила требуют исправления
3. Попробуйте другой criteria template
4. Создайте custom template с подходящими правилами

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
