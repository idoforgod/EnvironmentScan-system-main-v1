#!/usr/bin/env python3
"""
Integration Test: Translation Parallelization
Tests the full translation workflow with real orchestrator integration
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent / "env-scanning"))

from core.translation_parallelizer import TranslationParallelizer


def create_test_data(project_root: Path, date_str: str):
    """Create realistic test data for translation"""

    # Create directories
    (project_root / "raw").mkdir(parents=True, exist_ok=True)
    (project_root / "structured").mkdir(parents=True, exist_ok=True)

    # Sample data mimicking real scan results
    scan_data = {
        "scan_metadata": {
            "date": date_str,
            "parallelization": "agent_swarm_multiprocessing",
            "execution_mode": "parallel",
            "agents_used": ["arxiv", "blog", "policy", "patent"],
            "total_items": 10,
            "total_sources_scanned": 4
        },
        "items": [
            {
                "id": 1,
                "title": "AI Breakthrough in Language Models",
                "source": "arXiv",
                "category": "Technology",
                "description": "New research shows significant improvements in LLM efficiency"
            },
            {
                "id": 2,
                "title": "Climate Policy Updates",
                "source": "Federal Register",
                "category": "Environment",
                "description": "New regulations for carbon emissions"
            },
            {
                "id": 3,
                "title": "Economic Outlook 2026",
                "source": "Economic Blog",
                "category": "Economy",
                "description": "Analysis of global economic trends"
            }
        ]
    }

    classified_data = {
        "scan_metadata": {
            "date": date_str,
            "classification": "STEEPs",
            "total_items": 10
        },
        "items": [
            {
                "id": 1,
                "signal": "AI Breakthrough in Language Models",
                "steep_category": "Technology",
                "likelihood": "High",
                "impact": "High",
                "time_horizon": "Near-term (1-2 years)"
            },
            {
                "id": 2,
                "signal": "Climate Policy Updates",
                "steep_category": "Environment",
                "likelihood": "Medium",
                "impact": "High",
                "time_horizon": "Mid-term (3-5 years)"
            }
        ]
    }

    # Write test files
    scan_file = project_root / "raw" / f"daily-scan-{date_str}.json"
    classified_file = project_root / "structured" / f"classified-signals-{date_str}.json"

    with open(scan_file, 'w', encoding='utf-8') as f:
        json.dump(scan_data, f, indent=2, ensure_ascii=False)

    with open(classified_file, 'w', encoding='utf-8') as f:
        json.dump(classified_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Test data created:")
    print(f"  • {scan_file.name} ({scan_file.stat().st_size} bytes)")
    print(f"  • {classified_file.name} ({classified_file.stat().st_size} bytes)")

    return scan_file, classified_file


def test_parallel_translation():
    """Test parallel translation with realistic data"""

    print("=" * 70)
    print("Integration Test: Translation Parallelization")
    print("=" * 70)

    project_root = Path(__file__).parent.parent / "env-scanning"
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Step 1: Create test data
    print("\n1. Creating test data...")
    scan_file, classified_file = create_test_data(project_root, date_str)

    # Step 2: Initialize translator
    print("\n2. Initializing translator...")
    translator = TranslationParallelizer(project_root)
    print(f"✓ Translator initialized: {translator.max_concurrent} max workers")

    # Step 3: Define translation tasks
    print("\n3. Defining translation tasks...")
    tasks = [
        (f"raw/daily-scan-{date_str}.json",
         f"raw/daily-scan-{date_str}-ko.json",
         "json"),
        (f"structured/classified-signals-{date_str}.json",
         f"structured/classified-signals-{date_str}-ko.json",
         "json")
    ]
    print(f"✓ {len(tasks)} translation tasks defined")

    # Step 4: Execute parallel translation
    print("\n4. Executing parallel translation...")
    print("   (This simulates Step 1.2b in the workflow)")

    start_time = time.time()
    results = translator.translate_files_parallel(tasks)
    parallel_time = time.time() - start_time

    # Step 5: Analyze results
    print("\n5. Results:")
    success_count = 0
    for result in results:
        status_icon = "✓" if result["status"] == "success" else "✗"
        print(f"   {status_icon} {result['source_file']}")
        print(f"      → {result['target_file']}")
        print(f"      Time: {result['execution_time']:.3f}s")
        print(f"      Worker PID: {result.get('worker_pid', 'N/A')}")

        if result["status"] == "success":
            success_count += 1
        else:
            print(f"      Error: {result.get('error', 'Unknown')}")

    print(f"\n   Total time: {parallel_time:.3f}s")
    print(f"   Success rate: {success_count}/{len(tasks)}")

    # Step 6: Verify outputs
    print("\n6. Verifying outputs...")
    for _, target_file, _ in tasks:
        target_path = project_root / target_file
        if target_path.exists():
            size = target_path.stat().st_size
            print(f"   ✓ {target_file} ({size} bytes)")

            # Verify it's valid JSON with translation metadata
            with open(target_path) as f:
                data = json.load(f)
                if "scan_metadata" in data:
                    lang = data["scan_metadata"].get("language")
                    translated_at = data["scan_metadata"].get("translated_at")
                    print(f"      Language: {lang}, Translated at: {translated_at}")
        else:
            print(f"   ✗ {target_file} NOT FOUND")
            return False

    # Step 7: Performance analysis
    print("\n7. Performance Analysis:")
    print(f"   Parallel execution time: {parallel_time:.3f}s")

    # Estimate sequential time (sum of individual times)
    sequential_estimate = sum(r["execution_time"] for r in results)
    print(f"   Sequential estimate: {sequential_estimate:.3f}s")

    if parallel_time < sequential_estimate:
        speedup = sequential_estimate / parallel_time
        print(f"   Speedup: {speedup:.2f}x ✨")
    else:
        print(f"   Note: Parallel overhead detected (small files)")

    # Step 8: Check for parallel execution evidence
    print("\n8. Parallel Execution Evidence:")
    worker_pids = set(r.get('worker_pid') for r in results if r.get('worker_pid'))
    if len(worker_pids) > 1:
        print(f"   ✓ Multiple workers detected: {len(worker_pids)} different PIDs")
        print(f"     Worker PIDs: {sorted(worker_pids)}")
    else:
        print(f"   ⚠ Only one worker PID detected (sequential or single task)")

    # Success criteria
    print("\n" + "=" * 70)
    print("Test Results:")
    print("=" * 70)

    all_success = success_count == len(tasks)
    outputs_exist = all(
        (project_root / target).exists()
        for _, target, _ in tasks
    )

    if all_success and outputs_exist:
        print("✅ PASS: All translations successful")
        print(f"   • {success_count}/{len(tasks)} files translated")
        print(f"   • Execution time: {parallel_time:.3f}s")
        print(f"   • All output files created")
        return True
    else:
        print("❌ FAIL: Translation issues detected")
        return False


def test_sequential_fallback():
    """Test that sequential fallback works"""

    print("\n" + "=" * 70)
    print("Integration Test: Sequential Fallback")
    print("=" * 70)

    project_root = Path(__file__).parent.parent / "env-scanning"
    date_str = datetime.now().strftime("%Y-%m-%d")

    translator = TranslationParallelizer(project_root)

    # Create task with valid file
    tasks = [(f"raw/daily-scan-{date_str}.json",
              f"raw/daily-scan-{date_str}-ko-fallback.json",
              "json")]

    print("\n1. Testing sequential fallback...")
    start_time = time.time()
    results = translator._translate_sequential(tasks)
    fallback_time = time.time() - start_time

    print(f"✓ Sequential fallback completed in {fallback_time:.3f}s")

    if results[0]["status"] == "success":
        print("✅ PASS: Sequential fallback works correctly")
        return True
    else:
        print("❌ FAIL: Sequential fallback failed")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("INTEGRATION TEST SUITE: Translation Parallelization")
    print("=" * 70)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python Version: {sys.version.split()[0]}")
    print("=" * 70)

    # Run tests
    test1_pass = test_parallel_translation()
    print("\n")
    test2_pass = test_sequential_fallback()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Parallel Translation: {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Sequential Fallback:  {'✅ PASS' if test2_pass else '❌ FAIL'}")
    print("=" * 70)

    if test1_pass and test2_pass:
        print("\n🎉 ALL INTEGRATION TESTS PASSED")
        sys.exit(0)
    else:
        print("\n⚠️  SOME TESTS FAILED")
        sys.exit(1)
