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
