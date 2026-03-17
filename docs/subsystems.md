# Подсистемы управления качеством

Spec Kit включает минимальный набор подсистем для контроля качества. Основной инструмент --- `/speckit.loop`.

---

## Quality Loop --- ядро системы

Итеративная оценка и улучшение кода: evaluate -> score -> critique -> refine -> repeat.

```bash
/speckit.loop --criteria backend
/speckit.loop --criteria backend,security,testing
/speckit.loop --project-type web-app
```

Подробнее: [Quality Loop](quality-loop.md)

---

## Templates --- шаблоны критериев

Управление шаблонами критериев качества: просмотр, поиск, сравнение, комбинирование.

```bash
/speckit.templates list
/speckit.templates info backend
/speckit.templates recommend web-app
```

Подробнее: [Шаблоны](templates.md)

---

## Plans --- планы качества

Сохраненные конфигурации loop с пресетами для разных сценариев.

```bash
/speckit.plans                          # Список планов
/speckit.plans --show production-ready  # Детали
/speckit.plans --apply quick-start      # Применить
```

**Пресеты:** quick-start, production-ready, continuous-improvement, security-focus, performance-focus, stability, aggressive, ci-cd.

---

## Внутренние компоненты (без standalone-команд)

Эти компоненты используются внутри loop, но не имеют отдельных команд:

- **Priority Profiles** --- взвешенный скоринг по типу проекта (web-app, microservice, ml-service). Используется через `--priority-profile` в loop.
- **Gate Policies** --- политики pass/fail для CI/CD (production, staging, development). Используется через `--gate-preset` в loop.
