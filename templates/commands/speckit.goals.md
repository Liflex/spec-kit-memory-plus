---
description: Manage quality goals for your project
long_description: |
  Define, track, and achieve quality goals for your project.

  The Quality Goals System allows you to:
  - Define target scores, pass rates, category targets, and more
  - Track progress towards goals over time
  - Get actionable recommendations based on goal status
  - Integrate goals with your quality loop workflow
  - Use pre-configured presets for common scenarios

  **Goal Types:**
  - `target-score`: Achieve minimum average score
  - `pass-rate`: Achieve minimum pass rate
  - `category-target`: Achieve minimum score in specific category
  - `streak`: Maintain consecutive passed runs
  - `improvement`: Improve score by percentage
  - `stability`: Keep score variance below threshold

  **Goal Presets:**
  - `production-ready`: High quality standards (0.9 score, 95% pass rate, 85% stability)
  - `ci-gate`: CI/CD quality gates (80% pass rate, 0.75 score, 5-streak)
  - `security-focused`: Security priority (0.95 security score, 90% stability)
  - `quick-start`: Easy initial goals (0.75 score, 70% pass rate)
  - `stability`: Consistency focus (90% stability, 10-streak, 0.8 score)
  - `comprehensive`: Complete coverage (6 goals across all dimensions)

  **Examples:**

  Apply a preset:
  ```
  /speckit.goals preset apply production-ready
  ```

  List available presets:
  ```
  /speckit.goals preset list
  ```

  Get recommended preset:
  ```
  /speckit.goals preset recommend --project-type production --strictness strict
  ```

  Create a custom target score goal:
  ```
  /speckit.goals create target-score --name "Production Ready" --target 0.9 --window 10
  ```

  List all goals:
  ```
  /speckit.goals list
  ```

  Show goal progress:
  ```
  /speckit.goals progress
  /speckit.goals progress --goal-id <goal-id>
  ```

  Update a goal:
  ```
  /speckit.goals update <goal-id> --target 0.95
  ```

  Delete a goal:
  ```
  /speckit.goals delete <goal-id>
  ```

  Get goals summary:
  ```
  /speckit.goals summary
  ```

  Export goals as JSON:
  ```
  /speckit.goals export --json
  ```

  Check goals after quality loop:
  ```
  /speckit.loop --check-goals
  ```

  Get smart goal suggestions:
  ```
  /speckit.goals suggest
  ```

  Apply a suggestion:
  ```
  /speckit.goals suggest apply 1
  ```
---

# Quality Goals Management

The quality goals system helps you define and track quality targets for your project.

## Quick Start with Presets

The fastest way to get started is to apply a pre-configured preset:

```bash
# Apply production-ready goals
/speckit.goals preset apply production-ready

# Apply CI gate goals
/speckit.goals preset apply ci-gate

# Apply security-focused goals
/speckit.goals preset apply security-focused
```

## Subcommands

### `preset apply` - Apply a goal preset

```bash
/speckit.goals preset apply <preset-name>
```

**Presets:**
- `production-ready` — High quality standards for production
- `ci-gate` — Quality gates for CI/CD pipelines
- `security-focused` — Security-critical project goals
- `quick-start` — Easy goals for getting started
- `stability` — Focus on score consistency
- `comprehensive` — Complete quality coverage

**Options:**
- `--dry-run`: Show what goals would be created without creating them

### `preset list` - List available presets

```bash
/speckit.goals preset list [--json]
```

Shows all available presets with their goal configurations.

### `preset recommend` - Get preset recommendation

```bash
/speckit.goals preset recommend [options]
```

**Options:**
- `--project-type <type>`: Project type (general, security, ci, production)
- `--strictness <level>`: Quality strictness (strict, standard, relaxed)
- `--current-score <value>`: Current quality score (0-1)
- `--current-pass-rate <value>`: Current pass rate (0-100)

Recommends the best preset based on your project's current state and requirements.

### `category apply` - Apply category-specific goal template

```bash
/speckit.goals category apply <category-name>
```

**Categories:**
- `security` — Security quality goals (0.85 security score, 85% stability, 10-streak)
- `performance` — Performance quality goals (0.80 performance score, 80% stability, 10% improvement)
- `testing` — Testing quality goals (0.85 testing score, 80% stability, 7-streak)
- `documentation` — Documentation quality goals (0.80 docs score, 75% stability)
- `code_quality` — Code quality goals (0.85 score, 80% stability, 5% improvement)
- `infrastructure` — Infrastructure quality goals (0.80 score, 80% stability)
- `observability` — Observability quality goals (0.80 score, 75% stability)
- `reliability` — Reliability quality goals (0.85 score, 85% stability, 10-streak)
- `cicd` — CI/CD quality goals (0.85 score, 85% stability, 5-streak)
- `correctness` — Correctness quality goals (0.90 score, 90% stability)
- `accessibility` — Accessibility quality goals (0.85 score, 80% stability)
- `ux_quality` — UX quality goals (0.80 score, 75% stability)

**Options:**
- `--dry-run`: Show what goals would be created without creating them

### `category list` - List available category templates

```bash
/speckit.goals category list [--json]
```

Shows all available category templates with their goal configurations.

### `category info` - Get category template details

```bash
/speckit.goals category info <category-name>
```

Shows detailed information about a specific category template.

### `category recommend` - Get category template recommendation

```bash
/speckit.goals category recommend [options]
```

**Options:**
- `--project-type <type>`: Project type (general, security, performance, testing, etc.)
- `--focus-area <category>`: Specific category to focus on
- `--scores <json>`: Current category scores as JSON (e.g., '{"security": 0.6, "performance": 0.9}')

Recommends the best category template based on your project's current state and focus area.

### `suggest` - Generate smart goal suggestions

```bash
/speckit.goals suggest [options]
```

Generate intelligent, data-driven goal suggestions based on your quality history.

**Options:**
- `--task <alias>`: Analyze specific task (default: current/all)
- `--runs <n>`: Number of recent runs to analyze (default: 50)
- `--max <n>`: Maximum suggestions to generate (default: 10)
- `--no-presets`: Skip goal presets, show only individual suggestions
- `--json`: Export as JSON

**Output includes:**
- Suggested goals with confidence levels
- Rationale and supporting evidence for each suggestion
- Alternative targets (conservative/moderate/aggressive)
- Expected effort and achievability
- Goal presets for different scenarios
- Top recommendations

**How it works:**
The goal suggester analyzes your quality history to:
1. Calculate achievable targets based on recent performance
2. Identify weak categories that need improvement
3. Detect positive trends to build upon
4. Find areas with high improvement potential
5. Suggest stability goals to reduce volatility

**Example output:**
```
# Quality Goal Suggestions

**Generated:** 2026-03-13T10:30:00
**Suggestions:** 5

## Summary
Based on 25 quality runs with average score of 0.78 and 82% pass rate.
Identified 3 actionable optimization opportunities.

### Top Recommendations
1. Achieve Consistent Quality
2. Improve Security Quality
3. Reduce Quality Volatility

## Suggested Goals

### 1. Achieve Consistent Quality 🔒
**Type:** target-score
**Target:** 0.82
**Current:** 0.78
**Confidence:** high
**Effort:** medium

Maintain average score above 0.82

**Why:** Based on recent performance (avg: 0.78), this target is achievable with focused effort. Best score: 0.85

**Alternatives:**
  - conservative: 0.80
  - moderate: 0.82
  - aggressive: 0.85

**Evidence:**
  - Current average: 0.78
  - Standard deviation: 0.06
  - Best historical score: 0.85
```

### `suggest apply` - Apply a suggestion

```bash
/speckit.goals suggest apply <number>
```

Apply a specific suggestion from the suggestions list.

**Example:**
```bash
# Show suggestions
/speckit.goals suggest

# Apply the first suggestion
/speckit.goals suggest apply 1
```

This creates the actual goal based on the suggested parameters.

### `suggest wizard` - Interactive suggestion mode

```bash
/speckit.goals suggest wizard
```

Interactive mode for exploring and selecting goal suggestions.

**Features:**
- Browse suggestions with detailed explanations
- Preview alternative targets
- See supporting evidence
- Apply multiple suggestions at once
- Get guidance on goal combinations

**Workflow:**
1. Shows suggestions with confidence levels
2. You can drill down into each suggestion
3. Preview what applying would do
4. Select suggestions to apply
5. Confirm and create goals

### `create` - Create a new quality goal

```bash
/speckit.goals create <type> [options]
```

**Types:**
- `target-score` - Target average quality score
- `pass-rate` - Target pass rate percentage
- `category` - Target score for specific category
- `streak` - Target consecutive passed runs
- `improvement` - Target improvement percentage
- `stability` - Target score stability (0-100)

**Options:**
- `--name <name>` (required): Goal name
- `--target <value>` (required): Target value
- `--category <name>`: Category name (for category goals)
- `--window <size>`: Number of runs to consider (default: 10)
- `--threshold <value>`: Warning threshold (default: 75% of target)
- `--deadline <date>`: Optional deadline (ISO format)
- `--description <text>`: Goal description

### `list` - List all goals

```bash
/speckit.goals list [--json]
```

**Options:**
- `--json`: Export as JSON

### `progress` - Show goal progress

```bash
/speckit.goals progress [--goal-id <id>] [--json]
```

**Options:**
- `--goal-id <id>`: Specific goal to show (default: all)
- `--json`: Export as JSON

### `summary` - Show goals summary

```bash
/speckit.goals summary [--json]
```

Shows overall progress across all goals.

### `update` - Update a goal

```bash
/speckit.goals update <goal-id> [options]
```

**Options:**
- `--name <name>`: New name
- `--target <value>`: New target value
- `--window <size>`: New window size
- `--threshold <value>`: New warning threshold
- `--deadline <date>`: New deadline

### `delete` - Delete a goal

```bash
/speckit.goals delete <goal-id>
```

### `check` - Check goals after quality run

```bash
/speckit.goals check [--json]
```

Updates all goals based on latest quality history.

### `export` - Export goals

```bash
/speckit.goals export [--json] [--yaml]
```

**Options:**
- `--json`: Export as JSON (default)
- `--yaml`: Export as YAML
- `--output <file>`: Write to file instead of stdout

Exports all goals to a portable format for backup or sharing.

### `import` - Import goals

```bash
/speckit.goals import <file> [--merge]
```

**Options:**
- `--merge`: Merge with existing goals (default: replace all)

Imports goals from a previously exported file.

## Integration with Quality Loop

Goals are automatically checked after each quality run when using:

```bash
/speckit.loop --check-goals
```

This will:
1. Run the quality loop
2. Save results to history
3. Update all goal progress
4. Show goal status with recommendations

## Goal Status

Goals can have the following statuses:
- **Not Started**: No quality history yet
- **In Progress**: Active tracking towards goal
- **At Risk**: Below warning threshold
- **Achieved**: Target reached
- **Failed**: Deadline passed without achieving target

## Example Workflow

```bash
# Create production quality goal
/speckit.goals create target-score \
  --name "Production Ready" \
  --target 0.9 \
  --window 10 \
  --description "Average 0.9+ score over 10 runs"

# Create security-specific goal
/speckit.goals create category \
  --name "Security Excellence" \
  --category security \
  --target 0.95 \
  --window 15

# Run quality loop with goal checking
/speckit.loop backend --check-goals

# Check progress
/speckit.goals progress

# Get summary
/speckit.goals summary
```
