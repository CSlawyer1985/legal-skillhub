"""元典开放 API 调用库。

优先从平台 Secret ``YUANDIAN_API_KEY`` 取凭据，同时兼容旧版本地
``config.py``。现行结构化接口使用 ``X-API-Key`` 认证。
"""

import importlib.util
import os
import sys
from pathlib import Path

import requests


BASE_URL = "https://open.chineselaw.com/open"
DEFAULT_TIMEOUT = 60.0
_PLACEHOLDERS = {"", "YOUR_YUANDIAN_API_KEY_HERE"}


def _local_config_value(name):
    """仅读取同目录 config.py，避免误导入系统里的同名模块。"""
    path = Path(__file__).with_name("config.py")
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("prc_legal_research_config", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, name, None)


def _api_key():
    key = os.getenv("YUANDIAN_API_KEY") or _local_config_value("API_KEY")
    if not isinstance(key, str) or key.strip() in _PLACEHOLDERS:
        raise ValueError("未配置 YUANDIAN_API_KEY，请由平台 Secret 或本地 config.py 提供")
    return key.strip()


def _timeout():
    try:
        return max(1.0, float(os.getenv("YUANDIAN_API_TIMEOUT", DEFAULT_TIMEOUT)))
    except ValueError:
        return DEFAULT_TIMEOUT


def _headers(json_body=False):
    headers = {"Accept": "application/json", "X-API-Key": _api_key()}
    if json_body:
        headers["Content-Type"] = "application/json; charset=utf-8"
    return headers


def _decode_response(resp, path):
    if not 200 <= resp.status_code < 300:
        print(f"[错误] {path}: HTTP {resp.status_code}", file=sys.stderr)
        return None
    try:
        result = resp.json()
    except (ValueError, TypeError):
        print(f"[错误] {path}: 响应不是有效 JSON", file=sys.stderr)
        return None
    if not isinstance(result, dict):
        print(f"[错误] {path}: 响应结构无效", file=sys.stderr)
        return None
    if result.get("status") == "success" or result.get("code") in (200, 201):
        if "data" in result:
            return result.get("data")
        if "extra" in result:
            return result.get("extra")
        return result
    message = result.get("message") or result.get("msg") or "未知错误"
    print(f"[错误] {path}: {message}", file=sys.stderr)
    return None


def _post(path, payload):
    """POST 请求封装，兼容 data 与 extra 成功载荷。"""
    try:
        resp = requests.post(
            f"{BASE_URL}{path}",
            headers=_headers(json_body=True),
            json=payload,
            timeout=_timeout(),
        )
    except (requests.RequestException, ValueError) as exc:
        print(f"[错误] {path}: {exc}", file=sys.stderr)
        return None
    return _decode_response(resp, path)


def _get(path, params):
    """GET 请求封装，兼容 data 与 extra 成功载荷。"""
    try:
        resp = requests.get(
            f"{BASE_URL}{path}",
            headers=_headers(),
            params=params,
            timeout=_timeout(),
        )
    except (requests.RequestException, ValueError) as exc:
        print(f"[错误] {path}: {exc}", file=sys.stderr)
        return None
    return _decode_response(resp, path)


# ──────────────────────────────────────────────
# 一、法律法规类
# ──────────────────────────────────────────────

def search_law_vector(query, rewrite_flag=True, fatiao_filter=None, return_num=10):
    """法律法规语义检索，返回现行接口的 extra 对象。"""
    payload = {
        "query": query,
        "rewrite_flag": rewrite_flag,
        "return_num": return_num,
    }
    if fatiao_filter:
        payload["fatiao_filter"] = fatiao_filter
    return _post("/law_vector_search", payload)


def search_fagui(keyword=None, search_mode=None, fgmc=None, sxx=None,
                 xljb_1=None, fbrq_start=None, fbrq_end=None,
                 ssrq_start=None, ssrq_end=None, top_k=10):
    """
    法规关键词检索
    - keyword: 法规关键词（可不填，此时按过滤条件返回列表）
    - search_mode: AND/OR，默认 AND
    - fgmc: 法规名称过滤
    - sxx: 时效性过滤（现行有效/失效/已被修改/部分失效/尚未生效）
    - xljb_1: 效力级别过滤（宪法/法律/司法解释/行政法规/部门规章等）
    - fbrq_start/fbrq_end: 发布日期范围，格式 yyyy-MM-dd
    - ssrq_start/ssrq_end: 实施日期范围，格式 yyyy-MM-dd
    - top_k: 返回条数，默认10，最大50
    返回: list[dict] 法规列表，每条含 id/fgmc/xljb_1/sxx/fbrq/ssrq/content(高亮片段) 等
    """
    payload = {"top_k": top_k}
    if keyword:
        payload["keyword"] = keyword
    if search_mode:
        payload["search_mode"] = search_mode
    if fgmc:
        payload["fgmc"] = fgmc
    if sxx:
        payload["sxx"] = sxx
    if xljb_1:
        payload["xljb_1"] = xljb_1
    if fbrq_start:
        payload["fbrq_start"] = fbrq_start
    if fbrq_end:
        payload["fbrq_end"] = fbrq_end
    if ssrq_start:
        payload["ssrq_start"] = ssrq_start
    if ssrq_end:
        payload["ssrq_end"] = ssrq_end
    return _post("/rh_fg_search", payload)


def get_fagui_detail(id=None, fgmc=None, refer_date=None):
    """
    法规详情（获取全文 content）
    - id: 法规ID（与 fgmc 至少填一个）
    - fgmc: 法规名称
    - refer_date: 参考日期，格式 yyyy-MM-dd（不填则返回当前有效版本）
    返回: dict 法规详情，含 id/fgmc/xljb_1/sxx/fbrq/ssrq/fbbm/content 等
    """
    payload = {}
    if id:
        payload["id"] = id
    if fgmc:
        payload["fgmc"] = fgmc
    if refer_date:
        payload["refer_date"] = refer_date
    return _post("/rh_fg_detail", payload)


def search_fatiao(keyword, search_mode=None, fgmc=None, sxx=None,
                  xljb_1=None, fbrq_start=None, fbrq_end=None,
                  ssrq_start=None, ssrq_end=None, top_k=10):
    """
    法条关键词检索
    - keyword: 法条关键词（必填）
    - search_mode: AND/OR，默认 AND
    - fgmc: 法规名称过滤
    - sxx: 时效性过滤
    - xljb_1: 效力级别过滤
    - fbrq_start/fbrq_end: 发布日期范围
    - ssrq_start/ssrq_end: 实施日期范围
    - top_k: 返回条数，默认10，最大50
    返回: list[dict] 法条列表，每条含 id/fgid/ftmc/ft_num/fgmc/content/llm_content/sxx 等
    注：llm_content 格式为 "- 《{fgmc}》{ft_num}##{content}"，适合直接传给 LLM
    """
    payload = {"keyword": keyword, "top_k": top_k}
    if search_mode:
        payload["search_mode"] = search_mode
    if fgmc:
        payload["fgmc"] = fgmc
    if sxx:
        payload["sxx"] = sxx
    if xljb_1:
        payload["xljb_1"] = xljb_1
    if fbrq_start:
        payload["fbrq_start"] = fbrq_start
    if fbrq_end:
        payload["fbrq_end"] = fbrq_end
    if ssrq_start:
        payload["ssrq_start"] = ssrq_start
    if ssrq_end:
        payload["ssrq_end"] = ssrq_end
    return _post("/rh_ft_search", payload)


def get_fatiao_detail(id=None, fgmc=None, ftnum=None, refer_date=None):
    """
    法条详情
    - id: 法条ID（与 fgmc+ftnum 至少填一组）
    - fgmc: 法规名称（id 为空时必填）
    - ftnum: 法条号（id 为空时必填，如"第一百条"）
    - refer_date: 参考日期，格式 yyyy-MM-dd
    返回: dict 法条详情，含 id/fgid/ftmc/ft_num/fgmc/content/sxx/xljb_1/fbrq/ssrq 等
    """
    payload = {}
    if id:
        payload["id"] = id
    if fgmc:
        payload["fgmc"] = fgmc
    if ftnum:
        payload["ftnum"] = ftnum
    if refer_date:
        payload["refer_date"] = refer_date
    return _post("/rh_ft_detail", payload)


# ──────────────────────────────────────────────
# 二、案例文书类
# ──────────────────────────────────────────────

def search_case_vector(query, rewrite_flag=True, wenshu_filter=None, return_num=10):
    """案例语义检索，返回现行接口的 extra 对象。"""
    payload = {
        "query": query,
        "rewrite_flag": rewrite_flag,
        "return_num": return_num,
    }
    if wenshu_filter:
        payload["wenshu_filter"] = wenshu_filter
    return _post("/case_vector_search", payload)


def search_qwal(qw=None, search_mode=None, title=None, ah=None,
                ay=None, jbdw=None, xzqh_p=None, wszl=None, ajlb=None,
                ja_start=None, ja_end=None, top_k=10):
    """
    权威案例关键词检索（指导性案例、典型案例等）
    - qw: 全文关键词
    - search_mode: and/or，默认 and
    - title: 标题精确匹配
    - ah: 案号
    - ay: 案由列表（多值为或关系）
    - jbdw: 经办法院列表
    - xzqh_p: 省级行政区列表（北京/上海/广东等）
    - wszl: 文书种类列表（判决书/裁定书/调解书/决定书）
    - ajlb: 案件类别（刑事案件/民事案件/行政案件等）
    - ja_start/ja_end: 裁判日期范围，格式 yyyy-MM-dd
    - top_k: 返回条数，默认10，最大50
    返回: dict，含 total（命中总数）和 lst（列表，每条含 id/ah/title/ay/content/llm_content 等）
    注：请求体不能为空，至少传一个字段（如 top_k）
    """
    payload = {"top_k": top_k}
    if qw:
        payload["qw"] = qw
    if search_mode:
        payload["search_mode"] = search_mode
    if title:
        payload["title"] = title
    if ah:
        payload["ah"] = ah
    if ay:
        payload["ay"] = ay
    if jbdw:
        payload["jbdw"] = jbdw
    if xzqh_p:
        payload["xzqh_p"] = xzqh_p
    if wszl:
        payload["wszl"] = wszl
    if ajlb:
        payload["ajlb"] = ajlb
    if ja_start:
        payload["ja_start"] = ja_start
    if ja_end:
        payload["ja_end"] = ja_end
    return _post("/rh_qwal_search", payload)


def search_ptal(qw=None, fxgc=None, search_mode=None, title=None, ah=None,
                ay=None, jbdw=None, xzqh_p=None, wszl=None, ajlb=None,
                ja_start=None, ja_end=None, yyft=None, ft_search_mode=None,
                top_k=10):
    """
    普通案例关键词检索（裁判文书网等）
    - qw: 全文关键词
    - fxgc: 分析过程关键词（独立检索字段）
    - search_mode: and/or，默认 and
    - title: 标题精确匹配
    - ah: 案号
    - ay: 案由列表
    - jbdw: 经办法院/承办单位列表
    - xzqh_p: 省级行政区列表
    - wszl: 文书种类列表
    - ajlb: 案件类别
    - ja_start/ja_end: 结案/裁判日期范围
    - yyft: 援引法条列表（如 ["中华人民共和国刑法第二条"]，法条号需为中文格式）
    - ft_search_mode: yyft 拼接模式，and/or，默认 and
    - top_k: 返回条数，默认10，最大50
    返回: dict，含 total 和 lst（每条含 id/ah/title/ay/content/llm_content 等）
    """
    payload = {"top_k": top_k}
    if qw:
        payload["qw"] = qw
    if fxgc:
        payload["fxgc"] = fxgc
    if search_mode:
        payload["search_mode"] = search_mode
    if title:
        payload["title"] = title
    if ah:
        payload["ah"] = ah
    if ay:
        payload["ay"] = ay
    if jbdw:
        payload["jbdw"] = jbdw
    if xzqh_p:
        payload["xzqh_p"] = xzqh_p
    if wszl:
        payload["wszl"] = wszl
    if ajlb:
        payload["ajlb"] = ajlb
    if ja_start:
        payload["ja_start"] = ja_start
    if ja_end:
        payload["ja_end"] = ja_end
    if yyft:
        payload["yyft"] = yyft
    if ft_search_mode:
        payload["ft_search_mode"] = ft_search_mode
    return _post("/rh_ptal_search", payload)


def get_case_detail(type, id=None, ah=None):
    """
    案例详情（普通案例或权威案例）
    - type: "ptal"（普通案例）或 "qwal"（权威案例）【必填】
    - id: 案例 ID（与 ah 至少填一个）
    - ah: 案号
    返回: list[dict] 最多10条，普通案例含 content/dsr/fxgc/pjjg 等详细字段
    """
    params = {"type": type}
    if id:
        params["id"] = id
    if ah:
        params["ah"] = ah
    return _get("/rh_case_details", params)


# ──────────────────────────────────────────────
# 三、企业信息类
# ──────────────────────────────────────────────

def search_company_by_name(name, num=2):
    """
    按企业名称/股票简称搜索企业详情
    - name: 企业名称或股票简称等检索词【必填】
    - num: 返回条数，默认2，最大50
    返回: list[dict] 企业详情列表，每条含工商信息/股东/知识产权/涉诉/风险等模块
    注：data 字段的 key 为中文
    """
    params = {"name": name, "num": num}
    return _get("/rh_company_info", params)


def get_company_detail(id=None, tyshxydm=None):
    """
    按企业ID或统一社会信用代码精确查询企业详情
    - id: 企业 ID（与 tyshxydm 至少填一个，优先用 id）
    - tyshxydm: 统一社会信用代码
    返回: dict 单条企业详情，含工商信息/股东/知识产权/涉诉/风险等模块
    注：data 字段的 key 为中文
    """
    params = {}
    if id:
        params["id"] = id
    if tyshxydm:
        params["tyshxydm"] = tyshxydm
    return _get("/rh_company_detail", params)


# ──────────────────────────────────────────────
# 快速测试
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("=== 测试：法条检索 ===")
    results = search_fatiao("合同违约责任", sxx="现行有效", top_k=3)
    if results:
        for item in results:
            print(f"- {item.get('ftmc')}")
            print(f"  {item.get('content', '')[:60]}...")

    print("\n=== 测试：法条详情 ===")
    detail = get_fatiao_detail(fgmc="中华人民共和国民法典", ftnum="第五百七十七条")
    if detail:
        print(f"法条：{detail.get('ftmc')}")
        print(f"内容：{detail.get('content')}")
