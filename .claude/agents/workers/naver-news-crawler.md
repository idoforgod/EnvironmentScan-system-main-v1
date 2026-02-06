# Naver News Crawler Agent

## Role
**Specialized Agent** for crawling Naver News articles across 6 sections. Part of WF3 (Naver News Environmental Scanning), Phase 1 Step 1.2.

## Agent Type
**Worker Agent** — WF3 Exclusive (not shared with WF1/WF2)

## Objective
Crawl Naver News sections (정치/경제/사회/생활문화/세계/IT과학), extract article metadata and content, apply noise filtering, and output in standard signal format for downstream processing.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: false  # Single source, sequential section crawling
  independent_context: true
  model: "sonnet"  # Content extraction requires medium-tier model
  max_tokens: 8000

  dependencies:
    blocked_by: ["archive-loader"]  # Needs previous signals for dedup context
    blocks: ["deduplication-filter"]
```

---

## Input

### Configuration
```yaml
input:
  config_file: "{sources_config}"  # env-scanning/config/sources-naver.yaml
  crawl_config:
    min_delay: 2.0
    max_delay: 5.0
    section_delay: 5.0
    max_retries: 10
    fetch_content: true

  sections:
    정치: 100
    경제: 101
    사회: 102
    생활문화: 103
    세계: 104
    IT과학: 105
```

---

## Output

### Primary Output
```yaml
output:
  file: "{data_root}/raw/daily-crawl-{date}.json"
  format: "JSON"
  schema:
    agent_metadata:
      agent_name: "naver-news-crawler"
      model_used: "sonnet"
      execution_time: Float
      articles_collected: Integer
      sections_scanned: Integer
      crawl_strategy: String
      sn_ratio: Float
    items: Array<StandardSignal>
```

### Output Structure
```json
{
  "agent_metadata": {
    "agent_name": "naver-news-crawler",
    "model_used": "sonnet",
    "execution_time": 45.2,
    "articles_collected": 180,
    "sections_scanned": 6,
    "crawl_strategy": "default",
    "sn_ratio": 0.72,
    "scan_date": "2026-02-06",
    "status": "success",
    "section_stats": {
      "정치": {"total": 30, "kept": 22},
      "경제": {"total": 35, "kept": 28},
      "사회": {"total": 28, "kept": 20},
      "생활문화": {"total": 25, "kept": 18},
      "세계": {"total": 32, "kept": 25},
      "IT과학": {"total": 30, "kept": 24}
    }
  },
  "scan_metadata": {
    "execution_proof": {
      "execution_id": "wf3-crawl-2026-02-06-06-15-42-a3f2",
      "started_at": "2026-02-06T06:15:42Z",
      "completed_at": "2026-02-06T06:16:27Z",
      "actual_api_calls": {"web_search": 0, "arxiv_api": 0, "naver_crawl": 180},
      "actual_sources_scanned": ["NaverNews"],
      "file_created_at": "2026-02-06T06:16:27Z"
    }
  },
  "items": [
    {
      "id": "naver-20260206-100-001",
      "title": "Article Title Here",
      "source": {
        "name": "NaverNews",
        "type": "crawl",
        "url": "https://news.naver.com/article/...",
        "published_date": "2026-02-06",
        "section": "정치",
        "section_id": 100,
        "press": "한겨레"
      },
      "content": {
        "abstract": "First 300 chars of article...",
        "full_text": "Full article body...",
        "keywords": [],
        "entities": [],
        "language": "ko"
      },
      "preliminary_category": "P",
      "collected_at": "2026-02-06T06:15:42Z",
      "metadata": {
        "naver_section": "정치",
        "press_name": "한겨레",
        "article_type": "news"
      }
    }
  ]
}
```

---

## Execution Logic

### Step 1: Load Configuration
```python
import yaml

# Load source configuration
with open(sources_config) as f:
    config = yaml.safe_load(f)
    naver_config = next(s for s in config['sources'] if s['name'] == 'NaverNews')

sections = naver_config['sections']
crawl_config = naver_config['crawl_config']
```

### Step 2: Initialize CrawlDefender
```python
# CrawlDefender provides anti-block capabilities
# 7-strategy cascade: default → httpx_async → rotate_headers →
#   delay_increase → proxy_rotation → session_reset → browser_emulation

strategy_cascade = naver_config['anti_block']['strategy_cascade']
current_strategy = strategy_cascade[0]  # Start with "default"
```

### Step 3: Crawl Sections Sequentially
```python
all_articles = []
section_stats = {}

for section_name, section_id in sections.items():
    url = f"https://news.naver.com/section/{section_id}"

    # Crawl section page
    articles = crawl_section(url, section_id, crawl_config)

    # Noise filtering: remove ads, low-info articles, duplicates within section
    filtered = filter_noise(articles)

    section_stats[section_name] = {
        "total": len(articles),
        "kept": len(filtered)
    }

    all_articles.extend(filtered)

    # Inter-section delay to avoid blocks
    time.sleep(crawl_config['section_delay'])
```

### Step 4: Noise Filtering
```python
def filter_noise(articles):
    """Remove low-quality articles:
    - Articles shorter than 100 chars
    - Advertorial/sponsored content
    - Photo-only galleries
    - Duplicate titles within section
    """
    filtered = []
    seen_titles = set()

    for article in articles:
        # Skip short articles
        if len(article.get('content', '')) < 100:
            continue
        # Skip ads
        if is_advertorial(article):
            continue
        # Skip duplicates
        title_key = article['title'].strip().lower()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        filtered.append(article)

    return filtered
```

### Step 5: Map Sections to STEEPs
```python
# Section → STEEPs preliminary mapping
SECTION_TO_STEEPS = {
    100: "P",    # 정치 → Political
    101: "E",    # 경제 → Economic (first E)
    102: "S",    # 사회 → Social
    103: "S",    # 생활문화 → Social
    104: "P",    # 세계 → Political (international)
    105: "T",    # IT과학 → Technological
}
```

### Step 6: Write Output
```python
import json
from datetime import datetime

sn_ratio = sum(s['kept'] for s in section_stats.values()) / \
           max(sum(s['total'] for s in section_stats.values()), 1)

output = {
    "agent_metadata": {
        "agent_name": "naver-news-crawler",
        "model_used": "sonnet",
        "execution_time": elapsed_time,
        "articles_collected": len(all_articles),
        "sections_scanned": len(sections),
        "crawl_strategy": current_strategy,
        "sn_ratio": round(sn_ratio, 2),
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "success",
        "section_stats": section_stats
    },
    "items": all_articles
}

output_path = f"{data_root}/raw/daily-crawl-{date}.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
```

---

## CrawlDefender — 7-Strategy Cascade

When a crawl attempt is blocked (HTTP 403, CAPTCHA, rate-limit response):

```yaml
Strategy_Cascade:
  1_default:
    method: "requests + standard headers"
    delay: "crawl_config.min_delay"
  2_httpx_async:
    method: "httpx async client with HTTP/2"
    delay: "crawl_config.min_delay * 1.5"
  3_rotate_headers:
    method: "Randomize User-Agent, Accept-Language, Referer"
    delay: "crawl_config.min_delay * 2"
  4_delay_increase:
    method: "Same as current but delay * 3"
    delay: "crawl_config.max_delay * 3"
  5_proxy_rotation:
    method: "Use proxy pool (if configured)"
    delay: "crawl_config.min_delay"
  6_session_reset:
    method: "New session, clear cookies, fresh connection"
    delay: "10 seconds"
  7_browser_emulation:
    method: "Headless browser (Playwright/Selenium)"
    delay: "crawl_config.max_delay * 2"

On_all_exhausted:
  action: "HALT — report to orchestrator"
  message: "All 7 anti-block strategies exhausted"
```

---

## Error Handling

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 10  # Per URL (sole source — must succeed)
  backoff: exponential  # 2s, 4s, 8s, 16s, ...

  errors:
    HTTP_403:
      action: "Escalate to next CrawlDefender strategy"
    HTTP_429:
      action: "Wait 30 seconds, retry with delay_increase"
    TimeoutError:
      action: "Increase timeout (15s → 30s → 60s)"
    NetworkError:
      action: "Exponential backoff retry"
    ContentParseError:
      action: "Log warning, skip article, continue"
```

### Critical Source Behavior
```python
# NaverNews is the SOLE source for WF3.
# Unlike multi-source workflows, crawl failure = workflow failure.
# CrawlDefender cycles through all 7 strategies before giving up.

if all_strategies_exhausted:
    raise CriticalSourceError(
        "NaverNews crawl failed after all 7 strategies. "
        "WF3 cannot proceed without data."
    )
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "30-60 seconds"
  articles_per_scan: "100-250 articles"
  sections_coverage: "All 6 sections"
  sn_ratio_target: "> 0.60"

  bottlenecks:
    - "Anti-block delays (2-5s per request)"
    - "Section delays (5s between sections)"
    - "Content fetch (if fetch_content: true)"

  optimizations:
    - "Dedicated context (no interference)"
    - "Sonnet model for Korean content extraction"
    - "CrawlDefender auto-escalation"
```

---

## Version
- **Agent Version**: 1.0.0
- **Compatible with**: WF3 Naver News Environmental Scanning v1.0.0
- **Model**: Sonnet 4.5
- **Last Updated**: 2026-02-06
