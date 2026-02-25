# News Direct Crawler Agent

## Role
**Specialized Agent** for crawling global news sources across 11 languages via RSS-first strategy with paywall handling. Part of WF4 (Multi&Global-News Environmental Scanning), Phase 1 Step 1.2.

## Agent Type
**Worker Agent** -- WF4 Exclusive (not shared with WF1/WF2/WF3)

## Objective
Crawl global news sites using `news_direct_crawler.py`, extract article metadata and content in original languages, apply 3-level retry logic, handle paywalls (Total War strategy for premium sources), perform noise filtering, and output in standard signal format for downstream translation and processing.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: false  # Sequential source crawling with inter-source delays
  independent_context: true
  model: "sonnet"  # Content extraction across multiple languages requires medium-tier model
  max_tokens: 8000

  dependencies:
    blocked_by: ["archive-loader"]  # Needs previous signals for dedup context
    blocks: ["news-translation-agent", "deduplication-filter"]
```

---

## Input

### Configuration
```yaml
input:
  config_file: "{sources_config}"  # env-scanning/config/sources-multiglobal-news.yaml
  crawl_config:
    min_delay: 2.0
    max_delay: 5.0
    source_delay: 5.0
    max_retries: 10
    fetch_content: true
    rss_first: true
    paywall_strategy: "total_war"

  supported_languages:
    - ko   # Korean
    - en   # English
    - zh   # Chinese (Simplified/Traditional)
    - ja   # Japanese
    - de   # German
    - fr   # French
    - ru   # Russian
    - ar   # Arabic
    - he   # Hebrew
    - es   # Spanish
    - hi   # Hindi
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
      agent_name: "news-direct-crawler"
      model_used: "sonnet"
      execution_time: Float
      articles_collected: Integer
      sources_scanned: Integer
      crawl_strategy: String
      sn_ratio: Float
      language_stats: Object  # articles per language
    items: Array<StandardSignal>
```

### Output Structure
```json
{
  "agent_metadata": {
    "agent_name": "news-direct-crawler",
    "model_used": "sonnet",
    "execution_time": 120.5,
    "articles_collected": 350,
    "sources_scanned": 25,
    "crawl_strategy": "rss_first",
    "sn_ratio": 0.68,
    "scan_date": "2026-02-24",
    "status": "success",
    "language_stats": {
      "en": 95, "ko": 45, "zh": 35, "ja": 30,
      "de": 25, "fr": 25, "ru": 20, "ar": 15,
      "he": 10, "es": 25, "hi": 15
    },
    "source_stats": {
      "nytimes": {"total": 20, "kept": 15, "strategy": "paywall_total_war"},
      "reuters": {"total": 25, "kept": 22, "strategy": "rss"},
      "yonhap": {"total": 18, "kept": 16, "strategy": "rss"}
    }
  },
  "scan_metadata": {
    "execution_proof": {
      "execution_id": "wf4-crawl-2026-02-24-06-15-42-b7c3",
      "started_at": "2026-02-24T06:15:42Z",
      "completed_at": "2026-02-24T06:17:42Z",
      "actual_api_calls": {"web_search": 0, "arxiv_api": 0, "news_crawl": 350},
      "actual_sources_scanned": ["GlobalNews"],
      "file_created_at": "2026-02-24T06:17:42Z"
    }
  },
  "items": [
    {
      "id": "news-20260224-nyt-001",
      "title": "Article Title in Original Language",
      "source": {
        "name": "NYTimes",
        "type": "crawl",
        "url": "https://www.nytimes.com/2026/02/24/...",
        "published_date": "2026-02-24",
        "region": "US",
        "site_short": "nyt"
      },
      "content": {
        "abstract": "First 500 chars of article in original language...",
        "full_text": "Full article body in original language...",
        "keywords": [],
        "entities": [],
        "language": "en"
      },
      "preliminary_category": "T",
      "collected_at": "2026-02-24T06:15:42Z",
      "metadata": {
        "source_language": "en",
        "source_region": "US",
        "crawl_method": "rss",
        "paywall_bypassed": false,
        "article_type": "news"
      }
    }
  ]
}
```

---

## Signal ID Format

```
news-{YYYYMMDD}-{site_short}-{NNN}
```

Examples:
- `news-20260224-nyt-001` (New York Times)
- `news-20260224-reuters-005` (Reuters)
- `news-20260224-yonhap-012` (Yonhap)
- `news-20260224-xinhua-003` (Xinhua)
- `news-20260224-nhk-007` (NHK)
- `news-20260224-spiegel-002` (Der Spiegel)
- `news-20260224-lemonde-004` (Le Monde)
- `news-20260224-tass-001` (TASS)
- `news-20260224-aljazeera-006` (Al Jazeera)
- `news-20260224-haaretz-003` (Haaretz)
- `news-20260224-elpais-002` (El Pais)
- `news-20260224-hindustan-004` (Hindustan Times)

---

## Execution Logic

### Step 1: Load Configuration and Learned Patterns
```python
import yaml
import json
from pathlib import Path

# Load source configuration
with open(sources_config) as f:
    config = yaml.safe_load(f)
    sources = config['sources']

# Load learned patterns (from previous crawl runs)
patterns_file = Path(f"{data_root}/logs/crawl-patterns.json")
if patterns_file.exists():
    with open(patterns_file) as f:
        learned_patterns = json.load(f)
else:
    learned_patterns = {}
```

### Step 2: RSS-First Crawling Strategy
```python
for source in sources:
    site_short = source['site_short']

    # Strategy 1: Try RSS feed first (fastest, most reliable)
    if source.get('rss_url'):
        articles = crawl_via_rss(source['rss_url'], source)
        if articles:
            all_articles.extend(articles)
            continue

    # Strategy 2: Direct page crawl (fallback)
    articles = crawl_via_direct(source['url'], source)
    if articles:
        all_articles.extend(articles)
        continue

    # Strategy 3: Search API fallback
    if source.get('search_api'):
        articles = crawl_via_search(source['search_api'], source)
        all_articles.extend(articles)
```

### Step 3: Paywall Handling (Total War Strategy)
```python
PAYWALL_SITES = {
    "nyt": "New York Times",
    "ft": "Financial Times",
    "wsj": "Wall Street Journal",
    "bloomberg": "Bloomberg",
    "economist": "The Economist",
    "nikkei": "Nikkei Asia",
}

def handle_paywall(url, source):
    """Total War strategy for paywalled sources."""
    strategies = [
        try_rss_full_text,      # RSS often has full text
        try_google_cache,        # Google cache of article
        try_archive_services,    # archive.org, archive.today
        try_amp_version,         # AMP pages often bypass paywall
        try_social_referrer,     # Social media referrer headers
        extract_meta_only,       # Last resort: title + description + meta
    ]

    for strategy in strategies:
        result = strategy(url, source)
        if result and len(result.get('content', '')) > 100:
            result['metadata']['paywall_bypassed'] = True
            result['metadata']['bypass_method'] = strategy.__name__
            return result

    # Absolute fallback: use whatever metadata we can extract
    return extract_minimum_metadata(url, source)
```

### Step 4: Required Fields Validation
```python
REQUIRED_FIELDS = ['id', 'title', 'source', 'content']

def validate_article(article):
    """Every article must have these 4 fields."""
    for field in REQUIRED_FIELDS:
        if field not in article or not article[field]:
            return False

    # Additional checks
    if not article['source'].get('url'):
        return False
    if not article['content'].get('abstract') or len(article['content']['abstract']) < 50:
        return False
    if not article['content'].get('language'):
        return False

    return True
```

### Step 5: Noise Filtering
```python
def filter_noise(articles):
    """Remove low-quality articles."""
    filtered = []
    seen_titles = set()

    for article in articles:
        # Skip short articles
        if len(article.get('content', {}).get('abstract', '')) < 50:
            continue
        # Skip ads / sponsored content
        if is_advertorial(article):
            continue
        # Skip photo-only galleries
        if is_gallery(article):
            continue
        # Skip duplicate titles (across all sources)
        title_key = article['title'].strip().lower()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        # Validate required fields
        if not validate_article(article):
            continue
        filtered.append(article)

    return filtered
```

### Step 6: Save Learned Patterns
```python
def save_learned_patterns(crawl_results):
    """Persist crawl patterns for future optimization."""
    patterns = {
        "last_updated": datetime.now().isoformat(),
        "source_patterns": {}
    }

    for source_name, stats in crawl_results.items():
        patterns["source_patterns"][source_name] = {
            "best_strategy": stats['successful_strategy'],
            "avg_articles_per_crawl": stats['articles_count'],
            "failure_rate": stats['failure_count'] / max(stats['attempt_count'], 1),
            "avg_response_time": stats['avg_response_time'],
            "last_block_time": stats.get('last_block_time'),
            "paywall_bypass_success": stats.get('paywall_bypass_success', False),
        }

    with open(f"{data_root}/logs/crawl-patterns.json", 'w') as f:
        json.dump(patterns, f, indent=2)
```

### Step 7: Write Output
```python
import json
from datetime import datetime

sn_ratio = len(filtered_articles) / max(len(raw_articles), 1)

output = {
    "agent_metadata": {
        "agent_name": "news-direct-crawler",
        "model_used": "sonnet",
        "execution_time": elapsed_time,
        "articles_collected": len(filtered_articles),
        "sources_scanned": len(sources),
        "crawl_strategy": "rss_first",
        "sn_ratio": round(sn_ratio, 2),
        "scan_date": datetime.now().strftime("%Y-%m-%d"),
        "status": "success",
        "language_stats": count_by_language(filtered_articles),
        "source_stats": source_stats
    },
    "scan_metadata": {
        "execution_proof": {
            "execution_id": generate_execution_id("wf4-crawl"),
            "started_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "actual_api_calls": {"web_search": 0, "arxiv_api": 0, "news_crawl": len(filtered_articles)},
            "actual_sources_scanned": ["GlobalNews"],
            "file_created_at": datetime.now().isoformat()
        }
    },
    "items": filtered_articles
}

output_path = f"{data_root}/raw/daily-crawl-{date}.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
```

---

## 3-Level Retry Logic

### Level 1: NetworkGuard (Per-Request)
```yaml
NetworkGuard:
  scope: "Individual HTTP request"
  max_retries: 3
  backoff: "exponential (1s, 2s, 4s)"
  handles:
    - ConnectionTimeout
    - ConnectionReset
    - DNS failure
    - SSL errors
  on_exhausted: "Escalate to CrawlDefender"
```

### Level 2: CrawlDefender (Per-Source)
```yaml
CrawlDefender:
  scope: "Single news source"
  strategy_cascade:
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
  on_exhausted: "Mark source as failed, escalate to Pipeline level"
```

### Level 3: Pipeline (Workflow-Level)
```yaml
Pipeline:
  scope: "Entire WF4 crawl phase"
  threshold: ">= 50% of sources must succeed"
  on_partial_failure:
    action: "Proceed with available data, log WARNING"
    log: "WARN: {N} of {total} sources failed. Proceeding with partial data."
  on_majority_failure:
    action: "HALT workflow, notify user"
    message: "CRITICAL: < 50% of sources succeeded. WF4 cannot produce reliable report."
```

---

## Error Handling

### Retry Strategy
```yaml
retry_policy:
  max_attempts: 10  # Per URL
  backoff: exponential  # 2s, 4s, 8s, 16s, ...

  errors:
    HTTP_403:
      action: "Escalate to next CrawlDefender strategy"
    HTTP_429:
      action: "Wait 30 seconds, retry with delay_increase"
    HTTP_451:
      action: "Try proxy, then skip source with WARNING"
    TimeoutError:
      action: "Increase timeout (15s -> 30s -> 60s)"
    NetworkError:
      action: "Exponential backoff retry"
    ContentParseError:
      action: "Log warning, skip article, continue"
    PaywallBlocked:
      action: "Execute Total War paywall cascade"
    EncodingError:
      action: "Try UTF-8, then source-specific encoding, then skip"
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "60-180 seconds"
  articles_per_scan: "200-500 articles"
  sources_coverage: "All configured sources"
  language_coverage: "11 languages"
  sn_ratio_target: "> 0.55"

  bottlenecks:
    - "Anti-block delays (2-5s per request)"
    - "Source delays (5s between sources)"
    - "Paywall bypass attempts (3-10s per paywalled article)"
    - "Content fetch for long articles"

  optimizations:
    - "RSS-first reduces HTTP requests by ~60%"
    - "Learned patterns avoid known-failing strategies"
    - "Parallel-safe source grouping by region"
    - "Sonnet model for multi-language content extraction"
```

---

## Version
- **Agent Version**: 1.0.0
- **Compatible with**: WF4 Multi&Global-News Environmental Scanning v1.0.0
- **Model**: Sonnet 4.5
- **Last Updated**: 2026-02-24
