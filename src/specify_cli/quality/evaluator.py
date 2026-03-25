"""
Evaluator

Evaluates artifacts against quality rules.
Supports priority-aware scoring with domain multipliers.
Exp 55: Enhanced with category scores and severity counts for quality gates.
"""

import re
import subprocess
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
from datetime import datetime

from specify_cli.quality.models import (
    CriteriaTemplate,
    EvaluationResult,
    FailedRule,
    QualityRule,
    Phase,
    RuleCheckType,
    PriorityProfile,
)
from specify_cli.quality.rules import RuleManager
from specify_cli.quality.scorer import Scorer
from specify_cli.quality.priority_profiles import PriorityProfilesManager


class Evaluator:
    """Evaluate artifact against quality rules with priority-aware scoring"""

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
        phase: str = "A",
        priority_profile: Optional[str] = None,
        cascade_strategy: Optional[str] = None,
        project_root: Optional[str] = None,
    ) -> EvaluationResult:
        """Evaluate artifact against criteria

        Args:
            artifact: Artifact content (markdown with code blocks)
            criteria: Criteria template
            phase: Evaluation phase ("A" or "B")
            priority_profile: Optional priority profile name for domain-based weighting
            cascade_strategy: Optional cascade merge strategy (avg/max/min/wgt/weighted)
            project_root: Optional project root for loading custom profiles

        Returns:
            EvaluationResult with score, passed/failed rules
        """
        # Convert phase string to enum
        phase_enum = Phase(phase)

        # Get priority profile if specified (supports cascade profiles with "+" syntax)
        profile = None
        if priority_profile:
            # Check for cascade profile syntax (e.g., "web-app+mobile-app")
            is_cascade, profile_names, cascade_error = PriorityProfilesManager.parse_cascade_profile(priority_profile)

            if cascade_error:
                # Invalid cascade syntax - fall back to default
                profile = criteria.get_default_profile()
            elif is_cascade:
                # Resolve cascade profile with specified strategy
                # Normalize strategy alias (e.g., "avg" -> "average", "wgt" -> "weighted")
                strategy = PriorityProfilesManager.normalize_strategy_alias(cascade_strategy) if cascade_strategy else "average"

                profile = PriorityProfilesManager.resolve_cascade_profile(
                    priority_profile,
                    Path(project_root) if project_root else None,
                    strategy=strategy
                )
                if profile is None:
                    # Cascade resolution failed - fall back to default
                    profile = criteria.get_default_profile()
            else:
                # Single profile
                profile = criteria.get_priority_profile(priority_profile, project_root)
                if profile is None:
                    # Fall back to default if specified profile not found
                    profile = criteria.get_default_profile()

        # Get active rules for phase
        active_rules = self.rule_manager.get_rules_for_phase(criteria, phase_enum)

        # Check each rule
        passed_rules = []
        failed_rules = []
        warnings = []

        for rule in active_rules:
            passed, reason = self._check_rule(rule, artifact)

            if passed:
                passed_rules.append(rule)
            elif rule.severity.value == "fail":
                failed_rules.append(FailedRule(rule_id=rule.id, reason=reason, category=rule.category, weight=rule.weight, severity=rule.severity.value))
            else:  # warn or info
                warnings.append(FailedRule(rule_id=rule.id, reason=reason, category=rule.category, weight=rule.weight, severity=rule.severity.value))

        # Calculate score with priority weighting
        score = self.scorer.calculate_score(
            passed_rules=passed_rules,
            all_rules=active_rules,
            priority_profile=profile,
        )

        # Check if passed
        threshold = criteria.get_phase_config(phase_enum).threshold
        passed = self.scorer.check_passed(score, threshold, failed_rules)

        # Exp 55: Calculate category scores and severity counts for quality gates
        category_scores = self.scorer.get_category_scores(
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            all_rules=active_rules,
        )
        severity_counts = self.scorer.get_severity_counts(
            failed_rules=failed_rules,
            warnings=warnings,
        )

        # Build category breakdown for JSON reports
        category_breakdown = {
            "categories": [
                {
                    "name": cat,
                    "score": stats["score"],
                    "passed": stats["passed"],
                    "failed": stats["failed"],
                    "total": stats["total"],
                }
                for cat, stats in category_scores.items()
            ],
            "total_issues": len(failed_rules) + len(warnings),
        }

        return EvaluationResult(
            score=score,
            passed=passed,
            threshold=threshold,
            phase=phase,
            passed_rules=[r.id for r in passed_rules],
            failed_rules=failed_rules,
            warnings=warnings,
            evaluated_at=datetime.now().isoformat(),
            priority_profile=priority_profile,
            category_breakdown=category_breakdown,  # Exp 55
            category_scores=category_scores,  # Exp 55
            severity_counts=severity_counts,  # Exp 55
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
            "correctness.type_hints": self._check_type_hints,
            "correctness.structure": self._check_structure,
            "security.input_validation": self._check_input_validation,
            "security.secrets": self._check_secrets,

            # Security template rules (Exp 19)
            "security.no_hardcoded_secrets": self._check_secrets,
            "security.sql_injection_prevention": self._check_sql_injection_prevention,
            "security.xss_prevention": self._check_xss_prevention,
            "security.authentication": self._check_authentication,
            "security.authorization": self._check_authorization,
            "security.https_only": self._check_https_only,
            "security.csrf_protection": self._check_csrf_protection,

            # Security template Phase B rules (Exp 20)
            "security.error_handling": self._check_secure_error_handling,
            "security.cors_configuration": self._check_cors_configuration,
            "security.csp_headers": self._check_csp_headers,
            "security.rate_limiting": self._check_rate_limiting,
            "security.jwt_token_handling": self._check_jwt_token_handling,
            "security.env_variable_usage": self._check_env_variable_usage,

            # Security template remaining Phase B rules (Exp 21)
            "security.dependencies": self._check_dependencies,
            "security.api_key_management": self._check_api_key_management,
            "security.secret_rotation": self._check_secret_rotation,

            # GraphQL security rules (Exp 23)
            "security.graphql_query_depth_limiting": self._check_graphql_query_depth_limiting,
            "security.graphql_query_complexity_analysis": self._check_graphql_query_complexity_analysis,
            "security.graphql_introspection_disabled": self._check_graphql_introspection_disabled,
            "security.graphql_rate_limiting": self._check_graphql_rate_limiting,
            "security.graphql_batch_query_limiting": self._check_graphql_batch_query_limiting,
            "security.graphql_persisted_queries": self._check_graphql_persisted_queries,
            "security.graphql_field_authorization": self._check_graphql_field_authorization,
            "security.graphql_mutation_idempotency": self._check_graphql_mutation_idempotency,

            # Database Phase A rules (Exp 27)
            "correctness.primary_key": self._check_db_primary_key,
            "correctness.foreign_keys": self._check_db_foreign_keys,
            "correctness.indexes": self._check_db_indexes,
            "correctness.data_types": self._check_db_data_types,
            "correctness.not_null": self._check_db_not_null,
            "security.sql_injection": self._check_db_sql_injection,
            "correctness.timestamps": self._check_db_timestamps,

            # Frontend Phase A rules (Exp 28)
            "correctness.components": self._check_fe_components,
            "correctness.state_management": self._check_fe_state_management,
            "quality.props_validation": self._check_fe_props_validation,
            "correctness.routing": self._check_fe_routing,
            "quality.responsive": self._check_fe_responsive,
            "accessibility.alt_text": self._check_fe_alt_text,

            # Backend Phase A rules (Exp 29)
            "correctness.api_structure": self._check_be_api_structure,
            "correctness.service_layer": self._check_be_service_layer,
            "correctness.dependency_injection": self._check_be_dependency_injection,
            "quality.error_responses": self._check_be_error_responses,
            "correctness.validation": self._check_be_validation,
            "quality.logging": self._check_be_logging,

            # Testing Phase A rules (Exp 30)
            "correctness.test_structure": self._check_test_structure,
            "correctness.assertions": self._check_test_assertions,
            "quality.test_isolation": self._check_test_isolation,
            "correctness.edge_cases": self._check_test_edge_cases,
            "quality.mocks_usage": self._check_test_mocks,
            "correctness.error_tests": self._check_test_error_tests,
            "quality.coverage": self._check_test_coverage,
            "testing.e2e_coverage": self._check_test_e2e,
            "testing.component_testing": self._check_test_component,

            # Config Phase A rules (Exp 31)
            "correctness.required_fields": self._check_config_required_fields,
            "correctness.field_types": self._check_config_field_types,
            "quality.comments": self._check_config_comments,

            # Docs rules (+ Exp 31)
            "correctness.title": self._check_title,
            "correctness.purpose": self._check_purpose,
            "quality.installation": self._check_installation,
            "quality.usage": self._check_usage,
            "correctness.links": self._check_docs_links,
            "quality.structure": self._check_docs_structure,

            # Code-Gen Phase B rules (Exp 32)
            "performance.complexity": self._check_complexity,
            "correctness.resource_cleanup": self._check_resource_cleanup,
            "quality.exception_handling": self._check_exception_handling,
            "correctness.imports": self._check_imports,
            "quality.context_managers": self._check_context_managers,

            # Backend Phase B rules (Exp 33)
            "performance.async_operations": self._check_async_operations,
            "quality.http_status_codes": self._check_http_status_codes,
            "correctness.content_negotiation": self._check_content_negotiation,
            "quality.resource_naming": self._check_resource_naming,
            "quality.security_headers": self._check_security_headers,

            # Backend Phase B remaining rules (Exp 35)
            "quality.domain_errors": self._check_domain_errors,
            "quality.error_consistency": self._check_error_consistency,
            "security.stack_trace_sanitization": self._check_stack_trace_sanitization,
            "quality.api_versioning": self._check_api_versioning,
            "correctness.schema_validation": self._check_schema_validation,
            "quality.idempotency": self._check_idempotency,

            # Backend GraphQL Phase B rules (Exp 39)
            "quality.graphql_n_plus1_prevention": self._check_gql_n_plus1,
            "quality.graphql_error_handling": self._check_gql_error_handling,
            "quality.graphql_pagination": self._check_gql_pagination,
            "quality.graphql_subscriptions_auth": self._check_gql_subscriptions_auth,
            "quality.graphql_description_documentation": self._check_gql_description_docs,
            "quality.graphql_federation_consistency": self._check_gql_federation,
            "performance.graphql_query_cost_analysis": self._check_gql_query_cost,

            # Frontend Phase B rules (Exp 36)
            "performance.lazy_loading": self._check_fe_lazy_loading,
            "quality.semantic_html": self._check_fe_semantic_html,
            "quality.css_organization": self._check_fe_css_organization,
            "performance.react_hooks_optimization": self._check_fe_hooks_optimization,
            "correctness.error_boundaries": self._check_fe_error_boundaries,
            "quality.component_composition": self._check_fe_component_composition,
            "quality.api_integration": self._check_fe_api_integration,
            "quality.form_validation": self._check_fe_form_validation,
            "quality.environment_config": self._check_fe_environment_config,
            "quality.state_persistence": self._check_fe_state_persistence,

            # Database Phase B rules (Exp 41)
            "performance.denormalization": self._check_db_denormalization,
            "quality.migrations": self._check_db_migrations,
            "quality.constraints": self._check_db_constraints,
            "quality.transaction_boundaries": self._check_db_transaction_boundaries,
            "quality.query_isolation": self._check_db_query_isolation,
            "correctness.unique_constraints": self._check_db_unique_constraints,
            "security.sensitive_data": self._check_db_sensitive_data,
            "quality.connection_pooling": self._check_db_connection_pooling,
            "quality.backup_strategy": self._check_db_backup_strategy,

            # Config Phase B rules (Exp 42)
            "quality.defaults": self._check_config_defaults,
            "quality.environment_vars": self._check_config_environment_vars,
            "correctness.value_ranges": self._check_config_value_ranges,
            "correctness.enum_validation": self._check_config_enum_validation,
            "quality.env_separation": self._check_config_env_separation,
            "security.secret_references": self._check_config_secret_references,
            "security.sensitive_fields": self._check_config_sensitive_fields,
            "performance.optimizations": self._check_config_optimizations,

        }

        method = check_methods.get(rule.id)
        if method:
            return method(artifact, artifact_lower)

        # Fallback: keyword matching with noise filtering
        keywords = self._extract_keywords(rule.check)

        if not keywords:
            return False, "No meaningful keywords in rule check"

        found = sum(1 for kw in keywords if kw in artifact_lower)

        if found >= len(keywords) * 0.5:  # 50% of keywords
            return True, f"Found {found}/{len(keywords)} keywords"
        else:
            return False, f"Only found {found}/{len(keywords)} keywords"

    # Noise words filtered from keyword fallback matching
    _KEYWORD_NOISE_WORDS = frozenset({
        "verify", "check", "ensure", "validate", "confirm",
        "the", "a", "an", "is", "are", "was", "were",
        "for", "of", "in", "on", "to", "and", "or", "no", "not",
        "with", "that", "this", "from", "by", "at", "as",
        "should", "must", "can", "be", "has", "have",
        "used", "using", "properly", "correctly",
    })

    @staticmethod
    def _extract_keywords(check_text: str) -> List[str]:
        """Extract meaningful keywords from rule check description.

        Handles: empty/None check, punctuation stripping, noise word filtering,
        compound word splitting (e.g., 'useState/useReducer' -> two keywords).

        Returns:
            List of lowercase meaningful keywords
        """
        if not check_text or not check_text.strip():
            return []

        # Split on whitespace, then split compound tokens on /
        raw_tokens = check_text.lower().split()
        tokens = []
        for token in raw_tokens:
            if "/" in token:
                tokens.extend(token.split("/"))
            else:
                tokens.append(token)

        # Strip punctuation from edges and filter noise
        import string
        keywords = []
        for token in tokens:
            cleaned = token.strip(string.punctuation)
            if cleaned and len(cleaned) >= 2 and cleaned not in Evaluator._KEYWORD_NOISE_WORDS:
                keywords.append(cleaned)

        return keywords

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

    # Patterns that indicate real authentication/authorization documentation
    _AUTH_DOC_PATTERNS = [
        r"\b(?:bearer|basic)\s+(?:token|auth)",  # Bearer token, Basic auth
        r"\bauthorization\s*:",                    # Authorization: header
        r"\bapi[_\s-]?key\b",                    # API key, api_key, api-key
        r"\boauth\s*[12]?\b",                     # OAuth, OAuth2
        r"\bjwt\b",                               # JWT
        r"\b(?:auth|authn|authz)\s+(?:endpoint|middleware|guard|decorator|required)",  # auth endpoint/middleware
        r"\blogin\s*\(",                          # login() function call
        r"\b(?:sign[_\s]?in|sign[_\s]?up)\b",    # sign_in, sign up
        r"\b(?:access|refresh)[_\s]?token\b",     # access_token, refresh token
        r"@(?:requires_auth|login_required|authenticate)\b",  # decorators
        r"\bAuthentication\b",                    # Authentication section heading (case-sensitive)
        r"\bBearer\b",                            # Bearer (case-sensitive)
    ]

    def _check_auth_documentation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for real authentication documentation patterns"""
        found = []
        for pattern in self._AUTH_DOC_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} auth documentation patterns"

    # Patterns that indicate real parameter documentation (not just generic words)
    _PARAMETER_DOC_PATTERNS = [
        r"\bparam(?:eter)?s?\s*[:\-|]",          # param:, parameters:, params -
        r"\bquery\s+(?:param|string|parameter)",  # query param, query string
        r"\brequest\s+body\b",                    # request body
        r"\b(?:path|query|header|body)\s+param",  # path param, query param
        r"@param\b",                               # JSDoc @param
        r":param\s+\w+:",                          # Sphinx :param name:
        r"\bArgs\s*:",                            # Google-style Args:
        r"\bParameters\s*:",                      # numpy-style Parameters:
        r"\brequired\s*[:\-]\s*(?:true|false|yes|no)", # required: true
        r"\btype\s*:\s*(?:string|integer|number|boolean|array|object)", # type: string (OpenAPI)
        r"\bin\s*:\s*(?:query|path|header|body|cookie)", # in: query (OpenAPI)
        r"\b(?:request|req)\.\s*(?:params|query|body|headers)\b", # req.params, request.body
        r"\bargument\s*[:\-|]",                   # argument: / argument -
    ]

    def _check_parameters(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for real parameter documentation patterns"""
        found = []
        for pattern in self._PARAMETER_DOC_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} parameter documentation patterns"

    # Patterns that indicate real response/schema documentation (not just "return" + "result")
    _RESPONSE_DOC_PATTERNS = [
        r"\bresponse\s*(?:schema|body|code|status|type|format)\b",  # response schema/body/code
        r"\b(?:200|201|204|400|401|403|404|500)\s*[:\-]",  # 200: OK, 404 - Not Found
        r"\breturn(?:s|ed)?\s+(?:a|the|an)\s+",  # returns a/the/an (doc style)
        r"\b(?:response|output)\s*:\s*$",         # response: (on its own line, YAML-like)
        r"\bschema\s*[:\{]",                      # schema: or schema {
        r"\b(?:response|output)\s+(?:example|format|type|object)\b",  # response example/format
        r"\breturn\s+type\b",                     # return type
        r'\b"(?:status|data|error|message|result)"\s*:',  # JSON keys in response examples
        r"\bContent-Type\s*:",                    # Content-Type header
        r"\bapplication/json\b",                  # application/json
    ]

    def _check_responses(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for real response/schema documentation patterns"""
        found = []
        for pattern in self._RESPONSE_DOC_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} response documentation patterns"

    # Patterns that indicate real test constructs (not just the word "test")
    _TEST_PATTERNS = [
        r"\bdef\s+test_\w+",              # Python: def test_something()
        r"\bclass\s+Test\w+",             # Python: class TestSomething
        r"\bimport\s+(?:pytest|unittest)", # Python: import pytest / import unittest
        r"\bfrom\s+(?:pytest|unittest)\b", # Python: from pytest import ...
        r"\b(?:pytest|unittest)\.main\b",  # pytest.main() / unittest.main()
        r"\bdescribe\s*\(",               # JS: describe('...',
        r"\bit\s*\(\s*['\"]",             # JS: it('should...', / it("should...",
        r"\btest\s*\(\s*['\"]",           # JS: test('should...',
        r"\bexpect\s*\(",                 # JS: expect(result)
        r"\bassert\s+\w+",               # Python: assert something
        r"\b(?:assert|expect)\w*\.\w+\(", # assert/expect chaining: assertEquals(), expect().toBe()
        r"@pytest\.\w+",                  # @pytest.mark, @pytest.fixture
        r"\bbeforeEach\s*\(",             # JS: beforeEach(
        r"\bafterEach\s*\(",              # JS: afterEach(
        r"\bsetup_method\b",             # Python: setup_method
        r"\bteardown_method\b",          # Python: teardown_method
    ]

    def _check_tests(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for real test constructs (not just the word 'test')"""
        found = []
        for pattern in self._TEST_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} test patterns"

    # Patterns that indicate real error handling constructs (not just keywords)
    _ERROR_HANDLING_PATTERNS = [
        r"\btry\s*:",                    # Python try:
        r"\btry\s*\{",                   # JS/Java try {
        r"\bexcept\s+\w+",              # except Exception, except ValueError
        r"\bexcept\s*:",                 # bare except:
        r"\bcatch\s*\(",                 # catch(e), catch (Exception e)
        r"\bcatch\s*\{",                 # catch {
        r"\braise\s+\w+",               # raise ValueError, raise Exception
        r"\bthrow\s+\w+",               # throw new Error, throw error
        r"\bfinally\s*[:{]",            # finally: or finally {
        r"\brescue\s+\w+",              # Ruby rescue StandardError
        r"\bon_error\s*\(",             # on_error callback
        r"\berror_handler\s*\(",        # error_handler()
        r"\.catch\s*\(",                # promise.catch()
        r"\bwith\s+\w+\s*\(.*\)\s*:",  # Python context manager (with open() as f:)
    ]

    def _check_error_handling(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for real error handling constructs (not just keywords)"""
        found = []
        for pattern in self._ERROR_HANDLING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} error-handling patterns"

    # Regex for real Python comments: # at line start or after whitespace, followed by space/text
    _COMMENT_PATTERN = re.compile(
        r"(?:^|\n)\s*#\s+\S"  # indented or not, # followed by space and text
        r"|(?:^|\n)\s*//\s*\S"  # JS/C++ style // comment
        r'|"""\s*\S'  # docstring with content
        r"|'''\s*\S"  # single-quote docstring with content
    )

    def _check_readability(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for real comments/docstrings (not CSS colors or URL anchors)"""
        has_docstring = '"""' in artifact or "'''" in artifact
        if has_docstring:
            return True, "Has docstrings"
        matches = self._COMMENT_PATTERN.findall(artifact)
        if matches:
            return True, f"Has {len(matches)} comment(s)"
        return False, "No comments or docstrings found"

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

    # Patterns that indicate real input validation logic (not just keyword presence)
    _VALIDATION_PATTERNS = [
        r"\bvalidate\s*\(",           # validate(data)
        r"\bsanitize\s*\(",           # sanitize(input)
        r"\bis_valid\s*\(",           # obj.is_valid()
        r"\braise\s+(?:ValueError|TypeError|ValidationError)",  # raise ValueError
        r"\bif\s+not\s+isinstance\b", # if not isinstance(x, int)
        r"\bif\s+isinstance\b",       # if isinstance(x, int)
        r"\bassert\s+isinstance\b",   # assert isinstance(x, int)
        r"\bschema\.validate\b",      # schema.validate(data)
        r"@validator\b",              # pydantic @validator
        r"@field_validator\b",        # pydantic v2 @field_validator
        r"\bif\s+len\s*\(",           # if len(x) > 0
        r"\bif\s+not\s+\w+\s*:",      # if not data:
        r"\bverify\s*\(",             # verify(token)
        r"\bensure\s*\(",             # ensure(condition)
        r"\bcheck_\w+\s*\(",          # check_permissions(), check_auth()
        r"\bvalidation_error",        # validation_error handling
    ]

    def _check_input_validation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for input validation patterns (not just keywords)"""
        found = []
        for pattern in self._VALIDATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} validation patterns"

    # Patterns that indicate a value is a placeholder, not a real secret
    _PLACEHOLDER_PATTERNS = [
        r"^\$\{",          # ${ENV_VAR}
        r"^\$\(",          # $(ENV_VAR)
        r"^%\w+%$",        # %ENV_VAR%
        r"^\<.+\>$",       # <your-secret>
        r"^YOUR_",         # YOUR_API_KEY_HERE
        r"_HERE$",         # API_KEY_HERE
        r"^xxx+$",         # xxx, xxxx
        r"^\*{3,}",        # ***, ****REDACTED****
        r"^CHANGE.?ME",    # CHANGEME, CHANGE_ME
        r"^TODO",          # TODO: replace
        r"^REPLACE",       # REPLACE_WITH_YOUR_KEY
        r"^example",       # example_token
        r"^test$",         # test
        r"^dummy",         # dummy_key
        r"^fake",          # fake_token
        r"^placeholder",   # placeholder
        r"^\.\.\.$",       # ...
    ]

    # Patterns for known secret formats (value-only, no assignment context needed)
    _KNOWN_SECRET_FORMATS = [
        (r"\bAKIA[0-9A-Z]{16}\b", "AWS Access Key ID"),
        (r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}", "JWT token"),
        (r"\bghp_[A-Za-z0-9]{36}\b", "GitHub personal access token"),
        (r"\bsk-[A-Za-z0-9]{20,}\b", "OpenAI/Stripe secret key"),
        (r"(?:postgresql|postgres|mysql|mongodb|redis|amqp)://\w+:[^@\s]{3,}@", "connection string with credentials"),
    ]

    def _check_secrets(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for no hardcoded secrets"""
        # Check assignment-based patterns (password = "...", etc.)
        secret_patterns = [
            r"password\s*=\s*['\"]([^'\"]+)['\"]",
            r"api_key\s*=\s*['\"]([^'\"]+)['\"]",
            r"secret\s*=\s*['\"]([^'\"]+)['\"]",
            r"token\s*=\s*['\"]([^'\"]+)['\"]",
        ]
        for pattern in secret_patterns:
            match = re.search(pattern, artifact, re.IGNORECASE)
            if match:
                value = match.group(1)
                if not self._is_placeholder(value):
                    return False, "Potential hardcoded secret found"

        # Check known secret formats (AWS keys, JWT, GitHub PAT, etc.)
        for pattern, label in self._KNOWN_SECRET_FORMATS:
            if re.search(pattern, artifact):
                return False, f"Potential {label} found"

        return True, "No hardcoded secrets detected"

    def _is_placeholder(self, value: str) -> bool:
        """Check if a value is a placeholder, env var reference, or example"""
        stripped = value.strip()
        for pattern in self._PLACEHOLDER_PATTERNS:
            if re.search(pattern, stripped, re.IGNORECASE):
                return True
        return False

    # Exp 19: Patterns for SQL injection prevention
    _SQL_INJECTION_PATTERNS = [
        r"\bparameterized\s+quer(?:y|ies)\b",      # parameterized queries
        r"\bprepared\s+statement",                   # prepared statement
        r"\bplaceholder\s*[?%$]",                    # placeholder ?, %s, $1
        r"\bORM\b",                                  # ORM usage
        r"\b(?:SQLAlchemy|Sequelize|Prisma|TypeORM|Hibernate|ActiveRecord|Django\s+ORM)\b",  # specific ORMs
        r"\bbind\s*(?:param|variable|value)",        # bind parameters
        r"\bquery\s*\(\s*['\"].*\?\s*['\"]",        # query("... ? ...", args)
        r"\bexecute\s*\(\s*['\"].*%s",              # execute("... %s ...", args)
        r"\bsanitize\s*\(",                          # sanitize() call
        r"\bescape\s*\(",                            # escape() call
        r"\bno\s+(?:string\s+)?concatenation\b",    # no string concatenation
        r"\bsql\s+injection\b",                      # explicit mention of SQL injection
    ]

    def _check_sql_injection_prevention(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for SQL injection prevention patterns"""
        found = []
        for pattern in self._SQL_INJECTION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} SQL injection prevention patterns"

    # Exp 19: Patterns for XSS prevention
    _XSS_PREVENTION_PATTERNS = [
        r"\b(?:output|html)\s+encoding\b",           # output/html encoding
        r"\b(?:escape|sanitize)\s*(?:html|output)\b", # escape/sanitize HTML
        r"\bCSP\b",                                   # Content Security Policy
        r"\bContent-Security-Policy\b",               # CSP header
        r"\binnerHTML\b",                              # innerHTML (checking for unsafe usage)
        r"\btextContent\b",                            # safe textContent usage
        r"\bDOMPurify\b",                              # DOMPurify library
        r"\b(?:xss|cross.site.scripting)\b",          # explicit XSS mention
        r"\bsanitize\s*\(",                            # sanitize() call
        r"\b(?:encode|escape)(?:Html|URI|Url)\b",     # encodeHtml, escapeURI
        r"\bunsafe-inline\b",                          # CSP directive
        r"\bX-XSS-Protection\b",                      # XSS protection header
    ]

    def _check_xss_prevention(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for XSS prevention patterns"""
        found = []
        for pattern in self._XSS_PREVENTION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} XSS prevention patterns"

    # Exp 19: Patterns for authentication implementation
    _AUTHENTICATION_PATTERNS = [
        r"\b(?:auth|authn)\s+middleware\b",           # auth middleware
        r"@(?:requires_auth|login_required|authenticate|auth_required)\b",  # decorators
        r"\b(?:passport|devise|guardian|spring.security)\b",  # auth frameworks
        r"\bAuthenticate\b",                           # Authenticate (case-sensitive)
        r"\b(?:sign[_\s]?in|log[_\s]?in)\s*\(",      # sign_in(), login()
        r"\b(?:Bearer|Basic)\s+(?:token|auth)\b",     # Bearer token
        r"\bauthorization\s*:\s*['\"]?Bearer\b",      # Authorization: Bearer
        r"\b(?:session|cookie)\s+(?:auth|based)\b",    # session auth, cookie-based
        r"\bmfa\b",                                    # MFA
        r"\btwo.factor\b",                             # two-factor
        r"\bauth\s+guard\b",                           # auth guard
        r"\b(?:verify|validate)\s*(?:token|session|credentials)\b",  # verify token
    ]

    def _check_authentication(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for authentication implementation patterns"""
        found = []
        for pattern in self._AUTHENTICATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} authentication patterns"

    # Exp 19: Patterns for authorization checks
    _AUTHORIZATION_PATTERNS = [
        r"\b(?:authz|authorization)\s+(?:check|middleware|guard|policy)\b",  # authz check
        r"\b(?:role|permission)\s*(?:check|guard|required)\b",  # role check
        r"\b(?:can|has_permission|is_authorized|has_role)\s*\(",  # can(), has_permission()
        r"@(?:requires_role|requires_permission|authorize|permission_required)\b",  # decorators
        r"\bRBAC\b",                                   # Role-Based Access Control
        r"\bABAC\b",                                   # Attribute-Based Access Control
        r"\bACL\b",                                    # Access Control List
        r"\b(?:access|permission)\s+(?:control|denied|granted)\b",  # access control
        r"\bforbidden\b",                              # forbidden response
        r"\b(?:check|verify)\s*(?:permission|role|access)\b",  # check permission
        r"\bpolicy\s*\.\s*(?:can|authorize|check)\b", # policy.can(), policy.authorize()
    ]

    def _check_authorization(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for authorization implementation patterns"""
        found = []
        for pattern in self._AUTHORIZATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} authorization patterns"

    # Exp 19: Patterns for HTTPS enforcement
    _HTTPS_PATTERNS = [
        r"\bhttps://",                                 # HTTPS URL
        r"\bHTTPS\s+(?:only|redirect|enforce|required)\b",  # HTTPS only/redirect
        r"\bHSTS\b",                                   # HSTS header
        r"\bStrict-Transport-Security\b",              # full HSTS header name
        r"\bssl\s*[=:]\s*(?:true|on)\b",              # ssl=true
        r"\bforce_ssl\b",                              # force_ssl setting
        r"\bsecure\s*[=:]\s*true\b",                  # secure: true (cookie flag)
        r"\b(?:redirect|rewrite).*https\b",           # redirect to https
        r"\btls\b",                                    # TLS
        r"\bcertificate\b",                            # certificate
    ]

    def _check_https_only(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for HTTPS enforcement patterns"""
        found = []
        for pattern in self._HTTPS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} HTTPS enforcement patterns"

    # Exp 19: Patterns for CSRF protection
    _CSRF_PATTERNS = [
        r"\bcsrf\b",                                   # CSRF mention
        r"\bxsrf\b",                                   # XSRF (alternative name)
        r"\bcross.site\s+request\s+forgery\b",        # full name
        r"\bSameSite\s*[=:]\s*(?:Strict|Lax|None)\b", # SameSite cookie attribute
        r"\b(?:csrf|xsrf)[_\-]?token\b",              # csrf_token, xsrf-token
        r"\b(?:csrf|xsrf)[_\-]?protect\b",            # csrf_protect
        r"\borigin\s+(?:check|validation|header)\b",  # origin check
        r"\banti.?forgery\b",                          # anti-forgery (ASP.NET)
        r"\b(?:verify|validate)\s+origin\b",          # verify origin
        r"@csrf_exempt\b",                             # Django csrf_exempt decorator
    ]

    def _check_csrf_protection(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for CSRF protection patterns"""
        found = []
        for pattern in self._CSRF_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} CSRF protection patterns"

    # Exp 20: Patterns for secure error handling (no info leakage)
    _SECURE_ERROR_HANDLING_PATTERNS = [
        r"\bgeneric\s+error\s+message\b",              # generic error message
        r"\b(?:hide|mask|sanitize)\s+(?:error|stack|trace)\b",  # hide/mask errors
        r"\bno\s+stack\s*trace\b",                      # no stack trace
        r"\b(?:production|prod)\s+error\s+handler\b",  # production error handler
        r"\berror\s+(?:boundary|page|screen)\b",        # error boundary/page
        r"\b(?:500|internal)\s+server\s+error\b",       # 500 response
        r"\b(?:log|logger)\.\s*(?:error|exception)\b",  # log.error()
        r"\b(?:sentry|bugsnag|rollbar|datadog)\b",      # error tracking services
        r"\bcustom\s+error\s+(?:class|handler|response)\b",  # custom error handler
        r"\berrorHandler\s*\(",                          # errorHandler() middleware
        r"\b@(?:exception_handler|error_handler)\b",    # decorators
        r"\bapp\.use\s*\(\s*(?:error|err)\b",           # Express error middleware
    ]

    def _check_secure_error_handling(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for secure error handling patterns (no info leakage)"""
        found = []
        for pattern in self._SECURE_ERROR_HANDLING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} secure error handling patterns"

    # Exp 20: Patterns for CORS configuration
    _CORS_PATTERNS = [
        r"\bCORS\b",                                    # CORS mention
        r"\bAccess-Control-Allow-Origin\b",             # CORS header
        r"\bAccess-Control-Allow-Methods\b",            # CORS methods header
        r"\bAccess-Control-Allow-Headers\b",            # CORS headers header
        r"\bAccess-Control-Allow-Credentials\b",        # CORS credentials header
        r"\bcors\s*\(",                                  # cors() middleware call
        r"\bcors\s*[=:]\s*\{",                          # cors config object
        r"\ballowed[_\s]?origins?\b",                   # allowed_origins
        r"\borigin\s*[=:]\s*['\"\[]",                   # origin = "..." or origin: [...]
        r"\bcross[_\-\s]?origin\b",                     # cross-origin
    ]

    def _check_cors_configuration(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for CORS configuration patterns"""
        found = []
        for pattern in self._CORS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} CORS configuration patterns"

    # Exp 20: Patterns for Content Security Policy headers
    _CSP_HEADER_PATTERNS = [
        r"\bContent-Security-Policy\b",                 # CSP header
        r"\bCSP\b",                                      # CSP abbreviation
        r"\bdefault-src\b",                              # CSP directive
        r"\bscript-src\b",                               # CSP directive
        r"\bstyle-src\b",                                # CSP directive
        r"\bobject-src\b",                               # CSP directive
        r"\bimg-src\b",                                  # CSP directive
        r"\bframe-ancestors\b",                          # CSP directive
        r"\b(?:helmet|csp)\s*\(",                        # helmet() or csp() middleware
        r"\bunsafe-(?:inline|eval)\b",                   # CSP values
        r"\bnonce-[A-Za-z0-9+/=]+\b",                  # CSP nonce
        r"\breport-uri\b",                               # CSP reporting
    ]

    def _check_csp_headers(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for Content Security Policy header patterns"""
        found = []
        for pattern in self._CSP_HEADER_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} CSP header patterns"

    # Exp 20: Patterns for rate limiting
    _RATE_LIMITING_PATTERNS = [
        r"\brate[_\s\-]?limit(?:ing|er|ed)?\b",        # rate limit/limiting/limiter
        r"\bthrottle\b",                                 # throttle
        r"\brequests?\s+per\s+(?:second|minute|hour)\b", # requests per second
        r"\b(?:express-rate-limit|ratelimit|slowapi|django-ratelimit)\b",  # libraries
        r"\b(?:429|too\s+many\s+requests)\b",           # 429 status
        r"\bX-RateLimit-\w+\b",                          # rate limit headers
        r"\bbucket\s+(?:size|capacity)\b",              # token bucket
        r"\bsliding\s+window\b",                         # sliding window algorithm
        r"\bexponential\s+backoff\b",                    # backoff strategy
        r"\bmax[_\s]?requests?\b",                       # max_requests config
    ]

    def _check_rate_limiting(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for rate limiting patterns"""
        found = []
        for pattern in self._RATE_LIMITING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} rate limiting patterns"

    # Exp 20: Patterns for JWT token handling
    _JWT_HANDLING_PATTERNS = [
        r"\bjwt\b",                                      # JWT mention
        r"\bjson\s+web\s+token\b",                       # full name
        r"\b(?:verify|validate)\s*(?:jwt|token)\b",     # verify/validate JWT
        r"\btoken\s+expir(?:ation|y|es?)\b",            # token expiration
        r"\b(?:access|refresh)\s*token\b",               # access/refresh token
        r"\bhttpOnly\b",                                  # httpOnly cookie
        r"\bsecure\s*:\s*true\b",                        # secure cookie flag
        r"\b(?:jsonwebtoken|jose|pyjwt|jwt-decode)\b",  # JWT libraries
        r"\bjwt\.(?:sign|verify|decode)\b",              # jwt.sign/verify/decode
        r"\btoken\s+(?:revocation|blacklist|invalidat)\b", # token management
        r"\b(?:iat|exp|nbf|iss|aud|sub)\b",             # JWT standard claims
    ]

    def _check_jwt_token_handling(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for JWT token handling patterns"""
        found = []
        for pattern in self._JWT_HANDLING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} JWT handling patterns"

    # Exp 20: Patterns for environment variable usage
    _ENV_VARIABLE_PATTERNS = [
        r"\bprocess\.env\.\w+\b",                       # Node.js process.env
        r"\bos\.environ\b",                              # Python os.environ
        r"\bos\.getenv\s*\(",                            # Python os.getenv()
        r"\bENV\s*\[\s*['\"]",                           # Ruby ENV["..."]
        r"\b(?:dotenv|python-dotenv|django-environ)\b", # env libraries
        r"\b\.env\b",                                    # .env file mention
        r"\.gitignore\b",                                  # .gitignore mention (env context)
        r"\benvironment\s+variable\b",                   # explicit mention
        r"\b(?:secret|vault)\s+manager\b",              # secret manager
        r"\b(?:AWS\s+Secrets\s+Manager|HashiCorp\s+Vault|Azure\s+Key\s+Vault)\b",  # specific services
        r"\bconfig\s*\(\s*['\"](?:SECRET|KEY|TOKEN|PASSWORD)\b",  # config("SECRET_...")
    ]

    def _check_env_variable_usage(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for environment variable usage patterns"""
        found = []
        for pattern in self._ENV_VARIABLE_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} env variable usage patterns"

    # Exp 21: Patterns for dependency security checks
    _DEPENDENCY_SECURITY_PATTERNS = [
        r"\b(?:npm|yarn|pnpm)\s+audit\b",               # npm audit, yarn audit
        r"\bpip\s+audit\b",                               # pip audit
        r"\b(?:safety|pip-audit)\s+check\b",              # safety check
        r"\b(?:snyk|dependabot|renovate|mend)\b",         # dependency scanning tools
        r"\b(?:CVE|vulnerability|vulnerable)\b",           # vulnerability mentions
        r"\bdependency\s+(?:update|upgrade|scan|check|audit)\b",  # dependency operations
        r"\bpackage[_\s\-]?lock\b",                         # package-lock.json
        r"\block\s*file\b",                                # lock file
        r"\b(?:outdated|deprecated)\s+(?:package|dependenc|module)\b",  # outdated packages
        r"\b(?:semver|semantic\s+version)\b",              # semver
        r"\bsupply\s+chain\b",                            # supply chain security
        r"\b(?:SBOM|software\s+bill\s+of\s+materials)\b", # SBOM
    ]

    def _check_dependencies(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for dependency security patterns"""
        found = []
        for pattern in self._DEPENDENCY_SECURITY_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} dependency security patterns"

    # Exp 21: Patterns for API key management
    _API_KEY_MANAGEMENT_PATTERNS = [
        r"\bapi[_\s\-]?key\s+(?:rotation|scope|permission|management)\b",  # API key management
        r"\bscoped\s+(?:key|permissions?|access)\b",       # scoped permissions
        r"\b(?:key|token)\s+rotation\b",                   # key rotation
        r"\bminimal\s+permission\b",                       # minimal permissions
        r"\bleast\s+privilege\b",                          # least privilege
        r"\b(?:revoke|invalidate)\s+(?:key|token)\b",     # revoke/invalidate
        r"\bapi[_\s\-]?key\s+(?:expir|ttl|lifetime)\b",   # key expiration
        r"\b(?:key|token)\s+(?:store|vault|manager)\b",    # key storage
        r"\bper[_\s\-]?(?:environment|env)\s+keys?\b",      # per-environment keys
        r"\b(?:read[_\s\-]?only|write[_\s\-]?only)\s+(?:key|token|access)\b",  # scoped access
    ]

    def _check_api_key_management(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for API key management patterns"""
        found = []
        for pattern in self._API_KEY_MANAGEMENT_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} API key management patterns"

    # Exp 21: Patterns for secret rotation
    _SECRET_ROTATION_PATTERNS = [
        r"\b(?:secret|key|token|cert(?:ificate)?)\s+rotation\b",  # secret rotation
        r"\brotate\s+(?:secret|key|token|cert|credential)\b",     # rotate secrets
        r"\b(?:expir(?:ation|y|es?)|ttl)\s+(?:monitor|check|alert)\b",  # expiration monitoring
        r"\bcertificate\s+(?:renewal|expir\w*|monitor)\b",  # certificate renewal/expiration
        r"\bauto(?:matic)?\s+rotation\b",                  # automatic rotation
        r"\brotation\s+(?:policy|schedule|interval)\b",    # rotation policy
        r"\b(?:AWS\s+Secrets\s+Manager|HashiCorp\s+Vault|Azure\s+Key\s+Vault)\b",  # secret managers
        r"\bkey\s+(?:lifecycle|versioning)\b",             # key lifecycle
        r"\b(?:graceful|zero[_\s\-]?downtime)\s+rotation\b",  # graceful rotation
        r"\b(?:old|previous|deprecated)\s+(?:key|secret|token)\b",  # old key handling
    ]

    def _check_secret_rotation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for secret rotation patterns"""
        found = []
        for pattern in self._SECRET_ROTATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} secret rotation patterns"

    # Exp 23: Patterns for GraphQL query depth limiting
    _GRAPHQL_DEPTH_LIMITING_PATTERNS = [
        r"\b(?:depth|max[_\s\-]?depth)\s*(?:limit|:|\=)",  # depth limit, maxDepth:
        r"\bgraphql[_\-\s]?depth[_\-\s]?limit\b",          # graphql-depth-limit package
        r"\b(?:depthLimit|depth_limit)\s*\(",               # depthLimit() function
        r"\bmax\s*(?:depth|nested|nesting)\b",              # max depth/nesting
        r"\bquery\s+depth\b",                               # query depth
        r"\bnested\s+(?:query|queries|field|level)\b",      # nested queries
        r"\b(?:depth|nesting)\s+(?:check|validation|restrict)\b",  # depth check
        r"\bvalidation[_\-\s]?rule.*depth\b",               # validation rule for depth
        r"\b(?:5|6|7|8|10)\s+levels?\b",                    # typical depth limits
        r"\b(?:graphql|query)\s+(?:complexity|cost).*depth\b",  # complexity with depth
    ]

    def _check_graphql_query_depth_limiting(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL query depth limiting patterns"""
        found = []
        for pattern in self._GRAPHQL_DEPTH_LIMITING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL depth limiting patterns"

    # Exp 23: Patterns for GraphQL query complexity analysis
    _GRAPHQL_COMPLEXITY_PATTERNS = [
        r"\b(?:query|graphql)\s+complexity\b",               # query complexity
        r"\bcomplexity\s+(?:limit|analysis|score|cost)\b",   # complexity limit/analysis
        r"\bgraphql[_\-\s]?(?:validation[_\-\s]?)?complexity\b",  # graphql-validation-complexity
        r"\bcost\s+(?:analysis|limit|based)\b",              # cost analysis
        r"\bfield\s+(?:cost|weight|complexity)\b",           # field cost/weight
        r"\bmax[_\s\-]?complexity\b",                         # maxComplexity
        r"\bcomplexity\s*[=:]\s*\d+",                        # complexity = N or complexity: N
        r"\b(?:complexity|cost)\s+(?:calculator|estimat)\b",  # complexity calculator
        r"@complexity\b",                                       # @complexity directive
        r"\bcomplexityLimit\s*\(",                             # complexityLimit() function
    ]

    def _check_graphql_query_complexity_analysis(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL query complexity analysis patterns"""
        found = []
        for pattern in self._GRAPHQL_COMPLEXITY_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL complexity analysis patterns"

    # Exp 23: Patterns for GraphQL introspection disabled in production
    _GRAPHQL_INTROSPECTION_PATTERNS = [
        r"\bintrospection\s*[=:]\s*(?:false|disabled|off)\b",  # introspection: false
        r"\bdisable[_\s]?introspection\b",                     # disable introspection
        r"\bintrospection\s+disabled\b",                        # introspection disabled
        r"\bno[_\s\-]?introspection\b",                         # no introspection
        r"\b(?:NODE_ENV|ENVIRONMENT|ENV)\s*[=!]=*\s*['\"]?production\b",  # env check
        r"\bproduction\s+(?:mode|environment|config)\b",       # production mode
        r"\b__schema\b",                                        # __schema (introspection query)
        r"\bintrospection\s+(?:query|queries)\b",              # introspection queries
        r"\bschema\s+(?:visibility|exposure|access)\b",        # schema visibility
        r"\bApolloServerPlugin.*introspection\b",              # Apollo introspection plugin
    ]

    def _check_graphql_introspection_disabled(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL introspection disabled in production"""
        found = []
        for pattern in self._GRAPHQL_INTROSPECTION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL introspection control patterns"

    # Exp 23: Patterns for GraphQL rate limiting (complexity-based)
    _GRAPHQL_RATE_LIMITING_PATTERNS = [
        r"\b(?:graphql|query)\s+rate[_\s\-]?limit\b",         # graphql rate limit
        r"\bcost[_\s\-]?based\s+rate[_\s\-]?limit\w*\b",       # cost-based rate limiting
        r"\bcomplexity[_\s\-]?based\s+(?:rate|limit|throttl)\w*\b",  # complexity-based limiting/throttling
        r"\bquery\s+cost\s+(?:limit|budget)\b",                # query cost limit
        r"\brate\s+limit.*(?:complexity|cost)\b",              # rate limit with complexity
        r"\b(?:complexity|cost)\s+(?:budget|quota|allowance)\b",  # complexity budget
        r"\bper[_\s\-]?query\s+(?:limit|cost|budget)\b",       # per-query limit
        r"\bthrottle.*(?:graphql|query|mutation)\b",            # throttle graphql
        r"\bgraphql[_\-\s]?rate[_\-\s]?limit\b",               # graphql-rate-limit package
        r"\bquery\s+(?:quota|budget)\b",                        # query quota
    ]

    def _check_graphql_rate_limiting(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL rate limiting patterns (complexity-based)"""
        found = []
        for pattern in self._GRAPHQL_RATE_LIMITING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL rate limiting patterns"

    # Exp 23: Patterns for GraphQL batch query limiting
    _GRAPHQL_BATCH_LIMITING_PATTERNS = [
        r"\bbatch\s+(?:query|queries|operation|request|limit)\b",  # batch query/limit
        r"\bmax[_\s\-]?(?:batch|operations?)\b",                   # maxBatch, max_operations
        r"\b(?:batch|operations?)\s+(?:per|limit|max|restrict)\b",  # batch per/limit
        r"\b(?:5|10|15|20)\s+operations?\b",                       # typical batch limits
        r"\bbatch[_\-\s]?(?:size|count|limit)\b",                  # batchSize, batch_count
        r"\b(?:limit|restrict)\s+batch\b",                         # limit/restrict batch
        r"\bmulti[_\-\s]?(?:query|operation)\b",                   # multi-query
        r"\bbatched\s+(?:requests?|quer(?:y|ies))\b",               # batched requests
        r"\barray\s+of\s+(?:query|queries|operation)\b",           # array of queries
        r"\boperation\s+(?:count|limit)\b",                        # operation count/limit
    ]

    def _check_graphql_batch_query_limiting(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL batch query limiting patterns"""
        found = []
        for pattern in self._GRAPHQL_BATCH_LIMITING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL batch limiting patterns"

    # Exp 23: Patterns for GraphQL persisted queries
    _GRAPHQL_PERSISTED_QUERIES_PATTERNS = [
        r"\bpersisted\s+quer(?:y|ies)\b",                      # persisted queries
        r"\bAPQ\b",                                              # Automatic Persisted Queries
        r"\bautomatic\s+persisted\b",                           # Automatic Persisted
        r"\bquery\s+(?:whitelist|allowlist|safelist)\b",        # query whitelist/allowlist
        r"\btrusted\s+(?:query|queries|operation)\b",           # trusted queries
        r"\bquery\s+(?:hash|id|registry)\b",                   # query hash/id/registry
        r"\bpre[_\-\s]?registered\s+(?:query|queries)\b",      # pre-registered queries
        r"\b(?:query|operation)\s+(?:document|store)\b",        # query document store
        r"\bsha256\s+hash\b",                                   # SHA256 hash (APQ)
        r"\b(?:persist|stored)\s+(?:query|queries|operation)\b",  # stored queries
    ]

    def _check_graphql_persisted_queries(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL persisted queries patterns"""
        found = []
        for pattern in self._GRAPHQL_PERSISTED_QUERIES_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL persisted queries patterns"

    # Exp 23: Patterns for GraphQL field-level authorization
    _GRAPHQL_FIELD_AUTH_PATTERNS = [
        r"\bfield[_\s\-]?level\s+(?:auth\w*|permissions?|access)\b",  # field-level auth/authorization
        r"\b@auth\b",                                              # @auth directive
        r"\b@(?:has_?role|requires_?role|authorized)\b",          # auth directives
        r"\bfield\s+(?:permission|authorization|guard)\b",        # field permission
        r"\bresolve[_\s]?(?:with|check)\s+(?:auth|permission)\b",  # resolve with auth
        r"\b(?:auth|permission)\s+(?:directive|middleware|guard)\b",  # auth directive
        r"\b(?:check|verify)\s+(?:field|resolver)\s+(?:permission|access)\b",  # check field permission
        r"\bgraphql[_\-\s]?(?:shield|auth)\b",                    # graphql-shield / graphql-auth
        r"\bfield\s+(?:visibility|access\s+control)\b",           # field visibility
        r"\bper[_\s\-]?field\s+(?:auth|security|check)\b",       # per-field auth
    ]

    def _check_graphql_field_authorization(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL field-level authorization patterns"""
        found = []
        for pattern in self._GRAPHQL_FIELD_AUTH_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL field authorization patterns"

    # Exp 23: Patterns for GraphQL mutation idempotency
    _GRAPHQL_IDEMPOTENCY_PATTERNS = [
        r"\bidempoten(?:cy|t)\s+(?:key|token|id)\b",             # idempotency key/token
        r"\bIdempotency[_\-\s]?Key\b",                           # Idempotency-Key header
        r"\bidempotent\s+(?:mutations?|operations?|requests?)\b",  # idempotent mutation(s)
        r"\b(?:mutation|request)\s+(?:idempoten|dedup)\b",        # mutation idempotency
        r"\b(?:retry|retries)\s+(?:safe|safely)\b",               # retry safely
        r"\bsafe\s+(?:retry|retries)\b",                          # safe retries
        r"\b(?:dedup|deduplicat)\w*\s+(?:mutation|request)\b",    # deduplicate mutations
        r"\b(?:client|request)[_\s\-]?(?:mutation[_\s\-]?)?id\b", # clientMutationId
        r"\bonce\s+(?:and\s+only\s+once|exactly)\b",              # once and only once
        r"\b(?:at[_\s\-]?most|exactly)[_\s\-]?once\b",           # at-most-once / exactly-once
    ]

    def _check_graphql_mutation_idempotency(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL mutation idempotency patterns"""
        found = []
        for pattern in self._GRAPHQL_IDEMPOTENCY_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} GraphQL idempotency patterns"

    # Exp 27: Patterns for database Phase A rules
    _DB_PRIMARY_KEY_PATTERNS = [
        r"\bPRIMARY\s+KEY\b",                          # PRIMARY KEY
        r"\bprimary[_\s]?key\b",                       # primary_key / primary key
        r"\bpk\b",                                     # pk shorthand
        r"\bid\s+(?:SERIAL|BIGSERIAL|INT|INTEGER|UUID)\b",  # id SERIAL/INT/UUID
        r"\bauto[_\s]?increment\b",                    # autoincrement
        r"\bIDENTITY\b",                               # IDENTITY (SQL Server)
        r"\bSERIAL\b",                                 # SERIAL (Postgres)
        r"\b_id\b",                                    # _id (MongoDB convention)
    ]

    _DB_FOREIGN_KEY_PATTERNS = [
        r"\bFOREIGN\s+KEY\b",                          # FOREIGN KEY
        r"\bREFERENCES\s+\w+",                         # REFERENCES table
        r"\bforeign[_\s]?key\b",                       # foreign_key
        r"\bON\s+DELETE\s+(?:CASCADE|SET\s+NULL|RESTRICT|NO\s+ACTION)\b",  # ON DELETE
        r"\bON\s+UPDATE\s+(?:CASCADE|SET\s+NULL|RESTRICT|NO\s+ACTION)\b",  # ON UPDATE
        r"\brelation(?:ship)?\b",                      # relationship
        r"\bForeignKey\b",                             # ORM ForeignKey
        r"\b(?:belongs_to|has_many|has_one)\b",        # Rails associations
    ]

    _DB_INDEX_PATTERNS = [
        r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\b",          # CREATE INDEX / CREATE UNIQUE INDEX
        r"\bindex\b",                                   # index mention
        r"\bINDEX\s*\(",                               # INDEX(column)
        r"\badd_index\b",                              # Rails add_index
        r"\bdb_index\s*=\s*True\b",                    # Django db_index=True
        r"\b(?:btree|hash|gin|gist|brin)\b",           # index types
        r"\bcomposite\s+(?:index|key)\b",              # composite index
        r"\b(?:covering|partial)\s+index\b",           # covering/partial index
    ]

    _DB_DATA_TYPES_PATTERNS = [
        r"\bVARCHAR\s*\(\d+\)",                        # VARCHAR(N)
        r"\b(?:INT|INTEGER|BIGINT|SMALLINT|TINYINT)\b",  # integer types
        r"\b(?:DECIMAL|NUMERIC)\s*\(\d+",              # DECIMAL(N,M)
        r"\b(?:TEXT|JSON|JSONB|BLOB|CLOB)\b",          # text/json/blob types
        r"\b(?:BOOLEAN|BOOL)\b",                       # boolean
        r"\b(?:TIMESTAMP|DATETIME|DATE|TIME)\b",       # temporal types
        r"\b(?:UUID|GUID)\b",                          # UUID/GUID
        r"\b(?:FLOAT|DOUBLE|REAL)\b",                  # floating point
        r"\b(?:CharField|IntegerField|FloatField|TextField)\b",  # Django fields
        r"\b(?:String|Integer|Float|Boolean|DateTime)\b",  # SQLAlchemy types
    ]

    _DB_NOT_NULL_PATTERNS = [
        r"\bNOT\s+NULL\b",                            # NOT NULL
        r"\bnot[_\s]?null\b",                         # not_null
        r"\bnullable\s*[:=]\s*(?:false|False)\b",     # nullable: false / nullable=False
        r"\brequired\b",                               # required field
        r"\bnull\s*[:=]\s*(?:false|False)\b",          # null: false / null=False
        r"\bblank\s*=\s*False\b",                      # Django blank=False
        r"\b(?:must|should)\s+(?:not\s+be\s+)?null\b", # must not be null
    ]

    _DB_SQL_INJECTION_PATTERNS = [
        r"\bparam(?:eter)?ized\s+quer(?:y|ies)\b",    # parameterized queries
        r"\bprepared\s+statements?\b",                  # prepared statement(s)
        r"\bplaceholder\b",                            # placeholder
        r"\bbind\s+(?:param|variable)\b",              # bind param/variable
        r"\b(?:ORM|orm)\b",                            # ORM usage
        r"\bsqlalchemy\b",                             # SQLAlchemy
        r"\bsequelize\b",                              # Sequelize
        r"\bprisma\b",                                 # Prisma
        r"\bquery\s*\(\s*['\"].*\?\s*['\"]",           # query("... ? ...", params)
        r"\b(?:no|avoid|prevent)\s+(?:string\s+)?concatenat",  # no string concatenation
        r"\bescap(?:e|ing)\s+(?:input|user|query)\b",  # escaping input
    ]

    _DB_TIMESTAMPS_PATTERNS = [
        r"\bcreated[_\s]?at\b",                        # created_at
        r"\bupdated[_\s]?at\b",                        # updated_at
        r"\bmodified[_\s]?at\b",                       # modified_at
        r"\b(?:date[_\s]?)?created\b",                 # date_created
        r"\b(?:date[_\s]?)?modified\b",                # date_modified
        r"\btimestamp\b",                               # timestamp column
        r"\bDEFAULT\s+(?:CURRENT_TIMESTAMP|NOW\(\)|GETDATE\(\))\b",  # DEFAULT CURRENT_TIMESTAMP
        r"\bauto_now(?:_add)?\b",                      # Django auto_now
    ]

    def _check_db_primary_key(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for primary key definitions in database schema"""
        found = []
        for pattern in self._DB_PRIMARY_KEY_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} primary key patterns"

    def _check_db_foreign_keys(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for foreign key definitions with constraints"""
        found = []
        for pattern in self._DB_FOREIGN_KEY_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} foreign key patterns"

    def _check_db_indexes(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for index definitions"""
        found = []
        for pattern in self._DB_INDEX_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} index patterns"

    def _check_db_data_types(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for appropriate data type definitions"""
        found = []
        for pattern in self._DB_DATA_TYPES_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} data type patterns"

    def _check_db_not_null(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for NOT NULL constraints on required fields"""
        found = []
        for pattern in self._DB_NOT_NULL_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} NOT NULL patterns"

    def _check_db_sql_injection(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for SQL injection prevention in database code"""
        found = []
        for pattern in self._DB_SQL_INJECTION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} SQL injection prevention patterns"

    def _check_db_timestamps(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for timestamp columns (created_at/updated_at)"""
        found = []
        for pattern in self._DB_TIMESTAMPS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} timestamp patterns"

    # Frontend Phase A patterns (Exp 28)
    # Backend Phase A patterns (Exp 29)
    _BE_API_STRUCTURE_PATTERNS = [
        r"\b(GET|POST|PUT|PATCH|DELETE)\s+/\w+",             # HTTP method + path
        r"\brouter\.(get|post|put|patch|delete)\s*\(",        # Express/Koa router
        r"@(Get|Post|Put|Patch|Delete)\s*\(",                    # NestJS decorators
        r"@app\.(get|post|put|patch|delete)\s*\(",             # Flask/FastAPI
        r"@(api_view|action)\b",                               # DRF decorators
        r"\bpath\s*\(\s*['\"]",                               # Django url path()
        r"\bAPIRouter\b",                                     # FastAPI APIRouter
        r"\bendpoint\b",                                      # generic endpoint mention
        r"\bREST\b",                                          # REST mention
        r"\b(GET|POST|PUT|DELETE)\b.*\b/\w+",                 # HTTP method in docs
    ]

    _BE_SERVICE_LAYER_PATTERNS = [
        r"\bclass\s+\w+Service\b",                            # class UserService
        r"\bclass\s+\w+Controller\b",                         # class UserController
        r"\bclass\s+\w+Repository\b",                         # class UserRepository
        r"\bservice\s*[:=]",                                   # service = / service:
        r"@Injectable\b",                                          # NestJS @Injectable
        r"@Service\b",                                             # Spring @Service
        r"\bservices/\w+",                                     # services/ directory
        r"\bcontrollers?/\w+",                                 # controllers/ directory
        r"\bbusiness.logic\b",                                 # business logic mention
        r"\bservice.layer\b",                                  # service layer mention
    ]

    _BE_DEPENDENCY_INJECTION_PATTERNS = [
        r"@Inject\b",                                              # NestJS/Angular @Inject
        r"@Injectable\b",                                          # NestJS @Injectable
        r"@Autowired\b",                                           # Spring @Autowired
        r"\bInject\s*\(",                                      # Python Inject()
        r"\bDepends\s*\(",                                     # FastAPI Depends()
        r"\bconstructor\s*\([^)]*\b\w+:\s*\w+",               # TS constructor injection
        r"\bdef\s+__init__\s*\(\s*self\s*,\s*\w+",            # Python __init__ injection
        r"\bproviders?\s*[:=]\s*\[",                           # NestJS providers array
        r"\bcontainer\.(register|resolve|bind)\b",             # DI container
        r"\bdependency.injection\b",                           # DI mention
    ]

    _BE_ERROR_RESPONSES_PATTERNS = [
        r"\b[45]\d{2}\b",                                      # 4xx/5xx status codes
        r"\bstatus\s*[:=]\s*[45]\d{2}\b",                     # status: 400
        r"\bHTTPException\b",                                  # FastAPI HTTPException
        r"\bHttpException\b",                                  # NestJS HttpException
        r"\bBadRequest\b",                                     # BadRequest error
        r"\bNotFound\b",                                       # NotFound error
        r"\berror.message\b",                                  # error.message field
        r"\b(error|err)\s*[:=]\s*{",                           # error response object
        r"\bres\.status\s*\(\s*[45]\d{2}\s*\)",               # Express res.status(400)
        r"\breturn\s+.*\berror\b",                             # return error response
    ]

    _BE_VALIDATION_PATTERNS = [
        r"\bvalidate\b",                                       # validate function/method
        r"\bvalidator\b",                                      # validator
        r"\bValidation\w*\b",                                  # ValidationError etc
        r"@IsString\b",                                            # class-validator
        r"@IsNotEmpty\b",                                          # class-validator
        r"\bBody\s*\(",                                        # NestJS Body()
        r"\bSchema\b",                                         # JSON Schema / Zod Schema
        r"\bz\.\w+\(\)",                                       # Zod z.string()
        r"\bJoi\.\w+\(",                                       # Joi validation
        r"\bpydantic\b",                                       # Pydantic
        r"\bBaseModel\b",                                      # Pydantic BaseModel
        r"\brequired\s*[:=]",                                  # required field
    ]

    _BE_LOGGING_PATTERNS = [
        r"\blogger\.\w+\(",                                    # logger.info/warn/error()
        r"\blogging\.\w+\(",                                   # Python logging.info()
        r"\bconsole\.(log|warn|error|info|debug)\(",           # console.log()
        r"\blog\.\w+\(",                                       # log.info()
        r"\b(winston|pino|bunyan|log4j|logback)\b",            # logging libraries
        r"@?Logger\b",                                             # NestJS Logger
        r"\bgetLogger\b",                                      # Python getLogger
        r"\blog.level\b",                                      # log level config
        r"\bstructured.log\b",                                 # structured logging
        r"\b(INFO|WARN|ERROR|DEBUG)\b",                        # log level constants
    ]

    def _check_be_api_structure(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for RESTful API structure with proper HTTP method mapping"""
        found = []
        for pattern in self._BE_API_STRUCTURE_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} API structure patterns"

    def _check_be_service_layer(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for service layer separation from controllers"""
        found = []
        for pattern in self._BE_SERVICE_LAYER_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} service layer patterns"

    def _check_be_dependency_injection(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for dependency injection patterns"""
        found = []
        for pattern in self._BE_DEPENDENCY_INJECTION_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} dependency injection patterns"

    def _check_be_error_responses(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper error responses with status codes and messages"""
        found = []
        for pattern in self._BE_ERROR_RESPONSES_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} error response patterns"

    def _check_be_validation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for input validation on all inputs"""
        found = []
        for pattern in self._BE_VALIDATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} validation patterns"

    def _check_be_logging(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for structured logging with context and levels"""
        found = []
        for pattern in self._BE_LOGGING_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} logging patterns"

    # Testing Phase A rules (Exp 30)
    _TEST_STRUCTURE_PATTERNS = [
        r"\barrange\b",                                            # AAA: Arrange
        r"\bact\b",                                                # AAA: Act
        r"\bgiven\b",                                              # BDD: Given
        r"\bwhen\b",                                               # BDD: When
        r"\bthen\b",                                               # BDD: Then
        r"\bdescribe\s*\(",                                        # describe() block
        r"\bit\s*\(",                                              # it() block
        r"\btest\s*\(",                                            # test() block
        r"\bdef\s+test_\w+",                                       # Python test method
        r"\b(beforeEach|afterEach|beforeAll|afterAll)\b",           # Jest/Mocha lifecycle
        r"\bsetup_method\b",                                       # pytest setup_method
        r"\bassert\b",                                             # assert keyword
    ]

    _TEST_ASSERTIONS_PATTERNS = [
        r"\bassert\s+\w+",                                        # Python assert
        r"\bassertEqual\b",                                       # unittest assertEqual
        r"\bassertTrue\b",                                        # unittest assertTrue
        r"\bassertRaises\b",                                      # unittest assertRaises
        r"\bassertIn\b",                                          # unittest assertIn
        r"\bexpect\s*\(",                                         # Jest/Chai expect()
        r"\b\.toBe\s*\(",                                         # Jest .toBe()
        r"\b\.toEqual\s*\(",                                      # Jest .toEqual()
        r"\b\.toHaveBeenCalled\b",                                # Jest mock assertion
        r"\b\.toThrow\s*\(",                                      # Jest .toThrow()
        r"\b\.toContain\s*\(",                                    # Jest .toContain()
        r"\bshould\.\w+",                                         # Chai should
        r"\bpytest\.raises\b",                                    # pytest.raises
    ]

    _TEST_ISOLATION_PATTERNS = [
        r"\b(beforeEach|afterEach)\s*\(",                          # Jest/Mocha hooks
        r"\b(beforeAll|afterAll)\s*\(",                             # Jest/Mocha hooks
        r"\bsetup_method\b",                                       # pytest setup_method
        r"\bteardown_method\b",                                    # pytest teardown_method
        r"\bsetUp\b",                                              # unittest setUp
        r"\btearDown\b",                                           # unittest tearDown
        r"@pytest\.fixture\b",                                     # pytest fixture
        r"\b@before\b",                                            # JUnit @Before
        r"\b@after\b",                                             # JUnit @After
        r"\bfixture\b",                                            # generic fixture mention
        r"\bconftest\b",                                           # pytest conftest
        r"\b(mock|patch|stub)\b",                                  # mocking for isolation
    ]

    _TEST_EDGE_CASES_PATTERNS = [
        r"\bnull\b",                                               # null value test
        r"\bNone\b",                                               # Python None test
        r"\bundefined\b",                                          # JS undefined test
        r"\bempty\b",                                              # empty value test
        r"\bnegative\b",                                           # negative value test
        r"\bboundar(y|ies)\b",                                     # boundary test
        r"\bedge.case\b",                                          # edge case mention
        r"\b(min|max|overflow|underflow)\b",                       # limit tests
        r"\binvalid\b",                                            # invalid input
        r"\bmalformed\b",                                          # malformed data
        r"\bcorrupt\b",                                            # corrupt data
        r"\b(timeout|retry)\b",                                    # timeout/retry
    ]

    _TEST_MOCKS_PATTERNS = [
        r"\bmock\b",                                               # mock keyword
        r"\bMock\(\)",                                             # Python Mock()
        r"\bMagicMock\b",                                          # Python MagicMock
        r"\bpatch\s*\(",                                           # Python patch()
        r"\b@patch\b",                                             # Python @patch decorator
        r"\bjest\.fn\b",                                           # Jest mock function
        r"\bjest\.mock\b",                                         # Jest module mock
        r"\bjest\.spyOn\b",                                        # Jest spy
        r"\bsinon\.\w+\b",                                         # Sinon.js mocks
        r"\bstub\b",                                               # stub keyword
        r"\bspy\b",                                                # spy keyword
        r"\bmockImplementation\b",                                 # Jest mock impl
        r"\bmockResolvedValue\b",                                  # Jest async mock
    ]

    _TEST_ERROR_TESTS_PATTERNS = [
        r"\bpytest\.raises\s*\(",                                  # pytest.raises()
        r"\bassertRaises\s*\(",                                    # unittest assertRaises
        r"\bexpect\s*\(.*\)\.toThrow\b",                           # Jest toThrow
        r"\.rejects\b",                                            # Jest .rejects
        r"\btry\b.*\bcatch\b",                                     # try/catch in test
        r"\bexcept\s+\w+",                                         # Python except
        r"\berror\b.*\btest\b|\btest\b.*\berror\b",                # error + test mention
        r"\bexception\b",                                          # exception keyword
        r"\bfail(ure|s|ed)?\b.*\b(test|case|scenario)\b",          # failure test
        r"\bthrows?\b",                                            # throws keyword
        r"\braise\b",                                              # Python raise
    ]

    _TEST_COVERAGE_PATTERNS = [
        r"\bcoverage\b",                                           # coverage keyword
        r"--cov\b",                                                # pytest --cov
        r"\bcollect.coverage\b",                                   # coverage collection
        r"\bcoverageThreshold\b",                                  # Jest coverage config
        r"\bnyc\b",                                                # Istanbul/nyc
        r"\bistanbul\b",                                           # Istanbul coverage
        r"\bcoverageReporters\b",                                  # Jest reporters
        r"\d+%\s*(coverage|covered|branch)\b",                     # percentage mention
        r"pytest-cov\b",                                           # pytest-cov plugin
        r"\bcoveralls\b",                                          # Coveralls service
        r"\bcodecov\b",                                            # Codecov service
    ]

    _TEST_E2E_PATTERNS = [
        r"\b(Playwright|playwright)\b",                            # Playwright
        r"\b(Cypress|cypress)\b",                                  # Cypress
        r"\b(Puppeteer|puppeteer)\b",                              # Puppeteer
        r"\b(Selenium|selenium)\b",                                # Selenium
        r"\b(e2e|end.to.end)\b",                                   # E2E keyword
        r"\bpage\.(goto|click|fill|waitFor)\b",                    # Playwright API
        r"\bcy\.\w+\(",                                            # Cypress API
        r"\bdriver\.\w+\(",                                        # Selenium driver
        r"\bbrowser\.\w+\(",                                       # browser automation
        r"\buser.journey\b",                                       # user journey test
    ]

    _TEST_COMPONENT_TESTING_PATTERNS = [
        r"@testing-library",                                       # Testing Library
        r"\brender\s*\(",                                          # render() call
        r"\bgetByRole\b",                                          # Testing Library query
        r"\bgetByText\b",                                          # Testing Library query
        r"\bgetByLabelText\b",                                     # Testing Library query
        r"\bgetByTestId\b",                                        # Testing Library query
        r"\bfireEvent\b",                                          # Testing Library events
        r"\buserEvent\b",                                          # Testing Library user events
        r"\bshallow\s*\(",                                         # Enzyme shallow
        r"\bmount\s*\(",                                           # Enzyme/Vue mount
        r"\bTestBed\b",                                            # Angular TestBed
        r"\bVue\s*Test\s*Utils\b",                                 # Vue Test Utils
        r"\bcomponent.test\b",                                     # component test file
    ]

    _FRONTEND_COMPONENT_PATTERNS = [
        r"\bexport\s+(?:default\s+)?(?:function|class|const)\s+\w+",  # export default function/class/const
        r"\bconst\s+\w+\s*[:=]\s*(?:\([^)]*\)|)\s*(?:=>|{)",  # arrow component
        r"\bfunction\s+\w+\s*\([^)]*\)\s*{",                  # function component
        r"\bclass\s+\w+\s+extends\s+(?:React\.)?Component",   # class component
        r"\breturn\s*\(\s*<",                                  # JSX return
        r"<\w+[A-Z]\w*[\s/>]",                                # PascalCase JSX tag (custom component)
        r"\bdefineComponent\b",                                # Vue defineComponent
        r"\b@Component\b",                                     # Angular @Component
        r"\bVue\.component\b",                                 # Vue.component
        r"\btemplate\s*:",                                      # Vue template option
    ]

    _FRONTEND_STATE_MGMT_PATTERNS = [
        r"\buseState\b",                                       # React useState
        r"\buseReducer\b",                                     # React useReducer
        r"\buseContext\b",                                     # React useContext
        r"\bsetState\b",                                       # class component setState
        r"\bthis\.state\b",                                    # class component state
        r"\bcreateStore\b",                                    # Redux/Zustand createStore
        r"\buseStore\b",                                       # Zustand/Pinia useStore
        r"\breactive\b",                                       # Vue reactive
        r"\bref\s*\(",                                         # Vue ref()
        r"\bcomputed\b",                                       # Vue/Angular computed
        r"\b@Input\b",                                         # Angular @Input
        r"\bSignal\b",                                         # Angular/Solid signals
    ]

    _FRONTEND_PROPS_VALIDATION_PATTERNS = [
        r"\binterface\s+\w+Props\b",                           # TypeScript interface Props
        r"\btype\s+\w+Props\b",                                # TypeScript type Props
        r"\bPropTypes\b",                                      # React PropTypes
        r"\bpropTypes\s*=",                                    # Component.propTypes =
        r"\bdefaultProps\b",                                   # defaultProps
        r"\bdefineProps\b",                                    # Vue defineProps
        r"\b@Prop\b",                                          # Vue/Angular @Prop
        r"\bprops\s*:\s*{",                                    # Vue props: { ... }
        r":\s*\w+Props\b",                                     # : ComponentProps type annotation
    ]

    _FRONTEND_ROUTING_PATTERNS = [
        r"\bRoute\b",                                          # React Route
        r"\bRouter\b",                                         # Router
        r"\bBrowserRouter\b",                                  # BrowserRouter
        r"\bSwitch\b",                                         # React Router Switch
        r"\bRoutes\b",                                         # React Router v6 Routes
        r"\buseNavigate\b",                                    # React Router useNavigate
        r"\buseRouter\b",                                      # Next.js/Vue useRouter
        r"\brouter\.(push|replace|go)\b",                      # router.push/replace
        r"\bcreateRouter\b",                                   # Vue createRouter
        r"\bRouterModule\b",                                   # Angular RouterModule
        r"\bpath\s*:\s*['\"/]",                                # route path definition
    ]

    _FRONTEND_RESPONSIVE_PATTERNS = [
        r"@media\b",                                           # CSS media queries
        r"\bmin-width\s*:",                                    # min-width breakpoint
        r"\bmax-width\s*:",                                    # max-width breakpoint
        r"\bresponsive\b",                                     # responsive class/keyword
        r"\b(?:sm|md|lg|xl|2xl):",                             # Tailwind breakpoints
        r"\bcol-(?:xs|sm|md|lg|xl)-\d+",                       # Bootstrap grid
        r"\bGrid\b",                                           # Material UI Grid
        r"\buseMediaQuery\b",                                  # useMediaQuery hook
        r"\bbreakpoint\b",                                     # breakpoint mention
        r"\bviewport\b",                                       # viewport mention
    ]

    _FRONTEND_ALT_TEXT_PATTERNS = [
        r"<img\b[^>]*\balt\s*=",                              # <img alt="...">
        r"\balt\s*[:=]\s*['\"]",                               # alt="..." or alt: "..."
        r"\balt\s*[:=]\s*{",                                   # alt={variable} in JSX
        r"\bImage\b[^>]*\balt\b",                              # Next.js Image alt
        r"\bariaLabel\b",                                      # aria-label (related a11y)
        r"\baria-label\b",                                     # aria-label HTML
        r"\brole\s*=",                                         # role attribute
        r"\bAccessibilityLabel\b",                             # React Native
    ]

    def _check_fe_components(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for component-based architecture in frontend code"""
        found = []
        for pattern in self._FRONTEND_COMPONENT_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} component patterns"

    def _check_fe_state_management(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper state management in frontend code"""
        found = []
        for pattern in self._FRONTEND_STATE_MGMT_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} state management patterns"

    def _check_fe_props_validation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for props type validation (TypeScript interfaces or PropTypes)"""
        found = []
        for pattern in self._FRONTEND_PROPS_VALIDATION_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} props validation patterns"

    def _check_fe_routing(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for routing configuration"""
        found = []
        for pattern in self._FRONTEND_ROUTING_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} routing patterns"

    def _check_fe_responsive(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for responsive design patterns"""
        found = []
        for pattern in self._FRONTEND_RESPONSIVE_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} responsive design patterns"

    def _check_fe_alt_text(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for alt text on images and accessibility attributes"""
        found = []
        for pattern in self._FRONTEND_ALT_TEXT_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} alt text/accessibility patterns"

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

    # Testing Phase A check methods (Exp 30)

    def _check_test_structure(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for Arrange-Act-Assert or Given-When-Then test structure"""
        found = []
        for pattern in self._TEST_STRUCTURE_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} test structure patterns"

    def _check_test_assertions(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for test assertions with descriptive messages"""
        found = []
        for pattern in self._TEST_ASSERTIONS_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} assertion patterns"

    def _check_test_isolation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for test isolation via setup/teardown or fixtures"""
        found = []
        for pattern in self._TEST_ISOLATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} test isolation patterns"

    def _check_test_edge_cases(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for edge case testing (null, empty, boundary, negative)"""
        found = []
        for pattern in self._TEST_EDGE_CASES_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} edge case patterns"

    def _check_test_mocks(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper mock/stub usage for external dependencies"""
        found = []
        for pattern in self._TEST_MOCKS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} mock patterns"

    def _check_test_error_tests(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for error handling tests (pytest.raises, assertRaises, toThrow)"""
        found = []
        for pattern in self._TEST_ERROR_TESTS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} error test patterns"

    def _check_test_coverage(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for test coverage configuration or reporting"""
        found = []
        for pattern in self._TEST_COVERAGE_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} coverage patterns"

    def _check_test_e2e(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for E2E test coverage with proper tooling"""
        found = []
        for pattern in self._TEST_E2E_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} E2E test patterns"

    def _check_test_component(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for component unit testing with proper queries"""
        found = []
        for pattern in self._TEST_COMPONENT_TESTING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) > 0, f"Found {len(found)} component test patterns"

    # Config Phase A check methods (Exp 31)

    _CONFIG_REQUIRED_FIELDS_PATTERNS = [
        r"\brequired\s*:",                          # required: [field1, field2]
        r"\brequired_fields\b",                     # required_fields reference
        r"\bmust\s+(?:have|contain|include)\b",     # must have/contain/include
        r"\bmandatory\b",                           # mandatory fields
        r"\bname\s*:",                               # name: value (common required field)
        r"\bversion\s*:",                            # version: value
        r"\bhost\s*:",                               # host: value
        r"\bport\s*:",                               # port: value
        r"\bdatabase\s*:",                           # database: value
        r"\burl\s*:",                                # url: value
        r"\b(?:api_)?key\s*:",                       # key: or api_key:
        r"\benv(?:ironment)?\s*:",                   # env: or environment:
        r"\bconfig\s*\(",                            # config() call
        r"(?:schema|model)\s*=\s*\{",               # schema = { or model = {
    ]

    def _check_config_required_fields(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for required configuration fields presence"""
        found = []
        for pattern in self._CONFIG_REQUIRED_FIELDS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} required field indicators"

    _CONFIG_FIELD_TYPES_PATTERNS = [
        r"\btype\s*:\s*(?:string|integer|number|boolean|array|object)\b",  # type: string
        r"\btype\s*:\s*(?:str|int|float|bool|list|dict)\b",               # Python types
        r"\b(?:int|str|float|bool)\s*\(",                                  # int(), str() casts
        r"\bTrue\b|\bFalse\b",                                            # boolean literals
        r":\s*\d+\s*$",                                                    # numeric values
        r":\s*(?:true|false)\s*$",                                         # boolean values (YAML)
        r":\s*\[",                                                         # array values
        r":\s*\{",                                                         # object/dict values
        r":\s*['\"]",                                                      # string values
        r"\b(?:integer|string|boolean|number)\b",                          # type keywords
        r"\btyping\.\w+\b",                                               # typing.List, etc.
        r"\bOptional\[",                                                   # Optional[str]
        r"\bUnion\[",                                                      # Union[str, int]
        r"\w+\s*:\s*(?:str|int|float|bool)\b",                            # Python annotations: var: str
        r"=\s*(?:True|False)\b",                                          # assignment: = True
    ]

    def _check_config_field_types(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper field type definitions in configuration"""
        found = []
        for pattern in self._CONFIG_FIELD_TYPES_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} field type indicators"

    _CONFIG_COMMENTS_PATTERNS = [
        r"#\s+\w+",                                  # YAML/Python comments: # explanation
        r"//\s+\w+",                                 # JSON5/JS comments: // explanation
        r"/\*.*\*/",                                 # Block comments: /* ... */
        r"<!--.*-->",                                # XML/HTML comments
        r"#\s*(?:NOTE|TODO|FIXME|WARNING|IMPORTANT)", # Marker comments
        r"#\s*(?:default|override|required|optional)", # Config annotation comments
        r"\bdescription\s*:",                         # description: field (self-documenting)
        r"\bcomment\s*:",                             # comment: field
        r"\bhelp\s*:",                                # help: text
    ]

    def _check_config_comments(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for comments explaining non-obvious configuration settings"""
        found = []
        for pattern in self._CONFIG_COMMENTS_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} comment/documentation indicators"

    # Docs Phase A check methods (Exp 31)

    _DOCS_LINKS_PATTERNS = [
        r"\[.+?\]\(.+?\)",                           # [text](url) markdown links
        r"\[.+?\]\[.+?\]",                           # [text][ref] reference links
        r"https?://\S+",                             # raw URLs
        r"<a\s+href=",                               # HTML links
        r"\[.+?\]:\s+\S+",                           # [ref]: url reference definitions
    ]

    def _check_docs_links(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for valid link formats in documentation"""
        found = []
        for pattern in self._DOCS_LINKS_PATTERNS:
            matches = re.findall(pattern, artifact)
            if matches:
                found.extend(matches[:3])  # Cap at 3 per pattern
        return len(found) > 0, f"Found {len(found)} link(s)"

    _DOCS_HEADING_HIERARCHY_PATTERNS = [
        r"^#\s+\w+",                                 # H1 heading
        r"^##\s+\w+",                                # H2 heading
        r"^###\s+\w+",                               # H3 heading
    ]

    def _check_docs_structure(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper heading hierarchy in documentation"""
        h1_count = len(re.findall(r"^#\s+\w+", artifact, re.MULTILINE))
        h2_count = len(re.findall(r"^##\s+\w+", artifact, re.MULTILINE))
        h3_count = len(re.findall(r"^###\s+\w+", artifact, re.MULTILINE))

        has_h1 = h1_count > 0
        has_h2 = h2_count > 0

        if has_h1 and has_h2:
            return True, f"Good heading hierarchy: H1={h1_count}, H2={h2_count}, H3={h3_count}"
        elif has_h1:
            return False, f"Only H1 headings found ({h1_count}), missing H2 sections"
        elif has_h2:
            return False, f"Has H2 ({h2_count}) but missing H1 title"
        else:
            return False, "No heading hierarchy found"

    # Code-Gen Phase B check methods (Exp 32)

    _COMPLEXITY_PATTERNS = [
        r"(?:for|while)\s.*:\s*\n\s+.*(?:for|while)\s.*:\s*\n\s+.*(?:for|while)\s",  # 3+ nested loops
        r"if\s.*:\s*\n\s+.*if\s.*:\s*\n\s+.*if\s.*:\s*\n\s+.*if\s",  # 4+ nested ifs
        r"\.then\(.*\.then\(.*\.then\(",  # deeply chained promises
    ]

    _COMPLEXITY_GOOD_PATTERNS = [
        r"\bearly\s+return\b",                    # early return pattern
        r"\breturn\b",                             # return statements (guard clauses)
        r"\bbreak\b",                              # loop breaks
        r"\bcontinue\b",                           # loop continues
        r"\bextract\w*\(|_helper\(|_process\(",    # extracted helper functions
        r"def\s+\w+\(.*\).*:\s*$",                 # function definitions (decomposition)
    ]

    def _check_complexity(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for excessive code complexity (deeply nested loops/conditionals)"""
        # Check for bad complexity patterns
        bad_found = []
        for pattern in self._COMPLEXITY_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.DOTALL):
                bad_found.append(pattern)

        # Check for good complexity-reducing patterns
        good_found = []
        for pattern in self._COMPLEXITY_GOOD_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                good_found.append(pattern)

        if bad_found and not good_found:
            return False, f"Found {len(bad_found)} excessive complexity patterns without mitigation"
        return True, f"Complexity OK: {len(bad_found)} deep nesting, {len(good_found)} mitigation patterns"

    _RESOURCE_CLEANUP_PATTERNS = [
        r"\bwith\s+\w+",                           # with statement
        r"\bfinally\s*:",                           # finally block
        r"\b__exit__\b",                            # context manager protocol
        r"\b__del__\b",                             # destructor
        r"\bclose\(\)",                             # explicit close
        r"\bdispose\(\)",                           # dispose pattern
        r"\bshutdown\(\)",                          # shutdown
        r"\bcleanup\(\)",                           # cleanup function
        r"\batexit\.register\b",                    # atexit handler
        r"\.close\b",                               # .close method
        r"\btry\s*:.*\bfinally\s*:",                # try/finally
        r"\basync\s+with\b",                        # async with
        r"\bcontextmanager\b",                      # contextlib
        r"\bExitStack\b",                           # ExitStack
        r"\busing\s*\(",                            # C# using
    ]

    def _check_resource_cleanup(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper resource cleanup (with statements, finally blocks)"""
        found = []
        for pattern in self._RESOURCE_CLEANUP_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.DOTALL):
                found.append(pattern)
        return len(found) >= 1, f"Found {len(found)} resource cleanup patterns"

    _EXCEPTION_HANDLING_PATTERNS = [
        r"\bexcept\s+\w+",                         # except SpecificError
        r"\bexcept\s+\(",                           # except (Error1, Error2)
        r"\bcatch\s*\(\s*\w+",                      # catch(SpecificError e)
        r"\braise\s+\w+",                           # raise SpecificError
        r"\bthrow\s+new\s+\w+",                     # throw new Error
        r"class\s+\w*(?:Error|Exception)\b",        # custom exception classes
        r"\bValueError\b",                          # specific built-in exceptions
        r"\bTypeError\b",
        r"\bKeyError\b",
        r"\bIOError\b|\bOSError\b",
        r"\bRuntimeError\b",
        r"\bFileNotFoundError\b",
        r"\bPermissionError\b",
        r"\bConnectionError\b",
        r"\bTimeoutError\b",
        r"\bHTTPError\b|\bRequestException\b",
    ]

    _EXCEPTION_BAD_PATTERNS = [
        r"\bexcept\s*:",                            # bare except:
        r"\bexcept\s+Exception\s*:",                # overly broad except Exception:
        r"\bcatch\s*\(\s*\)",                       # empty catch
        r"\bpass\s*$",                              # except: pass (swallowing)
    ]

    def _check_exception_handling(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for specific exception handling (no bare except, proper types)"""
        good_found = []
        for pattern in self._EXCEPTION_HANDLING_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                good_found.append(pattern)

        bad_found = []
        for pattern in self._EXCEPTION_BAD_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                bad_found.append(pattern)

        if good_found and not bad_found:
            return True, f"Good exception handling: {len(good_found)} specific patterns"
        elif good_found and bad_found:
            return True, f"Mixed: {len(good_found)} specific, {len(bad_found)} broad patterns"
        elif bad_found:
            return False, f"Poor exception handling: {len(bad_found)} bare/broad except patterns"
        # No exception handling at all - neutral pass (may not need it)
        return True, "No exception handling patterns found (may not be needed)"

    _IMPORTS_PATTERNS = [
        r"^import\s+\w+",                           # import module
        r"^from\s+\w+\s+import\b",                  # from module import
        r"^const\s+\w+\s*=\s*require\(",            # const x = require()
        r"^import\s+\{",                             # import { x } from
        r"^import\s+\w+\s+from\b",                  # import x from
        r"^use\s+\w+",                               # Rust use
        r"^#include\s+[<\"]",                        # C/C++ include
        r"^using\s+\w+",                             # C# using
        r"^package\s+\w+",                           # Go package
    ]

    _IMPORTS_GOOD_PATTERNS = [
        r"(?:^import\s+\w+\n)+",                    # grouped stdlib imports
        r"(?:^from\s+\w+\.\w+\s+import\b.*\n)+",   # grouped project imports
        r"^#\s*(?:stdlib|third.?party|local|project)", # import section comments
        r"__all__\s*=\s*\[",                         # __all__ exports
        r"^import\s+\w+\s*(?:,\s*\w+)+$",          # import a, b, c (grouped)
    ]

    def _check_imports(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for organized and necessary imports"""
        found = []
        for pattern in self._IMPORTS_PATTERNS:
            matches = re.findall(pattern, artifact, re.MULTILINE)
            found.extend(matches)

        good_found = []
        for pattern in self._IMPORTS_GOOD_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                good_found.append(pattern)

        if not found:
            return True, "No imports found (may not be needed)"
        return len(found) >= 1, f"Found {len(found)} import(s), {len(good_found)} organization patterns"

    _CONTEXT_MANAGER_PATTERNS = [
        r"\bwith\s+open\(",                         # with open(file)
        r"\bwith\s+\w+\.connect\(",                 # with db.connect()
        r"\bwith\s+\w+\.cursor\(",                  # with conn.cursor()
        r"\bwith\s+\w+\.session\(",                 # with session()
        r"\bwith\s+\w+\.begin\(",                   # with transaction.begin()
        r"\bwith\s+lock\b|\bwith\s+\w+_lock\b",    # with lock / with mutex_lock
        r"\basync\s+with\b",                        # async with
        r"\b@contextmanager\b",                     # contextlib decorator
        r"\bExitStack\b",                           # contextlib.ExitStack
        r"\bcontextlib\b",                          # contextlib module
        r"\bwith\s+tempfile\.",                     # with tempfile.NamedTemporaryFile
        r"\bwith\s+closing\(",                      # with closing(resource)
        r"\bwith\s+\w+\(\)\s+as\b",                # generic with X() as y
        r"\bwith\s+\w+\s+as\b",                    # generic with x as y
    ]

    def _check_context_managers(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper use of context managers for resource management"""
        found = []
        for pattern in self._CONTEXT_MANAGER_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                found.append(pattern)
        return len(found) >= 1, f"Found {len(found)} context manager patterns"

    # --- Backend Phase B rules (Exp 33) ---

    _ASYNC_OPERATIONS_PATTERNS = [
        r"\basync\s+def\b",                             # async def function
        r"\bawait\b",                                   # await expression
        r"\basyncio\b",                                 # asyncio module
        r"\baiohttp\b",                                 # aiohttp library
        r"\bhttpx\.AsyncClient\b",                      # httpx async
        r"\basync\s+with\b",                            # async context manager
        r"\basync\s+for\b",                             # async iterator
        r"\basyncio\.gather\b",                         # parallel async
        r"\basyncio\.create_task\b",                    # task creation
        r"\bPromise\.all\b",                            # JS Promise.all
        r"\bPromise\.allSettled\b",                     # JS Promise.allSettled
        r"\basync\s+function\b",                        # JS async function
        r"\b\.then\s*\(",                               # Promise chaining
    ]

    _ASYNC_BAD_PATTERNS = [
        r"\btime\.sleep\b",                             # blocking sleep in async
        r"\brequests\.(get|post|put|delete|patch)\b",   # blocking requests in async
    ]

    def _check_async_operations(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for async/await usage in I/O operations"""
        found = []
        for pattern in self._ASYNC_OPERATIONS_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                found.append(pattern)

        bad_found = []
        for pattern in self._ASYNC_BAD_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                bad_found.append(pattern)

        if bad_found and not found:
            return False, f"Found {len(bad_found)} blocking patterns but no async patterns"
        return len(found) >= 2, f"Found {len(found)} async patterns, {len(bad_found)} blocking patterns"

    _HTTP_STATUS_CODE_PATTERNS = [
        r"\b(200|201|204|301|302|304)\b",               # success/redirect codes
        r"\b(400|401|403|404|405|409|422|429)\b",       # client error codes
        r"\b(500|502|503|504)\b",                       # server error codes
        r"\bstatus[_\s]*code\b",                        # status_code reference
        r"\bHTTP_\d{3}_\w+\b",                            # HTTP_200_OK style
        r"\bHttpStatus\.\w+\b",                         # HttpStatus.OK
        r"\bStatusCode\.\w+\b",                         # StatusCode enum
        r"\bstatus\s*[:=]\s*\d{3}\b",                  # status: 200 / status = 200
        r"\b(OK|CREATED|NO_CONTENT|BAD_REQUEST|UNAUTHORIZED|FORBIDDEN|NOT_FOUND)\b",  # named constants
    ]

    def _check_http_status_codes(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper HTTP status code usage"""
        found = []
        for pattern in self._HTTP_STATUS_CODE_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} HTTP status code patterns"

    _CONTENT_NEGOTIATION_PATTERNS = [
        r"\bapplication/json\b",                        # JSON content type
        r"\btext/html\b",                               # HTML content type
        r"\btext/plain\b",                              # plain text
        r"\bapplication/xml\b",                         # XML content type
        r"\bContent-Type\b",                            # Content-Type header
        r"\bAccept\b.*header",                          # Accept header reference
        r"\bcontent_type\b",                            # content_type parameter
        r"\bmedia_type\b",                              # media type parameter
        r"\bproduces\b",                                # produces annotation
        r"\bconsumes\b",                                # consumes annotation
        r"\b406\b",                                     # Not Acceptable status
        r"\bresponse\.headers\b",                       # response headers
    ]

    def _check_content_negotiation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for content negotiation with Accept/Content-Type headers"""
        found = []
        for pattern in self._CONTENT_NEGOTIATION_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} content negotiation patterns"

    _RESOURCE_NAMING_PATTERNS = [
        r"[\"']/\w+s\b",                               # plural resource paths /users, /orders
        r"\broute\s*\(\s*[\"']/",                      # route("/path")
        r"@(Get|Post|Put|Delete|Patch)\s*\(",             # NestJS/Spring decorators
        r"\brouter\.(get|post|put|delete|patch)\s*\(", # Express router methods
        r"\bapp\.(get|post|put|delete|patch)\s*\(",    # Flask/Express app methods
        r"[\"']/api/",                                  # /api/ prefix
        r"[\"']/v\d+/",                                # versioned paths /v1/
        r"\b@app\.(get|post|put|delete)\s*\(",         # FastAPI decorators
        r"\bpath\s*\(\s*[\"']/",                       # Django path()
        r"\burl\s*\(\s*[\"']",                         # Django url()
    ]

    _RESOURCE_NAMING_GOOD_PATTERNS = [
        r"[\"']/\w+s/\{?\w+\}?[\"']",                 # /users/{id} - parameterized
        r"[\"']/\w+s/:\w+[\"']",                       # /users/:id - Express style
        r"[\"']/\w+s/<\w+>[\"']",                      # /users/<id> - Flask style
    ]

    def _check_resource_naming(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for RESTful resource naming conventions"""
        found = []
        for pattern in self._RESOURCE_NAMING_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                found.append(pattern)

        good_found = []
        for pattern in self._RESOURCE_NAMING_GOOD_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                good_found.append(pattern)

        return len(found) >= 2, f"Found {len(found)} resource patterns, {len(good_found)} parameterized patterns"

    _SECURITY_HEADERS_PATTERNS = [
        r"\bX-Content-Type-Options\b",                  # nosniff header
        r"\bX-Frame-Options\b",                         # clickjacking protection
        r"\bContent-Security-Policy\b",                 # CSP header
        r"\bStrict-Transport-Security\b",               # HSTS header
        r"\bX-XSS-Protection\b",                        # XSS protection header
        r"\bReferrer-Policy\b",                         # referrer policy
        r"\bPermissions-Policy\b",                      # permissions policy
        r"\bhelmet\b",                                  # helmet.js middleware
        r"\bsecure_headers\b",                          # secure_headers middleware
        r"\bnosniff\b",                                 # nosniff value
        r"\bDENY\b|\bSAMEORIGIN\b",                   # X-Frame-Options values
        r"\bcontentSecurityPolicy\b",                   # helmet CSP camelCase
        r"\bhsts\b",                                    # helmet HSTS shorthand
        r"\bframeguard\b",                              # helmet frameguard
    ]

    def _check_security_headers(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for security headers in responses"""
        found = []
        for pattern in self._SECURITY_HEADERS_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} security header patterns"

    # Backend Phase B remaining rules (Exp 35)

    _DOMAIN_ERRORS_PATTERNS = [
        r"\bclass\s+\w+(Error|Exception)\b",              # custom error classes
        r"\b(DomainError|BusinessError|ApplicationError)\b",  # domain error base
        r"\b(NotFound|AlreadyExists|Forbidden|Conflict)\w*\b",  # domain-specific errors
        r"\b(InsufficientFunds|InvalidState|Unauthorized)\b",  # business rule errors
        r"\braise\s+\w+(Error|Exception)\b",               # raising custom errors
        r"\bthrow\s+new\s+\w+(Error|Exception)\b",        # JS/TS throw custom
        r"\b(400|422)\b.*\b(validation|invalid|malformed)\b",  # validation status
        r"\b(domain|business)\s*(error|exception)\b",      # domain error references
        r"\berror_code\b|\berrorCode\b",                   # error code field
        r"\b@exception_handler\b|\berrorHandler\b",        # error handler decorators
    ]

    def _check_domain_errors(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for domain error separation from validation errors"""
        found = []
        for pattern in self._DOMAIN_ERRORS_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} domain error patterns"

    _ERROR_CONSISTENCY_PATTERNS = [
        r"\berror\s*[:{]\s*[{(]?\s*(code|message|details)\b",  # error: {code, message}
        r"\brequest_id\b|\brequestId\b|\brequest[-_]?id\b",    # request ID in errors
        r"\berror_code\b|\berrorCode\b",                        # error code field
        r"\b(error|exception)\s*(middleware|handler|filter)\b", # error middleware
        r"\berror\s*schema\b|\bErrorSchema\b|\bErrorResponse\b",  # error schema
        r"\bformatError\b|\bformat_error\b",                    # error formatter
        r"\b(error|err)\s*\.\s*(code|message|status)\b",       # error.code, error.message
        r"\bconsistent\s*error\b|\berror\s*format\b",           # error format references
        r"\b@ExceptionHandler\b|\b@exception_handler\b",        # exception handler decorator
    ]

    def _check_error_consistency(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for consistent error response format"""
        found = []
        for pattern in self._ERROR_CONSISTENCY_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} error consistency patterns"

    _STACK_TRACE_SANITIZATION_PATTERNS = [
        r"\bNODE_ENV\b|\bDJANGO_SETTINGS\b|\bFLASK_ENV\b",   # environment checks
        r"\bproduction\b.*\b(stack|trace|debug)\b",            # production stack handling
        r"\b(stack|trace|traceback)\b.*\b(hide|mask|remove|sanitize)\b",  # sanitize traces
        r"\bDEBUG\s*[=:]\s*(False|false|0)\b",                # DEBUG = False
        r"\bshow_error_details\b|\berror_detail\b",            # error detail config
        r"\bgeneric\s*(error|message)\b",                      # generic error message
        r"\binternal\s*server\s*error\b",                      # generic 500 message
        r"\brequest_id\b.*\b(correlat|track|trace)\b",         # request ID for correlation
        r"\b(mask|filter|strip)\s*(stack|trace|error)\b",      # strip traces
        r"\bexc_info\s*=\s*(True|true)\b",                     # server-side logging with trace
    ]

    def _check_stack_trace_sanitization(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for stack trace sanitization in production"""
        found = []
        for pattern in self._STACK_TRACE_SANITIZATION_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} stack trace sanitization patterns"

    _API_VERSIONING_PATTERNS = [
        r"[\"']/v\d+/",                                        # /v1/ URL versioning
        r"\bapi[-_]?version\b",                                 # api_version parameter
        r"\bAPI-Version\b|\bX-API-Version\b",                  # version header
        r"[\"']version[\"']\s*:",                               # 'version': config key
        r"\b@Version\b|\b@ApiVersion\b",                       # version decorator
        r"[Vv]ersioning",                                       # versioning reference
        r"\bdeprecated\b|\bdeprecation\b",                     # deprecation handling
        r"\brouter.*v\d\b|\bv\d.*router\b",                   # versioned router
        r"\bprefix\s*=\s*[\"']/v\d",                           # prefix='/v1'
        r"UrlPathVersioning|HeaderVersioning|QueryParameterVersioning",  # DRF versioning classes
    ]

    def _check_api_versioning(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for API versioning implementation"""
        found = []
        for pattern in self._API_VERSIONING_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} API versioning patterns"

    _SCHEMA_VALIDATION_PATTERNS = [
        r"\b(Zod|Joi|Yup|Ajv|jsonschema)\b",                  # validation libraries
        r"\bpydantic\b",                                        # Pydantic import
        r"\bBaseModel\b",                                       # Pydantic BaseModel
        r"\b(class-validator|class-transformer)\b",            # class-validator
        r"@Is(String|Number|Email|NotEmpty|Int|Boolean)\b",   # class-validator decorators
        r"\w+Dto\b|\w+Schema\b",                               # DTO/Schema class naming
        r"\b(schema|Schema)\s*\(\s*\{",                        # schema definition
        r"\b(validate|parse|safeParse)\s*\(",                      # validate/parse call
        r"\b(body|query|params)\s*\.\s*validate\b",           # request.body.validate
        r"\b@Body\b|\b@Query\b|\b@Param\b",                   # NestJS decorators
        r"\bOpenAPI\b|\bSwagger\b|\bopenapi\b",                # OpenAPI/Swagger
        r"\bJSON\s*Schema\b|\bjsonSchema\b",                   # JSON Schema
        r"\b(request|req)\s*\.\s*validated\b",                 # validated request data
        r"[Ss]erializer",                                       # DRF serializer
    ]

    def _check_schema_validation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for request/response schema validation"""
        found = []
        for pattern in self._SCHEMA_VALIDATION_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} schema validation patterns"

    _IDEMPOTENCY_PATTERNS = [
        r"\bIdempotency[-_]?Key\b",                            # Idempotency-Key header
        r"\bidempoten\w+\b",                                    # idempotent/idempotency
        r"\bPUT\b.*\b(update|replace)\b",                      # PUT is idempotent
        r"\bDELETE\b.*\b(remove|destroy)\b",                  # DELETE is idempotent
        r"\bcached\s*result\b|\bduplicate\s*request\b",        # cached/duplicate handling
        r"\b(retry|retries)\b.*\b(safe|idempoten)\b",         # safe retries
        r"\bupsert\b",                                          # upsert operation
        r"\bIF\s+NOT\s+EXISTS\b",                                # CREATE IF NOT EXISTS
        r"\bWHERE\s+NOT\s+EXISTS\b",                              # INSERT WHERE NOT EXISTS
        r"\bON\s+CONFLICT\b|\bon_conflict\b",                 # PostgreSQL upsert
        r"\bDO\s+UPDATE\b|\bDO\s+NOTHING\b",                  # PostgreSQL conflict action
        r"\b409\b.*\b(conflict|already)\b",                    # 409 Conflict status
        r"\bINSERT\s+OR\s+(REPLACE|IGNORE)\b",                # SQLite idempotency
    ]

    def _check_idempotency(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for idempotent operations"""
        found = []
        for pattern in self._IDEMPOTENCY_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE | re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} idempotency patterns"

    # Frontend Phase B pattern lists and check methods (Exp 36)

    _FE_LAZY_LOADING_PATTERNS = [
        r"\bReact\.lazy\s*\(",                          # React.lazy(() => import(...))
        r"\blazy\s*\(\s*\(\s*\)\s*=>",                 # lazy(() =>
        r"\bimport\s*\(",                               # dynamic import()
        r"<Suspense\b",                                 # <Suspense fallback=...>
        r"\bfallback\s*=",                              # fallback={<Loading />}
        r"\bloading\s*=\s*['\"]lazy['\"]",              # loading="lazy" on images
        r"<img\b[^>]*\bloading\s*=",                    # <img loading="lazy"
        r"\bIntersectionObserver\b",                    # IntersectionObserver for lazy load
        r"\buseInView\b|\binView\b",                    # react-intersection-observer
        r"\bloadable\b|\bLoadable\b",                   # @loadable-components
        r"\bcode\s*splitting\b|\bcode-splitting\b",     # code splitting mention
        r"\bchunk\b.*\bimport\b",                       # chunk import references
    ]

    def _check_fe_lazy_loading(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for lazy loading implementation"""
        found = []
        for pattern in self._FE_LAZY_LOADING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} lazy loading patterns"

    _FE_SEMANTIC_HTML_PATTERNS = [
        r"<header\b",                                   # <header>
        r"<nav\b",                                      # <nav>
        r"<main\b",                                     # <main>
        r"<footer\b",                                   # <footer>
        r"<section\b",                                  # <section>
        r"<article\b",                                  # <article>
        r"<aside\b",                                    # <aside>
        r"<figure\b",                                   # <figure>
        r"<figcaption\b",                               # <figcaption>
        r"<details\b",                                  # <details>
        r"<summary\b",                                  # <summary>
        r"<time\b",                                     # <time>
        r"<mark\b",                                     # <mark>
        r"\brole\s*=",                                  # role="navigation" etc.
        r"\baria-\w+\s*=",                              # aria-label, aria-hidden etc.
    ]

    def _check_fe_semantic_html(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for semantic HTML elements usage"""
        found = []
        for pattern in self._FE_SEMANTIC_HTML_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} semantic HTML patterns"

    _FE_CSS_ORGANIZATION_PATTERNS = [
        r"\bmodule\.css\b|\bmodule\.scss\b",            # CSS Modules
        r"\bstyled\s*\.\w+",                            # styled-components: styled.div
        r"\bstyled\s*\(",                               # styled(Component)
        r"\bcss\s*`",                                   # css`` tagged template
        r"\b(?:className|class)\s*=\s*\{?\s*styles\.",  # styles.container
        r"@apply\b",                                    # Tailwind @apply
        r"\btailwind\b",                                # Tailwind mention
        r"\b(?:makeStyles|createStyles|useStyles)\b",   # MUI styles
        r"\bsx\s*=\s*\{",                               # MUI sx prop
        r"\bBEM\b|__\w+--\w+",                          # BEM naming: block__element--modifier
        r"\b:global\b|\b:local\b",                      # CSS Modules :global/:local
        r"\.module\.(css|scss|less)\b",                 # import styles from '*.module.css'
        r"\bemotion\b|\b@emotion\b",                    # Emotion CSS-in-JS
    ]

    def _check_fe_css_organization(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for organized CSS approach (modules, CSS-in-JS, utility-first)"""
        found = []
        for pattern in self._FE_CSS_ORGANIZATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} CSS organization patterns"

    _FE_HOOKS_OPTIMIZATION_PATTERNS = [
        r"\buseMemo\s*\(",                              # useMemo(() => ...)
        r"\buseCallback\s*\(",                          # useCallback(() => ...)
        r"\bReact\.memo\s*\(",                          # React.memo(Component)
        r"\bmemo\s*\(\s*(?:function|\w+)\b",            # memo(function) or memo(Comp)
        r"\buseRef\s*\(",                               # useRef for stable references
        r"\buseTransition\s*\(",                        # useTransition for concurrent
        r"\buseDeferredValue\s*\(",                     # useDeferredValue
        r"\[\s*\]\s*\)\s*;?\s*$",                       # empty dependency array []
        r"\b(?:deps|dependencies)\b.*\[",               # explicit dependency arrays
        r"\bReact\.lazy\b",                             # React.lazy for code splitting
        r"\bshallowEqual\b",                            # shallowEqual comparison
        r"\bareEqual\b|\bisEqual\b",                    # custom equality checks
    ]

    def _check_fe_hooks_optimization(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for React hooks optimization (useMemo, useCallback, memo)"""
        found = []
        for pattern in self._FE_HOOKS_OPTIMIZATION_PATTERNS:
            if re.search(pattern, artifact, re.MULTILINE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} hooks optimization patterns"

    _FE_ERROR_BOUNDARIES_PATTERNS = [
        r"\bErrorBoundary\b",                           # ErrorBoundary component
        r"\bcomponentDidCatch\b",                       # componentDidCatch lifecycle
        r"\bgetDerivedStateFromError\b",                # getDerivedStateFromError
        r"\berror\s*boundary\b",                        # error boundary mention
        r"\bfallback\s*(?:UI|Component|Render)\b",     # fallbackUI/Component/Render
        r"\bwithErrorBoundary\b",                       # HOC wrapper
        r"\buseErrorBoundary\b",                        # react-error-boundary hook
        r"\bfallbackRender\s*=",                        # fallbackRender prop
        r"\bFallbackComponent\s*=",                     # FallbackComponent prop
        r"\bonError\s*=",                               # onError prop
        r"\bonReset\s*=",                               # onReset prop for retry
        r"\bresetErrorBoundary\b",                      # reset function
    ]

    def _check_fe_error_boundaries(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for error boundary implementation"""
        found = []
        for pattern in self._FE_ERROR_BOUNDARIES_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} error boundary patterns"

    _FE_COMPONENT_COMPOSITION_PATTERNS = [
        r"\bchildren\b",                                # children prop
        r"\{?\s*children\s*\}?",                        # {children} render
        r"\brender\s*(?:Props?|prop)\b",                # render props pattern
        r"\brender\s*=\s*\{",                           # render={fn} prop
        r"\bcompound\s*component\b",                    # compound component mention
        r"\bContext\.Provider\b",                        # Context.Provider
        r"\bcreateContext\b",                            # createContext
        r"\buseContext\s*\(",                            # useContext hook
        r"\bforwardRef\s*\(",                            # forwardRef
        r"\bReact\.forwardRef\b",                       # React.forwardRef
        r"\bslots?\s*(?:=|\:)",                         # slots pattern (Vue/Svelte/Radix)
        r"\bas\s*=\s*\{",                               # polymorphic as prop
        r"\bcompose\s*\(",                              # compose(HOC1, HOC2)
    ]

    def _check_fe_component_composition(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for component composition patterns (children, render props, compound)"""
        found = []
        for pattern in self._FE_COMPONENT_COMPOSITION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} component composition patterns"

    _FE_API_INTEGRATION_PATTERNS = [
        r"\buseQuery\s*\(",                             # React Query / TanStack Query
        r"\buseMutation\s*\(",                          # React Query mutations
        r"\buseSWR\s*\(",                               # SWR data fetching
        r"\buseRTK\w*Query\b",                          # RTK Query hooks
        r"\bcreateApi\s*\(",                            # RTK Query createApi
        r"\bfetch\s*\(",                                # fetch API
        r"\baxios\b",                                   # axios library
        r"\bisLoading\b|\bisFetching\b",                # loading state handling
        r"\bisError\b|\berror\s*&&",                    # error state handling
        r"\bdata\s*&&",                                 # data guard rendering
        r"\b(?:onSuccess|onError|onSettled)\b",         # query callbacks
        r"\bretry\b.*\b(?:count|times|logic)\b",        # retry logic
        r"\brefetch\b|\binvalidateQueries\b",           # refetch/invalidate
    ]

    def _check_fe_api_integration(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper API integration with loading/error/success states"""
        found = []
        for pattern in self._FE_API_INTEGRATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} API integration patterns"

    _FE_FORM_VALIDATION_PATTERNS = [
        r"\buseForm\s*\(",                              # react-hook-form
        r"\bregister\s*\(\s*['\"]",                     # register('fieldName')
        r"\bhandleSubmit\s*\(",                         # handleSubmit(onSubmit)
        r"\bformState\b|\berrors\.\w+",                 # form errors
        r"\bFormik\b|\buseFormik\s*\(",                 # Formik
        r"\bvalidation[Ss]chema\b",                     # validationSchema prop
        r"\bYup\.\w+\b|\bz\.\w+\b",                    # Yup.string() or z.string()
        r"\b(?:required|minLength|maxLength|pattern)\s*:", # validation rules
        r"\bonBlur\b.*\bvalidat",                       # validate on blur
        r"\bonSubmit\b",                                # onSubmit handler
        r"\binline\s*error\b|\berror\s*message\b",      # inline errors
        r"\bsetError\b|\bclearErrors\b",                # programmatic error control
        r"\bcontrolled\s*(?:input|component)\b",        # controlled inputs mention
    ]

    def _check_fe_form_validation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for client-side form validation implementation"""
        found = []
        for pattern in self._FE_FORM_VALIDATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} form validation patterns"

    _FE_ENVIRONMENT_CONFIG_PATTERNS = [
        r"\bprocess\.env\.\w+",                         # process.env.VAR
        r"\bimport\.meta\.env\.\w+",                    # Vite import.meta.env.VAR
        r"\bREACT_APP_\w+",                             # CRA env prefix
        r"\bVITE_\w+",                                  # Vite env prefix
        r"\bNEXT_PUBLIC_\w+",                           # Next.js env prefix
        r"\bNUXT_\w+|\bRUNTIME_CONFIG\b",              # Nuxt env
        r"\.env\b|\.env\.local\b|\.env\.production\b",  # .env files
        r"\benv\.example\b|\.env\.example\b",           # .env.example
        r"\benvSchema\b|\benv\.parse\b",                # env validation
        r"\b(?:config|getConfig)\s*\(\s*\)",            # config() getter
        r"\b(?:API_URL|BASE_URL|API_BASE)\b",           # common env var names
        r"\benvironmentVariable\b|\benvVar\b",          # env variable references
    ]

    def _check_fe_environment_config(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for environment-based configuration"""
        found = []
        for pattern in self._FE_ENVIRONMENT_CONFIG_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} environment config patterns"

    _FE_STATE_PERSISTENCE_PATTERNS = [
        r"\blocalStorage\.\w+",                         # localStorage.getItem/setItem
        r"\bsessionStorage\.\w+",                       # sessionStorage.getItem/setItem
        r"\btry\s*\{[^}]*(?:localStorage|sessionStorage)", # try/catch around storage
        r"\bJSON\.parse\s*\(",                          # JSON.parse for stored data
        r"\bJSON\.stringify\s*\(",                      # JSON.stringify for storing
        r"\bQuotaExceededError\b",                      # storage quota handling
        r"\bStorageEvent\b|\bstorage\s+event\b",       # storage event listening
        r"\buseLocalStorage\b|\busePersist\b",          # custom storage hooks
        r"\bpersist\b.*\bstate\b",                      # persist state mention
        r"\brehydrat[ei]\b",                            # rehydrate state
        r"\bIndexedDB\b|\bindexedDB\b",                 # IndexedDB usage
        r"\bidb\b|\bDexie\b|\blocalForage\b",          # IndexedDB libraries
    ]

    def _check_fe_state_persistence(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for proper state persistence with error handling"""
        found = []
        for pattern in self._FE_STATE_PERSISTENCE_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} state persistence patterns"

    # Exp 39: Backend GraphQL Phase B patterns and check methods

    _GQL_N_PLUS1_PATTERNS = [
        r"\bDataLoader\b",                                    # DataLoader (JS/Python)
        r"\bdataloader\b",                                    # dataloader package
        r"\bbatch[_\s\-]?(?:load|fetch|resolve|get)\w*\b",   # batch loading/fetching
        r"\bloader\s*\.\s*load\b",                            # loader.load()
        r"\bloader\s*\.\s*loadMany\b",                        # loader.loadMany()
        r"\bn\s*\+\s*1\b",                                    # N+1 mention
        r"\bbatch\s+(?:query|queries|request)\b",             # batch queries
        r"\bper[_\s\-]?request\s+(?:cache|caching|batch)\b",  # per-request cache
        r"\bbatch\s+(?:size|limit|threshold)\b",              # batch configuration
        r"\bquery\s+(?:count|batching|coalescing)\b",         # query batching
        r"\b(?:eager|join)[_\s\-]+(?:load|fetch)\w*\b",         # eager loading / join fetching / eager_load
        r"\bprefetch[_\s\-]?related\b",                       # Django prefetch_related
    ]

    def _check_gql_n_plus1(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL N+1 query prevention patterns"""
        found = []
        for pattern in self._GQL_N_PLUS1_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} N+1 prevention patterns"

    _GQL_ERROR_HANDLING_PATTERNS = [
        r"\bformatError\b",                                    # Apollo formatError hook
        r"\berror\s+(?:format|handler|middleware|plugin)\b",   # error formatting
        r"\bmask\w*\s+(?:error|internal|stack)\b",             # mask errors
        r"\bextensions\s*\.\s*code\b",                         # extensions.code
        r"\bGRAPHQL_VALIDATION_FAILED\b",                      # standard error codes
        r"\bBAD_USER_INPUT\b",                                 # Apollo error code
        r"\bApolloError\b",                                    # ApolloError class
        r"\bGraphQLError\b",                                   # GraphQLError class
        r"\b(?:error|exception)\s+(?:class|type|code)\b",      # error classification
        r"\berror\s*\.\s*(?:locations|path|message)\b",        # error fields
        r"\buser[_\s\-]?facing\s+error\b",                    # user-facing errors
        r"\bsanitize\w*\s+error\b",                            # sanitize errors
    ]

    def _check_gql_error_handling(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for structured GraphQL error handling patterns"""
        found = []
        for pattern in self._GQL_ERROR_HANDLING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} GraphQL error handling patterns"

    _GQL_PAGINATION_PATTERNS = [
        r"\bconnection\s+(?:spec|type|pattern)\b",            # connection spec/type
        r"\b(?:edges|nodes|pageInfo)\b",                       # Relay connection fields
        r"\bcursor[_\s\-]?based\s+pagination\b",              # cursor-based pagination
        r"\b(?:first|last|after|before)\s*[=:]\b",            # Relay pagination args
        r"\bhasNextPage\b",                                    # pageInfo field
        r"\bhasPreviousPage\b",                                # pageInfo field
        r"\bendCursor\b",                                      # pageInfo field
        r"\bstartCursor\b",                                    # pageInfo field
        r"\brelay\s+(?:connection|spec|cursor)\b",             # Relay spec
        r"\boffset[_\s\-]?(?:based\s+)?pagination\b",         # offset-based pagination
        r"\bpage[_\s\-]?(?:size|number|info)\b",               # pagination params
        r"\btotal[_\s\-]?count\b",                             # totalCount field
    ]

    def _check_gql_pagination(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL pagination patterns (connection-based)"""
        found = []
        for pattern in self._GQL_PAGINATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} GraphQL pagination patterns"

    _GQL_SUBSCRIPTIONS_AUTH_PATTERNS = [
        r"\bsubscription\s+(?:auth\w*|security|guard)\b",     # subscription auth
        r"\bwebsocket\s+(?:auth\w*|token|connect)\b",         # websocket auth
        r"\bconnection[_\s\-]?(?:init|params|context)\b",     # connection init
        r"\bonConnect\b",                                       # onConnect hook
        r"\bconnectionParams\b",                                # connectionParams
        r"\bws\s+(?:auth\w*|token|handshake)\b",               # ws authentication
        r"\b(?:auth\w*|verify)\s+(?:on\s+)?(?:connection|websocket|ws)\b",  # auth on connection
        r"\b(?:token|jwt)\s+(?:expir\w*|valid\w*|refresh)\b.*(?:subscription|websocket|ws)\b",  # token validation for subscriptions
        r"\bclose\s+(?:connection|socket)\s+(?:on\s+)?(?:auth|unauth)\b",  # close on auth failure
        r"\bsubscription\s+(?:middleware|guard|filter)\b",     # subscription guard
    ]

    def _check_gql_subscriptions_auth(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for secure GraphQL subscriptions authentication patterns"""
        found = []
        for pattern in self._GQL_SUBSCRIPTIONS_AUTH_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} GraphQL subscription auth patterns"

    _GQL_DESCRIPTION_DOCS_PATTERNS = [
        r'"""\s*\w',                                           # Python triple-quote docstring on type/field
        r"\bdescription\s*[:=]\s*['\"]",                       # description: "..." or description = "..."
        r"@deprecated\b",                                      # @deprecated directive
        r"\breason\s*[:=]\s*['\"]",                            # deprecation reason
        r"#\s+\w+.*(?:type|field|argument|input)\b",           # schema comments
        r"\bschema\s+(?:documentation|description|comment)\b", # schema documentation
        r"\bdocument\w*\s+(?:type|field|schema|argument)\b",   # document types/fields
        r"\b(?:field|argument|type)\s+description\b",          # field/argument description
        r"\bAPI\s+(?:documentation|reference|docs)\b",         # API docs
        r"\bGraphQL\s+(?:docs|documentation|schema\s+docs)\b", # GraphQL docs
    ]

    def _check_gql_description_docs(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL schema documentation patterns"""
        found = []
        for pattern in self._GQL_DESCRIPTION_DOCS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} GraphQL documentation patterns"

    _GQL_FEDERATION_PATTERNS = [
        r"@key\b",                                             # @key directive
        r"@extends\b",                                         # @extends directive
        r"@external\b",                                        # @external directive
        r"@provides\b",                                        # @provides directive
        r"@requires\b",                                        # @requires directive
        r"\b__resolveReference\b",                             # __resolveReference resolver
        r"\bfederat\w+\b",                                     # federation / federated
        r"\bsubgraph\b",                                       # subgraph
        r"\bsupergraph\b",                                     # supergraph
        r"\bentity\s+(?:type|resolution|resolver)\b",          # entity type/resolution
        r"\bApolloGateway\b",                                  # Apollo Gateway
        r"\b(?:service|schema)\s+(?:composit|stitch)\w*\b",   # schema composition/stitching
    ]

    def _check_gql_federation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL Federation consistency patterns"""
        found = []
        for pattern in self._GQL_FEDERATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} GraphQL federation patterns"

    _GQL_QUERY_COST_PATTERNS = [
        r"\b(?:query|field)\s+cost\b",                         # query/field cost
        r"\bcost\s+(?:weight|value|score|limit)\b",            # cost weight/limit
        r"\bcost\s*[=:]\s*\d+",                                # cost = N or cost: N
        r"@cost\b",                                            # @cost directive
        r"\bcost\s+(?:analysis|calculat|estimat)\w*\b",        # cost analysis
        r"\bmax[_\s\-]?cost\b",                                # maxCost
        r"\bfield\s+(?:weight|complexity|cost)\s*[=:]\b",      # field weight: N
        r"\bcost\s+(?:in\s+)?(?:response|extensions)\b",       # cost in response/extensions
        r"\bquery\s+(?:budget|quota|limit)\s+(?:cost|complex)\b",  # query budget/quota
        r"\b(?:high|expensive)[_\s\-]?cost\s+(?:query|quer|field)\b",  # expensive query logging
    ]

    def _check_gql_query_cost(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for GraphQL query cost analysis patterns"""
        found = []
        for pattern in self._GQL_QUERY_COST_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} GraphQL query cost patterns"

    # ── Database Phase B check methods (Exp 41) ──

    _DB_DENORMALIZATION_PATTERNS = [
        r"\bdenormaliz\w*\b",                                    # denormalize, denormalization
        r"\bmaterialized\s+view\b",                              # materialized view
        r"\bcreate\s+(?:materialized\s+)?view\b",                # CREATE VIEW / MATERIALIZED VIEW
        r"\bredundant\s+(?:column|field|data)\b",                # redundant column for perf
        r"\bcache[d_\s]?table\b",                                # cached/cache table
        r"\bread[_\s\-]?(?:replica|model|optimiz)\w*\b",        # read replica/model/optimized
        r"\bsummary[_\s]?table\b",                               # summary table
        r"\baggregate[d_\s]?(?:table|view|column)\b",            # aggregated table
        r"\bpre[_\s\-]?comput\w*\b",                             # precomputed
        r"\bcqrs\b",                                             # CQRS pattern
    ]

    def _check_db_denormalization(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for denormalization patterns"""
        found = []
        for pattern in self._DB_DENORMALIZATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} denormalization patterns"

    _DB_MIGRATIONS_PATTERNS = [
        r"\bmigrat\w+\b",                                       # migration, migrations, migrate
        r"\balembic\b",                                          # Alembic (Python)
        r"\bknex\s*\.\s*(?:schema|migrate)\b",                  # Knex.js
        r"\b(?:up|down)\s*\(\s*\)\b",                            # up()/down() methods
        r"\bdef\s+(?:upgrade|downgrade)\b",                      # def upgrade/downgrade
        r"\breversible\b",                                       # reversible migration
        r"\brollback\b",                                         # rollback support
        r"\balter\s+table\b",                                    # ALTER TABLE
        r"\badd[_\s]?column\b",                                  # add_column
        r"\bschema\s*\.\s*(?:create|drop|alter)\b",              # schema.create/drop/alter
        r"\bmigration[_\s]?(?:file|version|order)\b",            # migration file/version
    ]

    def _check_db_migrations(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for migration patterns"""
        found = []
        for pattern in self._DB_MIGRATIONS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} migration patterns"

    _DB_CONSTRAINTS_PATTERNS = [
        r"\bconstraint\s+\w+\b",                                # CONSTRAINT constraint_name
        r"\bcheck\s*\(",                                         # CHECK (...)
        r"\badd\s+constraint\b",                                 # ADD CONSTRAINT
        r"\bnamed?\s+constraint\b",                              # named constraint
        r"\bck_\w+\b",                                           # ck_ prefix convention
        r"\bchk_\w+\b",                                          # chk_ prefix convention
        r"\bconstraint[_\s]?name\b",                             # constraint_name
        r"\bvalidat\w+\s+(?:rule|constraint|check)\b",           # validation rule/constraint
        r"\bdomain\s+constraint\b",                              # domain constraint
        r"\bexclusion\s+constraint\b",                           # exclusion constraint (PG)
    ]

    def _check_db_constraints(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for named constraint patterns"""
        found = []
        for pattern in self._DB_CONSTRAINTS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} constraint patterns"

    _DB_TRANSACTION_PATTERNS = [
        r"\bbegin\s*(?:transaction|work)?\b",                    # BEGIN / BEGIN TRANSACTION
        r"\bcommit\b",                                           # COMMIT
        r"\brollback\b",                                         # ROLLBACK
        r"\btransaction\b",                                      # transaction
        r"\bsavepoint\b",                                        # SAVEPOINT
        r"\batomic\b",                                           # atomic (Django)
        r"\b(?:with|@)\s*(?:transaction|atomic)\b",              # with transaction / @atomic
        r"\bsession\s*\.\s*(?:begin|commit|rollback)\b",        # session.begin/commit/rollback
        r"\bconn(?:ection)?\s*\.\s*(?:begin|commit|rollback)\b", # conn.begin/commit
        r"\btry\b.*\bcommit\b|\bcommit\b.*\bexcept\b",          # try...commit...except pattern
    ]

    def _check_db_transaction_boundaries(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for transaction boundary patterns"""
        found = []
        for pattern in self._DB_TRANSACTION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE | re.DOTALL):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} transaction boundary patterns"

    _DB_QUERY_ISOLATION_PATTERNS = [
        r"\bjoin\b",                                             # JOIN
        r"\bleft\s+(?:outer\s+)?join\b",                         # LEFT JOIN
        r"\binner\s+join\b",                                     # INNER JOIN
        r"\beager[_\s\-]?load\w*\b",                             # eager loading
        r"\bprefetch[_\s]?related\b",                            # prefetch_related (Django)
        r"\bselect[_\s]?related\b",                              # select_related (Django)
        r"\b(?:include|includes)\s*[:(]\b",                      # includes (Rails/Sequelize)
        r"\bDataLoader\b",                                       # DataLoader (GraphQL)
        r"\bbatch\w*\s+(?:query|fetch|load)\b",                  # batch query/fetch
        r"\bn\s*\+\s*1\b",                                       # N+1 mention
        r"\bsubquer(?:y|ies)\b",                                 # subquery
    ]

    def _check_db_query_isolation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for N+1 prevention / query batching patterns"""
        found = []
        for pattern in self._DB_QUERY_ISOLATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} query isolation patterns"

    _DB_UNIQUE_CONSTRAINTS_PATTERNS = [
        r"\bunique\b",                                           # UNIQUE keyword
        r"\bunique\s+(?:constraint|index|key)\b",                # UNIQUE CONSTRAINT/INDEX/KEY
        r"\bcreate\s+unique\s+index\b",                          # CREATE UNIQUE INDEX
        r"\badd\s+(?:constraint\s+)?\w*\s*unique\b",             # ADD CONSTRAINT ... UNIQUE
        r"\bunique_together\b",                                  # unique_together (Django)
        r"\bUniqueConstraint\b",                                 # UniqueConstraint (Django)
        r"\b\.unique\s*\(\s*\)\b",                               # .unique() (Knex/Prisma)
        r"@unique\b",                                             # @unique (Prisma)
        r"\bunique\s*=\s*True\b",                                # unique=True (SQLAlchemy/Django)
        r"\bduplicate\s+(?:key|entry|check)\b",                  # duplicate key handling
    ]

    def _check_db_unique_constraints(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for unique constraint patterns"""
        found = []
        for pattern in self._DB_UNIQUE_CONSTRAINTS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} unique constraint patterns"

    _DB_SENSITIVE_DATA_PATTERNS = [
        r"\bbcrypt\b",                                           # bcrypt
        r"\bargon2\b",                                           # argon2
        r"\bscrypt\b",                                           # scrypt
        r"\bhash\w*\s+password\b|\bpassword\s+hash\w*\b",       # hash password / password hash
        r"\bencrypt\w*\b",                                       # encrypt, encrypted, encryption
        r"\baes[_\s\-]?(?:256|128|gcm)\b",                       # AES-256/128/GCM
        r"\bpgcrypto\b",                                         # pgcrypto (PostgreSQL)
        r"\bmask\w*\s+(?:data|field|column|pii)\b",              # mask data/field/PII
        r"\bpii\b",                                              # PII mention
        r"\btokeniz\w+\b",                                       # tokenize/tokenization
        r"\b(?:at[_\s\-]?rest|column[_\s\-]?level)\s+encrypt\w*\b",  # at-rest/column-level encryption
    ]

    def _check_db_sensitive_data(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for sensitive data protection patterns"""
        found = []
        for pattern in self._DB_SENSITIVE_DATA_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} sensitive data protection patterns"

    _DB_CONNECTION_POOLING_PATTERNS = [
        r"\b(?:connection|conn)[_\s\-]?pool\w*\b",              # connection pool/pooling
        r"\bmax[_\s\-]?connections?\b",                          # max_connections
        r"\bpool[_\s\-]?size\b",                                 # pool_size
        r"\bmin[_\s\-]?(?:idle|pool)\b",                         # min_idle/min_pool
        r"\bidle[_\s\-]?timeout\b",                              # idle_timeout
        r"\bmax[_\s\-]?(?:overflow|idle)\b",                     # max_overflow/max_idle
        r"\bpg[Bb]ouncer\b",                                     # PgBouncer
        r"\bHikariCP\b",                                         # HikariCP (Java)
        r"\bcreate[_\s]?(?:pool|engine)\b",                      # create_pool/create_engine
        r"\bpool\s*=\s*\w+",                                     # pool = ...
    ]

    def _check_db_connection_pooling(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for connection pooling patterns"""
        found = []
        for pattern in self._DB_CONNECTION_POOLING_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} connection pooling patterns"

    _DB_BACKUP_STRATEGY_PATTERNS = [
        r"\bbackup\b",                                           # backup
        r"\brestore\b",                                          # restore
        r"\brecovery\b",                                         # recovery
        r"\bretention\s+(?:policy|period|days)\b",               # retention policy
        r"\bpg_dump\b",                                          # pg_dump (PostgreSQL)
        r"\bmysqldump\b",                                        # mysqldump
        r"\bwal\s+(?:archiv|replicate)\w*\b",                    # WAL archiving
        r"\bpoint[_\s\-]?in[_\s\-]?time\s+recovery\b",          # point-in-time recovery (PITR)
        r"\bautomated?\s+backup\b",                              # automated backup
        r"\bcron\w*\s+backup\b|\bbackup\s+cron\w*\b",           # cron backup schedule
        r"\brpo\b|\brto\b",                                      # RPO/RTO mention
    ]

    def _check_db_backup_strategy(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for backup strategy patterns"""
        found = []
        for pattern in self._DB_BACKUP_STRATEGY_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} backup strategy patterns"

    # Config Phase B check methods (Exp 42)

    _CONFIG_DEFAULTS_PATTERNS = [
        r"\bdefault\s*[:=]",                                    # default: value / default = value
        r":-[^}]+\}",                                           # ${VAR:-default_value}
        r"\$\{\w+:-",                                           # ${VAR:- (env var with default)
        r"\bdefault_?\w*\s*[:=]",                               # default_port: / defaultTimeout =
        r"\bfallback\s*[:=]",                                   # fallback: value
        r"\|\s*default\b",                                      # Jinja2: | default(...)
        r"\b(?:optional|nullable)\s*[:=]\s*(?:true|yes)\b",     # optional: true
        r"\brequired\s*[:=]\s*(?:false|no)\b",                  # required: false
        r"\bif\s+not\s+\w+",                                    # if not var (Python fallback)
        r"\b\w+\s*\?\?\s*",                                     # nullish coalescing: x ?? default
        r"\b\w+\s*\|\|\s*",                                     # OR fallback: x || default
        r"\bgetattr\s*\(.+,.+,.+\)",                            # getattr(obj, attr, default)
    ]

    def _check_config_defaults(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for default values in configuration"""
        found = []
        for pattern in self._CONFIG_DEFAULTS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} default value patterns"

    _CONFIG_ENVIRONMENT_VARS_PATTERNS = [
        r"\$\{[A-Z_][A-Z0-9_]*\}",                             # ${VAR_NAME}
        r"\$\{[A-Z_][A-Z0-9_]*:-[^}]*\}",                      # ${VAR:-default}
        r"\$[A-Z_][A-Z0-9_]*\b",                                # $VAR_NAME
        r"\bos\.environ\b",                                     # os.environ (Python)
        r"\bos\.getenv\b",                                      # os.getenv() (Python)
        r"\bprocess\.env\b",                                    # process.env (Node.js)
        r"\bSystem\.getenv\b",                                  # System.getenv() (Java)
        r"\bENV\[",                                             # ENV['VAR'] (Ruby)
        r"\benv\s*\(",                                          # env('VAR') (Laravel/config)
        r"\b(?:dotenv|load_dotenv)\b",                          # dotenv library usage
        r"\.env\b",                                             # .env file reference
    ]

    def _check_config_environment_vars(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for environment variable usage in configuration"""
        found = []
        for pattern in self._CONFIG_ENVIRONMENT_VARS_PATTERNS:
            if re.search(pattern, artifact):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} environment variable patterns"

    _CONFIG_VALUE_RANGES_PATTERNS = [
        r"\bport\s*[:=]\s*\d+\b",                              # port: 8080
        r"\btimeout\s*[:=]\s*\d+\b",                            # timeout: 30
        r"\bmax[_\s]?\w*\s*[:=]\s*\d+\b",                      # max_connections: 100
        r"\bmin[_\s]?\w*\s*[:=]\s*\d+\b",                      # min_connections: 5
        r"\blimit\s*[:=]\s*\d+\b",                              # limit: 1000
        r"\bsize\s*[:=]\s*\d+\b",                               # size: 256
        r"\bretries?\s*[:=]\s*\d+\b",                           # retries: 3
        r"\binterval\s*[:=]\s*\d+\b",                           # interval: 60
        r"\bthreshold\s*[:=]\s*\d+\b",                          # threshold: 80
        r"\bttl\s*[:=]\s*\d+\b",                                # ttl: 3600
        r"\b(?:0|[1-9]\d*)\.\d+\b",                             # float values: 0.5, 1.5
    ]

    def _check_config_value_ranges(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for numeric value ranges in configuration"""
        found = []
        for pattern in self._CONFIG_VALUE_RANGES_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} value range patterns"

    _CONFIG_ENUM_VALIDATION_PATTERNS = [
        r"\blog[_\s]?level\s*[:=]\s*['\"]?(?:DEBUG|INFO|WARNING|ERROR|CRITICAL|WARN|TRACE|FATAL)\b",
        r"\benvironment\s*[:=]\s*['\"]?(?:development|staging|production|test|local)\b",
        r"\bmode\s*[:=]\s*['\"]?(?:debug|release|production|development|test)\b",
        r"\bdriver\s*[:=]\s*['\"]?(?:mysql|postgres|sqlite|mongodb|redis)\b",
        r"\bprotocol\s*[:=]\s*['\"]?(?:http|https|tcp|udp|ws|wss|grpc)\b",
        r"\bformat\s*[:=]\s*['\"]?(?:json|xml|yaml|csv|text|html)\b",
        r"\bstrategy\s*[:=]\s*['\"]?(?:round[_\-]?robin|random|least[_\-]?connections|hash)\b",
        r"\b(?:choices|enum|values|options|allowed)\s*[:=]\s*\[",  # choices: [a, b, c]
        r"\bEnum\b|\benum\b",                                      # Enum class usage
        r"\bLiteral\[",                                            # Literal['a', 'b']
        r"\b(?:OneOf|anyOf|oneOf)\b",                              # JSON Schema validators
    ]

    def _check_config_enum_validation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for enum/choice validation in configuration"""
        found = []
        for pattern in self._CONFIG_ENUM_VALIDATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} enum validation patterns"

    _CONFIG_ENV_SEPARATION_PATTERNS = [
        r"\bconfig\.\w*(?:dev|prod|staging|test|local)\b",      # config.dev, config.prod
        r"\b(?:dev|prod|staging|test|local)\.(?:yml|yaml|json|toml|ini|env)\b",  # dev.yml, prod.json
        r"\benvironment\s*[:=]\s*['\"]?(?:development|staging|production|test)\b",
        r"\bprofile\s*[:=]\s*['\"]?\w+\b",                      # profile: development
        r"\b(?:FLASK_ENV|NODE_ENV|RAILS_ENV|APP_ENV|DJANGO_SETTINGS_MODULE)\b",  # env vars
        r"\b(?:spring\.profiles\.active|application-\w+\.yml)\b",  # Spring profiles
        r"\bif\s+(?:env|environment|NODE_ENV)\s*[=!]==?\s*['\"]",  # if env == 'production'
        r"\benv/\w+\b",                                          # env/production directory
        r"\.env\.\w+",                                              # .env.production, .env.local
        r"\benvironments?\s*:\s*\n",                             # environments: block in YAML
    ]

    def _check_config_env_separation(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for environment-specific configuration separation"""
        found = []
        for pattern in self._CONFIG_ENV_SEPARATION_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} environment separation patterns"

    _CONFIG_SECRET_REFERENCES_PATTERNS = [
        r"\$\{[A-Z_]*(?:SECRET|KEY|TOKEN|PASSWORD|CREDENTIAL)\w*\}",  # ${SECRET_NAME}
        r"\!vault\b",                                           # !vault (Ansible Vault)
        r"\bssm:/",                                             # ssm:/ (AWS SSM)
        r"\bvault\s*[:=]",                                      # vault: path/to/secret
        r"\bsecret[_\s]?manager\b",                             # secret_manager reference
        r"\baws[_\s]?secrets?\b",                               # aws_secret / aws secrets
        r"\bgcp[_\s]?secret\w*\b",                              # gcp_secret_manager
        r"\bazure[_\s]?key[_\s]?vault\b",                       # azure_key_vault
        r"\bhashicorp\s+vault\b",                               # HashiCorp Vault
        r"\bsops\b",                                            # Mozilla SOPS encrypted
        r"\bsealed[_\s]?secret\b",                              # Kubernetes SealedSecret
    ]

    def _check_config_secret_references(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for secret manager references instead of plaintext"""
        found = []
        for pattern in self._CONFIG_SECRET_REFERENCES_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} secret reference patterns"

    _CONFIG_SENSITIVE_FIELDS_PATTERNS = [
        r"\b(?:password|passwd|pwd)\s*[:=].*\*{3,}",           # password: ***
        r"\b(?:password|passwd|pwd)\s*[:=].*REDACTED",         # password: REDACTED
        r"\bencrypted\s*[:=]",                                  # encrypted: true / encrypted: value
        r"\bsecret\s*[:=]\s*\$",                                # secret: ${VAR}
        r"\b(?:api[_\s]?key|token)\s*[:=]\s*\$",               # api_key: ${VAR}
        r"\b(?:ENC|AES|RSA)\s*\[",                              # ENC[encrypted_value]
        r"\bciphertext\b",                                      # ciphertext reference
        r"\bkms\s*[:=]",                                        # KMS encryption
        r"\b(?:pgcrypto|encrypt|decrypt)\b",                    # encryption functions
        r"\bsensitive\s*[:=]\s*(?:true|yes)\b",                # sensitive: true (Terraform)
        r"\b@sensitive\b",                                      # @sensitive annotation
    ]

    def _check_config_sensitive_fields(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for sensitive field protection in configuration"""
        found = []
        for pattern in self._CONFIG_SENSITIVE_FIELDS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} sensitive field protection patterns"

    _CONFIG_OPTIMIZATIONS_PATTERNS = [
        r"\btimeout\s*[:=]\s*\d+\b",                            # timeout: 30
        r"\bcache\s*[:=]",                                       # cache: {...}
        r"\bpool\s*[:=]",                                        # pool: {...}
        r"\bmax[_\s]?connections?\s*[:=]\s*\d+\b",              # max_connections: 100
        r"\bttl\s*[:=]\s*\d+\b",                                # ttl: 3600
        r"\bbuffer[_\s]?size\s*[:=]\s*\d+\b",                  # buffer_size: 4096
        r"\bworkers?\s*[:=]\s*\d+\b",                           # workers: 4
        r"\bthreads?\s*[:=]\s*\d+\b",                           # threads: 8
        r"\bconcurrency\s*[:=]\s*\d+\b",                        # concurrency: 10
        r"\bbatch[_\s]?size\s*[:=]\s*\d+\b",                   # batch_size: 100
        r"\bkeep[_\s]?alive\b",                                 # keepalive / keep_alive
    ]

    def _check_config_optimizations(self, artifact: str, artifact_lower: str) -> Tuple[bool, str]:
        """Check for performance-related configuration settings"""
        found = []
        for pattern in self._CONFIG_OPTIMIZATIONS_PATTERNS:
            if re.search(pattern, artifact, re.IGNORECASE):
                found.append(pattern)
        return len(found) >= 2, f"Found {len(found)} optimization patterns"
