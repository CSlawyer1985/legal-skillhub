#!/usr/bin/env python3
"""Test the API"""

import requests

url = "http://localhost:8000/api/v1/search"

print("Testing API search for '国家'...")
params = {"q": "国家", "limit": 5}
response = requests.get(url, params=params)
print(f"Status code: {response.status_code}")
data = response.json()
print(f"Success: {data['success']}")
print(f"Total results: {data['total']}")
for result in data['results']:
    print(f"\n- {result['law_title']} {result['article_no']} {result['article_title']}")
    print(f"  Content: {result['content'][:60]}...")

print("\n" + "="*50)
print("\nTesting health check...")
response = requests.get("http://localhost:8000/health")
print(f"Response: {response.json()}")
