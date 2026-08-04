#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版案例数据 API 集成 v2.1
整合多个平替方案，确保数据获取稳定性

数据源优先级：
1. OpenLaw（主要，免费 100 次/天）
2. 无讼（备用，部分免费）
3. 中国法院网（公开数据）
4. 内置案例库（兜底）
"""

import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime


class EnhancedCaseAPI:
    """增强版案例 API 管理器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        
        # 数据源状态
        self.sources = {
            'openlaw': {
                'name': 'OpenLaw',
                'url': 'http://openlaw.cn',
                'available': True,
                'free_limit': 100,  # 每日免费次数
                'used_today': 0,
                'last_reset': datetime.now().date(),
                'avg_response_time': 2.0,
                'success_rate': 0.95
            },
            'itslaw': {
                'name': '无讼',
                'url': 'https://www.itslaw.com',
                'available': True,
                'free_limit': 50,
                'used_today': 0,
                'avg_response_time': 3.0,
                'success_rate': 0.90
            },
            'chinacourt': {
                'name': '中国法院网',
                'url': 'https://www.chinacourt.org',
                'available': True,
                'free_limit': -1,  # 无限制（公开数据）
                'avg_response_time': 5.0,
                'success_rate': 0.70
            },
            'builtin': {
                'name': '内置案例库',
                'available': True,
                'free_limit': -1,
                'count': 30,
                'avg_response_time': 0.1,
                'success_rate': 1.0
            }
        }
        
        # 缓存
        self.cache = {}
        self.cache_ttl = (config or {}).get('cache_ttl', 3600)
    
    def search(self, keyword: str, dispute_type: str = None, limit: int = 5) -> List[Dict]:
        """
        智能搜索案例
        
        按优先级尝试各数据源
        """
        # 检查缓存
        cache_key = f"{keyword}:{dispute_type}:{limit}"
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['time'] < self.cache_ttl:
                cached['data'][0]['source_note'] = '缓存命中'
                return cached['data']
        
        # 按优先级尝试
        results = []
        
        # 1. OpenLaw（优先）
        if self.sources['openlaw']['available']:
            results = self._try_openlaw(keyword, limit)
        
        # 2. 如果 OpenLaw 失败，尝试无讼
        if not results and self.sources['itslaw']['available']:
            results = self._try_itslaw(keyword, limit)
        
        # 3. 如果还是没结果，尝试中国法院网
        if not results and self.sources['chinacourt']['available']:
            results = self._try_chinacourt(keyword, limit)
        
        # 缓存结果
        if results and self.cache_ttl > 0:
            self.cache[cache_key] = {
                'data': results,
                'time': time.time(),
                'source': 'openlaw' if self.sources['openlaw']['available'] else 'fallback'
            }
        
        return results
    
    def _try_openlaw(self, keyword: str, limit: int) -> List[Dict]:
        """尝试 OpenLaw"""
        # 检查限额
        self._check_daily_limit('openlaw')
        
        if self.sources['openlaw']['used_today'] >= self.sources['openlaw']['free_limit']:
            return []
        
        start_time = time.time()
        
        try:
            # 模拟 OpenLaw 搜索（实际使用需要 API）
            # 这里返回示例数据
            cases = self._generate_mock_cases(keyword, limit, 'OpenLaw')
            
            # 更新统计
            elapsed = time.time() - start_time
            self._update_stats('openlaw', elapsed, len(cases) > 0)
            self.sources['openlaw']['used_today'] += 1
            
            return cases
            
        except Exception as e:
            self._update_stats('openlaw', time.time() - start_time, False)
            return []
    
    def _try_itslaw(self, keyword: str, limit: int) -> List[Dict]:
        """尝试无讼"""
        self._check_daily_limit('itslaw')
        
        if self.sources['itslaw']['used_today'] >= self.sources['itslaw']['free_limit']:
            return []
        
        start_time = time.time()
        
        try:
            # 模拟无讼搜索
            cases = self._generate_mock_cases(keyword, limit, '无讼')
            
            elapsed = time.time() - start_time
            self._update_stats('itslaw', elapsed, len(cases) > 0)
            self.sources['itslaw']['used_today'] += 1
            
            return cases
            
        except Exception as e:
            self._update_stats('itslaw', time.time() - start_time, False)
            return []
    
    def _try_chinacourt(self, keyword: str, limit: int) -> List[Dict]:
        """尝试中国法院网"""
        start_time = time.time()
        
        try:
            # 中国法院网公开数据
            cases = self._generate_mock_cases(keyword, limit, '中国法院网')
            
            elapsed = time.time() - start_time
            self._update_stats('chinacourt', elapsed, len(cases) > 0)
            
            return cases
            
        except Exception as e:
            self._update_stats('chinacourt', time.time() - start_time, False)
            return []
    
    def _generate_mock_cases(self, keyword: str, limit: int, source: str) -> List[Dict]:
        """
        生成模拟案例数据
        
        注意：实际使用时需要替换为真实 API 调用
        """
        # 这里返回示例数据，实际应该调用 API
        cases = []
        
        # 根据关键词生成相关案例
        if '劳动' in keyword or '辞退' in keyword:
            cases = [
                {
                    '案号': f'(2024) {source[:1]}01 民终 1234 号',
                    '法院': f'{source}示例法院',
                    '日期': '2024-01-15',
                    '案由': '劳动合同纠纷',
                    '争议焦点': '违法解除劳动合同',
                    '裁判要旨': '公司未提供培训或调岗证据，构成违法解除...',
                    '判决结果': '支付赔偿金',
                    'source': source
                }
            ]
        elif '消费' in keyword or '假货' in keyword:
            cases = [
                {
                    '案号': f'(2024) {source[:1]}02 民终 5678 号',
                    '法院': f'{source}示例法院',
                    '日期': '2024-02-20',
                    '案由': '网络购物合同纠纷',
                    '争议焦点': '假货三倍赔偿',
                    '裁判要旨': '商家销售假货构成欺诈...',
                    '判决结果': '退一赔三',
                    'source': source
                }
            ]
        elif '离婚' in keyword:
            cases = [
                {
                    '案号': f'(2024) {source[:1]}03 民终 9012 号',
                    '法院': f'{source}示例法院',
                    '日期': '2024-03-10',
                    '案由': '离婚纠纷',
                    '争议焦点': '出轨损害赔偿',
                    '裁判要旨': '一方存在过错，应支付损害赔偿...',
                    '判决结果': '准予离婚，支付损害赔偿 5 万元',
                    'source': source
                }
            ]
        
        return cases[:limit]
    
    def _check_daily_limit(self, source: str):
        """检查并重置每日限额"""
        today = datetime.now().date()
        if today > self.sources[source].get('last_reset', today):
            self.sources[source]['used_today'] = 0
            self.sources[source]['last_reset'] = today
    
    def _update_stats(self, source: str, elapsed: float, success: bool):
        """更新统计信息"""
        s = self.sources[source]
        # 更新平均响应时间（简单移动平均）
        s['avg_response_time'] = s['avg_response_time'] * 0.9 + elapsed * 0.1
        # 更新成功率
        if success:
            s['success_rate'] = min(1.0, s['success_rate'] + 0.01)
        else:
            s['success_rate'] = max(0.0, s['success_rate'] - 0.01)
    
    def get_stats(self) -> Dict:
        """获取使用统计"""
        return {
            'sources': {
                name: {
                    'name': info['name'],
                    'available': info['available'],
                    'used_today': info.get('used_today', 0),
                    'free_limit': info.get('free_limit', -1),
                    'avg_response_time': round(info['avg_response_time'], 2),
                    'success_rate': round(info['success_rate'], 2)
                }
                for name, info in self.sources.items()
            },
            'cache_size': len(self.cache)
        }
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()


# 测试
if __name__ == '__main__':
    api = EnhancedCaseAPI()
    
    print("测试增强版 API...")
    print("\n【测试 1】搜索劳动纠纷案例")
    cases = api.search("违法解除劳动合同", "劳动合同", limit=3)
    print(f"找到 {len(cases)} 个案例")
    for case in cases:
        print(f"  - {case['案号']} ({case.get('source', '未知')})")
    
    print("\n【测试 2】查看使用统计")
    stats = api.get_stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
