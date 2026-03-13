"""
HTML Report Generator

Generates interactive HTML reports for quality loop results.
Features: score timeline, failed rules breakdown, profile information,
category breakdown with charts, quality distribution (Exp 54).

Exp 28: Initial HTML report with timeline and metrics
Exp 50: Category breakdown with doughnut chart
Exp 54: Distribution charts (severity pie chart, score distribution histogram)
Exp 56: Quality gate results section with visual status and violations
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json


class HTMLReportGenerator:
    """Generate interactive HTML reports for quality evaluation results"""

    # Severity colors for charts (Exp 54)
    SEVERITY_COLORS = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "low": "#28a745",
        "info": "#17a2b8",
        "unknown": "#6c757d",
    }

    # Severity order for sorting
    SEVERITY_ORDER = ["critical", "high", "medium", "low", "info", "unknown"]

    def __init__(self):
        """Initialize HTML report generator"""
        self.template_dir = Path(__file__).parent / "templates" / "html"
        # Import distribution stats functions (Exp 54)
        from specify_cli.quality.json_report import calculate_distribution_stats, get_severity_distribution
        self.calculate_distribution_stats = calculate_distribution_stats
        self.get_severity_distribution = get_severity_distribution

    def generate(
        self,
        result: Dict[str, Any],
        output_path: Optional[str] = None,
        include_timeline: bool = True,
        include_details: bool = True,
    ) -> str:
        """Generate HTML report from evaluation result

        Args:
            result: Evaluation result dict from QualityLoop
            output_path: Optional file path to save HTML
            include_timeline: Include score timeline chart
            include_details: Include detailed failed rules breakdown

        Returns:
            HTML content as string
        """
        state = result.get("state", {})
        score = result.get("score", 0.0)
        passed = result.get("passed", False)
        priority_profile = result.get("priority_profile", "default")
        gate_result = result.get("gate_result")  # Exp 56: Gate results

        # Build HTML content
        html_parts = [
            self._get_html_header(),
            self._get_styles(),
            "</head><body>",
            self._get_header_section(state, score, passed, priority_profile),
        ]

        # Add summary section
        html_parts.append(self._get_summary_section(state, score, passed))

        # Add gate results section if available (Exp 56)
        if gate_result:
            html_parts.append(self._get_gate_section(gate_result))

        # Add distribution sections (Exp 54)
        html_parts.append(self._get_distribution_section(state))

        # Add timeline if requested
        if include_timeline:
            html_parts.append(self._get_timeline_section(state))

        # Add details if requested
        if include_details:
            html_parts.append(self._get_details_section(state))

        # Add footer
        html_parts.extend([
            self._get_footer(),
            "</body></html>"
        ])

        html_content = "\n".join(html_parts)

        # Save if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html_content, encoding="utf-8")

        return html_content

    def _get_html_header(self) -> str:
        """Get HTML document header"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Spec Kit Quality Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>"""

    def _get_styles(self) -> str:
        """Get CSS styles for the report"""
        return """<style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        padding: 20px;
    }
    .container {
        max-width: 1200px;
        margin: 0 auto;
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        overflow: hidden;
    }
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px;
        text-align: center;
    }
    .header h1 { font-size: 2.5em; margin-bottom: 10px; }
    .header .subtitle { opacity: 0.9; font-size: 1.1em; }
    .score-badge {
        display: inline-block;
        padding: 15px 40px;
        border-radius: 50px;
        font-size: 2em;
        font-weight: bold;
        margin: 20px 0;
        color: white;
        transition: transform 0.3s;
    }
    .score-badge:hover { transform: scale(1.05); }
    .score-passed { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
    .score-failed { background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%); }
    .section {
        padding: 30px 40px;
        border-bottom: 1px solid #eee;
    }
    .section:last-child { border-bottom: none; }
    .section h2 {
        font-size: 1.5em;
        color: #333;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .section h2::before {
        content: '';
        width: 4px;
        height: 24px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 2px;
    }
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-top: 20px;
    }
    .metric-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
    }
    .metric-card .label { color: #666; font-size: 0.9em; margin-bottom: 5px; }
    .metric-card .value { color: #333; font-size: 1.8em; font-weight: bold; }
    .chart-container {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        height: 300px;
    }
    .rules-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
    }
    .rules-table th {
        background: #f8f9fa;
        padding: 12px;
        text-align: left;
        font-weight: 600;
        color: #333;
        border-bottom: 2px solid #dee2e6;
    }
    .rules-table td {
        padding: 12px;
        border-bottom: 1px solid #dee2e6;
    }
    .rules-table tr:hover { background: #f8f9fa; }
    .severity-fail { color: #dc3545; font-weight: 600; }
    .severity-warn { color: #ffc107; font-weight: 600; }
    .severity-info { color: #17a2b8; font-weight: 600; }
    .footer {
        background: #f8f9fa;
        padding: 20px 40px;
        text-align: center;
        color: #666;
        font-size: 0.9em;
    }
    .tag {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
        margin: 0 4px;
    }
    .tag-profile { background: #e3f2fd; color: #1976d2; }
    .tag-phase { background: #f3e5f5; color: #7b1fa2; }
    .category-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 10px;
        font-size: 0.8em;
        font-weight: 600;
        text-transform: capitalize;
    }
    .progress-bar {
        height: 8px;
        background: #e9ecef;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 10px;
    }
    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        transition: width 0.5s ease;
    }
</style>"""

    def _get_header_section(
        self, state: Dict, score: float, passed: bool, priority_profile: str
    ) -> str:
        """Get report header section"""
        run_id = state.get("run_id", "unknown")
        task_alias = state.get("task_alias", "unknown")
        status = state.get("status", "unknown").upper()

        badge_class = "score-passed" if passed else "score-failed"
        status_text = "PASSED" if passed else "FAILED"

        return f"""    <div class="header">
        <h1>Spec Kit Quality Report</h1>
        <div class="subtitle">Task: {task_alias} | Run: {run_id}</div>
        <div class="score-badge {badge_class}">{score:.2f}</div>
        <div>
            <span class="tag tag-profile">Profile: {priority_profile}</span>
            <span class="tag tag-phase">Status: {status_text}</span>
        </div>
    </div>"""

    def _get_summary_section(
        self, state: Dict, score: float, passed: bool
    ) -> str:
        """Get summary section with key metrics"""
        iteration = state.get("iteration", 1)
        max_iterations = state.get("max_iterations", 4)
        phase = state.get("phase", "A")
        started_at = state.get("started_at", "")

        # Calculate progress
        progress = (iteration / max_iterations) * 100

        # Get category breakdown
        category_breakdown = self._get_category_breakdown(state)

        summary_html = f"""    <div class="section">
        <h2>Summary</h2>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="label">Iteration</div>
                <div class="value">{iteration}/{max_iterations}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {progress}%"></div>
                </div>
            </div>
            <div class="metric-card">
                <div class="label">Phase</div>
                <div class="value">{phase}</div>
            </div>
            <div class="metric-card">
                <div class="label">Quality Score</div>
                <div class="value">{score:.2f}</div>
            </div>
            <div class="metric-card">
                <div class="label">Status</div>
                <div class="value" style="color: {'#38ef7d' if passed else '#f45c43'}">
                    {'PASS' if passed else 'FAIL'}
                </div>
            </div>
        </div>
    </div>"""

        # Add category breakdown section if there are issues
        if category_breakdown:
            summary_html += category_breakdown

        return summary_html

    def _get_gate_section(self, gate_result: Dict[str, Any]) -> str:
        """Get quality gate results section (Exp 56)

        Args:
            gate_result: Gate evaluation result dict

        Returns:
            HTML string with gate results
        """
        gate_status = gate_result.get("gate_result", "unknown")
        passed = gate_result.get("passed", False)
        blocked = gate_result.get("blocked", False)
        policy_name = gate_result.get("policy_name", "unknown")
        policy_desc = gate_result.get("policy_description", "")
        overall_threshold = gate_result.get("overall_threshold", 0.0)
        overall_score = gate_result.get("overall_score", 0.0)
        messages = gate_result.get("messages", [])
        severity_counts = gate_result.get("severity_counts", {})
        category_scores = gate_result.get("category_scores", {})

        # Determine status styling
        if gate_status == "passed":
            status_bg = "linear-gradient(135deg, #11998e 0%, #38ef7d 100%)"
            status_icon = "✅"
            status_text = "PASSED"
        elif gate_status == "failed":
            status_bg = "linear-gradient(135deg, #eb3349 0%, #f45c43 100%)"
            status_icon = "🚫"
            status_text = "FAILED" if blocked else "WARNING"
        else:
            status_bg = "linear-gradient(135deg, #ffc107 0%, #ff9800 100%)"
            status_icon = "⚠️"
            status_text = "WARNING"

        # Build severity badges
        severity_badges = []
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = severity_counts.get(sev, 0)
            if count > 0:
                color = self.SEVERITY_COLORS.get(sev, "#6c757d")
                severity_badges.append(f"""
                    <div style="display: inline-block; background: {color}; color: white;
                                padding: 4px 12px; border-radius: 12px; margin: 2px;
                                font-size: 0.85em; font-weight: 600;">
                        {sev.capitalize()}: {count}
                    </div>""")

        # Build category score bars
        category_bars = []
        for cat, score in sorted(category_scores.items(), key=lambda x: x[1]):
            percentage = score * 100
            color = "#38ef7d" if score >= 0.9 else "#ffc107" if score >= 0.7 else "#f45c43"
            category_bars.append(f"""
                <tr>
                    <td style="padding: 8px;"><strong>{cat}</strong></td>
                    <td style="padding: 8px; width: 60%;">
                        <div style="background: #e9ecef; border-radius: 4px; height: 8px; overflow: hidden;">
                            <div style="background: {color}; width: {percentage}%; height: 100%;"></div>
                        </div>
                    </td>
                    <td style="padding: 8px; text-align: right;">{percentage:.0f}%</td>
                </tr>""")

        # Build messages list
        messages_html = ""
        if messages:
            messages_html = "<ul style='margin-top: 15px; padding-left: 20px;'>"
            for msg in messages[:10]:  # Show first 10 messages
                messages_html += f"<li style='margin-bottom: 8px; color: #f45c43;'>{msg}</li>"
            if len(messages) > 10:
                messages_html += f"<li style='color: #666;'>... and {len(messages) - 10} more</li>"
            messages_html += "</ul>"

        return f"""    <div class="section">
        <h2>Quality Gate Results</h2>
        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px; margin-top: 20px;">
            <!-- Gate Status Card -->
            <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                        padding: 25px; border-radius: 12px; text-align: center;">
                <div style="font-size: 0.9em; color: #666; margin-bottom: 10px;">Policy</div>
                <div style="font-size: 1.4em; font-weight: bold; color: #333; margin-bottom: 5px;">
                    {policy_name}
                </div>
                <div style="font-size: 0.85em; color: #666; margin-bottom: 20px;">
                    {policy_desc}
                </div>
                <div style="background: {status_bg}; color: white; padding: 15px 25px;
                            border-radius: 50px; display: inline-block; margin-bottom: 15px;">
                    <span style="font-size: 1.8em;">{status_icon}</span>
                    <div style="font-size: 1.3em; font-weight: bold; margin-top: 5px;">{status_text}</div>
                </div>
                <div style="display: flex; justify-content: space-around; margin-top: 15px;">
                    <div>
                        <div style="font-size: 0.8em; color: #666;">Score</div>
                        <div style="font-size: 1.5em; font-weight: bold; color: #333;">
                            {overall_score:.2f}
                        </div>
                    </div>
                    <div>
                        <div style="font-size: 0.8em; color: #666;">Threshold</div>
                        <div style="font-size: 1.5em; font-weight: bold; color: #333;">
                            {overall_threshold:.2f}
                        </div>
                    </div>
                </div>
            </div>

            <!-- Gate Details -->
            <div style="background: #f8f9fa; padding: 20px; border-radius: 12px;">
                <h3 style="font-size: 1.1em; color: #333; margin-bottom: 15px;">
                    Issues by Severity
                </h3>
                <div style="margin-bottom: 20px;">
                    {''.join(severity_badges) if severity_badges else '<span style="color: #38ef7d;">No issues!</span>'}
                </div>

                {f'''
                <h3 style="font-size: 1.1em; color: #333; margin-bottom: 15px;">
                    Category Scores
                </h3>
                <table style="width: 100%; margin-bottom: 20px;">
                    {''.join(category_bars) if category_bars else '<tr><td colspan="3">No category data</td></tr>'}
                </table>
                ''' if category_bars else ''}

                {f'''
                <h3 style="font-size: 1.1em; color: #333; margin-bottom: 10px;">
                    {'Violations' if gate_status == 'failed' else 'Messages'}
                </h3>
                {messages_html}
                ''' if messages else f'''
                <div style="text-align: center; color: #38ef7d; font-weight: 600; padding: 20px;">
                    All gate checks passed!
                </div>
                '''}
            </div>
        </div>
    </div>"""

    def _get_category_breakdown(self, state: Dict) -> str:
        """Get category breakdown section (Exp 50)"""
        evaluation = state.get("evaluation", {})
        failed_rules = evaluation.get("failed_rules", [])
        warnings = evaluation.get("warnings", [])

        # Group by category
        from collections import defaultdict
        category_stats = defaultdict(lambda: {"fail": 0, "warn": 0})

        for rule in failed_rules:
            category = rule.get("category", "general")
            category_stats[category]["fail"] += 1

        for rule in warnings:
            category = rule.get("category", "general")
            category_stats[category]["warn"] += 1

        if not category_stats:
            return ""

        # Category colors for visualization
        category_colors = {
            "security": "#dc3545",
            "performance": "#fd7e14",
            "testing": "#6f42c1",
            "documentation": "#17a2b8",
            "code_quality": "#20c997",
            "infrastructure": "#6610f2",
            "observability": "#e83e8c",
            "reliability": "#007bff",
            "cicd": "#28a745",
            "correctness": "#ffc107",
            "accessibility": "#6c757d",
            "ux_quality": "#d63384",
            "general": "#adb5bd",
        }

        # Build category cards
        category_rows = []
        chart_data = []
        total_issues = sum(cat["fail"] + cat["warn"] for cat in category_stats.values())

        for category, stats in sorted(category_stats.items(), key=lambda x: x[1]["fail"] + x[1]["warn"], reverse=True):
            fail_count = stats["fail"]
            warn_count = stats["warn"]
            total = fail_count + warn_count
            percentage = (total / total_issues * 100) if total_issues > 0 else 0
            color = category_colors.get(category, category_colors["general"])

            category_rows.append(f"""
            <tr>
                <td><span class="category-badge" style="background: {color}; color: white;">{category}</span></td>
                <td style="text-align: center;"><span class="severity-fail">{fail_count}</span></td>
                <td style="text-align: center;"><span class="severity-warn">{warn_count}</span></td>
                <td style="text-align: center;"><strong>{total}</strong></td>
                <td style="text-align: center;">{percentage:.1f}%</td>
                <td>
                    <div class="progress-bar" style="height: 6px;">
                        <div class="progress-fill" style="width: {percentage}%; background: {color};"></div>
                    </div>
                </td>
            </tr>""")

            chart_data.append({
                "category": category,
                "count": total,
                "color": color
            })

        return f"""    <div class="section">
        <h2>Issues by Category</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <div>
                <table class="rules-table">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th style="text-align: center;">Failed</th>
                            <th style="text-align: center;">Warnings</th>
                            <th style="text-align: center;">Total</th>
                            <th style="text-align: center;">%</th>
                            <th>Progress</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(category_rows)}
                    </tbody>
                </table>
            </div>
            <div style="display: flex; justify-content: center; align-items: center;">
                <div class="chart-container" style="height: 250px;">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('categoryChart').getContext('2d');
        new Chart(ctx, {{
            type: 'doughnut',
            data: {{
                labels: {json.dumps([c["category"] for c in chart_data])},
                datasets: [{{
                    data: {json.dumps([c["count"] for c in chart_data])},
                    backgroundColor: {json.dumps([c["color"] for c in chart_data])},
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            padding: 15,
                            usePointStyle: true,
                            font: {{ size: 11 }}
                        }}
                    }},
                    tooltip: {{
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        callbacks: {{
                            label: function(context) {{
                                return context.label + ': ' + context.parsed + ' issues';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>"""

    def _get_distribution_section(self, state: Dict) -> str:
        """Get distribution section with severity and score charts (Exp 54)"""
        evaluation = state.get("evaluation", {})
        failed_rules = evaluation.get("failed_rules", [])
        warnings = evaluation.get("warnings", [])

        # Get severity distribution
        severity_dist = self.get_severity_distribution(failed_rules, warnings)

        # Calculate rule scores for score distribution
        rule_scores = []
        for rule in failed_rules:
            # Extract score from rule if available
            rule_score = self._extract_rule_score(rule)
            rule_scores.append(rule_score)

        # Calculate distribution stats
        dist_stats = self.calculate_distribution_stats(rule_scores) if rule_scores else None

        # Build severity pie chart
        severity_chart = self._get_severity_pie_chart(severity_dist)

        # Build score distribution chart
        score_chart = self._get_score_distribution_chart(dist_stats)

        return f"""    <div class="section">
        <h2>Quality Distribution</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
            <!-- Severity Distribution -->
            <div>
                <h3 style="font-size: 1.1em; color: #333; margin-bottom: 15px; text-align: center;">
                    Issues by Severity
                </h3>
                <div class="chart-container" style="height: 280px;">
                    <canvas id="severityChart"></canvas>
                </div>
            </div>
            <!-- Score Distribution -->
            <div>
                <h3 style="font-size: 1.1em; color: #333; margin-bottom: 15px; text-align: center;">
                    Score Distribution
                </h3>
                <div class="chart-container" style="height: 280px;">
                    <canvas id="scoreDistChart"></canvas>
                </div>
            </div>
        </div>
    </div>
    {severity_chart}
    {score_chart}"""

    def _extract_rule_score(self, rule: Dict[str, Any]) -> float:
        """Extract score from rule dict (Exp 54)

        Args:
            rule: Rule dict that may contain score

        Returns:
            Score value (0.0 if not available)
        """
        # Try to get score from rule metadata
        if "score" in rule:
            return float(rule["score"])

        # Calculate from severity if score not available
        severity = rule.get("severity", "medium")
        severity_scores = {
            "critical": 0.0,
            "high": 0.3,
            "medium": 0.5,
            "low": 0.7,
            "info": 0.9,
            "unknown": 0.5,
        }
        return severity_scores.get(severity, 0.5)

    def _get_severity_pie_chart(self, severity_dist: Dict[str, int]) -> str:
        """Generate severity distribution pie chart (Exp 54)

        Args:
            severity_dist: Dictionary with severity counts

        Returns:
            HTML/JS for Chart.js pie chart
        """
        # Filter out zero-count severities
        filtered_dist = {k: v for k, v in severity_dist.items() if v > 0}

        if not filtered_dist:
            return """    <script>
        // No severity data to display
    </script>"""

        # Sort by severity order
        labels = [k for k in self.SEVERITY_ORDER if k in filtered_dist]
        data = [filtered_dist[k] for k in labels]
        colors = [self.SEVERITY_COLORS[k] for k in labels]

        total = sum(data)

        return """    <script>
        const severityCtx = document.getElementById('severityChart').getContext('2d');
        new Chart(severityCtx, {
            type: 'pie',
            data: {
                labels: """ + json.dumps(labels) + """,
                datasets: [{
                    data: """ + json.dumps(data) + """,
                    backgroundColor: """ + json.dumps(colors) + """,
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            font: { size: 12 },
                            generateLabels: function(chart) {
                                const data = chart.data;
                                return data.labels.map((label, i) => ({
                                    text: label.charAt(0).toUpperCase() + label.slice(1) + ': ' + data.datasets[0].data[i] + ' (' +
                                          Math.round(data.datasets[0].data[i] / """ + str(total) + """ * 100) + '%)',
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    hidden: false,
                                    index: i
                                }));
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const percentage = (value / """ + str(total) + """ * 100).toFixed(1);
                                return label.charAt(0).toUpperCase() + label.slice(1) + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    </script>"""

    def _get_score_distribution_chart(self, dist_stats: Optional[Dict]) -> str:
        """Generate score distribution bar chart with percentiles (Exp 54)

        Args:
            dist_stats: Dictionary with distribution statistics

        Returns:
            HTML/JS for Chart.js bar chart
        """
        if not dist_stats or dist_stats.get("count", 0) == 0:
            return """    <script>
        // No score distribution data to display
    </script>"""

        # Extract percentile values
        percentiles = {
            "Min": dist_stats.get("min", 0),
            "P25": dist_stats.get("p25", 0),
            "Median": dist_stats.get("median", 0),
            "P75": dist_stats.get("p75", 0),
            "P90": dist_stats.get("p90", 0),
            "P95": dist_stats.get("p95", 0),
            "Max": dist_stats.get("max", 0),
        }

        labels = list(percentiles.keys())
        values = [round(v * 100) for v in percentiles.values()]  # Convert to percentage

        # Create gradient colors based on score
        colors = []
        for value in values:
            if value < 30:
                colors.append("#dc3545")  # Red for low scores
            elif value < 50:
                colors.append("#fd7e14")  # Orange
            elif value < 70:
                colors.append("#ffc107")  # Yellow
            elif value < 90:
                colors.append("#28a745")  # Green
            else:
                colors.append("#20c997")  # Teal for high scores

        return """    <script>
        const scoreDistCtx = document.getElementById('scoreDistChart').getContext('2d');
        new Chart(scoreDistCtx, {
            type: 'bar',
            data: {
                labels: """ + json.dumps(labels) + """,
                datasets: [{
                    label: 'Score (%)',
                    data: """ + json.dumps(values) + """,
                    backgroundColor: """ + json.dumps(colors) + """,
                    borderColor: """ + json.dumps([c.replace("0.8", "1") for c in colors]) + """,
                    borderWidth: 2,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + context.parsed.y + '%';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: value => value + '%'
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    </script>"""

    def _get_timeline_section(self, state: Dict) -> str:
        """Get timeline section with score chart"""
        events = self._extract_score_events(state)

        # Create canvas for Chart.js
        return """    <div class="section">
        <h2>Score Timeline</h2>
        <div class="chart-container">
            <canvas id="timelineChart"></canvas>
        </div>
    </div>
    <script>
        const ctx = document.getElementById('timelineChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: """ + json.dumps([e["label"] for e in events]) + """,
                datasets: [{
                    label: 'Quality Score',
                    data: """ + json.dumps([e["score"] for e in events]) + """,
                    borderColor: 'rgb(102, 126, 234)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 12,
                        titleFont: { size: 14 },
                        bodyFont: { size: 13 }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1.0,
                        ticks: { callback: value => (value * 100).toFixed(0) + '%' }
                    }
                }
            }
        });
    </script>"""

    def _get_details_section(self, state: Dict) -> str:
        """Get detailed failed rules section grouped by category (Exp 50)"""
        evaluation = state.get("evaluation", {})
        failed_rules = evaluation.get("failed_rules", [])
        warnings = evaluation.get("warnings", [])

        # Group by category
        from collections import defaultdict
        category_rules = defaultdict(lambda: {"fail": [], "warn": []})

        for rule in failed_rules:
            category = rule.get("category", "general")
            category_rules[category]["fail"].append(rule)

        for rule in warnings:
            category = rule.get("category", "general")
            category_rules[category]["warn"].append(rule)

        if not category_rules:
            return """    <div class="section">
        <h2>Failed Rules & Warnings</h2>
        <p style="text-align: center; color: #38ef7d; font-weight: 600; padding: 20px;">
            No issues found! Great job!
        </p>
    </div>"""

        # Category colors
        category_colors = {
            "security": "#dc3545",
            "performance": "#fd7e14",
            "testing": "#6f42c1",
            "documentation": "#17a2b8",
            "code_quality": "#20c997",
            "infrastructure": "#6610f2",
            "observability": "#e83e8c",
            "reliability": "#007bff",
            "cicd": "#28a745",
            "correctness": "#ffc107",
            "accessibility": "#6c757d",
            "ux_quality": "#d63384",
            "general": "#adb5bd",
        }

        # Build category sections
        sections = []
        for category in sorted(category_rules.keys(), key=lambda c: sum(len(r) for r in category_rules[c].values()), reverse=True):
            fail_rules = category_rules[category]["fail"]
            warn_rules = category_rules[category]["warn"]
            total = len(fail_rules) + len(warn_rules)

            if not fail_rules and not warn_rules:
                continue

            color = category_colors.get(category, category_colors["general"])

            rows = []
            for rule in fail_rules:
                rule_id = rule.get("rule_id", "unknown")
                reason = rule.get("reason", "No reason provided")
                rows.append(f"""
                <tr>
                    <td class="severity-fail">FAIL</td>
                    <td>{rule_id}</td>
                    <td>{reason}</td>
                </tr>""")

            for rule in warn_rules:
                rule_id = rule.get("rule_id", "unknown")
                reason = rule.get("reason", "No reason provided")
                rows.append(f"""
                <tr>
                    <td class="severity-warn">WARN</td>
                    <td>{rule_id}</td>
                    <td>{reason}</td>
                </tr>""")

            sections.append(f"""
        <div style="margin-bottom: 30px;">
            <h3 style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <span class="category-badge" style="background: {color}; color: white; font-size: 0.9em;">{category}</span>
                <span style="color: #666; font-size: 0.9em; font-weight: normal;">({total} issues)</span>
            </h3>
            <table class="rules-table">
                <thead>
                    <tr>
                        <th style="width: 80px;">Severity</th>
                        <th style="width: 250px;">Rule ID</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>""")

        return f"""    <div class="section">
        <h2>Failed Rules & Warnings by Category</h2>
        {''.join(sections)}
    </div>"""

    def _get_footer(self) -> str:
        """Get report footer"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"""    <div class="footer">
        <p>Generated by Spec Kit Quality Loop at {timestamp}</p>
        <p style="margin-top: 5px; font-size: 0.85em; color: #999;">
            Spec Kit - AI-powered quality evaluation for software specifications
        </p>
    </div>"""

    def _extract_score_events(self, state: Dict) -> List[Dict[str, Any]]:
        """Extract score events from state for timeline chart"""
        events = []

        # Add initial point
        events.append({
            "label": "Start",
            "score": 0.0
        })

        # Add current score
        current_score = state.get("current_score", 0.0)
        iteration = state.get("iteration", 1)
        events.append({
            "label": f"Iteration {iteration}",
            "score": current_score
        })

        # Add last score if different
        last_score = state.get("last_score")
        if last_score is not None and abs(last_score - current_score) > 0.01:
            events.insert(-1, {
                "label": f"Iteration {iteration - 1}",
                "score": last_score
            })

        return events


def generate_html_report(
    result: Dict[str, Any],
    output_path: Optional[str] = None,
    include_timeline: bool = True,
    include_details: bool = True,
) -> str:
    """Convenience function to generate HTML report

    Args:
        result: Evaluation result dict from QualityLoop
        output_path: Optional file path to save HTML
        include_timeline: Include score timeline chart
        include_details: Include detailed failed rules breakdown

    Returns:
        HTML content as string
    """
    generator = HTMLReportGenerator()
    return generator.generate(result, output_path, include_timeline, include_details)
