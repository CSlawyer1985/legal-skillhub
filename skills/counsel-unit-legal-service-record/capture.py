#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
顾问单位法律服务工作记录 - 对话自动捕获脚本 (capture.py)
由 AI 助手在 WorkBuddy 对话中调用：把"本次对话完成的顾问单位法律服务工作"
提炼成的结构化条目批量写入 data/records.json。

设计要点：
- 仅依赖标准库（json/os/uuid/fcntl），不引入 docx/openpyxl，启动快、稳健。
- 与 server.py 共用同一份 data/records.json 与同一把 .write.lock 文件锁：本脚本在持锁期间完成「读取→去重→追加→原子写」，server.py 同样在持锁期间完成「读取→修改→原子写」，跨进程互斥、无死锁。
- 支持单条（命令行参数）、批量（--json / --file / 管道 stdin）两种输入。
- 默认去重：相同 (单位, 日期, 工作内容) 已存在则跳过，防止 AI 重复触发重复记。

用法示例：
  单条：
    python capture.py --unit "浙江XX公司" --date 2026-08-19 \
        --content "审查《品牌授权协议》并提出修改意见" --hours 3 --followup "待客户确认" --lawyer "X律师"

  批量（管道）：
    echo '[{"unit":"A","date":"2026-08-19","content":"...","hours":2},
           {"unit":"A","date":"2026-08-19","content":"...","hours":1}]' | python capture.py

  批量（文件）：
    python capture.py --file /tmp/batch.json

  预览不写盘：
    python capture.py --dry-run --json '[{...}]'
"""
import os
import sys
import json
import uuid
import fcntl
import argparse
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "records.json")
LOCK_FILE = os.path.join(DATA_DIR, ".write.lock")
DEFAULT_LAWYER = "X律师"


# --------------------------------------------------------------------------- #
# 数据存取（轻量版，仅标准库；与 server.py 保持同路径、同结构）
# --------------------------------------------------------------------------- #
def _load_data():
    if not os.path.exists(DATA_FILE):
        return {"units": [], "records": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"units": [], "records": []}
        data.setdefault("units", [])
        data.setdefault("records", [])
        return data
    except Exception:
        return {"units": [], "records": []}


def _now_iso():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _atomic_save(data):
    """原子写（不加锁）：写临时文件后 os.replace。锁由调用方持有。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = DATA_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DATA_FILE)


def _commit(valid, no_dedup):
    """
    在单一文件锁内完成：load -> 去重 -> 追加 -> 原子写。
    避免同一进程对同一文件重复 flock 造成死锁。
    返回 (added, skipped, total)。
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOCK_FILE, "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        data = _load_data()
        existing = data.get("records", [])
        added, skipped = [], []
        for v in valid:
            key = (v["unit"], v["date"], v["content"])
            if not no_dedup and any(
                (e.get("unit"), e.get("date"), e.get("content")) == key for e in existing
            ):
                skipped.append(v)
                continue
            data["records"].append(v)
            if v["unit"] and v["unit"] not in data["units"]:
                data["units"].append(v["unit"])
            added.append(v)
        if added:
            _atomic_save(data)
        return added, skipped, len(data["records"])


# --------------------------------------------------------------------------- #
# 解析 / 校验
# --------------------------------------------------------------------------- #
def _normalize_records(args, raw_list):
    """把命令行参数 / JSON 对象 / JSON 数组统一成记录 dict 列表。"""
    recs = []
    if raw_list is not None:
        if isinstance(raw_list, dict):
            raw_list = [raw_list]
        if not isinstance(raw_list, list):
            raise ValueError("JSON 顶层必须是对象或数组")
        for item in raw_list:
            if not isinstance(item, dict):
                raise ValueError("每条记录必须是对象")
            recs.append(item)
    else:
        if args.unit or args.content:
            recs.append({
                "unit": args.unit or "",
                "date": args.date or "",
                "content": args.content or "",
                "hours": args.hours,
                "followup": args.followup or "",
                "remark": args.remark or "",
                "lawyer": args.lawyer or "",
            })
    return recs


def _validate(rec, default_lawyer, default_source="对话自动捕获"):
    unit = (rec.get("unit") or "").strip()
    date = (rec.get("date") or "").strip()
    content = (rec.get("content") or "").strip()
    if not unit:
        raise ValueError("顾问单位不能为空")
    if not date:
        raise ValueError("日期不能为空（格式 YYYY-MM-DD）")
    if not content:
        raise ValueError("律师工作内容不能为空")
    try:
        hours = float(rec.get("hours") or 0)
    except Exception:
        raise ValueError("工作时间必须为数字（小时）")
    if hours < 0:
        raise ValueError("工作时间不能为负数")
    source = (rec.get("source") or "").strip() or default_source or "对话自动捕获"
    remark = (rec.get("remark") or "").strip() or ("来源：" + source)
    return {
        "id": uuid.uuid4().hex,
        "unit": unit,
        "date": date,
        "content": content,
        "hours": round(hours, 2),
        "followup": (rec.get("followup") or "").strip(),
        "remark": remark,
        "lawyer": (rec.get("lawyer") or "").strip() or default_lawyer,
        "source": source,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


def main():
    ap = argparse.ArgumentParser(description="顾问单位法律服务工作记录 - 对话自动捕获 / 用户指定归入")
    ap.add_argument("--unit", help="顾问单位（单条）")
    ap.add_argument("--date", help="日期 YYYY-MM-DD（单条）")
    ap.add_argument("--content", help="律师工作内容（单条）")
    ap.add_argument("--hours", type=float, default=0, help="工作时间(小时)（单条，默认0）")
    ap.add_argument("--followup", help="后续工作（单条）")
    ap.add_argument("--remark", help="备注（单条）")
    ap.add_argument("--lawyer", help="经办律师（单条，缺省用 DEFAULT_LAWYER）")
    ap.add_argument("--lawyer-default", default=DEFAULT_LAWYER, help="缺省经办律师")
    ap.add_argument("--source", help="来源标识（如：用户指定归入 / 资料归入），缺省'对话自动捕获'")
    ap.add_argument("--json", help="JSON 字符串（对象或数组）")
    ap.add_argument("--file", help="JSON 文件路径（对象或数组）")
    ap.add_argument("--no-dedup", action="store_true", help="关闭去重（默认开启）")
    ap.add_argument("--dry-run", action="store_true", help="只校验与预览，不写盘")
    args = ap.parse_args()

    raw_list = None
    if args.json:
        try:
            raw_list = json.loads(args.json)
        except Exception as e:
            sys.stderr.write("JSON 解析失败：%s\n" % e)
            return 2
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                raw_list = json.load(f)
        except Exception as e:
            sys.stderr.write("读取文件失败：%s\n" % e)
            return 2
    elif not (args.unit or args.content) and not sys.stdin.isatty():
        try:
            raw_list = json.loads(sys.stdin.read().strip() or "[]")
        except Exception as e:
            sys.stderr.write("stdin JSON 解析失败：%s\n" % e)
            return 2

    try:
        recs = _normalize_records(args, raw_list)
    except ValueError as e:
        sys.stderr.write("参数错误：%s\n" % e)
        return 2

    if not recs:
        sys.stderr.write("未提供任何记录。\n")
        return 2

    valid = []
    for i, r in enumerate(recs, 1):
        try:
            valid.append(_validate(r, args.lawyer_default, args.source or "对话自动捕获"))
        except ValueError as e:
            sys.stderr.write("第 %d 条校验失败：%s -> %s\n" % (i, e, json.dumps(r, ensure_ascii=False)))
            return 2

    # 预览阶段的去重估算（dry-run 也读取现有记录，使 will_skip 准确；只读不写，安全）
    existing = _load_data().get("records", [])
    skipped_preview = 0
    to_add_preview = []
    for v in valid:
        key = (v["unit"], v["date"], v["content"])
        if not args.no_dedup and any((e.get("unit"), e.get("date"), e.get("content")) == key for e in existing):
            skipped_preview += 1
        else:
            to_add_preview.append(v)

    if args.dry_run:
        out = {
            "dry_run": True,
            "will_add": len(to_add_preview),
            "will_skip": skipped_preview,
            "items": [{"unit": x["unit"], "date": x["date"], "content": x["content"], "hours": x["hours"]} for x in to_add_preview],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    added, skipped, total = _commit(valid, args.no_dedup)
    result = {
        "added": len(added),
        "skipped": len(skipped),
        "total": total,
        "items": [{"id": x["id"], "unit": x["unit"], "date": x["date"], "content": x["content"], "hours": x["hours"]} for x in added],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.stderr.write("已写入 %d 条，跳过 %d 条（重复），当前共 %d 条记录。\n" % (len(added), len(skipped), total))
    return 0


if __name__ == "__main__":
    sys.exit(main())
