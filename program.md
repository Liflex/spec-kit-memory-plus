# AutoResearch Program: Spec Kit (v2 — Post-Audit)

> Based on [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
> Adapted for Spec Kit product improvement
> **v2**: Скорректировано после аудита 132 экспериментов. Фокус на качество, не количество.

---

## Overview

Вы — AI-исследователь в проекте **Spec Kit**. Ваша цель — автономно улучшать продукт через итеративные эксперименты.

**Ключевая идея**: Вы не пишете код как обычно. Вместо этого вы:
1. Читаете `program.md` (этот файл)
2. Предлагаете улучшение
3. **Проверяете: не дублирует ли это существующую функциональность?**
4. Запускаете эксперимент
5. **Пишете тест**
6. Оцениваете результат
7. Сохраняете или отбрасываете изменения
8. Повторяете

---

## Current State (Post-Audit + Cleanup)

После 132 экспериментов и ручного cleanup:
- **31 Python-файл** в `src/specify_cli/quality/` (было 62, сокращено вдвое)
- **58/58 quality tests passing** (было 48/58)
- **338 total tests passing** (было 328)

**Что удалено:** sms_integration, email_integration, webhook_integration, ab_testing, multi_variant_testing, quality_optimization, pareto_visualization, quality_simulation, industry_detector, alert_aggregation, alert_deduplication, alert_escalation, alert_dashboard, gate_policy_analytics, gate_policy_diff, report_aggregator, history_dashboard, correlation_analysis, quality_trend_analytics, smart_config_recommender и другие.

**Что объединено:** json_schema→json_report, template_integration→template_registry, gate_cascade+gate_policy_recommender→gate_policies, markdown_report→report_exporter.

**Диагноз**: Feature bloat ЧАСТИЧНО устранён. Ядро работает, тесты проходят. Остаётся много подсистем которые сомнительно нужны (quality_plans, quality_benchmarking, feedback_loop, goal_suggester) — но они стабильны и не мешают.

**Текущая фаза**: TESTING + CORE IMPROVEMENT — улучшаем тесты и ядро, не добавляем новое.

---

## Scope Boundaries (CRITICAL)

### Что является продуктом Spec Kit

Spec Kit — это **CLI-инструмент для оценки качества software specifications**. Его основная ценность:

1. **Quality Loop** — итеративная оценка и улучшение спецификаций (evaluate -> score -> critique -> refine)
2. **Criteria Templates** — правила оценки по доменам (backend, frontend, security, etc.)
3. **Priority Profiles** — взвешенное скоринг для разных типов проектов
4. **Reports** — вывод результатов (console, JSON, HTML, Markdown)
5. **Quality History** — отслеживание прогресса
6. **Quality Gates** — pass/fail решения для CI/CD

### Что НЕ является продуктом Spec Kit

```
STOP. Не добавляй эти фичи:

- Системы уведомлений (SMS, Email, Webhook, Slack) — это задача внешних инструментов
- Enterprise monitoring (dashboards, alerting pipelines) — это Grafana/Datadog
- Статистические движки (Bayesian optimization, genetic algorithms, ANOVA) — overkill для CLI tool
- Индустриальные пресеты (Fintech/Healthcare/Gaming) — преждевременная специализация
- A/B и multi-variant testing — нет пользовательской базы для тестирования
- Pareto front visualization — решает несуществующую проблему
```

**Правило**: Если фича требует отдельного сервера, базы данных, или подписки на внешний сервис — она вне scope.

---

## What You Can Modify

```
МОЖНО:
- src/specify_cli/quality/     # Ядро: loop, scorer, evaluator, rules, critique, refiner
- src/specify_cli/quality/templates/  # Criteria templates (YAML)
- tests/                       # Тесты (ПРИОРИТЕТ!)
- templates/commands/           # CLI command templates
- README.md, CHANGELOG.md      # Документация
- program.md                   # Этот файл

ЗАПРЕЩЕНО (без явного запроса):
- git push / git commit --amend / git reset --hard
- Удаление .claude/memory/
- Изменения ВНЕ проекта
- Создание НОВЫХ модулей в quality/ (см. "Complexity Budget")
```

**Safety Checks** (перед любой опасной операцией):
1. **Git операции** — всегда спрашивать подтверждение
2. **Удаление файлов** — всегда спрашивать подтверждение
3. **Крупные рефакторинги** — создать backup ветку

---

## Complexity Budget

**Текущий бюджет: 31 файл (в пределах нормы)**
**Целевой бюджет: 25-30 файлов**
**Жёсткий лимит: 35 файлов (НЕ ПРЕВЫШАТЬ)**

### Правило добавления

Прежде чем создать НОВЫЙ файл в `src/specify_cli/quality/`:

1. **Можно ли добавить в существующий файл?** — Если да, добавь туда
2. **Можно ли заменить 2+ существующих файла?** — Если да, объедини и удали старые
3. **Есть ли тесты для этого?** — Если нет, напиши тест СНАЧАЛА
4. **Кто будет пользователем?** — Если не можешь назвать конкретный use case, не создавай

**Net complexity rule**: Каждый новый файл ДОЛЖЕН сопровождаться удалением или объединением минимум одного существующего.

---

## Experiment Loop

### 1. Generate Idea

Прочитайте память (`.claude/memory/*.md`) для контекста.

**Перед генерацией идеи, задай себе вопросы:**
- Это улучшает ЯДРО (loop, scorer, evaluator, rules, critique, refiner)?
- Это улучшает TEMPLATES (правила оценки)?
- Это улучшает ТЕСТЫ (покрытие, надёжность)?
- Это УПРОЩАЕТ существующий код (рефакторинг, удаление)?

Если ответ на все 4 — "нет", **не делай этот эксперимент**.

### 2. Propose Change

```markdown
## Experiment N: {Title}

**Hypothesis**: {Что ожидаем улучшить}
**Target**: {Какой компонент изменяем}
**Metric**: {Как измеряем успех}
**Complexity Impact**: {+N файлов / -N файлов / 0 (рефакторинг)}
**Test Plan**: {Какой тест напишем}
```

### 3. Write Test FIRST

**ОБЯЗАТЕЛЬНО**: Перед внесением изменения напиши тест, который проверяет ожидаемое поведение.

```python
# tests/quality/test_{feature}.py
def test_feature_basic():
    """Базовый тест: фича работает"""
    ...

def test_feature_edge_case():
    """Edge case: фича не ломается на граничных данных"""
    ...
```

Запусти тест — он должен ПАДАТЬ (red phase).

### 4. Apply Change

Внесите изменение. Запустите тест — он должен ПРОХОДИТЬ (green phase).

### 5. Evaluate

Запустите ВСЕ тесты:

```bash
python -m pytest tests/ -v
```

**Metrics**:
- Все тесты проходят (включая старые)
- Complexity impact соответствует заявленному
- Нет новых файлов без удаления старых (или обоснование)

### 6. Decision

**Keep if**:
- Все тесты проходят
- Complexity budget не превышен
- Улучшение измеримо (score, coverage, simplicity)

**Discard if**:
- Тесты не написаны
- Добавляет сложность без удаления существующей
- Фича вне scope (см. "Scope Boundaries")
- Создаёт мета-систему поверх мета-системы
- Нет конкретного пользовательского use case

### 7. Log Result

Запись в memory — **только если эксперимент содержит переиспользуемый insight**.

**НЕ записывай:**
- "Добавил модуль X, интегрировал с Y" — это changelog, не lesson
- Описание кода, который и так в репозитории
- Записи длиннее 30 строк

**Записывай:**
- Неочевидные баги и их решения
- Паттерны, которые работают в 3+ местах
- Архитектурные решения с обоснованием

---

## Research Areas Priority

### Phase 1: CLEANUP (ВЫПОЛНЕНО)

~~Цель: сократить 62 файла до 25-30.~~ **Достигнуто: 31 файл.**

Удалены 30+ модулей (SMS, Email, Webhook, Bayesian, Pareto, ANOVA и т.д.).
Объединены 4 группы модулей. Все тесты проходят.

**Возможные дальнейшие объединения (если нужно до 25):**
- quality_goals + goal_gates + goal_suggester → goals.py
- result_card + live_progress + terminal_colors → display.py
- quality_anomaly + quality_benchmarking → analytics.py

### Phase 2: TESTING (ТЕКУЩИЙ ПРИОРИТЕТ)

Цель: тестовое покрытие для всех оставшихся модулей.

```
1. Unit тесты для ядра:
   - test_loop.py (integration)
   - test_scorer.py (расширить)
   - test_evaluator.py (расширить)
   - test_rules.py (расширить)

2. Тесты для подсистем:
   - test_gates.py
   - test_goals.py
   - test_reports.py
   - test_history.py

3. Integration тесты:
   - Полный цикл: load template → evaluate → score → report
   - CI/CD сценарий: evaluate → gate decision → exit code
```

### Phase 3: CORE IMPROVEMENT (после тестов)

Цель: улучшить качество того, что делает продукт ЛУЧШЕ для пользователя.

```
1. Улучшение critique.py:
   - Более точные промпты для критики
   - Контекстно-зависимая критика (разные подходы для разных доменов)

2. Улучшение templates:
   - Более точные правила (меньше false positives)
   - Примеры прохождения/непрохождения для каждого правила
   - Тестовые артефакты для валидации правил

3. Улучшение scorer.py:
   - Более справедливая калибровка весов
   - Объяснение почему получен конкретный score

4. CLI UX:
   - Понятные error messages
   - Helpful defaults
   - Минимум обязательных параметров
```

---

## Anti-Patterns (CRITICAL — запрещённые направления)

Эти паттерны привели к bloat с 10 до 62 файлов за 132 эксперимента. ВСЕ были повторены НЕСМОТРЯ на предупреждения. НЕ повторяй.

### 1. Meta-System Cascade
```
БЫЛО: Gates → Gate Recommender → Gate Analytics → Gate Diff → Gate Cascade (5 файлов)
БЫЛО: Alerts → Alert Aggregation → Alert Dedup → Alert Escalation → Alert Dashboard (5 файлов)
БЫЛО: Optimization → Pareto → Adaptive → Warm Start → Ensemble → Visualization (6 файлов)
СТАЛО: gates.py (1 файл). Остальное удалено.
```

### 2. Integration Without Users
```
БЫЛО: SMS notifications, Email notifications, Multi-Provider SMS Routing, Webhook Integration
ИТОГО: 4 модуля для 0 пользователей. Всё удалено.
ПРАВИЛО: Если фича требует сервер, API-ключ, или внешний сервис — она ВНЕ scope.
```

### 3. Premature Specialization
```
БЫЛО: 8 Industry presets (fintech, healthcare, gaming, government, education, iot, ecommerce, saas)
БЫЛО: Industry auto-detector с keyword scanning, dependency analysis, config detection
ИТОГО: 2 модуля для функционала который никто не просил. Удалено.
```

### 4. Statistics Theater
```
БЫЛО: Bayesian optimization, Genetic algorithms, Simulated Annealing, Response Surface Modeling,
      ANOVA, Tukey HSD, Bonferroni correction, Pareto front, Knee detection, Hypervolume metric
ИТОГО: 32 класса в quality_optimization.py. Для CLI tool. Удалено.
ПРАВИЛО: Если для объяснения фичи нужна PhD — она не нужна в CLI tool.
```

### 5. Feature Without Test
```
БЫЛО: 62 модуля, 627 классов, 1 тест. Соотношение 1:627.
СТАЛО: 31 модуль, 58 тестов. Улучшение, но далеко от идеала.
ПРАВИЛО: Нет теста — нет фичи. Тест ПЕРЕД кодом.
```

### 6. Lessons.md Bloat
```
БЫЛО: 3021 строк, 43 записи по 50-170 строк каждая, ВСЕ [IMPORTANT]
СТАЛО: ~100 строк, 7 записей по 10-20 строк каждая
ПРАВИЛО: Lesson ≠ changelog. Max 30 строк на запись. Max 10 [CRITICAL], max 20 [IMPORTANT].
```

### 7. Self-Reflection Loop
```
BAD:  "Улучшу процесс автоисследования" / "Оптимизирую промпты AutoResearch"
BAD:  "Создам фреймворк для генерации фреймворков"
BAD:  "Проанализирую как я мог бы лучше анализировать"
GOOD: Конкретное изменение кода с тестом.
ПРАВИЛО: Каждый эксперимент ОБЯЗАН произвести конкретное изменение (код/баг/тест/документация).
```

---

## Fixed Constants (prepare.py)

```python
# Fixed constants — DO NOT modify during experiments
PROJECT_NAME = "spec-kit"

# Quality Loop settings
DEFAULT_ITERATIONS = 4
DEFAULT_THRESHOLD_A = 0.8
DEFAULT_THRESHOLD_B = 0.9

# Criteria templates (built-in)
BUILTIN_CRITERIA = [
    "api-spec", "code-gen", "docs", "config",
    "database", "frontend", "backend", "infrastructure",
    "testing", "security", "performance", "ui-ux", "live-test"
]

# Complexity budget
MAX_QUALITY_FILES = 35  # Hard limit
TARGET_QUALITY_FILES = 25  # Ideal target
CURRENT_QUALITY_FILES = 31  # After cleanup (was 62)

# Evaluation budget (seconds)
EVALUATION_BUDGET = 60  # per iteration
```

---

## Stop Conditions

**Остановись если:**
- Complexity budget достигнут (30 файлов) и все тесты проходят
- 3 последовательных эксперимента не дали измеримых улучшений
- Пользователь явно попросил остановиться

**НЕ делай эксперимент если:**
- Он добавляет сложность без удаления существующей
- Нет конкретного пользовательского use case
- Нет плана тестирования
- Фича вне scope (см. "Scope Boundaries")
- Создаёт мета-систему поверх существующей мета-системы

**Качество > Количество**. Один хорошо протестированный рефакторинг ценнее 10 новых модулей.

---

## Example Research Session (v3)

```
Агент: Читаю program.md... фаза TESTING + CORE IMPROVEMENT.
Агент: В quality/ 31 файл, бюджет 25-35. Тесты: 58/58 quality, 338 total.
Агент: Experiment 133: Написать тесты для quality_history.py
Агент: Пишу test_history.py с 8 тестами (add_run, get_stats, compare)...
Агент: Тесты проходят. Coverage quality_history: 0 → 65%.
Агент: Experiment 134: Улучшить правила в frontend.yml
Агент: Пишу тест: sample artifact → expected score.
Агент: Убираю 1 false positive, добавляю 1 более точное правило.
Агент: Complexity: 31 (без изменений). Качество templates выросло.
Агент: Experiment 135: Улучшить critique prompts для security domain
Агент: Пишу тест: critique должна находить missing auth checks.
Агент: Улучшаю промпт в critique.py. Тест проходит.
```

---

## Memory Entry Rules (v2)

### Размер записи

- **Максимум 30 строк** на запись в lessons.md/patterns.md
- **Без дублирования кода** — код уже в репозитории
- **Без пересказа эксперимента** — это делает CHANGELOG

### Что записывать

```
ЗАПИСЫВАЙ:
- Неочевидный баг и его root cause (5-10 строк)
- Паттерн, переиспользуемый в 3+ местах (10-15 строк)
- Архитектурное решение с обоснованием "почему" (10-15 строк)

НЕ ЗАПИСЫВАЙ:
- "Создал модуль X с классами A, B, C" — это git log
- "Интегрировал X с Y через Z" — это changelog
- Полные code snippets — они в коде
- Каждый эксперимент — только значимые insights
```

### Метки приоритета

**[CRITICAL]** — Без этого непонятна архитектура проекта (max 10 записей)
**[IMPORTANT]** — Значимый переиспользуемый паттерн (max 20 записей)
**Без метки** — Не попадает в контекст AutoResearch

### Ротация

Когда lessons.md превышает 500 строк:
1. Удали записи без меток
2. Объедини похожие записи
3. Сократи записи до 15 строк каждая

---

## How to Start

```
Hi! Запусти автоисследование Spec Kit.
Читай program.md. Текущая фаза: TESTING + CORE IMPROVEMENT.
Cleanup завершён (31 файл). Фокус на тестах и улучшении ядра.
```

Агент будет:
1. Читать memory и program.md
2. Выбрать модуль без тестов → написать тесты
3. Или улучшить ядро (critique, templates, scorer) с тестом
4. Проверить что ВСЕ тесты проходят
5. НЕ создавать новых файлов
6. Повторять
