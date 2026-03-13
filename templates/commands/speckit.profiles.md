---
description: Manage and inspect priority profiles for quality evaluation
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

Priority profiles allow you to customize quality evaluation for different project types.
Each profile has domain multipliers that boost or reduce the importance of specific rule categories.

**Usage**: `/speckit.profiles <mode> [arguments]`

## Mode Detection

Parse arguments to determine mode:
- `list` → List mode (show all profiles)
- `show <name>` → Show mode (details of specific profile)
- `cascade <profile1+profile2+...>` → Cascade mode (show merged cascade profile)
- `compare <name1> <name2> [...]` → Compare mode (compare multiple profiles)
- `diff <profile1> <profile2>` → Diff mode (highlight differences between two profiles)
- `recommend "<description>"` → Recommend mode (suggest profile based on description)
- `recommend-intelligent "<description>" [top_n]` → Intelligent recommend mode (Top-N recommendations with explanations)
- `recommend-cascade "<description>"` → Recommend cascade mode (suggest cascade based on description)
- `detect` → Detect mode (auto-detect from project files)
- `domains` → Domains mode (list all domain tags)
- `strategies` → Strategies mode (list merge strategies)
- `presets` → Presets mode (list cascade presets)
- `compare-strategies <cascade>` → Compare-Strategies mode (compare merge strategies for cascade)
- `custom` → Custom mode (show custom profiles info)
- `validate` → Validate mode (validate custom profiles)
- `wizard` → **NEW** Wizard mode (interactive profile selection guide)
- No argument → Defaults to `list`

**JSON Output Flag:**
Add `--json` to any mode to get JSON output instead of formatted text:
- `/speckit.profiles list --json`
- `/speckit.profiles show web-app --json`
- `/speckit.profiles validate --json`

## Mode: List

**Usage**: `/speckit.profiles list`

Display all available priority profiles with their descriptions and emphasized domains.

**Output format:**
```
=== Priority Profiles ===

• default
  Default profile with neutral multipliers (all 1.0)

• web-app
  Web application profile: emphasizes web, API, and auth
  Emphasizes: web (1.5x), api (1.3x), auth (1.5x)

• mobile-app
  Mobile application profile: emphasizes mobile, API, and auth
  Emphasizes: mobile (2.0x), api (1.5x), auth (1.5x)

...
```

**JSON Output** (Exp 26):
Add `--json` flag to get JSON output for programmatic use:
```bash
/speckit.profiles list --json
```

**JSON format:**
```json
{
  "profiles": [
    {
      "name": "web-app",
      "is_custom": false,
      "description": "Web application profile: emphasizes web, API, and auth",
      "multipliers": {
        "web": 1.5,
        "api": 1.3,
        "auth": 1.5,
        ...
      }
    }
  ],
  "total": 15
}
```

**Use cases:**
- **Scripting** - Parse profiles in automation scripts
- **Tools integration** - Feed profile data into DevOps tools
- **Documentation generation** - Auto-generate profile documentation

## Mode: Show

**Usage**: `/speckit.profiles show <profile_name>`

Display detailed information about a specific profile.

**Output format:**
```
=== Profile: web-app ===

Description: Web application profile: emphasizes web, API, and auth

Domain Multipliers:
  web: 1.5x - Frontend web applications (React, Vue, Angular)
  api: 1.3x - REST/GraphQL APIs and services
  auth: 1.5x - Authentication and authorization
  data: 1.0x - Database, data pipelines, and data processing
  ...

Usage in quality loop:
  /speckit.loop --criteria backend --priority-profile web-app
```

**JSON Output** (Exp 26):
Add `--json` flag to get JSON output for programmatic use:
```bash
/speckit.profiles show web-app --json
```

**JSON format:**
```json
{
  "name": "web-app",
  "is_custom": false,
  "description": "Web application profile: emphasizes web, API, and auth",
  "multipliers": {
    "web": 1.5,
    "api": 1.3,
    "auth": 1.5,
    "data": 1.0,
    ...
  }
}
```

**Use cases:**
- **Profile validation** - Verify profile configuration in CI/CD
- **Documentation** - Generate profile reference docs
- **Tool integration** - Import profile data into external tools

## Mode: Cascade

**Usage**: `/speckit.profiles cascade <profile1+profile2+...>`

Display information about a cascade (merged) profile that combines multiple priority profiles.

**Cascade syntax:**
- Basic: Combine profiles using `+` separator: `web-app+mobile-app`
- Weighted: Add weights with `:` separator: `web-app:2+mobile-app:1` (2x weight on web-app)
- All source profiles must exist
- Multipliers are merged using the specified strategy (default: average)

**Merge strategies:**
- `average` (default) - Average multipliers (balanced approach)
- `max` - Take maximum multiplier (strict quality enforcement)
- `min` - Take minimum multiplier (lenient quality requirements)
- `weighted` - Weighted average (requires weights in cascade string)

**Examples:**
```bash
# Basic cascade (average strategy)
/speckit.profiles cascade web-app+mobile-app
/speckit.profiles cascade graphql-api+ml-service

# Weighted cascade (web-app gets 2x weight)
/speckit.profiles cascade web-app:2+mobile-app:1

# Triple cascade
/speckit.profiles cascade web-app+mobile-app+ml-service
```

**Output format:**
```
### Cascade Profile: web-app:2+mobile-app:1

Source profiles (2):
  - web-app
  - mobile-app
  Weights: web-app=2.00, mobile-app=1.00
  Strategy: weighted

Merged multipliers (weighted strategy):
  • api: 1.37x
  • auth: 1.50x
  • web: 1.27x
  • mobile: 1.20x
  • data: 1.07x

Source profile breakdown:
  web: web-app=1.5x, mobile-app=0.8x → 1.27x
  mobile: web-app=0.8x, mobile-app=2.0x → 1.20x
  api: web-app=1.3x, mobile-app=1.5x → 1.37x
```

**JSON Output** (Exp 27):
Add `--json` flag to get JSON output for programmatic use:

```bash
/speckit.profiles cascade web-app+mobile-app --json
/speckit.profiles cascade web-app:2+mobile-app:1 --json --strategy weighted
```

Example JSON output:
```json
{
  "cascade_str": "web-app+mobile-app",
  "is_cascade": true,
  "source_profiles": ["web-app", "mobile-app"],
  "merged_multipliers": {
    "web": 1.15,
    "mobile": 1.4,
    "api": 1.4
  },
  "description": "Cascade profile: web-app + mobile-app (average strategy)",
  "profile_count": 2,
  "strategy": "average"
}
```

**Use cases for cascade profiles:**
- **Fullstack apps**: `web-app+mobile-app` - equal emphasis on web and mobile
- **Web-first fullstack**: `web-app:2+mobile-app:1` - 2x weight on web
- **Web + ML**: `web-app+ml-service` - combines web frontend with ML data focus
- **GraphQL + Mobile**: `graphql-api+mobile-app` - GraphQL API with mobile client
- **Microservice + ML**: `microservice+ml-service` - distributed ML service
- **Hybrid projects**: Any combination of profiles for complex projects

**Integration with quality loop:**
```bash
# Use cascade profile in quality loop
/speckit.loop --criteria frontend,backend --priority-profile web-app+mobile-app

# Weighted cascade (web-first)
/speckit.loop --criteria frontend,backend --priority-profile web-app:2+mobile-app:1

# Auto-detection can be combined with cascade
/speckit.loop --criteria backend,api --priority-profile graphql-api+ml-service
```

**Cascade profile resolution:**
1. Parse cascade string (e.g., `web-app:2+mobile-app:1`)
2. Extract weights if specified (defaults to 1.0)
3. Validate all source profiles exist
4. Merge multipliers using specified strategy
5. Return merged profile for use in evaluation

## Mode: Strategies

**Usage**: `/speckit.profiles strategies [subcommand] [arguments]`

Manage and inspect merge strategies for cascade profiles.

**Subcommands:**
- `list` - List all strategies (default)
- `show <name>` - Show details of a specific strategy
- `recommend <use_case>` - Recommend strategy based on use case
- `validate <name>` - Validate a strategy name
- No subcommand → Defaults to `list`

### Strategies Subcommand: List

**Usage**: `/speckit.profiles strategies list`

Display all available merge strategies with detailed information.

**Output format:**
```
### Available Merge Strategies

Merge strategies determine how multipliers are combined when using cascade profiles.

#### average **(default)**
**Aliases:** avg, mean, bal
**Description:** Average multipliers (balanced approach)
**Use case:** Equal emphasis on all source profiles

**Behavior:** Calculates arithmetic mean of all multipliers

**When to use this strategy:**
- Working with multiple equally important profiles
- Balanced quality requirements across domains
- Default choice when uncertain

**Characteristics:**
- **result_range:** Moderate
- **quality_enforcement:** Balanced
- **iteration_speed:** Normal
- **noise_level:** Low

**Examples:**
- web-app (1.5) + mobile-app (2.0) → web: 1.15, mobile: 1.40
- Suitable for fullstack apps with balanced requirements

...

[Similar detailed output for max, min, weighted]
```

### Strategies Subcommand: Show

**Usage**: `/speckit.profiles strategies show <strategy_name>`

Display detailed information about a specific merge strategy.

**Example:**
```bash
/speckit.profiles strategies show average
/speckit.profiles strategies show max
/speckit.profiles strategies show min
/speckit.profiles strategies show weighted

# Aliases work too
/speckit.profiles strategies show avg
/speckit.profiles strategies show strict
```

**Output format:**
```
### Strategy: average

**Description:** Average multipliers (balanced approach)

**Aliases:** avg, mean, bal

**Use Case:** Equal emphasis on all source profiles

**Behavior:** Calculates arithmetic mean of all multipliers

**When to use this strategy:**
- Working with multiple equally important profiles
- Balanced quality requirements across domains
- Default choice when uncertain

**Characteristics:**
- **result_range:** Moderate
- **quality_enforcement:** Balanced
- **iteration_speed:** Normal
- **noise_level:** Low

**Examples:**
- web-app (1.5) + mobile-app (2.0) → web: 1.15, mobile: 1.40
- Suitable for fullstack apps with balanced requirements
```

### Strategies Subcommand: Recommend

**Usage**: `/speckit.profiles strategies recommend <use_case>`

Get a strategy recommendation based on your use case.

**Supported use cases:**
- `enterprise` - Enterprise applications with strict requirements
- `production` - Production systems with maximum quality standards
- `compliance` - Compliance-critical projects (HIPAA, PCI-DSS)
- `mvp` - MVP development with faster iteration
- `prototype` - Prototypes with rapid iteration
- `internal` - Internal tools with lenient requirements
- `fullstack` - Fullstack apps with balanced requirements
- `hybrid` - Hybrid projects with multi-domain approach
- `web-first` - Web-first apps with web emphasis
- `mobile-first` - Mobile-first apps with mobile emphasis
- `balanced` - Balanced requirements across domains
- `fast` - Fast iteration with lenient gates
- `strict` - Strict requirements with maximum enforcement
- `lenient` - Lenient approach with minimal enforcement
- `default` - Default scenario (safe choice)

**Examples:**
```bash
/speckit.profiles strategies recommend enterprise
/speckit.profiles strategies recommend mvp
/speckit.profiles strategies recommend production
/speckit.profiles strategies recommend fullstack
```

**Output format:**
```
### Strategy Recommendation

**Use Case:** enterprise

**Recommended Strategy:** max

**Reason:** Enterprise applications require strict quality enforcement

**Alternatives:**
- average

**Strategy Details:**
[Full strategy info for max]
```

### Strategies Subcommand: Validate

**Usage**: `/speckit.profiles strategies validate <strategy_name>`

Validate a merge strategy name (or alias).

**Examples:**
```bash
/speckit.profiles strategies validate average
/speckit.profiles strategies validate avg
/speckit.profiles strategies validate invalid_name
```

**Output format:**
```
✅ Valid strategy: average
Canonical name: average
Aliases: avg, mean, bal
```

Or for invalid:
```
❌ Invalid strategy: 'invalid_name'
Strategy 'invalid_name' not found. Available: average, max, min, weighted
```

### Strategy Selection Guide

| Strategy | Best For | Quality Level | Iteration Speed |
|----------|----------|---------------|-----------------|
| `average` (avg) | Most hybrid projects, balanced requirements | Moderate | Normal |
| `max` (strict) | Enterprise, production, compliance | Highest | Slowest |
| `min` (lenient) | MVP, prototypes, internal tools | Lowest | Fastest |
| `weighted` (wgt) | Asymmetric requirements (web-first, mobile-first) | Flexible | Normal |

**Quick decision flow:**
1. Need strict quality? → Use `max`
2. Fast iteration/MVP? → Use `min`
3. Web-first or mobile-first? → Use `weighted` with profile weights
4. Not sure? → Use `average` (default)

## Mode: Presets

**Usage**: `/speckit.profiles presets [category]`

Display predefined cascade profile presets for common hybrid project types.

**Without category (all presets):**
```bash
/speckit.profiles presets
```

**With category filter (Exp 22):**
```bash
/speckit.profiles presets fullstack
/speckit.profiles presets hybrid
/speckit.profiles presets backend
/speckit.profiles presets strategy
```

**Preset Categories:**
- `fullstack` - Full-stack applications (web + mobile + API)
- `hybrid` - Hybrid projects (web + ML, mobile + ML)
- `backend` - Backend-focused (API + data, microservice + ML)
- `strategy` - Strategy presets (conservative, aggressive)

**All Named Presets (Exp 22):**
- `fullstack-balanced` - Equal emphasis on web and mobile
- `fullstack-web-first` - Web-focused fullstack (2x weight on web)
- `fullstack-mobile-first` - **NEW** Mobile-focused fullstack (2x weight on mobile)
- `web-ml` - Web application with ML backend
- `mobile-ml` - Mobile-first ML application
- `api-data` - API with data processing pipeline
- `graphql-web` - GraphQL API with web frontend
- `graphql-mobile` - **NEW** GraphQL API with mobile client
- `microservice-ml` - Distributed ML service
- `conservative` - Conservative merging (min strategy)
- `aggressive` - Aggressive merging (max strategy)
- `balanced-fullstack` - **NEW** Balanced fullstack with API emphasis

**Using named presets directly (Exp 22):**

Named presets are now **first-class profiles** - you can use them directly by name:

```bash
# Use named preset in quality loop
/speckit.loop --priority-profile fullstack-balanced --criteria frontend,backend
/speckit.loop --priority-profile web-ml --criteria frontend,api
/speckit.loop --priority-profile mobile-ml --criteria mobile,api
/speckit.loop --priority-profile conservative --criteria backend

# Named presets work with all profile commands
/speckit.profiles show fullstack-balanced
/speckit.profiles show web-ml
/speckit.profiles cascade fullstack-balanced  # Shows expanded cascade
```

**Strategy Aliases (Exp 22):**

When using cascade profiles, you can now use short strategy aliases:

| Alias     | Canonical Strategy | Description                      |
|-----------|-------------------|----------------------------------|
| `avg`     | `average`         | Average multipliers (default)     |
| `mean`    | `average`         | Average multipliers               |
| `bal`     | `average`         | Balanced approach                 |
| `wgt`     | `weighted`        | Weighted average                  |
| `custom`  | `weighted`        | Custom weights                    |
| `strict`  | `max`             | Maximum multiplier (strict)       |
| `lenient` | `min`             | Minimum multiplier (lenient)      |

**Examples:**
```python
# In code
from specify_cli.quality import normalize_strategy_alias, expand_named_preset

# Normalize strategy aliases
strategy = normalize_strategy_alias("avg")     # Returns: "average"
strategy = normalize_strategy_alias("wgt")     # Returns: "weighted"
strategy = normalize_strategy_alias("strict")  # Returns: "max"

# Expand named presets to cascade strings
cascade = expand_named_preset("fullstack-balanced")
# Returns: "web-app:1+mobile-app:1"

cascade = expand_named_preset("conservative")
# Returns: "web-app+mobile-app" (with min strategy)
```

**Output format for presets mode:**
```
=== Named Cascade Presets ===

#### Fullstack
fullstack-balanced
  Cascade: web-app:1+mobile-app:1
  Strategy: average
  Description: Equal emphasis on web and mobile
  Use case: Applications with both web and mobile clients

fullstack-web-first
  Cascade: web-app:2+mobile-app:1
  Strategy: weighted
  Description: Web-focused fullstack (2x weight on web)
  Use case: Primary web UI with mobile companion app

fullstack-mobile-first
  Cascade: mobile-app:2+web-app:1
  Strategy: weighted
  Description: Mobile-focused fullstack (2x weight on mobile)
  Use case: Primary mobile app with web dashboard

#### Hybrid
web-ml
  Cascade: web-app+ml-service
  Strategy: average
  Description: Web application with ML backend
  Use case: Web apps using AI/ML features

...
```

**Using presets:**
Named presets simplify cascade profile usage:
- Copy preset name directly: `fullstack-balanced` instead of `web-app:1+mobile-app:1`
- Presets include strategy configuration
- Category filtering helps find relevant presets

```bash
# Fullstack web-first (from preset)
/speckit.loop --priority-profile fullstack-web-first --criteria frontend,backend

# Web + ML (from preset)
/speckit.loop --priority-profile web-ml --criteria frontend,api

# Conservative quality (from preset)
/speckit.loop --priority-profile conservative --criteria backend
```

## Mode: Compare

**Usage**: `/speckit.profiles compare <profile1> <profile2> [...]`

Compare multiple profiles side-by-side.

**Output format:**
```
=== Profile Comparison: web-app vs mobile-app vs default ===

Domain           | web-app  | mobile-app | default
-----------------|----------|------------|--------
web              | 1.5x     | 0.8x       | 1.0x
api              | 1.3x     | 1.5x       | 1.0x
mobile           | 0.8x     | 2.0x       | 1.0x
auth             | 1.5x     | 1.5x       | 1.0x
...
```

**JSON Output** (Exp 27):
Add `--json` flag to get JSON output for programmatic use:

```bash
/speckit.profiles compare web-app mobile-app --json
```

Example JSON output:
```json
{
  "comparison": {
    "profiles": ["web-app", "mobile-app"],
    "domains": {
      "web": {"web-app": 1.5, "mobile-app": 0.8},
      "mobile": {"web-app": 0.8, "mobile-app": 2.0}
    }
  },
  "profile_count": 2,
  "domain_count": 10
}
```

## Mode: Diff

**Usage**: `/speckit.profiles diff <profile1> <profile2>`

Compare two profiles and highlight differences.

**Output format:**
```
=== Profile Diff: web-app vs mobile-app ===

Differences (7 domains):

  mobile: 0.8x → 2.0x (↑ 1.2)
  web: 1.5x → 0.8x (↓ 0.7)
  data: 1.0x → 1.2x (↑ 0.2)
  infrastructure: 0.8x → 0.8x (no change)
  ...

Similar domains: graphql, microservices
```

**JSON Output** (Exp 27):
Add `--json` flag to get JSON output for programmatic use:

```bash
/speckit.profiles diff web-app mobile-app --json
```

Example JSON output:
```json
{
  "diff": {
    "differences": {
      "mobile": {"web-app": 0.8, "mobile-app": 2.0, "change": "increase", "difference": 1.2},
      "web": {"web-app": 1.5, "mobile-app": 0.8, "change": "decrease", "difference": -0.7}
    },
    "similar": ["graphql", "microservices"],
    "difference_count": 7
  },
  "profile1": "web-app",
  "profile2": "mobile-app"
}
```

## Mode: Compare-Strategies (Exp 24)

**Usage**: `/speckit.profiles compare-strategies <cascade_string>`

**NEW** - Compare how different merge strategies (average, max, min, weighted) affect the cascade profile multipliers.

This command helps you understand the impact of different merge strategies BEFORE running the quality loop, enabling informed strategy selection.

**Features:**
- **Strategy comparison**: See multiplier values for each strategy side-by-side
- **Statistics**: Max, min, and average multipliers per strategy
- **Recommendations**: Get suggested strategy based on cascade characteristics
- **Visual highlights**: Significant values (> 1.3x) and reduced values (< 0.8x) are highlighted

**Example:**
```bash
# Compare strategies for fullstack cascade
/speckit.profiles compare-strategies web-app+mobile-app

# Compare strategies for web + ML hybrid
/speckit.profiles compare-strategies web-app+ml-service

# Compare strategies for weighted cascade
/speckit.profiles compare-strategies web-app:2+mobile-app:1
```

**Output format:**
```
### Strategy Comparison: web-app+mobile-app

Source profiles: web-app, mobile-app

## Multiplier Comparison by Strategy

Domain           average      max          min
-------------------------------------------------
api              1.40         1.50         1.30
auth             1.50         1.50         1.50
mobile           1.40         **2.00**     *0.80*
web              1.15         **1.50**     *0.80*
data             1.10         1.20         1.00
infrastructure   0.80         0.80         0.80
ml               0.50         0.50         0.50
graphql          1.20         1.20         1.20
microservices    1.00         1.00         1.00
async            1.20         1.20         1.20

## Strategy Statistics

average    : max=1.50x, min=0.50x, avg=1.13x
max        : max=2.00x, min=0.50x, avg=1.19x
min        : max=1.50x, min=0.50x, avg=1.05x

**Recommendation:** average (balanced approach)

## Strategy Descriptions

**average** (avg, mean, bal)
  - Average multipliers (balanced approach)
  - Use case: Equal emphasis on all source profiles

**max** (strict)
  - Take maximum multiplier
  - Use case: Strict quality enforcement across all domains

**min** (lenient)
  - Take minimum multiplier
  - Use case: Minimal quality requirements, faster iteration
```

**Understanding the output:**
- **Bold values** (e.g., `**2.00**`) indicate significantly boosted multipliers (> 1.3x)
- **Italic values** (e.g., `*0.80*`) indicate reduced multipliers (< 0.8x)
- **average strategy**: Balanced approach, takes average of source multipliers
- **max strategy**: Strict quality, takes highest multiplier from each domain
- **min strategy**: Lenient quality, takes lowest multiplier from each domain
- **weighted strategy**: Only shown if weights are in cascade string

**When to use each strategy:**
- **average** (recommended): Best for most hybrid projects with balanced priorities
- **max**: Use when you need strict quality across all emphasized domains (e.g., production-critical systems)
- **min**: Use for rapid prototyping or minimum viable quality (e.g., MVP development)

**Integration with quality loop:**
```bash
# After comparing strategies, use the recommended one
/speckit.loop --criteria frontend,backend --priority-profile web-app+mobile-app --strategy avg

# Use max strategy for strict quality
/speckit.loop --criteria frontend,backend --priority-profile web-app+mobile-app --strategy max
```

**Implementation:**
```python
from specify_cli.quality import PriorityProfilesManager, print_strategy_comparison

# Get comparison dict for programmatic use
comparison = PriorityProfilesManager.compare_strategies("web-app+mobile-app")
# Returns: {"cascade_str": "...", "strategies": {...}, "recommendation": "..."}

# Get formatted output for display
output = print_strategy_comparison("web-app+mobile-app")
print(output)

# Include weighted strategy if cascade has weights
output = print_strategy_comparison("web-app:2+mobile-app:1", include_weighted=True)
print(output)
```


**JSON Output** (Exp 25):
Add `--json` flag to get JSON output for programmatic use:
```bash
/speckit.profiles compare-strategies web-app+mobile-app --json
/speckit.profiles compare-strategies web-app:2+mobile-app:1 --json
```

**JSON format:**
```json
{
  "cascade_str": "web-app+mobile-app",
  "source_profiles": ["web-app", "mobile-app"],
  "strategies": {
    "average": {
      "multipliers": {
        "web": 1.15,
        "mobile": 1.40,
        "api": 1.40
      },
      "description": "..."
    },
    "max": {
      "multipliers": {...},
      "description": "..."
    },
    "min": {
      "multipliers": {...},
      "description": "..."
    }
  },
  "statistics": {
    "average": {"max": 1.50, "min": 0.50, "avg": 1.13},
    "max": {"max": 2.00, "min": 0.50, "avg": 1.19},
    "min": {"max": 1.50, "min": 0.50, "avg": 1.05}
  },
  "recommendation": "average (balanced approach)"
}
```

**Use cases for JSON output:**
- CI/CD integration - parse strategies and auto-select
- Scripting - programmatic strategy comparison
- Tools integration - feed into other DevOps tools
- Reporting - generate strategy comparison reports

```python
# JSON output for programmatic use
from specify_cli.quality import print_strategy_comparison_json

json_output = print_strategy_comparison_json("web-app+mobile-app")
# Returns JSON string with all strategies, multipliers, statistics
```

## Mode: Recommend

**Usage**: `/speckit.profiles recommend "<project_description>"`

Analyze project description and recommend the most suitable priority profile.

**Example inputs:**
- "React SPA with Node.js backend"
- "iOS app with REST API"
- "ML inference service for image classification"
- "Data pipeline for ETL processing"

**Output format:**
```
=== Profile Recommendation ===

Input: "React SPA with Node.js backend"

Recommended: web-app

Reasoning:
  - "React" and "SPA" indicate web frontend
  - "Node.js backend" indicates API usage
  - Best fit: web-app profile (web: 1.5x, api: 1.3x)

Usage:
  /speckit.loop --criteria backend,frontend --priority-profile web-app
```

**JSON Output** (Exp 27):
Add `--json` flag to get JSON output for programmatic use:

```bash
/speckit.profiles recommend "React SPA with Node.js backend" --json
```

Example JSON output:
```json
{
  "recommended_profile": "web-app",
  "description": "React SPA with Node.js backend",
  "scores": {
    "web-app": 2,
    "graphql-api": 1
  },
  "matched_keywords": {
    "web-app": ["web", "spa", "react"],
    "graphql-api": []
  },
  "match_count": 2
}
```


## Mode: Recommend-Intelligent (Exp 24)

**Usage**: `/speckit.profiles recommend-intelligent "<project_description>" [top_n]`

**NEW** - Get intelligent Top-N profile recommendations with multi-factor scoring and explanations.

**Features:**
- **Multi-factor scoring**: Tech stack, project type, and priority alignment
- **Top-N recommendations**: Get multiple ranked options (default: 3)
- **Confidence levels**: High, medium, low, or none
- **Detailed explanations**: See why each profile was recommended
- **Hybrid detection**: Automatic cascade suggestions for hybrid projects

**Example:**
```bash
# Get top 3 recommendations
/speckit.profiles recommend-intelligent "Fullstack app with React web and iOS mobile app"

# Get top 5 recommendations
/speckit.profiles recommend-intelligent "ML-powered web application" 5
```

**Output format:**
```
### Profile Recommendations

1. **web-app** 🟢 (score: 2.15)
   Confidence: HIGH
   Reason: Tech stack matches: react, typescript, node
   Factors: tech: 1.2, type: 0.5, priorities: 0.45

💡 **Hybrid Suggestion**: web-app+mobile-app
```

**Implementation:**
```python
from specify_cli.quality import print_intelligent_recommendations
output = print_intelligent_recommendations(description, top_n=3)
```


## Mode: Recommend-Intelligent (Exp 24)

**Usage**: 

**NEW** - Get intelligent Top-N profile recommendations with multi-factor scoring and explanations.

**Features:**
- **Multi-factor scoring**: Tech stack, project type, and priority alignment
- **Top-N recommendations**: Get multiple ranked options (default: 3)
- **Confidence levels**: High, medium, low, or none
- **Detailed explanations**: See why each profile was recommended

**Example:**


**Output format:**


**Implementation:**


## Mode: Detect

**Usage**: `/speckit.profiles detect`

Auto-detect the appropriate priority profile based on project files and structure.

**Detection sources:**
- `package.json` → Detects web-app (React, Vue, Angular), mobile-app (React Native, Expo, Ionic)
- `requirements.txt` / `pyproject.toml` → Detects ml-service (tensorflow, pytorch), data-pipeline (airflow, pyspark)
- `go.mod` → Detects graphql-api (graphql), microservice (grpc, protobuf)
- File structure → Detects mobile-app (android/, ios/), graphql-api (schema.graphql), microservice (kubernetes/, docker-compose.yml)

**Output format:**
```
=== Auto-Detected Priority Profile ===

Project Root: /path/to/project

Detected Profile: web-app

Detection Scores:
  web-app: 8
  graphql-api: 2
  microservice: 1

Evidence:
  - Found: package.json with React, Next.js
  - Found: src/App.tsx (frontend file)
  - Found: vite.config.ts

Usage:
  /speckit.loop --criteria frontend,backend --priority-profile auto
```

**JSON Output** (Exp 26):
Add `--json` flag to get JSON output for programmatic use:
```bash
/speckit.profiles detect --json
```

**JSON format:**
```json
{
  "detected_profile": "web-app",
  "project_root": "/path/to/project",
  "scores": {
    "web-app": 8,
    "graphql-api": 2,
    "microservice": 1
  },
  "evidence": [
    "web-app profile matched with score 8",
    "graphql-api profile matched with score 2"
  ]
}
```

**Use cases:**
- **CI/CD integration** - Auto-detect profile in pipelines
- **Project analysis** - Programmatically determine project type
- **Tooling integration** - Feed detection results into DevOps tools

**Integration with quality loop:**
Use `--priority-profile auto` to automatically detect and use the best profile:

```bash
/speckit.loop --criteria backend --priority-profile auto
```

## Mode: Domains

**Usage**: `/speckit.profiles domains`

Display all available domain tags with descriptions.

**Output format:**
```
=== Domain Tags ===

web           - Frontend web applications (React, Vue, Angular)
api           - REST/GraphQL APIs and services
data          - Database, data pipelines, and data processing
infrastructure - DevOps, IaC, cloud infrastructure
mobile        - iOS/Android mobile applications
ml            - Machine learning services and models
graphql       - GraphQL-specific APIs and schemas
microservices - Distributed systems and microservices
async         - Async/concurrent operations and messaging
auth          - Authentication and authorization
```

**JSON Output** (Exp 26):
Add `--json` flag to get JSON output for programmatic use:
```bash
/speckit.profiles domains --json
```

**JSON format:**
```json
{
  "web": "Frontend web applications (React, Vue, Angular)",
  "api": "REST/GraphQL APIs and services",
  "data": "Database, data pipelines, and data processing",
  "infrastructure": "DevOps, IaC, cloud infrastructure",
  "mobile": "iOS/Android mobile applications",
  "ml": "Machine learning services and models",
  "graphql": "GraphQL-specific APIs and schemas",
  "microservices": "Distributed systems and microservices",
  "async": "Async/concurrent operations and messaging",
  "auth": "Authentication and authorization"
}
```

**Use cases:**
- **Documentation** - Generate domain reference documentation
- **Tool integration** - Import domain definitions into external tools
- **Validation** - Verify domain tag configuration

## Mode: Custom

**Usage**: `/speckit.profiles custom`

Display information about custom (user-defined) priority profiles.

**Output format:**
```
### Custom Priority Profiles

Custom profiles file: .speckit/priority-profiles.yml

Custom profiles (2):
  - my-web-app
  - data-heavy

✅ All custom profiles are valid
```

**If no custom profiles exist:**
```
### Custom Priority Profiles

No custom profiles defined.

To create custom profiles, add a file at:
  .speckit/priority-profiles.yml

Example format:
```yaml
priority_profiles:
  my-custom-profile:
    multipliers:
      web: 2.0
      api: 1.5
      auth: 1.8
    description: "My custom profile for web apps"
```
```

**Custom profiles can:**
- Override built-in profiles (define profile with same name)
- Add new profiles with custom multipliers
- Be used in quality loop with `--priority-profile <custom-name>`

**JSON Output** (Exp 27):
Add `--json` flag to get JSON output for programmatic use:

```bash
/speckit.profiles custom --json
```

Example JSON output:
```json
{
  "custom_profiles": [
    {
      "name": "my-web-app",
      "description": "My custom profile for web apps",
      "multipliers": {
        "web": 2.0,
        "api": 1.5,
        "auth": 1.8
      }
    },
    {
      "name": "data-heavy",
      "description": "Data-heavy applications",
      "multipliers": {
        "data": 2.0,
        "infrastructure": 1.5
      }
    }
  ],
  "count": 2,
  "file_path": ".speckit/priority-profiles.yml",
  "file_exists": true
}
```


## Mode: Wizard (Exp 26)

**Usage**: `/speckit.profiles wizard ["<project_description>"]`

**NEW** - Interactive profile selection wizard that guides you through choosing the right priority profile.

The wizard helps you:
1. **Auto-detects** project context from files (if available)
2. **Shows recommendations** with confidence scores
3. **Compares profiles** side-by-side
4. **Guides cascade selection** for hybrid projects
5. **Provides ready-to-use** commands

**Examples:**
```bash
# Run wizard with auto-detection
/speckit.profiles wizard

# Run wizard with project description
/speckit.profiles wizard "Fullstack app with React web and iOS mobile app"

# Run wizard with specific criteria for command output
/speckit.profiles wizard "ML-powered web application" --criteria frontend,api
```

**Wizard Output:**
```
### 🧙 Interactive Profile Selection Wizard

#### Step 1: Auto-Detection

✅ **Auto-detected profile:** `web-app`

**Detection evidence:**
  - Found: package.json with React, Next.js
  - Found: src/App.tsx (frontend file)
  - Found: vite.config.ts

---

#### Step 2: Profile Recommendations

**Based on:** Fullstack app with React web and iOS mobile app

1. **web-app** 🟢 (score: 2.15)
   Confidence: HIGH
   Reason: Tech stack matches: react, typescript, node
   Factors: tech=1.2, type=0.5, priorities=0.45

2. **mobile-app** 🟡 (score: 1.80)
   Confidence: MEDIUM
   Reason: Mobile app detected: ios, swift mentioned
   Factors: tech=0.9, type=0.6, priorities=0.3

3. **graphql-api** ⚪ (score: 0.45)
   Confidence: LOW
   Reason: GraphQL mentioned in description
   Factors: tech=0.3, type=0.1, priorities=0.05

💡 **Hybrid Suggestion:** `web-app+mobile-app`

---

#### Step 3: Profile Comparison

Domain           | web-app     | mobile-app  | ml-service
-----------------------------------------------------------------
web              | 1.5x        | 0.8x        | 0.5x
mobile           | 0.8x        | 2.0x        | 0.5x
api              | 1.3x        | 1.5x        | 1.2x
data             | 1.0x        | 1.2x        | 2.0x
ml               | 0.5x        | 0.5x        | 2.0x
auth             | 1.5x        | 1.5x        | 1.0x

*Run `/speckit.profiles compare <profile1> <profile2> [...]` for detailed comparison*

---

#### Step 4: Hybrid Projects (Cascade Profiles)

If your project spans multiple domains, you can combine profiles:

- **fullstack-balanced** - Equal web + mobile emphasis
- **web-ml** - Web application with ML backend
- **mobile-ml** - Mobile-first ML application
- **graphql-web** - GraphQL API with web frontend
- **api-data** - API with data processing

**Or create custom cascades:**
- `web-app+mobile-app` - Combine profiles (average strategy)
- `web-app:2+mobile-app:1` - Weighted (2x emphasis on web)
- `--strategy max` - Use strict quality for cascades

*Run `/speckit.profiles presets` to see all named presets*

---

#### Step 5: Ready-to-Use Commands

**Using auto-detected profile:**
```bash
/speckit.loop --criteria backend --priority-profile web-app
```

**Using specific profiles:**
```bash
/speckit.loop --criteria backend --priority-profile web-app
/speckit.loop --criteria backend --priority-profile mobile-app
/speckit.loop --criteria backend --priority-profile ml-service
```

**Using cascade profiles (hybrid projects):**
```bash
/speckit.loop --criteria backend --priority-profile fullstack-balanced
/speckit.loop --criteria backend --priority-profile web-app+mobile-app
/speckit.loop --criteria backend --priority-profile web-ml
```

**With merge strategy:**
```bash
/speckit.loop --criteria backend --priority-profile web-app+mobile-app --strategy max
/speckit.loop --criteria backend --priority-profile web-app+mobile-app --strategy min
/speckit.loop --criteria backend --priority-profile web-app+mobile-app --strategy avg
```

---

#### Additional Help

- `/speckit.profiles list` - List all available profiles
- `/speckit.profiles show <name>` - Show detailed profile info
- `/speckit.profiles compare <name1> <name2>` - Compare profiles
- `/speckit.profiles detect` - Auto-detect profile from project
- `/speckit.profiles recommend "<description>"` - Get recommendations
- `/speckit.profiles cascade <profile1+profile2>` - Preview cascade
- `/speckit.profiles compare-strategies <cascade>` - Compare strategies
- `/speckit.profiles presets` - List named cascade presets
```

**Implementation:**
```python
from specify_cli.quality import print_profile_wizard
from pathlib import Path

# Run wizard with auto-detection
output = print_profile_wizard(
    project_root=Path.cwd(),
    project_description=None,  # Optional description
    criteria_name="backend",    # Default criteria for command output
)
print(output)

# Run wizard with project description
output = print_profile_wizard(
    project_root=Path.cwd(),
    project_description="Fullstack app with React web and iOS mobile app",
    criteria_name="frontend,backend",
)
print(output)
```

**Use cases:**
- **New users** - Discover profiles without memorizing names
- **Complex projects** - Understand which profile fits best
- **Hybrid projects** - Get cascade recommendations
- **Team onboarding** - Teach profile selection workflow
- **Quick reference** - Get ready-to-use commands immediately

**Benefits:**
1. **Improved discoverability** - All profile options explained in one place
2. **Reduced learning curve** - Context-aware recommendations
3. **Better adoption** - Complex features (cascade, strategies) made accessible
4. **Faster workflow** - Ready-to-use commands without trial and error


## Mode: Validate

**Usage**: `/speckit.profiles validate`

Validate all custom profiles and report any errors.

**Output format:**
```
### Profile Validation

Custom profiles file: .speckit/priority-profiles.yml
Total profiles: 3
Valid: 2
Invalid: 1

❌ Validation Errors:

  my-broken-profile:
    - Multiplier for 'web' must be a number
    - Multiplier for 'auth' must be >= 0
```

**JSON Output:**
```bash
/speckit.profiles validate --json
```

Returns JSON with validation report including file path, valid/invalid counts, and detailed errors per profile.

**What is validated:**
- Required field `multipliers` exists
- Multiplier values are numbers (int or float)
- Multiplier values are non-negative (>= 0)

## Implementation Notes

**Import the required functions:**
```python
from specify_cli.quality import (
    PriorityProfilesManager,
    print_profile_summary,
    print_all_profiles,
    print_custom_profiles_info,
    # New functions
    validate_and_print,
    print_profile_diff,
    get_profile_json,
    get_all_profiles_json,
    get_domain_tags_json,
    get_validation_report_json,
    # Cascade functions (Exp 20-21)
    print_cascade_profile_info,
    list_available_cascades,
    list_merge_strategies,
    get_cascade_presets,
    recommend_cascade,
    # Exp 22: Strategy aliases and named presets
    normalize_strategy_alias,
    is_named_cascade_preset,
    resolve_named_preset,
    expand_named_preset,
    find_preset_by_cascade,
    list_named_presets_by_category,
    list_all_preset_names,
    get_preset_categories,
    print_named_presets_by_category,
    # Exp 22: Constants
    STRATEGY_ALIASES,
    NAMED_CASCADE_PRESETS,
    CASCADE_TO_PRESET_MAP,
    # Exp 25: Cascade strategy comparison
    compare_cascade_strategies,
    print_strategy_comparison,
    # Exp 26: Interactive profile wizard
    interactive_profile_wizard,
    print_profile_wizard,
    # Exp 26: JSON output for core commands
    print_all_profiles_json,
    print_profile_summary_json,
    print_domain_tags_json,
)
from specify_cli.quality.autodetect import (
    get_detection_details,
    print_detection_details,
    # Exp 26: JSON output for detect
    print_detection_details_json,
)
```

**For each mode:**
1. List: Use `print_all_profiles()` or `print_all_profiles_json()` for JSON (Exp 26)
2. Show: Use `print_profile_summary(profile_name)` or `print_profile_summary_json(profile_name)` for JSON (Exp 26)
3. Cascade: Use `print_cascade_profile_info(cascade_str, project_root, strategy)` for formatted cascade info
   - Now supports named presets: `print_cascade_profile_info("fullstack-balanced")`
   - Now supports strategy aliases: `strategy="avg"` instead of `strategy="average"`
4. Compare: Use `PriorityProfilesManager.compare_profiles(profile_names)`
5. Diff: Use `PriorityProfilesManager.print_profile_diff(profile1, profile2)` or `PriorityProfilesManager.diff_profiles(profile1, profile2)` for JSON
6. Compare-Strategies: Use `print_strategy_comparison(cascade_str)` or `compare_cascade_strategies(cascade_str)` for JSON dict
7. Recommend: Use `PriorityProfilesManager.recommend_profile(description)`
7. Recommend-cascade: Use `PriorityProfilesManager.recommend_cascade(description)`
8. Detect: Use `get_detection_details()` and `print_detection_details()` or `print_detection_details_json()` for JSON (Exp 26)
9. Domains: Use `PriorityProfilesManager.list_domain_tags()` or `print_domain_tags_json()` for JSON (Exp 26)
10. Strategies: Use `PriorityProfilesManager.list_merge_strategies()` (returns dict with aliases) or `list_merge_strategies_simple()` (returns list)
11. Presets: Use `PriorityProfilesManager.get_cascade_presets()` or `list_named_presets_by_category(category)` for filtering
12. Custom: Use `print_custom_profiles_info()`
13. Validate: Use `validate_and_print()` or `PriorityProfilesManager.get_validation_report_json()` for JSON
14. Wizard: Use `print_profile_wizard(project_root, project_description, criteria_name)` for interactive profile selection

**Exp 22: Strategy Aliases Functions:**
- `normalize_strategy_alias(alias)` - Convert alias to canonical name
  ```python
  normalize_strategy_alias("avg")  # Returns: "average"
  normalize_strategy_alias("wgt")  # Returns: "weighted"
  normalize_strategy_alias("strict")  # Returns: "max"
  ```

**Exp 22: Named Preset Functions:**
- `is_named_cascade_preset(name)` - Check if name is a preset
- `resolve_named_preset(name)` - Get preset configuration dict
- `expand_named_preset(name)` - Get cascade string from preset name
- `find_preset_by_cascade(cascade_str)` - Reverse lookup (cascade → preset name)
- `list_named_presets_by_category(category)` - List presets by category
  - Categories: `fullstack`, `hybrid`, `backend`, `strategy`
- `list_all_preset_names()` - Get all preset names
- `get_preset_categories()` - Get available categories
- `print_named_presets_by_category(category)` - Formatted output

**Exp 22: Constants:**
- `STRATEGY_ALIASES` - Dict mapping aliases to canonical names
- `NAMED_CASCADE_PRESETS` - Dict of all named preset configurations
- `CASCADE_TO_PRESET_MAP` - Reverse mapping from cascade string to preset name

**Enhanced Cascade Resolution (Exp 22):**
`resolve_cascade_profile()` and `get_cascade_profile_info()` now:
- Accept named presets directly: `resolve_cascade_profile("fullstack-balanced")`
- Accept strategy aliases: `resolve_cascade_profile("web-app+mobile-app", strategy="avg")`
- Automatically use preset's strategy if not overridden

**New JSON Output Functions:**
- `PriorityProfilesManager.get_profile_json(name, indent=2)` - Get single profile as JSON
- `PriorityProfilesManager.get_all_profiles_json(indent=2)` - Get all profiles as JSON
- `PriorityProfilesManager.get_domain_tags_json(indent=2)` - Get domain tags as JSON
- `PriorityProfilesManager.get_validation_report_json(indent=2)` - Get validation report as JSON
- `PriorityProfilesManager.diff_profiles(profile1, profile2)` - Get diff as JSON dict
- **Exp 26: Wrapper functions for easier CLI integration:**
  - `print_all_profiles_json(project_root, indent)` - List mode JSON output
  - `print_profile_summary_json(profile_name, project_root, indent)` - Show mode JSON output
  - `print_domain_tags_json(indent)` - Domains mode JSON output
  - `print_detection_details_json(details, project_root, indent)` - Detect mode JSON output (autodetect module)

**New Profile Diff Function:**
- `PriorityProfilesManager.diff_profiles(profile1, profile2)` - Returns dict with highlighted differences
- `PriorityProfilesManager.print_profile_diff(profile1, profile2)` - Returns formatted diff string

**New Profile Merge Function (Exp 19):**
- `PriorityProfilesManager.merge_profiles(profile_names, merged_name, strategy="average", weights=None)` - Merge multiple profiles
  - Strategy options: "average" (default), "max", "min", "weighted" (or aliases: "avg", "wgt")
  - Weights: Optional list of weights for "weighted" strategy

**New Cascade Functions (Exp 20-21):**
- `PriorityProfilesManager.parse_cascade_profile(cascade_str)` - Parse cascade string
- `PriorityProfilesManager.parse_weighted_cascade_profile(cascade_str)` - Parse weighted cascade (profile:weight)
- `PriorityProfilesManager.resolve_cascade_profile(cascade_str, project_root, strategy, weights)` - Resolve cascade to merged profile
  - Now supports named presets and strategy aliases (Exp 22)
- `PriorityProfilesManager.get_cascade_profile_info(cascade_str, project_root, strategy)` - Get cascade details
  - Now includes `preset_name`, `preset_category`, `preset_use_case` for named presets (Exp 22)
- `PriorityProfilesManager.print_cascade_profile_info(cascade_str, project_root, strategy)` - Get formatted cascade info string
- `PriorityProfilesManager.list_available_cascades(project_root)` - List common cascade combinations

**New Cascade Functions (Exp 21):**
- `PriorityProfilesManager.parse_weighted_cascade_profile(cascade_str)` - Parse weighted cascade
- `PriorityProfilesManager.recommend_cascade(description)` - Recommend cascade profile
- `PriorityProfilesManager.get_cascade_presets()` - Get predefined presets
  - Now returns `NAMED_CASCADE_PRESETS` constant (Exp 22)
- `PriorityProfilesManager.list_merge_strategies()` - List merge strategies
  - Now returns dict with aliases (Exp 22)

**Note on custom profiles:**
All list/show/compare commands automatically include custom profiles if they exist. Custom profiles are loaded from `.speckit/priority-profiles.yml` in the project root.

**Note on named presets (Exp 22):**
Named cascade presets are first-class profiles that can be used directly by name:
- `fullstack-balanced` instead of `web-app:1+mobile-app:1`
- `conservative` instead of `web-app+mobile-app` with min strategy
- Presets include category, strategy, and use case metadata
- 12 named presets across 4 categories: fullstack, hybrid, backend, strategy

## Error Handling

| Error | Action |
|-------|--------|
| Profile not found | Error: "Profile '{name}' not found. Available: {list}" |
| Invalid mode | Error: "Unknown mode '{mode}'. Available: list, show, compare, diff, recommend, detect, domains, custom, validate" |
| Empty description | Error: "Recommend mode requires a project description" |
| No project files | Warning: "Could not detect project type. Using 'default' profile" |
| Invalid custom profiles | Warning: "Custom profiles have validation errors. See `/speckit.profiles validate` for details" |

## Examples

```bash
# List all profiles (includes custom if defined)
/speckit.profiles list

# List all profiles as JSON (for CI/CD integration)
/speckit.profiles list --json

# Show web-app profile details
/speckit.profiles show web-app

# Show custom profile details
/speckit.profiles show my-custom-profile

# Show cascade profile (combines web-app and mobile-app)
/speckit.profiles cascade web-app+mobile-app

# Show cascade profile for web + ML hybrid project
/speckit.profiles cascade web-app+ml-service

# Compare web-app vs mobile-app
/speckit.profiles compare web-app mobile-app

# Diff two profiles to see differences
/speckit.profiles diff web-app mobile-app

# Get recommendation for React project
/speckit.profiles recommend "React SPA with Node.js backend"

# Get intelligent Top-N recommendations (Exp 24)
/speckit.profiles recommend-intelligent "Fullstack app with React web and iOS mobile app"

# Compare strategies for cascade before using it (Exp 25)
/speckit.profiles compare-strategies web-app+mobile-app

# Auto-detect profile from project files
/speckit.profiles detect

# Show custom profiles info
/speckit.profiles custom

# Validate custom profiles
/speckit.profiles validate

# Validate and get JSON report
/speckit.profiles validate --json

# List all domain tags
/speckit.profiles domains
```

## Creating Custom Profiles

Create a file at `.speckit/priority-profiles.yml` in your project root:

```yaml
priority_profiles:
  # Custom profile for heavy data processing
  data-heavy:
    multipliers:
      web: 0.5
      api: 1.0
      data: 2.5
      infrastructure: 1.5
      mobile: 0.3
      ml: 1.8
      graphql: 0.5
      microservices: 1.3
      async: 1.5
      auth: 0.8
    description: "Profile for data-heavy applications with ML pipelines"

  # Override built-in web-app with custom multipliers
  web-app:
    multipliers:
      web: 2.0
      api: 1.5
      data: 0.8
      infrastructure: 0.7
      mobile: 0.7
      ml: 0.5
      graphql: 1.3
      microservices: 1.0
      async: 1.3
      auth: 1.8
    description: "Custom web-app profile with stronger web emphasis"
```

**Custom profiles:**
- Can override built-in profiles (use same name)
- Add entirely new profiles
- Used automatically when specified in `--priority-profile`
- Merged with built-in profiles in list/show/compare commands

**Usage:**
```bash
/speckit.loop --criteria backend --priority-profile data-heavy
/speckit.loop --criteria frontend,backend --priority-profile web-app  # Uses your custom override
```

## Mode: Analyze

**Usage**: 

Perform quality gap analysis for a specific priority profile and criteria combination.
Shows which rules get the highest priority scores, critical rules, domain distribution, and potential gaps.

**Output format:**
### Quality Gap Analysis

**Profile:** web-app
**Description:** Web application profile: emphasizes web, API, and auth

**Criteria:** frontend v1.7
**Description:** Frontend quality criteria for React/Vue/Angular apps
**Phase:** B (10 active rules)

---

#### Top 10 Rules by Priority Score

Rules with highest effective weight (base × multiplier):

| Rank | Rule ID | Description | Severity | Base | Effective | Domains |
|------|---------|-------------|----------|------|-----------|---------|
| 1 | react_hooks_optimization | React Hooks Optimization... | 🟡 warn | 1 | **1.5** | web |
| 2 | error_boundaries | Error Boundaries... | 🟡 warn | 1 | **1.5** | web |
| 3 | xss_prevention | XSS Prevention... | 🔴 fail | 2 | **3.0** | web |
| 4 | api_integration | API Integration... | 🟡 warn | 1 | **1.3** | api |
| 5 | form_validation | Form Validation... | 🟡 warn | 1 | **1.3** | web |
| 6 | environment_config | Environment Configuration... | 🟡 warn | 1 | **1.2** | web |
| 7 | state_persistence | State Persistence... | 🟡 warn | 1 | **1.2** | web |
| 8 | component_composition | Component Composition... | 🟡 warn | 1 | **1.2** | web |
| 9 | component_library | Component Library... | 🟡 warn | 1 | **1.2** | web |
| 10 | typography_scale | Typography Scale... | 🟡 warn | 1 | **1.2** | web |

---

#### Critical Rules (2 rules)

Rules with  severity that must pass:

- **xss_prevention**: Output encoding, CSP headers
  - Severity: fail | Weight: 2 | Effective: **3.0**
  - Domains: web

- **error_states**: Error state UI
  - Severity: fail | Weight: 2 | Effective: **2.0**
  - Domains: web

---

#### Domain Distribution

| Domain | Rule Count | Multiplier | Emphasis |
|--------|------------|------------|----------|
| web | 8 | 1.5x | 🔥 high |
| api | 1 | 1.3x | ⚡ medium |
| async | 1 | 1.2x | ⚡ medium |
| infrastructure | 1 | 0.8x | 💤 low |

---

#### Gap Detection

Domains with many rules but low multiplier (potential gaps):

| Domain | Rule Count | Multiplier | Impact |
|--------|------------|------------|--------|
| infrastructure | 1 | 0.8x | -0.2 |

*Consider increasing multiplier for these domains if they are important for your project*

---

#### Multipliers Reference

| Domain | Multiplier |
|--------|------------|
| api | 1.3 |
| async | 1.2 |
| auth | 1.5 |
| data | 1.0 |
| graphql | 1.2 |
| infrastructure | 0.8 |
| mobile | 0.8 |
| ml | 0.5 |
| microservices | 1.0 |
| web | 1.5 |

---

#### Usage Examples

Run quality loop with this profile:



Compare with other profiles:



For hybrid projects, consider cascade profiles:



---

**Use cases:**
- Understand which rules will be prioritized before running quality loop
- Identify critical rules that must pass for your project type
- Discover potential gaps in quality coverage for your domain
- Compare how different profiles affect the same criteria

**Examples:**


---

## Integration with Quality Loop

Priority profiles are used in quality loop via `--priority-profile` flag:

```bash
# Single profile
/speckit.loop --criteria backend --priority-profile web-app
/speckit.loop --criteria frontend,backend,live-test --priority-profile mobile-app

# Cascade profile (combines multiple profiles)
/speckit.loop --criteria frontend,backend,live-test --priority-profile web-app+mobile-app
/speckit.loop --criteria backend,api --priority-profile graphql-api+ml-service

# Cascade profile with custom merge strategy (Exp 23)
/speckit.loop --criteria frontend,backend --priority-profile web-app+mobile-app --strategy max
/speckit.loop --criteria frontend,backend --priority-profile web-app+mobile-app --strategy min
/speckit.loop --criteria frontend,backend --priority-profile web-app+mobile-app --strategy avg

# Named presets (Exp 22)
/speckit.loop --priority-profile fullstack-balanced --criteria frontend,backend
/speckit.loop --priority-profile web-ml --criteria frontend,api
/speckit.loop --priority-profile conservative --criteria backend

# Auto-detect from project files
/speckit.loop --criteria backend --priority-profile auto
```

**Profile affects:**
- Rule scoring: Rules with matching domain_tags get multiplied
- Evaluation priority: Higher multiplier = more important rules
- Critique focus: Issues in high-multiplier domains are prioritized

**Cascade merge strategies (Exp 23):**
When using cascade profiles with `--priority-profile profile1+profile2`, you can specify merge strategy via `--strategy`:

| Strategy | Aliases | Description | Use case |
|----------|---------|-------------|----------|
| `average` | `avg`, `mean`, `bal` | Average multipliers | Balanced approach (default) |
| `max` | `strict` | Take maximum multiplier | Strictest quality requirements |
| `min` | `lenient` | Take minimum multiplier | Minimal requirements, faster iteration |
| `weighted` | `wgt`, `custom` | Weighted average | Custom weights in cascade string |

**Strategy examples:**
```bash
# Strict quality - take highest multiplier from each profile
/speckit.loop --priority-profile web-app+mobile-app --strategy max

# Lenient quality - take lowest multiplier from each profile
/speckit.loop --priority-profile web-app+mobile-app --strategy min

# Custom weights - web-app gets 2x weight
/speckit.loop --priority-profile web-app:2+mobile-app:1 --strategy wgt

# Strategy aliases work too
/speckit.loop --priority-profile web-app+mobile-app --strategy avg
/speckit.loop --priority-profile web-app+mobile-app --strategy strict
```

**Cascade profiles:**
When using `--priority-profile profile1+profile2`, the system:
1. Parses the cascade string
2. Validates all source profiles exist
3. Merges multipliers using specified strategy (default: average)
4. Uses the merged profile for evaluation

**Auto-detection:**
When using `--priority-profile auto`, the system analyzes project files (package.json, requirements.txt, etc.) to automatically select the best profile. Run `/speckit.profiles detect` to see what would be detected.
