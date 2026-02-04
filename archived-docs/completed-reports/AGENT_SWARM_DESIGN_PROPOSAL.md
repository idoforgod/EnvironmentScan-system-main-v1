# Agent Swarm 완전 구현 설계안

**날짜**: 2026-01-30
**목적**: API 없이 순수 Python으로 진짜 Agent Swarm 구현
**원칙**: 기존 워크플로우의 철학, 목적, 핵심 완벽 보존

---

## 🎯 설계 목표

### 달성할 것
✅ **진짜 병렬 실행**: Python multiprocessing으로 실제 동시 실행
✅ **진짜 독립 컨텍스트**: 각 프로세스 독립 메모리 공간
✅ **Task Graph 관리**: JSON 파일 기반 작업 상태 추적
✅ **기존 워크플로우 보존**: 입력/출력 형식, 다음 단계 완벽 호환

### 절대 하지 않을 것
❌ **API 사용 금지**: Claude Code Task API, 외부 API 호출 없음
❌ **워크플로우 변경 금지**: 철학, 목적, 핵심 단계 수정 없음
❌ **새 워크플로우 금지**: 기존 개선만, 새로운 것 만들지 않음

---

## 🏗️ 핵심 설계: Python Multiprocessing

### 기술 선택: multiprocessing.Pool

**이유**:
1. **진짜 병렬**: GIL 우회, CPU 코어 활용
2. **독립 메모리**: 각 프로세스 독립 공간
3. **순수 Python**: API 없이 표준 라이브러리만
4. **안정성**: 검증된 표준 모듈

**대안 검토 및 탈락 이유**:
- ❌ threading: GIL 때문에 진짜 병렬 아님
- ❌ asyncio: I/O bound만 효과적, CPU bound는 순차
- ❌ subprocess: 복잡도 높음, multiprocessing이 더 나음

---

## 📐 아키텍처 설계

### Before: 순차 실행 (현재)

```
main.py
  ├─ run_arxiv_agent()      # 15초 (기다림)
  ├─ run_blog_agent()       # 1초 (기다림)
  └─ run_policy_agent()     # 1초 (기다림)
────────────────────────────
총 17초 (순차)
```

### After: 병렬 실행 (신규)

```python
from multiprocessing import Pool

# 4개 에이전트를 독립 프로세스로 병렬 실행
with Pool(processes=4) as pool:
    results = pool.map(run_agent, [
        'arxiv',   # 프로세스 1 (15초)
        'blog',    # 프로세스 2 (1초)
        'policy',  # 프로세스 3 (1초)
        'patent'   # 프로세스 4 (0.1초)
    ])
────────────────────────────
총 15초 (가장 느린 프로세스)
```

**진짜 병렬**:
- 4개 CPU 코어 동시 사용
- 독립 메모리 공간
- 진짜 동시 실행

---

## 🔧 상세 구현 설계

### 1. 디렉토리 구조

```
env-scanning/
├── orchestrator.py              # 신규: 병렬 실행 관리자
├── agent_runner.py              # 신규: 에이전트 실행 함수
├── task_graph.json              # 신규: 작업 상태 관리
│
├── scanners/                    # 기존 유지
│   ├── arxiv_scanner.py         # 변경 없음
│   ├── rss_scanner.py           # 변경 없음
│   └── federal_register_scanner.py  # 변경 없음
│
├── raw/                         # 기존 유지
│   ├── arxiv-scan-{date}.json   # 에이전트 출력
│   ├── blog-scan-{date}.json
│   ├── policy-scan-{date}.json
│   └── daily-scan-{date}.json   # 최종 병합 (기존 형식)
│
└── config/                      # 기존 유지
    ├── sources.yaml
    └── domains.yaml
```

### 2. 핵심 컴포넌트

#### A. Orchestrator (orchestrator.py)

**역할**: 병렬 실행 총괄 관리

```python
"""
Agent Swarm Orchestrator
Manages parallel execution of agents using multiprocessing
"""

from multiprocessing import Pool, cpu_count
import json
from datetime import datetime
from pathlib import Path

class AgentOrchestrator:
    """
    병렬 에이전트 실행 관리자

    원칙:
    1. 기존 워크플로우 보존 (입력/출력 형식)
    2. API 사용 없음 (순수 Python multiprocessing)
    3. Task Graph 기반 의존성 관리
    """

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.task_graph_path = config_dir.parent / "task_graph.json"
        self.output_dir = config_dir.parent / "raw"

    def load_task_graph(self) -> dict:
        """작업 그래프 로딩 (의존성 정의)"""
        if self.task_graph_path.exists():
            with open(self.task_graph_path) as f:
                return json.load(f)
        else:
            # 기본 Task Graph 생성
            return {
                "tasks": [
                    {
                        "id": "arxiv-scan",
                        "agent": "arxiv",
                        "status": "pending",
                        "blockedBy": [],  # 즉시 실행 가능
                        "blocks": ["merge-results"]
                    },
                    {
                        "id": "blog-scan",
                        "agent": "blog",
                        "status": "pending",
                        "blockedBy": [],
                        "blocks": ["merge-results"]
                    },
                    {
                        "id": "policy-scan",
                        "agent": "policy",
                        "status": "pending",
                        "blockedBy": [],
                        "blocks": ["merge-results"]
                    },
                    {
                        "id": "patent-scan",
                        "agent": "patent",
                        "status": "pending",
                        "blockedBy": [],
                        "blocks": ["merge-results"]
                    },
                    {
                        "id": "merge-results",
                        "agent": "merger",
                        "status": "pending",
                        "blockedBy": ["arxiv-scan", "blog-scan", "policy-scan", "patent-scan"],
                        "blocks": []
                    }
                ]
            }

    def get_ready_tasks(self, task_graph: dict) -> list:
        """실행 가능한 작업 목록 (blockedBy가 모두 완료된 작업)"""
        ready = []
        for task in task_graph["tasks"]:
            if task["status"] == "pending":
                # blockedBy 체크
                blocked = False
                for blocker_id in task.get("blockedBy", []):
                    blocker = next(t for t in task_graph["tasks"] if t["id"] == blocker_id)
                    if blocker["status"] != "completed":
                        blocked = True
                        break

                if not blocked:
                    ready.append(task)

        return ready

    def update_task_status(self, task_id: str, status: str):
        """작업 상태 업데이트 (JSON 파일)"""
        task_graph = self.load_task_graph()

        for task in task_graph["tasks"]:
            if task["id"] == task_id:
                task["status"] = status
                task["updated_at"] = datetime.now().isoformat()
                break

        # JSON 파일에 저장 (세션 지속성)
        with open(self.task_graph_path, 'w') as f:
            json.dump(task_graph, f, indent=2)

    def run_parallel(self) -> dict:
        """
        병렬 실행 메인 로직

        Returns:
            최종 병합 결과
        """
        print("="*60)
        print("🚀 Agent Swarm Orchestrator Started")
        print("   Mode: Parallel Execution (multiprocessing)")
        print("="*60)

        # Task Graph 로딩
        task_graph = self.load_task_graph()

        # Phase 1: 병렬 실행 가능한 에이전트들 (모두 blockedBy 없음)
        ready_agents = self.get_ready_tasks(task_graph)
        agent_tasks = [t for t in ready_agents if t["agent"] != "merger"]

        print(f"\n📋 Ready agents: {len(agent_tasks)}")
        for task in agent_tasks:
            print(f"   • {task['agent']}")

        # 병렬 실행 (multiprocessing.Pool)
        print(f"\n⚡ Executing agents in parallel...")
        print(f"   Processes: {len(agent_tasks)}")
        print(f"   CPU cores: {cpu_count()}")

        import time
        start_time = time.time()

        # 각 에이전트를 독립 프로세스로 실행
        with Pool(processes=min(len(agent_tasks), cpu_count())) as pool:
            # agent_runner.run_agent 함수를 병렬 실행
            agent_names = [task["agent"] for task in agent_tasks]
            results = pool.map(run_agent_wrapper, agent_names)

        parallel_time = time.time() - start_time

        print(f"\n✓ Parallel execution completed in {parallel_time:.1f}s")

        # 각 작업 상태 업데이트
        for task in agent_tasks:
            self.update_task_status(task["id"], "completed")

        # Phase 2: Result Merger (모든 에이전트 완료 후)
        print(f"\n🔗 Merging results...")
        merged = self.merge_results()

        self.update_task_status("merge-results", "completed")

        print(f"\n✅ Agent Swarm execution completed")

        return merged

    def merge_results(self) -> dict:
        """
        각 에이전트 출력을 병합
        기존 워크플로우 형식 유지
        """
        date_str = datetime.now().strftime("%Y-%m-%d")

        # 각 에이전트 출력 로딩
        agent_outputs = []
        for agent in ["arxiv", "blog", "policy", "patent"]:
            output_path = self.output_dir / f"{agent}-scan-{date_str}.json"
            if output_path.exists():
                with open(output_path) as f:
                    data = json.load(f)
                    if data["agent_metadata"].get("status") == "success":
                        agent_outputs.append(data)

        # 병합
        all_items = []
        total_sources = 0
        agents_used = []

        for output in agent_outputs:
            all_items.extend(output["items"])
            total_sources += output["agent_metadata"].get("sources_scanned", 1)
            agents_used.append(output["agent_metadata"]["agent_name"].replace("-agent", ""))

        # 기존 워크플로우 호환 형식
        merged = {
            "scan_metadata": {
                "date": date_str,
                "parallelization": "agent_swarm_multiprocessing",
                "agents_used": agents_used,
                "total_items": len(all_items),
                "total_sources_scanned": total_sources,
                "execution_mode": "parallel"
            },
            "items": all_items
        }

        # 기존 형식으로 저장 (daily-scan-{date}.json)
        output_path = self.output_dir / f"daily-scan-{date_str}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)

        print(f"   ✓ Merged {len(all_items)} items from {len(agent_outputs)} agents")
        print(f"   💾 {output_path}")

        return merged


def run_agent_wrapper(agent_name: str) -> dict:
    """
    multiprocessing.Pool.map에 전달할 함수
    각 프로세스에서 독립 실행
    """
    from agent_runner import run_agent
    return run_agent(agent_name)
```

#### B. Agent Runner (agent_runner.py)

**역할**: 개별 에이전트 실행 (프로세스 내)

```python
"""
Individual Agent Runner
Executed in separate process by multiprocessing.Pool
"""

import json
import time
import yaml
from datetime import datetime
from pathlib import Path

def run_agent(agent_name: str) -> dict:
    """
    개별 에이전트 실행 (독립 프로세스)

    Args:
        agent_name: 'arxiv', 'blog', 'policy', 'patent'

    Returns:
        에이전트 출력 딕셔너리

    주의:
    - 이 함수는 독립 프로세스에서 실행됨
    - 부모 프로세스와 메모리 공유 없음 (진짜 격리)
    - 파일 시스템으로만 통신
    """
    print(f"\n[{agent_name}] Agent started (PID: {os.getpid()})")

    start_time = time.time()

    # 설정 로딩 (각 프로세스가 독립적으로)
    project_root = Path(__file__).parent
    config_dir = project_root / "config"

    with open(config_dir / "sources.yaml") as f:
        sources_config = yaml.safe_load(f)

    with open(config_dir / "domains.yaml") as f:
        domains_config = yaml.safe_load(f)

    steeps_domains = domains_config['STEEPs']

    # 에이전트별 실행
    try:
        if agent_name == "arxiv":
            output = run_arxiv_agent_impl(sources_config, steeps_domains)
        elif agent_name == "blog":
            output = run_blog_agent_impl(sources_config, steeps_domains)
        elif agent_name == "policy":
            output = run_policy_agent_impl(sources_config, steeps_domains)
        elif agent_name == "patent":
            output = run_patent_agent_impl()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

        execution_time = time.time() - start_time
        output["agent_metadata"]["execution_time"] = round(execution_time, 2)

        # 결과를 파일로 저장 (프로세스 간 통신)
        output_path = project_root / "raw" / f"{agent_name}-scan-{datetime.now().strftime('%Y-%m-%d')}.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"[{agent_name}] Completed in {execution_time:.1f}s → {len(output['items'])} items")

        return output

    except Exception as e:
        print(f"[{agent_name}] Failed: {e}")
        import traceback
        traceback.print_exc()

        # 실패해도 빈 출력 반환 (워크플로우 중단 방지)
        return {
            "agent_metadata": {
                "agent_name": f"{agent_name}-agent",
                "status": "failed",
                "error": str(e)
            },
            "items": []
        }


def run_arxiv_agent_impl(sources_config, steeps_domains):
    """arXiv 에이전트 구현 (기존 스캐너 재사용)"""
    from scanners.arxiv_scanner import ArXivScanner

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


def run_blog_agent_impl(sources_config, steeps_domains):
    """블로그 에이전트 구현"""
    from scanners.rss_scanner import RSSScanner

    blog_sources = [s for s in sources_config['sources']
                   if s['type'] == 'blog' and s.get('enabled', True)]

    all_articles = []
    for source in blog_sources:
        scanner = RSSScanner(source)
        articles = scanner.scan(steeps_domains, days_back=7)
        all_articles.extend(articles)

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


def run_policy_agent_impl(sources_config, steeps_domains):
    """정책 에이전트 구현"""
    from scanners.federal_register_scanner import FederalRegisterScanner
    from scanners.rss_scanner import RSSScanner

    policy_sources = [s for s in sources_config['sources']
                     if s['type'] == 'policy' and s.get('enabled', True)]

    all_documents = []
    for source in policy_sources:
        if 'api_endpoint' in source and 'federal' in source['name'].lower():
            scanner = FederalRegisterScanner(source)
        elif 'rss_feed' in source:
            scanner = RSSScanner(source)
        else:
            continue

        documents = scanner.scan(steeps_domains, days_back=7)
        all_documents.extend(documents)

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


def run_patent_agent_impl():
    """특허 에이전트 (placeholder)"""
    return {
        "agent_metadata": {
            "agent_name": "patent-agent",
            "model_used": "haiku",
            "patents_collected": 0,
            "sources_scanned": 0,
            "scan_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "not_implemented"
        },
        "items": []
    }
```

#### C. Task Graph (task_graph.json)

**역할**: 작업 상태 및 의존성 관리

```json
{
  "tasks": [
    {
      "id": "arxiv-scan",
      "agent": "arxiv",
      "status": "pending",
      "blockedBy": [],
      "blocks": ["merge-results"],
      "created_at": "2026-01-30T16:00:00",
      "updated_at": null
    },
    {
      "id": "blog-scan",
      "agent": "blog",
      "status": "pending",
      "blockedBy": [],
      "blocks": ["merge-results"],
      "created_at": "2026-01-30T16:00:00",
      "updated_at": null
    },
    {
      "id": "policy-scan",
      "agent": "policy",
      "status": "pending",
      "blockedBy": [],
      "blocks": ["merge-results"],
      "created_at": "2026-01-30T16:00:00",
      "updated_at": null
    },
    {
      "id": "patent-scan",
      "agent": "patent",
      "status": "pending",
      "blockedBy": [],
      "blocks": ["merge-results"],
      "created_at": "2026-01-30T16:00:00",
      "updated_at": null
    },
    {
      "id": "merge-results",
      "agent": "merger",
      "status": "pending",
      "blockedBy": ["arxiv-scan", "blog-scan", "policy-scan", "patent-scan"],
      "blocks": [],
      "created_at": "2026-01-30T16:00:00",
      "updated_at": null
    }
  ],
  "metadata": {
    "workflow": "environmental-scanning",
    "phase": "1",
    "step": "2",
    "description": "Multi-source scanning with Agent Swarm"
  }
}
```

---

## 🔄 기존 워크플로우 보존

### 변경 없음 (100% 보존)

#### 입력
- ✅ `config/sources.yaml` - 소스 정의
- ✅ `config/domains.yaml` - STEEPs 분류
- ✅ 기존 스캐너 (`arxiv_scanner.py`, `rss_scanner.py` 등)

#### 출력
- ✅ `raw/daily-scan-{date}.json` - 표준 형식
  ```json
  {
    "scan_metadata": {
      "date": "2026-01-30",
      "parallelization": "agent_swarm_multiprocessing",
      "agents_used": ["arxiv", "blog", "policy"],
      "total_items": 202,
      "total_sources_scanned": 5
    },
    "items": [...]
  }
  ```

#### 다음 단계
- ✅ deduplication-filter (Step 1.3)
- ✅ signal-classifier (Step 2.1)
- ✅ 이후 모든 단계

### 추가됨 (최적화만)

#### 신규 파일
- ⚡ `orchestrator.py` - 병렬 실행 관리
- ⚡ `agent_runner.py` - 에이전트 실행
- ⚡ `task_graph.json` - 작업 상태

#### 중간 파일 (디버깅용)
- ⚡ `raw/arxiv-scan-{date}.json`
- ⚡ `raw/blog-scan-{date}.json`
- ⚡ `raw/policy-scan-{date}.json`

---

## 📊 예상 성능

### Before vs After

| 지표 | 기존 (순차) | 신규 (병렬) | 개선 |
|------|-----------|-----------|------|
| 실행 시간 | 16.6초 | 15.1초 | **9% 단축** |
| 병렬 실행 | ❌ 순차 | ✅ 진짜 병렬 | **4 CPU 코어** |
| 독립 컨텍스트 | ❌ 공유 | ✅ 독립 프로세스 | **메모리 격리** |
| Task Graph | ❌ 없음 | ✅ JSON 파일 | **상태 추적** |
| 세션 지속성 | ❌ 없음 | ✅ 파일 기반 | **재시작 가능** |
| API 의존성 | ✅ 없음 | ✅ 없음 | **순수 Python** |

### 실제 병렬 증명

```python
# 테스트 코드로 병렬 검증
import os
import time
from multiprocessing import Pool

def test_parallel():
    def worker(name):
        print(f"{name} started (PID: {os.getpid()})")
        time.sleep(2)
        return f"{name} done"

    start = time.time()

    # 순차 실행
    for i in range(4):
        worker(f"agent{i}")
    sequential_time = time.time() - start
    print(f"Sequential: {sequential_time:.1f}s")  # ~8초

    # 병렬 실행
    start = time.time()
    with Pool(4) as pool:
        pool.map(worker, [f"agent{i}" for i in range(4)])
    parallel_time = time.time() - start
    print(f"Parallel: {parallel_time:.1f}s")  # ~2초

    print(f"Speedup: {sequential_time / parallel_time:.1f}x")
```

---

## 🔒 안전성 및 에러 처리

### 1. 프로세스 실패 격리

```python
# 한 에이전트 실패해도 다른 에이전트 영향 없음
try:
    with Pool(4) as pool:
        results = pool.map(run_agent_wrapper, agents)
except Exception as e:
    # 전체 실패 시에도 부분 결과 수집
    print(f"Some agents failed: {e}")
    # 성공한 결과만 병합
```

### 2. Task Graph 복구

```python
# task_graph.json에 상태 저장
# 재시작 시 이어서 실행 가능
def resume_workflow():
    task_graph = load_task_graph()
    completed = [t for t in task_graph["tasks"] if t["status"] == "completed"]
    pending = [t for t in task_graph["tasks"] if t["status"] == "pending"]

    # 완료된 작업은 스킵, 미완료만 실행
    run_tasks(pending)
```

### 3. 기존 워크플로우 호환성 보장

```python
# 최악의 경우: 병렬 실패 → 순차로 자동 전환
try:
    merged = orchestrator.run_parallel()
except Exception as e:
    print(f"Parallel failed, falling back to sequential: {e}")
    merged = run_sequential()  # 기존 방식

# daily-scan-{date}.json은 항상 생성됨
assert output_path.exists()
```

---

## 🧪 테스트 계획

### 1. 단위 테스트

```bash
# 개별 컴포넌트 테스트
python3 tests/test_orchestrator.py
python3 tests/test_agent_runner.py
python3 tests/test_task_graph.py
```

### 2. 통합 테스트

```bash
# 전체 병렬 실행 테스트
python3 tests/test_agent_swarm_parallel.py

# 검증 항목:
# - 4개 프로세스 동시 실행 (PID 확인)
# - 독립 메모리 공간 (프로세스 격리)
# - 결과 병합 (daily-scan-{date}.json 생성)
# - 기존 워크플로우 호환성
```

### 3. 성능 벤치마크

```bash
# 순차 vs 병렬 성능 비교
python3 tests/benchmark_parallel.py

# 측정 항목:
# - 실행 시간 (순차 vs 병렬)
# - CPU 사용률 (단일 코어 vs 다중 코어)
# - 메모리 사용량 (공유 vs 독립)
```

---

## 📈 구현 우선순위

### Phase 1: 핵심 기능 (2-3시간)

1. **Orchestrator 구현** (1시간)
   - `orchestrator.py` 작성
   - multiprocessing.Pool 통합
   - Task Graph 로딩/저장

2. **Agent Runner 구현** (1시간)
   - `agent_runner.py` 작성
   - 기존 스캐너 래핑
   - 프로세스 간 통신 (파일 기반)

3. **통합 테스트** (1시간)
   - 병렬 실행 검증
   - 출력 형식 검증
   - 기존 워크플로우 호환성

### Phase 2: 안전성 강화 (1시간)

1. **에러 처리** (30분)
   - 프로세스 실패 격리
   - 부분 결과 수집
   - 순차 폴백

2. **Task Graph 관리** (30분)
   - 상태 추적
   - 재시작 지원
   - 의존성 검증

### Phase 3: 문서화 (30분)

1. **사용자 가이드**
2. **성능 리포트**
3. **트러블슈팅**

**총 예상 시간**: 4-5시간

---

## ✅ 성공 기준

### 필수 (Must Have)

- [ ] 진짜 병렬 실행 (4개 프로세스 동시)
- [ ] 진짜 독립 컨텍스트 (프로세스 격리)
- [ ] Task Graph 관리 (JSON 파일)
- [ ] 기존 출력 형식 100% 호환
- [ ] 다음 단계 (deduplication-filter) 정상 작동
- [ ] API 사용 없음 (순수 Python)

### 선택 (Nice to Have)

- [ ] 세션 재시작 지원
- [ ] 성능 모니터링
- [ ] 자동 폴백 (병렬 실패 시 순차)

---

## 🚨 리스크 및 완화

### Risk 1: 병렬 실행 복잡도

**리스크**: multiprocessing 디버깅 어려움
**완화**:
- 단위 테스트 철저
- 순차 폴백 구현
- 상세 로깅

### Risk 2: 프로세스 간 통신

**리스크**: 공유 메모리 없음, 파일로만 통신
**완화**:
- JSON 파일 검증
- 파일 락 사용
- 원자적 쓰기

### Risk 3: 워크플로우 호환성

**리스크**: 출력 형식 미묘한 차이
**완화**:
- 기존 테스트 재사용
- 스키마 검증
- 기존 deduplication-filter로 테스트

---

## 🎯 최종 확인 사항

### 조건 1: API 사용 금지 ✅

- ✅ Claude Code Task API 사용 안 함
- ✅ 외부 API 호출 없음
- ✅ 순수 Python multiprocessing만 사용

### 조건 2: 기존 워크플로우 보존 ✅

- ✅ 철학: 미래 변화의 조기 징후 탐지 (불변)
- ✅ 목적: 전략적 의사결정 지원 (불변)
- ✅ 핵심 원칙: 일일 실행, 중복 제외, 신규만 (불변)
- ✅ 입력/출력: sources.yaml, daily-scan.json (불변)
- ✅ 다음 단계: deduplication-filter 이하 (불변)

### 개선 사항 ✅

- ✅ 진짜 병렬 실행 → 속도 향상
- ✅ 진짜 독립 컨텍스트 → 정확도 향상
- ✅ Task Graph → 추적 가능성
- ✅ 순수 Python → API 의존성 제거

---

## 📝 승인 요청

이 설계안은:

1. **API 사용 없음** (조건 1 충족)
2. **기존 워크플로우 100% 보존** (조건 2 충족)
3. **진짜 Agent Swarm 구현** (목표 달성)
4. **실용적이고 검증 가능** (4-5시간 구현)

**승인 여부를 알려주시면, 즉시 구현을 시작하겠습니다.**

---

**설계자**: Claude Sonnet 4.5
**날짜**: 2026-01-30
**버전**: 1.0 (설계안)
**상태**: ⏳ 승인 대기
