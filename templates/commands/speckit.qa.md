---
description: Unified quality assurance dashboard and command center
long_description: |
  The QA Dashboard provides a unified interface for all quality assurance features in Spec Kit.

  **Quick Overview:**
  - View quality metrics summary at a glance
  - Access all quality features from one place
  - Interactive mode for guided workflows
  - Direct access to quality commands

  **Quality Features Accessible:**
  - **Profiles** - Priority scoring profiles for domain-based quality
  - **Gates** - Quality gate policies for CI/CD
  - **Goals** - Quality goals and target tracking
  - **Insights** - Intelligent quality analytics
  - **Anomalies** - Statistical anomaly detection
  - **History** - Quality run history tracking
  - **Configs** - Loop configuration management
  - **Loop** - Quality loop execution

  **Dashboard Views:**
  - `overview` - Quick summary of quality status
  - `interactive` - Interactive menu for guided workflows
  - `check` - Quick quality check with recommendations
  - `compare` - Compare quality metrics across runs
  - `trends` - View quality trends over time

  **Examples:**

  Show quality overview:
  ```
  /speckit.qa overview
  ```

  Launch interactive dashboard:
  ```
  /speckit.qa interactive
  ```

  Quick quality check:
  ```
  /speckit.qa check
  ```

  Compare quality runs:
  ```
  /speckit.qa compare --runs 5
  ```
---

# Spec Kit QA Dashboard

Unified quality assurance command center for Spec Kit.

## Overview

The QA Dashboard provides a single entry point for all quality assurance features:

```bash
# Quick overview of quality status
/speckit.qa overview

# Interactive dashboard with guided workflows
/speckit.qa interactive

# Quick quality check with recommendations
/speckit.qa check

# Compare recent quality runs
/speckit.qa compare --runs 10

# View quality trends
/speckit.qa trends
```

## Quick Start

```bash
# 1. Get a quick overview of your quality status
/speckit.qa overview

# 2. Run a quick quality check
/speckit.qa check

# 3. Launch interactive dashboard for guided workflows
/speckit.qa interactive
```

## Subcommands

### `overview` - Quality Status Overview

```bash
/speckit.qa overview [--task <alias>]
```

Display a comprehensive overview of quality status.

**What it shows:**
- Current quality score and pass rate
- Active quality goals progress
- Recent anomalies (if any)
- Quality gate status
- Trend direction (improving/declining/stable)
- Top priority insights

**Example output:**
```
=== Spec Kit Quality Overview ===

Quality Score: 0.87 (↑ improving over 3 runs)
Pass Rate: 92% (184/200 rules)

Quality Goals: 3 active
  ✅ Security Score ≥ 0.90: 0.92 (ACHIEVED)
  ⚠️ Performance Score ≥ 0.85: 0.82 (AT-RISK)
  ❌ Testing Coverage ≥ 80%: 65% (FAILED)

Recent Anomalies: 2 detected
  🚨 Score drop on 2026-03-12 (-0.08)
  ⚠️ High iteration count (7 iterations)

Top Insights:
  - Focus on testing for +0.15 potential score gain
  - Performance optimization recommended

Next Steps:
  - /speckit.qa interactive for guided workflow
  - /speckit.goals suggest for goal recommendations
  - /speckit.loop --suggest-goals for smart goal suggestions
```

### `check` - Quick Quality Check

```bash
/speckit.qa check [--detailed] [--recommend]
```

Run a quick quality assessment with actionable recommendations.

**Options:**
- `--detailed`: Show detailed breakdown
- `--recommend`: Include specific recommendations

**What it does:**
1. Analyzes recent quality history
2. Checks goal progress
3. Detects anomalies
4. Generates insights
5. Provides prioritized recommendations

**Example output:**
```
=== Quick Quality Check ===

Assessment: GOOD with improvement opportunities

Current Status:
  Score: 0.87 (target: 0.90)
  Pass Rate: 92%
  Trend: Improving (+0.05 over last 5 runs)

Priority Actions:
  1. Fix testing coverage (65% → 80%)
     → /speckit.loop testing --suggest-goals

  2. Optimize performance rules
     → /speckit.qa overview --detailed

  3. Review security goals
     → /speckit.goals check

Recommendations:
  - Use --strict mode for production checks
  - Enable auto-update-goals for goal tracking
  - Run quality loop with insights: /speckit.loop --insights
```

### `interactive` - Interactive Dashboard

```bash
/speckit.qa interactive
```

Launch an interactive dashboard with guided workflows.

**Interactive Menu:**
```
=== Spec Kit QA Dashboard ===

Current Quality Score: 0.87 (↑ improving)

Select an action:
  1. 📊 View Quality Overview
  2. 🎯 Manage Quality Goals
  3. 🔧 Configure Priority Profiles
  4. 🚪 Set Quality Gates
  5. 📈 View Quality Insights
  6. 🔍 Check Anomalies
  7. 📜 View History
  8. ⚙️ Manage Configurations
  9. 🔄 Run Quality Loop
 10. 📋 Quick Quality Check
  0. Exit

Enter choice (1-10, 0 to exit):
```

**Menu Actions:**
1. **View Quality Overview** - Show detailed quality status
2. **Manage Quality Goals** - Goal management wizard
3. **Configure Priority Profiles** - Profile configuration
4. **Set Quality Gates** - Gate policy configuration
5. **View Quality Insights** - Insights and recommendations
6. **Check Anomalies** - Anomaly detection status
7. **View History** - Quality run history
8. **Manage Configurations** - Loop config management
9. **Run Quality Loop** - Execute quality loop
10. **Quick Quality Check** - Quick assessment

### `compare` - Compare Quality Runs

```bash
/speckit.qa compare [--runs <n>] [--task <alias>]
```

Compare quality metrics across recent runs.

**Options:**
- `--runs <n>`: Number of recent runs to compare (default: 5)
- `--task <alias>`: Specific task to analyze

**What it shows:**
- Score changes between runs
- Pass rate trends
- Category breakdown changes
- Iteration count patterns
- Anomaly indicators

**Example output:**
```
=== Quality Comparison (Last 5 Runs) ===

Run | Score | Change | Pass Rate | Iterations | Anomalies
----|-------|--------|-----------|------------|----------
R1  | 0.82  | -      | 85%       | 4          | 0
R2  | 0.84  | +0.02  | 87%       | 3          | 0
R3  | 0.78  | -0.06  | 82%       | 5          | 1 (drop)
R4  | 0.85  | +0.07  | 89%       | 4          | 0
R5  | 0.87  | +0.02  | 92%       | 3          | 0

Trend: Improving (average +0.03 per run)
Best Run: R5 (current)
Anomaly Detected: R3 had significant score drop

Category Breakdown (R4 → R5):
  Security: 0.90 → 0.92 (+0.02)
  Performance: 0.80 → 0.82 (+0.02)
  Testing: 0.75 → 0.78 (+0.03)
```

### `trends` - Quality Trends

```bash
/speckit.qa trends [--task <alias>] [--forecast]
```

View quality trends over time with optional forecasts.

**Options:**
- `--task <alias>`: Specific task to analyze
- `--forecast`: Show predictive forecasts

**What it shows:**
- Score trend line (direction and strength)
- Moving averages
- Predictive forecasts
- Seasonality patterns
- Trend confidence levels

## Integration with Quality Features

### Quality Goals Integration

```bash
# Check goal progress from dashboard
/speckit.qa overview

# Set goals interactively
/speckit.qa interactive
→ Select "Manage Quality Goals"

# Get goal recommendations
/speckit.goals suggest
```

### Quality Gates Integration

```bash
# Check gate status
/speckit.qa overview

# Configure gates
/speckit.gates recommend

# View gate history
/speckit.qa compare
```

### Quality Loop Integration

```bash
# Quick check before loop
/speckit.qa check

# Run loop with dashboard insights
/speckit.loop --suggest-goals

# Compare results after loop
/speckit.qa compare --runs 3
```

## Dashboard Workflows

### Workflow 1: New Project Setup

```bash
# 1. Get overview
/speckit.qa overview

# 2. Configure profile
/speckit.qa interactive
→ Select "Configure Priority Profiles"

# 3. Set initial goals
/speckit.goals suggest

# 4. Run first quality check
/speckit.qa check
```

### Workflow 2: Pre-Deployment Check

```bash
# 1. Run quick check
/speckit.qa check --recommend

# 2. Review gate status
/speckit.qa overview

# 3. Run strict quality loop
/speckit.loop --strict --gate-preset production

# 4. Verify results
/speckit.qa compare
```

### Workflow 3: Quality Improvement

```bash
# 1. Get insights
/speckit.qa overview

# 2. View trends
/speckit.qa trends --forecast

# 3. Get recommendations
/speckit.qa check --recommend

# 4. Apply improvements
/speckit.loop --suggest-goals --apply-suggestion 1
```

### Workflow 4: Anomaly Investigation

```bash
# 1. Check for anomalies
/speckit.qa overview

# 2. View anomaly details
/speckit.anomalies list

# 3. Compare runs
/speckit.qa compare --runs 10

# 4. Analyze root cause
/speckit.insights patterns
```

## Output Formats

### Text Output (default)

Clean, readable text output for terminal viewing.

### JSON Output

```bash
/speckit.qa overview --json
```

Structured JSON for programmatic access:

```json
{
  "quality_score": 0.87,
  "pass_rate": 0.92,
  "trend": "improving",
  "goals": {
    "active": 3,
    "achieved": 1,
    "at_risk": 1,
    "failed": 1
  },
  "anomalies": {
    "detected": 2,
    "critical": 0,
    "high": 2
  },
  "recommendations": [
    {
      "priority": "high",
      "action": "Focus on testing",
      "command": "/speckit.loop testing --suggest-goals"
    }
  ]
}
```

## Dashboard Configuration

The dashboard uses quality history data stored in `.speckit/quality-history/`.

**Location:** `.speckit/quality-history/<task-alias>/`

**Files:**
- `history.jsonl` - Quality run records
- `anomalies.json` - Anomaly detection results
- `goals.json` - Quality goals configuration
- `insights.json` - Latest insights report

## Tips

- **Start with overview**: Use `/speckit.qa overview` to get quick status
- **Use interactive mode**: Launch `/speckit.qa interactive` for guided workflows
- **Check before loops**: Run `/speckit.qa check` before quality loops
- **Compare regularly**: Use `/speckit.qa compare` to track progress
- **Monitor trends**: Use `/speckit.qa trends --forecast` for predictive insights

## Python API

```python
from specify_cli.quality import (
    get_quality_overview,
    run_quality_check,
    compare_quality_runs,
    get_quality_trends
)

# Get quality overview
overview = get_quality_overview(task_alias="backend")

# Run quality check
check = run_quality_check(detailed=True, recommend=True)

# Compare runs
comparison = compare_quality_runs(n_runs=5)

# Get trends
trends = get_quality_trends(forecast=True)
```

## Related Commands

- `/speckit.loop` - Run quality loop
- `/speckit.goals` - Manage quality goals
- `/speckit.gates` - Configure quality gates
- `/speckit.profiles` - Manage priority profiles
- `/speckit.insights` - View quality insights
- `/speckit.anomalies` - Check anomalies
- `/speckit.history` - View quality history
- `/speckit.configs` - Manage configurations
