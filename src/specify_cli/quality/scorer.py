"""
Scorer

Calculates quality scores from evaluation results.
Supports priority-aware scoring with domain multipliers.
Supports advanced quality gate policies (Exp 55).
"""

from typing import List, Optional, Dict, Any
from specify_cli.quality.models import QualityRule, FailedRule, CriteriaTemplate, PriorityProfile


class Scorer:
    """Calculate quality scores with priority-aware scoring"""

    def calculate_score(
        self,
        passed_rules: List[QualityRule],
        all_rules: List[QualityRule],
        priority_profile: Optional[PriorityProfile] = None,
    ) -> float:
        """Calculate score: sum(passed_weights) / sum(all_weights)

        Args:
            passed_rules: Rules that passed
            all_rules: All rules that were evaluated
            priority_profile: Optional priority profile for domain and category weighting (Exp 46)

        Returns:
            Score from 0.0 to 1.0
        """
        # Get multipliers from priority profile
        multipliers = {}
        category_multipliers = {}
        if priority_profile:
            multipliers = priority_profile.multipliers
            category_multipliers = priority_profile.category_multipliers

        # Calculate effective weights
        passed_weight = 0.0
        all_weight = 0.0

        for rule in all_rules:
            effective_weight = rule.get_effective_weight(multipliers, category_multipliers)
            all_weight += effective_weight

        for rule in passed_rules:
            effective_weight = rule.get_effective_weight(multipliers, category_multipliers)
            passed_weight += effective_weight

        if all_weight == 0:
            return 1.0  # No rules means perfect score

        return passed_weight / all_weight

    def calculate_score_simple(
        self,
        passed_rules: List[QualityRule],
        all_rules: List[QualityRule]
    ) -> float:
        """Calculate score without priority weighting (backward compatibility)

        Args:
            passed_rules: Rules that passed
            all_rules: All rules that were evaluated

        Returns:
            Score from 0.0 to 1.0
        """
        return self.calculate_score(passed_rules, all_rules, priority_profile=None)

    def check_passed(
        self,
        score: float,
        threshold: float,
        failed_rules: List[FailedRule]
    ) -> bool:
        """Check if evaluation passed

        Args:
            score: Calculated score
            threshold: Threshold to compare against
            failed_rules: Rules that failed

        Returns:
            True if passed (score >= threshold AND no fail-severity failures)
        """
        # Check if any fail-severity rules failed
        from specify_cli.quality.models import RuleSeverity

        has_fail_severity = any(
            rule_id.startswith("correctness.") or
            rule_id.startswith("security.")
            for rule_id in [r.rule_id for r in failed_rules]
        )

        # More precise check: look at actual rule severity
        # For now, use simple heuristic based on rule ID prefix
        # In production, would look up actual rule severity

        return score >= threshold and not has_fail_severity

    def calculate_distance_to_success(
        self,
        score: float,
        threshold: float
    ) -> float:
        """Calculate distance from score to threshold

        Args:
            score: Current score
            threshold: Target threshold

        Returns:
            Numeric gap (0.0 if already passed, otherwise threshold - score)
        """
        gap = threshold - score
        return max(0.0, gap)

    def get_rule_priority_score(
        self,
        rule: QualityRule,
        priority_profile: Optional[PriorityProfile] = None
    ) -> float:
        """Get the priority score (effective weight) for a single rule

        Args:
            rule: Rule to score
            priority_profile: Optional priority profile

        Returns:
            Effective weight with domain and category multipliers applied
        """
        multipliers = {}
        category_multipliers = {}
        if priority_profile:
            multipliers = priority_profile.multipliers
            category_multipliers = priority_profile.category_multipliers

        return rule.get_effective_weight(multipliers, category_multipliers)

    def list_priority_profiles(self, criteria: CriteriaTemplate) -> List[str]:
        """List available priority profiles from criteria

        Args:
            criteria: Criteria template

        Returns:
            List of priority profile names
        """
        return criteria.list_priority_profiles()

    def get_default_priority_profile(self, criteria: CriteriaTemplate) -> PriorityProfile:
        """Get or create default priority profile

        Args:
            criteria: Criteria template

        Returns:
            Default PriorityProfile
        """
        return criteria.get_default_profile()

    def validate_priority_profile(
        self,
        criteria: CriteriaTemplate,
        profile_name: str
    ) -> bool:
        """Check if a priority profile exists in criteria

        Args:
            criteria: Criteria template
            profile_name: Name of profile to validate

        Returns:
            True if profile exists
        """
        profile = criteria.get_priority_profile(profile_name)
        return profile is not None

    # Exp 55: Advanced quality gate evaluation support
    def get_severity_counts(
        self,
        failed_rules: List[FailedRule],
        warnings: List[FailedRule]
    ) -> Dict[str, int]:
        """Get severity counts from failed rules and warnings

        Args:
            failed_rules: List of failed rules
            warnings: List of warnings

        Returns:
            Dict with severity counts (critical, high, medium, low, info)
        """
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
        }

        # Count from failed rules
        for rule in failed_rules:
            severity = self._get_rule_severity(rule.rule_id)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        # Count from warnings
        for rule in warnings:
            severity = self._get_rule_severity(rule.rule_id)
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return severity_counts

    def _get_rule_severity(self, rule_id: str) -> str:
        """Get severity level for a rule ID

        Args:
            rule_id: Rule identifier

        Returns:
            Severity level (critical, high, medium, low, info)
        """
        # Map rule prefixes to severity levels
        severity_map = {
            "security.": "critical",
            "correctness.": "high",
            "performance.": "medium",
            "quality.": "low",
            "docs.": "info",
        }

        for prefix, severity in severity_map.items():
            if rule_id.startswith(prefix):
                return severity

        return "medium"  # Default severity

    def get_category_scores(
        self,
        passed_rules: List[QualityRule],
        failed_rules: List[FailedRule],
        all_rules: List[QualityRule],
    ) -> Dict[str, Dict[str, Any]]:
        """Get scores and failed counts per category

        Args:
            passed_rules: List of passed rules
            failed_rules: List of failed rules
            all_rules: List of all rules

        Returns:
            Dict mapping category name to {score, passed, failed, total}
        """
        category_stats = {}

        # Build category stats
        for rule in all_rules:
            cat = rule.category
            if cat not in category_stats:
                category_stats[cat] = {"total": 0, "passed": 0, "failed": 0}

            category_stats[cat]["total"] += 1

        for rule in passed_rules:
            cat = rule.category
            if cat in category_stats:
                category_stats[cat]["passed"] += 1

        for rule in failed_rules:
            cat = rule.category
            if cat in category_stats:
                category_stats[cat]["failed"] += 1

        # Calculate scores
        result = {}
        for cat, stats in category_stats.items():
            total = stats["total"]
            passed = stats["passed"]
            score = passed / total if total > 0 else 1.0

            result[cat] = {
                "score": round(score, 3),
                "passed": passed,
                "failed": stats["failed"],
                "total": total,
            }

        return result

    def check_gate_conditions(
        self,
        score: float,
        threshold: float,
        failed_rules: List[FailedRule],
        category_scores: Dict[str, Dict[str, Any]],
        severity_counts: Dict[str, int],
    ) -> Dict[str, Any]:
        """Check quality gate conditions with detailed results

        Args:
            score: Overall quality score
            threshold: Score threshold
            failed_rules: List of failed rules
            category_scores: Category scores dict
            severity_counts: Severity counts dict

        Returns:
            Dict with gate check results
        """
        passed = score >= threshold

        # Check for critical/high severity failures
        has_critical = severity_counts.get("critical", 0) > 0
        has_high = severity_counts.get("high", 0) > 0

        # Get failing categories
        failing_categories = []
        for cat, stats in category_scores.items():
            if stats["failed"] > 0:
                failing_categories.append(cat)

        return {
            "passed": passed and not has_critical,
            "score": score,
            "threshold": threshold,
            "has_critical_issues": has_critical,
            "has_high_issues": has_high,
            "failing_categories": failing_categories,
            "severity_counts": severity_counts,
            "category_scores": category_scores,
        }
