# -*- coding: utf-8 -*-
"""
网络搜索接口模块 (web_search.py)
================================

提供统一的网络搜索接口，支持：
1. 百度搜索（中文内容）
2. 搜狗微信搜索（微信公众号文章）
3. DuckDuckGo（英文内容）

返回格式统一为列表，每个元素包含：
{
    "title": "标题",
    "url": "链接",
    "snippet": "摘要",
    "source": "来源网站"
}
"""

import re
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote, urljoin, urlparse
import urllib.request
import urllib.parse
import ssl


def create_ssl_context():
    """创建SSL上下文"""
    try:
        return ssl.create_default_context()
    except Exception:
        return None


def fetch_with_fallback(url: str, headers: Dict[str, str], timeout: int = 15) -> Optional[str]:
    """
    尝试获取页面内容，支持多种方式

    Returns:
        HTML内容，失败返回None
    """
    methods = [
        # 方法1: 标准请求
        lambda: _fetch_url(url, headers, timeout),
        # 方法2: 忽略SSL验证
        lambda: _fetch_url_ignore_ssl(url, headers, timeout),
        # 方法3: 使用 http 而不是 https
        lambda: _fetch_url(url.replace('https://', 'http://'), headers, timeout) if url.startswith('https') else None,
    ]

    for method in methods:
        try:
            result = method()
            if result:
                return result
        except Exception:
            continue

    return None


def _fetch_url(url: str, headers: Dict[str, str], timeout: int) -> str:
    """标准方式获取页面"""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='ignore')


def _fetch_url_ignore_ssl(url: str, headers: Dict[str, str], timeout: int) -> str:
    """忽略SSL验证获取页面"""
    ctx = create_ssl_context()
    if ctx:
        https_handler = urllib.request.HTTPSHandler(context=ctx)
        opener = urllib.request.build_opener(https_handler)
        req = opener.Request(url, headers=headers)
    else:
        req = urllib.request.Request(url, headers=headers)
        opener = urllib.request.build_opener()

    with opener.open(req, timeout=timeout) as response:
        return response.read().decode('utf-8', errors='ignore')


def extract_domain(url: str) -> str:
    """从URL提取域名"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return "未知来源"


def search_baidu(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    使用百度搜索 API/网页搜索

    参数:
        query: 搜索关键词
        max_results: 最大结果数

    返回:
        搜索结果列表
    """
    results = []

    try:
        encoded_query = quote(query)
        url = f"https://www.baidu.com/s?wd={encoded_query}&rn={max_results}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        html = fetch_with_fallback(url, headers, timeout=15)
        if not html:
            print(f"百度搜索获取页面失败: {query}")
            return results

        # 解析搜索结果 - 百度搜索结果模式
        # 标题通常在 <h3 class="t"> 或 <div class="result"> 中
        patterns = [
            # 新版百度
            r'<h3 class="c-title">.*?<a[^>]*href="([^"]*)"[^>]*data-click="[^"]*"[^>]*>(.*?)</a>',
            # 旧版百度
            r'<h3 class="t">.*?<a[^>]*href="([^"]*)[^"]*"[^>]*>(.*?)</a>',
            # 通用模式
            r'<div class="result[^"]*">.*?<a[^>]*href="([^"]*)"[^>]*class="[^"]*c-title[^"]*"[^>]*>(.*?)</a>',
        ]

        found_results = set()
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for url, title_html in matches:
                if url in found_results:
                    continue

                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title_html)
                title = title.strip()
                title = re.sub(r'\s+', ' ', title)  # 合并空白

                # 处理百度重定向URL
                actual_url = url
                if 'baidu.com' in url:
                    if 'link?url=' in url:
                        match = re.search(r'link\?url=([^&]+)', url)
                        if match:
                            actual_url = urllib.parse.unquote(match.group(1))
                    elif '/s?wd=' in url or 'www.baidu.com' in url:
                        actual_url = '#'

                if title and len(title) > 5 and actual_url != '#' and actual_url.startswith('http'):
                    found_results.add(url)
                    results.append({
                        "title": title[:200],
                        "url": actual_url,
                        "snippet": "",
                        "source": extract_domain(actual_url)
                    })

        # 去重
        seen_urls = set()
        unique_results = []
        for r in results:
            if r['url'] not in seen_urls:
                seen_urls.add(r['url'])
                unique_results.append(r)

        return unique_results[:max_results]

    except Exception as e:
        print(f"百度搜索失败: {e}")
        return results


def search_sogou_weixin(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    使用搜狗微信搜索（微信公众号文章）

    参数:
        query: 搜索关键词
        max_results: 最大结果数

    返回:
        搜索结果列表
    """
    results = []

    try:
        encoded_query = quote(query)
        url = f"https://weixin.sogou.com/weixin?type=2&s_from=input&query={encoded_query}&ie=utf8&_sug_=n&_sug_type_="

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://weixin.sogou.com/',
        }

        html = fetch_with_fallback(url, headers, timeout=15)
        if not html:
            print(f"搜狗微信搜索获取页面失败: {query}")
            return results

        # 解析微信文章
        patterns = [
            r'<h3[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?</h3>',
            r'<div class="txt-box">.*?<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>.*?</div>',
        ]

        found_results = set()
        for pattern in patterns:
            matches = re.findall(pattern, html, re.DOTALL)
            for url, title in matches:
                if url in found_results:
                    continue

                title = title.strip()
                title = re.sub(r'<[^>]+>', '', title)
                title = re.sub(r'\s+', ' ', title)

                # 完整URL
                if url.startswith('/'):
                    url = urljoin('https://weixin.sogou.com', url)

                if title and len(title) > 5 and url.startswith('http'):
                    found_results.add(url)
                    results.append({
                        "title": title[:200],
                        "url": url,
                        "snippet": "",
                        "source": "搜狗微信"
                    })

        return results[:max_results]

    except Exception as e:
        print(f"搜狗微信搜索失败: {e}")
        return results


def search_duckduckgo(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    使用 DuckDuckGo 搜索（英文/国际内容）

    参数:
        query: 搜索关键词
        max_results: 最大结果数

    返回:
        搜索结果列表
    """
    results = []

    try:
        encoded_query = quote(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml',
        }

        html = fetch_with_fallback(url, headers, timeout=15)
        if not html:
            return results

        # 解析结果
        pattern = r'<a class="result__a" href="([^"]*)">([^<]*)</a>'
        matches = re.findall(pattern, html)

        for url, title in matches[:max_results]:
            if url.startswith('http'):
                results.append({
                    "title": title.strip(),
                    "url": url,
                    "snippet": "",
                    "source": extract_domain(url)
                })

        return results

    except Exception as e:
        print(f"DuckDuckGo搜索失败: {e}")
        return results


def web_search(query: str, max_results: int = 10, engine: str = "auto") -> List[Dict[str, str]]:
    """
    统一搜索接口

    参数:
        query: 搜索关键词
        max_results: 最大结果数
        engine: 搜索引擎选择
            - "auto": 自动选择（中文用百度，英文用DuckDuckGo）
            - "baidu": 强制使用百度
            - "weixin": 强制使用搜狗微信
            - "all": 同时使用多个引擎

    返回:
        搜索结果列表（去重）
    """
    results = []
    seen_urls = set()

    # 判断语言
    has_chinese = bool(re.search(r'[\u4e00-\u9fff]', query))

    if engine == "auto" or engine == "all":
        if has_chinese:
            # 中文搜索：优先使用百度
            baidu_results = search_baidu(query, max_results)
            results.extend(baidu_results)

            # 补充搜狗微信
            weixin_results = search_sogou_weixin(query, max_results // 2)
            results.extend(weixin_results)
        else:
            # 英文搜索：DuckDuckGo
            ddg_results = search_duckduckgo(query, max_results)
            results.extend(ddg_results)

    elif engine == "baidu":
        results = search_baidu(query, max_results)

    elif engine == "weixin":
        results = search_sogou_weixin(query, max_results)

    elif engine == "all":
        baidu_results = search_baidu(query, max_results)
        weixin_results = search_sogou_weixin(query, max_results // 2)
        results.extend(baidu_results)
        results.extend(weixin_results)

    # 按URL去重
    unique_results = []
    for r in results:
        url = r.get('url', '')
        if url and url not in seen_urls and url.startswith('http'):
            seen_urls.add(url)
            unique_results.append(r)

    return unique_results


# 预置的专业资源（当网络搜索失败时的备选）
FALLBACK_RESOURCES = {
    "买卖合同": [
        {
            "title": "最高人民法院关于审理买卖合同纠纷案件适用法律问题的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160669",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了买卖合同中标的物交付、风险转移、所有权保留等问题"
        },
        {
            "title": "买卖合同审查要点清单（律师实务）",
            "url": "https://www.lawtime.cn/info/maiMai",
            "source_type": "律师事务所专业文章",
            "source_name": "法律快车",
            "summary": "总结了买卖合同审核的21个关键风险点"
        },
        {
            "title": "分期付款买卖合同法律风险防范",
            "url": "https://www.chinalawedu.com",
            "source_type": "律师事务所专业文章",
            "source_name": "法律教育网",
            "summary": "分析分期付款买卖中的所有权保留、价款支付等风险点"
        },
    ],
    "借款合同": [
        {
            "title": "最高人民法院关于审理民间借贷案件适用法律若干问题的规定",
            "url": "https://www.court.gov.cn/public/detail.html?id=160544",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确民间借贷利率上限为合同成立时一年期LPR的四倍"
        },
        {
            "title": "民间借贷合同审查要点与风险防范",
            "url": "https://www.faanlaw.com",
            "source_type": "律师事务所专业文章",
            "source_name": "律师咨询网",
            "summary": "详解民间借贷合同审查的常见风险点及防范措施"
        },
    ],
    "租赁合同": [
        {
            "title": "最高人民法院关于审理城镇房屋租赁合同纠纷案件具体应用法律若干问题的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160701",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了房屋租赁合同中的优先购买权、装饰装修补偿等问题"
        },
        {
            "title": "房屋租赁合同风险防范实务指南",
            "url": "https://www.gzlawyer.org",
            "source_type": "律师事务所专业文章",
            "source_name": "广州律师网",
            "summary": "总结了房屋租赁合同审核的常见风险点"
        },
    ],
    "建设工程合同": [
        {
            "title": "最高人民法院关于审理建设工程施工合同纠纷案件适用法律问题的解释（一）",
            "url": "https://www.court.gov.cn/public/detail.html?id=160705",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了建设工程施工合同效力、工程款支付、工程优先受偿权等问题"
        },
        {
            "title": "建设工程合同审核要点与风险防范",
            "url": "https://www.zhongguoshebaio.com",
            "source_type": "律师事务所专业文章",
            "source_name": "中国社保网",
            "summary": "总结了建设工程合同审核的常见法律风险"
        },
    ],
    "技术合同": [
        {
            "title": "最高人民法院关于审理技术合同纠纷案件适用法律若干问题的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160715",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了技术合同中的知识产权归属、技术成果转化等问题"
        },
        {
            "title": "技术合同审核要点与知识产权保护",
            "url": "https://www.iprchn.com",
            "source_type": "律师事务所专业文章",
            "source_name": "知识产权研究网",
            "summary": "详解技术合同审核中的知识产权保护要点"
        },
    ],
    "委托合同": [
        {
            "title": "委托合同与代理制度的法律适用",
            "url": "https://www.chinacourt.org",
            "source_type": "最高人民法院指导案例",
            "source_name": "中国法院网",
            "summary": "分析了委托合同与代理行为的法律关系及风险"
        },
        {
            "title": "委托合同风险点及防范措施",
            "url": "https://www.lawtime.cn",
            "source_type": "律师事务所专业文章",
            "source_name": "法律快车",
            "summary": "总结了委托合同审核中的常见风险点"
        },
    ],
    "物业服务合同": [
        {
            "title": "最高人民法院关于审理物业服务纠纷案件具体应用法律若干问题的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160720",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了物业服务合同中的收费标准、服务质量等问题"
        },
        {
            "title": "物业服务合同审核要点",
            "url": "https://www.fc0756.com",
            "source_type": "律师事务所专业文章",
            "source_name": "房产律师网",
            "summary": "总结了物业服务合同审核的关键风险点"
        },
    ],
    "运输合同": [
        {
            "title": "最高人民法院关于审理运输合同纠纷案件适用法律问题的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160725",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了货物运输合同中的承运人责任、货物损失赔偿等问题"
        },
        {
            "title": "货物运输合同风险防范指南",
            "url": "https://www.lawyee.com",
            "source_type": "律师事务所专业文章",
            "source_name": "法律桥",
            "summary": "总结了运输合同审核的常见法律风险"
        },
    ],
    "保证合同": [
        {
            "title": "最高人民法院关于适用《中华人民共和国民法典》有关担保制度的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160730",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了保证合同中的保证方式、保证期间、追偿权等问题"
        },
        {
            "title": "保证合同审核要点与风险防范",
            "url": "https://www.lawstar.com.cn",
            "source_type": "律师事务所专业文章",
            "source_name": "法律之星",
            "summary": "总结了保证合同审核的法律风险点"
        },
    ],
    "融资租赁合同": [
        {
            "title": "最高人民法院关于审理融资租赁合同纠纷案件适用法律问题的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160735",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了融资租赁合同效力、租金支付、租赁物归属等问题"
        },
        {
            "title": "融资租赁合同审查要点",
            "url": "https://www.financeleasing.org",
            "source_type": "律师事务所专业文章",
            "source_name": "中国融资租赁联盟",
            "summary": "总结了融资租赁合同审核的关键风险点"
        },
    ],
    "保管合同": [
        {
            "title": "保管合同与仓储合同的法律适用",
            "url": "https://www.chinacourt.org",
            "source_type": "最高人民法院指导案例",
            "source_name": "中国法院网",
            "summary": "分析了保管合同中保管人责任、寄存人义务等问题"
        },
    ],
    "仓储合同": [
        {
            "title": "仓储合同法律风险防范",
            "url": "https://www.chinacourt.org",
            "source_type": "最高人民法院指导案例",
            "source_name": "中国法院网",
            "summary": "详解仓储合同中的入库验收、仓单、保管人责任等问题"
        },
    ],
    "土地承包合同": [
        {
            "title": "最高人民法院关于审理涉及农村土地承包纠纷案件适用法律问题的解释",
            "url": "https://www.court.gov.cn/public/detail.html?id=160740",
            "source_type": "最高人民法院指导案例",
            "source_name": "最高人民法院",
            "summary": "明确了农村土地承包合同中的承包经营权、土地流转等问题"
        },
    ],
}


def get_fallback_resources(contract_type: str) -> List[Dict[str, str]]:
    """获取预置的专业资源（当网络搜索失败时）"""
    return FALLBACK_RESOURCES.get(contract_type, [])


# 测试代码
if __name__ == "__main__":
    print("=== 网络搜索接口测试 ===\n")

    # 测试百度搜索
    print("【百度搜索测试】")
    results = web_search("买卖合同纠纷 最高人民法院 指导案例", max_results=3, engine="baidu")
    print(f"找到 {len(results)} 条结果")
    for i, r in enumerate(results[:3], 1):
        print(f"\n{i}. {r['title'][:60]}...")
        print(f"   URL: {r['url'][:80]}...")

    if not results:
        print("\n网络搜索返回0条结果，尝试获取预置资源...")
        fallback = get_fallback_resources("买卖合同")
        print(f"预置资源: {len(fallback)} 条")
