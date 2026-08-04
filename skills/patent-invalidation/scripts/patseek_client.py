#!/usr/bin/env python3
"""
PatSeek 专利检索客户端脚本

支持三种检索模式：
1. bool_search — 关键词/号码 Bool 检索（支持 AND/OR 组合、字段前缀）
2. get_patent  — 按公开号/申请号获取专利详情
3. semantic_search_async — 异步语义检索（提交 + 轮询 + 返回结果）

字段前缀: AP=(申请人) IPC=(分类号) PID=(公开号) AN=(申请号) AD/PD=(日期) NOT=(排除)

用法:
  python3 patseek_client.py bool "低空空域 AND 无人机" [--page 1] [--page-size 20]
  python3 patseek_client.py bool "AP=(华为) IPC=(H01M) AD>=2020" [--page-size 10]
  python3 patseek_client.py patent CN118658342A
  python3 patseek_client.py semantic "新能源汽车电池管理系统" [--timeout 180]
  python3 patseek_client.py task <task_id> [--include-partial]
  python3 patseek_client.py cancel <task_id>
  python3 patseek_client.py tasks [--limit 10]
"""

import argparse
import json
import os
import sys
import time

# 尝试导入 requests，若无则给出提示
try:
    import requests
except ImportError:
    print("错误: 需要安装 requests 库。请运行: pip install requests", file=sys.stderr)
    sys.exit(1)


def _load_dotenv() -> None:
    """轻量 .env 加载：按以下顺序查找，**不覆盖**已有环境变量。
    1. scripts/.env（脚本旁边）
    2. skill 根目录 .env（../.env，相对于本脚本）
    3. 当前工作目录 .env

    支持 KEY=VALUE / KEY="VALUE" / # 注释 / 空行。
    本实现零依赖（不引入 python-dotenv）；不写死任何示例 key。
    """
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(here, ".env"),
        os.path.normpath(os.path.join(here, "..", ".env")),
        os.path.join(os.getcwd(), ".env"),
    ]
    for p in candidates:
        if not os.path.isfile(p):
            continue
        try:
            with open(p, "r", encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith("#") or "=" not in ln:
                        continue
                    k, v = ln.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except OSError:
            pass


_load_dotenv()

BASE_URL = "https://patseek.cn"

# API Key 优先级: 命令行参数 > 环境变量 PATSEEK_API_KEY（环境变量可来自 export 或 .env）
API_KEY = os.environ.get("PATSEEK_API_KEY", "")


def get_headers(api_key: str) -> dict:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def bool_search(api_key: str, query: str, page: int = 1, page_size: int = 20) -> dict:
    """Bool 检索，支持 AND/OR 逻辑组合、字段前缀（AP/IPC/PID/AN/AD/PD/NOT）"""
    resp = requests.post(
        f"{BASE_URL}/v1/search",
        headers=get_headers(api_key),
        json={"query": query, "page": page, "page_size": page_size},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def get_patent(api_key: str, identifier: str) -> dict:
    """按公开号或申请号获取单条专利详情"""
    resp = requests.get(
        f"{BASE_URL}/v1/patent/{identifier}",
        headers=get_headers(api_key),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def semantic_search_async_submit(api_key: str, query: str) -> dict:
    """提交异步语义检索任务，返回 task_id 等信息"""
    resp = requests.post(
        f"{BASE_URL}/v1/semantic/async",
        headers=get_headers(api_key),
        json={"query": query},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def query_task(api_key: str, task_id: str, include_partial: bool = False) -> dict:
    """查询异步任务状态/结果"""
    params = {}
    if include_partial:
        params["include_partial"] = "true"
    resp = requests.get(
        f"{BASE_URL}/v1/tasks/{task_id}",
        headers=get_headers(api_key),
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def cancel_task(api_key: str, task_id: str) -> dict:
    """取消正在运行的异步任务"""
    resp = requests.delete(
        f"{BASE_URL}/v1/tasks/{task_id}",
        headers=get_headers(api_key),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def list_tasks(api_key: str, limit: int = 20) -> dict:
    """列出任务历史"""
    resp = requests.get(
        f"{BASE_URL}/v1/tasks",
        headers=get_headers(api_key),
        params={"limit": limit},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def semantic_search_async(api_key: str, query: str, timeout: int = 180) -> list:
    """
    异步语义检索完整流程：提交 -> 轮询 -> 返回结果列表

    轮询策略:
      前 10 秒: 每 2 秒查询一次
      10-60 秒: 每 5 秒查询一次
      60 秒后: 每 10 秒查询一次
    """
    # 1. 提交任务
    submit_data = semantic_search_async_submit(api_key, query)
    task_id = submit_data["task_id"]
    status = submit_data["status"]
    print(json.dumps(submit_data, ensure_ascii=False), file=sys.stderr)

    # 如果缓存命中，直接返回
    if status == "succeeded":
        task_data = query_task(api_key, task_id)
        return task_data.get("result", [])

    # 2. 轮询
    elapsed = 0
    while elapsed < timeout:
        interval = 2 if elapsed < 10 else (5 if elapsed < 60 else 10)
        time.sleep(interval)
        elapsed += interval

        task_data = query_task(api_key, task_id, include_partial=True)
        status = task_data["status"]
        received = task_data.get("progress", {}).get("received", 0)
        print(
            f"  [{elapsed}s] status={status}, received={received}",
            file=sys.stderr,
        )

        if status == "succeeded":
            return task_data.get("result", [])
        elif status in ("failed", "cancelled"):
            print(f"任务终止: {task_data.get('error')}", file=sys.stderr)
            return []

    print("轮询超时", file=sys.stderr)
    return []


# ── 格式化输出辅助函数 ──────────────────────────────────────────

def format_patent_brief(p: dict) -> str:
    """格式化单条专利的简要信息（Bool 检索结果）"""
    lines = [
        f"公开号: {p.get('pid', 'N/A')}",
        f"申请号: {p.get('appnum', 'N/A')}",
        f"名称:   {p.get('title', 'N/A')}",
        f"申请人: {p.get('applicant', 'N/A')}",
        f"IPC:    {p.get('ipcs', 'N/A')}",
        f"申请日: {p.get('appdate', 'N/A')}  公开日: {p.get('pubdate', 'N/A')}",
    ]
    abstract = p.get("abstract", "")
    if abstract:
        lines.append(f"摘要:   {abstract[:200]}{'...' if len(abstract) > 200 else ''}")
    return "\n".join(lines)


def format_semantic_patent_brief(p: dict) -> str:
    """格式化单条语义检索专利的简要信息"""
    lines = [
        f"公开号:   {p.get('pid', 'N/A')}",
        f"相似度:   {p.get('similarity', 'N/A')}",
        f"名称:     {p.get('title', 'N/A')}",
        f"申请人:   {p.get('applicant', 'N/A')}",
        f"IPC:      {p.get('ipcs', 'N/A')}",
        f"申请日:   {p.get('appdate', 'N/A')}  公开日: {p.get('pubdate', 'N/A')}",
    ]
    abstract = p.get("abstract", "")
    if abstract:
        lines.append(f"摘要:     {abstract[:200]}{'...' if len(abstract) > 200 else ''}")
    return "\n".join(lines)


# ── CLI 入口 ──────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="PatSeek 专利检索客户端",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # Bool 关键词检索
  python3 patseek_client.py bool "低空空域 AND 无人机" --page-size 5

  # 申请人限定
  python3 patseek_client.py bool "AP=(华为) 5G" --page-size 10

  # IPC + 日期
  python3 patseek_client.py bool "IPC=(H01M) AD>=2020" --page-size 10

  # 组合检索
  python3 patseek_client.py bool "AP=(比亚迪) IPC=(H01M) AD>=2020 NOT=(液态)"

  # 按公开号获取专利详情
  python3 patseek_client.py patent CN118658342A

  # 异步语义检索
  python3 patseek_client.py semantic "新能源汽车电池管理系统"

  # 查询任务状态
  python3 patseek_client.py task <task_id>

  # 取消任务
  python3 patseek_client.py cancel <task_id>

  # 列出任务历史
  python3 patseek_client.py tasks --limit 5
        """,
    )
    parser.add_argument(
        "--api-key",
        default=API_KEY,
        help="PatSeek API Key (或设置环境变量 PATSEEK_API_KEY)",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # bool 子命令
    bool_parser = subparsers.add_parser("bool", help="Bool 检索（支持 AND/OR、字段前缀 AP/IPC/PID/AN/AD/PD/NOT）")
    bool_parser.add_argument("query", help='检索表达式，如 "AP=(华为) IPC=(H01M) AD>=2020"')
    bool_parser.add_argument("--page", type=int, default=1, help="页码 (默认 1)")
    bool_parser.add_argument("--page-size", type=int, default=20, help="每页条数 1-100 (默认 20)")

    # patent 子命令
    patent_parser = subparsers.add_parser("patent", help="按公开号/申请号获取专利详情")
    patent_parser.add_argument("identifier", help="公开号或申请号，如 CN118658342A")

    # semantic 子命令
    semantic_parser = subparsers.add_parser("semantic", help="异步语义检索")
    semantic_parser.add_argument("query", help="技术方案或技术问题描述")
    semantic_parser.add_argument("--timeout", type=int, default=180, help="轮询超时秒数 (默认 180)")

    # task 子命令
    task_parser = subparsers.add_parser("task", help="查询异步任务状态/结果")
    task_parser.add_argument("task_id", help="任务 ID")
    task_parser.add_argument("--include-partial", action="store_true", help="是否返回运行中的部分结果")

    # cancel 子命令
    cancel_parser = subparsers.add_parser("cancel", help="取消异步任务")
    cancel_parser.add_argument("task_id", help="任务 ID")

    # tasks 子命令
    tasks_parser = subparsers.add_parser("tasks", help="列出任务历史")
    tasks_parser.add_argument("--limit", type=int, default=20, help="返回条数 1-100 (默认 20)")

    args = parser.parse_args()

    if not args.api_key:
        print("错误: 未提供 PatSeek API Key", file=sys.stderr)
        print("", file=sys.stderr)
        print("请通过以下方式之一提供 API Key：", file=sys.stderr)
        print("  1. 设置环境变量：export PATSEEK_API_KEY=ps_你的Key", file=sys.stderr)
        print("  2. 使用 --api-key 参数：python3 patseek_client.py --api-key ps_你的Key ...", file=sys.stderr)
        print("", file=sys.stderr)
        print("如何获取 API Key？", file=sys.stderr)
        print("  → 访问 https://patseek.cn 注册登录", file=sys.stderr)
        print("  → 进入「个人中心 → API Key 管理」创建新 Key", file=sys.stderr)
        print("  → Key 格式示例：ps_0931e2efa48df3aa2596de57c27d9449", file=sys.stderr)
        sys.exit(1)

    try:
        if args.command == "bool":
            result = bool_search(args.api_key, args.query, args.page, args.page_size)
            print(f"检索结果: 共 {result['total']} 条, 第 {result['current_page']}/{result['total_pages']} 页\n")
            for i, p in enumerate(result.get("patent_list", []), 1):
                print(f"--- 第 {i} 条 ---")
                print(format_patent_brief(p))
                print()

        elif args.command == "patent":
            result = get_patent(args.api_key, args.identifier)
            patents = result.get("patent_list", [])
            if not patents:
                print(f"未找到专利: {args.identifier}")
            else:
                p = patents[0]
                # 详情模式输出完整信息
                print(f"公开号:   {p.get('pid', 'N/A')}")
                print(f"申请号:   {p.get('appnum', 'N/A')}")
                print(f"名称:     {p.get('title', 'N/A')}")
                print(f"申请人:   {p.get('applicant', 'N/A')}")
                print(f"IPC:      {p.get('ipcs', 'N/A')}")
                print(f"申请日:   {p.get('appdate', 'N/A')}")
                print(f"公开日:   {p.get('pubdate', 'N/A')}")
                print(f"被引次数: {p.get('cited_cnt', 'N/A')}")
                print(f"\n摘要:\n{p.get('abstract', 'N/A')}")
                print(f"\n权利要求:\n{p.get('claims', 'N/A')}")
                print(f"\n说明书:\n{p.get('description', 'N/A')[:2000]}{'...' if len(p.get('description', '')) > 2000 else ''}")

        elif args.command == "semantic":
            results = semantic_search_async(args.api_key, args.query, args.timeout)
            print(f"\n语义检索完成，共 {len(results)} 条结果\n")
            for i, p in enumerate(results[:20], 1):
                print(f"--- 第 {i} 条 (相似度 {p.get('similarity', 'N/A')}%) ---")
                print(format_semantic_patent_brief(p))
                print()
            if len(results) > 20:
                print(f"... 还有 {len(results) - 20} 条结果未显示")

        elif args.command == "task":
            result = query_task(args.api_key, args.task_id, args.include_partial)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "cancel":
            result = cancel_task(args.api_key, args.task_id)
            print(json.dumps(result, ensure_ascii=False, indent=2))

        elif args.command == "tasks":
            result = list_tasks(args.api_key, args.limit)
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except requests.exceptions.HTTPError as e:
        resp = e.response
        status = resp.status_code
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        print(f"HTTP 错误 {status}: {body}", file=sys.stderr)
        if status == 401:
            print("", file=sys.stderr)
            print("提示: API Key 无效或已过期", file=sys.stderr)
            print("  → 请访问 https://patseek.cn 登录后检查 Key 状态", file=sys.stderr)
            print("  → 或在「个人中心 → API Key 管理」中重新创建 Key", file=sys.stderr)
        elif status == 402:
            print("", file=sys.stderr)
            print("提示: 积分不足，无法完成本次请求", file=sys.stderr)
            print("  → 请访问 https://patseek.cn 登录后充值积分", file=sys.stderr)
            print("  → 或在「个人中心」查看积分余额", file=sys.stderr)
        elif status == 403:
            print("", file=sys.stderr)
            print("提示: 该 API Key 已被禁用", file=sys.stderr)
            print("  → 请访问 https://patseek.cn 联系平台管理员", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.Timeout:
        print("请求超时", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("连接失败，请检查网络", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
