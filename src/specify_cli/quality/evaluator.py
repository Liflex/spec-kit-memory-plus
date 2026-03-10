"""
Evaluator

Evaluates artifacts against quality rules.
"""

import re
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional
from datetime import datetime

from specify_cli.quality.models import (
    CriteriaTemplate,
    EvaluationResult,
    FailedRule,
    QualityRule,
    Phase,
    RuleCheckType,
)
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.scorer import Scorer


class Evaluator:
    """Evaluate artifact against quality rules"""

    def __init__(self, rule_manager: RuleManager, scorer: Scorer):
        """Initialize evaluator

        Args:
            rule_manager: Rule manager instance
            scorer: Scorer instance
        """
        self.rule_manager = rule_manager
        self.scorer = scorer

    def evaluate(
        self,
        artifact: str,
        criteria: CriteriaTemplate,
        phase: str = "A"
    ) -> EvaluationResult:
        """Evaluate artifact against criteria

        Args:
            artifact: Artifact content (markdown with code blocks)
            criteria: Criteria template
            phase: Evaluation phase ("A" or "B")

        Returns:
            EvaluationResult with score, passed/failed rules
        """
        # Convert phase string to enum
        phase_enum = Phase(phase)

        # Get active rules for phase
        active_rules = self.rule_manager.get_rules_for_phase(criteria, phase_enum)

        # Check each rule
        passed_rules = []
        failed_rules = []
        warnings = []

        for rule in active_rules:
            passed, reason = self._check_rule(rule, artifact)

            if passed:
                passed_rules.append(rule.id)
            elif rule.severity.value == "fail":
                failed_rules.append(FailedRule(rule_id=rule.id, reason=reason))
            else:  # warn or info
                warnings.append(FailedRule(rule_id=rule.id, reason=reason))

        # Calculate score
        score = self.scorer.calculate_score(
            passed_rules=[r for r in active_rules if r.id in passed_rules],
            all_rules=active_rules
        )

        # Check if passed
        threshold = criteria.get_phase_config(phase_enum).threshold
        passed = self.scorer.check_passed(score, threshold, failed_rules)

        return EvaluationResult(
            score=score,
            passed=passed,
            threshold=threshold,
            phase=phase,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            evaluated_at=datetime.now().isoformat(),
        )

    def _check_rule(
        self,
        rule: QualityRule,
        artifact: str
    ) -> Tuple[bool, str]:
        """Check a single rule

        Args:
            rule: Rule to check
            artifact: Artifact content

        Returns:
            (passed, reason) tuple
        """
        if rule.check_type == RuleCheckType.executable:
            return self._check_executable(rule, artifact)
        elif rule.check_type == RuleCheckType.hybrid:
            # Check content first, then executable
            content_passed, content_reason = self._check_content(rule, artifact)
            if not content_passed:
                return False, content_reason
            return self._check_executable(rule, artifact)
        else:  # content
            return self._check_content(rule, artifact)

    def _check_content(
        self,
        rule: QualityRule,
        artifact: str
    ) -> Tuple[bool, str]:
        """Check rule using content analysis

        Args:
            rule: Rule to check
            artifact: Artifact content

        Returns:
            (passed, reason) tuple
        """
        artifact_lower = artifact.lower()

        # Rule-specific checks
        check_methods = {
            # API Spec rules
            "correctness.endpoints": self._check_crud_endpoints,
            "correctness.status_codes": self._check_status_codes,
            "correctness.content_types": self._check_content_types,
            "correctness.auth": self._check_auth_documentation,
            "quality.parameters": self._check_parameters,
            "quality.responses": self._check_responses,

            # Code Gen rules
            "correctness.tests": self._check_tests,
            "quality.error_handling": self._check_error_handling,
            "quality.readability": self._check_readability,
            "correctness.types": self._check_type_hints,
            "correctness.structure": self._check_structure,
            "security.input_validation": self._check_input_validation,
            "security.secrets": self._check_secrets,

            # Docs rules
            "correctness.title": self._check_title,
            "correctness.purpose": self._check_purpose,
            "quality.installation": self._check_installation,
            "quality.usage": self._check_usage,

            # Config rules
            "security.secrets": self._check_secrets,
        }

        method = check_methods.get(rule.id)
        if method:
            return method(artifact, artifact_lower)

        # Fallback: keyword matching
        keywords = rule.check.lower().split()
        found = sum(1 for kw in keywords if kw in artifact_lower)

        if found >= len(keywords) * 0.5:  # 50% of keywords
            return True, f"Found {found}/{len(keywords)} keywords"
        else:
            return False, f"Only found {found}/{len(keywords)} keywords"

    def _check_executable(
        self,
        rule: QualityRule,
        artifact: str
    ) -> Tuple[bool, str]:
        """Check rule using executable check

        Args:
            rule: Rule to check
            artifact: Artifact content

        Returns:
            (passed, reason) tuple
        """
        # For now, most executable checks are not implemented
        # In production, would run scripts, tests, etc.
        return True, "Executable check not implemented"

    # Rule-specific check methods

    def _check_crud_endpoints(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for all CRUD endpoints"""
        has_get = any(pattern in artifact_lower for pattern in ["get", "fetch", "list"])
        has_post = any(pattern in artifact_lower for pattern in ["post", "create", "add"])
        has_put = any(pattern in artifact_lower for pattern in ["put", "update", "patch"])
        has_delete = any(pattern in artifact_lower for pattern in ["delete", "remove", "destroy"])

        if all([has_get, has_post, has_put, has_delete]):
            return True, "All CRUD endpoints present"
        else:
            missing = []
            if not has_get: missing.append("GET")
            if not has_post: missing.append("POST")
            if not has_put: missing.append("PUT/PATCH")
            if not has_delete: missing.append("DELETE")
            return False, f"Missing endpoints: {', '.join(missing)}"

    def _check_status_codes(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for HTTP status codes"""
        codes = ["200", "201", "204", "400", "404", "500"]
        found = [code for code in codes if code in artifact]
        if len(found) >= 4:
            return True, f"Found {len(found)}/6 status codes"
        return False, f"Only found {len(found)}/6 status codes"

    def _check_content_types(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for Content-Type headers"""
        has_json = "application/json" in artifact_lower or "json" in artifact_lower
        has_html = "text/html" in artifact_lower or "html" in artifact_lower
        return has_json or has_html, f"Content-Type: {'JSON' if has_json else 'HTML' if has_html else 'None'}"

    def _check_auth_documentation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for authentication documentation"""
        auth_keywords = ["auth", "token", "bearer", "api key", "oauth", "jwt", "login"]
        found = [kw for kw in auth_keywords if kw in artifact_lower]
        return len(found) > 0, f"Found {len(found)} auth-related terms"

    def _check_parameters(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for parameter documentation"""
        param_keywords = ["param", "query", "body", "request", "argument", "field"]
        found = [kw for kw in param_keywords if kw in artifact_lower]
        return len(found) >= 2, f"Found {len(found)} parameter-related terms"

    def _check_responses(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for response schemas"""
        response_keywords = ["response", "schema", "return", "output", "result"]
        found = [kw for kw in response_keywords if kw in artifact_lower]
        return len(found) >= 2, f"Found {len(found)} response-related terms"

    def _check_tests(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for test presence"""
        test_keywords = ["test", "spec", "unittest", "pytest", "jest"]
        found = [kw for kw in test_keywords if kw in artifact_lower]
        return len(found) > 0, f"Found {len(found)} test-related terms"

    def _check_error_handling(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for error handling"""
        error_keywords = ["try", "except", "catch", "error", "throw", "raise", "exception"]
        found = [kw for kw in error_keywords if kw in artifact_lower]
        return len(found) >= 2, f"Found {len(found)} error-handling terms"

    def _check_readability(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for comments/docstrings"""
        has_hash_comment = "#" in artifact
        has_double_slash = "//" in artifact
        has_docstring = '"""' in artifact or "'''" in artifact
        return any([has_hash_comment, has_double_slip, has_docstring]), "Has comments or docstrings"

    def _check_type_hints(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for type hints"""
        type_patterns = [": int", ": str", ": bool", ": float", "-> ", "List[", "Dict["]
        found = [pattern for pattern in type_patterns if pattern in artifact]
        return len(found) >= 2, f"Found {len(found)} type hint patterns"

    def _check_structure(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper code structure"""
        structure_keywords = ["class ", "def ", "function ", "struct ", "interface "]
        found = [kw for kw in structure_keywords if kw in artifact_lower or kw in artifact]
        return len(found) > 0, f"Found {len(found)} structure definitions"

    def _check_input_validation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for input validation"""
        validation_keywords = ["validate", "sanitize", "check", "verify", "ensure"]
        found = [kw for kw in validation_keywords if kw in artifact_lower]
        return len(found) > 0, f"Found {len(found)} validation-related terms"

    def _check_secrets(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for no hardcoded secrets"""
        secret_patterns = [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][^'\"]+['\"]",
        ]
        for pattern in secret_patterns:
            if re.search(pattern, artifact, re.IGNORECASE):
                return False, "Potential hardcoded secret found"
        return True, "No hardcoded secrets detected"

    def _check_title(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for document title"""
        return bool(re.match(r"^#\s+\w+", artifact)), "Has title heading"

    def _check_purpose(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for purpose/overview section"""
        purpose_keywords = ["purpose", "overview", "introduction", "about", "what is"]
        found = [kw for kw in purpose_keywords if kw in artifact_lower]
        return len(found) > 0, "Has purpose/overview section"

    def _check_installation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for installation instructions"""
        install_keywords = ["install", "setup", "getting started", "quickstart", "npm install", "pip install"]
        found = [kw for kw in install_keywords if kw in artifact_lower]
        return len(found) > 0, "Has installation instructions"

    def _check_usage(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for usage examples"""
        usage_keywords = ["usage", "example", "how to", "use", "```"]
        found = [kw for kw in usage_keywords if kw in artifact_lower]
        return len(found) >= 2, "Has usage examples"
