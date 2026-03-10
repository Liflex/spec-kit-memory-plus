[**Русский**](#ru) | [English](#en)

---

<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>Spec Kit Memory System</h1>
    <h3><em>4-уровневая архитектура памяти + Quality Loop + Security Scanning</em></h3>
</div>

<p align="center">
    <strong>Глобальная интеграция памяти агентов, итеративное улучшение качества кода и защита от вредоносных скиллов.</strong>
</p>

---

## Обзор (Overview) {#ru}

SpecKit Memory System - это комплексная система для AI-агентов, работающих с фреймворком SpecKit spec-driven development. Она включает:

- **4-уровневую архитектуру памяти**: Файловая, Векторная, Контекстная и Идентификационная
- **Quality Loop**: Итеративное улучшение качества кода с автоматической оценкой
- **Security Scanning**: Двухуровневая защита от вредоносных скиллов и агентов
- **Интеграцию SkillsMP**: Доступ к 425K+ навыкам агентов из сообщества

### Ключевые возможности

#### Memory System
- **Чтение заголовков**: Эффективная загрузка контекста с накладными расходами ~1-2%
- **Обучение между проектами**: Обмен паттернами и уроками между всеми проектами
- **Умный поиск**: Автоматическое определение области (локально/глобально) с семантическим поиском

#### Quality Loop 🆕
- **Автоматическая оценка качества**: Score-based метрики (0.0-1.0)
- **Итеративное улучшение**: Цикл "Оценка → Критика → Исправление" до достижения threshold
- **12 built-in критериев**: Шаблоны для API, кода, документации, базы данных, frontend, backend, DevOps, тестов, безопасности, производительности, UI/UX
- **Stagnation detection**: Остановка когда качество plateaus

#### Security Scanning 🆕
- **Level 1**: Python статический сканер (из ai-factory)
- **Level 2**: LLM семантический обзор
- **Автоматическая защита**: Сканирование при получении скиллов и создании агентов
- **Три уровня результатов**: SAFE ✅, WARNING ⚠️, BLOCKED 🚫

#### Другие возможности
- **Создание агентов**: Автоматическое создание агентов на основе изученных паттернов
- **Автосохранение и резервирование**: Никогда не потеряете важные открытия

---

## Quality Loop - Итеративное улучшение качества 🆕

### Что такое Quality Loop?

Quality Loop автоматически оценивает ваш код против явных правил, генерирует целевую обратную связь и улучшает реализацию через несколько итераций. Вдохновлён Reflex Loop из [ai-factory](https://github.com/github/ai-factory).

### Зачем это нужно?

| Проблема | Решение Quality Loop |
|----------|---------------------|
| Код работает, но нет тестов | Автоматически находит и добавляет |
| Забыл обработку ошибок | Генерирует targeted fix |
| Документация неполная | Выявляет отсутствующие секции |
| Нет clear код | Предлагает улучшения readability |
| SQL injection уязвимости | Находит и предлагает исправления |
| Нет индексов в БД | Рекомендует индексы |
| Accessibility проблемы | Выявляет WCAG нарушения |

### Как это работает?

```
1. Оценка (Evaluate) → Проверка артефакта против правил
2. Критика (Critique) → Генерация обратной связи для провалившихся правил
3. Исправление (Refine) → Применение исправлений
4. Повтор → До достижения threshold или лимита итераций
```

### Использование

#### Команда 1: `/speckit.implementloop` — Реализация + Quality Loop

**Лучше для**: Новых фич, когда нужно реализовать + улучшить за один раз

```bash
/speckit.implementloop --criteria code-gen --max-iterations 4
```

**Что происходит**:
1. Реализует все задачи из `tasks.md`
2. Автоматически запускает quality loop на изменённых файлах
3. Повторяет: оценка → критика → исправление до threshold

**Вывод**:
```
=== Implementing Tasks from tasks.md ===
✅ Task 1: Create src/models/user.py
✅ Task 2: Create src/repositories/user_repository.py

=== Quality Loop Started ===

Iteration 1/4 | Phase A | Score: 0.72 | FAIL
Failed: correctness.tests, quality.error_handling

Iteration 2/4 | Phase A | Score: 0.84 | PASS (Phase A → B)

Iteration 3/4 | Phase B | Score: 0.91 | PASS

=== Quality Loop Complete ===
Stop Reason: threshold_reached
Score: 0.91
```

#### Команда 2: `/speckit.loop` — Отдельный Quality Loop

**Лучше для**: Код уже реализован, нужно улучшить качество

```bash
# Авто-детекция criteria по ключевым словам
/speckit.loop

# Указать явно
/speckit.loop --criteria code-gen --max-iterations 6

# Resume после прерывания
/speckit.loop resume

# Статус активного loop
/speckit.loop status

# Остановить loop
/speckit.loop stop
```

#### Команда 3: `/speckit.implement` — Обычная реализация

**Лучше для**: Обычный workflow, вручную решаете когда запускать quality loop

```bash
/speckit.implement
```

**В конце покажет рекомендацию**:
```
---
## 🔄 Quality Loop Available

Implementation complete! You can further improve code quality...

/speckit.loop --criteria code-gen --max-iterations 4
```

### Criteria Templates (12 built-in шаблонов)

| Template | Когда использовать | Правил | Ключевые проверки |
|----------|-------------------|--------|-------------------|
| `api-spec` | API спецификации, OpenAPI | 10 | Endpoints, status codes, auth |
| `code-gen` | Генерация кода, функции, классы | 11 | Тесты, ошибки, типы, структура |
| `docs` | Документация, README, гайды | 10 | Заголовок, установка, использование |
| `config` | Конфигурационные файлы, YAML/JSON | 9 | Синтаксис, типы, секреты |
| `database` | Базы данных, SQL, миграции | 10 | Primary/foreign keys, индексы, SQLi |
| `frontend` | Frontend код, React/Vue/Angular | 10 | Компоненты, state management, routing |
| `backend` | Backend сервисы, API | 10 | API структура, service layer, DI |
| `infrastructure` | DevOps, Docker, Kubernetes | 10 | Dockerfile, health checks, ресурсы |
| `testing` | Тестовые файлы, unit/integration | 10 | AAA паттерн, assertions, isolation |
| `security` | Безопасность, auth, XSS/SQLi | 10 | Секреты, валидация, auth, injection |
| `performance` | Производительность, оптимизация | 10 | Кэширование, async, запросы |
| `ui-ux` | UI/UX дизайн, accessibility | 10 | Alt текст, keyboard navigation, WCAG |

### Примеры использования criteria

#### API Design
```bash
/speckit.loop --criteria api-spec
# Проверит: CRUD операции, status codes, auth, параметры, error responses
```

#### Database Schema
```bash
/speckit.loop --criteria database
# Проверит: primary/foreign keys, индексы, SQL injection prevention
```

#### Security Review
```bash
/speckit.loop --criteria security --max-iterations 6
# Проверит: секреты, валидация, auth, XSS/SQLi prevention
```

#### Frontend Code
```bash
/speckit.loop --criteria frontend
# Проверит: компоненты, state management, accessibility
```

### Auto-detection критериев

Quality Loop автоматически определяет нужный criteria template по ключевым словам в описании задачи:

| Keywords | Template |
|----------|----------|
| "api", "endpoint", "rest", "graphql" | `api-spec` |
| "code", "implementation", "function" | `code-gen` |
| "docs", "readme", "documentation" | `docs` |
| "config", "settings", "yaml" | `config` |
| "database", "sql", "schema", "migration" | `database` |
| "frontend", "react", "vue", "component" | `frontend` |
| "backend", "service", "middleware" | `backend` |
| "docker", "kubernetes", "deploy" | `infrastructure` |
| "test", "testing", "unit", "integration" | `testing` |
| "security", "auth", "authorization" | `security` |
| "performance", "cache", "optimization" | `performance` |
| "ux", "accessibility", "responsive" | `ui-ux` |

### Score и Thresholds

**Formula**: `score = sum(passed_weights) / sum(all_active_weights)`

**Severity weights**:
- `fail`: weight = 2 (блокирует прохождение)
- `warn`: weight = 1 (снижает score)
- `info`: weight = 0 (только отслеживание)

**Thresholds**:
- Phase A: 0.8 (базовое качество)
- Phase B: 0.9 (строгое качество, production-ready)

**Пример score**:
```
Score: 0.84 → 84% правил прошли

Phase A: 0.84 ≥ 0.8 → PASS → переход к Phase B
Phase B: 0.84 < 0.9 → FAIL → продолжить улучшение
```

**Влияние fail-правил**:
```
Даже если score ≥ threshold:
- ЛЮБОЕ fail-severity правило = FAIL

Пример:
- Score: 0.92 (92%)
- Failed: correctness.tests (fail severity)
- Результат: FAIL (блокировано fail-правилом)
```

---

## Security Scanning - Защита от вредоносных скиллов 🆕

### Что такое Security Scanning?

Двухуровневая система защиты от вредоносных скиллов и агентов при получении из SkillsMP или создании новых.

### Зачем это нужно?

| Угроза | Защита |
|--------|--------|
| Prompt injection ("ignore previous") | Level 1: Детект паттернов |
| Data exfiltration (curl ~/.ssh) | Level 1: Детект команд |
| Stealth instructions ("don't tell user") | Level 1: Детект ключевых слов |
| Semantic threats (контекстуальные) | Level 2: LLM обзор |

### Как это работает?

```
┌────────────────┐
│ Skill/Agent    │
└───────┬────────┘
        │
        ▼
┌─────────────────────┐
│ Level 1: Scanner    │ ← Python static analysis
│ (ai-factory)        │   Детектит паттерны:
└───────┬─────────────┘   • prompt injection
        │                   • data exfiltration
        ├── CLEAN ──────► ✅ SAFE (installation proceeds)
        │
        ├── BLOCKED ────► 🚫 BLOCKED (deleted, not installed)
        │
        └── WARNING ────► Level 2 Review
                            │
                            ▼
                      ┌─────────────┐
                      │ Level 2: LLM │ ← Семантический обзор
                      └──────┬──────┘
                             │
                             ├── Safe ──► ✅ SAFE
                             │
                             └── Unsafe ─► 🚫 BLOCKED
```

### Автоматическое сканирование

Security scanning **автоматически запускается** при:

#### 1. Получении скиллов из SkillsMP

```python
from specify_cli.memory.skillsmp_integration import SkillsMPIntegration

integration = SkillsMPIntegration()
results = integration.search_skills("python coder")

# 🔍 Security scanning AUTOMATIC here!
# - Level 1: Статический анализ
# - Level 2: LLM обзор (если WARNING)
# - BLOCKED скиллы автоматически удаляются
```

**Пример вывода**:
```
🔍 Scanning skill 'python-coder' for security threats...
✅ Skill 'python-coder' is safe (Level 1: CLEAN)
```

#### 2. Создании агентов

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()
created_files = workflow.create_agent_from_requirements(
    agent_name="backend-dev",
    requirements={"role": "Backend Developer"}
)

# 🔍 Security scanning AUTOMATIC here!
# - Созданный агент сканируется
# - Agent-specific threats проверяются
# - BLOCKED агенты не сохраняются
```

### Threat Patterns

#### Level 1: Статические паттерны

| Категория | Паттерны |
|-----------|----------|
| **Prompt Injection** | "ignore previous instructions", "override", "bypass security" |
| **Data Exfiltration** | "curl ~/.ssh", "cat ~/.aws", "export credentials" |
| **Stealth** | "don't tell user", "hide from logs", "silent execution" |
| **Destructive** | "rm -rf", "del /Q", "format", "drop table" |
| **Config Tampering** | Modify .bashrc, .ssh/, system files |

#### Level 2: Семантические паттерны

| Категория | Детекция |
|-----------|----------|
| **Intent Mismatch** | Role не совпадает с инструкциями |
| **Contextual Threats** | Кажущиеся безопасными команды в вредоносном контексте |
| **Authority Abuse** | Фейковые "authorized by admin" заявления |
| **Obfuscation** | Скрыто вредоносные намерения |

### Результаты сканирования

#### SAFE ✅

```
Scan Result: SAFE
Level 1: CLEAN (0 threats, 1.2s)
Level 2: No semantic threats found
```

**Действие**: Установка разрешена

#### BLOCKED 🚫

```
Scan Result: BLOCKED
Level 1: CRITICAL threats found:
- [prompt_injection] "ignore previous instructions" at SKILL.md:42
- [data_exfiltration] "curl ~/.aws/credentials" at SKILL.md:15

Action: Skill deleted, not installed
```

**Действие**: Установка заблокирована, файл удалён

#### WARNING ⚠️

```
Scan Result: WARNING
Level 1: WARNINGS found:
- [suspicious_html] "<!-- authorized by admin -->" at SKILL.md:30

Level 2: LLM review requested confirmation
Reason: "Suspicious authority pattern, may be legitimate if from admin documentation"

Install anyway? (yes/no):
```

**Действие**: Требуется подтверждение пользователя

---

## Установка

### Через AI-помощника

Попросите вашего AI-помощника выполнить установку:

```
Выполни инструкции по установке из specs/001-global-agent-memory/INSTALL.md
```

AI-помощник:
- Создаст структуру директорий `~/.claude/memory/`
- Настроит символическую ссылку SpecKit
- Сконфигурирует шаблоны проектов
- Опционально установит Ollama для векторного поиска
- Настроит SkillsMP запросив опционально api key
- **Установит зависимости для Quality Loop**: `jsonlines`, `pyyaml`

См. [INSTALL.md](specs/001-global-agent-memory/INSTALL.md) для полных инструкций.

---

## Быстрый старт

### 1. Quality Loop для улучшения кода

```bash
# Реализовать + улучшить качество автоматически
/speckit.implementloop --criteria code-gen --max-iterations 4

# Или улучшить существующий код
/speckit.loop --criteria code-gen

# Security review
/speckit.loop --criteria security --max-iterations 6

# Database schema review
/speckit.loop --criteria database
```

### 2. Использование памяти

```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

memory = MemoryOrchestrator()

# Сохранение уроков
memory.add_lesson(
    title="Проблема с истечением JWT токена",
    problem="Токены доступа истекали через 1 час",
    solution="Увеличено до 24 часов + refresh токены"
)
```

### 3. Безопасный поиск агентов

```python
from specify_cli.memory.skillsmp_integration import SkillsMPIntegration

skillsmp = SkillsMPIntegration()

# 🔍 Security scanning AUTOMATIC при поиске
results = skillsmp.search_skills("миграция базы данных")

# Все результаты уже проверены на безопасность
for skill in results:
    print(f"{skill['title']}: {skill['description']}")
```

---

## 4-уровневая архитектура памяти

### Уровень 1: Файловая память

Постоянное хранилище в markdown файлах:
- `lessons.md` - Уроки из ошибок и исправлений
- `patterns.md` - Переиспользуемые решения
- `architecture.md` - Технические решения
- `projects-log.md` - История проектов

### Уровень 2: Векторная память

Семантический поиск с Ollama:
- Автоматические вложения
- RAG индексация
- Graceful degradation

### Уровень 3: Контекстная память

Рабочая память:
- Чтение заголовков (~1-2% overhead)
- Целевое глубокое чтение

### Уровень 4: Идентификационная память

Долгосрочное обучение:
- Паттерны программирования
- Предпочтения стека

---

## Интеграция с командами SpecKit

Память автоматически интегрируется с командами:

```bash
# /speckit.specify - Получает контекст памяти
/speckit.specify Создать систему пользовательской аутентификации

# /speckit.plan - Извлекает архитектурные решения
/speckit.plan Использовать Next.js с PostgreSQL

# /speckit.tasks - Предлагает паттерны
/speckit.tasks

# /speckit.implement - Реализует с рекомендацией Quality Loop
/speckit.implement

# 🆕 /speckit.implementloop - Реализует + Quality Loop
/speckit.implementloop --criteria code-gen

# 🆕 /speckit.loop - Quality Loop на существующем коде
/speckit.loop --criteria code-gen
```

---

## Создание агентов с защитой 🆕

Автоматическое создание с security scanning:

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()

# Поиск перед созданием
results = workflow.search_agents("фронтенд разработка")

# Создание с 🔍 automatic security scanning
agent = workflow.create_agent_from_requirements(
    agent_name="frontend-dev",
    requirements={
        "role": "Frontend Разработчик",
        "personality": "Творческий и внимательный"
    }
)
# 🔍 Security scan:
# - Level 1: Статический анализ созданных файлов
# - Level 2: LLM семантический обзор
# - BLOCKED агенты удаляются автоматически
```

---

## Производительность

| Метрика | Значение |
|---------|----------|
| Накладные расходы контекста | ~1-2% (130-280 токенов) |
| Время поиска (локально) | <200мс |
| Время поиска (векторно) | <1с |
| Quality Loop итерация | <60с |
| Security scan | <30с |
| Макс. записей на проект | 1000+ |

---

## Документация

### Memory System
- **[Quickstart Guide](docs/memory/quickstart.md)** - Начните работу за 5 минут
- **[Полная документация](docs/memory/README.md)** - Полный справочник API
- **[Руководство по установке](specs/001-global-agent-memory/INSTALL.md)** - AI-executable инструкции

### Quality Loop 🆕
- **[Quality Loop Documentation](docs/quality-loop.md)** - Полное руководство по Quality Loop
  - Все 12 criteria templates детально описаны
  - Как severity влияет на loop
  - Score calculation примеры
- **[Quickstart Guide](specs/002-implement-quality-loop/quickstart.md)** - Начните работу за 10 минут

### Security Scanning 🆕
- **[Security Scanning Documentation](docs/security-scanning.md)** - Полное руководство по security
- **[Security Contract](specs/002-implement-quality-loop/contracts/security-scan.md)** - API контракты

---

## Статус проекта

**Версия**: 0.3.0

**Реализация**: 200+ задач в 14 фазах завершено

### Фазы Memory System (v0.1.0)

| Фаза | Статус | Задачи |
|------|--------|--------|
| Фаза 3: Накопление памяти | ✅ Завершено | 12/12 |
| Фаза 4: Глобальная установка | ✅ Завершено | 14/14 |
| Фаза 5: Векторная память | ✅ Завершено | 10/10 |
| Фаза 6: Поиск SkillsMP | ✅ Завершено | 9/9 |
| Фаза 7: Создание агентов | ✅ Завершено | 8/8 |
| Фаза 8: Интеграция SpecKit | ✅ Завершено | 9/9 |
| Фаза 9: Полировка и выпуск | ✅ Завершено | 11/11 |

### Фазы Quality Loop + Security (v0.3.0) 🆕

| Фаза | Статус | Задачи |
|------|--------|--------|
| Phase 1: Setup | ✅ Завершено | 8/8 |
| Phase 2: Foundational | ✅ Завершено | 10/10 |
| Phase 3: Criteria Templates | ✅ Завершено | 12/12 |
| Phase 4: Evaluation & Scoring | ✅ Завершено | 9/9 |
| Phase 5: Critique & Refinement | ✅ Завершено | 8/8 |
| Phase 6: Quality Loop Orchestration | ✅ Завершено | 7/7 |
| Phase 7: CLI Commands | ✅ Завершено | 14/14 |
| Phase 8: Security Integration | ✅ Завершено | 9/9 |
| Phase 9: Tests | ✅ Завершено | 12/12 |
| Phase 10: Documentation | ✅ Завершено | 4/4 |

---

## Конфигурация

Конфигурация хранится в `~/.claude/spec-kit/config/memory.json`:

```json
{
  "enabled": true,
  "auto_save": true,
  "vector_search": {
    "enabled": true,
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "skillsmp": {
    "enabled": true,
    "api_key": "ваш-ключ-здесь"
  },
  "quality_loop": {
    "enabled": true,
    "default_criteria": "code-gen",
    "max_iterations": 4,
    "threshold_a": 0.8,
    "threshold_b": 0.9
  },
  "security_scanning": {
    "enabled": true,
    "level1_scanner": "ai-factory",
    "level2_llm": true
  }
}
```

---

## Лицензия

Этот проект расширяет [SpecKit](https://github.com/github/spec-kit), который распространяется по лицензии MIT.

---

## Поддержка

По проблемам и вопросам:
- Откройте issue в репозитории
- Проверьте [Решение проблем](docs/memory/README.md#troubleshooting)
- Ознакомьтесь [FAQ](docs/memory/README.md#faq)

---

---

<div align="center">
    <img src="./media/logo_large.webp" alt="Spec Kit Logo" width="200" height="200"/>
    <h1>Spec Kit Memory System</h1>
    <h3><em>4-Level Memory + Quality Loop + Security Scanning</em></h3>
</div>

<p align="center">
    <strong>Global agent memory, iterative quality improvement, and malicious skill protection.</strong>
</p>

---

## Overview {#en}

SpecKit Memory System is a comprehensive system for AI agents working with the SpecKit spec-driven development framework. It includes:

- **4-Level Memory Architecture**: File, Vector, Context, and Identity layers
- **Quality Loop**: Iterative code quality improvement with automatic evaluation
- **Security Scanning**: Two-level protection against malicious skills and agents
- **SkillsMP Integration**: Access to 425K+ agent skills from the community

### Key Features

#### Memory System
- **Headers-First Reading**: Efficient context loading with ~1-2% overhead
- **Cross-Project Learning**: Share patterns and lessons across all projects
- **Smart Search**: Automatic scope detection (local/global) with semantic search

#### Quality Loop 🆕
- **Automatic Quality Evaluation**: Score-based metrics (0.0-1.0)
- **Iterative Improvement**: "Evaluate → Critique → Refine" cycle until threshold
- **12 Built-in Criteria**: Templates for API, code, docs, database, frontend, backend, DevOps, tests, security, performance, UI/UX
- **Stagnation Detection**: Stops when quality plateaus

#### Security Scanning 🆕
- **Level 1**: Python static scanner (from ai-factory)
- **Level 2**: LLM semantic review
- **Automatic Protection**: Scanning on skill download and agent creation
- **Three Result Levels**: SAFE ✅, WARNING ⚠️, BLOCKED 🚫

---

## Quality Loop - Iterative Quality Improvement 🆕

### What is Quality Loop?

Quality Loop automatically evaluates your code against explicit rules, generates targeted feedback, and refines the implementation through multiple iterations. Inspired by Reflex Loop from [ai-factory](https://github.com/github/ai-factory).

### Why Use It?

| Problem | Quality Loop Solution |
|---------|----------------------|
| Code works but no tests | Automatically finds and adds them |
| Missing error handling | Generates targeted fix |
| Incomplete documentation | Identifies missing sections |
| Unclear code | Suggests readability improvements |
| SQL injection vulnerabilities | Finds and suggests fixes |
| Missing database indexes | Recommends indexes |
| Accessibility issues | Detects WCAG violations |

### How It Works?

```
1. Evaluate → Check artifact against rules
2. Critique → Generate feedback for failed rules
3. Refine → Apply fixes
4. Repeat → Until threshold or limit
```

### Usage

#### Command 1: `/speckit.implementloop` — Implement + Quality Loop

**Best for**: New features, implement + improve in one command

```bash
/speckit.implementloop --criteria code-gen --max-iterations 4
```

**What happens**:
1. Implements all tasks from `tasks.md`
2. Automatically runs quality loop on changed files
3. Repeats: evaluate → critique → refine until threshold

#### Command 2: `/speckit.loop` — Separate Quality Loop

**Best for**: Code already implemented, needs quality improvement

```bash
# Auto-detect criteria by keywords
/speckit.loop

# Specify explicitly
/speckit.loop --criteria code-gen --max-iterations 6

# Resume after interruption
/speckit.loop resume

# Check active loop status
/speckit.loop status
```

#### Command 3: `/speckit.implement` — Regular Implementation

**Best for**: Regular workflow, manually decide when to run quality loop

```bash
/speckit.implement
```

**Shows recommendation at end**:
```
---
## 🔄 Quality Loop Available

Implementation complete! You can further improve code quality...

/speckit.loop --criteria code-gen --max-iterations 4
```

### Criteria Templates (12 built-in)

| Template | Use for | Rules | Key checks |
|----------|---------|-------|------------|
| `api-spec` | API specs, OpenAPI | 10 | Endpoints, status codes, auth |
| `code-gen` | Code implementation | 11 | Tests, errors, types, structure |
| `docs` | Documentation, README | 10 | Title, installation, usage |
| `config` | Config files, YAML/JSON | 9 | Syntax, types, secrets |
| `database` | Databases, SQL, migrations | 10 | Primary/foreign keys, indexes, SQLi |
| `frontend` | Frontend code, React/Vue | 10 | Components, state management, routing |
| `backend` | Backend services, API | 10 | API structure, service layer, DI |
| `infrastructure` | DevOps, Docker, K8s | 10 | Dockerfile, health checks, resources |
| `testing` | Test files, unit/integration | 10 | AAA pattern, assertions, isolation |
| `security` | Security, auth, XSS/SQLi | 10 | Secrets, validation, auth, injection |
| `performance` | Performance, optimization | 10 | Caching, async, queries |
| `ui-ux` | UI/UX design, accessibility | 10 | Alt text, keyboard nav, WCAG |

### Score and Thresholds

**Formula**: `score = sum(passed_weights) / sum(all_active_weights)`

**Severity weights**:
- `fail`: weight = 2 (blocks passing)
- `warn`: weight = 1 (lowers score)
- `info`: weight = 0 (tracking only)

**Thresholds**:
- Phase A: 0.8 (base quality)
- Phase B: 0.9 (strict quality, production-ready)

---

## Security Scanning - Malicious Skill Protection 🆕

### What is Security Scanning?

Two-level protection system against malicious skills and agents when downloading from SkillsMP or creating new ones.

### Why Use It?

| Threat | Protection |
|--------|------------|
| Prompt injection ("ignore previous") | Level 1: Pattern detection |
| Data exfiltration (curl ~/.ssh) | Level 1: Command detection |
| Stealth instructions ("don't tell user") | Level 1: Keyword detection |
| Semantic threats | Level 2: LLM review |

### How It Works?

```
Skill/Agent → Level 1 Scan → CLEAN → ✅ SAFE
                        → BLOCKED → 🚫 BLOCKED
                        → WARNING → Level 2 Review → Safe → ✅
                                                   → Unsafe → 🚫
```

---

## Installation

### Via AI Assistant

Ask your AI assistant to execute installation:

```
Execute the installation instructions from specs/001-global-agent-memory/INSTALL.md
```

The AI assistant will:
- Create `~/.claude/memory/` directory structure
- Set up SpecKit symlink
- Configure project templates
- Optionally install Ollama for vector search
- **Install Quality Loop dependencies**: `jsonlines`, `pyyaml`

See [INSTALL.md](specs/001-global-agent-memory/INSTALL.md) for complete instructions.

---

## Quickstart

### 1. Quality Loop for Code Improvement

```bash
# Implement + improve quality automatically
/speckit.implementloop --criteria code-gen --max-iterations 4

# Or improve existing code
/speckit.loop --criteria code-gen

# Security review
/speckit.loop --criteria security --max-iterations 6
```

### 2. Memory Usage

```python
from specify_cli.memory.orchestrator import MemoryOrchestrator

memory = MemoryOrchestrator()

# Save lessons
memory.add_lesson(
    title="JWT Token Expiration Issue",
    problem="Access tokens expired after 1 hour",
    solution="Increased to 24 hours + refresh tokens"
)
```

### 3. Safe Agent Search

```python
from specify_cli.memory.skillsmp_integration import SkillsMPIntegration

skillsmp = SkillsMPIntegration()

# 🔍 Security scanning AUTOMATIC on search
results = skillsmp.search_skills("database migration")

# All results already security-checked
for skill in results:
    print(f"{skill['title']}: {skill['description']}")
```

---

## 4-Level Memory Architecture

### Level 1: File Memory

Persistent storage in markdown files:
- `lessons.md` - Learnings from mistakes
- `patterns.md` - Reusable solutions
- `architecture.md` - Technical decisions
- `projects-log.md` - Project history

### Level 2: Vector Memory

Semantic search with Ollama:
- Automatic embeddings
- RAG indexing
- Graceful degradation

### Level 3: Context Memory

Working memory:
- Headers-first reading (~1-2% overhead)
- Targeted deep reads

### Level 4: Identity Memory

Long-term learning:
- Coding patterns
- Tech stack preferences

---

## SpecKit Commands Integration

Memory automatically integrates with SpecKit commands:

```bash
# /speckit.specify - Gets memory context
/speckit.specify Build a user authentication system

# /speckit.plan - Retrieves architecture decisions
/speckit.plan Use Next.js with PostgreSQL

# /speckit.tasks - Suggests patterns from memory
/speckit.tasks

# /speckit.implement - Implements with quality recommendation
/speckit.implement

# 🆕 /speckit.implementloop - Implement + Quality Loop
/speckit.implementloop --criteria code-gen

# 🆕 /speckit.loop - Quality Loop on existing code
/speckit.loop --criteria code-gen
```

---

## Agent Creation with Protection 🆕

Automatic creation with security scanning:

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()

# Search before creating
results = workflow.search_agents("frontend development")

# Create with 🔍 automatic security scanning
agent = workflow.create_agent_from_requirements(
    agent_name="frontend-dev",
    requirements={
        "role": "Frontend Developer",
        "personality": "Creative and detail-oriented"
    }
)
# 🔍 Security scan:
# - Level 1: Static analysis of created files
# - Level 2: LLM semantic review
# - BLOCKED agents deleted automatically
```

---

## Performance

| Metric | Value |
|--------|-------|
| Context overhead (headers) | ~1-2% (130-280 tokens) |
| Search time (local) | <200ms |
| Search time (vector) | <1s |
| Quality Loop iteration | <60s |
| Security scan | <30s |
| Max entries per project | 1000+ |

---

## Documentation

### Memory System
- **[Quickstart Guide](docs/memory/quickstart.md)** - Get started in 5 minutes
- **[Full Documentation](docs/memory/README.md)** - Complete API reference
- **[Installation Guide](specs/001-global-agent-memory/INSTALL.md)** - AI-executable instructions

### Quality Loop 🆕
- **[Quality Loop Documentation](docs/quality-loop.md)** - Complete Quality Loop guide
  - All 12 criteria templates detailed
  - How severity affects loop
  - Score calculation examples
- **[Quickstart Guide](specs/002-implement-quality-loop/quickstart.md)** - Get started in 10 minutes

### Security Scanning 🆕
- **[Security Scanning Documentation](docs/security-scanning.md)** - Complete security guide
- **[Security Contract](specs/002-implement-quality-loop/contracts/security-scan.md)** - API contracts

---

## Project Status

**Version**: 0.3.0

**Implementation**: 200+ tasks across 14 phases complete

### Memory System Phases (v0.1.0)

| Phase | Status | Tasks |
|-------|--------|-------|
| Phase 3: Memory Accumulation | ✅ Complete | 12/12 |
| Phase 4: Global Installation | ✅ Complete | 14/14 |
| Phase 5: Vector Memory | ✅ Complete | 10/10 |
| Phase 6: SkillsMP Search | ✅ Complete | 9/9 |
| Phase 7: Agent Creation | ✅ Complete | 8/8 |
| Phase 8: SpecKit Integration | ✅ Complete | 9/9 |
| Phase 9: Polish & Release | ✅ Complete | 11/11 |

### Quality Loop + Security Phases (v0.3.0) 🆕

| Phase | Status | Tasks |
|-------|--------|-------|
| Phase 1: Setup | ✅ Complete | 8/8 |
| Phase 2: Foundational | ✅ Complete | 10/10 |
| Phase 3: Criteria Templates | ✅ Complete | 12/12 |
| Phase 4: Evaluation & Scoring | ✅ Complete | 9/9 |
| Phase 5: Critique & Refinement | ✅ Complete | 8/8 |
| Phase 6: Quality Loop Orchestration | ✅ Complete | 7/7 |
| Phase 7: CLI Commands | ✅ Complete | 14/14 |
| Phase 8: Security Integration | ✅ Complete | 9/9 |
| Phase 9: Tests | ✅ Complete | 12/12 |
| Phase 10: Documentation | ✅ Complete | 4/4 |

---

## Configuration

Configuration is stored in `~/.claude/spec-kit/config/memory.json`:

```json
{
  "enabled": true,
  "auto_save": true,
  "vector_search": {
    "enabled": true,
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "skillsmp": {
    "enabled": true,
    "api_key": "your-key-here"
  },
  "quality_loop": {
    "enabled": true,
    "default_criteria": "code-gen",
    "max_iterations": 4,
    "threshold_a": 0.8,
    "threshold_b": 0.9
  },
  "security_scanning": {
    "enabled": true,
    "level1_scanner": "ai-factory",
    "level2_llm": true
  }
}
```

---

## License

This project extends [SpecKit](https://github.com/github/spec-kit) which is licensed under the MIT license.

---

## Support

For issues and questions:
- Open an issue in the repository
- Check [Troubleshooting](docs/memory/README.md#troubleshooting)
- Review [FAQ](docs/memory/README.md#faq)
