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

## Что нового (What's New) 🆕

### Внедрённые функции

| Версия | Функция | Описание |
|--------|---------|----------|
| v0.3.0 | **Quality Loop** | Итеративное улучшение качества кода с автоматической оценкой |
| v0.3.0 | **Security Scanning** | Двухуровневая защита от вредоносных скиллов (Level 1: статический анализ, Level 2: LLM) |
| v0.3.0 | **12 Criteria Templates** | Built-in шаблоны для: API, кода, документации, базы данных, frontend, backend, DevOps, тестов, безопасности, производительности, UI/UX |
| v0.1.0 | **4-Level Memory** | Файловая, Векторная, Контекстная и Идентификационная память |
| v0.1.0 | **SkillsMP Integration** | Доступ к 425K+ навыкам агентов из сообщества с auto-security scanning |

### Новые команды (добавлено в форке)

| Команда | Описание |
|---------|----------|
| `/speckit.loop` | 🔄 Quality Loop на существующем коде - итеративное улучшение качества |
| `/speckit.implementloop` | 🔄 Реализация задач + Quality Loop в одной команде |

### Команды SpecKit (базовые)

| Команда | Описание |
|---------|----------|
| `/speckit.features` | 🚀 Быстрое создание фич (< 4 часов) - минимальный spec, plan, tasks |
| `/speckit.specify` | 📝 Создание спецификации фичи |
| `/speckit.plan` | 📋 Планирование архитектуры |
| `/speckit.tasks` | ✅ Генерация задач из плана |
| `/speckit.implement` | 🔨 Реализация задач |
| `/speckit.tobeads` | 📦 Импорт задач в Beads issue tracker |
| `/speckit.taskstoissues` | 🎫 Конвертация задач в GitHub issues |
| `/speckit.clarify` | ❓ Выявление неопределённостей в спецификации |
| `/speckit.checklist` | ☑️ Генерация чеклиста для фичи |
| `/speckit.analyze` | 🔍 Анализ консистенции артефактов |
| `/speckit.constitution` | 📜 Создание/обновление конституции проекта |

---

## Обзор (Overview) {#ru}

SpecKit Memory System - это комплексная система для AI-агентов, работающих с фреймворком SpecKit spec-driven development. Она включает:

### Ключевые возможности

#### 🧠 Memory System
- **4-уровневая архитектура**: Файловая, Векторная, Контекстная и Идентификационная
- **Чтение заголовков**: Эффективная загрузка контекста с накладными расходами ~1-2%
- **Обучение между проектами**: Обмен паттернами и уроками между всеми проектами
- **Умный поиск**: Автоматическое определение области (локально/глобально) с семантическим поиском

#### 🔄 Quality Loop
- **Автоматическая оценка качества**: Score-based метрики (0.0-1.0)
- **Итеративное улучшение**: Цикл "Оценка → Критика → Исправление" до достижения threshold
- **12 built-in критериев**: Для API, кода, документации, базы данных, frontend, backend, DevOps, тестов, безопасности, производительности, UI/UX
- **Stagnation detection**: Остановка когда качество plateaus

#### 🛡️ Security Scanning
- **Level 1**: Python статический сканер (из ai-factory)
- **Level 2**: LLM семантический обзор
- **Автоматическая защита**: Сканирование при получении скиллов и создании агентов
- **Три уровня результатов**: SAFE ✅, WARNING ⚠️, BLOCKED 🚫

#### 🔗 SkillsMP Integration
- **425K+ навыков**: Доступ к навыкам агентов из сообщества
- **Безопасный поиск**: Автоматическое security scanning при поиске
- **Создание агентов**: Автоматическое создание агентов на основе изученных паттернов

---

## Быстрый старт

### 🚀 Быстрая фича (< 4 часов)

```bash
# Создать спецификацию, план и задачи за один раз
/speckit.features

# AI задаст уточняющие вопросы и создаст:
# - spec.md (спецификация)
# - plan.md (архитектурный план)
# - tasks.md (зависимости задач)
```

### 🔄 Quality Loop для улучшения кода

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

### 📝 Полный workflow для больших фич

```bash
# 1. Создать спецификацию
/speckit.specify Создать систему пользовательской аутентификации

# 2. Создать план архитектуры
/speckit.plan Использовать Next.js с PostgreSQL

# 3. Генерация задач
/speckit.tasks

# 4. Реализация
/speckit.implement

# 5. (Опционально) Quality Loop
/speckit.loop --criteria code-gen
```

### 🔍 Поиск агентов в SkillsMP

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

## Quality Loop - Итеративное улучшение качества 🔄

### Что такое Quality Loop?

Quality Loop автоматически оценивает ваш код против явных правил, генерирует целевую обратную связь и улучшает реализацию через несколько итераций. Вдохновлён Reflex Loop из [ai-factory](https://github.com/github/ai-factory).

### Как это работает?

```
1. Оценка (Evaluate) → Проверка артефакта против правил
2. Критика (Critique) → Генерация обратной связи для провалившихся правил
3. Исправление (Refine) → Применение исправлений
4. Повтор → До достижения threshold или лимита итераций
```

### Команды Quality Loop

| Команда | Когда использовать |
|---------|-------------------|
| `/speckit.loop` | Код уже реализован, нужно улучшить качество |
| `/speckit.implementloop` | Новые фичи: реализовать + улучшить за один раз |
| `/speckit.implement` | Обычный workflow, вручную решаете когда запускать quality loop |

### Criteria Templates (12 built-in)

| Template | Когда использовать |
|----------|-------------------|
| `api-spec` | API спецификации, OpenAPI |
| `code-gen` | Генерация кода, функции, классы |
| `docs` | Документация, README, гайды |
| `config` | Конфигурационные файлы, YAML/JSON |
| `database` | Базы данных, SQL, миграции |
| `frontend` | Frontend код, React/Vue/Angular |
| `backend` | Backend сервисы, API |
| `infrastructure` | DevOps, Docker, Kubernetes |
| `testing` | Тестовые файлы, unit/integration |
| `security` | Безопасность, auth, XSS/SQLi |
| `performance` | Производительность, оптимизация |
| `ui-ux` | UI/UX дизайн, accessibility |

### Примеры использования

```bash
# API Design
/speckit.loop --criteria api-spec

# Database Schema
/speckit.loop --criteria database

# Security Review
/speckit.loop --criteria security --max-iterations 6

# Frontend Code
/speckit.loop --criteria frontend
```

---

## Security Scanning - Защита от вредоносных скиллов 🛡️

### Что такое Security Scanning?

Двухуровневая система защиты от вредоносных скиллов и агентов при получении из SkillsMP или создании новых.

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
        ├── CLEAN ──────► ✅ SAFE
        │
        ├── BLOCKED ────► 🚫 BLOCKED
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

### Threat Patterns

| Категория | Паттерны |
|-----------|----------|
| **Prompt Injection** | "ignore previous instructions", "override", "bypass security" |
| **Data Exfiltration** | "curl ~/.ssh", "cat ~/.aws", "export credentials" |
| **Stealth** | "don't tell user", "hide from logs", "silent execution" |
| **Destructive** | "rm -rf", "del /Q", "format", "drop table" |

---

## 4-уровневая архитектура памяти

| Уровень | Описание |
|---------|----------|
| **1. Файловая память** | Постоянное хранилище в markdown: lessons.md, patterns.md, architecture.md, projects-log.md |
| **2. Векторная память** | Семантический поиск с Ollama: RAG индексация, graceful degradation |
| **3. Контекстная память** | Рабочая память: чтение заголовков (~1-2% overhead), целевое глубокое чтение |
| **4. Идентификационная память** | Долгосрочное обучение: паттерны программирования, предпочтения стека |

---

## Установка

### Через AI-помощника

```
Выполни инструкции по установке из specs/001-global-agent-memory/INSTALL.md
```

AI-помощник:
- Создаст структуру директорий `~/.claude/memory/`
- Настроит символическую ссылку SpecKit
- Сконфигурирует шаблоны проектов
- Опционально установит Ollama для векторного поиска
- Установит зависимости для Quality Loop: `jsonlines`, `pyyaml`

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

### Quality Loop
- **[Quality Loop Documentation](docs/quality-loop.md)** - Полное руководство
  - Все 12 criteria templates детально описаны
  - Как severity влияет на loop
  - Score calculation примеры
- **[Quickstart Guide](specs/002-implement-quality-loop/quickstart.md)** - Начните за 10 минут

### Security Scanning
- **[Security Scanning Documentation](docs/security-scanning.md)** - Полное руководство
- **[Security Contract](specs/002-implement-quality-loop/contracts/security-scan.md)** - API контракты

---

## Статус проекта

**Версия**: 0.3.0

**Реализация**: 200+ задач в 24 фазах завершено

### Memory System Phases (v0.1.0)

| Фаза | Статус | Задачи |
|------|--------|--------|
| Фаза 3-9 | ✅ Завершено | 73/73 |

### Quality Loop + Security Phases (v0.3.0)

| Фаза | Статус | Задачи |
|------|--------|--------|
| Phase 1-10 | ✅ Завершено | 91/91 |

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

## What's New 🆕

### Implemented Features

| Version | Feature | Description |
|---------|---------|-------------|
| v0.3.0 | **Quality Loop** | Iterative code quality improvement with automatic evaluation |
| v0.3.0 | **Security Scanning** | Two-level malicious skill protection (Level 1: static analysis, Level 2: LLM) |
| v0.3.0 | **12 Criteria Templates** | Built-in templates for: API, code, docs, database, frontend, backend, DevOps, tests, security, performance, UI/UX |
| v0.1.0 | **4-Level Memory** | File, Vector, Context, and Identity memory layers |
| v0.1.0 | **SkillsMP Integration** | Access to 425K+ agent skills from community with auto-security scanning |

### New Commands (added in fork)

| Command | Description |
|---------|-------------|
| `/speckit.loop` | 🔄 Quality Loop on existing code - iterative quality improvement |
| `/speckit.implementloop` | 🔄 Implement tasks + Quality Loop in one command |

### SpecKit Commands (base)

| Command | Description |
|---------|-------------|
| `/speckit.features` | 🚀 Quick feature generation (< 4 hours) - minimal spec, plan, tasks |
| `/speckit.specify` | 📝 Create feature specification |
| `/speckit.plan` | 📋 Architecture planning |
| `/speckit.tasks` | ✅ Generate tasks from plan |
| `/speckit.implement` | 🔨 Implement tasks |
| `/speckit.tobeads` | 📦 Import tasks to Beads issue tracker |
| `/speckit.taskstoissues` | 🎫 Convert tasks to GitHub issues |
| `/speckit.clarify` | ❓ Identify underspecified areas |
| `/speckit.checklist` | ☑️ Generate feature checklist |
| `/speckit.analyze` | 🔍 Analyze artifact consistency |
| `/speckit.constitution` | 📜 Create/update project constitution |

---

## Overview {#en}

SpecKit Memory System is a comprehensive system for AI agents working with the SpecKit spec-driven development framework. It includes:

### Key Features

#### 🧠 Memory System
- **4-Level Architecture**: File, Vector, Context, and Identity layers
- **Headers-First Reading**: Efficient context loading with ~1-2% overhead
- **Cross-Project Learning**: Share patterns and lessons across all projects
- **Smart Search**: Automatic scope detection (local/global) with semantic search

#### 🔄 Quality Loop
- **Automatic Quality Evaluation**: Score-based metrics (0.0-1.0)
- **Iterative Improvement**: "Evaluate → Critique → Refine" cycle until threshold
- **12 Built-in Criteria**: Templates for API, code, docs, database, frontend, backend, DevOps, tests, security, performance, UI/UX
- **Stagnation Detection**: Stops when quality plateaus

#### 🛡️ Security Scanning
- **Level 1**: Python static scanner (from ai-factory)
- **Level 2**: LLM semantic review
- **Automatic Protection**: Scanning on skill download and agent creation
- **Three Result Levels**: SAFE ✅, WARNING ⚠️, BLOCKED 🚫

#### 🔗 SkillsMP Integration
- **425K+ Skills**: Access to agent skills from community
- **Safe Search**: Automatic security scanning on search
- **Agent Creation**: Automatic agent creation based on learned patterns

---

## Quickstart

### 🚀 Quick Feature (< 4 hours)

```bash
# Create spec, plan, and tasks in one go
/speckit.features

# AI will ask clarifying questions and create:
# - spec.md (specification)
# - plan.md (architecture plan)
# - tasks.md (task dependencies)
```

### 🔄 Quality Loop for Code Improvement

```bash
# Implement + improve quality automatically
/speckit.implementloop --criteria code-gen --max-iterations 4

# Or improve existing code
/speckit.loop --criteria code-gen

# Security review
/speckit.loop --criteria security --max-iterations 6

# Database schema review
/speckit.loop --criteria database
```

### 📝 Full Workflow for Big Features

```bash
# 1. Create specification
/speckit.specify Build a user authentication system

# 2. Create architecture plan
/speckit.plan Use Next.js with PostgreSQL

# 3. Generate tasks
/speckit.tasks

# 4. Implement
/speckit.implement

# 5. (Optional) Quality Loop
/speckit.loop --criteria code-gen
```

### 🔗 Safe Agent Search

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

## Quality Loop - Iterative Quality Improvement 🔄

### What is Quality Loop?

Quality Loop automatically evaluates your code against explicit rules, generates targeted feedback, and refines the implementation through multiple iterations. Inspired by Reflex Loop from [ai-factory](https://github.com/github/ai-factory).

### How It Works?

```
1. Evaluate → Check artifact against rules
2. Critique → Generate feedback for failed rules
3. Refine → Apply fixes
4. Repeat → Until threshold or limit
```

### Quality Loop Commands

| Command | When to use |
|---------|-------------|
| `/speckit.loop` | Code already implemented, needs quality improvement |
| `/speckit.implementloop` | New features: implement + improve in one command |
| `/speckit.implement` | Regular workflow, manually decide when to run quality loop |

### Criteria Templates (12 built-in)

| Template | Use for |
|----------|---------|
| `api-spec` | API specs, OpenAPI |
| `code-gen` | Code implementation |
| `docs` | Documentation, README |
| `config` | Config files, YAML/JSON |
| `database` | Databases, SQL, migrations |
| `frontend` | Frontend code, React/Vue |
| `backend` | Backend services, API |
| `infrastructure` | DevOps, Docker, K8s |
| `testing` | Test files, unit/integration |
| `security` | Security, auth, XSS/SQLi |
| `performance` | Performance, optimization |
| `ui-ux` | UI/UX design, accessibility |

---

## Security Scanning - Malicious Skill Protection 🛡️

### What is Security Scanning?

Two-level protection system against malicious skills and agents when downloading from SkillsMP or creating new ones.

### How It Works?

```
Skill/Agent → Level 1 Scan → CLEAN → ✅ SAFE
                        → BLOCKED → 🚫 BLOCKED
                        → WARNING → Level 2 Review → Safe → ✅
                                                   → Unsafe → 🚫
```

---

## 4-Level Memory Architecture

| Level | Description |
|-------|-------------|
| **1. File Memory** | Persistent storage in markdown: lessons.md, patterns.md, architecture.md, projects-log.md |
| **2. Vector Memory** | Semantic search with Ollama: RAG indexing, graceful degradation |
| **3. Context Memory** | Working memory: headers-first reading (~1-2% overhead), targeted deep reads |
| **4. Identity Memory** | Long-term learning: coding patterns, tech stack preferences |

---

## Installation

### Via AI Assistant

```
Execute the installation instructions from specs/001-global-agent-memory/INSTALL.md
```

The AI assistant will:
- Create `~/.claude/memory/` directory structure
- Set up SpecKit symlink
- Configure project templates
- Optionally install Ollama for vector search
- Install Quality Loop dependencies: `jsonlines`, `pyyaml`

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

### Quality Loop
- **[Quality Loop Documentation](docs/quality-loop.md)** - Complete guide
- **[Quickstart Guide](specs/002-implement-quality-loop/quickstart.md)** - Get started in 10 minutes

### Security Scanning
- **[Security Scanning Documentation](docs/security-scanning.md)** - Complete security guide
- **[Security Contract](specs/002-implement-quality-loop/contracts/security-scan.md)** - API contracts

---

## Project Status

**Version**: 0.3.0

**Implementation**: 200+ tasks across 24 phases complete

### Memory System Phases (v0.1.0)

| Phase | Status | Tasks |
|-------|--------|-------|
| Phase 3-9 | ✅ Complete | 73/73 |

### Quality Loop + Security Phases (v0.3.0)

| Phase | Status | Tasks |
|-------|--------|-------|
| Phase 1-10 | ✅ Complete | 91/91 |

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
