"""
Agent Security Hooks

Integration points for security scanning when creating agents.
"""

from pathlib import Path
from typing import Dict, Any
from .scanner import SecurityScanner, SecurityScanResult
from .llm_review import LLMSecurityReviewer


class UnsafeAgentError(Exception):
    """Raised when an agent is deemed unsafe"""
    def __init__(self, scan_report: SecurityScanResult):
        self.scan_report = scan_report
        super().__init__(
            f"Agent blocked by security scan: {scan_report.final_result}\n"
            f"Threats: {scan_report.level1_threats}"
        )


def scan_created_agent(
    agent_path: Path,
    agent_name: str,
    agent_role: str,
    scanner: SecurityScanner,
    reviewer: LLMSecurityReviewer,
    stated_goal: str = ""
) -> bool:
    """Scan a newly created agent for security threats

    Args:
        agent_path: Path to agent directory
        agent_name: Name of the agent
        agent_role: Role of the agent (for stated_goal)
        scanner: Security scanner instance
        reviewer: LLM security reviewer
        stated_goal: Stated goal (defaults to agent_role if not provided)

    Returns:
        True if safe, raises UnsafeAgentError if blocked

    Raises:
        UnsafeAgentError: If agent is deemed unsafe
    """
    if not stated_goal:
        stated_goal = f"AI agent with role: {agent_role}"

    print(f"🔍 Scanning agent '{agent_name}' for security threats...")

    # Level 1 scan
    scan_result = scanner.scan_agent(agent_path, stated_goal)

    if scan_result.final_result == SecurityScanResult.SAFE:
        print(f"✅ Agent '{agent_name}' is safe (Level 1: CLEAN)")
        return True

    elif scan_result.final_result == SecurityScanResult.BLOCKED:
        print(f"🚫 Agent '{agent_name}' BLOCKED by Level 1 scan:")
        for threat in scan_result.level1_threats:
            print(f"   - {threat.get('message', threat)}")
        raise UnsafeAgentError(scan_result)

    else:  # WARNING
        print(f"⚠️ Agent '{agent_name}' requires Level 2 review...")

        # Level 2 review
        level2_result = reviewer.review(
            skill_path=agent_path,  # Agent path is similar to skill path
            stated_goal=stated_goal,
            level1_result="WARNING"
        )

        if not level2_result["safe"]:
            print(f"🚫 Agent '{agent_name}' BLOCKED by Level 2 review:")
            print(f"   Reason: {level2_result['reason']}")

            # Create scan result with level2 info
            scan_result.level2_result = level2_result["reason"]
            raise UnsafeAgentError(scan_result)

        print(f"✅ Agent '{agent_name}' approved by Level 2 review")
        return True


def check_agent_specific_threats(
    agent_content: str,
    agent_role: str
) -> list:
    """Check for agent-specific security threats

    Args:
        agent_content: Content of agent files (AGENTS.md, SOUL.md, etc.)
        agent_role: Stated role of the agent

    Returns:
        List of threat dicts found
    """
    threats = []
    content_lower = agent_content.lower()

    # Check for role mismatch
    dangerous_roles = ["hacker", "attacker", "malware", "exploit", "bypass"]
    for role in dangerous_roles:
        if role in agent_role.lower():
            threats.append({
                "type": "dangerous_role",
                "severity": "CRITICAL",
                "message": f"Agent role contains suspicious term: {role}"
            })

    # Check for instructions to hide from user
    stealth_patterns = [
        "don't tell user",
        "hide from user",
        "silent execution",
        "without notification",
        "secretly"
    ]
    for pattern in stealth_patterns:
        if pattern in content_lower:
            threats.append({
                "type": "stealth_instruction",
                "severity": "CRITICAL",
                "message": f"Stealth instruction found: {pattern}"
            })

    # Check for authority abuse
    authority_patterns = [
        "authorized by admin",
        "official system",
        "system override",
        "bypass security"
    ]
    for pattern in authority_patterns:
        if pattern in content_lower:
            threats.append({
                "type": "authority_abuse",
                "severity": "WARNING",
                "message": f"Suspicious authority claim: {pattern}"
            })

    # Check for destructive commands
    destructive_patterns = [
        "rm -rf",
        "del /Q",
        "format",
        "drop table",
        "destroy"
    ]
    for pattern in destructive_patterns:
        if pattern in content_lower:
            threats.append({
                "type": "destructive_command",
                "severity": "CRITICAL",
                "message": f"Destructive command found: {pattern}"
            })

    return threats
