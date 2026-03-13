"""
JSON Report Generator & Schema

Generates JSON reports for quality loop results with category breakdown.
Includes JSON Schema for validation and distribution statistics.
Ideal for CI/CD integration and automated processing.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json


# ============================================================
# JSON Schema (formerly json_schema.py)
# ============================================================

# JSON Schema for Spec Kit Quality Report v1.0
QUALITY_REPORT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://speckit.dev/schemas/quality-report-v1.json",
    "title": "Spec Kit Quality Report",
    "description": "Quality evaluation report with category breakdown for CI/CD integration",
    "type": "object",
    "required": ["meta", "summary", "category_breakdown"],
    "properties": {
        "meta": {
            "type": "object",
            "description": "Report metadata",
            "required": ["version", "generated_at", "generator"],
            "properties": {
                "version": {
                    "type": "string",
                    "description": "Report format version",
                    "pattern": r"^\d+\.\d+$"
                },
                "generated_at": {
                    "type": "string",
                    "description": "ISO 8601 timestamp of report generation",
                    "format": "date-time"
                },
                "generator": {
                    "type": "string",
                    "description": "Generator name and version"
                }
            }
        },
        "summary": {
            "type": "object",
            "description": "Overall summary of quality evaluation",
            "required": ["score", "passed", "status", "priority_profile"],
            "properties": {
                "score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Overall quality score (0.0 to 1.0)"
                },
                "passed": {
                    "type": "boolean",
                    "description": "Whether quality gate passed"
                },
                "status": {
                    "type": "string",
                    "enum": ["completed", "failed", "stopped"],
                    "description": "Final status of the quality loop"
                },
                "priority_profile": {
                    "type": "string",
                    "description": "Priority profile used for scoring"
                },
                "iteration": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Number of iterations performed"
                },
                "max_iterations": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum iterations configured"
                },
                "phase": {
                    "type": "string",
                    "enum": ["A", "B"],
                    "description": "Current phase when loop stopped"
                },
                "run_id": {
                    "type": "string",
                    "description": "Unique run identifier"
                },
                "task_alias": {
                    "type": "string",
                    "description": "Task alias for the loop"
                }
            }
        },
        "category_breakdown": {
            "type": "object",
            "description": "Breakdown of issues by category",
            "required": ["categories", "total_issues"],
            "properties": {
                "categories": {
                    "type": "array",
                    "description": "List of categories with issue counts",
                    "items": {
                        "type": "object",
                        "required": ["name", "failed", "warnings", "total"],
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Category name (e.g., security, performance)"
                            },
                            "failed": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Number of failed rules in this category"
                            },
                            "warnings": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Number of warnings in this category"
                            },
                            "total": {
                                "type": "integer",
                                "minimum": 0,
                                "description": "Total issues in this category"
                            },
                            "rule_ids": {
                                "type": "array",
                                "description": "Rule IDs that triggered issues",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "total_issues": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Total number of issues across all categories"
                }
            }
        },
        "failed_rules": {
            "type": "array",
            "description": "List of failed rules with details",
            "items": {
                "type": "object",
                "required": ["rule_id", "category", "reason"],
                "properties": {
                    "rule_id": {
                        "type": "string",
                        "description": "Unique rule identifier"
                    },
                    "category": {
                        "type": "string",
                        "description": "Rule category"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Human-readable reason for failure"
                    }
                }
            }
        },
        "warnings": {
            "type": "array",
            "description": "List of warnings with details",
            "items": {
                "type": "object",
                "required": ["rule_id", "category", "reason"],
                "properties": {
                    "rule_id": {
                        "type": "string",
                        "description": "Unique rule identifier"
                    },
                    "category": {
                        "type": "string",
                        "description": "Rule category"
                    },
                    "reason": {
                        "type": "string",
                        "description": "Human-readable warning message"
                    }
                }
            }
        },
        "score_timeline": {
            "type": "array",
            "description": "Score progression across iterations",
            "items": {
                "type": "object",
                "required": ["label", "iteration", "score"],
                "properties": {
                    "label": {
                        "type": "string",
                        "description": "Label for this point (e.g., 'Iteration 1')"
                    },
                    "iteration": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "Iteration number"
                    },
                    "score": {
                        "type": "number",
                        "minimum": 0.0,
                        "maximum": 1.0,
                        "description": "Score at this point"
                    }
                }
            }
        },
        "gate_result": {
            "type": "object",
            "description": "Quality gate evaluation results",
            "properties": {
                "gate_result": {
                    "type": "string",
                    "enum": ["passed", "failed", "warning"],
                    "description": "Gate evaluation result"
                },
                "passed": {
                    "type": "boolean",
                    "description": "Whether the gate passed"
                },
                "blocked": {
                    "type": "boolean",
                    "description": "Whether the gate is blocking"
                },
                "policy_name": {
                    "type": "string",
                    "description": "Name of the gate policy used"
                },
                "policy_description": {
                    "type": "string",
                    "description": "Description of the gate policy"
                },
                "overall_threshold": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Overall score threshold required"
                },
                "overall_score": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "description": "Actual overall score achieved"
                },
                "messages": {
                    "type": "array",
                    "description": "Gate violation messages",
                    "items": {"type": "string"}
                },
                "category_scores": {
                    "type": "object",
                    "description": "Category scores achieved",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "score": {"type": "number"},
                            "passed": {"type": "integer"},
                            "failed": {"type": "integer"},
                            "total": {"type": "integer"}
                        }
                    }
                },
                "category_failed": {
                    "type": "object",
                    "description": "Failed counts per category",
                    "additionalProperties": {"type": "integer"}
                },
                "severity_counts": {
                    "type": "object",
                    "description": "Issue counts by severity",
                    "properties": {
                        "critical": {"type": "integer"},
                        "high": {"type": "integer"},
                        "medium": {"type": "integer"},
                        "low": {"type": "integer"},
                        "info": {"type": "integer"}
                    }
                },
                "block_on_failure": {
                    "type": "boolean",
                    "description": "Whether gate blocks on failure"
                }
            }
        },
        "distribution": {
            "type": "object",
            "description": "Quality distribution statistics",
            "properties": {
                "severity": {
                    "type": "object",
                    "description": "Issue counts by severity level",
                    "properties": {
                        "critical": {"type": "integer", "minimum": 0},
                        "high": {"type": "integer", "minimum": 0},
                        "medium": {"type": "integer", "minimum": 0},
                        "low": {"type": "integer", "minimum": 0},
                        "info": {"type": "integer", "minimum": 0},
                        "unknown": {"type": "integer", "minimum": 0}
                    }
                },
                "score_distribution": {
                    "type": "object",
                    "description": "Score distribution statistics",
                    "properties": {
                        "count": {"type": "integer", "minimum": 0},
                        "min": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "max": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                        "mean": {"type": "number"},
                        "median": {"type": "number"},
                        "p25": {"type": "number"},
                        "p75": {"type": "number"},
                        "p90": {"type": "number"},
                        "p95": {"type": "number"}
                    }
                }
            }
        }
    }
}


def get_schema() -> dict:
    """Get the JSON schema for quality reports"""
    return QUALITY_REPORT_SCHEMA


def validate_schema(report_data: dict) -> tuple[bool, list[str]]:
    """Validate a quality report against the schema

    Args:
        report_data: Report data to validate

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    required_sections = ["meta", "summary", "category_breakdown"]
    for section in required_sections:
        if section not in report_data:
            errors.append(f"Missing required section: {section}")

    if "meta" in report_data:
        meta = report_data["meta"]
        if "version" not in meta:
            errors.append("Missing meta.version")
        if "generated_at" not in meta:
            errors.append("Missing meta.generated_at")
        if "generator" not in meta:
            errors.append("Missing meta.generator")

    if "summary" in report_data:
        summary = report_data["summary"]
        required_fields = ["score", "passed", "status", "priority_profile"]
        for field in required_fields:
            if field not in summary:
                errors.append(f"Missing summary.{field}")

        if "score" in summary:
            score = summary["score"]
            if not isinstance(score, (int, float)):
                errors.append("summary.score must be a number")
            elif not (0.0 <= score <= 1.0):
                errors.append("summary.score must be between 0.0 and 1.0")

        if "passed" in summary and not isinstance(summary["passed"], bool):
            errors.append("summary.passed must be a boolean")

        if "status" in summary:
            valid_statuses = ["completed", "failed", "stopped"]
            if summary["status"] not in valid_statuses:
                errors.append(f"summary.status must be one of {valid_statuses}")

    if "category_breakdown" in report_data:
        breakdown = report_data["category_breakdown"]
        if "categories" not in breakdown:
            errors.append("Missing category_breakdown.categories")
        elif not isinstance(breakdown["categories"], list):
            errors.append("category_breakdown.categories must be an array")
        else:
            for i, cat in enumerate(breakdown["categories"]):
                if not isinstance(cat, dict):
                    errors.append(f"category_breakdown.categories[{i}] must be an object")
                    continue
                required_cat_fields = ["name", "failed", "warnings", "total"]
                for field in required_cat_fields:
                    if field not in cat:
                        errors.append(f"Missing category_breakdown.categories[{i}].{field}")

    for section in ["failed_rules", "warnings"]:
        if section in report_data and not isinstance(report_data[section], list):
            errors.append(f"{section} must be an array")

    if "score_timeline" in report_data and not isinstance(report_data["score_timeline"], list):
        errors.append("score_timeline must be an array")

    if "gate_result" in report_data:
        gate_result = report_data["gate_result"]
        if not isinstance(gate_result, dict):
            errors.append("gate_result must be an object")
        else:
            if "gate_result" in gate_result and gate_result["gate_result"] not in ["passed", "failed", "warning"]:
                errors.append("gate_result.gate_result must be 'passed', 'failed', or 'warning'")
            if "passed" in gate_result and not isinstance(gate_result["passed"], bool):
                errors.append("gate_result.passed must be a boolean")
            if "blocked" in gate_result and not isinstance(gate_result["blocked"], bool):
                errors.append("gate_result.blocked must be a boolean")

    if "distribution" in report_data:
        distribution = report_data["distribution"]
        if not isinstance(distribution, dict):
            errors.append("distribution must be an object")
        else:
            if "severity" in distribution and not isinstance(distribution["severity"], dict):
                errors.append("distribution.severity must be an object")
            if "score_distribution" in distribution and not isinstance(distribution["score_distribution"], dict):
                errors.append("distribution.score_distribution must be an object")

    return len(errors) == 0, errors


def get_schema_json(pretty: bool = True) -> str:
    """Get JSON schema as JSON string"""
    if pretty:
        return json.dumps(QUALITY_REPORT_SCHEMA, indent=2, ensure_ascii=False)
    return json.dumps(QUALITY_REPORT_SCHEMA, ensure_ascii=False)


def export_schema(output_path: str, pretty: bool = True) -> None:
    """Export JSON schema to a file for distribution"""
    schema_content = get_schema_json(pretty=pretty)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(schema_content, encoding="utf-8")


def get_schema_info() -> dict:
    """Get schema metadata and information"""
    return {
        "schema_id": QUALITY_REPORT_SCHEMA.get("$id", ""),
        "title": QUALITY_REPORT_SCHEMA.get("title", ""),
        "version": "1.0",
        "schema_format": QUALITY_REPORT_SCHEMA.get("$schema", ""),
        "description": QUALITY_REPORT_SCHEMA.get("description", ""),
        "required_sections": QUALITY_REPORT_SCHEMA.get("required", []),
        "available_sections": list(QUALITY_REPORT_SCHEMA.get("properties", {}).keys()),
    }


def print_schema_info() -> None:
    """Print schema information in human-readable format"""
    info = get_schema_info()
    print("Spec Kit Quality Report JSON Schema")
    print("=" * 50)
    print(f"Version: {info['version']}")
    print(f"Title: {info['title']}")
    print(f"Schema ID: {info['schema_id']}")
    print(f"Format: {info['schema_format']}")
    print(f"\nDescription: {info['description']}")
    print(f"\nRequired Sections: {', '.join(info['required_sections'])}")
    print(f"Available Sections: {', '.join(info['available_sections'])}")


def calculate_distribution_stats(scores: list) -> dict:
    """Calculate distribution statistics for a list of scores

    Args:
        scores: List of numeric scores (0.0 to 1.0)

    Returns:
        Dict with distribution statistics (min, max, mean, median, p25, p75, p90, p95)
    """
    if not scores:
        return {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
            "p25": None,
            "p75": None,
            "p90": None,
            "p95": None,
        }

    import statistics

    sorted_scores = sorted(scores)
    n = len(sorted_scores)

    def percentile(p: float) -> float:
        index = (p / 100) * (n - 1)
        lower = int(index)
        upper = min(lower + 1, n - 1)
        weight = index - lower
        if upper == lower:
            return sorted_scores[lower]
        return sorted_scores[lower] * (1 - weight) + sorted_scores[upper] * weight

    return {
        "count": n,
        "min": round(sorted_scores[0], 3),
        "max": round(sorted_scores[-1], 3),
        "mean": round(statistics.mean(sorted_scores), 3),
        "median": round(statistics.median(sorted_scores), 3),
        "p25": round(percentile(25), 3),
        "p75": round(percentile(75), 3),
        "p90": round(percentile(90), 3),
        "p95": round(percentile(95), 3),
    }


def get_severity_distribution(failed_rules: list, warnings: list) -> dict:
    """Get severity distribution for rules"""
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0, "unknown": 0}

    for rule in failed_rules:
        severity = str(rule.get("severity", "unknown")).lower()
        if severity not in severity_counts:
            severity = "unknown"
        severity_counts[severity] += 1

    for rule in warnings:
        severity = str(rule.get("severity", "info")).lower()
        if severity not in severity_counts:
            severity = "unknown"
        severity_counts[severity] += 1

    return severity_counts


# ============================================================
# JSON Report Generator
# ============================================================

class JSONReportGenerator:
    """Generate JSON reports for quality evaluation results with category breakdown"""

    def __init__(self):
        """Initialize JSON report generator"""
        self.calculate_distribution_stats = calculate_distribution_stats
        self.get_severity_distribution = get_severity_distribution

    def generate(
        self,
        result: Dict[str, Any],
        output_path: Optional[str] = None,
        pretty: bool = True,
        validate: bool = True,
        include_categories: Optional[List[str]] = None,
        exclude_categories: Optional[List[str]] = None,
    ) -> str:
        """Generate JSON report from evaluation result

        Args:
            result: Evaluation result dict from QualityLoop
            output_path: Optional file path to save JSON
            pretty: Pretty-print JSON with indentation
            validate: Validate report against schema before returning
            include_categories: Only include these categories (None = all)
            exclude_categories: Exclude these categories (None = none)

        Returns:
            JSON content as string
        """
        state = result.get("state", {})
        score = result.get("score", 0.0)
        passed = result.get("passed", False)
        priority_profile = result.get("priority_profile", "default")
        gate_result = result.get("gate_result")

        # Build structured JSON
        category_breakdown = self._get_category_breakdown(state)

        # Apply category filters
        filtered_categories = self._apply_category_filters(
            category_breakdown["categories"],
            include_categories,
            exclude_categories,
        )

        filtered_breakdown = {
            "categories": filtered_categories,
            "total_issues": sum(c["total"] for c in filtered_categories),
        }

        failed_rules = self._get_failed_rules(state)
        warnings = self._get_warnings(state)

        if include_categories:
            failed_rules = [r for r in failed_rules if r["category"] in include_categories]
            warnings = [w for w in warnings if w["category"] in include_categories]
        if exclude_categories:
            failed_rules = [r for r in failed_rules if r["category"] not in exclude_categories]
            warnings = [w for w in warnings if w["category"] not in exclude_categories]

        rule_scores = [rule.get("score", 0.0) for rule in failed_rules]
        severity_dist = self.get_severity_distribution(failed_rules, warnings)
        dist_stats = self.calculate_distribution_stats(rule_scores)

        report = {
            "meta": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "generator": "Spec Kit Quality Loop",
            },
            "summary": {
                "score": score,
                "passed": passed,
                "status": "completed" if passed else "failed",
                "priority_profile": priority_profile,
                "iteration": state.get("iteration", 1),
                "max_iterations": state.get("max_iterations", 4),
                "phase": state.get("phase", "A"),
                "run_id": state.get("run_id", ""),
                "task_alias": state.get("task_alias", ""),
            },
            "category_breakdown": filtered_breakdown,
            "failed_rules": failed_rules,
            "warnings": warnings,
            "score_timeline": self._get_score_timeline(state),
            "distribution": {
                "severity": severity_dist,
                "score_distribution": dist_stats,
            },
        }

        if gate_result:
            report["gate_result"] = gate_result

        if validate:
            is_valid, errors = validate_schema(report)
            if not is_valid:
                import warnings as py_warnings
                py_warnings.warn(f"JSON report validation warnings: {errors}")

        if pretty:
            json_content = json.dumps(report, indent=2, ensure_ascii=False)
        else:
            json_content = json.dumps(report, ensure_ascii=False)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(json_content, encoding="utf-8")

        return json_content

    def _get_category_breakdown(self, state: Dict) -> Dict[str, Any]:
        """Get category breakdown statistics"""
        evaluation = state.get("evaluation", {})
        failed_rules = evaluation.get("failed_rules", [])
        warnings = evaluation.get("warnings", [])

        from collections import defaultdict
        category_stats = defaultdict(lambda: {"fail": 0, "warn": 0, "rule_ids": []})

        for rule in failed_rules:
            category = rule.get("category", "general")
            category_stats[category]["fail"] += 1
            category_stats[category]["rule_ids"].append(rule.get("rule_id", ""))

        for rule in warnings:
            category = rule.get("category", "general")
            category_stats[category]["warn"] += 1
            if rule.get("rule_id") not in category_stats[category]["rule_ids"]:
                category_stats[category]["rule_ids"].append(rule.get("rule_id", ""))

        if not category_stats:
            return {"categories": [], "total_issues": 0}

        categories = []
        total_issues = 0

        for category, stats in sorted(
            category_stats.items(),
            key=lambda x: x[1]["fail"] + x[1]["warn"],
            reverse=True
        ):
            fail_count = stats["fail"]
            warn_count = stats["warn"]
            total = fail_count + warn_count
            total_issues += total

            categories.append({
                "name": category,
                "failed": fail_count,
                "warnings": warn_count,
                "total": total,
                "rule_ids": stats["rule_ids"],
            })

        return {
            "categories": categories,
            "total_issues": total_issues,
        }

    def _get_failed_rules(self, state: Dict) -> list:
        """Get failed rules list with categories"""
        evaluation = state.get("evaluation", {})
        failed_rules = evaluation.get("failed_rules", [])

        return [
            {
                "rule_id": rule.get("rule_id", ""),
                "category": rule.get("category", "general"),
                "reason": rule.get("reason", ""),
                "score": rule.get("score", 0.0),
                "severity": rule.get("severity", "medium"),
            }
            for rule in failed_rules
        ]

    def _get_warnings(self, state: Dict) -> list:
        """Get warnings list with categories"""
        evaluation = state.get("evaluation", {})
        warnings = evaluation.get("warnings", [])

        return [
            {
                "rule_id": rule.get("rule_id", ""),
                "category": rule.get("category", "general"),
                "reason": rule.get("reason", ""),
                "score": rule.get("score", 0.0),
                "severity": rule.get("severity", "info"),
            }
            for rule in warnings
        ]

    def _get_score_timeline(self, state: Dict) -> list:
        """Get score timeline for charts"""
        events = []

        events.append({
            "label": "Start",
            "iteration": 0,
            "score": 0.0,
        })

        current_score = state.get("current_score", 0.0)
        iteration = state.get("iteration", 1)
        events.append({
            "label": f"Iteration {iteration}",
            "iteration": iteration,
            "score": current_score,
        })

        last_score = state.get("last_score")
        if last_score is not None and abs(last_score - current_score) > 0.01:
            events.insert(-1, {
                "label": f"Iteration {iteration - 1}",
                "iteration": iteration - 1,
                "score": last_score,
            })

        return events

    def _apply_category_filters(
        self,
        categories: List[Dict[str, Any]],
        include_categories: Optional[List[str]],
        exclude_categories: Optional[List[str]],
    ) -> List[Dict[str, Any]]:
        """Apply category filters to category list"""
        filtered = categories

        if include_categories:
            filtered = [c for c in filtered if c["name"] in include_categories]

        if exclude_categories:
            filtered = [c for c in filtered if c["name"] not in exclude_categories]

        return filtered

    def validate_report(self, report_data: Dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate a report against the JSON schema"""
        return validate_schema(report_data)


def generate_json_report(
    result: Dict[str, Any],
    output_path: Optional[str] = None,
    pretty: bool = True,
    validate: bool = True,
    include_categories: Optional[List[str]] = None,
    exclude_categories: Optional[List[str]] = None,
) -> str:
    """Convenience function to generate JSON report"""
    generator = JSONReportGenerator()
    return generator.generate(
        result,
        output_path,
        pretty,
        validate,
        include_categories,
        exclude_categories,
    )
