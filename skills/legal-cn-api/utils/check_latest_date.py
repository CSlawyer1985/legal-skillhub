#!/usr/bin/env python3
"""Check the latest effective date in dataset"""

import json
from meilisearch import Client
import config

client = Client(config.MEILISEARCH_HOST, config.MEILISEARCH_MASTER_KEY)
index = client.index('legal_cn')

# Search for documents sorted by effective_date descending
result = index.search('', {
    'limit': 10,
    'sort': ['effective_date:desc']
})

print("最新生效日期前10条：")
print("-" * 60)
for hit in result['hits']:
    print(f"{hit['effective_date']} - {hit['law_title']} {hit['article_no']}")
