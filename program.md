# AutoResearch Program: Spec Kit (v2 — Post-Audit)

> Based on [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
> Adapted for Spec Kit product improvement
> **v3**: Фокус на реальные улучшения продукта, не бесконечное тестирование.

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

## Current State

- **31 Python-файл** в `src/specify_cli/quality/` (бюджет: 25-35)
- **1472 quality tests passing**, 1752 total
- Ядро стабильно, тесты в хорошем состоянии

**Текущая фаза**: PRODUCT IMPROVEMENT — реальные улучшения продукта для пользователей.

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
7. **Security** — автоматическая проверка спецификаций на security anti-patterns

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
- docs/                        # Руководства и справочники
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

**Текущий бюджет: 22 файла (после консолидации quality-скиллов)**
**Целевой бюджет: 20-25 файлов**
**Жёсткий лимит: 30 файлов (НЕ ПРЕВЫШАТЬ)**

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
- Это делает продукт ПОЛЕЗНЕЕ для пользователя?
- Это улучшает ЯДРО (loop, scorer, evaluator, rules, critique, refiner)?
- Это улучшает TEMPLATES (правила оценки, security checks)?
- Это УПРОЩАЕТ существующий код (рефакторинг, удаление)?
- Это исправляет реальный БАГ или edge case?

Если ответ на все — "нет", **не делай этот эксперимент**.

**Разнообразие**: Не делай 5 экспериментов подряд одного типа. Чередуй направления.

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

## Research Areas (все активны, чередовать)

### 1. Security & Safety

Автоматическая проверка спецификаций на security-проблемы:

```
- Улучшить security.yml template: добавить проверки на OWASP Top 10
- Проверка auth/authz разделов в спецификациях
- Детекция hardcoded secrets, insecure defaults в spec-файлах
- Проверка что spec описывает rate limiting, input validation
- Исследовать best practices (можно искать в интернете) и добавить как правила
```

### 2. Core Quality Improvement

Улучшить то, что делает продукт лучше для пользователя:

```
- critique.py: более точные промпты, контекстно-зависимая критика
- scorer.py: справедливая калибровка весов, объяснение score
- templates/*.yml: точнее правила, меньше false positives
- Исправление реальных багов и edge cases
```

### 3. CLI UX & Quality of Life

```
- Понятные error messages вместо tracebacks
- Helpful defaults — минимум обязательных параметров
- Быстрый старт: `speckit init` → готовая конфигурация
- Прогресс и feedback при долгих операциях
```

### 4. Documentation

```
- docs/usage-guide.md — главный справочник "как пользоваться"
- Decision guide: "я хочу X → используй Y"
- Полные сценарии от проблемы до результата
- README: краткий, со ссылками на usage-guide
```

### 5. Template Quality

```
- Исследовать реальные спецификации (open source) и проверить что правила адекватны
- Уменьшить false positives в существующих templates
- Добавить примеры pass/fail для каждого правила
- Новые домены если есть реальный use case
```

### 6. Bug Fixes & Refactoring

```
- Искать и чинить реальные баги (не выдумывать)
- Упрощение сложного кода
- Объединение модулей если это уменьшает сложность
- Тесты только как ЧАСТЬ фикса, не как самоцель
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

### 7. Documentation as Feature Listing
```
BAD:  "Возможности: HTML-отчёты, JSON-отчёты, Markdown-отчёты" — это список фич, не документация
BAD:  "/speckit.goals — управление целями качества" — однострочное описание без примеров
BAD:  Перечисление 20 команд таблицей без объяснения когда и зачем каждую использовать
GOOD: "Зачем: ...", "Когда использовать: ...", "Пример: ...", "Не нужно если: ..."
GOOD: Decision guide: "Я хочу X → используй команду Y"
GOOD: Полные сценарии: от проблемы до результата

ПРАВИЛО: Документация — это руководство "как пользоваться", а не каталог возможностей.
         Каждая команда/фича должна иметь: (1) зачем, (2) когда использовать, (3) пример,
         (4) что получится. Пользователь обращается к документации как к справочнику.
         Основной справочник: docs/usage-guide.md
```

### 8. Self-Reflection Loop
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

## Example Research Session (v4)

```
Агент: Читаю program.md... фаза PRODUCT IMPROVEMENT.
Агент: Experiment N: Добавить OWASP проверки в security.yml
Агент: Исследую OWASP Top 10 → добавляю 3 правила: injection checks,
       broken auth, security misconfiguration в шаблон.
Агент: Тест: spec без auth → должен получить warning. Проходит.
Агент: Experiment N+1: Fix — scorer даёт 0.0 на пустой spec вместо ошибки
Агент: Нашёл баг: division by zero при пустых criteria. Фикс + тест.
Агент: Experiment N+2: Улучшить error message при невалидном template path
Агент: Было: FileNotFoundError traceback. Стало: "Template 'xyz' not found.
       Available: backend, frontend, security. Run `speckit templates` to list all."
Агент: Experiment N+3: Уточнить правила в backend.yml
Агент: Исследую 3 open-source backend спеки. Правило "must describe caching"
       срабатывает ложно на простых CRUD API. Сужаю scope правила.
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
Читай program.md. Фаза: PRODUCT IMPROVEMENT.
Ищи реальные улучшения: security, UX, баги, template quality.
```

Агент будет:
1. Читать memory и program.md
2. Выбрать направление из Research Areas (чередовать!)
3. Сделать конкретное улучшение с тестом
4. Проверить что ВСЕ тесты проходят
5. Повторять, меняя направление
