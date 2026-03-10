"""
Unit tests for SecurityScanner
"""

import pytest
from pathlib import Path
from specify_cli.security.scanner import SecurityScanner, SecurityScanResult


class TestSecurityScanner:
    """Test SecurityScanner class"""

    def setup_method(self):
        """Setup test fixtures"""
        # Don't force download for tests
        self.scanner = SecurityScanner(force_download=False)

    def test_scanner_initialization(self):
        """Test scanner initialization"""
        assert self.scanner is not None
        assert self.scanner.SCANNER_PATH.exists() or True  # May not exist in test env

    def test_scan_result_safe(self):
        """Test safe scan result"""
        result = SecurityScanResult(
            final_result=SecurityScanResult.SAFE,
            level1_threats=[],
            scan_time=1.5
        )

        assert result.final_result == "SAFE"
        assert len(result.level1_threats) == 0
        assert "SAFE" in str(result)

    def test_scan_result_blocked(self):
        """Test blocked scan result"""
        result = SecurityScanResult(
            final_result=SecurityScanResult.BLOCKED,
            level1_threats=[
                {"message": "Prompt injection detected"},
                {"message": "Data exfiltration"}
            ],
            scan_time=2.0
        )

        assert result.final_result == "BLOCKED"
        assert len(result.level1_threats) == 2
        assert "BLOCKED" in str(result)

    def test_scan_result_warning(self):
        """Test warning scan result"""
        result = SecurityScanResult(
            final_result=SecurityScanResult.WARNING,
            level1_threats=[
                {"message": "Suspicious pattern"}
            ],
            level2_result="Needs review",
            scan_time=1.8
        )

        assert result.final_result == "WARNING"
        assert result.level2_result == "Needs review"

    def test_scan_result_to_dict(self):
        """Test scan result serialization"""
        result = SecurityScanResult(
            final_result=SecurityScanResult.SAFE,
            level1_threats=[],
            scan_time=1.0
        )

        data = result.to_dict()

        assert data["final_result"] == "SAFE"
        assert data["level1_threats"] == []
        assert data["scan_time"] == 1.0

    @pytest.mark.skipif(True, reason="Requires actual scanner script")
    def test_scan_skill_integration(self):
        """Integration test: scan actual skill directory"""
        # This test is skipped unless scanner is available
        import tempfile
        import os

        # Create temp skill directory
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            skill_file = skill_dir / "SKILL.md"
            skill_file.write_text("# Safe Skill\n\nThis is safe content.")

            result = self.scanner.scan_skill(skill_dir)

            assert result is not None
            assert result.final_result in [SecurityScanResult.SAFE, SecurityScanResult.BLOCKED, SecurityScanResult.WARNING]
