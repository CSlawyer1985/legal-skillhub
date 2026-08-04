#!/usr/bin/env python3
"""Test search directly"""

import sys
sys.path.insert(0, '.')

from meilisearch import Client
import config

print("Connecting to Meilisearch...")
meili = Client(config.MEILISEARCH_HOST, config.MEILISEARCH_MASTER_KEY)
INDEX_NAME = "legal_cn"

print(f"Testing search for '国家'...")
search_result = meili.search(INDEX_NAME, "国家", {"limit": 10})
print(f"Got {len(search_result['hits'])} hits:")
for hit in search_result["hits"]:
    print(f"- {hit['law_title']} {hit['article_no']} {hit['article_title']}: {hit['content'][:50]}...")

print("\nDone!")
