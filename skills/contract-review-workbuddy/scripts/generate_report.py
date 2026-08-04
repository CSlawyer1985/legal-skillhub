#!/usr/bin/env python3
"""
报告生成模块 v4.0
将审查结果生成为结构化报告
v4.0 增加：严重等级跨模块归一化、条款库推荐文本富化
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# v4.0 严重等级归一化映射
# 规则引擎产出英文（critical/high/medium/low），LLM 与条款库产出中文，
# 报告层统一归一到中文四档，保证统计、评分、分组口径一致。
SEVERITY_NORMALIZE = {
    'critical': '严重', 'high': '中等', 'medium': '一般', 'low': '提示',
    '严重': '严重', '中等': '中等', '一般': '一般', '提示': '提示',
    '高': '中等', '中': '一般', '低': '提示',
}

DEFAULT_SEVERITY = '一般'


def normalize_severity(value: Any) -> str:
    """将任意来源的严重等级归一为中文四档"""
    if not value:
        return DEFAULT_SEVERITY
    return SEVERITY_NORMALIZE.get(str(value).strip().lower(), None) \
        or SEVERITY_NORMALIZE.get(str(value).strip(), DEFAULT_SEVERITY)


# 严重等级排序权重
SEVERITY_WEIGHTS = {
    '严重': 0,
    '中等': 1,
    '一般': 2,
    '提示': 3,
}

# 严重等级 emoji
SEVERITY_EMOJI = {
    '严重': '🔴',
    '中等': '🟡',
    '一般': '🟢',
    '提示': 'ℹ️',
}

# 评分影响
SCORE_IMPACT = {
    '严重': -15,
    '中等': -8,
    '一般': -3,
    '提示': 0,
}

# 评分说明
SCORE_DESCRIPTIONS = {
    (90, 100): "风险较低，可放心签署",
    (70, 89): "风险中等，建议修改后签署",
    (50, 69): "风险偏高，需要认真修改",
    (0, 49): "风险很高，强烈建议咨询律师",
}


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, enable_clause_match: bool = True):
        """
        Args:
            enable_clause_match: v4.0 是否自动匹配条款库推荐文本
        """
        self.enable_clause_match = enable_clause_match
        self._matcher = None
    
    def _get_matcher(self):
        """v4.0 惰性加载条款匹配器"""
        if not self.enable_clause_match:
            return None
        if self._matcher is None:
            try:
                try:
                    from clause_matcher import ClauseMatcher
                except ImportError:
                    from .clause_matcher import ClauseMatcher
                self._matcher = ClauseMatcher()
                self._matcher.load()
            except Exception as e:
                logger.debug(f"条款匹配器不可用: {e}")
                self.enable_clause_match = False
                return None
        return self._matcher
    
    def _enrich_with_clauses(self, risks: List[Dict], contract_type: str) -> List[Dict]:
        """
        v4.0 为风险点附加条款库推荐文本
        
        写入字段：template（推荐范本）、clause_id、clause_name
        已有 template 的风险点不覆盖
        """
        matcher = self._get_matcher()
        if matcher is None:
            return risks
        
        matched = 0
        for risk in risks:
            if risk.get('template'):
                continue
            try:
                clause = matcher.match(risk, contract_type)
            except Exception as e:
                logger.debug(f"条款匹配失败: {e}")
                continue
            if not clause:
                continue
            risk['template'] = clause.get('recommended_text', '')
            risk['clause_id'] = clause.get('id', '')
            risk['clause_name'] = clause.get('name', '')
            if not risk.get('legal_basis'):
                risk['legal_basis'] = clause.get('legal_basis', '')
            matched += 1
        
        if matched:
            logger.info(f"条款库匹配成功 {matched}/{len(risks)} 个风险点")
        return risks
    
    def generate(self, risks: List[Dict], contract_info: Dict,
                 output_format: str = 'markdown') -> str:
        """
        生成审查报告
        
        Args:
            risks: 风险项列表
            contract_info: 合同基本信息
            output_format: 输出格式（markdown/json）
            
        Returns:
            报告内容字符串
        """
        # v4.0 严重等级归一化：规则引擎产出英文、LLM 产出中文，此处统一口径
        for risk in risks:
            risk['severity'] = normalize_severity(risk.get('severity'))
        
        # v4.0 自动匹配条款库推荐文本
        risks = self._enrich_with_clauses(risks, contract_info.get('contract_type', ''))
        
        # 按严重等级排序
        sorted_risks = sorted(risks, key=lambda r: SEVERITY_WEIGHTS.get(r.get('severity', '一般'), 99))
        
        # 计算评分
        score = self._calculate_score(risks)
        score_detail = self._get_score_detail(risks, score)
        
        # 统计
        stats = self._count_by_severity(risks)
        
        if output_format == 'json':
            return self._generate_json(sorted_risks, contract_info, score, score_detail, stats, risks)
        else:
            return self._generate_markdown(sorted_risks, contract_info, score, score_detail, stats, risks)
    
    def _calculate_score(self, risks: List[Dict]) -> int:
        """计算综合评分（0-100，分数越高风险越低）"""
        score = 100
        
        for risk in risks:
            severity = risk.get('severity', '一般')
            score += SCORE_IMPACT.get(severity, 0)
        
        return max(0, min(100, score))
    
    def _get_score_detail(self, risks: List[Dict], final_score: int) -> str:
        """获取评分说明"""
        # 查找匹配的评分区间
        for (low, high), desc in sorted(SCORE_DESCRIPTIONS.items(), reverse=True):
            if low <= final_score <= high:
                return desc
        return "无法评估"
    
    def _count_by_severity(self, risks: List[Dict]) -> Dict[str, int]:
        """按严重等级统计"""
        counts = {'严重': 0, '中等': 0, '一般': 0, '提示': 0}
        for risk in risks:
            severity = risk.get('severity', '一般')
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _generate_markdown(self, risks: List[Dict], contract_info: Dict,
                           score: int, score_detail: str, stats: Dict,
                           original_risks: List[Dict]) -> str:
        """生成 Markdown 格式报告"""
        lines = []
        
        # 标题
        lines.append("# 合同审查报告")
        lines.append("")
        
        # 基本信息
        lines.append("## 基本信息")
        lines.append("")
        lines.append(f"- **合同名称**：{contract_info.get('title', '未知')}")
        lines.append(f"- **合同类型**：{contract_info.get('contract_type', '未知')}")
        lines.append(f"- **审查视角**：{contract_info.get('party_role', '双方')}")
        lines.append(f"- **审查日期**：{datetime.now().strftime('%Y-%m-%d')}")
        
        parties = contract_info.get('parties', [])
        if parties:
            party_names = [f"{p.get('role', '')}: {p.get('name', '')}" for p in parties]
            party_str = "; ".join(party_names)
            # 保护隐私：主体名称脱敏显示
            if len(party_str) > 100:
                party_str = party_str[:100] + "..."
            lines.append(f"- **合同主体**：{party_str}")
        
        if contract_info.get('total_amount'):
            lines.append(f"- **合同金额**：{contract_info.get('total_amount', '')} {contract_info.get('currency', 'CNY')}")
        
        lines.append("")
        
        # 风险概况
        lines.append("## 📊 风险概况")
        lines.append("")
        lines.append("| 等级 | 数量 |")
        lines.append("|------|------|")
        lines.append(f"| 🔴 严重 | {stats.get('严重', 0)} 项 |")
        lines.append(f"| 🟡 中等 | {stats.get('中等', 0)} 项 |")
        lines.append(f"| 🟢 一般 | {stats.get('一般', 0)} 项 |")
        lines.append(f"| ℹ️ 提示 | {stats.get('提示', 0)} 项 |")
        lines.append("")
        
        # 评分
        lines.append(f"**⭐ 综合评分：{score}/100**（{score_detail}）")
        lines.append("")
        
        # 评分说明（v2.0 新增）
        lines.append("> **评分说明**：综合评分基于规则引擎检查（硬规则匹配）和 AI 语义审查结果计算。")
        lines.append("> - 满分 100 分，分数越高表示合同风险越低")
        lines.append("> - 严重风险每项扣 15 分，中等风险每项扣 8 分，一般风险每项扣 3 分")
        lines.append("> - 本评分仅供参考，不替代专业法律意见")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 风险详情
        if not risks:
            lines.append("## ✅ 审查结果")
            lines.append("")
            lines.append("恭喜！本次审查未发现明显风险点。但建议您仍仔细阅读合同全文，")
            lines.append("确保理解所有条款后再签署。")
            lines.append("")
        else:
            current_severity = None
            
            for risk in risks:
                severity = risk.get('severity', '一般')
                
                if severity != current_severity:
                    current_severity = severity
                    emoji = SEVERITY_EMOJI.get(severity, '⚪')
                    lines.append(f"## {emoji} {severity}风险")
                    lines.append("")
                
                # 风险标题
                title = risk.get('title', '未命名风险')
                lines.append(f"### {title}")
                lines.append("")
                
                # 位置处理（v2.0 修复 None 显示问题）
                clause_ref = risk.get('clause_ref')
                page = risk.get('page')
                
                if clause_ref or page:
                    location_parts = []
                    if clause_ref:
                        location_parts.append(f"条款: {clause_ref}")
                    if page:
                        location_parts.append(f"第 {page} 页")
                    lines.append(f"- **位置**：{', '.join(location_parts)}")
                
                # 原文引用
                if risk.get('text_snippet'):
                    # 确保不在中文字符中间截断（v2.0 新增安全截断）
                    snippet = risk['text_snippet']
                    if len(snippet) > 100:
                        snippet = snippet[:97] + "..."
                    # 过滤掉可能泄露个人信息的文本（简单脱敏）
                    import re
                    # 脱敏身份证号、手机号等
                    snippet = re.sub(r'\d{18}', '***', snippet)  # 身份证号
                    snippet = re.sub(r'\d{11}', '***', snippet)  # 手机号
                    lines.append(f"- **原文**：{snippet}")
                
                # 问题描述
                if risk.get('description'):
                    lines.append(f"- **问题**：{risk['description']}")
                
                # 法律依据
                if risk.get('legal_basis'):
                    lines.append(f"- **法律依据**：{risk['legal_basis']}")
                
                # 修改建议
                if risk.get('suggestion'):
                    lines.append(f"- **修改建议**：{risk['suggestion']}")
                
                # 推荐范本 / v4.0 条款库建议替换文本
                if risk.get('template'):
                    template = risk['template'].replace('\n', '\n  > ')
                    if risk.get('clause_id'):
                        label = f"建议替换为（条款库 {risk['clause_id']} {risk.get('clause_name', '')}）"
                    else:
                        label = "推荐范本"
                    lines.append(f"- **{label}**：\n\n  > {template}")
                
                lines.append("")
        
        # 缺失条款
        missing = contract_info.get('missing_clauses', [])
        if missing:
            lines.append("## 📋 缺失条款清单")
            lines.append("")
            for item in missing:
                lines.append(f"- [ ] {item}")
            lines.append("")
        
        # 特别提示
        special_notes = contract_info.get('special_notes', [])
        if special_notes:
            lines.append("## ℹ️ 特别提示")
            lines.append("")
            for note in special_notes:
                lines.append(f"- {note}")
            lines.append("")
        
        # 修改建议汇总
        if risks:
            lines.append("## 📝 修改建议汇总")
            lines.append("")
            for i, risk in enumerate(risks, 1):
                if risk.get('suggestion'):
                    lines.append(f"{i}. **{risk.get('title', '')}**")
                    lines.append(f"   → {risk['suggestion']}")
                    lines.append("")
        
        # 法规依据
        legal_bases = set()
        for risk in original_risks:
            if risk.get('legal_basis'):
                legal_bases.add(risk['legal_basis'])
        
        if legal_bases:
            lines.append("## ⚖️ 法规依据")
            lines.append("")
            lines.append("> 以下法规引用基于 2026 年现行有效的版本。如有更新，请以最新法规为准。")
            lines.append("")
            for basis in sorted(legal_bases):
                lines.append(f"- {basis}")
            lines.append("")
        
        # 免责声明（v2.0 更醒目）
        lines.append("---")
        lines.append("")
        lines.append("## ⚠️ 免责声明")
        lines.append("")
        lines.append("**重要提示**：")
        lines.append("")
        lines.append("- 本报告由 AI 智能审查工具生成，仅供参考，**不构成法律意见**。")
        lines.append("- 法律建议需由具备相应执业资格的律师提供。")
        lines.append("- 对于重大合同（标的额超过 100 万元或涉及核心商业利益），**强烈建议咨询专业执业律师**。")
        lines.append("- 本报告基于当前的法律法规进行审查，法律变更可能导致部分建议过时。")
        lines.append("- 因使用本报告而产生的任何损失，开发者不承担责任。")
        lines.append("")
        
        return '\n'.join(lines)
    
    def _generate_json(self, risks: List[Dict], contract_info: Dict,
                       score: int, score_detail: str, stats: Dict,
                       original_risks: List[Dict]) -> str:
        """生成 JSON 格式报告"""
        report = {
            'report_id': f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'generated_at': datetime.now().isoformat(),
            'skill_version': '2.0.0',
            'contract_info': contract_info,
            'score': score,
            'score_detail': score_detail,
            'statistics': stats,
            'scoring_method': {
                'description': '综合评分基于规则引擎和 AI 语义审查',
                'max_score': 100,
                'deductions': {
                    '严重': -15,
                    '中等': -8,
                    '一般': -3,
                    '提示': 0
                }
            },
            'risks': risks,
            'disclaimer': '本报告由 AI 生成，仅供使用者参考，不构成法律意见。对于重大合同，建议咨询专业执业律师。',
            'legal_basis_note': '引用法规基于 2026 年现行有效版本',
        }
        return json.dumps(report, ensure_ascii=False, indent=2)


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python generate_report.py <风险JSON文件> [合同信息JSON文件]")
        sys.exit(1)
    
    risks_path = sys.argv[1]
    contract_info_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 安全读取：限制文件大小
    try:
        file_size = os.path.getsize(risks_path)
        if file_size > 100 * 1024 * 1024:  # 最大 100MB
            print("错误：文件过大（最大 100MB）")
            sys.exit(1)
    except OSError:
        pass
    
    with open(risks_path, 'r', encoding='utf-8') as f:
        risks = json.load(f)
    
    contract_info = {}
    if contract_info_path:
        with open(contract_info_path, 'r', encoding='utf-8') as f:
            contract_info = json.load(f)
    
    generator = ReportGenerator()
    report = generator.generate(risks, contract_info)
    
    print(report)


if __name__ == '__main__':
    main()
