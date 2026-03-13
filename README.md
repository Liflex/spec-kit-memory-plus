# Spec Kit

> **Автоматизированный контроль качества спецификаций ПО на базе ИИ**

[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Spec Kit — система автоматической оценки качества спецификаций ПО с персистентной памятью агента. Итеративно проверяет артефакты по набору правил, генерирует критику и применяет улучшения через Quality Loop. Накапливает знания между сессиями — уроки, паттерны, архитектурные решения — и использует их для улучшения результатов.

---

## Быстрый старт

```bash
# Клонирование и установка
git clone https://github.com/github/spec-kit.git
cd spec-kit
pip install -r requirements.txt
```

### Python API (программный интерфейс)

```python
from specify_cli.quality import QualityLoop, RuleManager, Evaluator, Scorer, Critique, Refiner

loop = QualityLoop(RuleManager(), Evaluator(), Scorer(), Critique(), Refiner())

result = loop.run(
    artifact="My software specification...",
    task_alias="my-spec",
    criteria_name="backend",
    max_iterations=4,
)

print(f"Score: {result['score']:.2f}, Passed: {result['passed']}")
```

### CLI (Claude Code)

```bash
/speckit.loop --criteria backend                    # Запуск цикла оценки качества
/speckit.loop --project-type web-app                # Автовыбор шаблонов
/speckit.qa overview                                # Дашборд качества
/speckit.goals check                                # Проверка целей качества
/speckit.alerts check                               # Проверка оповещений
```

---

## Возможности

### Ядро системы

- **Quality Loop** — оценка, критика, улучшение (итеративный цикл)
- **13 шаблонов критериев** — backend, frontend, security, performance, testing, api-spec, database, docs, config, infrastructure, ui-ux, live-test, code-gen
- **Профили приоритетов** — доменная весовая оценка (web-app, microservice, ml-service, mobile-app и др.)
- **Автовыбор шаблонов** — `--project-type` автоматически подбирает нужные шаблоны

### Управление качеством

- **Цели (Goals)** — определение целевых показателей, отслеживание прогресса, рекомендации
- **История (History)** — тренды, статистика, сравнение запусков
- **Инсайты (Insights)** — рекомендации и оптимизация на базе ИИ
- **Аномалии (Anomalies)** — статистическое обнаружение аномалий
- **Бенчмарки (Benchmarks)** — перцентильный рейтинг, исторические базовые значения
- **Оповещения (Alerts)** — проактивные уведомления о проблемах качества
- **Технический долг (Debt)** — отслеживание и приоритизация долга качества
- **Обратная связь (Feedback Loop)** — адаптивное обучение конфигурации

### Продвинутые возможности

- **Политики шлюзов (Gate Policies)** — шлюзы качества для разных сред (production, staging, ci и др.)
- **Планы качества (Quality Plans)** — единые стратегии улучшения с пресетами
- **Отраслевые пресеты** — fintech, healthcare, ecommerce, saas, gaming, government, education, iot
- **Автоконфигурация** — настройка проекта одной командой с определением отрасли
- **Симуляция** — анализ «что если» перед применением изменений
- **Оптимизация** — байесовский, генетический, отжиг и другие методы
- **Мультивариантное тестирование** — сравнение A/B/C/n со статистическим анализом
- **Смешивание шаблонов** — объединение шаблонов в режимах union/consensus/weighted

### Память агента

- **3 уровня памяти** — сессионная (контекст), файловая (markdown), векторная (embeddings через Ollama)
- **Автоматическое чтение** — каждая команда `/speckit.*` читает накопленные знания перед выполнением
- **Немедленная запись** — уроки, паттерны и архитектурные решения сохраняются сразу при обнаружении
- **Векторный поиск** — семантический поиск по всей базе знаний через Ollama embeddings
- **Graceful degradation** — без Ollama работает только файловая память, без потери функциональности

### Отчётность

- **HTML** — интерактивные отчёты с графиками
- **Markdown** — человекочитаемые для документации
- **JSON** — машиночитаемые для CI/CD
- **Карточки результатов** — форматированный вывод в консоль

---

## Шаблоны критериев

| Шаблон | Описание |
|--------|----------|
| `backend` | Качество Backend API и серверной части |
| `frontend` | Качество Frontend UI/UX |
| `security` | Лучшие практики безопасности |
| `performance` | Оптимизация производительности |
| `testing` | Покрытие и качество тестов |
| `api-spec` | Полнота спецификации API |
| `database` | Схема БД и запросы |
| `docs` | Качество документации |
| `config` | Управление конфигурацией |
| `infrastructure` | Инфраструктура как код |
| `ui-ux` | Пользовательский интерфейс и UX |
| `live-test` | Валидация живого тестирования |
| `code-gen` | Качество генерации кода |

---

## Команды CLI

| Команда | Описание |
|---------|----------|
| `/speckit.loop` | Запуск цикла оценки качества |
| `/speckit.qa` | Дашборд QA |
| `/speckit.goals` | Управление целями качества |
| `/speckit.history` | История и тренды качества |
| `/speckit.insights` | Инсайты на базе ИИ |
| `/speckit.anomalies` | Обнаружение аномалий |
| `/speckit.benchmarks` | Бенчмаркинг |
| `/speckit.gates` | Политики шлюзов |
| `/speckit.alerts` | Оповещения о качестве |
| `/speckit.feedback` | Анализ обратной связи |
| `/speckit.debt` | Отслеживание технического долга |
| `/speckit.simulate` | Симуляция «что если» |
| `/speckit.plans` | Планы качества |
| `/speckit.industries` | Отраслевые пресеты |
| `/speckit.autoconfig` | Умная автоконфигурация |
| `/speckit.templates` | Реестр шаблонов |
| `/speckit.configs` | Конфигурации цикла |
| `/speckit.profiles` | Профили приоритетов |
| `/speckit.optimize` | Оптимизация качества |

Подробное описание и примеры см. в [docs/cli-reference.md](docs/cli-reference.md).

---

## Конфигурация

Базовая конфигурация проекта в `.speckit/config.yml`:

```yaml
quality:
  criteria: backend
  max_iterations: 4
  threshold_a: 0.8
  threshold_b: 0.9
  priority_profile: web-app
  gate_preset: production
```

Полный справочник по конфигурации см. в [docs/configuration.md](docs/configuration.md).

---

## Установка

### Требования

- Python 3.11+
- Git
- (Опционально) Ollama для векторной памяти

### Подробная установка

См. [INSTALL.md](INSTALL.md) для полной инструкции по установке:
- Интеграция с ИИ-ассистентами (Claude Code, Cursor)
- Настройка векторной памяти с Ollama
- Конфигурация команд CLI

---

## Документация

| Документ | Описание |
|----------|----------|
| [Подсистемы качества](docs/subsystems.md) | Цели, история, инсайты, оповещения, бенчмарки и др. |
| [Справочник CLI](docs/cli-reference.md) | Все команды с примерами |
| [Конфигурация](docs/configuration.md) | Файлы конфигурации, профили, политики шлюзов, оповещения |
| [Шаблоны и смешивание](docs/templates.md) | Реестр шаблонов, смешивание, пресеты |
| [Оптимизация](docs/optimization.md) | Методы оптимизации, Парето, симуляция |
| [Quality Loop](docs/quality-loop.md) | Архитектура и внутреннее устройство |
| [Память агента](docs/memory.md) | Уровни памяти, хранение, векторный поиск |
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
│   ├── loop_config.py         # Конфигурация цикла
│   ├── gate_policies.py       # Политики шлюзов
│   ├── quality_goals.py       # Система целей
│   ├── quality_history.py     # Отслеживание истории
│   ├── quality_insights.py    # Движок инсайтов
│   ├── quality_alerting.py    # Система оповещений
│   ├── template_registry.py   # Реестр шаблонов
│   └── ...                    # Другие модули
├── templates/commands/        # Шаблоны команд CLI
├── tests/                     # Тесты
├── docs/                      # Документация
├── INSTALL.md                 # Руководство по установке
└── README.md                  # Этот файл
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

MIT License — см. [LICENSE](LICENSE).

---

**Spec Kit** — Автоматизированный контроль качества спецификаций ПО на базе ИИ
