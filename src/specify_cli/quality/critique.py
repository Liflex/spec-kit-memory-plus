"""
Critique

Generates targeted feedback for failed rules.
"""

from typing import List, Dict
from specify_cli.quality.models import FailedRule, CritiqueResult


class Critique:
    """Generate critique for failed rules"""

    # Rule-specific fix instructions
    FIX_INSTRUCTIONS = {
        # API Spec rules
        "correctness.endpoints": (
            "Add the missing CRUD endpoint:\n"
            "1. Identify the missing operation (GET, POST, PUT, DELETE)\n"
            "2. Create the endpoint function\n"
            "3. Add proper routing and documentation"
        ),
        "correctness.status_codes": (
            "Add missing HTTP status codes:\n"
            "1. Include 200 for successful operations\n"
            "2. Include 201 for resource creation\n"
            "3. Include 400 for client errors\n"
            "4. Include 404 for not found\n"
            "5. Include 500 for server errors"
        ),
        "correctness.content_types": (
            "Specify Content-Type headers:\n"
            "1. Add 'Content-Type: application/json' for JSON responses\n"
            "2. Add 'Content-Type: text/html' for HTML responses"
        ),
        "correctness.auth": (
            "Document authentication requirements:\n"
            "1. Specify auth method (Bearer token, API key, OAuth)\n"
            "2. Show example Authorization header\n"
            "3. Document how to obtain credentials"
        ),
        "quality.parameters": (
            "Document request parameters:\n"
            "1. List all query parameters\n"
            "2. List all path parameters\n"
            "3. List all body fields with types"
        ),
        "quality.responses": (
            "Document response schemas:\n"
            "1. Define response body structure\n"
            "2. Specify field types and constraints\n"
            "3. Include example responses"
        ),

        # Code Gen rules
        "correctness.tests": (
            "Add unit tests:\n"
            "1. Create test file in tests/\n"
            "2. Write test cases for each function\n"
            "3. Mock external dependencies\n"
            "4. Cover success and failure cases"
        ),
        "quality.error_handling": (
            "Improve error handling:\n"
            "1. Wrap risky operations in try/except\n"
            "2. Validate inputs before processing\n"
            "3. Return meaningful error messages\n"
            "4. Log errors for debugging"
        ),
        "quality.readability": (
            "Improve code readability:\n"
            "1. Add comments explaining complex logic\n"
            "2. Add docstrings to functions/classes\n"
            "3. Use descriptive variable names\n"
            "4. Break up long functions"
        ),
        "correctness.type_hints": (
            "Add type hints:\n"
            "1. Add type annotations to function parameters\n"
            "2. Add return type annotations\n"
            "3. Use typing module for complex types"
        ),
        "correctness.structure": (
            "Improve code structure:\n"
            "1. Group related code into classes/modules\n"
            "2. Separate concerns (models, services, handlers)\n"
            "3. Follow project structure conventions"
        ),
        "security.input_validation": (
            "Add input validation:\n"
            "1. Validate parameter types and ranges\n"
            "2. Sanitize user input\n"
            "3. Check for required fields\n"
            "4. Handle edge cases"
        ),
        "security.secrets": (
            "Remove hardcoded secrets:\n"
            "1. Move secrets to environment variables\n"
            "2. Use config files (gitignored)\n"
            "3. Use secret management service\n"
            "4. Document required environment variables"
        ),
        "performance.complexity": (
            "Reduce code complexity:\n"
            "1. Extract helper methods for nested logic\n"
            "2. Use early returns to reduce nesting\n"
            "3. Consider using design patterns"
        ),
        "quality.logging": (
            "Add logging:\n"
            "1. Add log statements for key operations\n"
            "2. Use appropriate log levels (INFO, ERROR, DEBUG)\n"
            "3. Include contextual information"
        ),
        "correctness.imports": (
            "Clean up imports:\n"
            "1. Remove unused imports\n"
            "2. Group standard library imports\n"
            "3. Group third-party imports\n"
            "4. Follow import organization conventions"
        ),
        "performance.caching": (
            "Add caching for expensive operations:\n"
            "1. Identify slow/repeated operations\n"
            "2. Add caching decorator (e.g., @lru_cache)\n"
            "3. Set appropriate cache size/ttl"
        ),

        # Docs rules
        "correctness.title": (
            "Add document title:\n"
            "1. Add # Title at the top\n"
            "2. Make it descriptive and clear"
        ),
        "correctness.purpose": (
            "Add purpose/overview section:\n"
            "1. Add ## Overview or ## Introduction\n"
            "2. Explain what this documentation covers\n"
            "3. Mention target audience"
        ),
        "quality.installation": (
            "Add installation instructions:\n"
            "1. Add ## Installation section\n"
            "2. List prerequisites\n"
            "3. Provide step-by-step instructions"
        ),
        "quality.usage": (
            "Add usage examples:\n"
            "1. Add ## Usage section\n"
            "2. Include code examples in ``` blocks\n"
            "3. Show common use cases"
        ),
        "quality.structure": (
            "Improve heading hierarchy:\n"
            "1. Use # for main title\n"
            "2. Use ## for major sections\n"
            "3. Use ### for subsections\n"
            "4. Don't skip levels"
        ),
        "correctness.spelling": (
            "Fix spelling errors:\n"
            "1. Review for common typos\n"
            "2. Use spell checker\n"
            "3. Ask someone to review"
        ),
        "quality.code_blocks": (
            "Format code blocks:\n"
            "1. Use ```language for code\n"
            "2. Specify language (python, bash, etc.)\n"
            "3. Ensure code is syntactically correct"
        ),

        # Config rules
        "correctness.syntax": (
            "Fix file syntax:\n"
            "1. Validate YAML/JSON syntax\n"
            "2. Use linter/formatter\n"
            "3. Check for matching brackets/quotes"
        ),
        "correctness.required_fields": (
            "Add required fields:\n"
            "1. Check schema or documentation\n"
            "2. Add all required keys\n"
            "3. Use appropriate values"
        ),
        "correctness.field_types": (
            "Fix field value types:\n"
            "1. Check expected types for each field\n"
            "2. Convert strings to numbers/booleans as needed\n"
            "3. Use quotes for strings"
        ),
        "quality.comments": (
            "Add comments for complex settings:\n"
            "1. Explain non-obvious settings\n"
            "2. Add inline comments for tricky values\n"
            "3. Document any overrides"
        ),
        "correctness.paths": (
            "Fix file paths:\n"
            "1. Verify referenced files exist\n"
            "2. Use relative paths when possible\n"
            "3. Check path separators for OS"
        ),
        "quality.defaults": (
            "Add default values:\n"
            "1. Provide sensible defaults for optional fields\n"
            "2. Document what the default is\n"
            "3. Use production-safe defaults"
        ),
        "quality.environment_vars": (
            "Use environment variables:\n"
            "1. Replace hardcoded values with ${VAR}\n"
            "2. Add ${VAR:-default} for defaults\n"
            "3. Document required environment variables"
        ),
    }

    def __init__(self, max_issues: int = 5):
        """Initialize critique generator

        Args:
            max_issues: Maximum issues to generate (default: 5)
        """
        self.max_issues = max_issues

    def generate(
        self,
        failed_rules: List[Dict],
        artifact: str
    ) -> Dict:
        """Generate critique with fix instructions

        Args:
            failed_rules: List of {rule_id, reason} from evaluation
            artifact: Artifact content

        Returns:
            Critique dict with issues and fix instructions
        """
        # Limit to max_issues
        limited_rules = failed_rules[:self.max_issues]

        issues = []
        for failed in limited_rules:
            rule_id = failed["rule_id"]
            reason = failed["reason"]

            fix_instruction = self._generate_fix_instruction(
                rule_id, reason, artifact
            )

            issues.append({
                "rule_id": rule_id,
                "reason": reason,
                "fix": fix_instruction
            })

        return {
            "issues": issues,
            "total_failed": len(failed_rules),
            "addressed": len(limited_rules),
            "skipped": len(failed_rules) - len(limited_rules),
        }

    def _generate_fix_instruction(
        self,
        rule_id: str,
        reason: str,
        artifact: str
    ) -> str:
        """Generate specific fix instruction for a rule

        Args:
            rule_id: Rule that failed
            reason: Why it failed
            artifact: Artifact content

        Returns:
            Fix instruction string
        """
        # Use rule-specific instruction if available
        if rule_id in self.FIX_INSTRUCTIONS:
            return self.FIX_INSTRUCTIONS[rule_id]

        # Generic fix instruction
        return (
            f"Fix issue: {reason}\n"
            f"1. Identify the problem area in the artifact\n"
            f"2. Apply the fix based on the rule: {rule_id}\n"
            f"3. Verify the change addresses the failed check"
        )
