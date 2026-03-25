"""
Unit tests for Refiner
"""

import pytest
from specify_cli.quality.refiner import Refiner
from specify_cli.quality.models import CritiqueResult


class TestRefiner:
    """Test Refiner class"""

    def setup_method(self):
        """Setup test fixtures"""
        self.refiner = Refiner(llm_client=None)  # No LLM for testing

    def test_apply_no_fixes(self):
        """Test applying critique with no fixes"""
        artifact = "Original artifact content"
        critique = {"issues": [], "total_failed": 0, "addressed": 0, "skipped": 0}

        refined = self.refiner.apply(artifact, critique)

        # Without LLM, should return unchanged
        assert refined == artifact

    def test_apply_single_fix(self):
        """Test applying a single fix"""
        artifact = "def hello():\n    pass"
        critique = {
            "issues": [
                {
                    "rule_id": "quality.readability",
                    "reason": "No comments",
                    "fix": "Add comments explaining the function"
                }
            ],
            "total_failed": 1,
            "addressed": 1,
            "skipped": 0
        }

        refined = self.refiner.apply(artifact, critique)

        # Without LLM, returns unchanged
        # In production, would apply fix
        assert refined is not None

    def test_apply_multiple_fixes(self):
        """Test applying multiple fixes"""
        artifact = "Some artifact content"
        critique = {
            "issues": [
                {"rule_id": "rule1", "reason": "Reason 1", "fix": "Fix 1"},
                {"rule_id": "rule2", "reason": "Reason 2", "fix": "Fix 2"},
            ],
            "total_failed": 2,
            "addressed": 2,
            "skipped": 0
        }

        refined = self.refiner.apply(artifact, critique)

        assert refined is not None

    def test_apply_fix_with_llm(self):
        """Test applying fix with LLM (mock)"""
        # Create mock LLM client
        class MockLLM:
            def generate(self, prompt):
                return "Refined artifact content"

        refiner_with_llm = Refiner(llm_client=MockLLM())

        artifact = "Original content"
        critique = {
            "issues": [
                {"rule_id": "rule1", "reason": "Reason", "fix": "Fix"},
            ],
            "total_failed": 1,
            "addressed": 1,
            "skipped": 0
        }

        refined = refiner_with_llm.apply(artifact, critique)

        assert refined == "Refined artifact content"


class TestRuleBasedTransforms:
    """Test rule-based refiner transformations (Exp 45)"""

    def setup_method(self):
        self.refiner = Refiner(llm_client=None)

    # --- correctness.title ---

    def test_add_title_when_missing(self):
        artifact = "Some content without a title"
        issue = {"rule_id": "correctness.title", "reason": "No title", "fix": "Add title"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result.startswith("# Document Title\n")
        assert "Some content without a title" in result

    def test_add_title_skipped_when_present(self):
        artifact = "# My Title\n\nContent here"
        issue = {"rule_id": "correctness.title", "reason": "No title", "fix": "Add title"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- correctness.purpose ---

    def test_add_purpose_after_title(self):
        artifact = "# My Doc\n\nSome content"
        issue = {"rule_id": "correctness.purpose", "reason": "No overview", "fix": "Add overview"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "## Overview" in result
        assert result.index("# My Doc") < result.index("## Overview")

    def test_add_purpose_skipped_when_present(self):
        artifact = "# My Doc\n\n## Overview\n\nThis is about X."
        issue = {"rule_id": "correctness.purpose", "reason": "No overview", "fix": "Add overview"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- quality.installation ---

    def test_add_installation_section(self):
        artifact = "# My Doc\n\nContent"
        issue = {"rule_id": "quality.installation", "reason": "Missing", "fix": "Add installation"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "## Installation" in result

    def test_add_installation_skipped_when_present(self):
        artifact = "# My Doc\n\n## Installation\n\npip install foo"
        issue = {"rule_id": "quality.installation", "reason": "Missing", "fix": "Add installation"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- quality.usage ---

    def test_add_usage_section(self):
        artifact = "# My Doc\n\nContent"
        issue = {"rule_id": "quality.usage", "reason": "Missing", "fix": "Add usage"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "## Usage" in result

    def test_add_usage_skipped_when_present(self):
        artifact = "# My Doc\n\n## Usage\n\nExample here"
        issue = {"rule_id": "quality.usage", "reason": "Missing", "fix": "Add usage"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- quality.structure (heading hierarchy) ---

    def test_fix_heading_hierarchy_skipped_level(self):
        artifact = "# Title\n\n#### Subsection\n\nContent"
        issue = {"rule_id": "quality.structure", "reason": "Skipped levels", "fix": "Fix"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "## Subsection" in result
        assert "####" not in result

    def test_fix_heading_hierarchy_already_correct(self):
        artifact = "# Title\n\n## Section\n\n### Subsection"
        issue = {"rule_id": "quality.structure", "reason": "Skipped levels", "fix": "Fix"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- quality.code_blocks ---

    def test_fix_code_blocks_bare(self):
        artifact = "Example:\n\n```\nprint('hello')\n```"
        issue = {"rule_id": "quality.code_blocks", "reason": "No lang", "fix": "Add lang"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "```text" in result

    def test_fix_code_blocks_already_has_language(self):
        artifact = "Example:\n\n```python\nprint('hello')\n```"
        issue = {"rule_id": "quality.code_blocks", "reason": "No lang", "fix": "Add lang"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "```python" in result
        assert "```text" not in result

    # --- correctness.links ---

    def test_add_links_section_when_no_links(self):
        artifact = "# Doc\n\nNo links here"
        issue = {"rule_id": "correctness.links", "reason": "No links", "fix": "Add links"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "## References" in result

    def test_add_links_skipped_when_links_present(self):
        artifact = "# Doc\n\nSee [this](http://example.com)"
        issue = {"rule_id": "correctness.links", "reason": "No links", "fix": "Add links"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- quality.comments ---

    def test_add_comments_hint_to_config(self):
        artifact = "key: value\nother: data"
        issue = {"rule_id": "quality.comments", "reason": "No comments", "fix": "Add comments"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result.startswith("# TODO:")

    def test_add_comments_skipped_when_comment_present(self):
        artifact = "# Config file\nkey: value"
        issue = {"rule_id": "quality.comments", "reason": "No comments", "fix": "Add comments"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- Unknown rule falls through ---

    def test_unknown_rule_returns_unchanged(self):
        artifact = "Original content"
        issue = {"rule_id": "unknown.rule", "reason": "Something", "fix": "Fix it"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- Integration: apply() uses rule-based when no LLM ---

    def test_apply_uses_rule_based_without_llm(self):
        artifact = "Some content without title"
        critique = {
            "issues": [
                {"rule_id": "correctness.title", "reason": "No title", "fix": "Add title"}
            ],
            "total_failed": 1, "addressed": 1, "skipped": 0,
        }
        result = self.refiner.apply(artifact, critique)
        assert result.startswith("# Document Title\n")

    def test_apply_chains_multiple_rule_transforms(self):
        artifact = "Some content"
        critique = {
            "issues": [
                {"rule_id": "correctness.title", "reason": "No title", "fix": "Add title"},
                {"rule_id": "quality.usage", "reason": "Missing usage", "fix": "Add usage"},
            ],
            "total_failed": 2, "addressed": 2, "skipped": 0,
        }
        result = self.refiner.apply(artifact, critique)
        assert "# Document Title" in result
        assert "## Usage" in result


class TestCodeGenTransforms:
    """Test code-gen rule-based refiner transformations (Exp 46)"""

    def setup_method(self):
        self.refiner = Refiner(llm_client=None)

    # --- correctness.tests ---

    def test_add_tests_section_when_missing(self):
        artifact = "def calculate(x):\n    return x * 2"
        issue = {"rule_id": "correctness.tests", "reason": "No tests", "fix": "Add tests"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "# TODO: Add unit tests" in result
        assert "def test_example" in result

    def test_add_tests_skipped_when_tests_present(self):
        artifact = "def test_calc():\n    assert calculate(2) == 4"
        issue = {"rule_id": "correctness.tests", "reason": "No tests", "fix": "Add tests"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    def test_add_tests_skipped_when_pytest_present(self):
        artifact = "@pytest.mark.parametrize('x', [1, 2])\ndef check(x): pass"
        issue = {"rule_id": "correctness.tests", "reason": "No tests", "fix": "Add tests"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- quality.error_handling ---

    def test_add_error_handling_when_missing(self):
        artifact = "def process(data):\n    return data['key']"
        issue = {"rule_id": "quality.error_handling", "reason": "No error handling", "fix": "Add try/except"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "# TODO: Add error handling" in result
        assert "except" in result

    def test_add_error_handling_skipped_when_try_present(self):
        artifact = "try:\n    x = 1\nexcept ValueError:\n    pass"
        issue = {"rule_id": "quality.error_handling", "reason": "No error handling", "fix": "Add try/except"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    def test_add_error_handling_skipped_when_raise_present(self):
        artifact = "if not data:\n    raise ValueError('empty')"
        issue = {"rule_id": "quality.error_handling", "reason": "No error handling", "fix": "Add"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- correctness.type_hints ---

    def test_add_type_hints_when_missing(self):
        artifact = "def greet(name):\n    return f'Hello {name}'"
        issue = {"rule_id": "correctness.type_hints", "reason": "No type hints", "fix": "Add hints"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "# TODO: Add type hints" in result

    def test_add_type_hints_inserted_before_first_def(self):
        artifact = "# Module\n\ndef greet(name):\n    pass"
        issue = {"rule_id": "correctness.type_hints", "reason": "No type hints", "fix": "Add hints"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result.index("# TODO: Add type hints") < result.index("def greet")

    def test_add_type_hints_skipped_when_annotations_present(self):
        artifact = "def greet(name: str) -> str:\n    return f'Hello {name}'"
        issue = {"rule_id": "correctness.type_hints", "reason": "No type hints", "fix": "Add hints"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- security.input_validation ---

    def test_add_input_validation_when_missing(self):
        artifact = "def process(data):\n    return data"
        issue = {"rule_id": "security.input_validation", "reason": "No validation", "fix": "Add validation"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "# TODO: Add input validation" in result

    def test_add_input_validation_skipped_when_validate_present(self):
        artifact = "def process(data):\n    validate(data)\n    return data"
        issue = {"rule_id": "security.input_validation", "reason": "No validation", "fix": "Add validation"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    def test_add_input_validation_skipped_when_isinstance_present(self):
        artifact = "if not isinstance(x, int):\n    raise TypeError('bad type')"
        issue = {"rule_id": "security.input_validation", "reason": "No validation", "fix": "Add validation"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- correctness.imports ---

    def test_add_imports_section_when_missing(self):
        artifact = "def hello():\n    print('hi')"
        issue = {"rule_id": "correctness.imports", "reason": "No imports", "fix": "Add imports"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "# TODO: Add necessary imports" in result
        assert result.index("# TODO") < result.index("def hello")

    def test_add_imports_skipped_when_imports_present(self):
        artifact = "import os\n\ndef hello():\n    print(os.getcwd())"
        issue = {"rule_id": "correctness.imports", "reason": "No imports", "fix": "Add imports"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    def test_add_imports_skipped_when_from_import_present(self):
        artifact = "from pathlib import Path\n\ndef hello():\n    pass"
        issue = {"rule_id": "correctness.imports", "reason": "No imports", "fix": "Add imports"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- quality.context_managers ---

    def test_add_context_managers_when_open_without_with(self):
        artifact = "f = open('data.txt')\ndata = f.read()\nf.close()"
        issue = {"rule_id": "quality.context_managers", "reason": "No context mgr", "fix": "Use with"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert "# TODO: Use context managers" in result

    def test_add_context_managers_skipped_when_with_present(self):
        artifact = "with open('data.txt') as f:\n    data = f.read()"
        issue = {"rule_id": "quality.context_managers", "reason": "No context mgr", "fix": "Use with"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    def test_add_context_managers_skipped_when_no_resources(self):
        artifact = "x = 1 + 2\nprint(x)"
        issue = {"rule_id": "quality.context_managers", "reason": "No context mgr", "fix": "Use with"}
        result = self.refiner._apply_rule_based_fix(artifact, issue)
        assert result == artifact

    # --- Integration ---

    def test_apply_chains_code_gen_transforms(self):
        artifact = "def process(data):\n    return data"
        critique = {
            "issues": [
                {"rule_id": "correctness.tests", "reason": "No tests", "fix": "Add tests"},
                {"rule_id": "quality.error_handling", "reason": "No error handling", "fix": "Add"},
            ],
            "total_failed": 2, "addressed": 2, "skipped": 0,
        }
        result = self.refiner.apply(artifact, critique)
        assert "# TODO: Add unit tests" in result
        assert "# TODO: Add error handling" in result
