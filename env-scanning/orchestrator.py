#!/usr/bin/env python3
"""
Agent Swarm Orchestrator
Parallel execution manager using Python multiprocessing (NO API)

Principles:
1. Preserve existing workflow (input/output format)
2. No API usage (pure Python multiprocessing)
3. Task Graph based dependency management
"""

import os
import json
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Import new core modules for Phase 1 enhancements
from core.unified_task_manager import UnifiedTaskManager
from core.translation_parallelizer import TranslationParallelizer


class AgentOrchestrator:
    """
    병렬 에이전트 실행 관리자

    Uses Python multiprocessing for true parallel execution
    Each agent runs in independent process with isolated memory
    """

    def __init__(self, project_root: Path = None):
        if project_root is None:
            project_root = Path(__file__).parent

        self.project_root = project_root
        self.config_dir = project_root / "config"
        self.task_graph_path = project_root / "task_graph.json"
        self.output_dir = project_root / "raw"

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Phase 1 enhancements: Task Manager + Translation Parallelizer
        self.task_manager = UnifiedTaskManager(self.project_root)
        self.translator = TranslationParallelizer(self.project_root)

    def load_task_graph(self) -> Dict:
        """Load task graph (dependency definition)"""
        if self.task_graph_path.exists():
            with open(self.task_graph_path) as f:
                return json.load(f)
        else:
            # Create default Task Graph
            return self._create_default_task_graph()

    def _create_default_task_graph(self) -> Dict:
        """Create default task graph"""
        task_graph = {
            "tasks": [
                {
                    "id": "arxiv-scan",
                    "agent": "arxiv",
                    "status": "pending",
                    "blockedBy": [],
                    "blocks": ["merge-results"],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "blog-scan",
                    "agent": "blog",
                    "status": "pending",
                    "blockedBy": [],
                    "blocks": ["merge-results"],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "policy-scan",
                    "agent": "policy",
                    "status": "pending",
                    "blockedBy": [],
                    "blocks": ["merge-results"],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "patent-scan",
                    "agent": "patent",
                    "status": "pending",
                    "blockedBy": [],
                    "blocks": ["merge-results"],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "merge-results",
                    "agent": "merger",
                    "status": "pending",
                    "blockedBy": ["arxiv-scan", "blog-scan", "policy-scan", "patent-scan"],
                    "blocks": [],
                    "created_at": datetime.now().isoformat()
                }
            ],
            "metadata": {
                "workflow": "environmental-scanning",
                "phase": "1",
                "step": "2",
                "description": "Multi-source scanning with Agent Swarm"
            }
        }

        # Save to file
        with open(self.task_graph_path, 'w') as f:
            json.dump(task_graph, f, indent=2)

        return task_graph

    def get_ready_tasks(self, task_graph: Dict) -> List[Dict]:
        """Get tasks that are ready to execute (all blockedBy completed)"""
        ready = []

        for task in task_graph["tasks"]:
            if task["status"] == "pending":
                # Check blockedBy
                blocked = False
                for blocker_id in task.get("blockedBy", []):
                    blocker = next((t for t in task_graph["tasks"] if t["id"] == blocker_id), None)
                    if blocker and blocker["status"] != "completed":
                        blocked = True
                        break

                if not blocked:
                    ready.append(task)

        return ready

    def update_task_status(self, task_id: str, status: str):
        """Update task status (persist to JSON file)"""
        task_graph = self.load_task_graph()

        for task in task_graph["tasks"]:
            if task["id"] == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now().isoformat()
                break

        # Save to file (session persistence)
        with open(self.task_graph_path, 'w') as f:
            json.dump(task_graph, f, indent=2)

    def run_parallel(self) -> Dict:
        """
        Main parallel execution logic

        Returns:
            Final merged result
        """
        print("="*60)
        print("🚀 Agent Swarm Orchestrator Started")
        print("   Mode: TRUE Parallel Execution (multiprocessing)")
        print("   API: NONE (pure Python)")
        print("="*60)

        # Initialize workflow tasks for Ctrl+T visibility
        date_str = datetime.now().strftime("%Y-%m-%d")
        self.task_manager.initialize_workflow_tasks(date_str)

        # Load Task Graph
        task_graph = self.load_task_graph()

        # Mark Step 1.2 in progress
        self.task_manager.mark_step_in_progress("1.2")

        # Phase 1: Get ready agents (all with no blockedBy)
        ready_tasks = self.get_ready_tasks(task_graph)
        agent_tasks = [t for t in ready_tasks if t["agent"] != "merger"]

        print(f"\n📋 Ready agents: {len(agent_tasks)}")
        for task in agent_tasks:
            print(f"   • {task['agent']}")

        # Parallel execution (multiprocessing.Pool)
        print(f"\n⚡ Executing agents in TRUE parallel...")
        print(f"   Processes: {len(agent_tasks)}")
        print(f"   CPU cores available: {cpu_count()}")
        print(f"   Process isolation: ENABLED (independent memory)")

        start_time = time.time()

        # Import agent runner function
        from agent_runner import run_agent

        # Run agents in parallel (each in separate process)
        with Pool(processes=min(len(agent_tasks), cpu_count())) as pool:
            agent_names = [task["agent"] for task in agent_tasks]
            results = pool.map(run_agent, agent_names)

        parallel_time = time.time() - start_time

        print(f"\n✓ Parallel execution completed in {parallel_time:.1f}s")
        print(f"   Speedup vs sequential: ~{len(agent_tasks)}x potential")

        # Update task statuses
        for task in agent_tasks:
            self.update_task_status(task["id"], "completed")

        # Mark Step 1.2 completed
        self.task_manager.mark_step_completed("1.2")

        # Phase 2: Result Merger (after all agents complete)
        print(f"\n🔗 Merging results...")
        merged = self.merge_results()

        self.update_task_status("merge-results", "completed")

        # NEW: Step 1.2b - Parallel Translation
        self.task_manager.mark_step_in_progress("1.2b")
        print(f"\n📄 Step 1.2b: Translating scan results (parallel)...")

        translation_tasks = [
            (f"raw/daily-scan-{date_str}.json",
             f"raw/daily-scan-{date_str}-ko.json",
             "json"),
        ]

        translation_start = time.time()
        translation_results = self.translator.translate_files_parallel(translation_tasks)
        translation_time = time.time() - translation_start

        # Log results
        for result in translation_results:
            if result["status"] == "success":
                print(f"   ✓ {result['source_file']} → KR ({result['execution_time']:.1f}s)")
            else:
                print(f"   ⚠ Translation failed: {result['source_file']} - {result.get('error', 'Unknown error')}")

        print(f"   Parallel translation completed in {translation_time:.1f}s")
        self.task_manager.mark_step_completed("1.2b")

        print(f"\n✅ Agent Swarm execution completed")
        print(f"   Total time: {parallel_time:.1f}s")
        print(f"   Total items: {merged['scan_metadata']['total_items']}")

        return merged

    def merge_results(self) -> Dict:
        """
        Merge agent outputs
        Preserve existing workflow format
        """
        date_str = datetime.now().strftime("%Y-%m-%d")

        # Load each agent output
        agent_outputs = []
        for agent in ["arxiv", "blog", "policy", "patent"]:
            output_path = self.output_dir / f"{agent}-scan-{date_str}.json"
            if output_path.exists():
                with open(output_path) as f:
                    data = json.load(f)
                    if data["agent_metadata"].get("status") == "success":
                        agent_outputs.append(data)
                        print(f"   ✓ {agent}: {len(data['items'])} items")
                    else:
                        print(f"   ⚠ {agent}: {data['agent_metadata'].get('status')}")

        # Merge
        all_items = []
        total_sources = 0
        agents_used = []

        for output in agent_outputs:
            all_items.extend(output["items"])
            total_sources += output["agent_metadata"].get("sources_scanned", 1)
            agents_used.append(output["agent_metadata"]["agent_name"].replace("-agent", ""))

        # Preserve existing workflow format
        merged = {
            "scan_metadata": {
                "date": date_str,
                "parallelization": "agent_swarm_multiprocessing",
                "execution_mode": "parallel",
                "agents_used": agents_used,
                "total_items": len(all_items),
                "total_sources_scanned": total_sources
            },
            "items": all_items
        }

        # Save in existing format (daily-scan-{date}.json)
        output_path = self.output_dir / f"daily-scan-{date_str}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        print(f"   💾 {output_path}")

        return merged


def main():
    """CLI entry point"""
    import sys

    orchestrator = AgentOrchestrator()

    try:
        result = orchestrator.run_parallel()
        print("\n" + "="*60)
        print("✓ SUCCESS: Agent Swarm completed")
        print("="*60)
        sys.exit(0)

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
