"""
Live Quality Progress Display

Real-time progress tracking and visualization for quality loop iterations.
Provides animated terminal displays with ANSI colors, ETA calculation, and phase indicators.

Building on:
- Exp 99: ASCII-based terminal visualization
- Exp 100: ANSI color support and terminal detection
"""

import sys
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from threading import Lock, Thread
import io

from specify_cli.quality.terminal_colors import (
    TerminalInfo,
    ColorTheme,
    ColorScheme,
    ANSI,
    detect_terminal_capabilities,
    reset_terminal_cache,
)


class ProgressPhase(Enum):
    """Quality loop phases for progress display"""
    INIT = "initialize"
    EVALUATE = "evaluate"
    CRITIQUE = "critique"
    REFINE = "refine"
    COMPLETE = "complete"
    ERROR = "error"


class AnimationStyle(Enum):
    """Animation styles for progress indicators"""
    SPINNER = "spinner"
    DOTS = "dots"
    BAR = "bar"
    PULSE = "pulse"
    NONE = "none"


@dataclass
class ProgressState:
    """Current progress state"""
    phase: ProgressPhase = ProgressPhase.INIT
    iteration: int = 1
    max_iterations: int = 4
    current_phase_letter: str = "A"  # Phase A or B
    score: Optional[float] = None
    previous_score: Optional[float] = None
    passed: bool = False
    failed_rules_count: int = 0
    start_time: float = field(default_factory=time.time)
    phase_start_time: float = field(default_factory=time.time)
    last_update_time: float = field(default_factory=time.time)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProgressConfig:
    """Configuration for progress display"""
    enabled: bool = True
    animation_style: AnimationStyle = AnimationStyle.SPINNER
    show_eta: bool = True
    show_score_history: bool = True
    show_phase_indicator: bool = True
    show_iteration_progress: bool = True
    compact_mode: bool = False
    update_interval: float = 0.1  # Seconds between updates
    theme: Dict[str, str] = field(default_factory=lambda: ColorTheme.DEFAULT)

    # Terminal capability overrides (auto-detected if None)
    supports_ansi: Optional[bool] = None
    supports_unicode: Optional[bool] = None
    width: Optional[int] = None


class ProgressTracker:
    """
    Tracks and displays real-time progress for quality loop iterations.

    Features:
    - Animated progress indicators (spinner, dots, bar, pulse)
    - Live score updates with trend indicators
    - ETA calculation based on iteration timing
    - Phase transition notifications
    - Terminal-aware display (ANSI colors, Unicode, width detection)
    - Thread-safe state updates
    - Compact mode for narrow terminals
    """

    # Animation frames for different styles
    SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    DOT_FRAMES = ["⠁", "⠃", "⠇", "⡆", "⡇"]
    PULSE_FRAMES = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"]

    # ASCII fallbacks for non-Unicode terminals
    ASCII_SPINNER = ["-", "/", "|", "\\"]
    ASCII_DOTS = [".", "o", "O", "o"]
    ASCII_BAR = ["[=   ]", "[==  ]", "[=== ]", "[====]"]

    def __init__(self, config: Optional[ProgressConfig] = None):
        """Initialize progress tracker

        Args:
            config: Optional progress configuration
        """
        self.config = config or ProgressConfig()
        self.state = ProgressState()
        self._lock = Lock()
        self._frame_index = 0
        self._last_display = ""
        self._score_history: List[float] = []

        # Detect terminal capabilities
        self._terminal_info = self._detect_terminal()

        # Setup ANSI codes based on theme
        self._setup_ansi()

    def _detect_terminal(self) -> TerminalInfo:
        """Detect terminal capabilities for display formatting"""
        # Apply config overrides if set
        overrides = {}
        if self.config.supports_ansi is not None:
            overrides["supports_ansi"] = self.config.supports_ansi
        if self.config.supports_unicode is not None:
            overrides["supports_unicode"] = self.config.supports_unicode
        if self.config.width is not None:
            overrides["width"] = self.config.width

        return detect_terminal_capabilities(**overrides)

    def _setup_ansi(self):
        """Setup ANSI color codes based on terminal and theme"""
        self.ansi = ANSI(
            scheme=ColorScheme.BASIC if self._terminal_info.supports_ansi else ColorScheme.NONE,
            theme=self.config.theme,
        )
        self._supports_colors = self._terminal_info.supports_ansi
        self._supports_unicode = self._terminal_info.supports_unicode

    def _get_frames(self) -> List[str]:
        """Get animation frames based on terminal support"""
        style = self.config.animation_style

        if not self._supports_unicode:
            # ASCII fallbacks
            if style == AnimationStyle.SPINNER:
                return self.ASCII_SPINNER
            elif style == AnimationStyle.DOTS:
                return self.ASCII_DOTS
            elif style == AnimationStyle.BAR:
                return self.ASCII_BAR
            return [""]

        if style == AnimationStyle.SPINNER:
            return self.SPINNER_FRAMES
        elif style == AnimationStyle.DOTS:
            return self.DOT_FRAMES
        elif style == AnimationStyle.PULSE:
            return self.PULSE_FRAMES
        return [""]

    def _get_current_frame(self) -> str:
        """Get current animation frame"""
        frames = self._get_frames()
        if not frames:
            return ""
        frame = frames[self._frame_index % len(frames)]
        self._frame_index += 1
        return frame

    def _colorize(self, text: str, color_func: Optional[Callable] = None) -> str:
        """Apply color to text if supported"""
        if not self._supports_colors or color_func is None:
            return text
        return color_func(text)

    def _reset_line(self) -> str:
        """Get ANSI escape sequence to reset line"""
        if self._supports_colors:
            return "\r\033[K"
        return "\r" + " " * 80 + "\r"

    def calculate_eta(self) -> Optional[timedelta]:
        """Calculate estimated time remaining

        Returns:
            timedelta of estimated remaining time, or None if insufficient data
        """
        if self.state.iteration <= 1:
            return None

        elapsed = time.time() - self.state.start_time
        iterations_completed = self.state.iteration - 1

        if iterations_completed < 1:
            return None

        # Average time per iteration
        avg_time = elapsed / iterations_completed

        # Estimate remaining iterations
        # Account for possible phase A -> B transition
        remaining_iterations = (self.state.max_iterations * 2) - (self.state.iteration * 2 - (1 if self.state.current_phase_letter == "A" else 0))

        return timedelta(seconds=avg_time * remaining_iterations / 2)

    def format_score_bar(self, score: float, width: int = 20) -> str:
        """Format a visual score progress bar

        Args:
            score: Score value (0-1)
            width: Bar width in characters

        Returns:
            Formatted bar string
        """
        filled = int(score * width)
        empty = width - filled

        if self._supports_unicode:
            filled_char = "█"
            empty_char = "░"
        else:
            filled_char = "#"
            empty_char = "-"

        # Color based on score
        if score >= 0.9:
            color = self.ansi.green
        elif score >= 0.8:
            color = self.ansi.yellow
        elif score >= 0.6:
            color = self.ansi.bright_yellow
        else:
            color = self.ansi.red

        bar = self._colorize(filled_char * filled, color) + empty_char * empty
        return f"[{bar}] {score:.2f}"

    def format_phase_indicator(self) -> str:
        """Format the current phase indicator (A/B)"""
        phase = self.state.current_phase_letter

        if self._supports_colors:
            if phase == "A":
                return self._colorize(f"Phase {phase}", self.ansi.cyan)
            else:
                return self._colorize(f"Phase {phase}", self.ansi.bright_cyan)
        return f"Phase {phase}"

    def get_display_text(self) -> str:
        """Generate current progress display text

        Returns:
            Formatted progress display string
        """
        if self.config.compact_mode:
            return self._get_compact_display()
        return self._get_full_display()

    def _get_compact_display(self) -> str:
        """Generate compact single-line progress display"""
        frame = self._get_current_frame()
        phase = self.format_phase_indicator()
        iteration = f"{self.state.iteration}/{self.state.max_iterations}"

        # Score display
        if self.state.score is not None:
            score_text = f"{self.state.score:.2f}"
            # Add trend indicator
            if self.state.previous_score is not None:
                delta = self.state.score - self.state.previous_score
                if delta > 0.01:
                    trend = self._colorize("↑", self.ansi.green)
                elif delta < -0.01:
                    trend = self._colorize("↓", self.ansi.red)
                else:
                    trend = self._colorize("→", self.ansi.gray)
                score_text += f" {trend}"
        else:
            score_text = "..."
            trend = ""

        # Phase indicator
        phase_indicator = self._colorize(
            self.state.phase.value.upper(),
            self.ansi.bright_blue if self.state.phase != ProgressPhase.ERROR else self.ansi.red
        )

        parts = [
            frame,
            phase,
            iteration,
            phase_indicator,
            score_text,
        ]

        # ETA
        if self.config.show_eta:
            eta = self.calculate_eta()
            if eta:
                parts.append(f"ETA:{self._format_eta(eta)}")

        return " ".join(parts)

    def _get_full_display(self) -> str:
        """Generate full multi-line progress display"""
        lines = []

        # Header line with spinner and phase
        frame = self._get_current_frame() if self.config.animation_style != AnimationStyle.NONE else ""
        phase_text = self._colorize(
            self.state.phase.value.upper(),
            self.ansi.bright_blue if self.state.phase != ProgressPhase.ERROR else self.ansi.red
        )
        lines.append(f"{frame} {phase_text}: {self.state.message}")

        # Progress info
        if self.config.show_iteration_progress:
            phase = self.format_phase_indicator()
            iteration = f"{self.state.iteration}/{self.state.max_iterations}"
            lines.append(f"  {phase} | Iteration {iteration}")

        # Score bar
        if self.state.score is not None:
            bar = self.format_score_bar(self.state.score, width=30)

            # Add trend
            if self.config.show_score_history and self.state.previous_score is not None:
                delta = self.state.score - self.state.previous_score
                if abs(delta) >= 0.01:
                    delta_str = f"({delta:+.2f})"
                    if delta > 0:
                        delta_str = self._colorize(delta_str, self.ansi.green)
                    elif delta < 0:
                        delta_str = self._colorize(delta_str, self.ansi.red)
                    bar += f" {delta_str}"

            lines.append(f"  Score: {bar}")

        # Failed rules count
        if self.state.failed_rules_count > 0:
            count_text = self._colorize(str(self.state.failed_rules_count), self.ansi.red)
            lines.append(f"  Failed rules: {count_text}")

        # ETA
        if self.config.show_eta:
            eta = self.calculate_eta()
            if eta:
                lines.append(f"  ETA: {self._format_eta(eta)}")

        # Timing info
        elapsed = time.time() - self.state.start_time
        lines.append(f"  Elapsed: {self._format_duration(elapsed)}")

        return "\n".join(lines)

    def _format_eta(self, eta: timedelta) -> str:
        """Format ETA for display"""
        total_seconds = int(eta.total_seconds())
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def _format_duration(self, seconds: float) -> str:
        """Format duration for display"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.0f}s"

    def update(self, **kwargs) -> None:
        """Update progress state

        Args:
            **kwargs: State fields to update (phase, iteration, score, etc.)
        """
        with self._lock:
            # Update phase start time if phase changed
            if "phase" in kwargs and kwargs["phase"] != self.state.phase:
                self.state.phase_start_time = time.time()

            # Update score history if score changed
            if "score" in kwargs and kwargs["score"] != self.state.score:
                if self.state.score is not None:
                    self.state.previous_score = self.state.score
                self.state.score = kwargs["score"]
                self._score_history.append(self.state.score)

            # Update state
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)

            self.state.last_update_time = time.time()

    def display(self, file=None) -> None:
        """Display current progress

        Args:
            file: File object to write to (default: sys.stderr)
        """
        if not self.config.enabled:
            return

        if file is None:
            file = sys.stderr

        display_text = self.get_display_text()

        # Clear previous display and show new one
        file.write(self._reset_line())
        file.write(display_text)
        file.flush()

        self._last_display = display_text

    def finish(self, success: bool = True, final_message: str = "") -> None:
        """Finish progress display with final status

        Args:
            success: Whether the operation succeeded
            final_message: Optional final message to display
        """
        with self._lock:
            self.state.phase = ProgressPhase.COMPLETE if success else ProgressPhase.ERROR
            self.state.message = final_message or ("Complete" if success else "Error")

        # Show final state
        self.display()

        # Add newline to finalize
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr.write("\n")
            sys.stderr.flush()


class LiveProgressContext:
    """
    Context manager for automatic progress display during quality loop.

    Usage:
        with LiveProgressContext(config) as progress:
            progress.update(phase=ProgressPhase.EVALUATE, iteration=1)
            # ... do work ...
            progress.update(score=0.75)
    """

    def __init__(self, config: Optional[ProgressConfig] = None):
        """Initialize live progress context

        Args:
            config: Optional progress configuration
        """
        self.config = config or ProgressConfig()
        self.tracker: Optional[ProgressTracker] = None
        self._update_thread: Optional[Thread] = None
        self._running = False

    def __enter__(self) -> "LiveProgressContext":
        """Enter context, start progress display"""
        self.tracker = ProgressTracker(self.config)
        self._running = True

        # Start update thread for animations
        if self.config.animation_style != AnimationStyle.NONE:
            self._update_thread = Thread(target=self._update_loop, daemon=True)
            self._update_thread.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context, stop progress display"""
        self._running = False

        if self._update_thread:
            self._update_thread.join(timeout=0.5)

        # Show final state
        success = exc_type is None
        message = "" if success else str(exc_val)
        self.tracker.finish(success=success, final_message=message)

    def _update_loop(self) -> None:
        """Background thread loop for updating animations"""
        while self._running and self.tracker:
            self.tracker.display()
            time.sleep(self.config.update_interval)

    def update(self, **kwargs) -> None:
        """Update progress state"""
        if self.tracker:
            self.tracker.update(**kwargs)

    def display(self) -> None:
        """Force display update"""
        if self.tracker:
            self.tracker.display()


# Convenience functions for creating progress displays

def create_progress_config(
    enabled: bool = True,
    animation_style: str = "spinner",
    compact: bool = False,
    theme: str = "default",
) -> ProgressConfig:
    """Create progress configuration from common parameters

    Args:
        enabled: Enable progress display
        animation_style: Animation style (spinner, dots, bar, pulse, none)
        compact: Use compact single-line display
        theme: Color theme (default, dark, high-contrast, minimal)

    Returns:
        ProgressConfig instance
    """
    style_map = {
        "spinner": AnimationStyle.SPINNER,
        "dots": AnimationStyle.DOTS,
        "bar": AnimationStyle.BAR,
        "pulse": AnimationStyle.PULSE,
        "none": AnimationStyle.NONE,
    }

    theme_map = {
        "default": ColorTheme.DEFAULT,
        "dark": ColorTheme.DARK,
        "high-contrast": ColorTheme.HIGH_CONTRAST,
        "minimal": ColorTheme.MINIMAL,
    }

    return ProgressConfig(
        enabled=enabled,
        animation_style=style_map.get(animation_style, AnimationStyle.SPINNER),
        compact_mode=compact,
        theme=theme_map.get(theme, ColorTheme.DEFAULT),
    )


def track_quality_progress(
    enabled: bool = True,
    animation: str = "spinner",
    compact: bool = False,
    theme: str = "default",
) -> LiveProgressContext:
    """Create a live progress context for quality loop tracking

    Args:
        enabled: Enable progress display
        animation: Animation style (spinner, dots, bar, pulse, none)
        compact: Use compact single-line display
        theme: Color theme (default, dark, high-contrast, minimal)

    Returns:
        LiveProgressContext for use as context manager

    Example:
        with track_quality_progress() as progress:
            progress.update(phase=ProgressPhase.EVALUATE, iteration=1)
            # ... evaluation work ...
            progress.update(score=0.75, phase=ProgressPhase.CRITIQUE)
            # ... critique work ...
            progress.finish(success=True)
    """
    config = create_progress_config(
        enabled=enabled,
        animation_style=animation,
        compact=compact,
        theme=theme,
    )
    return LiveProgressContext(config)


# Progress callback type for integration with QualityLoop
ProgressCallback = Callable[[ProgressState], None]


def create_progress_callback(
    enabled: bool = True,
    animation: str = "spinner",
    compact: bool = False,
) -> Optional[ProgressCallback]:
    """Create a progress callback for QualityLoop integration

    Args:
        enabled: Enable progress display
        animation: Animation style
        compact: Use compact mode

    Returns:
        Callback function or None if disabled

    Example integration with QualityLoop:
        callback = create_progress_callback(compact=True)
        result = loop.run(
            artifact=artifact,
            task_alias="test",
            criteria_name="backend",
            progress_callback=callback,
        )
    """
    if not enabled:
        return None

    config = create_progress_config(enabled=True, animation_style=animation, compact=compact)
    tracker = ProgressTracker(config)

    def callback(state: ProgressState) -> None:
        """Update and display progress"""
        # Update tracker state from state
        tracker.phase = state.phase
        tracker.iteration = state.iteration
        tracker.score = state.score
        tracker.message = state.message
        tracker.display()

    return callback
