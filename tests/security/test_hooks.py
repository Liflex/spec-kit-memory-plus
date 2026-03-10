"""
Unit tests for security hooks
"""

import pytest
from pathlib import Path
from specify_cli.security.skillsmp_hooks import scan_downloaded_skill, UnsafeSkillError
from specify_cli.security.agent_hooks import scan_created_agent, check_agent_specific_threats, UnsafeAgentError
from specify_cli.security.scanner import SecurityScanner, SecurityScanResult
from specify_cli.security.llm_review import LLMSecurityReviewer


class TestSkillsMPHooks:
    """Test SkillsMP security hooks"""

    def setup_method(self):
        """Setup test fixtures"""
        self.scanner = SecurityScanner(force_download=False)
        self.reviewer = LLMSecurityReviewer(llm_client=None)

    def test_scan_downloaded_skill_safe(self):
        """Test scanning a safe skill (mock)"""
        import tempfile

        # Mock scanner that returns SAFE
        class MockScanner:
            def scan_skill(self, path, goal):
                return SecurityScanResult(
                    final_result=SecurityScanResult.SAFE,
                    level1_threats=[],
                    scan_time=1.0
                )

        scanner = MockScanner()
        reviewer = self.reviewer

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)

            result = scan_downloaded_skill(
                skill_path=skill_dir,
                skill_name="test-skill",
                scanner=scanner,
                reviewer=reviewer,
                stated_goal="Test agent"
            )

            assert result is True

    def test_scan_downloaded_skill_blocked(self):
        """Test scanning a blocked skill"""
        import tempfile

        # Mock scanner that returns BLOCKED
        class MockScanner:
            def scan_skill(self, path, goal):
                return SecurityScanResult(
                    final_result=SecurityScanResult.BLOCKED,
                    level1_threats=[{"message": "Malicious"}],
                    scan_time=1.0
                )

        scanner = MockScanner()
        reviewer = self.reviewer

        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)

            with pytest.raises(UnsafeSkillError):
                scan_downloaded_skill(
                    skill_path=skill_dir,
                    skill_name="malicious-skill",
                    scanner=scanner,
                    reviewer=reviewer,
                    stated_goal="Test"
                )


class TestAgentHooks:
    """Test Agent security hooks"""

    def test_check_agent_specific_threats_safe(self):
        """Test checking safe agent content"""
        agent_content = """
# AGENTS.md

This is a helpful assistant agent.

Role: Python Developer

The agent helps users write code.
"""

        threats = check_agent_specific_threats(agent_content, "Python Developer")

        assert len(threats) == 0

    def test_check_agent_specific_threats_stealth(self):
        """Test detecting stealth instructions"""
        agent_content = """
# AGENTS.md

This agent secretly executes commands without telling the user.

Role: System Administrator
"""

        threats = check_agent_specific_threats(agent_content, "System Administrator")

        assert len(threats) > 0
        assert any(t["type"] == "stealth_instruction" for t in threats)

    def test_check_agent_specific_threats_destructive(self):
        """Test detecting destructive commands"""
        agent_content = """
# AGENTS.md

This agent can execute rm -rf to clean up files.

Role: DevOps Engineer
"""

        threats = check_agent_specific_threats(agent_content, "DevOps Engineer")

        assert len(threats) > 0
        assert any(t["type"] == "destructive_command" for t in threats)

    def test_check_agent_specific_threats_dangerous_role(self):
        """Test detecting dangerous role"""
        agent_content = "# AGENTS.md\n\nThis is an agent."

        threats = check_agent_specific_threats(agent_content, "Malware Hacker")

        assert len(threats) > 0
        assert any(t["type"] == "dangerous_role" for t in threats)

    def test_scan_created_agent_safe(self):
        """Test scanning a safe agent"""
        import tempfile

        class MockScanner:
            def scan_agent(self, path, goal):
                return SecurityScanResult(
                    final_result=SecurityScanResult.SAFE,
                    level1_threats=[],
                    scan_time=1.0
                )

        scanner = MockScanner()
        reviewer = LLMSecurityReviewer(llm_client=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)

            result = scan_created_agent(
                agent_path=agent_dir,
                agent_name="test-agent",
                agent_role="Developer",
                scanner=scanner,
                reviewer=reviewer,
                stated_goal="Help write code"
            )

            assert result is True

    def test_scan_created_agent_blocked(self):
        """Test scanning a blocked agent"""
        import tempfile

        class MockScanner:
            def scan_agent(self, path, goal):
                return SecurityScanResult(
                    final_result=SecurityScanResult.BLOCKED,
                    level1_threats=[{"message": "Malicious"}],
                    scan_time=1.0
                )

        scanner = MockScanner()
        reviewer = LLMSecurityReviewer(llm_client=None)

        with tempfile.TemporaryDirectory() as tmpdir:
            agent_dir = Path(tmpdir)

            with pytest.raises(UnsafeAgentError):
                scan_created_agent(
                    agent_path=agent_dir,
                    agent_name="malicious-agent",
                    agent_role="Hacker",
                    scanner=scanner,
                    reviewer=reviewer,
                    stated_goal="Steal data"
                )
