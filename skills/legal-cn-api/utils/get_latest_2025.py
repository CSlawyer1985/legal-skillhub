#!/usr/bin/env python3
"""Get 2025 laws"""

from meilisearch import Client

client = Client("http://localhost:7700", "masterKey")
index = client.index('legal_cn')

result = index.search('', {
    'limit': 500,
    'sort': ['effective_date:desc']
})

seen_titles = set()
unique_latest = []

for hit in result['hits']:
    title = hit.get('law_title', '')
    date = hit.get('effective_date', '')
    if not date:
        continue
    date_str = str(date)
    if len(date_str) < 10:
        continue
    year = date_str[:4]
    if int(year) >= 2024 and title not in seen_titles and title:
        seen_titles.add(title)
        unique_latest.append((date_str, title))
        if len(unique_latest) >= 15:
            break

print("📅 最新生效的法律（2024-2026）：")
print("-" * 75)
for date, title in sorted(unique_latest, key=lambda x: x[0], reverse=True):
    print(f"  {date}  -  {title}")
