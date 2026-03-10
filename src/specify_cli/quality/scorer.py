"""
Scorer

Calculates quality scores from evaluation results.
"""

from typing import List
from specify_cli.quality.models import QualityRule, FailedRule


class Scorer:
    """Calculate quality scores"""

    def calculate_score(
        self,
        passed_rules: List[QualityRule],
        all_rules: List[QualityRule]
    ) -> float:
        """Calculate score: sum(passed_weights) / sum(all_weights)

        Args:
            passed_rules: Rules that passed
            all_rules: All rules that were evaluated

        Returns:
            Score from 0.0 to 1.0
        """
        passed_weight = sum(rule.weight for rule in passed_rules)
        all_weight = sum(rule.weight for rule in all_rules)

        if all_weight == 0:
            return 1.0  # No rules means perfect score

        return passed_weight / all_weight

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
