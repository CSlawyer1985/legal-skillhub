#!/usr/bin/env python3
"""
法眼 - 法规检索工具
用法: python3 regulation_search.py <关键词>
功能: 通过WebSearch API搜索国家法律法规数据库
"""

import sys
import json
from datetime import datetime


def search_regulation(keyword: str) -> dict:
    """
    搜索法规，返回:
    {
        "title": "法律名称",
        "status": "现行有效" | "已修订" | "已废止",
        "articles": [{"num": "第X条", "text": "条文内容"}],
        "source": "来源URL",
        "search_timestamp": "检索时间"
    }
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n🔍 正在检索「{keyword}」相关法规...")
    print(f"⏰ 检索时间: {timestamp}\n")

    # 检索建议
    suggestions = {
        "primary": {
            "name": "国家法律法规数据库",
            "url": "https://flk.npc.gov.cn",
            "description": "全国人大官方数据库，收录宪法、法律、行政法规、司法解释等"
        },
        "secondary": [
            {
                "name": "中国人大网法律库",
                "url": "http://www.npc.gov.cn",
                "description": "全国人大官网，查询最新立法动态"
            },
            {
                "name": "中国裁判文书网",
                "url": "https://wenshu.court.gov.cn",
                "description": "最高人民法院裁判文书公开平台，查询相关案由判例"
            },
            {
                "name": "司法部法律法规数据库",
                "url": "https://www.moj.gov.cn",
                "description": "司法部官方网站，查询行政法规和部门规章"
            }
        ],
        "search_keywords": [
            f"{keyword}",
            f"{keyword} 法条",
            f"{keyword} 司法解释",
            f"{keyword} 最新版本",
            f"{keyword} 修订",
            f"{keyword} 废止"
        ]
    }

    print("📋 建议检索渠道:\n")
    print(f"  优先渠道: {suggestions['primary']['name']}")
    print(f"  URL: {suggestions['primary']['url']}")
    print(f"  说明: {suggestions['primary']['description']}\n")

    print("  补充渠道:")
    for i, source in enumerate(suggestions['secondary'], 1):
        print(f"  {i}. {source['name']}")
        print(f"     URL: {source['url']}")
        print(f"     说明: {source['description']}\n")

    print("📝 建议搜索关键词:")
    for i, kw in enumerate(suggestions['search_keywords'], 1):
        print(f"  {i}. {kw}")

    print("\n" + "=" * 60)
    print("⚠️  注: 本工具提供检索路径指引，实际法规检索需通过WebSearch工具")
    print("    联网搜索上述数据库以获取最新法规原文和时效状态。")
    print("=" * 60)

    result = {
        "status": "needs_websearch",
        "keyword": keyword,
        "timestamp": timestamp,
        "suggestions": suggestions
    }

    return result


def search_by_case(keyword: str, case_type: str) -> dict:
    """
    按案由类型检索法规
    case_type: "contract" | "tort" | "property" | "family" | "labor" | "company"
    """
    case_type_map = {
        "contract": "合同纠纷",
        "tort": "侵权责任",
        "property": "物权纠纷",
        "family": "婚姻家庭继承",
        "labor": "劳动争议",
        "company": "公司/证券/保险"
    }

    type_name = case_type_map.get(case_type, case_type)

    print(f"\n🔍 正在检索「{keyword}」在【{type_name}】领域的相关法规...\n")

    # 根据案由类型提示专项搜索
    print(f"📌 在【{type_name}】领域，建议重点检索：")
    print(f"  1. {type_name}相关专门法律法规")
    print(f"  2. 最高人民法院关于{type_name}的司法解释")
    print(f"  3. {type_name}相关指导案例")

    return {
        "status": "needs_websearch",
        "keyword": keyword,
        "case_type": case_type,
        "type_name": type_name
    }


def list_available_resources():
    """列出可用的法规检索资源"""
    print("\n📚 法眼法规检索资源清单\n")
    print("=" * 60)

    resources = [
        {
            "category": "法律（全国人大及常委会制定）",
            "sources": [
                "国家法律法规数据库 (flk.npc.gov.cn)",
                "中国人大网 (www.npc.gov.cn)"
            ]
        },
        {
            "category": "行政法规（国务院制定）",
            "sources": [
                "国家法律法规数据库",
                "中国政府网 (www.gov.cn)"
            ]
        },
        {
            "category": "司法解释（最高人民法院/最高人民检察院）",
            "sources": [
                "最高人民法院网 (www.court.gov.cn)",
                "最高人民检察院网 (www.spp.gov.cn)"
            ]
        },
        {
            "category": "部门规章",
            "sources": [
                "各主管部门官方网站",
                "司法部法律法规数据库"
            ]
        },
        {
            "category": "地方性法规",
            "sources": [
                "各省/市人大网站",
                "国家法律法规数据库"
            ]
        }
    ]

    for item in resources:
        print(f"\n📁 {item['category']}:")
        for source in item['sources']:
            print(f"   - {source}")

    print("\n" + "=" * 60)
    print("提示: 使用方法: python3 regulation_search.py <关键词>")
    print("      python3 regulation_search.py --by-case <关键词> <案由类型>")
    print("      python3 regulation_search.py --resources")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 regulation_search.py <关键词>")
        print("  python3 regulation_search.py --by-case <关键词> <案由类型>")
        print("  python3 regulation_search.py --resources")
        print("\n示例:")
        print("  python3 regulation_search.py 民间借贷")
        print("  python3 regulation_search.py --by-case 劳动合同 劳动争议")
        print("  python3 regulation_search.py --resources")
        sys.exit(0)

    if sys.argv[1] == "--resources":
        list_available_resources()
        sys.exit(0)

    if sys.argv[1] == "--by-case":
        if len(sys.argv) < 4:
            print("用法: python3 regulation_search.py --by-case <关键词> <案由类型>")
            print("案由类型: contract, tort, property, family, labor, company")
            sys.exit(1)
        keyword = sys.argv[2]
        case_type = sys.argv[3]
        result = search_by_case(keyword, case_type)
    else:
        keyword = sys.argv[1]
        result = search_regulation(keyword)

    print(f"\n📤 返回结果:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
