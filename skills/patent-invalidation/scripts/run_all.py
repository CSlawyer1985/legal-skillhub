#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py —— M1（目标专利画像）+ M3（证据检索）一键管道
==========================================================

本脚本把原本散在 `invalidation_search.py` / `patseek_client.py` 里的多个
步骤串成一条管道，输入目标专利号 + 优先权日，输出一份结构化 JSON 报告
（含画像 + 现有技术命中 + 语义补盲命中 + 抵触/重复命中 + 公开日核验），
供 M4–M11（理由组合 / 特征映射 / 论证撰写 / 证据组织 / 请求书 / 程序
策略）后续使用。

输出 JSON 结构:
    {
      "meta": {"tool":"run_all","version":"1.0.6","target":...},
      "M1_profile": {<目标专利画像>},
      "M3_prior_art": {
        "bool_query":"...",
        "results":[{"pid":...,"title":...,"pubdate":...,"on_time":True/False, ...}],
        "total":N
      },
      "M3_semantic": {
        "query":"...",
        "results":[{"pid":...,"similarity":...,"pubdate":...,"on_time":True/False, ...}],
        "total":N
      },
      "M3_conflict": {  # 抵触申请（仅传 --applicant 时存在）
        "applicant":"...",
        "query":"...",
        "results":[...],
        "total":N
      },
      "M3_duplicate": {  # 重复授权
        "applicant":"...",
        "query":"...",
        "results":[...],
        "total":N
      },
      "summary": {
        "prior_art_candidates": [{"pid":...,"title":...,"pubdate":...,"on_time":True}, ...],
        "errors": [...]
      }
    }

时间死线: 公开日 < 优先权日（核心约束），标记 on_time 字段
"高度盖然性"：对 on_time=True 且 similarity 高（语义）或 IPC 命中（Bool）
的命中，标记 strong=True，便于 M4 选证据。

依赖:
    - PATSEEK_API_KEY（环境变量 / .env / --api-key）
    - requests

用法:
    # 必传
    python run_all.py --target-patent CN118658342A --priority-date 20150310
    # 可选
    python run_all.py --target-patent CN118658342A --priority-date 20150310 \\
        --ipc G02B --features "光学减振;测量装置" \\
        --applicant "华为" \\
        --prior-art-pages 5 --semantic-pages 20 \\
        --out report.json
"""
import argparse
import json
import os
import sys
from datetime import datetime
from typing import Optional

# 加载 .env（复用 patseek_client 的实现）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from patseek_client import (
        _load_dotenv, get_patent, bool_search, semantic_search_async
    )
    _load_dotenv()
except Exception as e:
    print(f"[warn] patseek_client 加载失败: {e}", file=sys.stderr)
    _load_dotenv = lambda: None  # noqa: E731
    get_patent = bool_search = semantic_search_async = None  # type: ignore


def norm_date(d: str) -> str:
    """YYYY-MM-DD / YYYY/MM/DD / YYYYMMDD → YYYYMMDD"""
    return d.replace("-", "").replace("/", "")[:8]


def on_time(pubdate: str, prio: str) -> bool:
    """公开日 < 优先权日？"""
    if not pubdate or not prio:
        return False
    p = norm_date(str(pubdate))
    return bool(p) and p < prio


def build_prior_art_query(features: str, ipc: str, prio: str) -> tuple[str, list[str]]:
    """构造现有技术 Bool 检索式（每个特征原词成组 + IPC + 时间死线）。"""
    feats = [f.strip() for f in (features or "").split(";") if f.strip()]
    feat_groups = " ".join(f"({f})" for f in feats)
    q = feat_groups
    if ipc:
        q += f" IPC=({ipc})"
    q += f" PD<{prio}"
    return q, feats


def build_prior_art_query_loose(features: str, ipc: str, prio: str) -> str:
    """宽松检索式（特征 OR + IPC + 时间死线）。

    当严格 AND 检索返回 0（特征过约束）时自动降级使用，避免冷门领域漏检。
    仅保留时间死线 PD<优先权日（核心硬约束），特征改为 OR 任一命中。
    """
    feats = [f.strip() for f in (features or "").split(";") if f.strip()]
    feat_or = " OR ".join(f"({f})" for f in feats) if feats else ""
    q = f"({feat_or})" if feat_or else ""
    if ipc:
        q += f" IPC=({ipc})"
    q += f" PD<{prio}"
    return q


def build_conflict_query(applicant: str, features: list[str], appdate: str) -> str:
    """构造抵触申请检索式：AP + features + AD<目标申请日 + PD>目标申请日。"""
    feat_groups = " ".join(f"({f})" for f in features)
    return f"AP=({applicant}) {feat_groups} AD<{appdate} PD>{appdate}"


def build_duplicate_query(applicant: str, features: list[str], appdate: str) -> str:
    """构造重复授权检索式：AP + features + 相近年份范围。"""
    feat_groups = " ".join(f"({f})" for f in features)
    yr = appdate[:4]
    return f"AP=({applicant}) {feat_groups} AD={int(yr) - 2}-{int(yr) + 2}"


def make_api_key_arg(api_key: str) -> dict:
    """统一处理 API key 优先级。"""
    return {"api_key": api_key} if api_key else {}


def run_pipeline(
    target_patent: str,
    priority_date: str,
    ipc: str = "",
    features: str = "",
    applicant: str = "",
    prior_art_pages: int = 1,
    semantic_pages: int = 20,
    api_key: str = "",
    out_path: str = "",
    verbose: bool = True,
) -> dict:
    """M1+M3 一键管道，输出结构化报告。"""
    prio = norm_date(priority_date)
    if not api_key:
        api_key = os.environ.get("PATSEEK_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "未提供 API Key。请通过 --api-key、$PATSEEK_API_KEY 或 .env 文件提供。"
        )
    if get_patent is None or bool_search is None or semantic_search_async is None:
        raise RuntimeError("patseek_client 未正确加载，请检查 scripts/ 目录与 requests 库。")

    report = {
        "meta": {
            "tool": "run_all",
            "version": "1.0.6",
            "target": target_patent,
            "priority_date": prio,
            "ipc": ipc,
            "features": features,
            "applicant": applicant,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        "M1_profile": None,
        "M3_prior_art": {"query": "", "query_mode": "strict", "results": [], "total": 0},
        "M3_semantic": {"query": "", "results": [], "total": 0},
        "M3_conflict": None,
        "M3_duplicate": None,
        "summary": {
            "prior_art_candidates": [],
            "errors": [],
        },
    }

    # ── M1: 目标专利画像 ──
    if verbose:
        print(f"[1/N] 目标专利画像 (patent {target_patent})...")
    try:
        prof = get_patent(api_key, target_patent)
        patents = prof.get("patent_list", [])
        if patents:
            p0 = patents[0]
            report["M1_profile"] = {
                "pid": p0.get("pid"),
                "appnum": p0.get("appnum"),
                "title": p0.get("title"),
                "applicant": p0.get("applicant"),
                "ipcs": p0.get("ipcs"),
                "appdate": p0.get("appdate"),
                "pubdate": p0.get("pubdate"),
                "abstract": p0.get("abstract", "")[:500],
                "claims_preview": (p0.get("claims", "") or "")[:1000],
                "cited_cnt": p0.get("cited_cnt"),
            }
            if verbose:
                print(f"       ✓ 公开号 {p0.get('pid')} | 申请日 {p0.get('appdate')} | 公开日 {p0.get('pubdate')} | 申请人 {p0.get('applicant')}")
    except Exception as e:
        report["summary"]["errors"].append(f"M1 profile: {e}")
        if verbose:
            print(f"       ✗ {e}", file=sys.stderr)

    # ── M3: 现有技术 Bool 检索 ──
    q_prior, feats = build_prior_art_query(features, ipc, prio)
    report["M3_prior_art"]["query"] = q_prior
    if verbose:
        print(f"[2/N] 现有技术 Bool 检索（{len(feats)} 特征）...")
        print(f"       检索式: {q_prior}")
    try:
        # v1.0.9: 按 --prior-art-pages 翻页聚合（此前仅取 page=1，参数未生效）
        results = []
        total = 0
        page_size = 20
        max_pages = max(1, prior_art_pages)
        for pg in range(1, max_pages + 1):
            r = bool_search(api_key, q_prior, page=pg, page_size=page_size)
            plist = r.get("patent_list", [])
            total = r.get("total", total)
            if not plist:
                break
            for p in plist:
                pd = str(p.get("pubdate", ""))
                ok = on_time(pd, prio)
                results.append({
                    "pid": p.get("pid"),
                    "title": p.get("title"),
                    "applicant": p.get("applicant"),
                    "appdate": p.get("appdate"),
                    "pubdate": pd,
                    "ipcs": p.get("ipcs"),
                    "on_time": ok,
                    "strong": ok and (not ipc or ipc in (p.get("ipcs") or "")),
                })
            if len(plist) < page_size:
                break  # 已到末页
        # v1.0.9: 严格 AND 返回 0 时自动降级为 OR 宽松式（避免冷门领域过约束漏检）
        query_mode = "strict"
        if total == 0 and feats:
            q_loose = build_prior_art_query_loose(features, ipc, prio)
            if verbose:
                print(f"       [降级] 严格式命中 0，改用宽松式(OR): {q_loose}")
            r = bool_search(api_key, q_loose, page=1, page_size=page_size)
            plist = r.get("patent_list", [])
            total = r.get("total", 0)
            query_mode = "loose"
            report["M3_prior_art"]["query"] = f"{q_prior}  [降级→] {q_loose}"
            for p in plist:
                pd = str(p.get("pubdate", ""))
                ok = on_time(pd, prio)
                results.append({
                    "pid": p.get("pid"),
                    "title": p.get("title"),
                    "applicant": p.get("applicant"),
                    "appdate": p.get("appdate"),
                    "pubdate": pd,
                    "ipcs": p.get("ipcs"),
                    "on_time": ok,
                    "strong": ok and (not ipc or ipc in (p.get("ipcs") or "")),
                })
        report["M3_prior_art"]["results"] = results
        report["M3_prior_art"]["total"] = total
        report["M3_prior_art"]["query_mode"] = query_mode
        if verbose:
            print(f"       ✓ 命中 {total} 条（{sum(1 for x in results if x['on_time'])} 条 on_time，模式={query_mode}）")
    except Exception as e:
        report["summary"]["errors"].append(f"M3 bool: {e}")
        if verbose:
            print(f"       ✗ {e}", file=sys.stderr)

    # ── M3: 语义补盲 ──
    if feats:
        sem_q = " ".join(feats)
        report["M3_semantic"]["query"] = sem_q
        if verbose:
            print(f"[3/N] 语义补盲（异步，可能等 30–180s）...")
        try:
            res = semantic_search_async(api_key, sem_q, timeout=180)
            results = []
            for p in res[:semantic_pages]:
                pd = str(p.get("pubdate", ""))
                ok = on_time(pd, prio)
                item = {
                    "pid": p.get("pid"),
                    "title": p.get("title"),
                    "similarity": p.get("similarity"),
                    "appdate": p.get("appdate"),
                    "pubdate": pd,
                    "applicant": p.get("applicant"),
                    "on_time": ok,
                    "strong": ok and (p.get("similarity") or 0) >= 80,
                }
                results.append(item)
            report["M3_semantic"]["results"] = results
            report["M3_semantic"]["total"] = len(res)
            if verbose:
                print(f"       ✓ 命中 {len(res)} 条（{sum(1 for x in results if x['on_time'])} 条 on_time）")
        except Exception as e:
            report["summary"]["errors"].append(f"M3 semantic: {e}")
            if verbose:
                print(f"       ✗ {e}", file=sys.stderr)

    # ── M3: 抵触申请 + 重复授权（仅传 --applicant 时）──
    if applicant and feats:
        # 目标申请日优先从画像取，否则用优先权日兜底
        appdate = ""
        if report["M1_profile"]:
            appdate = norm_date(str(report["M1_profile"].get("appdate", "")))
        if not appdate:
            appdate = prio
        if verbose:
            print(f"[4/N] 抵触申请 / 重复授权专项（AP={applicant}）...")

        # 抵触申请
        q_dk = build_conflict_query(applicant, feats, appdate)
        report["M3_conflict"] = {"applicant": applicant, "query": q_dk, "results": [], "total": 0}
        try:
            r = bool_search(api_key, q_dk, page=1, page_size=20)
            results = []
            for p in r.get("patent_list", []):
                pd = str(p.get("pubdate", ""))
                ad = str(p.get("appdate", ""))
                # 抵触：申请日早于目标 + 公开日晚于目标
                is_conflict = norm_date(ad) < appdate and norm_date(pd) > appdate
                results.append({
                    "pid": p.get("pid"),
                    "title": p.get("title"),
                    "appdate": ad,
                    "pubdate": pd,
                    "is_conflict": is_conflict,
                })
            report["M3_conflict"]["results"] = results
            report["M3_conflict"]["total"] = r.get("total", 0)
            if verbose:
                print(f"       ✓ 抵触：{report['M3_conflict']['total']} 条（{sum(1 for x in results if x['is_conflict'])} 条 true conflict）")
        except Exception as e:
            report["summary"]["errors"].append(f"M3 conflict: {e}")
            if verbose:
                print(f"       ✗ {e}", file=sys.stderr)

        # 重复授权
        q_dup = build_duplicate_query(applicant, feats, appdate)
        report["M3_duplicate"] = {"applicant": applicant, "query": q_dup, "results": [], "total": 0}
        try:
            r = bool_search(api_key, q_dup, page=1, page_size=20)
            results = []
            for p in r.get("patent_list", []):
                results.append({
                    "pid": p.get("pid"),
                    "title": p.get("title"),
                    "appdate": p.get("appdate"),
                    "pubdate": p.get("pubdate"),
                    "ipcs": p.get("ipcs"),
                })
            report["M3_duplicate"]["results"] = results
            report["M3_duplicate"]["total"] = r.get("total", 0)
            if verbose:
                print(f"       ✓ 重复授权：{report['M3_duplicate']['total']} 条")
        except Exception as e:
            report["summary"]["errors"].append(f"M3 duplicate: {e}")
            if verbose:
                print(f"       ✗ {e}", file=sys.stderr)

    # ── 汇总：候选现有技术（仅 on_time）──
    candidates = []
    for src_label, src in [
        ("bool", report["M3_prior_art"]["results"]),
        ("semantic", report["M3_semantic"]["results"]),
    ]:
        for x in src:
            if x.get("on_time"):
                x2 = dict(x)
                x2["source"] = src_label
                candidates.append(x2)
    # 按 strong 优先 + similarity 排序
    candidates.sort(key=lambda x: (x.get("strong", False), x.get("similarity", 0) or 0), reverse=True)
    report["summary"]["prior_art_candidates"] = candidates[:50]  # 上限 50

    if verbose:
        print(f"\n[Summary]")
        print(f"  目标专利        : {target_patent} (优先权日 {prio})")
        print(f"  现有技术候选    : {len(candidates)} 条 (strong={sum(1 for x in candidates if x.get('strong'))})")
        print(f"  语义补盲命中    : {report['M3_semantic']['total']} 条")
        if report["M3_conflict"]:
            print(f"  抵触申请命中    : {report['M3_conflict']['total']} 条 ({sum(1 for x in report['M3_conflict']['results'] if x['is_conflict'])} true)")
        if report["M3_duplicate"]:
            print(f"  重复授权命中    : {report['M3_duplicate']['total']} 条")
        if report["summary"]["errors"]:
            print(f"  错误            : {len(report['summary']['errors'])} 个（见 errors 字段）")

    # ── 输出 ──
    if out_path:
        os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        if verbose:
            print(f"\n  报告已写入: {out_path}")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(
        description="M1（目标专利画像）+ M3（证据检索）一键管道",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_all.py --target-patent CN118658342A --priority-date 20150310 \\
      --ipc G02B --features "光学减振;测量装置" \\
      --applicant "华为" \\
      --out report.json
        """,
    )
    ap.add_argument("--target-patent", required=True, help="目标专利公开号")
    ap.add_argument("--priority-date", required=True, help="目标专利优先权日 YYYYMMDD / YYYY-MM-DD")
    ap.add_argument("--ipc", default="", help="IPC 前 4 位（用于现有技术 Bool 检索）")
    ap.add_argument("--features", default="", help='核心技术特征，分号分隔，如 "光学减振;测量装置"')
    ap.add_argument("--applicant", default="", help="目标专利申请人（用于抵触/重复检索）")
    ap.add_argument("--api-key", default=os.environ.get("PATSEEK_API_KEY", ""), help="PatSeek API Key")
    ap.add_argument("--prior-art-pages", type=int, default=1, help="现有技术检索页数（默认 1，每页 20 条）")
    ap.add_argument("--semantic-pages", type=int, default=20, help="语义检索最多取前 N 条（默认 20）")
    ap.add_argument("--out", default="", help="输出 JSON 报告路径（默认打印到 stdout）")
    ap.add_argument("--quiet", action="store_true", help="静默模式（仅打印报告路径）")
    args = ap.parse_args()

    try:
        run_pipeline(
            target_patent=args.target_patent,
            priority_date=args.priority_date,
            ipc=args.ipc,
            features=args.features,
            applicant=args.applicant,
            prior_art_pages=args.prior_art_pages,
            semantic_pages=args.semantic_pages,
            api_key=args.api_key,
            out_path=args.out,
            verbose=not args.quiet,
        )
        return 0
    except RuntimeError as e:
        print(f"[fatal] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
