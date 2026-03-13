---
description: Detect and analyze quality anomalies in your project
long_description: |
  Monitor quality metrics for unusual patterns and regressions.

  The Quality Anomaly Detection system helps you:
  - Detect score regressions compared to historical baseline
  - Identify statistical outliers using z-score analysis
  - Monitor declining pass rates over time
  - Detect quality stagnation (plateaued improvement)
  - Find category-specific score drops
  - Identify sudden iteration spikes

  **Anomaly Types:**
  - `regression`: Score drop compared to rolling baseline
  - `outlier`: Statistical outlier (unusual score deviation)
  - `pass_rate_drop`: Declining pass rate over time
  - `stagnation`: Quality plateaued (no improvement)
  - `category_drop`: Specific category score drop
  - `iteration_spike`: Sudden increase in iteration count

  **Severity Levels:**
  - `critical`: Immediate action required (15%+ score drop)
  - `high`: Significant issue detected (10%+ drop)
  - `medium`: Moderate anomaly worth investigating
  - `low`: Minor deviation, monitor
  - `info`: Informational, no action needed

  **Examples:**

  Detect anomalies in current project:
  ```
  /speckit.anomalies detect
  ```

  Show anomaly report with details:
  ```
  /speckit.anomalies report
  ```

  Get quick summary:
  ```
  /speckit.anomalies summary
  ```

  Export anomalies as JSON for CI/CD:
  ```
  /speckit.anomalies export --json
  ```

  Filter by severity:
  ```
  /speckit.anomalies detect --min-severity high
  ```

  Filter by type:
  ```
  /speckit.anomalies detect --type regression,category_drop
  ```

  Adjust detection thresholds:
  ```
  /speckit.anomalies detect --regression-threshold 0.03 --z-score 3.0
  ```

  Show available anomaly types:
  ```
  /speckit.anomalies types
  ```

  Show detection configuration:
  ```
  /speckit.anomalies config show
  ```

  Reset to default configuration:
  ```
  /speckit.anomalies config reset
  ```

  Get recommendations for detected anomalies:
  ```
  /speckit.anomalies recommend
  ```
---

# Quality Anomaly Detection

Detect and analyze unusual patterns in your quality metrics to catch regressions early.

## Quick Start

The easiest way to detect anomalies:

```bash
# Detect all anomalies using default thresholds
/speckit.anomalies detect

# Get a quick summary of detected anomalies
/speckit.anomalies summary

# Get detailed recommendations for fixing anomalies
/speckit.anomalies recommend
```

## Understanding Anomalies

### Anomaly Types

| Type | Description | When to Investigate |
|------|-------------|---------------------|
| **regression** | Score dropped below rolling baseline | Recent quality decline |
| **outlier** | Statistical deviation from normal | Unusual single run |
| **pass_rate_drop** | Pass rate declining over time | Consistency issues |
| **stagnation** | Quality plateaued (no improvement) | Need new strategies |
| **category_drop** | Specific category score dropped | Targeted investigation |
| **iteration_spike** | Iteration count suddenly increased | Efficiency problems |

### Severity Levels

| Severity | Condition | Action Required |
|----------|-----------|-----------------|
| **CRITICAL** | 15%+ score drop | Immediate investigation |
| **HIGH** | 10%+ score drop | Investigate soon |
| **MEDIUM** | 5%+ score drop | Monitor closely |
| **LOW** | Minor deviation | Keep eye on it |
| **INFO** | Informational | No action needed |

## Detection Commands

### Detect Anomalies

Run anomaly detection on your quality history:

```bash
/speckit.anomalies detect [OPTIONS]
```

**Options:**
- `--min-severity LEVEL` - Minimum severity to report (default: low)
  - Values: info, low, medium, high, critical
- `--type TYPES` - Filter by anomaly types (comma-separated)
  - Values: regression, outlier, pass_rate_drop, stagnation, category_drop, iteration_spike
- `--category CATEGORY` - Filter by category name
- `--regression-threshold FLOAT` - Regression threshold (default: 0.05)
- `--regression-critical FLOAT` - Critical regression threshold (default: 0.15)
- `--z-score FLOAT` - Z-score threshold for outliers (default: 2.5)
- `--pass-rate-drop FLOAT` - Pass rate drop threshold (default: 0.10)
- `--stagnation-window INT` - Runs to check for stagnation (default: 10)
- `--stagnation-variance FLOAT` - Max variance for stagnation (default: 0.01)
- `--iteration-spike FLOAT` - Iteration spike multiplier (default: 2.0)
- `--json` - Output as JSON

**Examples:**

```bash
# Detect all anomalies
/speckit.anomalies detect

# Only show critical and high severity
/speckit.anomalies detect --min-severity high

# Only check for regressions and category drops
/speckit.anomalies detect --type regression,category_drop

# Custom thresholds for strict monitoring
/speckit.anomalies detect --regression-threshold 0.03 --z-score 2.0

# Check specific category
/speckit.anomalies detect --category security

# Export for CI/CD integration
/speckit.anomalies detect --json > anomalies.json
```

### Show Anomaly Report

Display detailed anomaly report:

```bash
/speckit.anomalies report [OPTIONS]
```

**Options:**
- `--format FORMAT` - Output format (default: text)
  - Values: text, markdown, json
- `--sort-by FIELD` - Sort field (default: severity)
  - Values: severity, type, timestamp, delta

**Examples:**

```bash
# Detailed text report
/speckit.anomalies report

# Markdown report for documentation
/speckit.anomalies report --format markdown

# JSON report for automation
/speckit.anomalies report --format json

# Sort by timestamp (newest first)
/speckit.anomalies report --sort-by timestamp
```

### Get Summary

Quick one-line summary of anomalies:

```bash
/speckit.anomalies summary
```

**Example Output:**
```
Detected 5 anomalies: 2 critical, 1 high, 2 medium
Most common: regression (3), category_drop (2)
```

### Get Recommendations

Get actionable recommendations for fixing detected anomalies:

```bash
/speckit.anomalies recommend [OPTIONS]
```

**Options:**
- `--severity LEVEL` - Only recommend for specific severity
- `--type TYPE` - Only recommend for specific type
- `--category CATEGORY` - Only recommend for specific category

**Examples:**

```bash
# All recommendations
/speckit.anomalies recommend

# Only critical issues
/speckit.anomalies recommend --severity critical

# Regression-specific recommendations
/speckit.anomalies recommend --type regression
```

## Configuration Commands

### Show Configuration

Display current anomaly detection configuration:

```bash
/speckit.anomalies config show
```

**Example Output:**
```
Anomaly Detection Configuration:
  Regression threshold: 5.0% (critical: 15.0%)
  Z-score threshold: 2.5
  Pass rate drop threshold: 10.0%
  Stagnation window: 10 runs (variance: 1.0%)
  Iteration spike multiplier: 2.0x
  Category drop threshold: 10.0%
```

### Reset Configuration

Reset to default configuration:

```bash
/speckit.anomalies config reset
```

## Information Commands

### List Anomaly Types

Show available anomaly types with descriptions:

```bash
/speckit.anomalies types
```

**Example Output:**
```
Available Anomaly Types:
  regression       - Score drop compared to rolling baseline
  outlier          - Statistical outlier using z-score
  pass_rate_drop   - Declining pass rate over time
  stagnation       - Quality plateaued (no improvement)
  category_drop    - Specific category score drop
  iteration_spike  - Sudden increase in iteration count
```

### Show Statistics

Display anomaly statistics from history:

```bash
/speckit.anomalies stats [OPTIONS]
```

**Options:**
- `--by-severity` - Group by severity
- `--by-type` - Group by type
- `--by-category` - Group by category

**Examples:**

```bash
# Overall statistics
/speckit.anomalies stats

# By severity
/speckit.anomalies stats --by-severity

# By type
/speckit.anomalies stats --by-type

# By category
/speckit.anomalies stats --by-category
```

## Export Commands

### Export Anomalies

Export anomaly report for external use:

```bash
/speckit.anomalies export [OPTIONS]
```

**Options:**
- `--format FORMAT` - Export format (default: json)
  - Values: json, csv
- `--output FILE` - Output file path
- `--min-severity LEVEL` - Filter by minimum severity

**Examples:**

```bash
# Export as JSON
/speckit.anomalies export --json

# Save to file
/speckit.anomalies export --json --output anomalies.json

# Export only high and critical
/speckit.anomalies export --json --min-severity high

# Export as CSV for spreadsheet analysis
/speckit.anomalies export --format csv --output anomalies.csv
```

## Integration with Quality Loop

Detect anomalies after quality loop:

```bash
# Run quality loop with anomaly detection
/speckit.loop --criteria backend --detect-anomalies

# Check for anomalies after quality loop
/speckit.loop --criteria frontend
/speckit.anomalies detect
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Quality Check with Anomaly Detection

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Quality Loop
        run: speckit loop --criteria backend --max-iterations 4

      - name: Detect Anomalies
        run: |
          speckit anomalies detect --min-severity high --json > anomalies.json

      - name: Fail on Critical Anomalies
        run: |
          critical_count=$(jq '.anomalies_by_severity.critical // 0' anomalies.json)
          if [ "$critical_count" -gt 0 ]; then
            echo "Critical anomalies detected!"
            exit 1
          fi
```

## Python API

You can also use the anomaly detection system programmatically:

```python
from specify_cli.quality import (
    QualityAnomalyDetector,
    AnomalyDetectionConfig,
    detect_anomalies,
    format_anomaly_report,
)

# Custom configuration
config = AnomalyDetectionConfig(
    regression_threshold=0.03,  # 3% drop triggers alert
    z_score_threshold=2.0,  # More sensitive outlier detection
)

detector = QualityAnomalyDetector(config)

# Detect anomalies
report = detector.detect_all(runs)

# Format report
print(format_anomaly_report(report))

# Or use convenience function
report = detect_anomalies(runs, config=config)
```

## Best Practices

1. **Run Regularly**: Detect anomalies after each quality loop
2. **Adjust Thresholds**: Tune thresholds based on your project's natural variance
3. **Investigate Trends**: Look for patterns in anomaly types over time
4. **Use Recommendations**: Follow recommendations for fixing detected issues
5. **Integrate with Gates**: Configure quality gates to fail on critical anomalies

## Related Commands

- `/speckit.history` - View quality history and trends
- `/speckit.insights` - Get proactive improvement recommendations
- `/speckit.goals` - Set quality goals to prevent regressions
- `/speckit.gates` - Configure quality gates with anomaly checks
