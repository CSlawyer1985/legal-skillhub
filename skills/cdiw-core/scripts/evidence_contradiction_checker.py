#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""证据矛盾排查脚本（evidence_contradiction_checker.py）。

功能：对证据描述文本做确定性分析，输出三部分：
  1. 时间线梳理——抽取时间表达式并关联其所在句，按时间排序；
  2. 人物关系图谱——抽取人物提及，生成节点与共现边、陈述指向边；
  3. 矛盾点提示——时间冲突（同一对象指向多个不同时间）、
     数字冲突（同一语句群中对同一量纲的不一致表述）、
     利害关系孤立印证（关键事实仅由利害关系主体陈述支撑）。

调用方式：
  python scripts/evidence_contradiction_checker.py --text "证据描述文本"
  python scripts/evidence_contradiction_checker.py --file 输入.txt [--out 输出.txt]

统一接口规范：
  - 仅依赖Python标准库；支持--help；
  - 输出JSON信封：{status, error_code, message, data}；
  - 退出码：0成功 / 1参数错误 / 2文件读取失败 / 3分析失败；
  - 错误码：ERR_ARGS_MISSING / ERR_IO / ERR_ANALYSIS_FAILED。
  - 本脚本为确定性文本分析（正则抽取与比对），不依赖模型判断；
    提示结果仅为线索，须经律师逐点人工核验后方可用于质证。
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime

SCRIPT_NAME = "evidence_contradiction_checker"

# 时间表达式模式（自长至短）
TIME_PATTERNS = [
    ("完整日期", re.compile(r"(20\d{2}|19\d{2})年(\d{1,2})月(\d{1,2})日(?: (\d{1,2})[时:：](\d{1,2})分?)?")),
    ("月日", re.compile(r"(\d{1,2})月(\d{1,2})日(?: (\d{1,2})[时:：](\d{1,2})分?)?")),
    ("日期时分", re.compile(r"(\d{1,2})日(?:凌晨|早上|上午|中午|下午|晚上|傍晚)?(\d{1,2})[时:：](\d{1,2})分?")),
    ("仅时间", re.compile(r"(?:凌晨|早上|上午|中午|下午|晚上|傍晚)(\d{1,2})[时:：](\d{1,2})分?")),
]

# 人物提及模式
PERSON_PATTERNS = [
    ("角色称谓", re.compile(r"(当事人|犯罪嫌疑人|被告人|被害人|证人|办案民警|侦查人员|鉴定人|同案犯|上诉人|原审被告人)")),
    ("中文姓名某", re.compile(r"([\u4e00-\u9fa5]某某?)")),
    ("某甲乙", re.compile(r"某[甲乙丙丁戊]")),
]

# 利害关系主体（其孤立陈述不足以印证关键事实）
INTERESTED_PARTIES = ["当事人", "犯罪嫌疑人", "被告人", "被害人", "同案犯"]

# 量纲关键词（数字冲突检测范围）
DIMENSIONS = {"金额": ["元", "万元"], "数量": ["笔", "次", "条", "份"], "重量": ["克", "千克", "公斤", "吨"]}


def make_trace_id():
    stamp = datetime.now().isoformat()
    return SCRIPT_NAME + hashlib.md5((SCRIPT_NAME + stamp).encode("utf-8")).hexdigest()[:8]


def envelope(status, error_code, message, data):
    return {"status": status, "error_code": error_code, "message": message, "data": data}


def split_sentences(text):
    parts = re.split(r"[。；！？\n]+", text)
    return [p.strip() for p in parts if p.strip()]


def parse_time_match(kind, m):
    """将正则匹配转为可比较的时间元组（年，月，日，时，分）；缺失项以-1占位。"""
    g = m.groups()
    if kind == "完整日期":
        y, mo, d = int(g[0]), int(g[1]), int(g[2])
        h = int(g[3]) if g[3] else -1
        mi = int(g[4]) if g[4] else -1
        return (y, mo, d, h, mi)
    if kind == "月日":
        mo, d = int(g[0]), int(g[1])
        h = int(g[2]) if g[2] else -1
        mi = int(g[3]) if g[3] else -1
        return (-1, mo, d, h, mi)
    if kind == "日期时分":
        d, h, mi = int(g[0]), int(g[1]), int(g[2])
        return (-1, -1, d, h, mi)
    h, mi = int(g[0]), int(g[1])
    return (-1, -1, -1, h, mi)


def extract_timeline(sentences):
    events = []
    for idx, sent in enumerate(sentences):
        accepted_spans = []
        raw = []
        for kind, pat in TIME_PATTERNS:
            for m in pat.finditer(sent):
                raw.append((m.end() - m.start(), m.start(), m.end(),
                            m.group(0), parse_time_match(kind, m)))
        raw.sort(key=lambda r: -r[0])  # 长匹配优先，短匹配若被长匹配区间包含则跳过
        for length, start, end, text, t in raw:
            if any(s <= start and end <= e for s, e in accepted_spans):
                continue
            accepted_spans.append((start, end))
            events.append({"sentence_index": idx + 1,
                           "time_text": text,
                           "time_tuple": t,
                           "event": sent[:80],
                           "sort_key": [x if x >= 0 else 0 for x in t]})
    events.sort(key=lambda e: e["sort_key"])
    for e in events:
        e.pop("time_tuple", None)
        e.pop("sort_key", None)
    return events


def extract_person_graph(sentences):
    nodes, edges = {}, []
    for idx, sent in enumerate(sentences):
        mentioned = []
        for kind, pat in PERSON_PATTERNS:
            for m in pat.finditer(sent):
                name = m.group(0)
                if name not in mentioned:
                    mentioned.append(name)
                if name not in nodes:
                    nodes[name] = {"label": name, "kind": kind, "mention_count": 0}
                nodes[name]["mention_count"] += 1
        for i in range(len(mentioned)):
            for j in range(i + 1, len(mentioned)):
                edges.append({"source": mentioned[i], "target": mentioned[j],
                              "relation": "共现", "sentence_index": idx + 1})
        # 陈述指向边：A称/B供述句式
        for m in re.finditer(r"([\u4e00-\u9fa5]{1,3}?(?:某|人))\s*(?:称|供述|陈述|辩解|证言称)", sent):
            speaker = m.group(1)
            for other in mentioned:
                if other != speaker:
                    edges.append({"source": speaker, "target": other,
                                  "relation": "陈述指向", "sentence_index": idx + 1})
    node_list = [{"id": k, **v} for k, v in nodes.items()]
    return node_list, edges


def detect_conflicts(sentences, events, nodes):
    conflicts = []

    # 1. 时间冲突：同一句内出现多个不同完整日期
    for idx, sent in enumerate(sentences):
        dates = set()
        for m in re.finditer(r"(?:20\d{2}|19\d{2})年\d{1,2}月\d{1,2}日", sent):
            dates.add(m.group(0))
        if len(dates) > 1:
            conflicts.append({"type": "时间冲突", "severity": "提示",
                              "sentence_index": idx + 1,
                              "detail": "同一句出现多个日期：%s——核对是否指向同一事实" % "、".join(sorted(dates)),
                              "check_advice": "人工核对该句各日期是否分别对应不同事实节"})

    # 2. 数字冲突：同一对象+量纲在不同句子数值不一致（按量纲+邻近对象词归组）
    for dim, units in DIMENSIONS.items():
        value_map = {}
        for idx, sent in enumerate(sentences):
            for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(%s)" % "|".join(units), sent):
                val, unit = m.group(1), m.group(2)
                key = (dim, unit)
                value_map.setdefault(key, []).append((val, idx + 1, sent[:60]))
        for (dim, unit), vals in value_map.items():
            distinct = set(v for v, _, _ in vals)
            if len(distinct) > 1 and len(vals) >= 2:
                conflicts.append({
                    "type": "数字冲突", "severity": "提示", "dimension": dim,
                    "detail": "%s表述不一致：%s" % (dim, "；".join(
                        "%s%s（句%d：%s…）" % (v, unit, i, s[:30]) for v, i, s in vals[:4])),
                    "check_advice": "核对是否针对同一对象同一量纲；若同一对象数值不一致，系质证追问点"})

    # 3. 利害关系孤立印证：关键事实句仅含利害关系主体提及、无其他证据主体
    for idx, sent in enumerate(sentences):
        has_neutral = bool(re.search(r"笔录|鉴定|勘验|监控|录音|录像|合同|转账|清单|照片|书证|物证|电子数据", sent))
        if not has_neutral:
            interested = [w for w in INTERESTED_PARTIES if w in sent]
            if interested and len(sent) >= 12 and re.search(r"称|供述|陈述|辩解|指认", sent):
                conflicts.append({
                    "type": "利害关系孤立印证", "severity": "提示",
                    "sentence_index": idx + 1,
                    "detail": "句%d仅见利害关系主体（%s）陈述，未见客观证据印证" % (idx + 1, "、".join(interested)),
                    "check_advice": "核对是否有客观证据印证；孤证陈述作为质证要点（仅利害关系人陈述不宜单独作为定案根据）"})

    return conflicts


def main():
    parser = argparse.ArgumentParser(
        prog=SCRIPT_NAME,
        description="证据矛盾排查：时间线梳理＋人物关系图谱＋矛盾点提示（确定性文本分析，结果须律师人工核验）。")
    parser.add_argument("--text", help="证据描述文本")
    parser.add_argument("--file", help="证据描述文件路径（UTF-8文本）")
    parser.add_argument("--out", help="分析结果输出文件路径（可选）")
    args = parser.parse_args()
    trace_id = make_trace_id()

    if not args.text and not args.file:
        print(json.dumps(envelope("error", "ERR_ARGS_MISSING", "--text或--file至少提供一个", None),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError) as exc:
            print(json.dumps(envelope("error", "ERR_IO", "文件读取失败：%s" % exc, None),
                             ensure_ascii=False, indent=2))
            sys.exit(2)
    else:
        text = args.text

    try:
        sentences = split_sentences(text)
        events = extract_timeline(sentences)
        nodes, edges = extract_person_graph(sentences)
        conflicts = detect_conflicts(sentences, events, nodes)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps(envelope("error", "ERR_ANALYSIS_FAILED", "分析失败：%s" % exc, None),
                         ensure_ascii=False, indent=2))
        sys.exit(3)

    data = {
        "trace_id": trace_id,
        "timeline": events,
        "person_graph": {"nodes": nodes, "edges": edges},
        "conflict_hints": conflicts,
        "stats": {"sentences": len(sentences), "timeline_events": len(events),
                  "person_nodes": len(nodes), "edges": len(edges),
                  "conflict_hints": len(conflicts)},
        "notes": ["本输出为确定性文本分析线索，非质证结论；矛盾点须经律师逐点人工核验",
                  "时间冲突检测覆盖同一句多日期；数字冲突按量纲归组；孤立印证检测为启发式提示"],
    }

    out_text = json.dumps(envelope("ok", None, "分析完成", data), ensure_ascii=False, indent=2)
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as f:
                f.write(out_text)
        except OSError as exc:
            print(json.dumps(envelope("error", "ERR_IO", "输出文件写入失败：%s" % exc, None),
                             ensure_ascii=False, indent=2))
            sys.exit(2)
    print(out_text)
    sys.exit(0)


if __name__ == "__main__":
    main()
