"""
Security Scanner

Wrapper for ai-factory security-scan.py (Level 1 scanner).
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from platformdirs import user_cache_dir


class SecurityScanResult:
    """Result of security scan"""

    SAFE = "SAFE"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"

    def __init__(
        self,
        final_result: str,
        level1_threats: list,
        level2_result: Optional[str] = None,
        scan_time: Optional[float] = None,
    ):
        self.final_result = final_result
        self.level1_threats = level1_threats
        self.level2_result = level2_result
        self.scan_time = scan_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_result": self.final_result,
            "level1_threats": self.level1_threats,
            "level2_result": self.level2_result,
            "scan_time": self.scan_time,
        }

    def __repr__(self) -> str:
        if self.final_result == self.SAFE:
            return f"Scan Result: {self.SAFE} (Level 1: CLEAN)"
        elif self.final_result == self.BLOCKED:
            return f"Scan Result: {self.BLOCKED} ({len(self.level1_threats)} CRITICAL threats)"
        else:
            return f"Scan Result: {self.WARNING} (requires Level 2 review)"


class SecurityScanner:
    """Wrapper for ai-factory security-scan.py"""

    SCANNER_URL = "https://raw.githubusercontent.com/github/ai-factory/main/skills/aif-skill-generator/scripts/security-scan.py"
    CACHE_DIR = Path(user_cache_dir("specify-cli", "speckit"))
    SCANNER_PATH = CACHE_DIR / "security-scan.py"

    def __init__(self, force_download: bool = False):
        """Initialize security scanner

        Args:
            force_download: Force re-download of scanner script
        """
        self.SCANNER_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.force_download = force_download

    def _ensure_scanner(self) -> Path:
        """Ensure scanner script is downloaded

        Returns:
            Path to scanner script
        """
        if self.SCANNER_PATH.exists() and not self.force_download:
            return self.SCANNER_PATH

        # Download scanner
        import urllib.request

        try:
            print(f"Downloading security scanner from {self.SCANNER_URL}...")
            urllib.request.urlretrieve(self.SCANNER_URL, self.SCANNER_PATH)
            print(f"Downloaded to {self.SCANNER_PATH}")
            return self.SCANNER_PATH
        except Exception as e:
            raise RuntimeError(
                f"Failed to download security scanner: {e}\n"
                f"Please download manually from {self.SCANNER_URL} to {self.SCANNER_PATH}"
            )

    def scan_skill(
        self,
        skill_path: Path,
        stated_goal: Optional[str] = None
    ) -> SecurityScanResult:
        """Scan a skill directory for security threats

        Args:
            skill_path: Path to skill directory
            stated_goal: Stated goal of the skill (for Level 2 review)

        Returns:
            SecurityScanResult with final result (SAFE/BLOCKED/WARNING)
        """
        scanner_path = self._ensure_scanner()

        # Run scanner (Level 1)
        start_time = datetime.now()

        try:
            result = subprocess.run(
                ["python", str(scanner_path), str(skill_path)],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return SecurityScanResult(
                final_result=SecurityScanResult.WARNING,
                level1_threats=[],
                level2_result="Scanner timeout",
            )
        except FileNotFoundError:
            return SecurityScanResult(
                final_result=SecurityScanResult.WARNING,
                level1_threats=[],
                level2_result="Python not found",
            )

        scan_time = (datetime.now() - start_time).total_seconds()

        # Parse exit code
        if result.returncode == 0:
            # CLEAN (SAFE)
            return SecurityScanResult(
                final_result=SecurityScanResult.SAFE,
                level1_threats=[],
                scan_time=scan_time,
            )
        elif result.returncode == 1:
            # BLOCKED (CRITICAL threats)
            threats = self._parse_threats(result.stdout, result.stderr)
            return SecurityScanResult(
                final_result=SecurityScanResult.BLOCKED,
                level1_threats=threats,
                scan_time=scan_time,
            )
        elif result.returncode == 2:
            # WARNINGS (requires Level 2)
            threats = self._parse_threats(result.stdout, result.stderr)
            return SecurityScanResult(
                final_result=SecurityScanResult.WARNING,
                level1_threats=threats,
                scan_time=scan_time,
            )
        else:
            # Unknown error
            return SecurityScanResult(
                final_result=SecurityScanResult.WARNING,
                level1_threats=[],
                level2_result=f"Scanner error: {result.returncode}",
                scan_time=scan_time,
            )

    def scan_agent(
        self,
        agent_path: Path,
        stated_goal: Optional[str] = None
    ) -> SecurityScanResult:
        """Scan an agent directory for security threats

        Args:
            agent_path: Path to agent directory
            stated_goal: Stated goal of the agent (for Level 2 review)

        Returns:
            SecurityScanResult with final result (SAFE/BLOCKED/WARNING)
        """
        # Same as skill scan
        return self.scan_skill(agent_path, stated_goal)

    def _parse_threats(self, stdout: str, stderr: str) -> list:
        """Parse threats from scanner output

        Args:
            stdout: Stdout from scanner
            stderr: Stderr from scanner

        Returns:
            List of threat dicts
        """
        threats = []

        # Try JSON parsing
        try:
            data = json.loads(stdout)
            if "threats" in data:
                threats = data["threats"]
        except json.JSONDecodeError:
            # Fallback: parse line by line
            for line in (stdout + stderr).split("\n"):
                if "[CRITICAL]" in line or "[WARNING]" in line:
                    threats.append({"message": line.strip()})

        return threats
