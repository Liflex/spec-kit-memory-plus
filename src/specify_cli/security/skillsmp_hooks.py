"""
SkillsMP Security Hooks

Integration points for security scanning when downloading skills from SkillsMP.
"""

from pathlib import Path
from typing import Dict, Any, List
from .scanner import SecurityScanner, SecurityScanResult
from .llm_review import LLMSecurityReviewer


class UnsafeSkillError(Exception):
    """Raised when a skill is deemed unsafe"""
    def __init__(self, scan_report: SecurityScanResult):
        self.scan_report = scan_report
        super().__init__(
            f"Skill blocked by security scan: {scan_report.final_result}\n"
            f"Threats: {scan_report.level1_threats}"
        )


def scan_skillsmp_results(
    results: List[Dict[str, Any]],
    scanner: SecurityScanner,
    reviewer: LLMSecurityReviewer
) -> List[Dict[str, Any]]:
    """Scan all skills from SkillsMP search results

    Args:
        results: List of skill results from SkillsMP
        scanner: Security scanner instance
        reviewer: LLM security reviewer

    Returns:
        Filtered list of safe skills only
    """
    safe_results = []

    for skill in results:
        skill_id = skill.get("id", "unknown")
        skill_path = skill.get("local_path")  # If already downloaded

        if not skill_path:
            # Haven't downloaded yet, skip scanning (will scan on download)
            safe_results.append(skill)
            continue

        # Scan the skill
        scan_result = scanner.scan_skill(Path(skill_path))

        # Level 2 review if WARNING
        if scan_result.final_result == SecurityScanResult.WARNING:
            level2 = reviewer.review(
                skill_path=Path(skill_path),
                stated_goal=skill.get("description", ""),
                level1_result="WARNING"
            )

            if not level2["safe"]:
                # Block unsafe skills
                print(f"⚠️ Skill '{skill_id}' blocked by Level 2 review: {level2['reason']}")
                continue

        elif scan_result.final_result == SecurityScanResult.BLOCKED:
            # Block malicious skills
            print(f"🚫 Skill '{skill_id}' blocked by Level 1 scan: {scan_result.level1_threats}")
            continue

        # Safe skill
        safe_results.append(skill)

    return safe_results


def scan_downloaded_skill(
    skill_path: Path,
    skill_name: str,
    scanner: SecurityScanner,
    reviewer: LLMSecurityReviewer,
    stated_goal: str = ""
) -> bool:
    """Scan a downloaded skill before installation

    Args:
        skill_path: Path to downloaded skill directory
        skill_name: Name of the skill
        scanner: Security scanner instance
        reviewer: LLM security reviewer
        stated_goal: Stated goal of the skill

    Returns:
        True if safe, raises UnsafeSkillError if blocked

    Raises:
        UnsafeSkillError: If skill is deemed unsafe
    """
    print(f"🔍 Scanning skill '{skill_name}' for security threats...")

    # Level 1 scan
    scan_result = scanner.scan_skill(skill_path, stated_goal)

    if scan_result.final_result == SecurityScanResult.SAFE:
        print(f"✅ Skill '{skill_name}' is safe (Level 1: CLEAN)")
        return True

    elif scan_result.final_result == SecurityScanResult.BLOCKED:
        print(f"🚫 Skill '{skill_name}' BLOCKED by Level 1 scan:")
        for threat in scan_result.level1_threats:
            print(f"   - {threat.get('message', threat)}")
        raise UnsafeSkillError(scan_result)

    else:  # WARNING
        print(f"⚠️ Skill '{skill_name}' requires Level 2 review...")
        print(f"   Level 1 warnings: {len(scan_result.level1_threats)}")

        # Level 2 review
        level2_result = reviewer.review(
            skill_path=skill_path,
            stated_goal=stated_goal,
            level1_result="WARNING"
        )

        if not level2_result["safe"]:
            print(f"🚫 Skill '{skill_name}' BLOCKED by Level 2 review:")
            print(f"   Reason: {level2_result['reason']}")
            raise UnsafeSkillError(scan_result)

        print(f"✅ Skill '{skill_name}' approved by Level 2 review")
        return True
