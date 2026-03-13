"""
Quality Gate Policies

Advanced quality gate system with category and severity-based rules.
Supports preset profiles for different environments (production, staging, development, ci).

Exp 56: YAML config loader, gate policy validation, and enhanced management.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json


class GateResult(Enum):
    """Quality gate result"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"


class ValidationError(Enum):
    """Gate policy validation error types"""
    INVALID_THRESHOLD = "invalid_threshold"
    INVALID_SEVERITY_LIMIT = "invalid_severity_limit"
    INVALID_CATEGORY_LIMIT = "invalid_category_limit"
    INVALID_CATEGORY_SCORE = "invalid_category_score"
    DUPLICATE_POLICY_NAME = "duplicate_policy_name"
    MISSING_REQUIRED_FIELD = "missing_required_field"


@dataclass
class ValidationIssue:
    """Validation issue for gate policy"""
    error_type: ValidationError
    field: str
    message: str
    policy_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "field": self.field,
            "message": self.message,
            "policy_name": self.policy_name,
        }


@dataclass
class SeverityGate:
    """Severity-based gate rule"""
    critical_max: int = 0  # Maximum allowed critical issues
    high_max: int = 0  # Maximum allowed high issues
    medium_max: int = 5  # Maximum allowed medium issues
    low_max: int = 999  # Maximum allowed low issues (effectively no limit)
    info_max: int = 999  # Maximum allowed info issues

    def check(self, severity_counts: Dict[str, int]) -> tuple[bool, List[str]]:
        """Check if severity counts are within limits

        Args:
            severity_counts: Dict with severity counts (critical, high, medium, low, info)

        Returns:
            Tuple of (passed, violation_messages)
        """
        violations = []

        if severity_counts.get("critical", 0) > self.critical_max:
            violations.append(
                f"Critical issues ({severity_counts['critical']}) exceed maximum ({self.critical_max})"
            )

        if severity_counts.get("high", 0) > self.high_max:
            violations.append(
                f"High issues ({severity_counts['high']}) exceed maximum ({self.high_max})"
            )

        if severity_counts.get("medium", 0) > self.medium_max:
            violations.append(
                f"Medium issues ({severity_counts['medium']}) exceed maximum ({self.medium_max})"
            )

        if severity_counts.get("low", 0) > self.low_max:
            violations.append(
                f"Low issues ({severity_counts['low']}) exceed maximum ({self.low_max})"
            )

        return len(violations) == 0, violations

    def validate(self) -> List[ValidationIssue]:
        """Validate severity gate configuration

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check that severity limits are non-negative
        if self.critical_max < 0:
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_SEVERITY_LIMIT,
                field="critical_max",
                message=f"critical_max must be >= 0, got {self.critical_max}"
            ))

        if self.high_max < 0:
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_SEVERITY_LIMIT,
                field="high_max",
                message=f"high_max must be >= 0, got {self.high_max}"
            ))

        if self.medium_max < 0:
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_SEVERITY_LIMIT,
                field="medium_max",
                message=f"medium_max must be >= 0, got {self.medium_max}"
            ))

        if self.low_max < 0:
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_SEVERITY_LIMIT,
                field="low_max",
                message=f"low_max must be >= 0, got {self.low_max}"
            ))

        if self.info_max < 0:
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_SEVERITY_LIMIT,
                field="info_max",
                message=f"info_max must be >= 0, got {self.info_max}"
            ))

        # Check logical ordering (critical <= high <= medium <= low <= info)
        if not (self.critical_max <= self.high_max <= self.medium_max <= self.low_max <= self.info_max):
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_SEVERITY_LIMIT,
                field="severity_ordering",
                message="Severity limits should follow: critical <= high <= medium <= low <= info"
            ))

        return issues


@dataclass
class CategoryGate:
    """Category-based gate rule"""
    category: str
    min_score: float = 0.0  # Minimum score for this category
    max_failed: int = 999  # Maximum failed rules in this category

    def check(self, category_score: float, failed_count: int) -> tuple[bool, List[str]]:
        """Check if category meets requirements

        Args:
            category_score: Score for this category (0.0 to 1.0)
            failed_count: Number of failed rules in this category

        Returns:
            Tuple of (passed, violation_messages)
        """
        violations = []

        if category_score < self.min_score:
            violations.append(
                f"Category '{self.category}' score ({category_score:.2f}) below minimum ({self.min_score:.2f})"
            )

        if failed_count > self.max_failed:
            violations.append(
                f"Category '{self.category}' failed rules ({failed_count}) exceed maximum ({self.max_failed})"
            )

        return len(violations) == 0, violations

    def validate(self) -> List[ValidationIssue]:
        """Validate category gate configuration

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check min_score is in valid range
        if not (0.0 <= self.min_score <= 1.0):
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_CATEGORY_SCORE,
                field="min_score",
                message=f"min_score must be between 0.0 and 1.0, got {self.min_score}",
                policy_name=self.category,
            ))

        # Check max_failed is non-negative
        if self.max_failed < 0:
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_CATEGORY_LIMIT,
                field="max_failed",
                message=f"max_failed must be >= 0, got {self.max_failed}",
                policy_name=self.category,
            ))

        return issues


@dataclass
class GatePolicy:
    """Quality gate policy definition

    A gate policy defines rules for quality evaluation:
    - Overall score threshold
    - Category-specific thresholds
    - Severity-based issue limits
    """
    name: str
    description: str
    overall_threshold: float = 0.8
    severity_gate: Optional[SeverityGate] = None
    category_gates: List[CategoryGate] = field(default_factory=list)
    block_on_failure: bool = True  # If True, gate failures block the action

    def __post_init__(self):
        """Initialize default severity gate if not provided"""
        if self.severity_gate is None:
            self.severity_gate = SeverityGate()

    def check(
        self,
        overall_score: float,
        category_scores: Dict[str, float],
        category_failed: Dict[str, int],
        severity_counts: Dict[str, int],
    ) -> tuple[GateResult, List[str]]:
        """Check if quality gate passes

        Args:
            overall_score: Overall quality score (0.0 to 1.0)
            category_scores: Dict mapping category name to score
            category_failed: Dict mapping category name to failed count
            severity_counts: Dict mapping severity to count

        Returns:
            Tuple of (result, messages)
        """
        all_messages = []
        failed = False
        warnings = []

        # Check overall score
        if overall_score < self.overall_threshold:
            failed = True
            all_messages.append(
                f"Overall score ({overall_score:.2f}) below threshold ({self.overall_threshold:.2f})"
            )

        # Check severity gates
        if self.severity_gate:
            passed, violations = self.severity_gate.check(severity_counts)
            if not passed:
                failed = True
                all_messages.extend(violations)

        # Check category gates
        for cat_gate in self.category_gates:
            cat_score = category_scores.get(cat_gate.category, 1.0)
            cat_failed = category_failed.get(cat_gate.category, 0)

            passed, violations = cat_gate.check(cat_score, cat_failed)
            if not passed:
                failed = True
                all_messages.extend(violations)

        # Determine result
        if failed:
            result = GateResult.FAILED if self.block_on_failure else GateResult.WARNING
        else:
            result = GateResult.PASSED

        return result, all_messages

    def validate(self) -> List[ValidationIssue]:
        """Validate gate policy configuration

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check name is provided
        if not self.name or not self.name.strip():
            issues.append(ValidationIssue(
                error_type=ValidationError.MISSING_REQUIRED_FIELD,
                field="name",
                message="Policy name is required"
            ))

        # Check overall_threshold is in valid range
        if not (0.0 <= self.overall_threshold <= 1.0):
            issues.append(ValidationIssue(
                error_type=ValidationError.INVALID_THRESHOLD,
                field="overall_threshold",
                message=f"overall_threshold must be between 0.0 and 1.0, got {self.overall_threshold}",
                policy_name=self.name,
            ))

        # Validate severity gate
        if self.severity_gate:
            issues.extend(self.severity_gate.validate())

        # Validate category gates
        for cat_gate in self.category_gates:
            issues.extend(cat_gate.validate())

        # Check for duplicate category gates
        category_names = [cg.category for cg in self.category_gates]
        duplicates = [name for name in set(category_names) if category_names.count(name) > 1]
        for dup in duplicates:
            issues.append(ValidationIssue(
                error_type=ValidationError.DUPLICATE_POLICY_NAME,
                field="category_gates",
                message=f"Duplicate category gate '{dup}'",
                policy_name=self.name,
            ))

        return issues


# Preset gate policies for different environments
GATE_PRESETS: Dict[str, GatePolicy] = {
    "production": GatePolicy(
        name="production",
        description="Strict quality gate for production deployments",
        overall_threshold=0.95,
        severity_gate=SeverityGate(
            critical_max=0,
            high_max=0,
            medium_max=2,
            low_max=5,
        ),
        category_gates=[
            CategoryGate("security", min_score=0.98, max_failed=0),
            CategoryGate("correctness", min_score=0.95, max_failed=1),
            CategoryGate("performance", min_score=0.90, max_failed=2),
        ],
        block_on_failure=True,
    ),
    "staging": GatePolicy(
        name="staging",
        description="Standard quality gate for staging environments",
        overall_threshold=0.85,
        severity_gate=SeverityGate(
            critical_max=0,
            high_max=2,
            medium_max=5,
            low_max=10,
        ),
        category_gates=[
            CategoryGate("security", min_score=0.90, max_failed=1),
            CategoryGate("correctness", min_score=0.85, max_failed=3),
        ],
        block_on_failure=True,
    ),
    "development": GatePolicy(
        name="development",
        description="Relaxed quality gate for development",
        overall_threshold=0.70,
        severity_gate=SeverityGate(
            critical_max=0,
            high_max=5,
            medium_max=10,
            low_max=999,
        ),
        category_gates=[
            CategoryGate("security", min_score=0.80, max_failed=3),
        ],
        block_on_failure=False,
    ),
    "ci": GatePolicy(
        name="ci",
        description="Quality gate for CI/CD pipelines with blocking on failures",
        overall_threshold=0.80,
        severity_gate=SeverityGate(
            critical_max=0,
            high_max=0,
            medium_max=3,
            low_max=10,
        ),
        category_gates=[
            CategoryGate("security", min_score=0.95, max_failed=0),
            CategoryGate("correctness", min_score=0.85, max_failed=2),
        ],
        block_on_failure=True,
    ),
    "strict": GatePolicy(
        name="strict",
        description="Ultra-strict quality gate for critical systems",
        overall_threshold=0.98,
        severity_gate=SeverityGate(
            critical_max=0,
            high_max=0,
            medium_max=0,
            low_max=2,
        ),
        category_gates=[
            CategoryGate("security", min_score=1.0, max_failed=0),
            CategoryGate("correctness", min_score=0.98, max_failed=0),
            CategoryGate("performance", min_score=0.95, max_failed=1),
            CategoryGate("quality", min_score=0.90, max_failed=2),
        ],
        block_on_failure=True,
    ),
    "lenient": GatePolicy(
        name="lenient",
        description="Very relaxed quality gate for experimental features",
        overall_threshold=0.60,
        severity_gate=SeverityGate(
            critical_max=0,
            high_max=10,
            medium_max=20,
            low_max=999,
        ),
        category_gates=[],
        block_on_failure=False,
    ),
}


class GatePolicyManager:
    """Manager for quality gate policies with YAML config support (Exp 56)"""

    @staticmethod
    def get_preset(name: str) -> Optional[GatePolicy]:
        """Get a preset gate policy by name

        Args:
            name: Policy name (production, staging, development, ci, strict, lenient)

        Returns:
            GatePolicy or None if not found
        """
        return GATE_PRESETS.get(name)

    @staticmethod
    def list_presets() -> List[str]:
        """List available preset names

        Returns:
            List of preset names
        """
        return list(GATE_PRESETS.keys())

    @staticmethod
    def create_custom_policy(
        name: str,
        description: str,
        overall_threshold: float = 0.8,
        severity_gate: Optional[SeverityGate] = None,
        category_gates: Optional[List[CategoryGate]] = None,
        block_on_failure: bool = True,
    ) -> GatePolicy:
        """Create a custom gate policy

        Args:
            name: Policy name
            description: Policy description
            overall_threshold: Overall score threshold (0.0 to 1.0)
            severity_gate: Optional severity gate rules
            category_gates: Optional list of category-specific gates
            block_on_failure: Whether failures should block

        Returns:
            New GatePolicy instance
        """
        return GatePolicy(
            name=name,
            description=description,
            overall_threshold=overall_threshold,
            severity_gate=severity_gate or SeverityGate(),
            category_gates=category_gates or [],
            block_on_failure=block_on_failure,
        )

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> GatePolicy:
        """Create gate policy from dict (e.g., from YAML config)

        Args:
            data: Policy data dict

        Returns:
            GatePolicy instance
        """
        severity_gate = None
        if "severity_gate" in data:
            sg = data["severity_gate"]
            severity_gate = SeverityGate(
                critical_max=sg.get("critical_max", 0),
                high_max=sg.get("high_max", 0),
                medium_max=sg.get("medium_max", 5),
                low_max=sg.get("low_max", 999),
                info_max=sg.get("info_max", 999),
            )

        category_gates = []
        for cg_data in data.get("category_gates", []):
            category_gates.append(
                CategoryGate(
                    category=cg_data["category"],
                    min_score=cg_data.get("min_score", 0.0),
                    max_failed=cg_data.get("max_failed", 999),
                )
            )

        return GatePolicy(
            name=data["name"],
            description=data.get("description", ""),
            overall_threshold=data.get("overall_threshold", 0.8),
            severity_gate=severity_gate,
            category_gates=category_gates,
            block_on_failure=data.get("block_on_failure", True),
        )

    @staticmethod
    def to_dict(policy: GatePolicy) -> Dict[str, Any]:
        """Convert gate policy to dict (for serialization)

        Args:
            policy: GatePolicy instance

        Returns:
            Dict representation
        """
        return {
            "name": policy.name,
            "description": policy.description,
            "overall_threshold": policy.overall_threshold,
            "severity_gate": {
                "critical_max": policy.severity_gate.critical_max,
                "high_max": policy.severity_gate.high_max,
                "medium_max": policy.severity_gate.medium_max,
                "low_max": policy.severity_gate.low_max,
                "info_max": policy.severity_gate.info_max,
            } if policy.severity_gate else None,
            "category_gates": [
                {
                    "category": cg.category,
                    "min_score": cg.min_score,
                    "max_failed": cg.max_failed,
                }
                for cg in policy.category_gates
            ],
            "block_on_failure": policy.block_on_failure,
        }

    @staticmethod
    def validate_policy(policy: GatePolicy) -> Tuple[bool, List[ValidationIssue]]:
        """Validate a gate policy

        Args:
            policy: GatePolicy to validate

        Returns:
            Tuple of (is_valid, issues)
        """
        issues = policy.validate()
        return len(issues) == 0, issues

    @staticmethod
    def load_from_yaml(yaml_content: str) -> Tuple[List[GatePolicy], List[ValidationIssue]]:
        """Load gate policies from YAML content (Exp 56)

        Args:
            yaml_content: YAML string containing policy definitions

        Returns:
            Tuple of (policies, validation_issues)
        """
        try:
            import yaml
        except ImportError:
            # If PyYAML is not available, return empty
            return [], [ValidationIssue(
                error_type=ValidationError.MISSING_REQUIRED_FIELD,
                field="yaml",
                message="PyYAML is not installed. Install with: pip install pyyaml"
            )]

        policies = []
        issues = []

        try:
            data = yaml.safe_load(yaml_content)
            if not data:
                return [], []

            policies_data = data.get("gate_policies", [])
            if not policies_data:
                return [], []

            # Check for duplicate policy names
            policy_names = []
            for pd in policies_data:
                name = pd.get("name", "")
                if name in policy_names:
                    issues.append(ValidationIssue(
                        error_type=ValidationError.DUPLICATE_POLICY_NAME,
                        field="name",
                        message=f"Duplicate policy name '{name}'",
                        policy_name=name,
                    ))
                policy_names.append(name)

            # Load policies
            for pd in policies_data:
                try:
                    policy = GatePolicyManager.from_dict(pd)
                    is_valid, policy_issues = GatePolicyManager.validate_policy(policy)
                    if is_valid:
                        policies.append(policy)
                    else:
                        issues.extend(policy_issues)
                except Exception as e:
                    issues.append(ValidationIssue(
                        error_type=ValidationError.MISSING_REQUIRED_FIELD,
                        field="policy",
                        message=f"Failed to load policy: {str(e)}"
                    ))

        except Exception as e:
            issues.append(ValidationIssue(
                error_type=ValidationError.MISSING_REQUIRED_FIELD,
                field="yaml",
                message=f"Failed to parse YAML: {str(e)}"
            ))

        return policies, issues

    @staticmethod
    def load_from_project(project_root: Optional[str] = None) -> Dict[str, GatePolicy]:
        """Load custom gate policies from project config (Exp 56)

        Looks for .speckit/gate-policies.yml in the project root.

        Args:
            project_root: Project root directory (defaults to current working directory)

        Returns:
            Dict mapping policy name to GatePolicy
        """
        if project_root is None:
            from pathlib import Path
            project_root = str(Path.cwd())

        config_path = Path(project_root) / ".speckit" / "gate-policies.yml"

        if not config_path.exists():
            # Try alternate extensions
            for ext in [".yaml", ".yaml.example"]:
                alt_path = Path(project_root) / ".speckit" / f"gate-policies{ext}"
                if alt_path.exists():
                    config_path = alt_path
                    break
            else:
                # No config file found
                return {}

        try:
            yaml_content = config_path.read_text(encoding="utf-8")
            policies, issues = GatePolicyManager.load_from_yaml(yaml_content)

            # Log validation issues if any (but don't fail)
            if issues:
                import sys
                print(f"Warning: Issues found in gate policies config: {len(issues)}", file=sys.stderr)
                for issue in issues[:5]:  # Show first 5 issues
                    print(f"  - {issue.message}", file=sys.stderr)

            # Return as dict
            return {policy.name: policy for policy in policies}

        except Exception as e:
            # Silently fail on config errors
            return {}

    @staticmethod
    def get_policy(name: str, project_root: Optional[str] = None) -> Optional[GatePolicy]:
        """Get a gate policy by name, checking both presets and project config (Exp 56)

        Args:
            name: Policy name
            project_root: Project root directory for custom policies

        Returns:
            GatePolicy or None if not found
        """
        # Check presets first
        preset = GatePolicyManager.get_preset(name)
        if preset:
            return preset

        # Check project config
        custom_policies = GatePolicyManager.load_from_project(project_root)
        return custom_policies.get(name)

    @staticmethod
    def list_all_policies(project_root: Optional[str] = None) -> List[str]:
        """List all available policies (presets + custom) (Exp 56)

        Args:
            project_root: Project root directory for custom policies

        Returns:
            List of policy names
        """
        policies = set(GatePolicyManager.list_presets())
        custom_policies = GatePolicyManager.load_from_project(project_root)
        policies.update(custom_policies.keys())
        return sorted(list(policies))

    @staticmethod
    def get_policy_summary(name: str, project_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a summary of a policy for display (Exp 57)

        Args:
            name: Policy name
            project_root: Project root for custom policies

        Returns:
            Dict with summary or None if not found
        """
        policy = GatePolicyManager.get_policy(name, project_root)
        if not policy:
            return None

        # Determine if preset or custom
        is_preset = name in GATE_PRESETS

        return {
            "name": policy.name,
            "description": policy.description,
            "overall_threshold": policy.overall_threshold,
            "is_preset": is_preset,
            "severity_limits": {
                "critical": policy.severity_gate.critical_max,
                "high": policy.severity_gate.high_max,
                "medium": policy.severity_gate.medium_max,
                "low": policy.severity_gate.low_max,
            } if policy.severity_gate else None,
            "category_count": len(policy.category_gates),
            "category_names": [cg.category for cg in policy.category_gates],
            "block_on_failure": policy.block_on_failure,
        }

    @staticmethod
    def show_policy(name: str, project_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get full details of a policy (Exp 57)

        Args:
            name: Policy name
            project_root: Project root for custom policies

        Returns:
            Dict with full policy details or None if not found
        """
        policy = GatePolicyManager.get_policy(name, project_root)
        if not policy:
            return None

        is_preset = name in GATE_PRESETS

        return {
            "name": policy.name,
            "description": policy.description,
            "overall_threshold": policy.overall_threshold,
            "is_preset": is_preset,
            "severity_gate": {
                "critical_max": policy.severity_gate.critical_max,
                "high_max": policy.severity_gate.high_max,
                "medium_max": policy.severity_gate.medium_max,
                "low_max": policy.severity_gate.low_max,
                "info_max": policy.severity_gate.info_max,
            } if policy.severity_gate else None,
            "category_gates": [
                {
                    "category": cg.category,
                    "min_score": cg.min_score,
                    "max_failed": cg.max_failed,
                }
                for cg in policy.category_gates
            ],
            "block_on_failure": policy.block_on_failure,
        }

    @staticmethod
    def compare_policies(*names: str, project_root: Optional[str] = None) -> List[Dict[str, Any]]:
        """Compare multiple policies side-by-side (Exp 57)

        Args:
            *names: Policy names to compare
            project_root: Project root for custom policies

        Returns:
            List of policy summaries for comparison
        """
        results = []
        for name in names:
            summary = GatePolicyManager.get_policy_summary(name, project_root)
            if summary:
                results.append(summary)
        return results

    @staticmethod
    def diff_policies(name1: str, name2: str, project_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Show differences between two policies (Exp 57)

        Args:
            name1: First policy name
            name2: Second policy name
            project_root: Project root for custom policies

        Returns:
            Dict with differences or None if either not found
        """
        policy1 = GatePolicyManager.get_policy(name1, project_root)
        policy2 = GatePolicyManager.get_policy(name2, project_root)

        if not policy1 or not policy2:
            return None

        # Calculate differences
        differences = {
            "policy1": name1,
            "policy2": name2,
            "overall_threshold": {
                "policy1": policy1.overall_threshold,
                "policy2": policy2.overall_threshold,
                "diff": policy2.overall_threshold - policy1.overall_threshold,
            },
            "severity_diff": {},
            "category_diff": {
                "only_in_policy1": [],
                "only_in_policy2": [],
                "both": [],
            },
            "block_on_failure_diff": {
                "policy1": policy1.block_on_failure,
                "policy2": policy2.block_on_failure,
                "same": policy1.block_on_failure == policy2.block_on_failure,
            },
        }

        # Severity differences
        if policy1.severity_gate and policy2.severity_gate:
            for severity in ["critical_max", "high_max", "medium_max", "low_max", "info_max"]:
                val1 = getattr(policy1.severity_gate, severity)
                val2 = getattr(policy2.severity_gate, severity)
                differences["severity_diff"][severity] = {
                    "policy1": val1,
                    "policy2": val2,
                    "diff": val2 - val1,
                    "same": val1 == val2,
                }

        # Category differences
        cats1 = {cg.category: cg for cg in policy1.category_gates}
        cats2 = {cg.category: cg for cg in policy2.category_gates}

        all_cat_names = set(cats1.keys()) | set(cats2.keys())
        for cat_name in sorted(all_cat_names):
            if cat_name in cats1 and cat_name in cats2:
                cg1 = cats1[cat_name]
                cg2 = cats2[cat_name]
                differences["category_diff"]["both"].append({
                    "category": cat_name,
                    "min_score_diff": cg2.min_score - cg1.min_score,
                    "max_failed_diff": cg2.max_failed - cg1.max_failed,
                    "same": cg1.min_score == cg2.min_score and cg1.max_failed == cg2.max_failed,
                })
            elif cat_name in cats1:
                differences["category_diff"]["only_in_policy1"].append(cat_name)
            else:
                differences["category_diff"]["only_in_policy2"].append(cat_name)

        return differences

    @staticmethod
    def export_policy_yaml(name: str, project_root: Optional[str] = None) -> Optional[str]:
        """Export a policy to YAML format (Exp 57)

        Args:
            name: Policy name
            project_root: Project root for custom policies

        Returns:
            YAML string or None if not found
        """
        policy = GatePolicyManager.get_policy(name, project_root)
        if not policy:
            return None

        try:
            import yaml
        except ImportError:
            return "# PyYAML not installed. Install with: pip install pyyaml"

        policy_dict = GatePolicyManager.to_dict(policy)
        return yaml.dump({"gate_policies": [policy_dict]}, default_flow_style=False)

    @staticmethod
    def validate_all_policies(project_root: Optional[str] = None) -> List[Dict[str, Any]]:
        """Validate all policies and return results (Exp 57)

        Args:
            project_root: Project root for custom policies

        Returns:
            List of validation results
        """
        results = []

        # Validate presets
        for name in GatePolicyManager.list_presets():
            policy = GatePolicyManager.get_preset(name)
            is_valid, issues = GatePolicyManager.validate_policy(policy)
            results.append({
                "name": name,
                "is_preset": True,
                "is_valid": is_valid,
                "issue_count": len(issues),
                "issues": [issue.to_dict() for issue in issues],
            })

        # Validate custom policies
        custom_policies = GatePolicyManager.load_from_project(project_root)
        for name, policy in custom_policies.items():
            is_valid, issues = GatePolicyManager.validate_policy(policy)
            results.append({
                "name": name,
                "is_preset": False,
                "is_valid": is_valid,
                "issue_count": len(issues),
                "issues": [issue.to_dict() for issue in issues],
            })

        return results

    @staticmethod
    def cascade_policies(
        policy_names: List[str],
        strategy: str = "strict",
        cascade_name: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
        """Cascade multiple gate policies into a merged policy (Exp 59)

        This is a convenience wrapper around GatePolicyCascade that returns
        dict-compatible results for CLI integration.

        Args:
            policy_names: List of policy names to merge
            strategy: Merge strategy (strict, lenient, average, union, intersection)
            cascade_name: Optional name for the cascade
            project_root: Project root for custom policies

        Returns:
            Tuple of (cascade_dict, issues_list)
        """
        # GatePolicyCascade and CascadeStrategy are defined below in this file

        # Validate strategy
        valid_strategies = ["strict", "lenient", "average", "union", "intersection"]
        if strategy not in valid_strategies:
            return None, [{
                "error_type": "invalid_strategy",
                "message": f"Invalid strategy '{strategy}'. Valid options: {', '.join(valid_strategies)}",
            }]

        try:
            strategy_enum = CascadeStrategy(strategy)
        except ValueError:
            return None, [{
                "error_type": "invalid_strategy",
                "message": f"Invalid strategy '{strategy}'",
            }]

        # Perform cascade
        cascade, issues = cascade_gate_policies(policy_names, strategy, cascade_name, project_root)

        # Convert issues to dict format
        issues_list = [issue.to_dict() for issue in issues]

        if cascade is None:
            return None, issues_list

        # Return cascade as dict
        return cascade.to_dict(), issues_list

    @staticmethod
    def list_cascade_presets() -> List[Dict[str, Any]]:
        """List available cascade presets (Exp 59)

        Returns:
            List of preset dicts with name, description, policies, strategy
        """
        # GatePolicyCascade defined below in this file

        presets = []
        for name, preset in GatePolicyCascade.CASCADE_PRESETS.items():
            presets.append({
                "name": name,
                "description": preset["description"],
                "policies": preset["policies"],
                "strategy": preset["strategy"],
            })
        return presets

    @staticmethod
    def get_cascade_preset(name: str, project_root: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a cascade preset by name (Exp 59)

        Args:
            name: Preset name
            project_root: Project root for custom policies

        Returns:
            Cascade dict or None if not found
        """
        # GatePolicyCascade defined below in this file

        preset = GatePolicyCascade.get_cascade_preset(name)
        if preset is None:
            return None

        # Execute the cascade
        result, issues = GatePolicyManager.cascade_policies(
            policy_names=preset["policies"],
            strategy=preset["strategy"],
            cascade_name=name,
            project_root=project_root,
        )

        return result


def evaluate_quality_gate(
    evaluation_result: Dict[str, Any],
    gate_policy: Optional[GatePolicy] = None,
    gate_preset: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Evaluate quality gate against evaluation result

    Args:
        evaluation_result: Evaluation result dict from quality loop
        gate_policy: Optional custom gate policy
        gate_preset: Optional preset name (production, staging, development, ci)
        project_root: Optional project root for custom policies (Exp 56)

    Returns:
        Dict with gate result, messages, and details
    """
    # Determine which policy to use
    policy = gate_policy
    if gate_preset:
        policy = GatePolicyManager.get_policy(gate_preset, project_root)

    if policy is None:
        # Default to ci preset if none specified
        policy = GatePolicyManager.get_preset("ci")

    # Extract data from evaluation result
    overall_score = evaluation_result.get("score", 0.0)
    state = evaluation_result.get("state", {})
    evaluation = state.get("evaluation", {})

    # Get category scores and failed counts
    category_scores = {}
    category_failed = {}

    # Try to get from category_breakdown
    category_breakdown = evaluation.get("category_breakdown", {})
    if category_breakdown:
        for cat in category_breakdown.get("categories", []):
            cat_name = cat.get("name", "")
            # Calculate score: (total - failed) / total
            total = cat.get("total", 0)
            failed = cat.get("failed", 0)
            if total > 0:
                cat_score = (total - failed) / total
            else:
                cat_score = 1.0

            category_scores[cat_name] = cat_score
            category_failed[cat_name] = failed

    # Get severity counts
    severity_counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }

    # Count from failed_rules
    failed_rules = evaluation.get("failed_rules", [])
    for rule in failed_rules:
        # Try to get severity from rule
        severity = rule.get("severity", "medium").lower()
        if severity not in severity_counts:
            severity = "medium"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    # Run gate check
    result, messages = policy.check(
        overall_score=overall_score,
        category_scores=category_scores,
        category_failed=category_failed,
        severity_counts=severity_counts,
    )

    return {
        "gate_result": result.value,
        "passed": result == GateResult.PASSED,
        "blocked": result == GateResult.FAILED and policy.block_on_failure,
        "policy_name": policy.name,
        "policy_description": policy.description,
        "overall_threshold": policy.overall_threshold,
        "overall_score": overall_score,
        "messages": messages,
        "category_scores": category_scores,
        "category_failed": category_failed,
        "severity_counts": severity_counts,
        "block_on_failure": policy.block_on_failure,
    }


# ============================================================
# Gate Policy Cascade (formerly gate_cascade.py)
# ============================================================

class CascadeStrategy(Enum):
    """Cascade merge strategy for gate policies"""
    STRICT = "strict"
    LENIENT = "lenient"
    AVERAGE = "average"
    UNION = "union"
    INTERSECTION = "intersection"


class CascadeValidationError(Enum):
    """Cascade merge validation error types"""
    POLICY_NOT_FOUND = "policy_not_found"
    EMPTY_POLICY_LIST = "empty_policy_list"
    INVALID_STRATEGY = "invalid_strategy"
    INCOMPATIBLE_POLICIES = "incompatible_policies"


@dataclass
class CascadeGatePolicy:
    """Merged gate policy from multiple source policies"""
    name: str
    description: str
    source_policies: List[str]
    strategy: CascadeStrategy
    merged_policy: GatePolicy

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "source_policies": self.source_policies,
            "strategy": self.strategy.value,
            "merged_policy": GatePolicyManager.to_dict(self.merged_policy),
        }


@dataclass
class CascadeValidationIssue:
    """Validation issue for cascade merge"""
    error_type: CascadeValidationError
    message: str
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "details": self.details or {},
        }


class GatePolicyCascade:
    """Manager for cascading gate policies"""

    CASCADE_PRESETS: Dict[str, Dict[str, Any]] = {
        "prod-security": {
            "description": "Production policy with enhanced security",
            "policies": ["production", "strict"],
            "strategy": "strict",
        },
        "staging-plus": {
            "description": "Staging policy with extra safety margin",
            "policies": ["staging", "ci"],
            "strategy": "strict",
        },
        "dev-flexible": {
            "description": "Development policy with CI integration",
            "policies": ["development", "ci"],
            "strategy": "lenient",
        },
        "balanced": {
            "description": "Balanced policy averaging production and development",
            "policies": ["production", "development"],
            "strategy": "average",
        },
        "full-coverage": {
            "description": "Union of production and staging for comprehensive coverage",
            "policies": ["production", "staging"],
            "strategy": "union",
        },
        "common-only": {
            "description": "Intersection of all policies for consensus checks",
            "policies": ["production", "ci", "staging"],
            "strategy": "intersection",
        },
    }

    @staticmethod
    def list_cascade_presets() -> List[str]:
        return list(GatePolicyCascade.CASCADE_PRESETS.keys())

    @staticmethod
    def get_cascade_preset(name: str) -> Optional[Dict[str, Any]]:
        return GatePolicyCascade.CASCADE_PRESETS.get(name)

    @staticmethod
    def _validate_policy_list(
        policy_names: List[str], project_root: Optional[str] = None
    ) -> Tuple[bool, List[CascadeValidationIssue]]:
        issues = []
        if not policy_names:
            issues.append(CascadeValidationIssue(
                error_type=CascadeValidationError.EMPTY_POLICY_LIST,
                message="Policy list cannot be empty",
            ))
            return False, issues

        for name in policy_names:
            policy = GatePolicyManager.get_policy(name, project_root)
            if policy is None:
                issues.append(CascadeValidationIssue(
                    error_type=CascadeValidationError.POLICY_NOT_FOUND,
                    message=f"Policy '{name}' not found",
                    details={"policy_name": name},
                ))

        return len(issues) == 0, issues

    @staticmethod
    def _merge_severity_strict(severity_gates: List[SeverityGate]) -> SeverityGate:
        return SeverityGate(
            critical_max=min(sg.critical_max for sg in severity_gates),
            high_max=min(sg.high_max for sg in severity_gates),
            medium_max=min(sg.medium_max for sg in severity_gates),
            low_max=min(sg.low_max for sg in severity_gates),
            info_max=min(sg.info_max for sg in severity_gates),
        )

    @staticmethod
    def _merge_severity_lenient(severity_gates: List[SeverityGate]) -> SeverityGate:
        return SeverityGate(
            critical_max=max(sg.critical_max for sg in severity_gates),
            high_max=max(sg.high_max for sg in severity_gates),
            medium_max=max(sg.medium_max for sg in severity_gates),
            low_max=max(sg.low_max for sg in severity_gates),
            info_max=max(sg.info_max for sg in severity_gates),
        )

    @staticmethod
    def _merge_severity_average(severity_gates: List[SeverityGate]) -> SeverityGate:
        count = len(severity_gates)
        return SeverityGate(
            critical_max=round(sum(sg.critical_max for sg in severity_gates) / count),
            high_max=round(sum(sg.high_max for sg in severity_gates) / count),
            medium_max=round(sum(sg.medium_max for sg in severity_gates) / count),
            low_max=round(sum(sg.low_max for sg in severity_gates) / count),
            info_max=round(sum(sg.info_max for sg in severity_gates) / count),
        )

    @staticmethod
    def _merge_threshold_strict(policies: List[GatePolicy]) -> float:
        return max(p.overall_threshold for p in policies)

    @staticmethod
    def _merge_threshold_lenient(policies: List[GatePolicy]) -> float:
        return min(p.overall_threshold for p in policies)

    @staticmethod
    def _merge_threshold_average(policies: List[GatePolicy]) -> float:
        return round(sum(p.overall_threshold for p in policies) / len(policies), 2)

    @staticmethod
    def _merge_category_gates_strict(all_category_gates: List[List[CategoryGate]]) -> List[CategoryGate]:
        category_map: Dict[str, List[CategoryGate]] = {}
        for gates_list in all_category_gates:
            for gate in gates_list:
                if gate.category not in category_map:
                    category_map[gate.category] = []
                category_map[gate.category].append(gate)

        merged_gates = []
        for category, gates in category_map.items():
            merged_gates.append(CategoryGate(
                category=category,
                min_score=max(g.min_score for g in gates),
                max_failed=min(g.max_failed for g in gates),
            ))
        return merged_gates

    @staticmethod
    def _merge_category_gates_lenient(all_category_gates: List[List[CategoryGate]]) -> List[CategoryGate]:
        category_map: Dict[str, List[CategoryGate]] = {}
        for gates_list in all_category_gates:
            for gate in gates_list:
                if gate.category not in category_map:
                    category_map[gate.category] = []
                category_map[gate.category].append(gate)

        merged_gates = []
        for category, gates in category_map.items():
            merged_gates.append(CategoryGate(
                category=category,
                min_score=min(g.min_score for g in gates),
                max_failed=max(g.max_failed for g in gates),
            ))
        return merged_gates

    @staticmethod
    def _merge_category_gates_average(all_category_gates: List[List[CategoryGate]]) -> List[CategoryGate]:
        category_map: Dict[str, List[CategoryGate]] = {}
        for gates_list in all_category_gates:
            for gate in gates_list:
                if gate.category not in category_map:
                    category_map[gate.category] = []
                category_map[gate.category].append(gate)

        merged_gates = []
        for category, gates in category_map.items():
            count = len(gates)
            merged_gates.append(CategoryGate(
                category=category,
                min_score=round(sum(g.min_score for g in gates) / count, 2),
                max_failed=round(sum(g.max_failed for g in gates) / count),
            ))
        return merged_gates

    @staticmethod
    def _merge_category_gates_union(all_category_gates: List[List[CategoryGate]]) -> List[CategoryGate]:
        seen_categories: Dict[str, CategoryGate] = {}
        for gates_list in all_category_gates:
            for gate in gates_list:
                if gate.category not in seen_categories:
                    seen_categories[gate.category] = gate
        return list(seen_categories.values())

    @staticmethod
    def _merge_category_gates_intersection(all_category_gates: List[List[CategoryGate]]) -> List[CategoryGate]:
        if not all_category_gates:
            return []

        all_categories = [{gate.category for gate in gates} for gates in all_category_gates]
        common_categories = set.intersection(*all_categories) if all_categories else set()

        category_map: Dict[str, List[CategoryGate]] = {}
        for gates_list in all_category_gates:
            for gate in gates_list:
                if gate.category in common_categories:
                    if gate.category not in category_map:
                        category_map[gate.category] = []
                    category_map[gate.category].append(gate)

        merged_gates = []
        for category, gates in category_map.items():
            count = len(gates)
            merged_gates.append(CategoryGate(
                category=category,
                min_score=round(sum(g.min_score for g in gates) / count, 2),
                max_failed=round(sum(g.max_failed for g in gates) / count),
            ))
        return merged_gates

    @staticmethod
    def cascade(
        policy_names: List[str],
        strategy: CascadeStrategy = CascadeStrategy.STRICT,
        cascade_name: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> Tuple[Optional[CascadeGatePolicy], List[CascadeValidationIssue]]:
        """Cascade multiple gate policies into a single merged policy"""
        issues = []

        is_valid, validation_issues = GatePolicyCascade._validate_policy_list(policy_names, project_root)
        if not is_valid:
            return None, validation_issues

        policies = []
        for name in policy_names:
            policy = GatePolicyManager.get_policy(name, project_root)
            if policy:
                policies.append(policy)

        if not policies:
            issues.append(CascadeValidationIssue(
                error_type=CascadeValidationError.EMPTY_POLICY_LIST,
                message="No valid policies found to cascade",
            ))
            return None, issues

        if cascade_name is None:
            cascade_name = "+".join(policy_names)

        try:
            strategy_methods = {
                CascadeStrategy.STRICT: GatePolicyCascade._cascade_strict,
                CascadeStrategy.LENIENT: GatePolicyCascade._cascade_lenient,
                CascadeStrategy.AVERAGE: GatePolicyCascade._cascade_average,
                CascadeStrategy.UNION: GatePolicyCascade._cascade_union,
                CascadeStrategy.INTERSECTION: GatePolicyCascade._cascade_intersection,
            }

            merge_fn = strategy_methods.get(strategy)
            if merge_fn is None:
                issues.append(CascadeValidationIssue(
                    error_type=CascadeValidationError.INVALID_STRATEGY,
                    message=f"Unknown cascade strategy: {strategy}",
                ))
                return None, issues

            merged = merge_fn(policies, cascade_name)

            cascade_policy = CascadeGatePolicy(
                name=cascade_name,
                description=f"Cascade of {', '.join(policy_names)} using {strategy.value} strategy",
                source_policies=policy_names,
                strategy=strategy,
                merged_policy=merged,
            )

            return cascade_policy, []

        except Exception as e:
            issues.append(CascadeValidationIssue(
                error_type=CascadeValidationError.INCOMPATIBLE_POLICIES,
                message=f"Failed to cascade policies: {str(e)}",
            ))
            return None, issues

    @staticmethod
    def _cascade_strict(policies: List[GatePolicy], name: str) -> GatePolicy:
        severity_gates = [p.severity_gate for p in policies if p.severity_gate]
        merged_severity = GatePolicyCascade._merge_severity_strict(severity_gates) if severity_gates else SeverityGate()
        return GatePolicy(
            name=name,
            description=f"Strict cascade of {len(policies)} policies",
            overall_threshold=GatePolicyCascade._merge_threshold_strict(policies),
            severity_gate=merged_severity,
            category_gates=GatePolicyCascade._merge_category_gates_strict([p.category_gates for p in policies]),
            block_on_failure=any(p.block_on_failure for p in policies),
        )

    @staticmethod
    def _cascade_lenient(policies: List[GatePolicy], name: str) -> GatePolicy:
        severity_gates = [p.severity_gate for p in policies if p.severity_gate]
        merged_severity = GatePolicyCascade._merge_severity_lenient(severity_gates) if severity_gates else SeverityGate()
        return GatePolicy(
            name=name,
            description=f"Lenient cascade of {len(policies)} policies",
            overall_threshold=GatePolicyCascade._merge_threshold_lenient(policies),
            severity_gate=merged_severity,
            category_gates=GatePolicyCascade._merge_category_gates_lenient([p.category_gates for p in policies]),
            block_on_failure=all(p.block_on_failure for p in policies),
        )

    @staticmethod
    def _cascade_average(policies: List[GatePolicy], name: str) -> GatePolicy:
        severity_gates = [p.severity_gate for p in policies if p.severity_gate]
        merged_severity = GatePolicyCascade._merge_severity_average(severity_gates) if severity_gates else SeverityGate()
        block_count = sum(1 for p in policies if p.block_on_failure)
        return GatePolicy(
            name=name,
            description=f"Average cascade of {len(policies)} policies",
            overall_threshold=GatePolicyCascade._merge_threshold_average(policies),
            severity_gate=merged_severity,
            category_gates=GatePolicyCascade._merge_category_gates_average([p.category_gates for p in policies]),
            block_on_failure=block_count > len(policies) / 2,
        )

    @staticmethod
    def _cascade_union(policies: List[GatePolicy], name: str) -> GatePolicy:
        severity_gates = [p.severity_gate for p in policies if p.severity_gate]
        merged_severity = GatePolicyCascade._merge_severity_strict(severity_gates) if severity_gates else SeverityGate()
        return GatePolicy(
            name=name,
            description=f"Union cascade of {len(policies)} policies",
            overall_threshold=GatePolicyCascade._merge_threshold_strict(policies),
            severity_gate=merged_severity,
            category_gates=GatePolicyCascade._merge_category_gates_union([p.category_gates for p in policies]),
            block_on_failure=any(p.block_on_failure for p in policies),
        )

    @staticmethod
    def _cascade_intersection(policies: List[GatePolicy], name: str) -> GatePolicy:
        severity_gates = [p.severity_gate for p in policies if p.severity_gate]
        merged_severity = GatePolicyCascade._merge_severity_lenient(severity_gates) if severity_gates else SeverityGate()
        return GatePolicy(
            name=name,
            description=f"Intersection cascade of {len(policies)} policies",
            overall_threshold=GatePolicyCascade._merge_threshold_lenient(policies),
            severity_gate=merged_severity,
            category_gates=GatePolicyCascade._merge_category_gates_intersection([p.category_gates for p in policies]),
            block_on_failure=all(p.block_on_failure for p in policies),
        )


def cascade_gate_policies(
    policy_names: List[str],
    strategy: str = "strict",
    cascade_name: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Tuple[Optional[CascadeGatePolicy], List[CascadeValidationIssue]]:
    """Convenience function to cascade gate policies"""
    try:
        strategy_enum = CascadeStrategy(strategy)
    except ValueError:
        return None, [CascadeValidationIssue(
            error_type=CascadeValidationError.INVALID_STRATEGY,
            message=f"Invalid strategy '{strategy}'. Valid options: strict, lenient, average, union, intersection",
        )]
    return GatePolicyCascade.cascade(policy_names, strategy_enum, cascade_name, project_root)


def format_cascade_policy(cascade: CascadeGatePolicy) -> str:
    """Format cascade policy for display"""
    lines = [
        f"=== Cascade Gate Policy: {cascade.name} ===",
        "",
        f"Description: {cascade.description}",
        f"Strategy: {cascade.strategy.value}",
        f"Source Policies: {', '.join(cascade.source_policies)}",
        "",
        "--- Merged Policy ---",
        f"Overall Threshold: {cascade.merged_policy.overall_threshold:.2f}",
        f"Block on Failure: {cascade.merged_policy.block_on_failure}",
        "",
        "Severity Limits:",
    ]

    if cascade.merged_policy.severity_gate:
        sg = cascade.merged_policy.severity_gate
        lines.extend([
            f"  Critical: {sg.critical_max} max",
            f"  High:     {sg.high_max} max",
            f"  Medium:   {sg.medium_max} max",
            f"  Low:      {sg.low_max} max",
            f"  Info:     {sg.info_max} max",
        ])

    if cascade.merged_policy.category_gates:
        lines.append("")
        lines.append("Category Gates:")
        for cg in cascade.merged_policy.category_gates:
            lines.append(f"  {cg.category:15} min_score: {cg.min_score:.2f}  max_failed: {cg.max_failed}")

    return "\n".join(lines)


def format_cascade_policy_json(cascade: CascadeGatePolicy, indent: int = 2) -> str:
    """Format cascade policy as JSON"""
    import json
    return json.dumps(cascade.to_dict(), indent=indent)


# ============================================================
# Gate Policy Recommender (formerly gate_policy_recommender.py)
# ============================================================

import os
import re


class RecommendationReason(Enum):
    """Reason for policy recommendation"""
    CI_ENVIRONMENT = "ci_environment"
    PRODUCTION_BRANCH = "production_branch"
    PROJECT_TYPE = "project_type"
    QUALITY_SCORE = "quality_score"
    USER_PREFERENCE = "user_preference"
    SECURITY_SENSITIVE = "security_sensitive"
    CRITICAL_SYSTEM = "critical_system"
    EXPERIMENTAL = "experimental"


@dataclass
class PolicyRecommendation:
    """Gate policy recommendation with details"""
    policy_name: str
    confidence: float
    reasons: List[str]
    alternative_policies: List[Tuple[str, str]]
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "policy_name": self.policy_name,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "alternative_policies": [
                {"name": name, "reason": reason}
                for name, reason in self.alternative_policies
            ],
            "context": self.context,
        }


class GatePolicyRecommender:
    """Recommends appropriate gate policies based on context"""

    POLICY_CHARACTERISTICS = {
        "production": {
            "threshold": 0.95, "strictness": "very_high",
            "use_cases": ["production", "main", "release", "deploy"],
            "project_types": ["web-app", "graphql-api", "microservice"],
            "security_sensitive": True, "is_cascade": False,
        },
        "staging": {
            "threshold": 0.85, "strictness": "high",
            "use_cases": ["staging", "pre-production", "qa", "test"],
            "project_types": ["web-app", "graphql-api", "microservice"],
            "security_sensitive": True, "is_cascade": False,
        },
        "development": {
            "threshold": 0.70, "strictness": "medium",
            "use_cases": ["production", "dev", "feature", "wip"],
            "project_types": None, "security_sensitive": False, "is_cascade": False,
        },
        "ci": {
            "threshold": 0.80, "strictness": "high",
            "use_cases": ["ci", "pull-request", "merge-request", "integration"],
            "project_types": None, "security_sensitive": True,
            "blocking": True, "is_cascade": False,
        },
        "strict": {
            "threshold": 0.98, "strictness": "ultra",
            "use_cases": ["critical", "security", "compliance", "finance", "healthcare"],
            "project_types": ["graphql-api", "microservice"],
            "security_sensitive": True, "is_cascade": False,
        },
        "lenient": {
            "threshold": 0.60, "strictness": "low",
            "use_cases": ["prototype", "experimental", "spike", "poc", "demo"],
            "project_types": None, "security_sensitive": False, "is_cascade": False,
        },
        "prod-security": {
            "threshold": 0.98, "strictness": "ultra",
            "use_cases": ["production", "security", "critical", "compliance"],
            "project_types": ["graphql-api", "microservice", "web-app"],
            "security_sensitive": True, "is_cascade": True,
            "source_policies": ["production", "strict"], "strategy": "strict",
            "description": "Production policy with enhanced security",
        },
        "staging-plus": {
            "threshold": 0.88, "strictness": "high",
            "use_cases": ["staging", "ci", "pre-production", "qa", "integration"],
            "project_types": ["web-app", "graphql-api", "microservice"],
            "security_sensitive": True, "is_cascade": True,
            "source_policies": ["staging", "ci"], "strategy": "strict",
            "description": "Staging policy with extra safety margin",
        },
        "dev-flexible": {
            "threshold": 0.72, "strictness": "medium-low",
            "use_cases": ["development", "ci", "feature", "integration"],
            "project_types": None, "security_sensitive": False, "is_cascade": True,
            "source_policies": ["development", "ci"], "strategy": "lenient",
            "description": "Development policy with CI integration",
        },
        "balanced": {
            "threshold": 0.83, "strictness": "balanced",
            "use_cases": ["production", "development", "hybrid"],
            "project_types": ["web-app", "graphql-api", "microservice"],
            "security_sensitive": True, "is_cascade": True,
            "source_policies": ["production", "development"], "strategy": "average",
            "description": "Balanced policy averaging production and development",
        },
        "full-coverage": {
            "threshold": 0.95, "strictness": "very_high",
            "use_cases": ["production", "staging", "comprehensive"],
            "project_types": ["web-app", "graphql-api", "microservice"],
            "security_sensitive": True, "is_cascade": True,
            "source_policies": ["production", "staging"], "strategy": "union",
            "description": "Union of production and staging for comprehensive coverage",
        },
        "common-only": {
            "threshold": 0.75, "strictness": "medium",
            "use_cases": ["consensus", "team", "standardized"],
            "project_types": None, "security_sensitive": True, "is_cascade": True,
            "source_policies": ["production", "ci", "staging"], "strategy": "intersection",
            "description": "Intersection of all policies for consensus checks",
        },
    }

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self._context: Dict[str, Any] = {}
        self._scores: Dict[str, float] = {}

    def recommend(
        self,
        current_score: Optional[float] = None,
        failed_categories: Optional[List[str]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> PolicyRecommendation:
        """Generate gate policy recommendation"""
        self._context = {}
        self._scores = {}

        self._detect_ci_environment()
        self._detect_branch()
        self._detect_project_type()
        self._detect_security_sensitivity()

        self._calculate_ci_scores()
        self._calculate_branch_scores()
        self._calculate_project_type_scores()
        self._calculate_security_scores()
        self._calculate_cascade_scores()

        if current_score is not None:
            self._adjust_for_quality(current_score, failed_categories)

        if user_preferences:
            self._apply_user_preferences(user_preferences)

        if not self._scores:
            best_policy = "ci"
            confidence = 0.5
        else:
            best_policy = max(self._scores.items(), key=lambda x: x[1])
            confidence = min(0.95, best_policy[1] / max(self._scores.values()))

        reasons = self._generate_reasons(best_policy[0] if isinstance(best_policy, tuple) else best_policy)
        alternatives = self._generate_alternatives(best_policy[0] if isinstance(best_policy, tuple) else best_policy)

        return PolicyRecommendation(
            policy_name=best_policy[0] if isinstance(best_policy, tuple) else best_policy,
            confidence=confidence,
            reasons=reasons,
            alternative_policies=alternatives,
            context=self._context,
        )

    def _detect_ci_environment(self) -> None:
        ci_indicators = {
            "CI": ["true", "1", "yes"], "CONTINUOUS_INTEGRATION": ["true", "1", "yes"],
            "GITHUB_ACTIONS": ["true"], "GITLAB_CI": ["true"], "TRAVIS": ["true"],
            "JENKINS_URL": [None], "BUILD_NUMBER": [None],
            "GO_PIPELINE_NAME": [None], "TEAMCITY_VERSION": [None],
        }
        is_ci = False
        ci_provider = None
        for env_var, valid_values in ci_indicators.items():
            value = os.environ.get(env_var, "")
            if value:
                is_ci = True
                providers = {
                    "GITHUB_ACTIONS": "GitHub Actions", "GITLAB_CI": "GitLab CI",
                    "TRAVIS": "Travis CI", "JENKINS_URL": "Jenkins",
                    "GO_PIPELINE_NAME": "GoCD", "TEAMCITY_VERSION": "TeamCity",
                }
                ci_provider = providers.get(env_var)
                break
        self._context["is_ci"] = is_ci
        self._context["ci_provider"] = ci_provider

    def _detect_branch(self) -> None:
        branch = os.environ.get("GITHUB_REF_NAME") or os.environ.get("GITLAB_REF_NAME") or os.environ.get("BRANCH_NAME")
        if not branch:
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=self.project_root, capture_output=True, text=True, timeout=5,
                )
                if result.returncode == 0:
                    branch = result.stdout.strip()
            except (OSError, subprocess.TimeoutExpired, FileNotFoundError):
                pass
        self._context["branch"] = branch or "unknown"
        self._context["branch_type"] = self._classify_branch((branch or "").lower())

    def _classify_branch(self, branch: str) -> str:
        for pattern in ["main", "master", "production", "prod", "release", "live", "deploy", "publish"]:
            if pattern in branch:
                return "production"
        for pattern in ["staging", "stage", "preprod", "pre-production", "qa", "test", "testing", "integration"]:
            if pattern in branch:
                return "staging"
        for pattern in ["dev", "develop", "development", "wip"]:
            if pattern in branch:
                return "development"
        for pattern in ["feature", "feat", "branch", "enhancement", "bug", "fix", "hotfix", "experiment"]:
            if pattern in branch:
                return "feature"
        return "unknown"

    def _detect_project_type(self) -> None:
        try:
            from .autodetect import ProfileDetector
            detector = ProfileDetector(self.project_root)
            self._context["project_type"] = detector.detect()
        except Exception:
            self._context["project_type"] = "unknown"

    def _detect_security_sensitivity(self) -> None:
        has_security_dirs = any(
            (self.project_root / d).is_dir() for d in ["auth", "security", "crypto", "payments"]
        )
        security_files = 0
        for pattern in ["auth", "security", "crypto", "password", "token"]:
            try:
                security_files += sum(1 for _ in self.project_root.rglob(f"*{pattern}*") if _.is_file())
            except OSError:
                pass
        self._context["security_sensitive"] = has_security_dirs or security_files > 2

    def _calculate_ci_scores(self) -> None:
        if self._context.get("is_ci"):
            self._scores["ci"] = self._scores.get("ci", 0) + 3.0
            self._scores["staging"] = self._scores.get("staging", 0) + 2.0
            if self._context.get("branch_type") == "production":
                self._scores["production"] = self._scores.get("production", 0) + 2.0

    def _calculate_branch_scores(self) -> None:
        branch_type = self._context.get("branch_type", "unknown")
        branch_scores = {
            "production": {"production": 4.0, "strict": 2.0},
            "staging": {"staging": 4.0, "ci": 2.0},
            "development": {"development": 3.0, "ci": 1.0},
            "feature": {"development": 2.0, "lenient": 1.0},
        }
        for policy, score in branch_scores.get(branch_type, {}).items():
            self._scores[policy] = self._scores.get(policy, 0) + score

    def _calculate_project_type_scores(self) -> None:
        project_type = self._context.get("project_type", "unknown")
        if project_type in ["graphql-api", "microservice"]:
            self._scores["production"] = self._scores.get("production", 0) + 1.0
            self._scores["ci"] = self._scores.get("ci", 0) + 1.0
        elif project_type == "ml-service":
            self._scores["development"] = self._scores.get("development", 0) + 0.5

    def _calculate_security_scores(self) -> None:
        if self._context.get("security_sensitive"):
            self._scores["production"] = self._scores.get("production", 0) + 1.5
            self._scores["strict"] = self._scores.get("strict", 0) + 1.0
            self._scores["ci"] = self._scores.get("ci", 0) + 0.5

    def _detect_hybrid_scenario(self) -> Dict[str, Any]:
        hybrid = {"is_hybrid": False, "reason": [], "recommended_cascades": []}
        is_prod = self._context.get("branch_type") == "production"
        is_security = self._context.get("security_sensitive", False)
        is_ci = self._context.get("is_ci", False)
        is_staging = self._context.get("branch_type") == "staging"
        is_dev = self._context.get("branch_type") == "development"

        if is_prod and is_security:
            hybrid["is_hybrid"] = True
            hybrid["reason"].append("Production branch with security requirements")
            hybrid["recommended_cascades"].append("prod-security")
        if (is_ci and is_staging) or (is_ci and self._context.get("branch_type") in ["development", "feature"]):
            hybrid["is_hybrid"] = True
            hybrid["reason"].append("CI environment with staging requirements")
            hybrid["recommended_cascades"].append("staging-plus")
        if is_ci and is_dev:
            hybrid["is_hybrid"] = True
            hybrid["reason"].append("CI environment during development")
            hybrid["recommended_cascades"].append("dev-flexible")
        project_type = self._context.get("project_type", "")
        if project_type in ["web-app", "graphql-api", "microservice"] and not is_prod and not is_staging:
            hybrid["is_hybrid"] = True
            hybrid["reason"].append("Mixed production/development environment")
            hybrid["recommended_cascades"].append("balanced")
        if not is_prod and not is_staging and self._context.get("branch_type") in ["development", "feature"]:
            hybrid["is_hybrid"] = True
            hybrid["reason"].append("Team standardization scenario")
            hybrid["recommended_cascades"].append("common-only")

        self._context["hybrid_scenario"] = hybrid
        return hybrid

    def _calculate_cascade_scores(self) -> None:
        hybrid = self._detect_hybrid_scenario()
        if not hybrid["is_hybrid"]:
            return
        for cascade_name in hybrid["recommended_cascades"]:
            if cascade_name in self.POLICY_CHARACTERISTICS:
                self._scores[cascade_name] = self._scores.get(cascade_name, 0) + 3.0

        branch_type = self._context.get("branch_type", "")
        is_ci = self._context.get("is_ci", False)
        is_security = self._context.get("security_sensitive", False)

        if branch_type == "production" and is_security:
            self._scores["prod-security"] = self._scores.get("prod-security", 0) + 2.0
        if branch_type == "staging" or is_ci:
            boost = 2.0 if is_security else 1.0
            self._scores["staging-plus"] = self._scores.get("staging-plus", 0) + boost
        if branch_type == "development" and is_ci:
            self._scores["dev-flexible"] = self._scores.get("dev-flexible", 0) + 2.0
        if branch_type in ["development", "feature", "unknown"]:
            self._scores["balanced"] = self._scores.get("balanced", 0) + 1.0
        if is_ci and is_security:
            self._scores["full-coverage"] = self._scores.get("full-coverage", 0) + 1.5
        if branch_type in ["feature", "development"]:
            self._scores["common-only"] = self._scores.get("common-only", 0) + 0.5

    def _adjust_for_quality(self, current_score: float, failed_categories: Optional[List[str]]) -> None:
        if current_score < 0.5:
            self._scores["lenient"] = self._scores.get("lenient", 0) + 1.0
            self._scores["development"] = self._scores.get("development", 0) + 0.5
        if failed_categories and "security" in failed_categories:
            self._scores["strict"] = self._scores.get("strict", 0) + 2.0
            self._scores["production"] = self._scores.get("production", 0) + 1.0
        self._context["current_score"] = current_score
        self._context["failed_categories"] = failed_categories or []

    def _apply_user_preferences(self, preferences: Dict[str, Any]) -> None:
        if "preferred_policy" in preferences:
            preferred = preferences["preferred_policy"]
            if preferred in self.POLICY_CHARACTERISTICS:
                self._scores[preferred] = self._scores.get(preferred, 0) + 10.0
        strictness = preferences.get("strictness_level")
        if strictness == "strict":
            self._scores["strict"] = self._scores.get("strict", 0) + 2.0
            self._scores["production"] = self._scores.get("production", 0) + 1.5
        elif strictness == "balanced":
            self._scores["ci"] = self._scores.get("ci", 0) + 1.0
            self._scores["staging"] = self._scores.get("staging", 0) + 1.0
        elif strictness == "lenient":
            self._scores["development"] = self._scores.get("development", 0) + 1.5
            self._scores["lenient"] = self._scores.get("lenient", 0) + 1.0
        if preferences.get("security_first"):
            self._scores["strict"] = self._scores.get("strict", 0) + 1.5
            self._scores["production"] = self._scores.get("production", 0) + 1.0

    def _generate_reasons(self, policy_name: str) -> List[str]:
        reasons = []
        policy_chars = self.POLICY_CHARACTERISTICS.get(policy_name, {})
        if policy_chars.get("is_cascade", False):
            source_policies = policy_chars.get("source_policies", [])
            strategy = policy_chars.get("strategy", "")
            description = policy_chars.get("description", "")
            reasons.append(f"Cascade policy combining: {', '.join(source_policies)}")
            reasons.append(f"Strategy: {strategy} - {description}")
            hybrid = self._context.get("hybrid_scenario", {})
            if hybrid.get("is_hybrid") and policy_name in hybrid.get("recommended_cascades", []):
                for hr in hybrid.get("reason", []):
                    if hr not in reasons:
                        reasons.append(hr)
        if self._context.get("is_ci"):
            reasons.append(f"Running in {self._context.get('ci_provider', 'CI')} environment")
        branch = self._context.get("branch", "")
        branch_type = self._context.get("branch_type", "")
        if branch_type in ("production", "staging", "feature"):
            reasons.append(f"On {branch_type} branch '{branch}'")
        project_type = self._context.get("project_type")
        if project_type and project_type != "unknown":
            reasons.append(f"Detected project type: {project_type}")
        if self._context.get("security_sensitive"):
            reasons.append("Project appears security-sensitive")
        current_score = self._context.get("current_score")
        if current_score is not None:
            reasons.append(f"Current quality score: {current_score:.2f}")
            if current_score < 0.7:
                reasons.append("Quality score below threshold - lenient policy recommended")
        failed = self._context.get("failed_categories", [])
        if failed:
            reasons.append(f"Failed categories: {', '.join(failed)}")
        return reasons

    def _generate_alternatives(self, recommended_policy: str) -> List[Tuple[str, str]]:
        alternatives = []
        sorted_scores = sorted(self._scores.items(), key=lambda x: -x[1])
        for policy, score in sorted_scores:
            if policy != recommended_policy and len(alternatives) < 3:
                alternatives.append((policy, self._get_alternative_reason(policy, score)))
        if not alternatives:
            if recommended_policy != "ci":
                alternatives.append(("ci", "Default for CI/CD pipelines"))
            if recommended_policy != "development":
                alternatives.append(("development", "For development workflows"))
        return alternatives

    def _get_alternative_reason(self, policy: str, score: float) -> str:
        cascade_reasons = {
            "prod-security": "Cascade: Production + Strict for critical deployments",
            "staging-plus": "Cascade: Staging + CI for enhanced safety",
            "dev-flexible": "Cascade: Development + CI for active development",
            "balanced": "Cascade: Average of Production + Development",
            "full-coverage": "Cascade: Union of Production + Staging for comprehensive checks",
            "common-only": "Cascade: Intersection for team consensus",
        }
        standard_reasons = {
            "production": "For production deployments (strict)",
            "staging": "For staging/pre-production",
            "development": "For development workflows",
            "ci": "For CI/CD pipelines",
            "strict": "For critical systems (ultra-strict)",
            "lenient": "For experimental features",
        }
        return cascade_reasons.get(policy) or standard_reasons.get(policy, f"Score: {score:.1f}")


def recommend_gate_policy(
    project_root: Optional[Path] = None,
    current_score: Optional[float] = None,
    failed_categories: Optional[List[str]] = None,
    user_preferences: Optional[Dict[str, Any]] = None,
) -> PolicyRecommendation:
    """Convenience function to get gate policy recommendation"""
    recommender = GatePolicyRecommender(project_root)
    return recommender.recommend(current_score, failed_categories, user_preferences)


def format_recommendation(recommendation: PolicyRecommendation) -> str:
    """Format recommendation for display"""
    lines = [
        "=== Gate Policy Recommendation ===", "",
        f"Recommended Policy: {recommendation.policy_name}",
        f"Confidence: {recommendation.confidence:.0%}", "", "Reasons:",
    ]
    for reason in recommendation.reasons:
        lines.append(f"  - {reason}")
    if recommendation.alternative_policies:
        lines.append("")
        lines.append("Alternative Policies:")
        for policy, reason in recommendation.alternative_policies:
            lines.append(f"  - {policy}: {reason}")
    return "\n".join(lines)


def format_recommendation_json(recommendation: PolicyRecommendation, indent: int = 2) -> str:
    """Format recommendation as JSON"""
    return json.dumps(recommendation.to_dict(), indent=indent)
