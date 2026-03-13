# CLI Reference

Все команды Spec Kit доступны как slash-команды в Claude Code.

---

## Core Commands

### /speckit.loop

Запуск quality evaluation loop.

```bash
# Basic
/speckit.loop --criteria backend
/speckit.loop --criteria backend,security,testing

# Auto template selection by project type
/speckit.loop --project-type web-app
/speckit.loop --project-type microservice

# With priority profile
/speckit.loop --criteria backend --priority-profile web-app+mobile-app --strategy max

# With gate policy
/speckit.loop --gate-preset production --strict

# With goal suggestions
/speckit.loop --suggest-goals --auto-update-goals

# With feedback collection
/speckit.loop --criteria backend --collect-feedback

# With blend preset
/speckit.loop --blend-preset full_stack_secure

# Reports
/speckit.loop --html-output quality-report.html
/speckit.loop --json-output quality-report.json
/speckit.loop --show-result-card
/speckit.loop --show-result-card --result-card-compact --result-card-theme dark

# Save/load configs
/speckit.loop --save-config my-config
/speckit.loop --config my-config
```

---

### /speckit.qa

QA Dashboard — единый центр управления.

```bash
/speckit.qa overview      # Quality overview
/speckit.qa check         # Quick quality check
/speckit.qa compare --runs 5
/speckit.qa trends --forecast
/speckit.qa interactive
```

---

### /speckit.goals

Управление целями качества.

```bash
/speckit.goals create --type target_score --target 0.90
/speckit.goals check
/speckit.goals suggest
```

---

### /speckit.history

История качества.

```bash
/speckit.history list --runs 10
/speckit.history stats
/speckit.history compare --runs 5
```

---

### /speckit.insights

AI-рекомендации.

```bash
/speckit.insights generate
/speckit.insights optimize
/speckit.insights export
```

---

### /speckit.anomalies

Обнаружение аномалий.

```bash
/speckit.anomalies detect
/speckit.anomalies types
/speckit.anomalies recommend
```

---

### /speckit.benchmarks

Бенчмарки и перцентили.

```bash
/speckit.benchmarks create --name my-benchmark --runs 50
/speckit.benchmarks compare --category security
/speckit.benchmarks report --output report.json
/speckit.benchmarks list
```

---

### /speckit.benchmark-trends

Анализ трендов бенчмарков.

```bash
/speckit.benchmark-trends analyze --task my-api --runs 50
/speckit.benchmark-trends categories --task my-api
/speckit.benchmark-trends forecast --horizon 10
/speckit.benchmark-trends compare
```

---

### /speckit.trend-goals

Рекомендации целей по трендам.

```bash
/speckit.trend-goals analyze
/speckit.trend-goals analyze --strategy optimistic
/speckit.trend-goals categories
/speckit.trend-goals wizard
```

---

### /speckit.gates

Gate policies.

```bash
/speckit.gates list
/speckit.gates recommend
/speckit.gates compare --policies production,staging
```

---

### /speckit.alerts

Quality alerts.

```bash
/speckit.alerts check
/speckit.alerts history --hours 24
/speckit.alerts summary
/speckit.alerts list
```

---

### /speckit.feedback

Feedback loop.

```bash
/speckit.feedback analyze
/speckit.feedback analyze --runs 50 --task my-api-spec
/speckit.feedback analyze --output feedback-report.md
/speckit.feedback analyze --json --output feedback.json
/speckit.feedback suggestions
/speckit.feedback trends
/speckit.feedback insights --priority high,critical
```

---

### /speckit.debt

Quality debt.

```bash
/speckit.debt --analyze
/speckit.debt --summary
/speckit.debt --suggest --strategy quick_wins
/speckit.debt --analyze --category security --severity critical
/speckit.debt --analyze --top 20
/speckit.debt --analyze --json --output debt.json
/speckit.debt --analyze --task my-api-spec
```

---

### /speckit.simulate

What-if simulation.

```bash
/speckit.simulate --threshold 0.85 0.90
/speckit.simulate --iterations 6
/speckit.simulate --compare --threshold 0.85 0.90 --iterations 5
/speckit.simulate --report
/speckit.simulate --threshold 0.85 0.90 --json
```

---

### /speckit.plans

Quality plans.

```bash
/speckit.plans
/speckit.plans --category production
/speckit.plans --show production-ready
/speckit.plans --apply quick-start
/speckit.plans --recommend production deployment
/speckit.plans --compare quick-start production-ready
/speckit.plans --wizard
/speckit.plans --create "My Plan" --category production --strict
/speckit.plans --export production-ready --output ./plan.yml
/speckit.plans --import ./plan.yml --id team-shared
/speckit.plans --show production-ready --json
```

---

### /speckit.industries

Industry presets.

```bash
/speckit.industries --list
/speckit.industries --info fintech
/speckit.industries --compare fintech,healthcare
/speckit.industries --detect
/speckit.industries --detect-json
/speckit.industries --recommend
```

---

### /speckit.autoconfig

Auto-configuration.

```bash
/speckit.autoconfig
/speckit.autoconfig --apply
/speckit.autoconfig --json
/speckit.autoconfig --interactive
```

---

### /speckit.configs

Loop configurations.

```bash
/speckit.configs list
/speckit.configs load goal-driven-development
```

---

### /speckit.profiles

Priority profiles.

```bash
/speckit.profiles list
/speckit.profiles show web-app
/speckit.profiles compare web-app,microservice
```

---

### /speckit.templates

Template registry.

```bash
python speckit_templates.py list
python speckit_templates.py list --category infrastructure
python speckit_templates.py info api-gateway
python speckit_templates.py search security
python speckit_templates.py recommend web-app
python speckit_templates.py stats
python speckit_templates.py compare frontend mobile backend
python speckit_templates.py diff backend frontend
python speckit_templates.py blend frontend backend --mode union
python speckit_templates.py presets list
python speckit_templates.py presets info full_stack_secure
python speckit_templates.py presets apply full_stack_secure --output stack.yml
```

---

### /speckit.optimize

Quality optimization.

```bash
speckit optimize
speckit optimize --method bayesian
speckit optimize --iterations 2-6 --threshold-a 0.7-0.9
speckit optimize --objectives quality_score,cost
speckit optimize --max-iterations 50
speckit optimize --json --output results.json
```

---

### /speckit.multivariant

Multi-variant testing.

```bash
/speckit.multivariant --create "Test" --variants '[...]' --method tukey_hsd
/speckit.multivariant --list --status completed
/speckit.multivariant --record --test-id <id> --label A --score 0.79
/speckit.multivariant --analyze --test-id <id>
/speckit.multivariant --quick --results '{"A": {"score": 0.82}, "B": {"score": 0.87}}'
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Quality Gate
on: [pull_request, push]
jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Quality Loop
        run: /speckit.loop --criteria backend --json-output report.json
      - name: Check Gate
        run: /speckit.gates evaluate --report report.json --preset production
```

### Jenkins

```groovy
pipeline {
    stages {
        stage('Quality Check') {
            steps {
                sh '/speckit.loop --criteria backend --gate-preset ci'
            }
        }
    }
}
```
