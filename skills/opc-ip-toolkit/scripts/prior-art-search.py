#!/usr/bin/env python3
"""
专利查新检索脚本
Prior Art Search Tool

功能：
1. 调用智慧芽API进行专利检索（如配置了API Key）
2. 引导用户使用免费工具进行初步检索
3. 生成检索报告

使用方法：
    # 有API Key时
    export ZHIYUYA_APP_ID="your_app_id"
    export ZHIHIYA_APP_KEY="your_app_key"
    python prior-art-search.py --keywords "人工智能 语音识别"
    
    # 无API Key时
    python prior-art-search.py --keywords "人工智能 语音识别" --free

作者：OPC知识产权助手
版本：v1.0
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# ============================================================
# 配置区域
# ============================================================

# 免费检索工具URL
FREE_TOOLS = {
    "国家知识产权局": "https://pss-system.cponline.cnipa.gov.cn/",
    "SooPAT": "http://www.soopat.com/",
    "CNIPA.AI": "https://cnipa.ai/",
    "佰腾网": "https://www.baitiangroup.com/",
}

# ============================================================
# API调用（如有API Key）
# ============================================================

class ZhiyuyaPatentSearch:
    """智慧芽专利检索"""
    
    def __init__(self, app_id: str = None, app_key: str = None):
        self.app_id = app_id or os.environ.get('ZHIYUYA_APP_ID')
        self.app_key = app_key or os.environ.get('ZHIYUYA_APP_KEY')
        self.base_url = "https://open.zhihuiya.com/v1"
        
        if not self.app_id or not self.app_key:
            print("⚠️  未配置智慧芽API Key，将使用免费工具引导模式")
            self.available = False
        else:
            self.available = True
    
    def search(self, query: str, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        """
        搜索专利
        
        Args:
            query: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            Dict: 搜索结果
        """
        if not self.available:
            return None
        
        try:
            import requests
            
            url = f"{self.base_url}/patent/search"
            headers = {
                "Content-Type": "application/json",
                "X-App-Id": self.app_id,
                "X-App-Key": self.app_key
            }
            payload = {
                "query": query,
                "page_num": page,
                "page_size": page_size
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"✗ API调用失败：{response.status_code}")
                return None
                
        except ImportError:
            print("✗ 请先安装requests库：pip install requests")
            return None
        except Exception as e:
            print(f"✗ 发生错误：{e}")
            return None
    
    def get_patent_detail(self, patent_number: str) -> Optional[Dict]:
        """
        获取专利详情
        
        Args:
            patent_number: 专利号
            
        Returns:
            Dict: 专利详情
        """
        if not self.available:
            return None
        
        try:
            import requests
            
            url = f"{self.base_url}/patent/detail/{patent_number}"
            headers = {
                "X-App-Id": self.app_id,
                "X-App-Key": self.app_key
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            print(f"✗ 获取详情失败：{e}")
            return None


# ============================================================
# 检索逻辑
# ============================================================

class PatentSearcher:
    """专利检索器"""
    
    def __init__(self):
        self.zhiyuya = ZhiyuyaPatentSearch()
        self.results = []
    
    def parse_keywords(self, keywords: str) -> List[str]:
        """
        解析关键词
        
        Args:
            keywords: 原始关键词字符串
            
        Returns:
            List[str]: 关键词列表
        """
        # 支持多种分隔符
        for sep in [' ', '，', ',', '、', ';', '；']:
            if sep in keywords:
                return [k.strip() for k in keywords.split(sep) if k.strip()]
        return [keywords.strip()]
    
    def build_search_query(self, keywords: List[str], mode: str = 'and') -> str:
        """
        构建检索式
        
        Args:
            keywords: 关键词列表
            mode: 'and' 或 'or'
            
        Returns:
            str: 检索式
        """
        if not keywords:
            return ""
        
        if mode == 'or':
            return f"({' OR '.join(keywords)})"
        else:
            return ' AND '.join(keywords)
    
    def search_with_api(self, query: str) -> List[Dict]:
        """
        使用API搜索
        
        Args:
            query: 检索式
            
        Returns:
            List[Dict]: 搜索结果
        """
        if not self.zhiyuya.available:
            return []
        
        print(f"🔍 正在通过智慧芽API检索：{query}")
        
        result = self.zhiyuya.search(query, page_size=20)
        
        if result and 'data' in result:
            patents = result['data'].get('patents', [])
            print(f"✓ 找到 {len(patents)} 条相关专利\n")
            return patents
        
        return []
    
    def search_free_tools(self, keywords: List[str]) -> Dict:
        """
        生成免费工具使用指南
        
        Args:
            keywords: 关键词列表
            
        Returns:
            Dict: 免费工具使用指南
        """
        query = ' '.join(keywords)
        
        guide = {
            "检索建议": {
                "建议关键词": keywords,
                "检索式示例": self.build_search_query(keywords)
            },
            "免费检索工具": {}
        }
        
        for name, url in FREE_TOOLS.items():
            if name == "国家知识产权局":
                guide["免费检索工具"][name] = {
                    "网址": url,
                    "使用建议": f"进入专利检索页面，使用关键词「{query}」进行检索",
                    "检索技巧": [
                        "使用简单关键词开始",
                        "添加技术领域限定",
                        "查看同族专利了解全球布局"
                    ]
                }
            elif name == "SooPAT":
                guide["免费检索工具"][name] = {
                    "网址": url,
                    "使用建议": f"在搜索框输入「{query}」，选择合适的检索字段",
                    "检索技巧": [
                        "支持中英文混合检索",
                        "可查看专利全文和法律状态"
                    ]
                }
            elif name == "CNIPA.AI":
                guide["免费检索工具"][name] = {
                    "网址": url,
                    "使用建议": f"使用AI辅助理解专利内容，输入「{query}」",
                    "检索技巧": [
                        "AI可帮助理解和分析专利",
                        "适合快速了解技术领域"
                    ]
                }
        
        return guide
    
    def analyze_risk(self, keywords: List[str]) -> Dict:
        """
        分析检索风险
        
        Args:
            keywords: 关键词列表
            
        Returns:
            Dict: 风险分析结果
        """
        return {
            "检索关键词": keywords,
            "检索式": self.build_search_query(keywords),
            "风险评估": {
                "建议": "建议先进行初步检索，了解现有技术情况",
                "检索步骤": [
                    "1. 使用核心关键词检索初步了解技术领域",
                    "2. 扩展同义词、近义词进行补充检索",
                    "3. 关注检索到的相关专利的技术方案",
                    "4. 如发现相同或相近技术，分析差异点",
                    "5. 必要时咨询专业代理人"
                ]
            },
            "预期结果解读": {
                "🟢 低风险": "未发现相同或相近技术，可继续申请",
                "🟡 中风险": "发现部分相近技术，需聚焦差异点",
                "🔴 高风险": "发现相同技术方案，建议重新评估或调整"
            }
        }
    
    def generate_report(self, keywords: List[str], use_api: bool = True) -> str:
        """
        生成检索报告
        
        Args:
            keywords: 关键词列表
            use_api: 是否使用API
            
        Returns:
            str: 检索报告
        """
        query = self.build_search_query(keywords)
        
        report = f"""# 专利查新检索报告

## 检索信息
- **检索日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **检索关键词**: {' | '.join(keywords)}
- **检索式**: {query}

## 检索方式
"""
        
        if use_api and self.zhiyuya.available:
            patents = self.search_with_api(query)
            if patents:
                report += f"### API检索结果（智慧芽）\n"
                report += f"找到 {len(patents)} 条相关专利\n\n"
                
                for i, p in enumerate(patents[:10], 1):
                    report += f"**{i}. {p.get('title', '未知标题')}**\n"
                    report += f"- 专利号：{p.get('patent_number', 'N/A')}\n"
                    report += f"- 申请人：{p.get('applicant', 'N/A')}\n"
                    report += f"- 申请日：{p.get('application_date', 'N/A')}\n"
                    report += f"- 摘要：{p.get('abstract', 'N/A')[:200]}...\n\n"
            else:
                report += "API未返回结果，请尝试免费工具。\n\n"
        else:
            report += "未使用API，将通过以下免费工具引导检索。\n\n"
        
        # 免费工具指南
        free_guide = self.search_free_tools(keywords)
        report += "## 免费检索工具使用指南\n\n"
        for name, info in free_guide["免费检索工具"].items():
            report += f"### {name}\n"
            report += f"- **网址**: {info['网址']}\n"
            report += f"- **使用建议**: {info['使用建议']}\n"
            if '检索技巧' in info:
                report += "- **检索技巧**:\n"
                for tip in info['检索技巧']:
                    report += f"  - {tip}\n"
            report += "\n"
        
        # 风险分析
        risk = self.analyze_risk(keywords)
        report += "## 风险评估与建议\n\n"
        report += f"**检索式**: {risk['检索式']}\n\n"
        report += "### 检索步骤建议\n"
        for step in risk['风险评估']['检索步骤']:
            report += f"{step}\n"
        report += "\n"
        
        report += "### 结果解读\n"
        for level, desc in risk['预期结果解读'].items():
            report += f"- {level}：{desc}\n"
        
        report += """
---

**⚠️  重要提示**：
1. 本报告仅为初步检索结果，不构成专利新颖性/创造性的正式判断
2. 建议在专业代理人的指导下完成完整查新
3. 检索结果需结合具体技术方案分析

*本报告由AI辅助生成*
"""
        
        return report


# ============================================================
# 命令行接口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='专利查新检索工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用API检索
  python prior-art-search.py -k "人工智能 语音识别"
  
  # 纯免费模式
  python prior-art-search.py -k "人工智能 语音识别" --free
  
  # 多关键词OR检索
  python prior-art-search.py -k "人工智能,机器学习,深度学习" --mode or
  
  # 保存报告到文件
  python prior-art-search.py -k "智能水杯" -o report.md
        """
    )
    
    parser.add_argument('-k', '--keywords', type=str, required=True,
                        help='检索关键词，多个关键词用空格或逗号分隔')
    parser.add_argument('-m', '--mode', type=str, choices=['and', 'or'], default='and',
                        help='关键词组合方式：and(默认)或or')
    parser.add_argument('--free', action='store_true',
                        help='强制使用免费工具模式')
    parser.add_argument('-o', '--output', type=str,
                        help='输出报告文件路径')
    parser.add_argument('--api-id', type=str,
                        help='智慧芽API App ID（也可通过环境变量ZHIYUYA_APP_ID设置）')
    parser.add_argument('--api-key', type=str,
                        help='智慧芽API App Key（也可通过环境变量ZHIYUYA_APP_KEY设置）')
    
    args = parser.parse_args()
    
    # 初始化检索器
    if args.api_id and args.api_key:
        os.environ['ZHIYUYA_APP_ID'] = args.api_id
        os.environ['ZHIYUYA_APP_KEY'] = args.api_key
    
    searcher = PatentSearcher()
    
    # 解析关键词
    keywords = searcher.parse_keywords(args.keywords)
    
    print("\n" + "="*60)
    print("🔍 专利查新检索工具 v1.0")
    print("="*60)
    print(f"\n检索关键词: {' | '.join(keywords)}")
    print(f"组合方式: {args.mode.upper()}")
    
    # 检查API可用性
    if not args.free and searcher.zhiyuya.available:
        print("\n✅ 已配置智慧芽API，将优先使用API检索")
    else:
        print("\n📌 使用免费工具模式")
    
    # 生成报告
    use_api = not args.free and searcher.zhiyuya.available
    report = searcher.generate_report(keywords, use_api)
    
    # 输出报告
    print("\n" + "-"*60)
    print("检索报告预览：")
    print("-"*60)
    print(report)
    
    # 保存文件
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n✓ 报告已保存到: {args.output}")
        except Exception as e:
            print(f"\n✗ 保存失败: {e}")
    else:
        # 默认保存
        output_dir = "./output"
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"patent_search_report_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\n✓ 报告已保存到: {filepath}")
        except Exception as e:
            print(f"\n✗ 保存失败: {e}")
    
    print("\n" + "="*60)
    print("💡 建议下一步：")
    print("   1. 根据报告中的链接访问免费检索工具")
    print("   2. 根据实际情况分析技术方案的新颖性")
    print("   3. 必要时咨询专业专利代理人")
    print("="*60)


if __name__ == "__main__":
    main()
