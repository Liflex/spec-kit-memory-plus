# Quality History Commands

Track and analyze quality runs over time to identify trends, measure improvement, and make data-driven decisions.

## Overview

Quality history tracking automatically saves results from every quality loop run and provides powerful analysis tools:

- **Statistics**: Pass rates, average scores, iteration counts
- **Trends**: Improving, declining, or stable quality over time
- **Comparisons**: Compare any two runs side-by-side
- **Category Trends**: Track specific categories (security, performance, etc.)

## Commands

### `speckit history`

View quality history summary with statistics and recent runs.

```bash
speckit history [options]
```

**Options:**
- `--task <alias>` - Filter by task alias (e.g., `--task spec.md`)
- `--limit <n>` - Number of recent runs to show (default: 10)
- `--format <text|json>` - Output format (default: text)
- `--stats` - Show detailed statistics
- `--trends` - Show trend analysis
- `--runs` - Show recent runs list

**Examples:**

```bash
# Show recent runs
speckit history

# Show statistics for a specific task
speckit history --task spec.md --stats

# Show trends analysis
speckit history --trends

# Export history as JSON for CI/CD
speckit history --format json --limit 50 > history.json
```

**Output (text format):**

```
## Quality History

Total Runs: 25 | Passed: 20 | Failed: 5
Pass Rate: 80.0%

### Score Statistics
Average: 0.856 | Min: 0.742 | Max: 0.923
Average Iterations: 2.4

Most Failed Category: security
Most Used Profile: web-app

### Recent Runs (last 5)
1. [2026-03-13 10:30] spec.md - Score: 0.912 ✓ (2 iterations)
2. [2026-03-13 09:15] spec.md - Score: 0.885 ✓ (3 iterations)
3. [2026-03-12 16:45] plan.md - Score: 0.723 ✗ (4 iterations)
...
```

**Output (JSON format):**

```json
{
  "statistics": {
    "total_runs": 25,
    "passed_runs": 20,
    "pass_rate": 0.8,
    "avg_score": 0.856,
    "avg_iterations": 2.4
  },
  "trends": {
    "direction": "improving",
    "score_change": 0.056,
    "trend_description": "Moderate improvement (+5.6%)"
  },
  "recent_runs": [...]
}
```

### `speckit history compare`

Compare two quality runs to see what changed.

```bash
speckit history compare <run_id1> <run_id2> [options]
```

**Options:**
- `--format <text|json>` - Output format (default: text)

**Examples:**

```bash
# Compare two runs by ID
speckit history compare spec.md-20260313-103000 spec.md-20260313-091500

# Compare with JSON output
speckit history compare <run1> <run2> --format json
```

**Output:**

```
## Run Comparison

Run 1: spec.md-20260313-103000 (Score: 0.912)
Run 2: spec.md-20260313-091500 (Score: 0.885)

### Changes
Score: +0.027 (+3.1%) ✓ Improved
Iterations: -1 (fewer is better) ✓ Improved

### Category Changes
- security: +0.056 (improved)
- performance: +0.012 (improved)
- testing: -0.008 (declined)

### Gate Comparison
Both runs passed the quality gate
```

### `speckit history clear`

Clear quality history (use with caution).

```bash
speckit history clear [options]
```

**Options:**
- `--task <alias>` - Clear only history for this task
- `--all` - Clear all history (requires confirmation)

**Examples:**

```bash
# Clear history for a specific task
speckit history clear --task spec.md

# Clear all history (interactive confirmation)
speckit history clear --all
```

### `speckit history detect-anomalies`

Detect anomalies in quality history using statistical analysis.

```bash
speckit history detect-anomalies [options]
```

**Options:**
- `--task <alias>` - Filter by task alias
- `--limit <n>` - Number of recent runs to analyze (default: 50)
- `--format <text|json>` - Output format (default: text)
- `--severity <all|critical|high>` - Minimum severity to show (default: all)

**Examples:**

```bash
# Detect anomalies in all runs
speckit history detect-anomalies

# Show only critical anomalies as JSON
speckit history detect-anomalies --severity critical --format json

# Check specific task for anomalies
speckit history detect-anomalies --task spec.md --limit 100
```

**Anomaly Types:**

- **Regression**: Significant score drop compared to rolling baseline
- **Outlier**: Statistical outlier using z-score analysis
- **Pass Rate Drop**: Declining pass rate over time
- **Stagnation**: Quality scores have plateaued
- **Category Drop**: Specific category score decline
- **Iteration Spike**: Sudden increase in iteration counts

**Output (text format):**

```
## Quality Anomaly Report

**Analyzed:** 50 runs
**Detected:** 3 anomalies
**Timestamp:** 2026-03-13T10:30:00

**Severity Breakdown:**
  - CRITICAL: 1
  - HIGH: 2

### Detected Anomalies

🚨 **Quality Regression: 15.2% drop** [CRITICAL]
   Score dropped from 0.856 (baseline) to 0.726 (current)
   Run ID: `spec.md-20260313-103000`
   💡 Critical quality regression detected! Score dropped by 15.2%. Investigate immediately - this may indicate a serious code issue.

⚠️ **Pass Rate Decline: 12.5%** [HIGH]
   Pass rate dropped from 85.0% to 72.5% over time
   💡 Pass rate is declining. Review recent changes and consider if quality standards are too strict or if quality is actually degrading.

⚡ **Iteration Spike: 6 iterations** [MEDIUM]
   This run required 6 iterations, 2.4x the average (2.5)
   Run ID: `spec.md-20260312-164500`
   💡 High iteration count may indicate quality issues or inefficient refinement. Consider adjusting quality thresholds.
```

**Use in CI/CD:**

```yaml
# .github/workflows/quality-check.yml
- name: Check for Anomalies
  run: |
    result=$(speckit history detect-anomalies --format json --severity critical)
    if echo "$result" | grep -q '"critical": [1-9]'; then
      echo "Critical anomalies detected!"
      exit 1
    fi
```

### `speckit history dashboard`

Generate an interactive HTML dashboard for visual quality history analysis.

```bash
speckit history dashboard [options]
```

**Options:**
- `--task <alias>` - Filter by task alias
- `--output <path>` - Output file path (default: `.speckit/quality-history/dashboard.html`)
- `--limit <n>` - Maximum number of runs to include (default: 50)
- `--no-trends` - Skip trend analysis
- `--open` - Open dashboard in browser after generation

**Examples:**

```bash
# Generate dashboard for all runs
speckit history dashboard

# Generate dashboard for specific task
speckit history dashboard --task spec.md --output my-dashboard.html

# Generate with 100 runs and auto-open
speckit history dashboard --limit 100 --open
```

**Dashboard Features:**

The HTML dashboard includes:

1. **Anomaly Alerts** (Exp 68)
   - Automatic anomaly detection on dashboard load
   - Severity-based visual indicators
   - Actionable recommendations for each anomaly
   - Quick overview of anomaly counts by severity

2. **Statistics Overview**
   - Total runs, pass rate, average score
   - Most failed categories, most used profiles
   - Score range and average iterations

3. **Quality Trends**
   - Direction indicator (improving/declining/stable)
   - Score change with percentage
   - Category-level trends

4. **Visual Charts**
   - Quality Score Timeline (line chart)
   - Pass Rate Evolution (rolling average)
   - Category Score Trends (multi-line)
   - Iteration Count History (bar chart)
   - Run Duration Over Time (bar chart)
   - Severity Distribution (doughnut chart)

5. **Interactive Filters**
   - Filter by task, profile, status
   - Adjust run limit
   - Reset filters button

6. **Run History Table**
   - Run ID, task, score, status
   - Iterations, phase, profile
   - Failed categories, duration, timestamp

**Dashboard Location:**

By default, the dashboard is saved to:
```
.speckit/quality-history/dashboard.html
```

Open the file in any modern web browser to view the interactive dashboard.

## Python API

You can also use the history tracking API directly:

```python
from specify_cli.quality.quality_history import (
    QualityHistoryManager,
    get_quality_statistics,
    get_quality_trends,
    format_statistics_report,
    format_trends_report,
    format_history_json,
)
from specify_cli.quality.history_dashboard import generate_history_dashboard
from specify_cli.quality.quality_anomaly import (
    detect_anomalies,
    format_anomaly_report,
    format_anomalies_json,
    get_anomaly_summary,
)

# Get statistics
stats = get_quality_statistics(task_alias="spec.md")
print(format_statistics_report(stats))

# Get trends
trends = get_quality_trends(task_alias="spec.md", min_runs=3)
if trends:
    print(format_trends_report(trends))

# Detect anomalies
manager = QualityHistoryManager()
runs = manager.load_history(task_alias="spec.md", limit=50)
if len(runs) >= 3:
    anomaly_report = detect_anomalies(runs, task_alias="spec.md")
    if anomaly_report.anomalies_detected > 0:
        print(format_anomaly_report(anomaly_report))
        # Get one-line summary
        print(get_anomaly_summary(anomaly_report))

# Get recent runs
manager = QualityHistoryManager()
recent = manager.get_recent_runs(limit=10)
for run in recent:
    print(f"{run.timestamp}: {run.score:.3f}")

# Compare runs
comparison = manager.compare_runs(run_id1, run_id2)
if comparison:
    print(f"Score change: {comparison.score_delta:+.3f}")

# Generate HTML dashboard
html = generate_history_dashboard(
    output_path="quality-dashboard.html",
    task_alias="spec.md",
    limit=100,
    include_trends=True
)
print(f"Dashboard saved to quality-dashboard.html")
```

## History Storage

Quality history is stored in:

```
.speckit/quality-history/
├── index.jsonl          # Master index (one JSON per line)
└── <run_id>.json        # Individual run files
```

Each run record includes:
- Run ID and timestamp
- Score and pass/fail status
- Phase and stop reason
- Iterations used
- Priority profile and cascade strategy
- Criteria template name
- Category scores
- Severity counts
- Gate policy and result (if applicable)
- Failed categories
- Duration in seconds

## Use Cases

### CI/CD Integration

Track quality trends in your CI/CD pipeline:

```yaml
# .github/workflows/quality-check.yml
- name: Run Quality Check
  run: speckit loop spec.md --json-output report.json

- name: Save to History
  run: speckit history --format json --limit 100 > history.json

- name: Check for Decline
  run: |
    if grep -q '"direction": "declining"' history.json; then
      echo "Quality is declining!"
      exit 1
    fi
```

### Project Health Dashboard

Generate health metrics for dashboards:

```bash
# Get history as JSON
speckit history --format json --stats --trends > quality-metrics.json

# Use in Grafana, Datadog, or custom dashboard
```

### Performance Analysis

Analyze iteration counts and duration:

```bash
# Show runs with high iteration counts
speckit history --runs --limit 50 | grep "iterations: [4-9]"
```

### Regression Detection

Compare recent runs to detect quality regressions:

```bash
# Get last 10 runs and check for decline
speckit history --trends --limit 10
```

## Notes

- History is saved automatically after each quality loop run (unless `--no-history` is specified)
- History files use JSONL format for efficient appending
- Individual run files allow easy access to specific runs
- All history operations are local to the project (`.speckit/quality-history/`)
- Use `--format json` for integration with external tools
