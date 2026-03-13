# Configuration

---

## Project Configuration

Файл `.speckit/config.yml` в корне проекта:

```yaml
quality:
  criteria: backend
  max_iterations: 4
  threshold_a: 0.8
  threshold_b: 0.9

  priority_profile: web-app
  cascade_strategy: max

  strict_mode: false
  lenient_mode: false

  html_output: .speckit/quality-report.html
  markdown_output: .speckit/quality-report.md
  json_output: .speckit/quality-report.json

  gate_preset: production
  gate_goal_mode: balanced
  auto_update_goals: true
```

---

## Custom Priority Profiles

Файл `.speckit/priority-profiles.yml`:

```yaml
profiles:
  my-custom-profile:
    name: "My Custom Profile"
    description: "Custom domain weighting"
    multipliers:
      correctness: 1.2
      security: 1.5
      performance: 1.3
      testing: 1.1
```

**Встроенные профили:** web-app, mobile-app, microservice, graphql-api, ml-service, data-pipeline, desktop, serverless, terraform.

---

## Custom Gate Policies

Файл `.speckit/gate-policies.yml`:

```yaml
policies:
  my-policy:
    name: "My Custom Policy"
    description: "Custom quality gate"
    overall_threshold: 0.85

    severity_gates:
      critical:
        max_failures: 0
        block: true
      high:
        max_failures: 2
        block: false

    category_gates:
      security:
        min_score: 0.90
        block: true
```

**Встроенные политики:** production, staging, development, ci, strict, lenient.

---

## Alert Configuration

Файл `.speckit/alerts.yml`:

```yaml
enabled: true
cooldown_minutes: 60
aggregate_count: 1

webhooks:
  slack: https://hooks.slack.com/services/YOUR/WEBHOOK
  teams: https://outlook.office.com/webhook/YOUR-WEBHOOK

conditions:
  critical-quality-drop:
    enabled: true
    threshold: 0.10
    cooldown_minutes: 30
```

---

## Category-Based Scoring

Категории оценки:
- Correctness
- Security
- Performance
- Testing
- Documentation
- Code Quality
- Infrastructure
- Observability
- Reliability
- CI/CD
- Accessibility
- UX Quality
