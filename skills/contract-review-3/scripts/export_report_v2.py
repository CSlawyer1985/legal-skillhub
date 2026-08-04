#!/usr/bin/env python3
"""
合同审核报告生成器 - Phase 3（增强版）
功能：整合解析、识别、审核、合同库检索、差异比对，生成结构化报告
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

# 导入同目录下的模块（兼容相对导入和绝对导入）
try:
    from .parse_contract import ContractParser
    from .classify_contract import ContractClassifier
    from .risk_review import RiskReviewEngine, RiskLevel
except ImportError:
    # 绝对导入模式
    from parse_contract import ContractParser
    from classify_contract import ContractClassifier
    from risk_review import RiskReviewEngine, RiskLevel


class EnhancedReportGenerator:
    """增强版审核报告生成器"""

    def __init__(self, text: str, contract_type: str = None, style: str = 'markdown',
                 enable_gap_analysis: bool = True, enable_professional_review: bool = False,
                 enable_revision: bool = False):
        """
        初始化报告生成器

        Args:
            text: 合同文本内容
            contract_type: 可选的指定合同类型
            style: 输出格式 ('markdown' | 'docx' | 'json')
            enable_gap_analysis: 是否启用差异比对
            enable_professional_review: 是否启用网络专业资源审查（附加功能）
            enable_revision: 是否生成修订稿（附加功能）
        """
        self.text = text
        self.contract_type = contract_type
        self.style = style
        self.enable_gap_analysis = enable_gap_analysis
        self.enable_professional_review = enable_professional_review
        self.enable_revision = enable_revision

        # 执行各阶段分析
        self._run_analysis()

    def _run_analysis(self):
        """运行各阶段分析"""
        # Phase 0: 合同解析
        parser = ContractParser(self.text)
        self.parsed = parser.parse()

        # Phase 1: 类型识别
        classifier = ContractClassifier(self.text)
        self.classified = classifier.classify()

        # 如果用户指定了类型，覆盖分类结果
        if self.contract_type:
            self.classified['contract_type'] = self.contract_type
            self.classified['specified'] = True
        else:
            self.classified['specified'] = False

        # Phase 2: 风险审核（使用最终确定的类型）
        detected_type = self.classified.get('contract_type')
        risk_engine = RiskReviewEngine(self.text, detected_type)
        self.reviewed = risk_engine.review()

        # Phase 2.5: 合同库检索 + 差异比对
        if self.enable_gap_analysis:
            self._run_gap_analysis(detected_type)

        # Phase 3: 网络专业资源审查（可选附加功能）
        if self.enable_professional_review:
            self._run_professional_review(detected_type)

        # Phase 4: 修订稿生成（可选附加功能）
        if self.enable_revision:
            self._run_revision()

    def _run_gap_analysis(self, detected_type: str):
        """运行差异比对分析"""
        try:
            try:
                from .library_search import ContractLibrarySearch
                from .gap_analysis import GapAnalysisEngine
            except ImportError:
                from library_search import ContractLibrarySearch
                from gap_analysis import GapAnalysisEngine

            # 检索相似模板
            search = ContractLibrarySearch()
            templates = search.search(self.text, detected_type, top_k=3)
            self.template_matches = templates

            if templates:
                # 获取最佳匹配模板内容
                best_template = templates[0]
                template_content = search.get_template_content(best_template.template_path)
                self.template_content = template_content

                # 执行差异比对（启用法律合规审核）
                gap_engine = GapAnalysisEngine(
                    self.text, template_content, detected_type,
                    enable_legal_check=True
                )
                self.gap_result = gap_engine.analyze()
                self.legal_results = self.gap_result.get('legal_compliance', [])
            else:
                self.template_matches = []
                self.template_content = ""
                self.gap_result = {'summary': {}, 'gaps': [], 'missing_clauses': [], 'legal_compliance': []}
                self.legal_results = []

        except ImportError as e:
            print(f"差异分析模块导入失败: {e}")
            self.template_matches = []
            self.template_content = ""
            self.gap_result = {'summary': {}, 'gaps': [], 'missing_clauses': [], 'legal_compliance': []}
            self.legal_results = []
        except Exception as e:
            print(f"差异分析执行失败: {e}")
            self.template_matches = []
            self.template_content = ""
            self.gap_result = {'summary': {}, 'gaps': [], 'missing_clauses': [], 'legal_compliance': []}
            self.legal_results = []

    def _run_professional_review(self, detected_type: str):
        """运行网络专业资源审查"""
        try:
            try:
                from .professional_review import ProfessionalResourceReviewer
            except ImportError:
                from professional_review import ProfessionalResourceReviewer

            reviewer = ProfessionalResourceReviewer(
                contract_text=self.text,
                contract_type=detected_type,
                enable=True,
                max_results=10
            )
            self.professional_result = reviewer.search()

        except ImportError as e:
            print(f"专业资源审查模块导入失败: {e}")
            self.professional_result = None
        except Exception as e:
            print(f"专业资源审查执行失败: {e}")
            self.professional_result = None

    def _run_revision(self):
        """运行修订稿生成"""
        try:
            try:
                from .contract_revision import ContractReviser
            except ImportError:
                from contract_revision import ContractReviser

            # 收集需要修订的内容
            risk_items = []
            gap_items = []

            # 从风险审核结果中提取风险项
            risks = self.reviewed.get('risks', {})
            for level, items in risks.items():
                for item in items:
                    item['risk_level'] = level.value if hasattr(level, 'value') else str(level)
                    risk_items.append(item)

            # 从差异分析中提取缺失/偏离项
            gaps = self.gap_result.get('gaps', [])
            for gap in gaps:
                if gap.get('type') in ['缺失', '偏离']:
                    gap_items.append(gap)

            revisor = ContractReviser(
                contract_text=self.text,
                review_result=self.reviewed,
                risk_items=risk_items,
                gap_items=gap_items,
                legal_items=self.legal_results
            )

            self.revision_result = revisor
            self.revision_marked_text = revisor.generate_marked_text()
            self.revision_statistics = revisor.generate_statistics()

            # 生成修订项列表（用于 Track Changes）
            self.revision_changes = []
            for change in revisor.changes:
                self.revision_changes.append({
                    'clause_title': change.clause_title,
                    'change_type': change.change_type.value,
                    'original_text': change.original_text,
                    'new_text': change.new_text,
                    'reason': change.reason,
                    'legal_basis': change.legal_basis,
                })

        except ImportError as e:
            print(f"修订稿生成模块导入失败: {e}")
            self.revision_result = None
            self.revision_changes = []
        except Exception as e:
            print(f"修订稿生成执行失败: {e}")
            self.revision_result = None
            self.revision_changes = []

    def save_revision_as_docx(self, output_path: str) -> bool:
        """
        保存修订稿为 Word 文档（带格式版本）

        Args:
            output_path: 输出文件路径

        Returns:
            是否保存成功
        """
        if hasattr(self, 'revision_result') and self.revision_result:
            try:
                self.revision_result.save_as_docx(output_path)
                return True
            except Exception as e:
                print(f"保存修订稿 Word 失败: {e}")
                return False
        return False

    def save_track_changes_docx(self, output_path: str) -> bool:
        """
        保存修订稿为 Word 原生 Track Changes 格式

        这是真正的 Word 修订模式文档，可以在 Word 中直接审阅、接受/拒绝修订。

        Args:
            output_path: 输出文件路径

        Returns:
            是否保存成功
        """
        try:
            try:
                from .track_changes_docx import create_track_changes_docx
            except ImportError:
                from track_changes_docx import create_track_changes_docx

            if hasattr(self, 'revision_changes') and self.revision_changes:
                create_track_changes_docx(
                    original_text=self.text,
                    changes=self.revision_changes,
                    output_path=output_path,
                    author="AI审核助手"
                )
                return True
            else:
                print("没有修订内容需要保存")
                return False

        except ImportError as e:
            print(f"Track Changes 模块导入失败: {e}")
            return False
        except Exception as e:
            print(f"保存 Track Changes 文档失败: {e}")
            return False

    def _run_learning(self, final_doc_path: str = None):
        """
        运行定稿学习（检查错别字+学习修改模式）

        Args:
            final_doc_path: 用户定稿文档路径（可选）
        """
        try:
            try:
                from .contract_learner import ContractLearner, analyze_final_document
            except ImportError:
                from contract_learner import ContractLearner, analyze_final_document

            if final_doc_path:
                # 分析用户定稿
                result = analyze_final_document(
                    final_doc_path=final_doc_path,
                    ai_suggestions_path=None,  # 可以传入AI修订稿进行对比学习
                    learning_data_path=final_doc_path.replace('.docx', '_learning.json')
                )
                self.learning_result = result
            else:
                # 仅检查当前合同的错别字和病句
                learner = ContractLearner()
                learner.document_text = self.text
                learner.document_name = "当前审核合同"
                issues = learner.check_issues()
                learner.issues = issues
                self.learning_result = {
                    'issues_count': len(issues),
                    'issues_report': learner.format_issues_report(),
                    'patterns_report': learner.format_patterns_report(),
                }

        except ImportError as e:
            print(f"定稿学习模块导入失败: {e}")
            self.learning_result = None
        except Exception as e:
            print(f"定稿学习执行失败: {e}")
            self.learning_result = None

    def analyze_final_document(self, final_doc_path: str) -> dict:
        """
        分析用户定稿文档

        Args:
            final_doc_path: 用户定稿文档路径

        Returns:
            分析结果字典，包含：
            - issues_report: 错别字/病句报告
            - patterns_report: 修改模式报告
            - suggestions: 改进建议
        """
        self._run_learning(final_doc_path)
        return self.learning_result or {}
        return False

    def generate(self) -> str:
        """生成报告"""
        if self.style == 'json':
            return self._generate_json()
        else:
            return self._generate_markdown()

    def _generate_markdown(self) -> str:
        """生成 Markdown 格式报告"""
        basic = self.parsed.get('basic_info', {})
        classified = self.classified
        summary = self.reviewed.get('summary', {})
        risks = self.reviewed.get('risks', {})

        # 标题
        report = f"""# 合同审核报告

**生成时间**：{datetime.now().strftime('%Y年%m月%d日 %H:%M')}
**合同类型**：{classified.get('contract_type', '未识别')}
**风险评分**：{self.reviewed.get('risk_score', 0):.0f}/100

---

## 一、审核结论

{summary.get('overall_assessment', '无法生成结论')}

| 风险等级 | 数量 |
|---------|------|
| 🔴 高风险 | {summary.get('high_risk_count', 0)} 项 |
| 🟡 中风险 | {summary.get('medium_risk_count', 0)} 项 |
| 🟢 低风险 | {summary.get('low_risk_count', 0)} 项 |

"""

        # 差异分析摘要（如果启用）
        if self.enable_gap_analysis and hasattr(self, 'gap_result'):
            gap_summary = self.gap_result.get('summary', {})
            if gap_summary.get('total_gaps', 0) > 0:
                report += f"""| 模板比对 | 数量 |
|---------|------|
| ⚠️ 缺失条款 | {gap_summary.get('missing_count', 0)} 项 |
| ⚡ 偏离条款 | {gap_summary.get('different_count', 0)} 项 |
| 📋 必要条款缺失 | {gap_summary.get('essential_gaps', 0)} 项 |

"""

        # 合同基本信息
        report += """---

## 二、合同基本信息

| 字段 | 内容 |
|-----|------|
"""
        report += f"| 合同名称 | {basic.get('contract_name', '未明确')} |\n"
        report += f"| 甲方（委托方） | {basic.get('party_a', '未明确')} |\n"
        report += f"| 乙方（受托方） | {basic.get('party_b', '未明确')} |\n"
        report += f"| 签署日期 | {basic.get('signing_date', '未明确')} |\n"
        report += f"| 合同金额 | {basic.get('contract_amount', '未明确')} |\n"

        if classified.get('specified'):
            report += f"\n*类型来源：用户指定*\n"
        else:
            report += f"\n*类型识别置信度：{classified.get('confidence', 0):.1f}*\n"

        # 高风险条款
        high_risks = risks.get(RiskLevel.HIGH, [])
        if high_risks:
            report += self._format_risk_section('## 三、🔴 高风险条款（必须修改）', high_risks)

        # 中风险条款
        medium_risks = risks.get(RiskLevel.MEDIUM, [])
        if medium_risks:
            report += self._format_risk_section('## 四、🟡 中风险条款（建议修改）', medium_risks)

        # 差异分析（如果启用）
        if self.enable_gap_analysis and hasattr(self, 'gap_result'):
            report += self._format_gap_section()

        # 低风险条款
        low_risks = risks.get(RiskLevel.LOW, [])
        if low_risks:
            report += self._format_risk_section('## 七、🟢 低风险条款（可保留参考）', low_risks)

        # 关键条款清单
        key_clauses = self.parsed.get('key_clauses', {})
        if key_clauses:
            report += """---

## 八、关键条款摘要

"""
            for clause_type, items in key_clauses.items():
                if items:
                    report += f"**{clause_type}**：\n"
                    for item in items[:3]:
                        content = item.get('content', '')[:100]
                        report += f"- {content}...\n"
                    report += "\n"

        # 网络专业资源参考（可选附加功能）
        if self.enable_professional_review and hasattr(self, 'professional_result'):
            report += self._format_professional_review_section()

        # 修订稿下载链接（可选附加功能）
        if self.enable_revision and hasattr(self, 'revision_result') and self.revision_result:
            report += self._format_revision_section()

        # 页脚
        report += f"""

---

*本报告由 WorkBuddy 合同审核 Skill（v1.1）自动生成*
*仅供参考，最终意见以执业律师判断为准*
"""

        return report

    def _format_risk_section(self, title: str, items: List[Dict]) -> str:
        """格式化风险章节"""
        section = f"\n---\n\n{title}\n\n"
        for i, item in enumerate(items, 1):
            section += f"### {i}. {item['title']}\n\n"
            section += f"- **风险类型**：{item['type']}\n"
            section += f"- **问题描述**：{item['description']}\n"
            section += f"- **修改建议**：{item['suggestion']}\n"
            if item.get('reference'):
                section += f"- **参考依据**：{item['reference']}\n"
            section += "\n"
        return section

    def _format_gap_section(self) -> str:
        """格式化差异分析章节（包括模板比对 + 法律合规审核）"""
        gaps = self.gap_result.get('gaps', [])
        missing = [g for g in gaps if g.get('type') == '缺失']
        different = [g for g in gaps if g.get('type') == '偏离']
        legal_compliance = getattr(self, 'legal_results', [])

        section = "\n---\n\n## 五、📋 模板比对分析\n\n"

        # 比对摘要
        if self.template_matches:
            best = self.template_matches[0]
            section += f"**参照模板**：{best.template_name}\n"
            section += f"**相似度**：{best.similarity_score:.1f}%\n\n"

        if not gaps and not legal_compliance:
            section += "✅ 未发现明显差异\n\n"
            return section

        # 缺失条款
        if missing:
            section += "### ⚠️ 缺失条款\n\n"
            for item in missing:
                legal_basis = item.get('legal_basis', '')
                legal_source = item.get('legal_source', '')
                
                section += f"**{item['clause']}**（{item['importance']}）\n\n"
                section += f"- 差异：{item['difference']}\n"
                section += f"- 建议：{item['suggestion']}\n"
                if legal_basis:
                    section += f"- 法律依据：{legal_basis}\n"
                if legal_source and legal_source != '通用':
                    section += f"- 法律来源：{legal_source}\n"
                section += "\n"

        # 偏离条款
        if different:
            section += "### ⚡ 偏离条款\n\n"
            for item in different:
                legal_basis = item.get('legal_basis', '')
                
                section += f"**{item['clause']}**（{item['importance']}）\n\n"
                section += f"- 差异：{item['difference']}\n"
                section += f"- 建议：{item['suggestion']}\n"
                if legal_basis:
                    section += f"- 法律依据：{legal_basis}\n"
                section += "\n"

        # 法律合规报告
        if legal_compliance:
            section += self._format_legal_compliance_section()

        return section

    def _format_legal_compliance_section(self) -> str:
        """格式化法律合规审核章节"""
        legal_results = getattr(self, 'legal_results', [])
        
        if not legal_results:
            return ""

        section = "\n---\n\n## 六、⚖️ 法律合规审核报告\n\n"

        # 按法律来源分组
        by_source = {
            '民法典': [],
            '司法解释': [],
            '行政法规': [],
            '行业规范': [],
        }

        for item in legal_results:
            source = item.get('legal_source', '行业规范')
            by_source.setdefault(source, []).append(item)

        # 统计摘要
        section += "| 法律来源 | 问题数 |\n|---------|-------|\n"
        for source, items in by_source.items():
            if items:
                status_counts = {}
                for item in items:
                    status = item.get('status', 'missing')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                missing_count = status_counts.get('missing', 0)
                non_compliant_count = status_counts.get('non_compliant', 0)
                section += f"| {source} | {missing_count + non_compliant_count} 项 |\n"

        section += "\n"

        # 按来源详细列出
        source_order = ['民法典', '司法解释', '行政法规', '行业规范']
        
        for source in source_order:
            items = by_source.get(source, [])
            if not items:
                continue

            if source == '民法典':
                section += "### 📕 民法典规定\n\n"
            elif source == '司法解释':
                section += "### 📗 最高人民法院司法解释\n\n"
            elif source == '行政法规':
                section += "### 📘 国务院行政法规\n\n"
            elif source == '行业规范':
                section += "### 📙 行业规范与实务经验\n\n"

            for item in items:
                status_icon = "❌" if item.get('status') == 'non_compliant' else "⚠️"
                section += f"{status_icon} **{item['clause']}**\n\n"
                section += f"- **法律依据**：{item.get('legal_basis', 'N/A')}\n"
                section += f"- **发现问题**：{item.get('findings', 'N/A')}\n"
                section += f"- **合规建议**：{item.get('suggestion', 'N/A')}\n\n"

        section += "\n"
        return section

    def _format_professional_review_section(self) -> str:
        """格式化网络专业资源参考章节"""
        if not hasattr(self, 'professional_result') or not self.professional_result:
            return ""

        result = self.professional_result
        findings = result.findings

        if not findings:
            return ""

        section = "\n---\n\n## 九、📱 网络专业资源参考\n\n"
        section += "*本章节通过网络检索最高人民法院指导案例、律师实务文章等权威资源，为合同审核提供参考意见*\n\n"

        # 按资源类型分组
        by_type = {}
        for f in findings:
            source_type = f.source_type.value if hasattr(f.source_type, 'value') else str(f.source_type)
            by_type.setdefault(source_type, []).append(f)

        # 统计摘要
        section += "| 资源类型 | 数量 |\n|---------|------|\n"
        for source_type, items in by_type.items():
            section += f"| {source_type} | {len(items)} 篇 |\n"
        section += "\n"

        # 按类型详细列出
        type_order = [
            ('最高人民法院指导案例', '🔴'),
            ('高级人民法院典型案例', '🟠'),
            ('地方法院典型案例', '🟡'),
            ('律师事务所专业文章', '🟢'),
            ('微信公众号专业文章', '🔵'),
            ('学术研究文章', '⚪'),
        ]

        for source_type, icon in type_order:
            items = by_type.get(source_type, [])
            if not items:
                continue

            section += f"### {icon} {source_type}\n\n"

            for i, finding in enumerate(items, 1):
                # 标题 + 链接
                section += f"**{i}. {finding.title}**\n\n"
                section += f"- **出处**：[点击查看]({finding.url})\n"
                section += f"- **来源网站**：{finding.source_name}\n"

                if finding.publish_date:
                    section += f"- **发布日期**：{finding.publish_date}\n"

                # 关联的合同条款
                if finding.related_clause:
                    section += f"- **关联条款**：{finding.related_clause}\n"

                # 关键观点
                if finding.key_points:
                    section += "- **关键观点**：\n"
                    for point in finding.key_points[:2]:
                        section += f"  - {point}\n"

                # 修改建议（结合审核意见）
                if finding.suggestions:
                    section += "- **修改建议**：\n"
                    for suggestion in finding.suggestions[:2]:
                        section += f"  - {suggestion}\n"

                section += "\n"

        # 风险提示
        section += """> **⚠️ 免责声明**：网络检索结果仅供参考，建议结合具体案情和法律专业人士意见综合判断。

"""
        return section

    def _format_revision_section(self) -> str:
        """格式化修订稿章节"""
        if not hasattr(self, 'revision_result') or not self.revision_result:
            return ""

        stats = self.revision_statistics or {}

        section = "\n---\n\n## 十、📝 合同修订稿\n\n"
        section += "*基于以上审核意见自动生成的修订建议*\n\n"

        # 修订统计
        section += "| 修改类型 | 数量 |\n|---------|------|\n"
        section += f"| ✏️ 修改条款 | {stats.get('replacements', 0)} 项 |\n"
        section += f"| ➕ 新增条款 | {stats.get('additions', 0)} 项 |\n"
        section += f"| ➖ 删除条款 | {stats.get('deletions', 0)} 项 |\n"
        section += f"| 💬 批注建议 | {stats.get('comments', 0)} 项 |\n"
        section += f"| **合计** | **{stats.get('total_changes', 0)} 项** |\n\n"

        # 修订说明
        section += """### 📋 修订说明

修订稿标记说明：
- ~~删除线~~ = 需要删除的原文
- **加粗下划线** = 新增内容
- 对应修改建议见下方详细说明

### 📥 下载修订稿

修订稿已生成，可通过以下方式获取：

1. **Word Track Changes 文档（⭐推荐）**：原生修订模式，可直接接受/拒绝修订
   - 删除内容显示为删除线（红色）
   - 新增内容显示为下划线（蓝色）
   - 支持逐条审阅修订
2. **带格式 Word 文档**：包含完整的修订标记和批注
3. **Markdown 文本**：可直接查看修订内容

> 💡 **提示**：请结合审核报告中的具体修改建议，仔细核对每处修订内容。

### 📚 使用说明

**Track Changes 模式**：
1. 在 Word 中打开修订稿文档
2. 切换到「审阅」选项卡
3. 可逐条「接受」或「拒绝」修订
4. 或使用「接受所有修订」一键完成

**定稿后上传**：
> 📤 如您对修订稿进行二次修改后定稿，可上传定稿文档，系统将自动：
> 1. 检查错别字、病句、不通顺表达
> 2. 学习您的修改模式和行文风格
> 3. 为后续审核提供个性化参考

"""
        return section

    def _generate_json(self) -> str:
        """生成 JSON 格式报告"""
        result = {
            'generated_at': datetime.now().isoformat(),
            'basic_info': self.parsed.get('basic_info', {}),
            'classification': {
                'contract_type': self.classified.get('contract_type'),
                'confidence': self.classified.get('confidence'),
                'specified': self.classified.get('specified', False),
                'ranking': self.classified.get('ranking', []),
            },
            'risk_review': self.reviewed,
            'gap_analysis': self.gap_result if self.enable_gap_analysis else None,
            'template_matches': [
                {
                    'name': t.template_name,
                    'score': t.similarity_score,
                    'path': t.template_path,
                }
                for t in getattr(self, 'template_matches', [])
            ] if self.enable_gap_analysis else [],
            'structure': self.parsed.get('structure', []),
            'key_clauses': self.parsed.get('key_clauses', {}),
            'statistics': self.parsed.get('statistics', {}),
        }
        return json.dumps(result, ensure_ascii=False, indent=2)

    def save(self, output_path: str = None) -> str:
        """保存报告到文件"""
        if not output_path:
            base_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'outputs'
            )
            os.makedirs(base_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = os.path.join(base_dir, f'审核报告_{timestamp}')

        if self.style == 'json':
            file_path = f'{output_path}.json'
            content = self._generate_json()
        else:
            file_path = f'{output_path}.md'
            content = self._generate_markdown()

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path

    def save_professional_docx(self, output_path: str = None) -> str:
        """
        保存专业版 Word 报告（精美格式）
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            报告文件路径
        """
        try:
            try:
                from .export_report_professional import create_professional_report
            except ImportError:
                from export_report_professional import create_professional_report
            
            # 准备报告数据
            report_data = {
                'parsed': self.parsed,
                'classified': self.classified,
                'reviewed': self.reviewed,
                'risk_score': self.reviewed.get('risk_score', 0),
                'gap_result': self.gap_result if hasattr(self, 'gap_result') else None,
                'legal_results': self.legal_results if hasattr(self, 'legal_results') else [],
            }
            
            # 生成专业报告
            if not output_path:
                base_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    'outputs'
                )
                os.makedirs(base_dir, exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = os.path.join(base_dir, f'审核报告_{timestamp}.docx')
            
            return create_professional_report(report_data, output_path)
            
        except ImportError as e:
            print(f"专业报告模块导入失败: {e}")
            return None
        except Exception as e:
            print(f"生成专业 Word 报告失败: {e}")
            return None


def main(text: str, contract_type: str = None, style: str = 'markdown',
         output_path: str = None, enable_gap: bool = True,
         enable_professional_review: bool = False,
         enable_revision: bool = False) -> str:
    """
    主入口函数

    Args:
        text: 合同文本内容
        contract_type: 可选的指定合同类型
        style: 输出格式 ('markdown' | 'json')
        output_path: 可选的输出文件路径
        enable_gap: 是否启用差异比对
        enable_professional_review: 是否启用网络专业资源审查（附加功能）
        enable_revision: 是否生成修订稿（附加功能）

    Returns:
        报告内容
    """
    generator = EnhancedReportGenerator(
        text, contract_type, style, enable_gap,
        enable_professional_review, enable_revision
    )

    if output_path:
        saved_path = generator.save(output_path)
        print(f"报告已保存至: {saved_path}")

    return generator.generate()


if __name__ == '__main__':
    sample = """
    咨询服务合同

    合同编号：ZX-2024-001
    委托方（甲方）：某科技有限公司
    受托方（乙方）：某律师事务所

    签署日期：2024年3月15日

    第一条 服务内容
    乙方为甲方提供法律咨询服务。

    第二条 服务费用
    咨询服务费共计人民币50万元。

    第三条 保密条款
    双方应对本合同内容保密。
    """

    report = main(sample, '委托合同', 'markdown')
    print(report)
