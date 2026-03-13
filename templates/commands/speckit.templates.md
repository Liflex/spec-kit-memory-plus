---
name: templates
version: 1.0.0
description: |
  Quality Template Registry and Discovery (Exp 125)

  Provides a central registry for all quality templates with discovery,
  metadata extraction, and template combination recommendations.
---

# Quality Template Registry and Discovery

> **Experiment 125:** Central registry for quality template discovery and recommendations

The Template Registry provides visibility into all available quality templates, their metadata, and recommended combinations for different project types.

## Commands

### List All Templates

```bash
# List all available templates
speckit templates list

# List only built-in templates
speckit templates list --builtin

# List templates by category
speckit templates list --category infrastructure
speckit templates list --category core

# Show detailed information
speckit templates list --details
```

**Output:**
```
==================================================================================================
Name                      Version    Category         Rules     Description
==================================================================================================
Api Spec                  1.3        core             15        API specification quality rules (OpenAPI/Swagger/GraphQL)
Api Gateway               1.0        infrastructure   52        Quality rules for API Gateway configuration
Backend                   1.3        core             18        Backend development quality rules
Cache                     1.0        infrastructure   35        Caching strategy and implementation quality rules
Container                 1.0        infrastructure   28        Container and containerization quality rules
Database                  1.3        core             20        Database design and query quality rules
Desktop                   1.0        architecture     15        Desktop application quality rules
Docs                      1.3        core             12        Documentation quality and completeness rules
Frontend                  1.3        core             22        Frontend development quality rules
Grpc                      1.0        architecture     18        gRPC service quality rules
Infrastructure            1.3        core             16        Infrastructure and DevOps quality rules
Message Queue             1.0        infrastructure   25        Message queue and event-driven quality rules
Mobile                    1.0        domain           20        Mobile application quality rules
Performance               1.3        core             25        Performance optimization quality rules
Security                  1.3        core             30        Security and vulnerability prevention rules
Serverless                1.0        infrastructure   22        Serverless and FaaS quality rules
Service Mesh              1.0        infrastructure   18        Service mesh configuration quality rules
Testing                   1.3        core             25        Test quality and coverage rules
Terraform                 1.0        infrastructure   20        Terraform and IaC quality rules
Ui Ux                     1.3        core             15        UI/UX quality rules
Websocket                 1.0        infrastructure   12        WebSocket implementation quality rules
==================================================================================================
Total: 21 templates | Built-in: 13 | Custom: 8 | Total Rules: 406
```

### Show Template Details

```bash
# Show detailed information about a specific template
speckit templates info <template-name>

# Example:
speckit templates info api-gateway
```

**Output:**
```
Template: API Gateway
Version: 1.0
Category: Infrastructure
File: src/specify_cli/quality/templates/api-gateway.yml

Description:
Quality rules for API Gateway configuration (Kong, AWS API Gateway, NGINX, Traefik, Envoy)

Statistics:
  Rules: 52
  Severity Breakdown:
    fail: 12
    warn: 35
    info: 5

Domain Tags:
  api, auth, gateway, infrastructure, performance, caching, async, reliability

Priority Profiles:
  - default
  - web-app
  - mobile-app
  - ml-service
  - data-pipeline
  - graphql-api
  - microservice

Phases:
  - A (threshold: 0.8)
  - B (threshold: 0.9)

Compatible Templates:
  backend, infrastructure, security, performance, testing, service-mesh, terraform
```

### Search Templates

```bash
# Search templates by keyword
speckit templates search <query>

# Examples:
speckit templates search security
speckit templates search graphql
speckit templates search performance
speckit templates search api
```

### Get Recommendations

```bash
# Get template recommendations for a project type
speckit templates recommend <project-type>

# Examples:
speckit templates recommend web-app
speckit templates recommend microservice
speckit templates recommend ml-service
```

**Output:**
```
==================================================================================================
Combination                Use Case                        Templates
==================================================================================================
Full Stack Web App         Web application with            frontend, backend, api-spec,
                           frontend and backend            security, performance, testing,
                                                           docs
Microservices Platform     Microservices-based             api-gateway, service-mesh,
                           architecture                    backend, security, performance,
                                                           testing, infrastructure
==================================================================================================

Recommended: frontend, backend, api-spec, security, performance, testing, docs

Usage:
  speckit loop --criteria frontend,backend,api-spec,security,performance,testing,docs
```

### Show Template Statistics

```bash
# Show overall statistics
speckit templates stats
```

**Output:**
```
Quality Template Registry Statistics

Templates:
  Total: 21
  Built-in: 13
  Custom: 8

By Category:
  core: 13
  infrastructure: 8
  architecture: 2
  domain: 1

Rules:
  Total Rules: 406
  Average Rules per Template: 19.3

Most Popular Domain Tags:
  - api: 8 templates
  - infrastructure: 7 templates
  - web: 6 templates
  - security: 6 templates
  - performance: 5 templates
```

## Recommended Template Combinations

### Full Stack Web Application
```bash
speckit loop --criteria frontend,backend,api-spec,security,performance,testing,docs
```
**Use case:** Web application with frontend and backend components

### Microservices Platform
```bash
speckit loop --criteria api-gateway,service-mesh,backend,security,performance,testing,infrastructure
```
**Use case:** Microservices-based distributed architecture

### ML/Data Pipeline
```bash
speckit loop --criteria database,backend,performance,testing,docs,config
```
**Use case:** Machine learning or data processing pipeline

### Mobile App with API
```bash
speckit loop --criteria mobile,api-spec,backend,security,performance,testing
```
**Use case:** Mobile application with backend API

### GraphQL API Service
```bash
speckit loop --criteria api-spec,backend,security,performance,testing,docs
```
**Use case:** GraphQL API service

### Serverless Application
```bash
speckit loop --criteria serverless,api-gateway,security,performance,testing,docs
```
**Use case:** Serverless/FaaS application

### Desktop Application
```bash
speckit loop --criteria desktop,backend,security,testing,docs
```
**Use case:** Desktop application (Electron, Tauri, native)

### Infrastructure as Code
```bash
speckit loop --criteria terraform,infrastructure,container,config,security
```
**Use case:** Infrastructure as Code projects

## Integration with Quality Loop

The template registry integrates seamlessly with the quality loop:

```bash
# 1. Discover available templates
speckit templates list

# 2. Get recommendations for your project
speckit templates recommend web-app

# 3. Use recommended templates in quality loop
speckit loop --criteria frontend,backend,api-spec,security,performance,testing,docs
```

## Programmatic Usage

```python
from specify_cli.quality import get_registry, print_template_table

# Get the registry
registry = get_registry()

# List all templates
templates = registry.list_templates()
print(print_template_table(templates))

# Get template metadata
template = registry.get_template("api-gateway")
print(f"{template.display_name}: {template.rule_count} rules")

# Search templates
results = registry.search_templates("security")

# Get recommendations
recommendations = registry.get_recommendations("web-app")

# Get statistics
stats = registry.get_template_stats()
```

## Template Categories

- **Core (13 templates):** Original built-in criteria for common software quality concerns
- **Infrastructure (8 templates):** Infrastructure and DevOps related quality rules
- **Architecture (2 templates):** Architecture pattern specific rules
- **Domain (1 template):** Domain-specific rules (e.g., mobile)
