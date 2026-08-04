#!/usr/bin/env python3
"""Get unique latest laws by effective date"""

from meilisearch import Client

client = Client("http://localhost:7700", "masterKey")
index = client.index('legal_cn')

# Get unique law titles by latest effective date
result = index.search('', {
    'limit': 50,
    'sort': ['effective_date:desc']
})

# Collect unique law titles
seen_titles = set()
unique_latest = []

for hit in result['hits']:
    title = hit.get('law_title', '')
    date = hit.get('effective_date', '')
    if title not in seen_titles and date and title:
        seen_titles.add(title)
        unique_latest.append((date, title))
        if len(unique_latest) >= 10:
            break

print("📅 最新生效的10部法律：")
print("-" * 70)
for date, title in sorted(unique_latest, key=lambda x: x[0], reverse=True):
    print(f"  {date}  -  {title}")
