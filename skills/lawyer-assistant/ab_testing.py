#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A/B 测试框架 v2.9
用于对比不同描述方式、提示词策略的效果

测试维度：
1. 描述方式对比（一句话 vs 多维度 vs 混合式）
2. 用户视角对比（当事人 vs 律师 vs 法学生等）
3. 提示词策略对比
4. 响应时间对比
"""

import json
import random
import time
from datetime import datetime
from typing import Dict, List
from pathlib import Path


class ABTestingFramework:
    """A/B 测试框架"""
    
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            self.output_dir = Path(__file__).parent / "ab_tests"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试配置
        self.test_configs = {
            'description_style': {
                'name': '描述方式对比测试',
                'variants': ['simple', 'structured', 'mixed'],
                'metric': 'accuracy',
                'sample_size': 100
            },
            'user_perspective': {
                'name': '用户视角对比测试',
                'variants': ['party', 'lawyer', 'student', 'hr', 'judge'],
                'metric': 'satisfaction',
                'sample_size': 50
            },
            'prompt_strategy': {
                'name': '提示词策略对比测试',
                'variants': ['direct', 'guided', 'interactive'],
                'metric': 'completeness',
                'sample_size': 50
            }
        }
        
        # 测试结果存储
        self.results_file = self.output_dir / "results.json"
        self.results = self._load_results()
    
    def _load_results(self) -> dict:
        """加载测试结果"""
        if self.results_file.exists():
            with open(self.results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'tests': [], 'summary': {}}
    
    def _save_results(self):
        """保存测试结果"""
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
    
    def create_test(self, test_type: str, test_cases: List[dict]) -> dict:
        """
        创建 A/B 测试
        
        Args:
            test_type: 测试类型（description_style, user_perspective, prompt_strategy）
            test_cases: 测试案例列表
            
        Returns:
            测试配置
        """
        if test_type not in self.test_configs:
            return {'error': f'未知的测试类型：{test_type}'}
        
        config = self.test_configs[test_type]
        
        test_run = {
            'test_id': self._generate_test_id(),
            'test_type': test_type,
            'test_name': config['name'],
            'created_at': datetime.now().isoformat(),
            'status': 'running',
            'variants': {v: {'samples': 0, 'metrics': []} for v in config['variants']},
            'test_cases_count': len(test_cases),
            'results': []
        }
        
        return test_run
    
    def run_test(self, test_run: dict, test_cases: List[dict], process_func) -> dict:
        """
        运行 A/B 测试
        
        Args:
            test_run: 测试配置
            test_cases: 测试案例
            process_func: 处理函数（接收案例，返回结果）
            
        Returns:
            测试结果
        """
        variants = test_run['variants']
        
        for i, case in enumerate(test_cases):
            # 随机分配变体
            variant = random.choice(list(variants.keys()))
            
            # 处理案例
            start_time = time.time()
            result = process_func(case, variant)
            end_time = time.time()
            
            # 记录指标
            metrics = {
                'case_id': case.get('case_id', f'case_{i}'),
                'variant': variant,
                'accuracy': result.get('accuracy', 0),
                'completeness': result.get('completeness', 0),
                'satisfaction': result.get('satisfaction', 0),
                'response_time': end_time - start_time,
                'timestamp': datetime.now().isoformat()
            }
            
            # 更新统计
            variants[variant]['samples'] += 1
            variants[variant]['metrics'].append(metrics)
            
            test_run['results'].append(metrics)
            
            # 进度报告
            if (i + 1) % 10 == 0:
                print(f"进度：{i+1}/{len(test_cases)}")
        
        # 计算汇总统计
        test_run['summary'] = self._calculate_summary(variants)
        test_run['status'] = 'completed'
        test_run['completed_at'] = datetime.now().isoformat()
        
        # 保存结果
        self.results['tests'].append(test_run)
        self._save_results()
        
        return test_run
    
    def _calculate_summary(self, variants: dict) -> dict:
        """计算汇总统计"""
        summary = {}
        
        for variant, data in variants.items():
            metrics = data['metrics']
            if not metrics:
                continue
            
            summary[variant] = {
                'samples': data['samples'],
                'avg_accuracy': sum(m['accuracy'] for m in metrics) / len(metrics),
                'avg_completeness': sum(m['completeness'] for m in metrics) / len(metrics),
                'avg_satisfaction': sum(m['satisfaction'] for m in metrics) / len(metrics),
                'avg_response_time': sum(m['response_time'] for m in metrics) / len(metrics),
                'winner_score': self._calculate_winner_score(metrics)
            }
        
        # 确定获胜者
        if summary:
            winner = max(summary.items(), key=lambda x: x[1]['winner_score'])
            summary['winner'] = winner[0]
            summary['winner_metrics'] = winner[1]
        
        return summary
    
    def _calculate_winner_score(self, metrics: list) -> float:
        """计算获胜分数（加权）"""
        if not metrics:
            return 0
        
        avg_accuracy = sum(m['accuracy'] for m in metrics) / len(metrics)
        avg_completeness = sum(m['completeness'] for m in metrics) / len(metrics)
        avg_satisfaction = sum(m['satisfaction'] for m in metrics) / len(metrics)
        
        # 准确率优先（权重 50%）
        return avg_accuracy * 0.5 + avg_completeness * 0.3 + avg_satisfaction * 0.2
    
    def _generate_test_id(self) -> str:
        """生成测试 ID"""
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = hashlib.md5(f"abtest_{timestamp}".encode()).hexdigest()[:8]
        return f"ABT_{timestamp}_{random_str}"
    
    def get_test_results(self, test_id: str = None) -> dict:
        """获取测试结果"""
        if test_id:
            for test in self.results['tests']:
                if test['test_id'] == test_id:
                    return test
            return {'error': '未找到测试'}
        
        return self.results
    
    def generate_report(self, test_id: str = None) -> str:
        """生成测试报告"""
        results = self.get_test_results(test_id)
        
        if 'error' in results:
            return results['error']
        
        report = []
        report.append("=" * 60)
        report.append(f"A/B 测试报告 - {results.get('test_name', 'N/A')}")
        report.append("=" * 60)
        report.append(f"测试 ID: {results['test_id']}")
        report.append(f"测试类型：{results['test_type']}")
        report.append(f"样本数量：{results['test_cases_count']}")
        report.append(f"完成时间：{results.get('completed_at', 'N/A')}")
        report.append("")
        
        # 各变体对比
        report.append("【各变体表现】")
        summary = results.get('summary', {})
        for variant, metrics in summary.items():
            if variant in ['winner', 'winner_metrics']:
                continue
            report.append(f"  {variant}:")
            report.append(f"    样本数：{metrics['samples']}")
            report.append(f"    准确率：{metrics['avg_accuracy']*100:.1f}%")
            report.append(f"    完整度：{metrics['avg_completeness']*100:.1f}%")
            report.append(f"    满意度：{metrics['avg_satisfaction']:.1f}星")
            report.append(f"    响应时间：{metrics['avg_response_time']:.2f}秒")
        report.append("")
        
        # 获胜者
        if 'winner' in summary:
            report.append("【获胜者】")
            report.append(f"  🏆 {summary['winner']}")
            report.append(f"  准确率：{summary['winner_metrics']['avg_accuracy']*100:.1f}%")
            report.append(f"  综合得分：{summary['winner_metrics']['winner_score']*100:.1f}")
        
        report.append("")
        report.append("=" * 60)
        
        return '\n'.join(report)


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("A/B 测试框架测试")
    print("=" * 60)
    
    framework = ABTestingFramework()
    
    # 创建模拟测试案例
    test_cases = [
        {'case_id': f'case_{i}', 'text': f'测试案例{i}'}
        for i in range(30)
    ]
    
    # 创建测试
    print("\n【创建测试】")
    test_run = framework.create_test('description_style', test_cases)
    print(f"测试 ID: {test_run['test_id']}")
    print(f"测试名称：{test_run['test_name']}")
    print(f"变体：{list(test_run['variants'].keys())}")
    
    # 模拟处理函数
    def mock_process(case, variant):
        # 模拟不同变体的表现
        if variant == 'structured':
            return {'accuracy': 0.96, 'completeness': 0.95, 'satisfaction': 4.7}
        elif variant == 'mixed':
            return {'accuracy': 0.91, 'completeness': 0.88, 'satisfaction': 4.5}
        else:  # simple
            return {'accuracy': 0.72, 'completeness': 0.65, 'satisfaction': 3.8}
    
    # 运行测试
    print("\n【运行测试】")
    results = framework.run_test(test_run, test_cases[:10], mock_process)
    
    # 生成报告
    print("\n【测试报告】")
    report = framework.generate_report(results['test_id'])
    print(report)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
