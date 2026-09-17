#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""案件状态副本与回滚脚本（backup_manager.py）。

功能：管理 case_status.md 的写入前副本与回滚，承载大纲 8.4.1 的
「写入前自动留存上一版本副本、按日滚动保留近 N 日、回滚须经承办律师确认」规则。

动作：
  create   写入前留存副本（按日滚动，保留期由 --retention-days 控制）
  list     列出当前可回滚副本
  restore  回滚到指定日期副本（须 --confirm，回滚前先留存当前版）

调用方式：
  python scripts/backup_manager.py --case-dir <案件文件夹> --action create
  python scripts/backup_manager.py --case-dir <案件文件夹> --action list
  python scripts/backup_manager.py --case-dir <案件文件夹> --action restore \
      --target 2026-08-31 --confirm
  python scripts/backup_manager.py --case-dir <案件文件夹> --action create --retention-days 7

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2路径或数据缺失 / 3操作失败；
  - 错误码：MISSING_PARAM / NOT_FOUND / INVALID / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timedelta

SCRIPT_NAME = "backup_manager"
STATUS_NAME = "case_status.md"
BAK_DIR_NAME = "backups"
VALID_ACTIONS = ("create", "list", "restore")


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def emit(env, code):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(code)


def today():
    return datetime.now().strftime("%Y-%m-%d")


def bak_root(case_dir):
    return os.path.join(case_dir, BAK_DIR_NAME)


def action_create(case_dir, retention_days, tid):
    src = os.path.join(case_dir, STATUS_NAME)
    if not os.path.isfile(src):
        emit(envelope("error", "NOT_FOUND",
                      "状态文件不存在，无需留存副本：%s" % src, {"trace_id": tid}), 2)
    bdir = bak_root(case_dir)
    os.makedirs(bdir, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    dst = os.path.join(bdir, "case_status_%s.bak" % stamp)
    try:
        shutil.copy2(src, dst)
    except OSError as exc:
        emit(envelope("error", "ERR_IO", "副本写入失败：%s（%s）" % (dst, exc),
                      {"trace_id": tid}), 3)

    # 按日滚动清理：保留近 retention_days 日
    cutoff = (datetime.now() - timedelta(days=int(retention_days))).strftime("%Y-%m-%d")
    removed = []
    for fn in sorted(os.listdir(bdir)):
        if not fn.startswith("case_status_") or not fn.endswith(".bak"):
            continue
        fdate = fn[len("case_status_"):][:10]
        if fdate < cutoff:
            try:
                os.remove(os.path.join(bdir, fn))
                removed.append(fn)
            except OSError:
                pass

    return {"trace_id": tid, "action": "create", "backup_file": dst,
            "retention_days": retention_days, "cutoff_date": cutoff,
            "removed": removed, "current_effective": today()}


def action_list(case_dir, tid):
    bdir = bak_root(case_dir)
    if not os.path.isdir(bdir):
        emit(envelope("error", "NOT_FOUND", "副本目录不存在：%s" % bdir,
                      {"trace_id": tid, "backups": []}), 2)
    items = []
    for fn in sorted(os.listdir(bdir), reverse=True):
        if fn.startswith("case_status_") and fn.endswith(".bak"):
            p = os.path.join(bdir, fn)
            items.append({"file": fn, "date": fn[len("case_status_"):][:10],
                          "size": os.path.getsize(p),
                          "mtime": datetime.fromtimestamp(os.path.getmtime(p)).isoformat()})
    msg = "可回滚副本 %d 份" % len(items) if items else "无可回滚副本"
    return {"trace_id": tid, "action": "list", "count": len(items),
            "backups": items, "message_note": msg}


def action_restore(case_dir, target, confirm, tid):
    if not confirm:
        emit(envelope("error", "INVALID",
                      "回滚须经承办律师确认：请追加 --confirm 参数（对应大纲 8.4.1"
                      "经承办律师确认后回滚）", {"trace_id": tid}), 3)
    bdir = bak_root(case_dir)
    if not os.path.isdir(bdir):
        emit(envelope("error", "NOT_FOUND", "副本目录不存在：%s" % bdir, {"trace_id": tid}), 2)
    cands = sorted([f for f in os.listdir(bdir)
                    if f.startswith("case_status_%s" % target) and f.endswith(".bak")])
    if not cands:
        emit(envelope("error", "NOT_FOUND",
                      "无可回滚副本：%s（先用 --action list 查看可回滚日期）" % target,
                      {"trace_id": tid}), 2)
    chosen = os.path.join(bdir, cands[-1])
    src = os.path.join(case_dir, STATUS_NAME)

    # 回滚前先留存当前版
    pre_bak = None
    if os.path.isfile(src):
        os.makedirs(bdir, exist_ok=True)
        pre_bak = os.path.join(bdir, "case_status_pre-restore-%s.bak"
                               % datetime.now().strftime("%Y-%m-%d-%H%M%S"))
        try:
            shutil.copy2(src, pre_bak)
        except OSError as exc:
            emit(envelope("error", "ERR_IO", "回滚前留存当前版失败：%s" % exc,
                          {"trace_id": tid}), 3)
    try:
        shutil.copy2(chosen, src)
    except OSError as exc:
        emit(envelope("error", "ERR_IO", "回滚失败：%s" % exc, {"trace_id": tid}), 3)

    return {"trace_id": tid, "action": "restore", "restored_from": chosen,
            "pre_restore_backup": pre_bak, "current_effective": today(),
            "note": "回滚动作须记入审计日志（logs/audit_log.jsonl）"}


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME, description="案件状态副本与回滚（create／list／restore）。")
    ap.add_argument("--case-dir", required=True, help="案件文件夹路径")
    ap.add_argument("--action", required=True, choices=VALID_ACTIONS, help="动作")
    ap.add_argument("--target", help="restore 目标副本日期（YYYY-MM-DD）")
    ap.add_argument("--retention-days", type=int, default=3, help="副本保留天数，默认 3")
    ap.add_argument("--confirm", action="store_true", help="确认执行回滚")
    args = ap.parse_args()
    tid = make_trace_id()

    if not os.path.isdir(args.case_dir):
        emit(envelope("error", "NOT_FOUND", "案件文件夹不存在：%s" % args.case_dir,
                      {"trace_id": tid}), 2)

    if args.action == "create":
        data = action_create(args.case_dir, args.retention_days, tid)
        emit(envelope("ok", None, "副本已留存：%s" % os.path.basename(data["backup_file"]), data), 0)
    elif args.action == "list":
        data = action_list(args.case_dir, tid)
        emit(envelope("ok", None, data["message_note"], data), 0)
    else:
        if not args.target:
            emit(envelope("error", "MISSING_PARAM",
                          "restore 须指定 --target 目标日期", {"trace_id": tid}), 1)
        data = action_restore(args.case_dir, args.target, args.confirm, tid)
        emit(envelope("ok", None, "已回滚至 %s" % args.target, data), 0)


if __name__ == "__main__":
    main()
