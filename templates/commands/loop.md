---
description: Run quality loop on code with iterative evaluation and refinement
scripts:
  sh: ~/.claude/spec-kit/scripts/bash/check-prerequisites.sh --json
  ps: ~/.claude/spec-kit/scripts/powershell/check-prerequisites.ps1 -Json
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

**Usage**: `/speckit.loop [--criteria <name>[,<name>,...]] [--project-type <type>] [--max-iterations <N>] [--threshold-a <0.0-1.0>] [--threshold-b <0.0-1.0>] [--artifact <path>] [--priority-profile <name>] [--strategy <strategy>] [--strict] [--lenient] [--html-output <path>] [--markdown-output <path>] [--json-output <path>] [--include-categories <cat1,cat2,...>] [--exclude-categories <cat1,cat2,...>] [--gate-preset <preset>] [--gate-policy <name>] [--gate-policy-auto] [--gate-goal-mode <mode>] [--auto-update-goals] [--suggest-goals] [--apply-suggestion <n>] [--max-suggestions <n>]`

**Parse Arguments**:
- `--criteria`: One or more criteria templates, comma-separated (default: auto-detect).
  Examples: `--criteria backend`, `--criteria backend,live-test`, `--criteria frontend,security,live-test`
  When multiple criteria are specified, their rules are merged (deduplicated by rule_id, last wins)
  and the strictest thresholds are used.

- `--project-type`: Project type for automatic template selection (Exp 128). Overrides `--criteria` if specified.
  Options: `web-app`, `microservice`, `ml-service`, `mobile-app`, `graphql-api`, `serverless`, `desktop`, `infrastructure`
  Example: `--project-type web-app` automatically selects frontend,backend,api-spec,security,performance,testing,docs

- `--max-iterations`: Max iterations (default: 4)
- `--threshold-a`: Phase A threshold (default: 0.8)
- `--threshold-b`: Phase B threshold (default: 0.9)
- `--artifact`: Path to artifact file (default: auto-detect)
- `--priority-profile`: Priority profile for domain-based scoring (default: auto).
  Available: auto, default, web-app, mobile-app, ml-service, data-pipeline, graphql-api, microservice.
  Cascade profiles: Combine multiple profiles with `+` (e.g., `web-app+mobile-app`).
  Named presets: fullstack-balanced, web-ml, mobile-ml, conservative, aggressive, etc.
  - `auto`: Auto-detect from project files (package.json, requirements.txt, etc.)
  - `default`: Neutral multipliers (all 1.0x)
  - `web-app+mobile-app`: Cascade profile for fullstack apps
  - `graphql-api+ml-service`: Cascade profile for GraphQL + ML
  - `fullstack-balanced`: Named preset for balanced fullstack (web-app+mobile-app with equal weights)
  Run `/speckit.profiles list` to see all profiles and `/speckit.profiles cascade <profile1+profile2>` for cascade info.
  Run `/speckit.profiles wizard` for an interactive profile selection guide.
- `--strategy`: Cascade merge strategy when using cascade profiles or weighted cascades (default: avg).
  Available strategies:
  - `avg`, `mean`, `bal`: Average strategy (default) - averages multipliers from all profiles
  - `max`, `strict`: Max strategy - uses highest multiplier for each domain (strictest requirements)
  - `min`, `lenient`: Min strategy - uses lowest multiplier for each domain (lenient requirements)
  - `wgt`, `weighted`, `custom`: Weighted strategy - requires weighted cascade syntax (e.g., `web-app:2+mobile-app:1`)
  Examples:
  - `--priority-profile web-app+mobile-app --strategy max`: Strictest requirements for each domain
  - `--priority-profile web-app+mobile-app --strategy min`: Lenient requirements for each domain
  - `--priority-profile web-app:2+mobile-app:1 --strategy wgt`: 2x weight on web, 1x on mobile
- `--strict`: **Shortcut** for strict quality mode. Equivalent to `--priority-profile web-app+mobile-app --strategy max`.
  Uses fullstack cascade profile with max strategy (highest multipliers per domain) for most demanding quality checks.
  Ideal for production-ready code where quality is critical.
- `--lenient`: **Shortcut** for lenient quality mode. Equivalent to `--priority-profile default --strategy min`.
  Uses default profile with min strategy (lowest multipliers) for relaxed requirements and faster iteration.
  Ideal for early development iterations and rapid prototyping.
- `--html-output`: Path to save interactive HTML report (e.g., `--html-output quality-report.html`).
  Generates a beautiful, interactive HTML report with:
  - Score timeline chart (Chart.js visualization)
  - Metrics grid (iterations, phase, score, status)
  - Failed rules & warnings table
  - Modern gradient design with responsive layout
  Example: `--html-output .speckit/quality-report.html`
  Default: No HTML report generated.
- `--markdown-output`: Path to save Markdown report (e.g., `--markdown-output quality-report.md`).
  Generates a clean, text-based Markdown report perfect for:
  - Git diffs and version control
  - Code review comments and pull requests
  - Issue tracker integration
  - Simple text-based logging
  Example: `--markdown-output .speckit/quality-report.md`
  Default: No Markdown report generated.
- `--json-output`: Path to save JSON report (e.g., `--json-output quality-report.json`).
  Generates a structured JSON report perfect for:
  - CI/CD pipeline integration
  - Automated quality gates
  - Programmatic analysis and monitoring
  - Integration with other tools (Jenkins, GitHub Actions, etc.)
  Includes category breakdown, failed rules, warnings, and score timeline.
  Example: `--json-output .speckit/quality-report.json`
  Default: No JSON report generated.
  **Note**: You can use `--html-output`, `--markdown-output`, and `--json-output` together to generate all formats.
- `--include-categories`: Only include specific categories in JSON report (comma-separated).
  Filters the JSON report to only show specified categories.
  Available categories: security, performance, testing, code-quality, documentation, infrastructure, api, database, frontend, backend, mobile, desktop, devops, monitoring, graphql, grpc, websocket, cache, serverless, service-mesh, terraform, container, migration, message-queue, general.
  Example: `--include-categories security,performance` — only show security and performance issues
  Default: All categories included
- `--exclude-categories`: Exclude specific categories from JSON report (comma-separated).
  Removes specified categories from the JSON report.
  Example: `--exclude-categories documentation,code-quality` — ignore docs and code quality issues
  Default: No categories excluded
  **Note**: `--include-categories` and `--exclude-categories` are mutually exclusive. Use one or the other, not both.
- `--gate-preset`: Quality gate preset for advanced gate evaluation (Exp 55).
  Available presets:
  - `production`: Strict gate for production (score ≥ 0.95, 0 critical/high, ≤2 medium, ≤5 low)
  - `staging`: Standard gate for staging (score ≥ 0.85, 0 critical, ≤2 high, ≤5 medium, ≤10 low)
  - `development`: Relaxed gate for development (score ≥ 0.70, 0 critical, ≤5 high, ≤10 medium)
  - `ci`: CI/CD pipeline gate with blocking (score ≥ 0.80, 0 critical/high, ≤3 medium, ≤10 low)
  - `strict`: Ultra-strict gate for critical systems (score ≥ 0.98, 0 critical/high/medium, ≤2 low)
  - `lenient`: Very relaxed gate for experimental features (score ≥ 0.60, 0 critical, ≤10 high)
  Example: `--gate-preset production` — use production quality gate
  Default: No gate evaluation (basic threshold check only)
  **Note**: Gate results are included in the result dict and can be used for CI/CD blocking
- `--gate-policy`: Custom gate policy name from project config (.speckit/gate-policies.yml).
  Allows defining project-specific quality gates with custom rules.
  See Gate Policy Configuration below for details.
  Default: No custom policy (use preset if specified)
- `--gate-policy-auto`: Automatically recommend and apply gate policy based on context (Exp 60).
  Uses AI-powered recommendation to select the best gate policy based on:
  - CI/CD environment (GitHub Actions, GitLab CI, etc.)
  - Git branch (production, staging, feature, etc.)
  - Project type (web-app, API, microservice, etc.)
  - Security sensitivity indicators
  - Current quality score
  Example: `--gate-policy-auto` — automatically select and apply recommended policy
  Default: Disabled (use --gate-preset or --gate-policy for manual selection)
  **Note**: Ignored if --gate-preset or --gate-policy is specified (manual selection takes precedence)
- `--gate-goal-mode`: Goal-based quality gate mode for validating against quality goals (Exp 71).
  Uses quality goals as gate criteria instead of score thresholds.
  Available modes:
  - `strict`: All goals must be achieved, at-risk goals block gate
  - `moderate`: All goals must be achieved or at-risk, failed goals block gate (default)
  - `lenient`: Only failed goals block gate, at-risk allowed
  - `conservative`: At-risk or failed goals block gate
  - `balanced`: At least 80% of goals must be achieved
  Example: `--gate-goal-mode strict` — block on any at-risk or failed goals
  Default: No goal gate evaluation (use gate-preset or gate-policy for score-based gates)
  **Note**: Requires goals to be configured (see `/speckit.goals`). Result includes `goal_gate_result` with pass/fail status.
- `--auto-update-goals`: Automatically update goal progress during quality loop (Exp 71).
  When used with `--gate-goal-mode`, updates goals before evaluating gate.
  This ensures the gate uses the latest goal progress.
  Example: `--gate-goal-mode moderate --auto-update-goals` — update goals then evaluate
  Default: Disabled (goals must be manually updated via `/speckit.goals check`)
  **Note**: Only effective when used with `--gate-goal-mode`
- `--suggest-goals`: Automatically generate and display smart goal suggestions (Exp 75).
  When enabled, analyzes quality history to suggest optimal goals before running the loop.
  Shows intelligent recommendations based on:
  - Recent performance patterns and trends
  - Category-specific improvement opportunities
  - Achievable targets with confidence levels
  - Alternative targets (conservative/moderate/aggressive)
  Example: `--suggest-goals` — show suggestions before running loop
  Default: Disabled (suggestions must be manually requested via `/speckit.goals suggest`)
  **Note**: Suggestions are displayed for review; use `--apply-suggestion` to apply automatically
- `--apply-suggestion <n>`: Automatically apply the Nth suggestion from goal suggestions (Exp 75).
  Requires `--suggest-goals` to be enabled. Applies the specified suggestion number before running the loop.
  Example: `--suggest-goals --apply-suggestion 1` — apply the top suggestion
  Example: `--suggest-goals --apply-suggestion 2` — apply the second suggestion
  Default: No auto-apply (suggestions are displayed only)
  **Note**: Only effective when used with `--suggest-goals`
- `--max-suggestions <n>`: Maximum number of goal suggestions to generate (Exp 75).
  Requires `--suggest-goals` to be enabled. Limits the number of suggestions shown.
  Example: `--suggest-goals --max-suggestions 5` — show up to 5 suggestions
  Default: 10 suggestions
  **Note**: Only effective when used with `--suggest-goals`
- `--show-result-card`: Display a visually appealing result card after quality loop completes (Exp 102).
  Shows a compact summary with:
  - Status indicator (excellent, good, acceptable, needs work, critical)
  - Score bar with visual progress
  - Failed rules grouped by category
  - Actionable next steps
  Example: `--show-result-card` — display result card after loop
  Default: Disabled (result card not shown)
- `--result-card-compact`: Use compact single-line format for result card (Exp 102).
  Requires `--show-result-card`. Uses minimal vertical space.
  Example: `--show-result-card --result-card-compact` — compact result card
  Default: Full box format with borders
- `--result-card-theme`: Color theme for result card (Exp 102).
  Available themes: `default`, `dark`, `high-contrast`, `minimal`
  Example: `--show-result-card --result-card-theme dark` — dark theme result card
  Default: `default` theme
- `--export-reports`: Export quality reports in multiple formats simultaneously (Exp 103, 104, 106).
  Generates reports in all specified formats with a single command.
  Available formats: `console`, `json`, `html`, `markdown`, `csv` (Exp 104, 105), `excel` (Exp 106)
  Example: `--export-reports json,html,markdown,csv,excel` — generate all reports
  Example: `--export-reports json,excel` — generate JSON and Excel only
  Default: No export (use individual --json-output, --html-output, --markdown-output flags)
- `--export-dir`: Directory to save exported reports (Exp 103, 104).
  Used with `--export-reports` to specify output directory.
  Example: `--export-reports json,html,csv --export-dir ./reports`
  Default: Current directory
- `--export-prefix`: Filename prefix for exported reports (Exp 103, 104).
  Used with `--export-reports` to customize filenames.
  Example: `--export-reports csv --export-prefix quality-check`
  Generates: `quality-check.json`, `quality-check.csv`, etc.
  Default: `quality_report`

**Quality Mode Shortcuts**:
The `--strict` and `--lenient` flags provide convenient presets for common quality scenarios:

| Mode | Shortcut | Equivalent To | Use Case |
|------|----------|---------------|----------|
| Strict | `--strict` | `--priority-profile web-app+mobile-app --strategy max` | Production code, critical quality |
| Lenient | `--lenient` | `--priority-profile default --strategy min` | Rapid prototyping, early iterations |

**Configuration Persistence** (Exp 72):
For consistent, repeatable quality checks, use configuration persistence:

```bash
# Save your quality loop configuration
speckit configs save my-production \
  --description "Production quality checks" \
  --criteria backend,security,performance \
  --strict \
  --gate-preset production

# Load and run the configuration
speckit configs load my-production

# List all available configurations
speckit configs list

# Get configuration recommendation
speckit configs recommend "I need to deploy my API to production"
```

Use `/speckit.configs` for complete configuration management including save, load, list, show, export, import, delete, and recommend commands.

**Report Output**:
Generate quality reports in multiple formats for different use cases:

| Flag | Value | Description | Use Case |
|------|-------|-------------|----------|
| `--html-output` | `<path>` | Path to save HTML report | Presentations, documentation, interactive viewing |
| `--markdown-output` | `<path>` | Path to save Markdown report | Git diffs, code reviews, issue trackers |
| `--json-output` | `<path>` | Path to save JSON report | CI/CD pipelines, automated processing, quality gates |
| `--export-reports` | `<formats>` | Comma-separated formats (Exp 104, 106) | Unified export interface |
| `--export-dir` | `<path>` | Output directory for exports (Exp 104) | Organized report storage |
| `--export-prefix` | `<name>` | Filename prefix (Exp 104) | Custom report naming |

**CSV Export** (Exp 104, 105):
The CSV format is ideal for data analysis and spreadsheet import. Enhanced for trend analysis and BI integration:

**Structure** (4 sections):
1. **Metadata Header**: Schema version, timestamp, run_id, artifact, criteria
2. **Run Metadata**: Configuration details (iterations, priority_profile, gate_status, benchmark_percentile)
3. **Category Scores**: Scores with weighted calculations per category
4. **Failed Rules Details**: Severity, messages, suggestions

**Features for BI Tools** (Exp 105):
- `run_id`: Unique identifier for each run (enables trend tracking)
- `timestamp`: ISO format timestamp for time-series analysis
- `gate_status`: PASSED/FAILED/NOT_EVALUATED for gate filtering
- `benchmark_percentile`: Percentile ranking for comparison
- Schema version for backwards compatibility

**BI Tool Integration**:
- Power BI: Import CSV, create visuals from run_id, timestamp, scores
- Tableau: Use timestamp for date dimension, run_id for granularity
- Excel/Sheets: Pivot tables by category, filter by gate_status

**Trend Analysis**:
```python
import pandas as pd
# Load multiple CSV exports
df = pd.concat([pd.read_csv(f"run_{i}.csv", skiprows=lambda x: x < 5 or x > 6)
                for i in range(1, 11)])
# Analyze score trends over time
df.plot(x='timestamp', y='score')
```

Example: `--export-reports csv --export-dir ./reports --export-prefix quality-check`
Generates: `./reports/quality-check.csv`

**Excel Export** (Exp 106):
The Excel format provides professional reports with conditional formatting and multiple sheets:

**Structure** (4 sheets):
1. **Metadata**: Run information (run_id, timestamp, artifact, criteria, gate status, benchmark data)
2. **Summary**: Key metrics overview (overall score, status, total rules, iterations)
3. **Category Scores**: Detailed breakdown with conditional formatting (color scale: red→yellow→green)
4. **Failed Rules Details**: Severity-coded failed rules with color indicators

**Features**:
- Conditional formatting on scores for quick visual assessment
- Professional styling with headers, borders, and colors
- Frozen header rows for easier navigation
- Auto-filter enabled for data analysis
- Severity color coding (red for fail, yellow for warning)
- Auto-adjusted column widths

**Requirements**:
- Requires `openpyxl`: `pip install openpyxl`
- Falls back gracefully if openpyxl not installed

Example: `--export-reports excel --export-dir ./reports --export-prefix quality-check`
Generates: `./reports/quality-check.xlsx`

**HTML Report** (`--html-output`):
- 📊 Score timeline with Chart.js visualization
- 📈 Metrics grid (iterations, phase, score, status)
- 🚨 Failed rules & warnings table grouped by category
- 🎨 Modern gradient design with responsive layout
- 📈 Category breakdown with doughnut chart
- 🎯 **Quality Distribution** (Exp 54):
  - **Severity pie chart**: Visual breakdown of issues by severity (critical, high, medium, low, info)
  - **Score distribution histogram**: Percentile visualization (min, p25, median, p75, p90, p95, max)

**Markdown Report** (`--markdown-output`):
- 📝 Clean text-based format
- 📋 Score timeline with ASCII progress bars
- 🚨 Failed rules & warnings in tables grouped by category
- ✅ Perfect for git diffs and code reviews
- 📈 Category breakdown with visual bars

**JSON Report** (`--json-output`):
- 🤖 Structured JSON format for programmatic processing
- 📊 Category breakdown with statistics
- 📈 Score timeline for trend analysis
- 🚨 Failed rules and warnings with categories
- ✅ Perfect for CI/CD integration and automated quality gates
- 🔍 Validated against JSON Schema (v1.0) for consistency
- 🎯 Supports category filtering with `--include-categories` / `--exclude-categories`

**JSON Schema Validation** (Exp 52):
- All JSON reports are validated against a published JSON Schema
- Schema version: 1.0 (https://speckit.dev/schemas/quality-report-v1.json)
- Validation is non-blocking (warnings only, won't break the loop)
- Use `get_schema()` from `specify_cli.quality.json_schema` to get the schema
- Use `validate_schema(report_data)` to validate any JSON report

**JSON Schema Export** (Exp 53):
Export the JSON schema to a file for distribution and IDE integration:
- `export_schema(output_path)` — Export schema to a file
- `get_schema_info()` — Get schema metadata and information
- `print_schema_info()` — Print schema information in human-readable format
- Standalone schema file: `schemas/quality-report-v1.json`

**Enhanced Distribution Statistics** (Exp 53):
JSON reports now include enhanced distribution statistics:
- **Severity breakdown**: Count of issues by severity (critical, high, medium, low, info)
- **Score distribution**: Statistical metrics (min, max, mean, median, p25, p75, p90, p95)
- Use for quality trend analysis and dashboards

**Advanced Quality Gate Policies** (Exp 55):
Quality gate policies provide advanced gate evaluation with:
- **Severity-based gates**: Maximum allowed issues per severity level
- **Category-based gates**: Minimum scores per category
- **Preset policies**: Pre-configured gates for different environments
- **Custom policies**: Project-specific gate rules via YAML config

**Gate Presets**:
```python
from specify_cli.quality import GatePolicyManager, GATE_PRESETS

# List available presets
presets = GatePolicyManager.list_presets()
# ['production', 'staging', 'development', 'ci', 'strict', 'lenient']

# Get a preset
production_gate = GatePolicyManager.get_preset('production')
print(f"{production_gate.name}: {production_gate.description}")
# production: Strict quality gate for production deployments
print(f"Overall threshold: {production_gate.overall_threshold}")
# Overall threshold: 0.95
print(f"Severity gates: {production_gate.severity_gate}")
# Severity gates: SeverityGate(critical_max=0, high_max=0, medium_max=2, low_max=5)
print(f"Category gates: {len(production_gate.category_gates)}")
# Category gates: 3 (security, correctness, performance)
```

**Custom Gate Policy Configuration** (`.speckit/gate-policies.yml`):
```yaml
gate_policies:
  my-production:
    description: "Custom production gate for my project"
    overall_threshold: 0.90
    severity_gate:
      critical_max: 0
      high_max: 1
      medium_max: 5
      low_max: 10
      info_max: 999
    category_gates:
      - category: security
        min_score: 0.95
        max_failed: 0
      - category: correctness
        min_score: 0.90
        max_failed: 2
      - category: performance
        min_score: 0.80
        max_failed: 3
    block_on_failure: true

  my-staging:
    description: "Relaxed staging gate"
    overall_threshold: 0.80
    severity_gate:
      critical_max: 0
      high_max: 3
      medium_max: 10
      low_max: 20
    category_gates:
      - category: security
        min_score: 0.85
        max_failed: 2
    block_on_failure: false
```

**Gate Evaluation Result**:
```json
{
  "gate_result": {
    "gate_result": "passed",
    "passed": true,
    "blocked": false,
    "policy_name": "production",
    "policy_description": "Strict quality gate for production deployments",
    "overall_threshold": 0.95,
    "overall_score": 0.96,
    "messages": [],
    "category_scores": {
      "security": {"score": 0.98, "passed": 49, "failed": 1, "total": 50},
      "correctness": {"score": 0.95, "passed": 38, "failed": 2, "total": 40}
    },
    "category_failed": {
      "security": 1,
      "correctness": 2
    },
    "severity_counts": {
      "critical": 0,
      "high": 1,
      "medium": 3,
      "low": 5,
      "info": 2
    }
  }
}
```

**Category Filtering** (Exp 52):
Filter JSON report by categories to focus on specific quality aspects:
- `--include-categories security,performance` — only security and performance issues
- `--exclude-categories documentation,code-quality` — ignore docs and code quality

This is useful for:
- CI/CD quality gates that only care about specific categories
- Generating focused reports for different teams
- Creating category-specific quality metrics

Examples:
- `/speckit.loop --criteria backend --strict --html-output report.html`: Strict backend check with HTML report
- `/speckit.loop --criteria frontend --lenient --markdown-output report.md`: Quick check with Markdown for PR
- `/speckit.loop --strict --html-output report.html --markdown-output report.md`: Both HTML and Markdown for full coverage
- `/speckit.loop --strict --json-output report.json`: JSON report for CI/CD integration
- `/speckit.loop --strict --html-output report.html --markdown-output report.md --json-output report.json`: All three formats for complete coverage
- `/speckit.loop --strict --json-output report.json --include-categories security,performance`: JSON report filtered to security and performance only
- `/speckit.loop --criteria backend --json-output report.json --exclude-categories documentation`: JSON report without documentation issues
- `/speckit.loop --suggest-goals`: Show goal suggestions before running loop
- `/speckit.loop --suggest-goals --apply-suggestion 1`: Show suggestions and apply top one
- `/speckit.loop --suggest-goals --max-suggestions 5 --apply-suggestion 2`: Show up to 5 suggestions, apply second
- `/speckit.loop --strict --suggest-goals --json-output report.json`: Strict mode with goal suggestions and JSON report
- `/speckit.loop --show-result-card`: Show result card after loop completes (Exp 102)
- `/speckit.loop --show-result-card --result-card-compact`: Compact result card (Exp 102)
- `/speckit.loop --show-result-card --result-card-theme dark`: Dark theme result card (Exp 102)

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
   # Priority profile: "web-app" — domain-based scoring for web applications
   # Cascade profile: "web-app+mobile-app" — merge multiple profiles
   # Cascade strategy: "max" — strictest requirements (uses highest multiplier per domain)
   # Shortcuts: --strict = strict mode, --lenient = lenient mode
   result = loop.run(
       artifact=artifact,
       task_alias=task_alias,
       criteria_name=criteria_name,  # e.g., "backend,live-test"
       max_iterations=max_iterations,
       threshold_a=threshold_a,
       threshold_b=threshold_b,
       priority_profile=priority_profile,  # e.g., "web-app+mobile-app"
       cascade_strategy=cascade_strategy,  # e.g., "max", "avg", "min", "wgt"
       strict_mode=strict_mode,  # bool from --strict flag
       lenient_mode=lenient_mode,  # bool from --lenient flag
       html_output=html_output,  # path from --html-output flag
       markdown_output=markdown_output,  # path from --markdown-output flag
       json_output=json_output,  # path from --json-output flag (Exp 51)
       llm_client=current_llm,
       show_result_card=show_result_card,  # bool from --show-result-card flag (Exp 102)
       result_card_compact=result_card_compact,  # bool from --result-card-compact flag (Exp 102)
       result_card_theme=result_card_theme,  # string from --result-card-theme flag (Exp 102)
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

Reports Generated:
- HTML: {html_report_path or "None (use --html-output to generate)"}
- Markdown: {markdown_report_path or "None (use --markdown-output to generate)"}
- JSON: {json_report_path or "None (use --json-output to generate)"}

Next Steps:
- Run `/speckit.loop` with --max-iterations {n+2} to continue
- OR manually fix remaining issues
- Run `/speckit.goals suggest` to get intelligent goal recommendations
- Run `/speckit.loop --suggest-goals` to show goal suggestions before running loop
- Run `/speckit.loop --suggest-goals --apply-suggestion 1` to apply top suggestion
- Run `/speckit.profiles list` to see available priority profiles
- Run `/speckit.profiles cascade <profile1+profile2>` to see cascade merge details
- Run `/speckit.profiles recommend "<description>"` for profile recommendation
- Use `--strategy max` for stricter requirements or `--strategy min` for faster iteration
- Use `--html-output report.html` to generate an interactive HTML report
- Use `--markdown-output report.md` to generate a Markdown report for code reviews
- Use `--json-output report.json` to generate a JSON report for CI/CD integration
```

## CI/CD Integration Examples (Exp 52)

The JSON report with schema validation is ideal for CI/CD pipelines:

### Quality Gate with Preset Policy (Exp 55)

```yaml
name: Quality Gate (Production)

on: [pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Loop with Production Gate
        run: |
          pip install speckit
          speckit loop --gate-preset production --json-output quality-report.json
      - name: Check Quality Gate
        run: |
          # Check if gate passed
          GATE_RESULT=$(jq -r '.gate_result.gate_result // "unknown"' quality-report.json)
          BLOCKED=$(jq -r '.gate_result.blocked // false' quality-report.json)
          SCORE=$(jq -r '.gate_result.overall_score // 0' quality-report.json)
          THRESHOLD=$(jq -r '.gate_result.overall_threshold // 0' quality-report.json)

          echo "Gate Result: $GATE_RESULT"
          echo "Score: $SCORE (threshold: $THRESHOLD)"

          if [ "$BLOCKED" = "true" ]; then
            echo "❌ Quality gate blocked!"
            echo "Messages:"
            jq -r '.gate_result.messages[]' quality-report.json | sed 's/^/  - /'
            exit 1
          fi
          echo "✅ Quality gate passed!"
      - name: Upload Quality Report
        uses: actions/upload-artifact@v3
        with:
          name: quality-report
          path: quality-report.json
```

### Quality Gate with Auto-Recommendation (Exp 60)

```yaml
name: Quality Gate (Auto-Recommended)

on: [pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Loop with Auto-Recommended Gate
        run: |
          pip install speckit
          speckit loop --gate-policy-auto --json-output quality-report.json
      - name: Display Gate Recommendation
        run: |
          # Show which policy was recommended
          POLICY=$(jq -r '.gate_result.recommendation.policy_name // "unknown"' quality-report.json)
          CONFIDENCE=$(jq -r '.gate_result.recommendation.confidence // 0' quality-report.json)
          echo "Recommended Policy: $POLICY (confidence: $CONFIDENCE%)"

          # Show reasons
          echo "Reasons:"
          jq -r '.gate_result.recommendation.reasons[]? // empty' quality-report.json | sed 's/^/  - /'
      - name: Check Quality Gate
        run: |
          # Check if gate passed
          GATE_RESULT=$(jq -r '.gate_result.gate_result // "unknown"' quality-report.json)
          BLOCKED=$(jq -r '.gate_result.blocked // false' quality-report.json)

          if [ "$BLOCKED" = "true" ]; then
            echo "❌ Quality gate blocked!"
            jq -r '.gate_result.messages[]' quality-report.json | sed 's/^/  - /'
            exit 1
          fi
          echo "✅ Quality gate passed!"
      - name: Upload Quality Report
        uses: actions/upload-artifact@v3
        with:
          name: quality-report
          path: quality-report.json
```

### Environment-Aware Quality Gate (Exp 60)

```yaml
# Automatically adjust gate based on branch/environment
name: Quality Gate (Environment-Aware)

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Loop with Auto Gate
        run: |
          pip install speckit
          # Auto-recommends policy based on:
          # - Branch type (main -> production, develop -> staging)
          # - CI environment (GitHub Actions)
          # - Project type (auto-detected)
          speckit loop --gate-policy-auto --json-output quality.json
      - name: Check Gate
        run: |
          PASSED=$(jq -r '.gate_result.passed // false' quality.json)
          POLICY=$(jq -r '.gate_result.recommendation.policy_name // "default"' quality.json)
          echo "Gate Policy: $POLICY"

          if [ "$PASSED" != "true" ]; then
            echo "❌ Quality gate failed with policy: $POLICY"
            exit 1
          fi
          echo "✅ Quality gate passed!"
```

### Quality Gate with Severity Limits (Exp 55)

```yaml
# Block PR if critical or too many high-severity issues
- name: Severity Quality Gate
  run: |
    speckit loop --gate-preset production --json-output quality.json

    CRITICAL=$(jq '.gate_result.severity_counts.critical // 0' quality.json)
    HIGH=$(jq '.gate_result.severity_counts.high // 0' quality.json)

    if [ "$CRITICAL" -gt 0 ]; then
      echo "❌ Critical issues found: $CRITICAL"
      exit 1
    fi

    if [ "$HIGH" -gt 2 ]; then
      echo "❌ Too many high-severity issues: $HIGH (max: 2)"
      exit 1
    fi

    echo "✅ Severity gate passed!"
```

### Category-Specific Quality Gate (Exp 55)

```yaml
# Check specific categories meet their thresholds
- name: Category Quality Gate
  run: |
    speckit loop --gate-preset ci --json-output quality.json

    # Check security category score
    SECURITY_SCORE=$(jq '.gate_result.category_scores.security.score // 1.0' quality.json)
    SECURITY_FAILED=$(jq '.gate_result.category_failed.security // 0' quality.json)

    echo "Security score: $SECURITY_SCORE"
    echo "Security failed: $SECURITY_FAILED"

    if (( $(echo "$SECURITY_SCORE < 0.95" | bc -l) )); then
      echo "❌ Security score below 0.95 threshold"
      exit 1
    fi

    if [ "$SECURITY_FAILED" -gt 0 ]; then
      echo "❌ Security has $SECURITY_FAILED failed rules (max: 0)"
      exit 1
    fi

    echo "✅ Category gate passed!"
```

### Multi-Environment Quality Gates (Exp 55)

```yaml
# Different gates for different environments
- name: Quality Gate (Environment-Aware)
  run: |
    ENV=${{ github.event_name == 'pull_request' && 'staging' || 'production' }}

    echo "Running quality gate for: $ENV"

    speckit loop --gate-preset $ENV --json-output quality.json

    GATE_PASSED=$(jq -r '.gate_result.passed // false' quality.json)

    if [ "$GATE_PASSED" != "true" ]; then
      echo "❌ Quality gate failed for $ENV"
      jq -r '.gate_result.messages[]' quality.json | sed 's/^/  /'
      exit 1
    fi

    echo "✅ Quality gate passed for $ENV!"
```

### CI/CD Integration Examples (Exp 52)

### GitHub Actions Example

```yaml
name: Quality Gate

on: [pull_request]

jobs:
  quality-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Loop
        run: |
          pip install speckit
          speckit loop --json-output quality-report.json
      - name: Check Quality Gate
        run: |
          # Parse JSON and check if quality gate passed
          SCORE=$(jq -r '.summary.score' quality-report.json)
          PASSED=$(jq -r '.summary.passed' quality-report.json)

          echo "Quality Score: $SCORE"
          echo "Passed: $PASSED"

          if [ "$PASSED" != "true" ]; then
            echo "❌ Quality gate failed!"
            exit 1
          fi
          echo "✅ Quality gate passed!"
      - name: Upload Quality Report
        uses: actions/upload-artifact@v3
        with:
          name: quality-report
          path: quality-report.json
```

### Security-Only Quality Gate

```yaml
# Only check security issues in CI/CD
- name: Security Quality Gate
  run: |
    speckit loop --json-output security-report.json --include-categories security
    SECURITY_ISSUES=$(jq '.category_breakdown.categories[] | select(.name=="security") | .failed' security-report.json)

    if [ "$SECURITY_ISSUES" -gt 0 ]; then
      echo "❌ Security issues found: $SECURITY_ISSUES"
      exit 1
    fi
```

### Performance Quality Gate with Threshold

```yaml
# Performance quality gate with custom threshold
- name: Performance Quality Gate
  run: |
    speckit loop --json-output perf-report.json --include-categories performance
    PERF_SCORE=$(jq '.category_breakdown.categories[] | select(.name=="performance") | .score' perf-report.json)

    # Require 0.8+ score for performance category
    if (( $(echo "$PERF_SCORE < 0.8" | bc -l) )); then
      echo "❌ Performance score too low: $PERF_SCORE"
      exit 1
    fi
```

### Category-Specific Quality Gates

```yaml
# Different quality gates for different categories
- name: Multi-Category Quality Gates
  run: |
    speckit loop --json-output quality.json

    # Security must be 100% (no failed rules)
    SECURITY_FAILED=$(jq '.category_breakdown.categories[]? | select(.name=="security") | .failed // 0' quality.json)
    if [ "$SECURITY_FAILED" -gt 0 ]; then
      echo "❌ Security gate failed: $SECURITY_FAILED issues"
      exit 1
    fi

    # Performance must have score >= 0.8
    PERF_SCORE=$(jq '.summary.score' quality.json)
    if (( $(echo "$PERF_SCORE < 0.8" | bc -l) )); then
      echo "⚠️ Performance below threshold: $PERF_SCORE"
      # Don't fail, just warn
    fi

    echo "✅ Quality gates passed!"
```

### Exclude Documentation from CI

```yaml
# Ignore documentation issues in automated CI checks
- name: Quality Gate (No Docs)
  run: |
    speckit loop --json-output quality.json --exclude-categories documentation
    PASSED=$(jq -r '.summary.passed' quality.json)

    if [ "$PASSED" != "true" ]; then
      echo "❌ Quality gate failed (excluding docs)"
      exit 1
    fi
```

### Export JSON Schema for CI/CD Validation

```yaml
# Export and validate JSON schema in CI/CD
- name: Setup Quality Schema
  run: |
    # Export schema for validation
    python -c "from specify_cli.quality import export_schema; export_schema('schemas/quality-report-v1.json')"

    # Validate reports against schema
    pip install jsonschema
    python -c "
    import json
    from jsonschema import validate, RefResolver
    schema = json.load(open('schemas/quality-report-v1.json'))
    report = json.load(open('quality-report.json'))
    validate(instance=report, schema=schema)
    print('✅ Report validated successfully')
    "
```

### Enhanced Distribution Statistics (Exp 53)

```yaml
# Use distribution statistics for quality dashboards
- name: Quality Metrics Dashboard
  run: |
    speckit loop --json-output quality.json

    # Extract distribution statistics
    CRITICAL=$(jq '.distribution.severity.critical // 0' quality.json)
    HIGH=$(jq '.distribution.severity.high // 0' quality.json)
    MEDIAN=$(jq '.distribution.score_distribution.median // 0' quality.json)
    P95=$(jq '.distribution.score_distribution.p95 // 0' quality.json)

    echo "📊 Quality Distribution:"
    echo "   Critical: $CRITICAL"
    echo "   High: $HIGH"
    echo "   Median Score: $MEDIAN"
    echo "   P95 Score: $P95"

    # Quality gate based on P95 score
    if (( $(echo "$P95 < 0.85" | bc -l) )); then
      echo "⚠️ P95 score below 0.85 threshold"
    fi
```


## Historical Trend Aggregation (Exp 107-108)

Generate comprehensive Excel reports with trend charts and integrated anomaly detection from quality history:

**Features**:
- 📊 **Embedded line charts** for score trends over time
- 📈 **Category-level trend analysis** with direction indicators
- 📋 **Multi-sheet Excel workbook** with professional formatting
- 📉 **Statistics summary** across all runs
- 🔍 **Run details** with full metadata
- ⚠️ **Integrated anomaly detection** (Exp 108) - Highlights issues automatically

**Usage**:
```python
from specify_cli.quality import export_trend_excel, aggregate_history_report

# Generate trend Excel report with anomaly detection
excel_bytes = export_trend_excel(
    task_alias="my-feature",  # Optional: filter by task
    limit=50,                 # Optional: max runs to include
    output_path="./reports/quality_trends.xlsx",
    detect_anomalies=True     # Default: include anomaly detection
)

# Aggregate history data for custom analysis
report = aggregate_history_report(
    task_alias="my-feature",
    limit=50,
    detect_anomalies=True  # Include anomaly summary
)

print(f"Overall trend: {report.overall_trend}")  # improving, declining, stable
print(f"Total runs: {report.total_runs}")

# Anomaly summary (if enabled)
if report.anomaly_summary:
    print(f"Anomalies detected: {report.anomaly_summary.total_anomalies}")
    print(f"Critical: {report.anomaly_summary.critical_count}")
    print(f"High: {report.anomaly_summary.high_count}")
    
# Category trends
for cat, trend in report.category_trends.items():
    print(f"{cat}: {trend.trend_direction} (avg: {trend.avg_score:.3f})")
```

**Excel Structure** (5 sheets):
1. **Overview**: Statistics summary, trend direction, total runs, **anomaly summary**
2. **Score History**: Timeline table with embedded line chart
3. **Anomalies** (NEW): Severity breakdown, anomaly types, detailed table with recommendations
4. **Category Trends**: Per-category performance with trend indicators
5. **Run Details**: Complete metadata for all runs

**Anomaly Detection** (Exp 108):
- Automatically detects regressions, outliers, pass rate drops, stagnation
- Color-coded severity in Excel: 🔴 Critical, 🟠 High, 🟡 Medium
- Detailed anomalies table with actionable recommendations
- Graceful fallback if anomaly detection unavailable

**Requirements**:
- Requires quality history data (`.speckit/quality-history/`)
- Requires `openpyxl`: `pip install openpyxl`
- Minimum 2 runs required for trend analysis
- Minimum 3 runs required for anomaly detection

