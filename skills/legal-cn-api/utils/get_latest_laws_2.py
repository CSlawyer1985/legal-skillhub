#!/usr/bin/env python3
"""Get unique latest laws by effective date"""

from meilisearch import Client

client = Client("http://localhost:7700", "masterKey")
index = client.index('legal_cn')

# Get more results
result = index.search('', {
    'limit': 200,
    'sort': ['effective_date:desc']
})

# Collect unique law titles by latest effective date
seen_titles = set()
unique_latest = []

for hit in result['hits']:
    title = hit.get('law_title', '')
    date = hit.get('effective_date', '')
    if title not in seen_titles and date and len(str(date)) >= 4 and title:
        seen_titles.add(title)
        # parse date
        if isinstance(date, str) and len(date) == 10:
            unique_latest.append((date, title))
        if len(unique_latest) >= 15:
            break

print("📅 最新生效的法律（按日期从新到旧）：")
print("-" * 75)
for date, title in sorted(unique_latest, key=lambda x: x[0], reverse=True):
    print(f"  {date}  -  {title}")
