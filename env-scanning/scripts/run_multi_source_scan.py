#!/usr/bin/env python3
"""
Multi-Source Scanner Executor
Orchestrates scanning across multiple configured sources
"""

import sys
import os
import json
import yaml
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for scanner imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanners.scanner_factory import ScannerFactory


def load_configuration():
    """
    Load configuration files

    Returns:
        Tuple of (sources_config, domains_config)
    """
    # Load sources.yaml
    sources_path = 'config/sources.yaml'
    if not os.path.exists(sources_path):
        raise FileNotFoundError(f"Configuration file not found: {sources_path}")

    with open(sources_path, 'r', encoding='utf-8') as f:
        sources_config = yaml.safe_load(f)

    # Load domains.yaml
    domains_path = 'config/domains.yaml'
    if not os.path.exists(domains_path):
        raise FileNotFoundError(f"Configuration file not found: {domains_path}")

    with open(domains_path, 'r', encoding='utf-8') as f:
        domains_config = yaml.safe_load(f)

    return sources_config, domains_config


def run_scan(days_back: int = 7) -> Dict[str, Any]:
    """
    Execute multi-source scan

    Args:
        days_back: Number of days to look back

    Returns:
        Dictionary with scan_metadata and items

    Raises:
        Exception: If critical source fails
    """
    print("=" * 60)
    print("Multi-Source Scanner - Starting")
    print("=" * 60)

    start_time = datetime.now()

    # 1. Load configurations
    print("\n[INFO] Loading configurations...")
    sources_config, domains_config = load_configuration()

    # 1.5. Source Health Check (System 1)
    disabled_sources = []
    try:
        from core.source_health_checker import SourceHealthChecker

        print("\n[INFO] Step 1.1.5: Source Health Check...")
        health_checker = SourceHealthChecker(
            sources_config=sources_config['sources'],
            health_dir='health/',
        )
        health_report = health_checker.check_all_sources()
        health_checker.save_report(health_report)
        health_checker.append_history(health_report)

        disabled_sources = health_checker.get_disabled_sources(health_report)
        if disabled_sources:
            print(f"[HEALTH] {len(disabled_sources)} source(s) disabled: {disabled_sources}")

    except ImportError:
        print("[WARNING] SourceHealthChecker not available, skipping health check")
    except Exception as e:
        print(f"[WARNING] Health check failed (non-blocking): {e}")

    # 2. Create scanner instances
    print("[INFO] Creating scanner instances...")
    scanners = ScannerFactory.create_all_scanners(
        sources_config['sources'],
        skip_sources=disabled_sources,
    )

    if len(scanners) == 0:
        raise ValueError("No enabled scanners found in configuration")

    print(f"\n[INFO] Loaded {len(scanners)} active scanner(s):")
    for scanner in scanners:
        critical_flag = "CRITICAL" if scanner.is_critical() else "non-critical"
        print(f"  - {scanner.get_name()} ({scanner.get_source_type()}, {critical_flag})")

    # 3. Execute each scanner
    all_items = []
    sources_scanned = 0
    sources_failed = 0

    for scanner in scanners:
        try:
            print(f"\n{'='*60}")
            print(f"[SCANNING] {scanner.get_name()}...")
            print(f"{'='*60}")

            # Execute scan
            items = scanner.scan(
                steeps_domains=domains_config['STEEPs'],
                days_back=days_back
            )

            all_items.extend(items)
            sources_scanned += 1

            print(f"[PROGRESS] Total items collected: {len(all_items)}")

        except Exception as e:
            sources_failed += 1
            error_msg = f"{scanner.get_name()} failed: {e}"

            # Critical source failure → halt workflow
            if scanner.is_critical():
                print(f"\n[CRITICAL ERROR] {error_msg}")
                print("[HALT] Critical source failed - stopping workflow")
                raise

            # Non-critical source failure → log and continue
            else:
                print(f"\n[ERROR] {error_msg}")
                print(f"[WARNING] Skipping {scanner.get_name()} (non-critical source)")
                continue

    # 4. Build result
    execution_time = (datetime.now() - start_time).total_seconds()

    result = {
        "scan_metadata": {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "sources_configured": len(scanners),
            "sources_scanned": sources_scanned,
            "sources_failed": sources_failed,
            "total_items": len(all_items),
            "execution_time": round(execution_time, 2),
            "mode": "multi_source",
            "days_back": days_back,
            "timestamp": datetime.now().isoformat()
        },
        "items": all_items
    }

    # 5. Summary
    print("\n" + "=" * 60)
    print("Multi-Source Scanner - Complete")
    print("=" * 60)
    print(f"Sources scanned: {sources_scanned}/{len(scanners)}")
    print(f"Sources failed: {sources_failed}")
    print(f"Total items: {len(all_items)}")
    print(f"Execution time: {execution_time:.2f}s")
    print("=" * 60)

    return result


def save_results(result: Dict[str, Any], output_path: str):
    """
    Save scan results to JSON file

    Args:
        result: Scan result dictionary
        output_path: Output file path
    """
    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(output_path)
    print(f"\n[SAVED] Output written to: {output_path}")
    print(f"[SIZE] {file_size:,} bytes ({file_size/1024:.1f} KB)")


def print_summary(result: Dict[str, Any]):
    """
    Print scan summary

    Args:
        result: Scan result dictionary
    """
    metadata = result['scan_metadata']
    items = result['items']

    print("\n" + "=" * 60)
    print("SCAN SUMMARY")
    print("=" * 60)
    print(f"Date: {metadata['date']}")
    print(f"Total signals: {metadata['total_items']}")
    print(f"Execution time: {metadata['execution_time']}s")
    print(f"Sources: {metadata['sources_scanned']}/{metadata['sources_configured']} successful")

    # Category distribution
    if items:
        category_counts = {}
        for item in items:
            cat = item.get('preliminary_category', 'Unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1

        print("\nCategory distribution:")
        for cat, count in sorted(category_counts.items()):
            pct = (count / len(items) * 100) if items else 0
            print(f"  {cat}: {count} signals ({pct:.1f}%)")

    print("=" * 60)


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Multi-Source Environmental Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan last 7 days (default)
  python run_multi_source_scan.py

  # Scan last 14 days
  python run_multi_source_scan.py --days-back 14

  # Custom output path
  python run_multi_source_scan.py --output custom/path.json

  # Quiet mode (less output)
  python run_multi_source_scan.py --quiet
        """
    )

    parser.add_argument(
        '--days-back',
        type=int,
        default=7,
        help='Number of days to look back (default: 7)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: raw/daily-scan-{date}.json)'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Reduce output verbosity'
    )

    args = parser.parse_args()

    # Suppress some output in quiet mode
    if args.quiet:
        # TODO: Implement quiet mode logging
        pass

    try:
        # Run scan
        result = run_scan(days_back=args.days_back)

        # Determine output path
        if args.output:
            output_path = args.output
        else:
            today = datetime.now().strftime('%Y-%m-%d')
            output_path = f"raw/daily-scan-{today}.json"

        # Save results
        save_results(result, output_path)

        # Print summary
        print_summary(result)

        return 0

    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Scan cancelled by user")
        return 130

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("[HELP] Make sure you're running from env-scanning/ directory")
        return 1

    except ValueError as e:
        print(f"\n[ERROR] {e}")
        return 1

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
