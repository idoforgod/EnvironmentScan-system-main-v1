# 📡 Source Scanners Module

Multi-source scanner architecture for collecting signals from diverse sources.

## 🏗️ Architecture

```
scanners/
├─ base_scanner.py       ← Abstract base class (all scanners inherit)
├─ scanner_factory.py    ← Factory pattern for creating scanners
├─ arxiv_scanner.py      ← arXiv academic paper scanner (ACTIVE)
└─ __init__.py           ← Module exports
```

## ✅ Active Scanners

### arXiv Scanner

**Status**: ✅ Production Ready (Validated 2026-01-30)

- **Type**: Academic papers
- **API**: http://export.arxiv.org/api/query
- **Authentication**: None required (open access)
- **Rate Limit**: 1 request per 3 seconds
- **Performance**: 100-150 papers in ~15 seconds
- **Reliability**: 100% success rate
- **Cost**: Free

**STEEPs Coverage**:
- T (Technological): cs.AI, cs.RO, cs.CV, quant-ph
- E (Economic): econ.EM, q-fin.EC, q-fin.TR
- E (Environmental): physics.ao-ph, physics.geo-ph
- S (Social): cs.CY, cs.HC
- P (Political): cs.CY
- s (spiritual): physics.soc-ph

## 🔮 Future Scanners

### Google Scholar (Planned)

- Type: Academic papers
- API: SerpAPI
- Authentication: API key required
- Status: Not yet implemented

### RSS Feeds (Planned)

- Type: Policy/News
- Sources: EU Press, WHO, Federal Register
- Authentication: None
- Status: Not yet implemented

## 📘 How to Add a New Scanner

### Step 1: Create Scanner Class

Create a new file `scanners/your_scanner.py`:

```python
from .base_scanner import BaseScanner
from typing import List, Dict, Any

class YourScanner(BaseScanner):
    """
    Your scanner description

    API: https://your-api-url.com
    Rate Limit: X requests per minute
    Authentication: API key / None
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Your initialization code
        self.api_key = config.get('api_key_env', None)

    def scan(self,
             steeps_domains: Dict[str, List[str]],
             days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Scan the source for signals

        Returns:
            List of signals in standard format
        """
        # 1. Build API query
        # 2. Make API request
        # 3. Parse response
        # 4. Convert to standard format using self.create_standard_signal()

        signals = []
        # Your scanning logic here
        return signals
```

### Step 2: Register Scanner

Edit `scanners/scanner_factory.py`:

```python
# In _register_default_scanners() function
from .your_scanner import YourScanner
ScannerFactory.register_scanner('source_type', 'Source Name', YourScanner)
```

### Step 3: Add Configuration

Edit `config/sources.yaml`:

```yaml
sources:
  - name: "Source Name"
    type: "academic|patent|policy|blog"
    enabled: true
    api_endpoint: "https://api.example.com"
    api_key_env: "YOUR_API_KEY"  # Optional
    rate_limit: 100  # per hour
    timeout: 30
    critical: false
    max_results: 50
```

### Step 4: Test

```bash
# Test your scanner
cd env-scanning
python3 scripts/run_multi_source_scan.py

# Verify output
cat raw/daily-scan-$(date +%Y-%m-%d).json
```

## 📋 Standard Signal Format

All scanners must return signals in this format:

```json
{
  "id": "source-identifier",
  "title": "Signal title",
  "source": {
    "name": "Source name",
    "type": "academic|patent|policy|blog",
    "url": "https://...",
    "published_date": "YYYY-MM-DD"
  },
  "content": {
    "abstract": "Signal description",
    "keywords": ["keyword1", "keyword2"],
    "language": "en"
  },
  "metadata": {
    // Source-specific fields
  },
  "preliminary_category": "S|T|E|P|s",
  "collected_at": "2026-01-30T10:00:00Z"
}
```

Use `self.create_standard_signal()` helper method for consistency.

## 🧪 Testing Your Scanner

### Unit Test Template

```python
import pytest
from scanners.your_scanner import YourScanner

def test_scanner_initialization():
    config = {
        'name': 'Your Scanner',
        'type': 'academic',
        'enabled': True
    }
    scanner = YourScanner(config)
    assert scanner.get_name() == 'Your Scanner'
    assert scanner.validate_config() == True

@pytest.mark.integration
def test_real_scan():
    """Integration test with real API (slow)"""
    scanner = YourScanner({
        'name': 'Your Scanner',
        'type': 'academic',
        'max_results': 5  # Small for testing
    })

    domains = {'T_Technological': ['AI', 'robotics']}
    results = scanner.scan(domains, days_back=7)

    assert len(results) > 0
    assert all('id' in r for r in results)
```

## 📊 BaseScanner Methods

### Required (Abstract)

- `scan(steeps_domains, days_back)` - Main scanning logic

### Provided (Helpers)

- `create_standard_signal()` - Create standard signal format
- `is_enabled()` - Check if scanner is enabled
- `is_critical()` - Check if scanner is critical
- `validate_config()` - Validate configuration
- `log_info/warning/error/success()` - Logging helpers
- `calculate_date_range()` - Calculate date range
- `format_date()` - Format datetime to string

## 🔧 Configuration Reference

### Required Fields

```yaml
name: "Scanner Name"
type: "academic|patent|policy|blog"
```

### Optional Fields

```yaml
enabled: true              # Default: true
critical: false            # Default: false
rate_limit: 100            # Requests per hour
timeout: 30                # Seconds
max_results: 50            # Per query
api_endpoint: "https://..."
api_key_env: "ENV_VAR_NAME"
```

### Special Fields

- `critical: true` - Failure halts entire workflow
- `critical: false` - Failure logged, workflow continues

## 🚦 Error Handling

### Rate Limiting

```python
def _respect_rate_limit(self):
    elapsed = time.time() - self.last_request_time
    if elapsed < self.RATE_LIMIT_DELAY:
        time.sleep(self.RATE_LIMIT_DELAY - elapsed)
    self.last_request_time = time.time()
```

### Timeout Handling

```python
try:
    response = make_api_call(timeout=self.timeout)
except TimeoutError:
    self.log_error("Request timed out")
    if self.is_critical():
        raise
    return []
```

### API Errors

```python
try:
    data = api.call()
except APIError as e:
    self.log_error(f"API error: {e}")
    if self.is_critical():
        raise
    return []
```

## 📈 Performance Guidelines

### Target Metrics

- **Execution time**: < 30 seconds per scanner
- **Success rate**: > 95% (100% for critical scanners)
- **Signals collected**: 50-200 per scan
- **API efficiency**: Minimize redundant calls

### Optimization Tips

1. **Batch requests** where possible
2. **Cache results** if API allows
3. **Respect rate limits** to avoid blocking
4. **Use connection pooling** for multiple requests
5. **Implement exponential backoff** for retries

## 🔒 Security

### API Keys

- **Never hardcode** API keys
- Use **environment variables** (`.env` file)
- Reference via `api_key_env` in config
- Load with `os.getenv('YOUR_API_KEY')`

### SSL/TLS

```python
# For trusted sources (like arXiv), SSL verification can be disabled
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

## 📚 Examples

### Minimal Scanner

```python
class MinimalScanner(BaseScanner):
    def scan(self, steeps_domains, days_back=7):
        # Hardcoded test data
        return [
            self.create_standard_signal(
                signal_id="test-001",
                title="Test Signal",
                source_url="https://example.com/1",
                published_date="2026-01-30",
                abstract="This is a test signal",
                keywords=["test", "example"],
                preliminary_category="T"
            )
        ]
```

### RSS Scanner Template

```python
class RSSScanner(BaseScanner):
    def scan(self, steeps_domains, days_back=7):
        import feedparser

        feed = feedparser.parse(self.config['rss_feed'])
        signals = []

        for entry in feed.entries[:self.max_results]:
            signal = self.create_standard_signal(
                signal_id=f"rss-{entry.id}",
                title=entry.title,
                source_url=entry.link,
                published_date=entry.published[:10],
                abstract=entry.summary,
                keywords=entry.get('tags', []),
                preliminary_category=self._guess_category(entry.title)
            )
            signals.append(signal)

        return signals
```

## 🆘 Troubleshooting

### Scanner Not Found

```
ValueError: Unsupported source: YourScanner
```

**Solution**: Register in `scanner_factory.py`:
```python
ScannerFactory.register_scanner('academic', 'YourScanner', YourScannerClass)
```

### Invalid Configuration

```
Invalid config for YourScanner, skipping
```

**Solution**: Ensure required fields in `sources.yaml`:
```yaml
- name: "YourScanner"
  type: "academic"
```

### Import Errors

```
ImportError: cannot import name 'YourScanner'
```

**Solution**: Add to `__init__.py`:
```python
from .your_scanner import YourScanner
__all__ = [..., 'YourScanner']
```

## 📞 Support

- **Issues**: Create issue in repository
- **Questions**: Contact maintainers
- **Contributions**: Pull requests welcome!

---

**Last Updated**: 2026-01-30
**Version**: 1.0.0
**Active Scanners**: 1 (arXiv)
**Planned Scanners**: 2+ (Scholar, RSS, etc.)
