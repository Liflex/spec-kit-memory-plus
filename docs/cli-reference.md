# CLI Reference

Все команды Spec Kit доступны как slash-команды в Claude Code / Cursor.

> Подробные описания с примерами "когда и зачем" --- см. [Руководство по использованию](usage-guide.md).

---

## Разработка через спецификации

### /speckit.constitution

Определение принципов и правил проекта. Используется один раз при старте.

```bash
/speckit.constitution Описание принципов проекта...
```

### /speckit.specify

Создание спецификации фичи из описания на естественном языке.

```bash
/speckit.specify Описание того, что нужно сделать...
```

### /speckit.clarify

Уточнение спецификации через вопросы ИИ. Можно задать фокус или вызвать без аргументов.

```bash
/speckit.clarify
/speckit.clarify Фокус на безопасности и производительности.
```

### /speckit.plan

Создание технического плана реализации. Укажите стек и архитектурные решения.

```bash
/speckit.plan Стек: FastAPI + PostgreSQL + React. Микросервисная архитектура.
```

### /speckit.tasks

Генерация задач из spec.md и plan.md. Обычно без аргументов.

```bash
/speckit.tasks
```

### /speckit.analyze

Аудит согласованности spec.md, plan.md, tasks.md. Не изменяет файлы.

```bash
/speckit.analyze
```

### /speckit.implement

Выполнение всех задач из tasks.md.

```bash
/speckit.implement
```

### /speckit.features

Быстрая фича (< 4 часов): создаёт spec + plan + tasks за один вызов.

```bash
/speckit.features Добавить валидацию email в форму регистрации.
```

### /speckit.checklist

Создание кастомного чеклиста для текущей фичи.

```bash
/speckit.checklist Проверить: безопасность, тесты, документация.
```

---

## Контроль качества

### /speckit.loop

Запуск итеративного цикла оценки качества.

```bash
# Базовый запуск
/speckit.loop --criteria backend
/speckit.loop --criteria backend,security,testing

# Автовыбор по типу проекта
/speckit.loop --project-type web-app

# С профилем приоритетов
/speckit.loop --criteria backend --priority-profile web-app

# С политикой шлюза
/speckit.loop --gate-preset production --strict

# С готовым пресетом шаблонов
/speckit.loop --blend-preset full_stack_secure

# Управление итерациями
/speckit.loop --criteria security --max-iterations 6

# С целями
/speckit.loop --suggest-goals --auto-update-goals

# С обратной связью
/speckit.loop --criteria backend --collect-feedback

# Вывод отчётов
/speckit.loop --html-output quality-report.html
/speckit.loop --json-output quality-report.json
/speckit.loop --show-result-card
/speckit.loop --show-result-card --result-card-compact --result-card-theme dark

# Управление конфигурациями
/speckit.loop --save-config my-config
/speckit.loop --config my-config

# Управление loop
/speckit.loop resume        # Возобновить прерванный
/speckit.loop status        # Текущий статус
/speckit.loop stop          # Остановить
/speckit.loop list          # Все loop'ы
/speckit.loop history <alias>  # История
/speckit.loop clean <alias>    # Очистить
```

### /speckit.implementloop

Реализация задач + quality loop в одной команде.

```bash
/speckit.implementloop --criteria code-gen --max-iterations 4
```

---

## Управление качеством

### /speckit.qa

QA Dashboard --- обзор состояния качества.

```bash
/speckit.qa overview      # Обзор
/speckit.qa check         # Быстрая проверка
/speckit.qa compare --runs 5
/speckit.qa trends --forecast
```

### /speckit.goals

Управление целями качества.

```bash
/speckit.goals create --type target_score --target 0.90
/speckit.goals check
/speckit.goals suggest
```

### /speckit.history

История и тренды качества.

```bash
/speckit.history list --runs 10
/speckit.history stats
/speckit.history compare --runs 5
```

### /speckit.gates

Политики шлюзов качества для разных окружений.

```bash
/speckit.gates list
/speckit.gates recommend
/speckit.gates compare --policies production,staging
```

### /speckit.alerts

Оповещения о проблемах качества.

```bash
/speckit.alerts check
/speckit.alerts history --hours 24
/speckit.alerts summary
/speckit.alerts list
```

### /speckit.insights

ИИ-рекомендации на основе истории запусков.

```bash
/speckit.insights generate
/speckit.insights optimize
/speckit.insights export
```

### /speckit.feedback

Анализ обратной связи и адаптивная настройка.

```bash
/speckit.feedback analyze
/speckit.feedback analyze --runs 50 --task my-api-spec
/speckit.feedback suggestions
/speckit.feedback trends
/speckit.feedback insights --priority high,critical
```

---

## Шаблоны и конфигурация

### /speckit.templates

Реестр шаблонов критериев.

```bash
/speckit.templates list
/speckit.templates list --category infrastructure
/speckit.templates info backend
/speckit.templates search security
/speckit.templates recommend web-app
/speckit.templates stats
/speckit.templates compare frontend backend
/speckit.templates diff backend frontend
/speckit.templates blend frontend backend --mode union
/speckit.templates presets list
/speckit.templates presets info full_stack_secure
/speckit.templates presets apply full_stack_secure --output stack.yml
/speckit.templates presets auto-detect
```

### /speckit.profiles

Профили приоритетов.

```bash
/speckit.profiles list
/speckit.profiles show web-app
/speckit.profiles compare web-app,microservice
```

### /speckit.configs

Сохранённые конфигурации loop.

```bash
/speckit.configs list
/speckit.configs load production-strict
```

### /speckit.plans

Планы качества --- комплексные стратегии улучшения.

```bash
/speckit.plans                              # Список планов
/speckit.plans --show production-ready      # Детали плана
/speckit.plans --apply quick-start          # Применить план
/speckit.plans --recommend production       # Рекомендации
/speckit.plans --wizard                     # Интерактивный мастер
```

---

## Интеграции

### /speckit.taskstoissues

Экспорт задач из tasks.md в GitHub Issues.

```bash
/speckit.taskstoissues
```

### /speckit.tobeads

Импорт задач из tasks.md в Beads issue tracker.

```bash
/speckit.tobeads
```

---

## CI/CD интеграция

### GitHub Actions

```yaml
name: Quality Gate
on: [pull_request]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Loop
        run: /speckit.loop --criteria backend --json-output report.json --gate-preset production
```
