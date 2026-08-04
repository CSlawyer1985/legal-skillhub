#!/usr/bin/env python3
"""Check the latest effective date in dataset"""

from meilisearch import Client

# Configuration
MEILISEARCH_HOST = "http://localhost:7700"
MEILISEARCH_MASTER_KEY = "masterKey"

client = Client(MEILISEARCH_HOST, MEILISEARCH_MASTER_KEY)
index = client.index('legal_cn')

# Search for documents sorted by effective_date descending
result = index.search('', {
    'limit': 10,
    'sort': ['effective_date:desc']
})

print("最新生效日期前10条：")
print("-" * 70)
for hit in result['hits']:
    date = hit.get('effective_date', '')
    if date and len(str(date)) >= 10:
        print(f"{date} - {hit['law_title']} {hit['article_no']}")
