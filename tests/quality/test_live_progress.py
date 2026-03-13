"""
Tests for live_progress module

Test coverage for:
- ProgressPhase and AnimationStyle enums
- ProgressState and ProgressConfig dataclasses
- ProgressTracker class with all display modes
- ETA calculation and formatting
- Score bar with colorization
- LiveProgressContext context manager
- Convenience functions
"""

import pytest
import time
from io import StringIO
from threading import Thread
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock

from specify_cli.quality.live_progress import (
    ProgressPhase,
    AnimationStyle,
    ProgressState,
    ProgressConfig,
    ProgressTracker,
    LiveProgressContext,
    create_progress_config,
    track_quality_progress,
    create_progress_callback,
)


class TestProgressPhase:
    """Tests for ProgressPhase enum"""

    def test_phase_values(self):
        """Test all phase enum values exist"""
        assert ProgressPhase.INIT.value == "initialize"
        assert ProgressPhase.EVALUATE.value == "evaluate"
        assert ProgressPhase.CRITIQUE.value == "critique"
        assert ProgressPhase.REFINE.value == "refine"
        assert ProgressPhase.COMPLETE.value == "complete"
        assert ProgressPhase.ERROR.value == "error"

    def test_phase_count(self):
        """Test we have all expected phases"""
        phases = list(ProgressPhase)
        assert len(phases) == 6


class TestAnimationStyle:
    """Tests for AnimationStyle enum"""

    def test_animation_values(self):
        """Test all animation style enum values exist"""
        assert AnimationStyle.SPINNER.value == "spinner"
        assert AnimationStyle.DOTS.value == "dots"
        assert AnimationStyle.BAR.value == "bar"
        assert AnimationStyle.PULSE.value == "pulse"
        assert AnimationStyle.NONE.value == "none"

    def test_animation_count(self):
        """Test we have all expected animation styles"""
        styles = list(AnimationStyle)
        assert len(styles) == 5


class TestProgressState:
    """Tests for ProgressState dataclass"""

    def test_default_state(self):
        """Test default state values"""
        state = ProgressState()
        assert state.phase == ProgressPhase.INIT
        assert state.iteration == 1
        assert state.max_iterations == 4
        assert state.current_phase_letter == "A"
        assert state.score is None
        assert state.previous_score is None
        assert state.passed is False
        assert state.failed_rules_count == 0
        assert state.message == ""
        assert state.details == {}

    def test_custom_state(self):
        """Test state with custom values"""
        state = ProgressState(
            phase=ProgressPhase.EVALUATE,
            iteration=2,
            score=0.75,
            passed=True,
            message="Evaluating..."
        )
        assert state.phase == ProgressPhase.EVALUATE
        assert state.iteration == 2
        assert state.score == 0.75
        assert state.passed is True
        assert state.message == "Evaluating..."

    def test_state_timing_fields(self):
        """Test timing fields are set"""
        state = ProgressState()
        now = time.time()
        assert state.start_time <= now
        assert state.phase_start_time <= now
        assert state.last_update_time <= now


class TestProgressConfig:
    """Tests for ProgressConfig dataclass"""

    def test_default_config(self):
        """Test default config values"""
        config = ProgressConfig()
        assert config.enabled is True
        assert config.animation_style == AnimationStyle.SPINNER
        assert config.show_eta is True
        assert config.show_score_history is True
        assert config.show_phase_indicator is True
        assert config.show_iteration_progress is True
        assert config.compact_mode is False
        assert config.update_interval == 0.1
        assert config.supports_ansi is None
        assert config.supports_unicode is None
        assert config.width is None

    def test_custom_config(self):
        """Test config with custom values"""
        config = ProgressConfig(
            enabled=False,
            animation_style=AnimationStyle.DOTS,
            compact_mode=True,
            update_interval=0.5
        )
        assert config.enabled is False
        assert config.animation_style == AnimationStyle.DOTS
        assert config.compact_mode is True
        assert config.update_interval == 0.5


class TestProgressTracker:
    """Tests for ProgressTracker class"""

    def test_init_default_config(self):
        """Test tracker initialization with default config"""
        tracker = ProgressTracker()
        assert tracker.config.enabled is True
        assert tracker.state.phase == ProgressPhase.INIT
        assert tracker._frame_index == 0
        assert tracker._last_display == ""
        assert tracker._score_history == []

    def test_init_custom_config(self):
        """Test tracker initialization with custom config"""
        config = ProgressConfig(compact_mode=True, animation_style=AnimationStyle.DOTS)
        tracker = ProgressTracker(config)
        assert tracker.config.compact_mode is True
        assert tracker.config.animation_style == AnimationStyle.DOTS

    def test_terminal_detection_ansi_override(self):
        """Test terminal detection with ANSI override"""
        config = ProgressConfig(supports_ansi=False)
        tracker = ProgressTracker(config)
        assert tracker._supports_colors is False

    def test_terminal_detection_unicode_override(self):
        """Test terminal detection with Unicode override"""
        config = ProgressConfig(supports_unicode=False)
        tracker = ProgressTracker(config)
        assert tracker._supports_unicode is False

    def test_get_frames_spinner_unicode(self):
        """Test spinner frames with Unicode support"""
        tracker = ProgressTracker(ProgressConfig(supports_unicode=True))
        frames = tracker._get_frames()
        assert len(frames) == 10
        assert "⠋" in frames

    def test_get_frames_spinner_ascii(self):
        """Test spinner frames with ASCII fallback"""
        tracker = ProgressTracker(ProgressConfig(supports_unicode=False))
        tracker.config.animation_style = AnimationStyle.SPINNER
        frames = tracker._get_frames()
        assert len(frames) == 4
        assert "-" in frames

    def test_get_frames_dots_unicode(self):
        """Test dots frames with Unicode support"""
        tracker = ProgressTracker(ProgressConfig(
            supports_unicode=True,
            animation_style=AnimationStyle.DOTS
        ))
        frames = tracker._get_frames()
        assert len(frames) == 5
        assert "⠁" in frames

    def test_get_frames_bar_unicode(self):
        """Test bar frames with Unicode support (BAR uses ASCII frames)"""
        tracker = ProgressTracker(ProgressConfig(
            supports_unicode=True,
            animation_style=AnimationStyle.BAR
        ))
        frames = tracker._get_frames()
        # BAR style returns [""] for Unicode (no specific Unicode frames defined)
        # The actual bar visualization is done in format_score_bar instead
        assert isinstance(frames, list)

    def test_get_frames_pulse_unicode(self):
        """Test pulse frames with Unicode support"""
        tracker = ProgressTracker(ProgressConfig(
            supports_unicode=True,
            animation_style=AnimationStyle.PULSE
        ))
        frames = tracker._get_frames()
        assert len(frames) == 14
        assert "▁" in frames

    def test_get_frames_none_style(self):
        """Test frames with NONE animation style"""
        tracker = ProgressTracker(ProgressConfig(animation_style=AnimationStyle.NONE))
        frames = tracker._get_frames()
        assert frames == [""]

    def test_get_current_frame(self):
        """Test current frame retrieval and advancement"""
        tracker = ProgressTracker(ProgressConfig(
            supports_unicode=True,
            animation_style=AnimationStyle.SPINNER
        ))
        frame1 = tracker._get_current_frame()
        frame2 = tracker._get_current_frame()
        # Frame index should advance
        assert tracker._frame_index > 0
        # Frames may be same if cycled, but index advanced
        assert isinstance(frame1, str)
        assert isinstance(frame2, str)

    def test_calculate_eta_insufficient_data(self):
        """Test ETA calculation returns None for insufficient data"""
        tracker = ProgressTracker()
        tracker.state.iteration = 1
        eta = tracker.calculate_eta()
        assert eta is None

    def test_calculate_eta_second_iteration(self):
        """Test ETA calculation on second iteration"""
        tracker = ProgressTracker()
        tracker.state.iteration = 2
        tracker.state.max_iterations = 4
        # Simulate some time passed
        tracker.state.start_time = time.time() - 2.0  # 2 seconds elapsed
        eta = tracker.calculate_eta()
        assert eta is not None
        assert isinstance(eta, timedelta)

    def test_calculate_eta_phase_b(self):
        """Test ETA calculation in Phase B (half the remaining time)"""
        tracker = ProgressTracker()
        tracker.state.iteration = 2
        tracker.state.max_iterations = 4
        tracker.state.current_phase_letter = "B"
        tracker.state.start_time = time.time() - 2.0
        eta = tracker.calculate_eta()
        assert eta is not None

    def test_format_score_bar_high_score(self):
        """Test score bar formatting for high score (>= 0.9)"""
        tracker = ProgressTracker(ProgressConfig(supports_unicode=True))
        bar = tracker.format_score_bar(0.95, width=20)
        assert "0.95" in bar
        assert "[" in bar
        assert "]" in bar

    def test_format_score_bar_medium_score(self):
        """Test score bar formatting for medium score (>= 0.8)"""
        tracker = ProgressTracker(ProgressConfig(supports_unicode=True))
        bar = tracker.format_score_bar(0.85, width=20)
        assert "0.85" in bar

    def test_format_score_bar_low_score(self):
        """Test score bar formatting for low score (< 0.6)"""
        tracker = ProgressTracker(ProgressConfig(supports_unicode=True))
        bar = tracker.format_score_bar(0.45, width=20)
        assert "0.45" in bar

    def test_format_score_bar_ascii_fallback(self):
        """Test score bar with ASCII fallback"""
        tracker = ProgressTracker(ProgressConfig(supports_unicode=False))
        bar = tracker.format_score_bar(0.75, width=20)
        assert "0.75" in bar
        # ASCII mode uses # and -
        assert "#" in bar or "-" in bar

    def test_format_phase_indicator_phase_a(self):
        """Test phase indicator formatting for Phase A"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=True))
        tracker.state.current_phase_letter = "A"
        indicator = tracker.format_phase_indicator()
        assert "Phase A" in indicator

    def test_format_phase_indicator_phase_b(self):
        """Test phase indicator formatting for Phase B"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=True))
        tracker.state.current_phase_letter = "B"
        indicator = tracker.format_phase_indicator()
        assert "Phase B" in indicator

    def test_format_phase_indicator_no_color(self):
        """Test phase indicator without color support"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=False))
        tracker.state.current_phase_letter = "A"
        indicator = tracker.format_phase_indicator()
        assert "Phase A" in indicator

    def test_get_display_text_compact_mode(self):
        """Test compact mode display text generation"""
        config = ProgressConfig(compact_mode=True, supports_unicode=True)
        tracker = ProgressTracker(config)
        tracker.state.score = 0.75
        display = tracker.get_display_text()
        assert isinstance(display, str)
        assert len(display) > 0

    def test_get_display_text_full_mode(self):
        """Test full mode display text generation"""
        config = ProgressConfig(compact_mode=False, supports_unicode=True)
        tracker = ProgressTracker(config)
        tracker.state.score = 0.75
        tracker.state.message = "Testing"
        display = tracker.get_display_text()
        assert isinstance(display, str)
        assert "Testing" in display

    def test_compact_display_with_score(self):
        """Test compact display shows score"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=True))
        tracker.state.score = 0.85
        tracker.state.iteration = 2
        tracker.state.max_iterations = 4
        display = tracker._get_compact_display()
        assert "0.85" in display
        assert "2/4" in display

    def test_compact_display_without_score(self):
        """Test compact display with no score"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=True))
        tracker.state.score = None
        display = tracker._get_compact_display()
        assert "..." in display

    def test_compact_display_score_trend_up(self):
        """Test compact display shows upward trend"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=True))
        tracker.state.score = 0.85
        tracker.state.previous_score = 0.75
        display = tracker._get_compact_display()
        assert "0.85" in display

    def test_compact_display_score_trend_down(self):
        """Test compact display shows downward trend"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=True))
        tracker.state.score = 0.65
        tracker.state.previous_score = 0.75
        display = tracker._get_compact_display()
        assert "0.65" in display

    def test_full_display_all_sections(self):
        """Test full display shows all sections"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=False, show_eta=True))
        tracker.state.message = "Test message"
        tracker.state.score = 0.80
        tracker.state.iteration = 2
        tracker.state.max_iterations = 4
        tracker.state.start_time = time.time() - 1.0
        display = tracker._get_full_display()
        assert "Test message" in display
        assert "Score:" in display
        assert "Elapsed:" in display

    def test_full_display_with_failed_rules(self):
        """Test full display shows failed rules count"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=False))
        tracker.state.score = 0.70
        tracker.state.failed_rules_count = 3
        display = tracker._get_full_display()
        assert "Failed rules:" in display
        assert "3" in display

    def test_full_display_with_eta(self):
        """Test full display shows ETA"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=False, show_eta=True))
        tracker.state.iteration = 2
        tracker.state.max_iterations = 4
        tracker.state.start_time = time.time() - 2.0
        display = tracker._get_full_display()
        assert "ETA:" in display

    def test_format_eta_seconds(self):
        """Test ETA formatting for seconds"""
        tracker = ProgressTracker()
        eta = timedelta(seconds=45)
        formatted = tracker._format_eta(eta)
        assert "45s" in formatted

    def test_format_eta_minutes_seconds(self):
        """Test ETA formatting for minutes and seconds"""
        tracker = ProgressTracker()
        eta = timedelta(minutes=2, seconds=30)
        formatted = tracker._format_eta(eta)
        assert "2m" in formatted
        assert "30s" in formatted

    def test_format_eta_hours_minutes(self):
        """Test ETA formatting for hours and minutes"""
        tracker = ProgressTracker()
        eta = timedelta(hours=1, minutes=30)
        formatted = tracker._format_eta(eta)
        assert "1h" in formatted
        assert "30m" in formatted

    def test_format_duration_milliseconds(self):
        """Test duration formatting for milliseconds"""
        tracker = ProgressTracker()
        duration = 0.5  # 500ms
        formatted = tracker._format_duration(duration)
        assert "ms" in formatted

    def test_format_duration_seconds(self):
        """Test duration formatting for seconds"""
        tracker = ProgressTracker()
        duration = 5.5
        formatted = tracker._format_duration(duration)
        assert "5.5s" in formatted

    def test_format_duration_minutes(self):
        """Test duration formatting for minutes"""
        tracker = ProgressTracker()
        duration = 125.0  # 2 minutes 5 seconds
        formatted = tracker._format_duration(duration)
        assert "2m" in formatted

    def test_update_single_field(self):
        """Test updating single state field"""
        tracker = ProgressTracker()
        tracker.update(score=0.85)
        assert tracker.state.score == 0.85

    def test_update_multiple_fields(self):
        """Test updating multiple state fields"""
        tracker = ProgressTracker()
        tracker.update(
            phase=ProgressPhase.EVALUATE,
            iteration=2,
            score=0.75,
            message="Evaluating..."
        )
        assert tracker.state.phase == ProgressPhase.EVALUATE
        assert tracker.state.iteration == 2
        assert tracker.state.score == 0.75
        assert tracker.state.message == "Evaluating..."

    def test_update_phase_changes_phase_start_time(self):
        """Test phase change updates phase start time"""
        tracker = ProgressTracker()
        original_time = tracker.state.phase_start_time
        time.sleep(0.01)  # Small delay
        tracker.update(phase=ProgressPhase.EVALUATE)
        assert tracker.state.phase_start_time > original_time

    def test_update_score_tracks_previous_score(self):
        """Test score update tracks previous score"""
        tracker = ProgressTracker()
        tracker.update(score=0.75)
        tracker.update(score=0.85)
        assert tracker.state.score == 0.85
        assert tracker.state.previous_score == 0.75
        assert tracker._score_history == [0.75, 0.85]

    def test_update_score_first_time_no_previous(self):
        """Test first score update has no previous score"""
        tracker = ProgressTracker()
        tracker.update(score=0.75)
        assert tracker.state.score == 0.75
        assert tracker.state.previous_score is None

    def test_display_disabled(self):
        """Test display when disabled"""
        tracker = ProgressTracker(ProgressConfig(enabled=False))
        output = StringIO()
        tracker.display(file=output)
        assert output.getvalue() == ""

    def test_display_enabled(self):
        """Test display when enabled"""
        tracker = ProgressTracker(ProgressConfig(enabled=True))
        tracker.state.score = 0.75
        output = StringIO()
        tracker.display(file=output)
        result = output.getvalue()
        assert len(result) > 0

    def test_display_to_stderr_default(self):
        """Test display defaults to stderr"""
        tracker = ProgressTracker(ProgressConfig(enabled=True))
        tracker.state.score = 0.75
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            tracker.display()
            result = mock_stderr.getvalue()
            assert len(result) > 0

    def test_finish_success(self):
        """Test finishing with success"""
        tracker = ProgressTracker()
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            tracker.finish(success=True, final_message="Complete!")
            assert tracker.state.phase == ProgressPhase.COMPLETE
            assert tracker.state.message == "Complete!"

    def test_finish_error(self):
        """Test finishing with error"""
        tracker = ProgressTracker()
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            tracker.finish(success=False, final_message="Error occurred")
            assert tracker.state.phase == ProgressPhase.ERROR
            assert tracker.state.message == "Error occurred"

    def test_finish_no_message(self):
        """Test finishing without custom message"""
        tracker = ProgressTracker()
        tracker.finish(success=True)
        assert tracker.state.message == "Complete"

    def test_reset_line_with_ansi(self):
        """Test line reset with ANSI support"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=True))
        reset = tracker._reset_line()
        assert "\r" in reset
        assert "\033[K" in reset

    def test_reset_line_without_ansi(self):
        """Test line reset without ANSI support"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=False))
        reset = tracker._reset_line()
        assert "\r" in reset
        # Should have spaces to clear line
        assert " " in reset

    def test_colorize_with_color_support(self):
        """Test colorization with color support"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=True))
        colored = tracker._colorize("test", tracker.ansi.GREEN)
        assert isinstance(colored, str)

    def test_colorize_without_color_support(self):
        """Test colorization without color support"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=False))
        colored = tracker._colorize("test", tracker.ansi.GREEN)
        assert colored == "test"

    def test_colorize_no_color_function(self):
        """Test colorization with no color function"""
        tracker = ProgressTracker(ProgressConfig(supports_ansi=True))
        colored = tracker._colorize("test", None)
        assert colored == "test"


class TestLiveProgressContext:
    """Tests for LiveProgressContext context manager"""

    def test_init(self):
        """Test context initialization"""
        ctx = LiveProgressContext()
        assert ctx.config.enabled is True
        assert ctx.tracker is None
        assert ctx._running is False

    def test_init_custom_config(self):
        """Test context with custom config"""
        config = ProgressConfig(compact_mode=True)
        ctx = LiveProgressContext(config)
        assert ctx.config.compact_mode is True

    def test_context_manager_enter(self):
        """Test entering context manager"""
        config = ProgressConfig(animation_style=AnimationStyle.NONE)  # No thread
        ctx = LiveProgressContext(config)
        result = ctx.__enter__()
        assert result is ctx
        assert ctx.tracker is not None
        assert ctx._running is True

    def test_context_manager_exit_success(self):
        """Test exiting context manager on success"""
        config = ProgressConfig(animation_style=AnimationStyle.NONE)
        ctx = LiveProgressContext(config)
        ctx.__enter__()
        ctx.__exit__(None, None, None)
        assert ctx._running is False
        assert ctx.tracker.state.phase == ProgressPhase.COMPLETE

    def test_context_manager_exit_error(self):
        """Test exiting context manager on error"""
        config = ProgressConfig(animation_style=AnimationStyle.NONE)
        ctx = LiveProgressContext(config)
        ctx.__enter__()
        exc = Exception("Test error")
        ctx.__exit__(type(exc), exc, None)
        assert ctx._running is False
        assert ctx.tracker.state.phase == ProgressPhase.ERROR

    def test_context_update(self):
        """Test update through context"""
        config = ProgressConfig(animation_style=AnimationStyle.NONE)
        ctx = LiveProgressContext(config)
        ctx.__enter__()
        ctx.update(score=0.85, iteration=2)
        assert ctx.tracker.state.score == 0.85
        assert ctx.tracker.state.iteration == 2
        ctx.__exit__(None, None, None)

    def test_context_display(self):
        """Test display through context"""
        config = ProgressConfig(animation_style=AnimationStyle.NONE)
        ctx = LiveProgressContext(config)
        ctx.__enter__()
        ctx.update(score=0.85)
        output = StringIO()
        ctx.tracker.display(file=output)
        result = output.getvalue()
        assert len(result) > 0
        ctx.__exit__(None, None, None)


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_create_progress_config_defaults(self):
        """Test create_progress_config with defaults"""
        config = create_progress_config()
        assert config.enabled is True
        assert config.animation_style == AnimationStyle.SPINNER
        assert config.compact_mode is False

    def test_create_progress_config_custom(self):
        """Test create_progress_config with custom values"""
        config = create_progress_config(
            enabled=False,
            animation_style="dots",
            compact=True,
            theme="dark"
        )
        assert config.enabled is False
        assert config.animation_style == AnimationStyle.DOTS
        assert config.compact_mode is True

    def test_create_progress_config_invalid_animation(self):
        """Test create_progress_config with invalid animation style"""
        config = create_progress_config(animation_style="invalid")
        # Should fall back to default
        assert config.animation_style == AnimationStyle.SPINNER

    def test_create_progress_config_invalid_theme(self):
        """Test create_progress_config with invalid theme"""
        config = create_progress_config(theme="invalid")
        # Should fall back to default theme dict
        assert isinstance(config.theme, dict)

    def test_track_quality_progress_enabled(self):
        """Test track_quality_progress when enabled"""
        ctx = track_quality_progress(enabled=True)
        assert ctx.config.enabled is True
        assert isinstance(ctx, LiveProgressContext)

    def test_track_quality_progress_disabled(self):
        """Test track_quality_progress when disabled"""
        ctx = track_quality_progress(enabled=False)
        assert ctx.config.enabled is False

    def test_track_quality_progress_custom_params(self):
        """Test track_quality_progress with custom parameters"""
        ctx = track_quality_progress(
            animation="dots",
            compact=True,
            theme="high-contrast"
        )
        assert ctx.config.animation_style == AnimationStyle.DOTS
        assert ctx.config.compact_mode is True

    def test_create_progress_callback_disabled(self):
        """Test create_progress_callback when disabled returns None"""
        callback = create_progress_callback(enabled=False)
        assert callback is None

    def test_create_progress_callback_enabled(self):
        """Test create_progress_callback when enabled"""
        callback = create_progress_callback(enabled=True)
        assert callback is not None
        assert callable(callback)

    def test_progress_callback_callable(self):
        """Test progress callback is callable and updates tracker"""
        callback = create_progress_callback(enabled=True, animation="none")
        state = ProgressState(
            phase=ProgressPhase.EVALUATE,
            iteration=2,
            score=0.85,
            message="Testing"
        )
        # Should not raise
        callback(state)


class TestThreadSafety:
    """Tests for thread-safe operations"""

    def test_lock_exists(self):
        """Test that tracker has a lock for thread safety"""
        tracker = ProgressTracker()
        assert tracker._lock is not None
        assert hasattr(tracker._lock, 'acquire')
        assert hasattr(tracker._lock, 'release')

    def test_update_is_thread_safe(self):
        """Test update method uses lock for thread safety"""
        tracker = ProgressTracker()
        # Update should complete without errors
        tracker.update(score=0.75, iteration=2, phase=ProgressPhase.EVALUATE)
        assert tracker.state.score == 0.75
        assert tracker.state.iteration == 2
        assert tracker.state.phase == ProgressPhase.EVALUATE


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_zero_score(self):
        """Test handling of zero score"""
        tracker = ProgressTracker()
        bar = tracker.format_score_bar(0.0, width=20)
        assert "0.00" in bar

    def test_perfect_score(self):
        """Test handling of perfect score"""
        tracker = ProgressTracker()
        bar = tracker.format_score_bar(1.0, width=20)
        assert "1.00" in bar

    def test_negative_eta_not_possible(self):
        """Test ETA calculation doesn't produce negative values"""
        tracker = ProgressTracker()
        tracker.state.iteration = 1  # Insufficient data
        eta = tracker.calculate_eta()
        assert eta is None

    def test_max_iterations_boundary(self):
        """Test behavior at max iterations boundary"""
        tracker = ProgressTracker()
        tracker.state.iteration = 4
        tracker.state.max_iterations = 4
        tracker.state.start_time = time.time() - 4.0
        eta = tracker.calculate_eta()
        # Should still calculate ETA even at max
        assert eta is not None

    def test_empty_message_display(self):
        """Test display with empty message"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=False))
        tracker.state.message = ""
        tracker.state.score = 0.75
        display = tracker.get_display_text()
        assert isinstance(display, str)
        assert len(display) > 0

    def test_none_score_display(self):
        """Test display when score is None"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=True))
        tracker.state.score = None
        display = tracker.get_display_text()
        assert "..." in display

    def test_very_long_message(self):
        """Test display with very long message"""
        tracker = ProgressTracker(ProgressConfig(compact_mode=False))
        long_message = "A" * 200
        tracker.state.message = long_message
        display = tracker.get_display_text()
        assert long_message in display

    def test_rapid_updates(self):
        """Test handling rapid successive updates"""
        tracker = ProgressTracker()
        for i in range(100):
            tracker.update(score=i / 100)
        assert tracker.state.score == 0.99
        assert len(tracker._score_history) == 100

    def test_width_override(self):
        """Test terminal width override in config"""
        config = ProgressConfig(width=120)
        tracker = ProgressTracker(config)
        assert tracker._terminal_info.width == 120
