#!/usr/bin/env python3
"""
Multi-Source Scanner Test
Tests newly implemented RSS and API scanners
"""

import json
import yaml
import time
from datetime import datetime
from pathlib import Path

# Add scanners to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from scanners.scanner_factory import ScannerFactory


def log(level, message):
    """Simple logging"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level:8s} | {message}")


def load_steeps_domains():
    """Load STEEPs domain definitions"""
    domains_path = Path(__file__).parent / "config" / "domains.yaml"

    with open(domains_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    steeps_domains = {}
    for category, data in config['STEEPs'].items():
        steeps_domains[category] = data.get('keywords', [])

    log("INFO", f"Loaded {len(steeps_domains)} STEEPs categories")
    return steeps_domains


def load_sources_config():
    """Load sources configuration"""
    sources_path = Path(__file__).parent / "config" / "sources.yaml"

    with open(sources_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config.get('sources', [])


def test_scanner(scanner_name, scanner_config, steeps_domains):
    """Test a single scanner"""
    log("TEST", f"Testing {scanner_name}...")

    try:
        # Create scanner
        start_time = time.time()
        scanner = ScannerFactory.create_scanner(scanner_config)

        # Validate configuration
        if not scanner.validate_config():
            log("ERROR", f"{scanner_name} configuration is invalid")
            return None

        log("SUCCESS", f"{scanner_name} scanner created successfully")

        # Scan (last 3 days for faster testing)
        log("INFO", f"Scanning {scanner_name} (last 3 days)...")
        scan_start = time.time()

        signals = scanner.scan(steeps_domains, days_back=3)

        scan_time = time.time() - scan_start

        # Report results
        log("SUCCESS", f"{scanner_name} scan completed in {scan_time:.2f}s")
        log("INFO", f"Found {len(signals)} signals")

        # Validate signal format
        if signals:
            sample_signal = signals[0]
            required_fields = ['id', 'title', 'source', 'content', 'preliminary_category', 'collected_at']

            missing_fields = [field for field in required_fields if field not in sample_signal]

            if missing_fields:
                log("WARNING", f"Sample signal missing fields: {missing_fields}")
            else:
                log("SUCCESS", "Signal format validated")

            # Display sample signal
            print(f"\n{'='*60}")
            print(f"SAMPLE SIGNAL FROM {scanner_name}:")
            print(f"{'='*60}")
            print(f"ID:       {sample_signal.get('id', 'N/A')}")
            print(f"Title:    {sample_signal.get('title', 'N/A')[:80]}...")
            print(f"Source:   {sample_signal.get('source', {}).get('name', 'N/A')}")
            print(f"Category: {sample_signal.get('preliminary_category', 'N/A')}")
            print(f"Date:     {sample_signal.get('source', {}).get('published_date', 'N/A')}")
            print(f"Keywords: {', '.join(sample_signal.get('content', {}).get('keywords', [])[:5])}")
            print(f"{'='*60}\n")

        return {
            'scanner': scanner_name,
            'status': 'SUCCESS',
            'signals_found': len(signals),
            'scan_time': scan_time,
            'sample_signal': signals[0] if signals else None
        }

    except Exception as e:
        log("ERROR", f"{scanner_name} test failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            'scanner': scanner_name,
            'status': 'FAILED',
            'error': str(e)
        }


def test_scanner_factory():
    """Test scanner factory registry"""
    log("TEST", "Testing Scanner Factory registry...")

    registered = ScannerFactory.get_registered_scanners()

    print(f"\n{'='*60}")
    print("REGISTERED SCANNERS:")
    print(f"{'='*60}")

    for source_type, scanner_names in registered.items():
        print(f"{source_type:12} : {', '.join(scanner_names)}")

    print(f"{'='*60}\n")

    log("SUCCESS", f"Found {sum(len(v) for v in registered.values())} registered scanners")

    return registered


def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("MULTI-SOURCE SCANNER TEST - Week 1 Free Sources")
    print("="*80 + "\n")

    # Load configuration
    log("INFO", "Loading configuration...")
    steeps_domains = load_steeps_domains()
    sources_config = load_sources_config()

    # Test factory
    registered_scanners = test_scanner_factory()

    # Test Week 1 scanners
    week1_scanners = [
        'SSRN',
        'EU Press Releases',
        'US Federal Register',
        'WHO Press Releases',
        'TechCrunch',
        'MIT Technology Review'
    ]

    test_results = []

    print("\n" + "="*80)
    print("TESTING WEEK 1 SCANNERS")
    print("="*80 + "\n")

    for source_config in sources_config:
        source_name = source_config.get('name')

        if source_name in week1_scanners and source_config.get('enabled', True):
            result = test_scanner(source_name, source_config, steeps_domains)
            if result:
                test_results.append(result)

            # Small delay between tests
            time.sleep(1)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80 + "\n")

    successful = [r for r in test_results if r['status'] == 'SUCCESS']
    failed = [r for r in test_results if r['status'] == 'FAILED']

    print(f"Total scanners tested: {len(test_results)}")
    print(f"Successful:            {len(successful)}")
    print(f"Failed:                {len(failed)}")

    if successful:
        print(f"\n{'Scanner':<30} {'Signals':<12} {'Time (s)':<12}")
        print("-" * 60)

        total_signals = 0
        total_time = 0

        for result in successful:
            signals = result.get('signals_found', 0)
            scan_time = result.get('scan_time', 0)

            print(f"{result['scanner']:<30} {signals:<12} {scan_time:<12.2f}")

            total_signals += signals
            total_time += scan_time

        print("-" * 60)
        print(f"{'TOTAL':<30} {total_signals:<12} {total_time:<12.2f}")

    if failed:
        print(f"\n⚠️  FAILED SCANNERS:")
        for result in failed:
            print(f"  - {result['scanner']}: {result.get('error', 'Unknown error')}")

    # Save test results
    output_dir = Path(__file__).parent / "logs"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"multi-source-test-{datetime.now().strftime('%Y-%m-%d')}.json"

    with open(output_path, 'w') as f:
        json.dump({
            'test_date': datetime.now().isoformat(),
            'scanners_tested': len(test_results),
            'successful': len(successful),
            'failed': len(failed),
            'results': test_results
        }, f, indent=2)

    log("INFO", f"Test results saved to {output_path}")

    # Final verdict
    print("\n" + "="*80)

    if failed:
        print("⚠️  TESTS COMPLETED WITH ERRORS")
        print(f"{len(failed)} scanner(s) failed - see logs for details")
        return 1
    else:
        print("✅ ALL TESTS PASSED")
        print(f"All {len(successful)} scanners are working correctly")
        return 0


if __name__ == "__main__":
    exit(main())
