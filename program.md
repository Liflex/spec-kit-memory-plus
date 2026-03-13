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

## Current State (Post-Audit)

После 132 экспериментов проект имеет:
- **62 Python-файла** в `src/specify_cli/quality/`
- **627 классов/функций**
- **1 тест** для нового кода (из 62 модулей)

**Диагноз**: Feature bloat. Много подсистем без тестов и без реальных пользователей.

**Текущая фаза**: CONSOLIDATION — улучшаем качество существующего, не добавляем новое.

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

**Текущий бюджет: 62 файла (ПРЕВЫШЕН)**
**Целевой бюджет: 25-30 файлов**

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

### Phase 1: CLEANUP (текущий приоритет)

Цель: сократить 62 файла до 25-30.

```
1. Удалить неиспользуемые модули:
   - sms_integration.py, email_integration.py, webhook_integration.py
   - ab_testing.py, multi_variant_testing.py
   - quality_optimization.py (32 класса для Bayesian/Genetic!)
   - pareto_visualization.py (32 класса для ASCII-графиков)
   - quality_simulation.py
   - industry_presets.py, industry_detector.py

2. Объединить связанные модули:
   - gate_policies + gate_cascade + gate_policy_recommender
     + gate_policy_analytics + gate_policy_diff → gates.py
   - alert_aggregation + alert_deduplication + alert_escalation
     + alert_dashboard + quality_alerting → alerts.py (если оставляем)
   - quality_goals + goal_gates + goal_suggester
     + trend_goal_suggester → goals.py
   - json_report + markdown_report + html_report
     + report_exporter + report_aggregator → reports.py
   - result_card + live_progress → display.py

3. Рефакторить __init__.py:
   - Lazy imports вместо eager imports
   - Экспортировать только публичный API
```

### Phase 2: TESTING (после cleanup)

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

## Anti-Patterns (запрещённые направления)

Эти паттерны привели к bloat в Phase 1. НЕ повторяй:

### 1. Meta-System Cascade
```
BAD:  Gates → Gate Recommender → Gate Analytics → Gate Diff → Gate Cascade
GOOD: Gates (один файл, покрывает все нужды)
```

### 2. Integration Without Users
```
BAD:  "Добавлю SMS-уведомления для quality alerts"
GOOD: "Улучшу console output чтобы критические проблемы были заметны"
```

### 3. Premature Specialization
```
BAD:  "Создам пресеты для 8 индустрий (fintech, healthcare, gaming...)"
GOOD: "Улучшу auto-detection для 3 основных типов проектов"
```

### 4. Statistics Theater
```
BAD:  "Добавлю Bayesian optimization + ANOVA + Pareto front"
GOOD: "Добавлю простой trend: score растёт или падает"
```

### 5. Feature Without Test
```
BAD:  "Создал 3 новых модуля, записал результат в lessons.md"
GOOD: "Создал 1 модуль с 5 тестами, все проходят"
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
MAX_QUALITY_FILES = 30  # Target after cleanup
CURRENT_QUALITY_FILES = 62  # Needs reduction!

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

## Example Research Session (v2)

```
Агент: Читаю program.md... фаза CLEANUP.
Агент: В quality/ 62 файла, бюджет 30.
Агент: Experiment 133: Объединить 5 gate_* файлов в gates.py
Агент: Пишу test_gates.py с тестами для основных gate операций...
Агент: Тесты проходят. Объединяю 5 файлов в 1.
Агент: Complexity: 62 → 58 файлов. Прогресс.
Агент: Experiment 134: Удалить sms_integration.py (вне scope)
Агент: Проверяю зависимости... никто не импортирует.
Агент: Удаляю. 58 → 57 файлов.
Агент: Experiment 135: Улучшить правила в frontend.yml
Агент: Пишу тест: sample artifact → expected score.
Агент: Добавляю 2 правила, убираю 1 false positive.
Агент: Complexity: 57 (без изменений). Качество templates выросло.
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
Читай program.md. Текущая фаза: CLEANUP.
Начни с сокращения файлов в quality/.
```

Агент будет:
1. Читать memory
2. Выбрать файлы для удаления/объединения
3. Написать тесты для сохраняемой функциональности
4. Провести cleanup
5. Проверить что всё работает
6. Повторять пока complexity budget не достигнут
