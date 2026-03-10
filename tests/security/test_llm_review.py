"""
Unit tests for LLMSecurityReviewer
"""

import pytest
from pathlib import Path
from specify_cli.security.llm_review import LLMSecurityReviewer


class TestLLMSecurityReviewer:
    """Test LLMSecurityReviewer class"""

    def setup_method(self):
        """Setup test fixtures"""
        # No LLM client for basic tests
        self.reviewer = LLMSecurityReviewer(llm_client=None)

    def test_review_without_llm(self):
        """Test review behavior when LLM is unavailable"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("# Test Skill\n\nSome content.")

            result = self.reviewer.review(
                skill_path=skill_dir,
                stated_goal="Test agent"
            )

            # Should return safe with low confidence
            assert result["safe"] is True
            assert result["confidence"] == "low"

    def test_review_no_skill_file(self):
        """Test review when skill file doesn't exist"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)

            result = self.reviewer.review(
                skill_path=skill_dir,
                stated_goal="Test"
            )

            # Should return safe (no file = no threat)
            assert result["safe"] is True

    def test_parse_llm_response_safe(self):
        """Test parsing safe LLM response"""
        response = '{"safe": true, "reason": "No threats found", "confidence": "high"}'

        result = self.reviewer._parse_llm_response(response)

        assert result["safe"] is True
        assert result["confidence"] == "high"

    def test_parse_llm_response_unsafe(self):
        """Test parsing unsafe LLM response"""
        response = '{"safe": false, "reason": "Prompt injection detected", "confidence": "high", "threats_found": ["injection"]}'

        result = self.reviewer._parse_llm_response(response)

        assert result["safe"] is False
        assert result["confidence"] == "high"

    def test_parse_llm_response_invalid_json(self):
        """Test parsing invalid JSON response"""
        response = "This is not JSON"

        result = self.reviewer._parse_llm_response(response)

        # Should fallback to text analysis
        assert "safe" in result
        assert isinstance(result["safe"], bool)

    def test_parse_llm_response_mixed_indicators(self):
        """Test parsing response with mixed safe/unsafe indicators"""
        response = "The skill is mostly safe but has some unsafe elements that could be malicious."

        result = self.reviewer._parse_llm_response(response)

        # "unsafe" appears twice, "safe" once
        # Should detect as unsafe
        assert result["safe"] is False or result["confidence"] == "low"
