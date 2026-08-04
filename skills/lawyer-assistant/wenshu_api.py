#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国裁判文书网数据接入尝试 v2.1
由于裁判文书网无官方 API 且有反爬机制，实现多种方案尝试

方案优先级：
1. 官方 API（如果存在）
2. 第三方封装 API
3. 简化版爬虫（仅限公开数据）
4. 平替方案（其他平台）
"""

import requests
import json
import re
from typing import List, Dict, Optional
from datetime import datetime
import time


class WenShuAPI:
    """
    裁判文书网数据接入
    
    注意事项：
    1. 裁判文书网无官方 API
    2. 有反爬虫机制（验证码、IP 限制）
    3. 需要登录才能查看全文
    4. 本模块仅尝试获取公开摘要信息
    """
    
    def __init__(self):
        self.base_url = "https://wenshu.court.gov.cn"
        self.search_url = "https://wenshu.court.gov.cn/website/wenshu/1/1/2/S201.html"
        self.timeout = 15
        
        # Session 管理
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 状态
        self.logged_in = False
        self.last_request = 0
        self.request_count = 0
    
    def search_cases(self, keyword: str, page: int = 1, page_size: int = 10) -> Dict:
        """
        搜索裁判文书
        
        注意：由于反爬机制，这个方法可能不稳定
        """
        # 频率控制
        now = time.time()
        if now - self.last_request < 2:  # 至少间隔 2 秒
            time.sleep(2 - (now - self.last_request))
        self.last_request = time.time()
        self.request_count += 1
        
        try:
            # 尝试访问搜索页面
            params = {
                'searchCondition': keyword,
                'page': page,
                'pageSize': page_size
            }
            
            response = self.session.get(
                self.search_url,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # 检查是否被拦截（验证码、登录等）
                if self._is_blocked(response.text):
                    return {
                        'success': False,
                        'error': '访问被拦截（可能需要验证码或登录）',
                        'data': [],
                        'suggestion': '建议使用平替方案（OpenLaw 等）'
                    }
                
                # 解析结果
                cases = self._parse_search_result(response.text)
                
                return {
                    'success': True,
                    'data': cases,
                    'total': len(cases),
                    'page': page
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
                'error': f'请求失败：{str(e)}',
                'data': [],
                'suggestion': '建议使用平替方案'
            }
    
    def _is_blocked(self, html: str) -> bool:
        """检查是否被拦截"""
        # 检查验证码
        if '验证码' in html or 'slider' in html.lower():
            return True
        
        # 检查登录提示
        if '登录' in html and '查看' in html:
            return True
        
        # 检查 IP 限制
        if 'IP' in html and '限制' in html:
            return True
        
        return False
    
    def _parse_search_result(self, html: str) -> List[Dict]:
        """
        解析搜索结果
        
        注意：这需要根据实际网页结构调整
        """
        cases = []
        
        # 尝试提取案例信息
        # 由于裁判文书网使用大量 JS，这里只能尝试提取部分信息
        
        # 示例正则（实际需要根据页面结构调整）
        pattern = r'文书标题[^>]*>([^<]+)'
        matches = re.findall(pattern, html)
        
        for match in matches[:10]:  # 最多 10 条
            cases.append({
                '案号': '未知',
                '标题': match.strip(),
                '法院': '未知',
                '日期': '未知',
                '来源': '裁判文书网',
                'url': 'https://wenshu.court.gov.cn/...'
            })
        
        return cases
    
    def get_case_detail(self, case_id: str) -> Dict:
        """
        获取文书详情
        
        需要登录才能查看全文
        """
        return {
            'success': False,
            'error': '查看文书详情需要登录',
            'data': None
        }
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            'logged_in': self.logged_in,
            'request_count': self.request_count,
            'last_request': datetime.fromtimestamp(self.last_request).strftime('%Y-%m-%d %H:%M:%S')
        }


class WenShuAlternative:
    """
    裁判文书网平替方案
    
    当裁判文书网无法访问时，使用以下平替：
    1. 中国法院网
    2. 各省市高级人民法院官网
    3. OpenLaw（已集成）
    4. 无讼
    """
    
    def __init__(self):
        self.sources = [
            {
                'name': '中国法院网',
                'url': 'https://www.chinacourt.org',
                'search_url': 'https://www.chinacourt.org/search.shtml',
                'available': True
            },
            {
                'name': '北京法院网',
                'url': 'https://bjgy.bjcourt.gov.cn',
                'available': True
            },
            {
                'name': '上海法院网',
                'url': 'https://hshfy.shfy.sh.cn',
                'available': True
            },
            {
                'name': 'OpenLaw',
                'url': 'http://openlaw.cn',
                'available': True,
                'has_api': True
            },
            {
                'name': '无讼',
                'url': 'https://www.itslaw.com',
                'available': True,
                'has_api': True
            }
        ]
    
    def search(self, keyword: str, source_index: int = 3) -> Dict:
        """
        搜索案例
        
        Args:
            keyword: 搜索关键词
            source_index: 数据源索引（默认使用 OpenLaw）
        """
        if source_index >= len(self.sources):
            return {
                'success': False,
                'error': '无效的数据源',
                'data': []
            }
        
        source = self.sources[source_index]
        
        # 如果有 API，使用 API
        if source.get('has_api'):
            if source['name'] == 'OpenLaw':
                # 使用已集成的 OpenLaw API
                from external_api import OpenLawAPI
                api = OpenLawAPI()
                return api.search_cases(keyword)
            elif source['name'] == '无讼':
                # TODO: 实现无讼 API
                return {
                    'success': False,
                    'error': '无讼 API 待实现',
                    'data': []
                }
        
        # 否则尝试网页搜索
        return self._web_search(keyword, source)
    
    def _web_search(self, keyword: str, source: Dict) -> Dict:
        """网页搜索（简化版）"""
        try:
            response = requests.get(
                source['search_url'],
                params={'keyword': keyword},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': [],  # 需要解析 HTML
                    'source': source['name']
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
    
    def get_available_sources(self) -> List[Dict]:
        """获取可用的数据源列表"""
        return self.sources


def test_wenshu_access():
    """测试裁判文书网接入"""
    print("=" * 60)
    print("裁判文书网数据接入测试")
    print("=" * 60)
    
    # 测试 1：直接访问
    print("\n【测试 1】尝试访问裁判文书网...")
    wen_shu = WenShuAPI()
    
    try:
        response = requests.get(wen_shu.base_url, timeout=10)
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            print("✅ 网站可访问")
            
            # 检查是否需要登录
            if '登录' in response.text:
                print("⚠️  需要登录才能查看完整内容")
            else:
                print("✅ 无需登录可访问部分内容")
        else:
            print(f"❌ 访问失败：HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ 访问异常：{e}")
    
    # 测试 2：尝试搜索
    print("\n【测试 2】尝试搜索案例...")
    result = wen_shu.search_cases("劳动争议", page=1, page_size=5)
    
    if result.get('success'):
        print(f"✅ 搜索成功，找到 {result.get('total', 0)} 个案例")
        for case in result.get('data', [])[:3]:
            print(f"  - {case.get('标题', 'N/A')}")
    else:
        print(f"❌ 搜索失败：{result.get('error', '未知错误')}")
        if result.get('suggestion'):
            print(f"💡 建议：{result.get('suggestion')}")
    
    # 测试 3：平替方案
    print("\n【测试 3】测试平替方案...")
    alt = WenShuAlternative()
    
    sources = alt.get_available_sources()
    print("可用数据源：")
    for i, source in enumerate(sources):
        api_tag = " (有 API)" if source.get('has_api') else ""
        print(f"  {i+1}. {source['name']}{api_tag}")
    
    # 测试 4：使用 OpenLaw 平替
    print("\n【测试 4】使用 OpenLaw 平替搜索...")
    result = alt.search("违法解除劳动合同", source_index=3)  # OpenLaw
    
    if result.get('success'):
        print(f"✅ OpenLaw 搜索成功")
    else:
        print(f"⚠️  OpenLaw 结果：{result.get('error', '未知')}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_wenshu_access()
