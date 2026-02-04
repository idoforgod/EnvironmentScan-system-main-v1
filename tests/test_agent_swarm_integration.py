#!/usr/bin/env python3
"""
Agent Swarm Integration Test
Tests all agents together (sequential for now, parallel in production)
"""

import sys
import json
import time
import yaml
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
env_scanning_path = project_root / "env-scanning"
sys.path.insert(0, str(env_scanning_path))

from scanners.arxiv_scanner import ArXivScanner
from scanners.rss_scanner import RSSScanner
from scanners.federal_register_scanner import FederalRegisterScanner


def load_configuration():
    """Load configuration files"""
    print("📋 Loading configuration...")

    # Load sources
    sources_path = project_root / "env-scanning" / "config" / "sources.yaml"
    with open(sources_path) as f:
        sources_config = yaml.safe_load(f)

    # Load domains
    domains_path = project_root / "env-scanning" / "config" / "domains.yaml"
    with open(domains_path) as f:
        domains_config = yaml.safe_load(f)

    return sources_config, domains_config


def run_arxiv_agent(sources_config, domains_config):
    """Run arXiv agent"""
    print("\n" + "="*60)
    print("🚀 Running arXiv Agent")
    print("="*60)

    start_time = time.time()

    # Get arXiv config
    arxiv_config = next(s for s in sources_config['sources'] if s['name'] == 'arXiv')

    # Scan
    scanner = ArXivScanner(arxiv_config)
    papers = scanner.scan(domains_config['STEEPs'], days_back=7)

    execution_time = time.time() - start_time

    # Create output
    output = {
        "agent_metadata": {
            "agent_name": "arxiv-agent",
            "model_used": "sonnet",
            "execution_time": round(execution_time, 2),
            "papers_collected": len(papers),
            "steeps_categories_scanned": 6,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "success"
        },
        "items": papers
    }

    # Write output
    output_path = project_root / "env-scanning" / "raw" / f"arxiv-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ arXiv: {len(papers)} papers in {execution_time:.1f}s")

    return output


def run_blog_agent(sources_config, domains_config):
    """Run blog agent"""
    print("\n" + "="*60)
    print("🚀 Running Blog Agent")
    print("="*60)

    start_time = time.time()

    # Get blog sources
    blog_sources = [
        s for s in sources_config['sources']
        if s['type'] == 'blog' and s.get('enabled', True)
    ]

    # Scan each blog
    all_articles = []
    for source in blog_sources:
        try:
            scanner = RSSScanner(source)
            articles = scanner.scan(domains_config['STEEPs'], days_back=7)
            all_articles.extend(articles)
            print(f"  ✓ {source['name']}: {len(articles)} articles")
        except Exception as e:
            print(f"  ⚠ {source['name']} failed: {e}")
            continue

    execution_time = time.time() - start_time

    # Create output
    output = {
        "agent_metadata": {
            "agent_name": "blog-agent",
            "model_used": "haiku",
            "execution_time": round(execution_time, 2),
            "articles_collected": len(all_articles),
            "sources_scanned": len(blog_sources),
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "success"
        },
        "items": all_articles
    }

    # Write output
    output_path = project_root / "env-scanning" / "raw" / f"blog-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Blog: {len(all_articles)} articles in {execution_time:.1f}s")

    return output


def run_policy_agent(sources_config, domains_config):
    """Run policy agent"""
    print("\n" + "="*60)
    print("🚀 Running Policy Agent")
    print("="*60)

    start_time = time.time()

    # Get policy sources
    policy_sources = [
        s for s in sources_config['sources']
        if s['type'] == 'policy' and s.get('enabled', True)
    ]

    # Scan each policy source
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

            documents = scanner.scan(domains_config['STEEPs'], days_back=7)
            all_documents.extend(documents)
            print(f"  ✓ {source['name']}: {len(documents)} documents")
        except Exception as e:
            print(f"  ⚠ {source['name']} failed: {e}")
            continue

    execution_time = time.time() - start_time

    # Create output
    output = {
        "agent_metadata": {
            "agent_name": "policy-agent",
            "model_used": "haiku",
            "execution_time": round(execution_time, 2),
            "documents_collected": len(all_documents),
            "sources_scanned": len(policy_sources),
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "success"
        },
        "items": all_documents
    }

    # Write output
    output_path = project_root / "env-scanning" / "raw" / f"policy-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✓ Policy: {len(all_documents)} documents in {execution_time:.1f}s")

    return output


def run_patent_agent():
    """Run patent agent (placeholder)"""
    print("\n" + "="*60)
    print("🚀 Running Patent Agent (Placeholder)")
    print("="*60)

    # Placeholder implementation
    output = {
        "agent_metadata": {
            "agent_name": "patent-agent",
            "model_used": "haiku",
            "execution_time": 0.1,
            "patents_collected": 0,
            "sources_scanned": 0,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "not_implemented",
            "message": "Patent scanner not yet implemented"
        },
        "items": []
    }

    # Write output
    output_path = project_root / "env-scanning" / "raw" / f"patent-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("⚠ Patent: Not implemented, returning empty results")

    return output


def merge_results(arxiv_output, blog_output, policy_output, patent_output):
    """Merge all agent outputs into single daily scan file"""
    print("\n" + "="*60)
    print("🔗 Merging Agent Results")
    print("="*60)

    # Collect items from successful agents
    all_items = []
    agents_used = []

    for output in [arxiv_output, blog_output, policy_output, patent_output]:
        agent_name = output["agent_metadata"]["agent_name"]
        status = output["agent_metadata"].get("status")

        if status == "success":
            all_items.extend(output["items"])
            agents_used.append(agent_name.replace("-agent", ""))
            print(f"  ✓ {agent_name}: {len(output['items'])} items")
        elif status == "not_implemented":
            print(f"  ⚠ {agent_name}: Skipped (not implemented)")

    # Calculate total execution time
    # In parallel mode, this would be max(execution_times)
    # For now (sequential), it's the sum
    total_sequential_time = sum([
        arxiv_output["agent_metadata"]["execution_time"],
        blog_output["agent_metadata"]["execution_time"],
        policy_output["agent_metadata"]["execution_time"],
        patent_output["agent_metadata"]["execution_time"]
    ])

    max_parallel_time = max([
        arxiv_output["agent_metadata"]["execution_time"],
        blog_output["agent_metadata"]["execution_time"],
        policy_output["agent_metadata"]["execution_time"],
        patent_output["agent_metadata"]["execution_time"]
    ])

    # Create merged output
    merged = {
        "scan_metadata": {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "parallelization": "agent_swarm",
            "execution_mode": "sequential_test",  # Will be "parallel" in production
            "agents_used": agents_used,
            "total_items": len(all_items),
            "total_sources_scanned": sum([
                arxiv_output["agent_metadata"].get("sources_scanned", 1),
                blog_output["agent_metadata"]["sources_scanned"],
                policy_output["agent_metadata"]["sources_scanned"],
                patent_output["agent_metadata"]["sources_scanned"]
            ]),
            "timing": {
                "sequential_total": round(total_sequential_time, 2),
                "parallel_equivalent": round(max_parallel_time, 2),
                "speedup": f"{(total_sequential_time / max_parallel_time):.1f}x"
            }
        },
        "items": all_items
    }

    # Write merged output (compatible with existing workflow)
    output_path = project_root / "env-scanning" / "raw" / f"daily-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Merged: {len(all_items)} total items")
    print(f"  Sequential time: {total_sequential_time:.1f}s")
    print(f"  Parallel equivalent: {max_parallel_time:.1f}s")
    print(f"  Speedup: {(total_sequential_time / max_parallel_time):.1f}x")
    print(f"\n💾 Saved: {output_path}")

    return merged


def validate_merged_output(merged):
    """Validate merged output is compatible with existing workflow"""
    print("\n" + "="*60)
    print("🔍 Validating Merged Output")
    print("="*60)

    errors = []

    # Test 1: Required structure
    if "scan_metadata" not in merged:
        errors.append("Missing scan_metadata")
    if "items" not in merged:
        errors.append("Missing items")

    # Test 2: Items structure (compatible with deduplication-filter)
    for i, item in enumerate(merged["items"]):
        if "id" not in item:
            errors.append(f"Item {i}: Missing id")
        if "source" not in item:
            errors.append(f"Item {i}: Missing source")
        if "preliminary_category" not in item:
            errors.append(f"Item {i}: Missing preliminary_category")

    # Test 3: STEEPs coverage
    categories = {item["preliminary_category"] for item in merged["items"]}
    if len(categories) < 2:
        errors.append(f"Insufficient STEEPs coverage: {categories}")

    # Report
    if errors:
        print("❌ Validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✓ All validation checks passed")
        print("✓ Output compatible with existing deduplication-filter")
        return True


def print_summary(merged):
    """Print final summary"""
    print("\n" + "="*60)
    print("📊 Agent Swarm Integration Test Summary")
    print("="*60)

    metadata = merged["scan_metadata"]

    print(f"\nExecution:")
    print(f"  • Mode: {metadata['execution_mode']}")
    print(f"  • Agents: {', '.join(metadata['agents_used'])}")
    print(f"  • Sequential time: {metadata['timing']['sequential_total']}s")
    print(f"  • Parallel equivalent: {metadata['timing']['parallel_equivalent']}s")
    print(f"  • Speedup: {metadata['timing']['speedup']}")

    print(f"\nResults:")
    print(f"  • Total items: {metadata['total_items']}")
    print(f"  • Sources scanned: {metadata['total_sources_scanned']}")

    # STEEPs breakdown
    category_counts = {}
    for item in merged["items"]:
        cat = item["preliminary_category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    print(f"\nSTEEPs Coverage:")
    category_names = {
        'S': 'Social',
        'T': 'Technological',
        'E': 'Economic/Environmental',
        'P': 'Political',
        's': 'spiritual'
    }
    for cat, count in sorted(category_counts.items()):
        print(f"  • {category_names.get(cat, cat)}: {count} items")

    print("\n" + "="*60)
    print("✓ Agent Swarm Integration Test PASSED!")
    print("="*60)


def main():
    """Main test execution"""
    print("="*60)
    print("🧪 Agent Swarm Integration Test")
    print("   Testing: arXiv + Blog + Policy + Patent (placeholder)")
    print("="*60)

    overall_start = time.time()

    try:
        # Load configuration
        sources_config, domains_config = load_configuration()

        # Run each agent (sequential for now, parallel in production)
        arxiv_output = run_arxiv_agent(sources_config, domains_config)
        blog_output = run_blog_agent(sources_config, domains_config)
        policy_output = run_policy_agent(sources_config, domains_config)
        patent_output = run_patent_agent()

        # Merge results
        merged = merge_results(arxiv_output, blog_output, policy_output, patent_output)

        # Validate
        if not validate_merged_output(merged):
            print("\n❌ Test FAILED: Validation errors")
            return 1

        # Summary
        print_summary(merged)

        overall_time = time.time() - overall_start
        print(f"\nTotal test time: {overall_time:.1f}s")

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
