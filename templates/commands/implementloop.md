---
description: Implement tasks and run quality loop in one command
scripts:
  sh: ~/.claude/spec-kit/scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: ~/.claude/spec-kit/scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

### Pre-flight: Ensure `.specify/` exists

Before running any scripts, ensure `.specify/` directory exists in the project root. If missing, copy from `~/.claude/spec-kit/.specify`:
```bash
SPECKIT_SOURCE="$HOME/.claude/spec-kit/.specify"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ ! -d "$REPO_ROOT/.specify" ] && [ -d "$SPECKIT_SOURCE" ]; then
  cp -r "$SPECKIT_SOURCE" "$REPO_ROOT/.specify"
fi
```

### Phase 1: Implementation (same as `/speckit.implement`)

Follow the exact same workflow as `/speckit.implement`:

1. **Check checklists status** (if exists)
2. **Load and analyze implementation context**
3. **Project setup verification**
4. **Parse tasks.md structure**
5. **Execute implementation following task plan**
   - Phase-by-phase execution
   - Respect dependencies
   - Follow TDD approach
   - Mark completed tasks as [X]
6. **Progress tracking and error handling**
7. **Completion validation**

Output after Phase 1:
```
=== Implementation Complete ===

Tasks Completed: {count}
Files Modified: {count}
Tests Created: {count}

Time: {duration}

---
## Starting Quality Loop...
```

### Phase 2: Quality Loop (automatic)

**Parse Arguments**:
- `--criteria <name>[,<name>,...]`: One or more criteria templates, comma-separated (default: auto-detect from task description).
  Examples: `--criteria backend`, `--criteria backend,live-test`, `--criteria frontend,security,live-test`
  When multiple criteria are specified, their rules are merged (deduplicated by rule_id, last wins)
  and the strictest thresholds are used.
- `--max-iterations <N>`: Max iterations (default: 4)
- `--threshold-a <0.0-1.0>`: Phase A threshold (default: 0.8)
- `--threshold-b <0.0-1.0>`: Phase B threshold (default: 0.9)

**Available Criteria Templates (13 built-in)**:
`api-spec`, `code-gen`, `docs`, `config`, `database`, `frontend`, `backend`,
`infrastructure`, `testing`, `security`, `performance`, `ui-ux`, `live-test`

**`live-test` — Physical Verification**: When included, the evaluator MUST actually run the code,
send real requests, launch browsers, and verify observable results. No mocks, no assumptions.
Designed to be combined: `--criteria backend,live-test`

**Step 1: Detect Artifact**

After implementation, detect artifact:
1. Use git diff to get all changed files
2. Read and concatenate changed files into artifact content
3. If no git, use all files referenced in tasks.md

**Step 2: Detect Task Alias and Criteria**

1. Get task alias from git branch or feature directory
2. Auto-detect criteria from first task description using RuleManager.auto_detect_criteria()

**Step 3: Initialize Quality Loop Components**

```python
from specify_cli.quality import (
    RuleManager, Scorer, Evaluator,
    Critique, Refiner, QualityLoop, LoopStateManager
)

rule_manager = RuleManager()
scorer = Scorer()
evaluator = Evaluator(rule_manager, scorer)
critique = Critique(max_issues=5)
refiner = Refiner(llm_client=current_llm)
state_manager = LoopStateManager()
loop = QualityLoop(rule_manager, evaluator, scorer, critique, refiner, state_manager)
```

**Step 4: Run Quality Loop**

```python
# criteria_name supports comma-separated: "backend,live-test"
result = loop.run(
    artifact=artifact,
    task_alias=task_alias,
    criteria_name=criteria_name,  # e.g., "backend,live-test"
    max_iterations=max_iterations,
    threshold_a=threshold_a,
    threshold_b=threshold_b,
    llm_client=current_llm
)
```

**Step 5: Display Iteration Progress**

For each iteration:
```
=== Quality Loop Iteration {n}/{max} ===

Phase: {phase} | Score: {score} | {PASS/FAIL}

Failed Rules:
- {rule_id}: {reason}

Warnings:
- {rule_id}: {reason}

Critique: {issues_count} issues to address
Refining artifact...
```

**Step 6: Final Summary**

```
=== Quality Loop Complete ===

Final Score: {score}
Phase: {phase}
Status: {passed/failed}
Stop Reason: {stop_reason}

Summary:
- Iterations: {n}/{max}
- Changed Files: {count}
- Total Time: {duration}

Quality Improvement:
- Initial Score: {initial_score}
- Final Score: {final_score}
- Improvement: +{delta}

Failed Rules Remaining:
{list of remaining issues}

Next Steps:
- Run `/speckit.loop --max-iterations {n+2}` to continue improving
- OR manually fix remaining issues
- OR run `/speckit.loop status` to see loop state
```

## Output Format

Combine both phases:

```
=== Implementing Tasks from tasks.md ===

[Implementation progress...]

✅ Phase 1: Setup - 8 tasks completed
✅ Phase 2: Foundational - 10 tasks completed
✅ Phase 3: User Story 1 - 9 tasks completed
...

=== Implementation Complete ===

Tasks Completed: 45
Files Modified: 12
Tests Created: 8

Time: 12m 30s

---
## Starting Quality Loop...

Detected artifact: 12 files changed
Auto-detected criteria: code-gen,live-test
Task alias: user-auth-jwt

=== Quality Loop Started ===

Iteration 1/4 | Phase A | Score: 0.72 | FAIL

Failed Rules:
- correctness.tests: "Unit tests not found"
- quality.error_handling: "No error handling detected"

Warnings:
- quality.readability: "Missing comments"

Critique: 2 issues to fix
Refining...

Iteration 2/4 | Phase A | Score: 0.84 | PASS (Phase A → B)

Iteration 3/4 | Phase B | Score: 0.88 | FAIL

Failed Rules:
- performance.caching: "No caching for expensive operations"

Critique: 1 issue to fix
Refining...

Iteration 4/4 | Phase B | Score: 0.92 | PASS

=== Quality Loop Complete ===

Final Score: 0.92
Phase: B
Status: PASSED
Stop Reason: threshold_reached

Summary:
- Iterations: 4/4
- Changed Files: 14
- Total Time: 4m 45s

Quality Improvement:
- Initial Score: 0.72
- Final Score: 0.92
- Improvement: +0.20

All quality gates passed! ✓
```

## Error Handling

Same as `/speckit.implement` for Phase 1.

For Phase 2, same as `/speckit.loop`:
| Error | Action |
|-------|--------|
| Criteria not found | Error with available templates |
| No artifact detected | Warning: "No changes detected. Skipping quality loop." |
| LLM unavailable | Warning: "LLM not available. Refinements limited." |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (implementation + quality loop passed) |
| 1 | Error (implementation failed OR quality loop failed) |
| 2 | Warning (quality loop incomplete but stopped) |
