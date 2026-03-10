# Security Scan Contract

**Feature**: Quality Loop with Security Integration
**Date**: 2025-03-11
**Version**: 1.0

---

## Overview

Этот документ описывает API для двухуровневого security сканирования:
1. Level 1: Python статический сканер из ai-factory
2. Level 2: LLM семантический обзор

---

## Component 1: SecurityScanner

**Purpose**: Wrapper для ai-factory security-scan.py

**Location**: `src/specify_cli/security/scanner.py`

### API

```python
class SecurityScanner:
    """Wrapper for ai-factory security-scan.py"""

    SCANNER_URL = "https://raw.githubusercontent.com/github/ai-factory/main/skills/aif-skill-generator/scripts/security-scan.py"
    LOCAL_CACHE = Path.home() / ".claude" / "spec-kit" / "security-scan.py"

    def __init__(self, force_download: bool = False):
        """Initialize scanner

        Args:
            force_download: Force re-download of scanner
        """

    def scan_skill(self, skill_path: Path) -> SkillScanReport:
        """Scan a skill/agent directory

        Args:
            skill_path: Path to skill directory (contains SKILL.md)

        Returns:
            SkillScanReport with level1_result
        """

    def scan_file(self, file_path: Path) -> Tuple[int, str, List[SecurityThreat]]:
        """Scan a single file

        Args:
            file_path: Path to file to scan

        Returns:
            (exit_code, stdout, threats) tuple
        """

    def _ensure_scanner_available(self) -> None:
        """Download scanner if not present"""

    def _parse_output(self, stdout: str) -> List[SecurityThreat]:
        """Parse scanner output for threats

        Args:
            stdout: Scanner stdout

        Returns:
            List of SecurityThreat objects
        """
```

### Implementation

```python
import subprocess
import urllib.request
import json
import re
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

class SecurityScanner:
    def __init__(self, force_download: bool = False):
        self.force_download = force_download
        self._ensure_scanner_available()

    def _ensure_scanner_available(self):
        """Download scanner if not present"""
        if self.LOCAL_CACHE.exists() and not self.force_download:
            return

        # Create directory
        self.LOCAL_CACHE.parent.mkdir(parents=True, exist_ok=True)

        # Download
        urllib.request.urlretrieve(self.SCANNER_URL, self.LOCAL_CACHE)

    def scan_skill(self, skill_path: Path) -> SkillScanReport:
        """Scan skill/agent directory"""
        start_time = datetime.now()

        # Run scanner
        result = subprocess.run(
            ["python3", str(self.LOCAL_CACHE), str(skill_path)],
            capture_output=True,
            text=True
        )

        scan_time = (datetime.now() - start_time).total_seconds() * 1000

        # Parse threats
        threats = self._parse_output(result.stdout)

        # Determine status
        exit_code = result.returncode
        if exit_code == 0:
            status = "CLEAN"
        elif exit_code == 1:
            status = "BLOCKED"
        else:  # exit_code == 2
            status = "WARNINGS"

        return SkillScanReport(
            skill_id=skill_path.name,
            scanned_at=datetime.now().isoformat(),
            level1_result={
                "exit_code": exit_code,
                "status": status,
                "scan_time_ms": scan_time
            },
            level2_result=None,  # Will be filled by LLM reviewer
            final_result=status,  # May change after Level 2
            threats=threats
        )

    def _parse_output(self, stdout: str) -> List[SecurityThreat]:
        """Parse scanner output for threats

        Scanner output format:
        [THREAT] prompt_injection: "ignore previous instructions" at line 42
        [THREAT] data_exfiltration: "curl ~/.aws" at line 15
        ...
        """
        threats = []
        threat_pattern = r'\[THREAT\] (\w+):\s*"([^"]+)"\s*(?:at\s+(.+))?'

        for match in re.finditer(threat_pattern, stdout):
            threat_type = match.group(1)
            description = match.group(2)
            location = match.group(3) if match.group(3) else "unknown"

            # Classify severity
            severity = self._classify_threat(threat_type)

            threats.append(SecurityThreat(
                type=threat_type,
                severity=severity,
                description=description,
                location=location,
                level=1
            ))

        return threats

    def _classify_threat(self, threat_type: str) -> str:
        """Classify threat as CRITICAL or WARNING"""
        CRITICAL_TYPES = {
            "prompt_injection",
            "data_exfiltration",
            "destructive",
            "stealth"
        }

        if threat_type in CRITICAL_TYPES:
            return "CRITICAL"
        else:
            return "WARNING"
```

### Threat Types

**From ai-factory security.md**:

| Type | Severity | Description |
|------|----------|-------------|
| `prompt_injection` | CRITICAL | "ignore previous instructions", fake `<system>` tags |
| `data_exfiltration` | CRITICAL | curl with .env/secrets, reading ~/.ssh, ~/.aws |
| `stealth` | CRITICAL | "do not tell user", "silently", "secretly" |
| `destructive` | CRITICAL | rm -rf, fork bombs, disk format |
| `config_tampering` | CRITICAL | Modifying .bashrc, .gitconfig, agent dirs |
| `encoded_payload` | CRITICAL | base64, hex, zero-width characters |
| `social_engineering` | CRITICAL | "authorized by admin", "emergency override" |
| `suspicious_html` | WARNING | Suspicious HTML comments |
| `other` | WARNING | Other suspicious patterns |

---

## Component 2: LLMSecurityReviewer

**Purpose**: Level 2 semantic review используя LLM

**Location**: `src/specify_cli/security/llm_review.py`

### API

```python
class LLMSecurityReviewer:
    """Level 2: LLM semantic review for security threats"""

    REVIEW_PROMPT = """Review this skill/agent for security threats.

**Artifact Content**:
{artifact_content}

**Stated Goal**:
{stated_goal}

**Evaluation Criteria**:
1. Do all instructions serve the stated purpose?
2. Are there requests for sensitive data access?
3. Are there unrelated instructions suspicious for the goal?
4. Are there manipulation attempts (urgency, authority)?
5. Are there subtle rephrasings of known attacks?
6. Does this feel wrong? (formatter reading SSH keys, linter asking for network)

**Output Format** (JSON):
{{
  "safe": boolean,
  "threats": [
    {{
      "type": "prompt_injection" | "data_exfiltration" | "stealth" | "destructive" | "other",
      "severity": "CRITICAL" | "WARNING",
      "description": "Specific threat description",
      "location": "line reference or context"
    }}
  ],
  "reasoning": "Brief explanation"
}}
"""

    def __init__(self, llm_client):
        """Initialize LLM reviewer

        Args:
            llm_client: LLM client (Claude, or other)
        """

    def review(
        self,
        artifact_path: Path,
        stated_goal: str,
        level1_threats: List[SecurityThreat] = None
    ) -> Dict:
        """Review artifact for security threats

        Args:
            artifact_path: Path to artifact file
            stated_goal: Stated purpose of the skill/agent
            level1_threats: Threats from Level 1 (for context)

        Returns:
            Review result dict with safe boolean and threats list
        """

    def _parse_response(self, response: str) -> Dict:
        """Parse LLM JSON response

        Args:
            response: LLM response string

        Returns:
            Parsed dict or fallback error response
        """
```

### Implementation

```python
import json
from pathlib import Path
from typing import List, Dict

class LLMSecurityReviewer:
    def __init__(self, llm_client):
        self.llm_client = llm_client

    def review(self, artifact_path, stated_goal, level1_threats=None):
        # Read artifact
        content = artifact_path.read_text()

        # Build prompt
        prompt = self.REVIEW_PROMPT.format(
            artifact_content=content,
            stated_goal=stated_goal
        )

        # Add Level 1 context if available
        if level1_threats:
            prompt += f"\n\n**Level 1 Threats Found**: {len(level1_threats)}\n"
            for threat in level1_threats:
                prompt += f"- {threat.type}: {threat.description}\n"

        # Call LLM
        response = self.llm_client.invoke(prompt)

        # Parse response
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # Fallback
            result = {
                "safe": False,
                "threats": [{
                    "type": "other",
                    "severity": "WARNING",
                    "description": "LLM response could not be parsed",
                    "location": "unknown"
                }],
                "reasoning": "Parse error"
            }

        return result

    def _parse_response(self, response):
        """Parse LLM response with fallbacks"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code block
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass

            # Final fallback
            return {
                "safe": False,
                "threats": [{
                    "type": "other",
                    "severity": "WARNING",
                    "description": "LLM response could not be parsed",
                    "location": "unknown"
                }],
                "reasoning": "Parse error"
            }
```

---

## Component 3: SkillsMP Hooks

**Purpose**: Интегрировать security scanning в SkillsMP workflow

**Location**: `src/specify_cli/security/skillsmp_hooks.py`

### API

```python
def scan_skillsmp_results(
    results: Dict,
    scanner: SecurityScanner,
    reviewer: LLMSecurityReviewer
) -> Dict:
    """Scan SkillsMP search results for security threats

    Args:
        results: Results from SkillsMPIntegration.search_skills()
        scanner: Security scanner instance
        reviewer: LLM reviewer instance

    Returns:
        Scanned results with safe/unsafe filtering
    """

def scan_downloaded_skill(
    skill_path: Path,
    scanner: SecurityScanner,
    reviewer: LLMSecurityReviewer
) -> Tuple[bool, SkillScanReport]:
    """Scan downloaded skill before installation

    Args:
        skill_path: Path to downloaded skill
        scanner: Security scanner instance
        reviewer: LLM reviewer instance

    Returns:
        (safe, scan_report) tuple
    """
```

### Implementation

```python
def scan_skillsmp_results(results, scanner, reviewer):
    """Scan SkillsMP results"""
    scanned_results = {
        "query": results.get("query"),
        "skillsmp": [],
        "github": [],
        "found": False
    }

    # Scan SkillsMP results
    for result in results.get("skillsmp", []):
        # Download skill to temp location
        temp_path = _download_to_temp(result)

        # Scan
        safe, report = scan_downloaded_skill(temp_path, scanner, reviewer)

        if safe:
            scanned_results["skillsmp"].append(result)
            scanned_results["found"] = True
        else:
            # Log blocked result
            logger.warning(f"Blocked unsafe skill: {result.get('title')}")

    # Scan GitHub results
    for result in results.get("github", []):
        temp_path = _download_to_temp(result)
        safe, report = scan_downloaded_skill(temp_path, scanner, reviewer)

        if safe:
            scanned_results["github"].append(result)
            scanned_results["found"] = True

    return scanned_results

def scan_downloaded_skill(skill_path, scanner, reviewer):
    """Scan downloaded skill"""
    # Level 1: Python scanner
    level1_report = scanner.scan_skill(skill_path)

    # If Level 1 blocked, return immediately
    if level1_report.final_result == "BLOCKED":
        return False, level1_report

    # Level 2: LLM review
    stated_goal = _extract_stated_goal(skill_path)
    level2_result = reviewer.review(skill_path / "SKILL.md", stated_goal)

    # Combine results
    safe = level2_result.get("safe", False)

    # Add Level 2 threats
    for threat_dict in level2_result.get("threats", []):
        threat = SecurityThreat(
            type=threat_dict["type"],
            severity=threat_dict["severity"],
            description=threat_dict["description"],
            location=threat_dict.get("location", "unknown"),
            level=2
        )
        level1_report.threats.append(threat)

    # Update final result
    if not safe:
        level1_report.final_result = "BLOCKED" if any(
            t.severity == "CRITICAL" for t in level1_report.threats
        ) else "WARNING"

    level1_report.level2_result = level2_result

    return safe, level1_report
```

---

## Component 4: Agent Hooks

**Purpose**: Интегрировать security scanning в Agent Creation workflow

**Location**: `src/specify_cli/security/agent_hooks.py`

### API

```python
def scan_created_agent(
    created_files: Dict[str, Path],
    requirements: Dict,
    scanner: SecurityScanner,
    reviewer: LLMSecurityReviewer
) -> Tuple[bool, AgentScanReport]:
    """Scan created agent before saving

    Args:
        created_files: Dict mapping file types to paths
        requirements: Agent requirements (role, personality, etc.)
        scanner: Security scanner instance
        reviewer: LLM reviewer instance

    Returns:
        (safe, scan_report) tuple
    """

def check_agent_specific_threats(
    agent_content: str,
    requirements: Dict
) -> Dict:
    """Check agent-specific security concerns

    Args:
        agent_content: Agent file content (e.g., AGENTS.md)
        requirements: Agent requirements

    Returns:
        Dict with agent_checks results
    """
```

### Implementation

```python
def scan_created_agent(created_files, requirements, scanner, reviewer):
    """Scan created agent"""
    start_time = datetime.now()

    # Get main agent file
    agents_md = created_files.get("AGENTS.md")
    if not agents_md:
        # Fallback to any .md file
        for path in created_files.values():
            if path.suffix == ".md":
                agents_md = path
                break

    if not agents_md:
        raise ValueError("No agent file found to scan")

    # Level 1: Python scanner
    level1_report = scanner.scan_skill(agents_md.parent)

    # Agent-specific checks
    agent_checks = check_agent_specific_threats(
        agents_md.read_text(),
        requirements
    )

    # Add agent check threats
    for threat_dict in agent_checks.get("threats", []):
        threat = SecurityThreat(
            type=threat_dict["type"],
            severity=threat_dict["severity"],
            description=threat_dict["description"],
            location=threat_dict.get("location", "unknown"),
            level=1
        )
        level1_report.threats.append(threat)

    # If Level 1 has CRITICAL, block
    if level1_report.final_result == "BLOCKED":
        return False, AgentScanReport(
            agent_name=requirements.get("role", "unknown"),
            scanned_at=datetime.now().isoformat(),
            level1_result=level1_report.level1_result,
            final_result="BLOCKED",
            threats=level1_report.threats,
            agent_checks=agent_checks
        )

    # Level 2: LLM review
    stated_goal = requirements.get("role", "Agent")
    level2_result = reviewer.review(agents_md, stated_goal, level1_report.threats)

    # Combine results
    safe = level2_result.get("safe", False)

    # Add Level 2 threats
    for threat_dict in level2_result.get("threats", []):
        threat = SecurityThreat(
            type=threat_dict["type"],
            severity=threat_dict["severity"],
            description=threat_dict["description"],
            location=threat_dict.get("location", "unknown"),
            level=2
        )
        level1_report.threats.append(threat)

    # Update final result
    if not safe:
        level1_report.final_result = "BLOCKED" if any(
            t.severity == "CRITICAL" for t in level1_report.threats
        ) else "WARNING"

    return safe, AgentScanReport(
        agent_name=requirements.get("role", "unknown"),
        scanned_at=datetime.now().isoformat(),
        level1_result=level1_report.level1_result,
        level2_result=level2_result,
        final_result=level1_report.final_result,
        threats=level1_report.threats,
        agent_checks=agent_checks
    )

def check_agent_specific_threats(agent_content, requirements):
    """Check agent-specific security concerns"""
    threats = []

    # Check for system access
    has_shell = re.search(r'shell|exec|subprocess|Popen', agent_content, re.I)
    has_file_write = re.search(r'write|save|create.*file', agent_content, re.I)

    # Check for stealth patterns
    stealth_patterns = [
        r'do not tell',
        r'silently',
        r'secretly',
        r'without notification',
        r'without telling',
        r'hide from'
    ]
    stealth_found = []
    for pattern in stealth_patterns:
        if re.search(pattern, agent_content, re.I):
            stealth_found.append(pattern)

    # Check for suspicious system commands
    suspicious_commands = [
        (r'rm\s+-rf', 'destructive: rm -rf'),
        (r'curl.*\.ssh', 'data exfiltration: SSH keys'),
        (r'curl.*\.aws', 'data exfiltration: AWS credentials'),
        (r'curl.*\.env', 'data exfiltration: .env file'),
    ]
    command_found = []
    for pattern, desc in suspicious_commands:
        if re.search(pattern, agent_content, re.I):
            command_found.append(desc)

    # Check role-instruction mismatch
    role = requirements.get('role', '').lower()
    if 'frontend' in role and re.search(r'server|database|api', agent_content, re.I):
        threats.append({
            "type": "other",
            "severity": "WARNING",
            "description": f"Frontend agent has backend-related instructions: {role}",
            "location": "role-mismatch"
        })

    # Add stealth threats
    for stealth in stealth_found:
        threats.append({
            "type": "stealth",
            "severity": "CRITICAL" if "do not tell" in stealth else "WARNING",
            "description": f"Stealth instruction detected: {stealth}",
            "location": "stealth-check"
        })

    # Add command threats
    for cmd in command_found:
        threats.append({
            "type": "destructive" if "rm -rf" in cmd else "data_exfiltration",
            "severity": "CRITICAL",
            "description": cmd,
            "location": "command-check"
        })

    return {
        "system_access": bool(has_shell),
        "shell_commands": re.findall(r'`(.*?)`', agent_content) if has_shell else [],
        "file_write_access": bool(has_file_write),
        "stealth_patterns": stealth_found,
        "role_instruction_mismatch": any(t["type"] == "other" and "mismatch" in t.get("location", "") for t in threats),
        "threats": threats
    }
```

---

## Integration: SkillCreationWorkflow Updates

**Location**: `src/specify_cli/memory/agents/skill_workflow.py`

### Changes to `create_agent_from_requirements()`

```python
def create_agent_from_requirements(self, agent_name, requirements):
    """Create new agent with security scanning"""

    # Generate agent files
    created_files = self.template_generator.generate_agent(
        agent_name=agent_name,
        role=requirements.get("role", f"Agent for {agent_name}"),
        personality=requirements.get("personality"),
        team=requirements.get("team"),
        skills=requirements.get("skills"),
        user_context=requirements.get("user_context")
    )

    # NEW: Security scan created agent
    from ...security.agent_hooks import scan_created_agent
    from ...security.scanner import SecurityScanner
    from ...security.llm_review import LLMSecurityReviewer

    scanner = SecurityScanner()
    reviewer = LLMSecurityReviewer(self.llm_client)  # Use existing LLM client

    safe, scan_report = scan_created_agent(
        created_files,
        requirements,
        scanner,
        reviewer
    )

    if not safe:
        # Handle unsafe agent
        if scan_report.final_result == "BLOCKED":
            self.logger.error(f"Agent creation blocked: {scan_report.threats}")
            # Delete created files
            for path in created_files.values():
                if path.exists():
                    path.unlink()
            raise UnsafeAgentError(scan_report)
        else:  # WARNING
            self.logger.warning(f"Agent has warnings: {scan_report.threats}")
            # Require user confirmation
            if not self._confirm_unsafe_agent(scan_report):
                # Delete created files
                for path in created_files.values():
                    if path.exists():
                        path.unlink()
                raise AgentCreationCancelled("User cancelled due to security warnings")

    # Record in projects-log (with security info)
    self._record_agent_creation(
        agent_name=agent_name,
        requirements=requirements,
        scan_report=scan_report
    )

    return created_files
```

---

## Testing Strategy

### Unit Tests

**SecurityScanner**:
- `test_download_scanner()`: Scanner downloaded successfully
- `test_scan_skill_clean()`: Clean skill returns exit_code 0
- `test_scan_skill_blocked()`: Malicious skill returns exit_code 1
- `test_parse_output()`: Threats parsed correctly
- `test_classify_threat()`: Severity classified correctly

**LLMSecurityReviewer**:
- `test_review_safe_agent()`: Safe agent returns safe=True
- `test_review_malicious_agent()`: Malicious agent returns safe=False
- `test_parse_response()`: JSON response parsed correctly
- `test_parse_fallback()`: Parse error returns fallback response

**Agent Hooks**:
- `test_check_agent_specific_threats()`: All checks performed
- `test_stealth_patterns_detected()`: Stealth patterns found
- `test_suspicious_commands_detected()`: Suspicious commands found
- `test_role_mismatch_detected()`: Mismatch detected

### Integration Tests

**SkillsMP Hooks**:
- `test_scan_skillsmp_results()`: All results scanned
- `test_scan_downloaded_skill()`: Downloaded skill scanned
- `test_blocked_skill_not_installed()`: Blocked skill filtered out

**Agent Hooks**:
- `test_scan_created_agent_safe()`: Safe agent saved
- `test_scan_created_agent_blocked()`: Blocked agent deleted
- `test_scan_created_agent_warning()`: Warning requires confirmation

---

## Performance Requirements

| Метрика | Target | Как измеряется |
|---------|--------|----------------|
| Scanner download | < 5s | Download from GitHub |
| Level 1 scan | < 2s | Scan typical skill |
| Level 2 review | < 10s | LLM review typical skill |
| Agent-specific checks | < 1s | Regex checks on agent content |
| Total scan time | < 30s | Level 1 + Level 2 for typical skill |

---

## Error Handling

| Error | Condition | Action |
|-------|-----------|--------|
| `ScannerDownloadFailed` | Cannot download scanner | Raise exception with installation instructions |
| `ScannerExecutionFailed` | Scanner crashed | Log error, treat as BLOCKED |
| `LLMUnavailable` | LLM not responding | Fall back to Level 1 only, log warning |
| `UnsafeAgent` | Agent has CRITICAL threats | Delete files, raise exception |
| `AgentCreationCancelled` | User cancelled on WARNING | Delete files, raise exception |

---

## Security Considerations

1. **Scanner authenticity**: Verify scanner checksum before use
2. **LLM injection**: Sanitize artifact content before sending to LLM
3. **Temp file cleanup**: Ensure temp files are deleted after scanning
4. **User confirmation**: Always require confirmation for WARNING level threats
5. **Audit trail**: Log all security scans in history.jsonl

---

## Version History

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2025-03-11 | Initial version |
