# `/speckit.feedback` - Quality Feedback Loop Analysis

Analyze quality loop results and get actionable improvement recommendations.

## Usage

```bash
# Analyze feedback with console output
/speckit.feedback analyze

# Analyze with more runs
/speckit.feedback analyze --runs 50

# Filter by specific task
/speckit.feedback analyze --task my-api-spec

# Export as Markdown
/speckit.feedback analyze --output feedback-report.md

# Export as JSON for CI/CD
/speckit.feedback analyze --json --output feedback.json

# Get quick suggestions only
/speckit.feedback suggestions

# Show trend visualization
/speckit.feedback trends

# Show insights only
/speckit.feedback insights --priority high,critical
```

## Options

| Option | Description |
|--------|-------------|
| `--runs, -r` | Number of recent runs to analyze (default: 20) |
| `--task, -t` | Filter by task alias |
| `--output, -o` | Output file path |
| `--json` | Export as JSON |
| `--markdown` | Export as Markdown |
| `--priority` | Filter insights by priority (critical,high,medium,low) |
| `--suggestions` | Show suggestions only |
| `--trends` | Show trend visualization only |
| `--adjustments` | Show configuration adjustments only |

## Output Examples

### Console Output

```
======================================================================
QUALITY FEEDBACK REPORT
======================================================================

Period: 2026-03-01 → 2026-03-13
Runs: 25

----------------------------------------------------------------------
OVERALL TREND

↑ IMPROVING
  Score: 0.87 (+8.3%)
  Velocity: +0.003/run

----------------------------------------------------------------------
CATEGORY TRENDS

  Security       ↑ 0.92 ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮░░ (+12.5%)
  Testing        ↑ 0.88 ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮░░░ (+7.2%)
  Performance    → 0.85 ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮░░░░ (+1.1%)
  Documentation  ↓ 0.78 ▮▮▮▮▮▮▮▮▮▮▮▮▮▮░░░░░░ (-3.4%)

----------------------------------------------------------------------
🚨 CRITICAL INSIGHTS

  • Documentation Quality Declining
    Documentation quality has declined by 3.4% over 25 runs.

----------------------------------------------------------------------
SUGGESTED ADJUSTMENTS

  [70%] Increase focus on weak areas: documentation
  [60%] Add focus on commonly failing rules: api_versioning

----------------------------------------------------------------------
AREAS SUMMARY

  📉 Weak: documentation
  📈 Strong: security, testing

----------------------------------------------------------------------
RECOMMENDATIONS

  📉 Focus on improving weak areas: documentation
  📈 Leverage strong areas: security, testing
  ⚙️  Consider 2 high-confidence configuration adjustment(s)
======================================================================
```

### JSON Output

```json
{
  "analysis_period": {
    "start": "2026-03-01T00:00:00",
    "end": "2026-03-13T23:59:59"
  },
  "total_runs": 25,
  "overall_trend": {
    "direction": "improving",
    "current_value": 0.87,
    "change_percent": 8.3,
    "velocity": 0.003
  },
  "insights": [...],
  "adjustments": [...],
  "recommendations": [...]
}
```

## Features

### Trend Analysis

- **Overall Quality Trend**: Track improvement or decline
- **Category Trends**: Per-category trend analysis
- **Velocity Metrics**: Rate of change per run
- **Significance Detection**: Statistical significance of changes

### Insights

- **Priority Levels**: Critical, High, Medium, Low
- **Impact Scoring**: Potential impact of improvements
- **Effort Estimation**: Estimated effort to implement
- **Actionable Suggestions**: Specific improvement actions

### Configuration Adjustments

- **Threshold Adjustments**: Increase/decrease quality thresholds
- **Iteration Tuning**: Adjust refinement iterations
- **Category Focus**: Add focus on weak areas
- **Profile Changes**: Suggest priority profile changes
- **Goal Adjustments**: Modify quality targets

### Recommendations

- **Weak Areas**: Identify areas needing attention
- **Strong Areas**: Leverage existing strengths
- **Action Items**: Prioritized improvement actions

## Integration with Quality Loop

```bash
# Run quality loop with feedback collection
/speckit.loop --criteria backend,security --collect-feedback

# Analyze feedback after loop
/speckit.feedback analyze

# Apply suggested adjustments
/speckit.loop --criteria backend,security --iterations 6
```

## CI/CD Integration

```yaml
# GitHub Actions
- name: Run Quality with Feedback
  run: |
    /speckit.loop --json --output result.json
    /speckit.feedback analyze --json --output feedback.json

- name: Check for Critical Issues
  run: |
    /speckit.feedback insights --priority critical
```

## Storage

Feedback results are stored in `.speckit/feedback/` as JSON files:

```
.speckit/feedback/
├── result_20260313_143022.json
├── result_20260313_150345.json
└── ...
```

## Minimum Requirements

- **3 runs**: Minimum for trend analysis
- **10 runs**: Recommended for confident insights
- **20+ runs**: Best for comprehensive analysis

## Related Commands

- `/speckit.loop` - Run quality evaluation
- `/speckit.history` - View quality history
- `/speckit.insights` - Generate quality insights
- `/speckit.goals` - Manage quality goals
- `/speckit.autoconfig` - Auto-configure quality setup
