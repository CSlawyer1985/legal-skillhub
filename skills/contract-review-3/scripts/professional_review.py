# -*- coding: utf-8 -*-
"""
专业资源审查模块 (professional_review.py)
==========================================

根据合同类型，自动检索网络专业资源（最高人民法院指导案例、
律师实务文章等），提取观点与审核意见结合。

功能特点：
1. 多源检索：最高人民法院官网 + 律师公众号 + 专业网站
2. 观点提取：自动提取与合同相关的风险点和修改建议
3. 来源标注：完整保留题目和网址链接
4. 可选功能：通过 enable 参数控制开关

使用示例：
    from professional_review import ProfessionalResourceReviewer

    reviewer = ProfessionalResourceReviewer(
        contract_text="...",
        contract_type="买卖合同",
        enable=True  # 默认关闭
    )
    results = reviewer.search()
"""

import re
import json
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import quote


class ResourceType(Enum):
    """资源类型枚举"""
    SUPREME_COURT_CASE = "最高人民法院指导案例"      # 最高人民法院发布的指导案例
    HIGH_COURT_CASE = "高级人民法院典型案例"        # 各地高级人民法院典型案例
    LOCAL_COURT_CASE = "地方法院典型案例"            # 各地方法院典型案例
    LAW_FIRM_ARTICLE = "律师事务所专业文章"          # 律师实务解读文章
    WECHAT_ARTICLE = "微信公众号专业文章"            # 微信公众号文章
    ACADEMIC_ARTICLE = "学术研究文章"               # 学术论文、研究文章


@dataclass
class ResourceFinding:
    """专业资源检索结果"""
    # 基本信息
    title: str                    # 文章/案例标题
    url: str                      # 网址链接
    source_type: ResourceType     # 资源类型
    source_name: str              # 来源名称（如"最高人民法院官网"、"XX律师事务所"）

    # 内容摘要
    summary: str                  # 内容摘要

    # 与合同的关联
    related_clause: str           # 关联的合同条款（可选）
    key_points: List[str]        # 关键观点列表

    # 修改建议（结合审核意见）
    suggestions: List[str]       # 修改建议列表

    # 元数据
    publish_date: str = ""        # 发布日期
    relevance_score: float = 0.0  # 相关性评分 (0-1)


@dataclass
class ProfessionalReviewResult:
    """专业资源审查最终结果"""
    contract_type: str
    enable: bool

    # 检索统计
    total_searched: int = 0
    total_found: int = 0

    # 检索结果
    findings: List[ResourceFinding] = field(default_factory=list)

    # 错误信息
    errors: List[str] = field(default_factory=list)


class ProfessionalResourceSearcher:
    """
    网络专业资源搜索引擎

    支持搜索：
    1. 最高人民法院指导案例
    2. 各级法院典型案例
    3. 律师事务所专业文章
    4. 微信公众号法律文章
    """

    # 合同类型对应的搜索关键词
    CONTRACT_KEYWORDS = {
        "买卖合同": ["买卖合同纠纷", "货物买卖", "标的物交付", "所有权转移", "质量异议"],
        "借款合同": ["民间借贷纠纷", "借款合同效力", "利息约定", "担保", "网贷"],
        "租赁合同": ["租赁合同纠纷", "房屋租赁", "租金支付", "优先购买权", "装饰装修"],
        "建设工程合同": ["建设工程纠纷", "施工合同", "工程款", "优先受偿权", "挂靠"],
        "技术合同": ["技术合同纠纷", "技术开发", "技术转让", "技术咨询", "知识产权"],
        "委托合同": ["委托合同纠纷", "代理", "居间", "行纪", "受托人义务"],
        "物业服务合同": ["物业服务纠纷", "物业管理", "业主委员会", "公共收益"],
        "运输合同": ["运输合同纠纷", "货物运输", "旅客运输", "承运人责任"],
        "保证合同": ["保证合同纠纷", "担保责任", "连带保证", "一般保证", "保证期间"],
        "融资租赁合同": ["融资租赁纠纷", "融资租赁合同效力", "租金支付"],
        "保管合同": ["保管合同纠纷", "寄存", "保管人责任", "有偿保管"],
        "仓储合同": ["仓储合同纠纷", "仓储保管", "入库验收", "仓单"],
        "保理合同": ["保理合同纠纷", "应收账款", "保理商", "追索权"],
        "中介合同": ["中介合同纠纷", "居间报酬", "跳单", "独家代理"],
        "行纪合同": ["行纪合同纠纷", "行纪人", "委托卖出", "委托买入"],
        "赠与合同": ["赠与合同纠纷", "撤销赠与", "公益捐赠", "道德义务"],
        "合伙合同": ["合伙纠纷", "合伙企业", "退伙", "合伙财产", "合伙债务"],
        "土地承包合同": ["土地承包纠纷", "农村土地", "流转", "承包经营权"],
    }

    # 权威来源列表
    AUTHORITATIVE_SOURCES = [
        {
            "name": "最高人民法院",
            "url_pattern": "https://www.court.gov.cn/*",
            "type": ResourceType.SUPREME_COURT_CASE,
            "priority": 1
        },
        {
            "name": "中国裁判文书网",
            "url_pattern": "https://wenshu.court.gov.cn/*",
            "type": ResourceType.LOCAL_COURT_CASE,
            "priority": 2
        },
        {
            "name": "中国法院网",
            "url_pattern": "https://www.chinacourt.org/*",
            "type": ResourceType.HIGH_COURT_CASE,
            "priority": 3
        },
        {
            "name": "无讼案例",
            "url_pattern": "https://www.itslaw.com/*",
            "type": ResourceType.LOCAL_COURT_CASE,
            "priority": 4
        },
        {
            "name": "威科先行",
            "url_pattern": "https://law.wkinfo.com.cn/*",
            "type": ResourceType.ACADEMIC_ARTICLE,
            "priority": 5
        },
    ]

    def __init__(self, contract_type: str):
        self.contract_type = contract_type
        self.search_keywords = self.CONTRACT_KEYWORDS.get(
            contract_type,
            [contract_type, f"{contract_type}纠纷", "合同风险"]
        )

    def build_search_queries(self) -> List[str]:
        """构建搜索查询语句"""
        queries = []

        # 基础查询：合同类型 + 纠纷/风险
        for keyword in self.search_keywords[:2]:
            queries.extend([
                f"最高人民法院 指导案例 {keyword}",
                f"最高人民法院 公报案例 {keyword}",
                f"最高法 典型案例 {keyword}",
            ])

        # 扩展查询：风险点 + 修改建议
        queries.extend([
            f"{self.contract_type} 合同风险 点 律师实务",
            f"{self.contract_type} 合同审查 注意事项",
            f"{self.contract_type} 纠纷 裁判要点 律师解读",
        ])

        return list(set(queries))  # 去重

    def search(self) -> List[Dict[str, Any]]:
        """
        执行网络搜索（通过外部搜索API）

        返回格式：
        [
            {
                "title": "文章标题",
                "url": "网址",
                "snippet": "摘要内容",
                "source": "来源网站"
            },
            ...
        ]
        """
        from scripts.web_search import web_search

        all_results = []
        queries = self.build_search_queries()

        for query in queries[:5]:  # 限制查询数量
            try:
                results = web_search(query, max_results=5)
                all_results.extend(results)
            except Exception as e:
                print(f"搜索失败 [{query}]: {e}")

        # 按URL去重
        seen = set()
        unique_results = []
        for r in all_results:
            url = r.get('url', '')
            if url and url not in seen:
                seen.add(url)
                unique_results.append(r)

        return unique_results


class ProfessionalResourceReviewer:
    """
    专业资源审查器

    整合网络专业资源，为合同审核提供专家级参考意见。

    使用方式：
        reviewer = ProfessionalResourceReviewer(
            contract_text="...",
            contract_type="买卖合同",
            enable=True  # 可选，默认False
        )
        result = reviewer.search()
    """

    def __init__(
        self,
        contract_text: str,
        contract_type: str,
        enable: bool = False,
        max_results: int = 10
    ):
        """
        初始化专业资源审查器

        参数:
            contract_text: 合同文本内容
            contract_type: 合同类型
            enable: 是否启用网络检索（默认关闭，需用户主动选择）
            max_results: 最大检索结果数
        """
        self.contract_text = contract_text
        self.contract_type = contract_type
        self.enable = enable
        self.max_results = max_results

        # 提取合同关键条款（用于关联检索结果）
        self.contract_clauses = self._extract_key_clauses()

    def _extract_key_clauses(self) -> List[str]:
        """提取合同中的关键条款名称"""
        clauses = []

        # 常见条款关键词
        clause_patterns = [
            r'第[一二三四五六七八九十百零\d]+条[^\n]*',  # 条款编号
            r'[第一二三四五六七八九十]+[、\.][^\n]*',     # 中文编号
            r'(?:标的|质量|数量|价款|付款|交付|验收|违约|争议|风险|所有权)',  # 关键概念
        ]

        for pattern in clause_patterns:
            matches = re.findall(pattern, self.contract_text)
            clauses.extend(matches)

        return list(set(clauses))[:20]  # 去重，最多20条

    def _classify_source_type(self, url: str, title: str) -> ResourceType:
        """根据URL和标题判断资源类型"""
        title_lower = title.lower()
        url_lower = url.lower()

        if 'court.gov.cn' in url_lower or '指导案例' in title:
            return ResourceType.SUPREME_COURT_CASE
        elif 'highcourt' in url_lower or '高级人民法院' in title:
            return ResourceType.HIGH_COURT_CASE
        elif 'wenshu.court' in url_lower:
            return ResourceType.LOCAL_COURT_CASE
        elif 'lawfirm' in url_lower or '律师' in title:
            return ResourceType.LAW_FIRM_ARTICLE
        elif 'weixin' in url_lower or '公众号' in title:
            return ResourceType.WECHAT_ARTICLE
        else:
            return ResourceType.ACADEMIC_ARTICLE

    def _calculate_relevance(self, result: Dict, contract_clause: str = "") -> float:
        """计算检索结果与合同的相关性评分"""
        score = 0.5  # 基础分

        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        url = result.get('url', '').lower()

        # 合同类型关键词匹配
        if self.contract_type.lower() in title:
            score += 0.2

        # 最高人民法院来源
        if 'court.gov.cn' in url:
            score += 0.15

        # 裁判案例类
        if any(k in title for k in ['案例', '裁判', '判决', '纠纷']):
            score += 0.1

        # 实务指导类
        if any(k in title for k in ['实务', '解读', '分析', '建议', '风险']):
            score += 0.1

        return min(score, 1.0)

    def _extract_key_points(self, snippet: str) -> List[str]:
        """从摘要中提取关键观点"""
        points = []

        # 提取分号/句号分隔的独立观点
        sentences = re.split(r'[；;。]', snippet)
        for s in sentences:
            s = s.strip()
            if len(s) > 10 and len(s) < 200:  # 过滤过短或过长的句子
                points.append(s)

        return points[:3]  # 最多3个观点

    def _generate_suggestions(self, result: Dict, finding: ResourceFinding) -> List[str]:
        """根据检索结果生成修改建议"""
        suggestions = []

        title = result.get('title', '')
        snippet = result.get('snippet', '')

        # 提取建议性语句
        suggestion_patterns = [
            r'建议[^\n。；]{10,100}',
            r'应当[^\n。；]{10,100}',
            r'可以[^\n。；]{10,100}',
            r'必须[^\n。；]{10,100}',
            r'注意[^\n。；]{10,100}',
            r'应当注意[^\n。；]{10,100}',
            r'必须注意[^\n。；]{10,100}',
        ]

        for pattern in suggestion_patterns:
            matches = re.findall(pattern, snippet)
            suggestions.extend(matches)

        # 如果没有提取到，生成通用建议
        if not suggestions:
            suggestions.append(
                f"建议参照\"{title}\"中的观点完善{self.contract_type}相关条款"
            )

        return suggestions[:2]  # 最多2条建议

    def search(self) -> ProfessionalReviewResult:
        """
        执行专业资源检索

        返回 ProfessionalReviewResult，包含：
        - 检索到的专业资源列表
        - 每个资源的观点和建议
        - 完整的出处信息（标题+链接）
        """
        result = ProfessionalReviewResult(
            contract_type=self.contract_type,
            enable=self.enable
        )

        if not self.enable:
            result.errors.append("网络检索功能已关闭")
            return result

        # 执行搜索
        try:
            searcher = ProfessionalResourceSearcher(self.contract_type)
            raw_results = searcher.search()

            result.total_searched = len(raw_results)

            # 处理搜索结果
            for r in raw_results[:self.max_results]:
                try:
                    title = r.get('title', '未获取到标题')
                    url = r.get('url', '#')
                    snippet = r.get('snippet', '')
                    source = r.get('source', '网络来源')

                    finding = ResourceFinding(
                        title=title,
                        url=url,
                        source_type=self._classify_source_type(url, title),
                        source_name=source or self._classify_source_name(url),
                        summary=snippet[:300] if snippet else '未获取到摘要',
                        related_clause=self._match_related_clause(title, snippet),
                        key_points=self._extract_key_points(snippet),
                        suggestions=self._generate_suggestions(r, None),
                        publish_date=r.get('date', ''),
                        relevance_score=self._calculate_relevance(r)
                    )

                    result.findings.append(finding)

                except Exception as e:
                    result.errors.append(f"处理结果失败: {str(e)}")

            result.total_found = len(result.findings)

            # 如果网络搜索失败，尝试使用预置资源
            if result.total_found == 0:
                self._load_fallback_resources(result)

        except Exception as e:
            result.errors.append(f"搜索执行失败: {str(e)}")
            # 尝试使用预置资源
            self._load_fallback_resources(result)

        return result

    def _load_fallback_resources(self, result: ProfessionalReviewResult):
        """加载预置的专业资源"""
        try:
            from .web_search import get_fallback_resources

            fallback = get_fallback_resources(self.contract_type)
            result.total_searched = len(fallback)

            for r in fallback:
                finding = ResourceFinding(
                    title=r.get('title', ''),
                    url=r.get('url', '#'),
                    source_type=ResourceType.SUPREME_COURT_CASE if '最高人民法院' in r.get('source_name', '') else ResourceType.LAW_FIRM_ARTICLE,
                    source_name=r.get('source_name', '预置资源'),
                    summary=r.get('summary', ''),
                    related_clause='合同通用条款',
                    key_points=[r.get('summary', '')] if r.get('summary') else [],
                    suggestions=[f"建议查阅：{r.get('title', '')}了解相关法律规定"],
                    publish_date='',
                    relevance_score=0.8
                )
                result.findings.append(finding)

            result.total_found = len(result.findings)

        except Exception as e:
            result.errors.append(f"加载预置资源失败: {str(e)}")

    def _classify_source_name(self, url: str) -> str:
        """根据URL提取来源名称"""
        if 'court.gov.cn' in url:
            return '最高人民法院'
        elif 'wenshu.court' in url:
            return '中国裁判文书网'
        elif 'chinacourt.org' in url:
            return '中国法院网'
        elif 'itslaw.com' in url:
            return '无讼案例'
        elif 'law.wkinfo' in url:
            return '威科先行'
        else:
            return '网络来源'

    def _match_related_clause(self, title: str, snippet: str) -> str:
        """匹配与合同条款的关联"""
        combined = title + snippet

        # 常见条款匹配
        clause_mapping = {
            '标的': '标的物条款',
            '质量': '质量条款',
            '价款': '价款条款',
            '付款': '付款条款',
            '交付': '交付条款',
            '验收': '验收条款',
            '违约': '违约责任条款',
            '风险': '风险转移条款',
            '所有': '所有权条款',
            '检验': '检验条款',
            '保修': '保修条款',
            '争议': '争议解决条款',
            '适用': '法律适用条款',
            '通知': '通知条款',
            '不可抗力': '不可抗力条款',
        }

        for keyword, clause in clause_mapping.items():
            if keyword in combined:
                return clause

        return '合同通用条款'


def search_professional_resources(
    contract_text: str,
    contract_type: str,
    enable: bool = False,
    max_results: int = 10
) -> ProfessionalReviewResult:
    """
    便捷函数：搜索专业资源

    参数:
        contract_text: 合同文本
        contract_type: 合同类型
        enable: 是否启用（默认关闭）
        max_results: 最大结果数

    返回:
        ProfessionalReviewResult 对象
    """
    reviewer = ProfessionalResourceReviewer(
        contract_text=contract_text,
        contract_type=contract_type,
        enable=enable,
        max_results=max_results
    )
    return reviewer.search()


# 测试代码
if __name__ == "__main__":
    sample_contract = """
    买卖合同

    第一条 标的物
    甲方向乙方购买电脑设备100台。

    第二条 价款
    合同总价为人民币50万元。

    第三条 付款条件
    甲方应于收货后30日内付款。

    第四条 违约责任
    任何一方违约应承担合同总价款50%的违约金。
    """

    print("=== 专业资源审查测试 ===\n")

    # 测试（不启用网络搜索）
    result = search_professional_resources(
        contract_text=sample_contract,
        contract_type="买卖合同",
        enable=False  # 默认关闭
    )

    print(f"功能状态: {'已启用' if result.enable else '已关闭'}")
    print(f"检索结果: {result.total_found} 条")
    print("\n提示: 如需启用网络检索，请设置 enable=True")
