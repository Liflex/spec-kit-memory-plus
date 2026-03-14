# AI-агенты и скиллы

SpecKit поддерживает систему AI-агентов с полуавтоматическим созданием и интеграцией в workflow разработки.

---

## Обзор

**Агенты** — специализированные AI-персоны с определённой ролью, навыками и личностью. Используются для:
- Специализированной помощи в конкретных доменах (frontend, backend, DevOps, ML)
- Контекстно-зависимого code review
- Автоматизации повторяющихся задач

**Скиллы** — готовые промпты/инструкции из сообщества (425K+ через SkillsMP).

---

## Команды

| Команда | Описание |
|---------|----------|
| `/speckit.createagent` | Создание агента в полуавтоматическом режиме |
| `/speckit.implement` | Автоматическое определение нужных агентов |

---

## Полуавтоматическое создание агентов

### Workflow

```
1. AI анализирует запрос → определяет тип агента
2. AI генерирует черновик → на основе шаблона
3. AI показывает черновик → пользователь просматривает
4. Пользователь подтверждает/редактирует → или просит web-поиск
5. AI применяет правки → сохраняет агента
```

### Пример сессии

```
Пользователь: /speckit.createagent Нужен агент для code review Python проектов

AI: Анализирую... Создаю агента на основе шаблона "backend-dev":
    - Роль: Python Code Reviewer
    - Навыки: PEP8, type hints, security patterns, async/await...

    === AGENTS.md ===
    # python-code-reviewer
    > Role: Python Code Reviewer
    ...

    [Показывает все файлы]

    Options:
    1. ✅ Confirm
    2. ✏️ Edit
    3. 🔍 Research (web search for best practices)
    4. ❌ Cancel

Пользователь: Добавь Django и SQL injection detection

AI: Applying feedback...

    Updated skills:
    - PEP8 and code style
    - Type hints validation
    - Security patterns
    - async/await patterns
    - Django best practices ✨ NEW
    - SQL injection detection ✨ NEW

    [Shows updated draft]

Пользователь: Confirm

AI: Saving agent...
    Created: ~/.claude/agents/python-code-reviewer/
    - AGENTS.md
    - SOUL.md
    - USER.md
    - MEMORY.md
    - memory/

    Agent "python-code-reviewer" ready for use!
```

---

## Доступные шаблоны

| Шаблон | Роль | Ключевые навыки |
|--------|------|-----------------|
| `frontend-dev` | Frontend Developer | React, TypeScript, CSS, Accessibility |
| `backend-dev` | Backend Developer | API design, Databases, Auth, Security |
| `fullstack-dev` | Fullstack Developer | Frontend + Backend + DevOps basics |
| `architect` | Software Architect | System design, Scalability, Security |
| `qa-tester` | QA Tester | Test automation, Edge cases, Quality |
| `devops` | DevOps Engineer | CI/CD, Docker, Kubernetes, Monitoring |
| `data-engineer` | Data Engineer | ETL, Pipelines, SQL optimization |
| `ml-engineer` | ML Engineer | Model training, Deployment, Python ML |

---

## Интеграция в /speckit.implement

При выполнении `/speckit.implement` система автоматически проверяет необходимость специализированных агентов.

### Триггеры определения

| Тип задач | Нужен агент |
|-----------|-------------|
| ML/AI, model training, inference | `ml-engineer` |
| CI/CD, Docker, Kubernetes | `devops` |
| ETL, data pipelines, big data | `data-engineer` |
| Complex testing, QA | `qa-tester` |
| Architecture decisions | `architect` |
| Frontend components, UI | `frontend-dev` |
| API, database, backend | `backend-dev` |

### Процесс

```
1. /speckit.implement анализирует tasks.md
2. Определяет требуемые специализации
3. Проверяет ~/.claude/agents/ на наличие нужных агентов
4. Если агент отсутствует — предлагает создать:

   ## Agent Capability Gap Detected
   
   Task "Train ML model" requires specialized expertise in ML/AI.
   
   Available agents: [frontend-dev, backend-dev]
   Missing: ml-engineer
   
   Options:
   1. Create agent now (semi-automatic) - recommended
   2. Continue without specialized agent
   3. Skip tasks requiring this expertise
   
   Create ml-engineer agent? (yes/no)

5. После создания — продолжает реализацию
```

---

## Структура агента

Каждый агент создаётся в `~/.claude/agents/{agent-name}/`:

```
~/.claude/agents/python-code-reviewer/
├── AGENTS.md      # Роль, команда, навыки
├── SOUL.md        # Личность, принципы, стиль общения
├── USER.md        # Профиль пользователя, предпочтения
├── MEMORY.md      # Сводка знаний
└── memory/
    ├── lessons.md      # Выученные правила (3+ повторений)
    ├── patterns.md     # Паттерны улучшений
    ├── projects-log.md # История задач
    ├── architecture.md # Решения
    └── handoff.md      # Контекст сессии
```

### AGENTS.md

Основной файл агента:

```markdown
# python-code-reviewer

> **Role**: Python Code Reviewer
> **Created**: 2026-03-15
> **Base Template**: backend-dev
> **Memory System**: 4-Level

---

## Agent Role

Специализированный агент для code review Python проектов.

---

## Team

- backend-dev
- qa-tester

## Skills

- PEP8 and code style
- Type hints validation
- Security patterns
- Django best practices
- SQL injection detection
```

### SOUL.md

Личность и стиль:

```markdown
# python-code-reviewer - Soul

## Personality

Внимательный к деталям, конструктивный в критике. 
Фокус на качестве кода, безопасности и поддерживаемости.

---

## Core Principles

1. **Clarity First** - Communicate clearly and concisely
2. **Context Awareness** - Always consider memory context
3. **Continuous Learning** - Learn from every interaction
```

---

## SkillsMP — готовые скиллы

Помимо создания агентов, можно использовать готовые скиллы из сообщества.

### Поиск и установка

```python
from specify_cli.memory.skillsmp.integration import SkillsMPIntegration

integration = SkillsMPIntegration()

# Поиск
results = integration.search_skills("react development", limit=5)

# Установка (с автоматической проверкой безопасности)
integration.download_skill(skill_id, target_dir)
```

### Требования

- API-ключ SkillsMP (опционально)
- Без ключа используется GitHub fallback

См. [INSTALL.md](../INSTALL.md) Step 7 для настройки API-ключа.

---

## Безопасность

Все агенты и скиллы проходят двухуровневую проверку:

| Уровень | Метод | Что проверяет |
|---------|-------|---------------|
| **Level 1** | Статический анализ | Prompt injection, data exfiltration, destructive commands |
| **Level 2** | LLM-обзор | Intent mismatch, contextual threats, obfuscation |

**Результаты:**
- `SAFE` — установка разрешена
- `BLOCKED` — установка заблокирована
- `WARNING` — требуется подтверждение пользователя

Подробнее: [security-scanning.md](security-scanning.md)

---

## Python API

### SemiAutomaticAgentCreator

```python
from specify_cli.memory.agents.skill_workflow import SemiAutomaticAgentCreator

creator = SemiAutomaticAgentCreator()

# Анализ запроса
analysis = creator.analyze_request("Нужен агент для ML задач")
# => {"suggested_template": "ml-engineer", "confidence": "high", ...}

# Генерация черновика
result = creator.generate_draft(
    agent_name="ml-assistant",
    base_template="ml-engineer",
    customizations={
        "skills": ["PyTorch", "Transformers", "MLOps"]
    }
)

# Показать черновик пользователю
for filename, content in result['files'].items():
    print(f"=== {filename} ===")
    print(content)

# Применить правки
creator.apply_feedback({
    "add_skills": ["ONNX export", "Model quantization"]
})

# Сохранить
saved_files = creator.save_agent()
```

### SkillCreationWorkflow

```python
from specify_cli.memory.agents.skill_workflow import SkillCreationWorkflow

workflow = SkillCreationWorkflow()

# Поиск существующих агентов
results = workflow.search_agents("python code review")

# Создание из требований
files = workflow.create_agent_from_requirements(
    agent_name="my-agent",
    requirements={
        "role": "Custom Agent",
        "skills": ["skill1", "skill2"],
        "personality": "Professional and helpful"
    }
)
```

---

## См. также

- [security-scanning.md](security-scanning.md) — система безопасности
- [memory.md](memory.md) — система памяти агентов
- [../INSTALL.md](../INSTALL.md) — установка и настройка