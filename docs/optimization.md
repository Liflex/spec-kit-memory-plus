# Optimization & Simulation

---

## Quality Optimization

Автоматический поиск оптимальной конфигурации с помощью продвинутых алгоритмов оптимизации.

```bash
speckit optimize                                    # Quick optimization
speckit optimize --method bayesian                  # Specific method
speckit optimize --iterations 2-6 --threshold-a 0.7-0.9
speckit optimize --objectives quality_score,cost    # Multi-objective
speckit optimize --max-iterations 50
speckit optimize --json --output results.json
```

### Optimization Methods

| Method | Best For | Speed | Global Optima |
|--------|----------|-------|---------------|
| `bayesian` | Most cases (recommended) | Medium | Excellent |
| `genetic` | Many parameters | Slow | Good |
| `annealing` | Tricky local optima | Medium | Good |
| `gradient` | Smooth spaces | Fast | Poor |
| `grid` | Few parameters | Very Slow | Exhaustive |
| `random` | Exploration | Fast | Poor |

### Response Surface Types

- `gaussian_process` — Non-parametric Bayesian model (default)
- `quadratic` — Second-order polynomial with interactions
- `linear` — First-order polynomial (fastest)

---

## Pareto Front Analysis

Для multi-objective optimization.

```bash
/speckit.pareto --analyze       # Analyze Pareto front
/speckit.pareto --knee          # Find knee point
/speckit.pareto --compromise    # Compromise solution
/speckit.pareto --metrics       # Pareto metrics
```

### Visualization

```bash
/speckit.visualize                                    # Auto-detect chart
/speckit.visualize --chart scatter                    # 2D scatter
/speckit.visualize --chart parallel --highlight knee  # Parallel coordinates
/speckit.visualize --chart dashboard --output report.txt
/speckit.visualize --compare --before old.json --after new.json
```

Chart types: scatter, parallel, bar, table, dashboard.

---

## Adaptive Method Selection

```bash
/speckit.adaptive --analyze                 # Recommend method
/speckit.adaptive --optimize --max-iterations 50
/speckit.adaptive --compare-methods
```

---

## Warm Start

Продолжение оптимизации с предыдущих результатов.

```bash
/speckit.warmstart --continue --previous results.json
/speckit.warmstart --transfer --source other_project.json
/speckit.warmstart --resume
```

---

## Ensemble Optimization

Комбинирование нескольких методов.

```bash
/speckit.ensemble --optimize
/speckit.ensemble --compare
/speckit.ensemble --optimize --methods bayesian,genetic,gradient
/speckit.ensemble --optimize --strategy voting
```

---

## Quality Simulation

What-if анализ перед применением изменений.

```bash
/speckit.simulate --threshold 0.85 0.90
/speckit.simulate --iterations 6
/speckit.simulate --compare --threshold 0.85 0.90 --iterations 5
/speckit.simulate --report
/speckit.simulate --threshold 0.85 0.90 --json
```

### Simulation Types

- `threshold` — изменение порогов качества
- `iterations` — изменение количества итераций
- `criteria` — добавление новых критериев
- `profile` — изменение профиля приоритетов
- `multi` — комбинация нескольких изменений

### Data Requirements

| Quality | Runs | Confidence |
|---------|------|------------|
| High | 20+ | High |
| Medium | 10-19 | Medium |
| Low | 5-9 | Low |
| Insufficient | < 5 | Cannot simulate |
