#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务评价系统 v2.6
用于用户满意度调查、分析方案满意度、律师满意度等多维度评价

功能：
1. 多维度评价（整体、分析方案、律师推荐）
2. 星级评价（1-5 星）
3. 不满意原因选择
4. 文字评价
5. 评价统计与分析
6. 改进建议生成
"""

import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class RatingSystem:
    """服务评价系统 v2.7"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化
        
        Args:
            data_dir: 数据存储目录
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent / "ratings"
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件
        self.ratings_file = self.data_dir / "ratings.json"
        self.stats_file = self.data_dir / "statistics.json"
        self.replies_file = self.data_dir / "replies.json"
        self.trends_file = self.data_dir / "trends.json"
        
        # 评价标签系统
        self.tag_categories = {
            'positive': [
                '专业准确', '分析详细', '实用建议', '响应快速', 
                '法条清晰', '案例相关', '律师匹配', '界面友好'
            ],
            'negative': [
                '分析不准', '建议无用', '响应慢', '法条错误', 
                '案例不相关', '律师不匹配', '计算错误', '内容简单'
            ],
            'feature': [
                '赔偿计算', '胜诉率', '律师推荐', '法条详解', 
                '案例推荐', '用户贡献', '文书模板'
            ]
        }
        
        # 评价维度
        self.rating_dimensions = {
            'overall': '整体服务',
            'analysis': '案件分析',
            'lawyer': '律师推荐',
            'winrate': '胜诉率统计',
            'articles': '法条详解',
            'cases': '案例推荐'
        }
        
        # 不满意原因选项
        self.dissatisfaction_reasons = {
            'analysis': [
                '分析不够专业',
                '法条引用错误',
                '赔偿计算不准',
                '建议不实用',
                '内容太简单',
                '内容太复杂',
                '其他'
            ],
            'lawyer': [
                '律师不匹配',
                '联系方式错误',
                '收费不合理',
                '胜诉率虚高',
                '地区不匹配',
                '专业不匹配',
                '其他'
            ],
            'cases': [
                '案例不相关',
                '案例太旧',
                '案例太少',
                '案例不真实',
                '其他'
            ],
            'overall': [
                '响应太慢',
                '功能不好用',
                '界面不友好',
                '信息不准确',
                '其他'
            ]
        }
        
        # 初始化数据
        self._init_data()
        
        # 加载数据
        self.ratings = self._load_json(self.ratings_file, [])
        self.stats = self._load_json(self.stats_file, self._default_stats())
        self.replies = self._load_json(self.replies_file, [])
        self.trends = self._load_json(self.trends_file, [])
    
    def _init_data(self):
        """初始化数据文件"""
        if not self.ratings_file.exists():
            self._save_json(self.ratings_file, [])
        
        if not self.stats_file.exists():
            self._save_json(self.stats_file, self._default_stats())
        
        if not self.replies_file.exists():
            self._save_json(self.replies_file, [])
        
        if not self.trends_file.exists():
            self._save_json(self.trends_file, [])
    
    def _default_stats(self) -> Dict:
        """默认统计数据"""
        return {
            'total_ratings': 0,
            'by_dimension': {
                dim: {
                    'count': 0,
                    'sum_stars': 0,
                    'avg_stars': 0,
                    '5_star': 0,
                    '4_star': 0,
                    '3_star': 0,
                    '2_star': 0,
                    '1_star': 0
                }
                for dim in self.rating_dimensions.keys()
            },
            'dissatisfaction_reasons': {
                reason: 0
                for reasons in self.dissatisfaction_reasons.values()
                for reason in reasons
            },
            'time_stats': {
                'today': 0,
                'this_week': 0,
                'this_month': 0
            }
        }
    
    def _load_json(self, filepath: Path, default):
        """加载 JSON 文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    
    def _save_json(self, filepath: Path, data):
        """保存 JSON 文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def add_tags_to_rating(self, rating_id: str, tags: List[str]) -> Dict:
        """
        为评价添加标签
        
        Args:
            rating_id: 评价 ID
            tags: 标签列表
            
        Returns:
            操作结果
        """
        # 查找评价
        for rating in self.ratings:
            if rating['rating_id'] == rating_id:
                # 验证标签
                valid_tags = []
                for tag in tags:
                    all_tags = (
                        self.tag_categories['positive'] + 
                        self.tag_categories['negative'] + 
                        self.tag_categories['feature']
                    )
                    if tag in all_tags:
                        valid_tags.append(tag)
                
                # 保存标签
                rating['data']['tags'] = valid_tags
                self._save_json(self.ratings_file, self.ratings)
                
                return {
                    'success': True,
                    'message': '标签添加成功',
                    'tags': valid_tags
                }
        
        return {
            'success': False,
            'error': '评价不存在'
        }
    
    def auto_tag_rating(self, rating_data: Dict) -> List[str]:
        """
        自动为评价添加标签
        
        Args:
            rating_data: 评价数据
            
        Returns:
            自动生成的标签列表
        """
        tags = []
        
        # 根据评分自动打标签
        dimensions = rating_data.get('dimensions', {})
        avg_stars = sum(dimensions.values()) / len(dimensions) if dimensions else 0
        
        if avg_stars >= 4.5:
            tags.extend(['专业准确', '分析详细'])
        elif avg_stars >= 4.0:
            tags.append('实用建议')
        elif avg_stars <= 2.5:
            tags.append('需要改进')
        
        # 根据文字评价提取标签
        comments = rating_data.get('comments', '')
        if '法条' in comments:
            tags.append('法条清晰' if avg_stars >= 4 else '法条错误')
        if '案例' in comments:
            tags.append('案例相关' if avg_stars >= 4 else '案例不相关')
        if '律师' in comments:
            tags.append('律师匹配' if avg_stars >= 4 else '律师不匹配')
        if '计算' in comments:
            tags.append('赔偿计算')
        
        return list(set(tags))  # 去重
    
    def submit_rating(self, rating_data: Dict) -> Dict:
        """
        提交评价
        
        Args:
            rating_data: 评价数据
                {
                    'user_id': '用户 ID',
                    'session_id': '会话 ID',
                    'dispute_type': '纠纷类型',
                    'dimensions': {  # 各维度评分
                        'overall': 5,
                        'analysis': 4,
                        'lawyer': 5,
                        ...
                    },
                    'dissatisfaction': {  # 不满意原因（可选）
                        'analysis': ['分析不够专业'],
                        'lawyer': ['地区不匹配']
                    },
                    'comments': '文字评价（可选）',
                    'suggestions': '改进建议（可选）',
                    'would_recommend': True  # 是否会推荐
                }
            
        Returns:
            提交结果
        """
        # 验证必填字段
        required = ['user_id', 'dimensions']
        missing = [f for f in required if f not in rating_data]
        
        if missing:
            return {
                'success': False,
                'error': f'缺少必填字段：{", ".join(missing)}'
            }
        
        # 验证评分范围
        dimensions = rating_data.get('dimensions', {})
        for dim, stars in dimensions.items():
            if not (1 <= stars <= 5):
                return {
                    'success': False,
                    'error': f'评分必须在 1-5 星之间（{dim}）'
                }
        
        # 自动添加标签
        auto_tags = self.auto_tag_rating(rating_data)
        rating_data['tags'] = auto_tags
        
        # 创建评价记录
        rating_record = {
            'rating_id': self._generate_rating_id(),
            'submit_time': datetime.now().isoformat(),
            'data': rating_data,
            'processed': False,
            'tags': auto_tags,
            'replies': []
        }
        
        # 保存评价
        self.ratings.append(rating_record)
        self._save_json(self.ratings_file, self.ratings)
        
        # 更新统计
        self._update_statistics(rating_data)
        
        # 更新趋势数据
        self._update_trends(rating_data)
        
        return {
            'success': True,
            'message': '感谢您的评价！',
            'rating_id': rating_record['rating_id'],
            'points_earned': 5 if rating_data.get('would_recommend', False) else 2,
            'auto_tags': auto_tags
        }
    
    def _generate_rating_id(self) -> str:
        """生成评价 ID"""
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = hashlib.md5(f"{timestamp}{len(self.ratings)}".encode()).hexdigest()[:8]
        return f"R_{timestamp}_{random_str}"
    
    def add_reply(self, rating_id: str, reply_data: Dict) -> Dict:
        """
        添加评价回复
        
        Args:
            rating_id: 评价 ID
            reply_data: 回复数据
                {
                    'reply_type': 'system|lawyer|admin',
                    'content': '回复内容',
                    'reply_by': '回复者 ID/名称'
                }
            
        Returns:
            操作结果
        """
        # 查找评价
        for rating in self.ratings:
            if rating['rating_id'] == rating_id:
                # 创建回复记录
                reply_record = {
                    'reply_id': self._generate_reply_id(),
                    'reply_time': datetime.now().isoformat(),
                    'reply_type': reply_data.get('reply_type', 'system'),
                    'content': reply_data.get('content', ''),
                    'reply_by': reply_data.get('reply_by', '系统')
                }
                
                # 保存回复
                rating['replies'].append(reply_record)
                self._save_json(self.ratings_file, self.ratings)
                
                # 保存到回复文件
                self.replies.append({
                    'rating_id': rating_id,
                    **reply_record
                })
                self._save_json(self.replies_file, self.replies)
                
                return {
                    'success': True,
                    'message': '回复成功',
                    'reply_id': reply_record['reply_id']
                }
        
        return {
            'success': False,
            'error': '评价不存在'
        }
    
    def get_replies(self, rating_id: str) -> List[Dict]:
        """获取评价的所有回复"""
        for rating in self.ratings:
            if rating['rating_id'] == rating_id:
                return rating.get('replies', [])
        return []
    
    def _generate_reply_id(self) -> str:
        """生成回复 ID"""
        import hashlib
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = hashlib.md5(f"reply_{timestamp}{len(self.replies)}".encode()).hexdigest()[:8]
        return f"RP_{timestamp}_{random_str}"
    
    def _update_trends(self, rating_data: Dict):
        """更新趋势数据"""
        now = datetime.now()
        period_key = now.strftime('%Y-%m')  # 按月统计
        
        # 查找或创建周期记录
        period_record = None
        for record in self.trends:
            if record['period'] == period_key:
                period_record = record
                break
        
        if not period_record:
            period_record = {
                'period': period_key,
                'total_ratings': 0,
                'by_dimension': {
                    dim: {'sum_stars': 0, 'count': 0}
                    for dim in self.rating_dimensions.keys()
                },
                'by_target': {
                    'platform': {'sum_stars': 0, 'count': 0},
                    'lawyer': {'sum_stars': 0, 'count': 0}
                }
            }
            self.trends.append(period_record)
        
        # 更新数据
        period_record['total_ratings'] += 1
        
        # 更新各维度
        dimensions = rating_data.get('dimensions', {})
        for dim, stars in dimensions.items():
            if dim in period_record['by_dimension']:
                period_record['by_dimension'][dim]['sum_stars'] += stars
                period_record['by_dimension'][dim]['count'] += 1
        
        # 更新目标维度（平台/律师）
        period_record['by_target']['platform']['sum_stars'] += dimensions.get('overall', 0)
        period_record['by_target']['platform']['count'] += 1
        
        if 'lawyer' in dimensions:
            period_record['by_target']['lawyer']['sum_stars'] += dimensions.get('lawyer', 0)
            period_record['by_target']['lawyer']['count'] += 1
        
        self._save_json(self.trends_file, self.trends)
    
    def get_trends(self, target: str = 'platform', period_count: int = 12) -> Dict:
        """
        获取满意度趋势
        
        Args:
            target: 'platform' 或 'lawyer'
            period_count: 返回多少个月的数据
            
        Returns:
            趋势数据
        """
        # 按时间排序
        sorted_trends = sorted(self.trends, key=lambda x: x['period'])[-period_count:]
        
        trend_data = {
            'target': target,
            'periods': [],
            'scores': [],
            'ratings_count': []
        }
        
        for record in sorted_trends:
            trend_data['periods'].append(record['period'])
            
            # 计算平均分
            if target in record['by_target']:
                target_data = record['by_target'][target]
                avg = round(
                    target_data['sum_stars'] / target_data['count'], 2
                ) if target_data['count'] > 0 else 0
                trend_data['scores'].append(avg)
                trend_data['ratings_count'].append(target_data['count'])
        
        return {
            'success': True,
            'data': trend_data
        }
    
    def _update_statistics(self, rating_data: Dict):
        """更新统计数据"""
        self.stats['total_ratings'] += 1
        
        # 更新各维度统计
        dimensions = rating_data.get('dimensions', {})
        for dim, stars in dimensions.items():
            if dim in self.stats['by_dimension']:
                dim_stats = self.stats['by_dimension'][dim]
                dim_stats['count'] += 1
                dim_stats['sum_stars'] += stars
                dim_stats['avg_stars'] = round(
                    dim_stats['sum_stars'] / dim_stats['count'], 2
                )
                
                # 更新星级分布
                star_key = f'{stars}_star'
                if star_key in dim_stats:
                    dim_stats[star_key] += 1
        
        # 更新不满意原因统计
        dissatisfaction = rating_data.get('dissatisfaction', {})
        for dim, reasons in dissatisfaction.items():
            for reason in reasons:
                if reason in self.stats['dissatisfaction_reasons']:
                    self.stats['dissatisfaction_reasons'][reason] += 1
        
        # 更新时间统计
        now = datetime.now()
        self.stats['time_stats']['today'] += 1
        # 简单实现，实际应该更精确
        if now.weekday() < 5:  # 本周
            self.stats['time_stats']['this_week'] += 1
        if now.day <= 30:  # 本月
            self.stats['time_stats']['this_month'] += 1
        
        self._save_json(self.stats_file, self.stats)
    
    def get_statistics(self, dimension: str = None) -> Dict:
        """
        获取统计数据
        
        Args:
            dimension: 维度（可选，不传则返回全部）
            
        Returns:
            统计数据
        """
        if dimension:
            if dimension not in self.stats['by_dimension']:
                return {
                    'success': False,
                    'error': f'未知的维度：{dimension}'
                }
            return {
                'success': True,
                'dimension': dimension,
                'name': self.rating_dimensions.get(dimension, dimension),
                'data': self.stats['by_dimension'][dimension]
            }
        
        return {
            'success': True,
            'total_ratings': self.stats['total_ratings'],
            'dimensions': {
                dim: {
                    'name': self.rating_dimensions[dim],
                    **data
                }
                for dim, data in self.stats['by_dimension'].items()
            },
            'dissatisfaction_reasons': self.stats['dissatisfaction_reasons'],
            'time_stats': self.stats['time_stats']
        }
    
    def get_rating_form(self, session_info: Dict = None) -> Dict:
        """
        获取评价表单
        
        Args:
            session_info: 会话信息（可选）
            
        Returns:
            评价表单结构
        """
        return {
            'form_version': '1.0',
            'dimensions': [
                {
                    'key': 'overall',
                    'name': '整体服务',
                    'required': True,
                    'stars': 5
                },
                {
                    'key': 'analysis',
                    'name': '案件分析质量',
                    'required': True,
                    'stars': 5
                },
                {
                    'key': 'lawyer',
                    'name': '律师推荐',
                    'required': False,
                    'stars': 5
                },
                {
                    'key': 'winrate',
                    'name': '胜诉率统计',
                    'required': False,
                    'stars': 5
                },
                {
                    'key': 'articles',
                    'name': '法条详解',
                    'required': False,
                    'stars': 5
                },
                {
                    'key': 'cases',
                    'name': '案例推荐',
                    'required': False,
                    'stars': 5
                }
            ],
            'dissatisfaction_reasons': self.dissatisfaction_reasons,
            'optional_fields': [
                {
                    'key': 'comments',
                    'name': '文字评价',
                    'type': 'text',
                    'max_length': 500
                },
                {
                    'key': 'suggestions',
                    'name': '改进建议',
                    'type': 'text',
                    'max_length': 500
                },
                {
                    'key': 'would_recommend',
                    'name': '是否会推荐给他人',
                    'type': 'boolean'
                }
            ],
            'session_info': session_info or {}
        }
    
    def generate_improvement_report(self) -> str:
        """
        生成改进建议报告
        
        Returns:
            格式化的改进建议报告
        """
        stats = self.get_statistics()
        
        if not stats.get('success') or stats['total_ratings'] == 0:
            return "暂无足够数据生成改进报告"
        
        report = []
        report.append("=" * 60)
        report.append("📊 服务评价分析与改进建议")
        report.append("=" * 60)
        report.append(f"总评价数：{stats['total_ratings']}")
        report.append("")
        
        # 各维度评分
        report.append("【各维度满意度】")
        for dim, data in stats['dimensions'].items():
            stars = '⭐' * round(data['avg_stars'])
            report.append(f"  {data['name']}: {data['avg_stars']}星 {stars}")
            report.append(f"    评价数：{data['count']} | 5 星：{data['5_star']} | 1 星：{data['1_star']}")
        report.append("")
        
        # 不满意原因分析
        report.append("【不满意原因 TOP5】")
        reasons = sorted(
            stats['dissatisfaction_reasons'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for i, (reason, count) in enumerate(reasons, 1):
            if count > 0:
                report.append(f"  {i}. {reason}: {count}次")
        report.append("")
        
        # 改进建议
        report.append("【改进建议】")
        
        # 根据评分最低的维度给出建议
        min_dim = min(
            stats['dimensions'].items(),
            key=lambda x: x[1]['avg_stars']
        )
        
        if min_dim[1]['avg_stars'] < 4.0:
            report.append(f"  ⚠️ 优先改进：{min_dim[1]['name']}（{min_dim[1]['avg_stars']}星）")
            
            # 根据不满意原因给出具体建议
            if min_dim[0] == 'analysis':
                report.append("    - 加强法律分析专业性")
                report.append("    - 提供更详细的法条解释")
                report.append("    - 优化赔偿计算准确性")
            elif min_dim[0] == 'lawyer':
                report.append("    - 优化律师匹配算法")
                report.append("    - 核实律师信息准确性")
                report.append("    - 增加律师数量")
            elif min_dim[0] == 'cases':
                report.append("    - 提高案例相关性")
                report.append("    - 更新案例库")
                report.append("    - 增加案例数量")
        
        # 通用建议
        report.append("  💡 通用建议：")
        report.append("    - 定期收集用户反馈")
        report.append("    - 持续优化核心功能")
        report.append("    - 加强数据准确性验证")
        report.append("")
        
        report.append("=" * 60)
        
        return '\n'.join(report)
    
    def get_user_ratings(self, user_id: str) -> List[Dict]:
        """获取用户的所有评价"""
        return [r for r in self.ratings if r['data'].get('user_id') == user_id]
    
    def get_recent_ratings(self, limit: int = 10) -> List[Dict]:
        """获取最近的评价"""
        sorted_ratings = sorted(
            self.ratings,
            key=lambda x: x['submit_time'],
            reverse=True
        )
        return sorted_ratings[:limit]
    
    def get_available_tags(self) -> Dict:
        """获取可用标签列表"""
        return self.tag_categories
    
    def get_tag_statistics(self) -> Dict:
        """获取标签使用统计"""
        tag_stats = {}
        
        # 统计所有标签的使用次数
        for rating in self.ratings:
            tags = rating.get('tags', [])
            for tag in tags:
                tag_stats[tag] = tag_stats.get(tag, 0) + 1
        
        # 排序
        sorted_tags = sorted(tag_stats.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_ratings': len(self.ratings),
            'tagged_ratings': sum(1 for r in self.ratings if r.get('tags')),
            'top_tags': sorted_tags[:20],
            'all_tags': tag_stats
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("服务评价系统测试")
    print("=" * 60)
    
    rs = RatingSystem()
    
    # 测试 1：获取评价表单
    print("\n【测试 1】获取评价表单...")
    form = rs.get_rating_form()
    print(f"评价维度：{len(form['dimensions'])}个")
    for dim in form['dimensions']:
        print(f"  - {dim['name']}（{'必填' if dim['required'] else '选填'}）")
    
    # 测试 2：提交评价
    print("\n【测试 2】提交评价...")
    rating_data = {
        'user_id': 'test_user_001',
        'session_id': 'session_123',
        'dispute_type': '劳动合同',
        'dimensions': {
            'overall': 5,
            'analysis': 4,
            'lawyer': 5,
            'winrate': 4,
            'articles': 5,
            'cases': 4
        },
        'dissatisfaction': {
            'analysis': ['内容太简单']
        },
        'comments': '整体很好，法条详解很实用！',
        'suggestions': '希望能增加更多案例',
        'would_recommend': True
    }
    
    result = rs.submit_rating(rating_data)
    print(f"提交结果：{result}")
    
    # 测试 3：获取统计
    print("\n【测试 3】获取统计数据...")
    stats = rs.get_statistics()
    print(f"总评价数：{stats.get('total_ratings', 0)}")
    
    if 'dimensions' in stats:
        for dim, data in stats['dimensions'].items():
            print(f"  {data['name']}: {data['avg_stars']}星")
    
    # 测试 4：生成改进报告
    print("\n【测试 4】生成改进报告...")
    report = rs.generate_improvement_report()
    print(report)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
