"""
Quality Loop Data Models

Defines all data structures for quality evaluation and loop state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, List, Any
from enum import Enum


class Phase(Enum):
    """Quality loop phase"""
    A = "A"  # Base quality (threshold ~0.8)
    B = "B"  # Strict quality (threshold ~0.9)


class LoopStatus(Enum):
    """Loop execution status"""
    running = "running"
    completed = "completed"
    stopped = "stopped"
    failed = "failed"


class StopReason(Enum):
    """Reasons for loop stopping"""
    threshold_reached = "threshold_reached"
    no_major_issues = "no_major_issues"
    iteration_limit = "iteration_limit"
    stagnation = "stagnation"
    user_stop = "user_stop"
    error = "error"


class RuleSeverity(Enum):
    """Rule severity levels"""
    fail = "fail"  # Blocks passing, weight 2
    warn = "warn"  # Lowers score, weight 1
    info = "info"  # Tracking only, weight 0


class RuleCheckType(Enum):
    """Rule check types"""
    content = "content"  # Content analysis (regex, keywords)
    executable = "executable"  # Run script/test
    hybrid = "hybrid"  # Both content and executable


@dataclass
class QualityRule:
    """Single quality rule"""
    id: str
    description: str
    severity: RuleSeverity
    weight: int  # 2=fail, 1=warn, 0=info
    phase: Phase
    check: str  # Check description or pattern
    check_type: RuleCheckType = RuleCheckType.content
    domain_tags: List[str] = field(default_factory=list)  # Domain tags for priority scoring
    category: str = "general"  # Rule category: security, performance, testing, etc. (Exp 46)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "severity": self.severity.value,
            "weight": self.weight,
            "phase": self.phase.value,
            "check": self.check,
            "check_type": self.check_type.value,
            "domain_tags": self.domain_tags,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityRule":
        # Handle weight as string or int (from YAML parsing)
        weight = data["weight"]
        if isinstance(weight, str):
            weight = int(weight)
        return cls(
            id=data["id"],
            description=data["description"],
            severity=RuleSeverity(data["severity"]),
            weight=weight,
            phase=Phase(data["phase"]),
            check=data["check"],
            check_type=RuleCheckType(data.get("check_type", "content")),
            domain_tags=data.get("domain_tags", []),
            category=data.get("category", "general"),
        )

    def get_effective_weight(self, multipliers: Dict[str, float], category_multipliers: Optional[Dict[str, float]] = None) -> float:
        """Calculate effective weight with domain and category multipliers

        Args:
            multipliers: Domain tag multipliers from priority profile
            category_multipliers: Category multipliers from priority profile (Exp 46)

        Returns:
            Effective weight (weight * domain_multiplier * category_multiplier)
        """
        if category_multipliers is None:
            category_multipliers = {}

        # Get domain multiplier (max of matching domain tags)
        domain_multiplier = 1.0
        if self.domain_tags and multipliers:
            for tag in self.domain_tags:
                if tag in multipliers:
                    domain_multiplier = max(domain_multiplier, multipliers[tag])

        # Get category multiplier
        category_multiplier = category_multipliers.get(self.category, 1.0)

        # Apply both multipliers
        return self.weight * domain_multiplier * category_multiplier


@dataclass
class PhaseConfig:
    """Configuration for a phase"""
    threshold: float
    active_levels: List[str] = field(default_factory=lambda: ["A"])

    def to_dict(self) -> Dict[str, Any]:
        return {
            "threshold": self.threshold,
            "active_levels": self.active_levels,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PhaseConfig":
        return cls(
            threshold=data["threshold"],
            active_levels=data.get("active_levels", ["A"]),
        )


@dataclass
class PriorityProfile:
    """Priority profile with domain and category multipliers"""
    name: str
    multipliers: Dict[str, float] = field(default_factory=dict)  # domain_tag -> multiplier
    description: str = ""
    category_multipliers: Dict[str, float] = field(default_factory=dict)  # category -> multiplier (Exp 46)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "multipliers": self.multipliers,
            "description": self.description,
            "category_multipliers": self.category_multipliers,
        }

    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "PriorityProfile":
        # Handle both direct dict format and nested format
        if isinstance(data, dict) and "multipliers" in data:
            return cls(
                name=name,
                multipliers=data.get("multipliers", {}),
                description=data.get("description", ""),
                category_multipliers=data.get("category_multipliers", {}),
            )
        # Assume data is the multipliers dict directly (backward compat)
        return cls(
            name=name,
            multipliers=data,
            description="",
            category_multipliers={},
        )

    def get_multiplier(self, domain_tag: str) -> float:
        """Get multiplier for a domain tag

        Args:
            domain_tag: Domain tag to look up

        Returns:
            Multiplier value (default 1.0 if not found)
        """
        return self.multipliers.get(domain_tag, 1.0)

    def get_category_multiplier(self, category: str) -> float:
        """Get multiplier for a rule category

        Args:
            category: Category to look up

        Returns:
            Multiplier value (default 1.0 if not found)
        """
        return self.category_multipliers.get(category, 1.0)


@dataclass
class CriteriaTemplate:
    """Criteria template with rules and priority profiles"""
    name: str
    version: float
    description: str
    phases: Dict[str, PhaseConfig]  # "a", "b" -> PhaseConfig
    rules: List[QualityRule]
    priority_profiles: Dict[str, PriorityProfile] = field(default_factory=dict)  # profile_name -> PriorityProfile

    def get_phase_config(self, phase) -> Optional[PhaseConfig]:
        """Get configuration for a phase"""
        if isinstance(phase, Phase):
            key = phase.value.lower()
        else:
            key = str(phase).lower()
        return self.phases.get(key)

    def get_active_rules(self, phase) -> List[QualityRule]:
        """Get rules active in a phase"""
        config = self.get_phase_config(phase)
        if not config:
            return []

        active_levels = config.active_levels
        return [
            rule for rule in self.rules
            if (rule.phase.value if isinstance(rule.phase, Phase) else str(rule.phase)) in active_levels
        ]

    def get_priority_profile(self, profile_name: str, project_root: Optional[str] = None) -> Optional[PriorityProfile]:
        """Get priority profile by name (checks custom profiles first)

        Args:
            profile_name: Name of the priority profile
            project_root: Project root directory for custom profiles

        Returns:
            PriorityProfile or None if not found
        """
        # First check built-in profiles in template
        if profile_name in self.priority_profiles:
            return self.priority_profiles[profile_name]

        # Then check custom profiles from .speckit/priority-profiles.yml
        if project_root:
            from pathlib import Path
            from specify_cli.quality.priority_profiles import PriorityProfilesManager

            custom_file = Path(project_root) / ".speckit" / "priority-profiles.yml"
            if custom_file.exists():
                import yaml
                try:
                    with open(custom_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    if data and "priority_profiles" in data:
                        custom_profiles = data["priority_profiles"]
                        if profile_name in custom_profiles:
                            profile_data = custom_profiles[profile_name]
                            return PriorityProfile.from_dict(profile_name, profile_data)
                except (yaml.YAMLError, IOError, OSError):
                    pass

        return None

    def list_priority_profiles(self, project_root: Optional[str] = None) -> List[str]:
        """List available priority profile names (built-in + custom)

        Args:
            project_root: Project root directory for custom profiles

        Returns:
            List of profile names
        """
        # Start with built-in profiles
        profile_names = list(self.priority_profiles.keys())

        # Add custom profiles
        if project_root:
            from pathlib import Path
            from specify_cli.quality.priority_profiles import PriorityProfilesManager

            custom_file = Path(project_root) / ".speckit" / "priority-profiles.yml"
            if custom_file.exists():
                import yaml
                try:
                    with open(custom_file, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)

                    if data and "priority_profiles" in data:
                        custom_names = list(data["priority_profiles"].keys())
                        # Add custom profiles not already in built-in
                        for name in custom_names:
                            if name not in profile_names:
                                profile_names.append(name)
                except (yaml.YAMLError, IOError, OSError):
                    pass

        return profile_names

    def get_default_profile(self) -> PriorityProfile:
        """Get default priority profile (creates if not exists)

        Returns:
            PriorityProfile with default multipliers (all 1.0)
        """
        if "default" in self.priority_profiles:
            return self.priority_profiles["default"]

        # Create default profile if not exists
        default_profile = PriorityProfile(
            name="default",
            multipliers={
                "web": 1.0,
                "api": 1.0,
                "data": 1.0,
                "infrastructure": 1.0,
                "mobile": 1.0,
                "ml": 1.0,
                "graphql": 1.0,
                "microservices": 1.0,
                "async": 1.0,
                "auth": 1.0,
            },
            description="Default profile with neutral multipliers"
        )
        self.priority_profiles["default"] = default_profile
        return default_profile

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "phases": {
                k: v.to_dict() for k, v in self.phases.items()
            },
            "rules": [rule.to_dict() for rule in self.rules],
            "priority_profiles": {
                k: v.to_dict() for k, v in self.priority_profiles.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CriteriaTemplate":
        phases = {
            k: PhaseConfig.from_dict(v)
            for k, v in data["phases"].items()
        }
        rules = [
            QualityRule.from_dict(r)
            for r in data.get("rules", [])
        ]

        # Load priority profiles
        priority_profiles = {}
        if "priority_profiles" in data:
            for profile_name, profile_data in data["priority_profiles"].items():
                priority_profiles[profile_name] = PriorityProfile.from_dict(profile_name, profile_data)

        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            phases=phases,
            rules=rules,
            priority_profiles=priority_profiles,
        )


@dataclass
class FailedRule:
    """Failed rule result"""
    rule_id: str
    reason: str
    category: str = "general"  # Rule category: security, performance, testing, etc. (Exp 50)
    weight: int = 1  # Rule weight for critique prioritization (Exp 37)
    severity: str = "fail"  # Original rule severity: fail/warn/info (Exp 43)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "reason": self.reason,
            "category": self.category,
            "weight": self.weight,
            "severity": self.severity,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailedRule":
        return cls(
            rule_id=data["rule_id"],
            reason=data["reason"],
            category=data.get("category", "general"),
            weight=data.get("weight", 1),
            severity=data.get("severity", "fail"),
        )


@dataclass
class EvaluationResult:
    """Result of evaluating an artifact"""
    score: float  # 0.0 to 1.0
    passed: bool
    threshold: float
    phase: str
    passed_rules: List[str]
    failed_rules: List[FailedRule]
    warnings: List[FailedRule]
    evaluated_at: str
    priority_profile: Optional[str] = None  # Name of priority profile used (if any)
    # Exp 55: Quality gate support fields
    category_breakdown: Optional[Dict[str, Any]] = None  # Category breakdown for JSON reports
    category_scores: Optional[Dict[str, Dict[str, Any]]] = None  # Category scores for gate evaluation
    severity_counts: Optional[Dict[str, int]] = None  # Severity counts for gate evaluation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "passed": self.passed,
            "threshold": self.threshold,
            "phase": self.phase,
            "passed_rules": self.passed_rules,
            "failed_rules": [r.to_dict() for r in self.failed_rules],
            "warnings": [w.to_dict() for w in self.warnings],
            "evaluated_at": self.evaluated_at,
            "priority_profile": self.priority_profile,
            "category_breakdown": self.category_breakdown,
            "category_scores": self.category_scores,
            "severity_counts": self.severity_counts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EvaluationResult":
        return cls(
            score=data["score"],
            passed=data["passed"],
            threshold=data["threshold"],
            phase=data["phase"],
            passed_rules=data.get("passed_rules", []),
            failed_rules=[
                FailedRule.from_dict(r) for r in data.get("failed_rules", [])
            ],
            warnings=[
                FailedRule.from_dict(w) for w in data.get("warnings", [])
            ],
            evaluated_at=data["evaluated_at"],
            priority_profile=data.get("priority_profile"),
            category_breakdown=data.get("category_breakdown"),
            category_scores=data.get("category_scores"),
            severity_counts=data.get("severity_counts"),
        )


@dataclass
class CritiqueResult:
    """Result of critique generation"""
    issues: List[Dict[str, str]]  # Each has rule_id, reason, fix
    total_failed: int
    addressed: int
    skipped: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "issues": self.issues,
            "total_failed": self.total_failed,
            "addressed": self.addressed,
            "skipped": self.skipped,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CritiqueResult":
        return cls(
            issues=data.get("issues", []),
            total_failed=data["total_failed"],
            addressed=data["addressed"],
            skipped=data.get("skipped", 0),
        )


@dataclass
class LoopState:
    """State of a quality loop run"""
    run_id: str
    task_alias: str
    status: LoopStatus
    iteration: int
    max_iterations: int
    phase: Phase
    current_step: str
    current_score: Optional[float] = None
    last_score: Optional[float] = None
    evaluation: Optional[EvaluationResult] = None
    critique: Optional[CritiqueResult] = None
    stop: Optional[Dict[str, Any]] = None
    started_at: Optional[str] = None
    updated_at: Optional[str] = None
    priority_profile: Optional[str] = None  # Priority profile used for this run

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_alias": self.task_alias,
            "status": self.status.value if isinstance(self.status, LoopStatus) else str(self.status),
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "phase": self.phase.value if isinstance(self.phase, Phase) else str(self.phase),
            "current_step": self.current_step,
            "current_score": self.current_score,
            "last_score": self.last_score,
            "evaluation": self.evaluation if isinstance(self.evaluation, dict) else (self.evaluation.to_dict() if self.evaluation else None),
            "critique": self.critique if isinstance(self.critique, dict) else (self.critique.to_dict() if self.critique else None),
            "stop": self.stop,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "priority_profile": self.priority_profile,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopState":
        return cls(
            run_id=data["run_id"],
            task_alias=data["task_alias"],
            status=LoopStatus(data["status"]),
            iteration=data["iteration"],
            max_iterations=data["max_iterations"],
            phase=Phase(data["phase"]),
            current_step=data["current_step"],
            current_score=data.get("current_score"),
            last_score=data.get("last_score"),
            evaluation=EvaluationResult.from_dict(data["evaluation"]) if data.get("evaluation") else None,
            critique=CritiqueResult.from_dict(data["critique"]) if data.get("critique") else None,
            stop=data.get("stop"),
            started_at=data.get("started_at"),
            updated_at=data.get("updated_at"),
            priority_profile=data.get("priority_profile"),
        )


@dataclass
class LoopEvent:
    """Event in loop history"""
    timestamp: str
    event_type: str  # plan_created, evaluation_done, refinement_done, etc.
    iteration: Optional[int] = None
    phase: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "iteration": self.iteration,
            "phase": self.phase,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LoopEvent":
        return cls(
            timestamp=data["timestamp"],
            event_type=data["event_type"],
            iteration=data.get("iteration"),
            phase=data.get("phase"),
            details=data.get("details"),
        )

    def to_jsonl(self) -> str:
        """Convert to JSONL format"""
        import json
        return json.dumps(self.to_dict())
