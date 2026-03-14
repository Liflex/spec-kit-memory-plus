"""
Skill Creation Workflow - Semi-automatic agent creation with search-before-create.

Integrates with SkillsMP to find existing agents/skills before creating new ones.
Supports semi-automatic mode: AI generates draft, user reviews and adjusts.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..logging import get_logger
from ..skillsmp.integration import SkillsMPIntegration
from .template_generator import AgentTemplateGenerator
from .agent_templates import (
    AGENT_TEMPLATES,
    get_template,
    list_templates,
    create_custom_template
)


class SemiAutomaticAgentCreator:
    """Semi-automatic agent creation workflow.

    Workflow:
    1. AI analyzes user request and determines agent type
    2. AI generates draft based on template
    3. AI shows draft to user for review
    4. User confirms, requests changes, or asks for web research
    5. AI applies changes and saves agent

    This class manages the state of an in-progress agent creation.
    """

    def __init__(self, memory_root: Optional[Path] = None):
        """Initialize semi-automatic creator.

        Args:
            memory_root: Root directory for memory files
        """
        self.logger = get_logger()
        self.memory_root = memory_root or Path.home() / ".claude" / "memory"

        # Current draft state
        self.current_draft: Optional[Dict[str, Any]] = None
        self.draft_files: Optional[Dict[str, str]] = None  # filename -> content

    def analyze_request(self, user_request: str) -> Dict[str, Any]:
        """Analyze user request and determine agent type.

        This is called by AI to understand what kind of agent is needed.

        Args:
            user_request: Natural language description of needed agent

        Returns:
            Analysis result with suggested template and customizations
        """
        # Keywords for template matching
        keywords = {
            "frontend": ["frontend", "react", "vue", "angular", "ui", "css", "компонент", "интерфейс"],
            "backend": ["backend", "api", "server", "database", "rest", "graphql", "сервер"],
            "fullstack": ["fullstack", "full-stack", "full stack", "полный стек"],
            "architect": ["architect", "architecture", "system design", "архитектор", "архитектура"],
            "qa-tester": ["test", "qa", "quality", "tester", "тест", "тестировщик"],
            "devops": ["devops", "ci/cd", "docker", "kubernetes", "deployment", "инфраструктура"],
            "data-engineer": ["data", "etl", "pipeline", "big data", "данные", "etl"],
            "ml-engineer": ["ml", "machine learning", "ai", "model", "машинное обучение"]
        }

        request_lower = user_request.lower()
        matched_template = None
        match_score = 0

        for template_name, template_keywords in keywords.items():
            score = sum(1 for kw in template_keywords if kw in request_lower)
            if score > match_score:
                match_score = score
                matched_template = template_name

        # Default to fullstack if no match
        if not matched_template:
            matched_template = "fullstack-dev"

        return {
            "user_request": user_request,
            "suggested_template": matched_template,
            "confidence": "high" if match_score >= 2 else "medium" if match_score == 1 else "low",
            "available_templates": list_templates(),
            "next_step": "generate_draft"
        }

    def generate_draft(
        self,
        agent_name: str,
        base_template: str = None,
        customizations: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate agent draft based on template and customizations.

        Args:
            agent_name: Name for the new agent
            base_template: Template to base draft on (e.g., "frontend-dev")
            customizations: Optional overrides for template fields

        Returns:
            Draft with files content for review
        """
        # Get base template
        if base_template and base_template in AGENT_TEMPLATES:
            template = get_template(base_template)
        else:
            template = get_template("fullstack-dev")

        # Apply customizations
        draft = {
            "name": agent_name,
            "role": customizations.get("role", template.get("role", f"Agent: {agent_name}")),
            "personality": customizations.get("personality", template.get("personality", "")),
            "team": customizations.get("team", template.get("team", [])),
            "skills": customizations.get("skills", template.get("skills", [])),
            "user_context": customizations.get("user_context", template.get("user_context", {})),
            "base_template": base_template
        }

        # Generate file contents (not saved yet, just for preview)
        self.draft_files = self._generate_draft_files(draft)
        self.current_draft = draft

        return {
            "draft": draft,
            "files": self.draft_files,
            "status": "ready_for_review",
            "next_step": "show_to_user"
        }

    def _generate_draft_files(self, draft: Dict[str, Any]) -> Dict[str, str]:
        """Generate file contents for draft without saving.

        Args:
            draft: Agent draft configuration

        Returns:
            Dict mapping filename to content
        """
        now = datetime.now().strftime("%Y-%m-%d")

        # AGENTS.md
        agents_content = f"""# {draft['name']}

> **Role**: {draft['role']}
> **Created**: {now}
> **Base Template**: {draft.get('base_template', 'custom')}
> **Memory System**: 4-Level (File + Vector + Context + Identity)

---

## Agent Role

{draft['role']}

---

## Team

"""
        for member in draft.get('team', []):
            agents_content += f"- **{member}**\n"
        if not draft.get('team'):
            agents_content += "_No team members defined_\n"

        agents_content += "\n## Skills\n\n"
        for skill in draft.get('skills', []):
            agents_content += f"- {skill}\n"
        if not draft.get('skills'):
            agents_content += "_No skills defined_\n"

        agents_content += """
## Memory Files

- **AGENTS.md** - This file (role, team, skills)
- **SOUL.md** - Personality and principles
- **USER.md** - User profile and preferences
- **MEMORY.md** - Knowledge summary
- **memory/** - 4-level memory files
"""

        # SOUL.md
        soul_content = f"""# {draft['name']} - Soul

> **Created**: {now}

---

## Personality

{draft.get('personality', 'Professional and constructive, focused on problem-solving.')}

---

## Core Principles

1. **Clarity First** - Communicate clearly and concisely
2. **Context Awareness** - Always consider memory context before acting
3. **Continuous Learning** - Learn from every interaction
4. **Graceful Degradation** - Function even when memory unavailable

---

## Communication Style

- **Tone**: Professional, direct, constructive
- **Language**: Russian (as requested)
- **Format**: Structured markdown with clear sections
"""

        # USER.md
        user_context = draft.get('user_context', {})
        user_content = f"""# User Profile

> **Last Updated**: {now}

---

## User Identity

"""
        if user_context.get('tech_stack'):
            user_content += f"**Preferred Stack**: {user_context['tech_stack']}\n"
        if user_context.get('editor'):
            user_content += f"**Editor**: {user_context['editor']}\n"

        user_content += f"""
---

## Work Style

{user_context.get('work_style', 'Detail-oriented but pragmatic, prefers working code over extensive documentation.')}
"""

        # MEMORY.md
        memory_content = f"""# {draft['name']} - Knowledge Summary

> **Role**: {draft['role']}
> **Last Updated**: {now}

---

## Quick Access

### Recent Lessons (5)
_See `memory/lessons.md` for full list_

### Active Patterns (5)
_See `memory/patterns.md` for full list_

---

## Memory Structure

This agent uses the **4-level memory system**:

1. **File-Based** (Level 1) - Structured markdown files
2. **Vector-Based** (Level 2) - Semantic search (if Ollama available)
3. **Contextual** (Level 3) - Session context with headers-first reading
4. **Identity** (Level 4) - AGENTS.md, SOUL.md, USER.md, MEMORY.md
"""

        return {
            "AGENTS.md": agents_content,
            "SOUL.md": soul_content,
            "USER.md": user_content,
            "MEMORY.md": memory_content
        }

    def apply_feedback(
        self,
        feedback: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply user feedback to current draft.

        Args:
            feedback: Dict with changes to apply:
                - add_skills: List of skills to add
                - remove_skills: List of skills to remove
                - update_role: New role description
                - update_personality: New personality
                - add_team: Team members to add
                - web_research_topic: Topic to search online

        Returns:
            Updated draft
        """
        if not self.current_draft:
            return {"error": "No draft in progress"}

        draft = self.current_draft.copy()

        # Apply skill changes
        if feedback.get("add_skills"):
            current_skills = set(draft.get("skills", []))
            draft["skills"] = list(current_skills | set(feedback["add_skills"]))

        if feedback.get("remove_skills"):
            current_skills = set(draft.get("skills", []))
            draft["skills"] = list(current_skills - set(feedback["remove_skills"]))

        # Apply other changes
        if feedback.get("update_role"):
            draft["role"] = feedback["update_role"]

        if feedback.get("update_personality"):
            draft["personality"] = feedback["update_personality"]

        if feedback.get("add_team"):
            current_team = set(draft.get("team", []))
            draft["team"] = list(current_team | set(feedback["add_team"]))

        # Regenerate files
        self.current_draft = draft
        self.draft_files = self._generate_draft_files(draft)

        return {
            "draft": draft,
            "files": self.draft_files,
            "status": "updated",
            "web_research_needed": feedback.get("web_research_topic")
        }

    def save_agent(self, agent_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Save current draft to disk.

        Args:
            agent_dir: Directory to save to (default: ~/.claude/agents/{name})

        Returns:
            Dict mapping file types to saved paths
        """
        if not self.current_draft or not self.draft_files:
            return {"error": "No draft to save"}

        agent_name = self.current_draft["name"]
        if agent_dir is None:
            agent_dir = self.memory_root.parent / "agents" / agent_name

        agent_dir.mkdir(parents=True, exist_ok=True)

        saved_files = {}
        for filename, content in self.draft_files.items():
            filepath = agent_dir / filename
            filepath.write_text(content, encoding="utf-8")
            saved_files[filename] = filepath
            self.logger.info(f"Saved: {filepath}")

        # Create memory subdirectory
        memory_dir = agent_dir / "memory"
        memory_dir.mkdir(exist_ok=True)

        # Create initial memory files
        for mem_file in ["lessons.md", "patterns.md", "projects-log.md", "architecture.md", "handoff.md"]:
            mem_path = memory_dir / mem_file
            if not mem_path.exists():
                mem_path.write_text(f"# {mem_file.replace('.md', '').title()}\n\n_No entries yet_\n", encoding="utf-8")

        saved_files["memory_dir"] = memory_dir

        # Clear draft state
        self.current_draft = None
        self.draft_files = None

        return saved_files

    def get_current_draft(self) -> Optional[Dict[str, Any]]:
        """Get current draft state.

        Returns:
            Current draft or None if no draft in progress
        """
        if self.current_draft:
            return {
                "draft": self.current_draft,
                "files": self.draft_files,
                "status": "in_progress"
            }
        return None

    def cancel_draft(self) -> None:
        """Cancel current draft."""
        self.current_draft = None
        self.draft_files = None


class SkillCreationWorkflow:
    """Workflow for creating agents with search-before-create pattern.

    Workflow:
    1. Define requirements (what agent needed)
    2. Search SkillsMP for existing agents
    3. Search GitHub as fallback
    4. Present options to user
    5a. Use existing agent OR
    5b. Create new agent with templates
    """

    def __init__(self, memory_root: Optional[Path] = None):
        """Initialize skill creation workflow.

        Args:
            memory_root: Root directory for memory files
        """
        self.logger = get_logger()
        self.memory_root = memory_root

        # Initialize components
        self.template_generator = AgentTemplateGenerator(memory_root=memory_root)
        self.semi_automatic = SemiAutomaticAgentCreator(memory_root=memory_root)
        self.skillsmp_integration = None

        # Try to initialize SkillsMP (optional)
        self._init_skillsmp()

    def _init_skillsmp(self) -> None:
        """Initialize SkillsMP integration if available."""
        try:
            self.skillsmp_integration = SkillsMPIntegration(
                global_home=self.memory_root or Path.home() / ".claude"
            )
            self.logger.info("SkillsMP integration available")
        except Exception as e:
            self.logger.warning(f"SkillsMP not available: {e}")
            self.skillsmp_integration = None

    def search_agents(
        self,
        query: str,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search for existing agents/skills.

        Args:
            query: Search query describing needed agent
            limit: Max results

        Returns:
            Search results with options
        """
        self.logger.info(f"=== Searching for Agents: '{query}' ===")

        results = {
            "query": query,
            "skillsmp": [],
            "github": [],
            "found": False
        }

        if self.skillsmp_integration:
            # Search SkillsMP first
            try:
                skillsmp_results = self.skillsmp_integration.search_skills(
                    query=query,
                    limit=limit
                )

                results["skillsmp"] = skillsmp_results
                if skillsmp_results:
                    results["found"] = True
                    self.logger.info(f"Found {len(skillsmp_results)} SkillsMP results")

            except Exception as e:
                self.logger.warning(f"SkillsMP search failed: {e}")

        # GitHub fallback if SkillsMP not available or no results
        if not results["found"]:
            try:
                github_results = self.skillsmp_integration.search_skills(
                    query=query,
                    limit=limit,
                    use_github_fallback=True
                )

                results["github"] = [r for r in github_results if r.get("source") == "github"]
                if results["github"]:
                    results["found"] = True
                    self.logger.info(f"Found {len(results['github'])} GitHub results")

            except Exception as e:
                self.logger.warning(f"GitHub search failed: {e}")

        return results

    def present_options(
        self,
        search_results: Dict[str, Any]
    ) -> str:
        """Present search options to user.

        Args:
            search_results: Results from search_agents()

        Returns:
            Formatted options text
        """
        output = f"\n=== Agent Search Results: '{search_results['query']}' ===\n\n"

        if not search_results["found"]:
            output += "No existing agents found.\n"
            output += "Recommendation: Create new agent from templates\n"
            return output

        # SkillsMP results
        if search_results["skillsmp"]:
            output += "## SkillsMP Agents (Verified)\n\n"
            for i, agent in enumerate(search_results["skillsmp"][:5], 1):
                title = agent.get("title", "Unknown")
                description = agent.get("description", "")
                stars = agent.get("github_stars", 0)

                output += f"{i}. **{title}**"
                if stars:
                    output += f" Stars: {stars}"
                output += "\n"

                if description:
                    output += f"   {description[:100]}...\n"
                output += "\n"

        # GitHub results
        if search_results["github"]:
            output += "## GitHub Agents (Community)\n\n"
            for i, agent in enumerate(search_results["github"][:5], 1):
                title = agent.get("title", "Unknown")
                description = agent.get("description", "")
                repo = agent.get("github_repo", "")

                output += f"{i}. **{title}**"
                if repo:
                    output += f" Repo: {repo}"
                output += "\n"

                if description:
                    output += f"   {description[:100]}...\n"
                output += "\n"

        output += "---\n\n"
        output += "**Options**:\n"
        output += "1. Use existing agent (specify number)\n"
        output += "2. Create new agent from templates\n"
        output += "3. Search with different query\n"

        return output

    def create_agent_from_requirements(
        self,
        agent_name: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Path]:
        """Create new agent from requirements.

        Args:
            agent_name: Name for new agent
            requirements: Agent requirements dict containing:
                - role: Primary role
                - personality: Optional personality traits
                - team: Optional team members
                - skills: Optional skill list
                - user_context: Optional user profile

        Returns:
            Dict mapping file types to created paths
        """
        self.logger.info(f"=== Creating Agent: {agent_name} ===")

        # Generate agent files
        created_files = self.template_generator.generate_agent(
            agent_name=agent_name,
            role=requirements.get("role", f"Agent for {agent_name}"),
            personality=requirements.get("personality"),
            team=requirements.get("team"),
            skills=requirements.get("skills"),
            user_context=requirements.get("user_context")
        )

        # Record in projects-log
        self._record_agent_creation(
            agent_name=agent_name,
            requirements=requirements
        )

        return created_files

    def _record_agent_creation(
        self,
        agent_name: str,
        requirements: Dict[str, Any]
    ) -> None:
        """Record agent creation in projects-log.

        Args:
            agent_name: Agent name
            requirements: Agent requirements
        """
        from ..file_manager import FileMemoryManager

        # Use a special "agents" project for tracking
        log_manager = FileMemoryManager(
            project_id="agents",
            memory_root=self.memory_root
        )

        # Build log entry
        title = f"Created agent: {agent_name}"
        content = f"""
### Agent Created

**Name**: {agent_name}
**Role**: {requirements.get('role', 'Not specified')}
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

### Requirements

"""
        for key, value in requirements.items():
            if value:
                content += f"- **{key}**: {value}\n"

        content += f"\n### Files Created\n\n"
        content += f"- AGENTS.md\n"
        content += f"- SOUL.md\n"
        content += f"- USER.md\n"
        content += f"- MEMORY.md\n"
        content += f"- memory/ (with 4-level memory system)\n"

        # Write to log
        log_manager.write_entry(
            file_type="log",
            title=title,
            content=content,
            one_liner=f"Agent {agent_name} created with 4-level memory"
        )

        self.logger.info(f"Recorded agent creation: {agent_name}")

    def get_agent_template(self, template_type: str) -> str:
        """Get predefined agent template.

        Args:
            template_type: Type of template (frontend, backend, fullstack, etc.)

        Returns:
            Template description
        """
        templates = {
            "frontend": {
                "role": "Frontend Developer Agent",
                "personality": "Creative and detail-oriented about UI/UX, focused on user experience",
                "skills": [
                    "React/Next.js development",
                    "TypeScript",
                    "CSS/Tailwind styling",
                    "Responsive design",
                    "Accessibility (WCAG)"
                ],
                "team": ["backend-dev", "tester"]
            },
            "backend": {
                "role": "Backend Developer Agent",
                "personality": "Analytical and systematic, focused on architecture and reliability",
                "skills": [
                    "API design (REST/GraphQL)",
                    "Database modeling",
                    "Authentication/authorization",
                    "Error handling and logging",
                    "Performance optimization"
                ],
                "team": ["frontend-dev", "architect"]
            },
            "fullstack": {
                "role": "Fullstack Developer Agent",
                "personality": "Versatile and adaptive, balance between frontend and backend",
                "skills": [
                    "Frontend: React/Next.js, TypeScript",
                    "Backend: Node.js, Express, PostgreSQL",
                    "API integration",
                    "DevOps basics",
                    "Testing (unit, integration)"
                ],
                "team": ["architect", "tester"]
            },
            "architect": {
                "role": "Software Architect Agent",
                "personality": "Strategic and forward-thinking, focused on scalability",
                "skills": [
                    "System design",
                    "Technology stack selection",
                    "Scalability patterns",
                    "Security architecture",
                    "Cost optimization"
                ],
                "team": ["frontend-dev", "backend-dev"]
            },
            "tester": {
                "role": "QA Tester Agent",
                "personality": "Thorough and skeptical, focused on quality and edge cases",
                "skills": [
                    "Test strategy design",
                    "Automation testing",
                    "Edge case identification",
                    "Performance testing",
                    "Security testing basics"
                ],
                "team": ["fullstack"]
            }
        }

        return templates.get(template_type, templates["fullstack"])

    def list_available_templates(self) -> List[str]:
        """List available agent templates.

        Returns:
            List of template names
        """
        return list_templates()
