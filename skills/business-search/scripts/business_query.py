#!/usr/bin/env python3
"""
企业信息查询脚本
Business Information Query Script

使用百度搜索收集企业相关信息

用法:
    python business_query.py <公司名称> [--type TYPE] [--count COUNT]

参数:
    公司名称    要查询的企业名称（必填）
    --type     查询类型：basic(默认)|shareholder|risk|finance|news|contact|all
    --count    返回结果数量，默认10条
"""

import json
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Optional


class BusinessSearch:
    """商业信息查询类"""

    # 预设的搜索模板
    SEARCH_TEMPLATES = {
        "basic": "{name} 工商信息 注册资本 成立时间 经营状态",
        "shareholder": "{name} 股东 法人代表 大股东 持股比例",
        "risk": "{name} 失信 被执行人 诉讼 行政处罚 经营异常",
        "finance": "{name} 融资 IPO 上市 投资 估值",
        "news": "{name} 最新 新闻 动态 媒体报道",
        "contact": "{name} 联系方式 地址 电话 官网",
    }

    def __init__(self):
        self.search_script = "~/.workbuddy/skills/baidu-search/scripts/search.py"

    def search(self, query: str, count: int = 10) -> List[Dict]:
        """执行百度搜索"""
        cmd = [
            sys.executable,
            self.search_script.replace("~", "C:/Users/98148"),
            json.dumps({"query": query, "count": count})
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                print(f"搜索出错: {result.stderr}", file=sys.stderr)
                return []

        except subprocess.TimeoutExpired:
            print("搜索超时", file=sys.stderr)
            return []
        except Exception as e:
            print(f"搜索异常: {e}", file=sys.stderr)
            return []

    def query_company(
        self,
        company_name: str,
        query_type: str = "all",
        count: int = 10
    ) -> Dict[str, List]:
        """查询企业信息"""
        results = {}

        if query_type == "all":
            # 查询所有类型
            for qtype, template in self.SEARCH_TEMPLATES.items():
                query = template.format(name=company_name)
                print(f"[{qtype}] 查询: {query}")
                results[qtype] = self.search(query, count)
        else:
            # 查询指定类型
            template = self.SEARCH_TEMPLATES.get(query_type, self.SEARCH_TEMPLATES["basic"])
            query = template.format(name=company_name)
            results[query_type] = self.search(query, count)

        return results

    def format_report(self, company_name: str, results: Dict) -> str:
        """生成结构化报告"""
        report = []
        report.append("=" * 60)
        report.append(f"企业信息查询报告")
        report.append("=" * 60)
        report.append(f"查询对象: {company_name}")
        report.append(f"查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        type_names = {
            "basic": "【工商基本信息】",
            "shareholder": "【股东与法人信息】",
            "risk": "【经营风险信息】",
            "finance": "【融资上市信息】",
            "news": "【新闻动态】",
            "contact": "【联系方式】",
        }

        for qtype, data in results.items():
            report.append("")
            report.append(type_names.get(qtype, qtype))
            report.append("-" * 40)

            if not data:
                report.append("未找到相关信息")
                continue

            for item in data[:10]:
                if isinstance(item, dict):
                    title = item.get("title", "")
                    url = item.get("url", "")
                    snippet = item.get("snippet", "")
                    report.append(f"• {title}")
                    if snippet:
                        report.append(f"  {snippet[:100]}...")
                    report.append(f"  来源: {url}")
                else:
                    report.append(f"• {item}")
            report.append("")

        report.append("=" * 60)
        report.append("提示: 以上信息仅供参考，具体信息请以官方渠道为准")
        report.append("=" * 60)

        return "\n".join(report)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    company_name = sys.argv[1]

    # 解析参数
    query_type = "all"
    count = 10

    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--type" and i + 1 < len(sys.argv):
            query_type = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--count" and i + 1 < len(sys.argv):
            count = int(sys.argv[i + 1])
            i += 2
        else:
            i += 1

    # 执行查询
    search = BusinessSearch()
    results = search.query_company(company_name, query_type, count)

    # 生成报告
    report = search.format_report(company_name, results)
    print(report)


if __name__ == "__main__":
    main()
