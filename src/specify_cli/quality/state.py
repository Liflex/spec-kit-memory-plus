"""
Loop State Manager

Handles persistence of loop state to run.json, history.jsonl, and current.json.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
import jsonlines

from specify_cli.quality.models import LoopState, LoopEvent, LoopStatus


class LoopStateManager:
    """Manage loop state persistence"""

    def __init__(self, evolution_dir: Optional[Path] = None):
        """Initialize state manager

        Args:
            evolution_dir: Directory for loop state files (default: .speckit/evolution/)
        """
        if evolution_dir is None:
            from specify_cli.cli_config import get_project_dir
            project_dir = get_project_dir()
            evolution_dir = project_dir / ".speckit" / "evolution"

        self.evolution_dir = Path(evolution_dir)
        self.evolution_dir.mkdir(parents=True, exist_ok=True)

        self.current_json_path = self.evolution_dir / "current.json"

    def get_loop_dir(self, task_alias: str) -> Path:
        """Get directory for a specific loop"""
        return self.evolution_dir / task_alias

    def get_run_json_path(self, task_alias: str) -> Path:
        """Get path to run.json for a loop"""
        return self.get_loop_dir(task_alias) / "run.json"

    def get_history_jsonl_path(self, task_alias: str) -> Path:
        """Get path to history.jsonl for a loop"""
        return self.get_loop_dir(task_alias) / "history.jsonl"

    def get_artifact_path(self, task_alias: str) -> Path:
        """Get path to artifact.md for a loop"""
        return self.get_loop_dir(task_alias) / "artifact.md"

    def save_state(self, state: LoopState) -> None:
        """Save loop state to run.json

        Args:
            state: Loop state to save
        """
        loop_dir = self.get_loop_dir(state.task_alias)
        loop_dir.mkdir(parents=True, exist_ok=True)

        run_json_path = self.get_run_json_path(state.task_alias)

        # Update timestamps
        now = datetime.now().isoformat()
        if state.started_at is None:
            state.started_at = now
        state.updated_at = now

        # Write run.json
        with open(run_json_path, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

        # Update current.json pointer if running
        if state.status == LoopStatus.running:
            with open(self.current_json_path, "w", encoding="utf-8") as f:
                json.dump({
                    "active_loop": state.task_alias,
                    "run_id": state.run_id,
                    "updated_at": now,
                }, f, indent=2, ensure_ascii=False)

    def load_state(self, task_alias: str) -> Optional[LoopState]:
        """Load loop state from run.json

        Args:
            task_alias: Task alias for the loop

        Returns:
            LoopState if found, None otherwise
        """
        run_json_path = self.get_run_json_path(task_alias)

        if not run_json_path.exists():
            return None

        with open(run_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return LoopState.from_dict(data)

    def get_active_loop(self) -> Optional[dict]:
        """Get active loop info from current.json

        Returns:
            Dict with active_loop and run_id if active, None otherwise
        """
        if not self.current_json_path.exists():
            return None

        with open(self.current_json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def clear_active_loop(self) -> None:
        """Remove current.json (no active loop)"""
        if self.current_json_path.exists():
            self.current_json_path.unlink()

    def append_event(self, event: LoopEvent, task_alias: str) -> None:
        """Append event to history.jsonl

        Args:
            event: Event to append
            task_alias: Task alias for the loop
        """
        loop_dir = self.get_loop_dir(task_alias)
        loop_dir.mkdir(parents=True, exist_ok=True)

        history_path = self.get_history_jsonl_path(task_alias)

        with open(history_path, "a", encoding="utf-8") as f:
            f.write(event.to_jsonl() + "\n")

    def get_history(self, task_alias: str, limit: Optional[int] = None) -> list[LoopEvent]:
        """Read events from history.jsonl

        Args:
            task_alias: Task alias for the loop
            limit: Maximum number of events to read (None = all)

        Returns:
            List of LoopEvent objects
        """
        history_path = self.get_history_jsonl_path(task_alias)

        if not history_path.exists():
            return []

        events = []
        with open(history_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    events.append(LoopEvent.from_dict(data))

        if limit is not None:
            events = events[-limit:]

        return events

    def save_artifact(self, artifact: str, task_alias: str) -> None:
        """Save artifact content to artifact.md

        Args:
            artifact: Artifact content (markdown)
            task_alias: Task alias for the loop
        """
        loop_dir = self.get_loop_dir(task_alias)
        loop_dir.mkdir(parents=True, exist_ok=True)

        artifact_path = self.get_artifact_path(task_alias)

        with open(artifact_path, "w", encoding="utf-8") as f:
            f.write(artifact)

    def load_artifact(self, task_alias: str) -> Optional[str]:
        """Load artifact content from artifact.md

        Args:
            task_alias: Task alias for the loop

        Returns:
            Artifact content if found, None otherwise
        """
        artifact_path = self.get_artifact_path(task_alias)

        if not artifact_path.exists():
            return None

        with open(artifact_path, "r", encoding="utf-8") as f:
            return f.read()

    def list_loops(self) -> list[dict]:
        """List all loops with their status

        Returns:
            List of dicts with task_alias, status, iteration, phase, current_score
        """
        loops = []

        for loop_dir in self.evolution_dir.iterdir():
            if not loop_dir.is_dir():
                continue

            run_json_path = loop_dir / "run.json"
            if not run_json_path.exists():
                continue

            with open(run_json_path, "r", encoding="utf-8") as f:
                state_data = json.load(f)

            loops.append({
                "task_alias": loop_dir.name,
                "status": state_data.get("status"),
                "iteration": state_data.get("iteration"),
                "max_iterations": state_data.get("max_iterations"),
                "phase": state_data.get("phase"),
                "current_score": state_data.get("current_score"),
                "updated_at": state_data.get("updated_at"),
            })

        # Sort by updated_at desc
        loops.sort(key=lambda x: x.get("updated_at", ""), reverse=True)

        return loops

    def delete_loop(self, task_alias: str) -> bool:
        """Delete all files for a loop

        Args:
            task_alias: Task alias for the loop

        Returns:
            True if deleted, False if not found or running
        """
        state = self.load_state(task_alias)

        if state and state.status == LoopStatus.running:
            # Don't delete running loops
            return False

        loop_dir = self.get_loop_dir(task_alias)

        if not loop_dir.exists():
            return False

        # Delete all files in loop directory
        for file in loop_dir.iterdir():
            file.unlink()

        # Remove directory
        loop_dir.rmdir()

        # Clear current.json if this was the active loop
        active = self.get_active_loop()
        if active and active.get("active_loop") == task_alias:
            self.clear_active_loop()

        return True
