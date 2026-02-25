"""
Tests for timeline_map_generator.py

Validates SOT config loading, evolution-map parsing, theme clustering,
STEEPs timeline computation, pSST ranking, escalation detection,
cross-WF signal extraction, and markdown formatting.
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add core module path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "env-scanning" / "core"))
import timeline_map_generator as tmg


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------

def _make_evolution_entry(
    signal_id="sig-001",
    thread_id="THREAD-WF1-001",
    canonical_title="Test Signal",
    state="NEW",
    psst_current=85,
    scan_date="2026-02-11",
    primary_category="T",
    keywords=None,
):
    """Helper to create a test evolution entry."""
    return {
        "signal_id": signal_id,
        "thread_id": thread_id,
        "canonical_title": canonical_title,
        "title": canonical_title,
        "state": state,
        "state_ko": {"NEW": "신규", "RECURRING": "반복 등장"}.get(state, state),
        "confidence": "N/A" if state == "NEW" else "HIGH",
        "appearance_count": 1,
        "primary_category": primary_category,
        "keywords": keywords or ["test", "signal"],
        "scan_date": scan_date,
        "metrics": {
            "velocity": 0.0,
            "direction": "STABLE",
            "expansion": 0.0,
            "days_tracked": 0,
            "psst_current": psst_current,
            "psst_previous": 0,
            "psst_delta": "0",
        },
        "thread_history_summary": [
            {"date": scan_date, "title": canonical_title, "psst": psst_current}
        ],
        "psst_score": psst_current,
    }


def _make_evolution_map(
    workflow="wf1-general",
    scan_date="2026-02-11",
    entries=None,
):
    """Helper to create a test evolution-map dict."""
    if entries is None:
        entries = []
    return {
        "tracker_version": "1.3.0",
        "workflow": workflow,
        "scan_date": scan_date,
        "computed_at": "2026-02-11T00:00:00Z",
        "config_source": "test",
        "config_used": {},
        "summary": {
            "total_signals_today": len(entries),
            "new_signals": len(entries),
            "recurring_signals": 0,
            "strengthening_signals": 0,
            "weakening_signals": 0,
            "transformed_signals": 0,
            "faded_threads": 0,
            "active_threads": len(entries),
        },
        "evolution_entries": entries,
        "faded_threads": [],
        "new_threads_created": [],
    }


def _make_evolution_index(threads=None):
    """Helper to create a test evolution-index dict."""
    return {
        "version": "1.3.0",
        "workflow": "wf1-general",
        "thread_id_counter": 10,
        "total_threads": len(threads) if threads else 0,
        "active_threads": len(threads) if threads else 0,
        "threads": threads or {},
    }


def _make_registry_yaml(tmp_path, timeline_map_config=None):
    """Create a minimal workflow-registry.yaml for testing."""
    config = {
        "system": {
            "signal_evolution": {
                "enabled": True,
                "timeline_map": timeline_map_config or {
                    "enabled": True,
                    "generator_script": "env-scanning/core/timeline_map_generator.py",
                    "output_filename_pattern": "timeline-map-{date}.md",
                    "lookback_days": 7,
                    "min_signals_for_theme": 2,
                    "top_n_psst": 10,
                },
            },
        },
    }
    import yaml
    registry_path = tmp_path / "workflow-registry.yaml"
    with open(registry_path, "w") as f:
        yaml.dump(config, f)
    return str(registry_path)


def _make_cross_map(correlations=None):
    """Create a test cross-evolution-map dict."""
    return {
        "tracker_version": "1.3.0",
        "computed_at": "2026-02-11T00:00:00Z",
        "total_correlations": len(correlations) if correlations else 0,
        "correlations": correlations or [],
    }


# ---------------------------------------------------------------------------
# Test 1: load_timeline_config
# ---------------------------------------------------------------------------

class TestLoadTimelineConfig:
    def test_load_timeline_config(self, tmp_path):
        """SOT에서 설정 읽기 정상."""
        registry_path = _make_registry_yaml(tmp_path)
        config = tmg.load_timeline_config(registry_path)

        assert config["enabled"] is True
        assert config["lookback_days"] == 7
        assert config["min_signals_for_theme"] == 2
        assert config["top_n_psst"] == 10

    def test_load_timeline_config_disabled(self, tmp_path):
        """enabled=false이면 빈 config 반환."""
        registry_path = _make_registry_yaml(tmp_path, timeline_map_config={
            "enabled": False,
            "lookback_days": 7,
        })
        config = tmg.load_timeline_config(registry_path)
        assert config == {}

    def test_load_timeline_config_missing_file(self, tmp_path):
        """파일 없으면 빈 dict 반환."""
        config = tmg.load_timeline_config(str(tmp_path / "nonexistent.yaml"))
        assert config == {}


# ---------------------------------------------------------------------------
# Test 3: load_evolution_maps_graceful
# ---------------------------------------------------------------------------

class TestLoadEvolutionMaps:
    def test_load_evolution_maps_graceful(self, tmp_path):
        """파일 없으면 빈 dict 반환 (crash 안 함)."""
        result = tmg.load_evolution_maps({
            "wf1": str(tmp_path / "missing-wf1.json"),
            "wf2": "",
            "wf3": str(tmp_path / "missing-wf3.json"),
        })
        assert result["wf1"] == {}
        assert result["wf2"] == {}
        assert result["wf3"] == {}

    def test_load_evolution_maps_with_data(self, tmp_path):
        """JSON 파일이 있으면 정상 로딩."""
        evo_map = _make_evolution_map(entries=[
            _make_evolution_entry(signal_id="sig-001"),
        ])
        path = tmp_path / "evolution-map.json"
        with open(path, "w") as f:
            json.dump(evo_map, f)

        result = tmg.load_evolution_maps({"wf1": str(path)})
        assert len(result["wf1"]["evolution_entries"]) == 1


# ---------------------------------------------------------------------------
# Test 4: cluster_by_theme_bilingual
# ---------------------------------------------------------------------------

class TestClusterByTheme:
    def test_cluster_by_theme_bilingual(self):
        """영어+한국어 키워드 모두 매칭."""
        entries = [
            _make_evolution_entry(
                signal_id="s1", canonical_title="AI tariff policy",
                keywords=["tariff", "trade"], primary_category="E",
                scan_date="2026-02-10",
            ),
            _make_evolution_entry(
                signal_id="s2", canonical_title="관세 전쟁 확대",
                keywords=["관세", "무역"], primary_category="P",
                scan_date="2026-02-11",
            ),
        ]

        clusters = tmg.cluster_by_theme(entries, min_signals=1)
        assert "trade_tariff" in clusters
        assert clusters["trade_tariff"]["count"] >= 2

    def test_cluster_minimum_threshold(self):
        """min_signals_for_theme 미만이면 테마 제외."""
        entries = [
            _make_evolution_entry(
                signal_id="s1", canonical_title="Nuclear arms treaty",
                keywords=["nuclear weapon", "arms control"],
                primary_category="P",
            ),
        ]

        # min_signals=2 → only 1 signal → should exclude
        clusters = tmg.cluster_by_theme(entries, min_signals=2)
        assert "nuclear_security" not in clusters

        # min_signals=1 → should include
        clusters = tmg.cluster_by_theme(entries, min_signals=1)
        assert "nuclear_security" in clusters


# ---------------------------------------------------------------------------
# Test 6: compute_steeps_timeline
# ---------------------------------------------------------------------------

class TestComputeSteepsTimeline:
    def test_compute_steeps_timeline(self):
        """날짜×STEEPs 매트릭스 정확성."""
        entries = [
            _make_evolution_entry(signal_id="s1", primary_category="T", scan_date="2026-02-10"),
            _make_evolution_entry(signal_id="s2", primary_category="T", scan_date="2026-02-10"),
            _make_evolution_entry(signal_id="s3", primary_category="E", scan_date="2026-02-10"),
            _make_evolution_entry(signal_id="s4", primary_category="T", scan_date="2026-02-11"),
            _make_evolution_entry(signal_id="s5", primary_category="P", scan_date="2026-02-11"),
        ]

        timeline = tmg.compute_steeps_timeline(entries)

        assert "2026-02-10" in timeline
        assert "2026-02-11" in timeline
        assert timeline["2026-02-10"]["T"] == 2
        assert timeline["2026-02-10"]["E"] == 1
        assert timeline["2026-02-11"]["T"] == 1
        assert timeline["2026-02-11"]["P"] == 1


# ---------------------------------------------------------------------------
# Test 7: compute_psst_rankings
# ---------------------------------------------------------------------------

class TestComputePsstRankings:
    def test_compute_psst_rankings(self):
        """pSST 내림차순 정렬 + top_n 제한."""
        entries = [
            _make_evolution_entry(signal_id="s1", canonical_title="A", psst_current=92),
            _make_evolution_entry(signal_id="s2", canonical_title="B", psst_current=88),
            _make_evolution_entry(signal_id="s3", canonical_title="C", psst_current=95),
            _make_evolution_entry(signal_id="s4", canonical_title="D", psst_current=80),
            _make_evolution_entry(signal_id="s5", canonical_title="E", psst_current=90),
        ]

        rankings = tmg.compute_psst_rankings(entries, top_n=3)

        assert len(rankings) == 3
        assert rankings[0]["psst_score"] == 95
        assert rankings[1]["psst_score"] == 92
        assert rankings[2]["psst_score"] == 90


# ---------------------------------------------------------------------------
# Test 8: detect_escalations
# ---------------------------------------------------------------------------

class TestDetectEscalations:
    def test_detect_escalations(self):
        """pSST 상승 추이 탐지."""
        clusters = {
            "trade_tariff": {
                "label_ko": "무역·관세 전쟁",
                "label_en": "Trade & Tariffs",
                "priority": "CRITICAL",
                "signals": [
                    {"scan_date": "2026-02-10", "psst_score": 85, "title": "Signal A"},
                    {"scan_date": "2026-02-10", "psst_score": 87, "title": "Signal B"},
                    {"scan_date": "2026-02-11", "psst_score": 93, "title": "Signal C"},
                    {"scan_date": "2026-02-11", "psst_score": 91, "title": "Signal D"},
                ],
                "count": 4,
            },
        }

        escalations = tmg.detect_escalations(clusters, min_signals=2)

        assert len(escalations) >= 1
        esc = escalations[0]
        assert esc["theme_id"] == "trade_tariff"
        assert esc["direction"] == "↑"  # avg increased from 86 to 92
        assert esc["current_psst"] == 93

    def test_no_escalation_stable(self):
        """pSST가 일정하면 에스컬레이션 없음 (count도 같을 때)."""
        clusters = {
            "test_theme": {
                "label_ko": "테스트",
                "label_en": "Test",
                "priority": "MEDIUM",
                "signals": [
                    {"scan_date": "2026-02-10", "psst_score": 85, "title": "A"},
                    {"scan_date": "2026-02-11", "psst_score": 85, "title": "B"},
                ],
                "count": 2,
            },
        }

        escalations = tmg.detect_escalations(clusters, min_signals=2)
        # Average is same, count is same per date → no escalation
        assert len(escalations) == 0


# ---------------------------------------------------------------------------
# Test 9: find_cross_wf_signals
# ---------------------------------------------------------------------------

class TestFindCrossWfSignals:
    def test_find_cross_wf_signals(self):
        """cross-evolution-map에서 교차 시그널 추출."""
        cross_map = _make_cross_map(correlations=[
            {
                "source_wf": "wf2",
                "source_thread_id": "THREAD-WF2-001",
                "source_title": "Quantum Computing Breakthrough",
                "target_wf": "wf1",
                "target_thread_id": "THREAD-WF1-005",
                "target_title": "Quantum AI Convergence",
                "title_similarity": 0.82,
                "keyword_similarity": 0.75,
                "combined_score": 0.79,
                "confidence": "MEDIUM",
                "lead_days": 3,
                "direction": "wf2→wf1",
            },
        ])

        result = tmg.find_cross_wf_signals(cross_map)
        assert len(result) == 1
        assert result[0]["source_wf"] == "wf2"

    def test_find_cross_wf_signals_empty(self):
        """빈 cross-map이면 빈 리스트."""
        assert tmg.find_cross_wf_signals({}) == []
        assert tmg.find_cross_wf_signals(None) == []


# ---------------------------------------------------------------------------
# Test 10: format_timeline_markdown_structure
# ---------------------------------------------------------------------------

class TestFormatTimelineMarkdown:
    def test_format_timeline_markdown_structure(self):
        """마크다운 출력에 필수 섹션 6개 존재."""
        md = tmg.format_timeline_markdown(
            scan_date="2026-02-11",
            lookback_days=7,
            wf_counts={"wf1": 10, "wf2": 5, "wf3": 15},
            theme_clusters={
                "ai_technology": {
                    "label_ko": "AI·기술 진화",
                    "label_en": "AI & Technology",
                    "priority": "HIGH",
                    "count": 5,
                    "signals": [
                        {"scan_date": "2026-02-11", "psst_score": 90,
                         "title": "AI Test", "source_wf": "WF1",
                         "canonical_title": "AI Test", "keywords": []},
                    ] * 5,
                },
            },
            steeps_timeline={
                "2026-02-10": {"T": 5, "E": 3},
                "2026-02-11": {"T": 8, "P": 2},
            },
            psst_rankings=[
                {"psst_score": 93, "scan_date": "2026-02-11",
                 "source_wf": "WF3", "title": "Top Signal",
                 "canonical_title": "Top Signal"},
            ],
            cross_wf_signals=[],
            escalations=[
                {"theme_id": "ai_technology", "label_ko": "AI·기술 진화",
                 "priority": "HIGH", "trajectory": "02-10(85) → 02-11(90)",
                 "current_psst": 90, "direction": "↑",
                 "date_stats": [], "signal_count": 5},
            ],
        )

        # Check all 6 required sections exist
        assert "# 시그널 진화 타임라인 맵" in md
        assert "## 타임라인 개관" in md
        assert "## 1. 핵심 테마별 시간축 추적" in md
        assert "## 2. STEEPs 도메인별 시간축 분포" in md
        assert "## 3. pSST 우선순위 Top-10 궤적" in md
        assert "## 4. 교차 워크플로우 시그널 궤적" in md
        assert "## 5. 에스컬레이션 모니터링" in md
        assert "## 6. 메타데이터" in md

        # Check metadata section
        assert f"engine: Timeline Map Generator v{tmg.VERSION}" in md
        assert "total_signals: 30" in md


# ---------------------------------------------------------------------------
# Test 11: generate_timeline_map_e2e
# ---------------------------------------------------------------------------

class TestGenerateTimelineMapE2E:
    def test_generate_timeline_map_e2e(self, tmp_path):
        """전체 파이프라인 통합 테스트."""
        # Prepare registry
        registry_path = _make_registry_yaml(tmp_path)

        # Prepare evolution maps
        wf1_entries = [
            _make_evolution_entry(
                signal_id="wf1-001", canonical_title="US-China Trade Tensions",
                keywords=["trade", "tariff", "us-china"], primary_category="E",
                psst_current=88, scan_date="2026-02-11",
            ),
            _make_evolution_entry(
                signal_id="wf1-002", canonical_title="AI Agent Revolution",
                keywords=["AI", "agent", "autonomous"], primary_category="T",
                psst_current=90, scan_date="2026-02-11",
            ),
            _make_evolution_entry(
                signal_id="wf1-003", canonical_title="Nuclear Arms Treaty Expires",
                keywords=["nuclear", "arms", "treaty", "nuclear weapon"], primary_category="P",
                psst_current=92, scan_date="2026-02-11",
            ),
        ]
        wf1_map = _make_evolution_map("wf1-general", "2026-02-11", wf1_entries)
        wf1_path = tmp_path / "wf1-evolution-map.json"
        with open(wf1_path, "w") as f:
            json.dump(wf1_map, f)

        wf2_entries = [
            _make_evolution_entry(
                signal_id="wf2-001", canonical_title="Quantum AI Convergence",
                keywords=["quantum", "AI", "convergence"], primary_category="T",
                psst_current=85, scan_date="2026-02-11",
            ),
        ]
        wf2_map = _make_evolution_map("wf2-arxiv", "2026-02-11", wf2_entries)
        wf2_path = tmp_path / "wf2-evolution-map.json"
        with open(wf2_path, "w") as f:
            json.dump(wf2_map, f)

        wf3_entries = [
            _make_evolution_entry(
                signal_id="wf3-001", canonical_title="트럼프 관세 확정",
                keywords=["관세", "트럼프", "무역"], primary_category="P",
                psst_current=93, scan_date="2026-02-11",
            ),
            _make_evolution_entry(
                signal_id="wf3-002", canonical_title="삼성 HBM4 양산",
                keywords=["반도체", "삼성", "HBM4", "semiconductor"], primary_category="T",
                psst_current=90, scan_date="2026-02-11",
            ),
        ]
        wf3_map = _make_evolution_map("wf3-naver", "2026-02-11", wf3_entries)
        wf3_path = tmp_path / "wf3-evolution-map.json"
        with open(wf3_path, "w") as f:
            json.dump(wf3_map, f)

        # Cross-evolution-map
        cross_map = _make_cross_map(correlations=[
            {
                "source_wf": "wf1", "source_thread_id": "T-WF1-001",
                "source_title": "US-China Trade Tensions",
                "target_wf": "wf3", "target_thread_id": "T-WF3-001",
                "target_title": "트럼프 관세 확정",
                "title_similarity": 0.78, "keyword_similarity": 0.80,
                "combined_score": 0.79, "confidence": "MEDIUM",
                "lead_days": 1, "direction": "wf1→wf3",
            },
        ])
        cross_path = tmp_path / "cross-evolution-map.json"
        with open(cross_path, "w") as f:
            json.dump(cross_map, f)

        # Output path
        output_path = tmp_path / "timeline-map-2026-02-11.md"

        # Execute
        md = tmg.generate_timeline_map(
            registry_path=registry_path,
            wf_evolution_map_paths={
                "wf1": str(wf1_path),
                "wf2": str(wf2_path),
                "wf3": str(wf3_path),
            },
            wf_index_paths={"wf1": "", "wf2": "", "wf3": ""},
            cross_evolution_map_path=str(cross_path),
            scan_date="2026-02-11",
            output_path=str(output_path),
        )

        # Verify
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# 시그널 진화 타임라인 맵" in content
        assert "2026-02-11" in content
        assert "총 6개 시그널" in content  # 3 + 1 + 2 = 6

        # Check sections
        assert "## 1. 핵심 테마별 시간축 추적" in content
        assert "## 2. STEEPs 도메인별 시간축 분포" in content
        assert "## 3. pSST 우선순위 Top-10 궤적" in content
        assert "## 4. 교차 워크플로우 시그널 궤적" in content
        assert "## 6. 메타데이터" in content


# ---------------------------------------------------------------------------
# Test 12: generate_timeline_map_no_data
# ---------------------------------------------------------------------------

class TestGenerateTimelineMapNoData:
    def test_generate_timeline_map_no_data(self, tmp_path):
        """입력 없어도 빈 마크다운 정상 출력."""
        registry_path = _make_registry_yaml(tmp_path)
        output_path = tmp_path / "timeline-empty.md"

        md = tmg.generate_timeline_map(
            registry_path=registry_path,
            wf_evolution_map_paths={"wf1": "", "wf2": "", "wf3": ""},
            wf_index_paths={"wf1": "", "wf2": "", "wf3": ""},
            cross_evolution_map_path="",
            scan_date="2026-02-11",
            output_path=str(output_path),
        )

        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "# 시그널 진화 타임라인 맵" in content
        assert "총 0개 시그널" in content
        assert "## 6. 메타데이터" in content


# ---------------------------------------------------------------------------
# Test: discover_evolution_history
# ---------------------------------------------------------------------------

class TestDiscoverEvolutionHistory:
    def test_discover_within_window(self):
        """lookback 범위 내 thread history만 추출."""
        index = _make_evolution_index(threads={
            "THREAD-WF1-001": {
                "canonical_title": "Trade Signal",
                "primary_category": "E",
                "keywords": ["trade"],
                "created_date": "2026-02-05",
                "last_seen_date": "2026-02-11",
                "state": "RECURRING",
                "appearance_count": 3,
                "appearances": [
                    {"scan_date": "2026-02-01", "signal_id": "s1", "title": "Old", "psst_score": 80},
                    {"scan_date": "2026-02-06", "signal_id": "s2", "title": "In range", "psst_score": 85},
                    {"scan_date": "2026-02-11", "signal_id": "s3", "title": "Current", "psst_score": 90},
                ],
                "metrics_history": [],
            },
        })

        entries = tmg.discover_evolution_history(index, lookback_days=7, scan_date="2026-02-11")

        # 02-01 is outside 7-day window (02-05 ~ 02-11), only 02-06 and 02-11 should be in
        dates = [e["scan_date"] for e in entries]
        assert "2026-02-01" not in dates
        assert "2026-02-06" in dates
        assert "2026-02-11" in dates
        assert len(entries) == 2
