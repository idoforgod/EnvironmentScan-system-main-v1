#!/usr/bin/env python3
"""
Generate large-scale test data for memory profiling and performance benchmarking.
Creates 10,000+ signals with realistic date distribution (90-day archive).
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.entity_extractor import EntityExtractor


def generate_test_signals(count: int = 10000, days_range: int = 90) -> list:
    """
    Generate test signals with realistic data.

    Args:
        count: Number of signals to generate
        days_range: Date range in days (signals distributed across this period)

    Returns:
        List of signal dictionaries
    """
    print(f"=== Generating {count:,} test signals ===\n")

    signals = []
    now = datetime.now()

    # Sample titles and abstracts for variety
    title_templates = [
        "Advances in {tech} for {domain} Applications",
        "{tech} Based Approach to {domain} Challenges",
        "Novel {tech} Framework for {domain} Systems",
        "{domain} Optimization Using {tech} Methods",
        "Breakthrough in {tech}: Implications for {domain}",
    ]

    technologies = [
        "Machine Learning", "Quantum Computing", "Blockchain", "AI",
        "Deep Learning", "Neural Networks", "CRISPR", "Nanotechnology",
        "Renewable Energy", "Autonomous Systems", "5G", "IoT",
    ]

    domains = [
        "Healthcare", "Climate Science", "Finance", "Transportation",
        "Agriculture", "Manufacturing", "Education", "Energy",
        "Security", "Communications",
    ]

    categories = ["T", "E", "S", "P", "s"]
    sources = ["arXiv", "Nature", "Science", "IEEE", "PubMed"]

    for i in range(count):
        # Generate random date within range
        days_ago = random.randint(0, days_range)
        signal_date = now - timedelta(days=days_ago)

        # Generate title
        tech = random.choice(technologies)
        domain = random.choice(domains)
        template = random.choice(title_templates)
        title = template.format(tech=tech, domain=domain)

        # Generate abstract
        abstract = f"This paper presents a comprehensive study on the application of {tech} in {domain}. " \
                   f"We demonstrate significant improvements over existing methods and discuss future directions."

        # Extract entities
        combined_text = f"{title} {abstract}"
        entities = EntityExtractor.extract(combined_text, max_entities=15)

        # Create signal
        signal = {
            "id": f"test-signal-{i+1:06d}",
            "title": title,
            "source": {
                "name": random.choice(sources),
                "type": "academic",
                "url": f"https://example.com/paper/{i+1}",
                "published_date": signal_date.strftime("%Y-%m-%d")
            },
            "content": {
                "abstract": abstract,
                "keywords": [tech.lower(), domain.lower(), "research"],
                "language": "en"
            },
            "metadata": {
                "test_data": True,
                "generated_at": now.isoformat()
            },
            "preliminary_category": random.choice(categories),
            "entities": entities,
            "collected_at": signal_date.isoformat(),
            "scan_date": signal_date.strftime("%Y-%m-%d")
        }

        signals.append(signal)

        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"  Generated {i+1:,} / {count:,} signals ({(i+1)/count*100:.0f}%)")

    print(f"\n✅ Generated {len(signals):,} signals")
    return signals


def save_test_database(signals: list, output_path: Path):
    """Save test signals to database file."""
    # Calculate statistics
    categories = {}
    sources = {}
    for signal in signals:
        cat = signal.get('preliminary_category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1

        source = signal.get('source', {}).get('name', 'Unknown')
        sources[source] = sources.get(source, 0) + 1

    # Get date range
    dates = [datetime.fromisoformat(s['collected_at']) for s in signals]
    min_date = min(dates).date()
    max_date = max(dates).date()

    database = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "total_signals": len(signals),
        "first_scan_date": str(min_date),
        "latest_scan_date": str(max_date),
        "statistics": {
            "total_scans": 1,
            "total_duplicates_prevented": 0,
            "sources": sources,
            "categories": categories,
            "test_data": True
        },
        "signals": signals
    }

    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(database, f, indent=2, ensure_ascii=False)

    file_size = output_path.stat().st_size
    print(f"  Saved to: {output_path}")
    print(f"  File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")


def main():
    """Main entry point."""
    # Configuration
    COUNT = 10000  # Number of signals
    DAYS_RANGE = 90  # Distribute across 90 days

    # Output path
    output_dir = Path("signals")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "database-test-10k.json"

    # Generate signals
    signals = generate_test_signals(count=COUNT, days_range=DAYS_RANGE)

    # Save database
    print(f"\n=== Saving test database ===")
    save_test_database(signals, output_path)

    # Show date distribution
    print(f"\n=== Date Distribution ===")
    now = datetime.now()
    buckets = {"0-7 days": 0, "8-30 days": 0, "31-60 days": 0, "61-90 days": 0}

    for signal in signals:
        collected_at = datetime.fromisoformat(signal['collected_at'])
        days_ago = (now - collected_at).days

        if days_ago <= 7:
            buckets["0-7 days"] += 1
        elif days_ago <= 30:
            buckets["8-30 days"] += 1
        elif days_ago <= 60:
            buckets["31-60 days"] += 1
        else:
            buckets["61-90 days"] += 1

    for bucket, count in buckets.items():
        pct = count / len(signals) * 100
        print(f"  {bucket:15s}: {count:5,} signals ({pct:5.1f}%)")

    print(f"\n✅ Test data generation complete!")
    print(f"   Use: python3 scripts/memory_profiler.py to benchmark")


if __name__ == '__main__':
    main()
