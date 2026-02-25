# News Translation Agent (Multi-Language to English)

## Role
**Specialized Agent** for translating crawled news articles from their original languages to English for uniform downstream analysis. Part of WF4 (Multi&Global-News Environmental Scanning), Phase 1 Step 1.2b.

## Agent Type
**Worker Agent** -- WF4 Exclusive (not shared with WF1/WF2/WF3)

## Objective
Translate ALL crawled articles to English so that downstream classification (STEEPs, FSSF), impact analysis, and report generation operate on a uniform language. English-language articles pass through unchanged. Original text is always preserved.

> **Distinction from shared translation-agent**: The shared `translation-agent` handles EN->KO translation
> for final report output. This agent handles **multi-language->EN** translation for internal analysis.
> They serve different purposes and operate at different pipeline stages.

---

## Agent Swarm Configuration

```yaml
agent_swarm:
  role: "specialized_worker"
  parallelization: false
  independent_context: true
  model: "sonnet"  # Multi-language translation requires medium-tier model
  max_tokens: 8000

  dependencies:
    blocked_by: ["news-direct-crawler"]
    blocks: ["deduplication-filter", "news-translation-agent-ko"]
```

---

## Supported Languages

| ISO Code | Language | Example Sources | Pass-Through |
|----------|----------|-----------------|--------------|
| `en` | English | NYT, Reuters, BBC, Bloomberg | YES (no translation needed) |
| `ko` | Korean | Yonhap, Chosun, Hankook | Translate to EN |
| `zh` | Chinese | Xinhua, SCMP, Caixin | Translate to EN |
| `ja` | Japanese | NHK, Nikkei, Asahi | Translate to EN |
| `de` | German | Der Spiegel, FAZ, Handelsblatt | Translate to EN |
| `fr` | French | Le Monde, AFP, Les Echos | Translate to EN |
| `ru` | Russian | TASS, Kommersant, RBC | Translate to EN |
| `ar` | Arabic | Al Jazeera, Al Arabiya | Translate to EN |
| `he` | Hebrew | Haaretz, Ynet, Globes | Translate to EN |
| `es` | Spanish | El Pais, La Nacion, Clarin | Translate to EN |
| `hi` | Hindi | Hindustan Times, NDTV, Dainik Jagran | Translate to EN |

---

## Input

```yaml
input:
  file: "{data_root}/raw/daily-crawl-{date}.json"
  format: "JSON"
  required_fields:
    - content.abstract  # Original-language text
    - content.language   # ISO 639-1 code
```

---

## Output

```yaml
output:
  file: "{data_root}/raw/daily-crawl-{date}.json"  # In-place update
  format: "JSON"
  modified_fields:
    - content.abstract           # Updated to English translation
    - content.original_abstract  # NEW: preserves original-language text
    - translation_confidence     # NEW: 0.0 - 1.0
    - translation_metadata:      # NEW: translation audit trail
        source_language: String
        method: String           # "pass_through" | "llm_translation"
        translated_at: ISO8601
```

---

## Execution Logic

### Step 1: Load Raw Crawl Data
```python
import json

with open(f"{data_root}/raw/daily-crawl-{date}.json") as f:
    crawl_data = json.load(f)
```

### Step 2: Load Translation Terms
```python
import yaml

with open("env-scanning/config/translation-terms.yaml") as f:
    terms = yaml.safe_load(f)

# Build term lookup for consistent translation
term_dict = {}
for entry in terms.get('terms', []):
    for lang_code, lang_term in entry.items():
        if lang_code != 'en':
            term_dict[(lang_code, lang_term)] = entry.get('en', lang_term)
```

### Step 3: Translate Each Article
```python
from datetime import datetime

for item in crawl_data['items']:
    lang = item['content'].get('language', 'en')
    original_abstract = item['content']['abstract']

    # Preserve original text
    item['content']['original_abstract'] = original_abstract

    if lang == 'en':
        # English pass-through: no translation needed
        item['translation_confidence'] = 1.0
        item['translation_metadata'] = {
            'source_language': 'en',
            'method': 'pass_through',
            'translated_at': datetime.now().isoformat()
        }
        continue

    # Translate non-English to English
    translated = translate_to_english(original_abstract, lang, term_dict)

    item['content']['abstract'] = translated['text']
    item['translation_confidence'] = translated['confidence']
    item['translation_metadata'] = {
        'source_language': lang,
        'method': 'llm_translation',
        'translated_at': datetime.now().isoformat()
    }
```

### Step 4: Translation Prompt Template
```
You are an expert multilingual translator specializing in news content.
Translate the following {source_language} news excerpt to English.

REQUIREMENTS:
1. Preserve factual accuracy -- do NOT add, remove, or interpret information
2. Preserve proper nouns (people, organizations, places) in their standard English forms
3. Use the following mandatory term translations:
   {term_mappings}
4. Maintain the journalistic tone of the original
5. If the text contains technical/domain-specific terminology, use the standard English equivalent
6. Preserve any numerical data, dates, and statistics exactly as stated

SOURCE TEXT ({source_language}):
{original_text}

OUTPUT FORMAT:
{
  "text": "English translation...",
  "confidence": 0.85,
  "notes": "Any translation ambiguities or uncertain terms"
}
```

### Step 5: Confidence Scoring
```python
def compute_translation_confidence(original, translated, lang):
    """
    Compute translation confidence based on multiple factors.
    Returns: float 0.0 - 1.0
    """
    confidence = 1.0

    # Factor 1: Length ratio (translated should be similar length to original)
    ratio = len(translated) / max(len(original), 1)
    if ratio < 0.3 or ratio > 3.0:
        confidence -= 0.3  # Suspicious length change

    # Factor 2: Language difficulty
    hard_languages = {'ar', 'zh', 'ja', 'he', 'hi', 'ru'}
    if lang in hard_languages:
        confidence -= 0.05  # Slight penalty for harder languages

    # Factor 3: Term preservation
    # Check if known terms were correctly translated
    term_score = check_term_preservation(original, translated, lang)
    confidence -= (1.0 - term_score) * 0.2

    # Factor 4: Proper noun preservation
    noun_score = check_proper_nouns(original, translated)
    confidence -= (1.0 - noun_score) * 0.15

    return max(round(confidence, 2), 0.0)
```

### Step 6: Write Updated File
```python
# Write back in-place
with open(f"{data_root}/raw/daily-crawl-{date}.json", 'w', encoding='utf-8') as f:
    json.dump(crawl_data, f, indent=2, ensure_ascii=False)
```

---

## Quality Checks

```yaml
post_translation_checks:
  - every_item_has_english_abstract: "All items have content.abstract in English"
  - every_item_has_original_preserved: "All items have content.original_abstract"
  - every_item_has_confidence: "All items have translation_confidence field"
  - confidence_threshold: "Average translation_confidence >= 0.7"
  - no_empty_translations: "No item has empty content.abstract after translation"
  - term_consistency: "Known terms from translation-terms.yaml consistently translated"
  - pass_through_correct: "English items have translation_confidence == 1.0"
```

---

## Error Handling

```yaml
retry_policy:
  max_attempts: 2
  backoff: "1s, 3s"

  errors:
    TranslationError:
      action: "Retry with simpler prompt (just title + first paragraph)"
    UnsupportedLanguage:
      action: "Log WARNING, keep original text in abstract, confidence = 0.0"
    JSONParseError:
      action: "Retry with stricter output format instruction"
    AllRetriesFailed:
      action: |
        - Keep original text in abstract
        - Set translation_confidence = 0.0
        - Set translation_metadata.method = "failed"
        - Log ERROR: "Translation failed for signal {id} (language: {lang})"
        - Continue pipeline (do NOT halt)
      note: "Failed translations are filtered by confidence threshold downstream"
```

---

## Performance Expectations

```yaml
performance:
  execution_time: "30-90 seconds"
  depends_on: "Number of non-English articles and language diversity"

  language_difficulty_tiers:
    tier_1_fast: ["en", "fr", "de", "es"]  # Close to English
    tier_2_medium: ["ko", "ja", "ru"]       # Different script, medium difficulty
    tier_3_slow: ["zh", "ar", "he", "hi"]   # Complex scripts, harder translation

  optimizations:
    - "Batch translation for same-language articles"
    - "English pass-through eliminates ~25-35% of translation work"
    - "Term dictionary pre-loading for consistent output"
    - "Sonnet model balances quality and speed across all 11 languages"
```

---

## Version
- **Agent Version**: 1.0.0
- **Compatible with**: WF4 Multi&Global-News Environmental Scanning v1.0.0
- **Model**: Sonnet 4.5
- **Last Updated**: 2026-02-24
