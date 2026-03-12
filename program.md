# AutoResearch Program: Spec Kit

> Based on [karpathy/autoresearch](https://github.com/karpathy/autoresearch)
> Adapted for Spec Kit product improvement

---

## Overview

Вы — AI-исследователь в проекте **Spec Kit**. Ваша цель — автономно улучшать продукт через итеративные эксперименты.

**Ключевая идея**: Вы не пишете код как обычно. Вместо этого вы:
1. Читаете `program.md` (этот файл)
2. Предлагаете улучшение
3. Запускаете эксперимент
4. Оцениваете результат
5. Сохраняете или отбрасываете изменения
6. Повторяете

---

## What You Can Modify

**В пределах проекта Spec Kit — МОЖНО МЕНЯТЬ ЧТО УГОДНО для улучшения:**

```
✅ ВСЕ директории и файлы проекта:
- src/*                          # Весь исходный код
- templates/*                    # Все шаблоны
- tests/*                        # Тесты
- docs/*                         # Документация
- README.md, CHANGELOG.md        # Основные файлы доки
- .speckit/*                     # Конфигурация
- .claude/*                      # Claude настройки
- program.md                     # Этот файл (обновляй инструкции по мере развития проекта)
- Любые другие файлы в проекте   # Включая новые директории и файлы

❌ ЗАПРЕЩЕНО (без явного запроса):
- git push                        # Никаких push в удалённый репозиторий!
- git commit --amend              # Никаких перезаписей истории
- git reset --hard                # Потеря изменений
- Удаление .claude/memory/        # Memory — священна, но можно дополнять
- Изменения ВНЕ проекта           # Только F:\IdeaProjects\spec-kit\
```

**Philosophy**:
- **Без ограничений** — если улучшение требует изменения в любой части проекта, делай
- **Рефакторинг приветствуется** — улучшай архитектуру, переименовывай, перемещай файлы
- **Новые директории** — создавай любую структуру которая нужна
- **Документация** — обновляй README, создавай новые файлы доки

**Safety Checks** (перед любой опасной операцией):
1. **Git операции** — всегда спрашивать подтверждение
2. **Удаление файлов** — всегда спрашивать подтверждение
3. **Крупные рефакторинги** — создать backup ветку
4. **Revert возможность** — сохранять git diff перед изменениями

---

## Fixed Constants (prepare.py)

Создайте `prepare.py` со следующими фиксированными константами:

```python
# Fixed constants — DO NOT modify during experiments
PROJECT_NAME = "spec-kit"
REPO_URL = "https://github.com/github/spec-kit"

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

# Evaluation budget (seconds)
EVALUATION_BUDGET = 60  # per iteration
```

---

## Experiment Loop

### 1. Generate Idea

Прочитайте память (`.claude/memory/*.md`) для контекста:
- `lessons.md` — прошлые ошибки
- `patterns.md` — успешные паттерны
- `architecture.md` — архитектурные решения

Предложите улучшение в одном из направлений:

**Areas for Research**:
- Новые criteria templates
- Улучшение существующих правил
- Оптимизация score calculation
- Улучшение critique/refinement prompts
- Новые auto-detection patterns

### 2. Propose Change

Опишите изменение в формате:

```markdown
## Experiment N: {Title}

**Hypothesis**: {Что ожидаем улучшить}
**Target**: {Какой компонент изменяем}
**Metric**: {Как измеряем успех}
```

Пример:
```markdown
## Experiment 1: Add React-specific rule

**Hypothesis**: Frontend criteria missing React hooks validation
**Target**: src/specify_cli/quality/templates/frontend.yml
**Metric**: Add rule `correctness.react_hooks` with fail severity
```

### 3. Apply Change

Внесите изменение в `src/specify_cli/quality/rules.py` или создайте новый template.

### 4. Evaluate

Запустите quality loop тест:

```bash
# Используйте /speckit.loop команду
# Протестируйте на sample artifact
```

**Metrics**:
- Score improvement: `current_score - baseline_score`
- Rule coverage: `% of rules passing`
- Critique quality: `refinement effectiveness`

### 5. Decision

**Keep if**:
- Score ≥ baseline + 0.05
- Новые правила релевантны
- Нет регрессии

**Discard if**:
- Score < baseline
- Ложные срабатывания
- Правила слишком строгие

### 6. Log Result

Добавьте запись в соответствующий memory файл:

**lessons.md** (если学到新东西):
```markdown
## {Lesson Title}

**Date:** {YYYY-MM-DD}
**Experiment:** N
**Problem:** {What didn't work}
**Solution:** {What learned}
**Tags:** {#tags}
```

**patterns.md** (если найден рабочий паттерн):
```markdown
## {Pattern Name}

**When to use:** {Context}
**How to implement:** {Steps}
```

---

## Research Areas Priority

Это НАЧАЛЬНЫЕ направления. Ты НЕ ограничен только ими!

### Starting Points (если нет других идей):
1. **Security Rules** — CORS, CSP, helmet.js, secret scanning
2. **Performance** — bundle size, Lighthouse metrics
3. **Testing** — mock patterns, test isolation
4. **Live-Test** — HTTP validation, DB testing
5. **Documentation** — examples, installation completeness

### Но также исследуй:
- **Architecture** — улучшай структуру проекта, рефактори
- **DX (Developer Experience)** — CLI usability, error messages
- **CI/CD** — GitHub actions, workflows
- **Tooling** — новые скрипты, утилиты
- **Code Quality** — linting, formatting, type checking
- **Anything else** — что принесёт пользу проекту

**Freedom**: Если идея кажется хорошей — реализуй, даже если её нет в этом списке!

---

## Baseline Metrics

Запишите начальные метрики перед первым экспериментом:

```
Current Built-in Criteria: 13
Total Rules: ~130
Average Coverage: ~75%
Typical Iteration Time: ~60s
```

---

## Stop Conditions

**НЕ останавливайся слишком рано!** Эксперимент продолжается пока:
- ❌ Есть идеи для улучшения
- ❌ Проект можно сделать лучше
- ❌ Есть область для исследования

**Остановиться можно когда:**
- ✅ Достигнут лимит итераций (по умолчанию 50, не 10!)
- ✅ Несколько последовательных экспериментов не дали улучшений
- ✅ Все очевидные улучшения реализованы
- ✅ Пользователь явно попросил остановиться

**Важно**: Лучше сделать 50 маленьких улучшений чем 10 больших. Итеративность ключ к успеху.

---

## Example Research Session

```
Агент: Читаю memory и program.md... есть паттерны для security.
Агент: Интересная идея — а что если добавить CI/CD integration?
Агент: Это не в списке приоритетов, но было бы полезно!
Агент: Experiment 1: добавить GitHub Actions workflow.
Агент: Создаю .github/workflows/quality.yml...
Агент: Добавляю JSON output для CI integration...
[Iteration 1] Добавлен workflow, JSON export работает
Агент: Сохраняю в patterns.md.
Агент: Experiment 2: улучшаю CLI error messages...
Агент: Это тоже не в списке, но улучшает DX!
```

---

## Notes

- **Think Big**: Не ограничивайся списком приоритетов — исследуй любые улучшения
- **Memory First**: Читай memory перед изменениями, но не бойся выходить за рамки
- **Incremental**: Маленькие изменения > большие рефакторинги, но делай много итераций
- **Log Everything**: Каждый эксперимент = запись в memory
- **Be Bold**: Рефактори, перемещай файлы, меняй архитектуру — если это улучшает проект
- **Create**: Новые директории, файлы, скрипты — всё что нужно
- **Document**: Обновляй README, создавай новую документацию
- **No Silos**: Не ограничивай себя "областями" — улучшай проект целиком

---

## How to Start

Запустите агента с этим program.md и скажите:

```
Hi! Запусти автоисследование Spec Kit.
Читай program.md и начни с первого эксперимента.
```

Агент будет:
1. Читать memory
2. Предлагать улучшение
3. Применять
4. Тестировать
5. Логировать результат
6. Повторять

---

**Happy Research!** 🚀
