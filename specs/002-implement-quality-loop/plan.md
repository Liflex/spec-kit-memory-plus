# Implementation Plan: Quality Loop with Security Integration

**Branch**: `002-implement-quality-loop` | **Date**: 2025-03-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-implement-quality-loop/spec.md`

## Summary

Добавить в SpecKit итеративный quality loop вдохновлённый Reflex Loop из ai-factory: три новые команды (`/speckit.implementloop`, `/speckit.loop`, обновление `/speckit.implement`) и двухуровневую security интеграцию для SkillsMP и создания агентов. Quality loop автоматически оценивает код по правилам с score-based измеримостью, генерирует критику, исправляет и повторяет до threshold. Security сканирование использует Python статический анализатор (Level 1) и LLM семантический обзор (Level 2) из ai-factory.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- Существующий: typer (CLI), rich (output), pydantic (validation)
- ai-factory: security-scan.py (Level 1 scanner)
- Новый: pyyaml/yaml (criteria templates), jsonlines (history.jsonl)

**Storage**:
- `.speckit/evolution/` — loop state (run.json, history.jsonl, artifact.md, current.json)
- `.speckit/criteria/` — criteria templates (YAML)
- `~/.claude/memory/` — lessons о безопасности

**Testing**: pytest с unit тестами для scoring, правил, scanner wrapper

**Target Platform**: CLI инструмент для разработчиков, работающих с SpecKit

**Project Type**: CLI tool (расширение существующего specify_cli)

**Performance Goals**:
- Quality loop: < 5 минут для implement + 4 итерации
- Security scan: < 30 секунд на скилл/агент
- Score calculation: < 1 секунда

**Constraints**:
- Python должен быть доступен для security-scan.py
- LLM должен быть доступен для Level 2 обзора
- `/speckit.implement` НЕ изменяется в логике (только рекомендация)
-backward compatibility с существующими командами

**Scale/Scope**:
- 3 новые команды (implementloop, loop, recommendation)
- 2 точки security интеграции (SkillsMP, Agent Creation)
- ~4 criteria templates (api-spec, code-gen, docs, config)
- ~2000 LOC добавляется к существующему коду

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Проект SpecKit не имеет конституции в `memory/constitution.md`. Используем стандартные практики разработки:

| Принцип | Статус | Детали |
|---------|--------|--------|
| **Library-First** | ✅ PASS | Quality loop будет отдельным модулем (`src/specify_cli/quality/`) |
| **CLI Interface** | ✅ PASS | Все команды доступны через CLI с текстовым выводом |
| **Test-First** | ⚠️ PARTIAL | Тесты будут написаны, но не TDD для всей фичи |
| **Integration Testing** | ⚠️ PARTIAL | Contract тесты для security scanner, но не все интеграции |
| **Simplicity** | ✅ PASS | Максимум 3 новых модулей, reuse существующего code |
| **Observability** | ✅ PASS | history.jsonl для аудита, score reporting |

**Gates Passed**: 4/6, 2 Partial (допустимо для фичи, не нарушающей принципы)

## Project Structure

### Documentation (this feature)

```text
specs/002-implement-quality-loop/
├── spec.md              # Feature specification (создан)
├── plan.md              # Этот файл (/speckit.plan)
├── research.md          # Phase 0: исследование
├── data-model.md        # Phase 1: модели данных
├── quickstart.md        # Phase 1: quickstart guide
├── contracts/           # Phase 1: контракты
│   ├── quality-eval.md  # Quality evaluation API
│   ├── security-scan.md # Security scan API
│   └── cli-commands.md  # CLI commands interface
└── tasks.md             # Phase 2: (будет создан /speckit.tasks)
```

### Source Code (repository root)

```text
src/specify_cli/
├── quality/                    # НОВЫЙ: Quality Loop Module
│   ├── __init__.py
│   ├── loop.py                 # QualityLoop: основной класс
│   ├── evaluator.py            # Evaluator: оценка по правилам
│   ├── rules.py                # Rule management и criteria templates
│   ├── scorer.py               # Score calculation
│   ├── critique.py             # Critique generator
│   ├── refiner.py              # Refinement applier
│   ├── state.py                # Loop state persistence (run.json, history.jsonl)
│   └── templates/              # Criteria templates (YAML)
│       ├── api-spec.yml
│       ├── code-gen.yml
│       ├── docs.yml
│       └── config.yml
├── security/                   # НОВЫЙ: Security Module
│   ├── __init__.py
│   ├── scanner.py              # Wrapper для ai-factory security-scan.py
│   ├── llm_review.py           # Level 2: LLM semantic review
│   ├── skillsmp_hooks.py       # Hooks для SkillsMP integration
│   └── agent_hooks.py          # Hooks для Agent Creation
├── commands/                   # ИЗМЕНЕНИЕ: Новые команды
│   ├── implementloop.py        # /speckit.implementloop command
│   ├── loop.py                 # /speckit.loop command
│   └── implement.py            # ОБНОВЛЕНИЕ: добавить рекомендацию
└── memory/                     # ИЗМЕНЕНИЕ: Security для agent creation
    └── agents/
        └── skill_workflow.py    # ОБНОВЛЕНИЕ: добавить security scan

tests/quality/                   # НОВЫЙ: Quality Loop тесты
├── test_scorer.py
├── test_evaluator.py
├── test_rules.py
└── test_state.py

tests/security/                  # НОВЫЙ: Security тесты
├── test_scanner.py
├── test_llm_review.py
└── test_hooks.py

.speckit/                        # НОВАЯ: Runtime state
├── evolution/
│   ├── current.json             # Активный loop pointer
│   └── <task-alias>/
│       ├── run.json             # Loop state
│       ├── history.jsonl        # Event stream
│       └── artifact.md          # Artifact content
└── criteria/                    # Runtime criteria override
    └── custom.yml

templates/commands/              # ИЗМЕНЕНИЕ: Новые команды
├── implementloop.md
└── loop.md
```

**Structure Decision**: Option 1 (Single project) с разделением на 3 новых модуля (`quality/`, `security/`) и обновлением существующих (`commands/`, `memory/agents/`). Структура следует существующим паттернам SpecKit и обеспечивает чёткое разделение ответственности.

---

## Phase 0: Research & Technical Decisions

### Unknowns to Resolve

1. **ai-factory security-scan.py интеграция**:
   - Как интегрировать external Python скрипт?
   - Где находится security-scan.py в ai-factory репозитории?
   - Как обрабатывать exit codes (0=CLEAN, 1=BLOCKED, 2=WARNINGS)?

2. **Criteria templates формат**:
   - Какой YAML schema для правил (id, description, severity, weight, phase, check)?
   - Как хранить и загружать templates?
   - Как auto-detect criteria для `--criteria auto-detect`?

3. **LLM semantic review**:
   - Как вызывать LLM из Python кода?
   - Как передавать результаты сканирования для review?
   - Как обрабатывать LLM ответ (CRITICAL/WARNING/SAFE)?

4. **Recommendation формат**:
   - Какой формат рекомендации в `/speckit.implement`?
   - Как детектировать, когда показывать?
   - Как сделать reusable recommendation template?

5. **Artifact detection**:
   - Как определить "artifact" для quality loop?
   - Это все изменённые файлы? Specific file pattern?
   - Как передаётся artifact между итерациями?

### Dependencies to Research

1. **ai-factory security patterns**:
   - Best practices для prompt injection detection
   - Data exfiltration patterns
   - Stealth instruction patterns

2. **Score-based evaluation**:
   - Weighted scoring formulas
   - Threshold progression (A → B)
   - Stagnation detection algorithms

3. **CLI recommendation patterns**:
   - Как другие CLI инструменты показывают рекомендации?
   - Best practices для actionable recommendations

### Integration Patterns

1. **SpecKit command integration**:
   - Как существующие команды вызывают друг друга?
   - Как `/speckit.implement` вызывает other commands?
   - Как передаётся контекст между commands?

2. **SkillsMP integration**:
   - Как `SkillsMPIntegration.search_skills()` работает?
   - Где hook для post-download scanning?
   - Как передавать скилл для сканирования?

3. **Memory System integration**:
   - Как `SkillCreationWorkflow` работает?
   - Где hook для post-create scanning?
   - Как сохранять результаты в memory?

---

## Phase 0: Research Output

См. [research.md](./research.md) для детальных решений по:
- ai-factory security-scan.py интеграция
- Criteria templates YAML schema
- LLM semantic review паттерны
- CLI recommendation format
- Artifact detection strategy

---

## Phase 1: Design & Contracts

### Data Model

См. [data-model.md](./data-model.md) для:
- QualityRule entity
- CriteriaTemplate entity
- EvaluationResult entity
- SecurityThreat entity
- SkillScanReport entity
- AgentScanReport entity
- LoopState entity

### CLI Contracts

См. [contracts/cli-commands.md](./contracts/cli-commands.md) для:
- `/speckit.implementloop` command signature и behaviour
- `/speckit.loop` command signature и behaviour
- `/speckit.implement` recommendation format
- Argument parsing и defaults

### Quality Evaluation Contract

См. [contracts/quality-eval.md](./contracts/quality-eval.md) для:
- Evaluator API (evaluate_artifact())
- Rule checking interface
- Score calculation interface
- Critique generation interface
- Refinement application interface

### Security Scan Contract

См. [contracts/security-scan.md](./contracts/security-scan.md) для:
- Level 1 scanner API (scan_skill(), scan_agent())
- Level 2 LLM review API (review_artifact())
- Threat classification (CRITICAL/WARNING/SAFE)
- Scan result reporting

### Quickstart Guide

См. [quickstart.md](./quickstart.md) для:
- Установка зависимостей
- Первый запуск `/speckit.implementloop`
- Первый запуск `/speckit.loop`
- Security scanning для SkillsMP
- Security scanning для Agent Creation

---

## Implementation Phases

### Phase 1.1: Quality Loop Foundation (Week 1)

**Цель**: Базовая quality loop инфраструктура без сканирования

1. **Create module structure**: `src/specify_cli/quality/`
2. **Implement state persistence**: `state.py` (run.json, history.jsonl, current.json)
3. **Implement scorer**: `scorer.py` (score calculation formula)
4. **Implement rules**: `rules.py` (load criteria templates, rule management)
5. **Implement evaluator**: `evaluator.py` (evaluate artifact against rules)
6. **Unit tests**: scorer, rules, evaluator, state

**Deliverables**:
- `quality/` module с 5 классами
- Unit тесты с >80% coverage
- `tests/quality/` directory

### Phase 1.2: Quality Loop Core (Week 2)

**Цель**: Основной quality loop цикл (evaluate → critique → refine → repeat)

1. **Implement critique**: `critique.py` (generate targeted feedback)
2. **Implement refiner**: `refiner.py` (apply targeted fixes)
3. **Implement loop**: `loop.py` (main QualityLoop class with iterations)
4. **Create criteria templates**: YAML files for api-spec, code-gen, docs, config
5. **Integration tests**: full loop iterations

**Deliverables**:
- `QualityLoop.run()` method с iteration logic
- 4 criteria templates в YAML
- Integration тесты для loop lifecycle

### Phase 1.3: CLI Commands (Week 2-3)

**Цель**: Три команды (/implementloop, /loop, recommendation)

1. **Create `/speckit.implementloop`**: `commands/implementloop.py`
2. **Create `/speckit.loop`**: `commands/loop.py`
3. **Update `/speckit.implement`**: add recommendation section
4. **Create command templates**: `templates/commands/implementloop.md`, `loop.md`
5. **CLI tests**: command invocation, argument parsing

**Deliverables**:
- 2 новые команды
- 1 обновлённая команда
- 2 command templates
- CLI тесты

### Phase 1.4: Security Integration (Week 3-4)

**Цель**: Двухуровневое security сканирование для SkillsMP и Agent Creation

1. **Create security module**: `src/specify_cli/security/`
2. **Implement scanner wrapper**: `scanner.py` (ai-factory security-scan.py wrapper)
3. **Implement LLM review**: `llm_review.py` (Level 2 semantic review)
4. **Create SkillsMP hooks**: `skillsmp_hooks.py` (post-download scan)
5. **Create Agent hooks**: `agent_hooks.py` (post-create scan)
6. **Update skill_workflow.py**: integrate security scans
7. **Security tests**: scanner, LLM review, hooks

**Deliverables**:
- `security/` module с 4 классами
- 2 hook points (SkillsMP, Agent Creation)
- Security тесты с threat examples
- Updated `SkillCreationWorkflow`

### Phase 1.5: Documentation & Polish (Week 4)

**Цель**: Полная документация и UX полировка

1. **Generate contracts**: quality-eval.md, security-scan.md, cli-commands.md
2. **Generate data model**: data-model.md
3. **Generate quickstart**: quickstart.md
4. **Create README updates**: добавить новые команды в основной README
5. **UX improvements**: better error messages, progress indicators
6. **Edge case handling**: interruption, false positives, oscillation

**Deliverables**:
- 5 documentation files
- Updated README.md
- Edge case coverage

---

## Constitution Re-check (Post-Design)

| Принцип | Статус | Детали |
|---------|--------|--------|
| **Library-First** | ✅ PASS | `quality/` и `security/` — reusable модули |
| **CLI Interface** | ✅ PASS | Все команды с text I/O, JSON history |
| **Test-First** | ✅ PASS | Unit + integration тесты для всех модулей |
| **Integration Testing** | ✅ PASS | Contract тесты для scanner, LLM review, hooks |
| **Simplicity** | ✅ PASS | 3 модуля, reuse существующего code, ~2000 LOC |
| **Observability** | ✅ PASS | history.jsonl, score reporting, security logs |

**Gates Passed**: 6/6 — все принципы соблюдены

---

## Dependencies & Risks

### External Dependencies

1. **ai-factory security-scan.py**:
   - **Risk**: External script может измениться
   - **Mitigation**: Pin version, fork если нужно, wrapper для абстракции

2. **LLM availability**:
   - **Risk**: LLM может быть недоступен
   - **Mitigation**: Graceful degradation (Level 1 only), warning пользователю

3. **Python availability**:
   - **Risk**: Python может не быть в PATH
   - **Mitigation**: Clear error message, installation instructions

### Technical Risks

1. **Quality loop stagnation**:
   - **Risk**: Loop может зациклиться на одном score
   - **Mitigation**: Stagnation detection, max_iterations limit

2. **False positives в security scan**:
   - **Risk**: Legitimate code блокируется
   - **Mitigation**: WARNING level для uncertain cases, user override

3. **Performance degradation**:
   - **Risk**: Quality loop может быть медленным
   - **Mitigation**: Parallel execution (PRODUCE || PREPARARE), max_iterations limit

### Integration Risks

1. **Backward compatibility**:
   - **Risk**: Новые команды ломают существующий workflow
   - **Mitigation**: `/speckit.implement` без изменений логики, только recommendation

2. **SpecKit evolution**:
   - **Risk**: SpecKit API изменится во время разработки
   - **Mitigation**: Минимизировать изменения в существующем code, использовать hooks

---

## Success Metrics

| Метрика | Target | Как измеряется |
|---------|--------|----------------|
| Quality loop время | < 5 мин | Benchmark на типовой задаче |
| Security scan время | < 30 сек | Benchmark на типовом скилле |
| Test coverage | >80% | pytest --cov |
| Commands работают | 3/3 | Manual testing + CI |
| Documentation completeness | 5/5 файлов | Checklist |
| User adoption | TBD | Post-release metrics |

---

## Next Steps

1. ✅ **Phase 0**: Выполнить research и создать research.md
2. ⏳ **Phase 1**: Создать data-model.md, contracts/, quickstart.md
3. ⏳ **Phase 2**: Запустить `/speckit.tasks` для генерации задач

**Текущий статус**: Phase 0 в процессе выполнения
