"""
Unit tests for LoopStateManager
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from specify_cli.quality.state import LoopStateManager
from specify_cli.quality.models import LoopState, LoopStatus, Phase, LoopEvent


class TestLoopStateManager:
    """Test LoopStateManager class"""

    def setup_method(self):
        """Setup test fixtures"""
        # Use a temporary directory for testing
        import tempfile
        self.temp_dir = Path(tempfile.mkdtemp())
        self.state_manager = LoopStateManager(evolution_dir=self.temp_dir)

    def teardown_method(self):
        """Cleanup test fixtures"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_save_and_load_state(self):
        """Test saving and loading loop state"""
        state = LoopState(
            run_id="test-run-001",
            task_alias="test-task",
            status=LoopStatus.running,
            iteration=1,
            max_iterations=4,
            phase=Phase.A,
            current_step="PLAN",
            current_score=0.5,
        )

        self.state_manager.save_state(state)
        loaded_state = self.state_manager.load_state("test-task")

        assert loaded_state is not None
        assert loaded_state.run_id == "test-run-001"
        assert loaded_state.task_alias == "test-task"
        assert loaded_state.iteration == 1

    def test_load_nonexistent_state(self):
        """Test loading non-existent state"""
        state = self.state_manager.load_state("nonexistent")

        assert state is None

    def test_save_artifact(self):
        """Test saving artifact content"""
        artifact_content = "# Test Artifact\n\nSome content here."

        self.state_manager.save_artifact(artifact_content, "test-task")

        loaded_artifact = self.state_manager.load_artifact("test-task")

        assert loaded_artifact == artifact_content

    def test_load_nonexistent_artifact(self):
        """Test loading non-existent artifact"""
        artifact = self.state_manager.load_artifact("nonexistent")

        assert artifact is None

    def test_append_and_get_events(self):
        """Test appending and retrieving events"""
        event = LoopEvent(
            timestamp=datetime.now().isoformat(),
            event_type="test_event",
            iteration=1,
            phase="A",
            details={"test": "data"}
        )

        self.state_manager.append_event(event, "test-task")
        events = self.state_manager.get_history("test-task")

        assert len(events) == 1
        assert events[0].event_type == "test_event"

    def test_get_history_with_limit(self):
        """Test getting history with limit"""
        for i in range(5):
            event = LoopEvent(
                timestamp=datetime.now().isoformat(),
                event_type=f"event_{i}",
                iteration=i + 1,
                phase="A",
            )
            self.state_manager.append_event(event, "test-task")

        events = self.state_manager.get_history("test-task", limit=3)

        assert len(events) == 3

    def test_active_loop_pointer(self):
        """Test active loop pointer (current.json)"""
        state = LoopState(
            run_id="test-run-001",
            task_alias="test-task",
            status=LoopStatus.running,
            iteration=1,
            max_iterations=4,
            phase=Phase.A,
            current_step="PLAN",
        )

        self.state_manager.save_state(state)

        active = self.state_manager.get_active_loop()

        assert active is not None
        assert active["active_loop"] == "test-task"
        assert active["run_id"] == "test-run-001"

    def test_clear_active_loop(self):
        """Test clearing active loop pointer"""
        state = LoopState(
            run_id="test-run-001",
            task_alias="test-task",
            status=LoopStatus.running,
            iteration=1,
            max_iterations=4,
            phase=Phase.A,
            current_step="PLAN",
        )

        self.state_manager.save_state(state)
        self.state_manager.clear_active_loop()

        active = self.state_manager.get_active_loop()

        assert active is None

    def test_list_loops(self):
        """Test listing all loops"""
        # Create two loops
        for i in range(2):
            state = LoopState(
                run_id=f"test-run-{i:03d}",
                task_alias=f"test-task-{i}",
                status=LoopStatus.completed,
                iteration=4,
                max_iterations=4,
                phase=Phase.B,
                current_step="DONE",
                current_score=0.9,
            )
            self.state_manager.save_state(state)
            self.state_manager.clear_active_loop()

        loops = self.state_manager.list_loops()

        assert len(loops) == 2

    def test_delete_loop(self):
        """Test deleting a loop"""
        state = LoopState(
            run_id="test-run-001",
            task_alias="test-task",
            status=LoopStatus.completed,
            iteration=4,
            max_iterations=4,
            phase=Phase.B,
            current_step="DONE",
        )

        self.state_manager.save_state(state)
        self.state_manager.clear_active_loop()

        deleted = self.state_manager.delete_loop("test-task")

        assert deleted is True

        # Verify deletion
        loaded_state = self.state_manager.load_state("test-task")
        assert loaded_state is None

    def test_delete_running_loop_fails(self):
        """Test that deleting a running loop fails"""
        state = LoopState(
            run_id="test-run-001",
            task_alias="test-task",
            status=LoopStatus.running,
            iteration=1,
            max_iterations=4,
            phase=Phase.A,
            current_step="PLAN",
        )

        self.state_manager.save_state(state)

        deleted = self.state_manager.delete_loop("test-task")

        assert deleted is False
