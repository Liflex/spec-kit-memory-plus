#!/usr/bin/env python3
"""
SkillsMP API Key Setup Script

Prompts user for SkillsMP API key (optional), validates it, and stores securely.
"""

import sys
import os
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

from specify_cli.memory.skillsmp.integration import SkillsMPIntegration
from specify_cli.memory.logging import get_logger

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def print_header(text: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def print_success(text: str):
    """Print success message."""
    print(f"[OK] {text}")


def print_warning(text: str):
    """Print warning message."""
    print(f"[WARN] {text}")


def print_error(text: str):
    """Print error message."""
    print(f"[ERROR] {text}")


def prompt_for_api_key() -> str:
    """Prompt user for API key input.

    Returns:
        API key string or empty string if skipped
    """
    print("\nSkillsMP API Key Setup (Optional)")
    print("-" * 60)
    print("\nSkillsMP provides access to 425K+ agent skills from the community.")
    print("Without an API key, the system will use GitHub fallback search.")
    print("\nGet your API key at: https://skillsmp.com/api-keys")
    print("\nPress Enter to skip (GitHub fallback will be used)")

    try:
        api_key = input("\nEnter SkillsMP API key (sk_live_*): ").strip()
        return api_key
    except (EOFError, KeyboardInterrupt):
        print("\n")
        return ""


def validate_api_key_format(api_key: str) -> bool:
    """Validate API key format.

    Args:
        api_key: API key to validate

    Returns:
        True if format is valid
    """
    if not api_key:
        return False

    # Basic format check
    if len(api_key) < 20:
        return False

    # Check for common prefixes
    valid_prefixes = ["sk_live_", "sk_test_"]
    if not any(api_key.startswith(prefix) for prefix in valid_prefixes):
        print_warning("API key should start with 'sk_live_' or 'sk_test_'")
        return False

    return True


def test_api_key(api_key: str) -> bool:
    """Test API key with actual API request.

    Args:
        api_key: API key to test

    Returns:
        True if API key works
    """
    print("\nTesting API key...")

    try:
        integration = SkillsMPIntegration(api_key=api_key)

        # Try a simple search query to test the API
        results = integration.search_skills(
            query="test",
            limit=1,
            use_github_fallback=False  # Only test SkillsMP API
        )

        if integration.has_api_key():
            print_success("API key validated successfully!")
            return True
        else:
            print_error("API key validation failed")
            return False

    except Exception as e:
        print_error(f"API key test failed: {e}")
        return False


def main():
    """Main setup function."""
    logger = get_logger()

    print_header("SkillsMP API Key Setup")

    # Check if key already exists
    integration = SkillsMPIntegration()

    if integration.has_api_key():
        print_success("SkillsMP API key already configured")
        response = input("\nDo you want to reconfigure? (y/n): ").strip().lower()

        if response != 'y':
            print("\nUsing existing API key configuration.")
            return 0

    # Prompt for API key
    api_key = prompt_for_api_key()

    # Skip if user pressed Enter
    if not api_key:
        print_warning("Skipped - GitHub fallback will be used for skill search")
        print("\nYou can add SkillsMP API key later by running:")
        print("  python ~/.claude/spec-kit/scripts/memory/setup_skillsmp_key.py")
        return 0

    # Validate format
    if not validate_api_key_format(api_key):
        print_error("Invalid API key format")
        print("\nExpected format: sk_live_* or sk_test_*")
        print("Get your API key at: https://skillsmp.com/api-keys")
        return 1

    # Test API key
    if not test_api_key(api_key):
        print_error("API key validation failed")
        print("\nPlease check:")
        print("  1. API key is correct")
        print("  2. Network connection is active")
        print("  3. SkillsMP service is available")
        return 1

    # Store API key
    if integration.setup_api_key(api_key):
        print_success("API key stored securely")

        # Show status
        status = integration.get_status()
        print("\nSkillsMP Status:")
        print(f"  Configured: {status['skillsmp']['configured']}")
        print(f"  API Key Stored: {status['skillsmp']['api_key_stored']}")

        print("\n" + "="*60)
        print_success("SkillsMP API key setup complete!")
        print("="*60)
        return 0
    else:
        print_error("Failed to store API key")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Setup failed: {e}")
        sys.exit(1)
