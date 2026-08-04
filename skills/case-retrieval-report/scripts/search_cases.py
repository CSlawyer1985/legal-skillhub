#!/usr/bin/env python3
"""
案例检索脚本 - 调用得理法律开放平台案例检索 API

用法:
    # 基础关键词检索
    python3 search_cases.py "民间借贷纠纷"

    # 指定条数和页码
    python3 search_cases.py "民间借贷纠纷" --size 10 --page 2

    # 指定排序
    python3 search_cases.py "民间借贷纠纷" --sort-field time --sort-order desc

    # 长文本语义匹配（案件材料匹配）
    python3 search_cases.py --long-text "原告与被告于2023年3月签订借款合同..."

API 文档：得理法律开放平台
端点：https://platform.delilegal.com/api/v1/generice/case/list
响应结构：{success, code, msg, body: {data:[...], totalCount, totalPage, queryId}}
"""

import argparse
import json
import os
import re
import ssl
import sys
import urllib.request
import urllib.error

API_URL = "https://platform.delilegal.com/api/v1/generice/case/list"

# 占位值集合
PLACEHOLDER_VALS = {"YOUR_API_KEY", "YOUR_APP_KEY", "YOUR_APPID", "YOUR APPID", "YOUR_SECRET", "", None}


def load_config():
    """从 config.json 读取 API Key"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "..", "config.json")
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"配置文件不存在: {config_path}\n"
            f"请在技能根目录创建 config.json，格式如下：\n"
            f'{{"apikey": "YOUR_API_KEY"}}\n'
            f"请前往 https://platform.delilegal.com 获取 API Key"
        )
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    apikey = cfg.get("apikey", "").strip()
    if apikey in PLACEHOLDER_VALS:
        raise FileNotFoundError(
            "config.json 中的 apikey 尚未配置或为占位符，请：\n"
            "1. 前往 https://platform.delilegal.com 注册/登录\n"
            "2. 在控制台生成 API Key\n"
            "3. 将 API Key 填入 config.json 的 \"apikey\" 字段"
        )
    return apikey


def search_cases(
    query: str = None,
    long_text: str = None,
    page_no: int = 1,
    page_size: int = 5,
    sort_field: str = "correlation",
    sort_order: str = "desc"
) -> dict:
    """
    调用得理案例检索 API 搜索裁判文书

    参数：
        query      - 检索关键词（与 long_text 二选一）
        long_text  - 长文本语义匹配（与 query 二选一）
        page_no    - 页码，默认 1
        page_size  - 每页条数，默认 5
        sort_field - 排序字段：correlation（相关性）/ time（时间）
        sort_order - 排序方向：desc（降序）/ asc（升序）

    返回：
        API 原始响应 dict，结构为 {success, code, msg, body: {data, totalCount, totalPage, queryId}}
    """
    apikey = load_config()

    # 构造请求体（扁平结构，无 condition 嵌套）
    payload_dict = {
        "pageNo": page_no,
        "pageSize": page_size,
        "sortField": sort_field,
        "sortOrder": sort_order,
    }

    # query 和 longText 二选一
    if long_text:
        payload_dict["longText"] = long_text
    elif query:
        payload_dict["query"] = query

    payload = json.dumps(payload_dict, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + apikey
        },
        method="POST",
    )

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return {"success": False, "code": e.code, "msg": f"HTTP {e.code}: {e.reason}", "body": body}
    except urllib.error.URLError as e:
        return {"success": False, "code": -1, "msg": f"网络连接失败: {e.reason}", "body": None}


def strip_em(text: str) -> str:
    """移除 <em> 高亮标签"""
    return re.sub(r"</?em>", "", str(text))


def format_result(result: dict) -> str:
    """将 API 响应格式化为可读 Markdown"""

    success = result.get("success", False)
    code = result.get("code", 0)

    if not success and code != 0:
        return f"❌ 检索失败: {result.get('msg', '未知错误')} (code: {code})"

    # 标准响应结构：数据在 body 字段下，body 内再有 data 列表
    # 兼容旧格式（直接在顶层 data 字段）
    body = result.get("body", result.get("data", {}))

    if isinstance(body, dict):
        total = body.get("totalCount", body.get("total", 0))
        data = body.get("data", body.get("list", body.get("records", [])))
    elif isinstance(body, list):
        total = len(body)
        data = body
    else:
        return f"❌ 响应数据格式异常，类型: {type(body)}"

    if not data:
        return f"未检索到相关案例（总数: {total}）"

    lines = [f"共检索到 **{total}** 条案例，当前显示第 1-{len(data)} 条\n"]

    for i, case in enumerate(data, 1):
        # 案件名称，优先取 title，其次 name，再次取案号
        title = strip_em(case.get("title", case.get("name", case.get("caseNumber", "无标题"))))
        lines.append(f"### {i}. {title}")

        # 案号（官方字段：caseNumber）
        case_no = case.get("caseNumber", case.get("caseNo", ""))
        if case_no:
            lines.append(f"- **案号：** {case_no}")

        # 案由（官方字段：cause）
        cause = case.get("cause", case.get("causeName", ""))
        if cause:
            lines.append(f"- **案由：** {cause}")

        # 审理法院（官方字段：court）
        court = case.get("court", case.get("courtName", ""))
        if court:
            lines.append(f"- **审理法院：** {court}")

        # 审级（官方字段：levelOfTrial）
        level_of_trial = case.get("levelOfTrial", case.get("courtLevelName", case.get("trialTypeName", "")))
        if level_of_trial:
            lines.append(f"- **审理程序：** {level_of_trial}")

        # 文书类型（官方字段：judgementType）
        doc_type = case.get("judgementType", case.get("judgementTypeName", ""))
        if doc_type:
            lines.append(f"- **文书类型：** {doc_type}")

        # 裁判日期（官方字段：judgementDate）
        judge_date = case.get("judgementDate", case.get("judgeDate", case.get("caseDate", "")))
        if judge_date:
            lines.append(f"- **裁判日期：** {judge_date}")

        # 公布类型（官方字段：publishTypeName）
        publish_type = case.get("publishTypeName", case.get("publishType", ""))
        if publish_type:
            lines.append(f"- **公布类型：** {publish_type}")

        # 摘要/内容
        content = case.get("content", "")
        summary = case.get("summary", case.get("abstract", ""))
        highlights = case.get("highlights", "")

        display_text = content or highlights or summary
        if display_text:
            display_text = strip_em(str(display_text))
            if len(display_text) > 300:
                display_text = display_text[:300] + "..."
            lines.append(f"- **摘要：** {display_text}")

        lines.append("")

    lines.append("---")
    lines.append("> 数据来源：得理案例数据库（得理法律开放平台）。类案判断须结合裁判三要素（基本事实、争议焦点、法律适用）综合评估，不得仅凭标题或案由认定。")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="案例检索 - 调用得理法律开放平台 API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s "民间借贷纠纷"
  %(prog)s "小产权房买卖合同无效" --size 20
  %(prog)s "劳动合同解除" --sort-field time --sort-order desc
  %(prog)s --long-text "原告与被告于2023年3月签订借款合同..."
        """)

    # keyword 与 --long-text 二选一
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("keyword", nargs="?", default=None,
                       help="检索关键词（自然语言，如'民间借贷利率上限'）")
    group.add_argument("--long-text", dest="long_text", default=None,
                       help="长文本语义匹配（传入案件材料文本）")

    # 分页
    parser.add_argument("--page", type=int, default=1, help="页码（默认 1）")
    parser.add_argument("--size", type=int, default=5, help="每页条数（默认 5）")

    # 排序
    parser.add_argument("--sort-field", dest="sort_field",
                        choices=["correlation", "time"],
                        default="correlation",
                        help="排序字段：correlation（相关性，默认）/ time（时间）")
    parser.add_argument("--sort-order", dest="sort_order",
                        choices=["desc", "asc"],
                        default="desc",
                        help="排序方向：desc（降序，默认）/ asc（升序）")

    args = parser.parse_args()

    if not args.keyword and not args.long_text:
        parser.error("必须提供关键词或使用 --long-text")

    result = search_cases(
        query=args.keyword,
        long_text=args.long_text,
        page_no=args.page,
        page_size=args.size,
        sort_field=args.sort_field,
        sort_order=args.sort_order,
    )
    print(format_result(result))


if __name__ == "__main__":
    main()
