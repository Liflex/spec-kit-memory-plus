# Подсистемы управления качеством

Spec Kit включает подсистемы для отслеживания и улучшения качества. Каждая решает конкретную задачу и может использоваться самостоятельно.

> Когда и зачем использовать каждую подсистему --- см. [Руководство по использованию](usage-guide.md#управление-качеством).

---

## Quality Goals --- цели качества

**Задача:** формализовать целевые показатели и отслеживать прогресс.

**Когда полезно:** вы хотите не просто "проверять", а целенаправленно улучшать качество до конкретного уровня.

```bash
/speckit.goals create --type target_score --target 0.90
/speckit.goals check
/speckit.goals suggest
```

**Типы целей:**
- `target_score` --- достичь определённого балла (напр. 0.90)
- `pass_rate` --- процент успешных прохождений
- `category` --- score по конкретной категории (security, performance...)
- `streak` --- серия успешных запусков подряд
- `improvement` --- улучшение по сравнению с прошлым запуском
- `stability` --- стабильность результатов (малый разброс)

---

## Quality History --- история запусков

**Задача:** хранить результаты всех запусков loop и показывать тренды.

**Когда полезно:** после 5+ запусков, чтобы видеть динамику: качество растёт или падает?

```bash
/speckit.history list --runs 10     # Последние 10 запусков
/speckit.history stats              # Среднее, медиана, тренд
/speckit.history compare --runs 5   # Сравнение запусков
```

---

## Quality Insights --- ИИ-рекомендации

**Задача:** анализ паттернов в истории запусков и генерация рекомендаций.

**Когда полезно:** накопилось 10+ запусков, хотите понять что улучшать в первую очередь.

```bash
/speckit.insights generate    # Создать рекомендации
/speckit.insights optimize    # Предложения по оптимизации настроек
```

**Типы инсайтов:** распознавание паттернов, анализ трендов, предиктивная аналитика, root cause analysis, action items.

---

## Gate Policies --- политики шлюзов

**Задача:** определить критерии "пройдено/не пройдено" для разных окружений.

**Когда полезно:** настраиваете CI/CD или хотите разные уровни строгости.

```bash
/speckit.gates list
/speckit.gates recommend
/speckit.gates compare --policies production,staging
```

**Встроенные политики:**

| Политика | Строгость | Описание |
|----------|-----------|----------|
| `production` | Высокая | 0 critical failures, score >= 0.85 |
| `staging` | Средняя | Допускает 1-2 warning |
| `ci` | Быстрая | Только critical rules |
| `development` | Низкая | Информирует, не блокирует |
| `strict` | Максимальная | Всё должно проходить |
| `lenient` | Минимальная | Только критические ошибки |

---

## QA Dashboard --- обзор

**Задача:** единая точка входа для быстрой оценки состояния качества.

**Когда полезно:** утренний check, перед release, для менеджмента.

```bash
/speckit.qa overview              # Текущее состояние
/speckit.qa check                 # Быстрая проверка
/speckit.qa compare --runs 5      # Сравнение
/speckit.qa trends --forecast     # Тренды с прогнозом
```

---

## Quality Alerts --- оповещения

**Задача:** проактивно сигнализировать о проблемах (падение score, провал целей, стагнация).

**Когда полезно:** хотите знать о проблемах до того, как они станут критичными.

```bash
/speckit.alerts check                # Текущие алерты
/speckit.alerts history --hours 24   # За последние 24 часа
/speckit.alerts summary              # Сводка
```

**Типы алертов:** Critical Quality Drop, Goal Failed, Pass Rate Critical, Stagnation Detected, Critical Rules Fail, Declining Trend, Goal At Risk, Anomaly Detected.

---

## Quality Feedback Loop --- обратная связь

**Задача:** адаптивная настройка loop на основе результатов. Анализирует что работает, предлагает улучшения конфигурации.

**Когда полезно:** запускаете loop регулярно и хотите оптимизировать параметры.

```bash
# Шаг 1: запустить loop с сбором feedback
/speckit.loop --criteria backend --collect-feedback

# Шаг 2: проанализировать
/speckit.feedback analyze
/speckit.feedback suggestions
/speckit.feedback trends
```

---

## Quality Plans --- планы улучшения

**Задача:** комплексные стратегии, объединяющие loop configs, goals, gates и profiles в один пакет.

**Когда полезно:** хотите одной командой настроить все аспекты контроля качества.

```bash
/speckit.plans                              # Список планов
/speckit.plans --show production-ready      # Детали
/speckit.plans --apply quick-start          # Применить
/speckit.plans --recommend production       # Рекомендации
/speckit.plans --wizard                     # Интерактивный мастер
```

**Пресеты:** quick-start, production-ready, continuous-improvement, security-focus, performance-focus, stability, aggressive, ci-cd.

---

## Loop Configurations --- конфигурации

**Задача:** сохранять и переиспользовать наборы настроек quality loop.

**Когда полезно:** часто запускаете loop с одинаковыми параметрами.

```bash
# Сохранить
/speckit.loop --criteria backend,security --gate-preset production --save-config my-config

# Загрузить
/speckit.loop --config my-config

# Список
/speckit.configs list
```

**Стандартные пресеты:** production-strict, ci-standard, development-quick, security-focused, frontend-qa, fullstack-comprehensive, api-focused, mobile-app-qa.

---

## Quality Anomalies --- обнаружение аномалий

**Задача:** статистическое обнаружение необычных результатов (резкие скачки/падения score).

**Когда полезно:** хотите автоматически детектировать нетипичные результаты.

```bash
/speckit.anomalies detect
/speckit.anomalies types
/speckit.anomalies recommend
```

---

## Quality Benchmarks --- бенчмарки

**Задача:** перцентильное ранжирование результатов и исторические baseline.

**Когда полезно:** хотите понять "0.85 --- это хорошо или плохо?" в контексте истории проекта.

```bash
/speckit.benchmarks create --name my-benchmark --runs 50
/speckit.benchmarks compare --category security
/speckit.benchmarks report --output report.json
```

**Уровни:**
- Excellent (90th+) --- Top 10%
- Above Average (75-90th) --- Top 25%
- Average (25-75th) --- Middle 50%
- Below Average (10-25th) --- Bottom 25%
- Poor (0-10th) --- Bottom 10%
