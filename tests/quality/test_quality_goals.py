"""
Test suite for quality_goals.py module.

Tests cover:
- QualityGoal dataclass creation and validation
- GoalStatus and GoalType enum handling
- QualityGoalsManager core operations
- Goal creation functions
- Goal status tracking and transitions
- Preset application
"""

import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

from specify_cli.quality.quality_goals import (
    GoalStatus,
    GoalType,
    QualityGoal,
    GoalProgress,
    GoalSummary,
    QualityGoalsManager,
    create_target_score_goal,
    create_pass_rate_goal,
    create_category_goal,
    create_streak_goal,
    create_improvement_goal,
    create_stability_goal,
    GoalPreset,
    apply_preset,
    list_presets,
    get_preset_info,
)


class TestQualityGoalDataclass:
    """Test QualityGoal dataclass creation and validation"""

    def test_create_minimal_goal(self):
        """Test creating a minimal quality goal"""
        goal = QualityGoal(
            goal_id="test-goal-1",
            name="Test Goal",
            description="A test quality goal",
            goal_type=GoalType.TARGET_SCORE,
            target_value=0.8,
            current_value=0.0,
            status=GoalStatus.NOT_STARTED,
            created_at="2024-01-01T00:00:00",
        )
        assert goal.goal_id == "test-goal-1"
        assert goal.name == "Test Goal"
        assert goal.goal_type == GoalType.TARGET_SCORE
        assert goal.target_value == 0.8
        assert goal.current_value == 0.0
        assert goal.status == GoalStatus.NOT_STARTED
        assert goal.achieved_at is None
        assert goal.category is None

    def test_create_goal_with_category(self):
        """Test creating a goal with a category"""
        goal = QualityGoal(
            goal_id="cat-goal-1",
            name="Category Goal",
            description="Goal with category",
            goal_type=GoalType.CATEGORY_TARGET,
            target_value=0.75,
            current_value=0.5,
            status=GoalStatus.IN_PROGRESS,
            created_at="2024-01-01T00:00:00",
            category="security",
        )
        assert goal.category == "security"
        assert goal.goal_type == GoalType.CATEGORY_TARGET

    def test_create_goal_with_achievement_date(self):
        """Test creating a goal with achievement date"""
        goal = QualityGoal(
            goal_id="achieved-goal",
            name="Achieved Goal",
            description="An achieved goal",
            goal_type=GoalType.TARGET_SCORE,
            target_value=0.8,
            current_value=0.85,
            status=GoalStatus.ACHIEVED,
            created_at="2024-01-01T00:00:00",
            achieved_at="2024-01-15T00:00:00",
        )
        assert goal.status == GoalStatus.ACHIEVED
        assert goal.achieved_at == "2024-01-15T00:00:00"


class TestGoalEnums:
    """Test GoalStatus and GoalType enums"""

    def test_goal_status_values(self):
        """Test all GoalStatus enum values exist"""
        assert GoalStatus.NOT_STARTED.value == "not_started"
        assert GoalStatus.IN_PROGRESS.value == "in_progress"
        assert GoalStatus.ACHIEVED.value == "achieved"
        assert GoalStatus.FAILED.value == "failed"
        assert GoalStatus.AT_RISK.value == "at_risk"

    def test_goal_type_values(self):
        """Test all GoalType enum values exist"""
        assert GoalType.TARGET_SCORE.value == "target_score"
        assert GoalType.PASS_RATE.value == "pass_rate"
        assert GoalType.CATEGORY_TARGET.value == "category_target"
        assert GoalType.STREAK.value == "streak"
        assert GoalType.IMPROVEMENT.value == "improvement"
        assert GoalType.STABILITY.value == "stability"


class TestGoalProgress:
    """Test GoalProgress dataclass"""

    def test_goal_progress_creation(self):
        """Test creating a goal progress object"""
        progress = GoalProgress(
            goal_id="test-goal",
            goal_name="Test Goal",
            current_value=0.75,
            target_value=0.8,
            progress_percent=93.75,
            status=GoalStatus.IN_PROGRESS,
            trend="stable",
            recent_values=[0.7, 0.72, 0.75],
            message="On track",
            actions=["Keep going"],
        )
        assert progress.goal_id == "test-goal"
        assert progress.current_value == 0.75
        assert progress.target_value == 0.8
        assert progress.progress_percent == 93.75
        assert progress.trend == "stable"


class TestGoalSummary:
    """Test GoalSummary dataclass"""

    def test_goal_summary_creation(self):
        """Test creating a goal summary object"""
        summary = GoalSummary(
            total_goals=10,
            achieved_goals=5,
            in_progress_goals=3,
            at_risk_goals=1,
            failed_goals=1,
            overall_progress=0.65,
        )
        assert summary.total_goals == 10
        assert summary.achieved_goals == 5
        assert summary.in_progress_goals == 3
        assert summary.at_risk_goals == 1
        assert summary.failed_goals == 1
        assert summary.overall_progress == 0.65


class TestQualityGoalsManagerBasic:
    """Test QualityGoalsManager basic operations"""

    def test_manager_init_default(self):
        """Test manager initialization with default path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            assert manager.goals_dir.exists()

    def test_manager_init_with_path(self):
        """Test manager initialization with custom path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "custom-goals")
            assert manager.goals_dir.name == "custom-goals"

    def test_create_goal(self):
        """Test creating a goal through the manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            goal = manager.create_goal(
                name="Test Goal",
                description="Test description",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            assert goal.name == "Test Goal"
            assert goal.goal_type == GoalType.TARGET_SCORE
            assert goal.target_value == 0.8
            assert goal.status == GoalStatus.NOT_STARTED

    def test_get_all_goals(self):
        """Test getting all goals"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            manager.create_goal(
                name="Goal 1",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            manager.create_goal(
                name="Goal 2",
                description="Test",
                goal_type=GoalType.PASS_RATE,
                target_value=0.9,
            )
            goals = manager.get_all_goals()
            assert len(goals) == 2

    def test_get_goal(self):
        """Test getting a specific goal by ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            created = manager.create_goal(
                name="Test Goal",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            retrieved = manager.get_goal(created.goal_id)
            assert retrieved is not None
            assert retrieved.name == "Test Goal"

    def test_get_nonexistent_goal(self):
        """Test getting a non-existent goal returns None"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            assert manager.get_goal("nonexistent") is None

    def test_update_goal(self):
        """Test updating a goal"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            goal = manager.create_goal(
                name="Test Goal",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            updated = manager.update_goal(
                goal_id=goal.goal_id,
                target_value=0.9,
                name="Updated Goal",
            )
            assert updated.target_value == 0.9
            assert updated.name == "Updated Goal"

    def test_delete_goal(self):
        """Test deleting a goal"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            goal = manager.create_goal(
                name="Test Goal",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            result = manager.delete_goal(goal.goal_id)
            assert result is True
            assert manager.get_goal(goal.goal_id) is None

    def test_delete_nonexistent_goal(self):
        """Test deleting a non-existent goal returns False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            result = manager.delete_goal("nonexistent")
            assert result is False

    def test_get_goal_summary(self):
        """Test getting summary of all goals"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            manager.create_goal(
                name="Goal 1",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            manager.create_goal(
                name="Goal 2",
                description="Test",
                goal_type=GoalType.PASS_RATE,
                target_value=0.9,
            )
            summary = manager.get_goal_summary()
            assert summary is not None
            assert summary.total_goals == 2


class TestQualityGoalsManagerProgress:
    """Test QualityGoalsManager progress tracking"""

    def test_update_goal_progress(self):
        """Test updating goal progress"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            goal = manager.create_goal(
                name="Test Goal",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            progress = manager.update_goal_progress(goal)
            assert progress.goal_id == goal.goal_id
            assert progress.goal_name == "Test Goal"
            assert isinstance(progress.progress_percent, float)

    def test_check_goals_after_run_empty_goals(self):
        """Test checking goals after a quality run with no goals"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            # No goals created

            result = {
                "total_score": 0.85,
                "criteria_scores": {"security": 0.9, "performance": 0.8},
            }

            progress_list = manager.check_goals_after_run(result, "backend")
            assert len(progress_list) == 0


class TestGoalCreationFunctions:
    """Test goal creation helper functions"""

    def test_create_target_score_goal(self):
        """Test creating a target score goal"""
        goal = create_target_score_goal(
            name="80% Score Goal",
            target_score=0.8,
        )
        assert goal.goal_type == GoalType.TARGET_SCORE
        assert goal.target_value == 0.8
        assert goal.status == GoalStatus.NOT_STARTED

    def test_create_pass_rate_goal(self):
        """Test creating a pass rate goal"""
        goal = create_pass_rate_goal(
            name="90% Pass Rate",
            target_pass_rate=90.0,
        )
        assert goal.goal_type == GoalType.PASS_RATE
        assert goal.target_value == 90.0
        assert goal.status == GoalStatus.NOT_STARTED

    def test_create_category_goal(self):
        """Test creating a category-specific goal"""
        goal = create_category_goal(
            name="Security Score",
            category="security",
            target_score=0.85,
        )
        assert goal.goal_type == GoalType.CATEGORY_TARGET
        assert goal.category == "security"
        assert goal.target_value == 0.85

    def test_create_streak_goal(self):
        """Test creating a streak goal"""
        goal = create_streak_goal(
            name="5 Pass Streak",
            target_streak=5,
        )
        assert goal.goal_type == GoalType.STREAK
        assert goal.target_value == 5
        assert goal.current_value == 0

    def test_create_improvement_goal(self):
        """Test creating an improvement goal"""
        goal = create_improvement_goal(
            name="20% Improvement",
            target_improvement=20.0,
        )
        assert goal.goal_type == GoalType.IMPROVEMENT
        assert goal.target_value == 20.0

    def test_create_stability_goal(self):
        """Test creating a stability goal"""
        goal = create_stability_goal(
            name="Score Stability",
            target_stability=95.0,
        )
        assert goal.goal_type == GoalType.STABILITY
        assert goal.target_value == 95.0


class TestGoalPresets:
    """Test goal preset functionality"""

    def test_list_presets(self):
        """Test listing all available presets"""
        presets = list_presets()
        assert isinstance(presets, dict)
        assert len(presets) > 0

    def test_get_preset_info(self):
        """Test getting info about a specific preset"""
        presets = list_presets()
        if presets:
            first_preset_name = list(presets.keys())[0]
            # Convert to enum
            preset_enum = GoalPreset[first_preset_name.upper()]
            info = get_preset_info(preset_enum)
            assert isinstance(info, dict)

    def test_apply_preset(self):
        """Test applying a preset to get goals"""
        presets = list_presets()
        if presets:
            first_preset_name = list(presets.keys())[0]
            preset_enum = GoalPreset[first_preset_name.upper()]
            goals = apply_preset(preset_enum)
            assert isinstance(goals, list)
            assert all(isinstance(g, QualityGoal) for g in goals)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_manager_operations(self):
        """Test operations on an empty manager"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            assert manager.get_goal("nonexistent") is None
            assert manager.get_all_goals() == []
            assert manager.delete_goal("nonexistent") is False
            summary = manager.get_goal_summary()
            # Summary might be None or have zero goals
            if summary:
                assert summary.total_goals == 0

    def test_boundary_target_values(self):
        """Test goals with boundary target values (0.0 and 1.0)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            goal1 = manager.create_goal(
                name="Min Goal",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.0,
            )
            assert goal1.target_value == 0.0

            goal2 = manager.create_goal(
                name="Max Goal",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=1.0,
            )
            assert goal2.target_value == 1.0


class TestToDictMethods:
    """Test to_dict conversion methods"""

    def test_goal_progress_to_dict(self):
        """Test GoalProgress to_dict method"""
        progress = GoalProgress(
            goal_id="test-goal",
            goal_name="Test Goal",
            current_value=0.75,
            target_value=0.8,
            progress_percent=93.75,
            status=GoalStatus.IN_PROGRESS,
            trend="stable",
            recent_values=[0.7, 0.72, 0.75],
            message="On track",
            actions=["Keep going"],
        )
        result = progress.to_dict()
        assert isinstance(result, dict)
        assert result["goal_id"] == "test-goal"
        assert result["progress_percent"] == 93.75

    def test_goal_summary_to_dict(self):
        """Test GoalSummary to_dict method"""
        summary = GoalSummary(
            total_goals=10,
            achieved_goals=5,
            in_progress_goals=3,
            at_risk_goals=1,
            failed_goals=1,
            overall_progress=0.65,
        )
        result = summary.to_dict()
        assert isinstance(result, dict)
        assert result["total_goals"] == 10
        assert result["overall_progress"] == 0.65


class TestGoalIdGeneration:
    """Test goal ID generation"""

    def test_goal_id_is_generated(self):
        """Test that create_goal generates a unique ID"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            goal1 = manager.create_goal(
                name="Test Goal",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            assert goal1.goal_id is not None
            assert len(goal1.goal_id) > 0

    def test_different_goals_have_different_ids(self):
        """Test that different goals get different IDs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            goal1 = manager.create_goal(
                name="Goal 1",
                description="Test",
                goal_type=GoalType.TARGET_SCORE,
                target_value=0.8,
            )
            goal2 = manager.create_goal(
                name="Goal 2",
                description="Test",
                goal_type=GoalType.PASS_RATE,
                target_value=0.9,
            )
            assert goal1.goal_id != goal2.goal_id


class TestCategoryGoals:
    """Test category-specific goal functionality"""

    def test_create_category_goal_different_categories(self):
        """Test creating goals for different categories"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = QualityGoalsManager(goals_dir=Path(tmpdir) / "goals")
            security_goal = manager.create_goal(
                name="Security Target",
                description="Security goal",
                goal_type=GoalType.CATEGORY_TARGET,
                target_value=0.85,
                category="security",
            )
            perf_goal = manager.create_goal(
                name="Performance Target",
                description="Performance goal",
                goal_type=GoalType.CATEGORY_TARGET,
                target_value=0.75,
                category="performance",
            )
            assert security_goal.category == "security"
            assert perf_goal.category == "performance"
            assert security_goal.goal_id != perf_goal.goal_id
