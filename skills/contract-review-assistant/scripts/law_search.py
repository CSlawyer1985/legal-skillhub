# -*- coding: utf-8 -*-
"""
法律知识库查询模块 v2.0
支持本地知识库检索 + 全国人大法规库实时查询
"""

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Optional


class LawSearch:
    """法律知识库搜索类 v2.0"""

    def __init__(self, index_path: str = None, use_online: bool = True):
        """
        初始化法律知识库

        Args:
            index_path: 索引文件路径，默认使用压缩版索引
            use_online: 是否启用全国人大法规库实时查询
        """
        if index_path is None:
            # 默认使用压缩版知识库索引（体积更小）
            skill_dir = Path(__file__).parent.parent
            index_path = skill_dir / "knowledge_base_compressed" / "law_index.json"

        self.index_path = Path(index_path)
        self.index_data = None
        self._load_index()
        
        # 在线查询
        self.use_online = use_online
        self._online_searcher = None
        
        # 在线搜索关键词（高风险条款需要实时查询）
        self.online_keywords = [
            "违约金", "违约责任", "保密", "知识产权", "不可抗力",
            "争议解决", "仲裁", "诉讼", "解除合同", "终止合同",
            "损害赔偿", "格式条款", "格式合同", "竞业限制",
            "服务期", "试用期", "社会保险", "年休假"
        ]

    def _load_index(self):
        """加载索引文件"""
        if self.index_path.exists():
            with open(self.index_path, 'r', encoding='utf-8') as f:
                self.index_data = json.load(f)
        else:
            print(f"⚠️ 索引文件不存在: {self.index_path}")
            self.index_data = {"files": [], "chunks": []}

    def _get_online_searcher(self):
        """懒加载在线搜索器"""
        if self._online_searcher is None and self.use_online:
            try:
                from scripts.official_law_search import NationalLawSearch
                self._online_searcher = NationalLawSearch()
            except ImportError:
                self._online_searcher = None
        return self._online_searcher

    def search(self, keyword: str, top_k: int = 5, law_type: str = None) -> List[Dict]:
        """
        搜索相关法律条文

        Args:
            keyword: 搜索关键词
            top_k: 返回前k条结果
            law_type: 指定法律类型（如"民法典"、"劳动合同法"等）

        Returns:
            搜索结果列表
        """
        results = []

        # 1. 先搜索本地知识库
        local_results = self._search_local(keyword, top_k, law_type)
        results.extend(local_results)

        # 2. 如果本地结果不足或关键词重要，查询全国人大法规库
        if len(results) < top_k and self.use_online:
            online_results = self._search_online(keyword, top_k - len(results))
            results.extend(online_results)

        # 去重并排序
        seen = set()
        unique_results = []
        for r in results:
            key = r.get("file", "") + r.get("title", "") + r.get("snippet", "")[:50]
            if key not in seen:
                seen.add(key)
                unique_results.append(r)

        return unique_results[:top_k]

    def _search_local(self, keyword: str, top_k: int, law_type: str = None) -> List[Dict]:
        """搜索本地知识库"""
        if not self.index_data or not keyword:
            return []

        results = []
        keyword_lower = keyword.lower()

        for chunk in self.index_data.get("chunks", []):
            text = chunk.get("content", "") or chunk.get("text", "")
            text_lower = text.lower()

            if keyword_lower in text_lower:
                file_name = chunk.get("file_name", "")

                if law_type and law_type not in file_name:
                    continue

                score = text_lower.count(keyword_lower)
                snippet = self._extract_snippet(text, keyword, 150)

                results.append({
                    "file": file_name,
                    "chunk_id": chunk.get("chunk_index", 0),
                    "score": score,
                    "snippet": snippet,
                    "full_text": text,
                    "source": "本地知识库"
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _search_online(self, keyword: str, top_k: int) -> List[Dict]:
        """查询全国人大法规库"""
        searcher = self._get_online_searcher()
        if not searcher:
            return []

        try:
            online_results = searcher.search_and_get_snippet(keyword, top_k)
            for r in online_results:
                r["source"] = "全国人大法规库（实时）"
            return online_results
        except Exception as e:
            print(f"在线查询失败: {e}")
            return []

    def _extract_snippet(self, text: str, keyword: str, max_length: int = 150) -> str:
        """提取包含关键词的文本片段"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        pos = text_lower.find(keyword_lower)

        if pos == -1:
            return text[:max_length] + "..." if len(text) > max_length else text

        start = max(0, pos - 50)
        end = min(len(text), pos + len(keyword) + 100)

        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet = snippet + "..."

        return snippet


# 测试
if __name__ == "__main__":
    searcher = LawSearch()

    # 测试搜索
    print("=" * 50)
    print("测试：搜索'违约金'相关法律条文")
    print("=" * 50)
    results = searcher.search("违约金", top_k=5)
    for i, r in enumerate(results, 1):
        print(f"\n【结果 {i}】{r['file']}")
        print(f"片段: {r['snippet']}")

    print("\n" + "=" * 50)
    print("测试：搜索'不可抗力'相关法律条文")
    print("=" * 50)
    results = searcher.search("不可抗力", top_k=3)
    for i, r in enumerate(results, 1):
        print(f"\n【结果 {i}】{r['file']}")
        print(f"片段: {r['snippet']}")
