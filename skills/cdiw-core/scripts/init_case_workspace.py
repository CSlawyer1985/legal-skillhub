#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""案件工作区初始化脚本（init_case_workspace.py）。

功能：按规格书 C-2／C-3 与 I-3 建立案件工作区固定结构——
  目录：03_正式文书/、04_正式文书（word版）/、logs/、
        working_notes/ 五子目录（阅卷摘录／证据清单／时间轴／矛盾清单／长文草稿）
  文件：case_status.md 骨架（按 Schema 七块字段）、citation_ledger.jsonl、
        logs/audit_log.jsonl、logs/feedback.log、logs/localization_log.jsonl

调用方式：
  python scripts/init_case_workspace.py --path ./案件/阿明案 --case 阿明案
  python scripts/init_case_workspace.py --path ./案件/阿明案 --case 阿明案 \
      --crime 帮助信息网络犯罪活动罪 --measure 刑事拘留

已存在的目录与文件逐项跳过并报告，不做覆盖。

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2路径冲突 / 3写入失败；
  - 错误码：MISSING_PARAM / INVALID / ERR_IO。
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime

SCRIPT_NAME = "init_case_workspace"

WORKING_NOTES = ["阅卷摘录", "证据清单", "时间轴", "矛盾清单", "长文草稿"]
DIRECTORIES = ["03_正式文书", "04_正式文书（word版）", "logs",
               "backups"] + ["working_notes/" + d for d in WORKING_NOTES]

JSONL_FILES = {
    "citation_ledger.jsonl": "引用台账（C-2：一行一事件，逐条登记法条/案例/数据/附件引用）",
    "logs/audit_log.jsonl": "审计日志（C-2：工具名、入参摘要、返回摘要、耗时、时间戳）",
    "logs/feedback.log": "使用观察记录（C-2：路由是否命中预期、纠正类型与原因）",
    "logs/localization_log.jsonl": "本地化采集记录（I-3：条目ID、地区、内容类型、采集核实时点、核对人）",
}

STATUS_SKELETON = """# 案件状态文件（case_status.md）

> 本文件为案件唯一权威数据源，读写仅经 scripts/case_state_manager.py。
> 结构依据 assets/schemas/case_status_schema.json（七块字段）。
> 生成时间：{ts}　初始化：scripts/init_case_workspace.py

## 一、案件标识
- 案件代称：{case}
- 案号：（无）
- 承办律师：
- 协办律师：

## 二、程序状态
- 当前阶段：侦查阶段
- 强制措施：{measure}
- 羁押地点：
- 办案机关及承办人：
- 各机关文书时间：

## 三、期限节点
- 刑拘起算：
- 报捕期限：
- 审查批捕期限：
- 侦查羁押期限及延长：
- 全部预警日期：

## 四、服务进程
- 标准服务清单销项状态：（未载入）
- 各线完成度：
- 工作清单（时间/承办律师/事项/用时）：

## 五、复杂度
- 罪名数：{crime_flag}
- 事实节数：
- 同案人数：
- 紧急度分级：待评估

## 六、待办与确认
- 待办优先级队列：
- 当事人确认记录：
- 选择笔录索引：

## 七、治理
- 引用台账索引：citation_ledger.jsonl
- 审计日志索引：logs/audit_log.jsonl
- 版本记录：主包 2.2.0
"""


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def emit(env, code):
    print(json.dumps(env, ensure_ascii=False, indent=2))
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(
        prog=SCRIPT_NAME, description="案件工作区初始化：目录骨架＋状态文件＋三类 JSONL。")
    ap.add_argument("--path", required=True, help="案件文件夹路径（不存在则创建）")
    ap.add_argument("--case", required=True, help="案件代称（虚构代称，禁止真实姓名）")
    ap.add_argument("--crime", default="", help="涉嫌罪名（可选）")
    ap.add_argument("--measure", default="待确认", help="强制措施类型（可选）")
    args = ap.parse_args()
    tid = make_trace_id()

    if not args.path or not args.case:
        emit(envelope("error", "MISSING_PARAM", "须指定 --path 与 --case", {"trace_id": tid}), 1)

    root = args.path
    if os.path.exists(root) and not os.path.isdir(root):
        emit(envelope("error", "INVALID", "路径已存在且非目录：%s" % root,
                      {"trace_id": tid}), 2)

    created_dirs, skipped_dirs = [], []
    for d in DIRECTORIES:
        p = os.path.join(root, d)
        if os.path.isdir(p):
            skipped_dirs.append(d)
        else:
            try:
                os.makedirs(p, exist_ok=True)
                created_dirs.append(d)
            except OSError as exc:
                emit(envelope("error", "ERR_IO", "目录创建失败：%s（%s）" % (p, exc),
                              {"trace_id": tid}), 3)

    created_files, skipped_files = [], []
    for rel, desc in JSONL_FILES.items():
        p = os.path.join(root, rel)
        if os.path.exists(p):
            skipped_files.append(rel)
            continue
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write("")
            created_files.append({"file": rel, "desc": desc})
        except OSError as exc:
            emit(envelope("error", "ERR_IO", "文件创建失败：%s（%s）" % (p, exc),
                          {"trace_id": tid}), 3)

    status_path = os.path.join(root, "case_status.md")
    status_created = False
    if os.path.exists(status_path):
        skipped_files.append("case_status.md")
    else:
        try:
            with open(status_path, "w", encoding="utf-8") as f:
                f.write(STATUS_SKELETON.format(
                    ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    case=args.case, measure=args.measure,
                    crime_flag=args.crime or "待确认"))
            status_created = True
            created_files.append({"file": "case_status.md", "desc": "案件状态骨架（七块字段）"})
        except OSError as exc:
            emit(envelope("error", "ERR_IO", "状态文件写入失败：%s（%s）" % (status_path, exc),
                          {"trace_id": tid}), 3)

    emit(envelope(
        "ok", None,
        "案件工作区已就绪：新建目录 %d 个、新建文件 %d 个，跳过已存在 %d 项"
        % (len(created_dirs), len(created_files), len(skipped_dirs) + len(skipped_files)),
        {"trace_id": tid, "case_dir": os.path.abspath(root), "case": args.case,
         "created_dirs": created_dirs, "skipped_dirs": skipped_dirs,
         "created_files": created_files, "skipped_files": skipped_files,
         "status_file": os.path.join(root, "case_status.md"),
         "status_created": status_created,
         "next": "口述或录入案件要素后调用 case_state_manager.py 补全状态字段"}), 0)


if __name__ == "__main__":
    main()
