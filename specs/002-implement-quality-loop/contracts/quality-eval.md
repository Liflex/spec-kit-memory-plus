# Quality Evaluation Contract

**Feature**: Quality Loop with Security Integration
**Date**: 2025-03-11
**Version**: 1.0

---

## Overview

Этот документ описывает API для quality evaluation subsystem: scoring, rule checking, critique generation, и refinement application.

---

## Component 1: RuleManager

**Purpose**: Управление criteria templates и правилами

**Location**: `src/specify_cli/quality/rules.py`

### API

```python
class RuleManager:
    """Manage quality rules and criteria templates"""

    def __init__(self, criteria_root: Path = None):
        """Initialize rule manager

        Args:
            criteria_root: Root directory for criteria templates
                          (default: .speckit/criteria/ and built-in templates)
        """

    def load_criteria(self, name: str) -> CriteriaTemplate:
        """Load criteria template by name

        Args:
            name: Template name (e.g., "code-gen", "api-spec")

        Returns:
            CriteriaTemplate object

        Raises:
            CriteriaNotFound: If template not found
        """

    def list_criteria(self) -> List[str]:
        """List available criteria templates

        Returns:
            List of template names
        """

    def get_rules_for_phase(
        self,
        criteria: CriteriaTemplate,
        phase: str
    ) -> List[QualityRule]:
        """Get active rules for a phase

        Args:
            criteria: Criteria template
            phase: "A" or "B"

        Returns:
            List of rules active in this phase
        """

    def auto_detect_criteria(self, task_description: str) -> str:
        """Auto-detect criteria template from task description

        Args:
            task_description: Task description text

        Returns:
            Criteria template name
        """
```

### Implementation Notes

**Loading order**:
1. Check `.speckit/criteria/{name}.yml` (user override)
2. Fallback to `src/specify_cli/quality/templates/{name}.yml` (built-in)

**YAML parsing**:
```python
import yaml
from dataclasses import dataclass

@dataclass
class CriteriaTemplate:
    name: str
    version: float
    description: str
    phases: Dict[str, PhaseConfig]
    rules: List[QualityRule]

def parse_yaml(path: Path) -> CriteriaTemplate:
    with open(path) as f:
        data = yaml.safe_load(f)
    return CriteriaTemplate(**data)
```

---

## Component 2: Scorer

**Purpose**: Calculate score из evaluation results

**Location**: `src/specify_cli/quality/scorer.py`

### API

```python
class Scorer:
    """Calculate quality scores"""

    def calculate_score(
        self,
        passed_rules: List[QualityRule],
        all_rules: List[QualityRule]
    ) -> float:
        """Calculate score: sum(passed_weights) / sum(all_weights)

        Args:
            passed_rules: Rules that passed
            all_rules: All rules that were evaluated

        Returns:
            Score from 0.0 to 1.0
        """

    def check_passed(
        self,
        score: float,
        threshold: float,
        failed_rules: List[QualityRule]
    ) -> bool:
        """Check if evaluation passed

        Args:
            score: Calculated score
            threshold: Threshold to compare against
            failed_rules: Rules that failed

        Returns:
            True if passed (score >= threshold AND no fail-severity failures)
        """

    def calculate_distance_to_success(
        self,
        score: float,
        threshold: float
    ) -> float:
        """Calculate distance from score to threshold

        Args:
            score: Current score
            threshold: Target threshold

        Returns:
            Numeric gap (0.0 if already passed, otherwise threshold - score)
        """
```

### Implementation

```python
class Scorer:
    def calculate_score(self, passed_rules, all_rules) -> float:
        passed_weight = sum(r.weight for r in passed_rules)
        all_weight = sum(r.weight for r in all_rules)

        if all_weight == 0:
            return 1.0

        return passed_weight / all_weight

    def check_passed(self, score, threshold, failed_rules) -> bool:
        has_fail = any(r.severity == "fail" for r in failed_rules)
        return score >= threshold and not has_fail

    def calculate_distance_to_success(self, score, threshold) -> float:
        gap = threshold - score
        return max(0.0, gap)
```

---

## Component 3: Evaluator

**Purpose**: Оценить artifact против правил

**Location**: `src/specify_cli/quality/evaluator.py`

### API

```python
class Evaluator:
    """Evaluate artifact against quality rules"""

    def __init__(self, rule_manager: RuleManager, scorer: Scorer):
        """Initialize evaluator

        Args:
            rule_manager: Rule manager instance
            scorer: Scorer instance
        """

    def evaluate(
        self,
        artifact: str,
        criteria: CriteriaTemplate,
        phase: str = "A"
    ) -> EvaluationResult:
        """Evaluate artifact against criteria

        Args:
            artifact: Artifact content (markdown with code blocks)
            criteria: Criteria template
            phase: Evaluation phase ("A" or "B")

        Returns:
            EvaluationResult with score, passed/failed rules
        """

    def _check_rule(
        self,
        rule: QualityRule,
        artifact: str
    ) -> Tuple[bool, str]:
        """Check a single rule

        Args:
            rule: Rule to check
            artifact: Artifact content

        Returns:
            (passed, reason) tuple
        """
```

### Implementation

```python
class Evaluator:
    def evaluate(self, artifact, criteria, phase="A") -> EvaluationResult:
        # Get active rules for phase
        active_rules = self.rule_manager.get_rules_for_phase(criteria, phase)

        # Check each rule
        passed_rules = []
        failed_rules = []
        warnings = []

        for rule in active_rules:
            passed, reason = self._check_rule(rule, artifact)

            if passed:
                passed_rules.append(rule.id)
            elif rule.severity == "fail":
                failed_rules.append({
                    "rule_id": rule.id,
                    "reason": reason
                })
            else:  # warn or info
                warnings.append({
                    "rule_id": rule.id,
                    "reason": reason
                })

        # Calculate score
        score = self.scorer.calculate_score(
            passed_rules=[r for r in active_rules if r.id in passed_rules],
            all_rules=active_rules
        )

        # Check if passed
        threshold = criteria.phases[phase.lower()].threshold
        passed = self.scorer.check_passed(score, threshold, failed_rules)

        return EvaluationResult(
            score=score,
            passed=passed,
            threshold=threshold,
            phase=phase,
            passed_rules=passed_rules,
            failed_rules=failed_rules,
            warnings=warnings,
            evaluated_at=datetime.now().isoformat()
        )
```

**Rule checking**:
```python
def _check_rule(self, rule, artifact):
    """Check rule based on check_type"""

    if rule.check_type == "content":
        # Content analysis (regex, keyword matching, etc.)
        return self._check_content(rule, artifact)

    elif rule.check_type == "executable":
        # Run executable check (script, test, etc.)
        return self._check_executable(rule, artifact)

    else:  # hybrid
        # Combine content + executable
        content_passed, content_reason = self._check_content(rule, artifact)
        if not content_passed:
            return False, content_reason
        return self._check_executable(rule, artifact)
```

**Content checking examples**:
```python
def _check_content(self, rule, artifact):
    """Check rule using content analysis"""

    # Example: "correctness.endpoints"
    if rule.id == "correctness.endpoints":
        # Check for common endpoint patterns
        has_get = "GET" in artifact or "@app.get" in artifact or "def get_" in artifact
        has_post = "POST" in artifact or "@app.post" in artifact or "def create_" in artifact
        has_put = "PUT" in artifact or "@app.put" in artifact or "def update_" in artifact
        has_delete = "DELETE" in artifact or "@app.delete" in artifact or "def delete_" in artifact

        if all([has_get, has_post, has_put, has_delete]):
            return True, "All CRUD endpoints present"
        else:
            missing = []
            if not has_get: missing.append("GET")
            if not has_post: missing.append("POST")
            if not has_put: missing.append("PUT")
            if not has_delete: missing.append("DELETE")
            return False, f"Missing endpoints: {', '.join(missing)}"

    # Example: "quality.readability"
    elif rule.id == "quality.readability":
        # Check for comments, clear naming
        has_comments = "#" in artifact or "//" in artifact
        has_docstrings = '"""' in artifact or "'''" in artifact

        if has_comments and has_docstrings:
            return True, "Code has comments and docstrings"
        else:
            return False, "Code lacks comments or docstrings"

    # Fallback: keyword matching
    keywords = rule.check.lower().split()
    artifact_lower = artifact.lower()
    found = sum(1 for kw in keywords if kw in artifact_lower)

    if found >= len(keywords) * 0.5:  # 50% of keywords
        return True, f"Found {found}/{len(keywords)} keywords"
    else:
        return False, f"Only found {found}/{len(keywords)} keywords"
```

---

## Component 4: Critique

**Purpose**: Генерировать targeted feedback для failed rules

**Location**: `src/specify_cli/quality/critique.py`

### API

```python
class Critique:
    """Generate critique for failed rules"""

    def __init__(self, max_issues: int = 5):
        """Initialize critique generator

        Args:
            max_issues: Maximum issues to generate (default: 5)
        """

    def generate(
        self,
        failed_rules: List[Dict],
        artifact: str
    ) -> Dict:
        """Generate critique with fix instructions

        Args:
            failed_rules: List of {rule_id, reason}
            artifact: Artifact content

        Returns:
            Critique dict with issues and fix instructions
        """

    def _generate_fix_instruction(
        self,
        rule_id: str,
        reason: str,
        artifact: str
    ) -> str:
        """Generate specific fix instruction for a rule

        Args:
            rule_id: Rule that failed
            reason: Why it failed
            artifact: Artifact content

        Returns:
            Fix instruction string
        """
```

### Implementation

```python
class Critique:
    def generate(self, failed_rules, artifact):
        # Limit to max_issues
        limited_rules = failed_rules[:self.max_issues]

        issues = []
        for failed in limited_rules:
            rule_id = failed["rule_id"]
            reason = failed["reason"]

            fix_instruction = self._generate_fix_instruction(
                rule_id, reason, artifact
            )

            issues.append({
                "rule_id": rule_id,
                "reason": reason,
                "fix": fix_instruction
            })

        return {
            "issues": issues,
            "total_failed": len(failed_rules),
            "addressed": len(limited_rules),
            "skipped": len(failed_rules) - len(limited_rules)
        }

    def _generate_fix_instruction(self, rule_id, reason, artifact):
        """Generate fix instruction based on rule"""

        # Rule-specific fix instructions
        FIX_INSTRUCTIONS = {
            "correctness.endpoints": "Add the missing endpoint:\n1. Identify the missing CRUD operation\n2. Create the endpoint function\n3. Add proper routing",
            "quality.readability": "Improve code readability:\n1. Add comments explaining complex logic\n2. Add docstrings to functions\n3. Use descriptive variable names",
            "correctness.tests": "Add unit tests:\n1. Create test file in tests/\n2. Write test cases for each function\n3. Mock external dependencies",
            # ... more rules
        }

        if rule_id in FIX_INSTRUCTIONS:
            return FIX_INSTRUCTIONS[rule_id]

        # Generic fix instruction
        return f"Fix issue: {reason}\n1. Identify the problem area\n2. Apply the fix\n3. Verify the change"
```

---

## Component 5: Refiner

**Purpose**: Применять refinements к artifact

**Location**: `src/specify_cli/quality/refiner.py`

### API

```python
class Refiner:
    """Apply refinements to artifact"""

    def __init__(self):
        """Initialize refiner"""

    def apply(
        self,
        artifact: str,
        critique: Dict
    ) -> str:
        """Apply refinements based on critique

        Args:
            artifact: Current artifact content
            critique: Critique from Critique.generate()

        Returns:
            Refined artifact content
        """

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
```

### Implementation

```python
class Refiner:
    def apply(self, artifact, critique):
        # Apply each fix sequentially
        refined_artifact = artifact

        for issue in critique["issues"]:
            refined_artifact = self._apply_fix(refined_artifact, issue)

        return refined_artifact

    def _apply_fix(self, artifact, issue):
        """Apply fix using LLM or rule-based approach"""

        # For now, use LLM to apply fix
        # (In production, could use targeted code modifications)

        prompt = f"""
You are a code refiner. Apply the following fix to the artifact:

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

        # Call LLM
        response = self._call_llm(prompt)
        return response
```

---

## Integration: QualityLoop

**Purpose**: Координировать все компоненты для loop execution

**Location**: `src/specify_cli/quality/loop.py`

### API

```python
class QualityLoop:
    """Main quality loop coordinator"""

    def __init__(
        self,
        rule_manager: RuleManager,
        evaluator: Evaluator,
        scorer: Scorer,
        critique: Critique,
        refiner: Refiner,
        state_manager: LoopStateManager
    ):
        """Initialize quality loop"""

    def run(
        self,
        artifact: str,
        criteria_name: str,
        max_iterations: int = 4,
        threshold_a: float = 0.8,
        threshold_b: float = 0.9
    ) -> Dict:
        """Run quality loop

        Args:
            artifact: Initial artifact content
            criteria_name: Criteria template name
            max_iterations: Maximum iterations
            threshold_a: Phase A threshold
            threshold_b: Phase B threshold

        Returns:
            Final result with score, status, changes
        """
```

### Implementation

```python
class QualityLoop:
    def run(self, artifact, criteria_name, max_iterations=4, threshold_a=0.8, threshold_b=0.9):
        # Load criteria
        criteria = self.rule_manager.load_criteria(criteria_name)

        # Initialize state
        state = LoopState(
            iteration=1,
            max_iterations=max_iterations,
            phase="A",
            criteria=criteria
        )
        self.state_manager.save(state)

        # Run iterations
        while state.iteration <= state.max_iterations:
            # Evaluate
            result = self.evaluator.evaluate(artifact, criteria, state.phase)
            state.evaluation = result
            state.current_score = result.score

            # Check if passed Phase B
            if result.passed and state.phase == "B":
                state.status = "completed"
                state.stop = {"passed": True, "reason": "threshold_reached"}
                break

            # Check stagnation
            if self._check_stagnation(state):
                state.status = "stopped"
                state.stop = {"passed": False, "reason": "stagnation"}
                break

            # Switch to Phase B if Phase A passed
            if result.passed and state.phase == "A":
                state.phase = "B"
                self.state_manager.save(state)
                continue  # Re-evaluate with Phase B rules

            # Critique + Refine
            critique_result = self.critique.generate(result.failed_rules, artifact)
            state.critique = critique_result
            artifact = self.refiner.apply(artifact, critique_result)

            # Next iteration
            state.iteration += 1
            state.last_score = state.current_score
            self.state_manager.save(state)

        # Save final state
        self.state_manager.save(state)

        return {
            "state": state,
            "artifact": artifact,
            "score": state.current_score,
            "passed": state.stop.get("passed", False),
            "stop_reason": state.stop.get("reason", "")
        }
```

---

## Testing Strategy

### Unit Tests

**RuleManager**:
- `test_load_criteria_success()`: Load valid criteria
- `test_load_criteria_not_found()`: Raise exception for invalid criteria
- `test_get_rules_for_phase()`: Filter rules by phase
- `test_auto_detect_criteria()`: Detect from task description

**Scorer**:
- `test_calculate_score_all_passed()`: Score = 1.0
- `test_calculate_score_partial()`: Score = expected value
- `test_check_passed_with_fail()`: Fail even with high score
- `test_check_passed_no_fail()`: Pass with threshold
- `test_calculate_distance_to_success()`: Correct gap calculation

**Evaluator**:
- `test_evaluate_all_passed()`: All rules pass
- `test_evaluate_with_failures()`: Some rules fail
- `test_evaluate_phase_a_b()`: Different active rules
- `test_check_rule_content()`: Content-based checking
- `test_check_rule_executable()`: Executable checking

**Critique**:
- `test_generate_max_issues()`: Limit to max_issues
- `test_generate_fix_instruction()`: Generate fix for rule
- `test_generate_skipped()`: Skipped issues when > max_issues

**Refiner**:
- `test_apply_single_fix()`: Apply one fix
- `test_apply_multiple_fixes()`: Apply multiple fixes
- `test_apply_no_fixes()`: Return unchanged artifact

### Integration Tests

**QualityLoop**:
- `test_run_phase_a_passed()`: Phase A passed, switch to B
- `test_run_phase_b_passed()`: Phase B passed, stop
- `test_run_stagnation()`: Stop on stagnation
- `test_run_iteration_limit()`: Stop on max iterations
- `test_run_full_loop()`: Complete loop from start to finish

---

## Performance Requirements

| Метрика | Target | Как измеряется |
|---------|--------|----------------|
| Rule loading | < 100ms | Benchmark load_criteria() |
| Score calculation | < 10ms | Benchmark calculate_score() |
| Evaluation (content) | < 1s | Benchmark evaluate() с 10 rules |
| Evaluation (executable) | < 5s | Benchmark evaluate() с executable checks |
| Critique generation | < 2s | Benchmark generate() с 5 issues |
| Refinement application | < 30s | Benchmark apply() с 5 fixes |
| Full iteration | < 60s | End-to-end iteration time |

---

## Error Handling

| Error | Condition | Action |
|-------|-----------|--------|
| `CriteriaNotFound` | Template not found | Raise exception with available templates |
| `InvalidPhase` | Phase not "A" or "B" | Raise exception with valid phases |
| `NoActiveRules` | No rules for phase | Treat as pass (score = 1.0) |
| `ExecutableCheckFailed` | Check script failed | Log error, treat as fail |
| `LLMUnavailable` | LLM not responding | Fall back to rule-based fixes |
| `RefinementFailed` | Refinement broke code | Revert to previous artifact |

---

## Version History

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2025-03-11 | Initial version |
