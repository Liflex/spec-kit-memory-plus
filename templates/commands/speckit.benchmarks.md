---
description: Quality benchmarking for comparing quality metrics against historical baselines and industry standards
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
- `create` → Create benchmark profile from historical data
- `compare` → Compare current quality to benchmark
- `report` → Generate comprehensive benchmark report
- `list` → List available benchmark profiles
- `delete` → Delete a benchmark profile
- No argument → Show overview and help

### Mode: Create

**Usage**: `/speckit.benchmarks create [--name <name>] [--task <alias>] [--runs <n>] [--output <path>]`

1. Get parameters:
   - `--name`: Benchmark profile name (default: {task}-benchmark)
   - `--task`: Task alias to analyze (default: default)
   - `--runs`: Max historical runs to include (default: 100)
   - `--output`: Optional JSON output path

2. Load quality history for task
3. Calculate percentile metrics for overall and category scores
4. Create BenchmarkProfile with calculated metrics
5. Display results:
   ```
   === Benchmark Profile Created ===

   Name: {name}
   Task: {task}
   Type: Historical
   Sample Size: {n} runs

   Overall Quality Percentiles:
     P0:   {min:.3f}
     P25:  {q1:.3f}
     P50:  {median:.3f}
     P75:  {q3:.3f}
     P100: {max:.3f}

   Category Percentiles:
     {category}: P50={median:.3f}, Mean={mean:.3f}
     ...
   ```

6. Save to JSON if output specified
7. Return profile object

### Mode: Compare

**Usage**: `/speckit.benchmarks compare [--score <value>] [--category <name>] [--benchmark <name>]`

1. Get parameters:
   - `--score`: Quality score to compare (default: use latest run)
   - `--category`: Category to compare (default: overall)
   - `--benchmark`: Benchmark profile name (default: auto-create from history)

2. Load or create benchmark profile
3. Get current score (from latest run or parameter)
4. Calculate percentile rank and comparison
5. Display results:
   ```
   === Benchmark Comparison ===

   Metric: {metric_name}
   Current Score: {score:.3f}
   Benchmark: {benchmark_name}

   Percentile Rank: {percentile:.1f}th
   Comparison: {comparison}

   Difference from Mean: {diff_mean:+.3f}
   Difference from Median: {diff_median:+.3f}
   Z-Score: {z_score:+.2f}

   Interpretation:
     {interpretation_text}
   ```

6. Return BenchmarkResult object

### Mode: Report

**Usage**: `/speckit.benchmarks report [--task <alias>] [--benchmark <name>] [--output <path>] [--format <json|text>]`

1. Get parameters:
   - `--task`: Task alias (default: default)
   - `--benchmark`: Benchmark profile name (optional, creates from history)
   - `--output`: Output path for report
   - `--format`: Report format (json or text, default: text)

2. Load or create benchmark profile
3. Get current scores from latest run
4. Generate comprehensive benchmark report:
   - Overall benchmark comparison
   - Category-wise comparisons
   - Summary statistics (excellent, above average, etc.)
   - Recommendations
   - Priority improvements

5. Display formatted report:
   ```
   === QUALITY BENCHMARK REPORT ===

   Profile: {profile_name}
   Task: {task}
   Generated: {timestamp}
   Sample Size: {n} runs
   Reliability: {reliability}

   OVERALL QUALITY
   ---------------
   Current Score: {score:.3f}
   Percentile Rank: {percentile}th
   Comparison: {comparison}

   CATEGORY SUMMARY
   ----------------
   Excellent: {n}
   Above Average: {n}
   Average: {n}
   Below Average: {n}
   Poor: {n}

   CATEGORY BREAKDOWN
   ------------------
   {category}: {score:.3f} ({percentile:.1f}th percentile)

   RECOMMENDATIONS
   ---------------
   1. {recommendation}
   ...

   PRIORITY IMPROVEMENTS
   ---------------------
   [HIGH] {category}: {percentile:.1f}th percentile
   ...
   ```

6. Save to file if output specified
7. Return BenchmarkReport object

### Mode: List

**Usage**: `/speckit.benchmarks list`

1. List all available benchmark profiles from `.speckit/benchmarks/`
2. Display:
   ```
   === Available Benchmarks ===

   {name}
     Type: {type}
     Task: {task}
     Sample Size: {n}
     Created: {date}
     Updated: {date}
   ...
   ```

### Mode: Delete

**Usage**: `/speckit.benchmarks delete <name>`

1. Confirm deletion
2. Delete benchmark profile file
3. Display: "Benchmark profile '{name}' deleted"

### Mode: Overview (No Argument)

**Usage**: `/speckit.benchmarks`

Display overview and help:
```
=== Quality Benchmarking ===

Quality benchmarking compares your current quality metrics against
historical baselines and industry standards.

Commands:
  create    Create a benchmark profile from historical data
  compare   Compare current quality to a benchmark
  report    Generate comprehensive benchmark report
  list      List available benchmark profiles
  delete    Delete a benchmark profile

Examples:
  /speckit.benchmarks create --name my-benchmark --runs 50
  /speckit.benchmarks compare --category security
  /speckit.benchmarks report --output benchmark-report.json
```

## Key Concepts

### Percentile Ranking

Percentile ranking shows where your current quality stands compared to historical data:
- **90th+ percentile**: Excellent - Top 10% of historical performance
- **75-90th percentile**: Above Average - Top 25% of historical performance
- **25-75th percentile**: Average - Middle 50% of historical performance
- **10-25th percentile**: Below Average - Bottom 25% of historical performance
- **0-10th percentile**: Poor - Bottom 10% of historical performance

### Benchmark Reliability

Benchmark reliability depends on sample size:
- **High**: 30+ runs - Reliable benchmarks
- **Medium**: 10-29 runs - Moderately reliable benchmarks
- **Low**: <10 runs - Limited reliability, continue collecting data

### Z-Score

Z-score indicates how many standard deviations the current score is from the mean:
- Positive: Above historical average
- Negative: Below historical average
- Magnitude indicates extremity

## Use Cases

1. **Track Quality Progress**: See if quality is improving relative to historical baseline
2. **Set Realistic Targets**: Use percentile data to set achievable quality goals
3. **Identify Regression**: Detect when quality drops below historical norms
4. **Category Focus**: Identify which categories need most improvement
5. **Industry Comparison**: Compare against industry quality standards

## Integration with Quality Loop

Use with quality loop for benchmark-aware quality evaluation:

```bash
# Run quality loop with benchmark report
/speckit.loop --criteria backend --json-output report.json

# Generate benchmark comparison
/speckit.benchmarks report --output benchmark.json

# Use benchmarks to set quality goals
/speckit.goals create --type target_score --target 0.85
```
