# Spec Kit

> **Автоматизированный контроль качества спецификаций ПО на базе ИИ**

[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Spec Kit --- система для spec-driven development и автоматической оценки качества кода. Включает два основных инструмента:

1. **Spec-Driven Development** --- полный цикл от идеи до кода: спецификация, уточнение, планирование, генерация задач, реализация.
2. **Quality Loop** --- итеративная оценка и улучшение кода по набору правил с 13 шаблонами критериев.

---

## Быстрый старт

```bash
# Клонирование и установка
git clone https://github.com/github/spec-kit.git
cd spec-kit
pip install -r requirements.txt
```

### Цикл разработки (основной workflow)

```bash
# В чате Claude Code / Cursor:
/speckit.specify Описание вашей фичи...        # 1. Создать спецификацию
/speckit.clarify                                # 2. Уточнить детали
/speckit.plan Ваш стек и архитектура...         # 3. Создать техплан
/speckit.tasks                                  # 4. Сгенерировать задачи
/speckit.implement                              # 5. Реализовать
```

### Проверка качества кода

```bash
/speckit.loop --criteria backend                # Оценить backend-код
/speckit.loop --criteria backend,security       # Несколько шаблонов
/speckit.loop --project-type web-app            # Автовыбор шаблонов
```

### Быстрая фича (< 4 часов)

```bash
/speckit.features Добавить endpoint GET /api/users/:id/stats
```

Подробное руководство с примерами для каждой команды: **[docs/usage-guide.md](docs/usage-guide.md)**

---

## Возможности

### Разработка через спецификации

| Команда | Что делает |
|---------|-----------|
| `/speckit.constitution` | Задать принципы проекта |
| `/speckit.specify` | Создать спецификацию фичи |
| `/speckit.clarify` | Уточнить требования (ИИ задаёт вопросы) |
| `/speckit.plan` | Создать технический план |
| `/speckit.tasks` | Разбить план на задачи |
| `/speckit.analyze` | Проверить согласованность spec/plan/tasks |
| `/speckit.implement` | Реализовать задачи |
| `/speckit.features` | Быстрая фича за один шаг |
| `/speckit.checklist` | Кастомный чеклист |

### Контроль качества

| Команда | Что делает |
|---------|-----------|
| `/speckit.loop` | Итеративная оценка и улучшение кода |
| `/speckit.implementloop` | Реализация + quality loop |
| `/speckit.goals` | Целевые показатели качества |
| `/speckit.history` | Тренды и статистика |
| `/speckit.gates` | Quality gates для CI/CD |
| `/speckit.qa` | Обзор состояния качества |
| `/speckit.insights` | ИИ-рекомендации по улучшению |
| `/speckit.alerts` | Оповещения о проблемах |
| `/speckit.feedback` | Адаптивная настройка |

### Шаблоны и конфигурация

| Команда | Что делает |
|---------|-----------|
| `/speckit.templates` | Управление шаблонами критериев |
| `/speckit.profiles` | Профили приоритетов по типу проекта |
| `/speckit.configs` | Сохранённые конфигурации loop |

### Интеграции

| Команда | Что делает |
|---------|-----------|
| `/speckit.taskstoissues` | Экспорт задач в GitHub Issues |
| `/speckit.tobeads` | Импорт задач в Beads |

---

## Шаблоны критериев (13 шт.)

| Шаблон | Описание |
|--------|----------|
| `backend` | Backend API и серверная часть |
| `frontend` | Frontend UI/UX |
| `security` | Безопасность |
| `performance` | Производительность |
| `testing` | Тесты |
| `api-spec` | Спецификация API |
| `database` | Схема БД |
| `docs` | Документация |
| `config` | Конфигурация |
| `infrastructure` | Инфраструктура |
| `ui-ux` | UI/UX дизайн |
| `live-test` | Живое тестирование |
| `code-gen` | Генерация кода |

---

## Конфигурация

Файл `.speckit/config.yml` в корне проекта:

```yaml
quality:
  criteria: backend
  max_iterations: 4
  threshold_a: 0.8
  threshold_b: 0.9
  priority_profile: web-app
  gate_preset: production
```

Подробнее: [docs/configuration.md](docs/configuration.md)

---

## Документация

| Документ | Описание |
|----------|----------|
| **[Руководство по использованию](docs/usage-guide.md)** | **Как и зачем использовать каждую команду (начните здесь)** |
| [Быстрый старт](docs/quickstart.md) | Пошаговый пример от идеи до кода |
| [Quality Loop](docs/quality-loop.md) | Архитектура, шаблоны, правила и веса |
| [Конфигурация](docs/configuration.md) | Файлы конфигурации, профили, политики |
| [Шаблоны](docs/templates.md) | Реестр шаблонов, смешивание, пресеты |
| [Память агента](docs/memory.md) | 3 уровня памяти, векторный поиск |
| [Установка](INSTALL.md) | Полное руководство по установке |

---

## Структура проекта

```
spec-kit/
├── src/specify_cli/quality/   # Ядро системы качества
│   ├── models.py              # Модели данных
│   ├── rules.py               # Управление правилами
│   ├── evaluator.py           # Оценка качества
│   ├── scorer.py              # Скоринг
│   ├── critique.py            # Генерация критики
│   ├── refiner.py             # Улучшение артефактов
│   ├── loop.py                # Координатор цикла качества
│   └── templates/             # Шаблоны критериев (YAML)
├── templates/commands/        # Шаблоны команд CLI
├── tests/                     # Тесты
├── docs/                      # Документация
└── README.md
```

---

## Разработка

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/
```

---

## Лицензия

MIT License --- см. [LICENSE](LICENSE).

---

**Spec Kit** --- Spec-Driven Development + Автоматический контроль качества
