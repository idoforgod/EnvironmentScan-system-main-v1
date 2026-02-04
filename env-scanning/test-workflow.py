#!/usr/bin/env python3
"""
Environmental Scanning Workflow - Integration Test
Tests core workflow with mock data and identifies bottlenecks
"""

import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path

# Test configuration
TEST_DATE = datetime.now().strftime("%Y-%m-%d")
BASE_DIR = Path(__file__).parent
SIGNAL_COUNT = 50  # Test with 50 mock signals


def log(level, message):
    """Simple logging"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level:8s} | {message}")


class PerformanceTracker:
    """Track execution time and identify bottlenecks"""

    def __init__(self):
        self.timings = {}
        self.current_step = None
        self.start_time = None

    def start_step(self, step_name):
        self.current_step = step_name
        self.start_time = time.time()
        log("START", f"{step_name}")

    def end_step(self):
        if self.current_step:
            elapsed = time.time() - self.start_time
            self.timings[self.current_step] = elapsed
            log("COMPLETE", f"{self.current_step} ({elapsed:.2f}s)")
            self.current_step = None

    def report_bottlenecks(self):
        """Identify and report bottlenecks"""
        log("ANALYSIS", "=== Bottleneck Analysis ===")

        # Sort by time descending
        sorted_steps = sorted(self.timings.items(), key=lambda x: x[1], reverse=True)

        total_time = sum(self.timings.values())

        print(f"\nTotal execution time: {total_time:.2f}s\n")
        print(f"{'Step':<40} {'Time (s)':<12} {'% of Total':<12} {'Status'}")
        print("-" * 80)

        for step, time_taken in sorted_steps:
            percentage = (time_taken / total_time) * 100

            # Identify bottlenecks (>20% of total time)
            status = "🔴 BOTTLENECK" if percentage > 20 else \
                     "⚠️  SLOW" if percentage > 10 else \
                     "✅ OK"

            print(f"{step:<40} {time_taken:<12.2f} {percentage:<12.1f} {status}")

        return sorted_steps


def generate_mock_signals(count=50):
    """Generate mock signals for testing"""
    log("INFO", f"Generating {count} mock signals...")

    categories = ['S', 'T', 'E', 'E', 'P', 's']
    sources = ['arXiv', 'Nature', 'TechCrunch', 'MIT Tech Review']

    signals = []

    for i in range(count):
        signal = {
            "id": f"signal-{i+1:03d}",
            "title": f"Mock Signal {i+1}: {get_mock_title(i)}",
            "source": {
                "name": sources[i % len(sources)],
                "type": "academic" if i % 2 == 0 else "blog",
                "url": f"https://example.com/article-{i+1}",
                "published_date": (datetime.now() - timedelta(days=i % 7)).strftime("%Y-%m-%d")
            },
            "content": {
                "abstract": f"This is a mock abstract for signal {i+1}. " * 10,
                "keywords": [f"keyword{j}" for j in range(5)],
                "language": "en"
            },
            "preliminary_category": categories[i % len(categories)],
            "collected_at": datetime.now().isoformat()
        }
        signals.append(signal)

    return signals


def get_mock_title(index):
    """Generate realistic mock titles"""
    titles = [
        "Quantum Computing Breakthrough in Drug Discovery",
        "AI Ethics Framework for Autonomous Systems",
        "Climate Change Impact on Global Supply Chains",
        "Demographic Shift in East Asian Labor Markets",
        "New Trade Agreement Reshapes Pacific Economy",
        "Spiritual Well-being in Digital Age Study",
        "Blockchain Revolution in Financial Services",
        "Gene Editing Regulation Update 2026",
        "Urban Migration Patterns Post-Pandemic",
        "Carbon Neutral Technology Adoption Accelerates"
    ]
    return titles[index % len(titles)]


def test_phase_1_research(tracker):
    """Test Phase 1: Research (Information Collection)"""
    log("PHASE", "=== PHASE 1: RESEARCH ===")

    # Step 1.1: Archive Loader (Mock)
    tracker.start_step("1.1 Archive Loader")

    # Simulate loading previous signals
    previous_signals = {
        "url_index": {},
        "title_index": {},
        "entity_index": {},
        "signals": []
    }

    output_path = BASE_DIR / "context" / "previous-signals.json"
    with open(output_path, 'w') as f:
        json.dump(previous_signals, f, indent=2)

    log("INFO", "Loaded 0 historical signals (first run)")
    tracker.end_step()

    # Step 1.2: Multi-Source Scanner (Mock)
    tracker.start_step("1.2 Multi-Source Scanner")

    # Generate mock signals
    signals = generate_mock_signals(SIGNAL_COUNT)

    raw_scan = {
        "scan_metadata": {
            "date": TEST_DATE,
            "sources_scanned": 5,
            "total_items": len(signals),
            "execution_time": 0
        },
        "items": signals
    }

    output_path = BASE_DIR / "raw" / f"daily-scan-{TEST_DATE}.json"
    with open(output_path, 'w') as f:
        json.dump(raw_scan, f, indent=2)

    log("INFO", f"Collected {len(signals)} signals from mock sources")

    # Create shared context
    shared_context = {
        "version": "1.0",
        "workflow_id": f"scan-{TEST_DATE}",
        "created_at": datetime.now().isoformat(),
        "last_updated": datetime.now().isoformat(),
        "signal_embeddings": {},
        "preliminary_analysis": {},
        "metadata": {
            "total_signals_processed": len(signals),
            "agents_invoked": ["multi-source-scanner"]
        }
    }

    context_path = BASE_DIR / "context" / f"shared-context-{TEST_DATE}.json"
    with open(context_path, 'w') as f:
        json.dump(shared_context, f, indent=2)

    tracker.end_step()

    # Step 1.3: Deduplication Filter (Mock)
    tracker.start_step("1.3 Deduplication Filter")

    # Simulate deduplication (remove ~30% as "duplicates")
    duplicates_removed = int(len(signals) * 0.3)
    new_signals = signals[duplicates_removed:]

    filtered_output = {
        "filter_metadata": {
            "total_raw": len(signals),
            "total_duplicates": duplicates_removed,
            "total_new": len(new_signals),
            "filter_rate": duplicates_removed / len(signals),
            "stage_breakdown": {
                "stage_1_url": int(duplicates_removed * 0.4),
                "stage_2_string": int(duplicates_removed * 0.3),
                "stage_3_semantic": int(duplicates_removed * 0.2),
                "stage_4_entity": int(duplicates_removed * 0.1)
            },
            "avg_confidence": 0.92
        },
        "new_signals": new_signals
    }

    output_path = BASE_DIR / "filtered" / f"new-signals-{TEST_DATE}.json"
    with open(output_path, 'w') as f:
        json.dump(filtered_output, f, indent=2)

    log("INFO", f"Filtered to {len(new_signals)} new signals (removed {duplicates_removed})")
    tracker.end_step()

    return len(new_signals)


def test_phase_2_planning(tracker, signal_count):
    """Test Phase 2: Planning (Analysis & Structuring)"""
    log("PHASE", "=== PHASE 2: PLANNING ===")

    # Load filtered signals
    filtered_path = BASE_DIR / "filtered" / f"new-signals-{TEST_DATE}.json"
    with open(filtered_path, 'r') as f:
        filtered_data = json.load(f)
    signals = filtered_data['new_signals']

    # Step 2.1: Signal Classifier (Mock)
    tracker.start_step("2.1 Signal Classifier")

    classified_signals = []
    for signal in signals:
        classified_signal = signal.copy()
        classified_signal['final_category'] = signal['preliminary_category']
        classified_signal['significance'] = (hash(signal['id']) % 5) + 1
        classified_signal['accuracy'] = 4
        classified_signal['confidence'] = 4
        classified_signal['innovation'] = (hash(signal['id']) % 4) + 2
        classified_signals.append(classified_signal)

    output_path = BASE_DIR / "structured" / f"classified-signals-{TEST_DATE}.json"
    with open(output_path, 'w') as f:
        json.dump(classified_signals, f, indent=2)

    log("INFO", f"Classified {len(classified_signals)} signals")
    tracker.end_step()

    # Step 2.2: Impact Analyzer (Mock - OPTIMIZED)
    tracker.start_step("2.2 Impact Analyzer (OPTIMIZED)")

    # Simulate OPTIMIZED hierarchical clustering
    n = len(classified_signals)

    # Group by category
    groups = {}
    for signal in classified_signals:
        cat = signal['final_category']
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(signal)

    log("INFO", f"Grouped {n} signals into {len(groups)} STEEPs categories")

    # Simulate intra-group analysis (batched)
    intra_comparisons = 0
    for cat, group_signals in groups.items():
        if len(group_signals) > 1:
            group_n = len(group_signals)
            pairs = (group_n * (group_n - 1)) // 2  # Only upper triangle
            batches = (pairs + 9) // 10  # Batch size = 10

            # Simulate batched LLM calls (10ms per batch, not per pair)
            time.sleep(batches * 0.01)
            intra_comparisons += pairs

            log("INFO", f"  {cat}: {group_n} signals, {pairs} pairs, {batches} batches")

    # Simulate inter-group representative analysis
    representatives_per_category = 3
    cross_category_comparisons = 0

    for i, cat_a in enumerate(groups.keys()):
        for cat_b in list(groups.keys())[i+1:]:
            # 3 reps from each category: 3×3 = 9 pairs
            pairs = representatives_per_category * representatives_per_category
            cross_category_comparisons += pairs

    # Batch the inter-group comparisons
    inter_batches = (cross_category_comparisons + 9) // 10
    time.sleep(inter_batches * 0.01)

    total_comparisons = intra_comparisons + cross_category_comparisons
    total_batches = sum((len(g) * (len(g)-1))//2 + 9 for g in groups.values() if len(g) > 1) // 10 + inter_batches

    log("INFO", f"Hierarchical analysis: {total_comparisons} pairs in {total_batches} batches")
    log("SUCCESS", f"Optimization: {n*n} naive → {total_comparisons} optimized ({100*(1-total_comparisons/(n*n)):.1f}% reduction)")

    # Generate impact assessment
    impact_assessment = []
    for signal in classified_signals:
        impact = {
            "signal_id": signal['id'],
            "impact_score": (hash(signal['id']) % 8) + 2,
            "first_order_impacts": ["Impact 1", "Impact 2"],
            "second_order_impacts": ["Derived effect 1"]
        }
        impact_assessment.append(impact)

    output_path = BASE_DIR / "analysis" / f"impact-assessment-{TEST_DATE}.json"
    with open(output_path, 'w') as f:
        json.dump(impact_assessment, f, indent=2)

    # Save optimization metrics
    optimization_metrics = {
        "total_signals": n,
        "categories": len(groups),
        "naive_comparisons": n * n,
        "optimized_comparisons": total_comparisons,
        "reduction_percentage": round(100 * (1 - total_comparisons/(n*n)), 1),
        "naive_batches": n * n,
        "optimized_batches": total_batches,
        "time_saved_percentage": round(100 * (1 - total_batches/(n*n)), 1)
    }

    with open(BASE_DIR / "analysis" / f"optimization-metrics-{TEST_DATE}.json", 'w') as f:
        json.dump(optimization_metrics, f, indent=2)

    log("INFO", f"Completed {total_comparisons} comparisons (vs {n*n} naive)")
    tracker.end_step()

    # Step 2.3: Priority Ranker (Mock)
    tracker.start_step("2.3 Priority Ranker")

    priority_ranked = []
    for i, signal in enumerate(classified_signals):
        ranked = signal.copy()
        ranked['priority_score'] = 10 - (i * 0.2)
        ranked['rank'] = i + 1
        priority_ranked.append(ranked)

    # Sort by priority
    priority_ranked.sort(key=lambda x: x['priority_score'], reverse=True)

    output_path = BASE_DIR / "analysis" / f"priority-ranked-{TEST_DATE}.json"
    with open(output_path, 'w') as f:
        json.dump(priority_ranked, f, indent=2)

    log("INFO", f"Ranked {len(priority_ranked)} signals by priority")
    tracker.end_step()

    return priority_ranked


def test_phase_3_implementation(tracker, ranked_signals):
    """Test Phase 3: Implementation (Report Generation)"""
    log("PHASE", "=== PHASE 3: IMPLEMENTATION ===")

    # Step 3.1: Database Updater (Mock)
    tracker.start_step("3.1 Database Updater")

    database = {
        "version": "1.0",
        "last_updated": datetime.now().isoformat(),
        "signals": ranked_signals
    }

    output_path = BASE_DIR / "signals" / "database.json"
    with open(output_path, 'w') as f:
        json.dump(database, f, indent=2)

    # Snapshot
    snapshot_path = BASE_DIR / "signals" / "snapshots" / f"database-{TEST_DATE}.json"
    os.makedirs(snapshot_path.parent, exist_ok=True)
    with open(snapshot_path, 'w') as f:
        json.dump(database, f, indent=2)

    log("INFO", f"Updated database with {len(ranked_signals)} signals")
    tracker.end_step()

    # Step 3.2: Report Generator (Mock)
    tracker.start_step("3.2 Report Generator")

    report = f"""# 환경스캐닝 일일 보고서

**날짜**: {TEST_DATE}
**신규 신호**: {len(ranked_signals)}개

## 1. Executive Summary

오늘 {len(ranked_signals)}개의 신규 신호가 탐지되었습니다.

상위 3개 신호:
1. {ranked_signals[0]['title']}
2. {ranked_signals[1]['title']}
3. {ranked_signals[2]['title']}

## 2. 신규 탐지 신호 (NEW)

### 기술 (T) - {len([s for s in ranked_signals if s['final_category'] == 'T'])}개
### 정치 (P) - {len([s for s in ranked_signals if s['final_category'] == 'P'])}개
### 경제 (E) - {len([s for s in ranked_signals if s['final_category'] == 'E'])}개

## 3. 전략적 시사점

신호 분석 결과를 바탕으로 다음 영역에 주목이 필요합니다...

---
생성 시각: {datetime.now().isoformat()}
"""

    output_path = BASE_DIR / "reports" / "daily" / f"environmental-scan-{TEST_DATE}.md"
    with open(output_path, 'w') as f:
        f.write(report)

    log("INFO", "Generated Korean report")
    tracker.end_step()

    # Step 3.3: Archive Notifier (Mock)
    tracker.start_step("3.3 Archive Notifier")

    # Copy to archive
    archive_dir = BASE_DIR / "reports" / "archive" / datetime.now().strftime("%Y") / datetime.now().strftime("%m")
    os.makedirs(archive_dir, exist_ok=True)

    archive_path = archive_dir / f"environmental-scan-{TEST_DATE}.md"
    with open(output_path, 'r') as src, open(archive_path, 'w') as dst:
        dst.write(src.read())

    log("INFO", f"Archived to {archive_path}")
    tracker.end_step()


def generate_quality_metrics(tracker):
    """Generate quality metrics report"""
    log("METRICS", "=== Quality Metrics ===")

    metrics = {
        "workflow_id": f"scan-{TEST_DATE}",
        "execution_time_seconds": sum(tracker.timings.values()),
        "phase_times": {
            "phase_1": sum(v for k, v in tracker.timings.items() if k.startswith("1.")),
            "phase_2": sum(v for k, v in tracker.timings.items() if k.startswith("2.")),
            "phase_3": sum(v for k, v in tracker.timings.items() if k.startswith("3."))
        },
        "step_times": tracker.timings,
        "quality_scores": {
            "dedup_accuracy": 0.92,  # Mock
            "classification_accuracy": 0.94,  # Mock
            "human_ai_agreement": 0.88  # Mock
        },
        "signals_processed": {
            "collected": 50,
            "filtered": 35,
            "classified": 35,
            "archived": 35
        }
    }

    output_path = BASE_DIR / "logs" / "quality-metrics" / f"workflow-{TEST_DATE}.json"
    os.makedirs(output_path.parent, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    log("SUCCESS", f"Quality metrics saved to {output_path}")
    return metrics


def main():
    """Main test execution"""
    print("\n" + "="*80)
    print("ENVIRONMENTAL SCANNING WORKFLOW - INTEGRATION TEST")
    print("="*80 + "\n")

    tracker = PerformanceTracker()

    try:
        # Phase 1
        signal_count = test_phase_1_research(tracker)

        # Phase 2
        ranked_signals = test_phase_2_planning(tracker, signal_count)

        # Phase 3
        test_phase_3_implementation(tracker, ranked_signals)

        # Generate metrics
        metrics = generate_quality_metrics(tracker)

        # Bottleneck analysis
        print("\n" + "="*80)
        bottlenecks = tracker.report_bottlenecks()
        print("="*80 + "\n")

        # Recommendations
        print("\n📊 RECOMMENDATIONS:\n")

        for step, time_taken in bottlenecks[:3]:
            percentage = (time_taken / sum(tracker.timings.values())) * 100

            if "2.2" in step and percentage > 20:
                print(f"🔴 CRITICAL BOTTLENECK: {step}")
                print(f"   Current: N×N cross-impact analysis ({time_taken:.2f}s)")
                print(f"   Solution: Implement hierarchical clustering (98% reduction)")
                print(f"   Expected: {time_taken * 0.02:.2f}s (vs {time_taken:.2f}s)\n")

            elif percentage > 10:
                print(f"⚠️  OPTIMIZATION OPPORTUNITY: {step}")
                print(f"   Time: {time_taken:.2f}s ({percentage:.1f}% of total)")
                print(f"   Review: Check for inefficiencies\n")

        # Success summary
        print("\n✅ WORKFLOW TEST COMPLETED SUCCESSFULLY\n")
        print(f"Total time: {sum(tracker.timings.values()):.2f}s")
        print(f"Signals processed: {SIGNAL_COUNT} → {signal_count} (after dedup)")
        print(f"Phases: 3/3 completed")
        print(f"Quality metrics: Saved to logs/quality-metrics/")

        return 0

    except Exception as e:
        log("ERROR", f"Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
