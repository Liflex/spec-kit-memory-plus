---
description: Get intelligent quality insights and improvement recommendations
long_description: |
  The Quality Insights System provides intelligent analytics and proactive quality improvement recommendations.

  Generate insights from your quality history:
  - **Pattern Recognition**: Identify recurring quality patterns (oscillation, degradation, spikes)
  - **Trend Analysis**: Understand quality trends with predictive forecasts
  - **Optimization Opportunities**: Find areas with highest improvement potential
  - **Action Items**: Get concrete, prioritized improvement actions
  - **Root Cause Analysis**: Identify underlying causes of quality issues
  - **Benchmarking**: Compare current quality against goals

  **Insight Types:**
  - `pattern` - Recurring quality patterns detected
  - `trend` - Quality trend direction and significance
  - `prediction` - Future quality forecasts
  - `optimization` - Areas with improvement potential
  - `root_cause` - Root cause of quality issues
  - `benchmark` - Comparison against goals
  - `action_item` - Specific improvement actions

  **Priority Levels:**
  - `critical` - Immediate attention required
  - `high` - Important improvement opportunity
  - `medium` - Worthwhile improvement
  - `low` - Nice-to-have optimization

  **Examples:**

  Generate insights for current task:
  ```
  /speckit.insights generate
  ```

  Generate insights with detailed output:
  ```
  /speckit.insights generate --detailed
  ```

  Export insights as JSON:
  ```
  /speckit.insights generate --json
  ```

  Export action items to file:
  ```
  /speckit.insights actions --output actions.md
  ```

  Get quick summary:
  ```
  /speckit.insights summary
  ```

  Analyze specific task:
  ```
  /speckit.insights generate --task <task-alias>
  ```
---

# Quality Insights

Get intelligent quality insights and improvement recommendations based on your quality history.

## Quick Start

```bash
# Generate insights for your quality history
/speckit.insights generate

# Get a quick summary
/speckit.insights summary

# Export actionable improvements
/speckit.insights actions --output improvements.md
```

## Subcommands

### `generate` - Generate quality insights

```bash
/speckit.insights generate [options]
```

Analyzes quality history and generates intelligent insights.

**Options:**
- `--task <alias>`: Analyze specific task (default: current/all)
- `--runs <n>`: Number of recent runs to analyze (default: 50)
- `--detailed`: Show detailed insights (default: brief)
- `--json`: Export as JSON
- `--output <file>`: Write to file

**Output includes:**
- Overall quality assessment
- Priority breakdown (critical/high/medium/low)
- Detected patterns (oscillation, degradation, spikes)
- Trend analysis with forecasts
- Optimization opportunities ranked by potential
- Root cause analysis
- Predictive insights
- Actionable recommendations

### `summary` - Get insights summary

```bash
/speckit.insights summary [--task <alias>]
```

Get a one-line summary of quality insights.

**Example output:**
```
CRITICAL: 2 critical, 5 high priority insights
```

### `patterns` - Show detected patterns

```bash
/speckit.insights patterns [--task <alias>]
```

Show only pattern-related insights.

**Patterns detected:**
- **Score Oscillation**: Cyclical up/down patterns
- **Gradual Degradation**: Slow quality decline over time
- **Iteration Spikes**: Runs requiring excessive iterations
- **Persistent Low Categories**: Categories consistently scoring low

### `trends` - Show trend analysis

```bash
/speckit.insights trends [--task <alias>]
```

Show quality trend analysis with forecasts.

**Trend directions:**
- `improving` - Quality improving over time
- `declining` - Quality declining (attention needed)
- `stable` - Quality stable
- `volatile` - High variability (stability needed)

### `optimization` - Show optimization opportunities

```bash
/speckit.insights optimization [--task <alias>]
```

Show areas with highest improvement potential.

**Shows:**
- Categories with low scores
- Pass rate optimization
- Iteration efficiency
- Ranked by improvement potential

### `actions` - Export action items

```bash
/speckit.insights actions [options]
```

Export concrete action items for quality improvement.

**Options:**
- `--output <file>`: Output file path (default: stdout)
- `--format <fmt>`: Output format (markdown, json)
- `--priority <min>`: Minimum priority (critical, high, medium, low)

**Output includes:**
- Action ID and title
- Priority and effort level
- Expected impact
- Step-by-step implementation guide

### `predict` - Predict future quality

```bash
/speckit.insights predict [--task <alias>] [--runs <n>]
```

Generate predictions for future quality scores.

**Predictions:**
- Next run expected score
- Pass rate forecasts
- Category-specific predictions
- Trend-based forecasts

## Integration with Quality Loop

Generate insights after quality loop:

```bash
# Run quality loop with insights
/speckit.loop backend --insights

# Generate insights for specific task
/speckit.history insights <task-alias>
```

## Insight Types Explained

### Pattern Insights
Identify recurring patterns in your quality data:
- **Cyclical**: Quality oscillating up and down
- **Degradation**: Gradual decline over time
- **Improvement**: Consistent improvement trend
- **Spike**: Sudden changes in iteration counts

### Trend Insights
Understand where your quality is heading:
- **Direction**: improving, declining, stable, or volatile
- **Strength**: How strong the trend is (0-1)
- **Forecast**: Predicted future state
- **Rate**: Change per run

### Optimization Insights
Find the best areas to focus improvement efforts:
- **Area**: Category or metric to optimize
- **Current**: Current value
- **Potential**: Expected value if optimized
- **Improvement**: Potential gain
- **Effort**: Estimated effort required

### Root Cause Insights
Understand why quality issues occur:
- **Primary failure categories**: Most common failure points
- **Iteration patterns**: Why some runs require more iterations
- **Category correlations**: Related issues across categories

## Example Workflow

```bash
# 1. Run quality loop
/speckit.loop backend --check-goals

# 2. Generate insights
/speckit.insights generate --detailed

# 3. Export action items
/speckit.insights actions --output improvements.md

# 4. Focus on top optimization opportunity
/speckit.loop <category> --config production-strict

# 5. Check progress
/speckit.insights summary
```

## Output Format

### Text Output
```
## Quality Insights for 'backend'

**Overall Assessment:** [Good] Quality is good. 3 high-priority improvements identified.
**Analyzed:** 25 runs
**Insights Generated:** 12

**Priority Breakdown:**
  🚨 CRITICAL: 1
  ⚠️ HIGH: 3
  ⚡ MEDIUM: 5
  💡 LOW: 3

### Patterns Detected
🔁 **Pattern: Gradual Degradation** [degradation]
   Quality degrading by 8.2% over recent runs
   💡 Schedule dedicated quality improvement sprints
```

### JSON Output
```json
{
  "insights_generated": 12,
  "insights_by_priority": {
    "critical": 1,
    "high": 3,
    "medium": 5,
    "low": 3
  },
  "insights": [...],
  "pattern_insights": [...],
  "trend_insights": [...],
  "optimization_insights": [...],
  "action_items": [...]
}
```

## Action Items Format

When exporting action items, you get:

```markdown
# Quality Improvement Action Items

Generated: 2026-03-13T10:30:00
Task: backend

## Summary
- Total actions: 8
- Critical: 2
- High: 4

## Action Items

### A001: Improve Security Quality
**Priority:** HIGH
**Effort:** MEDIUM
**Impact:** +0.12 expected score increase

Focus improvement efforts on security - review criteria, add rules, run dedicated loop

**Steps:**
1. Review security criteria template
2. Run quality loop with focus on security
3. Add specific security quality rules
4. Monitor progress in next 3 runs
```

## Tips

- **Run regularly**: Generate insights after each quality loop to track progress
- **Focus on critical/high**: Prioritize critical and high priority insights
- **Track trends**: Use trend analysis to see if improvements are working
- **Export actions**: Use action items for team planning and sprint backlog
- **Combine with goals**: Use insights to achieve quality goals faster

## Python API

```python
from specify_cli.quality import generate_insights, format_insights_report

# Generate insights
report = generate_insights(task_alias="backend", max_runs=50)

# Format as text
print(format_insights_report(report, detailed=True))

# Export as JSON
from specify_cli.quality import format_insights_json
json_str = format_insights_json(report)

# Export action items
from specify_cli.quality import export_action_items
export_action_items(report, "improvements.md")
```
