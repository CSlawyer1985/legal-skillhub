#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利预审自检 - IPC 白名单精确匹配（步骤 2 受理前提）
加载 references/ipc_whitelist.json，对任一保护中心做候选 IPC 主分类小类的精确匹配。

用法:
  python ipc_match.py --center 北京 --ipc H01M
  python ipc_match.py --center 73 --ipc G06F
  python ipc_match.py --center 江苏 --ipc G06F --verbose
  python ipc_match.py --center 深圳 --info        # 显示该中心白名单信息

匹配档位（match_level）:
  exact_full       候选 IPC 在【完整】白名单中命中 -> 高置信通过
  exact_full_miss  候选 IPC 不在【完整】白名单   -> 高置信一票否决
  exact_partial    候选 IPC 在【部分】白名单中命中 -> 可能漏判，建议核对官方
  exact_partial_miss 候选 IPC 不在【部分】白名单 -> 清单不全，结论不确定
  unknown          无官方 IPC 数据（派生/未公布）-> 退回产业领域粗匹配 + 用户确认
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(HERE, "..", "references", "ipc_whitelist.json")


def load():
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def resolve_center(data, center):
    """按 id（int 或数字串）或名称子串解析中心。"""
    # 数字 id
    try:
        cid = int(center)
        for c in data["centers"]:
            if c["id"] == cid:
                return c
    except ValueError:
        pass
    # 名称子串（不区分大小写）
    key = center.lower()
    hits = [c for c in data["centers"] if key in c["name"].lower()]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        names = "；".join(f"{h['id']}:{h['name']}" for h in hits)
        raise SystemExit(f"中心名『{center}』命中多个：{names}，请更精确或用 id")
    raise SystemExit(f"未找到中心：{center}")


def match(data, center, ipc, verbose=False):
    c = resolve_center(data, center)
    ipc = ipc.strip().upper()
    subs = set(c["subclasses"])
    out = {
        "center_id": c["id"],
        "center": c["name"],
        "industry": c["industry"],
        "confidence": c["confidence"],
        "list_partial": c["partial"],
        "candidate": ipc,
    }
    if not subs:
        out.update({
            "matched": None,
            "match_level": "unknown",
            "message": f"该中心无官方 IPC 白名单数据（{c['confidence']}），退回『产业领域粗匹配 + 用户确认』。产业领域：{c['industry']}；来源：{c['source']}",
        })
        return out

    if ipc in subs:
        if c["partial"]:
            out.update({
                "matched": True,
                "match_level": "exact_partial",
                "message": f"候选 {ipc} 命中【部分】白名单（仅收录 {len(subs)}/{c['count'] or '?'} 个小类），可能因清单不全漏判，建议核对官方：{c['source']}",
            })
        else:
            out.update({
                "matched": True,
                "match_level": "exact_full",
                "message": f"候选 {ipc} 命中【完整】白名单（{len(subs)} 个小类），高置信通过受理前提。",
            })
    else:
        if c["partial"]:
            out.update({
                "matched": False,
                "match_level": "exact_partial_miss",
                "message": f"候选 {ipc} 不在【部分】白名单（收录 {len(subs)}/{c['count'] or '?'}）。因清单不全，结论不确定；可能为真不符（一票否决）或数据缺失，须核对官方：{c['source']}",
            })
        else:
            out.update({
                "matched": False,
                "match_level": "exact_full_miss",
                "message": f"候选 {ipc} 不在【完整】白名单（共 {len(subs)} 个小类），高置信『不在产业领域/IPC 白名单』，触发一票否决，应终止深度检查。",
            })
    if verbose:
        out["source"] = c["source"]
        out["note"] = c.get("note", "")
    return out


def show_info(data, center):
    c = resolve_center(data, center)
    print(f"#{c['id']} {c['name']}")
    print(f"  产业领域 : {c['industry']}")
    print(f"  置信度   : {c['confidence']}  partial={c['partial']}  count={c['count']}")
    print(f"  已收录小类数: {len(c['subclasses'])}")
    print(f"  来源     : {c['source']}")
    if c["subclasses"]:
        preview = " ".join(c["subclasses"][:40])
        print(f"  小类预览 : {preview}{' …' if len(c['subclasses'])>40 else ''}")


def main():
    ap = argparse.ArgumentParser(description="专利预审 IPC 白名单精确匹配")
    ap.add_argument("--center", required=True, help="保护中心（名称子串或 id）")
    ap.add_argument("--ipc", help="候选 IPC 主分类小类，如 H01M")
    ap.add_argument("--info", action="store_true", help="仅显示该中心白名单信息")
    ap.add_argument("--verbose", action="store_true", help="附带来源与备注")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    data = load()
    if args.info:
        show_info(data, args.center)
        return
    if not args.ipc:
        ap.error("需提供 --ipc 或 --info")
    res = match(data, args.center, args.ipc, args.verbose)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        verdict = {True: "✅ 命中", False: "❌ 不命中", None: "⚠️ 未知"}[res["matched"]]
        print(f"[{verdict}] {res['center']}  <-  {res['candidate']}  ({res['match_level']})")
        print(f"    {res['message']}")


if __name__ == "__main__":
    main()
