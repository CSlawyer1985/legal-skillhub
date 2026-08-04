#!/usr/bin/env python3
"""
PIPL合规报告生成工具
使用pandas生成数据分析报告
"""

import argparse
import json
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

class ReportGenerator:
    """报告生成器（使用pandas）"""
    
    def __init__(self):
        self.report_types = {
            "compliance-summary": "合规检查汇总报告",
            "risk-analysis": "风险评估分析报告", 
            "audit-trend": "审计趋势分析报告",
            "data-mapping": "数据映射报告"
        }
    
    def generate_compliance_summary(self, check_results: List[Dict]) -> Dict:
        """生成合规检查汇总报告"""
        if not check_results:
            return {"error": "没有检查结果数据"}
        
        # 使用pandas进行数据分析
        df = pd.DataFrame(check_results)
        
        # 基本统计
        total_checks = len(df)
        high_risk_count = df[df['risk_level'] == 'high'].shape[0]
        medium_risk_count = df[df['risk_level'] == 'medium'].shape[0]
        low_risk_count = df[df['risk_level'] == 'low'].shape[0]
        
        # 按场景统计
        scenario_stats = df.groupby('scenario').agg({
            'overall_score': 'mean',
            'risk_level': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        # 按检查类别统计
        category_issues = {}
        for result in check_results:
            if 'categories' in result:
                for cat_key, cat_data in result['categories'].items():
                    if cat_key not in category_issues:
                        category_issues[cat_key] = 0
                    category_issues[cat_key] += cat_data.get('issue_count', 0)
        
        report = {
            "report_type": "compliance-summary",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_checks": total_checks,
                "overall_score": df['overall_score'].mean() if 'overall_score' in df.columns else 0,
                "risk_distribution": {
                    "high": high_risk_count,
                    "medium": medium_risk_count,
                    "low": low_risk_count
                }
            },
            "by_scenario": scenario_stats.to_dict('records') if not scenario_stats.empty else [],
            "by_category": category_issues,
            "pandas_info": {
                "rows": total_checks,
                "columns": list(df.columns) if not df.empty else [],
                "memory_usage": df.memory_usage(deep=True).sum() if not df.empty else 0
            }
        }
        
        return report
    
    def generate_risk_analysis(self, risk_assessments: List[Dict]) -> Dict:
        """生成风险评估分析报告"""
        if not risk_assessments:
            return {"error": "没有风险评估数据"}
        
        df = pd.DataFrame(risk_assessments)
        
        # 风险等级分析
        risk_level_dist = df['risk_level'].value_counts().to_dict()
        
        # 维度分数分析
        dimension_scores = {}
        if 'dimension_scores' in df.columns:
            # 提取维度分数
            all_dimensions = []
            for assessment in risk_assessments:
                if 'dimension_scores' in assessment:
                    for dim_key, dim_data in assessment['dimension_scores'].items():
                        all_dimensions.append({
                            'dimension': dim_key,
                            'name': dim_data.get('name', dim_key),
                            'score': dim_data.get('score', 0),
                            'weighted_score': dim_data.get('weighted_score', 0)
                        })
            
            if all_dimensions:
                dim_df = pd.DataFrame(all_dimensions)
                dimension_stats = dim_df.groupby(['dimension', 'name']).agg({
                    'score': ['mean', 'min', 'max', 'std'],
                    'weighted_score': 'mean'
                }).round(2).to_dict()
                
                dimension_scores = dimension_stats
        
        # 活动类型分析
        activity_stats = {}
        if 'activity' in df.columns:
            activity_stats = df.groupby('activity').agg({
                'overall_score': ['mean', 'count'],
                'risk_level': lambda x: x.mode().iloc[0] if not x.mode().empty else 'unknown'
            }).round(2).to_dict()
        
        report = {
            "report_type": "risk-analysis",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_assessments": len(df),
                "average_score": df['overall_score'].mean() if 'overall_score' in df.columns else 0,
                "risk_distribution": risk_level_dist
            },
            "dimension_analysis": dimension_scores,
            "activity_analysis": activity_stats,
            "statistics": {
                "dataframe_shape": df.shape,
                "columns": list(df.columns),
                "missing_values": df.isnull().sum().to_dict()
            }
        }
        
        return report
    
    def generate_audit_trend(self, audit_data: List[Dict], period: str = 'month') -> Dict:
        """生成审计趋势分析报告"""
        if not audit_data:
            return {"error": "没有审计数据"}
        
        df = pd.DataFrame(audit_data)
        
        # 确保有日期字段
        if 'check_time' not in df.columns and 'assessment_time' not in df.columns:
            return {"error": "缺少时间字段"}
        
        # 使用合适的日期字段
        time_column = 'check_time' if 'check_time' in df.columns else 'assessment_time'
        
        # 转换日期
        df['date'] = pd.to_datetime(df[time_column])
        
        # 按时间周期分组
        if period == 'day':
            df['period'] = df['date'].dt.date
        elif period == 'week':
            df['period'] = df['date'].dt.to_period('W').apply(lambda r: r.start_time)
        elif period == 'month':
            df['period'] = df['date'].dt.to_period('M').apply(lambda r: r.start_time)
        else:  # year
            df['period'] = df['date'].dt.to_period('Y').apply(lambda r: r.start_time)
        
        # 趋势分析
        trend_stats = df.groupby('period').agg({
            'overall_score': 'mean',
            'risk_level': lambda x: (x == 'high').sum() / len(x) if len(x) > 0 else 0
        }).round(2).reset_index()
        
        # 计算趋势
        trend_stats['score_trend'] = trend_stats['overall_score'].pct_change().fillna(0)
        trend_stats['risk_trend'] = trend_stats['risk_level'].pct_change().fillna(0)
        
        report = {
            "report_type": "audit-trend",
            "generated_at": datetime.now().isoformat(),
            "period": period,
            "trend_data": trend_stats.to_dict('records'),
            "summary": {
                "total_periods": len(trend_stats),
                "average_score": trend_stats['overall_score'].mean(),
                "average_risk_rate": trend_stats['risk_level'].mean(),
                "latest_score": trend_stats['overall_score'].iloc[-1] if len(trend_stats) > 0 else 0,
                "score_change": trend_stats['score_trend'].iloc[-1] if len(trend_stats) > 0 else 0
            },
            "statistics": {
                "data_points": len(df),
                "time_range": {
                    "start": df['date'].min().isoformat() if not df.empty else None,
                    "end": df['date'].max().isoformat() if not df.empty else None
                }
            }
        }
        
        return report
    
    def generate_data_mapping(self, mapping_data: Dict) -> Dict:
        """生成数据映射报告"""
        if not mapping_data or 'activities' not in mapping_data:
            return {"error": "没有数据映射信息"}
        
        activities = mapping_data['activities']
        df = pd.DataFrame(activities)
        
        # 数据流分析
        data_flow_analysis = {}
        if 'data_flows' in df.columns:
            # 分析数据流向
            all_flows = []
            for activity in activities:
                if 'data_flows' in activity:
                    for flow in activity['data_flows']:
                        all_flows.append(flow)
            
            if all_flows:
                flows_df = pd.DataFrame(all_flows)
                flow_stats = flows_df.groupby(['source', 'destination']).agg({
                    'data_type': 'unique',
                    'volume': ['sum', 'mean', 'count']
                }).round(2).to_dict()
                
                data_flow_analysis = flow_stats
        
        # 数据处理目的分析
        purpose_analysis = {}
        if 'purposes' in df.columns:
            purpose_counts = {}
            for activity in activities:
                if 'purposes' in activity:
                    for purpose in activity['purposes']:
                        if purpose not in purpose_counts:
                            purpose_counts[purpose] = 0
                        purpose_counts[purpose] += 1
            
            purpose_analysis = purpose_counts
        
        # 第三方分析
        third_party_analysis = {}
        if 'third_parties' in df.columns:
            third_party_counts = {}
            for activity in activities:
                if 'third_parties' in activity:
                    for third_party in activity['third_parties']:
                        name = third_party.get('name', 'unknown')
                        if name not in third_party_counts:
                            third_party_counts[name] = 0
                        third_party_counts[name] += 1
            
            third_party_analysis = third_party_counts
        
        report = {
            "report_type": "data-mapping",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_activities": len(activities),
                "data_categories": len(set().union(*[a.get('data_categories', []) for a in activities])),
                "third_party_count": len(third_party_analysis)
            },
            "data_flow_analysis": data_flow_analysis,
            "purpose_analysis": purpose_analysis,
            "third_party_analysis": third_party_analysis,
            "statistics": {
                "activities_by_risk": df['risk_level'].value_counts().to_dict() if 'risk_level' in df.columns else {},
                "data_volume": df['data_volume'].sum() if 'data_volume' in df.columns else 0
            }
        }
        
        return report
    
    def list_report_types(self) -> List[Dict]:
        """列出可用的报告类型"""
        reports = []
        for key, name in self.report_types.items():
            reports.append({
                "id": key,
                "name": name,
                "description": f"生成{name}"
            })
        return reports

def main():
    parser = argparse.ArgumentParser(description="PIPL合规报告生成工具（使用pandas）")
    parser.add_argument("--type", required=True, 
                       choices=["compliance-summary", "risk-analysis", "audit-trend", "data-mapping"],
                       help="报告类型")
    parser.add_argument("--input", help="输入JSON文件路径")
    parser.add_argument("--output", help="输出报告文件路径")
    parser.add_argument("--period", choices=["day", "week", "month", "year"], default="month",
                       help="趋势分析的时间周期")
    parser.add_argument("--list-types", action="store_true", help="列出可用的报告类型")
    parser.add_argument("--format", choices=["json", "csv", "excel"], default="json", help="输出格式")
    
    args = parser.parse_args()
    
    # 创建生成器
    generator = ReportGenerator()
    
    # 列出报告类型
    if args.list_types:
        report_types = generator.list_report_types()
        if args.format == "json":
            print(json.dumps(report_types, ensure_ascii=False, indent=2))
        else:
            print("可用的报告类型：")
            for report in report_types:
                print(f"📊 {report['name']} ({report['id']})")
                print(f"   描述：{report['description']}")
                print()
        return
    
    # 读取输入数据
    data = []
    if args.input:
        try:
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data = [data]  # 如果是单个对象，转换为列表
        except Exception as e:
            print(f"❌ 读取输入文件失败：{str(e)}")
            return
    else:
        # 如果没有输入文件，使用示例数据
        print("⚠️  没有提供输入文件，使用示例数据")
        data = get_sample_data(args.type)
    
    # 生成报告
    if args.type == "compliance-summary":
        report = generator.generate_compliance_summary(data)
    elif args.type == "risk-analysis":
        report = generator.generate_risk_analysis(data)
    elif args.type == "audit-trend":
        report = generator.generate_audit_trend(data, args.period)
    elif args.type == "data-mapping":
        report = generator.generate_data_mapping(data)
    else:
        print(f"❌ 未知的报告类型：{args.type}")
        return
    
    # 输出报告
    if args.format == "json":
        output_content = json.dumps(report, ensure_ascii=False, indent=2)
    elif args.format == "csv":
        # 将关键数据转换为CSV
        import io
        output = io.StringIO()
        if 'summary' in report:
            summary_df = pd.DataFrame([report['summary']])
            summary_df.to_csv(output, index=False)
            output_content = output.getvalue()
        else:
            output_content = "无法生成CSV格式"
    else:  # excel
        output_content = "Excel格式暂未实现"
    
    # 保存或打印报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_content)
        print(f"✅ 报告已保存至：{args.output}")
    else:
        print(output_content)

def get_sample_data(report_type: str) -> List[Dict]:
    """获取示例数据"""
    if report_type == "compliance-summary":
        return [
            {
                "scenario": "user_registration",
                "overall_score": 85,
                "risk_level": "medium",
                "categories": {
                    "consent": {"issue_count": 0},
                    "notification": {"issue_count": 2},
                    "security": {"issue_count": 1}
                }
            },
            {
                "scenario": "location_collection", 
                "overall_score": 60,
                "risk_level": "high",
                "categories": {
                    "consent": {"issue_count": 1},
                    "notification": {"issue_count": 1},
                    "security": {"issue_count": 2}
                }
            }
        ]
    elif report_type == "risk-analysis":
        return [
            {
                "activity": "用户画像分析",
                "overall_score": 75,
                "risk_level": "high",
                "dimension_scores": {
                    "data_sensitivity": {"score": 5, "weighted_score": 1.5},
                    "processing_scale": {"score": 5, "weighted_score": 1.0}
                }
            }
        ]
    else:
        return []

if __name__ == "__main__":
    main()