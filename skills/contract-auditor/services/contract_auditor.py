"""合同审计服务"""

import sys
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent))

from text_extractor import extract_text
from annotator_simple import create_annotated_markdown
try:
    from word_annotator import annotate_word_contract
except ImportError:
    from word_annotator_v2 import annotate_word_contract
from analyzers.payment_analyzer import PaymentAnalyzer
from analyzers.delivery_analyzer import DeliveryAnalyzer
from analyzers.compliance_checker import ComplianceChecker
from analyzers.risk_analyzer import RiskAnalyzer


@dataclass
class AuditFinding:
    """审计发现项"""
    category: str
    severity: str
    location: str
    description: str
    suggestion: str


@dataclass
class AuditReport:
    """审计报告"""
    contract_name: str
    findings: List[AuditFinding]
    summary: Dict[str, Any]
    risk_level: str


class ContractAuditor:
    """合同审计器"""
    
    def __init__(self):
        self.analyzers = {
            '金额条款': PaymentAnalyzer(),
            '交付条款': DeliveryAnalyzer(),
            '合规性': ComplianceChecker(),
            '风险提示': RiskAnalyzer(),
        }
    
    def audit(self, file_path: str) -> AuditReport:
        """审计合同文件"""
        # 提取文本
        text = extract_text(file_path)
        if not text:
            return AuditReport(
                contract_name=Path(file_path).name,
                findings=[],
                summary={'error': '无法提取合同文本'},
                risk_level='unknown'
            )
        
        # 分析各维度
        findings = []
        for category, analyzer in self.analyzers.items():
            results = analyzer.analyze(text)
            for r in results:
                findings.append(AuditFinding(
                    category=category,
                    severity=r.severity,
                    location=r.location,
                    description=r.description,
                    suggestion=r.suggestion
                ))
        
        # 生成摘要
        summary = self._generate_summary(findings)
        risk_level = self._calculate_risk_level(findings)
        
        return AuditReport(
            contract_name=Path(file_path).name,
            findings=findings,
            summary=summary,
            risk_level=risk_level
        )
    
    def audit_text(self, text: str, contract_name: str = "合同文本") -> AuditReport:
        """直接审计文本内容"""
        if not text:
            return AuditReport(
                contract_name=contract_name,
                findings=[],
                summary={'error': '合同文本为空'},
                risk_level='unknown'
            )
        
        findings = []
        for category, analyzer in self.analyzers.items():
            results = analyzer.analyze(text)
            for r in results:
                findings.append(AuditFinding(
                    category=category,
                    severity=r.severity,
                    location=r.location,
                    description=r.description,
                    suggestion=r.suggestion
                ))
        
        summary = self._generate_summary(findings)
        risk_level = self._calculate_risk_level(findings)
        
        return AuditReport(
            contract_name=contract_name,
            findings=findings,
            summary=summary,
            risk_level=risk_level
        )
    
    def _generate_summary(self, findings: List[AuditFinding]) -> Dict[str, Any]:
        """生成摘要"""
        if not findings:
            return {
                'total': 0,
                'by_severity': {},
                'by_category': {},
                'message': '未发现明显问题'
            }
        
        by_severity = {}
        by_category = {}
        
        for f in findings:
            by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
            by_category[f.category] = by_category.get(f.category, 0) + 1
        
        return {
            'total': len(findings),
            'by_severity': by_severity,
            'by_category': by_category
        }
    
    def _calculate_risk_level(self, findings: List[AuditFinding]) -> str:
        """计算风险等级"""
        if not findings:
            return 'low'
        
        critical = sum(1 for f in findings if f.severity == 'critical')
        high = sum(1 for f in findings if f.severity == 'high')
        
        if critical > 0 or high >= 3:
            return 'high'
        elif high > 0 or len(findings) >= 5:
            return 'medium'
        return 'low'


def format_report(report: AuditReport) -> str:
    """格式化报告为 Markdown"""
    lines = [
        f"# 合同审计报告：{report.contract_name}",
        "",
        f"**风险等级**: {'🔴 高' if report.risk_level == 'high' else '🟡 中' if report.risk_level == 'medium' else '🟢 低' if report.risk_level == 'low' else '⚪ 未知'}",
        f"**发现问题**: {report.summary.get('total', 0)} 项",
        "",
        "## 摘要",
        ""
    ]
    
    # 按严重程度统计
    by_severity = report.summary.get('by_severity', {})
    if by_severity:
        lines.append("### 按严重程度")
        severity_order = ['critical', 'high', 'medium', 'low']
        severity_names = {'critical': '严重', 'high': '高', 'medium': '中', 'low': '低'}
        for sev in severity_order:
            count = by_severity.get(sev, 0)
            if count > 0:
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(sev, '⚪')
                lines.append(f"- {emoji} {severity_names.get(sev, sev.upper())}: {count} 项")
        lines.append("")
    
    # 按类别统计
    by_category = report.summary.get('by_category', {})
    if by_category:
        lines.append("### 按类别")
        for cat, count in by_category.items():
            lines.append(f"- {cat}: {count} 项")
        lines.append("")
    
    # 详细发现
    if report.findings:
        lines.append("## 详细发现")
        lines.append("")
        
        # 按严重程度排序
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        sorted_findings = sorted(report.findings, key=lambda f: severity_order.get(f.severity, 4))
        
        severity_names = {'critical': '严重', 'high': '高', 'medium': '中', 'low': '低'}
        
        for i, f in enumerate(sorted_findings, 1):
            emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(f.severity, '⚪')
            sev_name = severity_names.get(f.severity, f.severity.upper())
            lines.append(f"### {i}. {emoji} [{sev_name}] {f.location}")
            lines.append(f"**类别**: {f.category}")
            lines.append(f"**问题**: {f.description}")
            lines.append(f"**建议**: {f.suggestion}")
            lines.append("")
    
    return '\n'.join(lines)


def audit_contract(file_path: str) -> str:
    """审计合同文件并返回格式化报告"""
    auditor = ContractAuditor()
    report = auditor.audit(file_path)
    return format_report(report)


def audit_contract_text(text: str, contract_name: str = "合同文本") -> str:
    """审计合同文本并返回格式化报告"""
    auditor = ContractAuditor()
    report = auditor.audit_text(text, contract_name)
    return format_report(report)


def audit_with_annotation(text: str, contract_name: str = "合同文本") -> tuple:
    """
    审计合同并生成批注文档
    
    Returns:
        (审计报告, 批注文档)
    """
    auditor = ContractAuditor()
    report = auditor.audit_text(text, contract_name)
    
    # 生成审计报告
    audit_report = format_report(report)
    
    # 生成批注文档
    findings = [
        {
            'category': f.category,
            'severity': f.severity,
            'location': f.location,
            'description': f.description,
            'suggestion': f.suggestion
        }
        for f in report.findings
    ]
    annotated_doc = create_annotated_markdown(text, findings, contract_name)
    
    return audit_report, annotated_doc


def audit_with_word_annotation(input_path: str, output_path: str = None) -> tuple:
    """
    审计 Word 合同并在原文件上添加批注
    
    Args:
        input_path: 原始合同文件路径
        output_path: 输出文件路径（默认在原文件名后加 _annotated）
    
    Returns:
        (审计报告, 输出文件路径)
    """
    auditor = ContractAuditor()
    report = auditor.audit(input_path)
    
    # 生成审计报告
    audit_report = format_report(report)
    
    # 准备 findings 数据
    findings = [
        {
            'category': f.category,
            'severity': f.severity,
            'location': f.location,
            'description': f.description,
            'suggestion': f.suggestion
        }
        for f in report.findings
    ]
    
    # 设置输出路径
    if output_path is None:
        input_file = Path(input_path)
        output_path = str(input_file.parent / f"{input_file.stem}_annotated{input_file.suffix}")
    
    # 在 Word 文件中添加批注
    success = annotate_word_contract(input_path, output_path, findings)
    
    if success:
        return audit_report, output_path
    else:
        return audit_report, None


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        print(audit_contract(file_path))
    else:
        # 测试文本
        test_text = """
技术服务合同

甲方：某某科技有限公司
乙方：某某软件公司

第一条 合同金额
本合同总金额为人民币壹拾万元整。
付款方式：合同签订后支付预付款，验收合格后支付尾款。

第二条 交付时间
乙方应在合理时间内完成系统开发并交付甲方。

第三条 验收标准
甲方验收合格后视为交付完成。

第四条 违约责任
任何一方违约，应承担相应的违约责任。
甲方有权单方解除合同。

第五条 知识产权
本合同涉及的知识产权归甲方所有。

如发生争议，提交甲方所在地人民法院诉讼。
"""
        print(audit_contract_text(test_text, "测试合同"))
