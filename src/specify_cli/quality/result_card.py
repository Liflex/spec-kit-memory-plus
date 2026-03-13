"""
Final Result Card with Actionable Summary (Exp 102)

Provides a visually appealing, actionable summary after quality loop completion.
Builds on:
- Exp 100: ANSI color system
- Exp 101: Live progress display
- ASCII/Unicode visualization for terminals

Features:
- Compact summary card with key metrics
- Category-grouped failed rules
- Actionable next steps
- Terminal-aware formatting (ANSI colors, Unicode/ASCII fallbacks)
- Trend indicators when history is available
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import re

from specify_cli.quality.terminal_colors import (
    TerminalInfo,
    ColorTheme,
    ColorScheme,
    ANSI,
    detect_terminal_capabilities,
)


class ResultStatus(Enum):
    """Quality result status"""
    EXCELLENT = "excellent"  # 0.95+ score, no failed rules
    GOOD = "good"  # 0.85+ score
    ACCEPTABLE = "acceptable"  # 0.75+ score
    NEEDS_WORK = "needs_work"  # 0.65+ score
    CRITICAL = "critical"  # < 0.65 score


@dataclass
class CategorySummary:
    """Summary of issues by category"""
    category: str
    failed_count: int
    warning_count: int
    total_count: int
    priority: str  # critical, high, medium, low
    sample_rules: List[str] = field(default_factory=list)


@dataclass
class ActionItem:
    """Actionable next step"""
    priority: str  # critical, high, medium, low
    title: str
    command: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ResultCardData:
    """Data for result card display"""
    score: float
    passed: bool
    status: ResultStatus
    iteration: int
    max_iterations: int
    phase: str
    total_rules: int
    passed_rules: int
    failed_rules: int
    warnings: int
    duration_seconds: float = 0.0
    category_summaries: List[CategorySummary] = field(default_factory=list)
    action_items: List[ActionItem] = field(default_factory=list)
    priority_profile: str = "default"
    trend_change: Optional[float] = None  # Score change from previous run
    gate_status: Optional[str] = None  # Quality gate status if checked


class ResultCardFormatter:
    """
    Formats quality results as visually appealing console output.

    Features:
    - Terminal-aware colors and formatting
    - Unicode/ASCII fallbacks for different terminals
    - Compact vs detailed display modes
    - Grouped by category with priority indicators
    """

    # Unicode box-drawing characters (for capable terminals)
    BOX_CHARS = {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "h": "─", "v": "│",
        "hl": "├", "hr": "┤", "ht": "┬", "hb": "┴",
        "cross": "┼",
    }

    # ASCII fallbacks
    ASCII_BOX = {
        "tl": "+", "tr": "+", "bl": "+", "br": "+",
        "h": "-", "v": "|",
        "hl": "+", "hr": "+", "ht": "+", "hb": "+",
        "cross": "+",
    }

    # Status emojis with ASCII fallbacks
    STATUS_ICONS = {
        ResultStatus.EXCELLENT: ("🌟", "★"),
        ResultStatus.GOOD: ("✓", "v"),
        ResultStatus.ACCEPTABLE: ("◐", "o"),
        ResultStatus.NEEDS_WORK: ("⚠", "!"),
        ResultStatus.CRITICAL: ("✕", "X"),
    }

    # Category icons
    CATEGORY_ICONS = {
        "security": ("🔒", "[SEC]"),
        "performance": ("⚡", "[PERF]"),
        "testing": ("🧪", "[TEST]"),
        "documentation": ("📚", "[DOC]"),
        "correctness": ("✅", "[OK]"),
        "infrastructure": ("🏗️", "[INFRA]"),
        "code_quality": ("✨", "[QUAL]"),
        "observability": ("📊", "[OBS]"),
        "reliability": ("🛡️", "[REL]"),
        "cicd": ("🔄", "[CI/CD]"),
        "api": ("🔌", "[API]"),
        "database": ("💾", "[DB]"),
        "frontend": ("🎨", "[FE]"),
        "backend": ("⚙️", "[BE]"),
        "general": ("📋", "[GEN]"),
    }

    # Priority colors
    PRIORITY_COLORS = {
        "critical": "red",
        "high": "bright_red",
        "medium": "yellow",
        "low": "gray",
    }

    def __init__(
        self,
        theme: ColorTheme = ColorTheme.DEFAULT,
        compact: bool = False,
        use_unicode: Optional[bool] = None,
        use_colors: Optional[bool] = None,
    ):
        """Initialize result card formatter

        Args:
            theme: Color theme for output
            compact: Use compact single-line format
            use_unicode: Force Unicode (None = auto-detect)
            use_colors: Force colors (None = auto-detect)
        """
        self.compact = compact
        self._terminal_info = detect_terminal_capabilities()
        self._supports_unicode = use_unicode if use_unicode is not None else self._terminal_info.supports_unicode
        self._supports_colors = use_colors if use_colors is not None else self._terminal_info.supports_ansi

        # Setup ANSI codes
        scheme = ColorScheme.BASIC if self._supports_colors else ColorScheme.NONE
        self.ansi = ANSI(scheme=scheme, theme=theme)

        # Select character set
        self.box = self.BOX_CHARS if self._supports_unicode else self.ASCII_BOX

    def _icon(self, icon_tuple: Tuple[str, str]) -> str:
        """Get icon based on terminal support"""
        return icon_tuple[0] if self._supports_unicode else icon_tuple[1]

    def _status_icon(self, status: ResultStatus) -> str:
        """Get status icon"""
        return self._icon(self.STATUS_ICONS.get(status, self.STATUS_ICONS[ResultStatus.GOOD]))

    def _category_icon(self, category: str) -> str:
        """Get category icon"""
        cat_key = category.lower().replace("-", "_").replace(" ", "_")
        return self._icon(self.CATEGORY_ICONS.get(cat_key, self.CATEGORY_ICONS["general"]))

    def _colorize(self, text: str, color_name: str = "white") -> str:
        """Apply color to text if supported"""
        if not self._supports_colors:
            return text

        color_func = getattr(self.ansi, color_name, None)
        if color_func:
            return color_func(text)
        return text

    def _draw_box(self, lines: List[str], width: int = 60) -> str:
        """Draw a box around content"""
        if self.compact:
            # Compact mode: just join lines with spacing
            return "\n".join(lines)

        # Full box mode
        result = []
        h_bar = self.box["h"] * (width - 2)

        # Top border
        result.append(self.box["tl"] + h_bar + self.box["tr"])

        # Content lines
        for line in lines:
            # Pad line to width
            # Strip ANSI codes for width calculation
            plain_line = re.sub(r'\033\[[0-9;]*m', '', line)
            padding = max(0, width - 2 - len(plain_line))
            result.append(self.box["v"] + line + " " * padding + self.box["v"])

        # Bottom border
        result.append(self.box["bl"] + h_bar + self.box["br"])

        return "\n".join(result)

    def _get_status_color(self, status: ResultStatus) -> str:
        """Get color name for status"""
        colors = {
            ResultStatus.EXCELLENT: "green",
            ResultStatus.GOOD: "cyan",
            ResultStatus.ACCEPTABLE: "yellow",
            ResultStatus.NEEDS_WORK: "bright_yellow",
            ResultStatus.CRITICAL: "red",
        }
        return colors.get(status, "white")

    def _get_priority_color(self, priority: str) -> str:
        """Get color name for priority"""
        return self.PRIORITY_COLORS.get(priority.lower(), "gray")

    def _format_score_bar(self, score: float, width: int = 15) -> str:
        """Format a visual score bar"""
        filled = int(score * width)
        empty = width - filled

        if self._supports_unicode:
            filled_char = "█"
            empty_char = "░"
        else:
            filled_char = "#"
            empty_char = "."

        # Color based on score
        if score >= 0.9:
            color = "green"
        elif score >= 0.8:
            color = "cyan"
        elif score >= 0.7:
            color = "yellow"
        else:
            color = "red"

        filled_bar = self._colorize(filled_char * filled, color)
        return f"[{filled_bar}{empty_char * empty}]"

    def _format_duration(self, seconds: float) -> str:
        """Format duration for display"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            mins = int(seconds // 60)
            secs = seconds % 60
            return f"{mins}m {secs:.0f}s"

    def _determine_status(self, data: ResultCardData) -> ResultStatus:
        """Determine overall status from result data"""
        score = data.score

        # Critical if many failed rules
        if data.failed_rules > 5 or score < 0.65:
            return ResultStatus.CRITICAL
        # Excellent if perfect score
        elif score >= 0.95 and data.failed_rules == 0:
            return ResultStatus.EXCELLENT
        # Good if high score
        elif score >= 0.85:
            return ResultStatus.GOOD
        # Acceptable if medium score
        elif score >= 0.75:
            return ResultStatus.ACCEPTABLE
        # Otherwise needs work
        else:
            return ResultStatus.NEEDS_WORK

    def _generate_action_items(self, data: ResultCardData) -> List[ActionItem]:
        """Generate actionable next steps"""
        actions = []

        # Critical failed rules first
        for cat_summary in data.category_summaries:
            if cat_summary.failed_count > 0:
                priority = cat_summary.priority
                actions.append(ActionItem(
                    priority=priority,
                    title=f"Fix {cat_summary.failed_count} {cat_summary} issue(s)",
                    description=f"Focus on: {', '.join(cat_summary.sample_rules[:3])}"
                ))

        # Score improvement
        if data.score < 0.9:
            priority = "high" if data.score < 0.8 else "medium"
            actions.append(ActionItem(
                priority=priority,
                title=f"Improve quality score ({data.score:.2f} → 0.90)",
                command="speckit.loop --suggest-goals"
            ))

        # Set up goals if none exist
        if data.score < 0.85:
            actions.append(ActionItem(
                priority="medium",
                title="Set quality goals for tracking",
                command="speckit.goals suggest"
            ))

        return actions

    def format(self, data: ResultCardData) -> str:
        """Format result card as console output

        Args:
            data: Result card data

        Returns:
            Formatted console output string
        """
        # Determine status
        if isinstance(data.status, str):
            data.status = ResultStatus(data.status)
        status = data.status if data.status in ResultStatus else self._determine_status(data)

        # Build lines
        lines = []

        # Header line with status
        status_icon = self._status_icon(status)
        status_color = self._get_status_color(status)
        status_text = self._colorize(f"{status_icon} {status.value.upper().replace('_', ' ')}", status_color)
        score_text = f"Score: {data.score:.2f}"
        lines.append(f"{status_text}  |  {score_text}")

        # Score bar
        score_bar = self._format_score_bar(data.score)
        lines.append(score_bar)

        # Quick stats (compact mode combines these)
        if self.compact:
            stats_parts = [
                f"Iteration: {data.iteration}/{data.max_iterations}",
                f"Rules: {data.passed_rules}/{data.total_rules}",
            ]
            if data.duration_seconds > 0:
                stats_parts.append(f"Time: {self._format_duration(data.duration_seconds)}")
            lines.append(" | ".join(stats_parts))
        else:
            lines.append(f"  Iteration: {data.iteration}/{data.max_iterations} (Phase {data.phase})")
            lines.append(f"  Rules: {self._colorize(str(data.passed_rules), 'green')}/{data.total_rules} passed")
            if data.failed_rules > 0:
                lines.append(f"  Failed: {self._colorize(str(data.failed_rules), 'red')} | Warnings: {data.warnings}")
            if data.duration_seconds > 0:
                lines.append(f"  Duration: {self._format_duration(data.duration_seconds)}")

        # Trend indicator if available
        if data.trend_change is not None:
            trend_icon = "↑" if data.trend_change > 0 else "↓" if data.trend_change < 0 else "→"
            trend_color = "green" if data.trend_change > 0 else "red" if data.trend_change < 0 else "gray"
            trend_text = self._colorize(f"{trend_icon} {abs(data.trend_change):+.2f}", trend_color)
            lines.append(f"  Trend: {trend_text} from previous run")

        # Gate status if available
        if data.gate_status:
            gate_passed = data.gate_status.upper() == "PASSED"
            gate_icon = "✓" if gate_passed else "✕"
            gate_color = "green" if gate_passed else "red"
            lines.append(f"  Gate: {self._colorize(f'{gate_icon} {data.gate_status}', gate_color)}")

        # Category breakdown (if issues exist)
        if data.category_summaries and not self.compact:
            lines.append("")  # blank line separator
            lines.append("Issues by Category:")
            for cat in data.category_summaries[:5]:  # Top 5 categories
                cat_icon = self._category_icon(cat.category)
                cat_color = self._get_priority_color(cat.priority)
                cat_text = self._colorize(f"{cat_icon} {cat.category}", cat_color)
                count_text = f"{cat.failed_count} failed"
                lines.append(f"  {cat_text}: {count_text}")

        # Action items
        if not data.action_items:
            data.action_items = self._generate_action_items(data)

        if data.action_items:
            lines.append("")  # blank line separator
            lines.append("Next Steps:")

            # Show top 3 actions
            for i, action in enumerate(data.action_items[:3], 1):
                priority_color = self._get_priority_color(action.priority)
                priority_mark = self._colorize(f"({action.priority[0].upper()})", priority_color)

                if action.command:
                    lines.append(f"  {i}. {priority_mark} {action.title}")
                    lines.append(f"     → {action.command}")
                else:
                    lines.append(f"  {i}. {priority_mark} {action.title}")

        # Draw box (unless compact)
        if self.compact:
            return "\n".join(lines)
        else:
            return self._draw_box(lines, width=max(60, max(len(line) for line in lines) + 4))


def create_result_card_data(
    result: Dict[str, Any],
    previous_score: Optional[float] = None,
) -> ResultCardData:
    """Create ResultCardData from quality loop result

    Args:
        result: Quality loop result dict
        previous_score: Previous run score for trend calculation

    Returns:
        ResultCardData populated with result information
    """
    state = result.get("state", {})
    evaluation = state.get("evaluation", {})
    gate_result = result.get("gate_result")

    # Basic metrics
    score = result.get("score", 0.0)
    passed = result.get("passed", False)
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 4)
    phase = state.get("phase", "A")

    # Rule counts
    total_rules = evaluation.get("total_rules", 0)
    passed_rules = evaluation.get("passed_rules", 0)
    failed_rules = evaluation.get("failed_rules", 0)
    warnings = len(evaluation.get("warnings", []))

    # Duration (if available from history)
    duration = 0.0
    if "duration_seconds" in result:
        duration = result["duration_seconds"]

    # Category summaries
    category_summaries = _create_category_summaries(evaluation)

    # Determine status
    if failed_rules == 0 and score >= 0.9:
        status = ResultStatus.EXCELLENT
    elif score >= 0.85:
        status = ResultStatus.GOOD
    elif score >= 0.75:
        status = ResultStatus.ACCEPTABLE
    elif score >= 0.65:
        status = ResultStatus.NEEDS_WORK
    else:
        status = ResultStatus.CRITICAL

    # Gate status
    gate_status = None
    if gate_result:
        gate_status = gate_result.get("gate_result", "unknown")

    # Priority profile
    priority_profile = result.get("priority_profile", "default")

    return ResultCardData(
        score=score,
        passed=passed,
        status=status,
        iteration=iteration,
        max_iterations=max_iterations,
        phase=phase,
        total_rules=total_rules,
        passed_rules=passed_rules,
        failed_rules=failed_rules,
        warnings=warnings,
        duration_seconds=duration,
        category_summaries=category_summaries,
        action_items=[],
        priority_profile=priority_profile,
        trend_change=(score - previous_score) if previous_score is not None else None,
        gate_status=gate_status,
    )


def _create_category_summaries(evaluation: Dict[str, Any]) -> List[CategorySummary]:
    """Create category summaries from evaluation result

    Args:
        evaluation: Evaluation dict from quality loop

    Returns:
        List of CategorySummary sorted by priority and count
    """
    failed_rules = evaluation.get("failed_rules", [])

    # Group by category
    from collections import defaultdict
    category_rules = defaultdict(list)

    for rule in failed_rules:
        category = rule.get("category", "general")
        category_rules[category].append(rule)

    # Create summaries
    summaries = []
    for category, rules in category_rules.items():
        count = len(rules)

        # Determine priority based on count and severity
        if count >= 5:
            priority = "critical"
        elif count >= 3:
            priority = "high"
        elif count >= 1:
            priority = "medium"
        else:
            priority = "low"

        # Get sample rule IDs
        sample_rules = [r.get("rule_id", r.get("id", "unknown")) for r in rules[:3]]

        summaries.append(CategorySummary(
            category=category,
            failed_count=count,
            warning_count=0,  # Warnings handled separately
            total_count=count,
            priority=priority,
            sample_rules=sample_rules,
        ))

    # Sort: priority (critical first) then count (high first)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    summaries.sort(key=lambda s: (priority_order.get(s.priority, 4), -s.failed_count))

    return summaries


def format_result_card(
    result: Dict[str, Any],
    previous_score: Optional[float] = None,
    compact: bool = False,
    theme: str = "default",
) -> str:
    """Format a result card from quality loop result

    Args:
        result: Quality loop result dict
        previous_score: Previous run score for trend indicator
        compact: Use compact single-line format
        theme: Color theme (default, dark, high-contrast, minimal)

    Returns:
        Formatted result card string

    Example:
        result = loop.run(artifact="...", criteria_name="backend")
        print(format_result_card(result, compact=True))
    """
    theme_map = {
        "default": ColorTheme.DEFAULT,
        "dark": ColorTheme.DARK,
        "high-contrast": ColorTheme.HIGH_CONTRAST,
        "minimal": ColorTheme.MINIMAL,
    }

    data = create_result_card_data(result, previous_score)
    formatter = ResultCardFormatter(
        theme=theme_map.get(theme, ColorTheme.DEFAULT),
        compact=compact,
    )

    return formatter.format(data)


def print_result_card(
    result: Dict[str, Any],
    previous_score: Optional[float] = None,
    compact: bool = False,
    theme: str = "default",
) -> None:
    """Print result card directly to console

    Args:
        result: Quality loop result dict
        previous_score: Previous run score for trend indicator
        compact: Use compact single-line format
        theme: Color theme

    Example:
        result = loop.run(artifact="...", criteria_name="backend")
        print_result_card(result)
    """
    card = format_result_card(result, previous_score, compact, theme)
    print()
    print(card)
    print()
