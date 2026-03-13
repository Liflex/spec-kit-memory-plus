# Templates & Blending

---

## Template Registry

Spec Kit включает 13 встроенных шаблонов критериев и систему для их комбинирования.

### Standalone CLI

```bash
python speckit_templates.py list                          # All templates
python speckit_templates.py list --category infrastructure
python speckit_templates.py info api-gateway              # Template details
python speckit_templates.py search security               # Search
python speckit_templates.py recommend web-app             # Recommendations
python speckit_templates.py stats                         # Statistics
python speckit_templates.py combinations                  # All combinations
```

### Compare & Diff

```bash
python speckit_templates.py compare frontend mobile backend
python speckit_templates.py compare api-spec graphql --diff
python speckit_templates.py diff backend frontend
```

---

## Template Blending

Комбинирование нескольких шаблонов в один.

```bash
python speckit_templates.py blend frontend backend --mode union
python speckit_templates.py blend security performance testing --mode consensus --name my-template
python speckit_templates.py blend backend api-spec --mode weighted --weights backend:0.7,api-spec:0.3 --output custom.yml
```

### Blend Modes

| Mode | Description |
|------|-------------|
| `union` | Все уникальные правила из всех шаблонов (полное покрытие) |
| `consensus` | Только правила, присутствующие в большинстве шаблонов (сбалансированно) |
| `weighted` | Взвешенный отбор с указанием влияния каждого шаблона |

### Examples

```bash
# Full-stack comprehensive
python speckit_templates.py blend frontend backend api-spec security testing docs \
  --mode union --name full-stack --output full-stack.yml

# Security-focused consensus
python speckit_templates.py blend security api-spec backend testing \
  --mode consensus --name security-focused

# Backend-heavy weighted
python speckit_templates.py blend backend frontend api-spec \
  --mode weighted --weights backend:0.6,frontend:0.25,api-spec:0.15 \
  --name backend-heavy --output backend-heavy.yml
```

---

## Blend Presets

Предварительно настроенные комбинации шаблонов.

```bash
python speckit_templates.py presets list
python speckit_templates.py presets list --tag web
python speckit_templates.py presets list --project-type microservice
python speckit_templates.py presets info full_stack_secure
python speckit_templates.py presets search security
python speckit_templates.py presets recommend web-app
python speckit_templates.py presets auto-detect
python speckit_templates.py presets auto-detect --verbose --project-root /path/to/project
python speckit_templates.py presets apply full_stack_secure --output stack.yml
```

### Available Presets

| Preset | Templates | Mode |
|--------|-----------|------|
| `full_stack_secure` | frontend, backend, api-spec, security, performance, testing | union |
| `microservices_robust` | api-gateway, service-mesh, backend, security, testing, infrastructure | consensus |
| `api_first` | api-spec, backend, security, docs, testing | union |
| `mobile_backend` | mobile, api-spec, backend, security, performance | union |
| `data_pipeline` | database, backend, performance, testing, docs | consensus |
| `cloud_native` | serverless, api-gateway, security, performance, infrastructure | union |
| `quality_rigorous` | testing, security, performance, docs, code-gen | union |
| `startup_mvp` | frontend, backend, api-spec, testing | consensus |
| `iot_platform` | backend, security, infrastructure, performance, testing | union |
| `devsecops` | security, infrastructure, terraform, testing, config | union |

n### Auto-Detection

Команда `auto-detect` анализирует кодовую базу и автоматически рекомендует подходящий пресет:

```bash
# Автоматическое определение пресета для текущего проекта
speckit templates presets auto-detect

# С подробной информацией и для другой директории
speckit templates presets auto-detect --verbose --project-root /path/to/project
```

Команда использует `ProfileDetector` для анализа файлов проекта (package.json, requirements.txt, и т.д.) и выбора наиболее подходящего пресета.
### Using Presets in Quality Loop

```bash
speckit loop --blend-preset full_stack_secure
speckit loop --blend-preset microservices_robust
speckit loop --project-type web-app  # Auto-selects full_stack_secure
```
