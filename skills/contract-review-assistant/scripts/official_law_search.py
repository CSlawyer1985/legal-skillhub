# -*- coding: utf-8 -*-
"""
全国人大法律法规库实时查询模块
从 https://flk.npc.gov.cn 实时查询最新法律法规
"""

import requests
import json
import time
import re
from typing import List, Dict, Optional


class NationalLawSearch:
    """全国人大法律法规库查询类"""

    # 官方搜索页面
    SEARCH_PAGE_URL = "https://flk.npc.gov.cn/search"
    
    # 尝试的API端点
    API_ENDPOINTS = [
        "https://flk.npc.gov.cn/api/v2/search",
        "https://flk.npc.gov.cn/search/getSearchResult",
        "https://search.flfg.gov.cn/api/law/search"
    ]

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://flk.npc.gov.cn/",
        "Origin": "https://flk.npc.gov.cn"
    }

    def __init__(self, timeout: int = 15):
        """
        初始化查询器

        Args:
            timeout: 请求超时时间（秒）
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def search(self, keyword: str, page: int = 1, page_size: int = 10) -> List[Dict]:
        """
        搜索法律法规

        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量

        Returns:
            搜索结果列表
        """
        results = []

        # 方法1：尝试POST请求API
        try:
            payload = {
                "searchText": keyword,
                "page": str(page),
                "size": str(page_size),
                "sort": "pubdate",
                "direction": "desc"
            }

            for api_url in self.API_ENDPOINTS:
                try:
                    response = self.session.post(
                        api_url,
                        json=payload,
                        timeout=self.timeout
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and data.get("code") == 200:
                            results = self._parse_api_result(data)
                            if results:
                                break
                except:
                    continue
        except Exception as e:
            print(f"API查询失败: {e}")

        # 方法2：抓取搜索页面
        if not results:
            results = self._scrape_search_page(keyword, page, page_size)

        return results[:page_size]

    def _parse_api_result(self, data: Dict) -> List[Dict]:
        """解析API返回结果"""
        results = []
        items = data.get("data", {}).get("items", [])
        if not items:
            items = data.get("data", [])
        if not items:
            items = data.get("result", [])
            
        for item in items:
            results.append({
                "title": item.get("title", item.get("lawName", "")),
                "publish_date": item.get("publishDate", item.get("pubDate", "")),
                "law_id": item.get("lawId", item.get("id", "")),
                "category": item.get("category", ""),
                "url": f"https://flk.npc.gov.cn/detail/{item.get('lawId', '')}",
                "source": "全国人大法规库"
            })
        return results

    def _scrape_search_page(self, keyword: str, page: int, page_size: int) -> List[Dict]:
        """从搜索页面抓取结果"""
        results = []
        
        try:
            params = {
                "type": "law",
                "search": keyword,
                "page": page
            }
            response = self.session.get(
                self.SEARCH_PAGE_URL,
                params=params,
                timeout=self.timeout
            )

            if response.status_code == 200:
                # 尝试从页面提取法律标题
                text = response.text
                
                # 匹配法律标题模式
                patterns = [
                    r'<a[^>]*class=["\'][^"\']*title=["\']([^"\']+)["\'][^>]*>([^<]*)</a>',
                    r'class="law-title"[^>]*>([^<]+)</[^>]+>',
                    r'<h3[^>]*>([^<]*' + re.escape(keyword) + r'[^<]*)</h3>',
                ]
                
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches[:page_size]:
                        if isinstance(match, tuple):
                            title = match[-1] if match[1].strip() else match[0]
                        else:
                            title = match
                        title = title.strip()
                        if title and keyword.lower() in title.lower():
                            results.append({
                                "title": title,
                                "url": f"https://flk.npc.gov.cn/search?search={keyword}",
                                "source": "全国人大法规库（网页抓取）"
                            })
        except Exception as e:
            print(f"页面抓取失败: {e}")
            
        return results

    def search_and_get_snippet(self, keyword: str, top_k: int = 3) -> List[Dict]:
        """
        搜索并获取相关条文片段

        Args:
            keyword: 搜索关键词
            top_k: 返回数量

        Returns:
            包含片段的搜索结果
        """
        results = self.search(keyword, page_size=top_k * 2)

        filtered_results = []
        for r in results[:top_k]:
            r["snippet"] = (
                f"《{r.get('title', '')}》"
                f"{'（' + r.get('publish_date', '') + '）' if r.get('publish_date') else ''}"
                f"\n来源：{r.get('source', '全国人大法规库')}"
                f"\n链接：{r.get('url', '')}"
            )
            filtered_results.append(r)

        return filtered_results


# 便捷函数
def search_national_law(keyword: str, top_k: int = 3) -> List[Dict]:
    """
    便捷函数：搜索全国人大法律法规库

    Args:
        keyword: 搜索关键词
        top_k: 返回数量

    Returns:
        搜索结果列表
    """
    searcher = NationalLawSearch()
    return searcher.search_and_get_snippet(keyword, top_k)


# 测试
if __name__ == "__main__":
    print("=" * 50)
    print("测试：全国人大法规库查询")
    print("=" * 50)

    searcher = NationalLawSearch()

    # 测试搜索
    print("\n搜索'劳动合同'相关法规:")
    results = searcher.search("劳动合同", page_size=5)
    
    if results:
        for i, r in enumerate(results, 1):
            print(f"\n【结果 {i}】")
            print(f"标题: {r.get('title', 'N/A')}")
            print(f"来源: {r.get('source', 'N/A')}")
    else:
        print("\n未能获取在线结果，请检查网络连接")
        print("提示：法规库API可能需要特殊认证或已变更")
        print("建议：访问 https://flk.npc.gov.cn 手动查询最新法规")

