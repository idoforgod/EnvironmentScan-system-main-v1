#!/usr/bin/env python3
"""
Standalone arXiv scanner for WF2 deep scanning.
Handles rate limiting properly and saves results.
"""

import sys
import json
import yaml
import urllib.request
import urllib.parse
import ssl
import xml.etree.ElementTree as ET
import time
import re
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, str(Path(__file__).parent.parent))
os.chdir(PROJECT_ROOT)

from utils.entity_extractor import EntityExtractor


def resolve_steeps(arxiv_categories, steeps_mapping):
    steeps_map = {
        'T': 'T_Technological', 'E': 'E_Economic',
        'E_Environmental': 'E_Environmental',
        'S': 'S_Social', 'P': 'P_Political', 's': 's_spiritual'
    }
    for cat in arxiv_categories:
        if cat in steeps_mapping:
            code = steeps_mapping[cat]
            return steeps_map.get(code, 'T_Technological')
    return 'T_Technological'


def fetch_with_retry(url, ssl_context, max_retries=3):
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=60, context=ssl_context) as response:
                return response.read()
        except Exception as e:
            err_str = str(e)
            if '429' in err_str:
                backoff = (attempt + 1) * 15
                print(f'  Rate limited, waiting {backoff}s (attempt {attempt+1}/{max_retries})')
                time.sleep(backoff)
            else:
                backoff = (attempt + 1) * 5
                print(f'  Error: {e}, retrying in {backoff}s')
                time.sleep(backoff)
    return None


def main():
    # Load config
    with open('env-scanning/config/sources-arxiv.yaml') as f:
        config_data = yaml.safe_load(f)

    source_config = config_data['sources'][0]
    query_groups = source_config['query_groups']
    steeps_mapping = source_config['category_steeps_mapping']

    # Scan window from temporal anchor state file (2026-02-18)
    # WF2: 48h lookback + 60min tolerance from T₀ = 2026-02-18T21:13:43 UTC
    window_start = datetime(2026, 2, 16, 20, 13, 43)  # effective_start (window_start - tolerance)
    window_end = datetime(2026, 2, 18, 21, 13, 43)    # T₀

    print(f'Effective window: {window_start.isoformat()} to {window_end.isoformat()}')
    print(f'Query groups: {len(query_groups)}')

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Wait for rate limit cooldown
    print('Waiting 10s for arXiv rate limit cooldown...')
    time.sleep(10)

    all_papers = []
    seen_ids = set()
    total_api_calls = 0
    failed_groups = []
    scan_start = datetime.now()

    for i, group in enumerate(query_groups, 1):
        name = group.get('name', f'group-{i}')
        categories = group.get('categories', [])
        max_results = group.get('max_results', 50)

        if not categories:
            continue

        cat_query = ' OR '.join([f'cat:{cat}' for cat in categories])
        query = urllib.parse.quote(f'({cat_query})')
        url = (f'https://export.arxiv.org/api/query?search_query={query}'
               f'&start=0&max_results={max_results}'
               f'&sortBy=submittedDate&sortOrder=descending')

        # Rate limit: 5 seconds between requests
        time.sleep(5)
        total_api_calls += 1

        xml_content = fetch_with_retry(url, ssl_context)
        if xml_content is None:
            print(f'[{i}/{len(query_groups)}] {name}: FAILED after retries')
            failed_groups.append(name)
            continue

        root = ET.fromstring(xml_content)
        ns = {'atom': 'http://www.w3.org/2005/Atom',
              'arxiv': 'http://arxiv.org/schemas/atom'}

        new_count = 0
        for entry in root.findall('atom:entry', ns):
            title_elem = entry.find('atom:title', ns)
            summary_elem = entry.find('atom:summary', ns)
            published_elem = entry.find('atom:published', ns)
            id_elem = entry.find('atom:id', ns)

            if any(e is None or not (e.text if e is not None else None)
                   for e in [title_elem, summary_elem, published_elem, id_elem]):
                continue

            title = re.sub(r'\s+', ' ', title_elem.text.strip())
            abstract = re.sub(r'\s+', ' ', summary_elem.text.strip())
            arxiv_url = id_elem.text.replace('http://arxiv.org/', 'https://arxiv.org/')
            arxiv_id = arxiv_url.split('/')[-1]
            pub_date = published_elem.text[:10]

            if arxiv_id in seen_ids:
                continue
            seen_ids.add(arxiv_id)

            # Categories
            cats = []
            pc = entry.find('arxiv:primary_category', ns)
            if pc is not None:
                cats.append(pc.get('term'))
            for ce in entry.findall('atom:category', ns):
                t = ce.get('term')
                if t and t not in cats:
                    cats.append(t)

            # Authors
            authors = [ae.find('atom:name', ns).text
                      for ae in entry.findall('atom:author', ns)
                      if ae.find('atom:name', ns) is not None]

            steeps = resolve_steeps(cats, steeps_mapping)

            # Temporal filter
            try:
                pub_dt = datetime.strptime(pub_date, '%Y-%m-%d')
                if pub_dt < window_start or pub_dt > window_end:
                    continue
            except ValueError:
                pass

            combined = f'{title} {abstract}'
            entities = EntityExtractor.extract(combined, max_entities=15)

            signal = {
                'id': f'arxiv-{arxiv_id}',
                'title': title,
                'source': {
                    'name': 'arXiv',
                    'type': 'academic',
                    'url': arxiv_url,
                    'published_date': pub_date
                },
                'content': {
                    'abstract': abstract,
                    'keywords': cats[:10],
                    'language': 'en'
                },
                'metadata': {
                    'arxiv_id': arxiv_id,
                    'authors': authors[:5],
                    'arxiv_categories': cats,
                    'steeps_mapping': steeps
                },
                'entities': entities,
                'preliminary_category': steeps[0] if steeps else 'T',
                'collected_at': datetime.now().isoformat()
            }
            all_papers.append(signal)
            new_count += 1

        print(f'[{i}/{len(query_groups)}] {name}: {new_count} new papers')

    scan_end = datetime.now()

    print(f'\n=== SCAN RESULTS ===')
    print(f'Total signals in window: {len(all_papers)}')
    print(f'API calls: {total_api_calls}')
    print(f'Failed groups: {len(failed_groups)} ({", ".join(failed_groups) if failed_groups else "none"})')
    print(f'Duration: {(scan_end - scan_start).total_seconds():.0f}s')

    cat_dist = {}
    for s in all_papers:
        cat = s.get('metadata', {}).get('steeps_mapping', 'Unknown')
        cat_dist[cat] = cat_dist.get(cat, 0) + 1
    print(f'\nSTEEPs distribution:')
    for cat, count in sorted(cat_dist.items(), key=lambda x: -x[1]):
        print(f'  {cat}: {count}')

    # Save
    scan_data = {
        'metadata': {
            'workflow': 'wf2-arxiv',
            'scan_date': '2026-02-18',
            'scanner_version': '2.0.0',
            'scan_window': {
                'start': '2026-02-16T21:13:43.875040+00:00',
                'end': '2026-02-18T21:13:43.875040+00:00',
                'lookback_hours': 48,
                'tolerance_minutes': 60
            },
            'query_groups': len(query_groups),
            'total_scanned': len(all_papers),
            'total_api_calls': total_api_calls,
            'failed_groups': failed_groups,
            'scan_started_at': scan_start.isoformat(),
            'scan_completed_at': scan_end.isoformat()
        },
        'scan_metadata': {
            'execution_proof': {
                'execution_id': f'wf2-scan-2026-02-18-{scan_start.strftime("%H-%M-%S")}-b7d3',
                'started_at': scan_start.isoformat(),
                'completed_at': scan_end.isoformat(),
                'actual_api_calls': {'web_search': 0, 'arxiv_api': total_api_calls},
                'actual_sources_scanned': ['arXiv'],
                'file_created_at': scan_end.isoformat()
            }
        },
        'items': all_papers
    }

    output = 'env-scanning/wf2-arxiv/raw/daily-scan-2026-02-18.json'
    with open(output, 'w') as f:
        json.dump(scan_data, f, indent=2, ensure_ascii=False)

    print(f'\nSaved to: {output}')


if __name__ == '__main__':
    main()
