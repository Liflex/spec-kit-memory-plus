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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "severity": self.severity.value,
            "weight": self.weight,
            "phase": self.phase.value,
            "check": self.check,
            "check_type": self.check_type.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QualityRule":
        return cls(
            id=data["id"],
            description=data["description"],
            severity=RuleSeverity(data["severity"]),
            weight=data["weight"],
            phase=Phase(data["phase"]),
            check=data["check"],
            check_type=RuleCheckType(data.get("check_type", "content")),
        )


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
class CriteriaTemplate:
    """Criteria template with rules"""
    name: str
    version: float
    description: str
    phases: Dict[str, PhaseConfig]  # "a", "b" -> PhaseConfig
    rules: List[QualityRule]

    def get_phase_config(self, phase: Phase) -> Optional[PhaseConfig]:
        """Get configuration for a phase"""
        key = phase.value.lower()
        return self.phases.get(key)

    def get_active_rules(self, phase: Phase) -> List[QualityRule]:
        """Get rules active in a phase"""
        config = self.get_phase_config(phase)
        if not config:
            return []

        active_levels = config.active_levels
        return [
            rule for rule in self.rules
            if rule.phase.value in active_levels
        ]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "phases": {
                k: v.to_dict() for k, v in self.phases.items()
            },
            "rules": [rule.to_dict() for rule in self.rules],
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
        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            phases=phases,
            rules=rules,
        )


@dataclass
class FailedRule:
    """Failed rule result"""
    rule_id: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FailedRule":
        return cls(
            rule_id=data["rule_id"],
            reason=data["reason"],
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "task_alias": self.task_alias,
            "status": self.status.value,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "phase": self.phase.value,
            "current_step": self.current_step,
            "current_score": self.current_score,
            "last_score": self.last_score,
            "evaluation": self.evaluation.to_dict() if self.evaluation else None,
            "critique": self.critique.to_dict() if self.critique else None,
            "stop": self.stop,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
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
