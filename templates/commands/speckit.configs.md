# Quality Loop Configs Commands

Save, load, and manage quality loop configurations for consistent, repeatable quality checks.

## Overview

Quality loop configurations allow you to:
- **Save** your quality loop parameters (criteria, thresholds, profiles, outputs, gates, etc.) with a name
- **Load** saved configurations to run consistent quality checks
- **Share** configurations with your team via export/import
- **Use presets** for common quality scenarios (production, CI/CD, development, etc.)

## Commands

### `speckit configs save`

Save a new quality loop configuration.

```bash
speckit configs save <name> --description "<desc>" [options]
```

**Required Arguments:**
- `<name>` - Configuration name (must be unique, use kebab-case)
- `--description` - Configuration description

**Options:**
- `--criteria <list>` - Comma-separated criteria templates
- `--max-iterations <n>` - Max iterations (default: 4)
- `--threshold-a <0.0-1.0>` - Phase A threshold (default: 0.8)
- `--threshold-b <0.0-1.0>` - Phase B threshold (default: 0.9)
- `--priority-profile <name>` - Priority profile name
- `--strategy <strategy>` - Cascade merge strategy
- `--strict` - Enable strict quality mode
- `--lenient` - Enable lenient quality mode
- `--html-output <path>` - HTML report output path
- `--markdown-output <path>` - Markdown report output path
- `--json-output <path>` - JSON report output path
- `--include-categories <list>` - Include specific categories
- `--exclude-categories <list>` - Exclude specific categories
- `--gate-preset <name>` - Gate policy preset
- `--gate-policy <name>` - Custom gate policy name
- `--gate-policy-auto` - Enable auto gate policy recommendation
- `--gate-goal-mode <mode>` - Goal-based gate mode
- `--auto-update-goals` - Auto-update goals during loop
- `--suggest-goals` - Enable automatic goal suggestions (Exp 78)
- `--auto-apply-goals` - Automatically apply top goal suggestion (requires --suggest-goals)
- `--goal-strategy <strategy>` - Goal suggestion strategy (optimistic, conservative, balanced, maintenance, stabilizing, catch-up)
- `--author <name>` - Configuration author
- `--tags <list>` - Comma-separated tags

**Examples:**

```bash
# Save a production-quality configuration
speckit configs save production-strict \
  --description "Strict quality checks for production deployment" \
  --criteria backend,security,performance \
  --max-iterations 6 \
  --threshold-a 0.85 \
  --threshold-b 0.95 \
  --priority-profile web-app \
  --strict \
  --html-output .speckit/quality-report.html \
  --json-output .speckit/quality-report.json \
  --gate-preset production \
  --author "QA Team" \
  --tags production,strict,comprehensive

# Save a quick development configuration
speckit configs save dev-quick \
  --description "Quick quality check for development" \
  --criteria backend \
  --max-iterations 2 \
  --lenient \
  --gate-preset development \
  --tags development,quick
```

### `speckit configs load`

Load and run a saved configuration.

```bash
speckit configs load <name>
```

**Arguments:**
- `<name>` - Configuration name (preset or custom)

**Examples:**

```bash
# Load a preset configuration
speckit configs load production-strict

# Load a custom configuration
speckit configs load my-team-standard

# Load a development configuration
speckit configs load dev-quick
```

### `speckit configs list`

List all available configurations.

```bash
speckit configs list [options]
```

**Options:**
- `--format <text|json>` - Output format (default: text)
- `--filter <tag>` - Filter by tag

**Examples:**

```bash
# List all configurations
speckit configs list

# List only production-related configs
speckit configs list --filter production

# List as JSON
speckit configs list --format json
```

**Output (text format):**

```
## Loop Configurations

### Presets

🔹 **production-strict**
   Strict quality checks for production deployment with comprehensive reporting
   Criteria: backend, security, performance, testing
   Tags: `production` `strict` `comprehensive`

🔹 **ci-standard**
   Standard CI/CD quality gate with JSON output for automation
   Criteria: backend, testing
   Tags: `ci` `automation` `standard`

🔹 **development-quick**
   Quick quality check for development iterations
   Criteria: backend
   Tags: `development` `quick` `lenient`

### Custom Configurations

**my-team-standard** (by QA Team, updated 2026-03-13T10:30:00)
   Team standard quality checks for all code reviews
   Criteria: backend, frontend, security
   Tags: `team` `standard`
```

### `speckit configs show`

Show detailed information about a configuration.

```bash
speckit configs show <name>
```

**Arguments:**
- `<name>` - Configuration name

**Examples:**

```bash
# Show preset details
speckit configs show production-strict

# Show custom config details
speckit configs show my-team-standard
```

**Output:**

```
## Configuration: production-strict

**Description:** Strict quality checks for production deployment with comprehensive reporting

### Core Parameters
- **Criteria:** backend, security, performance, testing
- **Max Iterations:** 6
- **Threshold A:** 0.85
- **Threshold B:** 0.95

### Priority Profile
- **Profile:** web-app+mobile-app
- **Strategy:** max

### Quality Mode
- **Strict Mode:** Enabled

### Output Formats
- HTML: .speckit/quality-report.html
- Markdown: .speckit/quality-report.md
- JSON: .speckit/quality-report.json

### Gate Policy
- **Preset:** production

**Tags:** production, strict, comprehensive

### Command Equivalent
```bash
/speckit.loop --criteria backend,security,performance,testing --max-iterations 6 --threshold-a 0.85 --threshold-b 0.95 --priority-profile web-app+mobile-app --strategy max --strict --html-output .speckit/quality-report.html --markdown-output .speckit/quality-report.md --json-output .speckit/quality-report.json --gate-preset production
```
```

### `speckit configs delete`

Delete a custom configuration.

```bash
speckit configs delete <name>
```

**Arguments:**
- `<name>` - Configuration name (cannot delete presets)

**Note:** Preset configurations cannot be deleted.

### `speckit configs export`

Export a configuration to a file for sharing.

```bash
speckit configs export <name> <output-path>
```

**Arguments:**
- `<name>` - Configuration name
- `<output-path>` - Output file path (.yml)

**Examples:**

```bash
# Export a custom configuration
speckit configs export my-team-standard ./team-config.yml

# Export a preset as a template
speckit configs export production-strict ./production-template.yml
```

### `speckit configs import`

Import a configuration from a file.

```bash
speckit configs import <file-path> [--name <new-name>]
```

**Arguments:**
- `<file-path>` - Path to config file (.yml)
- `--name` - Optional new name for the configuration

**Examples:**

```bash
# Import with original name
speckit configs import ./team-config.yml

# Import with a new name
speckit configs import ./production-template.yml --name my-production
```

### `speckit configs recommend`

Get a configuration recommendation based on your task description.

```bash
speckit configs recommend "<task description>"
```

**Examples:**

```bash
# Get recommendation for production deployment
speckit configs recommend "I need to deploy my API to production"

# Get recommendation for frontend work
speckit configs recommend "Building a React dashboard with UI components"

# Get recommendation for mobile app
speckit configs recommend "Developing a mobile app for iOS and Android"
```

## Built-in Presets

The following preset configurations are included:

| Preset | Description | Use Case |
|--------|-------------|----------|
| `production-strict` | Strict quality checks with comprehensive reporting | Production deployment |
| `ci-standard` | Standard CI/CD gate with JSON output | CI/CD pipelines |
| `development-quick` | Quick checks for rapid iteration | Development |
| `security-focused` | Security-focused with high thresholds | Security reviews |
| `frontend-qa` | Comprehensive frontend QA | Frontend projects |
| `fullstack-comprehensive` | Complete full-stack checks | Full-stack apps |
| `api-focused` | API correctness and security | API projects |
| `mobile-app-qa` | Mobile app quality assurance | Mobile development |
| `data-pipeline` | Data pipeline quality checks | Data engineering |
| `ml-service` | ML/AI service quality checks | ML projects |
| `goal-driven-development` | **Goal-aware** with automatic suggestions and application (Exp 78) | Continuous improvement |
| `quality-improvement-focus` | **Goal-aware** with conservative suggestions for steady progress (Exp 78) | Quality improvement |
| `aggressive-quality-targets` | **Goal-aware** with optimistic suggestions for rapid improvement (Exp 78) | Ambitious teams |
| `stability-focused` | **Goal-aware** with stabilizing suggestions to maintain quality (Exp 78) | Maintenance mode |
| `goal-aware-ci` | **Goal-aware** CI/CD with goal tracking and suggestions (Exp 78) | CI/CD with goals |

## Configuration File Format

Configurations are stored in YAML format:

```yaml
name: my-production-config
description: Production quality checks for my project
author: QA Team
tags:
  - production
  - strict
created_at: 2026-03-13T10:30:00
updated_at: 2026-03-13T10:30:00

# Core parameters
criteria:
  - backend
  - security
  - performance
max_iterations: 6
threshold_a: 0.85
threshold_b: 0.95

# Priority and cascade
priority_profile: web-app+mobile-app
cascade_strategy: max

# Quality modes
strict_mode: true
lenient_mode: false

# Output formats
html_output: .speckit/quality-report.html
markdown_output: .speckit/quality-report.md
json_output: .speckit/quality-report.json

# Category filtering
include_categories: null
exclude_categories: null

# Gate policies
gate_preset: production
gate_policy: null
gate_policy_auto: false
gate_goal_mode: null
auto_update_goals: false

# Exp 78: Goal suggestion settings
suggest_goals: false
auto_apply_goals: false
goal_suggestion_strategy: null
```

## Use Cases

### Team Standardization

Create a team standard configuration and share it:

```bash
# Create the configuration
speckit configs save team-standard \
  --description "Team standard quality checks" \
  --criteria backend,frontend,security \
  --gate-preset staging \
  --author "Backend Team"

# Export it
speckit configs export team-standard ./team-standard.yml

# Share with team (add to version control)
git add team-standard.yml
git commit -m "Add team quality config"
```

Team members can then import and use it:

```bash
speckit configs import ./team-standard.yml
speckit configs load team-standard
```

### CI/CD Integration

Use a preset configuration in CI/CD:

```yaml
# .github/workflows/quality-check.yml
- name: Run Quality Check
  run: |
    pip install speckit
    speckit configs load ci-standard
```

### Environment-Specific Configs

Create different configurations for different environments:

```bash
# Development
speckit configs save dev-config \
  --description "Development quality checks" \
  --lenient \
  --gate-preset development

# Staging
speckit configs save staging-config \
  --description "Staging quality checks" \
  --gate-preset staging

# Production
speckit configs save prod-config \
  --description "Production quality checks" \
  --strict \
  --gate-preset production
```

## Python API

You can also use the configuration API directly:

```python
from specify_cli.quality import (
    save_loop_config,
    load_loop_config,
    list_loop_configs,
    delete_loop_config,
    format_config_summary,
    format_config_details,
    recommend_config,
)

# Save a configuration
config = save_loop_config(
    name="my-config",
    description="My custom configuration",
    criteria=["backend", "security"],
    max_iterations=4,
    strict_mode=True,
    gate_preset="production",
    author="John Doe",
    tags=["custom", "strict"],
)

# Load a configuration
config = load_loop_config("production-strict")
if config:
    print(f"Loaded: {config.name}")
    print(f"Description: {config.description}")
    print(f"Criteria: {config.criteria}")

# List all configurations
configs = list_loop_configs()
for config in configs:
    print(f"{config['name']}: {config['description']}")

# Get recommendation
recommended = recommend_config("I need to deploy my API to production")
print(f"Recommended: {recommended.name}")

# Delete a configuration
deleted = delete_loop_config("my-config")
```

## Configuration Storage

Configurations are stored in:

```
.speckit/loop-configs/
├── index.json              # Configuration index
├── production-strict.yml   # Preset (read-only reference)
├── my-config.yml           # Custom configuration
└── team-standard.yml       # Team configuration
```

## Notes

- **Preset configurations** cannot be modified or deleted
- **Custom configurations** are stored in the project's `.speckit/loop-configs/` directory
- Configurations support **all quality loop parameters** including criteria, thresholds, profiles, outputs, and gates
- Use `--tags` to organize configurations for easier discovery
- Exported configurations can be **version controlled** for team sharing
- The `recommend` command uses **keyword matching** to suggest the best preset for your task
