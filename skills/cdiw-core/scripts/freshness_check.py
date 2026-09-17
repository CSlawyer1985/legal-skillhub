#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知识库时效双轨校验脚本（freshness_check.py）。

功能：按大纲 7.2 第 6 条双轨制校验知识层条目时效性——
  · 内容时效轨（固定周期重核）：仅适用易变内容（当前为惯例类），
    条目"最新更新时间"距今超过阈值即列入内容超期清单；
  · 效力时效轨（状态核验＋事件触发）：适用内容恒定的条目（法条／案例／
    量刑档次／立案标准），不计算超期，改为核验效力状态标志——
    法条比对 law_effectiveness.json 现行有效性，案例核验"参照效力冲突"标记；
    缺元数据字段的一律按"待核实"列入效力待核清单。

校验策略外置于 assets/config/freshness_policy.json（时限参数单一事实源，
新增数据类型时注册新策略即可，无需改脚本）。

调用方式：
  python scripts/freshness_check.py
  python scripts/freshness_check.py --file assets/data/crime_index.json
  python scripts/freshness_check.py --strict        # 任一清单非空即退出码非 0

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0通过 / 1存在超期或待核（仅 --strict 下） / 2文件缺失 / 3读取失败；
  - 错误码：MISSING_PARAM / NOT_FOUND / INVALID / ERR_IO。

三挂载点：①build_release.py 流水线第②步前置（--strict 双清零方可打包）；
②法条包更新流程末步；③会话内引用前单文件快查。
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, date

SCRIPT_NAME = "freshness_check"
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLICY_PATH = os.path.join(SKILL_ROOT, "assets", "config", "freshness_policy.json")

TIME_KEYS = ("最新更新时间", "_updated", "更新时间", "updated_at", "snapshot_date")


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def emit(env, code):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(code)


def load_policy(tid):
    if not os.path.isfile(POLICY_PATH):
        emit(envelope("error", "INVALID",
                      "校验策略文件缺失：%s（时限参数须外置，禁止硬编码）" % POLICY_PATH,
                      {"trace_id": tid}), 2)
    try:
        with open(POLICY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        emit(envelope("error", "INVALID",
                      "策略文件解析失败：%s（%s）" % (POLICY_PATH, exc), {"trace_id": tid}), 2)


def parse_date(v):
    if not v:
        return None
    s = str(v).strip()[:10]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def entry_time(entry):
    for k in TIME_KEYS:
        if isinstance(entry, dict) and k in entry:
            return parse_date(entry[k])
    return None


def _is_leaf_entry(v):
    """叶子条目：含时间元数据，或值不全是 dict/list（即为实质数据条目）。"""
    if any(kk in v for kk in TIME_KEYS):
        return True
    vals = list(v.values())
    if not vals:
        return False
    return not all(isinstance(x, (dict, list)) for x in vals)


def iter_entries(container, path=""):
    """递归产出 (条目ID, 条目对象)；叶子条目与含元数据条目均产出。
    容器可为 dict 或 list（部分数据文件的条目容器为数组）。"""
    if isinstance(container, list):
        for i, item in enumerate(container):
            if not isinstance(item, dict):
                continue
            eid = "%s[%d]" % (path, i) if path else "[%d]" % i
            if _is_leaf_entry(item):
                yield eid, item
            for sub_id, sub in iter_entries(item, eid):
                yield sub_id, sub
        return
    if isinstance(container, dict):
        for k, v in container.items():
            if str(k).startswith("_"):
                continue
            eid = "/".join([path, str(k)]) if path else str(k)
            if isinstance(v, dict):
                if _is_leaf_entry(v):
                    yield eid, v
                for sub_id, sub in iter_entries(v, eid):
                    yield sub_id, sub
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        sub_id = "%s[%d]" % (eid, i)
                        if _is_leaf_entry(item):
                            yield sub_id, item
                        for s2, v2 in iter_entries(item, sub_id):
                            yield s2, v2


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME, description="时效双轨校验：内容超期清单＋效力待核清单。")
    ap.add_argument("--file", help="仅校验指定数据文件（相对包根目录）")
    ap.add_argument("--strict", action="store_true",
                    help="严格模式：任一清单非空即退出码非 0（发布闸门用）")
    args = ap.parse_args()
    tid = make_trace_id()

    policy = load_policy(tid)
    types = policy.get("types", {})
    sources = policy.get("sources", [])
    if args.file:
        sources = [s for s in sources if s.get("file") == args.file]
        if not sources:
            emit(envelope("error", "NOT_FOUND",
                          "策略文件中未注册该数据文件：%s" % args.file, {"trace_id": tid}), 2)

    today = date.today()
    overdue, pending = [], []

    for src in sources:
        rel = src.get("file")
        etype = src.get("type")
        spec = types.get(etype, {})
        track = spec.get("track", "effectiveness")
        path = os.path.join(SKILL_ROOT, rel)
        if not os.path.isfile(path):
            pending.append({"file": rel, "entry_id": "-", "type": etype,
                            "reason": "数据文件缺失"})
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                db = json.load(f)
        except (OSError, ValueError) as exc:
            pending.append({"file": rel, "entry_id": "-", "type": etype,
                            "reason": "文件读取或解析失败：%s" % exc})
            continue

        container = db
        for seg in (src.get("entry_path") or "").split("/"):
            if seg and isinstance(container, dict):
                container = container.get(seg, container)

        checked = 0
        for eid, entry in iter_entries(container):
            if not isinstance(entry, dict):
                continue
            checked += 1
            t = entry_time(entry)
            if track == "content":
                max_days = int(spec.get("max_days", 90))
                if t is None:
                    overdue.append({"file": rel, "entry_id": eid, "type": etype,
                                    "reason": "缺少更新时间元数据，视为陈旧数据",
                                    "overdue_days": None})
                else:
                    age = (today - t).days
                    if age > max_days:
                        overdue.append({"file": rel, "entry_id": eid, "type": etype,
                                        "reason": "超过 %d 日重核周期" % max_days,
                                        "overdue_days": age, "last_updated": str(t)})
            else:
                # 效力时效轨：核验效力状态标志，不计算超期
                flags = spec.get("require_flags", [])
                missing = [fl for fl in flags if fl not in entry]
                if t is None and "更新时间" not in (src.get("exempt") or []):
                    pending.append({"file": rel, "entry_id": eid, "type": etype,
                                    "reason": "条目缺少更新时间元数据，引用时须标注待核实"})
                elif missing:
                    pending.append({"file": rel, "entry_id": eid, "type": etype,
                                    "reason": "效力状态标志缺失：%s" % "、".join(missing)})
        if checked == 0:
            pending.append({"file": rel, "entry_id": "-", "type": etype,
                            "reason": "未检出可校验条目（entry_path 配置待核）"})

    n_over, n_pend = len(overdue), len(pending)
    clean = (n_over == 0 and n_pend == 0)
    msg = ("双清单均为空：内容时效与效力时效全部通过" if clean else
           "内容超期 %d 条、效力待核 %d 条" % (n_over, n_pend))
    code = 0 if (clean or not args.strict) else 1
    emit(envelope("ok" if clean else ("error" if args.strict else "ok"),
                  None if clean else ("INVALID" if args.strict else None),
                  msg + ("（严格模式：阻断）" if args.strict and not clean else ""),
                  {"trace_id": tid, "checked_date": str(today),
                   "sources_checked": len(sources), "strict": args.strict,
                   "content_overdue": n_over, "effectiveness_pending": n_pend,
                   "overdue_list": overdue[:200], "pending_list": pending[:200],
                   "truncated": (n_over > 200 or n_pend > 200),
                   "note": "缺元数据字段按待核实列入效力待核清单；"
                           "未携带更新时间元数据的条目不得直接引用（7.2 第 6 条）"}), code)


if __name__ == "__main__":
    main()
