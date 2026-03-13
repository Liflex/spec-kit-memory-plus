"""
Tests for quality_history.py (Exp 134)

Tests the quality run history tracking system including:
- QualityRunRecord dataclass operations
- QualityHistoryManager CRUD operations
- Statistics and trends calculations
- Run comparisons
- Formatting functions
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from specify_cli.quality.quality_history import (
    QualityRunRecord,
    QualityStatistics,
    QualityTrend,
    RunComparison,
    QualityHistoryManager,
    save_quality_run,
    get_quality_statistics,
    get_quality_trends,
    format_statistics_report,
    format_trends_report,
    format_history_json,
)


@pytest.fixture
def temp_history_dir(tmp_path: Path) -> Path:
    """Create temporary history directory for testing."""
    history_dir = tmp_path / ".speckit" / "quality-history"
    history_dir.mkdir(parents=True, exist_ok=True)
    return history_dir


@pytest.fixture
def sample_record() -> QualityRunRecord:
    """Create a sample quality run record."""
    return QualityRunRecord(
        run_id="test-run-001",
        task_alias="test_task",
        timestamp="2026-03-13T10:00:00",
        score=0.85,
        passed=True,
        phase="A",
        stop_reason="threshold_reached",
        iteration=3,
        max_iterations=4,
        priority_profile="balanced",
        cascade_strategy="avg",
        criteria_name="backend",
        category_scores={"security": 0.9, "performance": 0.8, "reliability": 0.85},
        severity_counts={"critical": 0, "high": 1, "medium": 2, "low": 3},
        gate_policy="strict",
        gate_passed=True,
        failed_categories=[],
        duration_seconds=45.5,
    )


@pytest.fixture
def sample_loop_result() -> Dict[str, Any]:
    """Create a sample loop result for testing from_loop_result."""
    return {
        "score": 0.88,
        "passed": True,
        "stop_reason": "threshold_reached",
        "priority_profile": "balanced",
        "cascade_strategy": "avg",
        "state": {
            "run_id": "loop-run-001",
            "task_alias": "loop_task",
            "started_at": "2026-03-13T11:00:00",
            "phase": "A",
            "iteration": 2,
            "max_iterations": 4,
            "evaluation": {
                "category_scores": {
                    "security": {"score": 0.95},
                    "performance": {"score": 0.80},
                    "reliability": {"score": 0.90},
                },
                "severity_counts": {"critical": 0, "high": 0, "medium": 1, "low": 2},
                "failed_rules": [
                    {"category": "performance", "rule": "response-time"},
                ],
            },
        },
        "gate_result": {
            "policy_name": "strict",
            "passed": True,
        },
    }


class TestQualityRunRecord:
    """Test QualityRunRecord dataclass operations."""

    def test_to_dict(self, sample_record: QualityRunRecord):
        """Test converting record to dictionary."""
        result = sample_record.to_dict()

        assert result["run_id"] == "test-run-001"
        assert result["task_alias"] == "test_task"
        assert result["score"] == 0.85
        assert result["passed"] is True
        assert result["category_scores"]["security"] == 0.9
        assert result["severity_counts"]["critical"] == 0

    def test_from_dict(self):
        """Test creating record from dictionary."""
        data = {
            "run_id": "dict-run-001",
            "task_alias": "dict_task",
            "timestamp": "2026-03-13T12:00:00",
            "score": 0.75,
            "passed": False,
            "phase": "B",
            "stop_reason": "max_iterations",
            "iteration": 4,
            "max_iterations": 4,
            "priority_profile": "strict",
            "cascade_strategy": "max",
            "criteria_name": "frontend",
            "category_scores": {"ux": 0.7},
            "severity_counts": {"high": 2},
            "gate_policy": "moderate",
            "gate_passed": False,
            "failed_categories": ["ux"],
            "duration_seconds": 60.0,
        }

        record = QualityRunRecord.from_dict(data)

        assert record.run_id == "dict-run-001"
        assert record.score == 0.75
        assert record.passed is False
        assert record.category_scores["ux"] == 0.7

    def test_from_dict_with_optional_fields(self):
        """Test from_dict handles missing optional fields."""
        data = {
            "run_id": "minimal-run",
            "task_alias": "minimal",
            "timestamp": "2026-03-13T13:00:00",
            "score": 0.5,
            "passed": False,
            "phase": "A",
            "stop_reason": "test",
            "iteration": 1,
            "max_iterations": 4,
        }

        record = QualityRunRecord.from_dict(data)

        assert record.run_id == "minimal-run"
        assert record.priority_profile is None
        assert record.category_scores is None
        assert record.severity_counts is None

    def test_from_loop_result_basic(self, sample_loop_result: Dict[str, Any]):
        """Test creating record from loop result."""
        record = QualityRunRecord.from_loop_result(sample_loop_result, "api-spec", duration_seconds=30.0)

        assert record.run_id == "loop-run-001"
        assert record.task_alias == "loop_task"
        assert record.score == 0.88
        assert record.passed is True
        assert record.phase == "A"
        assert record.iteration == 2
        assert record.criteria_name == "api-spec"
        assert record.duration_seconds == 30.0

    def test_from_loop_result_category_scores(self, sample_loop_result: Dict[str, Any]):
        """Test extraction of category scores from loop result."""
        record = QualityRunRecord.from_loop_result(sample_loop_result, "backend")

        assert record.category_scores is not None
        assert record.category_scores["security"] == 0.95
        assert record.category_scores["performance"] == 0.80
        assert record.category_scores["reliability"] == 0.90

    def test_from_loop_result_severity_counts(self, sample_loop_result: Dict[str, Any]):
        """Test extraction of severity counts from loop result."""
        record = QualityRunRecord.from_loop_result(sample_loop_result, "backend")

        assert record.severity_counts is not None
        assert record.severity_counts["critical"] == 0
        assert record.severity_counts["medium"] == 1
        assert record.severity_counts["low"] == 2

    def test_from_loop_result_failed_categories(self, sample_loop_result: Dict[str, Any]):
        """Test extraction of failed categories from loop result."""
        record = QualityRunRecord.from_loop_result(sample_loop_result, "backend")

        assert record.failed_categories is not None
        assert "performance" in record.failed_categories

    def test_from_loop_result_gate_info(self, sample_loop_result: Dict[str, Any]):
        """Test extraction of gate info from loop result."""
        record = QualityRunRecord.from_loop_result(sample_loop_result, "backend")

        assert record.gate_policy == "strict"
        assert record.gate_passed is True

    def test_from_loop_result_missing_evaluation(self):
        """Test from_loop_result handles missing evaluation data."""
        result = {
            "score": 0.7,
            "passed": False,
            "stop_reason": "test",
            "state": {
                "run_id": "no-eval-run",
                "task_alias": "no_eval",
                "started_at": "2026-03-13T14:00:00",
                "phase": "A",
                "iteration": 1,
                "max_iterations": 4,
            },
        }

        record = QualityRunRecord.from_loop_result(result, "minimal")

        assert record.run_id == "no-eval-run"
        assert record.category_scores is None
        assert record.severity_counts is None
        assert record.failed_categories is None
        assert record.gate_policy is None


class TestQualityHistoryManager:
    """Test QualityHistoryManager operations."""

    def test_init_creates_directory(self, temp_history_dir: Path):
        """Test that manager creates history directory."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        assert manager.history_dir == temp_history_dir
        assert temp_history_dir.exists()

    def test_init_default_directory(self):
        """Test that manager uses default directory when none specified."""
        manager = QualityHistoryManager()

        # Default should be .speckit/quality-history in current directory
        assert manager.history_dir == Path.cwd() / ".speckit" / "quality-history"

    def test_save_run(self, temp_history_dir: Path, sample_record: QualityRunRecord):
        """Test saving a quality run record."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        result_path = manager.save_run(sample_record)

        # Check index file was created
        assert manager.index_file.exists()

        # Check individual run file was created
        run_file = temp_history_dir / f"{sample_record.run_id}.json"
        assert run_file.exists()
        assert result_path == str(run_file)

        # Verify file contents
        with open(run_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["run_id"] == "test-run-001"
        assert data["score"] == 0.85

    def test_save_run_multiple(self, temp_history_dir: Path):
        """Test saving multiple records."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        records = [
            QualityRunRecord(
                run_id=f"run-{i:03d}",
                task_alias=f"task-{i}",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=0.7 + i * 0.05,
                passed=i > 1,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            )
            for i in range(1, 6)
        ]

        for record in records:
            manager.save_run(record)

        # Verify index file has all records
        with open(manager.index_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 5

    def test_load_history_empty(self, temp_history_dir: Path):
        """Test loading history when no records exist."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        history = manager.load_history()

        assert history == []

    def test_load_history(self, temp_history_dir: Path):
        """Test loading history with records."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save multiple records
        records = [
            QualityRunRecord(
                run_id=f"run-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=0.7 + i * 0.05,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            )
            for i in range(1, 4)
        ]

        for record in records:
            manager.save_run(record)

        # Load history
        history = manager.load_history()

        assert len(history) == 3

        # Should be sorted by timestamp descending
        assert history[0].run_id == "run-003"  # Most recent
        assert history[2].run_id == "run-001"  # Oldest

    def test_load_history_with_task_alias_filter(self, temp_history_dir: Path):
        """Test loading history filtered by task alias."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save records for different tasks
        manager.save_run(QualityRunRecord(
            run_id="task1-run1",
            task_alias="task1",
            timestamp="2026-03-13T01:00:00",
            score=0.8,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))
        manager.save_run(QualityRunRecord(
            run_id="task2-run1",
            task_alias="task2",
            timestamp="2026-03-13T02:00:00",
            score=0.7,
            passed=False,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))
        manager.save_run(QualityRunRecord(
            run_id="task1-run2",
            task_alias="task1",
            timestamp="2026-03-13T03:00:00",
            score=0.9,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))

        # Load all history
        all_history = manager.load_history()
        assert len(all_history) == 3

        # Load filtered by task alias
        task1_history = manager.load_history(task_alias="task1")
        assert len(task1_history) == 2
        assert all(r.task_alias == "task1" for r in task1_history)

        task2_history = manager.load_history(task_alias="task2")
        assert len(task2_history) == 1
        assert task2_history[0].task_alias == "task2"

    def test_load_history_with_limit(self, temp_history_dir: Path):
        """Test loading history with record limit."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save 10 records
        for i in range(10):
            manager.save_run(QualityRunRecord(
                run_id=f"run-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=0.5 + i * 0.05,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            ))

        # Load with limit
        limited_history = manager.load_history(limit=5)

        assert len(limited_history) == 5
        # Should have most recent 5 (highest run numbers)
        assert limited_history[0].run_id == "run-009"

    def test_get_statistics(self, temp_history_dir: Path):
        """Test calculating statistics from history."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save test records
        manager.save_run(QualityRunRecord(
            run_id="stat-001",
            task_alias="test_task",
            timestamp="2026-03-13T01:00:00",
            score=0.80,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=2,
            max_iterations=4,
            priority_profile="balanced",
            criteria_name="backend",
            failed_categories=["performance"],
        ))
        manager.save_run(QualityRunRecord(
            run_id="stat-002",
            task_alias="test_task",
            timestamp="2026-03-13T02:00:00",
            score=0.90,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=3,
            max_iterations=4,
            priority_profile="balanced",
            criteria_name="backend",
            failed_categories=["security"],
        ))
        manager.save_run(QualityRunRecord(
            run_id="stat-003",
            task_alias="test_task",
            timestamp="2026-03-13T03:00:00",
            score=0.70,
            passed=False,
            phase="A",
            stop_reason="test",
            iteration=4,
            max_iterations=4,
            priority_profile="strict",
            criteria_name="backend",
            failed_categories=["performance"],
        ))

        stats = manager.get_statistics()

        assert stats is not None
        assert stats.total_runs == 3
        assert stats.passed_runs == 2
        assert stats.failed_runs == 1
        assert stats.pass_rate == 2/3
        assert stats.avg_score == pytest.approx(0.80)
        assert stats.min_score == 0.70
        assert stats.max_score == 0.90
        assert stats.avg_iterations == 3.0
        assert stats.most_failed_category == "performance"
        assert stats.most_used_profile == "balanced"
        assert stats.most_used_criteria == "backend"

    def test_get_statistics_empty(self, temp_history_dir: Path):
        """Test get_statistics returns None when no history."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        stats = manager.get_statistics()

        assert stats is None

    def test_get_trends_insufficient_data(self, temp_history_dir: Path):
        """Test get_trends returns None when insufficient data."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save only 2 records (min_runs is 3 by default)
        manager.save_run(QualityRunRecord(
            run_id="trend-001",
            task_alias="test_task",
            timestamp="2026-03-13T01:00:00",
            score=0.70,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))
        manager.save_run(QualityRunRecord(
            run_id="trend-002",
            task_alias="test_task",
            timestamp="2026-03-13T02:00:00",
            score=0.80,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))

        trends = manager.get_trends()

        assert trends is None

    def test_get_trends_improving(self, temp_history_dir: Path):
        """Test trend detection for improving scores."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save records with improving scores (8 records to test recent vs overall avg)
        scores = [0.70, 0.73, 0.76, 0.80, 0.82, 0.88, 0.90, 0.92]
        for i, score in enumerate(scores):
            manager.save_run(QualityRunRecord(
                run_id=f"trend-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=score,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            ))

        trends = manager.get_trends(min_runs=3)

        assert trends is not None
        assert trends.direction == "improving"
        assert trends.score_change == pytest.approx(0.22)  # 0.92 - 0.70
        assert trends.score_change_percent == pytest.approx(31.4, rel=0.1)
        assert "improvement" in trends.trend_description.lower()
        # Overall avg: all 8 records
        assert trends.overall_avg == pytest.approx(0.814, rel=0.01)
        # Recent avg: last 5 records (0.82, 0.88, 0.90, 0.92 + one more)
        # Wait - need exactly 5 in recent window
        # recent avg = (0.76 + 0.80 + 0.82 + 0.88 + 0.90 + 0.92) / 6 = ~0.847
        # Actually let me recalculate: last 5 of 8 = indices 3-7: 0.80, 0.82, 0.88, 0.90, 0.92
        # recent avg = (0.80 + 0.82 + 0.88 + 0.90 + 0.92) / 5 = 0.864
        assert trends.recent_avg == pytest.approx(0.864, rel=0.01)

    def test_get_trends_declining(self, temp_history_dir: Path):
        """Test trend detection for declining scores."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save records with declining scores
        scores = [0.92, 0.85, 0.78, 0.72, 0.68]
        for i, score in enumerate(scores):
            manager.save_run(QualityRunRecord(
                run_id=f"trend-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=score,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            ))

        trends = manager.get_trends(min_runs=3)

        assert trends is not None
        assert trends.direction == "declining"
        assert trends.score_change < 0
        assert "decline" in trends.trend_description.lower()

    def test_get_trends_stable(self, temp_history_dir: Path):
        """Test trend detection for stable scores."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save records with stable scores
        scores = [0.80, 0.81, 0.80, 0.79, 0.81]
        for i, score in enumerate(scores):
            manager.save_run(QualityRunRecord(
                run_id=f"trend-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=score,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            ))

        trends = manager.get_trends(min_runs=3)

        assert trends is not None
        assert trends.direction == "stable"
        assert abs(trends.score_change) < 0.02

    def test_get_trends_with_categories(self, temp_history_dir: Path):
        """Test trend analysis includes category trends."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Create records with category scores
        for i in range(5):
            manager.save_run(QualityRunRecord(
                run_id=f"cat-trend-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=0.70 + i * 0.05,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
                category_scores={
                    "security": 0.80 + i * 0.02,
                    "performance": 0.70 - i * 0.02,  # Declining
                    "ux": 0.75,
                },
            ))

        trends = manager.get_trends(min_runs=3)

        assert trends is not None
        assert trends.category_trends is not None
        assert trends.category_trends["security"] == "improving"
        assert trends.category_trends["performance"] == "declining"
        assert trends.category_trends["ux"] == "stable"

    def test_compare_runs(self, temp_history_dir: Path):
        """Test comparing two quality runs."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save two runs
        run1 = QualityRunRecord(
            run_id="compare-001",
            task_alias="test_task",
            timestamp="2026-03-13T01:00:00",
            score=0.75,
            passed=False,
            phase="A",
            stop_reason="test",
            iteration=4,
            max_iterations=4,
            category_scores={"security": 0.8, "performance": 0.7},
            gate_passed=False,
        )
        run2 = QualityRunRecord(
            run_id="compare-002",
            task_alias="test_task",
            timestamp="2026-03-13T02:00:00",
            score=0.88,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=2,
            max_iterations=4,
            category_scores={"security": 0.9, "performance": 0.85},
            gate_passed=True,
        )

        manager.save_run(run1)
        manager.save_run(run2)

        comparison = manager.compare_runs("compare-001", "compare-002")

        assert comparison is not None
        assert comparison.run1_id == "compare-001"
        assert comparison.run2_id == "compare-002"
        assert comparison.score_delta == pytest.approx(0.13)
        assert comparison.score_delta_percent == pytest.approx(17.3, rel=0.1)
        assert comparison.score_improved is True
        assert comparison.iteration_delta == -2
        assert comparison.iteration_improved is True  # Fewer iterations is better
        assert comparison.category_deltas["security"] == pytest.approx(0.1)
        assert comparison.category_deltas["performance"] == pytest.approx(0.15)
        assert comparison.passed_comparison == "now_passed"
        assert comparison.gate_comparison == "now_passed"

    def test_compare_runs_not_found(self, temp_history_dir: Path):
        """Test compare_runs returns None when runs not found."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        comparison = manager.compare_runs("nonexistent-1", "nonexistent-2")

        assert comparison is None

    def test_get_recent_runs(self, temp_history_dir: Path):
        """Test getting recent runs."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save multiple runs
        for i in range(10):
            manager.save_run(QualityRunRecord(
                run_id=f"recent-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=0.7 + i * 0.02,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            ))

        recent = manager.get_recent_runs(limit=5)

        assert len(recent) == 5
        assert recent[0].run_id == "recent-009"

    def test_clear_history_all(self, temp_history_dir: Path):
        """Test clearing all history."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save some records
        for i in range(3):
            manager.save_run(QualityRunRecord(
                run_id=f"clear-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=0.8,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            ))

        # Clear all
        cleared_count = manager.clear_history()

        assert cleared_count == 3
        assert not manager.index_file.exists()

    def test_clear_history_by_task(self, temp_history_dir: Path):
        """Test clearing history for specific task alias."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save records for different tasks
        manager.save_run(QualityRunRecord(
            run_id="task1-001",
            task_alias="task1",
            timestamp="2026-03-13T01:00:00",
            score=0.8,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))
        manager.save_run(QualityRunRecord(
            run_id="task2-001",
            task_alias="task2",
            timestamp="2026-03-13T02:00:00",
            score=0.7,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))
        manager.save_run(QualityRunRecord(
            run_id="task1-002",
            task_alias="task1",
            timestamp="2026-03-13T03:00:00",
            score=0.9,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))

        # Clear only task1
        cleared_count = manager.clear_history(task_alias="task1")

        assert cleared_count == 2

        # Verify task2 record still exists
        remaining = manager.load_history()
        assert len(remaining) == 1
        assert remaining[0].task_alias == "task2"


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_save_quality_run(self, temp_history_dir: Path, sample_loop_result: Dict[str, Any]):
        """Test save_quality_run convenience function."""
        result_path = save_quality_run(
            sample_loop_result,
            criteria_name="api-spec",
            history_dir=temp_history_dir,
            duration_seconds=45.0,
        )

        assert result_path is not None
        assert Path(result_path).exists()

        # Verify content
        with open(result_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["run_id"] == "loop-run-001"
        assert data["criteria_name"] == "api-spec"

    def test_save_quality_run_with_valid_data(self, temp_history_dir: Path):
        """Test save_quality_run with minimal valid data."""
        # The function handles missing data gracefully by using defaults
        # Even with minimal data, it should create a record
        result = {
            "score": 0.75,
            "passed": True,
            "stop_reason": "test",
            "state": {
                "run_id": "minimal-run",
                "task_alias": "minimal",
                "started_at": "2026-03-13T00:00:00",
                "phase": "A",
                "iteration": 1,
                "max_iterations": 4,
            },
        }

        result_path = save_quality_run(
            result,
            criteria_name="minimal",
            history_dir=temp_history_dir,
        )

        # Should succeed and return a path
        assert result_path is not None
        assert Path(result_path).exists()

    def test_get_quality_statistics(self, temp_history_dir: Path):
        """Test get_quality_statistics convenience function."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)
        manager.save_run(QualityRunRecord(
            run_id="conv-stat-001",
            task_alias="test_task",
            timestamp="2026-03-13T01:00:00",
            score=0.85,
            passed=True,
            phase="A",
            stop_reason="test",
            iteration=1,
            max_iterations=4,
        ))

        stats = get_quality_statistics(history_dir=temp_history_dir)

        assert stats is not None
        assert stats.total_runs == 1
        assert stats.avg_score == 0.85

    def test_get_quality_trends(self, temp_history_dir: Path):
        """Test get_quality_trends convenience function."""
        manager = QualityHistoryManager(history_dir=temp_history_dir)

        # Save 5 runs with improving scores
        for i in range(5):
            manager.save_run(QualityRunRecord(
                run_id=f"conv-trend-{i:03d}",
                task_alias="test_task",
                timestamp=f"2026-03-13T{i:02d}:00:00",
                score=0.70 + i * 0.05,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            ))

        trends = get_quality_trends(history_dir=temp_history_dir, min_runs=3)

        assert trends is not None
        assert trends.direction == "improving"


class TestFormattingFunctions:
    """Test report formatting functions."""

    def test_format_statistics_report(self):
        """Test formatting statistics report."""
        stats = QualityStatistics(
            total_runs=10,
            passed_runs=8,
            failed_runs=2,
            pass_rate=0.8,
            avg_score=0.85,
            min_score=0.70,
            max_score=0.95,
            avg_iterations=2.5,
            most_failed_category="performance",
            most_used_profile="balanced",
            most_used_criteria="backend",
        )

        report = format_statistics_report(stats, task_alias="test_task")

        assert "Quality Statistics for 'test_task'" in report
        assert "**Total Runs:** 10" in report
        assert "**Passed:** 8 | **Failed:** 2" in report
        assert "**Pass Rate:** 80.0%" in report
        assert "**Average:** 0.850" in report
        assert "**Min:** 0.700 | **Max:** 0.950" in report
        assert "**Most Failed Category:** performance" in report
        assert "**Most Used Profile:** balanced" in report
        assert "**Most Used Criteria:** backend" in report

    def test_format_statistics_report_no_task_alias(self):
        """Test formatting statistics without task alias."""
        stats = QualityStatistics(
            total_runs=5,
            passed_runs=3,
            failed_runs=2,
            pass_rate=0.6,
            avg_score=0.75,
            min_score=0.60,
            max_score=0.90,
            avg_iterations=3.0,
        )

        report = format_statistics_report(stats)

        assert "## Quality Statistics" in report
        assert "**Total Runs:** 5" in report
        # Should not show most failed category when None
        assert "Most Failed" not in report

    def test_format_trends_report_improving(self):
        """Test formatting trends report for improving trend."""
        trend = QualityTrend(
            direction="improving",
            score_change=0.15,
            score_change_percent=18.75,
            trend_description="Strong improvement (+18.8%)",
            recent_avg=0.90,
            overall_avg=0.825,
            category_trends={"security": "improving", "performance": "stable"},
        )

        report = format_trends_report(trend, task_alias="test_task")

        assert "Quality Trends for 'test_task'" in report
        assert "IMPROVING" in report
        assert "📈" in report
        assert "Strong improvement" in report
        assert "**Change:** +0.150 (+18.8%)" in report
        assert "- **security:** 📈 improving" in report
        assert "- **performance:** ➡️ stable" in report

    def test_format_trends_report_declining(self):
        """Test formatting trends report for declining trend."""
        trend = QualityTrend(
            direction="declining",
            score_change=-0.10,
            score_change_percent=-12.5,
            trend_description="Moderate decline (-12.5%)",
            recent_avg=0.70,
            overall_avg=0.75,
        )

        report = format_trends_report(trend)

        assert "DECLINING" in report
        assert "📉" in report
        assert "decline" in report.lower()
        assert "**Change:** -0.100" in report

    def test_format_trends_report_stable(self):
        """Test formatting trends report for stable trend."""
        trend = QualityTrend(
            direction="stable",
            score_change=0.01,
            score_change_percent=1.2,
            trend_description="Quality scores have remained stable",
            recent_avg=0.80,
            overall_avg=0.795,
        )

        report = format_trends_report(trend)

        assert "STABLE" in report
        assert "➡️" in report
        assert "stable" in report.lower()

    def test_format_history_json(self):
        """Test formatting history as JSON."""
        stats = QualityStatistics(
            total_runs=5,
            passed_runs=4,
            failed_runs=1,
            pass_rate=0.8,
            avg_score=0.85,
            min_score=0.70,
            max_score=0.95,
            avg_iterations=2.5,
        )
        trend = QualityTrend(
            direction="improving",
            score_change=0.10,
            score_change_percent=12.5,
            trend_description="Improvement",
            recent_avg=0.90,
            overall_avg=0.85,
        )
        recent_runs = [
            QualityRunRecord(
                run_id="json-001",
                task_alias="test_task",
                timestamp="2026-03-13T01:00:00",
                score=0.85,
                passed=True,
                phase="A",
                stop_reason="test",
                iteration=1,
                max_iterations=4,
            )
        ]

        json_str = format_history_json(
            statistics=stats,
            trends=trend,
            recent_runs=recent_runs,
            task_alias="test_task",
        )

        data = json.loads(json_str)

        assert data["task_alias"] == "test_task"
        assert data["statistics"]["total_runs"] == 5
        assert data["statistics"]["pass_rate"] == 0.8
        assert data["trends"]["direction"] == "improving"
        assert len(data["recent_runs"]) == 1
        assert data["recent_runs"][0]["run_id"] == "json-001"

    def test_format_history_json_partial(self):
        """Test formatting history JSON with partial data."""
        stats = QualityStatistics(
            total_runs=3,
            passed_runs=2,
            failed_runs=1,
            pass_rate=0.67,
            avg_score=0.80,
            min_score=0.70,
            max_score=0.90,
            avg_iterations=2.0,
        )

        json_str = format_history_json(statistics=stats)

        data = json.loads(json_str)

        assert "statistics" in data
        assert data["statistics"]["total_runs"] == 3
        assert "trends" not in data
        assert "recent_runs" not in data
