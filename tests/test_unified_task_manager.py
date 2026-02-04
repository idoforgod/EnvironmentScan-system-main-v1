#!/usr/bin/env python3
"""
Unit tests for UnifiedTaskManager

Tests:
1. Task initialization
2. Task status updates
3. Graceful degradation when Task API unavailable
4. Task mapping persistence
5. Error handling
"""

import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "env-scanning"))

from core.unified_task_manager import UnifiedTaskManager


class TestUnifiedTaskManager(unittest.TestCase):
    """Test cases for UnifiedTaskManager"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create logs directory
        (self.project_root / "logs").mkdir(parents=True, exist_ok=True)

        # Initialize task manager
        self.task_manager = UnifiedTaskManager(self.project_root)

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test task manager initialization"""
        self.assertIsNotNone(self.task_manager)
        self.assertEqual(self.task_manager.project_root, self.project_root)
        self.assertTrue(self.task_manager.task_api_enabled)
        self.assertEqual(len(self.task_manager.task_mapping), 0)

    def test_workflow_tasks_definition(self):
        """Test workflow tasks are correctly defined"""
        date_str = "2026-01-30"
        tasks = self.task_manager._define_workflow_tasks(date_str)

        # Check we have 15 tasks (3 phases + 12 steps)
        self.assertGreaterEqual(len(tasks), 15)

        # Check task structure
        for task in tasks:
            self.assertIn("step_id", task)
            self.assertIn("subject", task)
            self.assertIn("description", task)
            self.assertIn("activeForm", task)

        # Check specific tasks exist
        step_ids = [task["step_id"] for task in tasks]
        self.assertIn("phase1", step_ids)
        self.assertIn("1.2", step_ids)
        self.assertIn("1.2b", step_ids)
        self.assertIn("1.3", step_ids)

    def test_initialize_workflow_tasks(self):
        """Test workflow task initialization"""
        date_str = "2026-01-30"

        # Initialize tasks
        success = self.task_manager.initialize_workflow_tasks(date_str)

        # Should succeed (mock implementation)
        self.assertTrue(success)

        # Check task mapping created
        self.assertGreater(len(self.task_manager.task_mapping), 0)

        # Check workflow-status.json created
        workflow_status_path = self.project_root / "logs" / "workflow-status.json"
        self.assertTrue(workflow_status_path.exists())

        # Check workflow-status.json content
        with open(workflow_status_path) as f:
            data = json.load(f)
            self.assertIn("task_mapping", data)
            self.assertIn("last_updated", data)

    def test_task_mapping_persistence(self):
        """Test task mapping persists across instances"""
        date_str = "2026-01-30"

        # Initialize tasks with first instance
        self.task_manager.initialize_workflow_tasks(date_str)
        original_mapping = self.task_manager.task_mapping.copy()

        # Create new instance (should load mapping)
        new_manager = UnifiedTaskManager(self.project_root)

        # Check mapping loaded correctly
        self.assertEqual(new_manager.task_mapping, original_mapping)

    def test_mark_step_in_progress(self):
        """Test marking step as in_progress"""
        date_str = "2026-01-30"
        self.task_manager.initialize_workflow_tasks(date_str)

        # Mark step in progress
        step_id = "1.2"
        self.task_manager.mark_step_in_progress(step_id)

        # Should not raise exception (mock implementation logs only)
        self.assertTrue(True)

    def test_mark_step_completed(self):
        """Test marking step as completed"""
        date_str = "2026-01-30"
        self.task_manager.initialize_workflow_tasks(date_str)

        # Mark step completed
        step_id = "1.2"
        self.task_manager.mark_step_completed(step_id)

        # Should not raise exception (mock implementation logs only)
        self.assertTrue(True)

    def test_graceful_degradation(self):
        """Test graceful degradation when Task API unavailable"""
        # Disable Task API
        self.task_manager.task_api_enabled = False

        # Try to initialize tasks
        date_str = "2026-01-30"
        success = self.task_manager.initialize_workflow_tasks(date_str)

        # Should return False but not raise exception
        self.assertFalse(success)

        # Try to update task status
        self.task_manager.mark_step_in_progress("1.2")
        self.task_manager.mark_step_completed("1.2")

        # Should not raise exception
        self.assertTrue(True)

    def test_get_task_mapping(self):
        """Test getting task mapping"""
        date_str = "2026-01-30"
        self.task_manager.initialize_workflow_tasks(date_str)

        # Get task mapping
        mapping = self.task_manager.get_task_mapping()

        # Should return copy of mapping
        self.assertIsInstance(mapping, dict)
        self.assertEqual(mapping, self.task_manager.task_mapping)

        # Should be a copy (not reference)
        mapping["test"] = "value"
        self.assertNotIn("test", self.task_manager.task_mapping)

    def test_is_enabled(self):
        """Test checking if Task API is enabled"""
        # Initially enabled
        self.assertTrue(self.task_manager.is_enabled())

        # Disable
        self.task_manager.task_api_enabled = False
        self.assertFalse(self.task_manager.is_enabled())

    def test_missing_step_id(self):
        """Test behavior with non-existent step ID"""
        date_str = "2026-01-30"
        self.task_manager.initialize_workflow_tasks(date_str)

        # Try to update non-existent step
        self.task_manager.mark_step_in_progress("99.99")
        self.task_manager.mark_step_completed("99.99")

        # Should not raise exception (graceful handling)
        self.assertTrue(True)


def main():
    """Run tests"""
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run tests
    unittest.main(verbosity=2)


if __name__ == "__main__":
    main()
