#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户贡献案例系统 v2.2
允许用户提交真实案例，持续扩充案例库

功能：
1. 案例提交
2. 案例审核
3. 案例存储
4. 积分奖励
5. 案例展示
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path


class UserContribution:
    """用户贡献案例管理系统"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化
        
        Args:
            data_dir: 数据存储目录
        """
        if data_dir is None:
            # 默认存储在工作空间
            self.data_dir = Path(__file__).parent / "user_cases"
        else:
            self.data_dir = Path(data_dir)
        
        # 确保目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self.cases_file = self.data_dir / "cases.json"
        self.users_file = self.data_dir / "users.json"
        self.stats_file = self.data_dir / "stats.json"
        
        # 初始化数据
        self._init_data()
        
        # 加载数据
        self.cases = self._load_json(self.cases_file, [])
        self.users = self._load_json(self.users_file, {})
        self.stats = self._load_json(self.stats_file, {
            'total_submissions': 0,
            'approved': 0,
            'pending': 0,
            'rejected': 0
        })
    
    def _init_data(self):
        """初始化数据文件"""
        if not self.cases_file.exists():
            self._save_json(self.cases_file, [])
        
        if not self.users_file.exists():
            self._save_json(self.users_file, {})
        
        if not self.stats_file.exists():
            self._save_json(self.stats_file, {
                'total_submissions': 0,
                'approved': 0,
                'pending': 0,
                'rejected': 0
            })
    
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
    
    def submit_case(self, case_data: Dict, user_id: str = None) -> Dict:
        """
        提交案例
        
        Args:
            case_data: 案例数据
                {
                    '案号': 'xxx',
                    '法院': 'xxx',
                    '日期': 'xxx',
                    '纠纷类型': 'xxx',
                    '案情描述': 'xxx',
                    '争议焦点': 'xxx',
                    '裁判结果': 'xxx',
                    '裁判要旨': 'xxx',
                    '证据清单': ['xxx'],
                    '诉讼金额': 'xxx',
                    '律师': 'xxx（可选）',
                    '备注': 'xxx'
                }
            user_id: 用户 ID（可用邮箱、手机号或匿名 ID）
            
        Returns:
            提交结果
        """
        # 生成用户 ID（如果未提供）
        if not user_id:
            user_id = f"anonymous_{datetime.now().timestamp()}"
        
        # 验证必填字段
        required_fields = ['纠纷类型', '案情描述', '裁判结果']
        missing = [f for f in required_fields if not case_data.get(f)]
        
        if missing:
            return {
                'success': False,
                'error': f'缺少必填字段：{", ".join(missing)}',
                'case_id': None
            }
        
        # 创建案例记录
        case_id = self._generate_case_id()
        
        case_record = {
            'case_id': case_id,
            'user_id': user_id,
            'submit_time': datetime.now().isoformat(),
            'status': 'pending',  # pending, approved, rejected
            'review_note': '',
            'data': case_data,
            'source': 'user_contribution',
            'views': 0,
            'likes': 0,
            'useful_count': 0
        }
        
        # 保存案例
        self.cases.append(case_record)
        self._save_json(self.cases_file, self.cases)
        
        # 更新用户信息
        if user_id not in self.users:
            self.users[user_id] = {
                'user_id': user_id,
                'register_time': datetime.now().isoformat(),
                'total_submissions': 0,
                'approved_count': 0,
                'points': 0,  # 积分
                'level': '新手'  # 新手，贡献者，专家，达人
            }
        
        self.users[user_id]['total_submissions'] += 1
        self._save_json(self.users_file, self.users)
        
        # 更新统计
        self.stats['total_submissions'] += 1
        self.stats['pending'] += 1
        self._save_json(self.stats_file, self.stats)
        
        return {
            'success': True,
            'message': '案例提交成功，等待审核',
            'case_id': case_id,
            'user_id': user_id,
            'points_earned': 10  # 提交获得 10 积分
        }
    
    def _generate_case_id(self) -> str:
        """生成案例 ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = hashlib.md5(f"{timestamp}{len(self.cases)}".encode()).hexdigest()[:8]
        return f"UC_{timestamp}_{random_str}"
    
    def review_case(self, case_id: str, approved: bool, review_note: str = '') -> Dict:
        """
        审核案例
        
        Args:
            case_id: 案例 ID
            approved: 是否通过
            review_note: 审核意见
            
        Returns:
            审核结果
        """
        # 查找案例
        case = None
        case_index = -1
        for i, c in enumerate(self.cases):
            if c['case_id'] == case_id:
                case = c
                case_index = i
                break
        
        if not case:
            return {
                'success': False,
                'error': '案例不存在'
            }
        
        if case['status'] != 'pending':
            return {
                'success': False,
                'error': f'案例已审核（状态：{case["status"]}）'
            }
        
        # 更新状态
        case['status'] = 'approved' if approved else 'rejected'
        case['review_note'] = review_note
        case['review_time'] = datetime.now().isoformat()
        
        self.cases[case_index] = case
        self._save_json(self.cases_file, self.cases)
        
        # 更新统计
        self.stats['pending'] -= 1
        if approved:
            self.stats['approved'] += 1
            # 奖励积分（审核通过额外 +20）
            user_id = case['user_id']
            if user_id in self.users:
                self.users[user_id]['approved_count'] += 1
                self.users[user_id]['points'] += 20
                self._update_user_level(user_id)
        else:
            self.stats['rejected'] += 1
        
        self._save_json(self.stats_file, self.stats)
        self._save_json(self.users_file, self.users)
        
        return {
            'success': True,
            'message': f'案例已{"通过" if approved else "拒绝"}',
            'case_id': case_id,
            'status': case['status']
        }
    
    def _update_user_level(self, user_id: str):
        """更新用户等级"""
        user = self.users[user_id]
        approved = user['approved_count']
        
        if approved >= 50:
            user['level'] = '达人'
        elif approved >= 20:
            user['level'] = '专家'
        elif approved >= 5:
            user['level'] = '贡献者'
        else:
            user['level'] = '新手'
    
    def get_approved_cases(self, limit: int = 10, dispute_type: str = None) -> List[Dict]:
        """
        获取已审核通过的案例
        
        Args:
            limit: 返回数量
            dispute_type: 纠纷类型筛选
            
        Returns:
            案例列表
        """
        approved = [c for c in self.cases if c['status'] == 'approved']
        
        # 按纠纷类型筛选
        if dispute_type:
            approved = [c for c in approved if dispute_type in c['data'].get('纠纷类型', '')]
        
        # 按提交时间排序（最新的在前）
        approved.sort(key=lambda x: x['submit_time'], reverse=True)
        
        return approved[:limit]
    
    def search_cases(self, keyword: str, limit: int = 10) -> List[Dict]:
        """
        搜索用户贡献的案例
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量
            
        Returns:
            案例列表
        """
        approved = [c for c in self.cases if c['status'] == 'approved']
        
        results = []
        for case in approved:
            # 在多个字段中搜索关键词
            text = (
                case['data'].get('纠纷类型', '') +
                case['data'].get('案情描述', '') +
                case['data'].get('争议焦点', '') +
                case['data'].get('裁判结果', '')
            )
            
            if keyword.lower() in text.lower():
                results.append(case)
        
        # 按相关度排序（简单的关键词匹配数）
        results.sort(key=lambda x: text.lower().count(keyword.lower()), reverse=True)
        
        return results[:limit]
    
    def get_user_stats(self, user_id: str) -> Dict:
        """获取用户统计信息"""
        if user_id not in self.users:
            return {
                'success': False,
                'error': '用户不存在'
            }
        
        user = self.users[user_id]
        return {
            'success': True,
            'data': user
        }
    
    def get_system_stats(self) -> Dict:
        """获取系统统计信息"""
        return {
            'total_submissions': self.stats['total_submissions'],
            'approved': self.stats['approved'],
            'pending': self.stats['pending'],
            'rejected': self.stats['rejected'],
            'total_users': len(self.users),
            'approval_rate': round(
                self.stats['approved'] / max(1, self.stats['total_submissions']) * 100, 2
            )
        }
    
    def like_case(self, case_id: str) -> Dict:
        """点赞案例"""
        for case in self.cases:
            if case['case_id'] == case_id:
                case['likes'] += 1
                self._save_json(self.cases_file, self.cases)
                return {
                    'success': True,
                    'likes': case['likes']
                }
        
        return {
            'success': False,
            'error': '案例不存在'
        }
    
    def mark_useful(self, case_id: str) -> Dict:
        """标记为有用"""
        for case in self.cases:
            if case['case_id'] == case_id:
                case['useful_count'] += 1
                # 奖励提交者积分（每次 +1，上限 100）
                if case['useful_count'] <= 100:
                    user_id = case['user_id']
                    if user_id in self.users:
                        self.users[user_id]['points'] += 1
                        self._save_json(self.users_file, self.users)
                
                self._save_json(self.cases_file, self.cases)
                return {
                    'success': True,
                    'useful_count': case['useful_count']
                }
        
        return {
            'success': False,
            'error': '案例不存在'
        }


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("用户贡献案例系统测试")
    print("=" * 60)
    
    uc = UserContribution()
    
    # 测试 1：提交案例
    print("\n【测试 1】提交案例...")
    case_data = {
        '案号': '(2024) 京 01 民终 1234 号',
        '法院': '北京市第一中级人民法院',
        '日期': '2024-01-15',
        '纠纷类型': '劳动合同纠纷',
        '案情描述': '公司违法解除劳动合同，员工工作 3 年...',
        '争议焦点': '违法解除赔偿金计算',
        '裁判结果': '公司支付赔偿金 18 万元',
        '裁判要旨': '公司未提供培训或调岗证据，构成违法解除',
        '证据清单': ['劳动合同', '解除通知', '工资流水'],
        '诉讼金额': '18 万元',
        '备注': '典型案例，值得参考'
    }
    
    result = uc.submit_case(case_data, user_id='test_user_001')
    print(f"提交结果：{result}")
    
    if result['success']:
        case_id = result['case_id']
        
        # 测试 2：审核案例
        print("\n【测试 2】审核案例...")
        review_result = uc.review_case(case_id, approved=True, review_note='案例质量高，通过审核')
        print(f"审核结果：{review_result}")
        
        # 测试 3：获取已审核案例
        print("\n【测试 3】获取已审核案例...")
        cases = uc.get_approved_cases(limit=5)
        print(f"找到 {len(cases)} 个已审核案例")
        for case in cases:
            print(f"  - {case['data']['案号']}")
        
        # 测试 4：搜索案例
        print("\n【测试 4】搜索案例...")
        results = uc.search_cases("违法解除", limit=5)
        print(f"搜索到 {len(results)} 个相关案例")
        
        # 测试 5：点赞
        print("\n【测试 5】点赞案例...")
        like_result = uc.like_case(case_id)
        print(f"点赞结果：{like_result}")
        
        # 测试 6：用户统计
        print("\n【测试 6】用户统计...")
        user_stats = uc.get_user_stats('test_user_001')
        print(f"用户统计：{user_stats['data']}")
        
        # 测试 7：系统统计
        print("\n【测试 7】系统统计...")
        sys_stats = uc.get_system_stats()
        print(f"系统统计：{sys_stats}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
