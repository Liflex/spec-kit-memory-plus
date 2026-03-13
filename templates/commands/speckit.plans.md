# `speckit.plans` - Quality Plans

**Quality Plans** — Unified quality improvement plans that combine loop configurations, quality goals, gate policies, and priority profiles into a single, cohesive improvement strategy.

## Overview

Quality Plans provide pre-configured, comprehensive quality improvement strategies that integrate all quality system components:

- **Loop Configuration**: Iteration count, thresholds, quality modes
- **Quality Goals**: Target scores, pass rates, category targets
- **Gate Policies**: Quality gates for CI/CD and deployment
- **Priority Profiles**: Category weights and multipliers

## Commands

### List All Plans

```
speckit.plans
```

List all available quality plans (built-in presets + custom).

### List Plans by Category

```
speckit.plans --category production
```

List plans filtered by category:
- `general` — General purpose quality plans
- `production` — Production deployment readiness
- `security` — Security-focused plans
- `performance` — Performance optimization plans
- `stability` — Stability and reliability plans
- `improvement` — Continuous improvement plans
- `ci_cd` — CI/CD integration plans

### Show Plan Details

```
speckit.plans --show production-ready
```

Display detailed information about a specific plan including:
- Loop configuration
- Quality goals
- Gate policy settings
- Priority profile
- Estimated duration

### Apply a Plan

```
speckit.plans --apply production-ready
```

Apply a quality plan to your project. This will:
1. Save the loop configuration
2. Set quality goals
3. Configure gate policies
4. Set priority profile

### Get Recommendations

```
speckit.plans --recommend production deployment
```

Get plan recommendations based on keywords.

```
speckit.plans --recommend security performance --category security
```

Filter recommendations by category.

### Compare Plans

```
speckit.plans --compare quick-start production-ready
```

Compare two plans side-by-side.

### Interactive Wizard (NEW)

```
speckit.plans --wizard
```

Launch interactive wizard to create a custom quality plan step-by-step.

The wizard guides you through:
1. **Basic Information**: Plan ID, name, description, duration
2. **Category Selection**: Choose from general, production, security, performance, stability, improvement, ci_cd
3. **Loop Configuration**: Criteria, iterations, thresholds, quality modes
4. **Quality Goals**: Add specific targets and objectives
5. **Gate Policy**: Configure quality gates for deployment
6. **Priority Profile**: Set category weights and cascade strategy
7. **Review**: Confirm before creating the plan

```
speckit.plans --wizard --plan-id my-custom-plan
```

Start wizard with pre-configured plan ID.

### Quick Create

```
speckit.plans --create "My Plan" --category production --strict
```

Create a quality plan with smart defaults (non-interactive).

Parameters:
- `--name <name>`: Plan name (required)
- `--category <cat>`: Plan category (default: general)
- `--strict`: Enable strict mode (default: false)
- `--iterations <n>`: Max iterations (default: 4)

### Save Custom Plan

```
speckit.plans --save my-plan --name "My Custom Plan" --description "..."
```

Save a custom quality plan for reuse.

### Export/Import Plans

```
speckit.plans --export production-ready --output ./production-plan.yml
```

Export a plan to a file for team sharing.

```
speckit.plans --import ./team-plan.yml --id team-shared
```

Import a plan from a file.

### JSON Output

```
speckit.plans --json
```

Output all plans in JSON format for CI/CD integration.

```
speckit.plans --show production-ready --json
```

Output specific plan details in JSON format.

## Built-in Quality Plan Presets

| Plan ID | Name | Category | Duration | Description |
|---------|------|----------|----------|-------------|
| `quick-start` | Quick Start | general | 1-2 days | Basic quality checks for new projects |
| `production-ready` | Production Ready | production | 1-2 weeks | Comprehensive checks for production deployment |
| `continuous-improvement` | Continuous Improvement | improvement | Ongoing | Ongoing quality enhancement with progressive targets |
| `security-focus` | Security Focus | security | 1-2 weeks | Security-first quality plan for sensitive data |
| `performance-focus` | Performance Focus | performance | 1 week | Performance-optimized quality plan |
| `stability` | Stability | stability | Ongoing | Maintain quality standards and consistency |
| `aggressive` | Aggressive Improvement | improvement | 2-3 weeks | Rapid quality improvement with high targets |
| `ci-cd` | CI/CD Integration | ci_cd | Per pipeline | Quality plan optimized for CI/CD pipelines |

## Plan Details

### Quick Start

Best for: New projects, onboarding, getting started quickly

- **Iterations**: 2
- **Thresholds**: A=0.7, B=0.8
- **Criteria**: backend, frontend
- **Goals**: Initial Quality Baseline (0.75)
- **Gate**: development
- **Profile**: balanced

### Production Ready

Best for: Production deployment, comprehensive validation

- **Iterations**: 5
- **Thresholds**: A=0.85, B=0.9
- **Criteria**: backend, frontend, security, testing, performance
- **Goals**:
  - Production Quality Score (0.9)
  - Zero Critical Issues
  - High Test Coverage (0.85)
- **Gate**: production
- **Profile**: criticality-focused

### Continuous Improvement

Best for: Agile teams, ongoing quality enhancement

- **Iterations**: 4
- **Thresholds**: A=0.8, B=0.85
- **Criteria**: backend, frontend, testing, docs
- **Goals**:
  - Steady Quality Growth (5% improvement)
  - Documentation Coverage (0.8)
- **Gate**: staging
- **Profile**: balanced

### Security Focus

Best for: Applications handling sensitive data

- **Iterations**: 6
- **Thresholds**: A=0.9, B=0.95
- **Criteria**: security, backend, infrastructure
- **Goals**:
  - Zero Security Vulnerabilities (1.0)
  - Secure Infrastructure (0.95)
- **Gate**: production
- **Profile**: security-first

### Performance Focus

Best for: High-traffic applications

- **Iterations**: 5
- **Thresholds**: A=0.8, B=0.85
- **Criteria**: performance, backend, database, infrastructure
- **Goals**:
  - Optimal Performance (0.85)
  - Database Efficiency (0.85)
- **Gate**: staging
- **Profile**: performance-focused

### Stability

Best for: Maintaining quality standards

- **Iterations**: 3
- **Thresholds**: A=0.85, B=0.85
- **Criteria**: backend, frontend, testing
- **Goals**:
  - Consistent Quality (<5% variance)
  - High Reliability (0.88)
- **Gate**: staging
- **Profile**: balanced

### Aggressive Improvement

Best for: Rapid quality improvement sprints

- **Iterations**: 7
- **Thresholds**: A=0.9, B=0.92
- **Criteria**: All quality categories
- **Goals**:
  - Excellence Target (0.92)
  - All Categories Strong (100% pass rate)
  - Rapid Improvement (10% per sprint)
- **Gate**: production
- **Profile**: quality-first
- **Features**: Auto-goal suggestions enabled (optimistic)

### CI/CD Integration

Best for: CI/CD pipelines, automated checks

- **Iterations**: 2
- **Thresholds**: A=0.8, B=0.85
- **Criteria**: backend, frontend, testing
- **Goals**: Gate Passing (0.85)
- **Gate**: CI (auto-apply)
- **Profile**: balanced
- **Output**: JSON report for pipeline integration

## YAML Format

Quality plans are stored in YAML format:

```yaml
plan_id: production-ready
name: Production Ready
description: Comprehensive quality checks for production deployment.
plan_type: preset
category: production

loop_config:
  name: production-loop
  description: Production-ready quality loop configuration
  criteria:
    - backend
    - frontend
    - security
    - testing
    - performance
  max_iterations: 5
  threshold_a: 0.85
  threshold_b: 0.9
  strict_mode: true

goals:
  - name: Production Quality Score
    description: Achieve production-ready quality score
    goal_type: target_score
    target_value: 0.9

  - name: Zero Critical Issues
    description: No critical issues allowed
    goal_type: target_score
    target_value: 1.0
    category: security

  - name: High Test Coverage
    description: Maintain high test coverage
    goal_type: category_target
    target_value: 0.85
    category: testing

gate_preset: production
priority_profile: criticality-focused
estimated_duration: 1-2 weeks

tags:
  - production
  - comprehensive
  - deployment
```

## Examples

### Get Started with Quick Start

```
# See what quick-start offers
speckit.plans --show quick-start

# Apply it to your project
speckit.plans --apply quick-start

# Run quality loop with the applied configuration
speckit.loop
```

### Find the Right Plan

```
# Get recommendations for production deployment
speckit.plans --recommend production deployment

# Compare two plans
speckit.plans --compare production-ready security-focus

# List only production plans
speckit.plans --category production
```

### Team Collaboration

```
# Export a plan for team sharing
speckit.plans --export production-ready --output ./team-standards/production.yml

# Share the file, then import on another machine
speckit.plans --import ./team-standards/production.yml --id team-production

# Now use the team-shared plan
speckit.plans --apply team-production
```

### CI/CD Integration

```
# Apply CI/CD plan (generates JSON report)
speckit.plans --apply ci-cd

# Run quality loop (outputs quality-report.json)
speckit.loop

# Use JSON report in CI pipeline
if [ -f quality-report.json ]; then
  echo "Quality report generated"
fi
```

## CLI Options Summary

| Option | Description |
|--------|-------------|
| (no args) | List all plans |
| `--category <cat>` | Filter by category |
| `--show <plan-id>` | Show plan details |
| `--apply <plan-id>` | Apply plan to project |
| `--recommend <keywords>` | Get recommendations |
| `--compare <id1> <id2>` | Compare two plans |
| `--wizard` | Launch interactive wizard |
| `--plan-id <id>` | Pre-configure plan ID for wizard |
| `--create <name>` | Quick create with defaults |
| `--category <cat>` | Category for quick create |
| `--strict` | Enable strict mode (quick create) |
| `--iterations <n>` | Max iterations (quick create) |
| `--save <plan-id>` | Save custom plan |
| `--name <name>` | Plan name (for --save) |
| `--description <desc>` | Plan description (for --save) |
| `--export <plan-id>` | Export plan to file |
| `--import <path>` | Import plan from file |
| `--output <path>` | Output file path |
| `--json` | JSON output format |

## See Also

- `/speckit.configs` — Loop configuration management
- `/speckit.goals` — Quality goals system
- `/speckit.gates` — Quality gate policies
- `/speckit.profiles` — Priority profiles
- `/speckit.loop` — Run quality loop
