#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ledger_io.py — 台账快照的统一读取 + 投影（单一真源，供 refresh_dashboard / step5 巡检共用）。

背景（为什么需要它）：
  dws aitable record query 落盘的是"原始单元格"格式 {data:{records:[{recordId,cells:{<字段ID>:值}}]}}，
  singleSelect 值还是 {"id","name"}。而巡检 step5 需要"中文键"投影行（投诉编号/投诉人/处理状态…）。
  若把原始格式直接喂给 step5，会 rec.get(...) 命中字符串键 → AttributeError 崩溃 → 误报"巡检异常"。
  本模块把 load + project 收敛成一处，任何调用方拿到的都是干净的投影行。

用法:
  from ledger_io import load_records, to_engine
  recs  = load_records('/tmp/ledger.json')     # 兼容 raw / hook包裹 / 已是投影列表
  rows  = to_engine(recs)                       # -> 中文键投影行（幂等：已是投影行则原样返回）
"""
import json

# 表 <台账表ID> 字段ID（与 config.yaml 对齐）
FM = {
    "no": "01ZM8y7", "person": "wh1fk4j", "contact": "Ohw9pvL", "subject": "9QpIGT6",
    "ctype": "ZNOjYeZ", "channel": "HAMRsR2", "content": "mFCmvMP", "amount": "xdkb4lW",
    "recv": "OSLR9Wk", "deadline": "Ctv7j2o", "status": "BIi8AY4", "risk": "JKDjUT2",
    "score": "30WUmPm", "follow": "F6U44G1", "case_type": "3aXSkms", "raw": "rCdDjxk",
    "suggestion": "ev6l0q6", "final": "Q587I0X", "handler": "eb5uGrm",
    # 复核闭环新增字段：建好"复核状态"单选字段后，把其 fieldId 填到这里（占位符缺失时 cell() 返回 ""）
    "review_status": "<REVIEW_STATUS_FIELD_ID>",
}

# 投影行用到的字段（中文键 -> 逻辑名）
_ENGINE_KEYS = {
    "投诉编号": "no", "投诉人": "person", "联系方式": "contact", "被投诉主体": "subject",
    "投诉类型": "ctype", "投诉内容": "content", "诉求金额": "amount", "收到日期": "recv",
    "截止日期": "deadline", "处理状态": "status", "跟进记录": "follow",
    "投诉渠道": "channel", "风险等级": "risk", "风险评分": "score",
    "AI建议": "suggestion", "最终答复": "final", "处理人": "handler", "复核状态": "review_status",
}


def cell(rec, fid):
    """从一条原始记录里安全取某字段ID的值；singleSelect {id,name} 取 name。"""
    c = rec.get("cells", rec) if isinstance(rec, dict) else {}
    v = c.get(fid, "")
    if isinstance(v, dict):
        v = v.get("name", "")
    return str(v).strip() if v is not None else ""


def load_records(path):
    """读台账快照，兼容三种落盘形态，返回"记录列表"（可能是原始 cells 记录，也可能已是投影行）。
    还额外容忍 hook-output 临时文件的"散文前缀"：自动定位 JSON 起点再解析。"""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    obj = _loads_tolerant(text)
    if isinstance(obj, str):
        obj = _loads_tolerant(obj)
    if isinstance(obj, dict):
        # hook-output 包裹 {"type":"dws_tool_result","content":"<escaped json>"}
        if isinstance(obj.get("content"), str):
            obj = _loads_tolerant(obj["content"])
        recs = obj.get("data", {}).get("records") if isinstance(obj.get("data"), dict) else None
        if recs:
            return recs
        return obj.get("records") or obj.get("ledger") or obj.get("cases") or []
    return obj if isinstance(obj, list) else []


def _loads_tolerant(text):
    """json.loads，但先剥掉 hook 文件常见的散文前缀：优先定位 dws_tool_result 标记，
    退而取第一个 '{' 或 '[' 起始处。"""
    s = text.strip() if isinstance(text, str) else text
    if not isinstance(s, str):
        return s
    try:
        return json.loads(s)
    except ValueError:
        pass
    marker = s.find('{"type":"dws_tool_result"')
    if marker == -1:
        marker = s.find('{"type": "dws_tool_result"')
    start = marker if marker != -1 else min(
        [i for i in (s.find("{"), s.find("[")) if i != -1] or [0])
    return json.loads(s[start:])


def _is_raw(rec):
    """判断是否"原始单元格记录"（含 cells 或 fieldId 键），区别于已是中文键投影行。"""
    if not isinstance(rec, dict):
        return False
    if "cells" in rec:
        return True
    keys = set(rec.keys())
    # 投影行用中文键；原始行若出现任一 fieldId 也判为原始
    return bool(keys & set(FM.values()))


def project_one(rec):
    row = {zh: cell(rec, FM[logical]) for zh, logical in _ENGINE_KEYS.items()}
    # 保留 recordId：复核闭环脚本(batch_draft/review_apply)靠它把 AI建议/复核状态 回写到正确记录。
    # 原始快照里 recordId 在记录顶层而非 cells 内，投影时若不透传，写回载荷会丢主键。
    rid = rec.get("recordId") or rec.get("record_id") or rec.get("id") or ""
    if rid:
        row["recordId"] = str(rid)
    return row


def to_engine(records):
    """把记录列表归一为中文键投影行；已是投影行的元素原样透传（幂等）。"""
    return [project_one(r) if _is_raw(r) else r for r in records]


def load_engine(path):
    """一步到位：读文件 -> 投影行列表。巡检/看板都应经此拿数据。"""
    return to_engine(load_records(path))
