"""
检索策略自动生成模块 (Module B)
功能：基于解析后的技术交底书要素，自动生成3-5套递进式检索式
"""

import re
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass


# 同义词扩展字典（示例，完整版需专业词库）
SYNONYM_DICT = {
    "去除": ["脱除", "消除", "移除"],
    "苦味": ["涩味", "苦腥味", "苦涩味", "不良风味", "异味"],
    "涩味": ["苦味", "收敛感", "涩口"],
    "茶叶": ["茶鲜叶", "茶原料", "茶树叶", "茶"],
    "提取": ["浸提", "萃取", "获取", "分离"],
    "酶解": ["酶处理", "酶催化", "酶促反应", "生物酶处理"],
    "发酵": ["微生物发酵", "酶发酵", "发酵处理"],
    "干燥": ["烘干", "干燥处理", "热风干燥", "真空干燥"],
    "筛选": ["分级", "分离", "过滤", "粒度分级"],
    "降解": ["分解", "转化", "降解除", "水解"],
    "过滤": ["滤过", "筛分", "澄清"],
    "浓缩": ["富集", "提浓"],
    "纯化": ["精制", "精炼"],
    "杀菌": ["灭菌", "消毒", "高温杀菌"],
    "保存": ["储藏", "储存", "保鲜"],
}


@dataclass
class SearchQuery:
    """检索式对象"""
    type: str                    # 检索式类型：宽泛检索/精准检索/补充检索/引文追踪
    query: str                   # 检索式文本
    databases: List[str]         # 目标数据库
    purpose: str                 # 检索目的说明


class SearchStrategyGenerator:
    """检索策略自动生成器"""

    def __init__(self, elements: Dict):
        self.elements = elements
        self.core_keywords = self._extract_core_keywords()
        self.expanded_keywords = self._expand_keywords()

    def _extract_core_keywords(self) -> List[str]:
        """从技术特征和技术方案中提取核心关键词"""
        keywords = set()

        for feature in self.elements.get("tech_features", []):
            words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,}', feature)
            for word in words:
                if len(word) >= 2 and not self._is_stopword(word):
                    keywords.add(word)

        for problem in self.elements.get("tech_problems", []):
            words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,}', problem)
            for word in words:
                if len(word) >= 2 and not self._is_stopword(word):
                    keywords.add(word)

        tech_field = self.elements.get("tech_field", "")
        words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]{2,}', tech_field)
        for word in words:
            if len(word) >= 2 and not self._is_stopword(word):
                keywords.add(word)

        return list(keywords)

    def _is_stopword(self, word: str) -> bool:
        stopwords = {"的", "了", "和", "与", "或", "为", "在", "是", "等", "其", "该", "上", "下", "中", "对", "以", "及", "于", "并", "也", "而", "之", "将", "把", "被", "使", "可", "能", "要", "会", "有", "这", "那", "种", "类", "个", "所", "则", "但", "因", "从", "当", "如"}
        return word in stopwords

    def _expand_keywords(self) -> List[str]:
        """关键词同义词扩展"""
        expanded = set()

        for keyword in self.core_keywords:
            expanded.add(keyword)
            if keyword in SYNONYM_DICT:
                expanded.update(SYNONYM_DICT[keyword])
            for k, synonyms in SYNONYM_DICT.items():
                if keyword in synonyms:
                    expanded.add(k)
                    expanded.update(synonyms)

        return list(expanded)

    def generate_search_queries(self) -> List[SearchQuery]:
        """生成递进式检索式列表"""
        queries = []

        # 1. 宽泛检索
        broad_query = self._build_broad_query()
        queries.append(SearchQuery(
            type="宽泛检索",
            query=broad_query,
            databases=["CNIPA", "EPO Espacenet", "WIPO Patentscope"],
            purpose="广泛覆盖现有技术"
        ))

        # 2. 精准检索
        precise_query = self._build_precise_query()
        if precise_query:
            queries.append(SearchQuery(
                type="精准检索",
                query=precise_query,
                databases=["CNIPA", "EPO Espacenet"],
                purpose="精准命中核心技术方案"
            ))

        # 3. 同族专利追踪
        family_query = self._build_family_query()
        if family_query:
            queries.append(SearchQuery(
                type="同族专利追踪",
                query=family_query,
                databases=["EPO Espacenet", "WIPO Patentscope"],
                purpose="追踪同族专利"
            ))

        # 4. 申请人追踪
        applicant_query = self._build_applicant_query()
        if applicant_query:
            queries.append(SearchQuery(
                type="申请人追踪",
                query=applicant_query,
                databases=["CNIPA", "USPTO"],
                purpose="覆盖竞争对手专利"
            ))

        return queries

    def _build_broad_query(self) -> str:
        keyword_str = " OR ".join(self.expanded_keywords[:10])
        ipc_str = " OR ".join(self.elements.get("tech_field_ipc", []))
        if ipc_str:
            return f"({keyword_str}) AND ({ipc_str})"
        return keyword_str

    def _build_precise_query(self) -> str:
        keyword_str = " OR ".join(self.expanded_keywords[:5])
        ipc_str = " OR ".join(self.elements.get("tech_field_ipc", []))
        problems = self.elements.get("tech_problems", [])
        problem_str = " OR ".join(problems[:2]) if problems else ""

        parts = [f"({keyword_str})"]
        if ipc_str:
            parts.append(f"({ipc_str})")
        if problem_str:
            parts.append(f"({problem_str})")

        return " AND ".join(parts)

    def _build_family_query(self) -> str:
        ipc_str = " OR ".join(self.elements.get("tech_field_ipc", []))
        return ipc_str

    def _build_applicant_query(self) -> str:
        return ""


def adapt_query_for_database(query: str, database: str) -> str:
    """适配检索式到特定数据库语法"""
    return query


def generate_search_queries(elements: Dict) -> List[SearchQuery]:
    """便捷函数：基于交底书要素生成检索式"""
    generator = SearchStrategyGenerator(elements)
    return generator.generate_search_queries()


if __name__ == "__main__":
    sample_elements = {
        "tech_field": "茶叶加工技术领域",
        "tech_field_ipc": ["A23F3/06", "A23F3/08"],
        "tech_problems": ["去除茶叶苦味", "提高茶汤口感"],
        "tech_features": [
            "使用酶解处理茶叶鲜叶",
            "45℃恒温干燥2小时"
        ]
    }

    queries = generate_search_queries(sample_elements)
    print("自动生成的检索式：")
    for i, q in enumerate(queries, 1):
        print(f"\n检索式{i}（{q.type}）：{q.query}")
        print(f"  数据库：{', '.join(q.databases)}")