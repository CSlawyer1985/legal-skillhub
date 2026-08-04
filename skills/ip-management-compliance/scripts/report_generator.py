"""
报告自动渲染器模块 (Module E)
功能：生成标准化三性检索评估报告，支持Word/Markdown格式
"""

import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReportData:
    """报告数据对象"""
    disclosure_name: str = ""
    tech_field: str = ""
    tech_field_ipc: List[str] = None
    search_date: str = ""
    search_databases: List[str] = None
    exhaustive_check: str = "通过"
    tech_problems: List[str] = None
    tech_features: List[str] = None
    examples: List[Dict] = None
    search_queries: List[Dict] = None
    prior_art: List[Dict] = None
    novelty_conclusion: str = ""
    novelty_reason: str = ""
    creativity_conclusion: str = ""
    creativity_score: float = 0.0
    creativity_reason: str = ""
    utility_conclusion: str = ""
    utility_reason: str = ""
    overall_suggestion: str = ""
    suggestions: List[str] = None

    def __post_init__(self):
        if self.tech_field_ipc is None:
            self.tech_field_ipc = []
        if self.search_databases is None:
            self.search_databases = []
        if self.tech_problems is None:
            self.tech_problems = []
        if self.tech_features is None:
            self.tech_features = []
        if self.examples is None:
            self.examples = []
        if self.search_queries is None:
            self.search_queries = []
        if self.prior_art is None:
            self.prior_art = []
        if self.suggestions is None:
            self.suggestions = []


class ReportGenerator:
    """报告生成器"""

    def __init__(self, report_data: ReportData):
        self.data = report_data

    def generate_markdown(self) -> str:
        """生成Markdown格式报告"""
        lines = []
        lines.append("# 专利三性（新颖性/创造性/实用性）检索评估报告\n")
        lines.append("## 一、基础信息\n")
        lines.append(f"- **交底书名称**：{self.data.disclosure_name or '未命名'}")
        lines.append(f"- **技术领域**：{self.data.tech_field or '未指定'}")
        ipc_str = ", ".join(self.data.tech_field_ipc) if self.data.tech_field_ipc else "未匹配"
        lines.append(f"- **推荐IPC分类号**：{ipc_str}")
        lines.append(f"- **检索日期**：{self.data.search_date or datetime.now().strftime('%Y-%m-%d')}")
        db_str = ", ".join(self.data.search_databases) if self.data.search_databases else "未指定"
        lines.append(f"- **检索数据库**：{db_str}")
        lines.append(f"- **穷尽性校验结果**：{self.data.exhaustive_check}")

        lines.append("\n## 二、核心技术要素提取\n")
        lines.append("### 2.1 要解决的技术问题\n")
        if self.data.tech_problems:
            for i, p in enumerate(self.data.tech_problems, 1):
                lines.append(f"{i}. {p}")
        else:
            lines.append("未提取到技术问题")

        lines.append("\n### 2.2 核心技术方案（技术特征）\n")
        if self.data.tech_features:
            for i, f in enumerate(self.data.tech_features[:10], 1):
                lines.append(f"{i}. {f}")
        else:
            lines.append("未提取到技术特征")

        lines.append("\n## 三、现有技术检索结果\n")
        lines.append("| 序号 | 专利号 | 标题 | 公开日 | 相似度 |")
        lines.append("|------|--------|------|--------|--------|")
        for i, pa in enumerate(self.data.prior_art[:10], 1):
            lines.append(f"| {i} | {pa.get('patent_no', '')} | {pa.get('title', '')[:20]} | {pa.get('publish_date', '')} | {pa.get('similarity', 0):.0%} |")

        lines.append("\n## 四、三性评估结论\n")
        lines.append(f"**新颖性**：{self.data.novelty_conclusion} — {self.data.novelty_reason}")
        lines.append(f"**创造性**：{self.data.creativity_conclusion}（评分{self.data.creativity_score:.1f}/10）— {self.data.creativity_reason}")
        lines.append(f"**实用性**：{self.data.utility_conclusion} — {self.data.utility_reason}")

        lines.append("\n## 五、专利申请建议\n")
        lines.append(f"**综合结论**：{self.data.overall_suggestion}")
        for s in self.data.suggestions:
            lines.append(f"- {s}")

        lines.append(f"\n---\n*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        return "\n".join(lines)


def generate_three_criteria_report(
    disclosure_elements: Dict,
    search_results: Dict,
    evaluation_result: Dict,
    output_format: str = "markdown",
    output_path: str = None
) -> str:
    """便捷函数：生成三性检索评估报告"""
    report_data = ReportData(
        disclosure_name=disclosure_elements.get("name", ""),
        tech_field=disclosure_elements.get("tech_field", ""),
        tech_field_ipc=disclosure_elements.get("tech_field_ipc", []),
        search_date=datetime.now().strftime('%Y-%m-%d'),
        search_databases=search_results.get("databases", []),
        exhaustive_check="通过" if search_results.get("exhaustive_pass", True) else "部分通过",
        tech_problems=disclosure_elements.get("tech_problems", []),
        tech_features=disclosure_elements.get("tech_features", []),
        examples=disclosure_elements.get("examples", []),
        search_queries=search_results.get("queries", []),
        prior_art=search_results.get("prior_art", []),
        novelty_conclusion=evaluation_result.get("novelty", {}).get("conclusion", ""),
        novelty_reason=evaluation_result.get("novelty", {}).get("reason", ""),
        creativity_conclusion=evaluation_result.get("creativity", {}).get("conclusion", ""),
        creativity_score=evaluation_result.get("creativity", {}).get("score", 0.0),
        creativity_reason=evaluation_result.get("creativity", {}).get("reason", ""),
        utility_conclusion=evaluation_result.get("utility", {}).get("conclusion", ""),
        utility_reason=evaluation_result.get("utility", {}).get("reason", ""),
        overall_suggestion=evaluation_result.get("overall", ""),
        suggestions=evaluation_result.get("suggestions", [])
    )

    generator = ReportGenerator(report_data)
    content = generator.generate_markdown()

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return content


if __name__ == "__main__":
    print("报告自动渲染器 (Module E)")
    print("支持格式: Markdown")