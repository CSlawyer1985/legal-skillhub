#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedup_upsert.py — 智录采集层"确定性判重 + upsert 决策"引擎（纯本地计算，不调 dws）

背景：本环境 managed-DWS，脚本内 subprocess 调 dws 无效。因此采集流程拆成
  Agent 拉台账快照 → 本脚本本地判重 → Agent 按决策执行 dws create/update。
脚本把"编号+姓名+手机"三键判重固化成代码，杜绝靠 agent 自觉导致的 -new 重复件。

用法:
  python3 dedup_upsert.py --ledger <台账快照.json> --incoming <候选工单.json> \
      [--state intake_state.json] [--out decisions.json] [--today YYYY-MM-DD]

输入:
  --ledger   当前台账快照。支持两种格式：
             (a) dws 原始响应 {"data":{"records":[{"recordId,cells:{fieldId:...}}]}}
                 或 dws --format json 落盘的 {"type":"dws_tool_result","content":"<escaped>"}
             (b) 已投影好的列表 [{"recordId,case_no,raw_no,person,contact,amount,ctype,...}]
             脚本内按 DEFAULT_FIELDMAP 自动识别并归一。
  --incoming 候选工单列表，每条建议字段（缺项留空即可）：
             {"投诉编号","12315原始编号","投诉人","联系方式","诉求金额",
              "投诉类型","工单类型","收到日期","投诉内容","跟进","来源"}
  --state    可选，intake_state.json，用其中的 processed_keys 做本轮内重复拉取兜底跳过。

输出 (decisions.json):
  {
    "updates":[{recordId,matched_on,append_follow,fill_if_empty:{...},existing_no,person}],
    "creates":[{...原始候选 + _title建议}],
    "skipped":[{reason,person,matched_key}],
    "fingerprints":[新出现且已判定的指纹，供 agent 追加进 state.processed_keys]
  }

判重规则（命中任一即视为同一案件，优先级从高到低）：
  K1 12315原始编号 相同（非空）
  K2 投诉编号/标题 相同（非空、且非纯 WS 自增撞车——WS 自增只在完全相等时算）
  K3 投诉人姓名 相同（非空非"匿名"）且 手机号 集合有交集
  K4 投诉人姓名 相同 且 诉求金额相同 且 投诉类型相同
仅 K1~K4 全不命中 → 判为 NEW（create）。

保守原则：update 只**追加跟进**、只**建议填充空字段**（fill_if_empty），绝不自动改
状态/风险/答复——那些留给人工或既有 D 流程。
"""
import argparse
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import completeness  # noqa: E402
from datetime import datetime

# 与 config.yaml field_map 对齐（表 <YOUR_TABLE_ID>）
DEFAULT_FIELDMAP = {
    "case_no": "01ZM8y7",
    "complainant": "wh1fk4j",
    "contact": "Ohw9pvL",
    "subject": "9QpIGT6",
    "complaint_type": "ZNOjYeZ",
    "channel": "HAMRsR2",
    "content": "mFCmvMP",
    "amount": "xdkb4lW",
    "received_date": "OSLR9Wk",
    "deadline": "Ctv7j2o",
    "status": "BIi8AY4",
    "follow_up": "F6U44G1",
    "case_type": "3aXSkms",
    "raw_12315_no": "rCdDjxk",
}

PHONE_RE = re.compile(r"1[3-9]\d{9}")
# 信访编号 / 协查函号 / 内部工单号——跨渠道复述同一案件时的强锚点
REF_RE = re.compile(r"(WX\d{6,}|XH\d{6,}|ID\d{5,}|〔\d{4}〕\d+号|[一-龥]{2,8}协[查函]{1,2}〔\d{4}〕\d+号)")
# 监管协查函/调查函信号——这类由独立"协查任务系统"承接，智录不入库
COOP_RE = re.compile(r"(协查函|调查(函|通知书)|协助调查|协〔?\d{4}〕?\d*号|加[盖]?公章函复|函复贵局|提供[^。]{0,20}(原始|注册)[^。]{0,10}(视频|信息)[^。]{0,10}(盖章|函复)|市场监督管理局[^。]{0,8}协[查函])")
# 信访信号：信访编号/来访/反映等——也不归智录，交信访轨道
XINFANG_RE = re.compile(r"(信访编号|信访件|来信来访|来访|上访|群众来电来访|反映问题|WX\d{6,})")


def classify_type(cand):
    """返回'监管协查函'/'信访'/''（空=按12315消费者投诉走正常入库）。优先用候选自带字段。
    协查函与信访均由智录忽略，交独立轨道处理。"""
    ct = str(cand.get("工单类型", cand.get("case_type", ""))).strip()
    if ct:
        return ct
    blob = " ".join(str(cand.get(k, "")) for k in ("投诉内容", "content", "投诉编号", "case_no", "跟进", "follow", "来源", "source"))
    if COOP_RE.search(blob):
        return "监管协查函"
    if XINFANG_RE.search(blob):
        return "信访"
    return ""


def content_shingles(text):
    t = re.sub(r"\s+", "", text or "")
    return {t[i:i + 2] for i in range(len(t) - 1)} if len(t) >= 2 else set()


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _cellval(v):
    """singleSelect/date 等字段取可读值"""
    if isinstance(v, dict):
        return str(v.get("name", "")).strip()
    if v is None:
        return ""
    return str(v).strip()


def norm_phone_set(text):
    return set(PHONE_RE.findall(text or ""))


def norm_amount(v):
    s = re.sub(r"[^\d.]", "", str(v or ""))
    try:
        return round(float(s), 2) if s else None
    except ValueError:
        return None


def norm_name(v):
    n = (v or "").strip()
    return "" if n in ("", "匿名", "None") else n


def is_raw_no(v):
    """12315国家平台号：≥18位纯数字（形如 133****002026...）"""
    return bool(re.fullmatch(r"\d{18,}", (v or "").strip()))


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def coerce_candidates(obj):
    """incoming 可能是列表本身，或包了 {candidates:[...]} / {data:{records}}"""
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in ("candidates", "incoming", "records", "items"):
            if k in obj and isinstance(obj[k], list):
                return obj[k]
    return [obj] if isinstance(obj, dict) else []


def load_ledger(path):
    """把台账快照归一成逻辑键列表；兼容 dws 原始响应与已投影列表"""
    obj = load_json(path)
    # 处理 hook-output 里 {"type":"dws_tool_result","content":"<escaped json>"}
    if isinstance(obj, dict) and "content" in obj and isinstance(obj["content"], str):
        obj = json.loads(obj["content"])
    records = None
    if isinstance(obj, dict):
        records = obj.get("data", {}).get("records") if "data" in obj else obj.get("records")
    if records is None:
        # 已投影好的列表
        lst = obj if isinstance(obj, list) else obj.get("ledger", obj.get("cases", []))
        proj = []
        for r in lst:
            content = str(r.get("content", r.get("投诉内容", "")))
            proj.append({
                "recordId": r.get("recordId", ""),
                "case_no": str(r.get("case_no", r.get("投诉编号", ""))).strip(),
                "raw_no": str(r.get("raw_no", r.get("12315原始编号", ""))).strip(),
                "person": norm_name(r.get("person", r.get("投诉人", ""))),
                "phones": norm_phone_set(r.get("contact", r.get("联系方式", ""))),
                "amount": norm_amount(r.get("amount", r.get("诉求金额"))),
                "ctype": str(r.get("ctype", r.get("投诉类型", ""))).strip(),
                "has_deadline": bool(r.get("deadline", r.get("截止日期"))),
                "contact": str(r.get("contact", r.get("联系方式", ""))).strip(),
                "refs": set(REF_RE.findall(content + str(r.get("follow_up", r.get("跟进记录", ""))))),
                "shingles": content_shingles(content),
                "content": content,
            })
        return proj

    fm = DEFAULT_FIELDMAP
    proj = []
    for r in records:
        c = r.get("cells", {})
        contact = _cellval(c.get(fm["contact"], ""))
        content = _cellval(c.get(fm["content"], ""))
        follow = _cellval(c.get(fm["follow_up"], ""))
        proj.append({
            "recordId": r.get("recordId", ""),
            "case_no": _cellval(c.get(fm["case_no"], "")),
            "raw_no": _cellval(c.get(fm["raw_12315_no"], "")),
            "person": norm_name(_cellval(c.get(fm["complainant"], ""))),
            "phones": norm_phone_set(contact),
            "amount": norm_amount(c.get(fm["amount"])),
            "ctype": _cellval(c.get(fm["complaint_type"], "")),
            "has_deadline": bool(_cellval(c.get(fm["deadline"], ""))),
            "contact": contact,
            "refs": set(REF_RE.findall(content + follow)),
            "shingles": content_shingles(content),
            "content": content,
        })
    return proj


def cand_view(c):
    """从候选提取归一键；兼容中文键与逻辑键"""
    case_no = str(c.get("投诉编号", c.get("case_no", ""))).strip()
    raw = str(c.get("12315原始编号", c.get("raw_no", ""))).strip()
    # 候选若把12315号塞进投诉编号，自动分流
    if not raw and is_raw_no(case_no):
        raw, case_no = case_no, ""
    person = norm_name(c.get("投诉人", c.get("person", "")))
    contact = str(c.get("联系方式", c.get("contact", ""))).strip()
    content = str(c.get("投诉内容", c.get("content", "")))
    follow = str(c.get("跟进", c.get("follow", "")))
    return {
        "case_no": case_no, "raw_no": raw, "person": person,
        "phones": norm_phone_set(contact), "contact": contact,
        "amount": norm_amount(c.get("诉求金额", c.get("amount"))),
        "ctype": str(c.get("投诉类型", c.get("ctype", ""))).strip(),
        "deadline": str(c.get("截止日期", c.get("deadline", ""))).strip(),
        "received": str(c.get("收到日期", c.get("received_date", ""))).strip(),
        "refs": set(REF_RE.findall(content + follow)),
        "shingles": content_shingles(content),
    }


def fingerprint(v):
    basis = "|".join([v["case_no"], v["raw_no"], v["person"], ",".join(sorted(v["phones"]))])
    return hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def match_existing(v, ledger, content_thresh=0.55):
    """返回 (recordId, matched_on) 或 (None,None)。同案命中多条时取第一条。"""
    for e in ledger:
        # K1 12315原始编号强匹配
        if v["raw_no"] and e["raw_no"] and v["raw_no"] == e["raw_no"]:
            return e["recordId"], "K1_12315编号"
        # K2 投诉编号/标题相等
        if v["case_no"] and e["case_no"] and v["case_no"] == e["case_no"]:
            return e["recordId"], "K2_投诉编号"
        # K5 函号/信访编号/内部工单号相等（跨渠道复述同案最强锚点之一）
        if v["refs"] and e["refs"] and (v["refs"] & e["refs"]):
            return e["recordId"], "K5_函号"
        # K3 手机号相交 + 佐证(金额相等 或 类型相等 或 姓名前缀2字相同)
        if v["phones"] & e["phones"]:
            corroborate = (
                (v["amount"] is not None and v["amount"] == e["amount"])
                or (v["ctype"] and v["ctype"] == e["ctype"])
                or (v["person"] and e["person"] and v["person"][:2] == e["person"][:2])
            )
            if corroborate:
                return e["recordId"], "K3_手机+佐证"
        # K4 姓名相等 + 金额相等 + 类型相等
        if v["person"] and v["person"] == e["person"] \
                and v["amount"] is not None and v["amount"] == e["amount"] \
                and v["ctype"] == e["ctype"]:
            return e["recordId"], "K4_姓名+金额+类型"
        # K6 姓名相等 且 内容近重(Jaccard)
        if v["person"] and v["person"] == e["person"] \
                and jaccard(v["shingles"], e["shingles"]) >= content_thresh:
            return e["recordId"], "K6_姓名+内容近重"
    return None, None


def build_append(cand, matched_on, today):
    src = cand.get("来源", cand.get("source", "市监群"))
    follow = str(cand.get("跟进", cand.get("follow", ""))).strip()
    stamp = today or datetime.now().strftime("%Y-%m-%d")
    line = f"◎{stamp}—判重命中({matched_on})，同案不重复建单；{src}进展：{follow or '见本轮来件'}"
    return line


def decide(ledger, incoming, processed_keys, today):
    updates, creates, skipped, ignored, fps = [], [], [], [], []
    seen_this_run = set()
    for cand in incoming:
        # 前置过滤：监管协查函与信访都不归智录，交各自独立轨道处理，不入库
        ctype = classify_type(cand)
        if ctype in ("监管协查函", "信访"):
            dest = "协查任务系统" if ctype == "监管协查函" else "信访轨道"
            ignored.append({"reason": f"{ctype}→移交{dest}，智录不入库",
                            "kind": ctype,
                            "person": cand_view(cand)["person"] or "(单位/机关)",
                            "no": str(cand.get("投诉编号", cand.get("case_no", "")))})
            continue
        v = cand_view(cand)
        fp = fingerprint(v)
        fps.append(fp)
        # 本轮内或历史已处理过同一指纹 → 跳过（同一条消息重复拉取）
        if fp in processed_keys or fp in seen_this_run:
            skipped.append({"reason": "指纹已处理", "person": v["person"], "fp": fp})
            continue
        seen_this_run.add(fp)
        rid, matched_on = match_existing(v, ledger)
        if rid:
            upd = {
                "recordId": rid,
                "matched_on": matched_on,
                "append_follow": build_append(cand, matched_on, today),
                "person": v["person"] or "(匿名)",
                "fp": fp,
            }
            # 建议填充既有记录的空字段（不自动写，交 agent 决定）
            fill = {}
            if v["contact"] and not next((e for e in ledger if e["recordId"] == rid), {}).get("contact"):
                pass
            e = next((x for x in ledger if x["recordId"] == rid), {})
            if v["contact"] and not e.get("contact"):
                fill["联系方式"] = v["contact"]
            if v["deadline"] and not e.get("has_deadline"):
                fill["截止日期"] = v["deadline"]
            if v["raw_no"] and not e.get("raw_no"):
                fill["12315原始编号"] = v["raw_no"]
            if fill:
                upd["fill_if_empty"] = fill
            updates.append(upd)
        else:
            c = dict(cand)
            c["_fp"] = fp
            miss = completeness.missing_fields(cand)
            if miss:
                c["_待补全"] = miss
            creates.append(c)
    return {"updates": updates, "creates": creates, "skipped": skipped, "ignored": ignored, "fingerprints": fps}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--incoming", required=True)
    ap.add_argument("--state")
    ap.add_argument("--out", default="dedup_decisions.json")
    ap.add_argument("--today")
    args = ap.parse_args()

    ledger = load_ledger(args.ledger)
    incoming = coerce_candidates(load_json(args.incoming))
    processed_keys = set()
    if args.state:
        try:
            st = load_json(args.state)
            processed_keys = set(st.get("processed_keys", []))
        except (OSError, ValueError):
            processed_keys = set()

    res = decide(ledger, incoming, processed_keys, args.today)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)

    print(f"[dedup_upsert] 候选{len(incoming)} → 更新{len(res['updates'])} / "
          f"新建{len(res['creates'])} / 跳过{len(res['skipped'])} / 忽略{len(res['ignored'])}；已写 {args.out}")
    for ig in res["ignored"]:
        print(f"  IGNORE  {ig['reason']}  人={ig['person']}  编号={ig['no'] or '?'}")
    for u in res["updates"]:
        print(f"  UPDATE {u['recordId']}  命中={u['matched_on']}  人={u['person']}"
              + (f"  待填空={list(u.get('fill_if_empty', {}).keys())}" if u.get("fill_if_empty") else ""))
    for c in res["creates"]:
        v = cand_view(c)
        print(f"  CREATE  人={v['person'] or '(匿名)'}  编号={v['case_no'] or v['raw_no'] or '?'}")


if __name__ == "__main__":
    main()
