#!/usr/bin/env python3
"""
Standalone Test for arXiv Agent
Tests the arXiv agent in isolation (Agent Swarm step 1)
"""

import sys
import json
import time
import yaml
from pathlib import Path
from datetime import datetime

# Add project root and env-scanning to path
project_root = Path(__file__).parent.parent
env_scanning_path = project_root / "env-scanning"
sys.path.insert(0, str(env_scanning_path))

from scanners.arxiv_scanner import ArXivScanner


def load_configuration():
    """Load arXiv source configuration and STEEPs domains"""
    print("📋 Loading configuration...")

    # Load sources.yaml
    sources_path = project_root / "env-scanning" / "config" / "sources.yaml"
    with open(sources_path) as f:
        sources = yaml.safe_load(f)
        arxiv_config = next(s for s in sources['sources'] if s['name'] == 'arXiv')

    # Load domains.yaml
    domains_path = project_root / "env-scanning" / "config" / "domains.yaml"
    with open(domains_path) as f:
        domains = yaml.safe_load(f)
        steeps_domains = domains['STEEPs']

    print(f"   ✓ arXiv config loaded (enabled: {arxiv_config.get('enabled', False)})")
    print(f"   ✓ STEEPs domains loaded ({len(steeps_domains)} categories)")

    return arxiv_config, steeps_domains


def run_arxiv_agent(arxiv_config, steeps_domains):
    """
    Run arXiv agent independently
    Simulates Agent Swarm parallel execution
    """
    print("\n🚀 Starting arXiv agent (standalone mode)...")
    print(f"   Model: sonnet (simulated)")
    print(f"   Context: Independent 200K tokens")

    start_time = time.time()

    # Initialize scanner (reuses existing implementation)
    scanner = ArXivScanner(arxiv_config)

    # Scan papers
    print("\n📡 Scanning arXiv API...")
    papers = scanner.scan(
        steeps_domains=steeps_domains,
        days_back=7
    )

    execution_time = time.time() - start_time

    print(f"\n✓ Scan complete in {execution_time:.1f}s")

    return papers, execution_time


def create_agent_output(papers, execution_time):
    """Create standardized agent output"""
    output = {
        "agent_metadata": {
            "agent_name": "arxiv-agent",
            "model_used": "sonnet",
            "execution_time": round(execution_time, 2),
            "papers_collected": len(papers),
            "steeps_categories_scanned": 6,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "success",
            "parallelization_mode": "standalone_test"
        },
        "items": papers
    }

    return output


def write_output(output):
    """Write agent output to file"""
    output_dir = project_root / "env-scanning" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"arxiv-scan-{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Output saved: {output_path}")
    print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")

    return output_path


def validate_output(output):
    """Validate agent output structure"""
    print("\n🔍 Validating output...")

    errors = []

    # Test 1: Required metadata
    if "agent_metadata" not in output:
        errors.append("Missing agent_metadata")
    elif output["agent_metadata"]["agent_name"] != "arxiv-agent":
        errors.append(f"Wrong agent name: {output['agent_metadata']['agent_name']}")

    # Test 2: Items structure
    if "items" not in output:
        errors.append("Missing items")
    else:
        for i, item in enumerate(output["items"]):
            if not item.get("id", "").startswith("arxiv-"):
                errors.append(f"Item {i}: Invalid ID format (should start with 'arxiv-')")

            if item.get("source", {}).get("name") != "arXiv":
                errors.append(f"Item {i}: Wrong source name")

            if item.get("preliminary_category") not in ['S', 'T', 'E', 'P', 's']:
                errors.append(f"Item {i}: Invalid STEEPs category")

    # Test 3: STEEPs coverage
    if "items" in output:
        categories = {item["preliminary_category"] for item in output["items"]}
        if len(categories) < 2:
            errors.append(f"Insufficient STEEPs coverage (only {len(categories)} categories)")

    # Report
    if errors:
        print("   ❌ Validation FAILED:")
        for error in errors:
            print(f"      - {error}")
        return False
    else:
        print("   ✓ All validation checks passed")
        return True


def print_summary(output):
    """Print summary statistics"""
    print("\n" + "="*60)
    print("📊 arXiv Agent Test Summary")
    print("="*60)

    metadata = output["agent_metadata"]
    items = output["items"]

    print(f"\nAgent Info:")
    print(f"  • Model: {metadata['model_used']}")
    print(f"  • Execution time: {metadata['execution_time']}s")
    print(f"  • Papers collected: {metadata['papers_collected']}")

    print(f"\nSTEEPs Coverage:")
    category_counts = {}
    for item in items:
        cat = item["preliminary_category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    category_names = {
        'S': 'Social',
        'T': 'Technological',
        'E': 'Economic/Environmental',
        'P': 'Political',
        's': 'spiritual'
    }

    for cat, count in sorted(category_counts.items()):
        print(f"  • {category_names.get(cat, cat)}: {count} papers")

    print(f"\nSample Papers:")
    for item in items[:3]:
        print(f"  • [{item['preliminary_category']}] {item['title'][:60]}...")

    print("\n" + "="*60)
    print("✓ arXiv Agent standalone test completed successfully!")
    print("="*60)


def main():
    """Main test execution"""
    print("="*60)
    print("🧪 arXiv Agent Standalone Test")
    print("   Agent Swarm Step 1: Single Agent Isolation")
    print("="*60)

    try:
        # Load configuration
        arxiv_config, steeps_domains = load_configuration()

        # Check if arXiv is enabled
        if not arxiv_config.get('enabled', False):
            print("\n⚠️  arXiv is disabled in sources.yaml")
            print("   Enable it to run this test")
            return 1

        # Run agent
        papers, execution_time = run_arxiv_agent(arxiv_config, steeps_domains)

        # Create output
        output = create_agent_output(papers, execution_time)

        # Write output
        output_path = write_output(output)

        # Validate
        if not validate_output(output):
            print("\n❌ Test FAILED: Validation errors detected")
            return 1

        # Summary
        print_summary(output)

        return 0

    except Exception as e:
        print(f"\n❌ Test FAILED with error:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
