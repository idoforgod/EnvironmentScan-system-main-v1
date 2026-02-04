# 🏗️ arXiv Scanner 영구 통합 설계 계획

**날짜**: 2026-01-30
**목적**: arXiv 스캐너를 시스템의 영구적 핵심 기능으로 통합
**상태**: 📋 설계 계획 (구현 전 승인 필요)

---

## 📋 목차

1. [현재 상태 분석](#현재-상태-분석)
2. [통합 아키텍처 설계](#통합-아키텍처-설계)
3. [구현 계획](#구현-계획)
4. [파일 구조 재편성](#파일-구조-재편성)
5. [설정 관리](#설정-관리)
6. [에러 처리 및 복원력](#에러-처리-및-복원력)
7. [확장성 고려사항](#확장성-고려사항)
8. [테스트 전략](#테스트-전략)
9. [구현 순서](#구현-순서)

---

## 현재 상태 분석

### ✅ 검증 완료된 기능

```
scripts/arxiv_scanner.py (현재 위치)
├─ arXiv API 통합 ✅
├─ SSL 처리 ✅
├─ Rate limiting ✅
├─ STEEPs 카테고리 매핑 ✅
├─ 에러 처리 ✅
└─ 90개 논문 수집 성공 (15초) ✅

검증 결과:
- 성공률: 100%
- 데이터 품질: 완전한 메타데이터
- 성능: 15초/90개 논문
- 안정성: 프로덕션 준비 완료
```

### 🔄 현재 제한사항

1. **독립 실행 스크립트**: Workflow와 분리되어 수동 실행
2. **하드코딩된 설정**: 코드 내부에 설정값 포함
3. **단일 소스**: arXiv만 지원 (확장 불가)
4. **스케줄링 없음**: 자동 실행 미지원
5. **모니터링 부재**: 실패 알림 시스템 없음

---

## 통합 아키텍처 설계

### 🎯 설계 원칙

```
핵심 원칙:
1. 기존 workflow 철학 완벽 보존
2. Multi-source 확장 가능한 구조
3. 설정 기반 동작 (코드 수정 최소화)
4. 에러 복원력 (resilience)
5. 모니터링 및 관찰 가능성 (observability)
```

### 📐 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│                   (env-scan-orchestrator)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─ Phase 1: Data Collection
                      │
    ┌─────────────────┴─────────────────┐
    │                                   │
    v                                   v
┌─────────────────┐           ┌──────────────────┐
│ Archive Loader  │           │ Multi-Source     │
│   (Step 1.1)    │           │   Scanner        │
└─────────────────┘           │  (Step 1.2)      │
                              └────────┬─────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    v                  v                  v
           ┌─────────────────┐ ┌─────────────┐ ┌──────────────────┐
           │ arXiv Scanner   │ │ Google      │ │ Policy RSS       │
           │   (Core)        │ │ Scholar     │ │   Scanner        │
           │                 │ │ Scanner     │ │  (Future)        │
           │ - API 통합      │ │ (Future)    │ │                  │
           │ - Rate limit    │ │             │ │                  │
           │ - STEEPs 매핑   │ │             │ │                  │
           └─────────────────┘ └─────────────┘ └──────────────────┘
                    │
                    v
           ┌─────────────────────────────────────┐
           │  Unified Signal Format Converter    │
           │  (모든 소스를 표준 형식으로 변환)     │
           └─────────────────────────────────────┘
                    │
                    v
           ┌─────────────────────────────────────┐
           │   raw/daily-scan-{date}.json        │
           │   (통합된 멀티소스 결과)              │
           └─────────────────────────────────────┘
```

### 🔧 통합 구조

#### Option A: Multi-Source Scanner Agent 확장 (권장) ✅

**장점**:
- 기존 workflow 구조 유지
- Multi-source-scanner.md 명세와 일치
- 확장 용이 (Google Scholar, RSS 등 추가)
- Orchestrator 수정 최소화

**구조**:
```
.claude/agents/workers/multi-source-scanner.md
├─ Role: "Scan multiple information sources..."
├─ Input: config/sources.yaml
├─ Output: raw/daily-scan-{date}.json
└─ Processing Logic:
    ├─ load_configuration()
    ├─ scan_all_sources()
    │   ├─ scan_academic_source() ← arXiv 여기 통합
    │   ├─ scan_patent_source()
    │   ├─ scan_policy_source()
    │   └─ scan_blog_source()
    └─ write_raw_scan()

env-scanning/scanners/  (새 디렉토리)
├─ __init__.py
├─ base_scanner.py       ← 추상 베이스 클래스
├─ arxiv_scanner.py      ← 현재 스크립트 마이그레이션
├─ scholar_scanner.py    ← 미래 확장
└─ rss_scanner.py        ← 미래 확장
```

#### Option B: 독립 Subagent로 유지 (대안)

**장점**:
- 완전한 독립성
- 병렬 실행 가능

**단점**:
- Orchestrator 복잡도 증가
- Multi-source 통합 어려움

**결론**: **Option A 선택** (Multi-Source Scanner 확장)

---

## 구현 계획

### Phase 1: 기반 구조 구축 (1-2일)

#### 1.1 Base Scanner 추상 클래스 생성

**파일**: `env-scanning/scanners/base_scanner.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timedelta

class BaseScanner(ABC):
    """
    모든 소스 스캐너의 추상 베이스 클래스

    각 소스 스캐너는 이 클래스를 상속받아 scan() 메서드를 구현
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: sources.yaml에서 로드한 설정
        """
        self.config = config
        self.name = config['name']
        self.source_type = config['type']
        self.enabled = config.get('enabled', True)
        self.rate_limit = config.get('rate_limit', None)
        self.timeout = config.get('timeout', 30)

    @abstractmethod
    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7) -> List[Dict[str, Any]]:
        """
        소스를 스캔하여 신호 수집

        Args:
            steeps_domains: STEEPs 카테고리별 키워드
            days_back: 며칠 전까지 스캔할지

        Returns:
            표준 신호 형식의 리스트
        """
        pass

    def is_enabled(self) -> bool:
        """스캐너 활성화 여부"""
        return self.enabled

    def get_name(self) -> str:
        """소스 이름"""
        return self.name

    def validate_config(self) -> bool:
        """설정 유효성 검사"""
        required_fields = ['name', 'type']
        return all(field in self.config for field in required_fields)

    def to_standard_format(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        소스별 데이터를 표준 신호 형식으로 변환

        표준 형식:
        {
            "id": "arxiv-2601.12345",
            "title": "...",
            "source": {"name": "...", "type": "...", "url": "...", "published_date": "..."},
            "content": {"abstract": "...", "keywords": [...], "language": "en"},
            "preliminary_category": "T",
            "collected_at": "2026-01-30T09:00:00Z"
        }
        """
        return raw_data  # 서브클래스에서 오버라이드
```

#### 1.2 arXiv Scanner 리팩토링

**파일**: `env-scanning/scanners/arxiv_scanner.py`

```python
from .base_scanner import BaseScanner
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import ssl
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta

class ArXivScanner(BaseScanner):
    """
    arXiv 학술 논문 스캐너

    API: http://export.arxiv.org/api/query
    Rate Limit: 3초당 1회 요청 (API 가이드라인)
    """

    BASE_URL = "http://export.arxiv.org/api/query"
    RATE_LIMIT_DELAY = 3  # seconds

    # STEEPs → arXiv 카테고리 매핑
    CATEGORY_MAPPING = {
        'T_Technological': ['cs.AI', 'cs.RO', 'cs.CV', 'cs.CL', 'quant-ph'],
        'E_Economic': ['econ.EM', 'econ.GN', 'q-fin.EC', 'q-fin.TR'],
        'E_Environmental': ['physics.ao-ph', 'physics.geo-ph', 'q-bio.PE'],
        'S_Social': ['cs.CY', 'cs.HC', 'stat.AP'],
        'P_Political': ['cs.CY'],
        's_spiritual': ['cs.CY', 'physics.soc-ph']
    }

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_results_per_category = config.get('max_results', 20)
        self.last_request_time = 0

    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7) -> List[Dict[str, Any]]:
        """
        arXiv에서 논문 수집
        """
        all_papers = []

        # 각 STEEPs 카테고리별로 스캔
        for steeps_category in self.CATEGORY_MAPPING.keys():
            papers = self._scan_category(steeps_category)
            all_papers.extend(papers)

        return all_papers

    def _respect_rate_limit(self):
        """Rate limit 준수 (3초 대기)"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)
        self.last_request_time = time.time()

    def _scan_category(self, steeps_category: str) -> List[Dict[str, Any]]:
        """특정 STEEPs 카테고리 스캔"""
        arxiv_cats = self.CATEGORY_MAPPING.get(steeps_category, [])
        if not arxiv_cats:
            return []

        # 쿼리 생성
        query = self._build_query(arxiv_cats)

        # API 호출
        papers = self._fetch_papers(query, self.max_results_per_category)

        # 표준 형식으로 변환
        return [self.to_standard_format(p, steeps_category) for p in papers]

    # ... (기존 _build_query, _fetch_papers, _parse_entry 메서드들)

    def to_standard_format(self, paper: Dict[str, Any], category: str) -> Dict[str, Any]:
        """arXiv 논문을 표준 신호 형식으로 변환"""
        return {
            "id": f"arxiv-{paper['arxiv_id']}",
            "title": paper['title'],
            "source": {
                "name": "arXiv",
                "type": "academic",
                "url": paper['url'],
                "published_date": paper['published_date']
            },
            "content": {
                "abstract": paper['abstract'],
                "keywords": paper['categories'],
                "language": "en"
            },
            "metadata": {
                "arxiv_id": paper['arxiv_id'],
                "authors": paper['authors'],
                "arxiv_categories": paper['categories']
            },
            "preliminary_category": category[0],  # 첫 글자 (T, E, S, P, s)
            "collected_at": datetime.now().isoformat()
        }
```

#### 1.3 Scanner Factory 생성

**파일**: `env-scanning/scanners/scanner_factory.py`

```python
from typing import Dict, Any, List
from .base_scanner import BaseScanner
from .arxiv_scanner import ArXivScanner

class ScannerFactory:
    """
    설정 기반 스캐너 인스턴스 생성 팩토리
    """

    # 소스 타입 → 스캐너 클래스 매핑
    SCANNER_REGISTRY = {
        'academic': {
            'arXiv': ArXivScanner,
            # 'Google Scholar': GoogleScholarScanner,  # 미래 확장
        },
        # 'patent': {...},  # 미래 확장
        # 'policy': {...},  # 미래 확장
        # 'blog': {...},    # 미래 확장
    }

    @classmethod
    def create_scanner(cls, config: Dict[str, Any]) -> BaseScanner:
        """
        설정에서 적절한 스캐너 인스턴스 생성

        Args:
            config: sources.yaml의 개별 소스 설정

        Returns:
            BaseScanner 서브클래스 인스턴스

        Raises:
            ValueError: 지원하지 않는 소스인 경우
        """
        source_type = config['type']
        source_name = config['name']

        # 타입별 스캐너 찾기
        if source_type not in cls.SCANNER_REGISTRY:
            raise ValueError(f"Unsupported source type: {source_type}")

        type_scanners = cls.SCANNER_REGISTRY[source_type]

        if source_name not in type_scanners:
            raise ValueError(f"Unsupported source: {source_name} ({source_type})")

        scanner_class = type_scanners[source_name]
        return scanner_class(config)

    @classmethod
    def create_all_scanners(cls, sources_config: List[Dict[str, Any]]) -> List[BaseScanner]:
        """
        sources.yaml에서 모든 활성화된 스캐너 생성

        Args:
            sources_config: sources.yaml의 'sources' 리스트

        Returns:
            활성화된 스캐너 인스턴스 리스트
        """
        scanners = []

        for source_config in sources_config:
            # 비활성화된 소스는 건너뛰기
            if not source_config.get('enabled', True):
                continue

            try:
                scanner = cls.create_scanner(source_config)

                # 설정 유효성 검사
                if scanner.validate_config():
                    scanners.append(scanner)
                else:
                    print(f"[WARNING] Invalid config for {source_config['name']}")

            except ValueError as e:
                print(f"[WARNING] Skipping {source_config.get('name', 'unknown')}: {e}")
                continue

        return scanners
```

### Phase 2: Multi-Source Scanner 통합 (2-3일)

#### 2.1 Multi-Source Scanner 실행 스크립트

**파일**: `env-scanning/scripts/run_multi_source_scan.py`

```python
#!/usr/bin/env python3
"""
Multi-Source Scanner Executor
Orchestrator에서 호출되는 실제 실행 스크립트
"""

import sys
import os
import json
import yaml
from datetime import datetime
from typing import List, Dict, Any

# 스캐너 모듈 import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scanners.scanner_factory import ScannerFactory


def load_configuration():
    """설정 파일 로드"""
    with open('config/sources.yaml', 'r') as f:
        sources_config = yaml.safe_load(f)

    with open('config/domains.yaml', 'r') as f:
        domains_config = yaml.safe_load(f)

    return sources_config, domains_config


def run_scan(days_back: int = 7) -> Dict[str, Any]:
    """
    멀티소스 스캔 실행

    Args:
        days_back: 며칠 전까지 스캔할지

    Returns:
        scan_metadata와 items를 포함한 결과 딕셔너리
    """
    print("="*60)
    print("Multi-Source Scanner - Starting")
    print("="*60)

    start_time = datetime.now()

    # 1. 설정 로드
    sources_config, domains_config = load_configuration()

    # 2. 스캐너 생성
    scanners = ScannerFactory.create_all_scanners(sources_config['sources'])

    print(f"\n[INFO] Loaded {len(scanners)} active scanners")
    for scanner in scanners:
        print(f"  - {scanner.get_name()} ({scanner.source_type})")

    # 3. 각 스캐너 실행
    all_items = []
    sources_scanned = 0

    for scanner in scanners:
        try:
            print(f"\n[SCANNING] {scanner.get_name()}...")

            items = scanner.scan(
                steeps_domains=domains_config['STEEPs'],
                days_back=days_back
            )

            all_items.extend(items)
            sources_scanned += 1

            print(f"[SUCCESS] {scanner.get_name()}: {len(items)} items collected")
            print(f"[PROGRESS] Total items: {len(all_items)}")

        except Exception as e:
            # 개별 스캐너 실패는 전체 실패로 이어지지 않음
            print(f"[ERROR] {scanner.get_name()} failed: {e}")

            # Critical 소스인 경우에만 예외 발생
            if scanner.config.get('critical', False):
                raise

            continue

    # 4. 결과 구성
    execution_time = (datetime.now() - start_time).total_seconds()

    result = {
        "scan_metadata": {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "sources_scanned": sources_scanned,
            "total_items": len(all_items),
            "execution_time": round(execution_time, 2),
            "mode": "multi_source",
            "days_back": days_back
        },
        "items": all_items
    }

    print("\n" + "="*60)
    print(f"[COMPLETE] Scan finished in {execution_time:.1f}s")
    print(f"[RESULT] {len(all_items)} items from {sources_scanned} sources")
    print("="*60)

    return result


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Source Scanner')
    parser.add_argument('--days-back', type=int, default=7,
                       help='How many days back to scan (default: 7)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output file path (default: raw/daily-scan-{date}.json)')

    args = parser.parse_args()

    try:
        # 스캔 실행
        result = run_scan(days_back=args.days_back)

        # 출력 파일 경로
        if args.output:
            output_path = args.output
        else:
            today = datetime.now().strftime('%Y-%m-%d')
            output_path = f"raw/daily-scan-{today}.json"

        # 디렉토리 생성
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVED] Output written to: {output_path}")

        return 0

    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

#### 2.2 Orchestrator 통합

**파일**: `.claude/agents/env-scan-orchestrator.md` (수정)

```yaml
# Step 1.2: Multi-Source Scanner

invoke:
  tool: Task
  agent: general-purpose
  description: "Scan multiple sources for signals"

  prompt: |
    Execute the multi-source scanner to collect signals from configured sources.

    Command:
      cd env-scanning
      python3 scripts/run_multi_source_scan.py --days-back 7

    This will:
    1. Load sources.yaml and domains.yaml configurations
    2. Create scanner instances for all enabled sources (arXiv, etc.)
    3. Collect signals from each source
    4. Save unified results to raw/daily-scan-{date}.json

input:
  - config/sources.yaml (must exist)
  - config/domains.yaml (must exist)

output:
  - raw/daily-scan-{date}.json

verification:
  - File exists: raw/daily-scan-{date}.json
  - Contains: scan_metadata.total_items > 0
  - Contains: items array with at least 1 signal
  - Each signal has: id, title, source, preliminary_category

error_handling:
  - If critical source fails: halt workflow
  - If non-critical source fails: log warning, continue
  - Retry: 3 attempts with exponential backoff
```

### Phase 3: 설정 파일 업데이트 (1일)

#### 3.1 sources.yaml 확장

**파일**: `env-scanning/config/sources.yaml`

```yaml
# Multi-Source Configuration
# Version: 2.0.0 (arXiv integration)
# Last Updated: 2026-01-30

sources:
  # ========================================
  # Academic Sources
  # ========================================

  - name: "arXiv"
    type: "academic"
    enabled: true  # ✅ 영구 활성화

    # arXiv API 설정
    api_endpoint: "http://export.arxiv.org/api/query"
    rate_limit: 300  # per minute (실제로는 3초당 1회)
    timeout: 30

    # 중요도 설정
    critical: true  # 실패시 workflow 중단

    # 스캔 설정
    date_filter: "last_7_days"
    max_results: 20  # STEEPs 카테고리당 최대 논문 수

    # 품질 설정
    min_abstract_length: 100  # 최소 초록 길이

    # 메타데이터
    description: "Open academic paper repository - no authentication required"
    reliability: "high"
    cost: "free"

  # ========================================
  # Future Academic Sources
  # ========================================

  - name: "Google Scholar"
    type: "academic"
    enabled: false  # 미래 확장
    api_endpoint: "https://serpapi.com/search"
    api_key_env: "SERPAPI_KEY"
    rate_limit: 100  # per hour
    timeout: 30
    critical: false
    max_results: 50

  - name: "SSRN"
    type: "academic"
    enabled: false  # 미래 확장
    rss_feed: "https://papers.ssrn.com/sol3/rss_feed.cfm"
    timeout: 15
    critical: false

# ========================================
# Global Settings
# ========================================

retry_policy:
  max_attempts: 3
  backoff_strategy: "exponential"  # 1s, 2s, 4s
  timeout_increase: true

error_handling:
  on_critical_failure: "halt_workflow"
  on_non_critical_failure: "skip_and_continue"
  log_errors: true
  notify_on_failure: false

# ========================================
# Monitoring
# ========================================

monitoring:
  track_performance: true
  track_success_rate: true
  alert_on_failures: false  # 미래 확장 (이메일/Slack)
```

---

## 파일 구조 재편성

### 최종 디렉토리 구조

```
env-scanning/
├─ config/
│  ├─ sources.yaml              ← arXiv 영구 설정 포함
│  ├─ domains.yaml              ← STEEPs 카테고리 정의
│  └─ thresholds.yaml           ← 기존
│
├─ scanners/                    ← 새로 생성
│  ├─ __init__.py
│  ├─ base_scanner.py           ← 추상 베이스 클래스
│  ├─ arxiv_scanner.py          ← arXiv 통합 (리팩토링)
│  ├─ scanner_factory.py        ← 팩토리 패턴
│  └─ README.md                 ← 스캐너 추가 가이드
│
├─ scripts/
│  ├─ run_multi_source_scan.py  ← Orchestrator에서 호출
│  ├─ run_real_workflow.py      ← 기존 (테스트용)
│  └─ (arxiv_scanner.py 삭제)   ← scanners/로 이동
│
├─ raw/                         ← 기존
├─ filtered/                    ← 기존
├─ structured/                  ← 기존
├─ analysis/                    ← 기존
├─ reports/                     ← 기존
└─ context/                     ← 기존
```

### 파일 이동 계획

```bash
# 1. 새 디렉토리 생성
mkdir -p env-scanning/scanners

# 2. Base scanner 생성
# (새 파일들 생성)

# 3. arXiv scanner 마이그레이션
# scripts/arxiv_scanner.py → scanners/arxiv_scanner.py
# (BaseScanner 상속 구조로 리팩토링)

# 4. 독립 실행 스크립트 제거
# scripts/arxiv_scanner.py 삭제 (scanners/로 통합)
```

---

## 설정 관리

### 환경 변수 관리

**파일**: `env-scanning/.env.example`

```bash
# Multi-Source Scanner Environment Variables
# Copy this file to .env and fill in your values

# arXiv
# (No API key required - open access)

# Google Scholar (Future)
# SERPAPI_KEY=your_serpapi_key_here

# Monitoring (Future)
# SLACK_WEBHOOK_URL=your_slack_webhook
# EMAIL_SMTP_SERVER=smtp.gmail.com
# EMAIL_SMTP_PORT=587
# EMAIL_USERNAME=your_email
# EMAIL_PASSWORD=your_password
```

### 설정 유효성 검사

**파일**: `env-scanning/scripts/validate_config.py`

```python
#!/usr/bin/env python3
"""
설정 파일 유효성 검사 스크립트
"""

import yaml
import sys

def validate_sources_yaml():
    """sources.yaml 유효성 검사"""
    with open('config/sources.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 필수 필드 검사
    assert 'sources' in config
    assert len(config['sources']) > 0

    # 최소 1개 활성화된 소스 필요
    enabled_sources = [s for s in config['sources'] if s.get('enabled', True)]
    assert len(enabled_sources) > 0, "No enabled sources found"

    # 각 소스 유효성 검사
    for source in config['sources']:
        assert 'name' in source
        assert 'type' in source
        assert 'enabled' in source

    print(f"✅ sources.yaml valid: {len(enabled_sources)} enabled sources")
    return True

def validate_domains_yaml():
    """domains.yaml 유효성 검사"""
    with open('config/domains.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # STEEPs 카테고리 존재 확인
    assert 'STEEPs' in config

    required_categories = ['S_Social', 'T_Technological', 'E_Economic',
                          'E_Environmental', 'P_Political', 's_spiritual']

    for cat in required_categories:
        assert cat in config['STEEPs'], f"Missing category: {cat}"
        assert len(config['STEEPs'][cat]) > 0, f"Empty keywords for {cat}"

    print(f"✅ domains.yaml valid: {len(config['STEEPs'])} categories")
    return True

if __name__ == "__main__":
    try:
        validate_sources_yaml()
        validate_domains_yaml()
        print("\n✅ All configurations valid!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Configuration error: {e}")
        sys.exit(1)
```

---

## 에러 처리 및 복원력

### 에러 처리 전략

```python
# 1. Rate Limit 에러
class RateLimitError(Exception):
    """API rate limit exceeded"""
    pass

def handle_rate_limit_error(scanner, retry_count):
    """
    Rate limit 에러 처리

    전략:
    1. API 응답 헤더에서 reset 시간 확인
    2. 해당 시간만큼 대기
    3. 재시도 (최대 3회)
    """
    wait_time = scanner.get_rate_limit_reset_time()
    print(f"[RATE_LIMIT] Waiting {wait_time}s before retry...")
    time.sleep(wait_time)

# 2. Timeout 에러
def handle_timeout_error(scanner, retry_count):
    """
    Timeout 에러 처리

    전략:
    1. 첫 시도: 30s timeout
    2. 재시도 1: 60s timeout
    3. 재시도 2: 120s timeout
    """
    new_timeout = scanner.timeout * (2 ** retry_count)
    scanner.timeout = min(new_timeout, 300)  # 최대 5분

# 3. 네트워크 에러
def handle_network_error(scanner, retry_count):
    """
    네트워크 에러 처리

    전략: Exponential backoff (1s, 2s, 4s)
    """
    wait_time = 2 ** retry_count
    print(f"[NETWORK_ERROR] Retrying in {wait_time}s...")
    time.sleep(wait_time)
```

### Fallback 전략

```yaml
fallback_strategy:
  # Critical 소스 실패시
  critical_source_failure:
    action: "halt_workflow"
    notify: true
    log_level: "ERROR"

  # Non-critical 소스 실패시
  non_critical_source_failure:
    action: "skip_and_continue"
    notify: false
    log_level: "WARNING"

  # 모든 소스 실패시
  all_sources_failure:
    action: "use_cached_data"  # 이전 스캔 결과 사용
    max_cache_age: "24_hours"
    notify: true
    log_level: "CRITICAL"
```

---

## 확장성 고려사항

### 새 소스 추가 프로세스

**예시: Google Scholar 추가**

```python
# 1. Scanner 클래스 생성
# scanners/scholar_scanner.py

from .base_scanner import BaseScanner

class GoogleScholarScanner(BaseScanner):
    """Google Scholar via SerpAPI"""

    def scan(self, steeps_domains, days_back=7):
        # SerpAPI 호출 로직
        pass

    def to_standard_format(self, raw_data):
        # Scholar 데이터 → 표준 형식 변환
        pass

# 2. Factory에 등록
# scanners/scanner_factory.py

SCANNER_REGISTRY = {
    'academic': {
        'arXiv': ArXivScanner,
        'Google Scholar': GoogleScholarScanner,  # ← 추가
    }
}

# 3. sources.yaml에 추가
sources:
  - name: "Google Scholar"
    type: "academic"
    enabled: true  # ← 활성화
    api_key_env: "SERPAPI_KEY"
    ...

# 완료! 자동으로 스캔에 포함됨
```

### 확장 포인트

```python
# 1. 새 소스 타입 추가
class RSSScanner(BaseScanner):
    """Generic RSS feed scanner"""
    pass

# 2. 커스텀 필터 추가
class QualityFilter:
    """스캔 결과 품질 필터"""

    def filter(self, signals):
        # 낮은 품질 신호 제거
        return [s for s in signals if s.get('quality_score', 0) > 0.5]

# 3. 데이터 증강 추가
class SignalEnricher:
    """스캔 결과 데이터 증강"""

    def enrich(self, signal):
        # 외부 API로 추가 정보 수집
        signal['citations'] = get_citation_count(signal['id'])
        return signal
```

---

## 테스트 전략

### Unit Tests

**파일**: `env-scanning/tests/test_arxiv_scanner.py`

```python
import pytest
from scanners.arxiv_scanner import ArXivScanner

def test_arxiv_scanner_initialization():
    """arXiv 스캐너 초기화 테스트"""
    config = {
        'name': 'arXiv',
        'type': 'academic',
        'enabled': True,
        'max_results': 20
    }

    scanner = ArXivScanner(config)

    assert scanner.get_name() == 'arXiv'
    assert scanner.is_enabled() == True
    assert scanner.validate_config() == True

def test_arxiv_category_mapping():
    """STEEPs → arXiv 카테고리 매핑 테스트"""
    scanner = ArXivScanner({'name': 'arXiv', 'type': 'academic'})

    assert 'cs.AI' in scanner.CATEGORY_MAPPING['T_Technological']
    assert 'econ.EM' in scanner.CATEGORY_MAPPING['E_Economic']

@pytest.mark.integration
def test_arxiv_real_scan():
    """실제 arXiv 스캔 통합 테스트 (slow)"""
    scanner = ArXivScanner({
        'name': 'arXiv',
        'type': 'academic',
        'max_results': 5  # 빠른 테스트를 위해 5개만
    })

    domains = {'T_Technological': ['AI', 'machine learning']}
    results = scanner.scan(domains, days_back=7)

    assert len(results) > 0
    assert all('id' in r for r in results)
    assert all('title' in r for r in results)
```

### Integration Tests

**파일**: `env-scanning/tests/test_multi_source_integration.py`

```python
def test_multi_source_scan_execution():
    """멀티소스 스캔 통합 테스트"""
    from scripts.run_multi_source_scan import run_scan

    result = run_scan(days_back=7)

    # 메타데이터 검증
    assert 'scan_metadata' in result
    assert result['scan_metadata']['sources_scanned'] > 0
    assert result['scan_metadata']['total_items'] > 0

    # 아이템 검증
    assert 'items' in result
    assert len(result['items']) > 0

    # 표준 형식 검증
    for item in result['items']:
        assert 'id' in item
        assert 'title' in item
        assert 'source' in item
        assert 'preliminary_category' in item
```

### Performance Tests

```python
def test_scan_performance():
    """스캔 성능 테스트"""
    import time

    start = time.time()
    result = run_scan(days_back=7)
    elapsed = time.time() - start

    # 성능 목표: 100개 신호를 30초 이내에 수집
    items_per_second = len(result['items']) / elapsed

    assert items_per_second > 3, "Performance target: >3 items/second"
    assert elapsed < 60, "Should complete within 60 seconds"
```

---

## 구현 순서

### Week 1: 기반 구조 (추천 순서)

```
Day 1-2: 기반 클래스 및 아키텍처
├─ [ ] scanners/ 디렉토리 생성
├─ [ ] base_scanner.py 작성
├─ [ ] scanner_factory.py 작성
└─ [ ] Unit tests 작성

Day 3-4: arXiv Scanner 리팩토링
├─ [ ] arxiv_scanner.py를 BaseScanner 상속 구조로 변경
├─ [ ] to_standard_format() 구현
├─ [ ] Integration tests 작성
└─ [ ] 기존 스크립트와 비교 검증

Day 5: Multi-Source Runner
├─ [ ] run_multi_source_scan.py 작성
├─ [ ] CLI arguments 지원
├─ [ ] 에러 처리 추가
└─ [ ] End-to-end test
```

### Week 2: Orchestrator 통합

```
Day 6-7: Orchestrator 수정
├─ [ ] env-scan-orchestrator.md Step 1.2 업데이트
├─ [ ] Task tool 호출 구조 정의
├─ [ ] 입출력 검증 로직 추가
└─ [ ] 통합 테스트

Day 8-9: 설정 관리
├─ [ ] sources.yaml 업데이트 (arXiv 영구 설정)
├─ [ ] .env.example 작성
├─ [ ] validate_config.py 작성
└─ [ ] 문서화

Day 10: 최종 검증
├─ [ ] 전체 workflow 실행 (arXiv 포함)
├─ [ ] 성능 측정
├─ [ ] 문서 업데이트
└─ [ ] 배포 준비
```

---

## 체크리스트

### 구현 전 확인사항

- [ ] 기존 workflow 철학 이해
- [ ] Multi-source-scanner.md 명세 숙지
- [ ] STEEPs 프레임워크 이해
- [ ] 현재 파일 구조 파악

### 구현 중 확인사항

- [ ] BaseScanner 추상 클래스 올바르게 설계
- [ ] Factory pattern 적절히 적용
- [ ] 설정 기반 동작 (하드코딩 최소화)
- [ ] 에러 처리 완전성
- [ ] 테스트 커버리지 80% 이상

### 구현 후 확인사항

- [ ] 기존 검증 결과와 동일 (90개 논문 수집)
- [ ] 성능 저하 없음 (15초 이내)
- [ ] Orchestrator 통합 성공
- [ ] 전체 workflow 정상 동작
- [ ] 문서화 완료

---

## 예상 결과

### 통합 완료 후

```bash
# 1. 수동 실행 (테스트)
$ cd env-scanning
$ python3 scripts/run_multi_source_scan.py --days-back 7

# 출력:
# ============================================================
# Multi-Source Scanner - Starting
# ============================================================
#
# [INFO] Loaded 1 active scanners
#   - arXiv (academic)
#
# [SCANNING] arXiv...
# [SUCCESS] arXiv: 90 items collected
# [PROGRESS] Total items: 90
#
# ============================================================
# [COMPLETE] Scan finished in 15.1s
# [RESULT] 90 items from 1 sources
# ============================================================
#
# [SAVED] Output written to: raw/daily-scan-2026-01-30.json

# 2. Orchestrator 실행 (프로덕션)
# Orchestrator가 자동으로 Step 1.2에서 실행

# 3. 결과 파일 구조
$ cat raw/daily-scan-2026-01-30.json
{
  "scan_metadata": {
    "date": "2026-01-30",
    "sources_scanned": 1,
    "total_items": 90,
    "execution_time": 15.06,
    "mode": "multi_source"
  },
  "items": [
    {
      "id": "arxiv-2601.20858",
      "title": "When Flores Bloomz Wrong...",
      "source": {...},
      "preliminary_category": "T",
      ...
    }
  ]
}
```

### 시스템 상태

```
System Readiness: 95% → 97% (arXiv 영구 통합 완료)

완료된 기능:
  ✅ arXiv 영구 통합
  ✅ Multi-source 아키텍처
  ✅ 설정 기반 동작
  ✅ 확장 가능 구조
  ✅ 에러 복원력

다음 단계:
  🔄 Google Scholar 추가 (미래)
  🔄 Policy RSS 추가 (미래)
  🔄 LLM 분류 통합
```

---

## 승인 필요 사항

### 설계 결정 확인

1. **아키텍처 선택**: Multi-Source Scanner 확장 (Option A) ✅
2. **파일 구조**: `scanners/` 디렉토리 신규 생성 ✅
3. **설정 관리**: `sources.yaml`에 arXiv 영구 설정 ✅
4. **에러 처리**: Critical/Non-critical 구분 전략 ✅
5. **확장성**: Factory pattern + BaseScanner 상속 ✅

### 구현 범위 확인

**Phase 1 (필수)**:
- Base scanner 구조
- arXiv scanner 리팩토링
- Multi-source runner

**Phase 2 (선택)**:
- Google Scholar 추가 (미래 확장)
- Monitoring 시스템 (미래 확장)

### 사용자 승인 필요 질문

1. **설계 방향성 승인**: 위 설계안 전체 승인?
2. **구현 범위**: Phase 1만 진행? Phase 2도 포함?
3. **파일 구조**: `scanners/` 디렉토리 구조 승인?
4. **설정 관리**: `sources.yaml` 형식 승인?
5. **기타 요구사항**: 추가 기능이나 수정 필요한 부분?

---

**설계 계획 작성 완료**
**다음 단계**: 사용자 승인 후 구현 시작
**예상 구현 기간**: 1-2주 (Phase 1 기준)
**시스템 준비도**: 97% 예상 (통합 완료 후)
