#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenLaw 案例数据抓取与验证 v2.5
从 OpenLaw 网站获取真实案例进行验证测试

注意：
1. 遵守网站 robots.txt 和使用条款
2. 控制请求频率
3. 仅用于测试验证
"""

import requests
import json
import time
import re
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


class OpenLawScraper:
    """OpenLaw 案例抓取器"""
    
    def __init__(self, output_dir: str = None):
        """
        初始化
        
        Args:
            output_dir: 输出目录
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent / "test_cases" / "openlaw"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "http://openlaw.cn"
        self.search_url = "http://openlaw.cn/search"
        self.timeout = 15
        
        # Session 管理
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        # 频率控制
        self.last_request = 0
        self.request_delay = 2  # 秒
    
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
        # 频率控制
        now = time.time()
        if now - self.last_request < self.request_delay:
            time.sleep(self.request_delay - (now - self.last_request))
        self.last_request = time.time()
        
        try:
            params = {
                'keyword': keyword,
                'page': page,
                'pageSize': page_size
            }
            
            response = self.session.get(
                self.search_url,
                params=params,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                # 解析 HTML
                cases = self._parse_html(response.text)
                
                return {
                    'success': True,
                    'data': cases,
                    'total': len(cases),
                    'page': page,
                    'keyword': keyword
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
    
    def _parse_html(self, html: str) -> List[Dict]:
        """
        解析 HTML 提取案例信息
        
        注意：这需要根据实际网页结构调整
        """
        cases = []
        
        # 尝试提取案例信息
        # 使用正则表达式提取关键信息
        
        # 示例：提取案号
        case_no_pattern = r'\((\d{4})\)\s*([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]\d{2,4})\s*(民|刑|行)[^\)]*号'
        
        # 由于 OpenLaw 使用大量 JS，这里返回模拟数据用于测试
        # 实际使用时需要实现真实的 HTML 解析
        
        return cases
    
    def get_mock_cases(self, dispute_type: str, count: int = 100) -> List[Dict]:
        """
        获取模拟案例数据（用于测试）
        
        基于真实案例结构生成模拟数据
        
        Args:
            dispute_type: 纠纷类型
            count: 案例数量
            
        Returns:
            案例列表
        """
        cases = []
        
        # 不同纠纷类型的案例模板
        templates = {
            '劳动合同': [
                {
                    '案号': '(2024) 京 01 民终 XXXX 号',
                    '法院': '北京市第一中级人民法院',
                    '日期': '2024-01-15',
                    '案由': '劳动合同纠纷',
                    '当事人': {
                        '原告': '张某',
                        '被告': 'XX 科技有限公司'
                    },
                    '案情': '公司违法解除劳动合同...',
                    '争议焦点': '违法解除赔偿金',
                    '判决结果': '公司支付赔偿金 XX 万元',
                    '胜诉方': '员工'
                },
                {
                    '案号': '(2024) 沪 02 民终 XXXX 号',
                    '法院': '上海市第二中级人民法院',
                    '日期': '2024-02-20',
                    '案由': '劳动合同纠纷',
                    '当事人': {
                        '原告': '李某',
                        '被告': 'XX 商贸公司'
                    },
                    '案情': '拖欠工资、加班费...',
                    '争议焦点': '加班费计算',
                    '判决结果': '公司支付工资及加班费 XX 万元',
                    '胜诉方': '员工'
                }
            ],
            '消费纠纷': [
                {
                    '案号': '(2024) 京 04 民终 XXXX 号',
                    '法院': '北京市第四中级人民法院',
                    '日期': '2024-03-10',
                    '案由': '网络购物合同纠纷',
                    '当事人': {
                        '原告': '王某',
                        '被告': 'XX 电商平台'
                    },
                    '案情': '购买到假货...',
                    '争议焦点': '三倍赔偿',
                    '判决结果': '商家退一赔三',
                    '胜诉方': '消费者'
                }
            ],
            '离婚纠纷': [
                {
                    '案号': '(2024) 京 03 民终 XXXX 号',
                    '法院': '北京市第三中级人民法院',
                    '日期': '2024-01-25',
                    '案由': '离婚纠纷',
                    '当事人': {
                        '原告': '张某（女）',
                        '被告': '李某（男）'
                    },
                    '案情': '男方出轨...',
                    '争议焦点': '抚养权、财产分割',
                    '判决结果': '准予离婚，女方获得抚养权',
                    '胜诉方': '原告'
                }
            ],
            '借款纠纷': [
                {
                    '案号': '(2024) 粤 03 民终 XXXX 号',
                    '法院': '广东省深圳市中级人民法院',
                    '日期': '2024-02-15',
                    '案由': '民间借贷纠纷',
                    '当事人': {
                        '原告': '赵某',
                        '被告': '钱某'
                    },
                    '案情': '借款 10 万元未还...',
                    '争议焦点': '借贷关系是否成立',
                    '判决结果': '被告归还借款及利息',
                    '胜诉方': '原告'
                }
            ],
            '交通事故': [
                {
                    '案号': '(2024) 京 05 民终 XXXX 号',
                    '法院': '北京市第五中级人民法院',
                    '日期': '2024-03-05',
                    '案由': '机动车交通事故责任纠纷',
                    '当事人': {
                        '原告': '孙某',
                        '被告': '周某、XX 保险公司'
                    },
                    '案情': '车祸受伤...',
                    '争议焦点': '赔偿金额',
                    '判决结果': '保险公司赔偿 XX 万元',
                    '胜诉方': '原告'
                }
            ]
        }
        
        # 生成案例
        base_template = templates.get(dispute_type, templates['劳动合同'])
        
        for i in range(count):
            # 复制模板并添加变化
            template = base_template[i % len(base_template)].copy()
            
            # 添加变化
            template['案号'] = template['案号'].replace('XXXX', f'{1000+i}')
            template['序号'] = i + 1
            template['纠纷类型'] = dispute_type
            template['来源'] = 'OpenLaw（模拟）'
            template['抓取时间'] = datetime.now().isoformat()
            
            cases.append(template)
        
        return cases
    
    def save_cases(self, cases: List[Dict], filename: str = None):
        """保存案例到文件"""
        if filename is None:
            filename = f"openlaw_cases_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def load_cases(self, filename: str) -> List[Dict]:
        """从文件加载案例"""
        filepath = self.output_dir / filename
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)


# 测试
if __name__ == '__main__':
    print("=" * 60)
    print("OpenLaw 案例抓取测试")
    print("=" * 60)
    
    scraper = OpenLawScraper()
    
    # 生成模拟案例
    print("\n【生成模拟案例】")
    for dispute_type in ['劳动合同', '消费纠纷', '离婚纠纷', '借款纠纷', '交通事故']:
        cases = scraper.get_mock_cases(dispute_type, count=20)
        filepath = scraper.save_cases(cases, f"openlaw_{dispute_type}.json")
        print(f"{dispute_type}: {len(cases)} 个案例 -> {filepath}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
