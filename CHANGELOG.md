# Changelog

## [0.75.1] - 2026-03-13

### Added
- **Exp 132: Blend Preset Integration with Quality Loop**
  - Added `blend_preset` parameter to `QualityLoop.run()` for direct preset usage
  - Auto-detection and recommendation of blend presets based on project type
  - Intelligent project_type to blend_preset mapping in `TemplateRegistry`
  - Seamless integration: blend presets take precedence over project_type and criteria
  - New presets info method `get_all_blend_presets_info()` for CLI display

### Changed
- Updated `QualityLoop.run()` docstring with blend_preset parameter documentation
- Enhanced `TemplateRegistry.recommend_blend_preset()` with smart project type mapping
- Updated README.md with blend preset usage examples for quality loop

### Fixed
- Improved preset recommendation fallback to keyword matching when direct mapping fails



<!-- markdownlint-disable MD024 -->

Recent changes to the Specify CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- feat(quality): add `--project-type` parameter for automatic template selection (Exp 128)
  - Automatically selects optimal template combination based on project type
  - Supports 8 project types: web-app, microservice, ml-service, mobile-app, graphql-api, serverless, desktop, infrastructure
  - Overrides `--criteria` when specified for simplified UX
  - Example: `--project-type web-app` → frontend,backend,api-spec,security,performance,testing,docs

- feat(quality): add template comparison feature (Exp 129)
  - `speckit templates compare` - side-by-side comparison of 2-4 templates
  - `speckit templates diff` - diff-style comparison between two templates
  - Compare domain tags, severity breakdown, priority profiles, and phases
  - Visual checkmarks (✓/✗) for quick scanning of differences
  - Example: `speckit templates compare frontend mobile backend`

- feat(quality): add template blend feature (Exp 130)
  - `speckit templates blend` - blend multiple templates into a single configuration
  - Three blend modes: union (all rules), consensus (majority rules), weighted (custom weights)
  - Save blended templates to YAML files for reuse
  - Control template influence with custom weights
  - Example: `speckit templates blend frontend backend security --mode union --output full-stack.yml`
  - Weighted example: `speckit templates blend backend frontend --mode weighted --weights backend:0.7,frontend:0.3`

- feat(quality): add blend presets for common use cases (Exp 131)
  - `speckit templates presets list` - list all available blend presets
  - `speckit templates presets info <preset>` - show detailed preset information
  - `speckit templates presets search <query>` - search presets by keyword
  - `speckit templates presets recommend <project-type>` - recommend preset for project type
  - `speckit templates presets apply <preset>` - apply preset to create blended template
  - 10 built-in presets: full_stack_secure, microservices_robust, api_first, mobile_backend, data_pipeline, cloud_native, quality_rigorous, startup_mvp, iot_platform, devsecops
  - Filter presets by tag or project type
  - Example: `speckit templates presets apply full_stack_secure --output my-stack.yml`

- feat(extensions): support `.extensionignore` to exclude files/folders during `specify extension add` (#1781)

## [0.3.0] - 2025-03-11

### Added 🆕 Quality Loop System

- **Quality Loop** — Итеративное улучшение качества кода с автоматической оценкой
  - Score-based метрики (0.0-1.0) для измеримого качества кода
  - Автоматическая генерация критики и исправлений
  - Stagnation detection для предотвращения залипаний
  - Фазовая модель: Phase A (threshold 0.8), Phase B (threshold 0.9)

- **Новые CLI команды**:
  - `/speckit.implementloop` — Реализация задач + автоматический Quality Loop
  - `/speckit.loop` — Отдельный Quality Loop для существующего кода
    - Modes: new, resume, status, stop, list, history, clean
  - `/speckit.implement` — Обновлён с рекомендацией Quality Loop в конце

- **Criteria Templates** — 13 встроенных шаблонов правил качества (поддержка нескольких через запятую: `--criteria backend,live-test`):
  - `api-spec.yml` — для API спецификаций (10 правил: CRUD, status codes, auth)
  - `code-gen.yml` — для кода (11 правил: tests, error handling, types, structure)
  - `docs.yml` — для документации (10 правил: title, installation, usage)
  - `config.yml` — для конфигурации (9 правил: syntax, types, paths, secrets)
  - `database.yml` — для баз данных (10 правил: primary/foreign keys, indexes, SQLi)
  - `frontend.yml` — для frontend кода (10 правил: components, state management, routing)
  - `backend.yml` — для backend сервисов (10 правил: API structure, service layer, DI)
  - `infrastructure.yml` — для DevOps и IaC (10 правил: Dockerfile, health checks, scaling)
  - `testing.yml` — для тестовых файлов (10 правил: AAA pattern, assertions, isolation)
  - `security.yml` — для безопасности (10 правил: secrets, validation, auth, XSS/SQLi)
  - `performance.yml` — для производительности (10 правил: caching, async, queries)
  - `ui-ux.yml` — для UI/UX дизайна (10 правил: accessibility, responsive, states)
  - `live-test.yml` — физическое тестирование (10 правил: реальные HTTP запросы, браузер, БД, полная цепочка)

- **Auto-detection критериев** — Automatic detection по ключевым словам:
  - "api", "endpoint", "rest" → `api-spec`
  - "database", "sql", "schema" → `database`
  - "frontend", "react", "component" → `frontend`
  - "backend", "service", "middleware" → `backend`
  - "docker", "kubernetes", "deploy" → `infrastructure`
  - "test", "testing", "unit" → `testing`
  - "security", "auth", "authorization" → `security`
  - "performance", "cache", "optimization" → `performance`
  - "ux", "accessibility", "responsive" → `ui-ux`
  - "live", "physical", "runtime", "smoke" → `live-test`

- **Quality Loop Components**:
  - `RuleManager` — управление criteria templates с auto-detection
  - `Scorer` — расчёт score с weighted formula
  - `Evaluator` — оценка артефактов против правил
  - `Critique` — генерация targeted feedback
  - `Refiner` — применение исправлений (через LLM)
  - `QualityLoop` — оркестрация цикла
  - `LoopStateManager` — persistence (run.json, history.jsonl, artifact.md, current.json)

- **Persistence для Quality Loop**:
  - `.speckit/evolution/` — сохранение состояния loops
  - Resume capability после прерывания (Ctrl+C, crash)
  - Event stream для аудита (history.jsonl)

### Added 🆕 Security Scanning System

- **Двухуровневая защита** от вредоносных скиллов и агентов
  - **Level 1**: Python статический сканер (из ai-factory)
    - Детектирует: prompt injection, data exfiltration, stealth instructions
    - Детектирует: destructive commands, config tampering, encoded payloads
    - Exit codes: 0=CLEAN, 1=BLOCKED, 2=WARNINGS
  - **Level 2**: LLM семантический обзор
    - Анализирует контекст и намерения
    - Выявляет: authority abuse, obfuscation, intent mismatch

- **Автоматическое сканирование** при:
  - Получении скиллов из SkillsMP (`SkillsMPIntegration`)
  - Создании новых агентов (`SkillCreationWorkflow`)
  - Автоматическое удаление BLOCKED контента

- **Security Components**:
  - `SecurityScanner` — wrapper для ai-factory security-scan.py
  - `LLMSecurityReviewer` — Level 2 семантический обзор
  - `skillsmp_hooks.py` — hooks для SkillsMP integration
  - `agent_hooks.py` — hooks для Agent creation
  - Agent-specific threat detection

- **Три уровня результатов**:
  - **SAFE** ✅ — Безопасно, установка разрешена
  - **WARNING** ⚠️ — Требуется подтверждение пользователя
  - **BLOCKED** 🚫 — Опасно, автоматически удаляется

### Added

- **Unit тесты** для Quality Loop (9 тестовых файлов)
  - test_scorer.py — scoring, thresholds, distance calculation
  - test_rules.py — criteria templates, auto-detection
  - test_state.py — persistence, event streaming
  - test_evaluator.py — rule checking, content analysis
  - test_critique.py — fix instruction generation
  - test_refiner.py — refinement application
  - test_loop_integration.py — full loop workflow

- **Unit тесты** для Security Scanning (3 тестовых файла)
  - test_scanner.py — scan result parsing, threat detection
  - test_llm_review.py — LLM response parsing, fallback behavior
  - test_hooks.py — SkillsMP и Agent hooks

### Changed

- **README.md** — полное обновление с описанием Quality Loop и Security Scanning
  - Новые секции для Quality Loop (использование, примеры, benefits)
  - Новые секции для Security Scanning (как работает, угрозы, защита)
  - Обновлён список команд SpecKit с новыми командами
  - Обновлён статус проекта с фазами Quality Loop и Security
  - Добавлена таблица всех 13 criteria templates

- **docs/quality-loop.md** — расширена документация по Quality Loop
  - Детальное описание всех 13 criteria templates
  - Объяснение как severity влияет на loop (fail блокирует, warn снижает)
  - Примеры score calculation и phase transitions
  - Таблица auto-detection keywords

### Dependencies

- Added `jsonlines>=4.0` — для history.jsonl event streaming
- Added `pyyaml>=6.0` — для criteria templates (уже был, но явно указан)

### Documentation

- **[Quality Loop Documentation](docs/quality-loop.md)** — полное руководство по Quality Loop
  - Architecture, components, data flow
  - Все 13 criteria templates детально описаны
  - API reference, usage examples
  - Troubleshooting, performance metrics

- **[Security Scanning Documentation](docs/security-scanning.md)** — полное руководство по security
  - Threat patterns, detection methods
  - API reference, hooks documentation
  - Integration points, best practices

- **[Quickstart Guide](specs/002-implement-quality-loop/quickstart.md)** — начать за 10 минут
  - Part 1: Quality Loop (3 способа использования)
  - Part 2: Security Scanning (автоматическое сканирование)
  - Part 3-9: Workflows, configuration, troubleshooting

- **API Contracts**:
  - [CLI Commands Contract](specs/002-implement-quality-loop/contracts/cli-commands.md)
  - [Quality Evaluation Contract](specs/002-implement-quality-loop/contracts/quality-eval.md)
  - [Security Scan Contract](specs/002-implement-quality-loop/contracts/security-scan.md)

### Performance

- Quality Loop итерация: <60s
- Security scan: <30s
- Score calculation: <10ms
- Rule loading: <100ms
- Evaluation (10 rules): <1s

### Project Structure

```
src/specify_cli/
├── quality/                    # 🆕 Quality Loop Module
│   ├── __init__.py
│   ├── models.py              # Data models
│   ├── state.py               # Loop state manager
│   ├── rules.py               # Rule manager с auto-detection
│   ├── scorer.py              # Score calculator
│   ├── evaluator.py           # Evaluator
│   ├── critique.py            # Critique generator
│   ├── refiner.py             # Refiner
│   ├── loop.py                # Quality loop orchestrator
│   └── templates/             # Built-in criteria (12 шаблонов)
│       ├── api-spec.yml       # API спецификации
│       ├── code-gen.yml       # Генерация кода
│       ├── docs.yml           # Документация
│       ├── config.yml         # Конфигурация
│       ├── database.yml       # Базы данных 🆕
│       ├── frontend.yml       # Frontend код 🆕
│       ├── backend.yml        # Backend сервисы 🆕
│       ├── infrastructure.yml # DevOps & IaC 🆕
│       ├── testing.yml        # Тестовые файлы 🆕
│       ├── security.yml       # Безопасность 🆕
│       ├── performance.yml    # Производительность 🆕
│       ├── ui-ux.yml          # UI/UX дизайн 🆕
│       └── live-test.yml      # Физическое тестирование 🆕
├── security/                   # 🆕 Security Module
│   ├── __init__.py
│   ├── scanner.py              # Level 1 scanner wrapper
│   ├── llm_review.py           # Level 2 LLM reviewer
│   ├── skillsmp_hooks.py       # SkillsMP hooks
│   └── agent_hooks.py          # Agent creation hooks

.speckit/                        # 🆕 Runtime state
├── evolution/                  # Quality Loop state
│   ├── current.json
│   └── <task-alias>/
│       ├── run.json
│       ├── history.jsonl
│       └── artifact.md
└── criteria/                    # Custom criteria
    └── custom.yml

templates/commands/              # 🆕 Updated CLI templates
├── loop.md                      # /speckit.loop command
├── implementloop.md             # /speckit.implementloop command
└── implement.md                 # Updated with recommendation

tests/                           # 🆕 New tests
├── quality/                     # Quality Loop tests
│   ├── test_scorer.py
│   ├── test_rules.py
│   ├── test_state.py
│   ├── test_evaluator.py
│   ├── test_critique.py
│   ├── test_refiner.py
│   └── test_loop_integration.py
└── security/                    # Security tests
    ├── test_scanner.py
    ├── test_llm_review.py
    └── test_hooks.py
```

---

## [0.2.0] - 2026-03-09

### Changed

- fix: sync agent list comments with actual supported agents (#1785)
- feat(extensions): support multiple active catalogs simultaneously (#1720)
- Pavel/add tabnine cli support (#1503)
- Add Understanding extension to community catalog (#1778)
- Add ralph extension to community catalog (#1780)
- Update README with project initialization instructions (#1772)
- feat: add review extension to community catalog (#1775)
- Add fleet extension to community catalog (#1771)
- Integration of Mistral vibe support into speckit (#1725)
- fix: Remove duplicate options in specify.md (#1765)
- fix: use global branch numbering instead of per-short-name detection (#1757)
- Add Community Walkthroughs section to README (#1766)
- feat(extensions): add Jira Integration to community catalog (#1764)
- Add Azure DevOps Integration extension to community catalog (#1734)
- Fix docs: update Antigravity link and add initialization example (#1748)
- fix: wire after_tasks and after_implement hook events into command templates (#1702)
- make c ignores consistent with c++ (#1747)
- chore: bump version to 0.1.13 (#1746)
- feat: add kiro-cli and AGENT_CONFIG consistency coverage (#1690)
- feat: add verify extension to community catalog (#1726)
- Add Retrospective Extension to community catalog (#1741)
- fix(scripts): add empty description validation and branch checkout error handling (#1559)
- fix: correct Copilot extension command registration (#1724)
- fix(implement): remove Makefile from C ignore patterns (#1558)
- Add sync extension to community catalog (#1728)
- fix(checklist): clarify file handling behavior for append vs create (#1556)
- fix(clarify): correct conflicting question limit from 10 to 5 (#1557)
- chore: bump version to 0.1.12 (#1737)
- fix: use RELEASE_PAT so tag push triggers release workflow (#1736)
- fix: release-trigger uses release branch + PR instead of direct push to main (#1733)
- fix: Split release process to sync pyproject.toml version with git tags (#1732)
