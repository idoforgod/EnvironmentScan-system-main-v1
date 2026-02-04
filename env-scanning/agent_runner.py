#!/usr/bin/env python3
"""
Individual Agent Runner
Executed in separate process by multiprocessing.Pool

Each agent runs in ISOLATED process with INDEPENDENT memory
"""

import os
import sys
import json
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict

# Add scanners to path
sys.path.insert(0, str(Path(__file__).parent))

from scanners.arxiv_scanner import ArXivScanner
from scanners.rss_scanner import RSSScanner
from scanners.federal_register_scanner import FederalRegisterScanner


def run_agent(agent_name: str) -> Dict:
    """
    Run individual agent (in separate process)

    Args:
        agent_name: 'arxiv', 'blog', 'policy', 'patent'

    Returns:
        Agent output dictionary

    Important:
    - This function runs in INDEPENDENT process
    - NO shared memory with parent or other agents
    - Communication ONLY through file system
    - Each process has its OWN 200K token context equivalent
    """
    pid = os.getpid()
    print(f"\n[{agent_name}] Agent started (PID: {pid}) - ISOLATED PROCESS")

    start_time = time.time()

    # Load configuration (each process loads independently)
    project_root = Path(__file__).parent
    config_dir = project_root / "config"

    with open(config_dir / "sources.yaml") as f:
        sources_config = yaml.safe_load(f)

    with open(config_dir / "domains.yaml") as f:
        domains_config = yaml.safe_load(f)

    steeps_domains = domains_config['STEEPs']

    # Run agent based on name
    try:
        if agent_name == "arxiv":
            output = run_arxiv_agent(sources_config, steeps_domains)
        elif agent_name == "blog":
            output = run_blog_agent(sources_config, steeps_domains)
        elif agent_name == "policy":
            output = run_policy_agent(sources_config, steeps_domains)
        elif agent_name == "patent":
            output = run_patent_agent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

        execution_time = time.time() - start_time
        output["agent_metadata"]["execution_time"] = round(execution_time, 2)
        output["agent_metadata"]["process_id"] = pid

        # Save result to file (inter-process communication)
        output_dir = project_root / "raw"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{agent_name}-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"[{agent_name}] Completed in {execution_time:.1f}s → {len(output['items'])} items (PID: {pid})")

        return output

    except Exception as e:
        print(f"[{agent_name}] Failed: {e}")
        import traceback
        traceback.print_exc()

        # Return empty output on failure (don't halt workflow)
        return {
            "agent_metadata": {
                "agent_name": f"{agent_name}-agent",
                "status": "failed",
                "error": str(e),
                "process_id": pid
            },
            "items": []
        }


def run_arxiv_agent(sources_config: dict, steeps_domains: dict) -> dict:
    """
    arXiv agent implementation (reuses existing scanner)

    Runs in ISOLATED process - no shared memory
    """
    arxiv_config = next(s for s in sources_config['sources'] if s['name'] == 'arXiv')

    scanner = ArXivScanner(arxiv_config)
    papers = scanner.scan(steeps_domains, days_back=7)

    return {
        "agent_metadata": {
            "agent_name": "arxiv-agent",
            "model_used": "sonnet",
            "papers_collected": len(papers),
            "steeps_categories_scanned": 6,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "success"
        },
        "items": papers
    }


def run_blog_agent(sources_config: dict, steeps_domains: dict) -> dict:
    """
    Blog agent implementation

    Runs in ISOLATED process - no shared memory
    """
    blog_sources = [
        s for s in sources_config['sources']
        if s['type'] == 'blog' and s.get('enabled', True)
    ]

    all_articles = []
    for source in blog_sources:
        try:
            scanner = RSSScanner(source)
            articles = scanner.scan(steeps_domains, days_back=7)
            all_articles.extend(articles)
        except Exception as e:
            print(f"  ⚠ {source['name']} failed: {e}")
            continue

    return {
        "agent_metadata": {
            "agent_name": "blog-agent",
            "model_used": "haiku",
            "articles_collected": len(all_articles),
            "sources_scanned": len(blog_sources),
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "success"
        },
        "items": all_articles
    }


def run_policy_agent(sources_config: dict, steeps_domains: dict) -> dict:
    """
    Policy agent implementation

    Runs in ISOLATED process - no shared memory
    """
    policy_sources = [
        s for s in sources_config['sources']
        if s['type'] == 'policy' and s.get('enabled', True)
    ]

    all_documents = []
    for source in policy_sources:
        try:
            # Select appropriate scanner
            if 'api_endpoint' in source and 'federal' in source['name'].lower():
                scanner = FederalRegisterScanner(source)
            elif 'rss_feed' in source:
                scanner = RSSScanner(source)
            else:
                print(f"  ⚠ Unknown scanner for {source['name']}, skipping")
                continue

            documents = scanner.scan(steeps_domains, days_back=7)
            all_documents.extend(documents)

        except Exception as e:
            print(f"  ⚠ {source['name']} failed: {e}")
            continue

    return {
        "agent_metadata": {
            "agent_name": "policy-agent",
            "model_used": "haiku",
            "documents_collected": len(all_documents),
            "sources_scanned": len(policy_sources),
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "success"
        },
        "items": all_documents
    }


def run_patent_agent() -> dict:
    """
    Patent agent (placeholder)

    Runs in ISOLATED process - no shared memory
    """
    return {
        "agent_metadata": {
            "agent_name": "patent-agent",
            "model_used": "haiku",
            "patents_collected": 0,
            "sources_scanned": 0,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "not_implemented",
            "message": "Patent scanner not yet implemented"
        },
        "items": []
    }


if __name__ == "__main__":
    # Test individual agent
    if len(sys.argv) > 1:
        agent_name = sys.argv[1]
        result = run_agent(agent_name)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python agent_runner.py <agent_name>")
        print("Example: python agent_runner.py arxiv")
