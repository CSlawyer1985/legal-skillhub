"""
Tavily 检索封装 — 用于法律研究中的二手文献（Secondary Sources）检索

二手文献类型：
- 头部律所文章（金杜、君合、方达、中伦、通商、环球、海问、竞天公诚、植德、汉坤等）
- 政府网站政策解读、答记者问
- 法学院校研究文章
- 法学期刊、学术论文
- 书籍、出版物
- 其他网络法律文章
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from config import TAVILY_API_KEY
from tavily import TavilyClient

client = TavilyClient(api_key=TAVILY_API_KEY)


def search_secondary_sources(query, max_results=10, search_depth="advanced",
                             include_domains=None, exclude_domains=None):
    """
    综合检索二手文献（Secondary Sources），覆盖律所、政府、学术、期刊等所有来源
    - query: 检索关键词
    - max_results: 返回结果数，默认10
    - search_depth: "basic" 或 "advanced"（更深入），默认 advanced
    - include_domains: 限定域名列表
    - exclude_domains: 排除域名列表
    返回: list[dict]，每条含 title/url/content/score
    """
    kwargs = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
    }
    if include_domains:
        kwargs["include_domains"] = include_domains
    if exclude_domains:
        kwargs["exclude_domains"] = exclude_domains

    result = client.search(**kwargs)
    return result.get("results", [])


def search_lawfirm_articles(query, max_results=5):
    """
    专门检索头部律所的法律分析文章
    优先：金杜、君合、方达、中伦、通商、环球、海问、竞天公诚、植德、汉坤等
    """
    lawfirm_domains = [
        "kwm.com",              # 金杜 King & Wood Mallesons
        "junhe.com",            # 君合
        "fangda-partners.com",  # 方达
        "zhonglun.com",         # 中伦
        "tongshang.com",        # 通商
        "haiwen-law.com",       # 海问
        "hankunlaw.com",        # 汉坤
        "jingtian.com",         # 竞天公诚
        "meritsandtree.com",    # 植德
        "globe-law.com",        # 环球
        "allbrightlaw.com",     # 锦天城
        "dehenglaw.com",        # 德恒
        "grandalllaw.com",      # 国浩
        "yingkelawyer.com",     # 盈科
    ]
    return search_secondary_sources(
        query=query,
        max_results=max_results,
        include_domains=lawfirm_domains,
    )


def search_government_interpretations(query, max_results=5):
    """
    检索政府网站的政策解读、答记者问、部门规章解读等
    """
    gov_domains = [
        "gov.cn",
        "npc.gov.cn",       # 全国人大
        "court.gov.cn",     # 最高人民法院
        "spp.gov.cn",       # 最高人民检察院
        "moj.gov.cn",       # 司法部
        "mhrss.gov.cn",     # 人力资源和社会保障部
        "samr.gov.cn",      # 市场监管总局
        "csrc.gov.cn",      # 证监会
        "pbc.gov.cn",       # 中国人民银行
        "mofcom.gov.cn",    # 商务部
    ]
    return search_secondary_sources(
        query=query,
        max_results=max_results,
        include_domains=gov_domains,
    )


def search_academic_sources(query, max_results=5):
    """
    检索法学院校、学术期刊、学术数据库的研究文章和论文
    """
    academic_domains = [
        "cnki.net",             # 中国知网
        "wanfangdata.com.cn",   # 万方数据
        "pku.edu.cn",           # 北京大学
        "tsinghua.edu.cn",      # 清华大学
        "ruc.edu.cn",           # 中国人民大学
        "cupl.edu.cn",          # 中国政法大学
        "whu.edu.cn",           # 武汉大学
        "zuel.edu.cn",          # 中南财经政法大学
        "ecupl.edu.cn",         # 华东政法大学
        "iolaw.org.cn",         # 中国社科院法学所
        "chinalawreview.org",   # 中国法律评论
        "legaldaily.com.cn",    # 法治日报
        "legal.people.com.cn",  # 人民网法治
    ]
    return search_secondary_sources(
        query=query,
        max_results=max_results,
        include_domains=academic_domains,
    )


# ──────────────────────────────────────────────
# 快速测试
# ──────────────────────────────────────────────

if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "合同违约责任 法律分析"

    print(f"=== 综合检索：{keyword} ===")
    results = search_secondary_sources(keyword, max_results=3)
    for r in results:
        print(f"- [{r.get('score', 0):.2f}] {r['title']}")
        print(f"  {r['url']}")
        print(f"  {r.get('content', '')[:100]}...")
        print()

    print(f"\n=== 律所文章检索：{keyword} ===")
    results = search_lawfirm_articles(keyword, max_results=3)
    for r in results:
        print(f"- {r['title']}")
        print(f"  {r['url']}")
        print()

    print(f"\n=== 学术检索：{keyword} ===")
    results = search_academic_sources(keyword, max_results=3)
    for r in results:
        print(f"- {r['title']}")
        print(f"  {r['url']}")
        print()
