---
description: Manage and inspect quality gate policies for quality evaluation
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

Quality gate policies define rules for quality evaluation with:
- **Overall score threshold**: Minimum score required to pass
- **Severity-based gates**: Maximum allowed issues per severity level
- **Category-based gates**: Minimum scores per category
- **Blocking behavior**: Whether failures block actions

**Usage**: `/speckit.gates <mode> [arguments]`

## Mode Detection

Parse arguments to determine mode:
- `list` → List mode (show all gate policies)
- `show <name>` → Show mode (details of specific policy)
- `compare <name1> <name2> [...]` → Compare mode (compare multiple policies)
- `diff <name1> <name2>` → Diff mode (highlight differences between two policies)
- `validate [name]` → Validate mode (validate policy or all policies)
- `export <name>` → Export mode (export policy to YAML)
- `recommend` → Recommend mode (AI-powered policy recommendation)
- `wizard` → Wizard mode (interactive guide to select gate policy) (Exp 60)
- `cascade <policy1> <policy2> [...]` → Cascade mode (merge multiple policies with strategy)
- `cascade-presets` → List available cascade presets
- `cascade-preset <name>` → Use a predefined cascade preset
- `analytics <policy1> <policy2> [...]` → Analytics mode (analyze cascade policies) (Exp 63)
- `presets` → Presets mode (list built-in presets)
- `goal <mode> [arguments]` → Goal Gate mode (Exp 71 - quality goal-based gates)
- No argument → Defaults to `list`

**JSON Output Flag:**
- `--json` → Output in JSON format (for programmatic use)

**Analytics Flags (Exp 63):**
- `--strategy <name>` → Cascade strategy for analysis (strict, lenient, average, union, intersection)
- `--format <format>` → Output format: text, json
- `--compare-strategies` → Compare all cascade strategies side-by-side
- `--categories` → Show category distribution analysis

## Mode: List

**Usage**: `/speckit.gates list`

Lists all available gate policies (presets + custom from `.speckit/gate-policies.yml`).

Display format:
```
=== Quality Gate Policies ===

Built-in Presets:
  production    - Strict quality gate for production deployments (threshold: 0.95)
  staging       - Standard quality gate for staging environments (threshold: 0.85)
  development   - Relaxed quality gate for development (threshold: 0.70)
  ci            - Quality gate for CI/CD pipelines (threshold: 0.80)
  strict        - Ultra-strict quality gate for critical systems (threshold: 0.98)
  lenient       - Very relaxed quality gate for experimental features (threshold: 0.60)

Custom Policies (from .speckit/gate-policies.yml):
  my-production - Custom production gate for my project (threshold: 0.90)
  my-staging    - Relaxed staging gate (threshold: 0.80)

Total: 6 presets, 2 custom
```

JSON output format:
```json
{
  "presets": [
    {"name": "production", "description": "...", "overall_threshold": 0.95}
  ],
  "custom": [
    {"name": "my-production", "description": "...", "overall_threshold": 0.90}
  ],
  "total_count": 8
}
```

## Mode: Show

**Usage**: `/speckit.gates show <name>`

Shows full details of a specific gate policy.

Example:
```
=== Gate Policy: production ===

Description: Strict quality gate for production deployments

Overall Threshold: 0.95
Block on Failure: Yes

Severity Limits:
  Critical: 0 max (must be zero)
  High:     0 max (must be zero)
  Medium:   2 max
  Low:      5 max
  Info:     999 max (effectively no limit)

Category Gates:
  security     min_score: 0.98  max_failed: 0
  correctness  min_score: 0.95  max_failed: 1
  performance  min_score: 0.90  max_failed: 2

Source: Built-in preset
```

If policy not found:
```
Error: Gate policy '{name}' not found.
Available policies: production, staging, development, ci, strict, lenient, my-production, my-staging
```

## Mode: Compare

**Usage**: `/speckit.gates compare <name1> <name2> [...]`

Compares multiple policies side-by-side.

Example:
```
=== Gate Policy Comparison ===

                    production    staging       development
─────────────────────────────────────────────────────────────
Overall Threshold  0.95          0.85          0.70
Block on Failure   Yes           Yes           No

Severity Limits:
  Critical          0 max         0 max         0 max
  High              0 max         2 max         5 max
  Medium            2 max         5 max         10 max
  Low               5 max         10 max        999 max

Category Gates:
  security          0.98/0        0.90/1        0.80/3
  correctness       0.95/1        0.85/3        -
  performance       0.90/2        -             -
```

Category gate format: `min_score/max_failed`

## Mode: Diff (Exp 62 - Enhanced)

**Usage**: `/speckit.gates diff <name1> <name2> [--format <format>] [--no-color]`

Shows detailed differences between two policies with enhanced visualization.

**Format options:**
- `text` (default) - Human-readable text with color-coded impact indicators
- `table` - ASCII table format for side-by-side comparison
- `compact` - One-line compact format
- `json` - JSON output for programmatic use

**Example - Text format:**
```
=== Policy Diff ===

Comparing: production vs staging

Summary:
  Total differences: 8
  Stricter in production: 6
  More lenient in production: 0
  Assessment: Policy 1 is stricter

Overall Threshold:
  production: 0.95 ↓
  staging: 0.95
  ▼ Stricter - Overall threshold increased

Severity Limits:
  Critical: 0 → 0 (Stricter)
  High: 0 → 2 (Lenient)
  Medium: 2 → 5 (Lenient)
  Low: 5 → 10 (Lenient)

Category Gates:
  security: min_score: 0.98 → 0.90 (Lenient)
    production: 0.98
    staging: 0.90
  correctness: min_score: 0.95 → 0.85 (Lenient)
    production: 0.95
    staging: 0.85
  performance: REMOVED - Category 'performance' gate removed in policy2

Blocking Behavior:
  production: Yes (blocks)
  staging: Yes (blocks)
  Change: No change
```

**Example - Table format:**
```
=== Policy Diff Table ===

Field                      | production       | staging           | Impact
------------------------------------------------------------------------------------
overall_threshold          | 0.95             | 0.85              | Stricter
critical_max               | 0                | 0                 | Same
high_max                   | 0                | 2                 | Lenient
medium_max                 | 2                | 5                 | Lenient
category:security          | 0.98/0           | 0.90/1            | Lenient
category:correctness       | 0.95/1           | 0.85/3            | Lenient
category:performance       | present          | absent            | Stricter
```

**Example - Compact format:**
```
▼ overall_threshold: 0.95→0.85 | ▲ high_max: 0→2 | ▲ medium_max: 2→5 | ▼ category:security: 0.98→0.90
```

**Impact indicators:**
- `▼` (red) - Policy 1 is stricter (more restrictive)
- `▲` (green) - Policy 1 is more lenient (less restrictive)
- `=` (white) - Both policies have the same value

**Use `--no-color`** to disable color output (useful for logs or non-TTY environments).

**Python API:**
```python
from specify_cli.quality.gate_policy_diff import (
    format_policy_diff,
    GatePolicyDiffVisualizer,
    get_diff_impact_summary,
)
from specify_cli.quality.gate_policies import GatePolicyManager

# Get raw diff data
diff_data = GatePolicyManager.diff_policies('production', 'staging')

# Format as text with colors
formatted = format_policy_diff(
    'production', 'staging', diff_data,
    format_type='text',
    use_colors=True
)
print(formatted)

# Format as table
formatted = format_policy_diff(
    'production', 'staging', diff_data,
    format_type='table'
)
print(formatted)

# Get impact summary
summary = get_diff_impact_summary(diff_data)
print(f"Total changes: {summary['total_changes']}")
print(f"Policy 1 stricter: {summary['policy1_stricter']}")
```

## Mode: Validate

**Usage**: `/speckit.gates validate [name]`

Validates gate policies for configuration errors.

Without argument, validates all policies:
```
=== Validating All Gate Policies ===

✓ production - Valid
✓ staging - Valid
✓ development - Valid
✓ ci - Valid
✓ strict - Valid
✓ lenient - Valid
✓ my-production - Valid
✓ my-staging - Valid

All 8 policies are valid.
```

With argument, validates specific policy:
```
=== Validating Gate Policy: my-custom ===

✓ Valid

Configuration is correct.
```

If validation fails:
```
=== Validating Gate Policy: my-custom ===

✗ Invalid (2 issues)

Issues:
  1. overall_threshold must be between 0.0 and 1.0, got 1.5
  2. Severity limits should follow: critical <= high <= medium <= low <= info
```

## Mode: Export

**Usage**: `/speckit.gates export <name>`

Exports a gate policy to YAML format for sharing or backup.

Example:
```
=== Gate Policy: production (YAML) ===

gate_policies:
  - name: production
    description: Strict quality gate for production deployments
    overall_threshold: 0.95
    severity_gate:
      critical_max: 0
      high_max: 0
      medium_max: 2
      low_max: 5
      info_max: 999
    category_gates:
      - category: security
        min_score: 0.98
        max_failed: 0
      - category: correctness
        min_score: 0.95
        max_failed: 1
      - category: performance
        min_score: 0.90
        max_failed: 2
    block_on_failure: true
```

Add `--json` flag for JSON output instead of YAML.

## Mode: Presets

**Usage**: `/speckit.gates presets`

Lists built-in preset policies only.

```
=== Built-in Presets ===

production  - Strict quality gate for production deployments (threshold: 0.95)
staging     - Standard quality gate for staging environments (threshold: 0.85)
development - Relaxed quality gate for development (threshold: 0.70)
ci          - Quality gate for CI/CD pipelines (threshold: 0.80)
strict      - Ultra-strict quality gate for critical systems (threshold: 0.98)
lenient     - Very relaxed quality gate for experimental features (threshold: 0.60)

Usage: /speckit.loop --gate-preset <preset-name>
```

## Mode: Recommend

**Usage**: `/speckit.gates recommend`

AI-powered gate policy recommendation based on:
- CI/CD environment (GitHub Actions, GitLab CI, etc.)
- Git branch (production, staging, feature, etc.)
- Project type (web-app, API, microservice, etc.)
- Security sensitivity indicators
- Current quality score (if available)

**Exp 61**: Now recommends cascade policies for hybrid scenarios!

Example output (standard policy):
```
=== Gate Policy Recommendation ===

Recommended Policy: ci
Confidence: 85%

Reasons:
  • Running in GitHub Actions environment
  • On feature branch 'feature/new-auth'
  • Detected project type: web-app
  • Current quality score: 0.78

Alternative Policies:
  • development: For development workflows
  • staging: For staging/pre-production
```

Example output (cascade policy):
```
=== Gate Policy Recommendation ===

Recommended Policy: prod-security
Confidence: 92%

Reasons:
  • Cascade policy combining: production, strict
  • Strategy: strict - Production policy with enhanced security - best for critical production deployments
  • Production branch with security requirements
  • On production branch 'main'
  • Project appears security-sensitive

Alternative Policies:
  • production: For production deployments (strict)
  • staging-plus: Cascade: Staging + CI for enhanced safety
  • strict: For critical systems (ultra-strict)
```

**Factors considered:**

1. **CI Environment**: If running in CI, recommends `ci` or `staging` policies
2. **Branch Type**:
   - `main/master/production` → `production` or `prod-security` (if security-sensitive)
   - `staging/qa` → `staging` or `staging-plus` (if in CI)
   - `dev/development` → `development` or `dev-flexible` (if in CI)
   - `feature/*` → `development` or `balanced`
3. **Project Type**: Some projects (APIs, microservices) get stricter recommendations
4. **Security**: Projects with auth/payment/crypto get security-focused cascade policies
5. **Quality Score**: Low scores may trigger more lenient recommendations
6. **Hybrid Scenarios** (Exp 61):
   - Production + Security → `prod-security` cascade
   - Staging + CI → `staging-plus` cascade
   - Development + CI → `dev-flexible` cascade
   - Mixed environments → `balanced` cascade
   - Comprehensive coverage → `full-coverage` cascade
   - Team consensus → `common-only` cascade

**JSON Output:**
```json
{
  "policy_name": "ci",
  "confidence": 0.85,
  "reasons": [
    "Running in GitHub Actions environment",
    "On feature branch 'feature/new-auth'",
    "Detected project type: web-app"
  ],
  "alternative_policies": [
    {"name": "development", "reason": "For development workflows"},
    {"name": "staging", "reason": "For staging/pre-production"}
  ],
  "context": {
    "is_ci": true,
    "ci_provider": "GitHub Actions",
    "branch": "feature/new-auth",
    "branch_type": "feature",
    "project_type": "web-app",
    "security_sensitive": false
  }
}
```

**Python API:**
```python
from specify_cli.quality.gate_policy_recommender import recommend_gate_policy, format_recommendation

# Get recommendation
recommendation = recommend_gate_policy()
print(format_recommendation(recommendation))

# With current quality score
recommendation = recommend_gate_policy(current_score=0.78)

# With user preferences
recommendation = recommend_gate_policy(
    user_preferences={
        "strictness_level": "strict",
        "security_first": True
    }
)
```

## Mode: Wizard (Exp 60)

**Usage**: `/speckit.gates wizard`

Interactive wizard that guides users through selecting the appropriate gate policy based on their context.

**Wizard Questions:**

1. **Environment**: Where will this code run?
   ```
   Where will this code be deployed?
   1) Production - Live production environment
   2) Staging - Pre-production testing
   3) Development - Local/dev environment
   4) CI/CD - Automated pipeline
   5) Experimental - Prototype/POC
   ```

2. **CI Environment** (if applicable): Are you running in CI?
   ```
   Are you running in a CI/CD pipeline?
   - Auto-detected if CI=true, GITHUB_ACTIONS, etc.
   ```

3. **Project Type**: What type of project is this?
   ```
   What is your project type?
   1) Web Application
   2) GraphQL API
   3) Microservice
   4) ML Service
   5) Data Pipeline
   6) Mobile App
   7) Desktop App
   8) Other
   ```

4. **Security**: Is this security-sensitive?
   ```
   Does your project handle:
   - Authentication/authorization
   - Payments/financial data
   - Personal information (PII)
   - Health data (HIPAA)
   - Other sensitive data
   ```

5. **Quality Score** (optional): What's your current quality score?
   ```
   Enter current quality score (0.0-1.0) if known:
   - Leave blank to skip
   - Used to adjust recommendation for low scores
   ```

**Wizard Output:**

```
=== Gate Policy Wizard Result ===

Recommended Policy: production
Confidence: 92%

Reasons:
  • Production environment detected
  • Project appears security-sensitive (auth, payment files found)
  • Web application project type
  • High quality score: 0.94

Policy Details:
  Overall Threshold: 0.95
  Block on Failure: Yes

  Severity Limits:
    Critical: 0 max
    High:     0 max
    Medium:   2 max
    Low:      5 max

  Category Gates:
    security    min_score: 0.98  max_failed: 0
    correctness min_score: 0.95  max_failed: 1
    performance min_score: 0.90  max_failed: 2

Alternative Policies:
  • staging: For pre-production testing
  • strict: For critical systems (ultra-strict)

Usage in Quality Loop:
  /speckit.loop --gate-preset production
  OR use --gate-policy-auto for automatic selection
```

**Python API:**
```python
from specify_cli.quality.gate_policy_recommender import recommend_gate_policy, format_recommendation

# Run wizard programmatically
recommendation = recommend_gate_policy(
    current_score=0.94,
    failed_categories=["security"],
    user_preferences={
        "strictness_level": "strict",
        "security_first": True
    }
)

print(format_recommendation(recommendation))
```

**Wizard Features:**
- **Auto-detection**: Detects CI environment, branch, project type automatically
- **Context-aware**: Recommendations based on security sensitivity, quality metrics
- **User preferences**: Supports manual overrides for strictness and security priorities
- **Alternatives**: Shows 2-3 alternative policies with rationale
- **Usage examples**: Provides ready-to-use command examples

**Integration with Quality Loop:**
```bash
# Option 1: Use wizard to get recommendation, then manually specify
/speckit.gates wizard
# Output: Recommended Policy: production
/speckit.loop --gate-preset production

# Option 2: Use auto-recommendation directly in loop
/speckit.loop --gate-policy-auto
# Automatically recommends and applies policy based on context
```

## Mode: Cascade (Exp 59)

**Usage**: `/speckit.gates cascade <policy1> <policy2> [...] [--strategy <strategy>] [--name <name>]`

Merges multiple gate policies into a single combined policy using various merge strategies.

**Strategies:**
- `strict` (default) - Take strictest values (highest threshold, lowest limits)
- `lenient` - Take most lenient values (lowest threshold, highest limits)
- `average` - Average values across all policies
- `union` - Combine all category gates from all policies
- `intersection` - Keep only category gates present in all policies

**Example:**
```
=== Cascade Gate Policy: production+staging ===

Description: Cascade of production, staging using strict strategy
Strategy: strict
Source Policies: production, staging

--- Merged Policy ---
Overall Threshold: 0.95
Block on Failure: True

Severity Limits:
  Critical: 0 max
  High:     0 max
  Medium:   2 max
  Low:      5 max
  Info:     999 max

Category Gates:
  security        min_score: 0.98  max_failed: 0
  correctness     min_score: 0.95  max_failed: 1
  performance     min_score: 0.90  max_failed: 2
```

**Use cases:**
- `production + security` → Extra strict production gate
- `staging + ci` → Staging gate with CI integration
- `development + lenient` → Flexible development gate
- `production + strict + custom` → Custom strict production gate

**JSON Output:**
```json
{
  "name": "production+staging",
  "description": "Cascade of production, staging using strict strategy",
  "source_policies": ["production", "staging"],
  "strategy": "strict",
  "merged_policy": {
    "name": "production+staging",
    "overall_threshold": 0.95,
    "block_on_failure": true,
    "severity_gate": {
      "critical_max": 0,
      "high_max": 0,
      "medium_max": 2,
      "low_max": 5,
      "info_max": 999
    },
    "category_gates": [...]
  }
}
```

**Python API:**
```python
from specify_cli.quality.gate_cascade import cascade_gate_policies, format_cascade_policy

# Cascade multiple policies
cascade, issues = cascade_gate_policies(
    policy_names=["production", "security"],
    strategy="strict"
)

if cascade:
    print(format_cascade_policy(cascade))
    # Use the merged policy
    policy = cascade.merged_policy
else:
    for issue in issues:
        print(f"Error: {issue.message}")
```

## Mode: Cascade Presets

**Usage**: `/speckit.gates cascade-presets`

Lists predefined cascade presets for quick use.

```
=== Cascade Presets ===

prod-security    - Production policy with enhanced security
                  (production + strict, strategy: strict)

staging-plus     - Staging policy with extra safety margin
                  (staging + ci, strategy: strict)

dev-flexible     - Development policy with CI integration
                  (development + ci, strategy: lenient)

balanced         - Balanced policy averaging production and development
                  (production + development, strategy: average)

full-coverage    - Union of production and staging for comprehensive coverage
                  (production + staging, strategy: union)

common-only      - Intersection of all policies for consensus checks
                  (production + ci + staging, strategy: intersection)
```

## Mode: Cascade Preset

**Usage**: `/speckit.gates cascade-preset <name> [--strategy <strategy>]`

Uses a predefined cascade preset. Optionally override the strategy.

```
=== Cascade Gate Policy: prod-security ===

Description: Production policy with enhanced security
Strategy: strict
Source Policies: production, strict

--- Merged Policy ---
Overall Threshold: 0.98
Block on Failure: True
...
```

## Mode: Analytics (Exp 63)

**Usage**: `/speckit.gates analytics <policy1> <policy2> [...] [--strategy <strategy>] [--format <format>]`

Analyzes cascade policies with detailed metrics and insights.

**Format options:**
- `text` (default) - Human-readable analytics report
- `json` - JSON output for CI/CD integration

**Example - Analyze cascade impact:**
```
=== Cascade Policy Analytics ===

Cascade: production+staging
Source Policies: production, staging
Strategy: strict

--- Metrics ---
Overall Threshold: 0.95
Strictness Score: 0.87 / 1.0
Coverage Score: 0.75 / 1.0

Severity Limits:
  Critical   0
  High       0
  Medium     2
  Low        5

Category Impacts (sorted by impact):
  security         [██████████] 1.47 (weight: 1.5, risk: high)
  correctness      [████████░░] 1.33 (weight: 1.4, risk: high)
  performance      [██████░░░░] 1.08 (weight: 1.2, risk: medium)

Recommendations:
  • Policy is ultra-strict. Consider using 'lenient' strategy for development environments.
  • Missing category gates for: testing
```

**Example - Compare strategies:**
```
/speckit.gates analytics production staging --compare-strategies

=== Cascade Strategy Comparison ===

✓ STRICT vs LENIENT
  Threshold Diff: +0.10
  Strictness Diff: +0.15
  Coverage Diff: 0.00
  Winner: STRICT
  Rationale: strict strategy is stricter (0.87 vs 0.72)

= STRICT vs AVERAGE
  Threshold Diff: +0.05
  Strictness Diff: +0.08
  Coverage Diff: 0.00
  Winner: TIE
  Rationale: Both strategies have similar strictness levels
```

**Example - Category distribution:**
```
/speckit.gates analytics production --categories

=== Category Distribution Analysis ===

Category impacts sorted by potential impact:

  security         [██████████] 1.47 (weight: 1.5, threshold: 0.98, priority: critical)
  correctness      [████████░░] 1.33 (weight: 1.4, threshold: 0.95, priority: high)
  performance      [██████░░░░] 1.08 (weight: 1.2, threshold: 0.90, priority: high)
```

**Analytics Features:**

1. **Strictness Score** (0.0 to 1.0): Overall strictness combining:
   - Overall threshold (40%)
   - Severity gate limits (30%)
   - Category gate strictness (20%)
   - Blocking behavior (10%)

2. **Coverage Score** (0.0 to 1.0): Coverage of high-priority categories:
   - Security, correctness, performance, testing

3. **Category Impact Analysis**: For each category gate:
   - Weight: Priority multiplier (e.g., security=1.5x)
   - Impact score: Combined threshold and failure limit
   - Risk level: critical, high, medium, low

4. **Recommendations**: Actionable suggestions based on:
   - Strictness level (too strict/lenient?)
   - Coverage gaps (missing categories?)
   - Risk distribution (too many high-risk categories?)

**Python API:**
```python
from specify_cli.quality.gate_policy_analytics import (
    GatePolicyAnalytics,
    analyze_cascade_policy,
    compare_cascade_strategies,
    format_analytics_report,
)

# Analyze cascade impact
analytics = GatePolicyAnalytics()
report, warnings = analytics.analyze_cascade_impact(
    policy_names=["production", "staging"],
    strategy="strict"
)

if report:
    print(format_analytics_report(report))

    # Get JSON output
    import json
    print(json.dumps(report.to_dict(), indent=2))

# Compare strategies
comparisons = analytics.compare_strategies(
    policy_names=["production", "staging"],
    strategies=["strict", "lenient", "average"]
)

for comp in comparisons:
    print(f"{comp.strategy1} vs {comp.strategy2}: {comp.winner}")

# Analyze category distribution
distributions, warnings = analytics.analyze_category_distribution("production")
if distributions:
    for dist in distributions:
        print(f"{dist.category}: {dist.potential_impact:.2f} ({dist.priority})")
```

**Convenience functions:**
```python
from specify_cli.quality.gate_policy_analytics import (
    analyze_cascade_policy,
    compare_cascade_strategies,
)

# Quick analysis
analysis_dict, warnings = analyze_cascade_policy(
    policy_names=["production", "security"],
    strategy="strict"
)

# Compare strategies
comparison_list = compare_cascade_strategies(
    policy_names=["production", "staging"],
    strategies=["strict", "lenient"]
)
```

**Use cases:**
- **Policy optimization**: Understand which categories drive quality
- **Strategy selection**: Compare cascade strategies before deployment
- **Risk assessment**: Identify high-risk categories that need attention
- **Coverage gaps**: Find missing category gates
- **CI/CD integration**: JSON output for automated analysis

## Mode: Goal Gates (Exp 71)

**Usage**: `/speckit.gates goal <mode> [arguments]`

Manages goal-based quality gates that validate against quality goals.

### Goal Gate Sub-Modes:

#### `goal list` - List Goal Gate Presets
```
=== Goal Gate Presets ===

strict      - All goals must be achieved, at-risk goals block gate
moderate    - All goals must be achieved or at-risk, failed goals block gate (default)
lenient     - Only failed goals block gate, at-risk allowed
conservative- At-risk or failed goals block gate
balanced    - At least 80% of goals must be achieved

Usage: /speckit.loop --gate-goal-mode moderate
```

#### `goal show <preset>` - Show Goal Gate Preset Details
```
=== Goal Gate Preset: moderate ===

Mode: all_must_pass
Allow At-Risk: Yes
Description: All goals must be achieved or at-risk, failed goals block gate

Behavior:
  ✓ Achieved goals: Pass
  ⚠ At-risk goals: Pass
  ✗ Failed goals: BLOCK
  ○ Not started: BLOCK
```

#### `goal evaluate <mode>` - Evaluate Goal Gate
```
=== Goal Gate Evaluation: moderate ===

Evaluating quality goals...

Gate Result: FAILED
Message: 2 goal(s) not achieved

Goal Summary:
  Total: 5
  Achieved: 2
  At Risk: 1
  Failed: 2

Blocked Goals:
  - Security Score Goal [failed]
    Target: 0.85, Current: 0.72
  - Test Coverage Goal [at_risk]
    Target: 80%, Current: 75%
```

#### `goal recommend` - Recommend Goal Gate Mode
```
=== Goal Gate Recommendation ===

Recommended Mode: conservative
Confidence: 85%

Reasons:
  • Production environment detected
  • Failed goals present in current evaluation
  • Security-sensitive project type

Alternative Modes:
  • moderate: For standard workflows
  • lenient: For development environments
```

**JSON Output:**
```json
{
  "recommended_mode": "conservative",
  "confidence": 0.85,
  "reasons": [
    "Production environment detected",
    "Failed goals present"
  ],
  "alternatives": [
    {"mode": "moderate", "reason": "For standard workflows"},
    {"mode": "lenient", "reason": "For development"}
  ]
}
```

#### `goal check [mode]` - Quick Goal Status Check
```
=== Goal Status Check ===

Goal Gate Mode: moderate (default)

Active Goals: 5
  ✓ Achieved: 2 (40%)
  ⚠ At-Risk: 1 (20%)
  ✗ Failed: 2 (40%)

Gate Status: BLOCKED
Action Required: Fix failed goals before proceeding
```

**Integration with Quality Loop:**
```bash
# Use goal-based gate in quality loop
/speckit.loop --gate-goal-mode strict

# Combine with goal presets
/speckit.loop --goal-preset production --gate-goal-mode moderate

# Auto-update goals during loop
/speckit.loop --gate-goal-mode moderate --auto-update-goals
```

**Python API:**
```python
from specify_cli.quality.goal_gates import (
    create_goal_gate,
    evaluate_goal_gate,
    format_goal_gate_result,
    list_goal_gate_presets,
    recommend_goal_gate,
    create_aware_gate,
)

# Create goal gate
gate = create_goal_gate(
    name="my-goal-gate",
    mode="moderate",
    goals_file=".speckit/quality-goals.json"
)

# Evaluate gate
result = gate.evaluate(evaluation_result)
print(format_goal_gate_result(result))

# Goal-aware gate (auto-updates goals)
aware_gate = create_aware_gate(
    name="my-aware-gate",
    mode="strict",
    auto_update=True
)

# Evaluate and update goals in one call
result = aware_gate.evaluate_and_update(
    evaluation_result=eval_result,
    score=0.85,
    category_scores={"security": 0.90, "performance": 0.80}
)

# List presets
presets = list_goal_gate_presets()
for name, description in presets.items():
    print(f"{name}: {description}")

# Get recommendation
recommended = recommend_goal_gate(
    project_type="production",
    strictness="moderate"
)
print(f"Recommended: {recommended}")
```

**Goal Gate Modes:**

| Mode | Behavior | Use Case |
|------|----------|----------|
| `strict` | All goals achieved, at-risk blocks | Production, critical systems |
| `moderate` | All goals achieved/at-risk, failed blocks | Standard deployment (default) |
| `lenient` | Only failed blocks | Development, feature branches |
| `conservative` | At-risk or failed blocks | Security-sensitive, compliance |
| `balanced` | 80%+ achieved | Progressive quality improvement |

**Use Cases:**

1. **Production Deployment**: Use `strict` or `conservative` mode to ensure all quality goals are met before deploying to production.

2. **Staging/QA**: Use `moderate` mode to allow at-risk goals while blocking on failed goals.

3. **Development**: Use `lenient` mode to focus only on failed goals without blocking on at-risk.

4. **Compliance**: Use `conservative` mode for regulated industries (healthcare, finance).

5. **Progressive Improvement**: Use `balanced` mode to ensure 80%+ goal achievement while allowing flexibility.

**Integration with Quality Goals:**

Goal-based gates work seamlessly with:
- **Quality Goals System** (Exp 68): Define and track quality goals
- **Goal Presets** (Exp 69): Pre-configured goal sets
- **Category Templates** (Exp 70): Category-focused goals

```python
from specify_cli.quality import (
    apply_preset,  # Apply goal preset
    create_aware_gate,  # Create goal-aware gate
    save_quality_run,  # Save to history
)

# Apply production goals preset
apply_preset("production", ".speckit/quality-goals.json")

# Create goal-aware gate that auto-updates
gate = create_aware_gate("production-goals", mode="strict")

# Use in quality loop
result = gate.evaluate_and_update(
    evaluation_result,
    score=0.92,
    category_scores=category_scores
)

# Save to history for tracking
if result.passed:
    save_quality_run(evaluation_result, ".speckit/quality-history.jsonl")
```

## Python API Usage

All operations are available via Python API:

```python
from specify_cli.quality.gate_policies import GatePolicyManager

# List all policies
policies = GatePolicyManager.list_all_policies()
# ['ci', 'development', 'lenient', 'production', 'staging', 'strict']

# Show policy details
details = GatePolicyManager.show_policy('production')
print(details['description'])
# "Strict quality gate for production deployments"

# Compare policies
comparison = GatePolicyManager.compare_policies('production', 'staging')
for policy in comparison:
    print(f"{policy['name']}: threshold={policy['overall_threshold']}")

# Diff policies
diff = GatePolicyManager.diff_policies('production', 'development')
print(diff['overall_threshold']['diff'])
# 0.25 (development is more lenient)

# Validate all policies
validation = GatePolicyManager.validate_all_policies()
for result in validation:
    if not result['is_valid']:
        print(f"Invalid: {result['name']}")
```

## Custom Policies

Create custom policies in `.speckit/gate-policies.yml`:

```yaml
gate_policies:
  my-production:
    description: "Custom production gate"
    overall_threshold: 0.90
    severity_gate:
      critical_max: 0
      high_max: 1
      medium_max: 5
      low_max: 10
    category_gates:
      - category: security
        min_score: 0.95
        max_failed: 0
    block_on_failure: true
```

Use with: `/speckit.loop --gate-policy my-production`

## Error Handling

| Error | Action |
|-------|--------|
| Policy not found | Error: "Gate policy '{name}' not found. Available: {list}" |
| Invalid mode | Error: "Unknown mode '{mode}'. Available: list, show, compare, diff, validate, export, presets" |
| YAML parse error | Error: "Failed to parse gate-policies.yml: {error}" |
| Validation error | Error: "Policy '{name}' has validation issues: {count}" |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (policy not found, invalid mode, etc.) |
| 2 | Validation failed (for validate mode) |
