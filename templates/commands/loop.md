---
description: Run quality loop on code with iterative evaluation and refinement
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

### Mode Detection

Parse arguments to determine mode:
- `resume` → Resume mode (continue active loop)
- `status` → Status mode (show active loop)
- `stop` → Stop mode (stop active loop)
- `list` → List mode (show all loops)
- `history [alias]` → History mode (show loop history)
- `clean [alias|--all]` → Clean mode (delete loop files)
- No argument or `--criteria` etc. → New loop mode

### Mode: Resume

**Usage**: `/speckit.loop resume`

1. Get active loop from `.speckit/evolution/current.json`
2. If no active loop, error: "No active loop. Use `/speckit.loop` to start a new loop."
3. Load state from `.speckit/evolution/<task_alias>/run.json`
4. Display current progress:
   ```
   === Resuming Quality Loop ===

   Task Alias: {task_alias}
   Iteration: {iteration}/{max_iterations}
   Phase: {phase}
   Current Score: {score}
   Last Score: {last_score}
   Status: {status}

   Resume? (yes/no):
   ```
5. If user confirms, continue loop execution from current state
6. Use QualityLoop.run() with resumed artifact and state

### Mode: Status

**Usage**: `/speckit.loop status`

1. Get active loop from `.speckit/evolution/current.json`
2. If no active loop, info: "No active loop running."
3. Load and display:
   ```
   === Active Loop Status ===

   Task Alias: {task_alias}
   Run ID: {run_id}
   Status: {status}
   Iteration: {iteration}/{max_iterations}
   Phase: {phase}
   Current Score: {score}
   Last Score: {last_score}
   Step: {current_step}
   Started: {started_at}
   Updated: {updated_at}
   ```

### Mode: Stop

**Usage**: `/speckit.loop stop [reason]`

1. Get active loop from `.speckit/evolution/current.json`
2. If no active loop, error: "No active loop to stop."
3. Load state, set status=stopped, stop.reason=user_stop
4. Clear current.json
5. Display: "Loop stopped: {task_alias}"

### Mode: List

**Usage**: `/speckit.loop list`

1. List all loops from evolution directory
2. Display:
   ```
   === Quality Loops ===

   {task_alias}  |  {status}  |  {iteration}/{max_iterations}  |  Phase {phase}  |  Score: {score}
   ...
   ```
3. Sort by updated_at desc

### Mode: History

**Usage**: `/speckit.loop history [task_alias]`

1. If alias not provided, use active loop or error
2. Load events from `.speckit/evolution/<alias>/history.jsonl`
3. Display:
   ```
   === Loop History: {task_alias} ===

   {timestamp} | {event_type} | Iteration {iteration} | Phase {phase} | {details}
   ...
   ```

### Mode: Clean

**Usage**: `/speckit.loop clean [task_alias|--all]`

1. If `--all`, list all loops and ask confirmation
2. If alias provided, check if running:
   - If running, error: "Cannot clean running loop. Stop it first."
   - If not running, confirm deletion
3. Delete loop directory
4. Update current.json if was active
5. Display: "Loop deleted: {task_alias}"

### Mode: New Loop

**Usage**: `/speckit.loop [--criteria <name>[,<name>,...]] [--max-iterations <N>] [--threshold-a <0.0-1.0>] [--threshold-b <0.0-1.0>] [--artifact <path>]`

**Parse Arguments**:
- `--criteria`: One or more criteria templates, comma-separated (default: auto-detect).
  Examples: `--criteria backend`, `--criteria backend,live-test`, `--criteria frontend,security,live-test`
  When multiple criteria are specified, their rules are merged (deduplicated by rule_id, last wins)
  and the strictest thresholds are used.
- `--max-iterations`: Max iterations (default: 4)
- `--threshold-a`: Phase A threshold (default: 0.8)
- `--threshold-b`: Phase B threshold (default: 0.9)
- `--artifact`: Path to artifact file (default: auto-detect)

**Step 1: Detect Artifact**

Auto-detect artifact:
1. Try git diff against HEAD~1 for changed files
2. Fallback: parse tasks.md for file paths
3. Read and concatenate all relevant files into artifact content

**Step 2: Detect Task Alias**

1. Get git branch name
2. Format as task alias (remove feature/, fix/, etc.)
3. Or use `specs/XXX-{branch-name}` format

**Step 3: Auto-detect Criteria**

If `--criteria` not provided:
1. Read tasks.md first task description
2. Use RuleManager.auto_detect_criteria()

**Available Criteria Templates (13 built-in)**:
`api-spec`, `code-gen`, `docs`, `config`, `database`, `frontend`, `backend`,
`infrastructure`, `testing`, `security`, `performance`, `ui-ux`, `live-test`

**`live-test` — Physical Verification Criteria**:
When `live-test` is included in `--criteria`, the evaluator MUST perform real execution:
- **Backend**: Start the server, send actual HTTP requests to endpoints, verify responses and DB writes
- **Frontend**: Launch a real browser via Playwright/Selenium, navigate pages, click buttons, fill forms, verify renders
- **Database**: Run real migrations, insert data, verify constraints and indexes
- **API**: Call real endpoints with synthetic payloads, assert full request-response-storage chain
- **CLI**: Execute real commands, verify output and side effects

"Looks correct in code" is NOT a passing check. Only "executed and produced expected result" passes.
`live-test` is designed to be combined with other criteria: `--criteria backend,live-test`

**Step 4: Run Quality Loop**

1. Initialize components:
   ```python
   rule_manager = RuleManager()
   scorer = Scorer()
   evaluator = Evaluator(rule_manager, scorer)
   critique = Critique(max_issues=5)
   refiner = Refiner(llm_client=current_llm)
   state_manager = LoopStateManager()
   loop = QualityLoop(rule_manager, evaluator, scorer, critique, refiner, state_manager)
   ```

2. Run loop (criteria_name supports comma-separated values):
   ```python
   # Single criteria: "backend"
   # Multiple criteria: "backend,live-test" — rules merged, strictest thresholds
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

**Step 5: Display Progress**

For each iteration, display:
```
Iteration {n}/{max} | Phase {phase} | Score: {score} | {PASS/FAIL}

Failed: {rule_ids}
Warnings: {rule_ids}

Critique: {issues_count} issues to fix
Refining...
```

**Step 6: Final Summary**

```
=== Quality Loop Complete ===

Iteration {final_iteration}/{max_iterations} | Phase {final_phase} | Score: {final_score} | {PASS/FAIL}
Stop Reason: {stop_reason}
Distance to Success: {gap} (threshold: {threshold}, score: {score})

Failed Rules Remaining: {count}
- {rule_id}: {reason}

Changed Files: {count}
- {file_paths}

Iterations: {total_iterations}
Total Time: {duration}

Next Steps:
- Run `/speckit.loop` with --max-iterations {n+2} to continue
- OR manually fix remaining issues
```

## Error Handling

| Error | Action |
|-------|--------|
| No tasks.md | Error: "No tasks.md found. Run `/speckit.tasks` first." |
| Criteria not found | Error: "Criteria '{name}' not found. Available: {list}". If comma-separated, shows which specific name failed. |
| Git not detected | Warning: "Git not detected. Artifact detection will use all source files." |
| Loop already running | Error: "Loop '{alias}' is already running. Stop it first." |
| LLM unavailable | Warning: "LLM not available. Refinements will be limited." |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 2 | Warning (incomplete but continued) |
