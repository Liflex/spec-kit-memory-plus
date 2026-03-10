# Implementation Tasks: Quality Loop with Security Integration

**Feature**: Quality Loop Implementation with Security Integration
**Created**: 2025-03-11
**Total Tasks**: 88
**Estimated Duration**: 40-60 hours

---

## Task Format Legend

- `- [ ]` - Checkbox (mark complete when done)
- `TXXX` - Task ID (sequential execution order)
- `[P]` - Parallelizable (can run simultaneously with other [P] tasks)
- `[US#]` - User Story (maps to user stories from spec.md)
- File paths included for each task

---

## Phase 1: Setup & Project Initialization

**Goal**: Initialize project structure and dependencies
**Independent Test Criteria**: All dependencies installed, tests pass, type checking valid

- [x] T001 Create quality module directory structure at src/specify_cli/quality/
- [x] T002 [P] Create security module directory structure at src/specify_cli/security/
- [x] T003 [P] Create .speckit/evolution/ directory for loop state persistence
- [x] T004 [P] Create .speckit/criteria/ directory for custom criteria templates
- [x] T005 [P] Add pyyaml dependency to pyproject.toml for YAML parsing
- [x] T006 [P] Add jsonlines dependency to pyproject.toml for history.jsonl
- [x] T007 [P] Create src/specify_cli/quality/__init__.py
- [x] T008 [P] Create src/specify_cli/security/__init__.py

---

## Phase 2: Foundational Components

**Goal**: Implement core data models and utilities
**Independent Test Criteria**: All models validate correctly, persistence works

- [x] T009 Define LoopState dataclass in src/specify_cli/quality/models.py
- [x] T010 Define EvaluationResult dataclass in src/specify_cli/quality/models.py
- [x] T011 Define CriteriaTemplate dataclass in src/specify_cli/quality/models.py
- [x] T012 Define QualityRule dataclass in src/specify_cli/quality/models.py
- [x] T013 Define SecurityReport dataclass in src/specify_cli/security/models.py
- [x] T014 [P] Define Threat dataclass in src/specify_cli/security/models.py
- [x] T015 Implement LoopStateManager in src/specify_cli/quality/state.py
- [x] T016 Implement save_state() method with JSON serialization in LoopStateManager
- [x] T017 Implement load_state() method with JSON deserialization in LoopStateManager
- [x] T018 Implement append_event() for history.jsonl in LoopStateManager

---

## Phase 3: User Story 1 - Criteria Templates

**Goal**: User can define and use quality criteria templates
**Independent Test Criteria**: Built-in templates load successfully, custom templates override built-ins

### Story Goal
As a developer, I want to define reusable quality criteria templates so that I can standardize quality checks across projects.

### Tasks

- [x] T019 [US1] Create RuleManager class in src/specify_cli/quality/rules.py
- [x] T020 [US1] Implement load_criteria() with user override and built-in fallback in RuleManager
- [x] T021 [US1] Implement list_criteria() to return available template names in RuleManager
- [x] T022 [US1] Implement get_rules_for_phase() filtering by phase in RuleManager
- [x] T023 [US1] Implement auto_detect_criteria() with keyword mapping in RuleManager
- [x] T024 [P] [US1] Create built-in api-spec.yml template in src/specify_cli/quality/templates/
- [x] T025 [P] [US1] Create built-in code-gen.yml template in src/specify_cli/quality/templates/
- [x] T026 [P] [US1] Create built-in docs.yml template in src/specify_cli/quality/templates/
- [x] T027 [P] [US1] Create built-in config.yml template in src/specify_cli/quality/templates/

---

## Phase 4: User Story 2 - Evaluation & Scoring

**Goal**: System evaluates artifacts and calculates quality scores
**Independent Test Criteria**: Scores calculate correctly (0.0-1.0), thresholds enforced, failures detected

### Story Goal
As a developer, I want automatic evaluation of code quality so that I can measure improvements objectively.

### Tasks

- [x] T028 [US2] Create Scorer class in src/specify_cli/quality/scorer.py
- [x] T029 [US2] Implement calculate_score() with weighted formula in Scorer
- [x] T030 [US2] Implement check_passed() with threshold and fail-severity in Scorer
- [x] T031 [US2] Implement calculate_distance_to_success() for gap analysis in Scorer
- [x] T032 [US2] Create Evaluator class in src/specify_cli/quality/evaluator.py
- [x] T033 [US2] Implement evaluate() with rule checking in Evaluator
- [x] T034 [US2] Implement _check_rule() with content-based analysis in Evaluator
- [x] T035 [P] [US2] Implement _check_content() for keyword/pattern matching in Evaluator
- [x] T036 [P] [US2] Implement _check_executable() for script-based checks in Evaluator

---

## Phase 5: User Story 3 - Critique & Refinement

**Goal**: System generates targeted feedback and applies fixes
**Independent Test Criteria**: Critiques generate fix instructions, refinements apply successfully

### Story Goal
As a developer, I want automatic suggestions for fixing quality issues so that I can improve code efficiently.

### Tasks

- [x] T037 [US3] Create Critique class in src/specify_cli/quality/critique.py
- [x] T038 [US3] Implement generate() with issue limiting in Critique
- [x] T039 [US3] Implement _generate_fix_instruction() with rule-specific templates in Critique
- [x] T040 [P] [US3] Define FIX_INSTRUCTIONS mapping for common rules in Critique
- [x] T041 [US3] Create Refiner class in src/specify_cli/quality/refiner.py
- [x] T042 [US3] Implement apply() with sequential fix application in Refiner
- [x] T043 [US3] Implement _apply_fix() using LLM in Refiner
- [x] T044 [P] [US3] Add fallback to rule-based fixes when LLM unavailable in Refiner

---

## Phase 6: User Story 4 - Quality Loop Orchestration

**Goal**: System coordinates full quality loop with iterations
**Independent Test Criteria**: Loops run to completion or threshold, state persists across sessions

### Story Goal
As a developer, I want an iterative quality improvement loop so that code automatically improves until quality threshold is reached.

### Tasks

- [x] T045 [US4] Create QualityLoop class in src/specify_cli/quality/loop.py
- [x] T046 [US4] Implement run() with iteration loop in QualityLoop
- [x] T047 [US4] Implement _check_stagnation() with delta detection in QualityLoop
- [x] T048 [US4] Implement phase transition logic (A → B) in QualityLoop
- [x] T049 [US4] Integrate state persistence with LoopStateManager in QualityLoop
- [x] T050 [P] [US4] Add user interruption handling (Ctrl+C) in QualityLoop
- [x] T051 [P] [US4] Implement stop condition checking in QualityLoop

---

## Phase 7: User Story 5 - CLI Commands

**Goal**: Users interact with quality loop via intuitive commands
**Independent Test Criteria**: All commands execute, arguments validate, output formats match specification

### Story Goal
As a developer, I want simple CLI commands to run quality loops so that I can integrate quality checks into my workflow.

### Tasks

- [x] T052 [US5] Create /speckit.loop command template in templates/commands/loop.md
- [x] T053 [US5] Implement argument parsing (--criteria, --max-iterations, --thresholds) in loop command
- [x] T054 [US5] Implement new loop mode with artifact detection in loop command
- [x] T055 [US5] Implement resume mode from current.json in loop command
- [x] T056 [US5] Implement status mode display in loop command
- [x] T057 [US5] Implement stop mode in loop command
- [x] T058 [US5] Implement list mode showing all loops in loop command
- [x] T059 [US5] Implement history mode with event stream in loop command
- [x] T060 [US5] Implement clean mode with confirmation in loop command
- [x] T061 [P] [US5] Create /speckit.implementloop command template in templates/commands/implementloop.md
- [x] T062 [P] [US5] Implement Phase 1 (implement) execution in implementloop command
- [x] T063 [P] [US5] Implement Phase 2 (quality loop) execution in implementloop command
- [x] T064 [P] [US5] Update /speckit.implement template in templates/commands/implement.md
- [x] T065 [P] [US5] Add quality loop recommendation section to implement command output

---

## Phase 8: Security Scanning Integration

**Goal**: Protect users from malicious skills and agents
**Independent Test Criteria**: Scanner detects threats, LLM review catches semantic issues, integration blocks malicious content

### Tasks

- [x] T066 Implement SecurityScanner class in src/specify_cli/security/scanner.py
- [x] T067 Implement scan_skill() wrapping ai-factory security-scan.py in SecurityScanner
- [x] T068 Implement _download_scanner() with cache check in SecurityScanner
- [x] T069 Implement LLMSecurityReviewer class in src/specify_cli/security/llm_review.py
- [x] T070 Implement review() method with semantic analysis in LLMSecurityReviewer
- [x] T071 [P] Integrate scan_skillsmp_results() into SkillsMPIntegration in src/specify_cli/memory/skillsmp_integration.py
- [x] T072 [P] Integrate scan_downloaded_skill() into SkillsMPIntegration in src/specify_cli/memory/skillsmp_integration.py
- [x] T073 [P] Integrate scan_created_agent() into SkillCreationWorkflow in src/specify_cli/memory/agents/skill_workflow.py
- [x] T074 [P] Add check_agent_specific_threats() for agent-specific patterns in SkillCreationWorkflow

---

## Phase 9: Tests

**Goal**: Comprehensive test coverage for quality and security components
**Independent Test Criteria**: All tests pass, coverage >80%

### Unit Tests

- [x] T075 [P] Test RuleManager: load_criteria(), list_criteria(), auto_detect_criteria()
- [x] T076 [P] Test Scorer: calculate_score(), check_passed(), calculate_distance_to_success()
- [x] T077 [P] Test Evaluator: evaluate() with pass/fail scenarios
- [x] T078 [P] Test Critique: generate() with max_issues limiting
- [x] T079 [P] Test Refiner: apply() with single and multiple fixes
- [x] T080 [P] Test QualityLoop: run() with threshold, stagnation, limit conditions
- [x] T081 [P] Test SecurityScanner: scan_skill() with threat detection
- [x] T082 [P] Test LLMSecurityReviewer: review() with semantic analysis

### Integration Tests

- [x] T083 Test /speckit.loop command: new, resume, status, stop, list, history, clean modes
- [x] T084 Test /speckit.implementloop command: full workflow from implementation to quality loop
- [ ] T085 Test security integration: SkillsMP download blocks malicious skills
- [ ] T086 Test security integration: Agent creation blocks malicious agents

---

## Phase 10: Documentation

**Goal**: Complete user and developer documentation
**Independent Test Criteria**: All examples work, documentation covers all features

- [x] T087 Create user guide for quality loop in docs/quality-loop.md
- [x] T088 Create security scanning guide in docs/security-scanning.md

---

## Dependencies

### User Story Completion Order

```
Setup (Phase 1)
    ↓
Foundational (Phase 2)
    ↓
US1: Criteria Templates (Phase 3)
    ↓
US2: Evaluation & Scoring (Phase 4)
    ↓
US3: Critique & Refinement (Phase 5)
    ↓
US4: Quality Loop Orchestration (Phase 6)
    ↓
US5: CLI Commands (Phase 7)
    ↓
Security Integration (Phase 8)
    ↓
Tests (Phase 9)
    ↓
Documentation (Phase 10)
```

### Inter-Story Dependencies

- **US1 → US2**: Criteria templates required for evaluation
- **US2 → US3**: Evaluation results required for critique
- **US3 → US4**: Critique and refinement required for loop
- **US4 → US5**: Loop logic required for CLI commands
- **US5 → Security**: CLI commands use security scanning

---

## Parallel Execution Opportunities

### Phase 1: Setup
```bash
# Can run in parallel (T002, T003, T004, T005, T006, T007, T008)
mkdir -p src/specify_cli/security/
mkdir -p .speckit/evolution/ .speckit/criteria/
# Edit pyproject.toml for dependencies
# Create __init__.py files
```

### Phase 3: Criteria Templates
```bash
# Can run in parallel (T024, T025, T026, T027)
# Create all 4 built-in templates simultaneously
```

### Phase 4: Evaluation & Scoring
```bash
# Can run in parallel (T035, T036)
# Implement content and executable checkers simultaneously
```

### Phase 5: Critique & Refinement
```bash
# Can run in parallel (T040, T044)
# Define fix instructions and add fallback simultaneously
```

### Phase 6: Quality Loop Orchestration
```bash
# Can run in parallel (T050, T051)
# Add interruption handling and stop condition checking simultaneously
```

### Phase 7: CLI Commands
```bash
# Can run in parallel (T061, T062, T063, T064, T065)
# Implement implementloop and implement updates simultaneously
```

### Phase 8: Security Integration
```bash
# Can run in parallel (T071, T072, T073, T074)
# Integrate all security hooks simultaneously
```

### Phase 9: Tests
```bash
# Can run in parallel (T075-T082)
# Run all unit test files simultaneously
```

---

## Implementation Strategy

### MVP Scope (Recommended First Delivery)

**Focus**: Core quality loop with basic CLI

**Phases**: 1-7 (Setup through CLI Commands)

**Excluded from MVP**:
- Security scanning integration (Phase 8)
- Comprehensive tests (Phase 9) - only smoke tests
- Full documentation (Phase 10) - only quickstart

**MVP Tasks**: T001-T065

**MVP Success Criteria**:
- `/speckit.loop` works with new, resume, status modes
- `/speckit.implementloop` runs implement → quality loop
- Built-in criteria templates (api-spec, code-gen) work
- Quality scores calculate correctly (0.0-1.0)
- Basic refinement improves code

### Incremental Delivery

1. **Sprint 1**: Phases 1-2 (Setup, Foundational) - 18 tasks
2. **Sprint 2**: Phases 3-4 (Criteria, Evaluation) - 18 tasks
3. **Sprint 3**: Phases 5-6 (Critique, Loop) - 15 tasks
4. **Sprint 4**: Phase 7 (CLI Commands) - 14 tasks
5. **Sprint 5**: Phase 8 (Security) - 9 tasks
6. **Sprint 6**: Phases 9-10 (Tests, Docs) - 14 tasks

---

## Validation Checklist

- [ ] All 88 tasks follow strict format: `- [ ] [TaskID] [P?] [Story?] Description`
- [ ] All user story tasks have [US#] labels
- [ ] All parallelizable tasks have [P] markers
- [ ] File paths specified for implementation tasks
- [ ] Each user story phase is independently testable
- [ ] Dependencies clearly documented
- [ ] MVP scope clearly defined
- [ ] Incremental delivery strategy documented

---

## Next Steps

1. **Start Implementation**: Begin with T001 from Phase 1
2. **Run Tests**: After each phase, run relevant tests
3. **Track Progress**: Mark tasks complete as you finish them
4. **Adjust as Needed**: Update tasks if implementation reveals new requirements

---

**Ready for implementation!** Run `/speckit.implement` to begin executing these tasks.
