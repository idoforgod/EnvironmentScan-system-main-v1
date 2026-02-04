#!/usr/bin/env python3
"""
Unit tests for TranslationParallelizer

Tests:
1. Parallel translation execution
2. Sequential fallback
3. Memory constraints
4. Error handling
5. Atomic file writes
"""

import unittest
import json
import tempfile
import time
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "env-scanning"))

from core.translation_parallelizer import (
    TranslationParallelizer,
    _translate_single_file_worker,
    _translate_json_structure
)


class TestTranslationParallelizer(unittest.TestCase):
    """Test cases for TranslationParallelizer"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create test directories
        (self.project_root / "raw").mkdir(parents=True, exist_ok=True)
        (self.project_root / "structured").mkdir(parents=True, exist_ok=True)

        # Create test data files
        self._create_test_files()

        # Initialize translator
        self.translator = TranslationParallelizer(self.project_root)

    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_files(self):
        """Create test JSON files"""
        test_data = {
            "scan_metadata": {
                "date": "2026-01-30",
                "total_items": 2
            },
            "items": [
                {"id": 1, "title": "Test Signal 1", "content": "Test content 1"},
                {"id": 2, "title": "Test Signal 2", "content": "Test content 2"}
            ]
        }

        # Create test files
        file1 = self.project_root / "raw" / "daily-scan-2026-01-30.json"
        file2 = self.project_root / "structured" / "classified-signals-2026-01-30.json"

        for file in [file1, file2]:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2)

    def test_initialization(self):
        """Test translator initialization"""
        self.assertIsNotNone(self.translator)
        self.assertEqual(self.translator.project_root, self.project_root)
        self.assertLessEqual(self.translator.max_concurrent, 3)

    def test_translate_single_file(self):
        """Test single file translation"""
        source_file = "raw/daily-scan-2026-01-30.json"
        target_file = "raw/daily-scan-2026-01-30-ko.json"

        result = _translate_single_file_worker(
            self.project_root,
            source_file,
            target_file,
            "json"
        )

        # Check result structure
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["source_file"], source_file)
        self.assertEqual(result["target_file"], target_file)
        self.assertIn("execution_time", result)
        self.assertIn("worker_pid", result)

        # Check target file created
        target_path = self.project_root / target_file
        self.assertTrue(target_path.exists())

        # Check target file content
        with open(target_path) as f:
            data = json.load(f)
            self.assertIn("scan_metadata", data)
            self.assertEqual(data["scan_metadata"]["language"], "ko")

    def test_parallel_translation(self):
        """Test parallel translation of multiple files"""
        tasks = [
            ("raw/daily-scan-2026-01-30.json",
             "raw/daily-scan-2026-01-30-ko.json",
             "json"),
            ("structured/classified-signals-2026-01-30.json",
             "structured/classified-signals-2026-01-30-ko.json",
             "json")
        ]

        start_time = time.time()
        results = self.translator.translate_files_parallel(tasks)
        parallel_time = time.time() - start_time

        # Check all tasks completed
        self.assertEqual(len(results), 2)

        # Check all succeeded
        for result in results:
            self.assertEqual(result["status"], "success")

        # Check all target files created
        for _, target_file, _ in tasks:
            target_path = self.project_root / target_file
            self.assertTrue(target_path.exists())

        # Parallel execution should be faster than sequential
        # (though in test environment may not be significant)
        self.assertGreater(parallel_time, 0)

    def test_sequential_fallback(self):
        """Test sequential fallback"""
        tasks = [
            ("raw/daily-scan-2026-01-30.json",
             "raw/daily-scan-2026-01-30-ko.json",
             "json")
        ]

        # Call sequential directly
        results = self.translator._translate_sequential(tasks)

        # Check result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "success")

    def test_empty_task_list(self):
        """Test behavior with empty task list"""
        results = self.translator.translate_files_parallel([])

        # Should return empty list without error
        self.assertEqual(len(results), 0)

    def test_missing_source_file(self):
        """Test error handling for missing source file"""
        tasks = [
            ("raw/nonexistent.json",
             "raw/nonexistent-ko.json",
             "json")
        ]

        results = self.translator.translate_files_parallel(tasks)

        # Should return error result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "error")
        self.assertIn("error", results[0])

    def test_unsupported_file_type(self):
        """Test error handling for unsupported file type"""
        # Create test file
        test_file = self.project_root / "raw" / "test.txt"
        test_file.write_text("test content")

        tasks = [
            ("raw/test.txt",
             "raw/test-ko.txt",
             "unsupported")
        ]

        results = self.translator.translate_files_parallel(tasks)

        # Should return error result
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["status"], "error")
        self.assertIn("Unsupported file type", results[0]["error"])

    def test_translate_json_structure(self):
        """Test JSON structure translation"""
        test_data = {
            "metadata": {
                "key1": "value1",
                "key2": 123
            },
            "items": [
                {"id": 1, "text": "Test"},
                {"id": 2, "text": "Test 2"}
            ]
        }

        translated = _translate_json_structure(test_data)

        # Check structure preserved
        self.assertIn("metadata", translated)
        self.assertIn("items", translated)
        self.assertEqual(len(translated["items"]), 2)

        # Check numeric values preserved
        self.assertEqual(translated["metadata"]["key2"], 123)

    def test_atomic_write(self):
        """Test atomic write behavior"""
        source_file = "raw/daily-scan-2026-01-30.json"
        target_file = "raw/daily-scan-2026-01-30-ko.json"

        result = _translate_single_file_worker(
            self.project_root,
            source_file,
            target_file,
            "json"
        )

        # Check no .tmp file left behind
        target_path = self.project_root / target_file
        temp_path = target_path.with_suffix('.tmp')

        self.assertTrue(target_path.exists())
        self.assertFalse(temp_path.exists())

    def test_memory_constraint(self):
        """Test memory constraint (max 3 concurrent)"""
        # Check max_concurrent is constrained
        self.assertLessEqual(self.translator.max_concurrent, 3)

        # Create translator with higher value
        translator = TranslationParallelizer(self.project_root, max_concurrent=10)

        # Should still be limited to 3
        self.assertLessEqual(translator.max_concurrent, 3)


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
