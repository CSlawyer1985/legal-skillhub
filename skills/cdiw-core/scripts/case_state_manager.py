#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""案件状态文件读写与更新管理器（case_state_manager.py）。

功能：
  1. 创建案件（生成case_id、创建案件工作区目录结构、初始化case_status.md与服务进程字段）；
  2. 更新节点（追加型字段：meetings/receptions/communications/documents/todos/files/deadlines/consents）；
  3. 断点续接读取（read）；
  4. 运行日志记录（log，追加logs/script_runs.jsonl）；
  5. 委托人确认记录（confirm，写入service_progress.confirmations）；
  6. 阶段服务进程确认表生成（report，按assets/templates/service_progress_confirm.md格式）。

调用方式：
  python scripts/case_state_manager.py --action {create|read|update|log|confirm|report}
      --case_id CASE-20260820-001 --field meetings --payload '{...}' --workspace {案件工作区路径}

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status: "ok"|"error", error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2数据文件缺失或损坏 / 3计算或校验失败；
  - 错误码：ERR_ARGS_MISSING / ERR_CASE_NOT_FOUND / ERR_CASE_EXISTS /
    ERR_FIELD_INVALID / ERR_DATE_INVALID / ERR_TYPE_INVALID / ERR_IO；
  - 每次调用追加运行日志至案件工作区logs/；trace_id=脚本名+时间戳哈希前八位。
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_NAME = "case_state_manager"
STATUS_FILE = "case_status.md"
LIST_FIELDS = {"deadlines", "meetings", "receptions", "communications",
               "documents", "todos", "files", "consents"}
WORKDIRS = ["meetings", "receptions", "communications", "documents",
            "reports", "confirmations", "logs"]

# 侦查阶段标准服务清单（按assets/templates/investigation_service_checklist.md载入：
# 接待8次＋会见6次＋公安沟通3次＋检察沟通2次＋书面意见3份）
DEFAULT_CHECKLIST = [
    {"category": "接待", "item": "首次接待（接案，三问框架）"},
    {"category": "接待", "item": "提请批准逮捕前的接待"},
    {"category": "接待", "item": "批捕前的接待"},
    {"category": "接待", "item": "批捕后的接待（逮捕原因七分法）"},
    {"category": "接待", "item": "羁押必要性审查的接待"},
    {"category": "接待", "item": "移送审查起诉前的接待"},
    {"category": "接待", "item": "会见前沟通待转达事项与会见后通报（对应六次会见）"},
    {"category": "接待", "item": "机动接待（按需，一般不超过8次含电话）"},
    {"category": "会见", "item": "第一次会见（接案后，七步法）"},
    {"category": "会见", "item": "第二次会见（刑拘后报捕前）"},
    {"category": "会见", "item": "第三次会见（检察官提审前辅导）"},
    {"category": "会见", "item": "第四次会见（逮捕后两天内，不得推迟）"},
    {"category": "会见", "item": "第五次会见（逮捕后一个月左右）"},
    {"category": "会见", "item": "第六次会见（侦查终结前，三说）"},
    {"category": "沟通", "item": "公安第一次沟通（递交委托手续）"},
    {"category": "沟通", "item": "公安第二次沟通（报捕前提交取保候审申请书）"},
    {"category": "沟通", "item": "公安第三次沟通（侦查终结前沟通意见）"},
    {"category": "沟通", "item": "检察第一次沟通（审查批捕阶段提交意见并当面沟通）"},
    {"category": "沟通", "item": "检察第二次沟通（羁押必要性审查沟通）"},
    {"category": "文书", "item": "取保候审申请书（报捕前三日内）"},
    {"category": "文书", "item": "不予批准逮捕律师意见书（审查批捕阶段）"},
    {"category": "文书", "item": "羁押必要性审查申请书（逮捕后一个月左右）"},
]


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code,
            "message": message, "data": data}


def out(obj, code):
    print(json.dumps(obj, ensure_ascii=False, indent=2))
    return code


def yaml_value(v):
    """将Python值序列化为YAML行内标量（嵌套dict/list序列化为JSON以保证往返一致）。"""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    s = str(v)
    if s == "" or re.search(r"[:{}\[\],#&*!|>'\"%@`]", s) or s != s.strip():
        return json.dumps(s, ensure_ascii=False)
    return s


def dump_state(state):
    """将状态字典序列化为YAML文本（两级结构＋行内JSON列表项）。"""
    lines = []
    for key, val in state.items():
        if isinstance(val, dict):
            lines.append("%s:" % key)
            for k2, v2 in val.items():
                if isinstance(v2, list):
                    lines.append("  %s:" % k2)
                    for item in v2:
                        lines.append("  - %s" % json.dumps(item, ensure_ascii=False))
                else:
                    lines.append("  %s: %s" % (k2, yaml_value(v2)))
        elif isinstance(val, list):
            lines.append("%s:" % key)
            for item in val:
                lines.append("  - %s" % json.dumps(item, ensure_ascii=False))
        else:
            lines.append("%s: %s" % (key, yaml_value(val)))
    return "\n".join(lines) + "\n"


def load_state(text):
    """解析本脚本生成的YAML子集（两级字典＋行内JSON列表项）。"""
    state = {}
    current_block = None
    current_list = None
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        if raw.startswith("  - "):
            item_raw = raw[4:].strip()
            try:
                item = json.loads(item_raw)
            except ValueError:
                item = {"raw": item_raw}
            if current_list is not None:
                current_list.append(item)
            continue
        if raw.startswith("  ") and not raw.startswith("  -"):
            if current_block is not None and ":" in raw:
                k, _, v = raw.strip().partition(":")
                v = v.strip()
                if v == "":
                    current_list = []
                    current_block[k] = current_list
                else:
                    current_list = None
                    current_block[k] = parse_scalar(v)
            continue
        if ":" in raw:
            k, _, v = raw.partition(":")
            v = v.strip()
            if v == "":
                if k in LIST_FIELDS:
                    # 顶层列表字段：dump_state输出为“key:”＋缩进列表项，读回时初始化为列表
                    current_block = None
                    current_list = []
                    state[k] = current_list
                else:
                    current_block = {}
                    state[k] = current_block
                    current_list = None
            else:
                current_block = None
                current_list = None
                state[k] = parse_scalar(v)
    return state


def parse_scalar(s):
    if s.startswith("{") and s.endswith("}"):
        try:
            return json.loads(s)
        except ValueError:
            try:
                return parse_flow_yaml(s)
            except Exception:
                return s
    if s in ("true", "false"):
        return s == "true"
    if s == "null":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if s.startswith('"') and s.endswith('"'):
        try:
            return json.loads(s)
        except ValueError:
            return s
    return s


def parse_flow_yaml(s):
    """解析无引号的YAML行内流式映射（如 {a: 1, b: x}）。"""
    inner = s[1:-1]
    result = {}
    depth = 0
    buf = ""
    parts = []
    for ch in inner:
        if ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    for part in parts:
        if ":" in part:
            k, _, v = part.partition(":")
            result[k.strip()] = parse_scalar(v.strip())
    return result


def status_path(workspace):
    return os.path.join(workspace, STATUS_FILE)


def gen_case_id(workspace):
    today = datetime.now().strftime("%Y%m%d")
    prefix = "CASE-%s-" % today
    n = 1
    # 扫描工作区及其父目录中当日已有案件目录/文件，取最大序号＋1，避免同日多案件编号冲突
    abs_ws = os.path.abspath(workspace)
    search_dirs = {os.path.dirname(abs_ws) or ".", workspace}
    for d in search_dirs:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if name.startswith(prefix):
                try:
                    n = max(n, int(name[len(prefix):]) + 1)
                except ValueError:
                    pass
    return "%s%03d" % (prefix, n)


def build_initial_state(case_id, payload):
    now = now_str()
    basic = {
        "client_alias": "××",
        "charges": ["××罪"],
        "measure": {"type": "刑事拘留", "start": ""},
        "detention_place": "××",
        "authority": "××",
        "handler": "××",
        "offense_date": "××",
        "client_age": "××",
        "victim_age": "××",
        "offense_count": 0,
        "cross_region": False,
        "accomplices_total": 1,
        "prior_record": "无",
        "arrest_manner": "××",
        "family_contact": {"alias": "××", "relation": "××"},
        "family_demand": "",
    }
    if payload:
        for k, v in payload.items():
            basic[k] = v
    charges = basic.get("charges", [])
    if isinstance(charges, str):
        charges = [charges]
    complexity = {
        "charge_count": len(charges),
        "fact_count": payload.get("fact_count", 1) if payload else 1,
        "accomplice_count": basic.get("accomplices_total", 1),
        "level": "标准",
    }
    if complexity["charge_count"] > 1 or complexity["fact_count"] > 1 or complexity["accomplice_count"] > 1:
        complexity["level"] = "复杂"
    case_name = payload.get("case_name", "某某涉嫌%s案" % "、".join(charges)) if payload else "某某涉嫌××罪案"
    checklist = []
    for entry in DEFAULT_CHECKLIST:
        checklist.append({"category": entry["category"], "item": entry["item"],
                          "baseline": 1, "completed": 0, "details": [],
                          "status": "未完成"})
    return {
        "case_id": case_id,
        "case_name": case_name,
        "created_at": now,
        "updated_at": now,
        "basic_info": basic,
        "complexity": complexity,
        "stage": {"current": "侦查", "entered_at": now, "history": []},
        "emergency": {"level": "蓝", "assessed_at": now},
        "deadlines": [],
        "meetings": [],
        "receptions": [],
        "communications": [],
        "documents": [],
        "service_progress": {
            "stage": "侦查",
            "lawyer": (payload.get("lawyer", "") if payload else ""),
            "start_date": now[:10],
            "checklist": checklist,
            "monthly_worklog": [],
            "confirmations": [],
        },
        "consents": [],
        "todos": [],
        "files": [],
    }


def write_log(workspace, trace_id, params_digest, result_status):
    logs_dir = os.path.join(workspace, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    entry = {"time": now_str(), "trace_id": trace_id, "script": SCRIPT_NAME,
             "params": params_digest, "result": result_status}
    with open(os.path.join(logs_dir, "script_runs.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def action_create(args, trace_id):
    if not args.workspace:
        return out(envelope("error", "ERR_ARGS_MISSING", "--workspace为必填参数", None), 1)
    sp = status_path(args.workspace)
    if os.path.exists(sp):
        return out(envelope("error", "ERR_CASE_EXISTS", "案件已存在：%s" % sp, {"path": sp}), 1)
    payload = {}
    if args.payload:
        try:
            payload = json.loads(args.payload)
        except ValueError:
            return out(envelope("error", "ERR_FIELD_INVALID", "payload非法JSON", None), 1)
    case_id = args.case_id or gen_case_id(args.workspace)
    state = build_initial_state(case_id, payload)
    for d in WORKDIRS:
        os.makedirs(os.path.join(args.workspace, d), exist_ok=True)
    with open(sp, "w", encoding="utf-8") as f:
        f.write(dump_state(state))
    write_log(args.workspace, trace_id, "create %s" % case_id, "ok")
    done = sum(1 for c in state["service_progress"]["checklist"])
    return out(envelope("ok", None, "案件已创建", {
        "case_id": case_id, "path": sp,
        "workspace": args.workspace,
        "checklist_items": done,
        "service_baseline": "接待8＋会见6＋公安沟通3＋检察沟通2＋书面意见3"}), 0)


def load_or_error(args):
    if not args.workspace:
        return None, out(envelope("error", "ERR_ARGS_MISSING", "--workspace为必填参数", None), 1)
    sp = status_path(args.workspace)
    if not os.path.exists(sp):
        return None, out(envelope("error", "ERR_CASE_NOT_FOUND", "案件不存在：%s" % sp, {"path": sp}), 1)
    try:
        with open(sp, "r", encoding="utf-8") as f:
            state = load_state(f.read())
    except (OSError, ValueError) as exc:
        return None, out(envelope("error", "ERR_IO", "状态文件读取失败：%s" % exc, None), 2)
    return (state, sp), None


def action_read(args, trace_id):
    loaded, err = load_or_error(args)
    if err is not None:
        return err
    state, sp = loaded
    if args.case_id and state.get("case_id") != args.case_id:
        return out(envelope("error", "ERR_CASE_NOT_FOUND",
                            "case_id不匹配：%s != %s" % (args.case_id, state.get("case_id")), None), 1)
    order = ["stage", "service_progress", "todos", "emergency"]
    resume = {k: state.get(k) for k in order}
    write_log(args.workspace, trace_id, "read", "ok")
    return out(envelope("ok", None, "读取成功", {
        "case": state, "resume_context": resume,
        "resume_order": "stage→service_progress→todos→emergency"}), 0)


def action_update(args, trace_id):
    loaded, err = load_or_error(args)
    if err is not None:
        return err
    state, sp = loaded
    if not args.field:
        return out(envelope("error", "ERR_ARGS_MISSING", "--field为必填参数", None), 1)
    if args.field not in LIST_FIELDS and args.field not in state:
        return out(envelope("error", "ERR_FIELD_INVALID",
                            "字段非法：%s（合法字段：%s或已有顶层字段）" % (args.field, ",".join(sorted(LIST_FIELDS))), None), 1)
    if not args.payload:
        return out(envelope("error", "ERR_ARGS_MISSING", "--payload为必填参数", None), 1)
    try:
        payload = json.loads(args.payload)
    except ValueError:
        return out(envelope("error", "ERR_FIELD_INVALID", "payload非法JSON", None), 1)
    if args.field in LIST_FIELDS:
        state.setdefault(args.field, [])
        if isinstance(payload, list):
            state[args.field].extend(payload)
        else:
            payload.setdefault("seq", len(state[args.field]) + 1)
            state[args.field].append(payload)
    else:
        if isinstance(payload, dict) and isinstance(state.get(args.field), dict):
            state[args.field].update(payload)
        else:
            state[args.field] = payload
    # 同步服务进程销项：字段命中checklist条目时记入details
    checklist_sync(state, args.field, payload)
    state["updated_at"] = now_str()
    try:
        with open(sp, "w", encoding="utf-8") as f:
            f.write(dump_state(state))
    except OSError as exc:
        return out(envelope("error", "ERR_IO", "状态文件写入失败：%s" % exc, None), 2)
    write_log(args.workspace, trace_id, "update %s" % args.field, "ok")
    return out(envelope("ok", None, "更新成功", {"field": args.field, "payload": payload}), 0)


def checklist_sync(state, field, payload):
    """会见/沟通/文书/接待记录写入时同步销项服务清单（未完成→进行中/完成）。"""
    sp = state.get("service_progress") or {}
    checklist = sp.get("checklist") or []
    cat_map = {"meetings": "会见", "communications": "沟通",
               "documents": "文书", "receptions": "接待"}
    category = cat_map.get(field)
    if not category or not isinstance(payload, dict):
        return
    item_text = payload.get("node") or payload.get("purpose") or payload.get("name") or ""
    for entry in checklist:
        if entry.get("category") != category:
            continue
        if entry.get("status") == "未完成" and (
                (item_text and (item_text[:6] in entry.get("item", "")
                                or entry.get("item", "")[:6] in item_text))
                or payload.get("force_match")):
            entry["status"] = "进行中"
            entry["details"] = entry.get("details") or []
            entry["details"].append({"date": payload.get("date") or now_str(),
                                     "lawyer": payload.get("lawyer", ""),
                                     "minutes": payload.get("minutes", 0),
                                     "summary": item_text})
            entry["completed"] = len(entry["details"])
            break


def action_log(args, trace_id):
    if not args.workspace:
        return out(envelope("error", "ERR_ARGS_MISSING", "--workspace为必填参数", None), 1)
    if not args.payload:
        return out(envelope("error", "ERR_ARGS_MISSING", "--payload为必填参数", None), 1)
    try:
        payload = json.loads(args.payload)
    except ValueError:
        return out(envelope("error", "ERR_FIELD_INVALID", "payload非法JSON", None), 1)
    payload = dict(payload)
    payload.setdefault("time", now_str())
    payload.setdefault("trace_id", trace_id)
    payload.setdefault("script", SCRIPT_NAME)
    logs_dir = os.path.join(args.workspace, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    try:
        with open(os.path.join(logs_dir, "script_runs.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except OSError as exc:
        return out(envelope("error", "ERR_IO", "日志写入失败：%s" % exc, None), 2)
    return out(envelope("ok", None, "日志已记录", {"log": payload}), 0)


def action_confirm(args, trace_id):
    loaded, err = load_or_error(args)
    if err is not None:
        return err
    state, sp_path = loaded
    if not args.payload:
        return out(envelope("error", "ERR_ARGS_MISSING", "--payload为必填参数", None), 1)
    try:
        payload = json.loads(args.payload)
    except ValueError:
        return out(envelope("error", "ERR_FIELD_INVALID", "payload非法JSON", None), 1)
    record = {"date": payload.get("date", now_str()[:10]),
              "method": payload.get("method", "微信回复收到"),
              "content": payload.get("content", ""),
              "archived": payload.get("archived", True)}
    sp = state.setdefault("service_progress", {})
    sp.setdefault("confirmations", []).append(record)
    state["updated_at"] = now_str()
    try:
        with open(sp_path, "w", encoding="utf-8") as f:
            f.write(dump_state(state))
    except OSError as exc:
        return out(envelope("error", "ERR_IO", "状态文件写入失败：%s" % exc, None), 2)
    write_log(args.workspace, trace_id, "confirm", "ok")
    return out(envelope("ok", None, "确认已归档", {"confirmation": record}), 0)


def action_report(args, trace_id):
    """按service_progress_confirm.md格式生成《阶段服务进程确认表》文本。"""
    loaded, err = load_or_error(args)
    if err is not None:
        return err
    state, _ = loaded
    sp = state.get("service_progress") or {}
    checklist = sp.get("checklist") or []
    lines = []
    lines.append("阶段服务进程确认表")
    lines.append("")
    lines.append("案件名称：%s　案件阶段：%s　承办律师：%s　起止日期：%s 至 %s" % (
        state.get("case_name", ""), sp.get("stage", ""),
        sp.get("lawyer", ""), sp.get("start_date") or state.get("created_at", "")[:10],
        now_str()[:10]))
    lines.append("")
    lines.append("| 类别 | 日期 | 工作内容摘要 | 承办律师 | 工作用时 | 委托人确认签名 |")
    lines.append("|---|---|---|---|---|---|")
    unfinished = []
    total = done_cnt = 0
    for entry in checklist:
        total += 1
        details = entry.get("details") or []
        if entry.get("status") == "完成" or details:
            done_cnt += 1
        if not details:
            unfinished.append("[%s] %s" % (entry.get("category"), entry.get("item")))
        for d in details:
            lines.append("| %s | %s | %s | %s | %s |  |" % (
                entry.get("category"), d.get("date", ""), d.get("summary", ""),
                d.get("lawyer", ""), "%s分钟" % d.get("minutes", "")))
        if not details:
            lines.append("| %s | — | %s（未完成） |  |  |  |" % (
                entry.get("category"), entry.get("item")))
    lines.append("")
    lines.append("阶段服务小结：本阶段完成事项 %d/%d；未完成事项自动转入待办并列入衔接事项。" % (done_cnt, total))
    if unfinished:
        lines.append("衔接事项：")
        for u in unfinished:
            lines.append("- %s" % u)
    lines.append("")
    lines.append("委托人整体确认签名：＿＿＿＿＿＿＿＿　日期：＿＿＿＿＿＿")
    report_text = "\n".join(lines)
    reports_dir = os.path.join(args.workspace, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, "阶段服务进程确认表_%s.md" % now_str()[:10])
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(report_text + "\n")
    except OSError as exc:
        return out(envelope("error", "ERR_IO", "报告写入失败：%s" % exc, None), 2)
    write_log(args.workspace, trace_id, "report", "ok")
    return out(envelope("ok", None, "阶段服务进程确认表已生成（按service_progress_confirm.md格式）",
                        {"path": path, "text": report_text,
                         "completed": done_cnt, "total": total}), 0)


def build_parser():
    p = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="案件状态文件（case_status.md）读写与更新管理器；唯一写入通道，追加不覆盖。")
    p.add_argument("--action", required=True,
                   choices=["create", "read", "update", "log", "confirm", "report"],
                   help="create创建案件；read断点续接读取；update更新字段；log记录日志；confirm记录确认；report生成阶段确认表")
    p.add_argument("--case_id", help="案件编号（CASE-YYYYMMDD-NNN；create时可省略自动生成）")
    p.add_argument("--field", help="update时的顶层字段名（列表字段追加：deadlines/meetings/receptions/communications/documents/todos/files/consents）")
    p.add_argument("--payload", help="JSON字符串（create传基本信息、update传记录、log传日志、confirm传确认内容）")
    p.add_argument("--workspace", help="案件工作区路径（case_status.md所在目录）")
    return p


def main():
    args = build_parser().parse_args()
    trace_id = make_trace_id()
    handlers = {"create": action_create, "read": action_read,
                "update": action_update, "log": action_log,
                "confirm": action_confirm, "report": action_report}
    sys.exit(handlers[args.action](args, trace_id))


if __name__ == "__main__":
    main()
