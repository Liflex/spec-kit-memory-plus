"""
Terminal Colors and ANSI Support

Provides terminal capability detection, ANSI color codes,
color themes, and colorization utilities for CLI output.
Extracted from pareto_visualization.py (Exp 100) during cleanup.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import os
import sys


class ColorScheme(Enum):
    """Color schemes for visualizations."""
    NONE = "none"
    BASIC = "basic"
    EXTENDED = "extended"
    TRUECOLOR = "truecolor"


class ANSI:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"

    # Basic colors (foreground)
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright variants
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    INVERSE = "\033[7m"

    @staticmethod
    def fg_256(color_code: int) -> str:
        return f"\033[38;5;{color_code}m"

    @staticmethod
    def bg_256(color_code: int) -> str:
        return f"\033[48;5;{color_code}m"

    @staticmethod
    def fg_rgb(r: int, g: int, b: int) -> str:
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        return f"\033[48;2;{r};{g};{b}m"


class ColorTheme:
    """Predefined color themes for visualizations."""

    DEFAULT = {
        "title": ANSI.BOLD + ANSI.CYAN,
        "header": ANSI.BOLD + ANSI.BLUE,
        "pareto": ANSI.GREEN,
        "highlight": ANSI.BRIGHT_YELLOW,
        "dominated": ANSI.DIM,
        "grid": ANSI.DIM,
        "axis": ANSI.BLUE,
        "legend": ANSI.CYAN,
        "good": ANSI.GREEN,
        "warning": ANSI.YELLOW,
        "bad": ANSI.RED,
        "info": ANSI.CYAN,
    }

    DARK = {
        "title": ANSI.BOLD + ANSI.BRIGHT_CYAN,
        "header": ANSI.BOLD + ANSI.BRIGHT_BLUE,
        "pareto": ANSI.BRIGHT_GREEN,
        "highlight": ANSI.BRIGHT_YELLOW,
        "dominated": ANSI.DIM,
        "grid": "\033[90m",
        "axis": ANSI.BRIGHT_BLUE,
        "legend": ANSI.BRIGHT_CYAN,
        "good": ANSI.BRIGHT_GREEN,
        "warning": ANSI.BRIGHT_YELLOW,
        "bad": ANSI.BRIGHT_RED,
        "info": ANSI.BRIGHT_CYAN,
    }

    MINIMAL = {
        "title": ANSI.BOLD,
        "header": "",
        "pareto": "",
        "highlight": ANSI.BOLD,
        "dominated": ANSI.DIM,
        "grid": "",
        "axis": "",
        "legend": "",
        "good": "",
        "warning": "",
        "bad": "",
        "info": "",
    }

    HIGH_CONTRAST = {
        "title": ANSI.BOLD + ANSI.BRIGHT_WHITE,
        "header": ANSI.BOLD + ANSI.WHITE,
        "pareto": ANSI.BRIGHT_WHITE,
        "highlight": ANSI.BRIGHT_YELLOW + ANSI.BOLD,
        "dominated": ANSI.DIM,
        "grid": ANSI.WHITE,
        "axis": ANSI.WHITE,
        "legend": ANSI.WHITE,
        "good": ANSI.BRIGHT_WHITE,
        "warning": ANSI.BRIGHT_YELLOW,
        "bad": ANSI.BRIGHT_RED + ANSI.BOLD,
        "info": ANSI.BRIGHT_CYAN,
    }


@dataclass
class TerminalInfo:
    """Information about terminal capabilities."""
    supports_colors: bool = False
    supports_256_colors: bool = False
    supports_truecolor: bool = False
    supports_unicode: bool = True
    is_ci: bool = False
    width: int = 80
    color_scheme: ColorScheme = ColorScheme.NONE
    theme: Dict[str, str] = field(default_factory=dict)

    def get_color(self, key: str) -> str:
        return self.theme.get(key, "")

    def colorize(self, text: str, color_key: str) -> str:
        if not self.supports_colors:
            return text
        color = self.get_color(color_key)
        if color:
            return f"{color}{text}{ANSI.RESET}"
        return text


def detect_terminal_capabilities() -> TerminalInfo:
    """Detect terminal capabilities for color and unicode support."""
    info = TerminalInfo()

    if os.environ.get("NO_COLOR"):
        info.color_scheme = ColorScheme.NONE
        info.supports_unicode = True
        return info

    ci_indicators = [
        "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS",
        "GITLAB_CI", "TRAVIS", "JENKINS_URL", "BUILDKITE",
        "CIRCLECI", "APPVEYOR", "CODEBUILD_BUILD_ID",
        "TF_BUILD", "AZURE_PIPELINES", "BITBUCKET_BUILD_NUMBER"
    ]
    info.is_ci = any(os.environ.get(k) for k in ci_indicators)

    if info.is_ci and not os.environ.get("FORCE_COLOR"):
        term = os.environ.get("TERM", "")
        if "color" in term.lower() or "xterm" in term.lower():
            info.supports_colors = True
            info.supports_256_colors = True
        else:
            info.color_scheme = ColorScheme.NONE
            info.supports_unicode = True
            return info

    try:
        import shutil
        info.width = shutil.get_terminal_size(fallback=(80, 24)).columns
    except Exception:
        info.width = 80

    term = os.environ.get("TERM", "")
    colorterm = os.environ.get("COLORTERM", "")

    if sys.platform == "win32":
        if os.environ.get("WT_SESSION") or os.environ.get("TERM_PROGRAM") == "vscode":
            info.supports_colors = True
            info.supports_256_colors = True
            info.supports_truecolor = True
        elif colorterm in ("truecolor", "24bit"):
            info.supports_colors = True
            info.supports_256_colors = True
            info.supports_truecolor = True
        else:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                info.supports_colors = True
            except Exception:
                info.supports_colors = False
    else:
        info.supports_colors = (
            "color" in term.lower() or
            "xterm" in term.lower() or
            "screen" in term.lower() or
            "tmux" in term.lower() or
            bool(os.environ.get("FORCE_COLOR"))
        )
        info.supports_256_colors = (
            info.supports_colors and (
                "256color" in term or
                colorterm in ("256color", "truecolor", "24bit")
            )
        )
        info.supports_truecolor = (
            colorterm in ("truecolor", "24bit") or
            os.environ.get("FORCE_COLOR") == "truecolor"
        )

    lang = os.environ.get("LANG", "")
    lc_all = os.environ.get("LC_ALL", "")
    info.supports_unicode = (
        "utf" in lang.lower() or
        "utf" in lc_all.lower() or
        sys.platform != "win32" or
        bool(os.environ.get("WT_SESSION"))
    )

    if info.supports_truecolor:
        info.color_scheme = ColorScheme.TRUECOLOR
    elif info.supports_256_colors:
        info.color_scheme = ColorScheme.EXTENDED
    elif info.supports_colors:
        info.color_scheme = ColorScheme.BASIC
    else:
        info.color_scheme = ColorScheme.NONE

    if info.color_scheme == ColorScheme.NONE:
        info.theme = ColorTheme.MINIMAL
    elif os.environ.get("COLOR_THEME") == "dark":
        info.theme = ColorTheme.DARK
    elif os.environ.get("COLOR_THEME") == "high-contrast":
        info.theme = ColorTheme.HIGH_CONTRAST
    elif os.environ.get("COLOR_THEME") == "minimal":
        info.theme = ColorTheme.MINIMAL
    else:
        info.theme = ColorTheme.DARK if info.supports_256_colors else ColorTheme.DEFAULT

    return info


_terminal_info: Optional[TerminalInfo] = None


def get_terminal_info() -> TerminalInfo:
    """Get cached terminal info."""
    global _terminal_info
    if _terminal_info is None:
        _terminal_info = detect_terminal_capabilities()
    return _terminal_info


def reset_terminal_cache():
    """Reset terminal info cache (for testing)."""
    global _terminal_info
    _terminal_info = None
