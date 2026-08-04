#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
胜诉率统计系统 v2.3
基于案例数据分析胜诉率、赔偿区间、裁判倾向等

功能：
1. 胜诉率统计
2. 赔偿金额区间
3. 法院裁判倾向
4. 律师胜诉率
5. 诉讼时长统计
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path


class WinRateAnalyzer:
    """胜诉率分析系统"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化
        
        Args:
            data_dir: 数据存储目录
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent / "analytics"
        else:
            self.data_dir = Path(data_dir)
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件
        self.stats_file = self.data_dir / "win_rate_stats.json"
        self.lawyers_file = self.data_dir / "lawyers.json"
        self.firms_file = self.data_dir / "law_firms.json"
        
        # 初始化数据
        self._init_data()
        
        # 加载数据
        self.stats = self._load_json(self.stats_file, {})
        self.lawyers = self._load_json(self.lawyers_file, [])
        self.firms = self._load_json(self.firms_file, [])
    
    def _init_data(self):
        """初始化数据文件"""
        if not self.stats_file.exists():
            # 初始化示例统计数据
            initial_stats = {
                '劳动合同': {
                    'total_cases': 1000,
                    'employee_win': 650,  # 员工胜诉
                    'employer_win': 350,  # 用人单位胜诉
                    'win_rate': 65.0,  # 员工胜诉率
                    'avg_compensation': 85000,  # 平均赔偿
                    'min_compensation': 5000,
                    'max_compensation': 500000,
                    'avg_duration_days': 90,  # 平均审理天数
                    'regions': {
                        '北京': {'win_rate': 68.0, 'cases': 200},
                        '上海': {'win_rate': 65.0, 'cases': 180},
                        '广东': {'win_rate': 63.0, 'cases': 220},
                        '其他': {'win_rate': 64.0, 'cases': 400}
                    }
                },
                '消费纠纷': {
                    'total_cases': 800,
                    'consumer_win': 600,
                    'business_win': 200,
                    'win_rate': 75.0,
                    'avg_compensation': 15000,
                    'min_compensation': 500,
                    'max_compensation': 100000,
                    'avg_duration_days': 60
                },
                '离婚纠纷': {
                    'total_cases': 1200,
                    'plaintiff_win': 720,
                    'defendant_win': 480,
                    'win_rate': 60.0,
                    'avg_compensation': 150000,
                    'min_compensation': 10000,
                    'max_compensation': 2000000,
                    'avg_duration_days': 120
                },
                '借款纠纷': {
                    'total_cases': 1500,
                    'plaintiff_win': 1200,
                    'defendant_win': 300,
                    'win_rate': 80.0,
                    'avg_compensation': 120000,
                    'min_compensation': 1000,
                    'max_compensation': 1000000,
                    'avg_duration_days': 75
                },
                '交通事故': {
                    'total_cases': 900,
                    'victim_win': 810,
                    'driver_win': 90,
                    'win_rate': 90.0,
                    'avg_compensation': 180000,
                    'min_compensation': 10000,
                    'max_compensation': 1500000,
                    'avg_duration_days': 100
                }
            }
            self._save_json(self.stats_file, initial_stats)
        
        if not self.lawyers_file.exists():
            # 初始化示例律师数据
            initial_lawyers = [
                {
                    'name': '张律师',
                    'firm': 'XX 律师事务所',
                    'specialties': ['劳动合同', '消费纠纷'],
                    'years_experience': 10,
                    'total_cases': 500,
                    'win_cases': 420,
                    'win_rate': 84.0,
                    'regions': ['北京'],
                    'contact': {
                        'phone': '138****1234',
                        'email': 'zhang@example.com',
                        'wechat': 'zhang_lawyer'
                    },
                    'fee_range': '5000-20000 元',
                    'rating': 4.8,
                    'reviews': 120
                },
                {
                    'name': '李律师',
                    'firm': 'YY 律师事务所',
                    'specialties': ['离婚纠纷', '婚姻家庭'],
                    'years_experience': 15,
                    'total_cases': 800,
                    'win_cases': 680,
                    'win_rate': 85.0,
                    'regions': ['上海', '北京'],
                    'contact': {
                        'phone': '139****5678',
                        'email': 'li@example.com'
                    },
                    'fee_range': '8000-30000 元',
                    'rating': 4.9,
                    'reviews': 200
                },
                {
                    'name': '王律师',
                    'firm': 'ZZ 律师事务所',
                    'specialties': ['借款纠纷', '合同纠纷'],
                    'years_experience': 8,
                    'total_cases': 350,
                    'win_cases': 290,
                    'win_rate': 82.9,
                    'regions': ['广东', '深圳'],
                    'contact': {
                        'phone': '137****9012',
                        'email': 'wang@example.com'
                    },
                    'fee_range': '3000-15000 元',
                    'rating': 4.7,
                    'reviews': 85
                },
                {
                    'name': '赵律师',
                    'firm': 'AA 律师事务所',
                    'specialties': ['交通事故', '人身损害'],
                    'years_experience': 12,
                    'total_cases': 600,
                    'win_cases': 550,
                    'win_rate': 91.7,
                    'regions': ['北京', '天津'],
                    'contact': {
                        'phone': '136****3456',
                        'email': 'zhao@example.com'
                    },
                    'fee_range': '6000-25000 元',
                    'rating': 4.9,
                    'reviews': 150
                }
            ]
            self._save_json(self.lawyers_file, initial_lawyers)
        
        if not self.firms_file.exists():
            # 初始化示例律所数据
            initial_firms = [
                {
                    'name': 'XX 律师事务所',
                    'regions': ['北京'],
                    'specialties': ['劳动', '公司', '知识产权'],
                    'lawyers_count': 50,
                    'established_year': 2000,
                    'rating': 4.8,
                    'contact': {
                        'phone': '010-****1234',
                        'address': '北京市朝阳区建国门外大街 1 号国贸大厦 A 座 10 层',
                        'website': 'www.xxlaw.com',
                        'subway': '地铁 1 号线/10 号线国贸站 C 口出',
                        'landmark': '国贸桥东北角'
                    }
                },
                {
                    'name': 'YY 律师事务所',
                    'regions': ['上海', '北京'],
                    'specialties': ['婚姻', '家事', '继承'],
                    'lawyers_count': 30,
                    'established_year': 2005,
                    'rating': 4.9,
                    'contact': {
                        'phone': '021-****5678',
                        'address': '上海市浦东新区陆家嘴环路 1000 号恒生银行大厦 15 层',
                        'subway': '地铁 2 号线陆家嘴站 2 号口出',
                        'landmark': '东方明珠对面'
                    }
                },
                {
                    'name': 'ZZ 律师事务所',
                    'regions': ['广东', '深圳'],
                    'specialties': ['合同', '借款', '公司'],
                    'lawyers_count': 40,
                    'established_year': 2008,
                    'rating': 4.7,
                    'contact': {
                        'phone': '0755-****9012',
                        'address': '深圳市福田区深南大道 4001 号时代金融中心 18 层',
                        'subway': '地铁 1 号线/4 号线会展中心站 E 口出',
                        'landmark': '市民中心旁'
                    }
                },
                {
                    'name': 'AA 律师事务所',
                    'regions': ['北京', '天津'],
                    'specialties': ['交通事故', '人身损害', '保险'],
                    'lawyers_count': 25,
                    'established_year': 2010,
                    'rating': 4.9,
                    'contact': {
                        'phone': '010-****3456',
                        'address': '北京市东城区东长安街 1 号东方广场 W2 座 12 层',
                        'subway': '地铁 1 号线/5 号线东单站 B 口出',
                        'landmark': '王府井大街南口'
                    }
                }
            ]
            self._save_json(self.firms_file, initial_firms)
    
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
    
    def get_win_rate(self, dispute_type: str, region: str = None) -> Dict:
        """
        获取胜诉率
        
        Args:
            dispute_type: 纠纷类型
            region: 地区（可选）
            
        Returns:
            胜诉率数据
        """
        if dispute_type not in self.stats:
            return {
                'success': False,
                'error': f'暂无{dispute_type}的统计数据'
            }
        
        data = self.stats[dispute_type]
        
        result = {
            'success': True,
            'dispute_type': dispute_type,
            'win_rate': data.get('win_rate', 0),
            'total_cases': data.get('total_cases', 0),
            'avg_compensation': data.get('avg_compensation', 0),
            'compensation_range': {
                'min': data.get('min_compensation', 0),
                'max': data.get('max_compensation', 0)
            },
            'avg_duration_days': data.get('avg_duration_days', 0)
        }
        
        # 如果有地区数据
        if region and 'regions' in data:
            if region in data['regions']:
                result['region_data'] = data['regions'][region]
        
        return result
    
    def recommend_lawyers(self, dispute_type: str, region: str = None, limit: int = 3) -> List[Dict]:
        """
        推荐律师
        
        Args:
            dispute_type: 纠纷类型
            region: 地区
            limit: 返回数量
            
        Returns:
            推荐律师列表
        """
        # 筛选专业匹配的律师
        matched = []
        for lawyer in self.lawyers:
            # 检查专业匹配
            specialties = lawyer.get('specialties', [])
            if any(dispute_type in spec for spec in specialties):
                # 检查地区匹配
                if region:
                    lawyer_regions = lawyer.get('regions', [])
                    if region in lawyer_regions:
                        matched.append(lawyer)
                else:
                    matched.append(lawyer)
        
        # 按胜诉率排序
        matched.sort(key=lambda x: x.get('win_rate', 0), reverse=True)
        
        return matched[:limit]
    
    def recommend_firms(self, dispute_type: str, region: str = None, limit: int = 3) -> List[Dict]:
        """
        推荐律所
        
        Args:
            dispute_type: 纠纷类型
            region: 地区
            limit: 返回数量
            
        Returns:
            推荐律所列表
        """
        # 筛选专业匹配的律所
        matched = []
        for firm in self.firms:
            specialties = firm.get('specialties', [])
            if any(dispute_type in spec for spec in specialties):
                if region:
                    firm_regions = firm.get('regions', [])
                    if region in firm_regions:
                        matched.append(firm)
                else:
                    matched.append(firm)
        
        # 按评分排序
        matched.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        return matched[:limit]
    
    def get_analytics_report(self, dispute_type: str, region: str = None) -> str:
        """
        生成分析报告
        
        Args:
            dispute_type: 纠纷类型
            region: 地区
            
        Returns:
            格式化的分析报告
        """
        win_rate_data = self.get_win_rate(dispute_type, region)
        
        if not win_rate_data.get('success'):
            return win_rate_data.get('error', '无法生成报告')
        
        report = []
        report.append("=" * 60)
        report.append(f"📊 {dispute_type} 胜诉率分析报告")
        report.append("=" * 60)
        report.append("")
        
        # 胜诉率
        report.append("【胜诉率统计】")
        report.append(f"  总体胜诉率：{win_rate_data['win_rate']}%")
        report.append(f"  案例总数：{win_rate_data['total_cases']} 个")
        
        if 'region_data' in win_rate_data:
            region_info = win_rate_data['region_data']
            report.append(f"  {region}胜诉率：{region_info.get('win_rate', 'N/A')}%")
            report.append(f"  {region}案例数：{region_info.get('cases', 'N/A')} 个")
        report.append("")
        
        # 赔偿金额
        report.append("【赔偿金额统计】")
        report.append(f"  平均赔偿：{win_rate_data['avg_compensation']:,} 元")
        comp_range = win_rate_data['compensation_range']
        report.append(f"  赔偿区间：{comp_range['min']:,} - {comp_range['max']:,} 元")
        report.append("")
        
        # 审理时长
        report.append("【审理时长】")
        report.append(f"  平均审理：{win_rate_data['avg_duration_days']} 天")
        report.append("")
        
        # 推荐律师
        report.append("【推荐律师】")
        lawyers = self.recommend_lawyers(dispute_type, region, limit=3)
        for i, lawyer in enumerate(lawyers, 1):
            report.append(f"  {i}. {lawyer['name']} ({lawyer['firm']})")
            report.append(f"     胜诉率：{lawyer['win_rate']}%")
            report.append(f"     经验：{lawyer['years_experience']}年")
            report.append(f"     案例：{lawyer['total_cases']}个")
            if lawyer.get('contact'):
                contact = lawyer['contact']
                if contact.get('phone'):
                    report.append(f"     电话：{contact['phone']}")
                if contact.get('email'):
                    report.append(f"     邮箱：{contact['email']}")
            report.append(f"     收费：{lawyer.get('fee_range', '面议')}")
            report.append(f"     评分：⭐{lawyer.get('rating', 0)}")
            report.append("")
        
        # 推荐律所
        report.append("【推荐律所】")
        firms = self.recommend_firms(dispute_type, region, limit=2)
        for i, firm in enumerate(firms, 1):
            report.append(f"  {i}. {firm['name']}")
            report.append(f"     地区：{', '.join(firm.get('regions', []))}")
            report.append(f"     专业：{', '.join(firm.get('specialties', []))}")
            report.append(f"     律师数：{firm.get('lawyers_count', 0)}人")
            report.append(f"     成立：{firm.get('established_year', 'N/A')}年")
            if firm.get('contact'):
                contact = firm['contact']
                if contact.get('phone'):
                    report.append(f"     电话：{contact['phone']}")
                if contact.get('address'):
                    report.append(f"     地址：{contact['address']}")
                if contact.get('subway'):
                    report.append(f"     地铁：{contact['subway']}")
                if contact.get('landmark'):
                    report.append(f"     地标：{contact['landmark']}")
                if contact.get('website'):
                    report.append(f"     网站：{contact['website']}")
            report.append(f"     评分：⭐{firm.get('rating', 0)}")
            report.append("")
        
        report.append("=" * 60)
        report.append("⚠️ 以上数据仅供参考，具体案件请咨询专业律师")
        report.append("=" * 60)
        
        return '\n'.join(report)


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("胜诉率统计系统测试")
    print("=" * 60)
    
    analyzer = WinRateAnalyzer()
    
    # 测试 1：获取胜诉率
    print("\n【测试 1】获取劳动合同纠纷胜诉率...")
    result = analyzer.get_win_rate('劳动合同', '北京')
    print(f"胜诉率：{result.get('win_rate', 0)}%")
    print(f"平均赔偿：{result.get('avg_compensation', 0):,}元")
    
    # 测试 2：推荐律师
    print("\n【测试 2】推荐劳动法律师...")
    lawyers = analyzer.recommend_lawyers('劳动合同', '北京', limit=3)
    for lawyer in lawyers:
        print(f"  - {lawyer['name']} (胜诉率：{lawyer['win_rate']}%)")
    
    # 测试 3：生成完整报告
    print("\n【测试 3】生成分析报告...")
    report = analyzer.get_analytics_report('劳动合同', '北京')
    print(report)
