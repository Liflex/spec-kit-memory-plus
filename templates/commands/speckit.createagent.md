# /speckit.createagent - Create AI Agent (Semi-Automatic)

Semi-automatic agent creation with AI-driven draft generation and user review.

---

## Workflow

```
1. AI analyzes request → determines agent type
2. AI generates draft → based on template
3. AI shows draft → user reviews
4. User confirms/adjusts → or asks for web research
5. AI applies changes → saves agent
```

---

## Step 1: Analyze Request

Analyze the user's request to determine what kind of agent is needed.

Look for keywords:
- **frontend**: frontend, react, vue, angular, ui, css, interface
- **backend**: backend, api, server, database, rest, graphql
- **fullstack**: fullstack, full-stack, full stack
- **architect**: architect, architecture, system design
- **qa-tester**: test, qa, quality, tester
- **devops**: devops, ci/cd, docker, kubernetes, deployment
- **data-engineer**: data, etl, pipeline, big data
- **ml-engineer**: ml, machine learning, ai, model

Use Python to analyze:
```python
from specify_cli.memory.agents.skill_workflow import SemiAutomaticAgentCreator

creator = SemiAutomaticAgentCreator()
analysis = creator.analyze_request("USER_REQUEST_HERE")

print(f"Suggested template: {analysis['suggested_template']}")
print(f"Confidence: {analysis['confidence']}")
print(f"Available templates: {analysis['available_templates']}")
```

---

## Step 2: Generate Draft

Generate agent draft based on the suggested template (or user-specified one).

```python
# Generate draft
result = creator.generate_draft(
    agent_name="AGENT_NAME",
    base_template=analysis['suggested_template'],  # or user-specified
    customizations={
        # Optional overrides
        "role": "Custom role description",
        "skills": ["skill1", "skill2"],
        "personality": "Agent personality traits",
        "team": ["other-agent-1", "other-agent-2"]
    }
)

# Show draft files to user
for filename, content in result['files'].items():
    print(f"\n=== {filename} ===")
    print(content)
```

---

## Step 3: Show Draft to User

Present the generated draft files clearly:

```markdown
## Generated Agent: {agent_name}

**Template**: {base_template}
**Role**: {role}

### AGENTS.md
```markdown
{content}
```

### SOUL.md
```markdown
{content}
```

### USER.md
```markdown
{content}
```

### MEMORY.md
```markdown
{content}
```

---

**Options:**
1. ✅ **Confirm** - Save agent as-is
2. ✏️ **Edit** - Request changes (e.g., "add Django skills", "change personality")
3. 🔍 **Research** - Search web for best practices (e.g., "search for Python code review best practices")
4. 🔄 **Different template** - Start over with different base template
5. ❌ **Cancel** - Discard draft
```

---

## Step 4: Apply User Feedback

Based on user response:

### Option 1: Confirm - Save Agent
```python
saved = creator.save_agent()
print(f"Agent saved to: {saved}")
```

### Option 2: Edit - Apply Changes
```python
result = creator.apply_feedback({
    "add_skills": ["Django", "FastAPI", "SQLAlchemy"],
    "remove_skills": ["Express"],
    "update_personality": "More focused on code quality and security"
})

# Show updated draft
for filename, content in result['files'].items():
    print(f"\n=== {filename} (updated) ===")
    print(content)
```

### Option 3: Research - Search Web
```
Use WebSearch to find best practices, then apply findings:

1. Search for: "{topic} best practices"
2. Extract relevant skills/patterns
3. Apply to draft with creator.apply_feedback()
```

### Option 4: Different Template
```python
creator.cancel_draft()
# Go back to Step 2 with different template
```

### Option 5: Cancel
```python
creator.cancel_draft()
```

---

## Available Templates

| Template | Role | Key Skills |
|----------|------|------------|
| `frontend-dev` | Frontend Developer | React, TypeScript, CSS, Accessibility |
| `backend-dev` | Backend Developer | API design, Databases, Auth, Security |
| `fullstack-dev` | Fullstack Developer | Frontend + Backend + DevOps basics |
| `architect` | Software Architect | System design, Scalability, Security |
| `qa-tester` | QA Tester | Test automation, Edge cases, Quality |
| `devops` | DevOps Engineer | CI/CD, Docker, Kubernetes, Monitoring |
| `data-engineer` | Data Engineer | ETL, Pipelines, SQL optimization |
| `ml-engineer` | ML Engineer | Model training, Deployment, Python ML |

---

## Example Session

```
User: /speckit.createagent Need an agent for Python code review

AI: Analyzing request...
    Suggested template: backend-dev
    Confidence: medium

    Generating draft based on "backend-dev"...

    === AGENTS.md ===
    # python-code-reviewer
    > Role: Python Code Reviewer Agent
    > Base Template: backend-dev

    ## Skills
    - PEP8 and code style
    - Type hints validation
    - Security patterns
    - async/await patterns
    - Error handling

    [Shows full draft]

    Options:
    1. ✅ Confirm
    2. ✏️ Edit
    3. 🔍 Research
    4. ❌ Cancel

User: Add Django and SQL injection detection skills

AI: Applying feedback...

    Updated skills:
    - PEP8 and code style
    - Type hints validation
    - Security patterns
    - async/await patterns
    - Error handling
    - Django best practices ✨ NEW
    - SQL injection detection ✨ NEW

    [Shows updated draft]

User: Looks good, confirm

AI: Saving agent...
    Created: ~/.claude/agents/python-code-reviewer/
    - AGENTS.md
    - SOUL.md
    - USER.md
    - MEMORY.md
    - memory/

    Agent "python-code-reviewer" ready for use!
```

---

## Files Generated

Each agent gets:

```
~/.claude/agents/{agent-name}/
├── AGENTS.md      # Role, team, skills
├── SOUL.md        # Personality, principles, communication style
├── USER.md        # User profile and preferences
├── MEMORY.md      # Knowledge summary
└── memory/
    ├── lessons.md      # Learned rules (3+ repeats)
    ├── patterns.md     # Improvement patterns
    ├── projects-log.md # Task history
    ├── architecture.md # Decisions
    └── handoff.md      # Session context
```

---

## Security

All created agents are scanned with the two-level security system:
- **Level 1**: Static analysis (prompt injection, data exfiltration)
- **Level 2**: LLM review (intent mismatch, obfuscation)

See: docs/security-scanning.md