#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v3.0 综合测试脚本
使用 1000+ 案例进行多角度多模式解析测试

测试维度：
1. 输入模式对比（结构化 vs 混合式）
2. 纠纷类型覆盖（5 大类）
3. 信息完整度分级（完整/基本完整/不完整）
4. 智能追问效果测试
5. 准确率验证
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path
from lawyer_assistant import LawyerAssistant


class ComprehensiveTester:
    """综合测试器"""
    
    def __init__(self):
        self.assistant = LawyerAssistant()
        self.output_dir = Path(__file__).parent / "test_results"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试用例模板
        self.test_templates = self._load_test_templates()
        
        # 测试结果
        self.results = {
            'metadata': {
                'test_time': datetime.now().isoformat(),
                'version': 'v3.0',
                'total_cases': 0,
                'test_modes': ['structured', 'mixed']
            },
            'by_mode': {
                'structured': {'cases': 0, 'accurate': 0, 'avg_completeness': 0},
                'mixed': {'cases': 0, 'accurate': 0, 'avg_completeness': 0}
            },
            'by_dispute_type': {},
            'by_completeness': {
                'high': {'cases': 0, 'accurate': 0},  # >=90%
                'medium': {'cases': 0, 'accurate': 0},  # 60-90%
                'low': {'cases': 0, 'accurate': 0}  # <60%
            },
            'follow_up_stats': {
                'total_questions': 0,
                'avg_questions_per_case': 0
            },
            'detailed_results': []
        }
    
    def _load_test_templates(self) -> dict:
        """加载测试用例模板"""
        return {
            '劳动合同': [
                {
                    'structured': '当事人：张某，对手：XX 科技公司，纠纷：劳动合同，起因：公司违法解除，工作 5 年，诉求：赔偿金，证据：劳动合同',
                    'mixed': '公司违法辞退我（工作 5 年，月工资 2 万），有劳动合同和解除通知，能赔多少钱？',
                    'expected': {'纠纷类型': '劳动纠纷', '工作年限': '5', '月工资': '2 万'}
                },
                {
                    'structured': '当事人：李某，对手：XX 商贸公司，纠纷：劳动合同，起因：拖欠工资 3 个月，诉求：补发工资，证据：工资条',
                    'mixed': '公司拖欠工资 3 个月（每月 8000 元），有工资条和考勤记录，怎么办？',
                    'expected': {'纠纷类型': '劳动纠纷', '拖欠月数': '3'}
                }
            ],
            '消费纠纷': [
                {
                    'structured': '当事人：王某，对手：XX 电商平台，纠纷：消费纠纷，起因：网购买到假货，诉求：退一赔三，证据：订单截图',
                    'mixed': '网购买到假货（花 3000 元），有订单和支付记录，能退一赔三吗？',
                    'expected': {'纠纷类型': '消费纠纷', '金额': '3000'}
                }
            ],
            '离婚纠纷': [
                {
                    'structured': '当事人：赵某，对手：钱某，纠纷：离婚纠纷，起因：对方出轨，诉求：离婚和抚养权，证据：聊天记录',
                    'mixed': '老公出轨要离婚（有 5 岁孩子），想要抚养权，有聊天记录证据，能成功吗？',
                    'expected': {'纠纷类型': '离婚纠纷', '子女': '5 岁'}
                }
            ],
            '借款纠纷': [
                {
                    'structured': '当事人：孙某，对手：周某，纠纷：借款纠纷，起因：借款 10 万未还，诉求：归还借款，证据：借条',
                    'mixed': '朋友借了 10 万元（有借条），到期不还，能要回来吗？',
                    'expected': {'纠纷类型': '借款纠纷', '金额': '10 万'}
                }
            ],
            '交通事故': [
                {
                    'structured': '当事人：吴某，对手：郑某，纠纷：交通事故，起因：车祸受伤，诉求：赔偿医疗费，证据：事故认定书',
                    'mixed': '被车撞了（住院 15 天，医疗费 5 万），有事故认定书，能赔多少？',
                    'expected': {'纠纷类型': '交通事故', '医疗费': '5 万'}
                }
            ]
        }
    
    def generate_test_cases(self, count: int = 1000) -> list:
        """生成测试案例"""
        test_cases = []
        
        # 基于模板生成变体
        for dispute_type, templates in self.test_templates.items():
            cases_per_type = count // len(self.test_templates)
            
            for i in range(cases_per_type):
                template = templates[i % len(templates)]
                
                # 生成结构化测试用例
                test_cases.append({
                    'case_id': f'TEST_{len(test_cases)+1:05d}',
                    'dispute_type': dispute_type,
                    'mode': 'structured',
                    'input': self._generate_variant(template['structured'], i),
                    'expected': template['expected']
                })
                
                # 生成混合式测试用例
                test_cases.append({
                    'case_id': f'TEST_{len(test_cases)+1:05d}',
                    'dispute_type': dispute_type,
                    'mode': 'mixed',
                    'input': self._generate_variant(template['mixed'], i),
                    'expected': template['expected']
                })
        
        return test_cases[:count]
    
    def _generate_variant(self, template: str, variant_id: int) -> str:
        """生成变体（添加随机变化）"""
        # 简单实现，可以添加更多变化
        variations = [
            template,
            template + ' 急！',
            '请问，' + template,
            template + ' 在线等',
        ]
        return variations[variant_id % len(variations)]
    
    def run_test(self, test_cases: list) -> dict:
        """运行测试"""
        print("=" * 80)
        print(f"开始 v3.0 综合测试 - {len(test_cases)} 个案例")
        print("=" * 80)
        
        start_time = time.time()
        
        for i, case in enumerate(test_cases):
            # 解析案例
            parse_result = self.assistant.parse_case_info(case['input'])
            
            # 评估准确率
            accuracy = self._evaluate_accuracy(parse_result, case['expected'])
            completeness = parse_result.get('completeness', 0)
            
            # 更新统计
            self._update_stats(case, parse_result, accuracy, completeness)
            
            # 记录详细结果
            self.results['detailed_results'].append({
                'case_id': case['case_id'],
                'dispute_type': case['dispute_type'],
                'mode': case['mode'],
                'accuracy': accuracy,
                'completeness': completeness,
                'input_type': parse_result.get('input_type', 'unknown'),
                'follow_up_count': len(parse_result.get('missing_fields', []))
            })
            
            # 进度报告
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                print(f"进度：{i+1}/{len(test_cases)} ({(i+1)/len(test_cases)*100:.1f}%) - "
                      f"耗时：{elapsed:.1f}秒")
        
        # 计算最终统计
        self._calculate_final_stats()
        
        elapsed = time.time() - start_time
        print(f"\n测试完成 - 总耗时：{elapsed:.1f}秒")
        
        return self.results
    
    def _evaluate_accuracy(self, parse_result: dict, expected: dict) -> float:
        """评估准确率"""
        if not expected:
            return 0
        
        correct = 0
        total = len(expected)
        
        for key, value in expected.items():
            if key == '纠纷类型':
                if value in parse_result.get('纠纷类型', ''):
                    correct += 1
            else:
                # 检查其他字段
                if str(value) in str(parse_result):
                    correct += 1
        
        return correct / total if total > 0 else 0
    
    def _update_stats(self, case: dict, parse_result: dict, accuracy: float, completeness: float):
        """更新统计"""
        mode = case['mode']
        dispute_type = case['dispute_type']
        
        # 按模式统计
        self.results['by_mode'][mode]['cases'] += 1
        self.results['by_mode'][mode]['accurate'] += accuracy
        self.results['by_mode'][mode]['avg_completeness'] += completeness
        
        # 按纠纷类型统计
        if dispute_type not in self.results['by_dispute_type']:
            self.results['by_dispute_type'][dispute_type] = {
                'cases': 0, 'accurate': 0, 'structured': 0, 'mixed': 0
            }
        self.results['by_dispute_type'][dispute_type]['cases'] += 1
        self.results['by_dispute_type'][dispute_type]['accurate'] += accuracy
        if mode == 'structured':
            self.results['by_dispute_type'][dispute_type]['structured'] += 1
        else:
            self.results['by_dispute_type'][dispute_type]['mixed'] += 1
        
        # 按完整度分级统计
        if completeness >= 0.9:
            self.results['by_completeness']['high']['cases'] += 1
            self.results['by_completeness']['high']['accurate'] += accuracy
        elif completeness >= 0.6:
            self.results['by_completeness']['medium']['cases'] += 1
            self.results['by_completeness']['medium']['accurate'] += accuracy
        else:
            self.results['by_completeness']['low']['cases'] += 1
            self.results['by_completeness']['low']['accurate'] += accuracy
        
        # 追问统计
        follow_up_count = len(parse_result.get('missing_fields', []))
        self.results['follow_up_stats']['total_questions'] += follow_up_count
    
    def _calculate_final_stats(self):
        """计算最终统计"""
        self.results['metadata']['total_cases'] = sum(
            data['cases'] for data in self.results['by_mode'].values()
        )
        
        # 计算平均值
        for mode, data in self.results['by_mode'].items():
            if data['cases'] > 0:
                data['avg_accuracy'] = data['accurate'] / data['cases']
                data['avg_completeness'] = data['avg_completeness'] / data['cases']
        
        for dispute_type, data in self.results['by_dispute_type'].items():
            if data['cases'] > 0:
                data['avg_accuracy'] = data['accurate'] / data['cases']
        
        for level, data in self.results['by_completeness'].items():
            if data['cases'] > 0:
                data['avg_accuracy'] = data['accurate'] / data['cases']
        
        total_cases = self.results['metadata']['total_cases']
        if total_cases > 0:
            self.results['follow_up_stats']['avg_questions_per_case'] = (
                self.results['follow_up_stats']['total_questions'] / total_cases
            )
    
    def save_results(self, filename: str = None):
        """保存测试结果"""
        if filename is None:
            filename = f'v3_test_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 80)
        report.append(" " * 25 + "v3.0 综合测试报告")
        report.append("=" * 80)
        report.append(f"测试时间：{self.results['metadata']['test_time']}")
        report.append(f"测试版本：{self.results['metadata']['version']}")
        report.append(f"总案例数：{self.results['metadata']['total_cases']}")
        report.append("")
        
        # 按模式对比
        report.append("=" * 80)
        report.append("【输入模式对比】")
        report.append("=" * 80)
        report.append(f"{'模式':<15} {'案例数':<10} {'准确率':<10} {'完整度':<10} {'推荐度':<10}")
        report.append("-" * 80)
        
        for mode, data in self.results['by_mode'].items():
            mode_name = '结构化' if mode == 'structured' else '混合式'
            accuracy = data.get('avg_accuracy', 0) * 100
            completeness = data.get('avg_completeness', 0) * 100
            stars = '⭐' * round(accuracy / 20)
            report.append(f"{mode_name:<15} {data['cases']:<10} {accuracy:.1f}%{' '*5} {completeness:.1f}%{' '*5} {stars}")
        
        report.append("")
        
        # 按纠纷类型统计
        report.append("=" * 80)
        report.append("【纠纷类型统计】")
        report.append("=" * 80)
        
        for dispute_type, data in self.results['by_dispute_type'].items():
            accuracy = data.get('avg_accuracy', 0) * 100
            report.append(f"{dispute_type}: {data['cases']}例 - 准确率 {accuracy:.1f}% "
                         f"(结构化{data['structured']}例，混合式{data['mixed']}例)")
        
        report.append("")
        
        # 按完整度分级
        report.append("=" * 80)
        report.append("【信息完整度分级】")
        report.append("=" * 80)
        
        for level, data in self.results['by_completeness'].items():
            level_name = {'high': '完整 (≥90%)', 'medium': '基本完整 (60-90%)', 'low': '不完整 (<60%)'}
            accuracy = data.get('avg_accuracy', 0) * 100
            report.append(f"{level_name[level]}: {data['cases']}例 - 准确率 {accuracy:.1f}%")
        
        report.append("")
        
        # 智能追问统计
        report.append("=" * 80)
        report.append("【智能追问统计】")
        report.append("=" * 80)
        avg_questions = self.results['follow_up_stats']['avg_questions_per_case']
        report.append(f"总追问数：{self.results['follow_up_stats']['total_questions']}")
        report.append(f"平均每例追问：{avg_questions:.2f}个")
        
        report.append("")
        
        # 结论
        report.append("=" * 80)
        report.append("【测试结论】")
        report.append("=" * 80)
        
        structured_acc = self.results['by_mode']['structured'].get('avg_accuracy', 0) * 100
        mixed_acc = self.results['by_mode']['mixed'].get('avg_accuracy', 0) * 100
        
        if structured_acc > mixed_acc:
            report.append(f"🏆 获胜模式：结构化描述（准确率 {structured_acc:.1f}%）")
        else:
            report.append(f"🏆 获胜模式：混合式描述（准确率 {mixed_acc:.1f}%）")
        
        report.append("")
        report.append("💡 推荐策略：")
        report.append("  1. 正式咨询：使用结构化描述（准确率最高）")
        report.append("  2. 日常咨询：使用混合式描述（平衡速度和准确率）")
        report.append("  3. 快速咨询：使用一句话描述 + 智能追问")
        
        report.append("")
        report.append("=" * 80)
        
        return '\n'.join(report)


# 主测试函数
if __name__ == '__main__':
    tester = ComprehensiveTester()
    
    # 生成测试案例
    print("生成测试案例...")
    test_cases = tester.generate_test_cases(count=1000)
    print(f"已生成 {len(test_cases)} 个测试案例\n")
    
    # 运行测试
    results = tester.run_test(test_cases)
    
    # 生成报告
    print("\n")
    report = tester.generate_report()
    print(report)
    
    # 保存结果
    filepath = tester.save_results()
    print(f"\n测试结果已保存到：{filepath}")
