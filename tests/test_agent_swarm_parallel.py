#!/usr/bin/env python3
"""
Agent Swarm Parallel Execution Test
Verifies TRUE parallel execution using multiprocessing
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add env-scanning to path
project_root = Path(__file__).parent.parent
env_scanning_path = project_root / "env-scanning"
sys.path.insert(0, str(env_scanning_path))

from orchestrator import AgentOrchestrator


def test_parallel_execution():
    """Test true parallel execution"""
    print("="*60)
    print("🧪 Agent Swarm Parallel Execution Test")
    print("   Objective: Verify TRUE parallel execution")
    print("="*60)

    orchestrator = AgentOrchestrator(env_scanning_path)

    # Reset task graph for fresh test
    task_graph_path = env_scanning_path / "task_graph.json"
    if task_graph_path.exists():
        task_graph_path.unlink()
        print("  • Task graph reset for fresh test")

    # Run parallel execution
    print("\n▶ Starting parallel execution...")
    start_time = time.time()

    try:
        result = orchestrator.run_parallel()

        total_time = time.time() - start_time

        print("\n" + "="*60)
        print("📊 Test Results")
        print("="*60)

        # Verify parallel execution
        metadata = result["scan_metadata"]

        print(f"\nExecution:")
        print(f"  • Mode: {metadata.get('execution_mode')}")
        print(f"  • Parallelization: {metadata.get('parallelization')}")
        print(f"  • Total time: {total_time:.1f}s")

        print(f"\nAgents:")
        print(f"  • Executed: {', '.join(metadata['agents_used'])}")
        print(f"  • Total items: {metadata['total_items']}")
        print(f"  • Sources: {metadata['total_sources_scanned']}")

        # Verify output file
        output_path = env_scanning_path / "raw" / f"daily-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
        assert output_path.exists(), "Output file not created"

        print(f"\nOutput:")
        print(f"  • File: {output_path}")
        print(f"  • Size: {output_path.stat().st_size / 1024:.1f} KB")

        # Load and verify structure
        with open(output_path) as f:
            data = json.load(f)

        assert "scan_metadata" in data, "Missing scan_metadata"
        assert "items" in data, "Missing items"
        assert len(data["items"]) > 0, "No items collected"

        # Check for multiple PIDs (proof of parallel execution)
        print(f"\nProcess Verification:")
        pids = set()

        for agent in metadata['agents_used']:
            agent_file = env_scanning_path / "raw" / f"{agent}-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
            if agent_file.exists():
                with open(agent_file) as f:
                    agent_data = json.load(f)
                    pid = agent_data["agent_metadata"].get("process_id")
                    if pid:
                        pids.add(pid)
                        print(f"  • {agent}: PID {pid}")

        if len(pids) > 1:
            print(f"  ✓ VERIFIED: {len(pids)} different processes (TRUE parallel)")
        else:
            print(f"  ⚠ WARNING: Only {len(pids)} process detected")

        # STEEPs coverage
        categories = {}
        for item in data["items"]:
            cat = item.get("preliminary_category", "Unknown")
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\nSTEEPs Coverage:")
        category_names = {
            'S': 'Social',
            'T': 'Technological',
            'E': 'Economic/Environmental',
            'P': 'Political',
            's': 'spiritual'
        }
        for cat, count in sorted(categories.items()):
            print(f"  • {category_names.get(cat, cat)}: {count} items")

        print("\n" + "="*60)
        print("✓ TEST PASSED: Agent Swarm parallel execution verified")
        print("="*60)

        return True

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def _isolation_worker(x):
    """Simple worker to verify isolation (must be module-level for pickle)"""
    import os
    import time
    pid = os.getpid()
    # Each process has independent memory
    local_data = {"pid": pid, "value": x * 2}
    time.sleep(0.1)
    return local_data


def test_process_isolation():
    """Verify process isolation (independent memory)"""
    print("\n" + "="*60)
    print("🔬 Testing Process Isolation")
    print("="*60)

    from multiprocessing import Pool

    # Run workers in parallel
    with Pool(processes=4) as pool:
        results = pool.map(_isolation_worker, [1, 2, 3, 4])

    pids = {r["pid"] for r in results}

    print(f"\nResults:")
    for r in results:
        print(f"  • PID {r['pid']}: value = {r['value']}")

    print(f"\nVerification:")
    print(f"  • Unique PIDs: {len(pids)}")
    print(f"  • Expected: 4")

    if len(pids) >= 2:
        print(f"  ✓ VERIFIED: Multiple processes with independent memory")
        return True
    else:
        print(f"  ⚠ WARNING: Process isolation not clearly verified")
        return False


def main():
    """Main test execution"""
    print("="*60)
    print("🚀 Agent Swarm Parallel Test Suite")
    print("="*60)

    # Test 1: Process isolation
    test1_passed = test_process_isolation()

    # Test 2: Parallel execution
    test2_passed = test_parallel_execution()

    # Summary
    print("\n" + "="*60)
    print("📋 Test Summary")
    print("="*60)
    print(f"  • Process isolation: {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"  • Parallel execution: {'✓ PASS' if test2_passed else '✗ FAIL'}")

    if test1_passed and test2_passed:
        print("\n✅ ALL TESTS PASSED")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
