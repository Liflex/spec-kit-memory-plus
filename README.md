# Spec Kit

> **AI-Powered Quality Assurance for Software Specifications**

[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

Spec Kit — система автоматической оценки качества спецификаций ПО. Итеративно проверяет артефакты по набору правил, генерирует критику и применяет улучшения через Quality Loop.

---

## Quick Start

```bash
# Clone & install
git clone https://github.com/github/spec-kit.git
cd spec-kit
pip install -r requirements.txt
```

### Python API

```python
from specify_cli.quality import QualityLoop, RuleManager, Evaluator, Scorer, Critique, Refiner

loop = QualityLoop(RuleManager(), Evaluator(), Scorer(), Critique(), Refiner())

result = loop.run(
    artifact="My software specification...",
    task_alias="my-spec",
    criteria_name="backend",
    max_iterations=4,
)

print(f"Score: {result['score']:.2f}, Passed: {result['passed']}")
```

### CLI (Claude Code)

```bash
/speckit.loop --criteria backend                    # Run quality loop
/speckit.loop --project-type web-app                # Auto-select templates
/speckit.qa overview                                # Quality dashboard
/speckit.goals check                                # Check quality goals
/speckit.alerts check                               # Check for alerts
```

---

## Features

### Core Engine

- **Quality Loop** — evaluate, critique, refine (iterative cycle)
- **13 Criteria Templates** — backend, frontend, security, performance, testing, api-spec, database, docs, config, infrastructure, ui-ux, live-test, code-gen
- **Priority Profiles** — domain-weighted scoring (web-app, microservice, ml-service, mobile-app, etc.)
- **Auto Template Selection** — `--project-type` picks the right templates automatically

### Quality Management

- **Goals** — define targets, track progress, get suggestions
- **History** — track trends, statistics, run comparison
- **Insights** — AI-powered recommendations and optimization
- **Anomalies** — statistical anomaly detection
- **Benchmarks** — percentile ranking, historical baselines
- **Alerts** — proactive notifications for quality issues
- **Debt** — track and prioritize quality debt
- **Feedback Loop** — adaptive configuration learning

### Advanced

- **Gate Policies** — environment-specific quality gates (production, staging, ci, etc.)
- **Quality Plans** — unified improvement strategies with presets
- **Industry Presets** — fintech, healthcare, ecommerce, saas, gaming, government, education, iot
- **Auto-Configuration** — one-command project setup with industry detection
- **Simulation** — what-if analysis before applying changes
- **Optimization** — Bayesian, genetic, annealing and other methods
- **Multi-Variant Testing** — A/B/C/n comparison with statistical analysis
- **Template Blending** — combine templates with union/consensus/weighted modes

### Reporting

- **HTML** — interactive reports with charts
- **Markdown** — human-readable for documentation
- **JSON** — machine-readable for CI/CD
- **Result Cards** — rich console output

---

## Criteria Templates

| Template | Description |
|----------|-------------|
| `backend` | Backend API and server-side quality |
| `frontend` | Frontend UI/UX quality |
| `security` | Security best practices |
| `performance` | Performance optimization |
| `testing` | Test coverage and quality |
| `api-spec` | API specification completeness |
| `database` | Database schema and queries |
| `docs` | Documentation quality |
| `config` | Configuration management |
| `infrastructure` | Infrastructure as code |
| `ui-ux` | User interface and experience |
| `live-test` | Live testing validation |
| `code-gen` | Code generation quality |

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `/speckit.loop` | Run quality evaluation loop |
| `/speckit.qa` | QA Dashboard |
| `/speckit.goals` | Quality goals management |
| `/speckit.history` | Quality history and trends |
| `/speckit.insights` | AI-powered insights |
| `/speckit.anomalies` | Anomaly detection |
| `/speckit.benchmarks` | Benchmarking |
| `/speckit.gates` | Gate policies |
| `/speckit.alerts` | Quality alerts |
| `/speckit.feedback` | Feedback loop analysis |
| `/speckit.debt` | Quality debt tracking |
| `/speckit.simulate` | What-if simulation |
| `/speckit.plans` | Quality plans |
| `/speckit.industries` | Industry presets |
| `/speckit.autoconfig` | Smart auto-configuration |
| `/speckit.templates` | Template registry |
| `/speckit.configs` | Loop configurations |
| `/speckit.profiles` | Priority profiles |
| `/speckit.optimize` | Quality optimization |

See [docs/cli-reference.md](docs/cli-reference.md) for detailed usage and examples.

---

## Configuration

Basic project config in `.speckit/config.yml`:

```yaml
quality:
  criteria: backend
  max_iterations: 4
  threshold_a: 0.8
  threshold_b: 0.9
  priority_profile: web-app
  gate_preset: production
```

See [docs/configuration.md](docs/configuration.md) for full configuration reference.

---

## Installation

### Prerequisites

- Python 3.11+
- Git
- (Optional) Ollama for vector memory

### Detailed Setup

See [INSTALL.md](INSTALL.md) for comprehensive installation:
- AI assistant integration (Claude Code, Cursor)
- Vector memory setup with Ollama
- CLI command configuration

---

## Documentation

| Document | Description |
|----------|-------------|
| [Quality Subsystems](docs/subsystems.md) | Goals, History, Insights, Alerts, Benchmarks, and more |
| [CLI Reference](docs/cli-reference.md) | All commands with examples |
| [Configuration](docs/configuration.md) | Config files, profiles, gate policies, alerts |
| [Templates & Blending](docs/templates.md) | Template registry, blending, presets |
| [Optimization](docs/optimization.md) | Optimization methods, Pareto, simulation |
| [Quality Loop](docs/quality-loop.md) | Architecture and internals |
| [Installation](INSTALL.md) | Full installation guide |

---

## Project Structure

```
spec-kit/
├── src/specify_cli/quality/   # Core quality engine
│   ├── models.py              # Data models
│   ├── rules.py               # Rule management
│   ├── evaluator.py           # Quality evaluation
│   ├── scorer.py              # Scoring
│   ├── critique.py            # Critique generation
│   ├── refiner.py             # Artifact refinement
│   ├── loop.py                # Quality loop coordinator
│   ├── loop_config.py         # Loop configuration
│   ├── gate_policies.py       # Gate policies
│   ├── quality_goals.py       # Goals system
│   ├── quality_history.py     # History tracking
│   ├── quality_insights.py    # Insights engine
│   ├── quality_alerting.py    # Alert system
│   ├── template_registry.py   # Template registry
│   └── ...                    # Other modules
├── templates/commands/        # CLI command templates
├── tests/                     # Test suite
├── docs/                      # Documentation
├── INSTALL.md                 # Installation guide
└── README.md                  # This file
```

---

## Contributing

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
pytest tests/
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

**Spec Kit** — AI-Powered Quality Assurance for Software Specifications
