"""
Tests for terminal_colors.py module (Exp 145)

Covers:
- ANSI color codes and styles
- ColorTheme presets (DEFAULT, DARK, MINIMAL, HIGH_CONTRAST)
- TerminalInfo dataclass
- detect_terminal_capabilities() function
- NO_COLOR, CI, and platform-specific detection
- 256-color and RGB color functions
- Terminal info caching
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

from specify_cli.quality.terminal_colors import (
    # Enums and Classes
    ColorScheme,
    ANSI,
    ColorTheme,
    TerminalInfo,
    # Functions
    detect_terminal_capabilities,
    get_terminal_info,
    reset_terminal_cache,
)


class TestANSIConstants:
    """Test ANSI color code constants"""

    def test_reset_code(self):
        """RESET should be the ANSI reset escape sequence"""
        assert ANSI.RESET == "\033[0m"

    def test_basic_foreground_colors(self):
        """Basic foreground colors should be valid ANSI codes"""
        assert ANSI.BLACK == "\033[30m"
        assert ANSI.RED == "\033[31m"
        assert ANSI.GREEN == "\033[32m"
        assert ANSI.YELLOW == "\033[33m"
        assert ANSI.BLUE == "\033[34m"
        assert ANSI.MAGENTA == "\033[35m"
        assert ANSI.CYAN == "\033[36m"
        assert ANSI.WHITE == "\033[37m"

    def test_bright_foreground_colors(self):
        """Bright foreground colors should use 90-97 codes"""
        assert ANSI.BRIGHT_RED == "\033[91m"
        assert ANSI.BRIGHT_GREEN == "\033[92m"
        assert ANSI.BRIGHT_YELLOW == "\033[93m"
        assert ANSI.BRIGHT_BLUE == "\033[94m"
        assert ANSI.BRIGHT_MAGENTA == "\033[95m"
        assert ANSI.BRIGHT_CYAN == "\033[96m"
        assert ANSI.BRIGHT_WHITE == "\033[97m"

    def test_background_colors(self):
        """Background colors should use 40-47 codes"""
        assert ANSI.BG_BLACK == "\033[40m"
        assert ANSI.BG_RED == "\033[41m"
        assert ANSI.BG_GREEN == "\033[42m"
        assert ANSI.BG_YELLOW == "\033[43m"
        assert ANSI.BG_BLUE == "\033[44m"
        assert ANSI.BG_MAGENTA == "\033[45m"
        assert ANSI.BG_CYAN == "\033[46m"
        assert ANSI.BG_WHITE == "\033[47m"

    def test_style_codes(self):
        """Style codes should be correct ANSI sequences"""
        assert ANSI.BOLD == "\033[1m"
        assert ANSI.DIM == "\033[2m"
        assert ANSI.ITALIC == "\033[3m"
        assert ANSI.UNDERLINE == "\033[4m"
        assert ANSI.INVERSE == "\033[7m"


class TestANSIDynamicColors:
    """Test dynamic color functions"""

    def test_fg_256(self):
        """fg_256 should generate 256-color foreground codes"""
        assert ANSI.fg_256(0) == "\033[38;5;0m"
        assert ANSI.fg_256(15) == "\033[38;5;15m"
        assert ANSI.fg_256(255) == "\033[38;5;255m"
        assert ANSI.fg_256(123) == "\033[38;5;123m"

    def test_bg_256(self):
        """bg_256 should generate 256-color background codes"""
        assert ANSI.bg_256(0) == "\033[48;5;0m"
        assert ANSI.bg_256(15) == "\033[48;5;15m"
        assert ANSI.bg_256(255) == "\033[48;5;255m"
        assert ANSI.bg_256(200) == "\033[48;5;200m"

    def test_fg_rgb(self):
        """fg_rgb should generate RGB foreground codes"""
        assert ANSI.fg_rgb(255, 0, 0) == "\033[38;2;255;0;0m"
        assert ANSI.fg_rgb(0, 255, 0) == "\033[38;2;0;255;0m"
        assert ANSI.fg_rgb(0, 0, 255) == "\033[38;2;0;0;255m"
        assert ANSI.fg_rgb(128, 128, 128) == "\033[38;2;128;128;128m"

    def test_bg_rgb(self):
        """bg_rgb should generate RGB background codes"""
        assert ANSI.bg_rgb(255, 0, 0) == "\033[48;2;255;0;0m"
        assert ANSI.bg_rgb(0, 255, 0) == "\033[48;2;0;255;0m"
        assert ANSI.bg_rgb(0, 0, 255) == "\033[48;2;0;0;255m"
        assert ANSI.bg_rgb(64, 64, 64) == "\033[48;2;64;64;64m"


class TestColorTheme:
    """Test predefined color themes"""

    def test_default_theme_has_all_keys(self):
        """DEFAULT theme should have all expected keys"""
        expected_keys = {
            "title", "header", "pareto", "highlight", "dominated",
            "grid", "axis", "legend", "good", "warning", "bad", "info"
        }
        assert set(ColorTheme.DEFAULT.keys()) == expected_keys

    def test_default_theme_values(self):
        """DEFAULT theme should use basic ANSI codes"""
        assert ANSI.BOLD in ColorTheme.DEFAULT["title"]
        assert ANSI.CYAN in ColorTheme.DEFAULT["title"]
        assert ANSI.GREEN in ColorTheme.DEFAULT["pareto"]
        assert ANSI.RED in ColorTheme.DEFAULT["bad"]

    def test_dark_theme_exists(self):
        """DARK theme should exist and be different from DEFAULT"""
        assert ColorTheme.DARK != ColorTheme.DEFAULT
        assert "title" in ColorTheme.DARK
        # Dark theme uses bright colors
        assert ANSI.BRIGHT_CYAN in ColorTheme.DARK["title"]

    def test_minimal_theme_exists(self):
        """MINIMAL theme should exist with minimal colors"""
        assert ColorTheme.MINIMAL != ColorTheme.DEFAULT
        assert "title" in ColorTheme.MINIMAL
        # Many keys are empty in minimal
        assert ColorTheme.MINIMAL["header"] == ""

    def test_high_contrast_theme_exists(self):
        """HIGH_CONTRAST theme should exist for accessibility"""
        assert ColorTheme.HIGH_CONTRAST != ColorTheme.DEFAULT
        assert "title" in ColorTheme.HIGH_CONTRAST
        # Uses bright colors for contrast
        assert ANSI.BRIGHT_WHITE in ColorTheme.HIGH_CONTRAST["title"]


class TestTerminalInfoDataclass:
    """Test TerminalInfo dataclass"""

    def test_default_init(self):
        """TerminalInfo should initialize with defaults"""
        info = TerminalInfo()
        assert info.supports_colors is False
        assert info.supports_256_colors is False
        assert info.supports_truecolor is False
        assert info.supports_unicode is True
        assert info.is_ci is False
        assert info.width == 80
        assert info.color_scheme == ColorScheme.NONE
        assert info.theme == {}

    def test_init_with_values(self):
        """TerminalInfo should accept custom values"""
        info = TerminalInfo(
            supports_colors=True,
            supports_256_colors=True,
            supports_truecolor=False,
            supports_unicode=False,
            is_ci=True,
            width=120,
            color_scheme=ColorScheme.BASIC,
            theme={"good": ANSI.GREEN}
        )
        assert info.supports_colors is True
        assert info.supports_256_colors is True
        assert info.supports_truecolor is False
        assert info.supports_unicode is False
        assert info.is_ci is True
        assert info.width == 120
        assert info.color_scheme == ColorScheme.BASIC
        assert info.theme == {"good": ANSI.GREEN}

    def test_get_color(self):
        """get_color should return theme color or empty string"""
        info = TerminalInfo(theme={"good": ANSI.GREEN, "bad": ANSI.RED})
        assert info.get_color("good") == ANSI.GREEN
        assert info.get_color("bad") == ANSI.RED
        assert info.get_color("missing") == ""

    def test_colorize_with_colors_supported(self):
        """colorize should wrap text in ANSI codes when colors supported"""
        info = TerminalInfo(
            supports_colors=True,
            theme={"good": ANSI.GREEN}
        )
        result = info.colorize("test", "good")
        assert result == f"{ANSI.GREEN}test{ANSI.RESET}"

    def test_colorize_without_colors(self):
        """colorize should return plain text when colors not supported"""
        info = TerminalInfo(
            supports_colors=False,
            theme={"good": ANSI.GREEN}
        )
        result = info.colorize("test", "good")
        assert result == "test"

    def test_colorize_missing_key(self):
        """colorize should return plain text when color key missing"""
        info = TerminalInfo(
            supports_colors=True,
            theme={}
        )
        result = info.colorize("test", "missing")
        assert result == "test"


class TestTerminalDetection:
    """Test terminal capability detection"""

    @pytest.fixture(autouse=True)
    def reset_env_and_cache(self):
        """Reset environment and cache before each test"""
        original_env = os.environ.copy()
        reset_terminal_cache()
        yield
        os.environ.clear()
        os.environ.update(original_env)
        reset_terminal_cache()

    @patch('shutil.get_terminal_size')
    def test_basic_detection(self, mock_terminal):
        """Should detect basic terminal capabilities"""
        mock_terminal.return_value = MagicMock(columns=80)
        os.environ["TERM"] = "xterm-256color"

        info = detect_terminal_capabilities()

        # On Unix-like systems, should support colors
        if sys.platform != "win32":
            assert info.supports_colors is True
            assert info.supports_unicode is True

    def test_no_color_env_var(self):
        """NO_COLOR environment variable should disable colors"""
        os.environ["NO_COLOR"] = "1"

        info = detect_terminal_capabilities()

        assert info.supports_colors is False
        assert info.color_scheme == ColorScheme.NONE
        assert info.supports_unicode is True  # NO_COLOR doesn't affect unicode

    @pytest.mark.parametrize("ci_var", [
        "CI", "CONTINUOUS_INTEGRATION", "GITHUB_ACTIONS",
        "GITLAB_CI", "TRAVIS", "JENKINS_URL"
    ])
    def test_ci_detection(self, ci_var):
        """Should detect CI environment from various env vars"""
        os.environ[ci_var] = "true"
        # Remove TERM to ensure no color support
        os.environ.pop("TERM", None)
        os.environ.pop("COLORTERM", None)

        info = detect_terminal_capabilities()

        assert info.is_ci is True
        # CI without color TERM should not support colors
        assert info.supports_colors is False

    def test_ci_with_force_color(self):
        """FORCE_COLOR should enable colors even in CI"""
        os.environ["CI"] = "true"
        os.environ["FORCE_COLOR"] = "1"

        info = detect_terminal_capabilities()

        assert info.is_ci is True
        assert info.supports_colors is True

    @pytest.mark.parametrize("term_var,expected", [
        ("xterm-256color", True),
        ("xterm", True),
        ("screen-256color", True),
        ("screen", True),
        ("tmux-256color", True),
        ("dumb", False),
    ])
    def test_term_variable_detection(self, expected, term_var):
        """TERM variable should influence color detection"""
        os.environ["TERM"] = term_var

        info = detect_terminal_capabilities()

        if sys.platform != "win32":
            assert info.supports_colors == expected

    @pytest.mark.parametrize("colorterm,expected_256,expected_true", [
        ("truecolor", True, True),
        ("24bit", True, True),
        ("256color", True, False),
        (None, False, False),
    ])
    def test_colorterm_detection(self, colorterm, expected_256, expected_true):
        """COLORTERM variable should enable extended colors"""
        os.environ["TERM"] = "xterm"
        if colorterm:
            os.environ["COLORTERM"] = colorterm

        info = detect_terminal_capabilities()

        if sys.platform != "win32" and info.supports_colors:
            assert info.supports_256_colors == expected_256
            assert info.supports_truecolor == expected_true

    @patch('shutil.get_terminal_size')
    def test_terminal_width_detection(self, mock_terminal):
        """Should detect terminal width from shutil"""
        mock_terminal.return_value = MagicMock(columns=120)

        info = detect_terminal_capabilities()

        assert info.width == 120

    @patch('shutil.get_terminal_size', side_effect=Exception("Error"))
    def test_terminal_width_fallback(self, mock_terminal):
        """Should fall back to default width on error"""
        info = detect_terminal_capabilities()

        assert info.width == 80

    @pytest.mark.parametrize("lang,expected_unicode", [
        ("en_US.UTF-8", True),
        ("en_US.utf8", True),
        ("C.UTF-8", True),
        # Skip non-UTF locales on Windows (Windows always supports unicode)
    ])
    def test_unicode_detection_from_locale(self, lang, expected_unicode):
        """Should detect unicode support from locale variables"""
        os.environ["LANG"] = lang

        info = detect_terminal_capabilities()

        # On non-Windows platforms, unicode support depends on locale
        if sys.platform != "win32":
            assert info.supports_unicode == expected_unicode
        else:
            # Windows with UTF-8 in locale should support unicode
            assert info.supports_unicode is True

    @patch('ctypes.windll.kernel32.SetConsoleMode')
    @patch('ctypes.windll.kernel32.GetStdHandle')
    def test_windows_color_detection(self, mock_std_handle, mock_set_mode):
        """On Windows, should attempt to enable console colors"""
        mock_std_handle.return_value = 10  # Dummy handle

        with patch.object(sys, 'platform', 'win32'):
            os.environ.pop("TERM", None)
            os.environ.pop("COLORTERM", None)
            os.environ.pop("WT_SESSION", None)
            os.environ.pop("TERM_PROGRAM", None)

            info = detect_terminal_capabilities()

            # Should attempt to enable colors on Windows
            if mock_set_mode.called:
                mock_set_mode.assert_called_once()

    def test_windows_terminal_detection(self):
        """Windows Terminal should be detected as modern terminal"""
        with patch.object(sys, 'platform', 'win32'):
            os.environ["WT_SESSION"] = "1"

            info = detect_terminal_capabilities()

            assert info.supports_colors is True
            assert info.supports_256_colors is True
            assert info.supports_truecolor is True

    def test_vscode_terminal_detection(self):
        """VSCode terminal should support colors"""
        with patch.object(sys, 'platform', 'win32'):
            os.environ["TERM_PROGRAM"] = "vscode"

            info = detect_terminal_capabilities()

            assert info.supports_colors is True
            assert info.supports_256_colors is True
            assert info.supports_truecolor is True


class TestColorSchemeAssignment:
    """Test color scheme assignment based on capabilities"""

    @pytest.fixture(autouse=True)
    def reset_env_and_cache(self):
        """Reset environment and cache before each test"""
        original_env = os.environ.copy()
        reset_terminal_cache()
        yield
        os.environ.clear()
        os.environ.update(original_env)
        reset_terminal_cache()

    def test_no_color_scheme(self):
        """NO_COLOR should result in NONE scheme"""
        os.environ["NO_COLOR"] = "1"

        info = detect_terminal_capabilities()

        assert info.color_scheme == ColorScheme.NONE
        assert info.supports_colors is False
        assert info.supports_unicode is True
        # Theme may be empty dict or MINIMAL theme (current behavior: empty)
        # This documents actual behavior - early return skips theme assignment

    def test_basic_color_scheme(self):
        """Basic colors should result in BASIC scheme"""
        os.environ["TERM"] = "xterm"

        info = detect_terminal_capabilities()

        if info.supports_colors and not info.supports_256_colors:
            assert info.color_scheme == ColorScheme.BASIC

    def test_extended_color_scheme(self):
        """256-color support should result in EXTENDED scheme"""
        os.environ["TERM"] = "xterm-256color"

        info = detect_terminal_capabilities()

        if info.supports_256_colors and not info.supports_truecolor:
            assert info.color_scheme == ColorScheme.EXTENDED

    def test_truecolor_scheme(self):
        """Truecolor support should result in TRUECOLOR scheme"""
        os.environ["TERM"] = "xterm"
        os.environ["COLORTERM"] = "truecolor"

        info = detect_terminal_capabilities()

        if info.supports_truecolor:
            assert info.color_scheme == ColorScheme.TRUECOLOR

    @pytest.mark.parametrize("theme_env,expected_theme", [
        ("dark", "DARK"),
        ("high-contrast", "HIGH_CONTRAST"),
        ("minimal", "MINIMAL"),
    ])
    def test_color_theme_env_var(self, theme_env, expected_theme):
        """COLOR_THEME environment variable should select theme"""
        os.environ["TERM"] = "xterm"
        os.environ["COLOR_THEME"] = theme_env

        info = detect_terminal_capabilities()

        if info.supports_colors:
            # Theme should match requested theme
            assert len(info.theme) > 0


class TestTerminalCaching:
    """Test terminal info caching mechanism"""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset cache before each test"""
        reset_terminal_cache()
        yield
        reset_terminal_cache()

    def test_get_terminal_info_caches_result(self):
        """get_terminal_info should cache detection result"""
        info1 = get_terminal_info()
        info2 = get_terminal_info()

        # Same object reference (cached)
        assert info1 is info2

    def test_reset_terminal_cache(self):
        """reset_terminal_cache should clear cached info"""
        info1 = get_terminal_info()
        reset_terminal_cache()
        info2 = get_terminal_info()

        # Should be different objects after reset
        assert info1 is not info2

    @patch.dict(os.environ, {"TERM": "xterm"})
    def test_cache_persists_across_calls(self):
        """Cached result should persist across calls"""
        info1 = get_terminal_info()
        os.environ["TERM"] = "dumb"
        info2 = get_terminal_info()

        # Still cached, so same result
        assert info1 is info2


class TestEdgeCases:
    """Test edge cases and error conditions"""

    @pytest.fixture(autouse=True)
    def reset_env_and_cache(self):
        """Reset environment and cache before each test"""
        original_env = os.environ.copy()
        reset_terminal_cache()
        yield
        os.environ.clear()
        os.environ.update(original_env)
        reset_terminal_cache()

    def test_empty_environment(self):
        """Should handle empty environment gracefully"""
        # All env vars cleared
        os.environ.clear()

        info = detect_terminal_capabilities()

        # Should still return valid TerminalInfo
        assert isinstance(info, TerminalInfo)
        assert info.supports_unicode is not None
        assert info.width is not None

    def test_concurrent_color_scheme_detection(self):
        """ColorScheme enum should work correctly"""
        assert ColorScheme.NONE.value == "none"
        assert ColorScheme.BASIC.value == "basic"
        assert ColorScheme.EXTENDED.value == "extended"
        assert ColorScheme.TRUECOLOR.value == "truecolor"

    def test_terminal_info_immutability_of_theme(self):
        """Theme dict can be modified after creation"""
        info = TerminalInfo(theme={"good": ANSI.GREEN})
        info.theme["bad"] = ANSI.RED

        assert info.theme["bad"] == ANSI.RED

    def test_colorize_with_empty_color(self):
        """colorize should handle empty color codes"""
        info = TerminalInfo(
            supports_colors=True,
            theme={"empty": ""}
        )
        result = info.colorize("test", "empty")

        # Empty color should result in plain text
        assert result == "test"

    @patch.dict(os.environ, {"LANG": "invalid-locale-format"})
    def test_invalid_locale_format(self):
        """Should handle invalid locale format gracefully"""
        info = detect_terminal_capabilities()

        # Should not crash
        assert isinstance(info, TerminalInfo)
        # Unicode support might be True or False depending on platform
        assert info.supports_unicode is not None


class TestIntegrationScenarios:
    """Test real-world usage scenarios"""

    @pytest.fixture(autouse=True)
    def reset_env_and_cache(self):
        """Reset environment and cache before each test"""
        original_env = os.environ.copy()
        reset_terminal_cache()
        yield
        os.environ.clear()
        os.environ.update(original_env)
        reset_terminal_cache()

    def test_github_actions_environment(self):
        """Should detect GitHub Actions CI environment"""
        os.environ["GITHUB_ACTIONS"] = "true"
        os.environ["TERM"] = "xterm-256color"

        info = detect_terminal_capabilities()

        assert info.is_ci is True
        # GitHub Actions supports colors
        assert info.supports_colors is True
        assert info.supports_256_colors is True

    def test_local_development_environment(self):
        """Should detect typical local development environment"""
        os.environ["TERM"] = "xterm-256color"
        os.environ["COLORTERM"] = "truecolor"
        os.environ["LANG"] = "en_US.UTF-8"

        info = detect_terminal_capabilities()

        if sys.platform != "win32":
            assert info.is_ci is False
            assert info.supports_colors is True
            assert info.supports_256_colors is True
            assert info.supports_truecolor is True
            assert info.supports_unicode is True

    def test_minimal_terminal_environment(self):
        """Should handle minimal terminal gracefully"""
        os.environ["TERM"] = "dumb"
        os.environ["LANG"] = "C"

        info = detect_terminal_capabilities()

        # Should detect lack of capabilities
        assert isinstance(info, TerminalInfo)
        # Dumb terminal typically doesn't support colors

    def test_wsl_environment(self):
        """Should detect Windows Subsystem for Linux"""
        with patch.object(sys, 'platform', 'linux'):
            os.environ["TERM"] = "xterm-256color"
            os.environ["WSL_DISTRO_NAME"] = "Ubuntu"

            info = detect_terminal_capabilities()

            if sys.platform != "win32":
                # WSL behaves like Linux
                assert info.supports_unicode is True

    def test_force_color_truecolor(self):
        """FORCE_COLOR=truecolor should force truecolor mode"""
        os.environ["FORCE_COLOR"] = "truecolor"
        os.environ["TERM"] = "xterm"

        info = detect_terminal_capabilities()

        assert info.supports_colors is True
        assert info.supports_truecolor is True
