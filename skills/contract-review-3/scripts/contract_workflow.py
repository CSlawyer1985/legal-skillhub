#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交互式合同审核工作流
====================

提供交互式的附加功能选择流程。

使用方法：
    from contract_workflow import InteractiveReview

    workflow = InteractiveReview()
    result = workflow.run()
"""

import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

# 导入审核模块
try:
    from .parse_contract import ContractParser
    from .classify_contract import ContractClassifier
    from .risk_review import RiskReviewEngine, RiskLevel
    from .export_report_v2 import EnhancedReportGenerator
    from .track_changes_docx import create_track_changes_docx, create_compatible_docx
except ImportError:
    sys.path.insert(0, os.path.dirname(__file__))
    from parse_contract import ContractParser
    from classify_contract import ContractClassifier
    from risk_review import RiskReviewEngine, RiskLevel
    from export_report_v2 import EnhancedReportGenerator
    from track_changes_docx import create_track_changes_docx, create_compatible_docx


class InteractiveReview:
    """
    交互式合同审核工作流

    功能：
    1. 基础审核（自动执行）
    2. 交互式附加功能选择
    3. 修订稿生成（支持双重格式）
    """

    def __init__(self, workspace_path: str = None):
        """
        初始化工作流

        Args:
            workspace_path: 工作目录路径（用于保存输出文件）
        """
        self.workspace_path = workspace_path or os.getcwd()
        self.contract_text = None
        self.contract_type = None
        self.basic_report = None
        self.enhanced_generator = None

        # 功能开关
        self.enable_gap_analysis = True  # 默认启用模板比对
        self.enable_professional_review = False
        self.enable_revision = False

        # 选择选项映射
        self.option_map = {
            '1': 'network',
            '2': 'template',
            '3': 'revision',
            '4': 'all'
        }

    def set_contract(self, text: str, contract_type: str = None):
        """设置待审核合同"""
        self.contract_text = text
        self.contract_type = contract_type

    def run_basic_review(self) -> str:
        """执行基础审核"""
        print("\n" + "="*60)
        print("📋 合同审核进行中...")
        print("="*60)

        # Phase 0: 解析
        print("  ⏳ Phase 0: 合同解析...")
        parser = ContractParser(self.contract_text)
        parsed = parser.parse()

        # Phase 1: 类型识别
        print("  ⏳ Phase 1: 合同类型识别...")
        classifier = ContractClassifier(self.contract_text)
        classified = classifier.classify()
        detected_type = classified.get('contract_type', '未识别')
        confidence = classified.get('confidence', 0)

        if self.contract_type:
            detected_type = self.contract_type
            print(f"  ✅ 合同类型：{detected_type}（用户指定）")
        else:
            print(f"  ✅ 合同类型：{detected_type}（置信度 {confidence:.0%}）")

        # Phase 2: 风险审核
        print("  ⏳ Phase 2: 风险条款审核...")
        risk_engine = RiskReviewEngine(self.contract_text, detected_type)
        reviewed = risk_engine.review()
        risk_score = reviewed.get('risk_score', 0)

        summary = reviewed.get('summary', {})
        high = summary.get('high_risk_count', 0)
        medium = summary.get('medium_risk_count', 0)
        low = summary.get('low_risk_count', 0)

        print(f"  ✅ 风险评分：{risk_score:.0f}/100")
        print(f"     🔴 高风险 {high} 项 | 🟡 中风险 {medium} 项 | 🟢 低风险 {low} 项")

        # 返回基本信息
        return {
            'contract_type': detected_type,
            'confidence': confidence,
            'risk_score': risk_score,
            'risk_summary': summary,
            'parsed': parsed,
            'classified': classified,
            'reviewed': reviewed
        }

    def show_function_selection(self) -> Dict[str, bool]:
        """显示附加功能选择菜单"""
        print("\n" + "="*60)
        print("🎯 请选择附加功能（可多选）")
        print("="*60)
        print("""
  ┌──────────────────────────────────────────────────────────┐
  │  📱 [1] 网络专业资源审查                                   │
  │      └─ 检索最高法指导案例、律师实务文章                   │
  │      └─ 为审核意见提供权威参考                             │
  │                                                           │
  │  📋 [2] 模板比对分析（已启用）                             │
  │      └─ 对照标准模板，发现缺失/偏离条款                    │
  │      └─ 法律合规审查（民法典+司法解释）                    │
  │                                                           │
  │  📝 [3] 修订稿生成（Track Changes）                        │
  │      └─ 生成 Word 原生修订模式文档                         │
  │      └─ 支持接受/拒绝逐条修订                             │
  │                                                           │
  │  🚀 [4] 一键启用全部功能                                   │
  │                                                           │
  │  ⏭  [5] 跳过，继续查看基础报告                            │
  └──────────────────────────────────────────────────────────┘
        """)

        # 获取用户输入
        print("请输入选项编号（多选用空格分隔，如 \"1 3\"）：", end=" ")
        try:
            user_input = input().strip().lower()
        except EOFError:
            user_input = "5"  # 默认跳过

        # 解析选择
        result = {
            'network': False,
            'template': True,  # 默认启用
            'revision': False
        }

        if not user_input or user_input == '5':
            print("\n  ⏭ 继续查看基础报告...")
            return result

        if user_input == '4':
            # 全部启用
            result = {'network': True, 'template': True, 'revision': True}
            print("\n  ✅ 已启用全部附加功能")
            return result

        # 解析多选
        selected = user_input.split()
        for opt in selected:
            if opt == '1':
                result['network'] = True
                print("  ✅ 已启用：网络专业资源审查")
            elif opt == '2':
                result['template'] = True
                print("  ✅ 已启用：模板比对分析")
            elif opt == '3':
                result['revision'] = True
                print("  ✅ 已启用：修订稿生成")
            elif opt == '5':
                print("  ⏭ 已跳过附加功能")

        return result

    def run_enhanced_review(self, options: Dict[str, bool]) -> EnhancedReportGenerator:
        """执行增强审核"""
        print("\n" + "="*60)
        print("🔍 执行增强审核...")
        print("="*60)

        # 创建增强报告生成器
        generator = EnhancedReportGenerator(
            text=self.contract_text,
            contract_type=self.contract_type,
            style='markdown',
            enable_gap_analysis=options.get('template', True),
            enable_professional_review=options.get('network', False),
            enable_revision=options.get('revision', False)
        )

        self.enhanced_generator = generator

        # 显示各阶段进度
        print("  ⏳ 模板检索与比对...")
        if options.get('template'):
            templates = getattr(generator, 'template_matches', [])
            if templates:
                best = templates[0]
                print(f"     ✅ 找到 {len(templates)} 个相似模板")
                print(f"     📄 最佳匹配：{best.template_name}（{best.similarity_score:.1f}%）")

                gaps = getattr(generator, 'gap_result', {}).get('gaps', [])
                if gaps:
                    print(f"     ⚠️ 发现 {len(gaps)} 处差异")
            else:
                print("     ⚠️ 未找到相似模板")

        print("  ⏳ 法律合规审核...")
        legal_results = getattr(generator, 'legal_results', [])
        if legal_results:
            non_compliant = sum(1 for r in legal_results if r.get('status') != 'compliant')
            print(f"     ✅ 完成法律合规检查（{non_compliant} 项问题）")

        if options.get('network'):
            print("  ⏳ 网络专业资源审查...")
            prof_result = getattr(generator, 'professional_result', None)
            if prof_result:
                findings = prof_result.findings
                print(f"     ✅ 找到 {len(findings)} 篇相关资源")
            else:
                print("     ⚠️ 暂无可用网络资源")

        if options.get('revision'):
            print("  ⏳ 生成修订稿...")
            changes = getattr(generator, 'revision_changes', [])
            if changes:
                print(f"     ✅ 生成 {len(changes)} 项修订建议")
            else:
                print("     ⚠️ 未发现需要修订的内容")

        return generator

    def generate_reports(self, generator: EnhancedReportGenerator,
                        basename: str = "合同审核报告") -> Dict[str, str]:
        """生成各种格式的报告"""
        print("\n" + "="*60)
        print("📄 生成报告文件...")
        print("="*60)

        outputs = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_basename = basename.replace(' ', '_').replace('/', '_')

        # 1. Markdown 报告
        md_path = os.path.join(self.workspace_path, f"{safe_basename}_{timestamp}.md")
        generator.save(md_path.replace('.md', ''))  # save() 会添加扩展名
        outputs['markdown'] = md_path
        print(f"  ✅ Markdown 报告：{os.path.basename(md_path)}")

        # 2. 专业版 Word 报告
        docx_path = os.path.join(self.workspace_path, f"{safe_basename}_专业版_{timestamp}.docx")
        result = generator.save_professional_docx(docx_path)
        if result:
            outputs['docx'] = result
            print(f"  ✅ Word 报告（专业版）：{os.path.basename(result)}")

        # 3. 修订稿（Track Changes）
        if generator.enable_revision and hasattr(generator, 'revision_changes') and generator.revision_changes:
            revision_path = os.path.join(self.workspace_path, f"{safe_basename}_修订稿_{timestamp}.docx")

            # 优先尝试原生修订模式
            success = create_track_changes_docx(
                original_text=self.contract_text,
                changes=generator.revision_changes,
                output_path=revision_path,
                author="AI审核助手"
            )

            if success:
                outputs['track_changes'] = revision_path
                print(f"  ✅ Word 修订稿（Track Changes）：{os.path.basename(revision_path)}")
            else:
                # 回退到兼容模式
                compat_path = revision_path.replace('.docx', '_兼容版.docx')
                create_compatible_docx(
                    original_text=self.contract_text,
                    changes=generator.revision_changes,
                    output_path=compat_path,
                    author="AI审核助手"
                )
                outputs['compatible'] = compat_path
                print(f"  ✅ Word 修订稿（兼容版）：{os.path.basename(compat_path)}")

        return outputs

    def run(self) -> Dict:
        """
        运行完整的交互式审核流程

        Returns:
            审核结果字典
        """
        if not self.contract_text:
            return {'error': '请先设置合同文本（使用 set_contract 方法）'}

        # Step 1: 基础审核
        basic_result = self.run_basic_review()

        # Step 2: 交互式选择附加功能
        options = self.show_function_selection()

        # Step 3: 执行增强审核
        enhanced_generator = self.run_enhanced_review(options)

        # Step 4: 生成报告
        outputs = self.generate_reports(enhanced_generator)

        # Step 5: 返回结果
        return {
            'basic': basic_result,
            'enhanced': enhanced_generator,
            'report': enhanced_generator.generate(),
            'outputs': outputs,
            'options': options
        }

    def summary(self, result: Dict):
        """输出审核结果摘要"""
        basic = result.get('basic', {})
        options = result.get('options', {})
        outputs = result.get('outputs', {})

        print("\n" + "="*60)
        print("📊 审核完成！结果摘要")
        print("="*60)

        # 基本信息
        print(f"\n  📄 合同类型：{basic.get('contract_type', '未知')}")
        print(f"  ⚠️  风险评分：{basic.get('risk_score', 0):.0f}/100")

        risk_summary = basic.get('risk_summary', {})
        print(f"  🔴 高风险 {risk_summary.get('high_risk_count', 0)} 项")
        print(f"  🟡 中风险 {risk_summary.get('medium_risk_count', 0)} 项")
        print(f"  🟢 低风险 {risk_summary.get('low_risk_count', 0)} 项")

        # 启用的功能
        print("\n  🎯 已启用功能：")
        if options.get('template'):
            print("    ✓ 模板比对分析")
        if options.get('network'):
            print("    ✓ 网络专业资源审查")
        if options.get('revision'):
            print("    ✓ 修订稿生成")

        # 生成的文件
        print("\n  📁 生成文件：")
        for name, path in outputs.items():
            icon = {'markdown': '📝', 'docx': '📄', 'track_changes': '📝', 'compatible': '📝'}.get(name, '📄')
            print(f"    {icon} {os.path.basename(path)}")

        print("\n" + "="*60)
        print("💡 提示：修订稿可直接在 Word 中打开查看和审阅")
        print("="*60)


# 便捷函数
def quick_review(text: str, contract_type: str = None,
                enable_all: bool = False) -> Dict:
    """
    快速审核（默认启用模板比对，可选全部功能）

    Args:
        text: 合同文本
        contract_type: 指定合同类型（可选）
        enable_all: 是否启用全部附加功能

    Returns:
        审核结果
    """
    workflow = InteractiveReview()
    workflow.set_contract(text, contract_type)

    # 执行基础审核
    basic = workflow.run_basic_review()

    # 设置功能选项
    if enable_all:
        options = {'network': True, 'template': True, 'revision': True}
    else:
        options = {'network': False, 'template': True, 'revision': False}

    # 执行增强审核
    enhanced = workflow.run_enhanced_review(options)

    # 生成报告
    outputs = workflow.generate_reports(enhanced)

    return {
        'basic': basic,
        'enhanced': enhanced,
        'report': enhanced.generate(),
        'outputs': outputs
    }


if __name__ == "__main__":
    # 测试
    sample = """
    咨询服务合同

    委托方（甲方）：某科技有限公司
    受托方（乙方）：某律师事务所

    第一条 服务内容
    乙方为甲方提供法律咨询服务。

    第二条 服务费用
    咨询服务费共计人民币50万元整，甲方应于本合同签署后30日内支付。

    第三条 违约责任
    任何一方违约应承担相应法律责任，违约金为合同总价的50%。
    """

    print("=== 交互式合同审核测试 ===\n")

    # 自动测试（不等待输入）
    workflow = InteractiveReview()
    workflow.set_contract(sample)

    # 模拟用户选择 "5"（跳过）
    result = workflow.run()

    workflow.summary(result)

    print("\n报告预览：")
    print(result['report'][:500] + "...")
