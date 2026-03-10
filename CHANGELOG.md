# Changelog

<!-- markdownlint-disable MD024 -->

Recent changes to the Specify CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

- **Criteria Templates** — 4 встроенных шаблона правил качества:
  - `api-spec.yml` — для API спецификаций (CRUD, status codes, auth)
  - `code-gen.yml` — для кода (tests, error handling, types, structure)
  - `docs.yml` — для документации (title, installation, usage)
  - `config.yml` — для конфигурации (syntax, types, paths, secrets)

- **Quality Loop Components**:
  - `RuleManager` — управление criteria templates
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

### Dependencies

- Added `jsonlines>=4.0` — для history.jsonl event streaming
- Added `pyyaml>=6.0` — для criteria templates (уже был, но явно указан)

### Documentation

- **[Quality Loop Documentation](docs/quality-loop.md)** — полное руководство по Quality Loop
  - Architecture, components, data flow
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
│   ├── rules.py               # Rule manager
│   ├── scorer.py              # Score calculator
│   ├── evaluator.py           # Evaluator
│   ├── critique.py            # Critique generator
│   ├── refiner.py             # Refiner
│   ├── loop.py                # Quality loop orchestrator
│   └── templates/             # Built-in criteria
│       ├── api-spec.yml
│       ├── code-gen.yml
│       ├── docs.yml
│       └── config.yml
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
