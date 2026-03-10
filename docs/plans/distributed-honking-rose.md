# Анализ: Reflex Loop из ai-factory vs SpecKit

**Контекст:** Пользователь запросил изучение фичи Reflex Loop из проекта ai-factory и сравнение её с возможностями SpecKit для понимания преимуществ и потенциальных улучшений.

---

## Reflex Loop: Ключевые характеристики

### Архитектура

**Команда:** `/aif-loop` — строгий итеративный workflow для генерации с качественными воротами (quality-gated generation)

**Режимы работы:**
- `new <task>` — запуск нового loop с инициализацией состояния
- `resume [alias]` — продолжение активного loop
- `status` — отображение текущего прогресса
- `stop [reason]` — явная остановка
- `list` — список всех task aliases с статусами
- `history [alias]` — история событий
- `clean [alias|--all]` — удаление loop файлов

### 6 Фаз Итерации

| Фаза | Описание | Параллелизм |
|------|----------|-------------|
| `PLAN` | Короткий план (3-5 шагов) | — |
| `PRODUCE` | Генерация `artifact.md` | ✓ параллельно с PREPARE |
| `PREPARE` | Генерация check-скриптов из правил | ✓ параллельно с PRODUCE |
| `EVALUATE` | Запуск проверок, агрегация score | ✓ параллельные группы |
| `CRITIQUE` | Критика failed правил (только при fail) | — |
| `REFINE` | Целевая переработка artifact (только при fail) | — |

### Модель Персистентности

**4 файла на loop:**
```
.ai-factory/evolution/current.json              # глобальный указатель (активен пока loop запущен)
.ai-factory/evolution/<task-alias>/run.json     # single source of truth
.ai-factory/evolution/<task-alias>/history.jsonl # append-only event stream
.ai-factory/evolution/<task-alias>/artifact.md   # artifact content
```

### Система Правил Оценки

**Формула scoring:**
```
score = sum(passed_weights) / sum(all_active_weights)
passed = (score >= threshold) AND (no fail-severity rules failed)
```

**Уровни severity:**
- `fail` — weight 2, блокирует прохождение
- `warn` — weight 1, снижает score
- `info` — weight 0, только для отслеживания

**2-фазная модель:**
- **Phase A:** threshold 0.8, базовые правила correctness/coverage
- **Phase B:** threshold 0.9, строгие правила quality/performance/security

### Условия Остановки

1. `threshold_reached` — phase B и threshold пройден
2. `no_major_issues` — нет fail-severity правил
3. `iteration_limit` — достигнут лимит итераций (по умолчанию 4)
4. `user_stop` — пользовательская остановка
5. `stagnation` — stagnation detection (delta < 0.02 при 2+ итерациях)

### Защита от Over-engineering

1. Не создавать дополнительные index файлы
2. Держать план 3-5 шагов
3. Critique возвращает max 5 issues
4. Refiner меняет только failed-rule области
5. Один artifact (`artifact.md`) на итерацию

---

## SpecKit: Текущие Возможности

### Основные Команды

| Команда | Назначение |
|---------|------------|
| `/speckit.specify` | Создание спецификации из описания фичи |
| `/speckit.plan` | Генерация плана реализации из спецификации |
| `/speckit.tasks` | Генерация задач из плана |
| `/speckit.implement` | Реализация задач |
| `/speckit.features` | Быстрая генерация для малых задач (<4 часа) |
| `/speckit.analyze` | Анализ согласованности spec/plan/tasks |
| `/speckit.clarify` | Выявление недостаточно уточнённых областей |
| `/speckit.checklist` | Генерация чеклиста для фичи |
| `/speckit.constitution` | Создание/обновление конституции проекта |
| `/speckit.tobeads` | Импорт задач в Beads issue tracker |

### Memory System v0.1.0

**4-уровневая архитектура:**
1. **Файловая память** — lessons.md, patterns.md, architecture.md, projects-log.md
2. **Векторная память** — семантический поиск с Ollama
3. **Контекстная память** — headers-first reading (~1-2% overhead)
4. **Идентификационная память** — паттерны пользователя, предпочтения стека

### SDD (Spec-Driven Development)

**Принципы:**
- Спецификации как lingua franca (первичный артефакт)
- Код как выражение спецификации в конкретном языке/фреймворке
- Executable specifications (точные, полные, однозначные)
- Test-First Imperative (статья III конституции)
- Library-First Principle (статья I)
- Конституция с 9 статьями развития

---

## Сравнительный Анализ

### Что есть в Reflex Loop, но НЕТ в SpecKit

| Возможность | Reflex Loop | SpecKit | Потенциальная ценность |
|-------------|-------------|---------|------------------------|
| **Итеративный цикл с автоматической оценкой** | ✓ | ✗ | Высокая — качество артефактов |
| **Явные правила оценки с весами** | ✓ | ✗ | Высокая — предсказуемость |
| **Фазовая модель (A/B)** | ✓ | ✗ | Средняя — прогрессивная строгость |
| **Автоматическая критика и refinement** | ✓ | ✗ | Высокая — самоулучшение |
| **Stagnation detection** | ✓ | ✗ | Средняя — предотвращение залипаний |
| **Parallel execution (PRODUCE\|\|PREPARE)** | ✓ | ✗ | Средняя — производительность |
| **Event stream (history.jsonl)** | ✓ | ✗ | Средняя — аудит и отладка |
| **Score-based passing** | ✓ | ✗ | Высокая — измеримость качества |
| **Resume capability across sessions** | ✓ | Частично (memory) | Средняя — непрерывность |
| **Criteria templates** | ✓ | ✗ | Высокая — переиспользование |

### Что есть в SpecKit, но НЕТ в Reflex Loop

| Возможность | SpecKit | Reflex Loop | Примечание |
|-------------|---------|-------------|------------|
| **Memory System (4 уровня)** | ✓ | ✗ | SpecKit имеет уникальную систему памяти |
| **Spec-Driven Development методология** | ✓ | ✗ | SpecKit фокусируется на спецификациях |
| **Конституция проекта (9 статей)** | ✓ | ✗ | Архитектурные принципы |
| **Cross-project learning** | ✓ | ✗ | Обучение между проектами |
| **SkillsMP Integration (425K+ skills)** | ✓ | ✗ | Доступ к навыкам сообщества |
| **Multi-agent support (20+ агентов)** | ✓ | ✗ | Разные AI-ассистенты |
| **Agent creation workflow** | ✓ | ✗ | Создание агентов из паттернов |
| **Constitutional gates** | ✓ | Частично (criteria) | SpecKit имеет более строгую конституцию |
| **Branch-based workflow** | ✓ | ✗ | Ветки для спецификаций |
| **Global memory across projects** | ✓ | ✗ | Глобальная память |

---

## Ключевые Отличия

### 1. Философия

**Reflex Loop:**
- Фокус на **итеративном улучшении** одного артефакта
- Генерация → Оценка → Критика → Улучшение → Повтор
- Quality-gated через явные правила
- Score-based измеримость

**SpecKit:**
- Фокус на **spec-driven разработке**
- Спецификация → План → Задачи → Реализация
- Конституционные принципы (9 статей)
- Memory-first подход (накопление знаний)

### 2. Модель Качества

**Reflex Loop:**
- Количественная: `score = passed_weights / all_weights`
- Пороговая: `passed = score >= threshold AND no fails`
- Итеративная: улучшение через циклы

**SpecKit:**
- Качественная: конституционные принципы
- Процессуальная: test-first, library-first, integration-first
- Через шаблоны: чеклисты и gates

### 3. Persistency

**Reflex Loop:**
- 4 файла на loop (run.json, history.jsonl, artifact.md, current.json)
- Event-sourcing модель (history.jsonl)
- Resume across sessions

**SpecKit:**
- Markdown-based (spec.md, plan.md, tasks.md)
- Memory files (lessons.md, patterns.md, architecture.md)
- Глобальная память (~/.claude/memory/)

---

## Потенциальная Интеграция

### Что может SpecKit заимствовать у Reflex Loop

#### 1. Итеративный Quality Loop

**Текущий процесс SpecKit:**
```
specify → plan → tasks → implement
```

**С добавлением loop:**
```
specify → plan → tasks → implement → evaluate → [refine → re-evaluate]* → done
```

**Преимущества:**
- Автоматическая проверка качества реализации
- Feedback loop между spec и implementation
- Измеримый прогресс (score-based)

#### 2. Правила Оценки с Весами

**Для `/speckit.analyze`:**
```
{
  "rules": [
    {"id": "spec.traceability", "severity": "fail", "weight": 2},
    {"id": "plan.completeness", "severity": "warn", "weight": 1},
    {"id": "tasks.dependencies", "severity": "info", "weight": 0}
  ],
  "threshold": 0.8
}
```

**Преимущества:**
- Чёткие критерии качества
- Приоритизация проблем (fail > warn > info)
- Измеримый score

#### 3. Event Stream для Аудита

**history.jsonl формат:**
```json
{"ts":"2026-03-11T10:00:00Z","event":"spec_created","status":"ok"}
{"ts":"2026-03-11T10:15:00Z","event":"plan_generated","status":"ok"}
{"ts":"2026-03-11T11:00:00Z","event":"task_completed","task_id":"001","status":"ok"}
```

**Преимущества:**
- Полный аудит trail
- Восстановление после ошибок
- Аналитика процесса

#### 4. Resume Capability

**Команда `/speckit.resume`:**
- Читает current.json
- Восстанавливает контекст из history.jsonl
- Продолжает с последней точки

**Преимущества:**
- Работа через /clear без потери состояния
- Длинные задачи разбиваются на сессии
- Восстановление после сбоев

#### 5. Criteria Templates

**Переиспользуемые наборы правил:**
```
criteria/
  api-spec.yml    # Правила для OpenAPI спецификаций
  code-gen.yml    # Правила для генерации кода
  docs.yml        # Правила для документации
```

**Преимущества:**
- Стандартные quality gates
- Быстрый старт для типовых задач
- Консистентность между проектами

### Что может Reflex Loop заимствовать у SpecKit

#### 1. Memory System

**Контекст между loop-ами:**
- Уроки из предыдущих итераций
- Паттерны успешных решений
- Архитектурные решения

#### 2. Constitutional Principles

**Quality gates через конституцию:**
- Test-first gate
- Library-first gate
- Simplicity gate
- Integration-first gate

#### 3. Cross-project Learning

**Глобальная память:**
- Паттерны из всех проектов
- Универсальные уроки
- Best practices сообщества

---

## Рекомендации

### Для SpecKit: Приоритетные Заимствования

1. **Итеративный Quality Loop** (Высокий приоритет)
   - Добавить фазу EVALUATE после /speckit.implement
   - Автоматическая критика по правилам
   - Refinement cycle до прохождения threshold

2. **Правила Оценки с Весами** (Высокий приоритет)
   - Расширить /speckit.analyze с score-based оценкой
   - Определить стандартные rulesets
   - Добавить severity levels (fail/warn/info)

3. **Event Stream** (Средний приоритет)
   - history.jsonl для всех команд speckit.*
   - Аудит всех действий
   - Возможность восстановления

4. **Criteria Templates** (Средний приоритет)
   - Создать библиотеку templates
   - API-spec, code-gen, docs, config
   - Пользовательские templates

5. **Resume Capability** (Низкий приоритет)
   - Команда /speckit.resume
   - current.json указатель
   - Восстановление состояния

### Потенциальная Команда: `/speckit.loop`

```bash
/speckit.loop new <task>              # Новый loop с quality gates
/speckit.loop resume                  # Продолжение активного loop
/speckit.loop status                  # Текущий прогресс
/speckit.loop evaluate <artifact>     # Оценка по правилам
/speckit.loop refine                  # Улучшение на основе критики
```

**Интеграция с существующими командами:**
```
/speckit.loop new → использует /speckit.specify + /speckit.plan + /speckit.tasks
/speckit.loop evaluate → расширенная версия /speckit.analyze
/speckit.loop refine → использует /speckit.implement с критикой
```

---

## Заключение

### Уникальные Преимущества Reflex Loop

1. **Score-based качество** — измеримый, количественный подход
2. **Автоматическая итерация** — самоулучшение до threshold
3. **Правила с весами** — приоритизация проблем
4. **Event sourcing** — полный аудит и восстановимость
5. **Фазовая строгость** — прогрессивное повышение требований

### Уникальные Преимущества SpecKit

1. **Memory System** — 4-уровневая архитектура памяти
2. **SDD методология** — спецификация как source of truth
3. **Конституция** — архитектурные принципы
4. **Cross-project learning** — глобальное накопление знаний
5. **Multi-agent support** — 20+ AI-ассистентов

### Синергия

**Лучшее из обоих миров:**
- SpecKit обеспечивает **контекст и память**
- Reflex Loop обеспечивает **итеративное качество**
- Вместе: spec-driven development с quality-gated iteration

**Представьте:**
```
/speckit.loop new "API для курсов"
  → Загружает контекст из Memory (паттерны API design)
  → Создаёт спецификацию (spec-driven)
  → Генерирует план (с конституционными gates)
  → Итерирует реализацию с quality checks (loop)
  → Сохраняет уроки в Memory
```

Это было бы мощной комбинацией: **интеллектуальная память + итеративное качество**.
