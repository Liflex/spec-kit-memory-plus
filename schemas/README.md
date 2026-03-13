# Spec Kit JSON Schemas

This directory contains JSON schemas for Spec Kit quality reports.

## Available Schemas

### quality-report-v1.json

JSON Schema v1.0 for Spec Kit Quality Reports.

**Schema ID:** `https://speckit.dev/schemas/quality-report-v1.json`

**Sections:**
- `meta` - Report metadata (version, timestamp, generator)
- `summary` - Overall summary (score, status, profile)
- `category_breakdown` - Issues by category
- `failed_rules` - Failed rules with details
- `warnings` - Warning rules with details
- `score_timeline` - Score progression across iterations
- `distribution` - Enhanced distribution statistics (Exp 53)
  - `severity` - Severity breakdown (critical, high, medium, low, info)
  - `score_distribution` - Statistical distribution (min, max, mean, median, p25, p75, p90, p95)

## Usage

### IDE Integration

Add this schema to your IDE for autocompletion and validation:

```json
{
  "$schema": "./schemas/quality-report-v1.json"
}
```

### Python Validation

```python
from specify_cli.quality import validate_schema, get_schema

# Validate a report
is_valid, errors = validate_schema(report_data)

# Get schema programmatically
schema = get_schema()
```

### Export Schema

Export schema to a custom location:

```python
from specify_cli.quality import export_schema

export_schema("custom-path/schema.json")
```

### CLI Export

Export schema via CLI:

```bash
# Export to default location
speckit loop --export-schema

# Export to custom location
speckit loop --export-schema /path/to/schema.json
```

## Schema Versioning

- **v1.0** (Exp 52-53): Initial release with category breakdown, score timeline, distribution statistics

## CI/CD Integration

Use the schema for automated quality gate validation:

```yaml
# GitHub Actions example
- name: Validate Quality Report
  run: |
    pip install jsonschema
    python -c "
    import json
    from jsonschema import validate, RefResolver
    schema = json.load(open('schemas/quality-report-v1.json'))
    report = json.load(open('quality-report.json'))
    validate(instance=report, schema=schema)
    "
```

## Distribution

This schema is published at: `https://speckit.dev/schemas/quality-report-v1.json`

For updates and changes, see the Spec Kit project documentation.
