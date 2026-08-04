"""
联网检索执行器模块 (Module C)
功能：多库并行专利检索、结果去重、穷尽性校验
优先级：欧燕专利 > CNIPA > EPO Espacenet > WIPO Patentscope > USPTO > PatSeek 中国专利
"""

import time
import hashlib
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import multiprocessing

# 导入凭证配置
from .config import load_credentials


DATABASE_CONFIG = {
    "欧燕专利": {"name": "欧燕专利检索平台", "priority": 0},
    "CNIPA": {"name": "国知局专利公布公告网", "priority": 1},
    "EPO Espacenet": {"name": "欧洲专利局数据库", "priority": 2},
    "WIPO Patentscope": {"name": "WIPO专利数据库", "priority": 3},
    "USPTO": {"name": "美国专利商标局", "priority": 4},
    "PatSeek 中国专利": {"name": "谷歌专利", "priority": 5}
}


@dataclass
class PatentResult:
    patent_no: str = ""
    title: str = ""
    abstract: str = ""
    applicant: str = ""
    inventor: str = ""
    apply_date: str = ""
    publish_date: str = ""
    ipc_code: str = ""
    legal_status: str = ""
    similarity: float = 0.0
    source_db: str = ""
    source_url: str = ""


@dataclass
class SearchResult:
    total_count: int = 0
    results: List[PatentResult] = field(default_factory=list)
    databases_used: List[str] = field(default_factory=list)
    queries_used: List[str] = field(default_factory=list)
    exhaustive_check: Dict = field(default_factory=dict)


def calculate_hash(patent: Dict) -> str:
    content = f"{patent.get('patent_no', '')}{patent.get('title', '')}{patent.get('abstract', '')}"
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def deduplicate_results(results: List[Dict]) -> List[Dict]:
    seen = set()
    deduplicated = []
    for patent in results:
        h = calculate_hash(patent)
        if h not in seen:
            seen.add(h)
            deduplicated.append(patent)
    return deduplicated


def rank_by_similarity(results: List[Dict]) -> List[Dict]:
    return sorted(results, key=lambda x: x.get('similarity', 0), reverse=True)


def search_cnipa(query: str, max_results: int = 50) -> List[Dict]:
    """检索CNIPA - 需要适配官方接口"""
    # TODO: 实现CNIPA检索
    return []


def search_espacenet(query: str, max_results: int = 50) -> List[Dict]:
    """检索EPO Espacenet - 使用公开API"""
    # TODO: 实现Espacenet检索
    return []


def search_patentscope(query: str, max_results: int = 50) -> List[Dict]:
    """检索WIPO Patentscope - 使用公开API"""
    # TODO: 实现Patentscope检索
    return []


def search_patseek(query: str, max_results: int = 50) -> List[Dict]:
    """检索PatSeek 中国专利 - 补充检索用"""
    # TODO: 实现PatSeek 中国专利检索
    return []


def search_uyanip(query: str, max_results: int = 50) -> List[Dict]:
    """
    检索欧燕专利平台 - 使用凭证自动登录
    需要先加载凭证配置
    """
    import requests
    from bs4 import BeautifulSoup

    results = []
    creds = load_credentials()

    if not creds.uyanip_enabled:
        print("欧燕专利平台未启用，请在 config/credentials.toml 中设置 enabled=true")
        return results

    try:
        session = requests.Session()

        # 1. 登录获取Cookie
        login_url = "https://www.uyanip.com/api/login"
        login_data = {
            "username": creds.uyanip_username,
            "password": creds.uyanip_password
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json"
        }

        login_resp = session.post(login_url, json=login_data, headers=headers, timeout=10)

        if login_resp.status_code != 200:
            print(f"欧燕专利登录失败: {login_resp.status_code}")
            return results

        # 2. 执行搜索
        search_url = "https://www.uyanip.com/api/search"
        search_params = {"q": query, "page": 1, "size": min(max_results, 50)}

        search_resp = session.get(search_url, params=search_params, headers=headers, timeout=15)

        if search_resp.status_code != 200:
            print(f"欧燕专利搜索失败: {search_resp.status_code}")
            return results

        data = search_resp.json()

        # 3. 解析结果
        patents = data.get("data", []) if isinstance(data, dict) else []

        for p in patents:
            results.append({
                "patent_no": p.get("patent_no", ""),
                "title": p.get("title", ""),
                "abstract": p.get("abstract", ""),
                "applicant": p.get("applicant", ""),
                "inventor": p.get("inventor", ""),
                "apply_date": p.get("apply_date", ""),
                "publish_date": p.get("publish_date", ""),
                "ipc_code": p.get("ipc_code", ""),
                "legal_status": p.get("legal_status", ""),
                "similarity": p.get("score", 0.0),
                "source_db": "欧燕专利",
                "source_url": f"https://www.uyanip.com/patent/{p.get('patent_no', '')}"
            })

    except ImportError:
        print("提示: 需要安装 requests 和 beautifulsoup4 库才能使用欧燕专利平台")
        print("安装命令: pip install requests beautifulsoup4")
    except Exception as e:
        print(f"欧燕专利检索异常: {e}")

    return results


def search_uyanip_browser(query: str, max_results: int = 50) -> List[Dict]:
    """
    欧燕专利平台浏览器自动化检索（备选方案）
    当API不可用时使用浏览器自动化
    """
    results = []
    creds = load_credentials()

    if not creds.uyanip_enabled:
        return results

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # 1. 访问登录页
            page.goto("https://www.uyanip.com/login", timeout=30000)

            # 2. 填写登录信息
            page.fill("input[name='username']", creds.uyanip_username)
            page.fill("input[name='password']", creds.uyanip_password)
            page.click("button[type='submit']")

            page.wait_for_load_state("networkidle", timeout=10000)

            # 3. 执行搜索
            page.fill("input[name='search']", query)
            page.click("button.search-btn")
            page.wait_for_load_state("networkidle", timeout=15000)

            # 4. 解析结果列表
            patent_items = page.query_selector_all(".patent-item")

            for item in patent_items[:max_results]:
                title_el = item.query_selector(".title")
                title = title_el.inner_text().strip() if title_el else ""

                # 提取专利号等信息
                info_text = item.inner_text()

                results.append({
                    "patent_no": re.search(r'\d+', info_text).group() if re.search(r'\d+', info_text) else "",
                    "title": title,
                    "abstract": "",
                    "applicant": "",
                    "inventor": "",
                    "apply_date": "",
                    "publish_date": "",
                    "ipc_code": "",
                    "legal_status": "",
                    "similarity": 0.8,
                    "source_db": "欧燕专利",
                    "source_url": ""
                })

            browser.close()

    except ImportError:
        print("提示: 需要安装 playwright 库才能使用浏览器自动化")
        print("安装命令: pip install playwright && playwright install chromium")
    except Exception as e:
        print(f"欧燕专利浏览器检索异常: {e}")

    return results


SEARCH_FUNCTIONS = {
    "欧燕专利": search_uyanip,
    "CNIPA": search_cnipa,
    "EPO Espacenet": search_espacenet,
    "WIPO Patentscope": search_patentscope,
    "PatSeek 中国专利": search_patseek
}


def search_database(database: str, query: str, max_results: int = 50) -> List[Dict]:
    if database in SEARCH_FUNCTIONS:
        return SEARCH_FUNCTIONS[database](query, max_results)
    return []


def parallel_search(
    queries: List[Dict],
    databases: List[str],
    max_workers: int = 4,
    timeout: int = 30
) -> Tuple[List[Dict], List[str]]:
    all_results = []
    successful_databases = []

    with ThreadPoolExecutor(max_workers=min(max_workers, multiprocessing.cpu_count())) as executor:
        futures = {}
        for db in databases:
            for q in queries:
                query_text = q.get("query", "") if isinstance(q, dict) else str(q)
                future = executor.submit(search_database, db, query_text)
                futures[future] = (db, query_text)

        for future in futures:
            db, query_text = futures[future]
            try:
                results = future.result(timeout=timeout)
                if results:
                    all_results.extend(results)
                    if db not in successful_databases:
                        successful_databases.append(db)
            except TimeoutError:
                continue

    return all_results, successful_databases


def check_exhaustiveness(results: List[Dict], queries_used: List[str], databases_used: List[str]) -> Dict:
    check_items = {
        "multi_database_cross_validation": len(databases_used) >= 3,
        "keyword_classification_combination": len(queries_used) >= 2,
        "citation_tracking": "需补充",
        "applicant_tracking": "需补充",
        "non_patent_literature": "需补充",
        "result_convergence": len(queries_used) >= 3 and len(results) >= 50
    }

    passed = sum(1 for v in check_items.values() if v is True)
    total = len(check_items)

    return {
        "items": check_items,
        "passed_count": passed,
        "total_count": total,
        "pass_rate": f"{passed}/{total}",
        "overall": "通过" if passed >= 4 else "部分通过，需补充检索"
    }


def patent_search(
    queries: List[Dict],
    databases: List[str] = None,
    min_results: int = 50
) -> SearchResult:
    # 加载凭证
    creds = load_credentials()

    if databases is None:
        # 默认数据库列表
        default_databases = ["CNIPA", "EPO Espacenet", "WIPO Patentscope"]

        # 如果欧燕专利平台已启用，优先添加
        if creds.uyanip_enabled:
            databases = ["欧燕专利"] + default_databases
        else:
            databases = default_databases

    # 如果用户指定了数据库但没有欧燕专利，且凭证已启用，自动插入到第一位
    elif creds.uyanip_enabled and "欧燕专利" not in databases:
        databases = ["欧燕专利"] + databases

    all_results, successful_databases = parallel_search(queries, databases)
    deduplicated = deduplicate_results(all_results)
    ranked = rank_by_similarity(deduplicated)
    exhaustive = check_exhaustiveness(ranked, [q.get("query", "") for q in queries], successful_databases)

    patent_results = []
    for p in ranked[:min_results]:
        patent_results.append(PatentResult(
            patent_no=p.get("patent_no", ""),
            title=p.get("title", ""),
            abstract=p.get("abstract", ""),
            applicant=p.get("applicant", ""),
            similarity=p.get("similarity", 0.0),
            source_db=p.get("source_db", "")
        ))

    return SearchResult(
        total_count=len(patent_results),
        results=patent_results,
        databases_used=successful_databases,
        queries_used=[q.get("query", "") for q in queries],
        exhaustive_check=exhaustive
    )


if __name__ == "__main__":
    print("联网检索执行器 (Module C)")
    print("支持数据库: CNIPA, EPO Espacenet, WIPO Patentscope, USPTO, PatSeek 中国专利")