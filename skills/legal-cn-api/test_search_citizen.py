#!/usr/bin/env python3
"""Test API search for '公民'"""

import requests

url = "http://localhost:8000/api/v1/search"

print("Testing API search for '公民'...")
params = {"q": "公民", "limit": 5}
response = requests.get(url, params=params)
print(f"Status code: {response.status_code}")
data = response.json()
print(f"Success: {data['success']}")
print(f"Total results: {data['total']}")
print("-" * 60)
for i, result in enumerate(data['results']):
    print(f"\n{i+1}. {result['law_title']} {result['article_no']}")
    print(f"   {result['content'][:100]}...")

print("\n" + "="*60)
print("\nTesting search for '选举权'...")
params = {"q": "选举权", "limit": 3}
response = requests.get(url, params=params)
data = response.json()
for i, result in enumerate(data['results']):
    print(f"\n{i+1}. {result['law_title']} {result['article_no']}")
    print(f"   {result['content'][:100]}...")
