#!/usr/bin/env python3
"""
专利检索技能 - 命令行入口
"""

import sys
import os
import json
import argparse
from typing import Dict, List, Optional

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from patent_api import PatentAPI
    from patent_skill import PatentSkill
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("💡 请确保 patent_api.py 和 patent_skill.py 文件存在")
    sys.exit(1)

def handle_analysis(skill, args) -> str:
    """处理统计分析命令"""
    if not args.query:
        return "❌ 请输入查询条件"
    
    try:
        result = skill.api.get_analysis(
            query=args.query,
            dimension=args.dimension,
            data_scope=args.scope or 'cn'
        )
        
        if not result.get('success'):
            code = result.get('code') or result.get('errorCode', '')
            msg = result.get('message') or result.get('msg', '未知错误')
            return f"❌ 统计分析失败: {msg}" + (f" (code={code})" if code else "")

        items = skill.api.format_analysis(result)

        output = []
        output.append(f"📊 统计分析 - {args.dimension}")
        output.append(f"🔍 查询条件: {args.query}")
        output.append("=" * 50)

        if not items:
            output.append("无分析数据")
            return "\n".join(output)

        output.append(f"📈 分布情况 (前{args.limit}项):")
        for i, item in enumerate(items[:args.limit], 1):
            key = item.get('key', '未知')
            count = item.get('count', 0)
            output.append(f"{i:2d}. {key}: {count:,}件")
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ 统计分析失败: {e}"

def handle_help(skill, args) -> str:
    """处理帮助命令"""
    help_text = """
🏢 专利检索技能 - 使用指南
==================================================

🔍 基本命令:
  patent search <查询条件>      - 搜索专利
  patent detail <专利ID>       - 查看专利详情
  patent claims <专利ID>       - 获取权利要求
  patent description <专利ID>  - 获取说明书
  patent legal <专利ID>        - 查看法律信息

📊 分析命令:
  patent analysis <查询条件> --dimension <维度>  - 统计分析
  patent company <企业名称>                     - 企业画像

📚 扩展命令:
  patent copyright <查询条件>    - 搜索著作权
  patent trademark <查询条件>    - 搜索商标
  patent citing <专利ID>        - 引用分析
  patent similar <专利ID>       - 相似专利

🛠️ 常用参数:
  --page, -p <页码>            - 指定页码
  --page-size, -ps <条数>      - 每页显示条数
  --scope, -s <cn/all>         - 数据范围
  --sort, -st <relation/date>  - 排序方式
  --details, -d               - 显示详细信息

📖 示例:
  patent search "锂电池" --page-size 5 --details
  patent detail CN112968234A
  patent analysis "锂电池" --dimension applicant
  patent company "比亚迪股份有限公司"

🔧 配置说明:
  1. 申请API Token: https://www.9235.net/api/open
  2. 配置Token:
     openclaw config set skills.entries.patent-search.apiKey '您的Token'
  3. 重启服务: openclaw gateway restart

📞 支持:
  • 文档: https://docs.openclaw.ai
  • 社区: https://discord.com/invite/clawd
  • GitHub: https://github.com/openclaw/openclaw
    """
    return help_text

def create_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='专利检索技能 - 基于9235.net API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s search "锂电池" --page-size 5
  %(prog)s detail CN112968234A
  %(prog)s analysis "锂电池" --dimension applicant
  %(prog)s company "比亚迪股份有限公司"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索专利')
    search_parser.add_argument('query', help='检索式')
    search_parser.add_argument('--page', '-p', type=int, default=1, help='页码 (默认: 1)')
    search_parser.add_argument('--page-size', '-ps', type=int, default=10, help='每页条数 (默认: 10)')
    search_parser.add_argument(
        '--scope', '-s',
        choices=['cn', 'us', 'jp', 'kr', 'tw', 'wo', 'ep', 'all'],
        default='cn',
        help='数据范围：cn 中国；all/us/jp/kr/tw/wo/ep 全球/各国（Token 等级≥7）',
    )
    search_parser.add_argument('--sort', '-st', choices=['relation', 'date'], default='relation', help='排序方式 (默认: relation)')
    search_parser.add_argument('--details', '-d', action='store_true', help='显示详细信息')
    
    # 专利详情命令
    detail_parser = subparsers.add_parser('detail', help='查看专利详情')
    detail_parser.add_argument('patent_id', help='专利ID')
    
    # 权利要求命令
    claims_parser = subparsers.add_parser('claims', help='获取专利权利要求')
    claims_parser.add_argument('patent_id', help='专利ID')
    
    # 说明书命令
    desc_parser = subparsers.add_parser('description', help='获取专利说明书')
    desc_parser.add_argument('patent_id', help='专利ID')
    
    # 法律信息命令
    legal_parser = subparsers.add_parser('legal', help='查看专利法律信息')
    legal_parser.add_argument('patent_id', help='专利ID')
    
    # 引用分析命令
    citing_parser = subparsers.add_parser('citing', help='专利引用分析')
    citing_parser.add_argument('patent_id', help='专利ID')
    
    # 相似专利命令
    similar_parser = subparsers.add_parser('similar', help='查找相似专利')
    similar_parser.add_argument('patent_id', help='专利ID')
    
    # 统计分析命令
    analysis_parser = subparsers.add_parser('analysis', help='统计分析')
    analysis_parser.add_argument('query', help='检索式')
    analysis_parser.add_argument('--dimension', '-d', required=True, 
                                choices=['applicant', 'ipc', 'applicationYear', 'legalStatus'], 
                                help='分析维度')
    analysis_parser.add_argument(
        '--scope', '-s',
        choices=['cn', 'us', 'jp', 'kr', 'tw', 'wo', 'ep', 'all'],
        default='cn',
        help='数据范围（全球库需 Token 等级≥7）',
    )
    analysis_parser.add_argument('--limit', '-l', type=int, default=20, help='显示条数 (默认: 20)')
    
    # 企业画像命令
    company_parser = subparsers.add_parser('company', help='企业专利画像')
    company_parser.add_argument('company_name', help='企业名称')
    
    # 著作权搜索命令
    copyright_parser = subparsers.add_parser('copyright', help='搜索著作权')
    copyright_parser.add_argument('query', help='检索式')
    copyright_parser.add_argument('--type', '-t', choices=['software', 'works'], default='software', help='著作权类型 (默认: software)')
    copyright_parser.add_argument('--field', '-f', help='查询字段')
    copyright_parser.add_argument('--page', '-p', type=int, default=1, help='页码 (默认: 1)')
    copyright_parser.add_argument('--page-size', '-ps', type=int, default=10, help='每页条数 (默认: 10)')
    
    # 商标搜索命令
    trademark_parser = subparsers.add_parser('trademark', help='搜索商标')
    trademark_parser.add_argument('query', help='检索式或商标ID')
    trademark_parser.add_argument('--detail', '-d', action='store_true', help='查看商标详情')
    trademark_parser.add_argument('--trademark-id', '-id', help='商标ID (用于详情查看)')
    trademark_parser.add_argument('--page', '-p', type=int, default=1, help='页码 (默认: 1)')
    trademark_parser.add_argument('--page-size', '-ps', type=int, default=10, help='每页条数 (默认: 10)')
    trademark_parser.add_argument('--sort', '-st', help='排序字段')
    
    # 帮助命令
    help_parser = subparsers.add_parser('help', help='显示帮助信息')
    
    return parser

def main():
    """主函数"""
    parser = create_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
    
    args = parser.parse_args()
    
    try:
        # 初始化API客户端
        api = PatentAPI()
        
        # 初始化技能
        skill = PatentSkill(api)
        
        # 动态添加处理函数
        skill.handle_analysis = lambda a: handle_analysis(skill, a)
        skill.handle_help = lambda a: handle_help(skill, a)
        
        # 执行命令
        if args.command in skill.commands:
            handler = skill.commands[args.command]
            result = handler(args)
            print(result)
        else:
            parser.print_help()
            
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
        print("\n💡 请配置API Token:")
        print("   方法1: export PATENT_API_TOKEN='您的Token'")
        print("   方法2: 创建config.json文件")
        print("   方法3: openclaw config set skills.entries.patent-search.apiKey '您的Token'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()