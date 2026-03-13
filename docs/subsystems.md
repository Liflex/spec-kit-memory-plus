# Quality Subsystems

Spec Kit включает множество подсистем для управления качеством. Каждая работает как самостоятельно, так и в связке с другими.

---

## Quality Goals

Определение и отслеживание целей качества.

```bash
/speckit.goals create --type target_score --target 0.90
/speckit.goals check
/speckit.goals suggest
```

**Типы целей:**
- Target Score — целевой балл
- Pass Rate — процент прохождения
- Category — по категориям
- Streak — серия успешных запусков
- Improvement — улучшение по сравнению с прошлым
- Stability — стабильность результатов

---

## Quality History

Отслеживание трендов качества.

```bash
/speckit.history list --runs 10
/speckit.history stats
/speckit.history compare --runs 5
```

Возможности: история запусков, статистический анализ, обнаружение трендов, сравнение запусков, интерактивный HTML-дашборд.

---

## Quality Insights

AI-рекомендации по улучшению качества.

```bash
/speckit.insights generate
/speckit.insights optimize
/speckit.insights export
```

Типы: распознавание паттернов, анализ трендов, предиктивная аналитика, оптимизация, root cause analysis, action items.

---

## Quality Anomalies

Статистическое обнаружение аномалий.

```bash
/speckit.anomalies detect
/speckit.anomalies types
/speckit.anomalies recommend
```

---

## Quality Benchmarks

Перцентильное ранжирование и исторические baseline.

```bash
/speckit.benchmarks create --name my-benchmark --runs 50
/speckit.benchmarks compare --category security
/speckit.benchmarks report --output benchmark-report.json
/speckit.benchmarks list
```

**Уровни:**
- Excellent (90th+) — Top 10%
- Above Average (75-90th) — Top 25%
- Average (25-75th) — Middle 50%
- Below Average (10-25th) — Bottom 25%
- Poor (0-10th) — Bottom 10%

### Benchmark Trends

Анализ траектории перцентилей.

```bash
/speckit.benchmark-trends analyze --task my-api --runs 50
/speckit.benchmark-trends categories --task my-api
/speckit.benchmark-trends forecast --horizon 10
```

Velocity tracking, momentum analysis, trend segmentation, predictive forecasting, early warning system.

---

## Trend-Based Goals

Рекомендации целей на основе прогнозов.

```bash
/speckit.trend-goals analyze
/speckit.trend-goals analyze --strategy optimistic
/speckit.trend-goals categories
/speckit.trend-goals wizard
```

**Стратегии:** optimistic, conservative, stabilizing, maintenance, catch-up.

---

## Gate Policies

Quality gates для разных окружений.

```bash
/speckit.gates list
/speckit.gates recommend
/speckit.gates compare --policies production,staging
```

**Встроенные политики:** production, staging, development, ci, strict, lenient.

---

## QA Dashboard

Единый центр управления качеством.

```bash
/speckit.qa overview
/speckit.qa check
/speckit.qa compare --runs 5
/speckit.qa trends --forecast
/speckit.qa interactive
```

---

## Quality Alerts

Проактивные уведомления о проблемах качества.

```bash
/speckit.alerts check
/speckit.alerts history --hours 24
/speckit.alerts summary
/speckit.alerts list
```

**Условия:** Critical Quality Drop, Goal Failed, Pass Rate Critical, Stagnation Detected, Critical Rules Fail, Declining Trend, Goal At Risk, Anomaly Detected.

---

## Quality Feedback Loop

Адаптивная конфигурация на основе результатов.

```bash
/speckit.feedback analyze
/speckit.feedback analyze --runs 50
/speckit.feedback suggestions
/speckit.feedback trends
/speckit.feedback insights --priority high,critical
```

Сбор обратной связи:
```bash
/speckit.loop --criteria backend --collect-feedback
/speckit.feedback analyze
```

---

## Quality Debt

Отслеживание и приоритизация quality debt.

```bash
/speckit.debt --analyze
/speckit.debt --summary
/speckit.debt --suggest --strategy quick_wins
/speckit.debt --analyze --category security --severity critical
```

**Стратегии:** quick wins, critical-first, balanced, impact-focused, sustainable.

---

## Quality Plans

Комплексные планы улучшения качества, объединяющие loop configs, goals, gates и profiles.

```bash
/speckit.plans                              # List plans
/speckit.plans --show production-ready      # Plan details
/speckit.plans --apply quick-start          # Apply plan
/speckit.plans --recommend production       # Get recommendations
/speckit.plans --compare quick-start production-ready
/speckit.plans --wizard                     # Interactive wizard
```

**Пресеты:** quick-start, production-ready, continuous-improvement, security-focus, performance-focus, stability, aggressive, ci-cd.

---

## Industry Presets

Предварительно настроенные планы для индустрий.

```bash
/speckit.industries --list
/speckit.industries --info fintech
/speckit.industries --compare fintech,healthcare
/speckit.industries --detect              # Auto-detection
/speckit.industries --recommend           # Interactive wizard
```

| Industry | Compliance | Focus |
|----------|------------|-------|
| `fintech` | PCI-DSS, SOX, GDPR | Security, accuracy, audit |
| `healthcare` | HIPAA, FDA, HL7 | Patient safety, validation |
| `ecommerce` | PCI-DSS, GDPR, ADA | Performance, availability, UX |
| `saas` | SOC 2, GDPR, ISO 27001 | Uptime, data isolation |
| `gaming` | COPPA, GDPR, ESRB | Real-time performance |
| `government` | FedRAMP, NIST, WCAG | Accessibility, transparency |
| `education` | COPPA, FERPA, WCAG | Student privacy, accessibility |
| `iot` | ISO 27001, UL 2900 | Connectivity, OTA, power |

---

## Smart Auto-Configuration

Автоматическая настройка качества для проекта.

```bash
/speckit.autoconfig                # Get recommendation
/speckit.autoconfig --apply        # Apply automatically
/speckit.autoconfig --interactive  # Interactive mode
```

Что делает: определяет индустрию, рекомендует профиль, выбирает критерии, настраивает loop, задает цели.

---

## Loop Configurations

Сохранение и загрузка конфигураций quality loop.

```bash
/speckit.configs list
/speckit.loop --save-config my-config
/speckit.loop --config my-config
/speckit.configs load goal-driven-development
```

**Стандартные пресеты:** production-strict, ci-standard, development-quick, security-focused, frontend-qa, fullstack-comprehensive, api-focused, mobile-app-qa.

**Goal-aware пресеты:** goal-driven-development, quality-improvement-focus, aggressive-quality-targets, stability-focused, goal-aware-ci.

---

## Multi-Variant Testing

Сравнение нескольких конфигураций (A/B/C/n) со статистическим анализом.

```bash
/speckit.multivariant --create "Test" --variants '[...]' --method tukey_hsd
/speckit.multivariant --analyze --test-id <id>
/speckit.multivariant --quick --results '{"A": {"score": 0.82}, "B": {"score": 0.87}}'
```

ANOVA, Bonferroni/Tukey HSD/Holm correction, pairwise comparisons, automatic winner selection.
