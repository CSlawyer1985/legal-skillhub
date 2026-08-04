#!/usr/bin/env python3
"""
合规文案Pro版 - Level 2
Compliance Copy Pro

基于免费版合规扫描，增加：
- batch-scan: 批量ASIN扫描
- matrix: 合规修复优先级矩阵
- multi-market: 多市场合规对比

Author: Miaoji Studio Pro
Version: 1.0.0
"""

import sys
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ComplianceIssue:
    """合规问题"""
    issue_type: str
    severity: str  # critical, high, medium, low
    description: str
    affected_content: str
    suggested_fix: str
    regulation: str


@dataclass
class ComplianceResult:
    """合规结果"""
    asin: str
    overall_score: float
    issues: List[ComplianceIssue]
    scan_time: str
    market: str


class CompliancePro:
    """合规文案Pro版"""
    
    # 常见违规词库
    BANNED_WORDS = {
        "FDA相关": ["FDA批准", "治愈", "治疗", "医疗", "药用"],
        "绝对化用语": ["最好", "第一", "顶级", "完美", "极致"],
        "虚假宣传": ["100%", "保证", "承诺", "无效退款"],
        "儿童相关": ["适合儿童", "儿童安全", "无毒无害"]
    }
    
    # 市场法规要求
    MARKET_REGULATIONS = {
        "美国": ["FDA", "FTC", "CPSC"],
        "欧盟": ["GDPR", "EU-AI-Act", "GPSR"],
        "日本": ["景表法", "薬機法"],
        "英国": ["UK GDPR", "CMA"]
    }
    
    def __init__(self):
        self.scan_history: List[ComplianceResult] = []
    
    def scan_single(self, asin: str, content: str, market: str = "美国") -> ComplianceResult:
        """
        扫描单个ASIN
        
        Args:
            asin: ASIN
            content: 待检测内容
            market: 市场
        
        Returns:
            合规结果
        """
        issues = []
        content_lower = content.lower()
        
        # 检测违规词
        for category, words in self.BANNED_WORDS.items():
            for word in words:
                if word.lower() in content_lower:
                    issues.append(ComplianceIssue(
                        issue_type="违规词",
                        severity=self._get_severity(category, word),
                        description=f"包含{category}相关词汇: {word}",
                        affected_content=word,
                        suggested_fix=self._get_fix_suggestion(word),
                        regulation=", ".join(self.MARKET_REGULATIONS.get(market, []))
                    ))
        
        # 检测其他问题
        if "！" in content or "?" in content:
            issues.append(ComplianceIssue(
                issue_type="标点符号",
                severity="low",
                description="包含可能引起投诉的标点",
                affected_content="感叹号/问号",
                suggested_fix="使用句号或逗号替代",
                regulation="FTC"
            ))
        
        # 计算合规分
        base_score = 100
        penalty = sum({
            "critical": 20,
            "high": 10,
            "medium": 5,
            "low": 2
        }.get(i.severity, 5) for i in issues)
        
        overall_score = max(0, base_score - penalty)
        
        return ComplianceResult(
            asin=asin,
            overall_score=round(overall_score, 1),
            issues=issues,
            scan_time="2024-01-15",
            market=market
        )
    
    def _get_severity(self, category: str, word: str) -> str:
        """获取严重程度"""
        if category == "FDA相关":
            return "critical"
        elif category == "绝对化用语":
            return "high"
        elif category == "虚假宣传":
            return "high"
        else:
            return "medium"
    
    def _get_fix_suggestion(self, word: str) -> str:
        """获取修复建议"""
        replacements = {
            "FDA批准": "经认证",
            "治愈": "改善",
            "治疗": "支持",
            "医疗": "健康",
            "最好": "优质",
            "第一": "领先",
            "完美": "出众",
            "100%": "高浓度/高品质"
        }
        return f"建议替换为: {replacements.get(word, '合规表述')}"
    
    def batch_scan(self, asins: List[Dict]) -> List[ComplianceResult]:
        """
        批量扫描
        
        Args:
            asins: ASIN列表 [{"asin": "xxx", "content": "xxx", "market": "美国"}]
        
        Returns:
            扫描结果列表
        """
        results = []
        
        for item in asins:
            result = self.scan_single(
                item["asin"],
                item["content"],
                item.get("market", "美国")
            )
            results.append(result)
            self.scan_history.append(result)
        
        return results
    
    def generate_matrix(self, results: List[ComplianceResult] = None) -> Dict:
        """
        生成优先级矩阵
        
        Args:
            results: 合规结果列表
        
        Returns:
            优先级矩阵
        """
        if results is None:
            results = self.scan_history[-10:] if self.scan_history else []
        
        # 按ASIN和问题数分组
        matrix = {
            "critical": [],    # 高风险-高价值
            "high": [],        # 中高风险
            "medium": [],      # 中风险
            "low": []          # 低风险-可延后
        }
        
        for result in results:
            # 评估价值（假设销量越高价值越高）
            value_factor = "high" if result.overall_score < 70 else "medium" if result.overall_score < 85 else "low"
            
            risk_level = "critical" if any(i.severity == "critical" for i in result.issues) else \
                        "high" if len(result.issues) >= 3 else \
                        "medium" if len(result.issues) >= 1 else "low"
            
            item = {
                "asin": result.asin,
                "score": result.overall_score,
                "issue_count": len(result.issues),
                "risk_level": risk_level,
                "value_factor": value_factor,
                "action": self._get_matrix_action(risk_level, value_factor)
            }
            
            if risk_level == "critical":
                matrix["critical"].append(item)
            elif risk_level == "high":
                matrix["high"].append(item)
            elif risk_level == "medium":
                matrix["medium"].append(item)
            else:
                matrix["low"].append(item)
        
        return matrix
    
    def _get_matrix_action(self, risk: str, value: str) -> str:
        """获取矩阵建议"""
        if risk == "critical":
            return "立即修复"
        elif risk == "high" and value == "high":
            return "优先修复"
        elif risk == "high":
            return "近期修复"
        elif risk == "medium":
            return "计划修复"
        else:
            return "延后处理"
    
    def multi_market_compare(self, asin: str, contents: Dict[str, str]) -> Dict:
        """
        多市场合规对比
        
        Args:
            asin: ASIN
            contents: 各市场内容 {"美国": "xxx", "欧盟": "xxx", ...}
        
        Returns:
            对比结果
        """
        comparison = {
            "asin": asin,
            "markets": {},
            "summary": {}
        }
        
        market_results = {}
        for market, content in contents.items():
            result = self.scan_single(asin, content, market)
            market_results[market] = result
        
        # 汇总
        all_issues = defaultdict(list)
        for market, result in market_results.items():
            comparison["markets"][market] = {
                "score": result.overall_score,
                "issue_count": len(result.issues),
                "critical_issues": len([i for i in result.issues if i.severity == "critical"]),
                "compliant": result.overall_score >= 90
            }
            
            for issue in result.issues:
                all_issues[issue.affected_content].append({
                    "market": market,
                    "issue": issue.description
                })
        
        # 共同问题
        common_issues = [k for k, v in all_issues.items() if len(v) > 1]
        
        comparison["summary"] = {
            "best_market": min(comparison["markets"].items(), key=lambda x: x[1]["score"])[0] if comparison["markets"] else None,
            "worst_market": max(comparison["markets"].items(), key=lambda x: x[1]["score"])[0] if comparison["markets"] else None,
            "common_issues": common_issues,
            "global_compliant": all(r["compliant"] for r in comparison["markets"].values())
        }
        
        return comparison
    
    def generate_compliance_report(self, result: ComplianceResult) -> str:
        """生成合规报告"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"合规扫描报告 - {result.asin}")
        lines.append("=" * 60)
        
        lines.append(f"\n市场: {result.market}")
        lines.append(f"扫描时间: {result.scan_time}")
        lines.append(f"合规评分: {result.overall_score}分")
        
        if result.issues:
            lines.append(f"\n发现问题: {len(result.issues)}项")
            
            for issue in result.issues:
                severity_icon = "🔴" if issue.severity == "critical" else "🟠" if issue.severity == "high" else "🟡"
                lines.append(f"\n{severity_icon} [{issue.severity.upper()}] {issue.issue_type}")
                lines.append(f"   问题: {issue.description}")
                lines.append(f"   修复: {issue.suggested_fix}")
                lines.append(f"   法规: {issue.regulation}")
        else:
            lines.append("\n✅ 未发现合规问题")
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python compliance-pro.py <command> [args]")
        print("命令:")
        print("  batch-scan     - 批量ASIN扫描")
        print("  matrix         - 优先级矩阵")
        print("  multi-market   - 多市场对比")
        return
    
    command = sys.argv[1]
    checker = CompliancePro()
    
    if command == "batch-scan":
        asins = [
            {"asin": "B08N5WRWNW", "content": "这款是最好的无线耳机，100%防水，适合儿童使用！"},
            {"asin": "B07XGYJ8RZ", "content": "经过FDA批准的高端音响设备，保证给您完美的音乐体验！"},
            {"asin": "B09XYZ1234", "content": "优质蓝牙音箱，防水防尘，适合户外使用。"}
        ]
        
        results = checker.batch_scan(asins)
        
        print("=" * 60)
        print("批量合规扫描结果")
        print("=" * 60)
        
        for result in results:
            status = "✅" if result.overall_score >= 90 else "⚠️" if result.overall_score >= 70 else "❌"
            print(f"\n{status} {result.asin}: {result.overall_score}分 ({len(result.issues)}个问题)")
    
    elif command == "matrix":
        # 先生成一些测试结果
        asins = [
            {"asin": "B001", "content": "测试内容1", "market": "美国"},
            {"asin": "B002", "content": "测试内容2", "market": "美国"},
            {"asin": "B003", "content": "测试内容3", "market": "美国"}
        ]
        checker.batch_scan(asins)
        
        matrix = checker.generate_matrix()
        
        print("=" * 60)
        print("合规修复优先级矩阵")
        print("=" * 60)
        
        for priority, items in matrix.items():
            if items:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                print(f"\n{icon} {priority.upper()} ({len(items)}个)")
                for item in items:
                    print(f"   {item['asin']}: {item['score']}分 | {item['action']}")
    
    elif command == "multi-market":
        asin = "B08N5WRWNW"
        contents = {
            "美国": "Premium wireless earbuds with crystal clear sound quality",
            "欧盟": "Premium wireless earbuds mit kristallklarer Klangqualität",
            "日本": "プレミアムワイヤレスイヤフォン、高音质设计"
        }
        
        result = checker.multi_market_compare(asin, contents)
        
        print("=" * 60)
        print(f"多市场合规对比 - {asin}")
        print("=" * 60)
        
        print("\n【各市场评分】")
        for market, data in result["markets"].items():
            status = "✅" if data["compliant"] else "❌"
            print(f"  {status} {market}: {data['score']}分 ({data['issue_count']}个问题)")
        
        print("\n【汇总】")
        summary = result["summary"]
        if summary["best_market"]:
            print(f"  最佳市场: {summary['best_market']}")
        if summary["worst_market"]:
            print(f"  最差市场: {summary['worst_market']}")
        print(f"  全局合规: {'是' if summary['global_compliant'] else '否'}")
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
