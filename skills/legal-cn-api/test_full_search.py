#!/usr/bin/env python3
"""Test full database search"""

import requests

url = "http://localhost:8000/api/v1/search"

def search(query, limit=5):
    print(f"\n{'='*60}")
    print(f"搜索关键词: '{query}'")
    print('-'*60)
    params = {"q": query, "limit": limit}
    response = requests.get(url, params=params)
    data = response.json()
    print(f"找到 {data['total']} 条结果，显示前 {len(data['results'])} 条:\n")
    for i, result in enumerate(data['results']):
        category = result.get('category', '')
        status = result.get('status', '')
        status_mark = "✅" if status == "有效" else "⚠️"
        print(f"{i+1}. {status_mark} {result['law_title']} {result['article_no']} [{category}]")
        print(f"   {result['content'][:120]}..." if len(result['content']) > 120 else f"   {result['content']}")
        print()

if __name__ == "__main__":
    print("=== 法律数据库完整搜索测试 ===")
    print(f"API 地址: {url}")
    
    # 测试几个常见关键词
    search("公民")
    search("选举权")
    search("正当防卫")
    search("劳动合同")
    search("隐私权")
    search("不当得利")
