#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外部案例数据 API 集成 v2.0
支持多个平台的案例数据获取：
1. OpenLaw - 主要数据源（免费）
2. 聚合数据 - 备用数据源（付费）
3. 无讼 - 备用数据源
"""

import requests
import json
import time
from typing import List, Dict, Optional
from datetime import datetime


class OpenLawAPI:
    """OpenLaw 案例 API 客户端"""
    
    def __init__(self, api_key: str = None):
        """
        初始化 OpenLaw API
        
        Args:
            api_key: API Key（可选，免费版不需要）
        """
        self.api_key = api_key
        self.base_url = "http://openlaw.cn/api"
        self.search_url = "http://openlaw.cn/search"
        self.timeout = 10
        
        # 免费额度：100 次/天
        self.daily_limit = 100
        self.used_today = 0
        self.last_reset = datetime.now().date()
    
    def search_cases(self, keyword: str, page: int = 1, page_size: int = 10) -> Dict:
        """
        搜索案例
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索结果字典
        """
        # 检查日期，重置计数
        today = datetime.now().date()
        if today > self.last_reset:
            self.used_today = 0
            self.last_reset = today
        
        # 检查限额
        if self.used_today >= self.daily_limit:
            return {
                'success': False,
                'error': '超出每日免费限额（100 次/天）',
                'data': []
            }
        
        try:
            # 构建搜索 URL
            params = {
                'keyword': keyword,
                'page': page,
                'pageSize': page_size
            }
            
            if self.api_key:
                params['apiKey'] = self.api_key
            
            # 发送请求（使用网页搜索，因为 OpenLaw API 文档不完善）
            # 实际使用时需要查看最新 API 文档
            response = requests.get(
                self.search_url,
                params=params,
                timeout=self.timeout
            )
            
            self.used_today += 1
            
            if response.status_code == 200:
                # 解析 HTML 或使用 API 响应
                # 注意：这里需要根据实际 API 调整
                return {
                    'success': True,
                    'data': self._parse_search_result(response.text),
                    'total': 0,
                    'page': page,
                    'pageSize': page_size
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'data': []
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': []
            }
    
    def _parse_search_result(self, html: str) -> List[Dict]:
        """
        解析搜索结果
        
        注意：这需要根据实际网页结构调整
        """
        # TODO: 实现 HTML 解析
        # 使用 BeautifulSoup 或 lxml
        cases = []
        
        # 示例数据结构
        # cases.append({
        #     '案号': '(2023) 京 01 民终 1234 号',
        #     '法院': '北京市第一中级人民法院',
        #     '日期': '2023-05-10',
        #     '案由': '民间借贷纠纷',
        #     '争议焦点': '...',
        #     '裁判要旨': '...',
        #     '判决结果': '...',
        #     'url': 'http://openlaw.cn/...'
        # })
        
        return cases
    
    def get_case_detail(self, case_id: str) -> Dict:
        """
        获取案例详情
        
        Args:
            case_id: 案例 ID
            
        Returns:
            案例详情
        """
        url = f"{self.base_url}/case/{case_id}"
        
        try:
            response = requests.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json()
                }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'data': None
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': None
            }


class JuheAPI:
    """聚合数据法律 API 客户端"""
    
    def __init__(self, api_key: str):
        """
        初始化聚合数据 API
        
        Args:
            api_key: API Key（需要购买）
        """
        self.api_key = api_key
        self.base_url = "https://judge-api.juhe.cn/law"
        self.timeout = 10
    
    def search_cases(self, keyword: str, page: int = 1, page_size: int = 10) -> Dict:
        """
        搜索案例
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索结果
        """
        params = {
            'key': self.api_key,
            'keyword': keyword,
            'page': page,
            'pagesize': page_size
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/index",
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('error_code') == 0:
                    return {
                        'success': True,
                        'data': result.get('result', []),
                        'total': result.get('total', 0)
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('reason', '未知错误'),
                        'data': []
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}',
                    'data': []
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'data': []
            }


class CaseAPIManager:
    """案例 API 管理器 - 统一管理多个数据源"""
    
    def __init__(self, config: Dict = None):
        """
        初始化 API 管理器
        
        Args:
            config: 配置字典
                {
                    'openlaw_api_key': 'xxx',  # 可选
                    'juhe_api_key': 'xxx',     # 可选
                    'use_cache': True,         # 是否使用缓存
                    'cache_ttl': 3600,         # 缓存过期时间（秒）
                    'priority': 'openlaw'      # 优先使用的数据源
                }
        """
        self.config = config or {}
        
        # 初始化各 API 客户端
        self.openlaw = OpenLawAPI(self.config.get('openlaw_api_key'))
        
        juhe_key = self.config.get('juhe_api_key')
        self.juhe = JuheAPI(juhe_key) if juhe_key else None
        
        # 缓存（简单实现，生产环境建议用 Redis）
        self.use_cache = self.config.get('use_cache', True)
        self.cache_ttl = self.config.get('cache_ttl', 3600)
        self.cache = {}  # {key: {'data': data, 'time': timestamp}}
    
    def search(self, keyword: str, dispute_type: str = None, limit: int = 5) -> List[Dict]:
        """
        智能搜索案例
        
        Args:
            keyword: 搜索关键词
            dispute_type: 纠纷类型（用于优化搜索）
            limit: 返回数量限制
            
        Returns:
            案例列表
        """
        # 检查缓存
        cache_key = f"{keyword}:{dispute_type}:{limit}"
        if self.use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            if time.time() - cached['time'] < self.cache_ttl:
                return cached['data']
        
        # 按优先级尝试各数据源
        results = []
        
        # 1. 优先使用 OpenLaw（免费）
        if self.config.get('priority', 'openlaw') == 'openlaw':
            results = self._try_openlaw(keyword, limit)
        
        # 2. 如果 OpenLaw 失败，尝试聚合数据
        if not results and self.juhe:
            results = self._try_juhe(keyword, limit)
        
        # 3. 如果还是没结果，使用内置案例库补充
        if not results:
            # 返回空列表，由上层处理
            pass
        
        # 缓存结果
        if self.use_cache and results:
            self.cache[cache_key] = {
                'data': results,
                'time': time.time()
            }
        
        return results
    
    def _try_openlaw(self, keyword: str, limit: int) -> List[Dict]:
        """尝试 OpenLaw API"""
        result = self.openlaw.search_cases(keyword, page=1, page_size=limit)
        
        if result.get('success'):
            return result.get('data', [])
        else:
            print(f"OpenLaw API 失败：{result.get('error')}")
            return []
    
    def _try_juhe(self, keyword: str, limit: int) -> List[Dict]:
        """尝试聚合数据 API"""
        if not self.juhe:
            return []
        
        result = self.juhe.search_cases(keyword, page=1, page_size=limit)
        
        if result.get('success'):
            return result.get('data', [])
        else:
            print(f"聚合数据 API 失败：{result.get('error')}")
            return []
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        """获取使用统计"""
        return {
            'openlaw_used_today': self.openlaw.used_today,
            'openlaw_limit': self.openlaw.daily_limit,
            'cache_size': len(self.cache),
            'juhe_available': self.juhe is not None
        }


# 测试
if __name__ == '__main__':
    # 示例：使用 API 管理器
    config = {
        'openlaw_api_key': None,  # 免费版不需要
        'juhe_api_key': None,     # 需要购买
        'use_cache': True,
        'cache_ttl': 3600,
        'priority': 'openlaw'
    }
    
    manager = CaseAPIManager(config)
    
    # 测试搜索
    print("测试搜索：违法解除劳动合同")
    cases = manager.search("违法解除劳动合同", limit=3)
    
    print(f"找到 {len(cases)} 个案例")
    for case in cases:
        print(f"- {case.get('案号', 'N/A')}")
    
    # 显示统计
    stats = manager.get_stats()
    print(f"\n使用统计：{stats}")
