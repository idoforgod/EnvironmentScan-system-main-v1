#!/usr/bin/env python3
"""
Unified Task Manager
Bridges internal task tracking with Claude Code Task API

This module provides seamless integration between:
- Internal task_graph.json (orchestrator's 5 core tasks)
- Claude Code Task API (18 user-visible workflow tasks)
- workflow-status.json (source of truth for task mapping)

Key Principles:
1. Non-critical: Task API failures don't stop workflow
2. Graceful degradation: Falls back silently if API unavailable
3. User visibility: Enables Ctrl+T progress tracking
4. Zero breaking changes: Purely additive functionality
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class UnifiedTaskManager:
    """
    Manages dual-state task tracking:
    - Internal: task_graph.json (orchestrator use)
    - External: Claude Code Task API (user Ctrl+T visibility)

    The workflow-status.json file is the source of truth for task_mapping.
    """

    def __init__(self, project_root: Path):
        """
        Initialize task manager.

        Args:
            project_root: Path to env-scanning/ directory
        """
        self.project_root = project_root
        self.workflow_status_path = project_root / "logs" / "workflow-status.json"
        self.task_mapping: Dict[str, str] = {}  # step_id -> task_id
        self.task_api_enabled = True

        # Ensure logs directory exists
        self.workflow_status_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing task mapping if available
        self._load_task_mapping()

    def _load_task_mapping(self):
        """Load task mapping from workflow-status.json"""
        if self.workflow_status_path.exists():
            try:
                with open(self.workflow_status_path, 'r') as f:
                    data = json.load(f)
                    self.task_mapping = data.get("task_mapping", {})
            except Exception as e:
                logger.warning(f"Failed to load task mapping: {e}")
                self.task_mapping = {}

    def _save_task_mapping(self):
        """Save task mapping to workflow-status.json"""
        try:
            # Load existing data
            if self.workflow_status_path.exists():
                with open(self.workflow_status_path, 'r') as f:
                    data = json.load(f)
            else:
                data = {
                    "workflow": "environmental-scanning",
                    "created_at": datetime.now().isoformat()
                }

            # Update task_mapping
            data["task_mapping"] = self.task_mapping
            data["last_updated"] = datetime.now().isoformat()

            # Save
            with open(self.workflow_status_path, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"Failed to save task mapping: {e}")

    def initialize_workflow_tasks(self, date: str) -> bool:
        """
        Create all 18 workflow tasks in Claude Code Task API at workflow start.

        This provides Ctrl+T visibility for the entire workflow structure.

        Args:
            date: Date string (YYYY-MM-DD) for task descriptions

        Returns:
            True if successful, False if Task API unavailable
        """
        if not self.task_api_enabled:
            logger.info("Task API disabled, skipping workflow task initialization")
            return False

        try:
            # Define workflow tasks (3 Phases + ~15 Steps)
            workflow_tasks = self._define_workflow_tasks(date)

            # Create tasks via Task API
            for task_def in workflow_tasks:
                task_id = self._create_task(
                    subject=task_def["subject"],
                    description=task_def["description"],
                    activeForm=task_def["activeForm"]
                )

                if task_id:
                    self.task_mapping[task_def["step_id"]] = task_id
                    logger.debug(f"Created task {task_def['step_id']}: {task_id}")

            # Save mapping to workflow-status.json
            self._save_task_mapping()

            logger.info(f"Initialized {len(self.task_mapping)} workflow tasks")
            return True

        except Exception as e:
            logger.warning(f"Task API initialization failed: {e}")
            logger.info("Continuing workflow without Task API visibility")
            self.task_api_enabled = False
            return False

    def _define_workflow_tasks(self, date: str) -> List[Dict]:
        """
        Define the 18 workflow tasks structure.

        Returns:
            List of task definitions with step_id, subject, description, activeForm
        """
        return [
            # Phase 1: Research (4 steps)
            {
                "step_id": "phase1",
                "subject": "Phase 1: Research",
                "description": f"Research phase for {date} environmental scan. Load archives, scan sources, filter duplicates.",
                "activeForm": "Executing Phase 1 research"
            },
            {
                "step_id": "1.1",
                "subject": "Load archive context",
                "description": "Load previous scan results from archive for duplicate detection",
                "activeForm": "Loading archive context"
            },
            {
                "step_id": "1.2",
                "subject": "Scan multiple sources",
                "description": "Scan arxiv, blogs, policy docs, patents using agent swarm parallelization",
                "activeForm": "Scanning multiple sources"
            },
            {
                "step_id": "1.2b",
                "subject": "Translate scan results to Korean",
                "description": "Parallel translation of raw scan results to Korean (50% faster)",
                "activeForm": "Translating scan results"
            },
            {
                "step_id": "1.3",
                "subject": "Filter duplicate signals",
                "description": "Remove duplicate signals using embedding-based deduplication",
                "activeForm": "Filtering duplicate signals"
            },
            {
                "step_id": "1.3b",
                "subject": "Translate filtered results to Korean",
                "description": "Parallel translation of filtered results to Korean (50% faster)",
                "activeForm": "Translating filtered results"
            },
            # Phase 2: Planning (3 steps)
            {
                "step_id": "phase2",
                "subject": "Phase 2: Planning",
                "description": f"Planning phase for {date} environmental scan. Verify classifications, analyze impacts, rank priorities.",
                "activeForm": "Executing Phase 2 planning"
            },
            {
                "step_id": "2.1",
                "subject": "Verify signal classifications",
                "description": "Verify STEEPs framework classifications for all signals",
                "activeForm": "Verifying signal classifications"
            },
            {
                "step_id": "2.2",
                "subject": "Analyze impact assessment",
                "description": "Assess likelihood, impact, time horizon for each signal",
                "activeForm": "Analyzing impact assessment"
            },
            {
                "step_id": "2.3",
                "subject": "Rank signal priorities",
                "description": "Rank signals by urgency and strategic importance",
                "activeForm": "Ranking signal priorities"
            },
            # Phase 3: Action (4 steps)
            {
                "step_id": "phase3",
                "subject": "Phase 3: Action",
                "description": f"Action phase for {date} environmental scan. Generate reports, archive results, notify completion.",
                "activeForm": "Executing Phase 3 actions"
            },
            {
                "step_id": "3.1",
                "subject": "Generate markdown report",
                "description": "Generate comprehensive markdown report with lazy loading optimization",
                "activeForm": "Generating markdown report"
            },
            {
                "step_id": "3.2",
                "subject": "Archive scan results",
                "description": "Archive daily scan results with versioning",
                "activeForm": "Archiving scan results"
            },
            {
                "step_id": "3.3",
                "subject": "Update signal database",
                "description": "Update persistent signal database with new entries",
                "activeForm": "Updating signal database"
            },
            {
                "step_id": "3.4",
                "subject": "Send completion notification",
                "description": "Send workflow completion notification with summary statistics",
                "activeForm": "Sending completion notification"
            }
        ]

    def _create_task(self, subject: str, description: str, activeForm: str) -> Optional[str]:
        """
        Create a task via Claude Code Task API.

        Args:
            subject: Task title (imperative form)
            description: Detailed task description
            activeForm: Present continuous form for spinner

        Returns:
            Task ID if successful, None if failed
        """
        # NOTE: This is a placeholder for actual Task API integration
        # In real implementation, this would call the TaskCreate tool
        # For now, we'll return a mock task ID for testing

        try:
            # Mock implementation - replace with actual TaskCreate call
            task_id = f"task-{hash(subject) % 100000}"
            return task_id

        except Exception as e:
            logger.error(f"TaskCreate failed: {e}")
            return None

    def mark_step_in_progress(self, step_id: str):
        """
        Mark a step as in_progress in Task API.

        This is called BEFORE step execution to provide real-time Ctrl+T updates.

        Args:
            step_id: Step identifier (e.g., "1.2", "2.1", "phase1")
        """
        if not self.task_api_enabled:
            return

        task_id = self.task_mapping.get(step_id)
        if not task_id:
            logger.debug(f"No task mapping for step {step_id}")
            return

        try:
            self._update_task_status(task_id, "in_progress")
            logger.debug(f"Marked step {step_id} as in_progress")

        except Exception as e:
            logger.warning(f"Failed to update task status: {e}")

    def mark_step_completed(self, step_id: str):
        """
        Mark a step as completed in Task API.

        This is called AFTER step execution to provide real-time Ctrl+T updates.

        Args:
            step_id: Step identifier (e.g., "1.2", "2.1", "phase1")
        """
        if not self.task_api_enabled:
            return

        task_id = self.task_mapping.get(step_id)
        if not task_id:
            logger.debug(f"No task mapping for step {step_id}")
            return

        try:
            self._update_task_status(task_id, "completed")
            logger.debug(f"Marked step {step_id} as completed")

        except Exception as e:
            logger.warning(f"Failed to update task status: {e}")

    def _update_task_status(self, task_id: str, status: str):
        """
        Update task status via Claude Code Task API.

        Args:
            task_id: Task ID from task_mapping
            status: New status ("in_progress" or "completed")
        """
        # NOTE: This is a placeholder for actual Task API integration
        # In real implementation, this would call the TaskUpdate tool

        try:
            # Mock implementation - replace with actual TaskUpdate call
            logger.debug(f"TaskUpdate({task_id}, {status})")

        except Exception as e:
            logger.warning(f"TaskUpdate failed: {e}")

    def get_task_mapping(self) -> Dict[str, str]:
        """
        Get current task mapping (step_id -> task_id).

        Returns:
            Dictionary mapping step IDs to Task API task IDs
        """
        return self.task_mapping.copy()

    def is_enabled(self) -> bool:
        """
        Check if Task API is enabled.

        Returns:
            True if Task API is available, False if gracefully degraded
        """
        return self.task_api_enabled
