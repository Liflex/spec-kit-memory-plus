"""
Refiner

Applies refinements to artifacts based on critique.
"""

import re
from typing import Dict, Optional, Callable
from specify_cli.quality.models import CritiqueResult


class Refiner:
    """Apply refinements to artifact"""

    # Exp 45: Rule-based transformations for no-LLM fallback
    # Maps rule_id to a method name that performs the transformation
    RULE_TRANSFORMS = {
        # Doc rules (Exp 45)
        "correctness.title": "_transform_add_title",
        "correctness.purpose": "_transform_add_purpose",
        "quality.installation": "_transform_add_installation",
        "quality.usage": "_transform_add_usage",
        "quality.structure": "_transform_fix_heading_hierarchy",
        "quality.code_blocks": "_transform_fix_code_blocks",
        "correctness.links": "_transform_add_links_section",
        "quality.comments": "_transform_add_comments_hint",
        # Code-gen rules (Exp 46)
        "correctness.tests": "_transform_add_tests_section",
        "quality.error_handling": "_transform_add_error_handling",
        "correctness.type_hints": "_transform_add_type_hints",
        "security.input_validation": "_transform_add_input_validation",
        "correctness.imports": "_transform_add_imports_section",
        "quality.context_managers": "_transform_add_context_managers",
    }

    def __init__(self, llm_client=None):
        """Initialize refiner

        Args:
            llm_client: Optional LLM client for intelligent refinements
        """
        self.llm_client = llm_client

    def apply(
        self,
        artifact: str,
        critique: CritiqueResult
    ) -> str:
        """Apply refinements based on critique

        Args:
            artifact: Current artifact content
            critique: Critique from Critique.generate()

        Returns:
            Refined artifact content
        """
        # Apply each fix sequentially
        refined_artifact = artifact

        # Exp 40: Support both CritiqueResult (attribute) and dict access
        issues = critique.issues if hasattr(critique, 'issues') else critique["issues"]
        for issue in issues:
            refined_artifact = self._apply_fix(refined_artifact, issue)

        return refined_artifact

    def _apply_fix(
        self,
        artifact: str,
        issue: Dict
    ) -> str:
        """Apply a single fix to artifact

        Args:
            artifact: Artifact content
            issue: Issue with fix instruction

        Returns:
            Updated artifact
        """
        if self.llm_client:
            return self._apply_fix_with_llm(artifact, issue)

        # Exp 45: Try rule-based transformation before giving up
        return self._apply_rule_based_fix(artifact, issue)

    def _apply_rule_based_fix(
        self,
        artifact: str,
        issue: Dict
    ) -> str:
        """Apply rule-based transformation without LLM (Exp 45)

        Args:
            artifact: Artifact content
            issue: Issue dict with rule_id, reason, fix

        Returns:
            Transformed artifact or unchanged if no transform available
        """
        rule_id = issue.get("rule_id", "")
        method_name = self.RULE_TRANSFORMS.get(rule_id)
        if method_name:
            method = getattr(self, method_name, None)
            if method:
                return method(artifact, issue)
        return artifact

    # --- Rule-based transforms (Exp 45) ---

    def _transform_add_title(self, artifact: str, issue: Dict) -> str:
        """Add missing document title"""
        if re.match(r"^\s*#\s+\S", artifact):
            return artifact
        return "# Document Title\n\n" + artifact

    def _transform_add_purpose(self, artifact: str, issue: Dict) -> str:
        """Add missing purpose/overview section"""
        if re.search(r"^##\s+(Overview|Purpose|Introduction)", artifact, re.MULTILINE):
            return artifact
        # Insert after title if present, otherwise at top
        title_match = re.match(r"(^\s*#\s+.+\n)", artifact)
        if title_match:
            insert_pos = title_match.end()
            return artifact[:insert_pos] + "\n## Overview\n\nTODO: Describe the purpose of this document.\n\n" + artifact[insert_pos:]
        return "## Overview\n\nTODO: Describe the purpose of this document.\n\n" + artifact

    def _transform_add_installation(self, artifact: str, issue: Dict) -> str:
        """Add missing installation section"""
        if re.search(r"^##\s+Installation", artifact, re.MULTILINE):
            return artifact
        return artifact.rstrip() + "\n\n## Installation\n\nTODO: Add installation instructions.\n"

    def _transform_add_usage(self, artifact: str, issue: Dict) -> str:
        """Add missing usage section"""
        if re.search(r"^##\s+Usage", artifact, re.MULTILINE):
            return artifact
        return artifact.rstrip() + "\n\n## Usage\n\nTODO: Add usage examples.\n"

    def _transform_fix_heading_hierarchy(self, artifact: str, issue: Dict) -> str:
        """Fix heading hierarchy: ensure no skipped levels"""
        lines = artifact.split("\n")
        result = []
        max_level = 0
        for line in lines:
            heading_match = re.match(r"^(#{1,6})\s+", line)
            if heading_match:
                level = len(heading_match.group(1))
                if max_level == 0:
                    max_level = level
                elif level > max_level + 1:
                    # Fix skipped level: reduce to max_level + 1
                    fixed_level = max_level + 1
                    line = "#" * fixed_level + line[level:]
                    level = fixed_level
                max_level = max(max_level, level)
            result.append(line)
        return "\n".join(result)

    def _transform_fix_code_blocks(self, artifact: str, issue: Dict) -> str:
        """Add language hint to bare code blocks"""
        def add_language(match):
            # If already has language, keep it
            if match.group(1):
                return match.group(0)
            return "```text" + match.group(0)[3:]
        return re.sub(r"```(\w*)\n", add_language, artifact)

    def _transform_add_links_section(self, artifact: str, issue: Dict) -> str:
        """Add references section if no links found"""
        if re.search(r"\[.+?\]\(.+?\)", artifact):
            return artifact
        return artifact.rstrip() + "\n\n## References\n\nTODO: Add relevant links and references.\n"

    def _transform_add_comments_hint(self, artifact: str, issue: Dict) -> str:
        """Add comment hint for config files"""
        if artifact.lstrip().startswith("#") or artifact.lstrip().startswith("//"):
            return artifact
        return "# TODO: Add comments for complex settings\n" + artifact

    # --- Code-gen rule-based transforms (Exp 46) ---

    def _transform_add_tests_section(self, artifact: str, issue: Dict) -> str:
        """Add test section if no tests found"""
        if re.search(r"(def test_|class Test|@pytest|unittest|assert\s)", artifact):
            return artifact
        return artifact.rstrip() + "\n\n# TODO: Add unit tests\n# def test_example():\n#     assert function_under_test() == expected\n"

    def _transform_add_error_handling(self, artifact: str, issue: Dict) -> str:
        """Add error handling hint if no try/except found"""
        if re.search(r"(try:|except\s|raise\s|Error\(|Exception\()", artifact):
            return artifact
        return artifact.rstrip() + "\n\n# TODO: Add error handling\n# try:\n#     ...\n# except SpecificError as e:\n#     handle_error(e)\n"

    def _transform_add_type_hints(self, artifact: str, issue: Dict) -> str:
        """Add type hints reminder if no annotations found"""
        if re.search(r"(:\s*(str|int|float|bool|List|Dict|Optional|Any)\b|->)", artifact):
            return artifact
        # Insert comment after first def if exists
        def_match = re.search(r"^(def \w+\()", artifact, re.MULTILINE)
        if def_match:
            return artifact[:def_match.start()] + "# TODO: Add type hints to function signatures\n" + artifact[def_match.start():]
        return "# TODO: Add type hints to function signatures\n" + artifact

    def _transform_add_input_validation(self, artifact: str, issue: Dict) -> str:
        """Add input validation hint if no validation found"""
        if re.search(r"(validate|sanitize|isinstance\(|if not\s+\w+:|raise ValueError|raise TypeError)", artifact):
            return artifact
        return artifact.rstrip() + "\n\n# TODO: Add input validation\n# - Validate parameter types and ranges\n# - Sanitize user input before processing\n"

    def _transform_add_imports_section(self, artifact: str, issue: Dict) -> str:
        """Add imports section if no imports found"""
        if re.search(r"^(import |from \w+ import )", artifact, re.MULTILINE):
            return artifact
        return "# TODO: Add necessary imports\n# import os\n# from typing import List, Dict, Optional\n\n" + artifact

    def _transform_add_context_managers(self, artifact: str, issue: Dict) -> str:
        """Add context manager hint if file/resource operations lack 'with'"""
        if re.search(r"(with\s+\w+|__enter__|__exit__|@contextmanager|contextlib)", artifact):
            return artifact
        # Only add if there are file/resource operations
        if re.search(r"(open\(|connect\(|cursor\(|socket\(|Session\()", artifact):
            return artifact.rstrip() + "\n\n# TODO: Use context managers for resource management\n# with open(path) as f:\n#     data = f.read()\n"
        return artifact

    def _apply_fix_with_llm(
        self,
        artifact: str,
        issue: Dict
    ) -> str:
        """Apply fix using LLM

        Args:
            artifact: Artifact content
            issue: Issue with fix instruction

        Returns:
            Refined artifact
        """
        prompt = f"""You are a code refiner. Apply the following fix to the artifact:

**Issue**: {issue['rule_id']}
**Reason**: {issue['reason']}
**Fix Instruction**: {issue['fix']}

**Artifact**:
```
{artifact}
```

**Output**:
Return the refined artifact with the fix applied. Only modify the relevant sections.
"""

        try:
            # Call LLM (implementation depends on LLM client)
            if self.llm_client:
                response = self.llm_client.generate(prompt)
                return response
            else:
                return artifact
        except Exception as e:
            # If LLM fails, return unchanged
            print(f"Warning: LLM refinement failed for {issue['rule_id']}: {e}")
            return artifact
